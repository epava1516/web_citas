"""Opt-in stale-actor negatives and denied replays for N09D public entrypoints."""

import json
import os
import uuid
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import RequestFactory
from django.utils import timezone
from test_complaint_assignment import prepared as complaint_prepared
from test_complaint_authority_wait import _linked
from test_complaint_authority_wait import _queries as complaint_queries
from test_complaint_resolutions import REASON as COMPLAINT_REASON
from test_complaint_resolutions import RESPONSE
from test_operational_recovery_authority_wait import _snapshot
from test_privacy_release import REASON, confirm, fresh, plan, prepared
from test_privacy_release_authority_wait import _queries as release_queries
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety import complaints
from apps.safety.complaint_actions import act
from apps.safety.complaint_resolutions import resolve
from apps.safety.privacy_release import execute, propose

pytestmark = pytest.mark.django_db(transaction=True)

COMPLAINT_CHANGES = (
    'permission:safety.review_complaint', 'inactive', 'erased',
    'mfa_disabled', 'session_epoch', 'mfa_epoch',
)
RELEASE_CHANGES = (
    'permission:safety.review_rights_request',
    'permission:safety.execute_rights_request',
    'permission:safety.review_privacy_hold',
    'permission:safety.respond_rights_request',
    'inactive', 'erased', 'mfa_disabled', 'session_epoch', 'mfa_epoch',
)


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip('Explicit serial owned PostgreSQL N09D authority negatives only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_')
    _owned_database()


def _revoke(actor, change):
    # Fill the actual Django caches before an external ORM change; never patch guards.
    assert actor.is_active and actor.account_erased_at is None and actor.mfa_enabled
    actor.get_all_permissions()
    if change.startswith('permission:'):
        name = change.split(':', 1)[1]
        assert actor.has_perm(name)
        label, codename = name.split('.')
        permission = Permission.objects.get(content_type__app_label=label, codename=codename)
        assert actor.user_permissions.filter(pk=permission.pk).exists()
        User.objects.get(pk=actor.pk).user_permissions.remove(permission)
        assert actor.has_perm(name), 'Original actor must retain its legitimate old permission cache'
        assert not User.objects.get(pk=actor.pk).has_perm(name)
    else:
        field, value = {
            'inactive': ('is_active', False),
            'erased': ('account_erased_at', timezone.now()),
            'mfa_disabled': ('mfa_enabled', False),
            'session_epoch': ('session_version', actor.session_version + 1),
            'mfa_epoch': ('mfa_version', actor.mfa_version + 1),
        }[change]
        assert getattr(actor, field) != value
        assert User.objects.filter(pk=actor.pk).update(**{field: value}) == 1
        assert getattr(User.objects.get(pk=actor.pk), field) == value
        assert getattr(actor, field) != value


def _record(record_property, operation, change, before, after, *, result):
    record_property('complaint_release_current_authority', json.dumps({
        'operation': operation, 'change': change, 'result': result,
        'domain_before': before, 'domain_after': after,
        'domain_unchanged': before == after,
        'scope': 'Direct public view/service with legitimate stale actor; no middleware or wait claim',
    }, sort_keys=True, allow_nan=False))
    assert before == after


def _request(actor, method, path):
    factory = RequestFactory()
    request = (factory.post(path, {'purpose': 'Review synthetic current complaint independently'})
               if method == 'POST' else factory.get(path))
    request.user = actor
    request.session = {'account_version': actor.session_version, 'mfa_version': actor.mfa_version}
    request.LANGUAGE_CODE = 'en'
    return request


@pytest.mark.parametrize('change', COMPLAINT_CHANGES)
def test_inspection_rejects_current_authority_loss(request, settings, change, record_property):
    _owned_serial(request, settings)
    case, actor, _, _ = complaint_prepared(request)
    incoming = _request(actor, 'POST', f'/en/moderation/complaints/{case.pk}/')
    _revoke(actor, change)
    before = _snapshot(complaint_queries())
    response = complaints.inspect(incoming, case.pk)
    try:
        assert response.status_code == 403 and not response.streaming
    finally:
        response.close()
        _record(record_property, 'inspect', change, before, _snapshot(complaint_queries()),
                result=response.status_code)


