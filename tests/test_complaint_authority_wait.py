"""Four opt-in native HTTP authority diagnostics with observed PostgreSQL waits."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from test_complaint_assignment import action, prepared
from test_complaint_resolutions import inspection, listing_case, resolution
from test_operational_recovery_authority_wait import _observe_wait_and_revoke
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Listing, ModerationDecision, Revision
from apps.mediafiles.models import Blob, Photo
from apps.safety.models import (
    Complaint,
    ComplaintAccess,
    ComplaintAction,
    ComplaintNotice,
    ComplaintResolution,
)

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(
        Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip('Explicit serial owned PostgreSQL complaint wait diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_')
    _owned_database()


def _queries():
    # Full concrete scalar rows are hashed by the reused observer, never emitted.
    return {
        model.__name__: model.objects.all()
        for model in (
            Complaint, ComplaintAccess, ComplaintAction, ComplaintResolution,
            ComplaintNotice, Person, Listing, Revision, ModerationDecision, Photo, Blob,
        )
    }


def _state(case):
    return Complaint.objects.filter(pk=case.pk).values(
        'status', 'version', 'assigned_to_id', 'listing_decision_id', 'decision_id',
    ).get()


def _run(case, actor, client, route, payload, permission, label, record_property):
    case.refresh_from_db()
    assert actor.has_perm(permission)
    assert actor.mfa_enabled and actor.is_active
    _observe_wait_and_revoke(
        actor=actor, client=client, route=route, payload=payload,
        permission_name=permission, held_model=Complaint, held_pk=case.pk,
        queries=_queries(), minimal_state=lambda: _state(case),
        case_label=label, record_property=record_property,
    )


class _PhotoGet:
    """Only adapt the observer's callback interface; transport remains Client.get."""

    def __init__(self, client, probe):
        self.client = client
        self.probe = probe

    @property
    def session(self):
        return self.client.session

    def post(self, route, payload):
        assert payload == {}
        response = self.client.get(route)
        digest = hashlib.sha256()
        image_bytes = 0
        self.probe.update(
            method=response.wsgi_request.method,
            status=response.status_code,
            streaming=response.streaming,
        )
        try:
            assert response.wsgi_request.method == 'GET'
            if response.streaming:
                for chunk in response.streaming_content:
                    image_bytes += len(chunk)
                    assert image_bytes <= 1024 * 1024, 'Synthetic image exceeds1MiB bound'
                    digest.update(chunk)
            return response
        finally:
            response.close()
            self.probe.update(
                image_bytes=image_bytes,
                image_sha256=digest.hexdigest(),
                closed=response.closed,
            )


def _linked(request, images):
    case, person, decision, actor, client, _ = listing_case(request, rejected=True)
    case.refresh_from_db()
    person.refresh_from_db()
    decision.refresh_from_db()
    revision = Revision.objects.get(pk=decision.revision_id)
    listing = Listing.objects.get(pk=revision.listing_id)
    assert revision.status == 'rejected' and listing.status == 'rejected'
    assert case.listing_decision_id == decision.pk and decision.reviewer_id != actor.pk
    # Native helper consumes and closes all successful image streams when images=True.
    assert inspection(client, case, images=images).status_code == 200
    case.refresh_from_db()
    decision.refresh_from_db()
    revision.refresh_from_db()
    listing.refresh_from_db()
    person.refresh_from_db()
    return case, revision, actor, client


def test_complaint_inspection_denies_permission_revoked_during_actual_wait(
    request, settings, record_property,
):
    _owned_serial(request, settings)
    case, actor, client, _ = prepared(request)
    case.refresh_from_db()
    assert case.status == 'received' and case.assigned_to_id is None
    _run(
        case, actor, client, f'/en/moderation/complaints/{case.pk}/',
        {'purpose': 'Read current synthetic complaint for independent review'},
        'safety.review_complaint', 'complaint_inspection', record_property,
    )


def test_complaint_photo_denies_permission_revoked_during_actual_get_wait(
    request, settings, record_property,
):
    _owned_serial(request, settings)
    probe = {'method': None, 'status': None, 'streaming': None,
             'image_bytes': 0, 'image_sha256': None, 'closed': None}
    try:
        case, revision, actor, client = _linked(request, images=False)
        assert not ComplaintAccess.objects.filter(complaint=case, kind='image').exists()
        photo = revision.photos.filter(removed_at__isnull=True).order_by('pk').first()
        assert photo is not None
        photo.refresh_from_db()
        blob = Blob.objects.get(pk=photo.blob_id)
        assert blob.status == 'ready' and blob.derivative
        _run(
            case, actor, _PhotoGet(client, probe),
            f'/en/moderation/complaints/{case.pk}/photo/{photo.pk}/', {},
            'listings.review_listing', 'complaint_photo_get', record_property,
        )
        assert probe['method'] == 'GET' and probe['status'] == 403
        assert probe['streaming'] is False and probe['image_bytes'] == 0
        assert probe['closed'] is True
    finally:
        record_property('complaint_photo_stream_probe', json.dumps(
            probe, allow_nan=False, sort_keys=True,
        ))


def test_complaint_claim_denies_permission_revoked_during_actual_wait(
    request, settings, record_property,
):
    _owned_serial(request, settings)
    case, actor, client, _ = prepared(request)
    case.refresh_from_db()
    assert case.status == 'received' and case.assigned_to_id is None
    route, payload = action(client, case, 'claim')
    _run(case, actor, client, route, payload, 'safety.review_complaint',
         'complaint_claim', record_property)


def test_complaint_listing_resolution_denies_permission_revoked_during_actual_wait(
    request, settings, record_property,
):
    _owned_serial(request, settings)
    case, _, actor, client = _linked(request, images=True)
    assert ComplaintAccess.objects.filter(complaint=case, kind='image').exists()
    assert case.status == 'reviewing' and case.assigned_to_id == actor.pk
    route, payload = resolution(client, case)
    _run(case, actor, client, route, payload, 'safety.resolve_complaint',
         'complaint_listing_resolution', record_property)
