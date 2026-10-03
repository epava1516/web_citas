import pytest
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_intake import data
from test_rights_linking import link, ready
from test_rights_messages import clarification

from apps.core.models import Person
from apps.safety.models import RightsAccess, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


def test_new_message_requires_fresh_audited_read_before_link(request):
    # Make this request through its real public receipt so the requester can reply.
    request.getfixturevalue("directory")
    client = Client()
    response = client.post("/en/safety/rights/", data(client, kind="representation"))
    case = RightsRequest.objects.get()
    from django.contrib.auth.models import Permission
    from test_report_inspection import reviewer
    from test_rights_assignment import action

    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    path, claim = action(staff, case, "claim")
    staff.post(path, claim)
    inspect = f"/en/moderation/rights/{case.pk}/"
    staff.post(inspect, {"purpose": "Read current request reference before linking"})
    assert RightsAccess.objects.get().case_version == 2
    client.post(response.url, clarification(client, response.url))
    person = Person.objects.get(subject__username="fixture-v1-individual")
    path, linked = link(staff, case, person)
    assert staff.post(path, linked).status_code == 409
    case.refresh_from_db()
    assert case.person_id is None and case.version == 3
    staff.post(inspect, {"purpose": "Read newly submitted clarification and reference"})
    assert staff.post(path, linked).status_code == 302
    assert set(RightsAccess.objects.values_list("case_version", flat=True)) == {2, 3}


def test_legacy_or_older_page_read_does_not_authorize_current_link(request):
    case, user, staff = ready(request)
    inspect = f"/en/moderation/rights/{case.pk}/"
    RightsAccess.objects.filter(request=case).update(case_version=None)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    path, linked = link(staff, case, person)
    assert staff.post(path, linked).status_code == 409
    assert (
        staff.post(
            inspect,
            {"purpose": "Read earlier clarification page in this request", "message_before": 1},
        ).status_code
        == 200
    )
    assert staff.post(path, linked).status_code == 409
    assert (
        staff.post(
            inspect, {"purpose": "Read current reference and latest clarification page"}
        ).status_code
        == 200
    )
    assert staff.post(path, linked).status_code == 302