@pytest.mark.parametrize('change', COMPLAINT_CHANGES + ('permission:listings.review_listing',))
def test_photo_rejects_current_authority_loss(request, settings, change, record_property):
    _owned_serial(request, settings)
    case, revision, actor, _ = _linked(request, images=False)
    actor = User.objects.get(pk=actor.pk)
    photo = revision.photos.filter(removed_at__isnull=True).first()
    assert photo is not None
    incoming = _request(actor, 'GET', f'/en/moderation/complaints/{case.pk}/photo/{photo.pk}/')
    _revoke(actor, change)
    before = _snapshot(complaint_queries())
    response = complaints.photo(incoming, case.pk, photo.pk)
    try:
        assert response.status_code == 403 and not response.streaming
    finally:
        response.close()
        _record(record_property, 'photo', change, before, _snapshot(complaint_queries()),
                result=response.status_code)


def _complaint_service(request, operation):
    if operation == 'claim':
        case, actor, _, _ = complaint_prepared(request)
        case.refresh_from_db()
        values = dict(key=uuid.uuid4(), version=case.version, operation='claim',
                      reason='Synthetic independent complaint assignment')
        return act, case, User.objects.get(pk=actor.pk), values
    case, revision, actor, _ = _linked(request, images=True)
    case.refresh_from_db()
    values = dict(key=uuid.uuid4(), version=case.version, source_version=revision.edit_version,
                  outcome='reconsidered', reason=COMPLAINT_REASON, response=RESPONSE,
                  redaction_confirmed=True)
    return resolve, case, User.objects.get(pk=actor.pk), values


@pytest.mark.parametrize('operation,change', [
    (operation, change)
    for operation in ('claim', 'resolve')
    for change in COMPLAINT_CHANGES + (
        ('permission:safety.resolve_complaint',) if operation == 'resolve' else ()
    )
])
def test_complaint_service_rejects_current_authority_loss(
    request, settings, operation, change, record_property,
):
    _owned_serial(request, settings)
    service, case, actor, values = _complaint_service(request, operation)
    _revoke(actor, change)
    before = _snapshot(complaint_queries())
    with pytest.raises(PermissionDenied):
        service(actor, case.pk, **values)
    _record(record_property, operation, change, before, _snapshot(complaint_queries()),
            result='PermissionDenied')


def _release_service(request, settings, monkeypatch, operation):
    case, actor, client, verifier, other, receipt_client, receipt, person, held = prepared(
        request, settings, monkeypatch,
    )
    assert case.kind == 'restriction'
    values = dict(key=uuid.uuid4(), version=case.version, reason=REASON)
    if operation == 'execute':
        proposal = plan(case, actor)
        confirm(receipt_client, receipt, proposal)
        fresh(case, actor, client, verifier, other)
        case.refresh_from_db()
        values.update(version=case.version, proposal_id=proposal.pk)
    return (execute if operation == 'execute' else propose), case, User.objects.get(pk=actor.pk), person, held, values


@pytest.mark.parametrize('operation', ['propose', 'execute'])
@pytest.mark.parametrize('change', RELEASE_CHANGES)
def test_release_service_rejects_current_authority_loss(
    request, settings, monkeypatch, operation, change, record_property,
):
    _owned_serial(request, settings)
    service, case, actor, person, _, values = _release_service(
        request, settings, monkeypatch, operation,
    )
    _revoke(actor, change)
    before = _snapshot(release_queries(case, person))
    with pytest.raises(PermissionDenied):
        service(actor, case.pk, **values)
    _record(record_property, operation, change, before, _snapshot(release_queries(case, person)),
            result='PermissionDenied')


@pytest.mark.parametrize('operation', ['claim', 'resolve', 'propose', 'execute'])
def test_replay_requires_current_authority(
    request, settings, monkeypatch, operation, record_property,
):
    _owned_serial(request, settings)
    if operation in {'claim', 'resolve'}:
        service, case, actor, values = _complaint_service(request, operation)
        queries = complaint_queries()
        permission = 'safety.review_complaint' if operation == 'claim' else 'safety.resolve_complaint'
    else:
        service, case, actor, person, _, values = _release_service(
            request, settings, monkeypatch, operation,
        )
        queries = release_queries(case, person)
        permission = 'safety.review_privacy_hold'
    before_effect = _snapshot(queries)
    result = service(actor, case.pk, **values)
    after_effect = _snapshot(queries)
    assert before_effect != after_effect and result.pk is not None
    _revoke(actor, 'permission:' + permission)
    before = _snapshot(queries)
    assert before == after_effect
    with pytest.raises(PermissionDenied):
        service(actor, case.pk, **values)
    _record(record_property, operation + '_replay', 'permission:' + permission,
            before, _snapshot(queries), result='PermissionDenied')
