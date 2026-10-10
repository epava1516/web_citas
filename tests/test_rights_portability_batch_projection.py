"""Real PG batch-equivalence and late failures; pure reuse never skips fresh auditing."""

from copy import copy
from datetime import timedelta
from pathlib import Path
from uuid import uuid4, uuid5

import pytest
import test_rights_portability_coverage_batch as fixtures
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_coverage_use import prepared_covered_selection

from apps.core.models import User
from apps.listings.models import Revision
from apps.mediafiles.models import Photo
from apps.safety import rights_portability_batch_projection as projection
from apps.safety import rights_portability_coverage_batch as batch
from apps.safety import rights_portability_images as images
from apps.safety import rights_portability_selection_review as selection_review
from apps.safety.models import (
    RightsAction,
    RightsPortabilityCoverageRead,
    RightsPortabilitySelectionRead,
)

pytestmark = pytest.mark.django_db(transaction=True)
REASON = fixtures.REASON


def prepared(request, settings, monkeypatch, *, binary=False):
    original = fixtures.fixtures.ready

    def extra_revision(*args, **kwargs):
        result = original(*args, **kwargs)
        person = result[-1]
        revision = copy(Revision.objects.filter(listing__person=person).first())
        revision.pk = uuid4()
        revision._state.adding = True
        revision.save(force_insert=True)
        return result

    monkeypatch.setattr(fixtures.fixtures, 'ready', extra_revision)
    if binary:
        monkeypatch.setattr(fixtures, 'prepared_selection',
                            lambda request, settings, patch, account_only:
                            prepared_covered_selection(request, settings, patch, account_only, binary=True))
    return fixtures.prepared(request, settings, monkeypatch)


