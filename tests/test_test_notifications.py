"""Notification transport failures must never rewrite a test verdict."""
import json
import subprocess
from types import SimpleNamespace

import pytest

from scripts import test_notifications as notifications


def test_notification_uses_openclaw_without_exposing_credentials(tmp_path, monkeypatch):
    config = tmp_path / ".config/web_modelos/test-notifications.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"target": "synthetic-recipient", "account": "default",
                                  "container_service": "openclaw-gateway"}))
    monkeypatch.setattr(notifications.Path, "home", lambda: tmp_path)
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        assert kwargs["capture_output"] and kwargs["timeout"] <= 45
        return SimpleNamespace(stdout="owned-container\n")

    monkeypatch.setattr(notifications.subprocess, "run", run)
    result = notifications.notify("synthetic test", "FAIL", counts={"failed": 1})
    assert result["delivery"] == "sent" and result["result"] == "FAIL"
    assert commands[1][:4] == ["docker", "exec", "owned-container", "node"]
    assert "--channel" in commands[1] and "telegram" in commands[1]
    assert "synthetic-recipient" in commands[1]


def test_failed_delivery_keeps_test_result_and_redacts_provider_diagnostics(tmp_path, monkeypatch):
    config = tmp_path / ".config/web_modelos/test-notifications.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"target": "synthetic", "account": "default",
                                  "container_service": "openclaw-gateway"}))
    monkeypatch.setattr(notifications.Path, "home", lambda: tmp_path)

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["synthetic"], stderr="DO-NOT-LOG-SECRET")

    monkeypatch.setattr(notifications.subprocess, "run", fail)
    result = notifications.notify("synthetic transport failure", "PASS")
    assert result["delivery"] == "failed" and result["result"] == "PASS"
    assert "DO-NOT-LOG-SECRET" not in json.dumps(result)


def test_worker_and_runner_do_not_duplicate_pytest_notification(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Duplicate notification")

    monkeypatch.setattr(notifications, "notify", unexpected)
    notifications.pytest_sessionfinish(SimpleNamespace(config=SimpleNamespace(workerinput={})), 0)
    monkeypatch.setenv("LOCAL_CI_TELEGRAM_OWNER", "runner")
    notifications.pytest_sessionfinish(SimpleNamespace(config=SimpleNamespace()), 1)


@pytest.mark.parametrize("provider_failure", [False, True])
def test_explicit_receipt_directory_never_creates_default_artifacts(
    tmp_path, monkeypatch, provider_failure
):
    config = tmp_path / ".config/web_modelos/test-notifications.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"target": "synthetic-recipient", "account": "default",
                                  "container_service": "openclaw-gateway"}))
    monkeypatch.setattr(notifications.Path, "home", lambda: tmp_path)
    fake_root = tmp_path / "project"
    monkeypatch.setattr(notifications, "__file__", str(fake_root / "scripts/test_notifications.py"))

    def transport(command, **kwargs):
        if provider_failure:
            raise subprocess.CalledProcessError(1, command, stderr="DO-NOT-LOG-SECRET")
        return SimpleNamespace(stdout="owned-container\n")

    monkeypatch.setattr(notifications.subprocess, "run", transport)
    destination = fake_root / "docs/actas/terminal-receipts"
    result = notifications.notify("synthetic terminal receipt", "FAIL", receipt_dir=destination)
    assert result["delivery"] == ("failed" if provider_failure else "sent")
    assert result["result"] == "FAIL" and "receipt_error" not in result
    receipts = list(destination.glob("*.json"))
    assert len(receipts) == 1 and json.loads(receipts[0].read_text()) == result
    assert "DO-NOT-LOG-SECRET" not in receipts[0].read_text()
    assert not (fake_root / "artifacts").exists()


def test_failed_explicit_receipt_write_never_falls_back_to_artifacts(tmp_path, monkeypatch):
    config = tmp_path / ".config/web_modelos/test-notifications.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"target": "synthetic", "account": "default",
                                  "container_service": "openclaw-gateway"}))
    monkeypatch.setattr(notifications.Path, "home", lambda: tmp_path)
    fake_root = tmp_path / "project"
    monkeypatch.setattr(notifications, "__file__", str(fake_root / "scripts/test_notifications.py"))
    monkeypatch.setattr(notifications.subprocess, "run",
                        lambda *args, **kwargs: SimpleNamespace(stdout="owned-container\n"))
    blocked = tmp_path / "existing-file"
    blocked.write_text("preserve this file")
    result = notifications.notify("synthetic failed receipt write", "PASS", receipt_dir=blocked)
    assert result["delivery"] == "sent" and result["result"] == "PASS"
    assert result["receipt_error"] == "OSError" and blocked.read_text() == "preserve this file"
    assert not (fake_root / "artifacts").exists()
