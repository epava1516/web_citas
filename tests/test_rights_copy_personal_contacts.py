"""Copies include only the subject account's phone claims, with reviewed redaction."""

from copy import deepcopy
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_compilation import review_all
from test_rights_exports import prepared

from apps.core.models import Agency, PhoneClaim
from apps.safety.crypto import unseal
from apps.safety.rights_copy_inspection import inspect_page
from apps.safety.rights_copy_page_review import generate_pages, record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_personal_phone_claims_exclude_managers_and_allow_redaction_before_delivery(
    request, settings, monkeypatch, account_only
):
    if account_only:
        case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, _, _, _, person = prepared(request, settings)
        subject = person.subject
    owned = PhoneClaim.objects.create(
        phone="+34960000091",
        individual=subject,
        verified_at=timezone.now(),
        verification_procedure="synthetic-procedure",
    )
    pending = PhoneClaim.objects.create(phone="+34960000092", individual=subject)
    foreign = PhoneClaim.objects.create(phone="+34960000093", individual=actor)
    shared = PhoneClaim.objects.create(phone="+34960000094", agency=Agency.objects.first())
    read = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect account-owned contact claims",
        section="personal_contacts",
    )
    assert {row["phone"] for row in read["entries"]} >= {owned.phone, pending.phone}
    assert not {foreign.phone, shared.phone} & {row["phone"] for row in read["entries"]}
    assert (
        next(row for row in read["entries"] if row["phone"] == pending.phone)["verified_at"] is None
    )
    assert all(row["scope"] == "account_owned_claim" for row in read["entries"])
    entries = deepcopy(read["entries"])
    entries[0]["phone"] = foreign.phone
    with pytest.raises(ValidationError):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            0,
            "Reject foreign telephone injected into contact page",
            entries,
        )
    review_all(case, actor)
    current = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect contacts before final redaction",
        section="personal_contacts",
    )
    edited = deepcopy(current["entries"])
    for row in edited:
        row["phone"] = ""
    record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        current["read_id"],
        current["page_version"],
        "Redact telephone values in delivered private copy",
        edited,
    )
    export = generate_pages(
        actor, case.pk, case.version, uuid4(), "Deliver reviewed account-owned contact claims"
    )
    contacts = unseal(export.encrypted_payload)["account_activity"]["personal_contacts"]
    assert contacts and all(row["phone"] == "" for row in contacts)
    owned.refresh_from_db()
    assert owned.phone == "+34960000091"


def test_changed_contact_verification_invalidates_previously_read_page(request, settings):
    case, actor, _, _, _, person = prepared(request, settings)
    claim = PhoneClaim.objects.create(phone="+34960000095", individual=person.subject)
    read = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect contact before verification changes",
        section="personal_contacts",
    )
    claim.verified_at = timezone.now()
    claim.verification_procedure = "changed-synthetic-procedure"
    claim.save(update_fields=["verified_at", "verification_procedure"])
    with pytest.raises(ValidationError, match="source changed"):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            0,
            "Reject contact decision with obsolete verification",
            read["entries"],
        )
