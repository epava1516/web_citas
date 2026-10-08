"""SQL-only code-template prototype: fresh data/binds/candidates, no eligibility cache."""
import hashlib
import json
import os
import statistics
import time
from collections import Counter
from datetime import datetime
from datetime import timezone as datetime_timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import BooleanField, Case, Value, When
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.core.models import Person
from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings import sql_publication as proof
from apps.listings.models import Listing, Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('STATEMENT_TEMPLATE_OUTPUT'), reason='Explicit isolated code-template prototype only')]


def prepare_template():
    """Development-only compilation from current audited source, no DB values."""
    marker = '__owned_current_document_parameter__'
    instant = datetime(2099, 1, 1, tzinfo=datetime_timezone.utc)
    with patch.object(proof.timezone, 'now', return_value=instant):
        condition = proof.authority_proof(SimpleNamespace(version=marker), bulk=True) & proof.content_proof(bulk=True)
    query = Listing.objects.order_by().annotate(_sql_publication_positive=Case(
        When(condition, then=Value(True)), default=Value(False), output_field=BooleanField()))
    selected = query.values('pk', 'approved_revision_id', '_sql_publication_positive')
    compiler = selected.query.get_compiler(connection=connection)
    statement, params = compiler.as_sql()
    sources, from_params = compiler.get_from_clause()
    assert sources[0] == connection.ops.quote_name(Listing._meta.db_table) and not from_params
    ending = ' FROM ' + ' '.join(sources)
    assert statement.endswith(ending)
    head = statement[:-len(ending)]
    assert head.count('%s') == len(params)
    assert params.count(instant) == 1 and params.count(marker) >= 2
    return head, ' '.join(sources[1:]), tuple(params), instant, marker


