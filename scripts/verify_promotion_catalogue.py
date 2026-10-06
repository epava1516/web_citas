"""Run catalogue and affected rights gates on disposable PostgreSQL databases.

Run only after the performance measurement is terminal. Results are private;
fixtures use synthetic identities. This does not accept CR10 or real payments.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
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
    if subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=root).returncode:
        parser.error("Commit the tested source before running these gates")
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(args.output, 0o700)
    name = "promotion_gate_" + uuid.uuid4().hex
    names = ("test_" + name, name)
    result = {
        "schema": "promotion-catalogue-isolated-gates-v1",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "synthetic_data": True,
        "ephemeral_test_encryption_key": ephemeral_key,
        "tests": TESTS,
        "migration_exit": None,
        "pytest_exit": None,
        "cleanup_verified": False,
        "phase_accepted": False,
    }
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
        env["POSTGRES_DB"] = name
        env["PYTHONPATH"] = str(root)
        with (args.output / "migration.log").open("w") as log:
            result["migration_exit"] = subprocess.run(
                [sys.executable, "manage.py", "migrate", "--noinput"],
                cwd=root,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            ).returncode
        if result["migration_exit"] == 0:
            with (args.output / "pytest.log").open("w") as log:
                result["pytest_exit"] = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        *TESTS,
                        "-q",
                        "--junitxml=" + str(args.output.resolve() / "pytest.xml"),
                    ],
                    cwd=root,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                ).returncode
    finally:
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
        finally:
            admin.close()
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
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
