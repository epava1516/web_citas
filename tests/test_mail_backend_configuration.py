"""Production cannot turn account messages into logs or pretend local delivery."""

import base64
import json
import os
import subprocess
import sys

import pytest


def startup(production, backend=None):
    env = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}
    env.update(
        APP_ENV="production" if production else "development",
        DJANGO_SECRET_KEY="synthetic-mail-configuration-" + "x" * 64,
        MFA_ENCRYPTION_KEY=base64.urlsafe_b64encode(b"m" * 32).decode(),
        SAFETY_ENCRYPTION_KEY=base64.urlsafe_b64encode(b"s" * 32).decode(),
        VERIFICATION_PROVIDER="disabled",
    )
    if backend is not None:
        env["EMAIL_BACKEND"] = backend
    return subprocess.run(
        [sys.executable, "-c", (
            "import json; import config.settings as s; "
            "print(json.dumps({'production': s.PRODUCTION, 'backend': s.EMAIL_BACKEND}))"
        )], env=env, capture_output=True, text=True, timeout=15,
    )


@pytest.mark.parametrize("backend", [
    None, "", " ",
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
])
def test_production_rejects_missing_or_local_mail_backend(backend):
    result = startup(True, backend)
    assert result.returncode != 0 and not result.stdout
    assert "Production email requires an explicitly configured delivery backend" in result.stderr
    assert "synthetic-mail-configuration-" not in result.stderr


@pytest.mark.parametrize("production", [False, True])
def test_explicit_smtp_configuration_does_not_connect_or_send(production):
    backend = "django.core.mail.backends.smtp.EmailBackend"
    result = startup(production, backend)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"production": production, "backend": backend}


def test_development_keeps_local_console_default():
    result = startup(False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "production": False, "backend": "django.core.mail.backends.console.EmailBackend",
    }
