"""Account mail producer formats must remain strictly associated and redacted."""

import io
from contextlib import redirect_stdout

import pytest
from django.utils import timezone
from test_rights_access_recipient_payload import synthetic_log_bundle

from apps.core.accounts import send_token
from apps.core.models import AccountToken, User
from apps.safety.crypto import seal
from apps.safety.rights_access_delivery import log_records

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "language,prefix", [("es", "Enlace de un solo uso:\n"), ("en", "Single-use link:\n")]
)
@pytest.mark.parametrize("purpose", ["verify", "reset"])
def test_current_console_account_mail_is_owned_and_redacted(
    settings, tmp_path, language, prefix, purpose
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    settings.PUBLIC_ORIGIN = "https://synthetic.example.invalid"
    owner = User.objects.create(
        username="synthetic-mail-owner", email="synthetic-owner@example.invalid"
    )
    other = User.objects.create(
        username="synthetic-mail-other", email="synthetic-other@example.invalid"
    )
    stream = io.StringIO()
    with redirect_stdout(stream):
        send_token(owner, purpose, language)
    token = AccountToken.objects.get(user=owner)
    cutoff = timezone.now()
    content = "".join(f"{cutoff.isoformat()} {line}\n" for line in stream.getvalue().splitlines())
    path = tmp_path / "synthetic-console-origin.encrypted"
    path.write_text(seal(synthetic_log_bundle(timezone.now(), content)))
    path.chmod(0o600)
    settings.ACCESS_LOG_ORIGIN_BUNDLE = str(path)
    result = log_records({owner.email}, cutoff, owner=owner.pk, email=owner.email)
    assert len(result["candidates"]) == 1
    assert result["unprojected_candidates"] == []
    assert len(result["projected_mail"]) == 1
    projection = result["projected_mail"][0]["data"]
    assert projection["body"] == prefix + "[redacted]"
    assert projection["recipient"] == owner.email and projection["purpose"] == purpose
    assert str(token.pk) not in str(result) and token.digest not in str(result)
    assert "/account/token/" not in str(result)
    wrong_owner = log_records({owner.email}, cutoff, owner=other.pk, email=owner.email)
    assert wrong_owner["projected_mail"] == []
    assert len(wrong_owner["unprojected_candidates"]) == 1