def read_template(query, template, *, compiled_only=False):
    document = proof.submissions.current_publishing_document()
    try:
        if not document:
            raise ValidationError('No current document')
        proof.ContactsForm.base_fields['legal_version'].clean(document.version)
    except ValidationError:
        assert not compiled_only
        return proof.SQLPublication(query).rows
    head, joins, values, instant, marker = template
    fields, order_sql = proof.compact_order(query, 1)
    candidates = query.values('pk', 'approved_revision_id', *fields)
    candidate_sql, candidate_params = candidates.query.get_compiler(connection=connection).as_sql()
    # Each call obtains current bindings. The reused data describe CODE only;
    # authority/content rows are read again in this very statement's snapshot.
    now = timezone.now()
    params = [now if value == instant else document.version if value == marker else value for value in values]
    ordering_fields = ', '.join('"_current_candidates"."'+field+'" AS "'+field+'"' for field in fields)
    qualified_order = ', '.join('"_current_statement".'+part for part in order_sql.split(', '))
    source = f'''{head}, {ordering_fields}
        FROM ({candidate_sql}) AS "_current_candidates"
        INNER JOIN "listings_listing" ON "listings_listing"."id" = "_current_candidates"."pk"
        {joins}'''
    sql = f'''SELECT "_current_statement"."pk"::text AS pk,
        "_current_statement"."approved_revision_id"::text AS approved_revision_id,
        "_current_statement"."_sql_publication_positive"
        FROM ({source}) AS "_current_statement" ORDER BY {qualified_order}'''
    params += list(candidate_params)
    if compiled_only:
        return sql, params
    rows = proof.read_publication_values(proof.CapturedSQLRead(sql, params))
    by_id = {row['pk']: row for row in rows}
    assert len(by_id) == len(rows)
    return rows


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_statement_code_template(request, record_property, variant):
    request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        revisions = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, revision in enumerate(revisions):
            suffix = alpha(index)
            revision.description += ' '+suffix
            if revision.description_alternative:
                revision.description_alternative += ' '+suffix
            revision.telegram = 'bench'+suffix
        Revision.objects.bulk_update(revisions, ['description','description_alternative','telegram'], batch_size=250)
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    digest = projection.definitions_digest()
    assert projection.supported()
    start = time.perf_counter()
    template = prepare_template()
    prepared_seconds = time.perf_counter()-start
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE '+connection.ops.quote_name(table))
    output = Path(os.environ['STATEMENT_TEMPLATE_OUTPUT'], variant+'.json')
    report = {'variant':variant,'source_fingerprint':digest,'stage':'prepared',
        'template_code_sha256':hashlib.sha256((template[0]+template[1]).encode()).hexdigest(),
        'template_parameter_types':dict(Counter(type(v).__name__ for v in template[2])),
        'one_development_compilation_seconds':prepared_seconds}

    def persist():
        output.write_text(json.dumps(report,indent=2)+'\n')

    def read(data, mode, *, read_only=True):
        query = discovery.candidates(data)
        with transaction.atomic(), connection.cursor() as cursor:
            if read_only:
                cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute("SET LOCAL statement_timeout='2000ms'")
            start = time.perf_counter()
            rows = proof.SQLPublication(query).rows if mode == 'current' else read_template(query,template)
            elapsed = time.perf_counter()-start
        return rows, elapsed

    families = [('listing',{}),('search',{'q':'photography'})]
    expected = {}
    for family,data in families:
        old,_ = read(data,'current')
        new,_ = read(data,'template')
        assert new == old and len(old)==10000 and all(r['_sql_publication_positive'] for r in old)
        expected[family]=old
    target = Listing.objects.get(pk=expected['listing'][25]['pk'])
    assert str(target.pk) not in [r['pk'] for r in expected['listing'][:24]]
    mutations=[]
    for model, pk, values in [
        (Revision,target.approved_revision_id,{'description':'www.example.invalid'}),
        (Revision,target.approved_revision_id,{'description':'Texto válido 😀'}),
        (Revision,target.approved_revision_id,{'spoken_languages':[['es']]}),
        (Revision,target.approved_revision_id,{'days':[1]}),
        (Revision,target.approved_revision_id,{'telegram':' @Valid_name '}),
        (Revision,target.approved_revision_id,{'manager_version':998}),
        (Person,target.person_id,{'consent_revoked_at':timezone.now()}),
        (Listing,target.pk,{'expires_at':timezone.now()}),
    ]:
        with transaction.atomic():
            model.objects.filter(pk=pk).update(**values)
            for _,data in families:
                old,_=read(data,'current',read_only=False)
                new,_=read(data,'template',read_only=False)
                assert new==old
            transaction.set_rollback(True)
        mutations.append(sorted(values))
    # Candidate filtering, DISTINCT and search rank remain produced by the
    # actual public compiler, not reconstructed in the template.
    for data in [{'profile':[target.approved_revision.profile_type]}, {'q':'load'},
                 {'language':['es']}, {'day':['1']}, {'channel':['phone']}]:
        assert read(data,'template')[0] == read(data,'current')[0]
    report.update(stage='equivalence',mutation_fields=mutations,candidate_filter_vectors_equal=True)
    persist()
    before=stats_snapshot()
    samples=[]
    for pair in range(8):
        for family,data in families:
            for mode in ['current','template'] if pair%2==0 else ['template','current']:
                rows,elapsed=read(data,mode)
                assert rows==expected[family]
                samples.append({'pair':pair,'family':family,'mode':mode,'construction_and_read_seconds':elapsed,
                    'explicit_statement_rows_returned':len(rows)})
        report.update(stage='controls',samples=samples)
        persist()
    after=stats_snapshot()
    medians={f:{m:statistics.median(s['construction_and_read_seconds'] for s in samples if s['family']==f and s['mode']==m)
        for m in ['current','template']} for f,_ in families}
    deltas=[statistics.mean(
        next(s['construction_and_read_seconds'] for s in samples if s['pair']==pair and s['family']==f and s['mode']=='current')
        - next(s['construction_and_read_seconds'] for s in samples if s['pair']==pair and s['family']==f and s['mode']=='template')
        for f,_ in families) for pair in range(8)]
    threshold=max(.05,.15*statistics.mean(v['current'] for v in medians.values()))
    effect=statistics.median(deltas)>=threshold and sum(v>0 for v in deltas)>=6 and all(
        v['template']-v['current']<=max(.025,.10*v['current']) for v in medians.values())
    plans=[]
    for family,data in families:
        sql,params=read_template(discovery.candidates(data),template,compiled_only=True)
        with transaction.atomic(),connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute("SET LOCAL statement_timeout='2000ms'")
            cursor.execute('SET LOCAL jit=off')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) '+sql,params)
            plans.append({'family':family,'query_pattern':query_pattern(sql),'plan':redact_plan(cursor.fetchone()[0])})
    assert projection.supported() and projection.definitions_digest()==digest
    report.update(stage='complete',medians=medians,deltas=deltas,threshold_seconds=threshold,
        material_constructor_effect=effect,stats_before=before,stats_after=after,statistics_endpoints_equal=before==after,
        separate_candidate_plans=plans,
        scope='SQL-only development prototype, no public application change. Current SQLPublication constructor versus generated code template with fresh document/time bindings and freshly compiled full candidate filters/DISTINCT/rank/order; same single statement reads ALL actual authority/content. Template has no runtime data or retainedeligibility, prepared only in test outside controls; no crossrequest applicationcache introduced. Every sample rebuilds candidatequery before constructor timer equally; timer covers document lookup/validation, rule SQL construction/compilation, execution/fetch/dict/byid for current and template. Eight pairs/listing-search, full ordered proofvectors +offpage/fivefilter mutations, not nativecompleteacceptance. Exactrowfetch cardinality only, no scanned/affected inferred. Newplans aftercontrols, sourceCASEplans reused. No serverCPU/validation attribution from intervals. For integration code/data/version/schema/metadata dependencies and invalidation MUST be designed and tested before HTTP adoption.',
        not_measured=['wholeHTTPeffect','newnativeequivalence','per-rulevalidation/render','CPU PostgreSQL/waits/locks/IO',
            'rows_affected/scanned','templateapplicationdependencyguard (prototypeonly)','capacity'])
    persist()
    record_property('statement_template_probe',json.dumps(report))
