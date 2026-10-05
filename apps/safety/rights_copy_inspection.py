"""Audited page inspection; never authorizes release of a complete reviewed copy."""

import uuid

from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .models import RightsAction
from .rights import fingerprint
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_scope import permitted

PAGE_SIZE = 10
SECTIONS = {
    "revisions": lambda source: source["revisions"],
    "legal_acceptances": lambda source: source["legal_acceptances"],
    "favorites": lambda source: source["account_activity"]["favorites"],
    "verifications": lambda source: (source.get("representation") or {}).get("verifications", []),
    "representation_history": lambda source: (source.get("representation") or {}).get(
        "history", []
    ),
}
SALT = "rights-copy-inspection-v1"


@transaction.atomic
@sensitive_variables()
def inspect_page(user, case_id, version, key, purpose, section="revisions", page=1, cursor=""):
    caller_session_version = user.session_version
    caller_mfa_version = user.mfa_version
    if (
        section not in SECTIONS
        or type(page) is not int
        or page < 1
        or not 10 <= len(purpose.strip()) <= 200
    ):
        raise ValidationError("Invalid copy inspection page")
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    if (
        not actor.has_perm("safety.review_rights_request")
        or not actor.mfa_enabled
        or actor.session_version != caller_session_version
        or actor.mfa_version != caller_mfa_version
        or not permitted(actor, case)
    ):
        raise PermissionDenied
    if case.version != version:
        raise ValidationError("Request changed")
    proof = can_prepare(actor, case, person)
    source = source_copy(person, listing, case)
    binding = {
        "actor": actor.pk,
        "session": actor.session_version,
        "mfa": actor.mfa_version,
        "case": str(case.pk),
        "version": case.version,
        "proof": str(proof.pk),
        "source": fingerprint(canonical(source)),
        "section": section,
    }
    if cursor:
        try:
            received = signing.loads(cursor, salt=SALT, max_age=3600)
        except signing.BadSignature as error:
            raise ValidationError("Invalid or expired inspection cursor") from error
        if received != binding:
            raise ValidationError("Copy inspection source changed")
    elif page != 1:
        raise ValidationError("Inspect the first page before continuing")
    rows = SECTIONS[section](source)
    start = (page - 1) * PAGE_SIZE
    if start >= len(rows) and page != 1:
        raise ValidationError("Inspection page unavailable")
    signature = fingerprint(canonical({"binding": binding, "page": page, "purpose": purpose}))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_page_read"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting inspection key")
    else:
        try:
            with transaction.atomic():
                RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=version,
                    operation="copy_page_read",
                    payload_digest=signature,
                    encrypted_reason=seal({"purpose": purpose, "section": section, "page": page}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting inspection key") from error
    fresh = User.objects.get(pk=actor.pk)
    if (
        not fresh.has_perm("safety.review_rights_request")
        or not fresh.has_perm("safety.execute_rights_request")
        or not fresh.mfa_enabled
        or fresh.session_version != actor.session_version
        or fresh.mfa_version != actor.mfa_version
        or not permitted(fresh, case)
    ):
        raise PermissionDenied
    return {
        "schema": "rights-copy-inspection-page-v1",
        "inspection_only": True,
        "section": section,
        "page": page,
        "entries": rows[start : start + PAGE_SIZE],
        "has_next": start + PAGE_SIZE < len(rows),
        "cursor": signing.dumps(binding, salt=SALT),
        "next_key": str(uuid.uuid4()),
    }
