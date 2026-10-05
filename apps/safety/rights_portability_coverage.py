"""Explicit coverage declarations for portable fields and binaries; grants no authority."""

from django.core.exceptions import ValidationError

from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_portability import DATASETS, checked_assessment
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_images import checked_images
from apps.safety.rights_portability_selection import project_selected, row_reference


def exclusion(value):
    if not isinstance(value, dict) or value.get("status") != "excluded":
        raise ValidationError("Document a definite exclusion, not an unknown omission")
    return checked_assessment({name: value for name in DATASETS})[DATASETS[0]]


def compile_coverage(
    source, assessment, selection, omissions, images, image_omissions, *, field_evidence=None
):
    assessment = checked_assessment(assessment)
    if any(facts["status"] == "pending" for facts in assessment.values()):
        raise ValidationError("Pending datasets prevent final coverage")
    projection = project_selected(source, assessment, selection, field_evidence=field_evidence)
    if not isinstance(omissions, dict) or set(omissions) != set(DATASETS):
        raise ValidationError("Cover every dataset, including empty datasets")
    if not isinstance(images, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("photo"), str)
        or not isinstance(item.get("content_digest"), str)
        for item in images
    ):
        raise ValidationError("Invalid binary coverage declarations")
    checked_images(
        source, assessment, images, {item["photo"]: item["content_digest"] for item in images}
    )
    datasets = {}
    for name in DATASETS:
        rows = SECTIONS[name](source)
        row_decisions = omissions[name]
        if not isinstance(row_decisions, dict):
            raise ValidationError("Invalid coverage row decisions")
        if assessment[name]["status"] == "excluded":
            if row_decisions:
                raise ValidationError("Dataset exclusion already covers its rows")
            datasets[name] = {"status": "excluded", "rows": len(rows)}
            continue
        selectors = {item["row"]: set(item["fields"]) for item in selection[name]}
        missing_rows = set()
        included_count = excluded_count = 0
        for index, row in enumerate(rows):
            reference = row_reference(name, index, row)
            paths = {item["path"] for item in scalar_fields(row)}
            selected = selectors.get(reference, set())
            missing = paths - selected
            included_count += len(selected)
            excluded_count += len(missing)
            if not missing:
                continue
            missing_rows.add(reference)
            decision = row_decisions.get(reference)
            if not isinstance(decision, dict):
                raise ValidationError("Every omitted row or field needs evidence")
            if set(decision) == {"all"}:
                exclusion(decision["all"])
            elif set(decision) == {"fields"} and isinstance(decision["fields"], dict):
                if set(decision["fields"]) != missing:
                    raise ValidationError("Cover exactly the omitted scalar fields")
                for facts in decision["fields"].values():
                    exclusion(facts)
            else:
                raise ValidationError("Invalid omission coverage schema")
        if set(row_decisions) != missing_rows:
            raise ValidationError("Coverage contains unavailable or already included rows")
        datasets[name] = {
            "status": "covered",
            "rows": len(rows),
            "included_fields": included_count,
            "excluded_fields": excluded_count,
        }
    photos = [image["photo"] for row in source["revisions"] for image in row["images"]]
    if len(set(photos)) != len(photos):
        raise ValidationError("Duplicate source binary references")
    included = {item["photo"] for item in images}
    if not isinstance(image_omissions, dict):
        raise ValidationError("Explicit binary omission decisions required")
    if assessment["revisions"]["status"] == "excluded":
        if included or image_omissions:
            raise ValidationError("Revision exclusion already covers its binaries")
    else:
        if set(image_omissions) != set(photos) - included:
            raise ValidationError("Every omitted binary needs its own coverage")
        for facts in image_omissions.values():
            exclusion(facts)
    return {
        "schema": "portability-coverage-v1",
        "datasets": datasets,
        "included_images": len(included),
        "excluded_images": len(photos) - len(included),
        "projection": projection,
    }
