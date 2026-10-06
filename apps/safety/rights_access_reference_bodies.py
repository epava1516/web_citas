"""Typed historical evidence validation after an authorized coverage read audit."""

from copy import copy

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .models import RightsCopyInformationReview, RightsCopyPageReview
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_copy_inspection import PAGE_SIZE, SECTIONS, inspection_binding
from .rights_copy_page_review import checked_entries
from .rights_exports import canonical


@sensitive_variables()
def validated_bodies(case, coverage, author, source, facts):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Access evidence bodies require enclosing transaction")
    historical = copy(case)
    historical.version = coverage.export.action.expected_version
    result = {}
    for label, reference in facts.items():
        if reference["operation"] == "copy_info_review":
            review = (
                RightsCopyInformationReview.objects.select_for_update(of=("self",))
                .select_related("information")
                .filter(
                    action_id=reference["action"],
                    pk=coverage.information_review_id,
                    information__request=case,
                    outcome="approved",
                )
                .first()
            )
            if not review:
                raise ValidationError("Evidence must be the exact approved access information")
            # The enclosing preparation replay validated its policy, signatures,
            # ciphertext, historical authorization and independent review binding.
            result[label] = {
                "type": "approved_information",
                "body": checked_body(review.information.encrypted_information),
            }
            continue
        if reference["operation"] != "copy_page_save":
            raise ValidationError("Unsupported access evidence body")
        row = (
            RightsCopyPageReview.objects.select_for_update(of=("self",))
            .select_related("action", "read_action")
            .filter(
                action_id=reference["action"],
                request=case,
                actor=author,
                proof_id=coverage.export.proof_id,
                source_digest=coverage.export.information_binding.source_digest,
                purged_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if not row or row.section not in SECTIONS or row.page < 1 or row.version < 1:
            raise ValidationError("Historical access page evidence unavailable")
        read = row.read_action
        read_facts, reason = (
            checked_body(read.encrypted_reason),
            checked_body(row.action.encrypted_reason),
        )
        if (
            not isinstance(read_facts, dict)
            or set(read_facts) != {"purpose", "section", "page"}
            or read_facts["section"] != row.section
            or read_facts["page"] != row.page
            or not isinstance(read_facts["purpose"], str)
            or not isinstance(reason, dict)
            or set(reason) != {"reason"}
        ):
            raise ValidationError("Historical access page audit changed")
        binding = inspection_binding(author, historical, coverage.export.proof, source, row.section)
        read_digest = fingerprint(
            canonical({"binding": binding, "page": row.page, "purpose": read_facts["purpose"]})
        )
        if (
            read.request_id,
            read.actor_id,
            read.expected_version,
            read.operation,
            read.payload_digest,
        ) != (case.pk, author.pk, historical.version, "copy_page_read", read_digest):
            raise ValidationError("Historical page read signature changed")
        entries = checked_body(row.encrypted_entries)
        original = SECTIONS[row.section](source)
        start = (row.page - 1) * PAGE_SIZE
        if start >= len(original) and row.page != 1:
            raise ValidationError("Historical access page outside source")
        clean = checked_entries(source, row.section, original[start : start + PAGE_SIZE], entries)
        expected = fingerprint(
            canonical(
                {
                    "binding": binding,
                    "read": read.pk,
                    "page": row.page,
                    "page_version": row.version - 1,
                    "reason": reason["reason"],
                    "entries": clean,
                }
            )
        )
        if row.action.payload_digest != expected or canonical(clean) != canonical(entries):
            raise ValidationError("Historical access page body signature changed")
        result[label] = {
            "type": "reviewed_page",
            "section": row.section,
            "page": row.page,
            "body": entries,
        }
    return result
