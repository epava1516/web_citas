"""Offline typed database reconciliation. Physical deletion is a separate stage."""

import uuid
from hashlib import sha256

from cryptography.fernet import InvalidToken
from django.conf import settings
from django.db import connection, models, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import (
    AccountToken,
    Person,
    PhoneChallenge,
    RecoveryCode,
    RepresentationInvitation,
    User,
)
from apps.listings.models import Favorite, Listing, PublicationState, Rate, Revision
from apps.mediafiles.models import Blob, Photo
from scripts.recovery_ledger import LedgerIntegrityError, digest
from scripts.recovery_receipts import validate_receipt

from .crypto import seal, unseal
from .models import (
    RecoveryApplication,
    RecoveryMediaJob,
    RightsExport,
    RightsExportImage,
    RightsExportPart,
)
from .recovery_ownership import validate_empty_replacement, validate_ownership


def queue_media(application, receipt):
    for reference in receipt["references"].get("media_jobs", []):
        paths = reference["paths"]
        person_id = receipt["subject"] if receipt["scope"] == "person" else None
        if (
            Photo.objects.filter(blob_id=reference["blob"])
            .exclude(revision__listing__person_id=person_id)
            .exists()
        ):
            raise LedgerIntegrityError("Recovery media became shared")
        names = [path for path in paths.values() if path]
        if (
            Blob.objects.exclude(pk=reference["blob"])
            .filter(models.Q(original__in=names) | models.Q(derivative__in=names))
            .exists()
        ):
            raise LedgerIntegrityError("Recovery storage path became shared")
        blob = Blob.objects.select_for_update().filter(pk=reference["blob"]).first()
        job, created = RecoveryMediaJob.objects.select_for_update().get_or_create(
            application=application,
            blob_reference=reference["blob"],
            defaults={"blob": blob, "encrypted_paths": seal(paths)},
        )
        present = any(
            path and Blob._meta.get_field(field).storage.exists(path)
            for field, path in paths.items()
        )
        # Existing queued/failed jobs retain their retry budget and backoff.
        # Only a completed job can start a new cycle when files reappear.
        if created or (present and job.status == "completed"):
            job.encrypted_paths, job.status = seal(paths), "queued"
            job.attempts, job.completed_at, job.next_attempt_at = 0, None, timezone.now()
            job.save(
                update_fields=[
                    "encrypted_paths",
                    "status",
                    "attempts",
                    "completed_at",
                    "next_attempt_at",
                ]
            )
            if blob:
                blob.status, blob.phash, blob.signature, blob.regional_hashes = (
                    "erasing",
                    "",
                    {},
                    [],
                )
                blob.sha256 = uuid.uuid4().hex + uuid.uuid4().hex
                blob.width = blob.height = 0
                blob.save(
                    update_fields=[
                        "status",
                        "sha256",
                        "phash",
                        "signature",
                        "regional_hashes",
                        "width",
                        "height",
                    ]
                )


