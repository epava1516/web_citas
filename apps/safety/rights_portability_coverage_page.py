"""Reconstruct exact audited coverage pages from an already validated source."""

from itertools import islice

from django.core.exceptions import ValidationError

from .rights_copy_inspection import SECTIONS
from .rights_portability_catalog import FIELD_PAGE_SIZE, scalar_fields
from .rights_portability_selection import row_reference


def coverage_page(
    source, assessment, facts, body, summary, dataset, row_index, field_page, *, binary=False
):
    if binary:
        rows = [image for revision in source["revisions"] for image in revision["images"]]
        start = (field_page - 1) * 20
        fields = [dict(item) for item in rows[start : start + 20]]
        if field_page > 1 and not fields:
            raise ValidationError("Coverage binary page unavailable")
        included = {item["photo"]: item["conditions"] for item in facts.get("images", [])}
        for item in fields:
            if assessment["revisions"]["status"] == "excluded":
                item.update(status="excluded", conditions=assessment["revisions"])
            elif item["photo"] in included:
                item.update(status="included", conditions=included[item["photo"]])
            else:
                conditions = body["image_omissions"].get(item["photo"])
                item.update(status="excluded" if conditions else "pending", conditions=conditions)
        reference, more = None, start + 20 < len(rows)
    else:
        rows = SECTIONS[dataset](source)
        if not rows:
            if row_index or field_page != 1:
                raise ValidationError("Coverage inspection page unavailable")
            fields, reference, more = [], None, False
        else:
            if row_index >= len(rows):
                raise ValidationError("Coverage inspection row unavailable")
            row = rows[row_index]
            reference = row_reference(dataset, row_index, row)
            start = (field_page - 1) * FIELD_PAGE_SIZE
            fields = list(islice(scalar_fields(row), start, start + FIELD_PAGE_SIZE + 1))
            if field_page > 1 and not fields:
                raise ValidationError("Coverage inspection page unavailable")
            more, fields = len(fields) > FIELD_PAGE_SIZE, fields[:FIELD_PAGE_SIZE]
            selected = next(
                (
                    set(item["fields"])
                    for item in facts["selection"].get(dataset, [])
                    if item["row"] == reference
                ),
                set(),
            )
            omitted = body["omissions"][dataset].get(reference, {})
            for item in fields:
                if assessment[dataset]["status"] == "excluded":
                    item.update(status="excluded", conditions=assessment[dataset])
                elif item["path"] in selected:
                    item.update(
                        status="included",
                        conditions=facts.get("field_evidence", {})
                        .get(dataset, {})
                        .get(reference, {})
                        .get(item["path"], assessment[dataset]),
                    )
                else:
                    conditions = omitted.get("all", omitted.get("fields", {}).get(item["path"]))
                    item.update(
                        status="excluded" if conditions else "pending", conditions=conditions
                    )
    return {
        "dataset": dataset,
        "binary": binary,
        "row": reference,
        "row_index": row_index,
        "row_count": len(rows),
        "field_page": field_page,
        "fields": fields,
        "has_next_fields": more,
        "has_next_row": row_index + 1 < len(rows),
        "summary": {k: v for k, v in summary.items() if k != "projection"},
    }
