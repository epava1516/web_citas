"""Adapter negatives use metadata doubles; real producer coverage is separate."""
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

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


@pytest.mark.django_db(transaction=True)
def test_finite_content_registration_precedes_seed_and_preserves_private_originals(request, settings, monkeypatch, tmp_path):
    """Owned real producers; no simulation/digest is upgraded to full coverage."""
    import base64
    import hashlib
    import json
    from pathlib import Path

    from apps.safety.crypto import unseal
    from scripts.owned_rights_resource_content import capture_content, register_scenario
    from scripts.owned_scenario_inventory import publish_private_archive

    artifact = request.config.getoption("--gate-timings-output", default=None)
    if not artifact:
        pytest.skip("Requires own disposable PostgreSQL/Redis runner")
    monkeypatch.setenv("LOCAL_CI_FIXTURE_SNAPSHOTS", "0")
    request.getfixturevalue("photo_environment")
    settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    runner = Path(artifact).parent / "runner.json"
    registration = register_scenario(runner, [tmp_path])
    assert registration["baseline"]["runtime_stores"]["database"].startswith("test_promotion_gate_")
    assert registration["inputs"]["fixture_snapshots"] is False
    assert not any(registration["inputs"]["origin_inputs"].values())
    request.getfixturevalue("directory")
    with pytest.raises(ValueError, match="before creating"):
        register_scenario(runner, [tmp_path])
    # Every effective process input is checked again, even when its parent
    # runner started with a sanitized environment.
    old_backend = settings.EMAIL_BACKEND
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    with pytest.raises(ValueError, match="inputs changed"):
        capture_content(registration, runner, [tmp_path], seed_credentials=tmp_path / "credentials.json")
    settings.EMAIL_BACKEND = old_backend
    material = capture_content(registration, runner, [tmp_path], seed_credentials=tmp_path / "credentials.json")
    credentials = next(item for item in material["sources"] if item["reference"].endswith("credentials.json"))
    exact = base64.b64decode(credentials["content"], validate=True)
    assert hashlib.sha256(exact).hexdigest() == credentials["producer"]["sha256"]
    assert exact == (tmp_path / "credentials.json").read_bytes()
    # Exact originals are retained encrypted; neither public observation nor
    # assertions render their values or encoded content.
    secret = json.loads(exact)
    public = json.dumps(material["observation"])
    assert secret["password"] not in public
    assert all(not row["totp_secret"] or row["totp_secret"] not in public
               for row in secret["accounts"].values())
    output = Path(artifact).parent
    filename = "owned-content-private.encrypted"
    publish_private_archive(output, filename, seal(material).encode())
    assert (output / filename).stat().st_mode & 0o777 == 0o600
    decoded = unseal((output / filename).read_text())
    assert decoded["content_digest"] == material["content_digest"]
    databases = next(item for item in material["sources"] if item["reference"] == "owned-redis-all-databases")
    count = int(material["observation"]["runtime_stores"]["owned_redis_persistence_configuration"]["databases"])
    assert [row["database"] for row in databases["content"]] == list(range(count))
    assert any(item["category"] == "logs" for item in material["sources"])
    assert "historical_dependency_provenance_requires_independent_review" in material["pending"]
    assert material["pending"]  # This test is observation, not close acceptance.


def reviewed_metadata_fixture(monkeypatch):
    """Mechanical review bindings only; no runtime coverage or semantic approval."""
    from apps.safety.rights import fingerprint
    from apps.safety.rights_exports import canonical
    from scripts import owned_rights_resource_content

    case, inventory, scope, _, records = metadata_fixture()
    inputs = {"fixture_snapshots": False, "origin_inputs": {"logs": "", "redis": "", "resources": ""}}
    monkeypatch.setattr(owned_rights_resource_content, "process_inputs", lambda: deepcopy(inputs))
    sources = [{"reference": category, "category": category, "content": [], "requirements": []}
               for category in ("logs", "mail", "caches", "backups", "unlinked_records")]
    sources[0].update(content={"stdout": "Known typed synthetic infrastructure event", "stderr": ""},
                      requirements=["content_classification"])
    registration = {"inputs": inputs, "seed_execution": {"branch": "seed", "inputs": inputs},
                    "historical_origins": [{"ciphertext_sha256": "metadata-origin-a"},
                                           {"ciphertext_sha256": "metadata-origin-b"}]}
    material = {"registration": registration, "observation": {}, "sources": sources,
                "pending": [], "captured_at": timezone.now().isoformat(),
                "content_digest": fingerprint(canonical(sources))}
    reviews = {row["reference"]: {"operator": "synthetic-author", "reviewer": "synthetic-independent-reviewer",
        "original_digest": fingerprint(canonical(row)),
        "decision": "excluded_nonpersonal" if row["reference"] == "logs" else "observed_absence",
        "reason": "Mechanical synthetic decision binding only; actual private originals require root semantic review.",
        "records": [], "records_digest": fingerprint(canonical([]))} for row in sources}
    reason = "Synthetic dependency provenance for mechanical binding; not exclusion evidence for any actual capture."
    history = {"registration_digest": fingerprint(canonical(registration)), "operator": "synthetic-author",
               "reviewer": "synthetic-independent-reviewer", "origins": {
        row["ciphertext_sha256"]: {"classification": "no_link", "reason": reason,
            "evidence": {key: reason for key in ("producer_inputs", "creation_and_mounts", "seed_execution",
                                                "effective_settings", "no_restore_or_import")}}
        for row in registration["historical_origins"]}}
    return case, inventory, scope, material, reviews, history


