"""Profile operations reject account authority before accessing editorial resources."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from test_account_only_rectification import verified
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import RightsAction
from apps.safety.privacy_holds import hold
from apps.safety.rectification_recipients import prepare as recipients
from apps.safety.rectification_uploads import discard

pytestmark = pytest.mark.django_db(transaction=True)


def test_profile_consumers_reject_checked_account_without_side_effects(request, settings):
    case, actor, _, subject = verified(request, settings)
    actor.user_permissions.add(Permission.objects.get(codename="review_rectification"))
    actor = User.objects.get(pk=actor.pk)
    before = RightsAction.objects.count(), case.version, case.scope_status
    reason = "Independent synthetic own account scope request"
    operations = [
        lambda: hold(actor, case.pk, uuid4(), case.version, reason, "accuracy"),
        lambda: recipients(actor, case.pk, uuid4(), uuid4(), case.version, reason),
        lambda: discard(actor, case.pk, uuid4(), case.version, uuid4(), reason),
    ]
    for operation in operations:
        with pytest.raises(ValidationError, match="Profile scope required"):
            operation()
    case.refresh_from_db()
    assert (RightsAction.objects.count(), case.version, case.scope_status) == before
    subject.refresh_from_db()
    assert subject.first_name == ""
