"""Explicit real PostgreSQL wait: revoked rights inspection must remain private."""

import os
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from test_operational_recovery_authority_wait import _observe_wait_and_revoke
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_linking import ready

from apps.core.models import User
from apps.safety.models import RightsAccess, RightsAction, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


def test_rights_inspection_denies_permission_revoked_during_actual_case_wait(
    request, settings, record_property
):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL rights inspection wait only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()
    case, actor, client = ready(request)
    case.refresh_from_db()
    assert case.person_id is None and case.account_subject_id is None
    assert case.assigned_to_id == actor.pk and case.status == "reviewing"
    assert User.objects.get(pk=actor.pk).has_perm("safety.review_rights_request")
    assert RightsAccess.objects.filter(request=case, actor=actor).count() == 1
    queries = {
        "case": RightsRequest.objects.filter(pk=case.pk),
        "access": RightsAccess.objects.all(),
        "action": RightsAction.objects.all(),
    }

    def minimal_state():
        return RightsRequest.objects.filter(pk=case.pk).values(
            "version", "status", "response_version"
        ).get()

    _observe_wait_and_revoke(
        actor=actor,
        client=client,
        route=f"/en/moderation/rights/{case.pk}/",
        payload={"purpose": "Synthetic scoped inspection after an observed authority wait"},
        permission_name="safety.review_rights_request",
        held_model=RightsRequest,
        held_pk=case.pk,
        queries=queries,
        minimal_state=minimal_state,
        case_label="rights_inspection",
        record_property=record_property,
    )
