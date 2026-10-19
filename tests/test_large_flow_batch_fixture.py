"""The optimized preparation must still audit every native page and binary boundary."""

import pytest
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_covered_export_races import approved_coverage

from apps.safety.models import RightsPortabilityCoverageRead

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only,binary", [(True, False), (False, False), (False, True)])
def test_batched_preparation_keeps_real_coverage_approval_and_all_audited_pages(
    request,
    settings,
    monkeypatch,
    account_only,
    binary,
):
    from django.db import transaction

    from apps.safety.rights_exports import reviewer_case, source_copy
    from apps.safety.rights_portability_coverage_read_gate import required_pages

    case, author, _, _, coverage, decision, reviewer, _, _, _ = approved_coverage(
        request,
        settings,
        monkeypatch,
        account_only,
        binary=binary,
        batched=True,
    )
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        expected = required_pages(source_copy(person, listing, locked))
    actual = list(
        RightsPortabilityCoverageRead.objects.filter(
            coverage=coverage,
            action__actor=reviewer,
        ).values_list("dataset", "row_index", "field_page", "binary")
    )
    assert len(actual) == len(expected) and set(actual) == set(expected)
    assert any(row[3] for row in actual)  # Includes binary metadata even when no image selected.
    assert decision.outcome == "approved"
    case.refresh_from_db()
    assert case.status != "resolved"  # Preparing coverage must not close or deliver a response.
