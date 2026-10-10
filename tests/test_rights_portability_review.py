from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability import assessment
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import RightsAction, RightsPortabilityRead, RightsPortabilityReview
from apps.safety.rights_portability import save_assessment
from apps.safety.rights_portability_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("complete", [False, True])
def test_portability_independent_review_requires_read_and_resolved_datasets(
    request, settings, monkeypatch, complete
):
    case, author, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    value = assessment()
    if complete:
        for item in value.values():
            item.update(
                status="eligible",
                basis="contract",
                origin="provided",
                automated=True,
                subject_related=True,
                third_party_reviewed=True,
                reason="Synthetic reviewer confirmed dataset conditions",
                evidence="Synthetic evidence of origin and lawful processing",
            )
    row = save_assessment(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Prepare synthetic assessment for independent review",
        value,
    )
    permissions = Permission.objects.filter(
        codename__in=["review_rights_request", "execute_rights_request", "review_portability"]
    )
    author.user_permissions.add(*permissions)
    author = User.objects.get(pk=author.pk)
    reason = "Independently review synthetic portability assessment"
    with pytest.raises(PermissionDenied):
        record(author, case.pk, row.pk, uuid4(), case.version, "inspect", reason)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(*permissions)
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, row.pk, uuid4(), case.version, "review", reason, "approved")
    inspected, body = record(reviewer, case.pk, row.pk, uuid4(), case.version, "inspect", reason)
    assert body == value and inspected.action.actor_id == reviewer.pk
    if not complete:
        with pytest.raises(ValidationError):
            record(reviewer, case.pk, row.pk, uuid4(), case.version, "review", reason, "approved")
    key = uuid4()
    outcome = "approved" if complete else "rejected"
    decision, body = record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)
    assert body is None and decision.read_id == inspected.pk
    from apps.safety.rights_portability_review import validate_approved_assessment

    with transaction.atomic():
        if complete:
            assert (
                validate_approved_assessment(
                    decision, row, case, row.proof, row.source_digest, value
                )
                == value
            )
        else:
            with pytest.raises(ValidationError, match="Current approved"):
                validate_approved_assessment(
                    decision, row, case, row.proof, row.source_digest, value
                )

    assert (
        record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)[0].pk
        == decision.pk
    )
    assert RightsPortabilityReview.objects.count() == 1
    if complete:
        from apps.safety.crypto import unseal
        from apps.safety.models import RightsExport, RightsPortabilitySelection
        from apps.safety.rights_exports import source_copy
        from apps.safety.rights_portability_selection import row_reference
        from apps.safety.rights_portability_selection_store import save_selection

        with transaction.atomic():
            source = source_copy(None, None, case)
        from apps.safety.rights_portability_catalog import inspect_catalog

        catalog_key = uuid4()
        catalog_purpose = "Inspect synthetic scalar choices before guided selection"
        with monkeypatch.context() as catalog_settings:
            catalog_settings.setattr("apps.safety.rights_portability_catalog.FIELD_PAGE_SIZE", 2)
            catalog = inspect_catalog(
                author,
                case.pk,
                case.version,
                decision.pk,
                catalog_key,
                catalog_purpose,
                "subject_account",
            )
            assert len(catalog["fields"]) == 2 and catalog["has_next_fields"]
            assert catalog["row"] == row_reference("subject_account", 0, source["subject_account"])
            assert (
                inspect_catalog(
                    author,
                    case.pk,
                    case.version,
                    decision.pk,
                    catalog_key,
                    catalog_purpose,
                    "subject_account",
                )
                == catalog
            )
            second = inspect_catalog(
                author,
                case.pk,
                case.version,
                decision.pk,
                uuid4(),
                catalog_purpose,
                "subject_account",
                field_page=2,
            )
            assert not set(item["path"] for item in catalog["fields"]) & set(
                item["path"] for item in second["fields"]
            )
            actions_before_invalid_catalog = RightsAction.objects.count()
            with pytest.raises(ValidationError, match="row unavailable"):
                inspect_catalog(
                    author,
                    case.pk,
                    case.version,
                    decision.pk,
                    uuid4(),
                    catalog_purpose,
                    "subject_account",
                    row_index=99,
                )
            with pytest.raises(ValidationError, match="Conflicting portability use"):
                inspect_catalog(
                    author,
                    case.pk,
                    case.version,
                    decision.pk,
                    catalog_key,
                    catalog_purpose,
                    "subject_account",
                    field_page=2,
                )
            assert RightsAction.objects.count() == actions_before_invalid_catalog
            empty = inspect_catalog(
                author, case.pk, case.version, decision.pk, uuid4(), catalog_purpose, "profile"
            )
            assert empty["fields"] == [] and empty["row_count"] == 0 and empty["row"] is None
        account = source["subject_account"]
        field = next(
            name for name, content in account.items() if not isinstance(content, (dict, list))
        )
        selectors = {name: [] for name in value}
        selectors["subject_account"] = [
            {
                "row": row_reference("subject_account", 0, account),
                "fields": ["/" + field.replace("~", "~0").replace("/", "~1")],
            }
        ]
        selection_key = uuid4()
        selection_reason = "Save synthetic explicitly selected portable account fields"
        saved = save_selection(
            author,
            case.pk,
            case.version,
            decision.pk,
            selection_key,
            0,
            selection_reason,
            selectors,
        )
        assert unseal(saved.encrypted_selection)["selection"] == selectors
        assert (
            save_selection(
                author,
                case.pk,
                case.version,
                decision.pk,
                selection_key,
                0,
                selection_reason,
                selectors,
            ).pk
            == saved.pk
        )
        changed = {name: [] for name in value}
        with pytest.raises(ValidationError, match="Conflicting portability (selection|use)"):
            save_selection(
                author,
                case.pk,
                case.version,
                decision.pk,
                selection_key,
                0,
                selection_reason,
                changed,
            )
        assert RightsPortabilitySelection.objects.count() == 1
        from apps.safety.rights_portability_selection_store import inspect_selection

        inspect_key = uuid4()
        purpose = "Inspect synthetic saved portable field selection"
        inspected_selection, projected_selection = inspect_selection(
            author, case.pk, case.version, saved.pk, inspect_key, purpose
        )
        assert inspected_selection.pk == saved.pk
        assert len(projected_selection["datasets"]["subject_account"]) == 1
        assert (
            inspect_selection(author, case.pk, case.version, saved.pk, inspect_key, purpose)[1]
            == projected_selection
        )
        assert RightsAction.objects.filter(operation="selection_read").count() == 1
        from apps.safety.rights_portability_selection_review import inspect as independent_inspect

        with pytest.raises(PermissionDenied, match="Independent selection"):
            independent_inspect(author, case.pk, case.version, saved.pk, uuid4(), purpose)
        from apps.safety.models import RightsPortabilitySelectionReview
        from apps.safety.rights_portability_selection_review import record as selection_record

        with pytest.raises(ValidationError, match="Inspect this selection"):
            selection_record(
                reviewer, case.pk, case.version, saved.pk, uuid4(), purpose, "review", "approved"
            )
        independent_key = uuid4()
        independent_read, independent_projection = independent_inspect(
            reviewer, case.pk, case.version, saved.pk, independent_key, purpose
        )
        assert independent_projection == projected_selection
        assert independent_read.action.actor_id == reviewer.pk
        assert (
            independent_inspect(
                reviewer, case.pk, case.version, saved.pk, independent_key, purpose
            )[0].pk
            == independent_read.pk
        )
        assert RightsAction.objects.filter(operation="selection_inspect").count() == 1
        selection_path = reverse("rights_portability_selection_review", args=[case.pk, saved.pk])
        selected_marker = str(account[field]).encode()
        response = client.get(selection_path)
        assert response.status_code == 200 and selected_marker not in response.content
        assert b"no-store" in response["Cache-Control"].encode()
        # The HTTP inspection is the paginated operation: it needs its own key. Reusing the
        # service key for a different operation is an idempotency conflict, not a replay.
        page_inspection = {
            "key": uuid4(),
            "version": case.version,
            "operation": "inspect",
            "reason": purpose,
            "outcome": "",
        }
        assert client.post(selection_path, page_inspection).status_code == 200
        assert selected_marker in client.post(selection_path, page_inspection).content
        assert selected_marker not in client.get(selection_path).content
        assert (
            selection_path.encode() in client.get(reverse("rights_inspect", args=[case.pk])).content
        )
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(reviewer)
        assert csrf_client.post(selection_path, {}).status_code == 403
        decision_key = uuid4()
        selected_decision, decision_body = selection_record(
            reviewer, case.pk, case.version, saved.pk, decision_key, purpose, "review", "approved"
        )
        assert decision_body is None and selected_decision.read_id == independent_read.pk
        response = client.post(
            selection_path,
            {
                "key": decision_key,
                "version": case.version,
                "operation": "review",
                "reason": purpose,
                "outcome": "approved",
            },
        )
        assert response.status_code == 200 and selected_marker not in response.content
        assert (
            selection_record(
                reviewer,
                case.pk,
                case.version,
                saved.pk,
                decision_key,
                purpose,
                "review",
                "approved",
            )[0].pk
            == selected_decision.pk
        )
        second_read, _ = independent_inspect(
            reviewer, case.pk, case.version, saved.pk, uuid4(), purpose
        )
        assert (
            selection_record(
                reviewer,
                case.pk,
                case.version,
                saved.pk,
                decision_key,
                purpose,
                "review",
                "approved",
            )[0].pk
            == selected_decision.pk
        )
        RightsPortabilitySelectionReview.objects.filter(pk=selected_decision.pk).update(
            read=second_read
        )
        with pytest.raises(ValidationError):
            selection_record(
                reviewer,
                case.pk,
                case.version,
                saved.pk,
                decision_key,
                purpose,
                "review",
                "approved",
            )
        RightsPortabilitySelectionReview.objects.filter(pk=selected_decision.pk).update(
            read=independent_read
        )
        from apps.safety.rights_portability_selected_use import consume_selected

        selected_use_key = uuid4()
        assert (
            consume_selected(
                author,
                case.pk,
                case.version,
                saved.pk,
                selected_decision.pk,
                selected_use_key,
                purpose,
            )[1]
            == projected_selection
        )
        assert (
            consume_selected(
                author,
                case.pk,
                case.version,
                saved.pk,
                selected_decision.pk,
                selected_use_key,
                purpose,
            )[1]
            == projected_selection
        )
        assert RightsAction.objects.filter(operation="selection_use").count() == 1
        actions_before_invalid_decision = RightsAction.objects.count()
        RightsPortabilitySelectionReview.objects.filter(pk=selected_decision.pk).update(
            original_mfa_version=selected_decision.original_mfa_version + 1
        )
        with pytest.raises(ValidationError, match="review evidence changed"):
            consume_selected(
                author, case.pk, case.version, saved.pk, selected_decision.pk, uuid4(), purpose
            )
        assert RightsAction.objects.count() == actions_before_invalid_decision
        RightsPortabilitySelectionReview.objects.filter(pk=selected_decision.pk).update(
            original_mfa_version=selected_decision.original_mfa_version
        )
        audit_before = RightsAction.objects.count()
        RightsPortabilitySelection.objects.filter(pk=saved.pk).update(
            original_mfa_version=saved.original_mfa_version + 1
        )
        with pytest.raises(ValidationError, match="selection evidence changed"):
            inspect_selection(author, case.pk, case.version, saved.pk, uuid4(), purpose)
        assert RightsAction.objects.count() == audit_before
        RightsPortabilitySelection.objects.filter(pk=saved.pk).update(
            original_mfa_version=saved.original_mfa_version
        )
        assert not RightsExport.objects.exists()
        RightsPortabilitySelection.objects.filter(pk=saved.pk).update(selection_digest="0" * 64)
        with pytest.raises(ValidationError, match="Conflicting portability (selection|use)"):
            save_selection(
                author,
                case.pk,
                case.version,
                decision.pk,
                selection_key,
                0,
                selection_reason,
                selectors,
            )
        RightsPortabilitySelection.objects.filter(pk=saved.pk).update(
            selection_digest=saved.selection_digest
        )
    from apps.safety.rights_portability_use import consume_approved

    use_key = uuid4()
    use_reason = "Consume synthetic independently approved portability assessment"
    if complete:
        assert (
            consume_approved(author, case.pk, case.version, decision.pk, use_key, use_reason)[1]
            == value
        )
        assert (
            consume_approved(author, case.pk, case.version, decision.pk, use_key, use_reason)[0].pk
            == decision.pk
        )
        assert RightsAction.objects.filter(operation="portability_use").count() == 1
    else:
        with pytest.raises(ValidationError, match="Current approved"):
            consume_approved(author, case.pk, case.version, decision.pk, use_key, use_reason)
        assert not RightsAction.objects.filter(operation="portability_use").exists()
    path = reverse(
        "rights_portability_review", kwargs={"case_id": case.pk, "assessment_id": row.pk}
    )
    response = client.get(path)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert b"Synthetic evidence of origin" not in response.content
    response = client.post(
        path, {"key": uuid4(), "version": case.version, "operation": "inspect", "reason": reason}
    )
    assert response.status_code == 200
    if complete:
        assert b"Synthetic evidence of origin" in response.content
    assert (
        client.post(
            path,
            {
                "key": key,
                "version": case.version,
                "operation": "review",
                "reason": reason,
                "outcome": outcome,
            },
        ).status_code
        == 200
    )
    assert RightsPortabilityReview.objects.count() == 1
    assert b"Synthetic evidence of origin" not in client.get(path).content
    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsRequest

    with transaction.atomic():
        current = source_manifest(None, case)
        current_rows = {item["model"]: item for item in current["entries"]}
        assert current_rows["safety.RightsPortabilityRead"]["count"] == 0
        assert current_rows["safety.RightsPortabilityReview"]["count"] == 0
        inventory_case = RightsRequest.objects.create(
            submission_key=uuid4(),
            kind="erase",
            account_subject=case.account_subject,
            received_at=case.received_at,
            initial_due_at=case.initial_due_at,
            receipt_expires_at=case.receipt_expires_at,
        )
        projected = source_manifest(None, inventory_case)
        projected_rows = {item["model"]: item for item in projected["entries"]}
        assert projected_rows["safety.RightsPortabilityRead"]["count"] == 2
        assert projected_rows["safety.RightsPortabilityReview"]["count"] == 1
        assert current_rows["safety.RightsPortabilitySelection"]["count"] == 0
        assert projected_rows["safety.RightsPortabilitySelection"]["count"] == int(complete)
        assert current_rows["safety.RightsPortabilitySelectionRead"]["count"] == 0
        assert current_rows["safety.RightsPortabilitySelectionReview"]["count"] == 0
        assert projected_rows["safety.RightsPortabilitySelectionReview"]["count"] == int(complete)
        assert projected_rows["safety.RightsPortabilitySelectionRead"]["count"] == 2 * int(complete)
        if complete:
            selection_digest = projected_rows["safety.RightsPortabilitySelection"]["state_digest"]
            assert saved.encrypted_selection not in str(projected)
            RightsPortabilitySelection.objects.filter(pk=saved.pk).update(
                encrypted_selection="damaged"
            )
            changed = source_manifest(None, inventory_case)
            changed_rows = {item["model"]: item for item in changed["entries"]}
            assert (
                changed_rows["safety.RightsPortabilitySelection"]["state_digest"]
                != selection_digest
            )
            RightsPortabilitySelection.objects.filter(pk=saved.pk).update(
                encrypted_selection=saved.encrypted_selection
            )
        assert row.encrypted_assessment not in str(projected)
        original_digest = projected_rows["safety.RightsPortabilityReview"]["state_digest"]
        replacement_read = (
            RightsPortabilityRead.objects.filter(assessment=row)
            .exclude(pk=decision.read_id)
            .first()
        )
        for field, altered in [
            ("outcome", "rejected" if outcome == "approved" else "approved"),
            ("read_id", replacement_read.pk),
        ]:
            RightsPortabilityReview.objects.filter(pk=decision.pk).update(**{field: altered})
            changed = source_manifest(None, inventory_case)
            changed_rows = {item["model"]: item for item in changed["entries"]}
            assert changed_rows["safety.RightsPortabilityReview"]["state_digest"] != original_digest
            RightsPortabilityReview.objects.filter(pk=decision.pk).update(
                **{field: getattr(decision, field)}
            )

    RightsPortabilityReview.objects.filter(pk=decision.pk).update(read_id=replacement_read.pk)
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)
    RightsPortabilityReview.objects.filter(pk=decision.pk).update(read_id=decision.read_id)
    before = RightsAction.objects.count()
    RightsPortabilityReview.objects.filter(pk=decision.pk).update(
        original_mfa_version=decision.original_mfa_version + 1
    )
    with pytest.raises(ValidationError, match="evidence changed"):
        record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)
    assert RightsAction.objects.count() == before
    RightsPortabilityReview.objects.filter(pk=decision.pk).update(
        original_mfa_version=decision.original_mfa_version
    )
    latest_read = RightsPortabilityRead.objects.get(pk=decision.read_id)
    RightsPortabilityRead.objects.filter(pk=latest_read.pk).update(
        original_session_version=latest_read.original_session_version + 1
    )
    with pytest.raises(ValidationError, match="evidence changed"):
        record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)
    assert RightsAction.objects.count() == before
    case.refresh_from_db()
    assert case.status == "reviewing"

    RightsPortabilityRead.objects.filter(pk=latest_read.pk).update(
        original_session_version=latest_read.original_session_version
    )
    if complete:
        from datetime import timedelta

        from django.utils import timezone

        from apps.safety.tasks import purge_expired_portability_selections

        newer = save_selection(
            author,
            case.pk,
            case.version,
            decision.pk,
            uuid4(),
            saved.version,
            selection_reason,
            selectors,
        )
        actions_before_old_use = RightsAction.objects.count()
        with pytest.raises(ValidationError, match="Latest portability selection"):
            consume_selected(
                author,
                case.pk,
                case.version,
                saved.pk,
                selected_decision.pk,
                selected_use_key,
                purpose,
            )
        assert RightsAction.objects.count() == actions_before_old_use
        independent_inspect(reviewer, case.pk, case.version, newer.pk, uuid4(), purpose)
        rejected, _ = selection_record(
            reviewer, case.pk, case.version, newer.pk, uuid4(), purpose, "review", "rejected"
        )
        actions_before_rejected_use = RightsAction.objects.count()
        with pytest.raises(ValidationError, match="Approved portability selection"):
            consume_selected(author, case.pk, case.version, newer.pk, rejected.pk, uuid4(), purpose)
        assert RightsAction.objects.count() == actions_before_rejected_use
        audit_count = RightsAction.objects.count()
        assert purge_expired_portability_selections() == 0
        RightsPortabilitySelection.objects.filter(pk=saved.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        assert purge_expired_portability_selections() == 1
        assert purge_expired_portability_selections() == 0
        saved.refresh_from_db()
        assert saved.encrypted_selection == "" and saved.purged_at is not None
        assert saved.action_id and saved.selection_digest
        with pytest.raises(ValidationError, match="Portability selection expired"):
            save_selection(
                author,
                case.pk,
                case.version,
                decision.pk,
                selection_key,
                0,
                selection_reason,
                selectors,
            )
        assert RightsAction.objects.count() == audit_count
        case.refresh_from_db()
        assert case.status == "reviewing"
