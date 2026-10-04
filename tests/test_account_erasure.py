import uuid

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import Client
from test_erasure_execution import REASON, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.accounts import send_token
from apps.core.models import AccountToken, RecoveryCode
from apps.listings.models import Favorite
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import ErasureExecution

pytestmark = pytest.mark.django_db(transaction=True)
PURPOSES = ["account", "authentication", "account_preferences", "publication"]


def data(case):
    return dict(
        key=uuid.uuid4(), version=case.version, purposes=PURPOSES, reason=REASON, confirmed=True
    )


def test_account_erasure_revokes_access_preserves_audit_and_replays(request, settings, monkeypatch):
    case, actor, _, _, _, person, plan, stored, _, outsider = plan_fixture(
        request, settings, monkeypatch, selected_purposes=PURPOSES
    )
    subject = person.subject
    from apps.core.mfa import encrypt
    from apps.safety.erasure_inventory import prepare
    from apps.safety.erasure_plans import record

    subject.first_name = "Synthetic"
    subject.last_name = "Account subject"
    subject.mfa_enabled = True
    subject.mfa_secret_encrypted = encrypt("JBSWY3DPEHPK3PXP")
    subject.save(update_fields=["first_name", "last_name", "mfa_enabled", "mfa_secret_encrypted"])
    snapshot = prepare(actor, case.pk, uuid.uuid4(), case.version, REASON)
    plan = record(
        actor,
        case.pk,
        snapshot.pk,
        uuid.uuid4(),
        case.version,
        unseal(plan.encrypted_decisions)["decisions"],
    )
    old_email, old_pk = subject.email, subject.pk
    session = Client()
    session.force_login(subject)
    binding = session.session
    binding["mfa_version"] = subject.mfa_version
    binding.save()
    assert session.get("/en/favorites/").status_code == 200
    payload = data(case)
    result = execute(actor, case.pk, plan.pk, **payload)
    subject.refresh_from_db()
    assert subject.pk == old_pk and subject.account_erased_at
    assert subject.email != old_email and subject.email.endswith("@example.invalid")
    assert not subject.is_active and not subject.has_usable_password()
    assert not subject.first_name and not subject.last_name and not subject.email_verified_at
    assert not subject.mfa_enabled and not subject.mfa_secret_encrypted
    assert subject.role == "visitor" and subject.last_login is None
    marker, versions = subject.email, (subject.session_version, subject.mfa_version)
    assert execute(actor, case.pk, plan.pk, **payload).pk == result.pk
    subject.refresh_from_db()
    assert (subject.email, (subject.session_version, subject.mfa_version)) == (marker, versions)
    assert unseal(result.encrypted_result)["account_fields_cleared"]
    assert not AccountToken.objects.filter(user=subject).exists()
    assert not RecoveryCode.objects.filter(user=subject).exists()
    assert not Favorite.objects.filter(user=subject).exists()
    assert Favorite.objects.filter(user=outsider).exists()
    assert session.get("/en/favorites/").status_code == 302
    assert send_token(subject, "verify", "en") is None
    assert not AccountToken.objects.filter(user=subject).exists()
    person.refresh_from_db()
    case.refresh_from_db()
    assert person.subject_id == old_pk and person.publication_erased_at
    assert case.status == "reviewing" and stored.action_id
    assert ErasureExecution.objects.count() == 1


@pytest.mark.parametrize(
    "purposes", [["account"], ["account", "authentication", "account_preferences"]]
)
def test_account_erasure_requires_related_scope_decisions(request, settings, monkeypatch, purposes):
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=PURPOSES
    )
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **(data(case) | {"purposes": purposes}))
    person.subject.refresh_from_db()
    assert person.subject.is_active and not person.subject.account_erased_at
    assert AccountToken.objects.filter(user=person.subject).exists()
    assert not ErasureExecution.objects.exists()


def test_new_other_responsibility_invalidates_account_plan(request, settings, monkeypatch):
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=PURPOSES
    )
    person.subject.groups.add(Group.objects.create(name="Synthetic retained responsibility"))
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **data(case))
    person.subject.refresh_from_db()
    assert person.subject.is_active and not person.subject.account_erased_at
    assert not ErasureExecution.objects.exists()


@pytest.mark.parametrize("purpose", ["reset", "verify"])
def test_inflight_account_token_cannot_reactivate_erased_account(
    request, settings, monkeypatch, purpose
):
    import hashlib
    from concurrent.futures import ThreadPoolExecutor
    from datetime import timedelta
    from threading import Event, current_thread

    from django.db import close_old_connections, connections
    from django.utils import timezone

    from apps.core.accounts import token_user_state
    from apps.core.models import User
    from apps.safety.erasure_inventory import prepare
    from apps.safety.erasure_plans import record

    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=PURPOSES
    )
    raw = "synthetic-account-callback-secret"
    token = AccountToken.objects.create(
        user=person.subject,
        purpose=purpose,
        digest=hashlib.sha256(raw.encode()).hexdigest(),
        user_state=token_user_state(person.subject),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    snapshot = prepare(actor, case.pk, uuid.uuid4(), case.version, REASON)
    plan = record(
        actor,
        case.pk,
        snapshot.pk,
        uuid.uuid4(),
        case.version,
        unseal(plan.encrypted_decisions)["decisions"],
    )
    entered, resume = Event(), Event()
    original = User.objects.select_for_update

    def waiting_lock(*args, **kwargs):
        if current_thread().name.startswith("account_callback"):
            entered.set()
            assert resume.wait(timeout=30)
        return original(*args, **kwargs)

    monkeypatch.setattr(User.objects, "select_for_update", waiting_lock)

    def callback():
        close_old_connections()
        try:
            return (
                Client()
                .post(
                    f"/en/account/token/{token.pk}/{raw}/",
                    {
                        "password": "Synthetic-long-passphrase!734",
                        "confirm": "Synthetic-long-passphrase!734",
                    },
                )
                .status_code
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="account_callback") as pool:
        response = pool.submit(callback)
        try:
            assert entered.wait(timeout=15)
            execute(actor, case.pk, plan.pk, **data(case))
        finally:
            resume.set()
        assert response.result(timeout=30) == 400
    person.subject.refresh_from_db()
    assert person.subject.account_erased_at and not person.subject.is_active
    assert not person.subject.has_usable_password()
    assert not AccountToken.objects.filter(user=person.subject).exists()
