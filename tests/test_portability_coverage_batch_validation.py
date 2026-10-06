"""Approval must preserve original audited reads without replaying page services."""

import pytest
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_covered_export_races import approved_coverage

from apps.safety import rights_inspection_source as inspection
from apps.safety import rights_portability_selection_review as selected
from apps.safety.rights_portability_coverage_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def test_approval_replay_does_not_rebuild_full_source_per_read(request, settings, monkeypatch):
    case, _, _, _, coverage, decision, reviewer, _, _, _ = approved_coverage(
        request, settings, monkeypatch, False
    )
    calls = []
    for module in [inspection, selected]:
        original = module.source_copy

        def counted(*args, _original=original, **kwargs):
            calls.append(True)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, "source_copy", counted)
    result = record(
        reviewer,
        case.pk,
        case.version,
        coverage.pk,
        decision.action.key,
        "Approve synthetic coverage before observed export authority race",
        "approved",
    )
    assert result.pk == decision.pk and result.read_ids == decision.read_ids
    assert calls == [], "Approval replay rebuilt the source through page inspection"
