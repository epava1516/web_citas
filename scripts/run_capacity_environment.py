"""Launch the capacity controller under real Docker quotas, with owned durable output."""

import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import tarfile
import time
import uuid
from pathlib import Path

from capacity_artifacts import ARCHIVE_MAX_BYTES, MAX_FILE_BYTES
from check_capacity_environment import COMPOSE_NEUTRAL
from run_local_ci import hashes

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 ** 2
LABEL = "web-modelos-capacity-run"
TIMEOUT_SECONDS = 11500
LAUNCHER_FILES = {"controller.log", "launcher.json", "artifacts.tar"}


def host_tools():
    programs = {}
    for name in ["docker", "git"]:
        found = shutil.which(name)
        if found is None:
            raise SystemExit(f"Missing host tool: {name}")
        programs[name] = Path(found).resolve()
    libraries = {}
    for program in programs.values():
        result = subprocess.run(["ldd", str(program)], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[1] == "=>" and parts[2].startswith("/"):
                libraries[parts[0]] = Path(parts[2]).resolve()
            elif parts and parts[0].startswith("/"):
                libraries[Path(parts[0]).name] = Path(parts[0]).resolve()
    loader = next(name for name in libraries if name.startswith("ld-linux"))
    return programs, libraries, loader


def limit_client_log():
    # Kernel ceiling for controller.log, written by the Docker CLI child through its stdout.
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))


