"""Adapter negatives use metadata doubles; real producer coverage is separate."""
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.safety.crypto import seal
from apps.safety.rights_access_delivery import retained_resource_records
from scripts.owned_rights_resource_census import build_census, scope_dependencies


def metadata_fixture():
    cutoff = timezone.now() - timedelta(seconds=1)
    case = SimpleNamespace(pk="unit-case", account_subject_id=101)
    inventory = SimpleNamespace(pk=12, source_digest="unit-source", created_at=cutoff)
    scope = {"sessions": [], "session_evidence": [], "queued_processing": [],
             "queue_evidence": [], "log_origins": {}, "mail_scope": {}}
    observation = {"schema": "owned-scenario-observation-v1", "coverage_complete": False,
                   "run": "unit-double-not-a-real-run", "captured_at": timezone.now().isoformat(),
                   "pending": ["unknown content"], "containers": [{"id": "unit-container"}],
                   "files": [{"sha256": "unit-hash"}]}
    records = [{"subject_kind": "account", "subject_id": "101", "created_at": cutoff.isoformat(),
                "content": "unit producer provenance only", "source_reference": None}]
    return case, inventory, scope, observation, records


def test_observed_adapter_binds_exact_scope_without_claiming_completeness(settings, tmp_path):
    case, inventory, scope, observation, records = metadata_fixture()
    original = deepcopy((observation, records))
    body = build_census(case, inventory, scope, observation, records)
    assert (observation, records) == original
    assert body["request"] == str(case.pk) and body["inventory"] == inventory.pk
    assert body["source"] == inventory.source_digest and body["cutoff"] == inventory.created_at.isoformat()
    dependencies = scope_dependencies(scope)
    assert body["dependencies"] == dependencies
    path = tmp_path / "census.encrypted"
    path.write_text(seal(body))
    path.chmod(0o600)
    settings.ACCESS_RESOURCE_ORIGIN_BUNDLE = str(path)
    result = retained_resource_records(case, None, inventory, dependencies, {"logs": {}, "mail": {}})
    assert result["configured"] is True
    assert result["groups"] and result["groups"][0]["data"]["content"] == records[0]["content"]
    assert all(any(item.startswith(category + ":") for item in result["pending"])
               for category in body["categories"])
    assert all(category["pending"] for category in body["categories"].values())
    # No input caller can discard the provider's unresolved scopes afterwards.
    records[0]["content"] = "changed caller record"
    assert body["categories"]["unlinked_records"]["origins"][0]["records"][0]["content"] != records[0]["content"]


@pytest.mark.parametrize("change", ["request", "inventory", "source", "cutoff", "dependencies", "records"])
def test_observed_adapter_rejects_changed_binding_or_record_digest(settings, tmp_path, change):
    case, inventory, scope, observation, records = metadata_fixture()
    body = build_census(case, inventory, scope, observation, records)
    if change == "request":
        body[change] = "different-case"
    elif change == "inventory":
        body[change] += 1
    elif change == "source":
        body[change] = "different-source"
    elif change == "cutoff":
        body[change] = (inventory.created_at - timedelta(seconds=1)).isoformat()
    elif change == "dependencies":
        body[change]["mail"] = "changed-scope"
    else:
        body["categories"]["unlinked_records"]["origins"][0]["records"][0]["content"] += " altered"
    path = tmp_path / "census.encrypted"
    path.write_text(seal(body))
    path.chmod(0o600)
    settings.ACCESS_RESOURCE_ORIGIN_BUNDLE = str(path)
    with pytest.raises(ValidationError, match="census unavailable"):
        retained_resource_records(case, None, inventory, scope_dependencies(scope), {"logs": {}, "mail": {}})


@pytest.mark.parametrize("change", ["empty_records", "claims_complete", "no_pending", "before_cutoff", "future_record"])
def test_observed_provider_rejects_empty_or_unbounded_scope(change):
    case, inventory, scope, observation, records = metadata_fixture()
    if change == "empty_records":
        records = []
    elif change == "claims_complete":
        observation["coverage_complete"] = True
    elif change == "no_pending":
        observation["pending"] = []
    elif change == "before_cutoff":
        observation["captured_at"] = (inventory.created_at - timedelta(seconds=1)).isoformat()
    else:
        records[0]["created_at"] = (inventory.created_at + timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError):
        build_census(case, inventory, scope, observation, records)


def test_observed_dependencies_include_configured_redis_history_only():
    _, _, scope, _, _ = metadata_fixture()
    assert "redis_history" not in scope_dependencies(scope)
    scope["redis_history"] = {"configured": True, "pending": ["actual contents unknown"]}
    before = scope_dependencies(scope)
    assert "redis_history" in before
    scope["redis_history"]["pending"].append("another required source")
    assert scope_dependencies(scope)["redis_history"] != before["redis_history"]


def test_observed_dependencies_do_not_erase_blocked_scope():
    _, _, scope, _, _ = metadata_fixture()
    scope["blocked"] = ["unsupported retained record"]
    with pytest.raises(ValueError, match="Blocked scope"):
        scope_dependencies(scope)
