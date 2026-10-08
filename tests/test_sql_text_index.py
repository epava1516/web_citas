"""Partial-index membership remains current across writes and transaction rollback."""
import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Rate, Revision
from apps.listings.sql_publication import SQLPublication
from apps.listings.text_proof import rate_text_unknown, revision_text_unknown
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_indexed_unknowns_follow_writes_rollback_and_complete_native_population(request, record_property):
    request.getfixturevalue('directory')
    populate(50)
    assert connection.vendor == 'postgresql' and projection.supported()
    with connection.cursor() as cursor:
        cursor.execute('SELECT indexrelid::regclass::text, indisvalid FROM pg_index '
                       'WHERE indexrelid::regclass::text = ANY(%s)',
                       [['revision_text_unknown_v1', 'rate_text_unknown_v1']])
        assert dict(cursor.fetchall()) == {'revision_text_unknown_v1': True, 'rate_text_unknown_v1': True}
    expected = native_ids(candidates({}))
    target = candidates({}).get(pk=expected[25]).approved_revision
    rate = Rate.objects.filter(revision=target).first()
    assert rate is not None and target.listing_id not in expected[:24]
    observed = []
    for model, pk, change, unknown in [
        (Revision, target.pk, {'description': 'www.example.invalid'}, revision_text_unknown),
        (Revision, target.pk, {'description': 'Texto válido 😀'}, revision_text_unknown),
        (Revision, target.pk, {'description': 'a'*6001}, revision_text_unknown),
        (Revision, target.pk, {'title': ''}, revision_text_unknown),
        (Rate, rate.pk, {'concept': ''}, rate_text_unknown),
        (Rate, rate.pk, {'concept': 'Consulta 😀'}, rate_text_unknown),
    ]:
        assert not model.objects.filter(pk=pk).filter(unknown()).exists()
        with transaction.atomic():
            model.objects.filter(pk=pk).update(**change)
            assert model.objects.filter(pk=pk).filter(unknown()).exists()
            native = native_ids(candidates({}))
            p = SQLPublication(candidates({}), text_membership=True)
            assert p.visible_ids(candidates({})) == native
            control = SQLPublication(candidates({}), text_membership=False)
            assert control.visible_ids(candidates({})) == native
            assert p.rows == control.rows
            assert p.stats['native_fallback'] == 1
            for number in (1,2,3):
                page = projection.projected_page(candidates({}), number)
                assert page.paginator.count == len(native)
                assert [r.pk for r in page] == native[(number-1)*24:number*24]
            observed.append({'model': model._meta.label, 'fields': sorted(change),
                             'native_count':len(native), 'unknowns':p.stats['native_fallback']})
            transaction.set_rollback(True)
        assert not model.objects.filter(pk=pk).filter(unknown()).exists()
        restored = SQLPublication(candidates({}), text_membership=True)
        assert restored.visible_ids(candidates({})) == expected
        assert restored.stats['native_fallback'] == 0
    record_property('index_write_rollback_equivalence', observed)
