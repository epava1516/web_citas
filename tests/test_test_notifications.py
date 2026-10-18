"""Notification transport failures must never rewrite a test verdict."""
import json
import subprocess
from types import SimpleNamespace

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
