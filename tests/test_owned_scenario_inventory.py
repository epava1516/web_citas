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
    manifest = capture(runner, [tmp_path, settings.MEDIA_ROOT], seed_credentials=tmp_path / "credentials.json", capture_logs=True)
    assert len(manifest["log_origins"]) == 2
    import hashlib

    from apps.safety.crypto import unseal
    for origin in manifest["log_origins"]:
        archive = Path(artifact).parent / origin["archive"]
        assert archive.stat().st_mode & 0o777 == 0o600
        ciphertext = archive.read_bytes()
        assert len(ciphertext) == origin["publication"]["ciphertext_bytes"]
        assert hashlib.sha256(ciphertext).hexdigest() == origin["publication"]["ciphertext_sha256"]
        original = unseal(ciphertext.decode())
        assert original["until"] == origin["until"]
        assert original["capture_started_at"] <= original["capture_finished_at"]
        from cryptography.fernet import InvalidToken
        with pytest.raises(InvalidToken):
            unseal(ciphertext[:-1].decode())
        assert original["container_id"] == origin["container_id"]
        for stream, content in original["streams"].items():
            assert hashlib.sha256(content.encode()).hexdigest() == origin["streams"][stream]["sha256"]
        assert origin["subject_binding"] == "not_established"
    assert len(manifest["containers"]) == 2
    assert all("log_driver" in item for item in manifest["containers"])
    assert all("volume_name" in mount for item in manifest["containers"] for mount in item["mounts"])
    assert set(manifest["runtime_stores"]["owned_redis_persistence_configuration"]) == {
        "save", "appendonly", "appendfilename", "dbfilename", "databases"}
    assert "not inspected" in manifest["runtime_stores"]["redis_history_scope"]
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
    # Captured originals are not a reviewed, request-bound retained census.
    from types import SimpleNamespace

    from django.core.exceptions import ValidationError
    from django.utils import timezone

    from apps.safety.rights_access_delivery import retained_resource_records

    observed = manifest["log_origins"][0]
    monkeypatch.setattr(settings, "ACCESS_RESOURCE_ORIGIN_BUNDLE",
                        str(Path(artifact).parent / observed["archive"]))
    case = SimpleNamespace(pk="unreviewed-own-scenario",
                           account_subject_id=credentials[0]["account_subjects"][0])
    scoped_inventory = SimpleNamespace(pk=1, source_digest="unreviewed-observation",
                                       created_at=timezone.now())
    with pytest.raises(ValidationError, match="census unavailable"):
        retained_resource_records(case, None, scoped_inventory, {}, {})
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