@sensitive_variables()
def apply_database(receipt):
    selected = set(receipt["purposes"])
    refs = receipt["references"]
    person = (
        Person.objects.select_for_update().filter(pk=receipt["subject"]).first()
        if receipt["scope"] == "person"
        else None
    )
    account = (
        User.objects.select_for_update().filter(pk=refs["account"]["id"]).first()
        if "account" in refs
        else None
    )
    now = timezone.now()
    if account:
        if "authentication" in selected:
            AccountToken.objects.filter(user=account).delete()
            RecoveryCode.objects.filter(user=account).delete()
        if "account_preferences" in selected:
            Favorite.objects.filter(user=account).delete()
        if "account" in selected:
            marker = uuid.UUID(receipt["execution"]).hex
            account.username, account.email = "erased-" + marker, marker + "@example.invalid"
            account.first_name = account.last_name = ""
            account.email_verified_at = account.last_login = None
            account.is_active, account.role = False, "visitor"
            account.mfa_secret_encrypted, account.mfa_enabled, account.mfa_last_counter = (
                "",
                False,
                -1,
            )
            account.account_erased_at = now
            account.set_unusable_password()
        account.session_version = max(
            account.session_version + 1, refs["account"]["minimum_session_version"]
        )
        account.mfa_version = max(account.mfa_version + 1, refs["account"]["minimum_mfa_version"])
        account.save()
    if person:
        listings = Listing.objects.filter(person=person)
        revisions = Revision.objects.filter(listing__person=person)
        if "contact" in selected:
            PhoneChallenge.objects.filter(person=person).delete()
        if "representation" in selected:
            RepresentationInvitation.objects.filter(person=person).delete()
            person.consent_revoked_at, person.age_status = now, "pending"
        if "shared_contact_review" in selected:
            person.phone_claim = None
            revisions.update(
                phone="", whatsapp=False, edit_version=models.F("edit_version") + 1, updated_at=now
            )
        if selected & {"representation", "shared_contact_review"}:
            listings.update(
                status=models.Case(
                    models.When(status="published", then=models.Value("paused")),
                    default=models.F("status"),
                ),
                available_until=None,
                lifecycle_version=models.F("lifecycle_version") + 1,
            )
        if "publication" in selected:
            Rate.objects.filter(revision__listing__person=person).delete()
            for revision in revisions:
                revision.categories.clear()
                revision.services.clear()
                revision.travel_areas.clear()
            revisions.update(
                status="withdrawn",
                edit_version=models.F("edit_version") + 1,
                title="",
                description="",
                description_alternative="",
                profile_type="",
                municipality=None,
                postal_code=None,
                zone=None,
                spoken_languages=[],
                days=[],
                time_slot="",
                reception=False,
                travel=False,
                phone="",
                whatsapp=False,
                telegram="",
                contact_exposure_accepted=False,
                updated_at=now,
            )
            listings.update(
                status="withdrawn",
                approved_revision=None,
                available_until=None,
                published_at=None,
                expires_at=None,
                lifecycle_version=models.F("lifecycle_version") + 1,
            )
            # Restored projections also contain publication text and dates.
            # Reapply the selected erasure before any asynchronous refresh.
            PublicationState.objects.filter(listing__person=person).delete()
            person.publication_erased_at = now
        if "profile" in selected:
            person.alias, person.assigned_editor = "", None
        if "media" in selected:
            Photo.objects.filter(revision__listing__person=person).update(
                removed_at=now, approved=False, comparison_complete=True
            )
            shared = [reference for reference in refs["resources"]["photos"] if reference["shared"]]
            for reference in shared:
                replacement = reference.get("replacement", str(uuid.uuid4()))
                placeholder, _ = Blob.objects.select_for_update().get_or_create(
                    pk=replacement,
                    defaults={
                        "sha256": sha256(
                            ("recovery-placeholder:" + replacement).encode()
                        ).hexdigest(),
                        "status": "erased",
                    },
                )
                validate_empty_replacement(placeholder, person.pk)
                Photo.objects.filter(
                    pk=reference["photo"], revision__listing__person=person
                ).update(blob=placeholder)
        person.rights_version = max(
            person.rights_version + 1, refs["person"]["minimum_rights_version"]
        )
        person.manager_version = max(
            person.manager_version, refs["person"]["minimum_manager_version"]
        )
        person.save()
    if "transient_copy" in selected:
        exports = (
            RightsExport.objects.filter(person=person, account_subject_id=None)
            if receipt["scope"] == "person" and person
            else RightsExport.objects.filter(account_subject_id=receipt["subject"], person_id=None)
            if receipt["scope"] == "account"
            else RightsExport.objects.none()
        )
        from .rights_object_content import purge_export_objects

        purge_export_objects(exports)
        RightsExportImage.objects.filter(export__in=exports).update(encrypted_content="")
        RightsExportPart.objects.filter(export__in=exports).update(encrypted_content="")
        exports.update(encrypted_payload="", purged_at=now)


@sensitive_variables()
def reconcile(store, start):
    if not getattr(settings, "RECOVERY_MODE", False) or connection.in_atomic_block:
        raise RuntimeError("Explicit isolated recovery mode and no outer transaction required")
    receipts = store.recover(start)
    for receipt in receipts:
        validate_receipt(receipt)
    applied = 0
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [82940101])
        for receipt in receipts:
            signature = digest(receipt)
            previous = (
                RecoveryApplication.objects.select_for_update()
                .filter(pk=receipt["execution"])
                .first()
            )
            if previous:
                if (
                    previous.receipt_digest != signature
                    or previous.scope != receipt["scope"]
                    or previous.subject_reference != receipt["subject"]
                ):
                    raise LedgerIntegrityError("Conflicting recovery application")
                try:
                    if unseal(previous.encrypted_receipt) != receipt:
                        raise LedgerIntegrityError("Recovery audit receipt changed")
                except (InvalidToken, ValueError, TypeError) as error:
                    raise LedgerIntegrityError("Recovery audit receipt invalid") from error
                queue_media(previous, receipt)
                continue
            validate_ownership(receipt)
            application = RecoveryApplication.objects.create(
                execution_id=receipt["execution"],
                scope=receipt["scope"],
                subject_reference=receipt["subject"],
                receipt_digest=signature,
                encrypted_receipt=seal(receipt),
            )
            queue_media(application, receipt)
            apply_database(receipt)
            applied += 1
    return {
        "applied": applied,
        "pending_media_jobs": RecoveryMediaJob.objects.exclude(status="completed").count(),
        "publication_authorized": False,
    }
