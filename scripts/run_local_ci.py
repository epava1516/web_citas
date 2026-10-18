"""Run project checks with owned disposable PostgreSQL/Redis and durable evidence."""

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LONG_CASES = [
    "tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[short]",
    "tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[measured]",
    "tests/test_rights_portability_large_history.py",
    "tests/test_publication_state_tcp.py",
]

def regression_lane_files(lane):
    """Disjoint file lanes; their union retains the ordinary regression scope."""
    files = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "tests").rglob("test_*.py"))
    if lane == "all":
        return files
    return [name for name in files if name.startswith("tests/test_capacity_") == (lane == "capacity")]


SMOKE = [
    "tests/test_broker_envelope_schema.py",
    "tests/test_publication_state.py",
    "tests/test_retained_rdb_physical_metadata.py",
]
RIGHTS = [
    "tests/test_rights_verification.py",
    "tests/test_rights_access_scope_inventory.py",
    "tests/test_rights_access_coverage.py",
    "tests/test_rights_access_evidence_refs.py",
    "tests/test_rights_access_coverage_store.py",
    "tests/test_rights_access_field_decision.py",
    "tests/test_rights_access_recipient_payload.py",
    "tests/test_rights_access_response_draft.py",
    "tests/test_rights_access_response_mobile.py",
    "tests/test_access_close_localization.py",
    "tests/test_scoped_log_history_origins.py",
    "tests/test_scoped_redis_history_origins.py",
    "tests/test_retained_origin_inventory.py",
    "tests/test_retained_redis_origins.py",
    "tests/test_retained_rdb_physical_metadata.py",
    "tests/test_redis_history_scope.py",
    "tests/test_redis_retained_history.py",
    "tests/test_broker_envelope_schema.py",
]


def hashes():
    from canonical_artifacts import artifact_fingerprints

    files = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
        )
        .decode()
        .split("\0")
    )
    result = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(files))
        if name and (ROOT / name).is_file() and not name.startswith("docs/")
    }
    result.update(artifact_fingerprints(ROOT))
    return result


LABEL = "web-modelos-local-ci-run"


