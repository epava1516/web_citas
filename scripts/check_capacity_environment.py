"""Validate an owned, resource-limited capacity topology; never a capacity PASS."""

import argparse
import base64
import hashlib
import json
import os
import re
import resource
import shlex
import subprocess
import sys
import tarfile
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from capacity_artifacts import (
    ARCHIVE_MAX_BYTES,
    MAX_FILE_BYTES,
    ArchiveSink,
    parse_mountinfo,
    writable_storage,
    write_artifact,
)
from run_local_ci import hashes

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 * 1024
GIB = 1024 * MIB
ALLOCATIONS = {"pg": (100000, 1536), "redis": (25000, 512), "app": (275000, 6144)}
STORAGE_BUDGET_BYTES = 20 * GIB
MEMORY_PEAK_BUDGET_BYTES = 6 * GIB
LABEL = "web-modelos-capacity-run"
# The app image carries Compose labels of the normal project; owned containers must not match them.
COMPOSE_NEUTRAL = [item for key in ["project", "service", "version"]
                   for item in ("--label", f"com.docker.compose.{key}=")]
# Owned runtime users: no root, no capabilities, so Docker-managed /etc files stay unwritable.
CADDY_IMAGE = "caddy@sha256:881bbc60f9986d5ab8e7cfd6cf7e4ef3c9c0439fef2429d035d065577882f028"
OWNED_USERS = {"pg": "70:70", "redis": "999:1000", "objects": "10001:10001", "caddy": f"{os.getuid()}:{os.getgid()}"}
# The 16MiB shared-memory tmpfs is overfilled once per role to observe the kernel ENOSPC ceiling
# without inflating the measured cgroup peaks by the larger data tmpfs sizes.
FILL_PROBE = ("/dev/shm", 16)
OWNED_LOGS = {"pg": "/tmp/postgresql.log", "redis": "/tmp/redis.log", "caddy": "/tmp/caddy.log"}
PROBE = (
    'if touch /capacity-rootfs-probe 2>/dev/null; then echo rootfs=writable; else echo rootfs=readonly; fi; '
    'if (echo probe >> /etc/hosts) 2>/dev/null; then echo hosts=writable; else echo hosts=protected; fi; '
    'if err=$(dd if=/dev/zero of="$1/capacity-fill" bs=1048576 count="$2" 2>&1); '
    'then echo tmpfs=unbounded; elif echo "$err" | grep -q "No space left"; '
    'then echo tmpfs=enospc; else echo tmpfs=other; echo "$err"; fi; '
    'rm -f "$1/capacity-fill"'
)
PROBE_EXPECTED = ["rootfs=readonly", "hosts=protected", "tmpfs=enospc"]


def controller_self_probe(archive):
    """Observe kernel EROFS, RLIMIT_FSIZE and mount classification inside the owned controller."""
    try:
        Path("/capacity-rootfs-probe").write_text("x")
        rootfs = "writable"
    except OSError as error:
        rootfs = "readonly" if error.errno == 30 else f"errno-{error.errno}"
    child = subprocess.run(
        [sys.executable, "-c",
         "import resource,errno\n"
         "soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE)\n"
         "resource.setrlimit(resource.RLIMIT_FSIZE,(4096,hard))\n"
         "f=open('/tmp/capacity-rlimit-probe','wb')\n"
         "try:\n f.write(b'x'*8192); f.flush(); print('unbounded')\n"
         "except OSError as e: print('efbig' if e.errno==errno.EFBIG else 'errno-%d'%e.errno)\n"
         "finally:\n f.close()\n"
         "import os; os.unlink('/tmp/capacity-rlimit-probe')\n"],
        capture_output=True, text=True, timeout=30,
    )
    bounded, unbounded = writable_storage(parse_mountinfo(Path("/proc/self/mountinfo").read_text()),
                                          allowed={str(archive), "/run/docker.sock", "/var/run/docker.sock"})
    return {"rootfs": rootfs, "rlimit_fsize_child": child.stdout.strip() or child.stderr[-500:],
            "writable_tmpfs_bytes": bounded, "unbounded_writable": unbounded}


