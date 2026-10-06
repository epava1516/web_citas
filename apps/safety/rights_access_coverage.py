"""Access copy accounting, not authorization, approval or legal determination.

Every source row and delivered row is accounted for. Differences require explicit
motivated decisions; this compiler never removes the copy's partial flags.
"""

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from .rights import fingerprint
from .rights_copy_inspection import SECTIONS
from .rights_exports import canonical
from .rights_portability_catalog import scalar_fields
from .rights_portability_selection import row_reference

# Profile/account projections are deliberately incomplete. These boundaries must
# remain visible even when the projection itself has no pending_review marker.
UNPROJECTED = {"purpose_inventory", "other_subject_records"}


def decision(value, *, status):
    if (
        not isinstance(value, dict)
        or set(value) != {"status", "reason", "evidence"}
        or value["status"] != status
        or any(
            not isinstance(value[field], str) or not 20 <= len(value[field].strip()) <= 2000
            for field in ("reason", "evidence")
        )
    ):
        raise ValidationError("Explicit motivated access decision and evidence required")
    return value


def container_paths(value, prefix=""):
    """Include empty containers so injected objects cannot escape leaf accounting."""
    result = {}
    if isinstance(value, dict):
        result[prefix] = "object"
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid access object key")
            path = prefix + "/" + key.replace("~", "~0").replace("/", "~1")
            result.update(container_paths(child, path))
    elif isinstance(value, list):
        result[prefix] = "array"
        for index, child in enumerate(value):
            result.update(container_paths(child, prefix + "/" + str(index)))
    return result


@sensitive_variables()
def compile_coverage(source, delivered, declarations, expected_source, expected_delivery):
    """Validate declared accounting; independent evidence validation remains mandatory."""
    if (
        fingerprint(canonical(source)) != expected_source
        or fingerprint(canonical(delivered)) != expected_delivery
    ):
        raise ValidationError("Access coverage source or delivery changed")
    if (
        not isinstance(declarations, dict)
        or set(declarations) != {"sections", "boundaries"}
        or not isinstance(declarations["sections"], dict)
        or set(declarations["sections"]) != set(SECTIONS)
    ):
        raise ValidationError("Account for every access section, including empty sections")
    result = {
        "sections": {},
        "boundaries": {},
        "source": expected_source,
        "delivery": expected_delivery,
    }
    for section, project in SECTIONS.items():
        original, copied = project(source), project(delivered)
        rows = declarations["sections"][section]
        if not isinstance(rows, list) or len(rows) != len(original):
            raise ValidationError("Account for every original access row")
        seen = set()
        output = []
        for index, (row, declaration) in enumerate(zip(original, rows, strict=True)):
            if (
                not isinstance(declaration, dict)
                or set(declaration) != {"row", "delivered_index", "decisions"}
                or declaration["row"] != row_reference(section, index, row)
                or not isinstance(declaration["decisions"], dict)
            ):
                raise ValidationError("Access source row reference changed")
            position = declaration["delivered_index"]
            if position is None:
                copy_fields = {}
            elif type(position) is int and 0 <= position < len(copied) and position not in seen:
                source_containers = container_paths(row)
                delivered_containers = container_paths(copied[position])
                if any(
                    source_containers.get(path) != kind
                    for path, kind in delivered_containers.items()
                ):
                    raise ValidationError("Unaccounted container in access delivery")
                seen.add(position)
                copy_fields = {
                    item["path"]: item["value"] for item in scalar_fields(copied[position])
                }
            else:
                raise ValidationError("Every delivered row requires a unique source row")
            fields = {item["path"]: item["value"] for item in scalar_fields(row)}
            if not set(copy_fields) <= set(fields):
                raise ValidationError("Unaccounted data in access delivery")
            differences = {
                path
                for path in fields
                if path not in copy_fields
                or canonical(fields[path]) != canonical(copy_fields[path])
            }
            if set(declaration["decisions"]) != differences:
                raise ValidationError("Account for every omitted or redacted access field")
            for path in differences:
                decision(
                    declaration["decisions"][path],
                    status="omitted" if path not in copy_fields else "redacted",
                )
            # Empty objects have no scalar fields but omitting the row still needs a decision.
            if position is None and not fields:
                raise ValidationError("Empty source row requires explicit delivery")
            output.append(
                {
                    "row": declaration["row"],
                    "delivered_index": position,
                    "included_fields": len(fields) - len(differences),
                    "decisions": declaration["decisions"],
                }
            )
        if seen != set(range(len(copied))):
            raise ValidationError("Unaccounted row in access delivery")
        result["sections"][section] = output
    pending = (
        set(source.get("pending_review", []))
        | set(delivered.get("pending_review", []))
        | UNPROJECTED
    )
    boundaries = declarations["boundaries"]
    if not isinstance(boundaries, dict) or set(boundaries) != pending:
        raise ValidationError("Account for every projected and unprojected access boundary")
    for name, value in boundaries.items():
        # A declaration is not verification of this evidence. The consuming flow
        # must independently inspect and approve the cited exact records.
        if not isinstance(value, dict) or value.get("status") not in {"excluded", "supplemented"}:
            raise ValidationError("Pending access boundary prevents final accounting")
        result["boundaries"][name] = decision(value, status=value["status"])
    result["accounting_digest"] = fingerprint(canonical(result))
    return result
