"""Real producer artifacts are observed without declaring complete rights coverage."""
import json
from pathlib import Path

import pytest
from django.conf import settings
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.owned_scenario_inventory import capture

pytestmark = pytest.mark.django_db(transaction=True)


def test_seeded_fixture_resources_have_owned_provenance_and_pending_subject_binding(request, tmp_path):
    artifact = request.config.getoption("--gate-timings-output", default=None)
    if not artifact:
        pytest.skip("Requires explicit disposable CI producer inventory")
    request.getfixturevalue("directory")
    runner = Path(artifact).parent / "runner.json"
    manifest = capture(runner, [tmp_path, settings.MEDIA_ROOT])
    assert len(manifest["containers"]) == 2
    assert any(item["relative_path"].endswith("credentials.json") for item in manifest["files"])
    assert manifest["files"] and all(item["subject_binding"] == "not_established" for item in manifest["files"])
    assert manifest["coverage_complete"] is False and manifest["pending"]
    (Path(artifact).parent / "owned-scenario-inventory.json").write_text(json.dumps(manifest, indent=2))
