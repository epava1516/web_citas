"""Authority revocation between request admission and private evidence access."""

import pytest
from django.db.models.query import QuerySet
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import Report, ReportAccess

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("revoked", ["permission", "session", "mfa", "inactive"])
@pytest.mark.parametrize("revoked_during", ["scope", "payload"])
def test_report_inspection_rechecks_authority_after_scope_wait(
    request, monkeypatch, revoked, revoked_during
):
    from apps.safety import views

    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    original_get = QuerySet.get
    original_unseal = views.unseal
    observed = []
    decrypted = []

    def revoke():
        if revoked == "permission":
            User.objects.get(pk=user.pk).user_permissions.clear()
        else:
            values = {
                "session": {"session_version": user.session_version + 1},
                "mfa": {"mfa_version": user.mfa_version + 1},
                "inactive": {"is_active": False},
            }
            User.objects.filter(pk=user.pk).update(**values[revoked])

    def after_scope_wait(query, *args, **kwargs):
        row = original_get(query, *args, **kwargs)
        if query.model is Report and query.query.select_for_update:
            observed.append(row.pk)
            # Deterministic interleaving; real DB and authorization, no fake denial.
            if revoked_during == "scope":
                revoke()
        return row

    def record_decryption(value):
        decrypted.append(value)
        result = original_unseal(value)
        if revoked_during == "payload":
            revoke()
        return result

    monkeypatch.setattr(QuerySet, "get", after_scope_wait)
    monkeypatch.setattr(views, "unseal", record_decryption)
    response = staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect this synthetic report after an interleaved revocation"},
    )
    assert observed == [report.pk]
    assert response.status_code == 403
    assert b"private@example.invalid" not in response.content
    assert bool(decrypted) is (revoked_during == "payload")
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert not ReportAccess.objects.filter(report=report).exists()
