"""Independent verification authority must also survive a real final proof-row wait."""

import os
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from test_operational_recovery_authority_wait import _observe_wait_and_revoke
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_operations_authority_wait import _domain_queries, _fresh_operator
from test_rights_verification import payload as verification_payload
from test_rights_verification import prepared as verification_prepared
from test_rights_verification import read

from apps.safety.models import RightsProof, RightsProofEvent, RightsRequest
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def test_verification_result_denies_verify_permission_revoked_during_actual_proof_wait(
    request, settings, record_property
):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL final verification proof wait only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()
    case, initiator, original_client, person, verifier, client = verification_prepared(request, settings)
    assert celery_app.conf.task_always_eager
    case.refresh_from_db()
    initiator = _fresh_operator(initiator)
    read(original_client, case)
    path, values = verification_payload(original_client, case, "start")
    assert original_client.post(path, values).status_code == 302
    case.refresh_from_db()
    person.refresh_from_db()
    actor = _fresh_operator(verifier)
    read(client, case)
    case.refresh_from_db()
    proof = case.proofs.latest("created_at")
    proof.refresh_from_db()
    assert proof.status == "pending" and proof.case_version == case.version
    assert proof.provider == "simulator" and settings.RIGHTS_VERIFICATION_BACKEND == "simulator"
    assert proof.initiated_by_id == initiator.pk
    assert actor.pk not in (proof.initiated_by_id, case.assigned_to_id)
    assert actor.has_perm("safety.verify_rights_scope")
    assert not RightsProofEvent.objects.filter(proof=proof).exists()
    path, values = verification_payload(client, case, "result", outcome="passed")
    assert values["version"] == case.version

    def minimal_state():
        return RightsRequest.objects.filter(pk=case.pk).values(
            "version", "response_version", "status", "scope_status"
        ).get()

    _observe_wait_and_revoke(
        actor=actor, client=client, route=path, payload=values,
        permission_name="safety.verify_rights_scope", held_model=RightsProof, held_pk=proof.pk,
        queries=_domain_queries(case, person), minimal_state=minimal_state,
        case_label="rights_verification_result_proof_lock_revocation", record_property=record_property,
    )
