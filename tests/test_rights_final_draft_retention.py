"""Actual PostgreSQL cleanup preserves issued response evidence and replay."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_erasure_execution import PURPOSES, REASON, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import User
from apps.safety.erasure_execution import execute
from apps.safety.erasure_final import inspect, issue, prepare, review
from apps.safety.models import RightsAction
from apps.safety.tasks import purge_expired_access_response_drafts

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("state", ["unused", "issued", "legacy_issued"])
def test_expired_unused_text_is_purged_but_issued_evidence_survives(
    request, settings, monkeypatch, state
):
    case, actor, staff, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read(staff, case)
    arguments = actor, case.pk, case.version, case.response_version
    draft = prepare(
        *arguments,
        execution.pk,
        uuid4(),
        REASON,
        "Las credenciales indicadas se han suprimido; continúan pendientes otras finalidades y comprobaciones operativas.",
        True,
    )
    original = draft.encrypted_reason, draft.payload_digest, draft.key, draft.expected_version
    approval, response, key = None, None, uuid4()
    if state != "unused":
        reviewer = User.objects.get(username="fixture-v1-visitor")
        reviewer.user_permissions.add(
            *Permission.objects.filter(
                codename__in=[
                    "review_rights_request",
                    "execute_rights_request",
                    "respond_rights_request",
                ]
            )
        )
        other = Client()
        other.force_login(reviewer)
        session = other.session
        session["mfa_version"] = reviewer.mfa_version
        session.save()
        read(other, case)
        audited, _ = inspect(
            reviewer,
            case.pk,
            case.version,
            case.response_version,
            draft.pk,
            "Inspect exact erasure draft before independent approval",
        )
        approval = review(
            reviewer,
            case.pk,
            case.version,
            case.response_version,
            draft.pk,
            audited.pk,
            uuid4(),
            "approved",
            REASON,
        )
        response = issue(*arguments, approval.pk, key)
        if state == "legacy_issued":
            RightsAction.objects.filter(pk=draft.pk).update(final_response=None)
    fresh = None
    if state == "unused":
        fresh = prepare(
            *arguments,
            execution.pk,
            uuid4(),
            REASON,
            "Este borrador vigente debe conservar su texto mientras se completa la revisión independiente prevista.",
            True,
        )
    RightsAction.objects.filter(pk=draft.pk).update(created_at=timezone.now() - timedelta(hours=25))
    count = purge_expired_access_response_drafts()
    draft.refresh_from_db()
    assert count == (1 if state == "unused" else 0)
    assert (draft.payload_digest, draft.key, draft.expected_version) == original[1:]
    if state == "unused":
        assert draft.encrypted_reason == "" and draft.purged_at
    else:
        assert draft.encrypted_reason == original[0] and not draft.purged_at
        assert draft.final_response_id == response.pk
        assert issue(*arguments, approval.pk, key).pk == response.pk
    if fresh:
        fresh.refresh_from_db()
        assert fresh.encrypted_reason and not fresh.purged_at
    assert purge_expired_access_response_drafts() == 0


def test_unused_draft_cleanup_is_bounded_and_continues_on_next_run(request, settings, monkeypatch):
    case, actor, staff, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read(staff, case)
    draft = prepare(
        actor,
        case.pk,
        case.version,
        case.response_version,
        execution.pk,
        uuid4(),
        REASON,
        "Borrador sintético para comprobar limpieza acotada de texto caducado sin respuestas emitidas.",
        True,
    )
    # Synthetic ledger volume exercises cleanup, not additional verified executions.
    RightsAction.objects.bulk_create(
        [
            RightsAction(
                key=uuid4(),
                request=case,
                actor=actor,
                expected_version=draft.expected_version,
                operation=draft.operation,
                payload_digest=draft.payload_digest,
                encrypted_reason=draft.encrypted_reason,
            )
            for _ in range(100)
        ]
    )
    rows = RightsAction.objects.filter(request=case, operation="erase_final_draft")
    rows.update(created_at=timezone.now() - timedelta(hours=25))
    assert purge_expired_access_response_drafts() == 100
    assert rows.filter(purged_at__isnull=False, encrypted_reason="").count() == 100
    assert rows.filter(purged_at__isnull=True).count() == 1
    assert purge_expired_access_response_drafts() == 1
    assert purge_expired_access_response_drafts() == 0
    assert rows.count() == 101
