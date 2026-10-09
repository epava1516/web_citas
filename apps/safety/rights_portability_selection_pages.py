"""Bounded selection display and current independent page evidence; no cache."""

import math

from django.core.exceptions import ValidationError

from .crypto import unseal
from .models import RightsPortabilitySelectionRead
from .rights import fingerprint
from .rights_exports import canonical

PAGE_SIZE = 50


def page_count(selection):
    body = unseal(selection.encrypted_selection)
    total = sum(len(rows) for rows in body["selection"].values()) + len(body.get("images", []))
    return max(1, math.ceil(total / PAGE_SIZE)), total


def project_page(projected, binding, page):
    rows = [(dataset, index, row) for dataset, items in sorted(projected["datasets"].items())
            for index, row in enumerate(items)]
    rows.extend(("images", index, item) for index, item in enumerate(binding.get("images", [])))
    total, pages = len(rows), max(1, math.ceil(len(rows) / PAGE_SIZE))
    if type(page) is not int or not 1 <= page <= pages:
        raise ValidationError("Selection page unavailable")
    selected = rows[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
    body = {"schema": projected["schema"], "datasets": {name: [] for name in projected["datasets"]}}
    evidence = {}
    images = []
    for dataset, index, row in selected:
        if dataset == "images":
            images.append(row)
            continue
        body["datasets"][dataset].append(row)
        reference = binding["selection"][dataset][index]["row"]
        if reference in binding.get("field_evidence", {}).get(dataset, {}):
            evidence.setdefault(dataset, {})[reference] = binding["field_evidence"][dataset][reference]
    if "field_evidence" in binding:
        body["field_evidence"] = evidence
    if "images" in binding:
        body["images"] = images
    body["pagination"] = {"page": page, "pages": pages, "total": total, "rows": len(selected)}
    metadata = {"page": page, "pages": pages, "total": total, "size": PAGE_SIZE,
                "digest": fingerprint(canonical(body))}
    return body, metadata


def valid_metadata(value):
    if not isinstance(value, dict) or set(value) != {"page", "pages", "total", "size", "digest"}:
        return False
    return (all(type(value[name]) is int for name in ["page", "pages", "total", "size"])
            and value["size"] == PAGE_SIZE and value["total"] >= 0
            and value["pages"] == max(1, math.ceil(value["total"] / PAGE_SIZE))
            and 1 <= value["page"] <= value["pages"]
            and isinstance(value["digest"], str) and len(value["digest"]) == 64
            and all(char in "0123456789abcdef" for char in value["digest"]))


def complete_pages(row, case, proof, actor_id, session_version, mfa_version, *, ids=None):
    from .rights_portability_selection_review import validate_evidence

    if ids is not None and (not isinstance(ids, list) or not ids
                            or any(type(pk) is not int for pk in ids) or len(set(ids)) != len(ids)):
        raise ValidationError("Invalid selection page references")
    pages, total = page_count(row)
    reads = RightsPortabilitySelectionRead.objects.select_related("action").filter(
        selection=row, proof=proof, source_digest=row.source_digest,
        selection_digest=row.selection_digest, action__actor_id=actor_id,
        action__expected_version=case.version, original_session_version=session_version,
        original_mfa_version=mfa_version,
    ).order_by("-pk")
    if ids is not None:
        reads = reads.filter(pk__in=ids)
    chosen = {}
    for read in reads:
        metadata = read.page_metadata
        if not metadata:
            continue
        if not valid_metadata(metadata) or metadata["pages"] != pages or metadata["total"] != total:
            raise ValidationError("Selection page evidence changed")
        chosen.setdefault(metadata["page"], read)
    if set(chosen) != set(range(1, pages + 1)):
        raise ValidationError("Inspect every current selection page before deciding")
    result = [chosen[index].pk for index in range(1, pages + 1)]
    if ids is not None and result != ids:
        raise ValidationError("Selection page references changed")
    for read in chosen.values():
        validate_evidence(read, row, case, proof)
    return result
