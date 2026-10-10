"""Explicit scalar field selection; caller must bind selectors to approved evidence."""

from copy import deepcopy

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from .fast_canonical import content_reference
from .rights_copy_inspection import SECTIONS
from .rights_portability import DATASETS, checked_assessment


def row_reference(dataset, index, row):
    from .rights_inspection_source import shared_row_reference

    return shared_row_reference(
        dataset, index, row,
        lambda: content_reference({"dataset": dataset, "index": index, "row": row}),
    )


def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise ValidationError("Invalid portability field path")
    value = row
    for segment in path[1:].split("/"):
        # RFC6901 escape sequences; reject malformed aliases.
        escaped = segment.replace("~1", "").replace("~0", "")
        if "~" in escaped:
            raise ValidationError("Invalid portability field escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and key.isascii()
            and key.isdecimal()
            and str(int(key)) == key
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise ValidationError("Portability field unavailable")
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return deepcopy(value)


@sensitive_variables()
def project_selected(source, assessment, selection, *, field_evidence=None):
    """Project declared eligible fields; not a standalone authorization or delivery API."""
    checked = checked_assessment(assessment)
    eligible = {
        name for name, item in checked.items() if item["status"] in {"eligible", "granular"}
    }
    if not isinstance(selection, dict) or set(selection) != eligible:
        raise ValidationError("Select each eligible dataset explicitly")
    granular = {
        name for name in eligible if checked[name]["status"] == "granular" and selection[name]
    }
    if field_evidence is None:
        field_evidence = {}
    if not isinstance(field_evidence, dict) or set(field_evidence) != granular:
        raise ValidationError("Provide exact field evidence for mixed dataset selections")
    output = {}
    for dataset in sorted(eligible):
        rows = SECTIONS[dataset](source)
        references = {row_reference(dataset, index, row): row for index, row in enumerate(rows)}
        selectors = selection[dataset]
        if not isinstance(selectors, list):
            raise ValidationError("Invalid portability row selection")
        evidence_rows = field_evidence.get(dataset, {})
        if not isinstance(evidence_rows, dict):
            raise ValidationError("Invalid mixed row evidence")
        seen = set()
        projected = []
        for selector in selectors:
            if not isinstance(selector, dict) or set(selector) != {"row", "fields"}:
                raise ValidationError("Invalid portability row selector")
            reference, paths = selector["row"], selector["fields"]
            if not isinstance(reference, str) or reference not in references or reference in seen:
                raise ValidationError("Portability row unavailable or duplicated")
            if (
                not isinstance(paths, list)
                or not paths
                or any(not isinstance(path, str) for path in paths)
                or len(set(paths)) != len(paths)
            ):
                raise ValidationError("Select unique portability fields")
            if dataset in granular:
                evidence = evidence_rows.get(reference)
                if not isinstance(evidence, dict) or set(evidence) != set(paths):
                    raise ValidationError("Provide exact evidence for each selected mixed field")
                for decision in evidence.values():
                    if not isinstance(decision, dict) or decision.get("status") != "eligible":
                        raise ValidationError("Selected mixed fields require eligible conditions")
                    checked_assessment({name: decision for name in DATASETS})
            seen.add(reference)
            projected.append(
                {"fields": {path: pointer_value(references[reference], path) for path in paths}}
            )
        if dataset in granular and set(evidence_rows) != seen:
            raise ValidationError("Mixed evidence contains unselected rows")
        output[dataset] = projected
    return {"schema": "portability-selected-fields-v1", "datasets": output}
