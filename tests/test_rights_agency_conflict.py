"""Fresh agency conflict checks preserve historical relationships and exact scope."""

from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.core.models import Agency, AgencyMember, User
from apps.safety.rights_scope import agency_conflict

pytestmark = pytest.mark.django_db


def test_agency_conflict_observes_relationship_changes_without_stale_user_cache():
    owner = User.objects.create_user(username="scope-owner", email="scope-owner@example.invalid")
    reviewer = User.objects.create_user(username="scope-reviewer", email="scope-reviewer@example.invalid")
    peer = User.objects.create_user(username="scope-peer", email="scope-peer@example.invalid")
    agency = Agency.objects.create(name="Synthetic scope", owner=owner)
    other = Agency.objects.create(name="Other synthetic scope", owner=peer)

    def check(actor, scope, expected):
        with CaptureQueriesContext(connection) as queries:
            assert agency_conflict(actor, scope) is expected
        assert len(queries) == (1 if scope else 0)

    check(owner, agency.pk, True)
    check(reviewer, agency.pk, False)
    check(reviewer, None, False)
    check(reviewer, uuid4(), False)
    member = AgencyMember.objects.create(agency=other, user=reviewer)
    check(reviewer, agency.pk, False)
    check(reviewer, other.pk, True)
    member.active = False
    member.save(update_fields=["active"])
    check(reviewer, other.pk, True)  # Past membership still requires independent review.
    member.delete()
    check(reviewer, other.pk, False)
    member = AgencyMember.objects.create(agency=agency, user=reviewer, active=False)
    check(reviewer, agency.pk, True)
    member.delete()
    check(reviewer, agency.pk, False)
    Agency.objects.filter(pk=agency.pk).update(owner=reviewer)
    check(reviewer, agency.pk, True)
    check(owner, agency.pk, False)
