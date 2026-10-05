"""Signed page editing of a complete explicit selector draft, preserving other pages."""

from copy import deepcopy

from cryptography.fernet import InvalidToken
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import unseal
from .models import RightsAction, RightsPortabilityReview, RightsPortabilitySelection
from .rights_copy_page_review import fresh_authority
from .rights_exports import reviewer_case
from .rights_portability_catalog import inspect_catalog
from .rights_portability_selection_store import save_selection, validate_selection_evidence

SALT = "portability-selection-page-v1"
MAX_AGE = 1800


def latest_draft(case, user):
    return (
        RightsPortabilitySelection.objects.filter(request=case, actor=user)
        .order_by("-version")
        .first()
    )


@transaction.atomic
@sensitive_variables()
def prepare_page(
    user, case_id, version, review_id, key, purpose, dataset, row_index=0, field_page=1
):
    case, _, _ = reviewer_case(user, case_id)
    fresh_authority(user, case, user.session_version, user.mfa_version)
    catalog = inspect_catalog(
        user, case_id, version, review_id, key, purpose, dataset, row_index, field_page
    )
    baseline = latest_draft(case, user)
    review = RightsPortabilityReview.objects.select_related(
        "assessment", "read__action", "action"
    ).get(pk=review_id)
    selected = {}
    existing_evidence = {}
    if baseline:
        facts = validate_selection_evidence(baseline, review, case)
        selected = facts["selection"]
        existing_evidence = facts.get("field_evidence", {})
    chosen = next(
        (item["fields"] for item in selected.get(dataset, []) if item["row"] == catalog["row"]), []
    )
    granular = unseal(review.assessment.encrypted_assessment)[dataset]["status"] == "granular"
    page_paths = {item["path"] for item in catalog["fields"]}
    page_evidence = {
        path: facts
        for path, facts in existing_evidence.get(dataset, {}).get(catalog["row"], {}).items()
        if path in page_paths
    }
    token = signing.dumps(
        {
            "actor": user.pk,
            "case": str(case.pk),
            "version": version,
            "session": user.session_version,
            "mfa": user.mfa_version,
            "review": review_id,
            "action": RightsAction.objects.get(key=key).pk,
            "dataset": dataset,
            "granular": granular,
            "row_index": row_index,
            "field_page": field_page,
            "row": catalog["row"],
            "paths": [item["path"] for item in catalog["fields"]],
            "base_id": baseline.pk if baseline else None,
            "base_version": baseline.version if baseline else 0,
            "base_digest": baseline.selection_digest if baseline else None,
        },
        salt=SALT,
        compress=True,
    )
    return {
        **catalog,
        "token": token,
        "chosen": chosen,
        "granular": granular,
        "field_decisions": page_evidence,
    }


@transaction.atomic
@sensitive_variables()
def save_page(user, case_id, token, key, reason, paths, *, field_decisions=None):
    try:
        context = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except (signing.BadSignature, TypeError, ValueError) as error:
        raise ValidationError("Portability page expired or invalid") from error
    if not isinstance(context, dict) or (
        context.get("actor") != user.pk
        or context.get("case") != str(case_id)
        or context.get("session") != user.session_version
        or context.get("mfa") != user.mfa_version
    ):
        raise PermissionDenied
    case, _, _ = reviewer_case(user, case_id)
    fresh_authority(user, case, user.session_version, user.mfa_version)
    if (
        not isinstance(paths, list)
        or any(not isinstance(path, str) for path in paths)
        or len(set(paths)) != len(paths)
    ):
        raise ValidationError("Select unique fields from inspected page")
    action = RightsAction.objects.filter(
        pk=context.get("action"),
        request=case,
        actor=user,
        operation="selection_catalog",
        expected_version=context.get("version"),
    ).first()
    if action is None:
        raise ValidationError("Inspected portability page unavailable")
    try:
        purpose = unseal(action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Inspected portability page unavailable") from error
    catalog = inspect_catalog(
        user,
        case_id,
        context["version"],
        context["review"],
        action.key,
        purpose,
        context["dataset"],
        context["row_index"],
        context["field_page"],
    )
    allowed = [item["path"] for item in catalog["fields"]]
    if (
        allowed != context.get("paths")
        or catalog["row"] != context.get("row")
        or not set(paths) <= set(allowed)
    ):
        raise ValidationError("Select fields only from inspected page")
    baseline = None
    if context.get("base_id") is not None:
        baseline = (
            RightsPortabilitySelection.objects.select_for_update()
            .filter(
                pk=context["base_id"],
                request=case,
                actor=user,
                version=context["base_version"],
                selection_digest=context["base_digest"],
            )
            .first()
        )
        if baseline is None:
            raise ValidationError("Portability selection baseline changed")
    latest = latest_draft(case, user)
    retry = RightsPortabilitySelection.objects.filter(
        action__key=key, request=case, actor=user
    ).first()
    if retry is None and (latest.pk if latest else None) != (baseline.pk if baseline else None):
        raise ValidationError("Portability selection version changed")
    review = RightsPortabilityReview.objects.select_related(
        "assessment", "read__action", "action"
    ).get(pk=context["review"])
    if baseline:
        baseline_facts = validate_selection_evidence(baseline, review, case)
        selectors = deepcopy(baseline_facts["selection"])
        evidence = deepcopy(baseline_facts.get("field_evidence", {}))
    else:
        # Approved assessment was validated by the audited catalog operation above.
        assessment = unseal(review.assessment.encrypted_assessment)
        evidence = {}
        selectors = {
            name: []
            for name, item in assessment.items()
            if item["status"] in {"eligible", "granular"}
        }
    dataset = context["dataset"]
    existing = next((item for item in selectors[dataset] if item["row"] == catalog["row"]), None)
    previous_paths = existing["fields"] if existing else []
    kept = [path for path in previous_paths if path not in allowed]
    combined = kept + paths
    selectors[dataset] = [item for item in selectors[dataset] if item["row"] != catalog["row"]]
    if combined:
        selectors[dataset].append({"row": catalog["row"], "fields": combined})
    if context.get("granular"):
        if field_decisions is None and not paths:
            field_decisions = {}
        if not isinstance(field_decisions, dict) or set(field_decisions) != set(paths):
            raise ValidationError("Provide exact decisions for selected fields on this page")
        row_evidence = evidence.setdefault(dataset, {}).setdefault(catalog["row"], {})
        for path in allowed:
            row_evidence.pop(path, None)
        row_evidence.update(deepcopy(field_decisions))
        if not row_evidence:
            evidence[dataset].pop(catalog["row"], None)
        if not evidence[dataset]:
            evidence.pop(dataset, None)
    elif field_decisions:
        raise ValidationError("Unexpected granular field decisions")
    return save_selection(
        user,
        case_id,
        context["version"],
        context["review"],
        key,
        context["base_version"],
        reason,
        selectors,
        field_evidence=evidence or None,
        images=deepcopy(baseline_facts.get("images")) if baseline else None,
    )
