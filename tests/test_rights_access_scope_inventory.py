from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information

from apps.core.models import User
from apps.safety.models import RightsAction
from apps.safety.rights_access_scope_store import inspect

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_field_inventory_is_scoped_opaque_stable_and_detects_subject_changes(
    request, settings, monkeypatch, account_only
):
    case, author, _, _, _, person, subject, _, _, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    reason = "Audit synthetic subject record scope before access coverage"
    key = uuid4()
    import apps.safety.rights_access_scope_store as module

    real_source = module.source

    def audited(*args):
        assert RightsAction.objects.filter(key=key, operation="access_scope_read").exists()
        return real_source(*args)

    monkeypatch.setattr(module, "source", audited)
    row, manifest = inspect(author, case.pk, case.version, case.response_version, key, reason)
    assert (
        inspect(author, case.pk, case.version, case.response_version, key, reason)[0].pk == row.pk
    )
    assert manifest["digest"] == row.source_digest
    assert manifest["current_procedure_excluded"] and manifest["pending"]
    assert not any(
        entry["count"]
        for entry in manifest["entries"]
        if entry["model"]
        in ["safety.RightsRequest", "safety.RightsAction", "safety.RightsAccessScopeInventory"]
    )
    owner = subject if account_only else person.subject
    user_entry = next(entry for entry in manifest["entries"] if entry["model"] == "core.User")
    assert user_entry["count"] == 1 and "password" in user_entry["fields"]
    assert owner.password not in str(manifest)
    assert owner.email not in str(manifest)
    assert "core.User.groups" in [entry["model"] for entry in manifest["entries"]]
    before = case.version, case.response_version, case.status
    # A field omitted by the older erasure projection must still change access scope.
    User.objects.filter(pk=owner.pk).update(last_name="Changed synthetic subject identity")
    from django.db import transaction

    with transaction.atomic():
        assert real_source(case, None if account_only else person)["digest"] != manifest["digest"]
    # Account identity proof or the profile snapshot can reject the changed source first.
    with pytest.raises(ValidationError, match="Identity and scope|inventory changed"):
        inspect(author, case.pk, case.version, case.response_version, key, reason)
    User.objects.filter(pk=owner.pk).update(last_name=owner.last_name)
    assert inspect(author, case.pk, case.version, case.response_version, key, reason)[1] == manifest
    stale = User.objects.get(pk=author.pk)
    User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
    with pytest.raises(PermissionDenied):
        inspect(stale, case.pk, case.version, case.response_version, key, reason)
    User.objects.filter(pk=author.pk).update(session_version=author.session_version)
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status) == before
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.tasks import purge_expired_access_scope_inventory

    references = row.action_id, row.request_id, row.proof_id, row.source_digest
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save(update_fields=["expires_at"])
    assert purge_expired_access_scope_inventory() == 1
    assert purge_expired_access_scope_inventory() == 0
    row.refresh_from_db()
    assert row.purged_at and not row.encrypted_inventory
    assert (row.action_id, row.request_id, row.proof_id, row.source_digest) == references
