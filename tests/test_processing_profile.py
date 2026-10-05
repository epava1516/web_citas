"""Purpose preparation/review preserves profile publication and shared organization."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.db import transaction
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready
from test_rights_verification import read

from apps.core.models import User
from apps.safety.erasure_inventory import source_manifest
from apps.safety.processing_plans import prepare
from apps.safety.processing_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("kind", ["restriction", "object"])
def test_profile_prepare_and_independent_review_preserve_publication(
    request, settings, monkeypatch, kind
):
    request.getfixturevalue("directory")
    case, actor, _, _, _, person = ready(request, settings, monkeypatch, kind)
    listing = person.listing
    original = (
        person.manager_version,
        person.rights_version,
        person.agency_id,
        listing.status,
        listing.lifecycle_version,
        case.version,
        case.initial_due_at,
    )
    reason = "Synthetic independent treatment review of the selected profile purposes"
    with transaction.atomic():
        manifest = source_manifest(person, case)
    values = [
        dict(
            purpose=purpose,
            operation="continue",
            basis=reason,
            reason=reason,
            scope=reason,
            review_on=(timezone.localdate() + timedelta(days=7)).isoformat(),
        )
        for purpose in sorted({item["purpose"] for item in manifest["entries"]})
    ]
    plan = prepare(actor, case.pk, uuid4(), case.version, reason, values)
    assert plan.person_id == person.pk and plan.account_subject_id is None
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_processing_plan",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    _, body = record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", reason)
    assert body["manifest"]["person"] == str(person.pk)
    result, _ = record(
        reviewer, case.pk, plan.pk, uuid4(), case.version, "review", reason, "approved"
    )
    assert result.outcome == "approved"
    person.refresh_from_db()
    listing.refresh_from_db()
    case.refresh_from_db()
    assert (
        person.manager_version,
        person.rights_version,
        person.agency_id,
        listing.status,
        listing.lifecycle_version,
        case.version,
        case.initial_due_at,
    ) == original
