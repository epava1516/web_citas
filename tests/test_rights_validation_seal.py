"""Validation seals never accept what the full validation rejects (PostgreSQL)."""

from copy import copy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone
from test_portability_source_reads import WATCHED, counted
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_object_store import object_store  # noqa: F401
from test_rights_portability_covered_export_races import approved_coverage
from test_rights_portability_response_draft import REASON

from apps.core.models import User
from apps.safety import rights_portability_export, rights_validation_seal
from apps.safety.models import (
    RightsExportValidationSeal,
    RightsPortabilityCoverageRead,
    RightsPortabilitySelection,
)
from apps.safety.rights_exports import reviewer_case
from apps.safety.rights_portability_export import generate

pytestmark = pytest.mark.django_db(transaction=True)
WATCHED["full_export_validation"] = WATCHED["portability_export_binding"]


def generated(request, settings, monkeypatch):
    case, author, selection, selected, _, decision, reviewer, _, _, receipt = approved_coverage(
        request, settings, monkeypatch, False, binary=True
    )
    respond = Permission.objects.get(codename="respond_rights_request")
    author.user_permissions.add(respond)
    author = User.objects.get(pk=author.pk)
    export = generate(
        author,
        case.pk,
        case.version,
        selection.pk,
        selected.pk,
        uuid4(),
        REASON,
        coverage_review_id=decision.pk,
    )
    case.refresh_from_db()
    return case, author, export, receipt


def check(case, author, export):
    """Validate as the delivery path does, returning whether the sealed path was used."""
    counts = {}
    with transaction.atomic():
        locked, person, _ = reviewer_case(author, case.pk)
        export = type(export).objects.select_related("action", "proof").get(pk=export.pk)
        historical = copy(locked)
        historical.version = export.case_version
        historical.status = "reviewing"
        with counted(counts, "validation"):
            rights_portability_export.validate_export_binding(historical, person, export)
    return counts["validation"].get("full_export_validation", 0) == 0


def full_rejects(case, author, export):
    with transaction.atomic():
        locked, person, _ = reviewer_case(author, case.pk)
        export = type(export).objects.select_related("action", "proof").get(pk=export.pk)
        historical = copy(locked)
        historical.version, historical.status = export.case_version, "reviewing"
        try:
            rights_portability_export._validate_export_binding(historical, person, export)
        except ValidationError:
            return True
        finally:
            transaction.set_rollback(True)
    return False


def test_generation_seals_and_later_validations_use_it(request, settings, monkeypatch):
    case, author, export, _ = generated(request, settings, monkeypatch)
    assert RightsExportValidationSeal.objects.filter(export=export).exists()
    check(case, author, export)  # A different caller view may validate fully once and seal.
    assert check(case, author, export) is True
    assert full_rejects(case, author, export) is False


