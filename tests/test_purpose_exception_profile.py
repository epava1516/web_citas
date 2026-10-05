"""A profile-scoped exception cannot mutate publication or agency responsibilities."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.db import transaction
from django.test import Client
from django.utils import timezone
from test_processing_plans import REASON
from test_purpose_exception_consumption import approved, payload
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready
from test_rights_verification import read

from apps.core.models import Agency, User
from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import source_manifest
from apps.safety.models import PurposeExceptionReview, PurposeRestriction
from apps.safety.processing_plans import prepare
from apps.safety.processing_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def test_actual_profile_restriction_and_exception_preserve_publication_and_agency(
    request, settings, monkeypatch
):
    import test_purpose_exception_preparation

    original_act = test_purpose_exception_preparation.act
    profile = []

    def profile_prepared(request, settings, monkeypatch):
        case, actor, _, _, _, person = ready(request, settings, monkeypatch, "restriction")
        profile.append(person)
        favorite = Favorite.objects.create(user=person.subject, listing=person.listing)
        with transaction.atomic():
            manifest = source_manifest(person, case)
        decisions = [
            dict(
                purpose=p,
                operation="restrict" if p == "account_preferences" else "continue",
                basis=REASON,
                reason=REASON,
                scope=REASON,
                review_on=(timezone.localdate() + timedelta(days=7)).isoformat(),
            )
            for p in sorted({item["purpose"] for item in manifest["entries"]})
        ]
        plan = prepare(actor, case.pk, uuid4(), case.version, REASON, decisions)
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
        record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
        record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
        return case, actor, person.subject, plan, favorite, client

    def profile_link(user, case_id, key, version, operation, reason, **options):
        if operation == "link" and "link_account_id" in options:
            options = {"link_listing_id": profile[0].listing.pk}
        return original_act(user, case_id, key, version, operation, reason, **options)

    monkeypatch.setattr(test_purpose_exception_preparation, "prepared", profile_prepared)
    monkeypatch.setattr(test_purpose_exception_preparation, "act", profile_link)
    case, actor, _, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    person = profile[0]
    listing = person.listing
    original = (
        listing.status,
        listing.approved_revision_id,
        listing.lifecycle_version,
        person.manager_version,
    )
    agencies = list(Agency.objects.order_by("pk").values())
    assert case.person_id == person.pk and case.account_subject_id is None
    assert plan.inventory.person_id == person.pk and plan.inventory.account_subject_id is None
    result = execute(actor, case.pk, plan.pk, **payload(case, proposal))
    assert (
        PurposeExceptionReview.objects.get(proposal=proposal).consumed_action_id == result.action_id
    )
    assert not Favorite.objects.filter(pk=favorite.pk).exists()
    person.refresh_from_db()
    listing.refresh_from_db()
    assert (
        listing.status,
        listing.approved_revision_id,
        listing.lifecycle_version,
        person.manager_version,
    ) == original
    assert list(Agency.objects.order_by("pk").values()) == agencies
    assert PurposeRestriction.objects.get().active