def parse_options(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", action="store_true", help="Execute small case instrumentation only")
    parser.add_argument("--diagnose", action="store_true", help="SQL attribution during small-case preparation")
    parser.add_argument("--fixture-target", action="store_true", help="Validate full-sized synthetic data only")
    parser.add_argument("--selection-tcp", action="store_true", help="Measure target-sized selection page TCP only")
    parser.add_argument("--selection-concurrent", action="store_true", help="Two independent target TCP cases; requires --selection-tcp")
    parser.add_argument("--selection-gunicorn", action="store_true", help="Real two-worker Gunicorn; requires concurrent selection")
    parser.add_argument("--selection-profile", action="store_true", help="Extra profiled requests; requires Gunicorn")
    parser.add_argument("--database-heavy", action="store_true", help="Rebalance same4CPU budget to PG1.5/app2.25; requires Gunicorn")
    parser.add_argument("--selection-complete", action="store_true", help="All31pages and20fresh approvals; requires balanced Gunicorn")
    parser.add_argument("--delivery-complete", action="store_true", help="Complete native target delivery; requires balanced Gunicorn")
    parser.add_argument("--delivery-profile", action="store_true", help="Diagnostic stage profiles of one target case; requires balanced Gunicorn")
    parser.add_argument("--delivery-profile-full", action="store_true", help="Diagnostic single-case flow to downloads with stage profiles; requires --delivery-profile")
    parser.add_argument("--source-profile", action="store_true", help="Diagnostic whole-source cost attribution; same allocation as --delivery-profile, which it requires")
    parser.add_argument("--owned-controller", action="store_true", help="Require launcher-enforced controller and whole owned budget")
    parser.add_argument("--object-delivery", action="store_true", help="Real private RustFS and Caddy proxy in the same owned budget; requires owned complete delivery")
    parser.add_argument("--preflight-only", action="store_true", help="Verify owned object/proxy/worker topology only; never run capacity fixtures")
    parser.add_argument("--diagnostic-baseline-capture", action="store_true")
    parser.add_argument("--diagnostic-baseline-use", type=Path)
    parser.add_argument("--diagnostic-baseline-key", type=Path)
    args = parser.parse_args(argv)
    baseline = args.diagnostic_baseline_capture or args.diagnostic_baseline_use
    if baseline:
        if (args.diagnostic_baseline_capture and args.diagnostic_baseline_use
            or not args.diagnostic_baseline_key or not args.owned_controller
            or not args.object_delivery or not args.delivery_profile_full
            or not args.delivery_profile or args.delivery_complete or args.preflight_only
            or args.selection_complete or args.source_profile):
            parser.error("Baseline requires exclusive complete diagnostic mode and private key; never acceptance")
    elif args.diagnostic_baseline_key:
        parser.error("Baseline key requires diagnostic baseline mode")
    if args.preflight_only and not (args.object_delivery and args.owned_controller):
        parser.error("--preflight-only requires --object-delivery and --owned-controller")
    workload = (args.control, args.diagnose, args.fixture_target, args.selection_tcp, args.selection_concurrent,
                args.selection_gunicorn, args.selection_profile, args.database_heavy, args.selection_complete,
                args.delivery_complete, args.delivery_profile, args.delivery_profile_full, args.source_profile)
    if args.preflight_only and any(workload):
        parser.error("--preflight-only is exclusive with every workload/profile flag")
    if args.object_delivery and not (args.owned_controller and (args.delivery_complete or args.delivery_profile_full or args.preflight_only)):
        parser.error("--object-delivery requires --owned-controller and --delivery-complete, --delivery-profile-full or --preflight-only")
    if args.delivery_profile_full and (not args.delivery_profile or args.source_profile):
        parser.error("--delivery-profile-full requires --delivery-profile without --source-profile")
    if args.source_profile and not args.delivery_profile:
        parser.error("--source-profile requires --delivery-profile")
    if args.delivery_profile and (args.delivery_complete or args.selection_complete or args.selection_profile
                                  or not (args.selection_gunicorn and args.database_heavy)):
        parser.error("--delivery-profile requires --selection-gunicorn --database-heavy and no other completion mode")
    if args.delivery_complete and (args.selection_complete or args.selection_profile):
        parser.error("--delivery-complete is exclusive with selection completion/profiling")
    if args.delivery_complete and not (args.selection_gunicorn and args.database_heavy):
        parser.error("--delivery-complete requires --selection-gunicorn --database-heavy")
    if args.selection_complete and not (args.selection_gunicorn and args.database_heavy):
        parser.error("--selection-complete requires --selection-gunicorn --database-heavy")
    if args.database_heavy and not args.selection_gunicorn:
        parser.error("--database-heavy requires --selection-gunicorn")
    allocations = dict(ALLOCATIONS)
    if args.database_heavy:
        allocations.update(pg=(150000, 1536), app=(225000, 6144))
    if args.delivery_complete or args.delivery_profile:
        allocations.update(pg=(150000, 3072), app=(225000, 4608))
    if args.owned_controller:
        allocations.update(redis=(20000, 384))
    if args.object_delivery:
        allocations = {"pg": (150000, 3072), "redis": (10000, 384), "app": (175000, 3968),
                       "objects": (50000, 512), "caddy": (10000, 128)}
    if args.selection_profile and not args.selection_gunicorn:
        parser.error("--selection-profile requires --selection-gunicorn")
    if args.selection_gunicorn and not args.selection_concurrent:
        parser.error("--selection-gunicorn requires --selection-concurrent")
    if args.selection_concurrent and not args.selection_tcp:
        parser.error("--selection-concurrent requires --selection-tcp")
    if args.selection_tcp and (args.control or args.diagnose or args.fixture_target):
        parser.error("--selection-tcp is exclusive")
    if args.fixture_target and (args.control or args.diagnose):
        parser.error("--fixture-target is exclusive with --control/--diagnose")
    if args.diagnose and not args.control:
        parser.error("--diagnose requires --control")
    if args.diagnostic_baseline_key:
        args.diagnostic_baseline_key = args.diagnostic_baseline_key.absolute()
    if args.diagnostic_baseline_use:
        args.diagnostic_baseline_use = args.diagnostic_baseline_use.absolute()
    return args, allocations, parser


def main():
    args, allocations, parser = parse_options()
    run_id = os.environ.get("CAPACITY_RUN_ID") if args.owned_controller else None
    if run_id is not None and not re.fullmatch(r"\d{8}-\d{6}-[a-f0-9]{8}", run_id):
        parser.error("Invalid owned run identifier")
    run_id = run_id or time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "-" + uuid.uuid4().hex[:8]
    prefix = "web-modelos-capacity-" + run_id
    output = ROOT / "artifacts/capacity-environment" / run_id
    if args.owned_controller:
        # Only the launcher-created archive file is writable durable storage for the controller.
        archive = output / "artifacts.tar"
        if os.environ.get("CAPACITY_ARCHIVE") != str(archive):
            parser.error("Owned archive path differs from run identifier")
        sink = ArchiveSink(archive)
        emit = sink.write
    else:
        output.mkdir(parents=True)
        archive, sink = None, None

        def emit(name, text):
            return write_artifact(output, name, text)
    before = None
    report = {
        "id": run_id,
        "result": "ERROR",
        "scope": "Owned topology readiness only; not capacity, browser, N3 or storage budget proof.",
        "allocations": allocations,
        "steps": [],
        "controls": {},
        "cleanup": {},
        "artifacts": {},
        "images": {},
        "container_images": {},
        "kernel_probes": {},
        "writable_tmpfs_bytes": {},
    }
    if args.owned_controller:
        report["controller_name"] = os.environ["CAPACITY_CONTROLLER_NAME"]
    baseline_header = None
    if args.diagnostic_baseline_use:
        try:
            from cryptography.exceptions import InvalidTag
            from diagnostic_baseline_archive import Reader
            from diagnostic_baseline_codec import key, metadata
            with Reader(args.diagnostic_baseline_use) as source:
                baseline_header = metadata(source, key(args.diagnostic_baseline_key))
                if (not isinstance(baseline_header, dict)
                    or not isinstance(baseline_header.get("objects"), dict)
                    or not isinstance(baseline_header["objects"].get("keyring"), str)
                    or not isinstance(baseline_header["objects"].get("active_key"), str)):
                    raise ValueError("Baseline authenticated header shape invalid")
        except (ValueError, OSError, KeyError, TypeError, tarfile.TarError, InvalidTag):
            baseline_header = None
            report["baseline"] = "CACHE_REJECTED"
    containers = []
    network = prefix + "-net"
    network_attempted = False
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "LANG"}}

    private_values = set()
    private_names = ("RIGHTS_OBJECT_KEYS", "RIGHTS_OBJECT_SECRET_KEY", "POSTGRES_PASSWORD", "RIGHTS_DELIVERY_PROXY_SECRET", "RUSTFS_SECRET_KEY")

    def scrub(text):
        for value in private_values:
            text = text.replace(value, "<private>")
            text = text.replace(json.dumps(value)[1:-1], "<private>")
        return text

    def run(command, label, check=True):
        for item in command:
            if isinstance(item, str) and "=" in item and item.split("=", 1)[0] in private_names:
                private_values.add(item.split("=", 1)[1])
        start = time.monotonic()
        timeout = ((9000 if args.delivery_complete or args.delivery_profile_full else
                    5400 if args.selection_complete or args.delivery_profile else 600)
                   if args.selection_tcp and label == "control-pytest" else 180)
        if args.preflight_only and label == "control-pytest":
            # Small generation observes up to180s in addition to real fixture setup,
            # worker startup and teardown. This is a finite diagnostic, never a new SLA.
            timeout = 360
        safe_command = ["<private>" if isinstance(value, str) and any(token in value for token in
                        tuple(name + "=" for name in private_names)) else value
                        for value in command]
        step = {"label": label, "command": safe_command, "timeout_seconds": timeout}
        report["steps"].append(step)
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired as error:
            partial = "".join(part.decode(errors="replace") if isinstance(part, bytes) else part or ""
                              for part in (error.stdout, error.stderr))
            step.update(exit=None, timed_out=True, seconds=time.monotonic() - start)
            report["artifacts"][label + ".log"] = emit(label + ".log", scrub(partial[-MAX_FILE_BYTES // 2:]))
            raise
        step.update(exit=result.returncode, seconds=time.monotonic() - start)
        report["artifacts"][label + ".log"] = emit(label + ".log", scrub(result.stdout + result.stderr))
        if check and result.returncode:
            raise RuntimeError(f"{label} failed; see durable log")
        return result

    def absent(kind, name):
        """Exact-name inspect must fail with not-found; a filter returning nothing is not proof."""
        probe = run(["docker", kind, "inspect", "--format", "{{.Id}}", name], "absent-" + name, check=False)
        text = (probe.stdout + probe.stderr).lower()
        return probe.returncode != 0 and ("no such" in text or "not found" in text)

    def container(role, image, extra, command):
        name = prefix + "-" + role
        containers.append(name)  # Cleanup even if Docker partially creates then fails.
        quota, memory = allocations[role]
        owned = []
        if args.owned_controller:
            owned = ["--read-only", "--log-driver", "none", "--cap-drop=ALL",
                     "--security-opt=no-new-privileges", "--shm-size", str(16 * MIB)]
            if role in OWNED_USERS:
                owned += ["--user", OWNED_USERS[role]]
        else:
            owned = ["--log-driver", "local", "--log-opt", "max-size=4m", "--log-opt", "max-file=1",
                     "--log-opt", "compress=false"]
        run(
            ["docker", "run", "--pull=never", "-d", "--name", name, "--label", f"{LABEL}={run_id}",
             *COMPOSE_NEUTRAL,
             "--network", network, "--network-alias", role,
             "--cpus", str(quota / 100000), "--memory", str(memory * MIB),
             "--memory-swap", str(memory * MIB), "--pids-limit", "256",
             *owned, *extra, image, *command], "start-" + role,
        )
        controls = run(
            ["docker", "exec", name, "cat", "/sys/fs/cgroup/cpu.max",
             "/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory.swap.max"], "controls-" + role,
        ).stdout.splitlines()
        if controls != [f"{quota} 100000", str(memory * MIB), "0"]:
            raise RuntimeError(f"Unverified effective limits: {role}")
        report["controls"][role] = controls
        report["container_images"][role] = run(
            ["docker", "inspect", "--format", "{{.Image}}", name], "image-of-" + role).stdout.strip()
        if report["container_images"][role] != report["images"][image]:
            raise RuntimeError(f"Container image differs from inspected image: {role}")
        if args.owned_controller:
            bounded, unbounded = writable_storage(parse_mountinfo(
                run(["docker", "exec", name, "cat", "/proc/self/mountinfo"], "mounts-" + role).stdout))
            if unbounded:
                raise RuntimeError(f"Unbounded writable mounts in {role}: {unbounded}")
            report["writable_tmpfs_bytes"][role] = bounded
            point, size = FILL_PROBE
            if bounded.get(point) != size * MIB:
                raise RuntimeError(f"Probe tmpfs differs from declared size: {role}")
            observed = run(["docker", "exec", name, "sh", "-c", PROBE, "probe", point, str(size + 1)],
                           "kernel-probe-" + role).stdout.splitlines()
            report["kernel_probes"][role] = observed
            if observed != PROBE_EXPECTED:
                raise RuntimeError(f"Kernel storage controls not observed: {role}")
        return name

    try:
        before = hashes()
        report["artifacts"]["source-hashes.json"] = emit("source-hashes.json", json.dumps(before, indent=2))
        report["source_manifest_sha256"] = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
        if args.owned_controller:
            controller_controls = [Path("/sys/fs/cgroup/" + name).read_text().strip()
                                   for name in ["cpu.max", "memory.max", "memory.swap.max"]]
            if controller_controls != ["5000 100000", str(128 * MIB), "0"]:
                raise RuntimeError("Owned controller kernel quotas unavailable")
            if resource.getrlimit(resource.RLIMIT_FSIZE) != (ARCHIVE_MAX_BYTES, ARCHIVE_MAX_BYTES):
                raise RuntimeError("Controller kernel file ceiling unavailable")
            report["controls"]["controller"] = controller_controls
            probe = controller_self_probe(archive)
            report["kernel_probes"]["controller"] = probe
            if probe["rootfs"] != "readonly" or probe["rlimit_fsize_child"] != "efbig" or probe["unbounded_writable"]:
                raise RuntimeError("Controller kernel storage controls not observed")
            report["writable_tmpfs_bytes"]["controller"] = probe["writable_tmpfs_bytes"]
            if sum(quota for quota, _ in allocations.values()) + 5000 != 400000:
                raise RuntimeError("Aggregate CPU reservation differs from4CPU")
            if sum(memory for _, memory in allocations.values()) + 128 != 8192:
                raise RuntimeError("Aggregate RAM reservation differs from8GiB")
        report["head"] = run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], "git-head").stdout.strip()
        interpreter = (ROOT / ".venv/bin/python3").resolve()
        report["interpreter"] = {"path": str(interpreter),
                                 "sha256": hashlib.sha256(interpreter.read_bytes()).hexdigest()}
        object_image = "rustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c"
        images = ["postgres:17-alpine", "redis:7.4-alpine", "web-modelos-app:latest"]
        if args.object_delivery:
            images += [object_image, CADDY_IMAGE]
        for image in images:
            report["images"][image] = run(["docker", "image", "inspect", "--format", "{{.Id}}", image],
                                          "image-" + re.sub(r"[^a-zA-Z0-9_-]", "_", image.split(":")[0])).stdout.strip()
        network_attempted = True
        run(["docker", "network", "create", "--internal", "--label", f"{LABEL}={run_id}", network], "network")
        owned_pg = ["--tmpfs", "/var/run/postgresql:size=16777216,uid=70,gid=70",
                    "--tmpfs", "/tmp:size=16777216,uid=70,gid=70"] if args.owned_controller else []
        pg = container(
            "pg", "postgres:17-alpine",
            ["--tmpfs", "/var/lib/postgresql/data:size=" + str(2 ** 31 if args.delivery_complete or args.delivery_profile else 2 ** 30)
             + (",uid=70,gid=70,mode=0700" if args.owned_controller else ""),
             *owned_pg,
             "-e", "POSTGRES_USER=ci", "-e", "POSTGRES_PASSWORD=ci-synthetic",
             "-e", "POSTGRES_DB=capacity_ci"],
            ["postgres", "-c", "logging_collector=on", "-c", "log_directory=/tmp",
             "-c", "log_filename=postgresql.log", "-c", "log_rotation_size=0"] if args.owned_controller else [],
        )
        container("redis", "redis:7.4-alpine",
                  ["--tmpfs", "/data:size=16777216,uid=999,gid=1000",
                   "--tmpfs", "/tmp:size=16777216,uid=999,gid=1000"] if args.owned_controller else [],
                  ["redis-server", "--save", "", "--appendonly", "no", "--maxmemory", "268435456",
                   *(["--logfile", OWNED_LOGS["redis"]] if args.owned_controller else [])])
        python_root = Path.home() / ".local/share/uv/python"
        if not python_root.is_dir():
            raise RuntimeError("Current uv interpreter root missing")
        object_env, delivery_mount = [], []
        if args.object_delivery:
            delivery_volume = prefix + "-delivery"
            run(["docker", "volume", "create", "--label", f"{LABEL}={run_id}", "--driver", "local",
                 "--opt", "type=tmpfs", "--opt", "device=tmpfs", "--opt",
                 f"o=size=536870912,uid={os.getuid()},gid={os.getgid()},mode=0750", delivery_volume], "delivery-volume")
            delivery_mount = ["--mount", f"type=volume,src={delivery_volume},dst=/srv/delivery"]
            object_env = ["-e", "RIGHTS_OBJECT_STORAGE_ENABLED=1", "-e", "RIGHTS_PROXY_DELIVERY_ENABLED=1",
                          "-e", "RIGHTS_OBJECT_ENDPOINT=http://objects:9000", "-e", "RIGHTS_OBJECT_REGION=us-east-1",
                          "-e", "RIGHTS_OBJECT_BUCKET=capacity-private", "-e", "RIGHTS_OBJECT_ACCESS_KEY=capacity-synthetic",
                          "-e", "RIGHTS_OBJECT_SECRET_KEY=capacity-synthetic-private-secret",
                          "-e", "RIGHTS_OBJECT_ACTIVE_KEY=" + (baseline_header["objects"]["active_key"] if baseline_header else "capacity-v1"), "-e",
                          "RIGHTS_OBJECT_KEYS=" + (baseline_header["objects"]["keyring"] if baseline_header else json.dumps({"capacity-v1": base64.b64encode(os.urandom(32)).decode()})),
                          "-e", "RIGHTS_DELIVERY_ROOT=/srv/delivery", "-e", "RIGHTS_DELIVERY_GENERATION=" + run_id,
                          "-e", "RIGHTS_DELIVERY_PROXY_SECRET=capacity-synthetic-proxy-secret-32-bytes"]
            container("objects", object_image,
                      ["--tmpfs", "/data:size=1073741824,uid=10001,gid=10001",
                       "--tmpfs", "/logs:size=16777216,uid=10001,gid=10001",
                       "-e", "RUSTFS_ACCESS_KEY=capacity-synthetic",
                       "-e", "RUSTFS_SECRET_KEY=capacity-synthetic-private-secret",
                       "-e", "RUSTFS_CONSOLE_ENABLE=false"], [])
            # Reuse the verified production route, with an HTTP-only isolated listener.
            route = (ROOT / "Caddyfile").read_text().split("    @delivery path", 1)[1].split("    @static path", 1)[0]
            caddy_config = "{\n admin off\n auto_https off\n}\n:8080 {\n    @delivery path" + route + "    respond 404\n}\n"
            container("caddy", CADDY_IMAGE,
                      ["--tmpfs", f"/tmp:size=100663296,exec,uid={os.getuid()},gid={os.getgid()}",
                       "--tmpfs", f"/data:size=16777216,uid={os.getuid()},gid={os.getgid()}",
                       "--tmpfs", f"/config:size=16777216,uid={os.getuid()},gid={os.getgid()}",
                       "--mount", f"type=volume,src={delivery_volume},dst=/srv/delivery,readonly",
                       "-e", "RIGHTS_DELIVERY_PROXY_SECRET=capacity-synthetic-proxy-secret-32-bytes",
                       "--entrypoint", "sh"],
                      ["-c", "cp /usr/bin/caddy /tmp/caddy-runtime && "
                       "cmp -s /usr/bin/caddy /tmp/caddy-runtime && printf %s "
                       + shlex.quote(caddy_config) + " > /tmp/Caddyfile && "
                       "exec /tmp/caddy-runtime run --config /tmp/Caddyfile --adapter caddyfile "
                       "> /tmp/caddy.log 2>&1"])
        baseline_mounts = []
        if args.diagnostic_baseline_key:
            baseline_mounts += ["--mount", f"type=bind,src={args.diagnostic_baseline_key},dst={args.diagnostic_baseline_key},readonly"]
        if args.diagnostic_baseline_use:
            baseline_mounts += ["--mount", f"type=bind,src={args.diagnostic_baseline_use},dst={args.diagnostic_baseline_use},readonly"]
        app = container(
            "app", "web-modelos-app:latest",
            ["--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
             "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", str(ROOT),
             "--mount", f"type=bind,src={ROOT},dst={ROOT},readonly",
             "--mount", f"type=bind,src={python_root},dst={python_root},readonly",
             "--tmpfs", f"/tmp:size=1073741824,uid={os.getuid()},gid={os.getgid()}",
             *delivery_mount, *object_env, *baseline_mounts,
             "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "DJANGO_SETTINGS_MODULE=config.settings",
             "-e", "DB_HOST=pg", "-e", "DB_PORT=5432", "-e", "POSTGRES_DB=capacity_ci",
             "-e", "POSTGRES_USER=ci", "-e", "POSTGRES_PASSWORD=ci-synthetic",
             "-e", "REDIS_URL=redis://redis:6379/0", "--entrypoint", str(ROOT / ".venv/bin/python3")],
            ["-c", "import time; time.sleep(" + str(10000 if args.delivery_complete or args.delivery_profile_full else 6000 if args.selection_complete or args.delivery_profile else 1800) + ")"],
        )
        if args.object_delivery:
            bootstrap = ("import time; from apps.safety.object_storage.factory import repository; "
                         "repo=repository()\n"
                         "for attempt in range(120):\n"
                         " try:\n  repo.client.create_bucket(Bucket=repo.bucket); repo.validate_bucket(); break\n"
                         " except Exception:\n  if attempt ==119: raise\n  time.sleep(.5)\n")
            run(["docker", "exec", app, str(ROOT / ".venv/bin/python3"), "-c", bootstrap], "object-bootstrap")
            report["object_delivery"] = {"enabled": True, "generation": run_id,
                "readiness": "Actual S3 create_bucket and fresh validate; Caddy readiness checked by server client",
                "scope": "Synthetic own objects/proxy; no assumption512MiB sufficient; OOM invalidates run"}
        if args.owned_controller:
            report["owned_storage_ceiling_bytes"] = (
                sum(sum(points.values()) for points in report["writable_tmpfs_bytes"].values())
                + ARCHIVE_MAX_BYTES
                + (args.diagnostic_baseline_use.stat().st_size if args.diagnostic_baseline_use else 0)
                + (args.diagnostic_baseline_key.stat().st_size if args.diagnostic_baseline_key else 0))
            report["storage_scope"] = (
                "Kernel-enforced writable ceiling: every writable tmpfs reported by each container's mountinfo "
                "(RAM-backed, also inside memory peaks) plus the single RLIMIT_FSIZE-capped artifact archive. "
                "Root filesystems read-only and Docker logs disabled, observed by probes. Pre-existing images, "
                "read-only sources/interpreter and Docker daemon metadata are infrastructure, not run storage.")
            if report["owned_storage_ceiling_bytes"] > STORAGE_BUDGET_BYTES:
                raise RuntimeError("Owned storage ceiling exceeds20GiB")
        for attempt in range(30):
            ready = run(["docker", "exec", pg, "pg_isready", "-U", "ci", "-d", "capacity_ci"],
                        "pg-ready-" + str(attempt), check=False)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Own PG readiness timed out")
        # Explicit current source, migrations, private synthetic database and broker.
        probe = (
            "import django,json,tempfile; django.setup(); "
            "from django.core.management import call_command; "
            "from django.db import connection; import redis; "
            "call_command('migrate',interactive=False,verbosity=0); call_command('check'); "
            "cursor=connection.cursor(); cursor.execute('select version(),current_database()'); "
            "row=cursor.fetchone(); "
            "assert row[1]=='capacity_ci'; "
            "assert redis.Redis(host='redis').ping(); "
            "f=tempfile.TemporaryFile(dir='/tmp'); f.write(b'synthetic-media'); f.seek(0); "
            "assert f.read()==b'synthetic-media'; f.close(); "
            "print(json.dumps({'postgres':row[0],'database':row[1],'redis_ping':True,"
            "'migrations_applied':True,'temporary_media_io':True,'django':django.get_version()}))"
        )
        run(["docker", "exec", app, str(ROOT / ".venv/bin/python3"), "-c", probe], "django-probe")
        if args.object_delivery:
            mounts = {}
            for role in ("app", "caddy"):
                rows = json.loads(run(["docker", "inspect", "--format", "{{json .Mounts}}", prefix + "-" + role],
                                      "delivery-mount-" + role).stdout)
                match = [row for row in rows if row.get("Destination") == "/srv/delivery"]
                if len(match) != 1 or match[0].get("Type") != "volume" or match[0].get("Name") != delivery_volume:
                    raise RuntimeError("Delivery mount differs from own shared volume")
                if match[0].get("RW") != (role == "app"):
                    raise RuntimeError("Delivery mount permissions differ from appRW/CaddyRO")
                mounts[role] = match[0]
            run(["docker", "exec", app, str(ROOT / ".venv/bin/python3"), "-c",
                 "from pathlib import Path; Path('/srv/delivery/preflight-write').write_bytes(b'own')"], "delivery-write-app")
            write = run(["docker", "exec", prefix + "-caddy", "sh", "-c",
                         "printf denied > /srv/delivery/preflight-write"], "delivery-write-caddy", check=False)
            if write.returncode == 0 or "Read-only file system" not in write.stderr:
                raise RuntimeError("Caddy readonly mount not enforced by kernel")
            run(["docker", "exec", app, str(ROOT / ".venv/bin/python3"), "-c",
                 "from pathlib import Path; p=Path('/srv/delivery/preflight-write'); assert p.read_bytes()==b'own'; p.unlink()"], "delivery-write-clean")
            report["object_delivery"]["mounts"] = mounts
            volume = json.loads(run(["docker", "volume", "inspect", delivery_volume], "delivery-volume-inspect").stdout)[0]
            if volume.get("Options", {}).get("type") != "tmpfs" or "size=536870912" not in volume.get("Options", {}).get("o", ""):
                raise RuntimeError("Delivery own volume lacks bounded tmpfs")
            owned_volumes = run(["docker", "volume", "ls", "--format", "{{.Name}}", "--filter", f"label={LABEL}={run_id}"], "delivery-volume-count").stdout.split()
            if owned_volumes != [delivery_volume]:
                raise RuntimeError("Unexpected own volume census")
            report["object_delivery"]["owned_volume_count"] = len(owned_volumes)
            report["object_delivery"]["volume"] = volume
        if args.control or args.fixture_target or args.selection_tcp or args.preflight_only:
            settings_source = (
                "from config.settings import *\n"
                "CAPACITY_ENVIRONMENT_VERIFIED = True\n"
                f"CAPACITY_BASELINE_CAPTURE = {args.diagnostic_baseline_capture!r}\n"
                f"CAPACITY_BASELINE_INPUT = {str(args.diagnostic_baseline_use or '')!r}\n"
                f"CAPACITY_BASELINE_KEY = {str(args.diagnostic_baseline_key or '')!r}\n"
                f"CAPACITY_PREFLIGHT_ONLY = {args.preflight_only!r}\n"
                f"CAPACITY_OBJECT_DELIVERY = {args.object_delivery!r}\n"
                "MEDIA_ROOT = '/tmp/capacity-media'\n"
                f"CAPACITY_SQL_DIAGNOSE = {args.diagnose!r}\n"
                f"CAPACITY_SELECTION_GUNICORN = {args.selection_gunicorn!r}\n"
                f"CAPACITY_SELECTION_PROFILE = {args.selection_profile or args.delivery_profile!r}\n"
                f"CAPACITY_DELIVERY_PROFILE = {args.delivery_profile!r}\n"
                f"CAPACITY_DELIVERY_PROFILE_FULL = {args.delivery_profile_full!r}\n"
                f"CAPACITY_SELECTION_COMPLETE = {args.selection_complete!r}\n"
                f"CAPACITY_DELIVERY_COMPLETE = {args.delivery_complete!r}\n"
                "DATABASES['default']['TEST'] = {'NAME': 'test_capacity_ci'}\n"
            )
            run(["docker", "exec", app, str(ROOT / ".venv/bin/python3"), "-c",
                 "from pathlib import Path; Path('/tmp/capacity_settings.py').write_text(" +
                 repr(settings_source) + ")"], "control-settings")
            result = run(
                ["docker", "exec", "-e", f"PYTHONPATH=/tmp:{ROOT}",
                 "-e", "DJANGO_SETTINGS_MODULE=capacity_settings", app,
                 str(ROOT / ".venv/bin/python3"), "-m", "pytest", "-q", "--tb=short",
                 "-o", "DJANGO_SETTINGS_MODULE=capacity_settings", "-o", "junit_family=xunit1",
                 "-p", "no:cacheprovider", "--basetemp=/tmp/capacity-pytest",
                 "--junitxml=/tmp/capacity-control.xml",
                 "tests/test_capacity_object_preflight.py" if args.preflight_only else
                 "tests/test_capacity_delivery_complete.py" if args.delivery_complete else
                 "tests/test_capacity_source_profile.py" if args.source_profile else
                 "tests/test_capacity_delivery_profile.py" if args.delivery_profile else
                 "tests/test_capacity_selection_concurrent_tcp.py" if args.selection_concurrent else
                 "tests/test_capacity_selection_tcp.py" if args.selection_tcp else
                 "tests/test_capacity_target_fixture.py" if args.fixture_target else "tests/test_capacity_case_control.py"],
                "control-pytest", check=False,
            )
            if args.diagnostic_baseline_capture and result.returncode == 0:
                # Ciphertext only; never use run(capture_output=True) for the
                # complete binary snapshot in the128MiB controller.
                transfer = subprocess.Popen(["docker", "exec", app, "cat", "/tmp/diagnostic-baseline.bin"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
                parts = []
                try:
                    number = 0
                    while True:
                        block = bytearray()
                        while len(block) < 8 * MIB:
                            value = transfer.stdout.read(8 * MIB - len(block))
                            if not value:
                                break
                            block.extend(value)
                        if not block:
                            break
                        name = f"baseline.{number:04}.bin"
                        report["artifacts"][name] = sink.write_binary(name, bytes(block))
                        parts.append(name)
                        number += 1
                        if number > 32:
                            raise RuntimeError("Baseline fragment quota exceeded")
                    if transfer.wait(timeout=30) != 0 or not parts:
                        raise RuntimeError("Baseline ciphertext transfer failed")
                finally:
                    transfer.stdout.close()
                    if transfer.poll() is None:
                        transfer.terminate()
                        transfer.wait(timeout=5)
                report["artifacts"]["baseline.index.json"] = emit("baseline.index.json", json.dumps({"parts": parts}))
            junit = run(["docker", "exec", app, "cat", "/tmp/capacity-control.xml"],
                        "control-junit")
            report["artifacts"]["pytest.xml"] = emit("pytest.xml", junit.stdout)
            suites = list(ET.fromstring(junit.stdout).iter("testsuite"))
            report["junit"] = [suite.attrib for suite in suites]
            if args.preflight_only:
                properties = {item.attrib["name"]: item.attrib["value"] for suite in suites for item in suite.iter("property")}
                proof = json.loads(properties.get("object_delivery_preflight", "{}"))
                if not all(proof.get(name) is True for name in ("s3_aead", "s3_purge", "caddy_bytes", "caddy_replay_denied", "worker_purge", "beat_purge")):
                    raise RuntimeError("Requested object/proxy/worker preflight proof missing")
                report["object_delivery"]["preflight"] = proof
            if args.diagnose:
                properties = {item.attrib["name"]: item.attrib["value"]
                              for suite in suites for item in suite.iter("property")}
                if not json.loads(properties.get("preparation_sql_attribution", "{}")):
                    raise RuntimeError("Requested SQL diagnosis missing: INVALID instrument")
            if args.delivery_complete:
                properties = {item.attrib["name"]: item.attrib["value"]
                              for suite in suites for item in suite.iter("property")}
                measurements = json.loads(properties.get("delivery_measurements", "{}"))
                cases = measurements.get("cases", [])
                report["stage_violations"] = [row.get("violations", []) for row in cases]
                if (len(cases) == 2 and not measurements.get("errors")
                        and all("binary_download_p95" in row for row in cases)
                        and any(report["stage_violations"])):
                    # Every stage measured to the end and a limit was breached: valid FAIL, not ERROR.
                    report["result"] = "FAIL_DELIVERY_STAGE_LIMITS"
                    raise RuntimeError("Valid delivery stage limit breach; see stage_violations")
            if result.returncode or not suites or any(
                int(suite.attrib.get(key, 0)) for suite in suites
                for key in ("failures", "errors", "skipped")
            ) or sum(int(suite.attrib.get("tests", 0)) for suite in suites) != 1:
                raise RuntimeError("Small control did not pass exactly one required test")
            if args.preflight_only:
                report["result"] = "READY_NOT_CAPACITY"
            elif args.delivery_profile:
                properties = {item.attrib["name"]: item.attrib["value"]
                              for suite in suites for item in suite.iter("property")}
                if args.source_profile:
                    if not json.loads(properties.get("source_profile", "{}")).get("source_copy"):
                        raise RuntimeError("Requested source profile missing: INVALID instrument")
                elif not json.loads(properties.get("delivery_profile", "{}")).get("server_profiles"):
                    raise RuntimeError("Requested stage profiles missing: INVALID instrument")
                report["result"] = "PROFILE_DIAGNOSTIC_NOT_CAPACITY"
                if args.diagnostic_baseline_capture or args.diagnostic_baseline_use:
                    report["diagnostic_baseline"] = {"mode": "capture" if args.diagnostic_baseline_capture else "reuse-or-full-real-fallback", "acceptance_eligible": False}
            elif args.delivery_complete:
                properties = {item.attrib["name"]: item.attrib["value"]
                              for suite in suites for item in suite.iter("property")}
                measurements = json.loads(properties.get("delivery_measurements", "{}"))
                if len(measurements.get("cases", [])) != 2 or measurements.get("errors") or not all(
                    row.get("success") for row in measurements["cases"]
                ):
                    raise RuntimeError("Complete target delivery measurements missing")
                report["result"] = "DELIVERY_STAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3"
            elif args.selection_tcp:
                properties = {item.attrib["name"]: item.attrib["value"]
                              for suite in suites for item in suite.iter("property")}
                measurements = json.loads(properties.get("selection_tcp_measurements", "{}"))
                cases = measurements.get("cases", []) if args.selection_concurrent else [measurements]
                if len(cases) != (2 if args.selection_concurrent else 1) or any(len(case.get("samples", [])) != (620 if args.selection_complete else 20) for case in cases):
                    raise RuntimeError("Requested TCP measurements missing")
                report["result"] = "SELECTION_TCP_PASS_NOT_FULL_CAPACITY"
            elif args.fixture_target:
                properties = {item.attrib["name"]: item.attrib["value"]
                              for suite in suites for item in suite.iter("property")}
                if len(json.loads(properties.get("target_fixture_manifest", "[]"))) != 2:
                    raise RuntimeError("Requested target fixture manifest missing")
                report["result"] = "FIXTURE_VALID_NOT_CAPACITY"
            else:
                report["result"] = "CONTROL_PASS_NOT_TARGET_CAPACITY"
        else:
            report["result"] = "READY_NOT_CAPACITY"

    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        report["cgroup_memory"] = {}
        for role in allocations:
            name = prefix + "-" + role
            if name not in containers:
                continue
            try:
                observed = run(["docker", "exec", name, "cat", "/sys/fs/cgroup/memory.current",
                                "/sys/fs/cgroup/memory.peak", "/sys/fs/cgroup/memory.swap.peak",
                                "/sys/fs/cgroup/memory.events"], "memory-" + role, check=False)
                lines = observed.stdout.splitlines()
                events = dict(line.split() for line in lines[3:])
                if observed.returncode or len(lines) < 4:
                    raise RuntimeError("Memory counters unavailable")
                report["cgroup_memory"][role] = {
                    "current_bytes": int(lines[0]), "peak_bytes": int(lines[1]),
                    "swap_peak_bytes": int(lines[2]), "oom_kill": int(events.get("oom_kill", -1))}
            except Exception as exc:
                report.setdefault("memory_collection_errors", {})[role] = str(exc)
        report["controller_peak_rss_bytes"] = next(int(line.split()[1]) * 1024
            for line in Path("/proc/self/status").read_text().splitlines() if line.startswith("VmHWM:"))
        report["host_cli_child_peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024
        report["memory_scope"] = (
            "Disjoint container cgroup peaks including cache, plus host controller/maximum CLI child RSS. "
            "CLI commands sequential; sum is conservative upper bound, not synchronous peak. "
            "Controller CPU/memory has no kernel quota; no global enforced capacity claim."
        )
        if args.owned_controller:
            try:
                report["controller_cgroup_peak_bytes"] = int(Path("/sys/fs/cgroup/memory.peak").read_text())
            except (OSError, ValueError) as exc:
                report.setdefault("memory_collection_errors", {})["controller"] = str(exc)
            report["owned_memory_upper_bound_bytes"] = (
                sum(item["peak_bytes"] for item in report["cgroup_memory"].values()) + 128 * MIB)
            report["memory_scope"] = (
                "Disjoint application/PG/Redis/optional objects+proxy cgroup peaks including cache and tmpfs, plus full128MiB "
                "controller kernel ceiling including all CLI children/final collection; conservative "
                "whole-owned-runtime upper bound, not synchronous peak. Host bootstrap/terminal collector and "
                "shared OS/daemon are infrastructure, outside timed workload.")
            complete = (set(report["cgroup_memory"]) == set(allocations)
                        and "controller_cgroup_peak_bytes" in report)
            swapped = any(item["swap_peak_bytes"] for item in report["cgroup_memory"].values())
            killed = any(item["oom_kill"] for item in report["cgroup_memory"].values())
            if not complete:
                report["global_memory_verdict"] = "NOT_PROVEN"
                if args.preflight_only:
                    report["result"] = "INVALID"
            elif swapped or killed:
                report["global_memory_verdict"] = "INVALID_SWAP_OR_OOM"
                report["result"] = "INVALID"
            elif report["owned_memory_upper_bound_bytes"] > MEMORY_PEAK_BUDGET_BYTES:
                report["global_memory_verdict"] = "NOT_PROVEN_UPPER_BOUND_ABOVE_6GIB"
            else:
                report["global_memory_verdict"] = "WITHIN_6GIB_UPPER_BOUND"
        for role, path in OWNED_LOGS.items():
            name = prefix + "-" + role
            if args.owned_controller and name in containers:
                try:
                    run(["docker", "exec", name, "cat", path], "server-log-" + role, check=False)
                except Exception as exc:
                    report.setdefault("log_collection_errors", {})[role] = str(exc)
        for name in reversed(containers):
            try:
                if not args.owned_controller:
                    run(["docker", "logs", name], "logs-" + name, check=False)
                removal = run(["docker", "rm", "-fv", name], "remove-" + name, check=False)
                gone = absent("container", name)
                report["cleanup"][name] = {"absent": gone, "removal_exit": removal.returncode}
                if not gone:
                    report["result"] = "ERROR"
            except Exception as exc:
                report["cleanup"][name] = {"error": str(exc)}
                report["result"] = "ERROR"
        if args.object_delivery and "delivery_volume" in locals():
            try:
                removal = run(["docker", "volume", "rm", delivery_volume], "remove-delivery-volume", check=False)
                gone = absent("volume", delivery_volume)
                report["cleanup"][delivery_volume] = {"absent": gone, "removal_exit": removal.returncode}
                if not gone:
                    report["result"] = "ERROR"
            except Exception as exc:
                report["cleanup"][delivery_volume] = {"error": str(exc)}
                report["result"] = "ERROR"
        if network_attempted:
            try:
                run(["docker", "network", "rm", network], "remove-network", check=False)
                gone = absent("network", network)
                report["cleanup"][network] = {"absent": gone}
                if not gone:
                    report["result"] = "ERROR"
            except Exception as exc:
                report["cleanup"][network] = {"error": str(exc)}
                report["result"] = "ERROR"
        try:
            labelled = run(["docker", "ps", "-a", "--format", "{{.Names}}", "--filter", f"label={LABEL}={run_id}"],
                           "labelled-containers", check=False)
            labelled_volumes = run(["docker", "volume", "ls", "--format", "{{.Name}}", "--filter", f"label={LABEL}={run_id}"],
                                   "labelled-volumes", check=False)
            labelled_networks = run(["docker", "network", "ls", "--format", "{{.Name}}",
                                     "--filter", f"label={LABEL}={run_id}"], "labelled-networks", check=False)
            # The owned controller itself carries the label until the launcher removes it.
            remaining = [item for item in labelled.stdout.split() + labelled_networks.stdout.split() + labelled_volumes.stdout.split()
                         if item != report.get("controller_name")]
            report["cleanup"]["labelled_remaining"] = remaining
            if labelled.returncode or labelled_networks.returncode or labelled_volumes.returncode or remaining:
                report["result"] = "ERROR"
        except Exception as exc:
            report["cleanup"]["labelled_remaining"] = {"error": str(exc)}
            report["result"] = "ERROR"
        try:
            report["sources_unchanged"] = before is not None and hashes() == before
        except Exception as exc:
            report["sources_unchanged"] = False
            report["source_hash_error"] = str(exc)
        if not report["sources_unchanged"]:
            report["result"] = "INVALID"
        emit("report.json", json.dumps(report, indent=2))
        if sink is not None:
            sink.close()
    print(json.dumps({"result": report["result"], "evidence": str(output)}))
    return 0 if report["result"] in {"READY_NOT_CAPACITY", "CONTROL_PASS_NOT_TARGET_CAPACITY", "FIXTURE_VALID_NOT_CAPACITY", "SELECTION_TCP_PASS_NOT_FULL_CAPACITY", "DELIVERY_STAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3",
                                               "PROFILE_DIAGNOSTIC_NOT_CAPACITY"} else 1


if __name__ == "__main__":
    sys.exit(main())
