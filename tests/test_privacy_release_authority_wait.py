"""Two explicit native restriction-release POSTs must reject authority revoked in PG waits."""

import os
import uuid
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from django.utils import timezone
from test_operational_recovery_authority_wait import _observe_wait_and_revoke
from test_privacy_release import REASON, confirm, fresh, plan, prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.safety.models import (
    PrivacyHoldReleaseProposal,
    PrivacyPublicationHold,
    RightsAccess,
    RightsAction,
    RightsNotice,
    RightsProof,
    RightsProofEvent,
    RightsRequest,
    RightsResponse,
    RightsResponseAcknowledgement,
)
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip('Explicit serial owned PostgreSQL restriction-release wait diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_')
    _owned_database()


def _actor_and_proof(case, actor, person, held, settings):
    case.refresh_from_db()
    person.refresh_from_db()
    held.refresh_from_db()
    actor = User.objects.get(pk=actor.pk)
    assert actor.is_active and actor.account_erased_at is None and actor.mfa_enabled
    assert all(actor.has_perm('safety.' + permission) for permission in (
        'review_rights_request', 'execute_rights_request',
        'review_privacy_hold', 'respond_rights_request',
    ))
    assert case.kind == 'restriction', 'Native prepared(kind) fixes restriction; no other kind claimed'
    assert case.status == 'reviewing' and case.assigned_to_id == actor.pk
    assert case.scope_status == 'simulated_passed'
    assert case.person_id == person.pk and case.manager_version == person.manager_version
    assert held.active and held.person_id == person.pk and held.action.request_id == case.pk
    assert held.action.actor_id != actor.pk
    assert held.subject_snapshot == str(person.subject_id or '')
    assert held.proof.scope == case.kind
    proof = case.proofs.latest('created_at')
    proof.refresh_from_db()
    assert proof.status == 'passed' and proof.provider == 'simulator'
    assert settings.RIGHTS_VERIFICATION_BACKEND == 'simulator'
    assert proof.scope == 'restriction' and proof.case_version == case.version
    assert proof.person_id == person.pk and proof.manager_version == person.manager_version
    assert proof.person_rights_version == person.rights_version
    assert proof.subject_id_snapshot == str(person.subject_id or '')
    assert proof.channel_digest == case.receipt_digest
    now = timezone.now()
    assert proof.expires_at > now and case.receipt_expires_at > now
    return actor, proof


def _queries(case, person):
    return {
        'case': RightsRequest.objects.filter(pk=case.pk),
        'actions': RightsAction.objects.filter(request=case),
        'access': RightsAccess.objects.filter(request=case),
        'proof': RightsProof.objects.filter(request=case),
        'proof_event': RightsProofEvent.objects.filter(proof__request=case),
        'person': Person.objects.filter(pk=person.pk),
        'listing': Listing.objects.filter(person=person),
        'revision': Revision.objects.filter(listing__person=person),
        'hold': PrivacyPublicationHold.objects.filter(action__request=case),
        'proposal': PrivacyHoldReleaseProposal.objects.filter(action__request=case),
        'response': RightsResponse.objects.filter(request=case),
        'ack': RightsResponseAcknowledgement.objects.filter(response__request=case),
        'notice': RightsNotice.objects.filter(response__request=case),
    }


def _minimal_state(case_id, held_id):
    result = RightsRequest.objects.filter(pk=case_id).values(
        'version', 'response_version', 'status', 'scope_status',
    ).get()
    result['hold_active'] = PrivacyPublicationHold.objects.get(pk=held_id).active
    result['release_proposals'] = PrivacyHoldReleaseProposal.objects.filter(
        action__request_id=case_id,
    ).count()
    result['executed_proposals'] = PrivacyHoldReleaseProposal.objects.filter(
        action__request_id=case_id, released_at__isnull=False,
    ).count()
    return result


def test_privacy_release_propose_denies_permission_revoked_during_actual_hold_wait(
    request, settings, monkeypatch, record_property
):
    _owned_serial(request, settings)
    case, actor, client, _, _, _, _, person, held = prepared(request, settings, monkeypatch)
    assert celery_app.conf.task_always_eager
    actor, _ = _actor_and_proof(case, actor, person, held, settings)
    assert not PrivacyHoldReleaseProposal.objects.filter(action__request=case).exists()
    _observe_wait_and_revoke(
        actor=actor, client=client,
        route=f'/en/moderation/rights/{case.pk}/publication-hold/release/',
        payload={'key': uuid.uuid4(), 'version': case.version,
                 'operation': 'propose', 'reason': REASON},
        permission_name='safety.review_privacy_hold',
        held_model=PrivacyPublicationHold, held_pk=held.pk,
        queries=_queries(case, person), minimal_state=lambda: _minimal_state(case.pk, held.pk),
        case_label='restriction_release_propose_review_revocation', record_property=record_property,
    )


def test_privacy_release_execute_denies_permission_revoked_during_actual_proposal_wait(
    request, settings, monkeypatch, record_property
):
    _owned_serial(request, settings)
    case, actor, client, verifier, verifier_client, receipt_client, receipt, person, held = prepared(
        request, settings, monkeypatch,
    )
    assert celery_app.conf.task_always_eager
    actor, _ = _actor_and_proof(case, actor, person, held, settings)
    proposal = plan(case, actor)
    proposal.refresh_from_db()
    confirm(receipt_client, receipt, proposal)
    fresh_proof = fresh(case, actor, client, verifier, verifier_client)
    fresh_proof.refresh_from_db()
    case.refresh_from_db()
    held.refresh_from_db()
    proposal.refresh_from_db()
    actor, proof = _actor_and_proof(case, actor, person, held, settings)
    acknowledgement = RightsResponseAcknowledgement.objects.get(response_id=proposal.response_id)
    assert acknowledgement.channel_digest == case.receipt_digest
    assert proof.pk == fresh_proof.pk and proof.pk != proposal.proof_id
    assert proof.created_at > acknowledgement.created_at and proof.created_at > proposal.created_at
    assert proposal.response.response_version == case.response_version
    assert proposal.action.actor_id == actor.pk and proposal.hold_id == held.pk
    assert proposal.released_at is None and proposal.released_action_id is None
    assert proposal.released_proof_id is None
    assert held.release_proposals.order_by('-pk').first().pk == proposal.pk
    _observe_wait_and_revoke(
        actor=actor, client=client,
        route=f'/en/moderation/rights/{case.pk}/publication-hold/release/',
        payload={'key': uuid.uuid4(), 'version': case.version, 'proposal_id': proposal.pk,
                 'operation': 'execute', 'reason': REASON},
        permission_name='safety.review_privacy_hold',
        # Execute first locks a proposal query joining Hold; observe this first blocked table.
        held_model=PrivacyHoldReleaseProposal, held_pk=proposal.pk,
        queries=_queries(case, person), minimal_state=lambda: _minimal_state(case.pk, held.pk),
        case_label='restriction_release_execute_review_revocation', record_property=record_property,
    )
