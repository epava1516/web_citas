"""Own PostgreSQL/Redis/worker/Beat probe; no normal services or capacity load."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    import psycopg
    from cryptography.fernet import Fernet
    from psycopg import sql

    out = Path(os.environ["PUBLICATION_PROBE_OUTPUT"])
    out.mkdir(exist_ok=False)
    env = os.environ.copy()
    for line in (ROOT / ".env").read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key in {
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "MFA_ENCRYPTION_KEY",
        }:
            env[key] = value.strip().strip("\"'")
    database = "publication_probe_" + uuid.uuid4().hex[:12]
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env.update(
        APP_ENV="development",
        DB_HOST="127.0.0.1",
        DB_PORT="55432",
        POSTGRES_DB=database,
        REDIS_URL=f"redis://127.0.0.1:{port}/0",
        TASK_QUEUE_GENERATION=uuid.uuid4().hex,
        SAFETY_ENCRYPTION_KEY=Fernet.generate_key().decode(),
        DEMO_PASSWORD="Synthetic-" + uuid.uuid4().hex + "!7",
        DJANGO_SETTINGS_MODULE="publication_probe_settings",
        PYTHONPATH=str(out) + ":" + str(ROOT),
        PUBLICATION_PROBE_OUTPUT=str(out),
    )
    (out / "publication_probe_settings.py").write_text(
        "from config.settings import *\n"
        'MEDIA_ROOT = Path(os.environ["PUBLICATION_PROBE_OUTPUT"]) / "private"\n'
        'CELERY_TASK_DEFAULT_QUEUE = os.environ["POSTGRES_DB"]\n'
        "CELERY_TASK_ALWAYS_EAGER = False\n"
        'CELERY_BEAT_SCHEDULE = {"refresh-publication-state": CELERY_BEAT_SCHEDULE["refresh-publication-state"]}\n'
    )
    tracked = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).split(b"\0")
    hashes = {
        p.decode(): hashlib.sha256((ROOT / p.decode()).read_bytes()).hexdigest()
        for p in tracked
        if p and (ROOT / p.decode()).is_file()
    }
    (out / "frozen-manifest.json").write_text(
        json.dumps(
            {
                "source_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "source_sha256": hashes,
                "database": database,
                "scope": "real worker/Beat30s; synthetic fixture; no capacity load",
            },
            indent=2,
        )
    )
    admin = psycopg.connect(
        dbname="postgres",
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        host="127.0.0.1",
        port=55432,
        autocommit=True,
    )
    processes = []
    logs = []
    result = {"database": database, "success": False}

    def start(args, label):
        log = (out / f"{label}.log").open("w")
        logs.append(log)
        p = subprocess.Popen(args, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        processes.append(p)
        return p

    try:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        start(
            [
                "/usr/bin/redis-server",
                "--bind",
                "127.0.0.1",
                "--port",
                str(port),
                "--save",
                "",
                "--appendonly",
                "no",
                "--dir",
                str(out),
            ],
            "redis",
        )
        import redis as redis_client

        conn = redis_client.Redis(host="127.0.0.1", port=port)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                if conn.ping():
                    break
            except redis_client.ConnectionError:
                time.sleep(0.1)
        else:
            raise AssertionError("Own Redis not ready")
        os.environ.update(env)
        import django

        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(out))
        django.setup()
        from django.core.management import call_command
        from django.db import connection
        from django.utils import timezone

        from apps.listings import moderation
        from apps.listings.models import Listing, PublicationDirty, PublicationState

        call_command("migrate", verbosity=0)
        call_command("seed_demo", credentials_file=str(out / "credentials.json"), verbosity=0)
        start(
            [
                str(ROOT / ".venv/bin/celery"),
                "-A",
                "config.celery",
                "worker",
                "--pool=solo",
                "--concurrency=1",
                "-Q",
                database,
                "--loglevel=INFO",
            ],
            "worker",
        )

        def wait_clean(timeout=65):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if (
                    not PublicationDirty.objects.exists()
                    and PublicationState.objects.count() == Listing.objects.count()
                ):
                    return
                time.sleep(0.2)
            raise AssertionError("Own worker did not reconcile publication state")

        wait_clean()
        listing = next(
            r for r in Listing.objects.filter(status="published") if moderation.publicly_visible(r)
        )
        Listing.objects.filter(pk=listing.pk).update(status="paused")
        assert PublicationDirty.objects.filter(listing_id=listing.pk).exists()
        start(
            [
                str(ROOT / ".venv/bin/celery"),
                "-A",
                "config.celery",
                "beat",
                "--loglevel=INFO",
                "--schedule",
                str(out / "beat-schedule"),
            ],
            "beat",
        )
        began = time.monotonic()
        wait_clean()
        assert not PublicationState.objects.get(listing=listing).eligible
        Listing.objects.filter(pk=listing.pk).update(status="published")
        wait_clean()
        assert PublicationState.objects.get(listing=listing).eligible
        from apps.core.models import Person

        Person.objects.filter(pk=listing.person_id).update(consent_revoked_at=timezone.now())
        assert PublicationDirty.objects.filter(listing_id=listing.pk).exists()
        assert not moderation.publicly_visible(Listing.objects.get(pk=listing.pk))
        wait_clean()
        assert not PublicationState.objects.get(listing=listing).eligible
        result.update(
            success=True,
            beat_interval_seconds=30,
            beat_pause_resume_revoke=True,
            wall_seconds=time.monotonic() - began,
            scope="Synthetic authority only; no real identity or capacity acceptance",
        )
        connection.close()
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=5)
        for log in logs:
            log.close()
        admin.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database))
        )
        result["database_absent"] = not admin.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", [database]
        ).fetchone()
        admin.close()
        shutil.rmtree(out / "private", ignore_errors=True)
        (out / "credentials.json").unlink(missing_ok=True)
        result["owned_process_pids"] = [p.pid for p in processes]
        result["processes_terminal"] = all(p.poll() is not None for p in processes)
        result["sources_unchanged"] = all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        )
        (out / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
