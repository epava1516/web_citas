"""Real 8MiB threshold with synthetic retained revisions within normal field limits."""

import json
import time
import tracemalloc
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from django.db import transaction
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url

from apps.listings.models import Revision
from apps.safety.crypto import unseal
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record
from apps.safety.rights_portability_selection_store import save_selection
from scripts.reconstruct_rights_copy import reconstruct

pytestmark = pytest.mark.django_db(transaction=True)


def test_large_approved_history_uses_actual_8mib_transport(
    request, settings, monkeypatch, tmp_path, record_property
):
    original_ready = fixtures.ready
    description = ("Synthetic retained historical description. " * 200)[:6000]
    assert len(description) == 6000
    history_count = 1500

    def ready_with_history(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        person = result[-1]
        Revision.objects.bulk_create(
            [
                Revision(
                    listing=person.listing,
                    manager_version=person.manager_version,
                    title=f"Synthetic retained revision {index}",
                    description=description,
                )
                for index in range(history_count)
            ],
            batch_size=100,
        )
        return result

    monkeypatch.setattr(fixtures, "ready", ready_with_history)
    case, author, baseline, previous, person, _, receipt = fixtures.prepared_selection(
        request, settings, monkeypatch, False
    )
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    body = unseal(baseline.encrypted_selection)
    chosen = [
        {"row": row_reference("revisions", index, revision), "fields": ["/description"]}
        for index, revision in enumerate(source["revisions"])
        if revision["description"] == description
    ]
    assert len(chosen) == history_count
    body["selection"]["revisions"] = chosen
    reason = "Approve synthetic retained history for real-size private transport"
    row = save_selection(
        author,
        case.pk,
        case.version,
        baseline.assessment_review_id,
        uuid4(),
        baseline.version,
        reason,
        body["selection"],
        field_evidence=body["field_evidence"],
    )
    reviewer = previous.action.actor
    record(reviewer, case.pk, case.version, row.pk, uuid4(), reason)
    decision, _ = record(
        reviewer, case.pk, case.version, row.pk, uuid4(), reason, "review", "approved"
    )
    key, version = uuid4(), case.version
    tracemalloc.start()
    started = time.perf_counter()
    try:
        export = generate(author, case.pk, version, row.pk, decision.pk, key, reason)
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    record_property("generation_seconds", elapsed)
    record_property("generation_python_peak_bytes", peak)
    assert generate(author, case.pk, version, row.pk, decision.pk, key, reason).pk == export.pk
    public = Client()
    response = public.post(url(receipt, export), {"key": uuid4()})
    assert response.status_code == 200
    manifest = response.json()
    assert manifest["schema"] == "rights-data-manifest-v1"
    assert manifest["size"] > 8 * 1024 * 1024
    assert len(manifest["data_parts"]) >= 2
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(response.content)
    for part in manifest["data_parts"]:
        response = public.post(url(receipt, export) + f"part/{part['id']}/", {"key": uuid4()})
        assert response.status_code == 200 and len(response.content) <= 8 * 1024 * 1024
        (tmp_path / f"rights-data-part-{part['position']}.zip").write_bytes(response.content)
    output = tmp_path / "reconstructed.json"
    assert reconstruct(manifest_path, tmp_path, output) == manifest["size"]
    delivered = json.loads(output.read_bytes())
    assert delivered["datasets"]["revisions"] == [
        {"fields": {"/description": description}} for _ in range(history_count)
    ]
    assert "field_evidence" not in delivered
    case.refresh_from_db()
    assert case.version == version + 1 and case.status == "reviewing"
    record_property("document_bytes", manifest["size"])
    record_property("historical_revisions", history_count)
