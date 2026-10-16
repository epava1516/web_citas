"""Finite PostgreSQL cost audit; never replace the application's mark function."""
import json
import os
import time
from importlib import import_module
from pathlib import Path

import pytest
from django.db import connection
from django.db.models import Max
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Match, Photo
from apps.safety.canonical_kernel_loader import kernel_identity
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_publication_mark_cost(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_publication_mark_cost.py' for x in request.config.args):
        pytest.skip('Explicit bounded diagnostic only')
    out=Path(request.config.getoption('--gate-timings-output')).parent
    run=json.loads((out/'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER']=='web-modelos-ci-pg-'+run['id']
    assert kernel_identity()['mode']=='native-sealed'
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state,'delay',lambda:None)
    populate(10000)
    target=Listing.objects.get(person__individual__username='fixture-v1-individual')
    draft=Revision.objects.create(listing=target,manager_version=target.person.manager_version)
    Photo.objects.create(revision=draft,blob=target.approved_revision.photos.first().blob)
    assert not Match.objects.exists()
    all_ids=list(Listing.objects.filter(status='published').values_list('pk',flat=True))
    assert len(all_ids)==10000
    original=import_module('apps.listings.migrations.0015_publication_state').MARK
    current=import_module('apps.listings.migrations.0020_publication_match_counterparts').MARK
    with connection.cursor() as cursor:
        for table in ['listings_listing','listings_revision','mediafiles_photo','mediafiles_match']:
            cursor.execute('ANALYZE '+table)
    records=[]
    for block in range(3):
        arms=[('baseline',original),('current',current)]
        if block%2:
            arms.reverse()
        for arm,source in arms:
            connection.close()
            with connection.cursor() as cursor:
                cursor.execute('CREATE TEMP TABLE cr09_mark_scope (value integer)')
                needle='FUNCTION listings_publication_mark('
                assert source.count(needle)==1
                cursor.execute(source.replace(needle,'FUNCTION pg_temp.cr09_mark('))
                cursor.execute("SELECT prosrc FROM pg_proc WHERE oid='listings_publication_mark(uuid[])'::regprocedure")
                assert cursor.fetchone()[0]==current.split('$$')[1]
                cursor.execute('SHOW plan_cache_mode')
                mode=cursor.fetchone()[0]
                cursor.execute('DELETE FROM listings_publicationdirty')
                sequence=[('empty',[])] + [('single',[target.pk])]*10 + [('bulk',all_ids)]*2 + [('single_after_bulk',[target.pk])]*5
                for repeat,(phase,ids) in enumerate(sequence):
                    before=PublicationDirty.objects.aggregate(n=Max('generation'))['n'] or 0
                    wall,cpu=time.perf_counter(),time.thread_time()
                    cursor.execute('SELECT pg_temp.cr09_mark(%s::uuid[])',[ids])
                    record={'arm':arm,'block':block,'phase':phase,'repeat':repeat,'input_ids':len(ids),'wall_ms':(time.perf_counter()-wall)*1000,'caller_cpu_ms':(time.thread_time()-cpu)*1000,'plan_cache_mode':mode}
                    changed=set(PublicationDirty.objects.filter(generation__gt=before).values_list('listing_id',flat=True))
                    assert changed==set(ids)
                    records.append(record)
                cursor.execute("SELECT prosrc FROM pg_proc WHERE oid='listings_publication_mark(uuid[])'::regprocedure")
                assert cursor.fetchone()[0]==current.split('$$')[1]
    record_property('publication_mark_cost',json.dumps(records))
    record_property('limits','Owned synthetic PG10k, no Match rows, actual global0020 untouched. Baseline lacks required counterpart behavior and is only a cost reference. Session-local pg_temp copies, AB/BA, fresh session each arm, cold/single/bulk/repeated. Wall includes client/SQL/PLpgSQL planning/execution, caller CPU is not PG CPU. No HTTP/p95 or causal regression proof.')
