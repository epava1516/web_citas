"""Observed PostgreSQL account-lock waits must not preserve stale copy authority."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_account_linking import account
from test_rights_assignment import action
from test_rights_exports import url
from test_rights_responses import ready

from apps.core.models import User
from apps.listings.models import Favorite, Listing
from apps.safety.models import RightsExport, RightsExportDownload, RightsExportPreview
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic own account copy review"


def prepared_account(request, settings, monkeypatch):
    import test_rights_exports

    request.getfixturevalue("directory")
    subject = account()

    def link_account(staff, case, person):
        path, values = action(staff, case, "link")
        return path, values | {"link_account_id": subject.pk}

    monkeypatch.setattr(test_rights_exports, "link", link_account)
    case, actor, staff, public, receipt, _ = ready(request, settings, monkeypatch, "access")
    return case, actor, staff, subject, public, receipt


@pytest.mark.parametrize("operation", ["preview", "generate", "download"])
def test_copy_rechecks_source_after_observed_account_wait(
    request, settings, monkeypatch, operation
):
    case, actor, _, subject, _, receipt = prepared_account(request, settings, monkeypatch)
    source = None
    export = None
    if operation != "preview":
        source = preview(actor, case.pk, case.version, REASON)
    if operation == "download":
        export = generate(actor, case.pk, uuid4(), case.version, REASON, source)
    case.refresh_from_db()
    version = case.version
    before = (
        RightsExportPreview.objects.count(),
        RightsExport.objects.count(),
        RightsExportDownload.objects.count(),
    )
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            if operation == "download":
                return Client().post(url(receipt, export), {"key": uuid4()}).status_code
            try:
                user = User.objects.get(pk=actor.pk)
                if operation == "preview":
                    preview(user, case.pk, version, REASON)
                else:
                    generate(user, case.pk, uuid4(), version, REASON, source)
            except ValidationError:
                return "denied"
            return "admitted"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(pk=subject.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if operation == "generate":
                Favorite.objects.create(user=locked_user, listing=Listing.objects.first())
            else:
                locked_user.mfa_version += 1
                locked_user.save(update_fields=["mfa_version"])
        assert future.result(timeout=15) == (404 if operation == "download" else "denied")
    assert (
        RightsExportPreview.objects.count(),
        RightsExport.objects.count(),
        RightsExportDownload.objects.count(),
    ) == before
    case.refresh_from_db()
    assert case.version == version
