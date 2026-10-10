"""Opt-in PostgreSQL/media bootstrap snapshots, confined to disposable local CI."""

import hashlib
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import psycopg
from django.apps import apps
from django.conf import settings
from django.db import connections
from psycopg import sql

_CACHE = {}
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Snapshot:
    template: str
    media: Path
    database: str


def context():
    if os.environ.get("LOCAL_CI_FIXTURE_SNAPSHOTS") != "1":
        return None
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    run = os.environ.get("LOCAL_CI_SNAPSHOT_RUN", "")
    root = os.environ.get("LOCAL_CI_SNAPSHOT_ROOT", "")
    database = connections["default"].settings_dict
    expected = "test_promotion_gate_ci" + ("_" + worker if worker else "")
    if (
        os.environ.get("DJANGO_SETTINGS_MODULE") != "local_ci_settings"
        or not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{8}", run)
        or (worker and not re.fullmatch(r"gw[0-9]+", worker))
        or database["ENGINE"] != "django.db.backends.postgresql"
        or database["NAME"] != expected
        or database["USER"] != "ci"
        or database["HOST"] != "127.0.0.1"
        or not root
        or settings.PRODUCTION
        or settings.MEDIA_STORAGE_PROVIDER != "local"
    ):
        raise RuntimeError("Fixture snapshots require the exact disposable local CI database")
    snapshot_root = Path(root).resolve()
    if not snapshot_root.is_relative_to(Path(os.environ["LOCAL_CI_TEMPORARY"]).resolve()):
        raise RuntimeError("Fixture snapshot media must remain inside this CI run")
    if (
        not Path(settings.MEDIA_ROOT)
        .resolve()
        .is_relative_to(Path(os.environ["LOCAL_CI_TEMPORARY"]).resolve())
    ):
        raise RuntimeError("Fixture test media must remain inside this CI run")
    return run, worker, snapshot_root, database


def cache_key(run, worker):
    digest = hashlib.sha256()
    # Every project Python source read by the bootstrap is covered; no stale cache
    # is reused after fixture/model/migration/configuration changes.
    for folder in (ROOT / "apps", ROOT / "config"):
        for path in sorted(folder.rglob("*.py")):
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(path.read_bytes())
    for name in ("directory_snapshot.py", "test_discovery.py", "test_photos.py"):
        digest.update((ROOT / "tests" / name).read_bytes())
    digest.update(
        repr(
            (
                settings.SECRET_KEY,
                settings.SAFETY_ENCRYPTION_KEY,
                settings.VERIFICATION_PROVIDER,
                settings.STORAGES,
                settings.PASSWORD_HASHERS,
            )
        ).encode()
    )
    return run, worker, digest.hexdigest()


def template_name(key):
    return "fixture_directory_" + hashlib.sha256(repr(key).encode()).hexdigest()[:32]


def _admin(database):
    return psycopg.connect(
        dbname="postgres",
        user=database["USER"],
        password=database["PASSWORD"],
        host=database["HOST"],
        port=database["PORT"],
        autocommit=True,
    )


def _quiescent(cursor, names):
    cursor.execute("SELECT datname FROM pg_stat_activity WHERE datname = ANY(%s)", [names])
    if cursor.fetchall():
        raise RuntimeError("Fixture snapshot database has live connections; none were terminated")


def _empty_fixture_database():
    tables = {model._meta.db_table for model in apps.get_models(include_auto_created=True)}
    tables -= {"django_content_type", "auth_permission"}
    query = sql.SQL(" UNION ALL ").join(
        sql.SQL("SELECT EXISTS(SELECT 1 FROM {})").format(sql.Identifier(table))
        for table in sorted(tables)
    )
    with connections["default"].cursor() as cursor:
        cursor.execute(query)
        return not any(row[0] for row in cursor.fetchall())


def seed_or_restore(seed):
    """Restore only directory bootstrap; rights reads/decisions are never cached."""
    current = context()
    if current is None:
        seed()
        return "seed"
    run, worker, root, database = current
    if connections["default"].in_atomic_block:
        raise RuntimeError("Fixture snapshots require transactional-test autocommit")
    if not _empty_fixture_database():
        # Preserve any setup performed before requesting directory, as before.
        seed()
        return "seed_existing_setup"
    key = cache_key(run, worker)
    snapshot = _CACHE.get(key)
    target = database["NAME"]
    if snapshot is None:
        seed()
        template = template_name(key)
        media = root / template
        if media.exists():
            raise RuntimeError("Fixture snapshot directory already exists")
        shutil.copytree(settings.MEDIA_ROOT, media)
        connections.close_all()
        with _admin(database) as admin, admin.cursor() as cursor:
            _quiescent(cursor, [target, template])
            cursor.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                    sql.Identifier(template), sql.Identifier(target)
                )
            )
            cursor.execute(
                sql.SQL("ALTER DATABASE {} ALLOW_CONNECTIONS false").format(
                    sql.Identifier(template)
                )
            )
        _CACHE[key] = Snapshot(template, media, target)
        return "seed_snapshot"
    if snapshot.database != target:
        raise RuntimeError("Fixture snapshot belongs to another worker database")
    connections.close_all()
    with _admin(database) as admin, admin.cursor() as cursor:
        _quiescent(cursor, [target, snapshot.template])
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(target)))
        cursor.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                sql.Identifier(target), sql.Identifier(snapshot.template)
            )
        )
    destination = Path(settings.MEDIA_ROOT)
    # photo_environment supplies a new test-owned tmp_path; remove only its media.
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(snapshot.media, destination)
    return "restore_snapshot"