def durable(path, value):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def process_start_ticks(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return int(fields[19])


def recover():
    """Close dead runs honestly: originals untouched, recovery written separately."""
    recovered = []
    for record in sorted((ROOT / "artifacts/local-ci").glob("*/runner.json")):
        output = record.parent
        if (output / "result.json").exists() or (output / "interruption.json").exists():
            continue
        runner = json.loads(record.read_text())
        try:
            running = process_start_ticks(runner["pid"]) == runner["start_ticks"]
        except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
            running = False
        if running:
            continue
        cleanup = {}
        child = runner.get("child")
        if child:
            try:
                orphan = process_start_ticks(child["pid"]) == child["start_ticks"]
            except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
                orphan = False
            if orphan:
                # The step child runs in its own session; end exactly that group.
                os.killpg(child["pid"], signal.SIGTERM)
                time.sleep(5)
                try:
                    if process_start_ticks(child["pid"]) == child["start_ticks"]:
                        os.killpg(child["pid"], signal.SIGKILL)
                except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
                    pass
            cleanup["child"] = {**child, "was_running": orphan}
        for name in runner["containers"]:
            inspected = subprocess.run(
                ["docker", "container", "inspect", "--format",
                 '{{index .Config.Labels "' + LABEL + '"}}', name],
                capture_output=True, text=True,
            )
            if inspected.returncode == 0 and inspected.stdout.strip() != runner["id"]:
                cleanup[name] = {"skipped": "label does not prove ownership"}
                continue
            if inspected.returncode == 0:
                subprocess.run(["docker", "rm", "-f", "-v", name], capture_output=True)
            probe = subprocess.run(["docker", "container", "inspect", name],
                                   capture_output=True, text=True)
            cleanup[name] = {"absent": probe.returncode != 0
                             and "no such" in (probe.stdout + probe.stderr).lower(),
                             "was_present": inspected.returncode == 0}
        temporary = runner.get("temporary")
        if temporary and Path(temporary).is_dir() and (Path(temporary) / "local_ci_settings.py").exists():
            shutil.rmtree(temporary)
        cleanup["temporary"] = {"path": temporary, "absent": not temporary or not Path(temporary).exists()}
        logs = {item.name: item.stat().st_size for item in sorted(output.glob("*.log"))}
        durable(output / "interruption.json", {
            "id": runner["id"],
            "result": "INTERRUPTED",
            "written_by": "run_local_ci.py --recover, not by the interrupted run",
            "recovered_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "runner_alive": False,
            "original_artifacts": logs,
            "junit_present": (output / "pytest.xml").exists(),
            "cleanup": cleanup,
            "verdict": "Incomplete evidence: never PASS; rerun the selection with frozen sources.",
        })
        recovered.append(runner["id"])
    print(json.dumps({"recovered": recovered}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=["checks", "smoke", "rights", "focused", "regression", "full"],
        default="checks",
    )
    parser.add_argument(
        "--native-source", type=Path, help="Pinned librdb checkout; copied before build"
    )
    parser.add_argument(
        "--test", action="append", help="Explicit test file/node for focused profile"
    )
    parser.add_argument("--regression-lane", choices=["all", "functional", "capacity"], default="all",
                        help="Optional disjoint regression lanes; both lanes required for complete regression")
    parser.add_argument("--timeout", type=int, default=7200, help="Seconds per command")
    parser.add_argument("--isolate-test-broker", action="store_true",
                        help="Use a fresh owned broker generation for each pytest case")
    parser.add_argument(
        "--benchmark-normal-refresh", action="store_true",
        help="Use actual worker/Beat with this run's owned Redis for an explicit focused HTTP gate",
    )
    parser.add_argument(
        "--benchmark-generator-freeze", action="store_true",
        help="Apply the documented GC preparation to the benchmark client only",
    )
    parser.add_argument(
        "--benchmark-observe-workers", action="store_true",
        help="Enable existing worker instrumentation only for the explicit short HTTP diagnostic",
    )
    parser.add_argument("--benchmark-prepare-static", action="store_true",
                        help="Compose product worker startup with ingress observation")
    parser.add_argument(
        "--benchmark-ingress-only", action="store_true",
        help="Observe WSGI/SQL/GC without pre-importing application handlers; diagnostic only",
    )
    parser.add_argument("--benchmark-pg-statements", action="store_true",
                        help="Owned server planning/execution diagnosis; requires dedicated preload adapter")
    parser.add_argument("--benchmark-sql-shapes", action="store_true",
                        help="Bounded SQL cardinalities in the owned ingress diagnostic only")
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Parallel pytest workers (xdist, whole files per worker; 1 = serial); never for capacity runs",
    )
    parser.add_argument(
        "--fixture-snapshots", action="store_true",
        help="Cache directory bootstrap in own PostgreSQL/media per worker",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Mark dead runs without a terminal result as INTERRUPTED and remove their declared resources",
    )
    args = parser.parse_args()
    if (args.benchmark_normal_refresh or args.benchmark_generator_freeze or args.benchmark_observe_workers) and (
        args.profile != "focused" or args.workers != 1
    ):
        parser.error("Benchmark switches require focused selection and --workers 1")
    if args.benchmark_normal_refresh and (
        not args.test or any(
            not (item == "tests/test_contract_http_load.py"
                 or item.startswith("tests/test_contract_http_load.py::"))
            for item in args.test
        )
    ):
        parser.error("Normal benchmark refresh requires the explicit contract HTTP test")
    if args.benchmark_observe_workers and args.test != [
        "tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[short]"
    ]:
        parser.error("Worker observer requires the explicit short HTTP diagnostic")
    if args.benchmark_prepare_static and not args.benchmark_ingress_only:
        parser.error("Static startup observation requires ingress-only diagnostic")
    if args.benchmark_ingress_only and not args.benchmark_observe_workers:
        parser.error("Ingress-only requires the explicit short worker diagnostic")
    if args.benchmark_pg_statements and not args.benchmark_sql_shapes:
        parser.error("Server statement diagnosis requires explicit SQL shapes diagnostic")
    if args.benchmark_sql_shapes and not args.benchmark_ingress_only:
        parser.error("SQL shapes require the explicit ingress-only diagnostic")
    if args.recover:
        return recover()
    if (args.profile == "focused") != bool(args.test):
        parser.error("--test is required for focused and forbidden for other profiles")
    for selected in args.test or []:
        path = Path(selected.split("::", 1)[0])
        if (
            path.is_absolute()
            or not (ROOT / path).resolve().is_relative_to(ROOT / "tests")
            or path.suffix != ".py"
            or not (ROOT / path).is_file()
        ):
            parser.error("Focused selections must name existing Python tests under tests/")
    if args.profile != "checks" and args.native_source is None:
        parser.error("Test profiles require --native-source")
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    if not 1 <= args.workers <= 15:
        parser.error("--workers must be between 1 and 15 (one Redis database each)")
    if args.regression_lane != "all" and args.profile != "regression":
        parser.error("--regression-lane requires --profile regression")
    if args.regression_lane == "capacity" and args.workers != 1:
        parser.error("Capacity lane requires --workers 1 for isolated observations")
    for program in ["docker", "uv", "git"]:
        if not shutil.which(program):
            parser.error(f"Missing prerequisite: {program}")
    run_id = time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "-" + uuid.uuid4().hex[:8]
    output = ROOT / "artifacts/local-ci" / run_id
    output.mkdir(parents=True)
    report = {
        "id": run_id,
        "profile": args.profile,
        "result": "ERROR",
        "steps": [],
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "excluded": LONG_CASES if args.profile == "regression" else [],
        "selection": {"smoke": SMOKE, "rights": RIGHTS, "focused": args.test}.get(args.profile, []),
        "regression_lane": args.regression_lane,
        "lane_excluded_files": (sorted(set(regression_lane_files("all"))
                                      - set(regression_lane_files(args.regression_lane)))
                                if args.profile == "regression" else []),
        "workers": args.workers,
        "fixture_snapshots": args.fixture_snapshots,
        "benchmark_observe_workers": args.benchmark_observe_workers,
        "benchmark_ingress_only": args.benchmark_ingress_only,
        "benchmark_prepare_static": args.benchmark_prepare_static,
        "benchmark_sql_shapes": args.benchmark_sql_shapes,
        "benchmark_pg_statements": args.benchmark_pg_statements,
        "benchmark_normal_refresh": args.benchmark_normal_refresh,
        "benchmark_generator_freeze": args.benchmark_generator_freeze,
        "limits": "Local verification; skips/exclusions are not PASS or phase acceptance.",
    }
    before = hashes()
    (output / "source-hashes.json").write_text(json.dumps(before, indent=2))
    # Declared before creating anything, so a killed run can be recovered by exact identity.
    runner = {
        "id": run_id,
        "pid": os.getpid(),
        "start_ticks": process_start_ticks(os.getpid()),
        "command": sys.argv,
        "head": report["head"],
        "containers": [f"web-modelos-ci-{service}-{run_id}" for service in ("pg", "redis")],
        "label": f"{LABEL}={run_id}",
        "temporary": None,
    }
    durable(output / "runner.json", runner)
    containers = []
    exit_code = 1
    # Do not inherit benchmark switches, production credentials or normal broker URLs.
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        in {"PATH", "HOME", "USER", "LANG", "LC_ALL", "UV_CACHE_DIR", "PLAYWRIGHT_BROWSERS_PATH"}
        or k.startswith("XDG_")
    }

    def interrupted(signum, frame):
        # Termination must take the same cleanup path as an interactive interrupt.
        raise KeyboardInterrupt(f"signal {signum}")

    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)

    def run(command, label):
        started = time.monotonic()
        print(f"{label} — {output}", flush=True)
        step = {"name": label, "command": command, "exit": None}
        report["steps"].append(step)
        with (output / f"{len(report['steps']):02d}-{label}.log").open("w") as log:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            runner["child"] = {"pid": process.pid, "start_ticks": process_start_ticks(process.pid),
                               "step": label}
            durable(output / "runner.json", runner)
            try:
                step["exit"] = process.wait(timeout=args.timeout)
            except BaseException:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise
            finally:
                step["seconds"] = time.monotonic() - started
        if step["exit"]:
            raise RuntimeError(f"{label} failed; inspect its log")

    try:
        with tempfile.TemporaryDirectory(prefix="web-modelos-local-ci-") as temporary:
            work = Path(temporary)
            runner["temporary"] = str(work)
            durable(output / "runner.json", runner)
            for service, image, inside, extra in [
                (
                    "pg",
                    "postgres:17-alpine",
                    "5432",
                    [
                        "--tmpfs",
                        "/var/lib/postgresql/data",
                        "-e",
                        "POSTGRES_USER=ci",
                        "-e",
                        "POSTGRES_PASSWORD=ci-synthetic",
                        "-e",
                        "POSTGRES_DB=promotion_gate_ci",
                    ],
                ),
                ("redis", "redis:7.4-alpine", "6379", []),
            ]:
                name = f"web-modelos-ci-{service}-{run_id}"
                containers.append(name)
                # Existing images only: no downloads, subscriptions or published ports on other hosts.
                run(
                    [
                        "docker",
                        "run",
                        "--pull=never",
                        "-d",
                        "--name",
                        name,
                        "--label",
                        runner["label"],
                        "-p",
                        f"127.0.0.1::{inside}",
                        *extra,
                        image,
                    ],
                    f"start-{service}",
                )
                port = (
                    subprocess.check_output(["docker", "port", name, inside], text=True)
                    .strip()
                    .rsplit(":", 1)[1]
                )
                env.update(
                    {"DB_PORT": port, "LOCAL_CI_POSTGRES_CONTAINER": name}
                    if service == "pg"
                    else {"REDIS_URL": f"redis://127.0.0.1:{port}/0"}
                )
                if service == "redis" and args.benchmark_normal_refresh:
                    env.update(
                        WEB_MODELOS_REFRESH_MODE="normal_worker_beat",
                        WEB_MODELOS_BENCHMARK_OWNED_REDIS_URL=env["REDIS_URL"],
                        LOCAL_CI_BENCHMARK_RUN=run_id,
                        LOCAL_CI_BENCHMARK_REDIS_CONTAINER=name,
                    )
                if args.benchmark_observe_workers:
                    env["WEB_MODELOS_BENCHMARK_OBSERVE_WORKERS"] = "1"
                if args.benchmark_ingress_only:
                    env["WEB_MODELOS_BENCHMARK_INGRESS_ONLY"] = "1"
                if args.benchmark_pg_statements:
                    env["WEB_MODELOS_BENCHMARK_PG_STATEMENTS"] = "1"
                if args.benchmark_sql_shapes:
                    env["WEB_MODELOS_BENCHMARK_SQL_SHAPES"] = "1"
                if args.benchmark_prepare_static:
                    env["WEB_MODELOS_BENCHMARK_PREPARE_STATIC"] = "1"
                if args.benchmark_generator_freeze:
                    env["WEB_MODELOS_GENERATOR_GC_FREEZE"] = "1"
                probe = (
                    ["pg_isready", "-U", "ci", "-d", "promotion_gate_ci"]
                    if service == "pg"
                    else ["redis-cli", "ping"]
                )
                deadline = time.monotonic() + 45
                while subprocess.run(
                    ["docker", "exec", name, *probe], capture_output=True
                ).returncode:
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"{service} readiness timeout")
                    time.sleep(0.25)
            if args.fixture_snapshots:
                env.update(
                    LOCAL_CI_FIXTURE_SNAPSHOTS="1", LOCAL_CI_SNAPSHOT_RUN=run_id,
                    LOCAL_CI_SNAPSHOT_ROOT=str(work / "fixture-snapshots"),
                    LOCAL_CI_TEMPORARY=str(work),
                )
            env.update(
                POSTGRES_DB="promotion_gate_ci",
                POSTGRES_USER="ci",
                POSTGRES_PASSWORD="ci-synthetic",
                DB_HOST="127.0.0.1",
                DJANGO_DEBUG="1",
                DJANGO_SETTINGS_MODULE="local_ci_settings",
                PYTHONPATH=f"{work}:{ROOT}",
            )
            (work / "local_ci_settings.py").write_text(
                "import os\n"
                "from config.settings import *\n"
                "# Parallel workers: own test database (pytest-django), media and broker key\n"
                "# prefix. The broker stays on Redis database 0, which retained-origin\n"
                "# validation requires; isolation comes from the per-worker generation prefix.\n"
                "_WORKER = os.environ.get('PYTEST_XDIST_WORKER', '')\n"
                f"MEDIA_ROOT = Path({str(work / 'media')!r}) / (_WORKER or 'main')\n"
                "_CASE_QUEUE = os.environ.get('LOCAL_CI_TEST_QUEUE_GENERATION', '')\n"
                "if _WORKER or _CASE_QUEUE:\n"
                "    TASK_QUEUE_GENERATION = _CASE_QUEUE or ('ci' + _WORKER)\n"
                "    os.environ['TASK_QUEUE_GENERATION'] = TASK_QUEUE_GENERATION\n"
                "    CELERY_BROKER_TRANSPORT_OPTIONS = {\n"
                "        'global_keyprefix': f'clasificados:{TASK_QUEUE_GENERATION}:'\n"
                "    }\n"
            )
            run(["uv", "sync", "--locked", "--offline"], "dependencies")
            run(["uv", "run", "ruff", "check", "."], "ruff")
            run(["uv", "run", "python", "scripts/check_docs.py"], "documentation")
            run(["uv", "run", "python", "manage.py", "check"], "django")
            run(
                ["uv", "run", "python", "manage.py", "makemigrations", "--check", "--dry-run"],
                "migrations",
            )
            if args.profile != "checks":
                source = work / "native-source"
                shutil.copytree(args.native_source.resolve(), source)
                run(
                    [
                        "uv",
                        "run",
                        "python",
                        "scripts/prepare_native_test_tools.py",
                        "--source",
                        str(source),
                        "--output",
                        str(work / "native-tools"),
                        "--env-file",
                        str(work / "native.env"),
                    ],
                    "native-build",
                )
                manifest = json.loads((work / "native-tools/manifest.json").read_text())
                env.update(manifest["environment"])
                (output / "native-manifest.json").write_text(json.dumps(manifest, indent=2))
                command = [
                    "uv",
                    "run",
                    "pytest",
                    "-p",
                    "scripts.local_ci_reports",
                    f"--local-ci-report-journal={output / 'pytest-reports.jsonl'}",
                    "-p",
                    "scripts.catalogue_gate_timings",
                    f"--gate-timings-output={output / 'test-timings.json'}",
                    "-q",
                    "--tb=short",
                    f"--basetemp={work / 'pytest'}",
                    f"--junitxml={output / 'pytest.xml'}",
                    "-o",
                    "junit_family=xunit1",
                    *(["-n", str(args.workers), "--dist", "loadfile"] if args.workers > 1 else []),
                ]
                if args.isolate_test_broker:
                    env["LOCAL_CI_ISOLATED_BROKER_RUN"] = run_id
                    command.extend(["-p", "scripts.local_ci_broker"])
                if args.profile == "smoke":
                    command.extend(SMOKE)
                elif args.profile == "rights":
                    command.extend(RIGHTS)
                elif args.profile == "focused":
                    command.extend(args.test)
                elif args.profile == "regression":
                    if args.regression_lane != "all":
                        selected = set(regression_lane_files(args.regression_lane))
                        command.extend("--ignore=" + name for name in regression_lane_files("all")
                                       if name not in selected)
                    for case in LONG_CASES:
                        command.extend(
                            ["--ignore=" + case] if "::" not in case else ["--deselect=" + case]
                        )
                run(command, "pytest")
            report["result"] = "PASS"
            exit_code = 0
    except (Exception, KeyboardInterrupt) as error:
        report["error"] = str(error) or type(error).__name__
    finally:
        report["cleanup"] = {}
        for name in containers:
            removal = subprocess.run(
                ["docker", "rm", "-f", "-v", name], capture_output=True, text=True
            )
            # Exact-name inspect must report not-found; an empty regex filter is not proof.
            inventory = subprocess.run(
                ["docker", "container", "inspect", "--format", "{{.Id}}", name],
                capture_output=True,
                text=True,
            )
            absent = inventory.returncode != 0 and "no such" in (
                inventory.stdout + inventory.stderr
            ).lower()
            report["cleanup"][name] = {
                "absent": absent,
                "removal_exit": removal.returncode,
                "inventory_exit": inventory.returncode,
            }
            if not absent:
                report["result"], exit_code = "ERROR", 1
        report["sources_unchanged"] = before == hashes()
        if not report["sources_unchanged"]:
            report["result"], exit_code = "INVALID", 1
        junit = output / "pytest.xml"
        if junit.exists():
            try:
                tree = ET.parse(junit).getroot()
                report["junit"] = [dict(suite.attrib) for suite in tree.iter("testsuite")]
                report["skipped"] = [
                    {"case": case.get("name"), "reason": case.find("skipped").get("message")}
                    for case in tree.iter("testcase")
                    if case.find("skipped") is not None
                ]
            except ET.ParseError as error:
                report["junit_error"] = str(error)
                report["result"], exit_code = "ERROR", 1
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"{report['result']}: {output / 'result.json'}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
