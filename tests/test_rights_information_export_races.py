"""Bound information exports reject evidence changed during observed PostgreSQL waits."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_information_export import approved_information

from apps.core.models import LegalDocument, User
from apps.safety.models import (
    RightsAction,
    RightsExport,
    RightsExportDownload,
    RightsExportInformationBinding,
    RightsRequest,
)
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("operation", ["generate", "download"])
@pytest.mark.parametrize("change", ["policy", "decision"])
def test_bound_copy_rechecks_evidence_after_observed_wait(
    request, settings, monkeypatch, account_only, operation, change
):
    case, actor, _, _, receipt, _, _, _, decision, document, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    reason = "Generate synthetic approved copy for observed concurrency"
    source = preview(actor, case.pk, case.version, reason)
    export = None
    if operation == "download":
        export = generate(
            actor, case.pk, uuid4(), case.version, reason, source, information_review_id=decision.pk
        )
    case.refresh_from_db()
    version = case.version
    before = (
        RightsAction.objects.count(),
        RightsExport.objects.count(),
        RightsExportInformationBinding.objects.count(),
        RightsExportDownload.objects.count(),
    )
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            if operation == "download":
                return (
                    Client()
                    .post(
                        url(receipt, export),
                        {"key": uuid4(), "purpose": "Download synthetic copy after observed wait"},
                    )
                    .status_code
                )
            try:
                generate(
                    user,
                    case.pk,
                    uuid4(),
                    version,
                    reason,
                    source,
                    information_review_id=decision.pk,
                )
            except (PermissionDenied, ValidationError):
                return "denied"
            return "admitted"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if change == "policy":
                LegalDocument.objects.filter(pk=document.pk).update(
                    body="Changed policy during wait"
                )
            else:
                type(decision).objects.filter(pk=decision.pk).update(outcome="rejected")
        assert future.result(timeout=20) == (404 if operation == "download" else "denied")
    assert before == (
        RightsAction.objects.count(),
        RightsExport.objects.count(),
        RightsExportInformationBinding.objects.count(),
        RightsExportDownload.objects.count(),
    )
