"""Assessment writes and reads recheck source/proof after observed PostgreSQL waits."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_account_copy_races import prepared_account
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability import assessment
from test_rights_responses import ready

from apps.core.models import User
from apps.safety.models import RightsAction, RightsPortabilityAssessment, RightsRequest
from apps.safety.rights_portability import inspect_assessment, save_assessment

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("operation", ["save", "inspect"])
@pytest.mark.parametrize("change", ["source", "proof"])
def test_assessment_operation_rechecks_after_observed_case_wait(
    request, settings, monkeypatch, account_only, operation, change
):
    if account_only:
        case, actor, _, subject, _, _ = prepared_account(
            request, settings, monkeypatch, "portability"
        )
        person = None
    else:
        case, actor, _, _, _, person = ready(request, settings, monkeypatch, "portability")
        subject = None
    value = assessment()
    reason = "Synthetic portability assessment concurrency check"
    row = None
    if operation == "inspect":
        row = save_assessment(actor, case.pk, case.version, uuid4(), 0, reason, value)
    before = (RightsAction.objects.count(), RightsPortabilityAssessment.objects.count())
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                if operation == "save":
                    save_assessment(
                        user,
                        case.pk,
                        case.version,
                        uuid4(),
                        0,
                        reason,
                        value,
                        expected_source_digest=source_digest,
                    )
                else:
                    inspect_assessment(user, case.pk, case.version, row.pk, uuid4(), reason)
            except (PermissionDenied, ValidationError):
                return "denied"
            return "admitted"
        finally:
            connections.close_all()

    from apps.safety.rights import fingerprint
    from apps.safety.rights_exports import canonical, reviewer_case, source_copy

    with transaction.atomic():
        current, profile, listing = reviewer_case(actor, case.pk)
        source_digest = fingerprint(canonical(source_copy(profile, listing, current)))
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if change == "proof":
                case.proofs.update(status="failed")
            elif account_only:
                User.objects.filter(pk=subject.pk).update(first_name="Changed synthetic source")
            else:
                person.listing.revisions.update(description="Changed source during observed wait")
        assert future.result(timeout=20) == "denied"
    assert before == (RightsAction.objects.count(), RightsPortabilityAssessment.objects.count())
