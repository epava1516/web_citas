"""Private content observations for the finite, owned access scenario.

This module does not certify coverage. Unknown formats and unclassified sources
remain pending; only the existing independently reviewed application package can
be issued. Callers must encrypt returned originals, which can contain secrets.
"""
import base64
import hashlib
import json
import os
import time
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.safety.rights import fingerprint
from apps.safety.rights_exports import canonical
from scripts.owned_scenario_inventory import bounded_process_output, hash_regular_file

MAX_BYTES = 32 * 1024 * 1024


def _digest(value):
    return fingerprint(canonical(value))


def _encoded(value):
    return base64.b64encode(value).decode("ascii")


def process_inputs():
    """Effective settings, not an inference from the parent runner environment."""
    from django.db import connection

    return {
        "database": {key: str(connection.settings_dict[key]) for key in ("ENGINE", "NAME", "HOST", "PORT")},
        "media_root": str(settings.MEDIA_ROOT),
        "storage": settings.MEDIA_STORAGE_PROVIDER,
        "mail_backend": settings.EMAIL_BACKEND,
        "session_engine": settings.SESSION_ENGINE,
        "celery_eager": settings.CELERY_TASK_ALWAYS_EAGER,
        "broker": settings.CELERY_BROKER_URL,
        "logging": settings.LOGGING,
        "fixture_snapshots": os.environ.get("LOCAL_CI_FIXTURE_SNAPSHOTS") == "1",
        "origin_inputs": {name: str(getattr(settings, name, "")) for name in (
            "ACCESS_LOG_ORIGIN_BUNDLE", "ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE", "ACCESS_RESOURCE_ORIGIN_BUNDLE")},
    }


def register_scenario(runner_path, roots):
    """Register actual birth and inputs before seed/account/profile producers run.

    Nonempty stores are preserved in the baseline and are never called absent.
    Reusing a seeded database or selecting any retained bundle is rejected here;
    the separate historical scenario remains supported by its existing adapter.
    """
    from apps.core.models import User
    from scripts.owned_scenario_inventory import capture

    if User.objects.exists():
        raise ValueError("Register the finite scenario before creating its accounts")
    inputs = process_inputs()
    if inputs["fixture_snapshots"] or any(inputs["origin_inputs"].values()):
        raise ValueError("Finite seed scenario cannot inherit snapshots or retained bundles")
    observation = capture(runner_path, roots)
    for container in observation["containers"]:
        expected = {("tmpfs", "/var/lib/postgresql/data")} if "-pg-" in container["name"] else {("volume", "/data")}
        if any((mount["type"], mount["destination"]) not in expected for mount in container["mounts"]):
            raise ValueError("Finite scenario contains an undeclared external storage mount")
    project = Path(__file__).resolve().parents[1]
    if Path(runner_path).absolute().parent != project / "artifacts/local-ci" / observation["run"]:
        raise ValueError("Scenario registration requires its exact runner artifact root")
    producer_sources = ["scripts/run_local_ci.py", "scripts/owned_scenario_inventory.py",
                        "scripts/owned_rights_resource_content.py", "scripts/owned_rights_resource_census.py",
                        "tests/directory_snapshot.py",
                        "tests/test_discovery.py", "tests/test_rights_access_coverage_store.py",
                        "apps/core/management/commands/seed_demo.py",
                        "docs/evidencias/cr09-historicos-dependencias-matriz-20261014.json"]
    baseline_sources, baseline_pending = _runtime_originals(observation)
    dependency_manifest = json.loads((project / producer_sources[-1]).read_text())
    return {"registered_at": timezone.now().isoformat(), "inputs": inputs,
            "historical_origins": dependency_manifest["origins"],
            "baseline_sources": baseline_sources, "baseline_pending": baseline_pending,
            "baseline": observation,
            "producer_sources": {name: hashlib.sha256((project / name).read_bytes()).hexdigest()
                                 for name in producer_sources}}


def _redis_keys(client):
    keys = []
    total = 0
    for key in client.scan_iter(count=100):
        keys.append(key)
        total += len(key)
        if len(keys) > 10000 or total > MAX_BYTES:
            raise ValueError("Bounded Redis key census exceeded")
    if len(keys) != len(set(keys)):
        raise ValueError("Redis SCAN was unstable during capture")
    return sorted(keys)


