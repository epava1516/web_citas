"""Audit-only return elision keeps every real child guard and physical inspection."""

from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_batch_projection import prepared

from apps.core.models import User
from apps.listings.models import Revision
from apps.safety import rights_exports
from apps.safety import rights_portability_batch_projection as projection
from apps.safety import rights_portability_coverage_batch as batch
from apps.safety import rights_portability_selection_review as review
from apps.safety.models import (
    RightsAction,
    RightsPortabilityCoverageRead,
    RightsPortabilitySelectionRead,
)
from apps.safety.rights_exports import reviewer_case
from apps.safety.rights_inspection_source import inspection_source
from apps.safety.rights_verification import authorized_proof

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Inspect each original child with unchanged fresh authority and bytes"


def test_four_children_validate_projection_once_without_copying_discarded_return(
    request, settings, monkeypatch
):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    project, physical = review.project_selected, rights_exports._read_image_blob
    calls, reads, copies = [], [], []
    native_copy = projection.deepcopy

    def selected(*args, **kwargs):
        calls.append(True)
        return project(*args, **kwargs)

    def actual_read(*args, **kwargs):
        reads.append(True)
        return physical(*args, **kwargs)

    def copied(value):
        copies.append(True)
        return native_copy(value)

    monkeypatch.setattr(review, "project_selected", selected)
    monkeypatch.setattr(rights_exports, "_read_image_blob", actual_read)
    monkeypatch.setattr(projection, "deepcopy", copied)
    before = RightsPortabilitySelectionRead.objects.count()
    key = uuid4()
    args = reviewer, case.pk, case.version, coverage.pk, key, REASON, "revisions"
    pages = batch.inspect_batch(*args)
    assert len(pages) == len(reads) == 4
    assert len(calls) == 1 and not copies
    assert RightsPortabilitySelectionRead.objects.count() == before + 4
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == 4
    # Replaying the same real audits with pure reuse disabled preserves all output.
    native = projection.project

    def no_reuse(*args, **kwargs):
        context = projection._current.set(None)
        try:
            return native(*args, **kwargs)
        finally:
            projection._current.reset(context)

    monkeypatch.setattr(review, "project_in_batch", no_reuse)
    repeated = batch.inspect_batch(*args)
    assert [(action.pk, page) for action, page in repeated] == [
        (action.pk, page) for action, page in pages
    ]
    assert len(calls) == 5 and len(reads) == 8
    assert projection._current.get() is None


@pytest.mark.parametrize("change", ["session", "source"])
def test_fresh_child_two_drift_rolls_back_all_audits_and_clears_context(
    request, settings, monkeypatch, change
):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    native = batch.inspect_page
    actions, selections = (
        RightsAction.objects.count(),
        RightsPortabilitySelectionRead.objects.count(),
    )
    children = []

    def changed(*args, **kwargs):
        result = native(*args, **kwargs)
        children.append(True)
        if len(children) == 2:
            if change == "session":
                User.objects.filter(pk=reviewer.pk).update(
                    session_version=reviewer.session_version + 1
                )
            else:
                Revision.objects.filter(listing__person=case.person).update(
                    title="Late actual source drift"
                )
        return result

    monkeypatch.setattr(batch, "inspect_page", changed)
    with pytest.raises((PermissionDenied, ValidationError)):
        batch.inspect_batch(
            reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions"
        )
    # Authority is checked per child; the source snapshot is checked at the
    # enclosing operation's exit. Both changes must reject and roll back all.
    assert len(children) == (2 if change == "session" else 4)
    assert RightsAction.objects.count() == actions
    assert RightsPortabilitySelectionRead.objects.count() == selections
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
    assert projection._current.get() is None


def test_public_projection_returns_independent_values_after_audit_only_marker(
    request, settings, monkeypatch
):
    case, _, coverage, user = prepared(request, settings, monkeypatch)
    selection = coverage.selection_review.selection
    with transaction.atomic():
        case, person, listing = reviewer_case(user, case.pk)
        proof = authorized_proof(case, person, case.kind)
        with (
            inspection_source(person, listing, case) as source,
            projection.batch_projection(source, user, case, proof),
        ):
            _, hidden = review.record(
                user,
                case.pk,
                case.version,
                selection.pk,
                uuid4(),
                REASON,
                _inspection_source=source,
                _audit_only=True,
            )
            assert hidden is None
            _, first = review.record(
                user,
                case.pk,
                case.version,
                selection.pk,
                uuid4(),
                REASON,
                _inspection_source=source,
            )
            expected = projection.deepcopy(first)
            first.clear()
            _, second = review.record(
                user,
                case.pk,
                case.version,
                selection.pk,
                uuid4(),
                REASON,
                _inspection_source=source,
            )
            assert second == expected
    assert projection._current.get() is None