def extract(archive, output):
    """Copy simple regular members of the owned archive; tolerate a truncated tail."""
    receipts, problems = {}, []
    try:
        with tarfile.open(archive, mode="r:") as source:
            for member in source:
                if not member.isfile() or Path(member.name).name != member.name or member.name in LAUNCHER_FILES:
                    problems.append(f"rejected member: {member.name!r}")
                    continue
                data = source.extractfile(member).read()
                (output / member.name).write_bytes(data)
                receipts[member.name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    except (tarfile.TarError, OSError) as error:
        problems.append(f"{type(error).__name__}: {error}")
    return receipts, problems


def absent(docker, kind, name):
    probe = subprocess.run([docker, kind, "inspect", "--format", "{{.Id}}", name], capture_output=True, text=True)
    text = (probe.stdout + probe.stderr).lower()
    return probe.returncode != 0 and ("no such" in text or "not found" in text)


def main():
    run_id = time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "-" + uuid.uuid4().hex[:8]
    name = "web-modelos-capacity-" + run_id + "-controller"
    output = ROOT / "artifacts/capacity-environment" / run_id
    output.mkdir(parents=True)
    archive = output / "artifacts.tar"
    archive.touch(mode=0o600)
    before = hashes()
    programs, libraries, loader = host_tools()
    docker = str(programs["docker"])
    head = subprocess.run([str(programs["git"]), "-C", str(ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    python_root = Path.home() / ".local/share/uv/python"
    socket = Path("/var/run/docker.sock")
    bootstrap = f"""
import os, resource, runpy, sys
from pathlib import Path
root = Path({str(ROOT)!r})
tools = Path('/tmp/tools')
tools.mkdir()
loader = '/opt/host-tools/lib/{loader}'
for tool in ['docker', 'git']:
    wrapper = '#!/bin/sh\\nexec ' + loader + ' --library-path /opt/host-tools/lib /opt/host-tools/native/' + tool + ' "$@"\\n'
    (tools / tool).write_text(wrapper)
    (tools / tool).chmod(0o755)
os.environ['PATH'] = str(tools) + ':' + os.environ['PATH']
resource.setrlimit(resource.RLIMIT_FSIZE, ({ARCHIVE_MAX_BYTES}, {ARCHIVE_MAX_BYTES}))
sys.path.insert(0, str(root / 'scripts'))
sys.argv = [str(root / 'scripts/check_capacity_environment.py'), '--owned-controller', *{sys.argv[1:]!r}]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    command = [
        docker, "--host", "unix:///var/run/docker.sock", "run", "--pull=never",
        "--rm", "--sig-proxy=false", "--name", name, "--label", f"{LABEL}={run_id}", *COMPOSE_NEUTRAL,
        "--network", "none",
        "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--user", f"{os.getuid()}:{os.getgid()}", "--group-add", str(socket.stat().st_gid),
        "--cpus", "0.05", "--memory", str(128 * MIB), "--memory-swap", str(128 * MIB),
        "--pids-limit", "128", "--log-driver", "none", "--workdir", str(ROOT),
        "--mount", f"type=bind,src={ROOT},dst={ROOT},readonly",
        "--mount", f"type=bind,src={archive},dst={archive}",
        "--mount", f"type=bind,src={python_root},dst={python_root},readonly",
        "--mount", "type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock",
        "--tmpfs", f"/tmp:size=67108864,exec,uid={os.getuid()},gid={os.getgid()}",  # Tool wrappers.
        "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", f"HOME={Path.home()}",
        "-e", f"CAPACITY_RUN_ID={run_id}", "-e", f"CAPACITY_CONTROLLER_NAME={name}",
        "-e", f"CAPACITY_ARCHIVE={archive}",
    ]
    mounts = {f"native/{key}": path for key, path in programs.items()}
    mounts.update({f"lib/{key}": path for key, path in libraries.items()})
    for target, source in mounts.items():
        command += ["--mount", f"type=bind,src={source},dst=/opt/host-tools/{target},readonly"]
    command += ["--entrypoint", str(ROOT / ".venv/bin/python3"), "web-modelos-app:latest", "-c", bootstrap]
    report = {"id": run_id, "controller": name, "head": head, "command": command,
              "timeout_seconds": TIMEOUT_SECONDS,
              "source_manifest_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
              "scope": "Owned controller and all its CLI children constrained; host Docker bootstrap/"
                       "terminal collection and shared OS/daemon are infrastructure outside timed workload. "
                       "The Docker socket grants daemon API access regardless of bind mode; every resource is "
                       "named and labelled with this run identifier and removed by exact name.",
              "tools": {target: {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                  "bytes": source.stat().st_size} for target, source in mounts.items()}}
    print(f"owned-controller — {output}", flush=True)
    try:
        try:
            with (output / "controller.log").open("w") as log:
                process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=TIMEOUT_SECONDS, check=False, preexec_fn=limit_client_log)
            report["exit"] = process.returncode
        except subprocess.TimeoutExpired:
            report["exit"] = None
            report["timed_out"] = True
    finally:
        report["cleanup"] = {}
        for suffix in ["controller", "app", "redis", "pg"]:
            owned = "web-modelos-capacity-" + run_id + "-" + suffix
            subprocess.run([docker, "rm", "-fv", owned], capture_output=True)
            report["cleanup"][owned] = absent(docker, "container", owned)
        network = "web-modelos-capacity-" + run_id + "-net"
        subprocess.run([docker, "network", "rm", network], capture_output=True)
        report["cleanup"][network] = absent(docker, "network", network)
        labelled = subprocess.run([docker, "ps", "-a", "-q", "--filter", f"label={LABEL}={run_id}"],
                                  capture_output=True, text=True)
        networks = subprocess.run([docker, "network", "ls", "-q", "--filter", f"label={LABEL}={run_id}"],
                                  capture_output=True, text=True)
        report["cleanup"]["no_labelled_resources"] = (
            labelled.returncode == 0 and networks.returncode == 0
            and not labelled.stdout.strip() and not networks.stdout.strip())
        report["artifacts"], report["archive_problems"] = extract(archive, output)
        report["archive_bytes"] = archive.stat().st_size
        report["archive_within_ceiling"] = report["archive_bytes"] <= ARCHIVE_MAX_BYTES
        log_bytes = (output / "controller.log").stat().st_size
        report["controller_log"] = {"bytes": log_bytes, "within_ceiling": log_bytes <= MAX_FILE_BYTES,
                                    "sha256": hashlib.sha256((output / "controller.log").read_bytes()).hexdigest()}
        report["sources_unchanged"] = hashes() == before
        (output / "launcher.json").write_text(json.dumps(report, indent=2) + "\n")
    result = json.loads((output / "report.json").read_text()) if (output / "report.json").exists() else {}
    cleanup = all(report["cleanup"].values())
    success = (report.get("exit") == 0 and report["sources_unchanged"] and cleanup
               and not report["archive_problems"] and report["archive_within_ceiling"]
               and report["controller_log"]["within_ceiling"] and result.get("head") == head)
    print(json.dumps({"result": result.get("result", "INVALID_CONTROLLER_NO_REPORT"),
                      "cleanup_verified": cleanup, "launcher_success": success, "evidence": str(output)}))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
