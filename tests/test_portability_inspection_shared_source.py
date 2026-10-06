"""Native PostgreSQL equivalence and late-change gates for shared inspection source."""

from uuid import uuid4, uuid5

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.listings.models import Revision
from apps.safety import rights_inspection_source as shared
from apps.safety import rights_portability_coverage_inspection as inspection
from apps.safety import rights_portability_selection_review as selected
from apps.safety.models import RightsAction, RightsPortabilityCoverageRead
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_portability_coverage_store import save_coverage

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Inspect synthetic coverage with transaction scoped source checks"


def ready(request, settings, monkeypatch, account_only=False):
    case, author, _, decision, person, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    coverage = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        REASON,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    return case, coverage, decision.action.actor, person


@pytest.mark.parametrize("account_only", [False, True])
def test_native_shared_read_and_unshared_replay_are_equivalent_with_two_source_reads(
    request, settings, monkeypatch, account_only
):
    case, coverage, reviewer, _ = ready(request, settings, monkeypatch, account_only)
    calls = []
    for module in [shared, selected]:
        original = module.source_copy

        def counted(*args, _original=original, **kwargs):
            calls.append(True)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, "source_copy", counted)
    key = uuid4()
    args = (
        reviewer,
        case.pk,
        case.version,
        coverage.pk,
        key,
        REASON,
        "subject_account" if account_only else "profile",
    )
    action, page = inspection.inspect_page(*args)
    assert len(calls) == 2
    original_record = inspection.record

    def unshared(*args, **kwargs):
        kwargs.pop("_inspection_source", None)
        return original_record(*args, **kwargs)

    monkeypatch.setattr(inspection, "record", unshared)
    calls.clear()
    replay, legacy_page = inspection.inspect_page(*args)
    assert len(calls) == 4
    assert replay.pk == action.pk and legacy_page == page
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == 1


@pytest.mark.parametrize("change", ["source", "permission", "session", "mfa"])
def test_change_after_page_compilation_rolls_back_both_audited_reads(
    request, settings, monkeypatch, change
):
    case, coverage, reviewer, person = ready(request, settings, monkeypatch)
    original_page = inspection.coverage_page
    revision = Revision.objects.filter(listing=person.listing).first()
    original_description = revision.description
    key = uuid4()
    child_key = uuid5(key, "coverage-inspection:profile:0:1:False")
    before = RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count()

    def altered(*args, **kwargs):
        page = original_page(*args, **kwargs)
        if change == "source":
            Revision.objects.filter(pk=revision.pk).update(
                description="Synthetic late source drift"
            )
        elif change == "permission":
            reviewer.user_permissions.clear()
            reviewer.groups.clear()
        else:
            field = "session_version" if change == "session" else "mfa_version"
            User.objects.filter(pk=reviewer.pk).update(**{field: getattr(reviewer, field) + 1})
        return page

    monkeypatch.setattr(inspection, "coverage_page", altered)
    with pytest.raises((PermissionDenied, ValidationError)):
        inspection.inspect_page(
            reviewer, case.pk, case.version, coverage.pk, key, REASON, "profile"
        )
    assert not RightsAction.objects.filter(key__in=[key, child_key]).exists()
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == before
    revision.refresh_from_db()
    assert revision.description == original_description
