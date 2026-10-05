"""Binary deliveries retain authorization after observed PostgreSQL waits."""

from uuid import uuid4

import pytest
import test_rights_exports as exports
import test_rights_portability_export_races as races
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.rights_portability_image_read import inspect
from apps.safety.rights_portability_image_selection import prepare, save
from apps.safety.rights_portability_selection_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("transport", ["generate", "image", "package"])
@pytest.mark.parametrize("change", ["replay", "proof", "source", "binding"])
def test_binary_export_rechecks_after_observed_wait(
    request, settings, monkeypatch, transport, change
):
    original_prepare = races.prepared_selection
    original_url = exports.url

    def binary_selection(request, settings, monkeypatch, account_only):
        assert not account_only
        case, author, baseline, previous, person, subject, receipt = original_prepare(
            request, settings, monkeypatch, False
        )
        reason = "Inspect synthetic portable binary before observed concurrent wait"
        page = prepare(
            author,
            case.pk,
            case.version,
            baseline.assessment_review_id,
            uuid4(),
            reason,
            0,
            0,
        )
        conditions = {
            "status": "eligible",
            "basis": "contract",
            "origin": "provided",
            "automated": True,
            "subject_related": True,
            "third_party_reviewed": True,
            "reason": reason,
            "evidence": "Synthetic explicit binary eligibility evidence",
        }
        row = save(author, uuid4(), page["token"], reason, True, conditions)
        reviewer = previous.action.actor
        record(reviewer, case.pk, case.version, row.pk, uuid4(), reason)
        inspect(
            reviewer,
            case.pk,
            case.version,
            row.pk,
            page["declaration"]["photo"],
            uuid4(),
            reason,
        )
        decision, _ = record(
            reviewer, case.pk, case.version, row.pk, uuid4(), reason, "review", "approved"
        )
        return case, author, row, decision, person, subject, receipt

    def binary_url(receipt, export):
        base = original_url(receipt, export)
        if transport == "image":
            return base + f"image/{export.images.get().pk}/"
        if transport == "package":
            return base + f"part/{export.parts.exclude(attachments=[]).get().pk}/"
        return base

    monkeypatch.setattr(races, "prepared_selection", binary_selection)
    monkeypatch.setattr(exports, "url", binary_url)
    races.test_portability_export_rechecks_after_observed_wait(
        request,
        settings,
        monkeypatch,
        False,
        "generate" if transport == "generate" else "download",
        change,
    )
