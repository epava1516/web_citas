import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import close_old_connections, connections, transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared, url

from apps.safety.models import RightsAction, RightsExport
from apps.safety.tasks import purge_expired_exports

pytestmark = pytest.mark.django_db(transaction=True)


def test_expired_content_removed_without_deleting_source_or_audit(request, settings):
    case, user, _, client, receipt, person = prepared(request, settings)
    export = make_copy(case, user)
    source_count = person.listing.revisions.count()
    original_proof = export.proof_id
    assert purge_expired_exports() == 0
    RightsExport.objects.filter(pk=export.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_exports() == 1
    export.refresh_from_db()
    assert export.encrypted_payload == "" and export.purged_at is not None
    assert (
        export.proof_id == original_proof
        and RightsAction.objects.filter(pk=export.action_id).exists()
    )
    assert person.listing.revisions.count() == source_count
    date = export.purged_at
    assert purge_expired_exports() == 0
    export.refresh_from_db()
    assert export.purged_at == date
    # Moving the expiry cannot revive a purged artifact or its download button.
    RightsExport.objects.filter(pk=export.pk).update(expires_at=timezone.now() + timedelta(hours=1))
    assert client.post(url(receipt, export), {"key": uuid.uuid4()}).status_code == 404
    assert not client.get(receipt).context["exports"]


def test_locked_copy_skipped_then_purged_on_next_scan(request, settings):
    case, user, _, _, _, _ = prepared(request, settings)
    export = make_copy(case, user)
    RightsExport.objects.filter(pk=export.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    def scan():
        close_old_connections()
        try:
            return purge_expired_exports()
        finally:
            connections.close_all()

    with transaction.atomic():
        RightsExport.objects.select_for_update().get(pk=export.pk)
        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(scan).result(timeout=10) == 0
        assert RightsExport.objects.get(pk=export.pk).encrypted_payload
    assert purge_expired_exports() == 1
