"""Synthetic signed suffixes test ordering/atomicity, not real new rights decisions."""

from copy import deepcopy
from uuid import uuid4

import pytest
from test_erasure_execution import payload, plan_fixture
from test_recovery_apply import stored_receipt
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken, RecoveryCode
from apps.listings.models import Favorite
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryApplication, RecoveryOutbox
from apps.safety.recovery_apply import reconcile
from scripts.recovery_ledger import LedgerIntegrityError

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("second_kind", ["valid", "foreign", "conflicting", "invalid_schema"])
def test_signed_multiple_events_apply_atomically_or_reject_whole_suffix(
    request, settings, monkeypatch, tmp_path, second_kind
):
    case, actor, _, _, _, person, plan, _, _, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    account = person.subject
    tokens = list(AccountToken.objects.filter(user=account))
    codes = list(RecoveryCode.objects.filter(user=account))
    favorites = list(Favorite.objects.filter(user=account))
    execution = execute(actor, case.pk, plan.pk, **payload(case))
    first = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    AccountToken.objects.bulk_create(tokens)
    RecoveryCode.objects.bulk_create(codes)
    Favorite.objects.bulk_create(favorites)
    before = type(account).objects.filter(pk=account.pk).values().get()
    second = deepcopy(first)
    second["execution"] = str(uuid4()) if second_kind != "conflicting" else first["execution"]
    second["references"]["account"]["minimum_session_version"] += 3
    second["references"]["person"]["minimum_rights_version"] += 3
    if second_kind == "foreign":
        second["references"]["resources"]["favorites"] = [
            str(Favorite.objects.get(user=outsider, listing=person.listing).pk)
        ]
    elif second_kind == "invalid_schema":
        second["purposes"].append("unknown_synthetic_purpose")
    store, start = stored_receipt(tmp_path, first)
    encoded, _ = store.codec.append(store.checkpoint(), str(uuid4()), second)
    store.append(encoded)
    settings.RECOVERY_MODE = True
    if second_kind != "valid":
        with pytest.raises(LedgerIntegrityError):
            reconcile(store, start)
        assert not RecoveryApplication.objects.exists()
        assert AccountToken.objects.filter(user=account).count() == len(tokens)
        assert RecoveryCode.objects.filter(user=account).count() == len(codes)
        assert Favorite.objects.filter(user=account).count() == len(favorites)
        assert type(account).objects.filter(pk=account.pk).values().get() == before
    else:
        assert reconcile(store, start)["applied"] == 2
        account.refresh_from_db()
        person.refresh_from_db()
        assert account.session_version >= second["references"]["account"]["minimum_session_version"]
        assert person.rights_version >= second["references"]["person"]["minimum_rights_version"]
        assert not AccountToken.objects.filter(user=account).exists()
        assert not RecoveryCode.objects.filter(user=account).exists()
        assert not Favorite.objects.filter(user=account).exists()
        assert RecoveryApplication.objects.count() == 2
        after = type(account).objects.filter(pk=account.pk).values().get()
        assert reconcile(store, start)["applied"] == 0
        assert type(account).objects.filter(pk=account.pk).values().get() == after
    assert Favorite.objects.filter(user=outsider, listing=person.listing).exists()
