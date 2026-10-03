import io
import json
import stat

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client
from test_photos import photo_environment  # noqa: F401

from apps.core.mfa import decrypt
from apps.core.models import Agency, Person, User
from apps.listings.models import Listing, Submission
from apps.mediafiles.models import Photo


@pytest.mark.django_db(transaction=True)
def test_demo_fixture_reproducible_private_credentials_and_real_publication(
    request, tmp_path, monkeypatch
):
    request.getfixturevalue("photo_environment")
    monkeypatch.setenv("DEMO_PASSWORD", "Long-synthetic-fixture-password!873")
    target = tmp_path / "credentials.json"
    output = io.StringIO()
    call_command("seed_demo", credentials_file=str(target), stdout=output)
    assert User.objects.count() == 8 and Person.objects.count() == 4
    assert User.objects.filter(role="individual").count() == 2
    assert Submission.objects.count() == 4 and Photo.objects.count() == 4
    assert sorted(Listing.objects.values_list("status", flat=True)) == [
        "pending",
        "published",
        "published",
        "withdrawn",
    ]
    assert Agency.objects.get().people.count() == 2
    credentials = json.loads(target.read_text())
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert credentials["password"] not in output.getvalue()
    secrets = []
    for user in User.objects.filter(mfa_enabled=True):
        name = user.username.removeprefix("fixture-v1-")
        secret = credentials["accounts"][name]["totp_secret"]
        assert decrypt(user.mfa_secret_encrypted) == secret and secret not in output.getvalue()
        secrets.append(secret)
    assert len(set(secrets)) == 3
    before = target.read_bytes()
    call_command("seed_demo", credentials_file=str(target), stdout=output)
    assert target.read_bytes() == before and User.objects.count() == 8
    public = Client()
    for listing in Listing.objects.all():
        assert public.get(f"/es/listing/{listing.pk}/").status_code == (
            200 if listing.status == "published" else 404
        )


@pytest.mark.django_db(transaction=True)
def test_demo_fixture_refuses_production_and_existing_namespace(settings, tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "Long-synthetic-fixture-password!873")
    target = tmp_path / "credentials.json"
    settings.PRODUCTION = True
    with pytest.raises(CommandError):
        call_command("seed_demo", credentials_file=str(target))
    assert not User.objects.exists() and not target.exists()
    settings.PRODUCTION = False
    user = User.objects.create_user(
        username="fixture-v1-individual", email="untouched@example.invalid"
    )
    with pytest.raises(CommandError):
        call_command("seed_demo", credentials_file=str(target))
    user.refresh_from_db()
    assert user.email == "untouched@example.invalid" and not target.exists()


@pytest.mark.django_db(transaction=True)
def test_demo_credential_write_failure_rolls_back_accounts_and_owned_media(
    request, tmp_path, monkeypatch, settings
):
    request.getfixturevalue("photo_environment")
    monkeypatch.setenv("DEMO_PASSWORD", "Long-synthetic-fixture-password!873")
    from apps.core.management.commands import seed_demo

    def fail_write(*args, **kwargs):
        raise OSError("Synthetic credential write failure")

    monkeypatch.setattr(seed_demo.json, "dump", fail_write)
    target = tmp_path / "credentials.json"
    with pytest.raises(OSError):
        call_command("seed_demo", credentials_file=str(target), stdout=io.StringIO())
    assert not User.objects.exists() and not Photo.objects.exists() and not target.exists()
    assert not any(path.is_file() for path in settings.MEDIA_ROOT.rglob("*"))
