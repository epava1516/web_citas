"""Scoped, audited erasure inventory. Preparation never deletes or closes a request."""

import json
import uuid

from django import forms
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import Agency, AgencyMember, Person
from apps.mediafiles.models import Blob, Photo

from .crypto import seal, unseal
from .models import ErasureInventory, RightsAction, RightsRequest
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)


@sensitive_variables()
def source_manifest(person):
    subject = person.subject_id
    profile = "revision__listing__person"
    scopes = [
        ("core.Person", Q(pk=person.pk), "profile", None),
        ("listings.Listing", Q(person=person), "publication", None),
        (
            "core.PhoneClaim",
            Q(pk=person.phone_claim_id),
            "shared_contact_review",
            ["pk", "phone", "verified_at", "verification_procedure"],
        ),
        ("listings.Revision", Q(listing__person=person), "publication", None),
        ("listings.Rate", Q(revision__listing__person=person), "publication", None),
        ("mediafiles.Photo", Q(**{profile: person}), "media", None),
        (
            "mediafiles.MediaErasure",
            Q(execution__person=person),
            "media",
            ["pk", "blob_id", "status", "attempts", "next_attempt_at", "completed_at"],
        ),
        (
            "mediafiles.UploadAttempt",
            Q(**{profile: person}),
            "media",
            ["pk", "result", "created_at"],
        ),
        (
            "mediafiles.Match",
            Q(photo__revision__listing__person=person)
            | Q(candidate__revision__listing__person=person),
            "evidence",
            ["pk", "decision", "review_version", "resolved_at"],
        ),
        (
            "mediafiles.PhotoRestriction",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "reason_code"],
        ),
        (
            "mediafiles.PhotoAppeal",
            Q(restriction__person=person),
            "evidence",
            ["pk", "status", "result", "resolved_at"],
        ),
        (
            "core.PhoneChallenge",
            Q(person=person),
            "contact",
            ["pk", "manager_version", "expires_at", "used_at"],
        ),
        (
            "core.RepresentationInvitation",
            Q(person=person),
            "representation",
            ["pk", "manager_version", "expires_at", "used_at"],
        ),
        (
            "core.RepresentationAction",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "action", "created_at"],
        ),
        (
            "core.VerificationCheck",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "status", "completed_at"],
        ),
        (
            "core.VerificationEvent",
            Q(verification__person=person),
            "evidence",
            ["pk", "outcome", "created_at"],
        ),
        (
            "core.ManagerReview",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "outcome", "created_at"],
        ),
        (
            "core.ManagerAppeal",
            Q(decision__person=person),
            "evidence",
            ["pk", "status", "result", "resolved_at"],
        ),
        (
            "listings.Submission",
            Q(**{profile: person}),
            "evidence",
            ["pk", "declaration_version", "created_at"],
        ),
        (
            "listings.ModerationDecision",
            Q(**{profile: person}),
            "evidence",
            ["pk", "outcome", "created_at"],
        ),
        (
            "listings.Appeal",
            Q(decision__revision__listing__person=person),
            "evidence",
            ["pk", "status", "result", "resolved_at"],
        ),
        (
            "listings.LifecycleAction",
            Q(listing__person=person),
            "evidence",
            ["pk", "manager_version", "operation", "created_at"],
        ),
        (
            "safety.Report",
            Q(listing__person=person) | Q(reported_subject_id=subject)
            if subject
            else Q(listing__person=person),
            "third_party_evidence",
            ["pk", "version", "status"],
        ),
        ("safety.Restriction", Q(listing__person=person), "evidence", ["pk", "active"]),
        (
            "safety.RightsRequest",
            Q(person=person),
            "third_party_evidence",
            ["pk", "version", "response_version", "status"],
        ),
        (
            "safety.RightsExport",
            Q(person=person),
            "transient_copy",
            ["pk", "expires_at", "purged_at"],
        ),
        (
            "safety.RightsExportImage",
            Q(export__person=person),
            "transient_copy",
            ["pk", "export_id"],
        ),
        (
            "safety.PrivacyPublicationHold",
            Q(person=person),
            "evidence",
            ["pk", "active", "manager_version"],
        ),
    ]
    report_scope = Q(report__listing__person=person)
    complaint_scope = Q(decision__report__listing__person=person) | Q(
        listing_decision__revision__listing__person=person
    )
    for label, scope, fields in [
        ("safety.ReportAccess", report_scope, ["pk", "case_version", "created_at"]),
        (
            "safety.ReportAction",
            report_scope,
            ["pk", "operation", "expected_version", "created_at"],
        ),
        ("safety.ReportNotice", report_scope, ["pk", "status", "attempts", "recovery_version"]),
        ("safety.Complaint", complaint_scope, ["pk", "version", "status"]),
        (
            "safety.ComplaintAction",
            Q(complaint__decision__report__listing__person=person)
            | Q(complaint__listing_decision__revision__listing__person=person),
            ["pk", "operation", "expected_version"],
        ),
        (
            "safety.RightsProof",
            Q(person=person),
            ["pk", "case_version", "manager_version", "scope", "status", "expires_at"],
        ),
        (
            "safety.RightsWithdrawal",
            Q(person=person),
            ["pk", "previous_manager_version", "created_at"],
        ),
        (
            "safety.RightsResponse",
            Q(request__person=person),
            ["pk", "case_version", "response_version", "kind"],
        ),
        (
            "safety.RightsNotice",
            Q(response__request__person=person),
            ["pk", "status", "attempts", "recovery_version"],
        ),
        (
            "safety.RightsImageAccess",
            Q(photo__revision__listing__person=person),
            ["pk", "case_version", "created_at"],
        ),
        ("safety.RightsExportDownload", Q(export__person=person), ["pk", "created_at"]),
    ]:
        scopes.append((label, scope, "dependent_evidence", fields))
    if subject:
        scopes += [
            (
                "core.User",
                Q(pk=subject),
                "account",
                [
                    "pk",
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "is_active",
                    "role",
                    "session_version",
                    "mfa_version",
                ],
            ),
            (
                "core.AccountToken",
                Q(user_id=subject),
                "authentication",
                ["pk", "purpose", "expires_at", "used_at"],
            ),
            ("core.RecoveryCode", Q(user_id=subject), "authentication", ["pk", "used_at"]),
            (
                "core.LegalAcceptance",
                Q(user_id=subject),
                "evidence",
                ["pk", "document_id", "action", "created_at"],
            ),
            ("listings.Favorite", Q(user_id=subject), "account_preferences", ["pk", "created_at"]),
        ]
    entries = []
    for label, scope, purpose, fields in scopes:
        model = apps.get_model(label)
        rows = list(model.objects.filter(scope).order_by("pk").values(*(fields or [])))
        # Raw values never leave this function: no account secret or intake body is read.
        entries.append(
            {
                "model": label,
                "purpose": purpose,
                "count": len(rows),
                "state_digest": fingerprint(canonical(rows)),
                "disposition": "review_required",
            }
        )
    for field in ["categories", "services", "travel_areas"]:
        through = apps.get_model("listings.Revision")._meta.get_field(field).remote_field.through
        rows = list(
            through.objects.filter(revision__listing__person=person).order_by("pk").values()
        )
        entries.append(
            {
                "model": "listings.Revision." + field,
                "purpose": "publication",
                "count": len(rows),
                "state_digest": fingerprint(canonical(rows)),
                "disposition": "review_required",
            }
        )
    blobs = Blob.objects.filter(photos__revision__listing__person=person).distinct().order_by("pk")
    media = []
    for blob in blobs:
        media.append(
            {
                "blob": str(blob.pk),
                "shared_reference": Photo.objects.filter(blob=blob)
                .exclude(revision__listing__person=person)
                .exists(),
                "state_digest": fingerprint(
                    canonical(
                        {
                            "status": blob.status,
                            "original": blob.original.name,
                            "derivative": blob.derivative.name,
                            "sha256": blob.sha256,
                            "phash": blob.phash,
                            "signature": blob.signature,
                            "regional_hashes": blob.regional_hashes,
                        }
                    )
                ),
            }
        )
    shared_phone = bool(
        person.phone_claim_id
        and Person.objects.filter(phone_claim_id=person.phone_claim_id)
        .exclude(pk=person.pk)
        .exists()
    )
    cross_role = bool(
        subject
        and (
            Agency.objects.filter(owner_id=subject).exists()
            or AgencyMember.objects.filter(user_id=subject).exists()
            or Person.objects.filter(individual_id=subject).exclude(pk=person.pk).exists()
            or person.subject.is_staff
            or person.subject.is_superuser
        )
    )
    return {
        "schema": "erasure-inventory-v1",
        "person": str(person.pk),
        "manager_version": person.manager_version,
        "entries": entries,
        "media": media,
        "shared_phone": shared_phone,
        "account_has_other_responsibilities": cross_role,
        "execution_ready": False,
        "pending": [
            "per_purpose_legal_review",
            "dependent_evidence_and_third_party_redaction",
            "unlinked_account_or_orphaned_resources",
            "sessions_logs_cache_cdn_and_backups",
            "recipient_notifications",
            "execution_and_restore_tombstones",
        ],
    }


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, key, version, purpose):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
    ):
        raise PermissionDenied
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    if (
        case.kind != "erase"
        or case.version != version
        or case.assigned_to_id != user.pk
        or not 20 <= len(purpose.strip()) <= 200
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect assigned current erasure request / Consulta la solicitud de supresión asignada actual"
        )
    proof = authorized_proof(case, person, "erase")
    signature = fingerprint(canonical({"version": version, "purpose": purpose}))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "erasure_inventory"
            and previous.payload_digest == signature
        ):
            return ErasureInventory.objects.get(action=previous)
        raise ValidationError("Conflicting action key / Clave incompatible")
    manifest = source_manifest(person)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="erasure_inventory",
                payload_digest=signature,
                encrypted_reason=seal({"reason": purpose}),
            )
            return ErasureInventory.objects.create(
                action=action,
                proof=proof,
                person=person,
                source_digest=fingerprint(canonical(manifest)),
                encrypted_manifest=seal(manifest),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error


class InventoryForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    purpose = forms.CharField(
        min_length=20, max_length=200, label="Finalidad de preparación / Preparation purpose"
    )


@login_required
@sensitive_post_parameters("purpose")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inspect(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    if case.kind != "erase":
        return private(HttpResponse("Unsupported request type", status=409))
    form = InventoryForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    manifest = None
    inventory = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            inventory = prepare(request.user, case.pk, **form.cleaned_data)
            manifest = unseal(inventory.encrypted_manifest)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
    return private(
        render(
            request,
            "safety/erasure_inventory.html",
            {"case": case, "form": form, "manifest": manifest, "inventory": inventory},
            status=status,
        )
    )
