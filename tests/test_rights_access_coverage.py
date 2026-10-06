from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights import fingerprint
from apps.safety.rights_access_coverage import UNPROJECTED, compile_coverage
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical
from apps.safety.rights_portability_selection import row_reference


def fixture():
    source = {
        "profile": {"alias": "Synthetic", "contact": "Synthetic shared contact"},
        "subject_account": None,
        "revisions": [],
        "legal_acceptances": [],
        "representation": None,
        "account_activity": {"favorites": [], "personal_contacts": [], "agency_relationships": []},
        "partial": True,
        "simulation": True,
        "pending_review": ["shared_contacts"],
    }
    delivered = deepcopy(source)
    del delivered["profile"]["contact"]
    declarations = {
        "sections": {section: [] for section in SECTIONS},
        "boundaries": {
            name: {
                "status": "excluded",
                "reason": "Synthetic explicit scope exclusion",
                "evidence": "Synthetic records for independent review",
            }
            for name in UNPROJECTED | {"shared_contacts"}
        },
    }
    declarations["sections"]["profile"] = [
        {
            "row": row_reference("profile", 0, source["profile"]),
            "delivered_index": 0,
            "decisions": {
                "/contact": {
                    "status": "omitted",
                    "reason": "Synthetic shared third party contact",
                    "evidence": "Synthetic contact ownership record",
                }
            },
        }
    ]
    return source, delivered, declarations


def compile(source, delivered, declarations):
    return compile_coverage(
        source,
        delivered,
        declarations,
        fingerprint(canonical(source)),
        fingerprint(canonical(delivered)),
    )


def test_every_field_and_unprojected_boundary_is_accounted_without_authorizing():
    source, delivered, declarations = fixture()
    before = deepcopy((source, delivered, declarations))
    result = compile(source, delivered, declarations)
    assert result["sections"]["profile"][0]["included_fields"] == 1
    assert set(result["boundaries"]) == UNPROJECTED | {"shared_contacts"}
    assert (source, delivered, declarations) == before
    assert source["partial"] and delivered["partial"]
    assert "approved" not in result and "complete" not in result


@pytest.mark.parametrize(
    "change",
    [
        "missing_field",
        "missing_boundary",
        "unknown_boundary",
        "pending",
        "foreign_field",
        "foreign_row",
        "stale_reference",
        "false_index",
        "missing_section",
        "redacted_without_decision",
    ],
)
def test_incomplete_or_conflicting_accounting_is_rejected(change):
    source, delivered, declarations = fixture()
    row = declarations["sections"]["profile"][0]
    if change == "missing_field":
        row["decisions"] = {}
    elif change == "missing_boundary":
        del declarations["boundaries"]["shared_contacts"]
    elif change == "unknown_boundary":
        declarations["boundaries"]["unknown"] = {}
    elif change == "pending":
        declarations["boundaries"]["shared_contacts"]["status"] = "pending"
    elif change == "foreign_field":
        delivered["profile"]["foreign"] = "Foreign synthetic subject"
    elif change == "foreign_row":
        delivered["revisions"] = [{"title": "Foreign synthetic revision"}]
    elif change == "stale_reference":
        row["row"] = "0" * 64
    elif change == "false_index":
        row["delivered_index"] = False
    elif change == "missing_section":
        del declarations["sections"]["favorites"]
    elif change == "redacted_without_decision":
        delivered["profile"]["alias"] = "Redacted"
    with pytest.raises(ValidationError):
        compile(source, delivered, declarations)


def test_old_delivery_digest_rejected_even_when_new_rows_could_be_accounted():
    source, delivered, declarations = fixture()
    digest = fingerprint(canonical(delivered))
    delivered["simulation"] = False
    with pytest.raises(ValidationError, match="changed"):
        compile_coverage(source, delivered, declarations, fingerprint(canonical(source)), digest)


def test_injected_empty_container_cannot_escape_scalar_accounting():
    source, delivered, declarations = fixture()
    delivered["profile"]["foreign_empty_object"] = {}
    with pytest.raises(ValidationError, match="container"):
        compile(source, delivered, declarations)


def test_redaction_requires_motivated_exact_field_decision():
    source, delivered, declarations = fixture()
    delivered["profile"]["alias"] = "Reviewed redacted alias"
    declarations["sections"]["profile"][0]["decisions"]["/alias"] = {
        "status": "redacted",
        "reason": "Synthetic third party reference in original alias",
        "evidence": "Synthetic exact original and sanitized field review",
    }
    result = compile(source, delivered, declarations)
    assert result["sections"]["profile"][0]["included_fields"] == 0
    declarations["sections"]["profile"][0]["decisions"]["/alias"]["status"] = "omitted"
    with pytest.raises(ValidationError, match="motivated"):
        compile(source, delivered, declarations)