def test_exact_external_content_decision_resolves_only_its_typed_requirement(monkeypatch):
    from scripts.owned_rights_resource_census import reviewed_content_census

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    body = reviewed_content_census(case, inventory, scope, material, reviews, history)
    assert all(not category["pending"] for category in body["categories"].values())
    assert body["categories"]["logs"]["origins"][0]["records"] == []


@pytest.mark.parametrize("change", ["omitted_source", "same_actor", "changed_original", "nonempty_absence", "changed_seed"])
def test_reviewed_content_binding_rejects_omissions_and_mutations(monkeypatch, change):
    from apps.safety.rights import fingerprint
    from apps.safety.rights_exports import canonical
    from scripts.owned_rights_resource_census import reviewed_content_census

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    if change == "omitted_source":
        del reviews["logs"]
    elif change == "same_actor":
        reviews["logs"]["reviewer"] = reviews["logs"]["operator"]
    elif change == "changed_original":
        material["sources"][0]["content"]["stdout"] += " changed"
        material["content_digest"] = fingerprint(canonical(material["sources"]))
    elif change == "changed_seed":
        material["registration"]["seed_execution"]["branch"] = "restore_snapshot"
    else:
        material["sources"][1]["content"] = ["actually retained"]
        material["content_digest"] = fingerprint(canonical(material["sources"]))
        reviews["mail"]["original_digest"] = fingerprint(canonical(material["sources"][1]))
    with pytest.raises(ValueError):
        reviewed_content_census(case, inventory, scope, material, reviews, history)


@pytest.mark.parametrize("requirement", ["unknown_requirement", "typed_content_reader", "producer_association"])
def test_review_reason_cannot_waive_unknown_reader_or_association(monkeypatch, requirement):
    from apps.safety.rights import fingerprint
    from apps.safety.rights_exports import canonical
    from scripts.owned_rights_resource_census import reviewed_content_census

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    material["sources"][0]["requirements"].append(requirement)
    material["content_digest"] = fingerprint(canonical(material["sources"]))
    reviews["logs"]["original_digest"] = fingerprint(canonical(material["sources"][0]))
    body = reviewed_content_census(case, inventory, scope, material, reviews, history)
    assert body["categories"]["logs"]["pending"] == ["logs:" + requirement]


@pytest.mark.parametrize("change", ["omitted", "extra", "indeterminate", "registration"])
def test_historical_review_requires_exact_preregistered_manifest(monkeypatch, change):
    from scripts.owned_rights_resource_census import reviewed_content_census

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    if change == "omitted":
        del history["origins"]["metadata-origin-a"]
    elif change == "extra":
        history["origins"]["unregistered"] = deepcopy(history["origins"]["metadata-origin-a"])
    elif change == "indeterminate":
        history["origins"]["metadata-origin-a"]["classification"] = "indeterminate"
    else:
        history["registration_digest"] = "changed"
    body = reviewed_content_census(case, inventory, scope, material, reviews, history)
    assert all("historical_dependency_provenance" in row["pending"] for row in body["categories"].values())


