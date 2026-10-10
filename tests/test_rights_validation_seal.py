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
