"""Real PG batch-equivalence and late failures; pure reuse never skips fresh auditing."""

from copy import copy
from datetime import timedelta
from uuid import uuid4, uuid5

import pytest
import test_rights_portability_coverage_batch as fixtures
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_coverage_use import prepared_covered_selection

from apps.core.models import User
from apps.listings.models import Revision
from apps.safety import rights_portability_coverage_batch as batch
from apps.safety import rights_portability_images as images
from apps.safety import rights_portability_selection_review as selection_review
from apps.safety.models import RightsAction, RightsPortabilityCoverageRead, RightsPortabilitySelectionRead

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
    def uncached(context, user, case, proof, row, review, source, assessment, binding, operation):
        return operation(source, assessment, binding['selection'], field_evidence=binding.get('field_evidence'))

    monkeypatch.setattr(selection_review, 'project_in_batch', uncached)
    direct = batch.inspect_batch(*args)
    assert [(action.pk, page) for action, page in direct] == [(action.pk, page) for action, page in pages]
    assert len(projected) == 5 and len(audited) == 8
    assert RightsPortabilitySelectionRead.objects.count() == selected_before + 4


@pytest.mark.parametrize('mutation', ['session', 'mfa', 'proof', 'source', 'expiry', 'cipher', 'signature'])
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
    assert RightsAction.objects.count() == before_actions
    assert RightsPortabilitySelectionRead.objects.count() == before_selection
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
