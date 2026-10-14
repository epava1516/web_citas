"""Real producer artifacts are observed without declaring complete rights coverage."""
import json
from pathlib import Path

import pytest
from django.conf import settings
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.owned_scenario_inventory import capture

pytestmark = pytest.mark.django_db(transaction=True)


def test_seeded_fixture_resources_have_owned_provenance_and_pending_subject_binding(request, tmp_path, monkeypatch):
    artifact = request.config.getoption("--gate-timings-output", default=None)
    if not artifact:
        pytest.skip("Requires explicit disposable CI producer inventory")
    # This scenario observes actual producer artifacts, including credentials
    # outside MEDIA_ROOT, so it must execute the seed rather than restore a clone.
    monkeypatch.setenv("LOCAL_CI_FIXTURE_SNAPSHOTS", "0")
    request.getfixturevalue("directory")
    runner = Path(artifact).parent / "runner.json"
    manifest = capture(runner, [tmp_path, settings.MEDIA_ROOT], seed_credentials=tmp_path / "credentials.json")
    assert len(manifest["containers"]) == 2
    assert manifest["runtime_stores"]["database"].startswith("test_promotion_gate_")
    assert manifest["runtime_stores"]["owned_redis_db0_keys"] == 0
    assert manifest["runtime_stores"]["celery_eager"] is True
    assert any(item["relative_path"].endswith("credentials.json") for item in manifest["files"])
    media = [item for item in manifest["files"] if item.get("database_references")]
    assert media and all(item["subject_binding"] == "explicit_database_relation" for item in media)
    credentials = [item for item in manifest["files"] if item["relative_path"].endswith("credentials.json")]
    assert len(credentials) == 1 and credentials[0]["subject_binding"] == "explicit_seed_producer_mapping"
    assert len(credentials[0]["account_subjects"]) == 8
    assert credentials[0]["excluded_fields"] == ["password", "accounts.*.totp_secret"]
    assert manifest["coverage_complete"] is False and manifest["pending"]
    (Path(artifact).parent / "owned-scenario-inventory.json").write_text(json.dumps(manifest, indent=2))
    credential_values = json.loads((tmp_path / "credentials.json").read_text())
    exported = json.dumps(manifest)
    assert credential_values["password"] not in exported
    assert all(not value["totp_secret"] or value["totp_secret"] not in exported
               for value in credential_values["accounts"].values())
    metadata = json.loads(runner.read_text())
    original = next(item for item in media if any(
        ref["field"] == "original" for ref in item["database_references"]))
    path = Path(metadata["temporary"]) / original["relative_path"]
    previous = path.read_bytes()
    try:
        path.write_bytes(previous + b"synthetic-content-alteration")
        with pytest.raises(RuntimeError, match="Observed original differs"):
            capture(runner, [tmp_path, settings.MEDIA_ROOT], seed_credentials=tmp_path / "credentials.json")
    finally:
        path.write_bytes(previous)