def _redis_value(client, key, budget):
    # Bound the value on the owned Redis before sending its wire to Python.
    script = """
    local value = redis.call('DUMP', KEYS[1])
    if value and string.len(value) > tonumber(ARGV[1]) then
        return redis.error_reply('bounded owned census exceeded')
    end
    return {value or false, redis.call('TYPE', KEYS[1]).ok, redis.call('PTTL', KEYS[1])}
    """
    return client.eval(script, 1, key, max(0, budget))


@sensitive_variables()
def _runtime_originals(observation):
    """Read all actual configured local stores without deleting/consuming values."""
    import redis
    from django.contrib.sessions.models import Session
    from django.core import mail
    from django.core.cache import caches

    started_at = timezone.now().isoformat()
    sources = []
    pending = []
    sessions = []
    session_bytes = 0
    for row in Session.objects.order_by("session_key").iterator(chunk_size=100):
        value = {"key": row.session_key, "encoded": row.session_data,
                 "decoded": row.get_decoded(), "expires_at": row.expire_date.isoformat()}
        session_bytes += len(canonical(value).encode())
        if len(sessions) >= 10000 or session_bytes > MAX_BYTES:
            raise ValueError("Bounded session content census exceeded")
        sessions.append(value)
    sources.append({"reference": "django-db-sessions", "category": "unlinked_records",
                    "format": "django-signed-session", "content": sessions,
                    "producer": "django.contrib.sessions.models.Session"})
    if settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend":
        messages = []
        mail_bytes = 0
        for message in getattr(mail, "outbox", []):
            wire = message.message().as_bytes()
            mail_bytes += len(wire)
            if len(messages) >= 10000 or mail_bytes > MAX_BYTES:
                raise ValueError("Bounded retained mail content census exceeded")
            messages.append(_encoded(wire))
        sources.append({"reference": "django-locmem-mail", "category": "mail", "format": "mime-base64",
                        "content": messages, "producer": settings.EMAIL_BACKEND})
    else:
        pending.append("mail:unsupported_retained_mail_backend")
    backend = caches["default"]
    if type(backend).__module__ == "django.core.cache.backends.locmem":
        with backend._lock:
            if len(backend._cache) > 10000 or sum(len(value) for value in backend._cache.values()) > MAX_BYTES:
                raise ValueError("Bounded cache content census exceeded")
            content = [{"key": key, "value_base64": _encoded(value),
                        "expires_at": backend._expire_info.get(key)}
                       for key, value in sorted(backend._cache.items())]
        sources.append({"reference": "django-locmem-cache", "category": "caches", "format": "pickle-base64",
                        "content": content, "producer": type(backend).__module__ + "." + type(backend).__name__})
        if content:
            pending.append("caches:cache_value_producer_protocol_required")
    elif type(backend).__module__ == "django.core.cache.backends.dummy":
        sources.append({"reference": "django-dummy-cache", "category": "caches",
                        "format": "nonretaining-backend", "content": [],
                        "producer": type(backend).__module__ + "." + type(backend).__name__})
    else:
        pending.append("caches:unsupported_cache_backend")
    endpoint = next(row for row in observation["containers"] if "-redis-" in row["name"])
    port = int(endpoint["ports"]["6379/tcp"][0]["HostPort"])
    if port == 56379:
        raise ValueError("Normal Redis endpoint is forbidden")
    client = redis.Redis(host="127.0.0.1", port=port, socket_connect_timeout=3, socket_timeout=3)
    try:
        count = int(client.config_get("databases")["databases"])
        if not 1 <= count <= 64:
            raise ValueError("Unbounded Redis database configuration")
        databases = []
        total = 0
        total_records = 0
        for database in range(count):
            selected = redis.Redis(host="127.0.0.1", port=port, db=database,
                                   socket_connect_timeout=3, socket_timeout=3)
            try:
                keys = _redis_keys(selected)
                rows = []
                for key in keys:
                    read_start = time.monotonic()
                    value, kind, expiry = _redis_value(selected, key, MAX_BYTES - total)
                    if value is None:
                        raise ValueError("Redis source changed during capture")
                    total += len(key) + len(value)
                    total_records += 1
                    if total > MAX_BYTES or total_records > 10000:
                        raise ValueError("Bounded Redis content census exceeded")
                    repeated, repeated_kind, repeated_expiry = _redis_value(selected, key, len(value))
                    elapsed_ms = int((time.monotonic() - read_start) * 1000) + 10
                    expiry_stable = (expiry == repeated_expiry == -1 or
                                     expiry >= 0 and 0 <= expiry - repeated_expiry <= elapsed_ms)
                    if value != repeated or kind != repeated_kind or not expiry_stable:
                        raise ValueError("Redis value, type or expiry changed during capture")
                    rows.append({"key_base64": _encoded(key), "dump_base64": _encoded(value),
                                 "type": kind.decode("ascii"), "pttl": expiry})
                if _redis_keys(selected) != keys:
                    raise ValueError("Redis key set changed during capture")
                databases.append({"database": database, "records": rows})
                if rows:
                    pending.append(f"caches:redis_db_{database}_producer_content_review_required")
            finally:
                selected.close()
        sources.append({"reference": "owned-redis-all-databases", "category": "caches",
                        "format": "redis-dump-base64", "content": databases,
                        "producer": {"container": endpoint["id"], "port": port}})
    finally:
        client.close()
    # Redis's own data directory is bounded to the owned container. Do not run
    # SAVE/BGSAVE, restore, clear databases or invoke normal Compose services.
    paths = bounded_process_output(["docker", "exec", endpoint["id"], "find", "/data", "-type", "f", "-print"])
    if paths["stderr"]:
        raise ValueError("Redis persistence listing was not clean")
    files = []
    for path in paths["stdout"].decode("utf-8").splitlines():
        if not path.startswith("/data/") or ".." in Path(path).parts or len(files) >= 100:
            raise ValueError("Unbounded Redis persistence path")
        files.append({"path": path, "content_scope": "requires existing retained-origin reader; not read by filename"})
    sources.append({"reference": "owned-redis-persistence", "category": "backups", "format": "redis-persistence-base64",
                    "content": files, "producer": {"container": endpoint["id"],
                    "configuration": observation["runtime_stores"]["owned_redis_persistence_configuration"]}})
    if files:
        pending.append("backups:redis_persistence_existing_reader_and_review_required")
    finished_at = timezone.now().isoformat()
    total_content = 0
    for source in sources:
        source["requirements"] = []
        if source["reference"] in {"django-db-sessions", "django-locmem-mail"}:
            source["requirements"].append("existing_copy_or_disclosure_review")
        if source["reference"] == "django-locmem-cache" and source["content"]:
            source["requirements"].append("typed_content_reader")
        if source["reference"] == "owned-redis-all-databases" and any(row["records"] for row in source["content"]):
            source["requirements"].append("typed_content_reader")
        if source["reference"] == "owned-redis-persistence" and source["content"]:
            source["requirements"].append("typed_content_reader")
        source["period"] = {"started_at": started_at, "finished_at": finished_at}
        total_content += len(canonical(source).encode())
        if total_content > MAX_BYTES:
            raise ValueError("Bounded aggregate runtime content census exceeded")
    return sources, pending