@pytest.mark.parametrize(
    "mutation",
    [
        "selection_ciphertext",
        "coverage_read_digest",
        "action_payload",
        "binding_digest",
        "part_ciphertext",
        "image_ciphertext",
        "newer_selection",
        "deleted_read",
    ],
)
def test_any_input_change_disables_the_seal_and_matches_full_validation(
    request, settings, monkeypatch, mutation
):
    case, author, export, _ = generated(request, settings, monkeypatch)
    check(case, author, export)
    binding = export.portability_binding
    with connection.cursor() as cursor:
        if mutation == "selection_ciphertext":
            cursor.execute(
                "UPDATE safety_rightsportabilityselection SET encrypted_selection = "
                "encrypted_selection || 'x' WHERE id = %s",
                [binding.review.selection_id],
            )
        elif mutation == "coverage_read_digest":
            read = RightsPortabilityCoverageRead.objects.filter(
                coverage=binding.coverage_review.coverage
            ).first()
            cursor.execute(
                "UPDATE safety_rightsportabilitycoverageread SET page_digest = %s WHERE id = %s",
                ["0" * 64, read.pk],
            )
        elif mutation == "action_payload":
            cursor.execute(
                "UPDATE safety_rightsaction SET payload_digest = %s WHERE id = %s",
                ["0" * 64, binding.review.action_id],
            )
        elif mutation == "binding_digest":
            cursor.execute(
                "UPDATE safety_rightsexportportabilitybinding SET inspection_digest = %s "
                "WHERE id = %s",
                ["0" * 64, binding.pk],
            )
        elif mutation == "part_ciphertext":
            part = export.parts.order_by("position").first()
            cursor.execute(
                "UPDATE safety_rightsexportpart SET encrypted_content = encrypted_content || 'x' "
                "WHERE id = %s",
                [part.pk],
            )
        elif mutation == "image_ciphertext":
            image = export.images.first()
            cursor.execute(
                "UPDATE safety_rightsexportimage SET encrypted_content = encrypted_content || 'x' "
                "WHERE id = %s",
                [image.pk],
            )
        elif mutation == "newer_selection":
            selection = RightsPortabilitySelection.objects.get(pk=binding.review.selection_id)
            selection.pk, selection.version = None, selection.version + 1
            selection.action_id = binding.review.action_id
            try:
                with transaction.atomic():
                    selection.save()
            except Exception:  # noqa: BLE001 - uniqueness may forbid it; fall back to touching it.
                cursor.execute(
                    "UPDATE safety_rightsportabilityselection SET created_at = now() WHERE id = %s",
                    [binding.review.selection_id],
                )
        elif mutation == "deleted_read":
            read = RightsPortabilityCoverageRead.objects.filter(
                coverage=binding.coverage_review.coverage
            ).last()
            cursor.execute(
                "DELETE FROM safety_rightsportabilitycoverageread WHERE id = %s", [read.pk]
            )
    rejected = full_rejects(case, author, export)
    try:
        sealed = check(case, author, export)
        accepted = True
    except ValidationError:
        sealed, accepted = False, False
    # The seal never holds after a change, and the outcome equals the full validation.
    assert sealed is False
    assert accepted is (not rejected)


def test_seal_expires_at_the_earliest_loaded_expiry_and_on_code_change(
    request, settings, monkeypatch
):
    case, author, export, _ = generated(request, settings, monkeypatch)
    check(case, author, export)  # Seal the fresh delivery caller before testing its expiry.
    seal = RightsExportValidationSeal.objects.filter(export=export).latest("pk")
    just_before = seal.valid_until - timedelta(seconds=1)
    monkeypatch.setattr(timezone, "now", lambda: just_before)
    assert full_rejects(case, author, export) is False  # No earlier expiry: full still accepts.
    assert check(case, author, export) is True
    monkeypatch.setattr(timezone, "now", lambda: seal.valid_until)
    try:
        assert check(case, author, export) is False
    except ValidationError:
        pass
    monkeypatch.undo()
    monkeypatch.setattr(rights_validation_seal, "rule_version", lambda: "changed-code")
    assert check(case, author, export) is False


def test_replay_preserves_the_order_that_validation_consumes():
    with connection.cursor() as cursor:
        cursor.execute("CREATE TEMP TABLE seal_order_fixture (id integer, position integer)")
        cursor.execute("INSERT INTO seal_order_fixture VALUES (1, 1), (2, 2)")
    statement = [("SELECT id FROM seal_order_fixture ORDER BY position", None)]
    before = rights_validation_seal._replay(statement)
    with connection.cursor() as cursor:
        cursor.execute("UPDATE seal_order_fixture SET position = 3 - position")
    assert rights_validation_seal._replay(statement) != before


def test_recording_seals_actual_results_not_a_later_database_state(request, settings, monkeypatch):
    case, author, export, _ = generated(request, settings, monkeypatch)
    caller = {"case": case, "person": None, "export": export}
    with transaction.atomic():
        with rights_validation_seal.recording() as state:
            with connection.cursor() as cursor:
                cursor.execute("SELECT username FROM core_user WHERE id = %s", [author.pk])
                cursor.fetchall()
        User.objects.filter(pk=author.pk).update(username="changed-after-validation")
        rights_validation_seal.create(export, state, caller)
        assert rights_validation_seal.holds(export, caller) is False


