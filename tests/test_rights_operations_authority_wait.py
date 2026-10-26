"""Four explicit real PostgreSQL waits; rights operations must deny revoked actors."""

import os
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from test_erasure_inventory import values as inventory_values
from test_operational_recovery_authority_wait import _observe_wait_and_revoke
from test_privacy_publication_holds import values as hold_values
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready
from test_rights_verification import payload as verification_payload
from test_rights_verification import prepared as verification_prepared
from test_rights_verification import read

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.safety.models import (
    ErasureInventory,
    PrivacyPublicationHold,
    RightsAccess,
    RightsAction,
    RightsProof,
    RightsProofEvent,
    RightsRequest,
)
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip('Explicit serial owned PostgreSQL rights-operation wait diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_')
    _owned_database()


def _domain_queries(case, person):
    return {
        'case': RightsRequest.objects.filter(pk=case.pk),
        'actions': RightsAction.objects.filter(request=case),
        'access': RightsAccess.objects.filter(request=case),
        'person': Person.objects.filter(pk=person.pk),
        'listing': Listing.objects.filter(person=person),
        'revisions': Revision.objects.filter(listing__person=person),
        'holds': PrivacyPublicationHold.objects.filter(action__request=case),
        'inventory': ErasureInventory.objects.filter(action__request=case),
        'proofs': RightsProof.objects.filter(request=case),
        'proof_events': RightsProofEvent.objects.filter(proof__request=case),
    }


def _case_state(case_id):
    return RightsRequest.objects.filter(pk=case_id).values(
        'version', 'response_version', 'status', 'scope_status',
    ).get()


def _fresh_operator(actor):
    current = User.objects.get(pk=actor.pk)
    assert current.is_active and current.account_erased_at is None and current.mfa_enabled
    assert current.has_perm('safety.review_rights_request')
    return current


def test_privacy_hold_denies_execute_permission_revoked_during_actual_case_wait(
    request, settings, monkeypatch, record_property
):
    _owned_serial(request, settings)
    case, actor, client, _, _, person = ready(request, settings, monkeypatch, 'restriction')
    assert celery_app.conf.task_always_eager
    case.refresh_from_db()
    person.refresh_from_db()
    actor = _fresh_operator(actor)
    read(client, case)
    case.refresh_from_db()
    proof = case.proofs.latest('created_at')
    proof.refresh_from_db()
    assert case.kind == 'restriction' and case.status == 'reviewing'
    assert case.assigned_to_id == actor.pk and proof.status == 'passed'
    assert proof.scope == case.kind and proof.case_version == case.version
    assert proof.provider == 'simulator' and settings.RIGHTS_VERIFICATION_BACKEND == 'simulator'
    assert not PrivacyPublicationHold.objects.filter(action__request=case).exists()
    _observe_wait_and_revoke(
        actor=actor, client=client,
        route=f'/en/moderation/rights/{case.pk}/publication-hold/',
        payload=hold_values(case), permission_name='safety.execute_rights_request',
        held_model=RightsRequest, held_pk=case.pk,
        queries=_domain_queries(case, person), minimal_state=lambda: _case_state(case.pk),
        case_label='rights_privacy_hold_execute_revocation', record_property=record_property,
    )


def test_erasure_inventory_denies_execute_permission_revoked_during_actual_case_wait(
    request, settings, monkeypatch, record_property
):
    _owned_serial(request, settings)
    case, actor, client, _, _, person = ready(request, settings, monkeypatch, 'erase')
    assert celery_app.conf.task_always_eager
    case.refresh_from_db()
    person.refresh_from_db()
    actor = _fresh_operator(actor)
    read(client, case)
    case.refresh_from_db()
    proof = case.proofs.latest('created_at')
    proof.refresh_from_db()
    assert case.kind == 'erase' and case.status == 'reviewing'
    assert case.assigned_to_id == actor.pk and proof.status == 'passed'
    assert proof.scope == case.kind and proof.case_version == case.version
    assert proof.provider == 'simulator' and settings.RIGHTS_VERIFICATION_BACKEND == 'simulator'
    assert not ErasureInventory.objects.filter(action__request=case).exists()
    _observe_wait_and_revoke(
        actor=actor, client=client,
        route=f'/en/moderation/rights/{case.pk}/erasure-inventory/',
        payload=inventory_values(case), permission_name='safety.execute_rights_request',
        held_model=RightsRequest, held_pk=case.pk,
        queries=_domain_queries(case, person), minimal_state=lambda: _case_state(case.pk),
        case_label='rights_erasure_inventory_execute_revocation', record_property=record_property,
    )


def test_verification_start_denies_review_permission_revoked_during_actual_case_wait(
    request, settings, record_property
):
    _owned_serial(request, settings)
    case, actor, client, person, _, _ = verification_prepared(request, settings)
    assert celery_app.conf.task_always_eager
    case.refresh_from_db()
    person.refresh_from_db()
    actor = _fresh_operator(actor)
    read(client, case)
    case.refresh_from_db()
    assert case.status == 'reviewing' and case.assigned_to_id == actor.pk
    assert case.person_id == person.pk and case.manager_version == person.manager_version
    assert settings.RIGHTS_VERIFICATION_BACKEND == 'simulator'
    assert not RightsProof.objects.filter(request=case).exists()
    path, values = verification_payload(client, case, 'start')
    assert values['version'] == case.version and values['operation'] == 'start'
    _observe_wait_and_revoke(
        actor=actor, client=client, route=path, payload=values,
        permission_name='safety.review_rights_request', held_model=RightsRequest, held_pk=case.pk,
        queries=_domain_queries(case, person), minimal_state=lambda: _case_state(case.pk),
        case_label='rights_verification_start_review_revocation', record_property=record_property,
    )


def test_verification_result_denies_verify_permission_revoked_during_actual_case_wait(
    request, settings, record_property
):
    _owned_serial(request, settings)
    case, initiator, original_client, person, verifier, client = verification_prepared(request, settings)
    assert celery_app.conf.task_always_eager
    case.refresh_from_db()
    initiator = _fresh_operator(initiator)
    read(original_client, case)
    path, values = verification_payload(original_client, case, 'start')
    assert original_client.post(path, values).status_code == 302
    case.refresh_from_db()
    person.refresh_from_db()
    actor = _fresh_operator(verifier)
    read(client, case)
    case.refresh_from_db()
    proof = case.proofs.latest('created_at')
    proof.refresh_from_db()
    assert proof.status == 'pending' and proof.case_version == case.version
    assert proof.provider == 'simulator' and settings.RIGHTS_VERIFICATION_BACKEND == 'simulator'
    assert proof.initiated_by_id == initiator.pk
    assert actor.pk not in (proof.initiated_by_id, case.assigned_to_id)
    assert actor.has_perm('safety.verify_rights_scope')
    assert not RightsProofEvent.objects.filter(proof__request=case).exists()
    path, values = verification_payload(client, case, 'result', outcome='passed')
    assert values['version'] == case.version and values['operation'] == 'result'
    _observe_wait_and_revoke(
        actor=actor, client=client, route=path, payload=values,
        permission_name='safety.verify_rights_scope', held_model=RightsRequest, held_pk=case.pk,
        queries=_domain_queries(case, person), minimal_state=lambda: _case_state(case.pk),
        case_label='rights_verification_result_verify_revocation', record_property=record_property,
    )
