"""Render only: never start services, resolve real env files or publish ports."""

import base64
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALUES = {
    "POSTGRES_PASSWORD": "synthetic-migrator-only",
    "POSTGRES_RUNTIME_PASSWORD": "synthetic-runtime-only",
    "DJANGO_SECRET_KEY": "synthetic-only-" + "x" * 64,
    "MFA_ENCRYPTION_KEY": base64.urlsafe_b64encode(b"m" * 32).decode(),
    "SAFETY_ENCRYPTION_KEY": base64.urlsafe_b64encode(b"s" * 32).decode(),
    "PUBLIC_HOSTNAME": "localhost",
    "TRUSTED_CADDY_IPS": "192.0.2.2",
}


def render_profile(tmp_path, values):
    env_file = tmp_path / "synthetic.env"
    env_file.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
    env_file.chmod(0o600)
    # No inherited deployment variables or .env contents; HOME is preserved unchanged.
    environment = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}
    environment["COMPOSE_DISABLE_ENV_FILE"] = "1"
    return subprocess.run(
        [
            "docker", "compose", "--env-file", str(env_file),
            "-f", "compose.yaml", "-f", "compose.runtime-role.yaml",
            "-f", "compose.production.example.yaml", "config", "--no-env-resolution",
            "--format", "json",
        ],
        cwd=ROOT, env=environment, text=True, capture_output=True, timeout=20,
    )


def test_prepared_profile_keeps_private_ports_roles_keys_and_limits(tmp_path):
    rendered = render_profile(tmp_path, VALUES)
    assert rendered.returncode == 0, rendered.stderr
    config = json.loads(rendered.stdout)
    services = config["services"]
    assert config["name"] == "web-modelos-production-example"
    assert config["networks"]["backend"]["internal"] is True
    for name in ("db", "redis", "objects", "app", "worker", "beat", "migrate-runtime"):
        assert not services[name].get("ports")
        assert set(services[name]["networks"]) == {"backend"}
    assert set(services["caddy"]["networks"]) == {"backend", "edge"}
    assert {int(port["target"]) for port in services["caddy"]["ports"]} == {80, 443}
    assert all(port["host_ip"] == "127.0.0.1" for port in services["caddy"]["ports"])
    for name in ("app", "worker", "beat"):
        env = services[name]["environment"]
        assert env["APP_ENV"] == "production" and env["DJANGO_DEBUG"] == "0"
        assert env["POSTGRES_USER"] != services["db"]["environment"]["POSTGRES_USER"]
        assert env["RIGHTS_EVIDENCE_ENFORCED"] == "1"
        assert env["VERIFICATION_PROVIDER"] == "disabled" and env["PAYMENTS_ENABLED"] == "0"
        assert env["FORWARDED_ALLOW_IPS"] == VALUES["TRUSTED_CADDY_IPS"]
        assert "--proxy-allow-from=" + VALUES["TRUSTED_CADDY_IPS"] in env["GUNICORN_CMD_ARGS"]
        assert "--proxy-protocol" in env["GUNICORN_CMD_ARGS"]
        assert services[name]["read_only"] and "ALL" in services[name]["cap_drop"]
    for name, memory, pids in [
        ("db", 1536, 128), ("app", 1536, 128), ("worker", 512, 128),
        ("migrate-runtime", 512, 128), ("redis", 128, 64), ("beat", 128, 64),
        ("caddy", 128, 64),
    ]:
        service = services[name]
        assert service["mem_limit"] == service["memswap_limit"] == memory * 1024**2
        assert service["pids_limit"] == pids and float(service["cpus"]) > 0
    caddy_mounts = {row["target"]: row for row in services["caddy"]["volumes"]}
    assert Path(caddy_mounts["/etc/caddy/Caddyfile"]["source"]).name == "Caddyfile.production.example"
    assert caddy_mounts["/etc/caddy/Caddyfile"]["read_only"]
    assert caddy_mounts["/srv/static"]["read_only"]


@pytest.mark.parametrize("missing", list(VALUES))
def test_prepared_profile_rejects_missing_operator_inputs(tmp_path, missing):
    rendered = render_profile(tmp_path, {key: value for key, value in VALUES.items() if key != missing})
    assert rendered.returncode != 0
    assert missing in rendered.stderr
