"""Security boundaries of subject-account correction, before flow integration."""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.safety.rectification_account import source, validate

pytestmark = pytest.mark.django_db(transaction=True)


def test_account_source_is_subject_scoped_and_binds_credentials(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    with pytest.raises(RuntimeError):
        source(person)
    with transaction.atomic():
        person = Person.objects.select_for_update().get(pk=person.pk)
        before = source(person)
        assert before["subject"] == str(person.subject_id)
        assert before["email"] == person.subject.email
        assert person.agency.owner.email != before["email"]
        assert person.subject.password not in str(before)
        user = person.subject
        user.set_password("Synthetic-changed-password!847")
        user.save(update_fields=["password"])
        assert source(person)["authentication_digest"] != before["authentication_digest"]
        person.subject = None
        with pytest.raises(ValidationError, match="Linked subject"):
            source(person)


def test_account_whitelist_and_uniqueness_do_not_mutate_accounts(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    user = person.subject
    before = user.email, user.first_name, user.password, user.session_version
    with transaction.atomic():
        person = Person.objects.select_for_update().get(pk=person.pk)
        assert validate({"first_name": " Synthetic ", "email": "NEW@EXAMPLE.INVALID"}, person) == {
            "first_name": "Synthetic",
            "email": "new@example.invalid",
        }
        for value in [
            {"role": "agency"},
            {"password": "secret"},
            {"username": "other"},
            {"email": person.agency.owner.email.upper()},
            {"email": "invalid"},
            {"first_name": None},
            {"last_name": "x" * 151},
        ]:
            with pytest.raises(ValidationError):
                validate(value, person)
        user.refresh_from_db()
        assert (user.email, user.first_name, user.password, user.session_version) == before
        user.account_erased_at = timezone.now()
        user.save(update_fields=["account_erased_at"])
        with pytest.raises(ValidationError, match="erased"):
            validate({"first_name": "Synthetic"}, person)


def test_account_proposal_http_is_audited_encrypted_and_rejects_stale_source(
    request, settings, monkeypatch
):
    from uuid import uuid4

    from test_rights_responses import ready

    from apps.safety.crypto import unseal
    from apps.safety.models import RightsRectificationProposal

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    user = person.subject
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {
            "operation": "preview",
            "purpose": "Inspect subject account source before proposing correction",
        },
    )
    assert page.status_code == 200
    assert page.context["source_fields"]["account"]["email"] == user.email
    assert page.context["form"].initial["account_email"] == user.email
    assert user.password.encode() not in page.content
    original = user.first_name
    revisions_before = person.listing.revisions.count()
    data = initial | {
        "key": uuid4(),
        "operation": "propose",
        "fields": ["account"],
        "account_first_name": "Synthetic account correction",
        "account_last_name": "Synthetic surname",
        "account_email": "new-subject@example.invalid",
        "reason": "Private scoped account correction justification",
    }
    user.first_name = "Changed source while preparing proposal"
    user.save(update_fields=["first_name"])
    assert staff.post(path, data).status_code == 409
    assert not RightsRectificationProposal.objects.exists()
    user.first_name = original
    user.save(update_fields=["first_name"])
    assert staff.post(path, data).status_code == 302
    proposal = RightsRectificationProposal.objects.get()
    assert unseal(proposal.encrypted_changes)["account"] == {
        "first_name": data["account_first_name"],
        "last_name": data["account_last_name"],
        "email": data["account_email"],
    }
    assert data["account_email"] not in proposal.encrypted_changes
    user.refresh_from_db()
    assert user.first_name == original and user.email != data["account_email"]
    assert person.listing.revisions.count() == revisions_before
    assert staff.get(path).context["source_fields"] is None


def test_account_wait_precedes_revision_and_blob_locks_and_refreshes_credentials(
    request, settings, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue

    from django.db import connection, connections
    from test_photo_reuse_races import observe_blocked
    from test_rights_responses import ready

    from apps.core.accounts import token_user_state
    from apps.core.models import User
    from apps.listings.models import Revision
    from apps.mediafiles.models import Blob
    from apps.safety.rights_rectification import source_snapshot
    from apps.safety.rights_scope import locked_case

    case, _, _, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    blob = revision.photos.first().blob
    pids = Queue()

    def reading():
        connections.close_all()
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
                locked_request, locked_person, listing = locked_case(case.pk, lock_listing=True)
                return source_snapshot(locked_request, locked_person, listing)[1]["account"]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=person.subject_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(reading)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            # These rows must remain available while the snapshot waits for User.
            Revision.objects.select_for_update(nowait=True).get(pk=revision.pk)
            Blob.objects.select_for_update(nowait=True).get(pk=blob.pk)
            user.set_password("Synthetic-password-changed-during-wait!847")
            user.save(update_fields=["password"])
            expected_digest = token_user_state(user)
        result = future.result(timeout=10)
    assert result["authentication_digest"] == expected_digest
    assert user.password not in str(result)
