"""Actual Django console output, synthetic token owner, encrypted captured origin."""

from datetime import timedelta

import pytest
from django.utils import timezone
from test_rights_access_recipient_payload import synthetic_log_bundle

from apps.core.accounts import send_token
from apps.core.models import User
from apps.safety.console_mail_projection import console_mail_projections
from apps.safety.rights_access_delivery import log_records
from scripts.collect_access_resource_logs import write_bundle

pytestmark = pytest.mark.django_db(transaction=True)


def test_console_mail_captured_projection_excludes_capability_and_rejects_unknowns(
    settings, capsys, tmp_path
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    owner = User.objects.create_user(username="console-owner", email="owner@example.invalid")
    other = User.objects.create_user(username="console-other", email="other@example.invalid")
    send_token(owner, "verify", "es")
    raw = capsys.readouterr().out
    cutoff = timezone.now()
    captured = "".join(f"{cutoff.isoformat()} {line}\n" for line in raw.splitlines())
    projection = console_mail_projections(captured, cutoff, owner=owner.pk, email=owner.email)
    assert len(projection) == 1
    value = next(iter(projection.values()))
    assert value["recipient"] == owner.email
    assert value["body"].endswith("[redacted]") and "/account/token/" not in str(value)
    assert not console_mail_projections(captured, cutoff, owner=other.pk, email=owner.email)
    assert not console_mail_projections(captured, cutoff, owner=owner.pk, email=other.email)
    assert not console_mail_projections(
        captured, cutoff - timedelta(seconds=1), owner=owner.pk, email=owner.email
    )
    assert not console_mail_projections(
        captured.replace("-" * 79, ""), cutoff, owner=owner.pk, email=owner.email
    )
    extra = captured.replace(
        "MIME-Version: 1.0", "MIME-Version: 1.0\n" + cutoff.isoformat() + " X-Private: unknown"
    )
    assert not console_mail_projections(extra, cutoff, owner=owner.pk, email=owner.email)
    body = synthetic_log_bundle(timezone.now(), captured)
    tmp_path.chmod(0o700)
    path = write_bundle(tmp_path, body)
    settings.ACCESS_LOG_ORIGIN_BUNDLE = str(path)
    result = log_records({owner.email}, cutoff, owner=owner.pk, email=owner.email)
    assert len(result["projected_mail"]) == 1
    assert not result["unprojected_candidates"]
    assert result["pending"] == body["pending"]
    assert "/account/token/" not in str(result)