def test_recording_preserves_dbapi_fetches_and_matches_ordered_replay():
    with transaction.atomic():
        with rights_validation_seal.recording() as state:
            with connection.cursor() as cursor:
                cursor.execute("SELECT n, n * 2 FROM generate_series(1, 5) AS n ORDER BY n")
                assert len(cursor.description) == 2
                assert cursor.fetchone() == (1, 2)
                assert cursor.fetchmany(2) == [(2, 4), (3, 6)]
                assert list(cursor) == [(4, 8), (5, 10)]
                assert cursor.fetchone() is None
                cursor.execute("SELECT 42 AS second_result")
                assert cursor.fetchall() == [(42,)]
        assert state["supported"]
        assert rights_validation_seal._replay(state["statements"]) == state["digests"]


def test_configuration_change_invalidates_rule_version(settings):
    original = rights_validation_seal.rule_version()
    settings.RIGHTS_ENABLED = "changed-after-validation"
    assert rights_validation_seal.rule_version() != original


def test_unsupported_parameters_decline_seal_without_rejecting_valid_export():
    from types import SimpleNamespace

    export = SimpleNamespace(expires_at=timezone.now() + timedelta(days=1))
    state = {
        "supported": True,
        "statements": [("SELECT %s", [object()])],
        "digests": ["a"],
        "expiries": [export.expires_at],
    }
    assert rights_validation_seal.create(export, state, {}) is None


def test_time_filtered_answer_without_expiry_column_declines_the_seal():
    now = timezone.now()
    with transaction.atomic(), rights_validation_seal.recording() as state:
        with connection.cursor() as cursor:
            cursor.execute("SELECT %s::timestamptz + interval '1 day' AS expires_at", [now])
            cursor.fetchall()
    assert state["supported"] is True  # The bound is visible: valid_until can absorb it.
    with transaction.atomic(), rights_validation_seal.recording() as state:
        with connection.cursor() as cursor:
            # An existence answer hides which rows (and expiries) made it true.
            cursor.execute("SELECT EXISTS (SELECT 1 WHERE %s::timestamptz < %s::timestamptz)",
                           [now, now + timedelta(days=1)])
            cursor.fetchall()
    assert state["supported"] is False


def test_recording_named_cursor_preserves_chunks_and_replays_consumed_rows():
    with transaction.atomic():
        with rights_validation_seal.recording() as state:
            with connection.chunked_cursor() as cursor:
                cursor.execute("SELECT n FROM generate_series(1, 8) AS n ORDER BY n")
                assert cursor.fetchmany(3) == [(1,), (2,), (3,)]
                assert cursor.fetchall() == [(4,), (5,), (6,), (7,), (8,)]
        assert state["supported"]
        assert rights_validation_seal._replay(state["statements"]) == state["digests"]


def test_access_downloads_do_not_reuse_a_portability_image_seal(request, settings):
    from test_rights_exports import make_copy, prepared, url

    case, author, _, client, receipt, _ = prepared(request, settings)
    export = make_copy(case, author)
    for _ in range(2):
        response = client.post(url(receipt, export), {"key": uuid4()})
        assert response.status_code == 200
    assert not RightsExportValidationSeal.objects.filter(export=export).exists()


def test_held_seal_rechecks_external_object_bytes(request, settings, monkeypatch, object_store):  # noqa: F811
    from apps.safety import rights_object_content

    case, author, export, _ = generated(request, settings, monkeypatch)
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True
    monkeypatch.setattr(rights_object_content, "repository", lambda: object_store)
    for row in export.images.all():
        content = rights_object_content.image_bytes(row)
        row.encrypted_content = rights_object_content.seal_binary(
            content, export.pk, "image", row.photo_id
        )
        row.save(update_fields=["encrypted_content"])
    for row in export.parts.all():
        content = rights_object_content.part_bytes(row)
        row.encrypted_content = rights_object_content.seal_binary(
            content, export.pk, "part", row.position
        )
        row.save(update_fields=["encrypted_content"])
    check(case, author, export)
    assert check(case, author, export) is True
    row = export.images.first()
    assert row is not None
    key = object_store.descriptor(row.encrypted_content)["key"]
    # The referenced SQL bytes stay identical: only the physical S3 object changes.
    object_store.client.put_object(Bucket=object_store.bucket, Key=key, Body=b"corrupt ciphertext")
    with pytest.raises(ValidationError, match="External export object"):
        check(case, author, export)
