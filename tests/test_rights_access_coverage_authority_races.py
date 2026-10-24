"""Actual PostgreSQL waits and authority; identity/proof fixtures remain synthetic."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety import rights_access_coverage_review
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccessCoverage, RightsAction
from apps.safety.rights import fingerprint
from apps.safety.rights_access_coverage import UNPROJECTED
from apps.safety.rights_access_coverage_store import required_references, save
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical, generate, preview
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independently inspect synthetic current access coverage after lock wait"


def prepared_coverage(request, settings, monkeypatch):
    case, author, staff, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, False
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    source = preview(author, case.pk, case.version, REASON)
    export = generate(
        author, case.pk, uuid4(), case.version, REASON, source,
        information_review_id=decision.pk,
    )
    delivered = unseal(export.encrypted_payload)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    reviewer = User.objects.get(pk=reviewer.pk)
    fresh(case, author, staff, reviewer, operator(reviewer))
    declarations = {
        "sections": {
            section: [
                {"row": row_reference(section, index, row), "delivered_index": index,
                 "decisions": {}}
                for index, row in enumerate(project(source))
            ]
            for section, project in SECTIONS.items()
        },
        "boundaries": {
            name: {"status": "excluded",
                   "reason": "Synthetic declaration awaiting independent evidence validation",
                   "evidence": "Synthetic referenced information review, not final approval"}
            for name in set(source["pending_review"]) | set(delivered["pending_review"]) | UNPROJECTED
        },
    }
    action = decision.action
    snapshot = {
        "action": action.pk, "request": str(action.request_id), "actor": action.actor_id,
        "version": action.expected_version, "operation": action.operation,
        "payload": action.payload_digest, "reason_ciphertext": fingerprint(action.encrypted_reason),
    }
    refs = {
        label: {"action": action.pk, "digest": fingerprint(canonical(snapshot))}
        for label in required_references(declarations)
    }
    coverage = save(
        author, case.pk, case.version, case.response_version, export.pk, uuid4(), REASON,
        delivered, declarations, refs, fingerprint(canonical(source)),
        fingerprint(canonical(delivered)),
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    read(operator(reviewer), case)
    return case, reviewer, coverage


@pytest.mark.parametrize("change", ["valid", "permission", "session", "mfa", "inactive"])
def test_coverage_inspection_checks_current_authority_before_decrypt_after_wait(
    request, settings, monkeypatch, change
):
    case, reviewer, coverage = prepared_coverage(request, settings, monkeypatch)
    key = uuid4()
    pids = Queue()
    coverage_decryptions = []
    real_checked_body = rights_access_coverage_review.checked_body

    def observed_checked_body(ciphertext):
        if ciphertext == coverage.encrypted_coverage:
            coverage_decryptions.append(True)
        return real_checked_body(ciphertext)

    monkeypatch.setattr(rights_access_coverage_review, "checked_body", observed_checked_body)

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=reviewer.pk)
            assert actor.has_perm("safety.respond_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                row, _, _ = rights_access_coverage_review.inspect(
                    actor, case.pk, case.version, coverage.pk, key, REASON
                )
                return row.pk
            except (PermissionDenied, ValidationError):
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsAccessCoverage.objects.select_for_update().get(pk=coverage.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            worker = pids.get(timeout=5)
            assert worker != holder
            observe_blocked(worker, holder)
            if change == "permission":
                reviewer.user_permissions.remove(
                    Permission.objects.get(codename="respond_rights_request")
                )
            elif change in {"session", "mfa"}:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=reviewer.pk).update(**{field: getattr(reviewer, field) + 1})
            elif change == "inactive":
                User.objects.filter(pk=reviewer.pk).update(is_active=False)
        result = future.result(timeout=60)
    if change == "valid":
        assert result == coverage.pk
        assert coverage_decryptions
        assert RightsAction.objects.filter(key=key, operation="access_cover_read").exists()
    else:
        assert result is None
        assert not RightsAction.objects.filter(key=key).exists()
        assert not coverage_decryptions, f"Coverage decrypted after {change} revocation during wait"