@pytest.mark.parametrize("change", [None, "disclosure", "material_digest", "public_permissions", "timeout"])
def test_explicit_external_review_waits_for_private_exact_material_only(monkeypatch, tmp_path, change):
    import json

    from apps.safety.rights import fingerprint
    from apps.safety.rights_exports import canonical
    from scripts import owned_rights_resource_content as content
    from scripts.owned_scenario_inventory import publish_private_archive

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    material["observation"]["run"] = "unit-private-callback"
    project = tmp_path / "project"
    monkeypatch.setattr(content, "__file__", str(project / "scripts/content.py"))
    review_root = project / "artifacts/local-ci/unit-private-callback"
    review_root.mkdir(parents=True, mode=0o700)
    author, reviewer = SimpleNamespace(pk=101), SimpleNamespace(pk=102)
    writes = []

    def respond(_):
        request = json.loads((review_root / f"owned-review-request-{inventory.pk}.json").read_text())
        original = review_root / request["originals"]
        assert original.stat().st_mode & 0o777 == 0o600
        response = {"material_digest": request["material_digest"], "scope_digest": request["scope_digest"],
                    "source_reviews": reviews, "history_review": history}
        if change == "disclosure":
            response["resource_content_decisions"] = {
                "exact-content-digest": {"status": "omitted", "reason": "Private source capability excluded after exact content review"}
            }
        if change == "material_digest":
            response["material_digest"] = "different-private-original"
        if change == "timeout" or writes:
            return
        publish_private_archive(review_root, request["response"], seal(response).encode())
        if change == "public_permissions":
            (review_root / request["response"]).chmod(0o644)
        writes.append(True)

    monkeypatch.setattr(content.time, "sleep", respond)
    ticks = iter([0, 0.1, 0.2, 2])
    monkeypatch.setattr(content.time, "monotonic", lambda: next(ticks))
    if change in {None, "disclosure"}:
        actual = content.await_external_review(case, inventory, scope, material, author, reviewer, timeout=1)
        expected = (reviews, history)
        if change == "disclosure":
            expected = (*expected, {"exact-content-digest": {
                "status": "omitted", "reason": "Private source capability excluded after exact content review"}})
        assert fingerprint(canonical(actual)) == fingerprint(canonical(expected))
    else:
        error = TimeoutError if change == "timeout" else (RuntimeError if change == "public_permissions" else ValueError)
        with pytest.raises(error):
            content.await_external_review(case, inventory, scope, material, author, reviewer, timeout=1)


def test_unmapped_content_pending_cannot_disappear_in_a_review(monkeypatch):
    from scripts.owned_rights_resource_census import reviewed_content_census

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    material["pending"].append("new_actual_source_requires_reader")
    body = reviewed_content_census(case, inventory, scope, material, reviews, history)
    assert all("new_actual_source_requires_reader" in row["pending"] for row in body["categories"].values())


@pytest.mark.parametrize("change", [None, "reassociation", "capability_injection", "future_timestamp"])
def test_only_exact_producer_bound_credential_projection_is_eligible(monkeypatch, change):
    import base64
    import json

    from apps.core.management.commands.seed_demo import NAMES
    from apps.safety.rights import fingerprint
    from apps.safety.rights_exports import canonical
    from scripts.owned_rights_resource_census import reviewed_content_census
    from scripts.owned_rights_resource_content import associated_content_records

    case, inventory, scope, material, reviews, history = reviewed_metadata_fixture(monkeypatch)
    body = {"synthetic_only": True, "password": "synthetic-private-capability",
            "accounts": {name: {"email": f"{name}@example.invalid", "totp_secret": "synthetic-private-totp"}
                         for name in NAMES}}
    subjects = list(range(101, 101 + len(NAMES)))
    source = {"reference": "file:credentials.json", "category": "unlinked_records",
              "format": "file-base64", "content": base64.b64encode(json.dumps(body).encode()).decode(),
              "producer": {"subject_binding": "explicit_seed_producer_mapping", "account_subjects": subjects,
                           "account_subject_created_at": {str(subject): inventory.created_at.isoformat() for subject in subjects}},
              "requirements": ["associated_content_disclosure_review"]}
    rows = associated_content_records(source)
    safe = canonical(rows)
    assert body["password"] not in safe
    assert "synthetic-private-totp" not in safe
    row = rows[0]
    if change == "reassociation":
        row["subject_id"] = "unrelated-account"
    elif change == "capability_injection":
        row["content"] += " synthetic-private-capability"
    elif change == "future_timestamp":
        row["created_at"] = (inventory.created_at + timedelta(seconds=1)).isoformat()
    material["sources"][-1] = source
    material["content_digest"] = fingerprint(canonical(material["sources"]))
    review = reviews.pop("unlinked_records")
    review.update(original_digest=fingerprint(canonical(source)), decision="included", records=[row],
                  records_digest=fingerprint(canonical([row])))
    reviews[source["reference"]] = review
    if change is None:
        result = reviewed_content_census(case, inventory, scope, material, reviews, history)
        assert result["categories"]["unlinked_records"]["origins"][0]["records"] == [row]
    else:
        with pytest.raises(ValueError, match="producer association/projection"):
            reviewed_content_census(case, inventory, scope, material, reviews, history)
