"""Run catalogue and affected rights gates on disposable PostgreSQL databases.

Run only after the performance measurement is terminal. Results are private;
fixtures use synthetic identities. This does not accept CR10 or real payments.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg
from cryptography.fernet import Fernet
from psycopg import sql

TESTS = [
    "tests/test_promotion_catalog.py",
    "tests/test_promotion_audit_inventory.py",
    "tests/test_rights_notice_inventory.py",
    "tests/test_account_inventory_dependencies.py",
    "tests/test_purpose_inventory_dependencies.py",
    "tests/test_rights_copy_scope.py",
]


def unrelated_task_log(root):
    """Only the independent delegation ledger may differ from the tested commit.

    Never stash, reset or commit a concurrent user's ledger to obtain a clean
    tree. Every other tracked change, including any tested source, still blocks.
    The ledger is not a test input; record its starting hash without its content.
    """
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "-z", "HEAD"], cwd=root
    ).decode().split("\0")
    changed = [name for name in changed if name]
    if any(name != ".ai/tasks/desarrollo.md" for name in changed):
        raise ValueError("Commit the tested source before running these gates")
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in changed}


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--test",
        action="append",
        dest="tests",
        help="Affected pytest selector; repeat to select cases",
    )
    args = parser.parse_args()
    selected = args.tests or TESTS
    root = Path(__file__).resolve().parents[1]
    for selector in selected:
        path = (root / selector.split("::", 1)[0]).resolve()
        if not path.is_file() or not path.is_relative_to(root / "tests"):
            parser.error("Test selection must refer to an existing file under tests/")
    env = os.environ.copy()
    allowed = {"POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "SAFETY_ENCRYPTION_KEY"}
    for line in args.env_file.read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key in allowed:
            env[key] = value.strip().strip("\"'")
    if not (allowed - {"SAFETY_ENCRYPTION_KEY"}) <= env.keys():
        parser.error("Required database configuration missing")
    ephemeral_key = not env.get("SAFETY_ENCRYPTION_KEY")
    if ephemeral_key:
        env["SAFETY_ENCRYPTION_KEY"] = Fernet.generate_key().decode("ascii")
    try:
        task_log_hashes = unrelated_task_log(root)
    except ValueError as error:
        parser.error(str(error))
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(args.output, 0o700)
    name = "promotion_gate_" + uuid.uuid4().hex
    names = ("test_" + name, name)
    source_paths = subprocess.check_output(
        [
            "git",
            "ls-files",
            "apps",
            "config",
            "templates",
            "static",
            "tests",
            "scripts",
            "pyproject.toml",
        ],
        cwd=root,
        text=True,
    ).splitlines()
    source_hashes = {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in source_paths
        if (root / path).is_file()
    }
    result = {
        "schema": "promotion-catalogue-isolated-gates-v1",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "synthetic_data": True,
        "source_sha256": source_hashes,
        "unrelated_task_log_sha256_at_start": task_log_hashes,
        "unrelated_task_log_scope": "Independent delegation ledger; not a tested source or acceptance",
        "sources_unchanged": False,
        "ephemeral_test_encryption_key": ephemeral_key,
        "tests": selected,
        "timing_seconds": {"configuration": time.perf_counter() - started},
        "diagnosis_timing": "Not measured in this invocation",
        "integration_timing": "Outside this invocation",
        "test_media_removed": False,
        "migration_exit": None,
        "pytest_exit": None,
        "cleanup_verified": False,
        "phase_accepted": False,
    }
    env_started = time.perf_counter()
    admin = psycopg.connect(
        dbname=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        host=env.get("DB_HOST", "127.0.0.1"),
        port=env.get("DB_PORT", "55432"),
        autocommit=True,
    )
    created = False
    try:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        created = True
        result["timing_seconds"]["database_preparation"] = time.perf_counter() - env_started
        env["POSTGRES_DB"] = name
        env["PYTHONPATH"] = str(root)
        stage_started = time.perf_counter()
        with (args.output / "migration.log").open("w") as log:
            result["migration_exit"] = subprocess.run(
                [sys.executable, "manage.py", "migrate", "--noinput"],
                cwd=root,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            ).returncode
        result["timing_seconds"]["migration"] = time.perf_counter() - stage_started
        if result["migration_exit"] == 0:
            stage_started = time.perf_counter()
            with (args.output / "pytest.log").open("w") as log:
                result["pytest_exit"] = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        *selected,
                        "-p",
                        "scripts.catalogue_gate_timings",
                        "--gate-timings-output=" + str(args.output.resolve() / "test-timings.json"),
                        "--basetemp=" + str(args.output.resolve() / "pytest-temp"),
                        "-q",
                        "--junitxml=" + str(args.output.resolve() / "pytest.xml"),
                    ],
                    cwd=root,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                ).returncode
            result["timing_seconds"]["pytest"] = time.perf_counter() - stage_started
    finally:
        cleanup_started = time.perf_counter()
        # Exact UUID namespace created by this invocation only; never project DB.
        try:
            for database in names if created else ():
                admin.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                        sql.Identifier(database)
                    )
                )
            present = admin.execute(
                "SELECT datname FROM pg_database WHERE datname = ANY(%s)", [list(names)]
            ).fetchall()
            result["cleanup_verified"] = not present
            # Owned synthetic fixture directory from this invocation only.
            media = args.output / "pytest-temp"
            if media.exists():
                shutil.rmtree(media)
            result["test_media_removed"] = not media.exists()
            result["timing_seconds"]["cleanup"] = time.perf_counter() - cleanup_started
        finally:
            admin.close()
            result["sources_unchanged"] = all(
                (root / path).is_file()
                and hashlib.sha256((root / path).read_bytes()).hexdigest() == digest
                for path, digest in source_hashes.items()
            )
            result["timing_seconds"]["total"] = time.perf_counter() - started
            result["artifact_sha256"] = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in args.output.iterdir()
                if path.is_file()
            }
            (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "source_commit",
                    "migration_exit",
                    "pytest_exit",
                    "cleanup_verified",
                    "phase_accepted",
                )
            }
        )
    )
    return (
        0
        if (
            result["migration_exit"] == 0
            and result["pytest_exit"] == 0
            and result["cleanup_verified"]
            and result["test_media_removed"]
            and result["sources_unchanged"]
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
