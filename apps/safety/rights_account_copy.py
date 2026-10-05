"""Explicit own-account projection; organization ownership grants no profile access."""

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from apps.listings.models import Favorite

from .rectification_account import locked_subject
from .rights_copy_data import date, legal_acceptances, personal_contacts


@sensitive_variables()
def source(case):
    user = locked_subject(None, case)
    account = {
        field: getattr(user, field)
        for field in ["username", "email", "first_name", "last_name", "role"]
    }
    account.update(
        date_joined=date(user.date_joined),
        last_login=date(user.last_login),
        email_verified_at=date(user.email_verified_at),
        active=user.is_active,
        mfa_enabled=user.mfa_enabled,
    )
    return {
        "schema": "subject-account-copy-v1",
        "partial": True,
        "simulation": True,
        "request_kind": case.kind,
        "pending_review": [
            "additional_rights_information",
            "purpose_inventory",
            "other_account_records",
        ],
        "subject_account": account,
        "legal_acceptances": legal_acceptances(user),
        "account_activity": {
            "personal_contacts": personal_contacts(user),
            "favorites": [
                {"listing_reference": str(item.listing_id), "created_at": date(item.created_at)}
                for item in Favorite.objects.filter(user=user).order_by("pk")
            ],
        },
        "representation": None,
        "profile": None,
        "revisions": [],
    }


@sensitive_variables()
def scope_matches(case, export):
    from .rights_verification import account_source_digest

    if not case.account_subject_id:
        return False
    try:
        return bool(
            export.account_subject_id == case.account_subject_id == export.proof.account_subject_id
            and not case.person_id
            and not export.person_id
            and not export.proof.person_id
            and case.manager_version is None
            and export.manager_version is None
            and export.proof.manager_version is None
            and export.subject_snapshot == str(case.account_subject_id)
            and export.proof.account_source_digest == account_source_digest(case)
        )
    except ValidationError:
        return False
