"""Fresh PostgreSQL image-evidence lookups; signatures remain checked per image."""

from copy import copy
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_coverage_use import prepared_covered_selection

from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsPortabilityImageRead
from apps.safety.rights_portability_image_read import required_reads, signature

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch):
    case, _, selection, review, *_ = prepared_covered_selection(
        request, settings, monkeypatch, False, binary=True
    )
    decisions = unseal(selection.encrypted_selection)["images"]
    evidence = RightsPortabilityImageRead.objects.select_related(
        "action", "selection_read__action", "photo"
    ).get(pk=review.image_reads[0])
    return case, selection, review.action.actor_id, decisions, evidence


def duplicate(evidence, case, *, another_photo=False):
    row = copy(evidence)
    row.pk = None
    if another_photo:
        photo = copy(evidence.photo)
        photo.pk = uuid4()
        # This synthetic fixture tests evidence lookup only, not binary eligibility.
        photo.removed_at = timezone.now()
        photo.save(force_insert=True)
        row.photo = photo
    reason = unseal(evidence.action.encrypted_reason)["reason"]
    action = copy(evidence.action)
    action.pk = None
    action.key = uuid4()
    action.payload_digest = signature(row, case, reason)
    action.save(force_insert=True)
    row.action = action
    row.save(force_insert=True)
    return row


@pytest.mark.parametrize("count", [1, 16])
def test_bulk_lookup_one_query_preserves_decision_order_and_all_signatures(
    request, settings, monkeypatch, count
):
    case, selection, actor, decisions, first = prepared(request, settings, monkeypatch)
    rows = [first] + [duplicate(first, case, another_photo=True) for _ in range(count - 1)]
    chosen_decisions = [dict(decisions[0], photo=str(row.photo_id)) for row in reversed(rows)]
    statements = []

    def observe(execute, statement, params, many, context):
        if isinstance(statement, str) and 'FROM "safety_rightsportabilityimageread"' in statement:
            statements.append(statement)
        return execute(statement, params, many, context)

    with transaction.atomic(), connection.execute_wrapper(observe):
        assert required_reads(selection, case, first.proof, chosen_decisions, actor) == [
            row.pk for row in reversed(rows)
        ]
    assert len(statements) == 1
    assert "DISTINCT ON" in statements[0]
    # A bad signature on the final item must still reject after validating earlier items.
    RightsAction.objects.filter(pk=rows[0].action_id).update(payload_digest="0" * 64)
    with transaction.atomic(), pytest.raises(ValidationError, match="Binary image evidence changed"):
        required_reads(selection, case, first.proof, chosen_decisions, actor)


def test_bulk_newest_corrupt_read_never_falls_back_but_exact_ids_keep_original(
    request, settings, monkeypatch
):
    case, selection, actor, decisions, first = prepared(request, settings, monkeypatch)
    newest = duplicate(first, case)
    with transaction.atomic():
        assert required_reads(selection, case, first.proof, decisions, actor) == [newest.pk]
    RightsAction.objects.filter(pk=newest.action_id).update(payload_digest="0" * 64)
    with transaction.atomic(), pytest.raises(ValidationError, match="Binary image evidence changed"):
        required_reads(selection, case, first.proof, decisions, actor)
    with transaction.atomic():
        assert required_reads(selection, case, first.proof, decisions, actor, ids=[first.pk]) == [
            first.pk
        ]


@pytest.mark.parametrize(
    "change", ["actor", "proof", "version", "selection_digest", "digest", "photo", "ids", "duplicates"]
)
def test_bulk_exact_scope_and_ids_are_not_widened(request, settings, monkeypatch, change):
    case, selection, actor, decisions, first = prepared(request, settings, monkeypatch)
    ids = None
    proof = first.proof
    if change == "actor":
        actor = selection.actor_id
    elif change == "proof":
        proof = copy(proof)
        proof.pk = uuid4()
    elif change == "version":
        RightsAction.objects.filter(pk=first.action_id).update(expected_version=case.version + 1)
    elif change == "digest":
        decisions = [dict(decisions[0], content_digest="0" * 64)]
    elif change == "selection_digest":
        RightsPortabilityImageRead.objects.filter(pk=first.pk).update(selection_digest="0" * 64)
    elif change == "photo":
        decisions = [dict(decisions[0], photo=str(uuid4()))]
    elif change == "ids":
        ids = [first.pk + 100000]
    else:
        decisions = decisions * 2
        ids = [first.pk, first.pk]
    with transaction.atomic(), pytest.raises(ValidationError):
        required_reads(selection, case, proof, decisions, actor, ids=ids)


def test_bulk_second_call_observes_changed_read_in_same_transaction(request, settings, monkeypatch):
    case, selection, actor, decisions, first = prepared(request, settings, monkeypatch)
    with transaction.atomic():
        assert required_reads(selection, case, first.proof, decisions, actor) == [first.pk]
        RightsPortabilityImageRead.objects.filter(pk=first.pk).update(source_digest="0" * 64)
        with pytest.raises(ValidationError, match="Binary image evidence changed"):
            required_reads(selection, case, first.proof, decisions, actor)