@pytest.mark.parametrize("invalid", [None, 1, "true"])
def test_audit_only_requires_exact_boolean_before_any_write(
    request, settings, monkeypatch, invalid
):
    case, _, coverage, user = prepared(request, settings, monkeypatch)
    before = RightsAction.objects.count()
    with pytest.raises(ValidationError, match="audit-only"):
        review.record(
            user,
            case.pk,
            case.version,
            coverage.selection_review.selection_id,
            uuid4(),
            REASON,
            _audit_only=invalid,
        )
    assert RightsAction.objects.count() == before


def test_audit_only_outside_batch_still_runs_full_pure_validation(request, settings, monkeypatch):
    case, _, coverage, user = prepared(request, settings, monkeypatch)
    native, calls = review.project_selected, []

    def checked(*args, **kwargs):
        calls.append(True)
        return native(*args, **kwargs)

    monkeypatch.setattr(review, "project_selected", checked)
    _, result = review.record(
        user,
        case.pk,
        case.version,
        coverage.selection_review.selection_id,
        uuid4(),
        REASON,
        _audit_only=True,
    )
    assert result is None and len(calls) == 1
    assert projection._current.get() is None


def projection_inputs(source, user, case, proof, row, review_row, operation):
    # Stub operation below tests only the pure context cache protocol. The
    # preceding domain tests independently exercise real signatures and guards.
    return (
        source,
        user,
        case,
        proof,
        row,
        review_row,
        source.source,
        {},
        {"selection": {}},
        operation,
    )


def test_audit_sentinel_never_hides_changed_ciphertext_key(request, settings, monkeypatch):
    from copy import copy

    case, _, coverage, user = prepared(request, settings, monkeypatch)
    selected = copy(coverage.selection_review.selection)
    calls = []
    original_ciphertext = selected.encrypted_selection

    def operation(*args, **kwargs):
        calls.append(selected.encrypted_selection)
        if selected.encrypted_selection != original_ciphertext:
            raise ValidationError("Fresh pure input changed")
        return {"fresh": True}

    with transaction.atomic():
        case, person, listing = reviewer_case(user, case.pk)
        proof = authorized_proof(case, person, case.kind)
        with (
            inspection_source(person, listing, case) as source,
            projection.batch_projection(source, user, case, proof),
        ):
            args = projection_inputs(
                source, user, case, proof, selected, selected.assessment_review, operation
            )
            assert projection.project(*args, _audit_only=True) is None
            assert projection.project(*args, _audit_only=True) is None
            assert len(calls) == 1
            # Change only this isolated in-memory row: no fabricated valid
            # ciphertext or approval is written to the real database.
            selected.encrypted_selection += "changed-key"
            with pytest.raises(ValidationError, match="Fresh pure input changed"):
                projection.project(*args, _audit_only=True)
            assert len(calls) == 2
    assert projection._current.get() is None


def test_failed_audit_operation_stores_no_marker_and_next_call_executes(
    request, settings, monkeypatch
):
    case, _, coverage, user = prepared(request, settings, monkeypatch)
    selected, calls = coverage.selection_review.selection, []

    def operation(*args, **kwargs):
        calls.append(True)
        if len(calls) == 1:
            raise ValidationError("Initial pure computation failed")
        return {"fresh": True}

    with transaction.atomic():
        case, person, listing = reviewer_case(user, case.pk)
        proof = authorized_proof(case, person, case.kind)
        with (
            inspection_source(person, listing, case) as source,
            projection.batch_projection(source, user, case, proof),
        ):
            args = projection_inputs(
                source, user, case, proof, selected, selected.assessment_review, operation
            )
            with pytest.raises(ValidationError, match="Initial pure computation failed"):
                projection.project(*args, _audit_only=True)
            assert not projection._current.get()["entries"]
            assert projection.project(*args, _audit_only=True) is None
            assert len(calls) == 2
            assert len(projection._current.get()["entries"]) == 1
    assert projection._current.get() is None


def test_each_child_latest_approval_queries_fetch_only_primary_keys(request, settings, monkeypatch):
    case, _, coverage, user = prepared(request, settings, monkeypatch, binary=True)
    statements = {"safety_rightsportabilityassessment": [], "safety_rightsportabilityselection": []}

    def captured(execute, statement, params, many, context):
        if isinstance(statement, str) and "ORDER BY" in statement and "LIMIT 1" in statement:
            for table in statements:
                if 'FROM "' + table + '"' in statement:
                    statements[table].append(statement)
        return execute(statement, params, many, context)

    with connection.execute_wrapper(captured):
        pages = batch.inspect_batch(
            user, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions"
        )
    assert len(pages) == 4
    # Other guards legitimately load full rows (including image evidence).
    # The optimized latest checks must still issue fresh id-only SQL for each
    # child in both families; removing .only("pk") makes this count fail.
    for table, queries in statements.items():
        id_only = [
            statement for statement in queries
            if statement.split(" FROM ", 1)[0] == 'SELECT "' + table + '"."id"'
        ]
        assert len(id_only) >= 4