def test_projection_reuse_keeps_four_real_audits_and_equivalent_outputs(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    original_project, original_images = selection_review.project_selected, images.audited_images
    projected, audited = [], []

    def project(*args, **kwargs):
        projected.append(True)
        return original_project(*args, **kwargs)

    def audit(*args, **kwargs):
        audited.append(True)
        return original_images(*args, **kwargs)

    monkeypatch.setattr(selection_review, 'project_selected', project)
    monkeypatch.setattr(images, 'audited_images', audit)
    key = uuid4()
    args = reviewer, case.pk, case.version, coverage.pk, key, REASON, 'revisions'
    selected_before = RightsPortabilitySelectionRead.objects.count()
    pages = batch.inspect_batch(*args)
    assert len(pages) == len(audited) == 4
    assert len(projected) == 1
    assert RightsPortabilitySelectionRead.objects.count() == selected_before + 4
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == 4
    for index, (action, page) in enumerate(pages):
        page_key = uuid5(key, f'coverage-batch-page:{index}')
        assert action.key == page_key
        selection_key = uuid5(page_key,
                              f"coverage-inspection:revisions:{page['row_index']}:{page['field_page']}:False")
        assert RightsPortabilitySelectionRead.objects.filter(action__key=selection_key).exists()
    # Same audited UUIDs and page digests when pure reuse is bypassed internally for equivalence.
    def uncached(context, user, case, proof, row, review, source, assessment, binding, operation,
                 *, _audit_only=False):
        value = operation(source, assessment, binding['selection'], field_evidence=binding.get('field_evidence'))
        return None if _audit_only else value

    monkeypatch.setattr(selection_review, 'project_in_batch', uncached)
    direct = batch.inspect_batch(*args)
    assert [(action.pk, page) for action, page in direct] == [(action.pk, page) for action, page in pages]
    assert len(projected) == 5 and len(audited) == 8
    assert RightsPortabilitySelectionRead.objects.count() == selected_before + 4


@pytest.mark.parametrize('mutation', ['session', 'mfa', 'permission', 'scope', 'active', 'proof', 'source', 'expiry', 'cipher', 'signature'])
def test_late_guard_failure_rolls_back_every_child_with_reused_projection(
    request, settings, monkeypatch, mutation
):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    original = batch.inspect_page
    selected = coverage.selection_review.selection
    before_selection = RightsPortabilitySelectionRead.objects.count()
    before_actions = RightsAction.objects.count()
    calls = []

    def later_mutation(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(True)
        if len(calls) == 2:
            if mutation in {'session', 'mfa'}:
                field = 'session_version' if mutation == 'session' else 'mfa_version'
                User.objects.filter(pk=reviewer.pk).update(**{field: getattr(reviewer, field) + 1})
            elif mutation == 'permission':
                reviewer.user_permissions.remove(*reviewer.user_permissions.filter(codename='review_portability'))
            elif mutation == 'scope':
                type(case).objects.filter(pk=case.pk).update(reported_subject_id=reviewer.pk)
            elif mutation == 'active':
                User.objects.filter(pk=reviewer.pk).update(is_active=False)
            elif mutation == 'proof':
                type(selected.proof).objects.filter(pk=selected.proof_id).update(status='failed')
            elif mutation == 'source':
                Revision.objects.filter(listing__person=case.person).update(title='Late synthetic source drift')
            elif mutation == 'expiry':
                type(selected).objects.filter(pk=selected.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
            elif mutation == 'cipher':
                type(selected).objects.filter(pk=selected.pk).update(encrypted_selection='invalid-ciphertext')
            else:
                RightsAction.objects.filter(pk=selected.action_id).update(payload_digest='0' * 64)
        return result

    monkeypatch.setattr(batch, 'inspect_page', later_mutation)
    with pytest.raises((PermissionDenied, ValidationError)):
        batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions')
    assert len(calls) >= 2
    assert projection._current.get() is None
    assert RightsAction.objects.count() == before_actions
    assert RightsPortabilitySelectionRead.objects.count() == before_selection
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()


def test_actual_binary_bytes_changed_after_second_child_are_not_cached(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    from apps.safety.crypto import unseal

    selected = coverage.selection_review.selection
    photo_id = unseal(selected.encrypted_selection)['images'][0]['photo']
    photo = Photo.objects.select_related('blob').get(pk=photo_id)
    path = Path(photo.blob.derivative.path)
    content = path.read_bytes()
    before_actions = RightsAction.objects.count()
    before_selection = RightsPortabilitySelectionRead.objects.count()
    original = batch.inspect_page
    calls = []

    def physical_change(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(True)
        if len(calls) == 2:
            # Preserve valid WebP framing; invalidate its actual SHA without changing PG metadata.
            path.write_bytes(content[:-1] + bytes([content[-1] ^ 1]))
        return result

    monkeypatch.setattr(batch, 'inspect_page', physical_change)
    try:
        with pytest.raises(ValidationError, match='exact portable image content'):
            batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions')
        assert len(calls) == 2
        assert RightsAction.objects.count() == before_actions
        assert RightsPortabilitySelectionRead.objects.count() == before_selection
        assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
        assert projection._current.get() is None
    finally:
        path.write_bytes(content)


@pytest.mark.parametrize('mutation', ['proof', 'proof_expiry'])
def test_final_proof_guard_rolls_back_after_last_child(request, settings, monkeypatch, mutation):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    selected = coverage.selection_review.selection
    before_actions = RightsAction.objects.count()
    before_selection = RightsPortabilitySelectionRead.objects.count()
    original = batch.inspect_page
    calls = []

    def after_last(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(True)
        if len(calls) == 4:
            values = ({'status': 'failed'} if mutation == 'proof'
                      else {'expires_at': timezone.now() - timedelta(seconds=1)})
            type(selected.proof).objects.filter(pk=selected.proof_id).update(**values)
        return result

    monkeypatch.setattr(batch, 'inspect_page', after_last)
    with pytest.raises((PermissionDenied, ValidationError)):
        batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions')
    assert len(calls) == 4
    assert RightsAction.objects.count() == before_actions
    assert RightsPortabilitySelectionRead.objects.count() == before_selection
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
    assert projection._current.get() is None


def test_projection_results_are_independent_and_context_does_not_survive_request(
    request, settings, monkeypatch
):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    original = selection_review.project_in_batch
    observed = []
    expected = []

    def collect(*args, **kwargs):
        # Exercise the public return contract even though this caller normally
        # discards it. Audit-only elision is covered by its own real-batch tests.
        kwargs["_audit_only"] = False
        value = original(*args, **kwargs)
        observed.append(value)
        if not expected:
            from copy import deepcopy
            expected.append(deepcopy(value))
            value['datasets']['synthetic_mutation'] = [{'fields': {'private': 'only first result'}}]
        else:
            assert value == expected[0]
        return value

    monkeypatch.setattr(selection_review, 'project_in_batch', collect)
    pages = batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions')
    assert len(pages) == len(observed) == 4
    assert len({id(value) for value in observed}) == 4
    assert projection._current.get() is None
    observed.clear()
    expected.clear()
    # A separate request reconstructs its own pure projection and retains independent values.
    pages = batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions')
    assert len(pages) == len(observed) == 4
    assert projection._current.get() is None
