"""Actual ORM constructor comparison on PostgreSQL-decoded synthetic revisions."""
import gc
import json
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

import pytest
from capacity_target_fixture import calibrated_rows
from django.db import connection, transaction

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision

DEFER = ('source_revision', 'step', 'edit_version', 'telegram',
         'contact_exposure_accepted', 'publisher_acceptance', 'updated_at')
CONSUMED = ('id', 'listing_id', 'manager_version', 'status', 'created_at', 'title',
            'description', 'description_alternative', 'profile_type', 'content_language',
            'municipality_id', 'postal_code_id', 'zone_id', 'spoken_languages', 'days',
            'time_slot', 'reception', 'travel', 'phone', 'whatsapp')
pytestmark = pytest.mark.django_db(transaction=True)


def test_constructor_original_vs_deferred_postgres_rows(record_property):
    assert connection.vendor == 'postgresql'
    rows, manifest = calibrated_rows('revision-defer-synthetic')
    user = User.objects.create_user(username='revision-defer-synthetic', role='individual')
    person = Person.objects.create(alias='revision-defer-synthetic', individual=user, subject=user)
    listing = Listing.objects.create(person=person)
    Revision.objects.bulk_create([Revision(listing=listing, manager_version=0, **row) for row in rows], batch_size=100)
    fields = [f for f in Revision._meta.concrete_fields if f.name != 'search_document']
    names = [f.attname for f in fields]
    keep = [i for i, f in enumerate(fields) if f.name not in DEFER]
    candidate_names = [names[i] for i in keep]
    from unittest.mock import patch

    from_db = Revision.from_db.__func__
    def captured(query):
        data, actual_names = [], []
        def record(cls, db, field_names, values):
            if cls is Revision:
                if not actual_names:
                    actual_names.extend(field_names)
                assert list(field_names) == actual_names
                data.append(tuple(values))
            return from_db(cls, db, field_names, values)
        with patch.object(Revision, 'from_db', classmethod(record)):
            list(query.iterator(chunk_size=1000))
        return actual_names, data
    with transaction.atomic():
        query = listing.revisions.select_for_update(of=('self',)).defer('search_document').select_related(
            'municipality', 'postal_code', 'zone').order_by('created_at', 'pk')
        actual_names, decoded = captured(query)
        actual_candidate_names, candidate_rows = captured(query.defer(*DEFER))
    assert actual_names == names and actual_candidate_names == candidate_names
    assert len(decoded) == 1500
    assert candidate_rows == [tuple(row[i] for i in keep) for row in decoded]
    # Both modes run the actual Django constructor; no simulated DB timings.
    def consume(mode):
        field_names, values = (names, decoded) if mode == 'original' else (candidate_names, candidate_rows)
        for row in values:
            last = Revision.from_db('default', field_names, row)
        return last
    for original_row, candidate_row in zip(decoded, candidate_rows, strict=True):
        original = Revision.from_db('default', names, original_row)
        candidate = Revision.from_db('default', candidate_names, candidate_row)
        assert [getattr(original, name) for name in CONSUMED] == [getattr(candidate, name) for name in CONSUMED]
        assert candidate.get_deferred_fields() - original.get_deferred_fields() == {
            f.attname for f in fields if f.name in DEFER}
    def no_sql(*args, **kwargs):
        raise AssertionError('Constructor unexpectedly issued SQL')
    def experiment(control=False):
        samples = []
        for mode in ('original', 'deferred') * 2:
            consume('original' if control else mode)
        with connection.execute_wrapper(no_sql):
            for block in range(10):
                for mode in ('original', 'deferred', 'deferred', 'original'):
                    wall, cpu = perf_counter_ns(), thread_time_ns()
                    consume('original' if control else mode)
                    elapsed_cpu, elapsed_wall = thread_time_ns()-cpu, perf_counter_ns()-wall
                    samples.append(dict(mode=mode, block=block, wall_ns=elapsed_wall, cpu_ns=elapsed_cpu))
        pairs = []
        for start in range(0, len(samples), 2):
            pair = {item['mode']: item for item in samples[start:start+2]}
            pairs.append({clock: pair['original'][clock] - pair['deferred'][clock]
                          for clock in ('wall_ns', 'cpu_ns')})
        import statistics
        blocks = [{clock: statistics.median(pair[clock] for pair in pairs[start:start+5])
                   for clock in ('wall_ns', 'cpu_ns')} for start in range(0,20,5)]
        wins = {clock: sum(pair[clock] > 0 for pair in pairs) for clock in ('wall_ns','cpu_ns')}
        gate = all(count >= 15 for count in wins.values()) and all(value > 0 for block in blocks for value in block.values())
        return dict(samples=samples, pairs=pairs, blocks=blocks, wins=wins, gate=gate)
    aa, ab = experiment(control=True), experiment()
    aa_neutral = all(5 < value < 15 for value in aa['wins'].values())
    samples, pairs, blocks, wins = (ab[name] for name in ('samples','pairs','blocks','wins'))
    gate = aa_neutral and ab['gate']
    report = dict(samples=samples, pairs=pairs, blocks=blocks, wins=wins, benefit_gate=gate,
                  aa_control=aa, aa_neutral=aa_neutral, defer=DEFER, consumed=CONSUMED, rows=1500, manifest=manifest,
                  gc_enabled=gc.isenabled(), gc_thresholds=gc.get_threshold(),
                  scope='constructor_only_predecoded_postgresql_rows_not_source_or_HTTP',
                  limits=['Rows and candidate column filtering prepared outside clocks',
                          'One model consumed at a time; not application batch memory',
                          'Does not measure SQL transfer, driver adaptation or source freshness',
                          'No product change; no prediction of HTTP benefit'])
    record_property('revision_defer_report', json.dumps(report))
    Path('/tmp/mod08-revision-defer-report.json').write_text(json.dumps(report, indent=2))
