"""Real PostgreSQL/media equivalence; run via CI --fixture-snapshots."""

import io
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
    # Reproduce transaction=True teardown, then the next test's fixture request.
    call_command("flush", interactive=False, stdout=io.StringIO())
    assert seed_or_restore(seed) == "restore_snapshot"
    assert User.objects.get(pk=user.pk).email == old_email
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
