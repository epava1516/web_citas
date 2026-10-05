"""Calendar permission revoked after request entry must hide the response."""

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


def test_calendar_permission_revoked_during_query(request, settings, monkeypatch):
    import apps.safety.publication_calendar_queue as queue
    import apps.safety.publication_purpose_release as module

    original = module.inspect
    checked = []

    def with_query(user, case_id, hold_id, key, version, reason):
        if not checked:
            checked.append(True)
            permission = Permission.objects.get(codename="review_purpose_calendar")
            user.user_permissions.add(permission)
            client = Client()
            client.force_login(user)
            session = client.session
            session["mfa_version"] = user.mfa_version
            session.save()
            authorize = queue.authorize
            revoked = []

            def revoke(actor, case, **kwargs):
                user.user_permissions.remove(permission)
                revoked.append(True)
                return authorize(actor, case, **kwargs)

            try:
                with monkeypatch.context() as scoped:
                    scoped.setattr(queue, "authorize", revoke)
                    response = client.get(
                        reverse("publication_calendar_queue"), {"attention": "all"}
                    )
                assert revoked == [True]
                assert response.status_code == 403
                assert "no-store" in response["Cache-Control"]
                assert b"Review measure" not in response.content
                assert b"Revisar medida" not in response.content
                assert b"cursor" not in response.content
            finally:
                user.user_permissions.add(permission)
        return original(user, case_id, hold_id, key, version, reason)

    monkeypatch.setattr(module, "inspect", with_query)
    run_flow(request, settings, monkeypatch, "restrict", mixed=False)
    assert checked == [True]
