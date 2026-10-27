"""Terminal-only test summaries through the owner's configured OpenClaw Telegram."""
import json
import os
import subprocess
import time
from pathlib import Path


def notify(name, result, *, counts=None, seconds=None, run_id=None, receipt_dir=None):
    config_path = Path.home() / ".config/web_modelos/test-notifications.json"
    receipt = {"delivery": "failed", "result": str(result), "name": str(name)}
    try:
        config = json.loads(config_path.read_text())
        containers = subprocess.run(
            ["docker", "ps", "--filter", "label=com.docker.compose.service=" + config["container_service"],
             "--format", "{{.ID}}"], capture_output=True, text=True, timeout=10, check=True,
        ).stdout.split()
        if len(containers) != 1:
            raise RuntimeError("Expected exactly one active OpenClaw gateway")
        message = f"web_modelos · {name}\nResultado: {result}"
        if counts:
            message += "\n" + ", ".join(f"{key}: {value}" for key, value in counts.items())
        if seconds is not None:
            message += f"\nDuración: {seconds:.1f} s"
        if run_id:
            message += f"\nRun: {run_id}"
        subprocess.run(
            ["docker", "exec", containers[0], "node", "openclaw.mjs", "message", "send",
             "--channel", "telegram", "--account", config["account"], "--target", config["target"],
             "--message", message, "--json"], capture_output=True, timeout=45, check=True,
        )
        receipt["delivery"] = "sent"
    except Exception as error:
        # Never log command stderr: provider diagnostics may contain credentials.
        receipt["error_type"] = type(error).__name__
    output = (Path(receipt_dir) if receipt_dir is not None
              else Path(__file__).resolve().parents[1] / "artifacts/test-notifications")
    try:
        output.mkdir(parents=True, exist_ok=True)
        (output / f"{time.time_ns()}-{os.getpid()}.json").write_text(json.dumps(receipt) + "\n")
    except OSError:
        receipt["receipt_error"] = "OSError"
    return receipt


def pytest_sessionstart(session):
    session._telegram_started = time.monotonic()


def pytest_sessionfinish(session, exitstatus):
    if hasattr(session.config, "workerinput"):
        return
    # The owned runner sends once after cleanup, including setup failures.
    if os.environ.get("LOCAL_CI_TELEGRAM_OWNER") == "runner":
        return
    reporter = session.config.pluginmanager.getplugin("terminalreporter")
    counts = {key: len(reporter.stats.get(key, [])) for key in ("passed", "failed", "error", "skipped")} if reporter else {}
    receipt = notify("pytest", "PASS" if exitstatus == 0 else f"EXIT {exitstatus}", counts=counts,
                     seconds=time.monotonic() - session._telegram_started)
    if receipt["delivery"] != "sent" and reporter:
        reporter.write_line("Telegram: envío fallido; recibo en artifacts/test-notifications")
