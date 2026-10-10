"""Real PostgreSQL/media equivalence; run via CI --fixture-snapshots."""

import io
import json
import os
from pathlib import Path

import pytest
from directory_snapshot import _CACHE, cache_key, context, seed_or_restore, template_name
from django.core.management import call_command
from django.db import connections
from test_photos import photo_environment  # noqa: F401

from apps.core.models import User


@pytest.mark.skipif(
    os.environ.get("LOCAL_CI_FIXTURE_SNAPSHOTS") != "1",
    reason="Requires explicit disposable local CI fixture-snapshot environment",
)
@pytest.mark.django_db(transaction=True)
def test_snapshot_restores_mutated_database_and_media(request, settings, tmp_path, monkeypatch):
    request.getfixturevalue("photo_environment")
    monkeypatch.setenv("DEMO_PASSWORD", "Long-directory-fixture-password!873")
    mode = context()
    # Selection for this feature must explicitly opt in; no silent PASS/skip.
    assert mode is not None, "Use local CI --fixture-snapshots"
    calls = []

    def seed():
        calls.append(True)
        call_command(
            "seed_demo", credentials_file=str(tmp_path / "credentials.json"), stdout=io.StringIO()
        )

    first = seed_or_restore(seed)
    assert first in {"seed_snapshot", "restore_snapshot"}
    media = Path(settings.MEDIA_ROOT)
    credentials = tmp_path / "credentials.json"
    original_credentials = credentials.read_bytes()
    original = {
        str(path.relative_to(media)): path.read_bytes()
        for path in media.rglob("*")
        if path.is_file()
    }
    assert original
    user = User.objects.get(username="fixture-v1-individual")
    old_email = user.email
    User.objects.filter(pk=user.pk).update(email="mutated@example.invalid")
    selected = media / next(iter(original))
    selected.write_bytes(b"mutated test media")
    (media / "extra-mutated-file").write_bytes(b"new file")
    credentials.unlink()
    # Reproduce transaction=True teardown, then the next test's fixture request.
    call_command("flush", interactive=False, stdout=io.StringIO())
    assert seed_or_restore(seed) == "restore_snapshot"
    assert User.objects.get(pk=user.pk).email == old_email
    assert credentials.read_bytes() == original_credentials
    assert credentials.stat().st_mode & 0o777 == 0o600
    assert {
        str(path.relative_to(media)): path.read_bytes()
        for path in media.rglob("*")
        if path.is_file()
    } == original
    assert len(calls) == (1 if first == "seed_snapshot" else 0)
    run, worker, _, database = mode
    assert _CACHE[cache_key(run, worker)].database == connections["default"].settings_dict["NAME"]
    assert (
        database["NAME"].endswith("_" + worker)
        if worker
        else database["NAME"] == "test_promotion_gate_ci"
    )
    assert template_name(cache_key(run, "gw0")) != template_name(cache_key(run, "gw1"))


def test_snapshot_falls_back_without_ci_optin(monkeypatch):
    monkeypatch.delenv("LOCAL_CI_FIXTURE_SNAPSHOTS", raising=False)
    calls = []
    assert seed_or_restore(lambda: calls.append("seed")) == "seed"
    assert calls == ["seed"]


def test_snapshot_refuses_unowned_environment(monkeypatch):
    monkeypatch.setenv("LOCAL_CI_FIXTURE_SNAPSHOTS", "1")
    monkeypatch.setenv("LOCAL_CI_SNAPSHOT_RUN", "not-a-run-id")
    with pytest.raises(RuntimeError, match="exact disposable"):
        context()


@pytest.mark.skipif(
    os.environ.get("LOCAL_CI_FIXTURE_SNAPSHOTS") != "1",
    reason="Requires explicit disposable local CI fixture-snapshot environment",
)
@pytest.mark.django_db(transaction=True)
def test_preexisting_test_setup_is_preserved_instead_of_restoring(request):
    request.getfixturevalue("photo_environment")
    user = User.objects.create(username="preexisting-synthetic-setup")
    calls = []
    assert seed_or_restore(lambda: calls.append("seed")) == "seed_existing_setup"
    assert calls == ["seed"]
    assert User.objects.filter(pk=user.pk, username="preexisting-synthetic-setup").exists()


