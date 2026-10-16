"""Observe owned CI resources; inventories never attest recipient coverage."""
import hashlib
import json
import os
import selectors
import stat
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


def capture(runner_path, roots, *, seed_credentials=None, capture_logs=False):
    runner_path = Path(runner_path)
    runner = json.loads(runner_path.read_text())
    run = runner["id"]
    ancestor = os.getpid()
    for _ in range(32):
        if ancestor == runner["pid"]:
            break
        data = Path(f"/proc/{ancestor}/stat").read_text()
        ancestor = int(data[data.rfind(")") + 2:].split()[1])
    else:
        raise RuntimeError("Inventory must execute inside its own live CI runner")
    data = Path(f"/proc/{runner['pid']}/stat").read_text()
    if int(data[data.rfind(")") + 2:].split()[19]) != runner["start_ticks"]:
        raise RuntimeError("Runner process identity changed")
    temporary = Path(runner["temporary"]).resolve(strict=True)
    if temporary.parent != Path("/tmp") or not temporary.name.startswith("web-modelos-local-ci-"):
        raise RuntimeError("Unrecognized disposable resource root")
    containers = []
    redis_port = None
    for service in ["pg", "redis"]:
        name = f"web-modelos-ci-{service}-{run}"
        if name not in runner["containers"]:
            raise RuntimeError("Container missing from runner inventory")
        info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
        if not info["State"]["Running"] or info["Config"]["Labels"].get("web-modelos-local-ci-run") != run:
            raise RuntimeError("Container identity mismatch")
        if service == "pg":
            verify_database_endpoint(info)
        else:
            bindings = info["NetworkSettings"]["Ports"].get("6379/tcp") or []
            if len(bindings) != 1 or bindings[0]["HostIp"] != "127.0.0.1":
                raise RuntimeError("Redis inventory endpoint is not exclusive loopback")
            redis_port = int(bindings[0]["HostPort"])
        mounts = []
        for mount in info["Mounts"]:
            row = {"type": mount["Type"], "destination": mount["Destination"],
                   "volume_name": mount.get("Name"), "read_write": mount["RW"]}
            if mount["Type"] == "volume":
                volume = json.loads(subprocess.check_output(
                    ["docker", "volume", "inspect", mount["Name"]], text=True))[0]
                if volume["Name"] != mount["Name"]:
                    raise RuntimeError("Owned volume identity changed")
                row["volume_created"] = volume["CreatedAt"]
                row["volume_driver"] = volume["Driver"]
            mounts.append(row)
        containers.append({"name": name, "id": info["Id"], "image_id": info["Image"],
                           "created": info["Created"], "ports": info["NetworkSettings"]["Ports"],
                           "resource_limits": {key: info["HostConfig"][key] for key in
                                               ("Memory", "MemorySwap", "NanoCpus", "CpusetCpus", "PidsLimit")},
                           "log_driver": info["HostConfig"]["LogConfig"]["Type"],
                           "log_content_scope": "not_captured; subject association pending",
                           "mounts": mounts})
    log_origins = []
    if capture_logs:
        expected = Path(__file__).resolve().parents[1] / "artifacts" / "local-ci" / run
        if runner_path.absolute().parent != expected:
            raise RuntimeError("Log archive directory differs from own runner artifact root")
        for container in containers:
            started_at = datetime.now(timezone.utc).isoformat()
            command = ["docker", "logs", "--timestamps", "--until", started_at, container["id"]]
            streams = bounded_process_output(command)
            finished_at = datetime.now(timezone.utc).isoformat()
            from apps.safety.crypto import seal
            archive = {"container_id": container["id"], "run": run,
                       "capture_started_at": started_at, "capture_finished_at": finished_at,
                       "until": started_at,
                       "streams": {key: value.decode("utf-8", errors="strict")
                                   for key, value in streams.items()}}
            destination = runner_path.parent / (container["name"] + "-logs-" + uuid.uuid4().hex + ".encrypted")
            ciphertext = seal(archive).encode()
            publication = publish_private_archive(destination.parent, destination.name, ciphertext)
            container["log_content_scope"] = "captured_encrypted_original; subject association pending"
            log_origins.append({"container_id": container["id"], "archive": destination.name,
                                "capture_started_at": started_at, "capture_finished_at": finished_at,
                                "until": started_at, "command": command, "publication": publication,
                                "streams": {key: {"bytes": len(value),
                                                  "sha256": hashlib.sha256(value).hexdigest()}
                                            for key, value in streams.items()},
                                "subject_binding": "not_established",
                                "scope": "Own live container logs at capture; no interleaving or historical exhaustiveness"})
    files = []
    seen = set()
    total_bytes = 0
    for declared in roots:
        root = Path(declared).resolve(strict=True)
        if not root.is_relative_to(temporary):
            raise RuntimeError("Resource root is outside the disposable scenario")
        for path in sorted(root.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise RuntimeError("Symlink needs separate resource classification")
            if not stat.S_ISREG(mode) or path in seen:
                continue
            seen.add(path)
            size, digest = hash_regular_file(temporary, path.relative_to(temporary),
                                             128 * 1024 * 1024 - total_bytes)
            total_bytes += size
            if len(files) >= 10000:
                raise RuntimeError("Bounded scenario inventory exceeded")
            files.append({"relative_path": str(path.relative_to(temporary)), "size": size,
                          "sha256": digest, "subject_binding": "not_established"})
    bind_media_files(files, temporary)
    if seed_credentials is not None:
        bind_seed_credentials(files, temporary, seed_credentials)
    return {"schema": "owned-scenario-observation-v1", "run": run, "head": runner["head"],
            "captured_at": datetime.now(timezone.utc).isoformat(), "containers": containers,
            "runtime_stores": observe_runtime_stores(redis_port), "log_origins": log_origins,
            "roots": [str(Path(root).relative_to(temporary)) for root in roots], "files": files,
            "fixture_snapshot_enabled": os.environ.get("LOCAL_CI_FIXTURE_SNAPSHOTS") == "1",
            "coverage_complete": False,
            "pending": ["subject association and inclusion/redaction decisions", "logs/mail/cache/backups outside declared roots", "historical import/restore provenance"],
            "scope": "Observed live own CI containers and declared fixture file roots only. Original hash verified; derivative hash is observation only. ORM references have no common snapshot guarantee. No content bodies in this manifest; optional encrypted log archives retain originals. No common capture cutoff or global exhaustiveness."}


def bind_media_files(files, temporary):
    """Bind observed bytes through current ORM references, never filename patterns."""
    from django.db import connection

    from apps.mediafiles.models import Photo

    if not connection.settings_dict["NAME"].startswith("test_promotion_gate_"):
        raise RuntimeError("Media provenance requires disposable test database")
    observed = {row["relative_path"]: row for row in files}
    for photo in Photo.objects.select_related("blob", "revision__listing__person"):
        person = photo.revision.listing.person
        for field in ["original", "derivative"]:
            stored = getattr(photo.blob, field)
            if not stored:
                continue
            path = Path(stored.path).resolve(strict=True)
            if not path.is_relative_to(temporary):
                raise RuntimeError("Referenced media is outside the disposable scenario")
            row = observed.get(str(path.relative_to(temporary)))
            if row is None:
                raise RuntimeError("Referenced media absent from declared inventory roots")
            if field == "original" and row["sha256"] != photo.blob.sha256:
                raise RuntimeError("Observed original differs from database content hash")
            row.setdefault("database_references", []).append({
                "photo": str(photo.pk), "blob": str(photo.blob_id),
                "revision": str(photo.revision_id), "person": str(person.pk),
                "account_subject": person.subject_id, "field": field,
                "created_at": photo.created_at.isoformat(),
                "source": "Photo.revision.listing.person; Photo.blob FileField path",
            })
            row["subject_binding"] = "explicit_database_relation"


def bind_seed_credentials(files, temporary, declared_path):
    """Explicit seed-demo recipe mapping; never export credential values."""
    from apps.core.management.commands import seed_demo
    from apps.core.models import User

    path = Path(declared_path).resolve(strict=True)
    if not path.is_relative_to(temporary):
        raise RuntimeError("Declared credentials are outside the disposable scenario")
    row = next((item for item in files if item["relative_path"] == str(path.relative_to(temporary))), None)
    if row is None or row["size"] > 65536:
        raise RuntimeError("Credential producer artifact missing or oversized")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != row["sha256"]:
        raise RuntimeError("Credential artifact changed after observation")
    body = json.loads(content)
    if body.get("synthetic_only") is not True or set(body) != {"synthetic_only", "password", "accounts"}:
        raise RuntimeError("Unexpected synthetic credential producer schema")
    if set(body["accounts"]) != set(seed_demo.NAMES):
        raise RuntimeError("Credential producer account set changed")
    subjects = []
    subject_created_at = {}
    for name in seed_demo.NAMES:
        # This is the producer's explicit key-to-username recipe, not a search
        # for matching text or UUIDs in arbitrary retained material.
        user = User.objects.get(username=f"fixture-v1-{name}")
        if body["accounts"][name]["email"] != user.email:
            raise RuntimeError("Credential producer mapping differs from current account")
        subjects.append(user.pk)
        subject_created_at[str(user.pk)] = user.date_joined.isoformat()
    row.update(account_subject_created_at=subject_created_at, subject_binding="explicit_seed_producer_mapping", account_subjects=subjects,
               producer_source="apps/core/management/commands/seed_demo.py",
               producer_sha256=hashlib.sha256(Path(seed_demo.__file__).read_bytes()).hexdigest(),
               excluded_fields=["password", "accounts.*.totp_secret"],
               retention_decision="pending_independent_review")


def verify_database_endpoint(info):
    from django.db import connection

    db = connection.settings_dict
    ports = info["NetworkSettings"]["Ports"].get("5432/tcp") or []
    matches = [p for p in ports if p["HostIp"] == "127.0.0.1" and p["HostPort"] == str(db["PORT"])]
    if db["HOST"] != "127.0.0.1" or not matches or not db["NAME"].startswith("test_promotion_gate_"):
        raise RuntimeError("Django database endpoint differs from owned PostgreSQL")


def hash_regular_file(root, relative, budget, *, include_content=False, require_private=False):
    """Read a stable bounded descriptor; optionally return the exact observed bytes.

    Content callers must keep these originals private: credential/capability and
    third party bytes are review material, never a recipient projection.
    """
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise RuntimeError("Unscoped inventory file path")
    root = Path(root).absolute()
    if ".." in root.parts:
        raise RuntimeError("Unscoped inventory root")
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    descriptor = None
    try:
        for part in root.parts[1:]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = following
        for part in relative.parts[:-1]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = following
        descriptor = os.open(relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError("Inventory file is not regular")
        if require_private and (before.st_uid != os.geteuid() or stat.S_IMODE(before.st_mode) != 0o600):
            raise RuntimeError("Private review file must be owned and mode 0600")
        count = 0
        digest = hashlib.sha256()
        chunks = [] if include_content else None
        while chunk := os.read(descriptor, 65536):
            count += len(chunk)
            if count > budget:
                raise RuntimeError("Bounded scenario inventory exceeded")
            digest.update(chunk)
            if chunks is not None:
                chunks.append(chunk)
        if include_content:
            # Equal-length writes can share filesystem timestamps. Verify the
            # captured private bytes against a second bounded descriptor read;
            # metadata equality alone does not establish content stability.
            os.lseek(descriptor, 0, os.SEEK_SET)
            verified_count = 0
            verified_digest = hashlib.sha256()
            while chunk := os.read(descriptor, 65536):
                verified_count += len(chunk)
                if verified_count > budget:
                    raise RuntimeError("Bounded scenario inventory exceeded")
                verified_digest.update(chunk)
            if verified_count != count or verified_digest.digest() != digest.digest():
                raise RuntimeError("Inventory file changed during observation")
        after = os.fstat(descriptor)
        def identity(value):
            return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        if identity(before) != identity(after) or count != before.st_size:
            raise RuntimeError("Inventory file changed during observation")
        result = (count, digest.hexdigest())
        return (*result, b"".join(chunks)) if chunks is not None else result
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory)


def observe_runtime_stores(redis_port):
    """Only observed metadata; counts never stand for complete retained coverage."""
    import redis
    from django.conf import settings
    from django.contrib.sessions.models import Session
    from django.core import mail
    from django.core.cache import caches
    from django.db import connection

    sessions = []
    for session in Session.objects.all():
        decoded = session.get_decoded()
        sessions.append({"key_sha256": hashlib.sha256(session.session_key.encode()).hexdigest(),
                         "auth_user_id": decoded.get("_auth_user_id"),
                         "expires_at": session.expire_date.isoformat(),
                         "scope": "Signed Django session subject field; authority/expiry not inferred"})
    backend = caches["default"]
    cache = {"backend": type(backend).__module__ + "." + type(backend).__name__,
             "content_scope": "not_inspected"}
    if cache["backend"] == "django.core.cache.backends.locmem.LocMemCache":
        with backend._lock:
            cache["observed_key_hashes"] = [hashlib.sha256(str(key).encode()).hexdigest()
                                            for key in backend._cache]
        cache["content_scope"] = "key metadata only; values and subject association pending"
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user")
        database, role = cursor.fetchone()
    client = redis.Redis(host="127.0.0.1", port=redis_port, db=0,
                         socket_connect_timeout=3, socket_timeout=3)
    try:
        keys = client.dbsize()
        persistence = {key: client.config_get(key)[key]
                       for key in ("save", "appendonly", "appendfilename", "dbfilename", "databases")}
    finally:
        client.close()
    return {"database": database, "database_role": role, "sessions": sessions,
            "cache": cache, "mail_backend": settings.EMAIL_BACKEND,
            "locmem_mail_count": len(mail.outbox) if hasattr(mail, "outbox") else None,
            "celery_eager": settings.CELERY_TASK_ALWAYS_EAGER,
            "owned_redis_db0_keys": keys,
            "owned_redis_persistence_configuration": persistence,
            "redis_history_scope": "Configuration observed only; files, other DBs and past snapshots not inspected",
            "limits": "Point observations; no log/archive/backup inspection, no cache value decoding, no global absence or recipient coverage claim."}


def bounded_process_output(command, *, max_bytes=8 * 1024 * 1024, timeout=15):
    """Drain both streams concurrently; kill/reap on overflow, timeout or error."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout
    total = 0
    try:
        with selectors.DefaultSelector() as selector:
            for key in streams:
                selector.register(getattr(process, key), selectors.EVENT_READ, key)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("Own log capture timed out")
                for event, _ in selector.select(remaining):
                    chunk = os.read(event.fileobj.fileno(), min(65536, max_bytes - total + 1))
                    if not chunk:
                        selector.unregister(event.fileobj)
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise RuntimeError("Own log capture exceeded byte budget")
                    streams[event.data].extend(chunk)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Own log capture timed out")
            if process.wait(timeout=remaining):
                raise RuntimeError("Own log capture command failed")
        return {key: bytes(value) for key, value in streams.items()}
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()
        process.stderr.close()


def publish_private_archive(directory, filename, ciphertext):
    """Anchor every directory component; publish complete bytes without replacement."""
    directory = Path(directory).absolute()
    if Path(filename).name != filename or filename in {"", ".", ".."}:
        raise RuntimeError("Archive filename must be a single component")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    temporary = ".private-" + uuid.uuid4().hex
    created = False
    try:
        for component in directory.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        metadata = os.fstat(descriptor)
        if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
            raise RuntimeError("Archive directory must be owned and not externally writable")
        target = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=descriptor)
        created = True
        with os.fdopen(target, "wb") as stream:
            stream.write(ciphertext)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, filename, src_dir_fd=descriptor, dst_dir_fd=descriptor, follow_symlinks=False)
        os.unlink(temporary, dir_fd=descriptor)
        created = False
        os.fsync(descriptor)
        return {"ciphertext_bytes": len(ciphertext), "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
                "directory_device": metadata.st_dev, "directory_inode": metadata.st_ino}
    finally:
        if created:
            os.unlink(temporary, dir_fd=descriptor)
        os.close(descriptor)