@sensitive_variables()
def capture_content(registration, runner_path, roots, *, seed_credentials):
    """Capture exact private originals and preserve every unsupported source."""
    from scripts.owned_scenario_inventory import capture

    inputs = process_inputs()
    project = Path(__file__).resolve().parents[1]
    if any(hashlib.sha256((project / name).read_bytes()).hexdigest() != digest
           for name, digest in registration["producer_sources"].items()):
        raise ValueError("Scenario producer sources changed after registration")
    if inputs != registration["inputs"]:
        raise ValueError("Effective scenario inputs changed after registration")
    observation = capture(runner_path, roots, seed_credentials=seed_credentials, capture_logs=True)
    if (observation["run"] != registration["baseline"]["run"]
            or observation["head"] != registration["baseline"]["head"]
            or observation["containers"] != registration["baseline"]["containers"]):
        # log_content_scope changes when originals are captured; compare actual
        # immutable identity below rather than permitting arbitrary differences.
        fields = ("name", "id", "image_id", "created", "ports", "mounts", "resource_limits", "log_driver")
        before = [{name: row[name] for name in fields} for row in registration["baseline"]["containers"]]
        after = [{name: row[name] for name in fields} for row in observation["containers"]]
        if (before != after or observation["run"] != registration["baseline"]["run"]
                or observation["head"] != registration["baseline"]["head"]):
            raise ValueError("Scenario producer identities changed after registration")
    if observation["roots"] != registration["baseline"]["roots"]:
        raise ValueError("Scenario roots changed after registration")
    temporary = Path(json.loads(Path(runner_path).read_text())["temporary"])
    sources, pending = _runtime_originals(observation)
    total = 0
    for item in observation["files"]:
        size, digest, content = hash_regular_file(temporary, item["relative_path"], MAX_BYTES - total,
                                                include_content=True)
        total += size
        if (size, digest) != (item["size"], item["sha256"]):
            raise ValueError("Observed file content changed before private content review")
        sources.append({"reference": "file:" + item["relative_path"], "category": "unlinked_records",
                        "format": "file-base64", "content": _encoded(content),
                        "producer": item,
                        "requirements": ["producer_association"] if item["subject_binding"] == "not_established"
                                        else ["associated_content_disclosure_review"]})
        if item["subject_binding"] == "not_established":
            pending.append("unlinked_records:unassociated_file:" + item["relative_path"])
    from apps.safety.crypto import unseal

    for origin in observation["log_origins"]:
        cipher_size, cipher_digest, ciphertext = hash_regular_file(
            Path(runner_path).parent, origin["archive"], MAX_BYTES - total, include_content=True, require_private=True)
        total += cipher_size
        if (cipher_digest != origin["publication"]["ciphertext_sha256"]
                or cipher_size != origin["publication"]["ciphertext_bytes"]):
            raise ValueError("Private log original changed")
        original = unseal(ciphertext.decode())
        sources.append({"reference": "container-log:" + origin["container_id"], "category": "logs",
                        "format": "docker-timestamped-streams", "content": original,
                        "producer": origin, "requirements": ["content_classification"]})
        pending.append("logs:producer_content_classification_required:" + origin["container_id"])
    # Runner artifacts are producers too. Read their exact current originals;
    # do not treat an output directory declaration as proof of empty retention.
    archive_names = {origin["archive"] for origin in observation["log_origins"]}
    artifact_root = Path(runner_path).absolute().parent
    for path in sorted(artifact_root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Runner artifact symlink requires separate provenance")
        relative = str(path.relative_to(artifact_root))
        if not path.is_file() or relative in archive_names:
            continue
        size, digest, content = hash_regular_file(artifact_root, relative, MAX_BYTES - total,
                                                include_content=True)
        total += size
        if len(sources) >= 10000:
            raise ValueError("Bounded source census exceeded")
        sources.append({"reference": "runner-artifact:" + relative,
                        "category": "unlinked_records", "format": "file-base64",
                        "content": _encoded(content), "producer": {"run": observation["run"],
                        "source": "scripts/run_local_ci.py", "sha256": digest},
                        "requirements": ["content_classification"]})
    # These are observations, never a no-link verdict for the 23 old captures.
    pending.append("historical_dependency_provenance_requires_independent_review")
    if sum(len(canonical(source).encode()) for source in sources) > MAX_BYTES:
        raise ValueError("Bounded aggregate private content census exceeded")
    return {"registration": registration, "observation": observation, "sources": sources,
            "pending": sorted(set(pending)), "captured_at": timezone.now().isoformat(),
            "content_digest": _digest(sources)}


@sensitive_variables()
def await_external_review(case, inventory, scope, material, author, reviewer, *, timeout=300):
    """Explicit isolated-scenario callback; never used by default regression.

    Root reads the private original envelope, performs independent semantic
    review, and publishes the encrypted response. A timeout or rejection cannot
    create a final response. This is an operator procedure, not an app audit.
    """
    from apps.safety.crypto import seal, unseal
    from scripts.owned_scenario_inventory import publish_private_archive

    if not 1 <= timeout <= 600:
        raise ValueError("External review timeout must be bounded to 1..600 seconds")
    if author.pk == reviewer.pk:
        raise ValueError("Application author and reviewer must be distinct")
    directory = Path(__file__).resolve().parents[1] / "artifacts/local-ci" / material["observation"]["run"]
    material_digest = _digest(material)
    scope_digest = _digest(scope)
    original_name = f"owned-review-originals-{inventory.pk}.encrypted"
    request_name = f"owned-review-request-{inventory.pk}.json"
    response_name = f"owned-review-response-{inventory.pk}.encrypted"
    original = {"case": str(case.pk), "inventory": inventory.pk, "author": author.pk,
                "application_reviewer": reviewer.pk, "scope": scope, "material": material}
    publication = publish_private_archive(directory, original_name, seal(original).encode())
    request = {"originals": original_name, "publication": publication, "response": response_name,
               "case": str(case.pk), "inventory": inventory.pk,
               "material_digest": material_digest, "scope_digest": scope_digest,
               "registration_digest": _digest(material["registration"]),
               "source_digests": {source["reference"]: _digest(source) for source in material["sources"]},
               "required_review": "External actual-content/provenance inspection; no automatic approval. Application review is separate.",
               "timeout_seconds": timeout,
               "resource_content_decisions": "If associated records are proposed, provide an exact map from fingerprint(content) to explicit content redaction/omission decisions. Raw inclusion is forbidden by the application."}
    publish_private_archive(directory, request_name, (canonical(request) + "\n").encode())
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            _, _, ciphertext = hash_regular_file(directory, response_name, MAX_BYTES,
                                                 include_content=True, require_private=True)
        except FileNotFoundError:
            time.sleep(0.25)
            continue
        response = unseal(ciphertext.decode("utf-8"))
        required = {"material_digest", "scope_digest", "source_reviews", "history_review"}
        if (set(response) not in (required, required | {"resource_content_decisions"})
                or response["material_digest"] != material_digest or response["scope_digest"] != scope_digest):
            raise ValueError("External review does not inspect this exact material and scope")
        result = (response["source_reviews"], response["history_review"])
        if "resource_content_decisions" in response:
            return (*result, response["resource_content_decisions"])
        return result
    raise TimeoutError("External actual-content review not received; scenario incomplete, never accepted")


@sensitive_variables()
def associated_content_records(source):
    """Exact permitted projections from observed producer relationships.

    This is a reader, not a disclosure decision. External reviewers select only
    pertinent rows; the application still performs its independent review.
    Credentials expose email only, with password/TOTP exclusions made explicit.
    """
    if not source["reference"].startswith("file:"):
        return []
    producer = source["producer"]
    result = []
    if producer.get("subject_binding") == "explicit_database_relation":
        for reference in producer["database_references"]:
            result.append({"subject_kind": "person", "subject_id": reference["person"],
                "created_at": reference["created_at"], "source_reference": None,
                "content": canonical({"format": "file-base64", "field": reference["field"],
                                      "bytes_base64": source["content"], "sha256": producer["sha256"]})})
    elif producer.get("subject_binding") == "explicit_seed_producer_mapping":
        from apps.core.management.commands.seed_demo import NAMES

        body = json.loads(base64.b64decode(source["content"], validate=True))
        if (body.get("synthetic_only") is not True
                or len(producer["account_subjects"]) != len(NAMES)
                or set(body["accounts"]) != set(NAMES)):
            raise ValueError("Observed synthetic credential producer protocol changed")
        for name, subject in zip(NAMES, producer["account_subjects"], strict=True):
            result.append({"subject_kind": "account", "subject_id": str(subject),
                "created_at": producer["account_subject_created_at"][str(subject)], "source_reference": None,
                "content": canonical({"email": body["accounts"][name]["email"],
                                      "excluded_capability_fields": ["password", "totp_secret"]})})
    return result