def test_snapshot_rejects_normal_database_alias(monkeypatch, settings):
    monkeypatch.setenv("LOCAL_CI_FIXTURE_SNAPSHOTS", "1")
    monkeypatch.setenv("LOCAL_CI_SNAPSHOT_RUN", "20261010-120000-12345678")
    monkeypatch.setenv("LOCAL_CI_SNAPSHOT_ROOT", "/tmp/owned-ci-fixture")
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "local_ci_settings")
    monkeypatch.setitem(connections["default"].settings_dict, "NAME", "promotion_gate_ci")
    with pytest.raises(RuntimeError, match="exact disposable"):
        context()


@pytest.mark.parametrize("mismatch", ["label", "port"])
def test_snapshot_refuses_container_label_or_port_mismatch(monkeypatch, mismatch):
    from directory_snapshot import _verify_container

    run = "20261010-120001-12345678"
    name = "web-modelos-ci-pg-" + run
    monkeypatch.setenv("LOCAL_CI_POSTGRES_CONTAINER", name)
    container = {
        "Name": "/" + name,
        "State": {"Running": True},
        "Config": {"Labels": {"web-modelos-local-ci-run": run}},
        "NetworkSettings": {"Ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54321"}]}},
    }
    if mismatch == "label":
        container["Config"]["Labels"]["web-modelos-local-ci-run"] = "another-run"
    else:
        container["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"] = "54322"
    monkeypatch.setattr(
        "directory_snapshot.subprocess.check_output",
        lambda *args, **kwargs: json.dumps([container]),
    )
    with pytest.raises(RuntimeError, match="label or port"):
        _verify_container(run, "gw0", {"HOST": "127.0.0.1", "PORT": "54321"})


def test_snapshot_container_identity_is_cached_only_for_same_worker_and_port(monkeypatch):
    from directory_snapshot import _verify_container

    run = "20261010-120002-12345678"
    name = "web-modelos-ci-pg-" + run
    monkeypatch.setenv("LOCAL_CI_POSTGRES_CONTAINER", name)
    container = {
        "Name": "/" + name,
        "State": {"Running": True},
        "Config": {"Labels": {"web-modelos-local-ci-run": run}},
        "NetworkSettings": {"Ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54323"}]}},
    }
    calls = []

    def inspect(*args, **kwargs):
        calls.append(args)
        return json.dumps([container])

    monkeypatch.setattr("directory_snapshot.subprocess.check_output", inspect)
    database = {"HOST": "127.0.0.1", "PORT": "54323"}
    _verify_container(run, "gw0", database)
    _verify_container(run, "gw0", database)
    assert len(calls) == 1
    _verify_container(run, "gw1", database)
    assert len(calls) == 2


@pytest.mark.skipif(
    os.environ.get("LOCAL_CI_FIXTURE_SNAPSHOTS") != "1",
    reason="Requires explicit disposable local CI fixture-snapshot environment",
)
@pytest.mark.django_db(transaction=True)
def test_occupied_database_falls_back_to_real_seed_without_terminating(
    request, settings, tmp_path, monkeypatch
):
    import psycopg
    from directory_snapshot import _admin

    request.getfixturevalue("photo_environment")
    monkeypatch.setenv("DEMO_PASSWORD", "Long-directory-fixture-password!873")
    mode = context()
    assert mode is not None
    database = mode[3]
    calls = []

    def seed():
        calls.append(True)
        call_command(
            "seed_demo", credentials_file=str(tmp_path / "credentials.json"), stdout=io.StringIO()
        )

    # A separate real connection models live_server starting before directory.
    with psycopg.connect(
        dbname=database["NAME"],
        user=database["USER"],
        password=database["PASSWORD"],
        host=database["HOST"],
        port=database["PORT"],
        autocommit=True,
    ) as live:
        assert seed_or_restore(seed) == "seed_busy_database"
        assert calls == [True]
        with live.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM core_user")
            assert cursor.fetchone()[0] > 0
        assert (tmp_path / "credentials.json").is_file()
        assert User.objects.filter(username="fixture-v1-individual").exists()
        # Occupancy remains genuine and no caller silently terminated it.
        with _admin(database) as admin, admin.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM pg_stat_activity WHERE datname=%s", [database["NAME"]]
            )
            assert cursor.fetchone()[0] >= 2


def test_seed_password_changes_cache_identity_without_exposing_password(settings, monkeypatch):
    first_password = "Synthetic-only-first-fixture-password!483"
    second_password = "Synthetic-only-second-fixture-password!926"
    monkeypatch.setenv("DEMO_PASSWORD", first_password)
    first = cache_key("20261010-120000-12345678", "gw0")
    monkeypatch.setenv("DEMO_PASSWORD", second_password)
    second = cache_key("20261010-120000-12345678", "gw0")
    assert first != second
    assert first_password not in repr(first) and second_password not in repr(second)
