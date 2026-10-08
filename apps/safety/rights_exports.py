"""Reviewed subject-scoped private copy; outstanding content remains explicit."""

import hashlib
import json
import uuid
from datetime import timedelta

from cryptography.fernet import InvalidToken
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.accounts import limited
from apps.core.models import User

from .crypto import cipher, seal, unseal
from .models import (
    RightsAction,
    RightsExport,
    RightsExportDownload,
    RightsExportImage,
    RightsExportPart,
    RightsExportPreview,
    RightsImageAccess,
    RightsRequest,
)
from .rectification_presentation import caption
from .rights import allowed, fingerprint
from .rights_copy_data import contact_data, image_inventory, subject_data
from .rights_scope import locked_case, permitted
from .rights_verification import PROCEDURE, authorized_proof, complete_read, enabled
from .views import private

# Keep intermediate ORM objects bounded while amortizing five relation queries.
COPY_REVISION_BATCH_SIZE = 250


@sensitive_variables()
def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


@sensitive_variables()
def source_copy(person, listing, case=None):
    if case and case.account_subject_id:
        from .rights_account_copy import source

        return source(case)
    # Same account lock as preference writers; held through snapshot generation.
    if person.subject_id:
        User.objects.select_for_update(no_key=True).get(pk=person.subject_id)
    revisions = []
    if listing:
        # Profile lock prevents a cooperating editor adding another revision mid-copy.
        from apps.catalog.models import Category, Municipality, Service
        from apps.listings.models import Rate
        from apps.mediafiles.models import Photo

        records = (
            listing.revisions.select_for_update(of=("self",))
            .select_related("municipality", "postal_code", "zone")
            .order_by("created_at", "pk")
            .prefetch_related(
                Prefetch(
                    "categories",
                    queryset=Category.objects.order_by("slug"),
                    to_attr="copy_categories",
                ),
                Prefetch(
                    "services", queryset=Service.objects.order_by("slug"), to_attr="copy_services"
                ),
                Prefetch(
                    "travel_areas",
                    queryset=Municipality.objects.order_by("code"),
                    to_attr="copy_travel_areas",
                ),
                Prefetch("rates", queryset=Rate.objects.order_by("pk"), to_attr="copy_rates"),
                Prefetch(
                    "photos",
                    queryset=Photo.objects.select_related("blob").order_by("created_at", "pk"),
                    to_attr="copy_photos",
                ),
            )
        )
        for revision in records.iterator(chunk_size=COPY_REVISION_BATCH_SIZE):
            revisions.append(
                {
                    "revision": str(revision.pk),
                    "status": revision.status,
                    "created_at": revision.created_at.isoformat(),
                    "title": revision.title,
                    "description": revision.description,
                    "description_alternative": revision.description_alternative,
                    "profile_type": revision.profile_type,
                    "content_language": revision.content_language,
                    "categories": [item.slug for item in revision.copy_categories],
                    "services": [item.slug for item in revision.copy_services],
                    "municipality": revision.municipality.code
                    if revision.municipality_id
                    else None,
                    "postal_code": revision.postal_code.code if revision.postal_code_id else None,
                    "zone": revision.zone.code if revision.zone_id else None,
                    "travel_areas": [item.code for item in revision.copy_travel_areas],
                    "spoken_languages": revision.spoken_languages,
                    "days": revision.days,
                    "time_slot": revision.time_slot,
                    "reception": revision.reception,
                    "travel": revision.travel,
                    "contacts": contact_data(person, revision),
                    "images": image_inventory(revision),
                    "rates": [
                        {
                            "concept": rate.concept,
                            "mode": rate.mode,
                            "amount": str(rate.amount) if rate.amount is not None else None,
                            "currency": rate.currency,
                            "duration_minutes": rate.duration_minutes,
                        }
                        for rate in revision.copy_rates
                    ],
                }
            )
    subject = subject_data(person)
    return {
        "schema": "subject-profile-copy-v2",
        "partial": True,
        "simulation": True,
        "pending_review": [
            "image_content",
            "shared_contacts",
            "additional_rights_information",
            *([] if subject["subject_account"] else ["unlinked_subject_account"]),
        ],
        **subject,
        "profile": {
            "alias": person.alias,
            "created_at": person.created_at.isoformat(),
            "listing": {
                "reference": str(listing.pk),
                "status": listing.status,
                "created_at": listing.created_at.isoformat(),
                "published_at": listing.published_at.isoformat() if listing.published_at else None,
                "expires_at": listing.expires_at.isoformat() if listing.expires_at else None,
                "available_until": listing.available_until.isoformat()
                if listing.available_until
                else None,
                "approved_revision": str(listing.approved_revision_id)
                if listing.approved_revision_id
                else None,
            }
            if listing
            else None,
        },
        "revisions": revisions,
    }


@sensitive_variables()
def reviewed_copy(source, value):
    # JSONField accepts objects directly and rejects invalid JSON before this service.
    if not isinstance(value, dict) or set(value) != set(source):
        raise ValidationError("Copy schema changed / Esquema de copia cambiado")
    expected = json.loads(canonical(source))
    try:
        if expected["profile"] is not None:
            alias = value["profile"]["alias"]
            if not isinstance(alias, str) or len(alias) > 80:
                raise ValueError
            expected["profile"]["alias"] = alias
        if expected["subject_account"] is not None:
            for field, maximum in [
                ("username", 150),
                ("email", 254),
                ("first_name", 150),
                ("last_name", 150),
            ]:
                text = value["subject_account"][field]
                if not isinstance(text, str) or len(text) > maximum:
                    raise ValueError
                # Redaction may remove material, but cannot add a different account identity.
                if text not in [expected["subject_account"][field], ""]:
                    raise ValueError
                expected["subject_account"][field] = text
        if "personal_contacts" in expected.get("account_activity", {}):
            original_contacts = expected["account_activity"]["personal_contacts"]
            changed_contacts = value["account_activity"]["personal_contacts"]
            if not isinstance(changed_contacts, list) or len(changed_contacts) != len(
                original_contacts
            ):
                raise ValueError
            for original_contact, changed_contact in zip(
                original_contacts, changed_contacts, strict=True
            ):
                phone = changed_contact["phone"]
                if phone not in [original_contact["phone"], ""]:
                    raise ValueError
                original_contact["phone"] = phone
        if len(value["revisions"]) != len(expected["revisions"]):
            raise ValueError
        for original, edited in zip(expected["revisions"], value["revisions"], strict=True):
            for field in ["title", "description", "description_alternative"]:
                text = edited[field]
                if not isinstance(text, str) or len(text) > (120 if field == "title" else 10000):
                    raise ValueError
                original[field] = text
            if edited["contacts"]["phone"] not in [original["contacts"]["phone"], ""]:
                raise ValueError
            original["contacts"]["phone"] = edited["contacts"]["phone"]
            if not edited["contacts"]["phone"]:
                original["contacts"]["whatsapp"] = False
            if len(edited["images"]) != len(original["images"]):
                raise ValueError
            for image, changed in zip(original["images"], edited["images"], strict=True):
                if not isinstance(changed["content_included"], bool):
                    raise ValueError
                image["content_included"] = changed["content_included"]
                code = changed["exclusion_code"]
                if code not in {"", "awaiting_review", "third_party", "unavailable"}:
                    raise ValueError
                if image["content_included"] != (code == ""):
                    raise ValueError
                image["exclusion_code"] = code
            if len(edited["rates"]) != len(original["rates"]):
                raise ValueError
            for rate, changed in zip(original["rates"], edited["rates"], strict=True):
                if not isinstance(changed["concept"], str) or len(changed["concept"]) > 80:
                    raise ValueError
                rate["concept"] = changed["concept"]
    except (TypeError, ValueError, KeyError, IndexError) as error:
        raise ValidationError("Invalid reviewed copy / Copia revisada no válida") from error
    if canonical(expected) != canonical(value):
        raise ValidationError("Only text redaction allowed / Solo se permite revisar los textos")
    return expected


def reviewer_case(user, case_id):
    case, person, listing = locked_case(case_id, lock_listing=True)
    if (
        not user.has_perm("safety.review_rights_request")
        or not user.mfa_enabled
        or not permitted(user, case)
    ):
        raise PermissionDenied
    return case, person, listing


def can_prepare(user, case, person):
    if not user.has_perm("safety.execute_rights_request"):
        raise PermissionDenied
    if (
        case.kind not in {"access", "portability"}
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
    ):
        raise ValidationError(
            "Inspect assigned access request / Consulta la solicitud de acceso asignada"
        )
    return authorized_proof(case, person, case.kind)


@transaction.atomic
@sensitive_variables()
def preview(user, case_id, version, purpose):
    case, person, listing = reviewer_case(user, case_id)
    if case.version != version or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError(
            "Request changed or purpose required / Solicitud cambiada o motivo obligatorio"
        )
    can_prepare(user, case, person)
    source = source_copy(person, listing, case)
    RightsExportPreview.objects.create(
        request=case,
        actor=user,
        case_version=case.version,
        source_digest=fingerprint(canonical(source)),
        purpose=purpose,
    )
    return source


@transaction.atomic
@sensitive_variables()
def generate(user, case_id, key, version, reason, copy, *, information_review_id=None):
    case, person, listing = reviewer_case(user, case_id)
    if not user.has_perm("safety.execute_rights_request"):
        raise PermissionDenied
    if case.kind == "portability":
        raise ValidationError(
            "Portability requires independently approved field selection / "
            "La portabilidad requiere una selección de campos aprobada independientemente"
        )
    signature_input = {"version": version, "reason": reason, "copy": copy}
    if information_review_id is not None:
        signature_input["information_review"] = information_review_id
        signature_input["session"] = user.session_version
        signature_input["mfa"] = user.mfa_version
        from apps.core.models import User

        from .rights_copy_page_review import fresh_authority

        fresh = User.objects.get(pk=user.pk)
        if not fresh.is_active:
            raise PermissionDenied
        fresh_authority(fresh, case, user.session_version, user.mfa_version)
    signature = fingerprint(canonical(signature_input))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "export"
            and previous.payload_digest == signature
        ):
            export = RightsExport.objects.select_related("proof").get(action=previous)
            if information_review_id is not None:
                from .models import RightsExportInformationBinding
                from .rights_copy_page_review import validate_generated_scope
                from .rights_information_export import validate_export_binding

                binding = RightsExportInformationBinding.objects.filter(
                    export=export, review_id=information_review_id
                ).first()
                if not binding:
                    raise ValidationError("Export information binding unavailable")
                validate_generated_scope(
                    case, person, listing, export, user, version, binding.source_digest
                )
                validate_export_binding(case, person, export)
                fresh_authority(
                    User.objects.get(pk=user.pk), case, user.session_version, user.mfa_version
                )
            return export
        raise ValidationError("Conflicting export key / Clave de exportación incompatible")
    if case.version != version or not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError(
            "Request changed or reason required / Solicitud cambiada o motivo obligatorio"
        )
    proof = can_prepare(user, case, person)
    source = source_copy(person, listing, case)
    if not RightsExportPreview.objects.filter(
        request=case,
        actor=user,
        case_version=case.version,
        source_digest=fingerprint(canonical(source)),
    ).exists():
        raise ValidationError("Preview current source first / Consulta primero la copia actual")
    cleaned = reviewed_copy(source, copy)
    information_review, information = None, None
    if information_review_id is not None:
        from uuid import uuid5

        from .rights_information_export import consume_approved

        information_review, information = consume_approved(
            user,
            case.pk,
            version,
            information_review_id,
            uuid5(key, "approved-information-use"),
            reason,
        )
        cleaned["additional_information"] = {
            "access": information["access"],
            "policy": {
                "version": information_review.information.policy_version,
                "language": information_review.information.policy_document.language,
                "digest": information_review.information.policy_digest,
            },
        }
        cleaned["pending_review"] = [
            item for item in cleaned["pending_review"] if item != "additional_rights_information"
        ]
    from apps.mediafiles.models import Blob, Photo

    selected_ids = [
        image["photo"]
        for revision in cleaned["revisions"]
        for image in revision["images"]
        if image["content_included"]
    ]
    list(
        Blob.objects.select_for_update()
        .filter(
            pk__in=Photo.objects.filter(
                pk__in=selected_ids, revision__listing__person=person
            ).values("blob_id")
        )
        .order_by("pk")
    )

    def audited_snapshots():
        for revision in cleaned["revisions"]:
            for image in revision["images"]:
                if not image["content_included"]:
                    continue
                photo, content = image_content(person, image["photo"])
                if not RightsImageAccess.objects.filter(
                    request=case,
                    actor=user,
                    photo=photo,
                    case_version=case.version,
                    content_digest=hashlib.sha256(content).hexdigest(),
                ).exists():
                    raise ValidationError(
                        "Inspect each selected image first / Consulta cada imagen seleccionada"
                    )
                yield image, photo, content

    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="export",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            export = RightsExport.objects.create(
                action=action,
                proof=proof,
                person=person,
                account_subject_id=case.account_subject_id,
                case_version=case.version + 1,
                manager_version=person.manager_version if person else None,
                subject_snapshot=str(person.subject_id or "")
                if person
                else str(case.account_subject_id),
                channel_digest=case.receipt_digest,
                encrypted_payload="",
                expires_at=min(proof.expires_at, timezone.now() + timedelta(hours=24)),
            )
            if information_review is not None:
                from .models import RightsExportInformationBinding

                row = information_review.information
                export.expires_at = min(export.expires_at, row.expires_at)
                export.save(update_fields=["expires_at"])
                RightsExportInformationBinding.objects.create(
                    export=export,
                    review=information_review,
                    source_digest=row.source_digest,
                    information_digest=fingerprint(row.encrypted_information),
                    policy_digest=row.policy_digest,
                    inspection_digest=information_review.read.action.payload_digest,
                    decision_digest=information_review.action.payload_digest,
                )
            for image, photo, content in audited_snapshots():
                attachment = RightsExportImage.objects.create(
                    export=export, photo=photo, encrypted_content=cipher().encrypt(content).decode()
                )
                image["attachment"] = str(attachment.pk)
            if all(
                image["content_included"] or image["exclusion_code"] == "third_party"
                for revision in cleaned["revisions"]
                for image in revision["images"]
            ):
                if "image_content" in cleaned["pending_review"]:
                    cleaned["pending_review"].remove("image_content")
            from .rights_copy_parts import packages

            cleaned["parts"] = []
            snapshots = (
                (attachment.pk, cipher().decrypt(attachment.encrypted_content.encode()))
                for attachment in export.images.order_by("created_at", "pk").iterator(chunk_size=1)
            )
            for position, package in enumerate(packages(snapshots), start=1):
                part = RightsExportPart.objects.create(
                    export=export,
                    position=position,
                    attachments=package["attachments"],
                    encrypted_content=cipher().encrypt(package["content"]).decode(),
                )
                cleaned["parts"].append(
                    {
                        "id": str(part.pk),
                        "position": position,
                        "attachments": package["attachments"],
                    }
                )
            from .rights_data_parts import stored_payload

            export.encrypted_payload = stored_payload(export, cleaned)
            export.save(update_fields=["encrypted_payload"])
    except IntegrityError as error:
        raise ValidationError("Conflicting export key / Clave incompatible") from error
    case.version += 1
    case.scope_status = "unverified"
    # Partial copy is not a final resolution of the access/portability request.
    case.save(update_fields=["version", "scope_status"])
    if information_review_id is not None:
        from .rights_information_export import validate_export_binding

        validate_export_binding(case, person, export)
        fresh_authority(User.objects.get(pk=user.pk), case, user.session_version, user.mfa_version)
    return export


class ReviewedCopyField(forms.JSONField):
    def prepare_value(self, value):
        return "" if value is None else super().prepare_value(value)


class CopyPresentationForm(forms.Form):
    """Static captions only; legacy constructors and JSON contents remain unchanged."""

    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, **kwargs)
        if language is not None:
            for field in self.fields.values():
                field.label = caption(field.label, language)
                if hasattr(field, "choices") and not hasattr(field, "queryset"):
                    field.choices = [
                        (value, caption(label, language)) for value, label in field.choices
                    ]
            for name, pair in {
                "operation": ("Operación", "Operation"),
                "section": ("Sección", "Section"),
                "page": ("Página", "Page"),
            }.items():
                if name in self.fields:
                    self.fields[name].label = pair[language == "en"]
            if "section" in self.fields:
                names = {
                    "profile": ("Perfil", "Profile"),
                    "subject_account": ("Cuenta del titular", "Subject account"),
                    "revisions": ("Revisiones", "Revisions"),
                    "legal_acceptances": ("Aceptaciones legales", "Legal acceptances"),
                    "favorites": ("Favoritos", "Favorites"),
                    "personal_contacts": ("Contactos personales", "Personal contacts"),
                    "agency_relationships": ("Relaciones con agencias", "Agency relationships"),
                    "verifications": ("Verificaciones", "Verifications"),
                    "representation_history": (
                        "Historial de representación",
                        "Representation history",
                    ),
                }
                self.fields["section"].choices = [
                    (value, names[value][language == "en"])
                    for value, _ in self.fields["section"].choices
                ]


class PageReviewForm(CopyPresentationForm):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.CharField(initial="save_page", widget=forms.HiddenInput)
    read_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    page_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado de revisión / Private review reason",
    )
    entries = ReviewedCopyField(
        widget=forms.Textarea, label="Entradas revisadas / Reviewed entries"
    )


class ExportForm(CopyPresentationForm):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("preview", "Consultar copia (auditoría) / Preview copy (audited)"),
            ("inspect_page", "Consultar sección por páginas / Inspect section pages"),
            ("inspect_saved_page", "Consultar decisiones guardadas / Inspect saved decisions"),
            ("compile_pages", "Compilar páginas revisadas / Compile reviewed pages"),
            ("generate_pages", "Generar desde páginas revisadas / Generate from reviewed pages"),
            (
                "generate_pages_with_information",
                "Generar páginas con información aprobada / Generate pages with approved information",
            ),
            ("generate", "Crear copia revisada / Create reviewed copy"),
        ]
    )
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )
    reason = forms.CharField(
        required=False,
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado de entrega / Private release reason",
    )
    section = forms.ChoiceField(
        required=False,
        choices=[
            (name, name)
            for name in [
                "profile",
                "subject_account",
                "revisions",
                "legal_acceptances",
                "favorites",
                "personal_contacts",
                "agency_relationships",
                "verifications",
                "representation_history",
            ]
        ],
    )
    page = forms.IntegerField(required=False, min_value=1, initial=1)
    information_review_id = forms.IntegerField(
        required=False,
        min_value=1,
        label="Referencia de aprobación de información / Information approval reference",
    )
    review_id = forms.IntegerField(
        required=False, min_value=1, label="Referencia de revisión / Review reference"
    )
    cursor = forms.CharField(required=False, max_length=2000, widget=forms.HiddenInput)
    copy = ReviewedCopyField(
        required=False,
        widget=forms.Textarea,
        label="Copia revisada; redacta datos ajenos / Reviewed copy; redact other people's data",
    )


@login_required
@sensitive_post_parameters("copy", "reason", "purpose", "entries")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ExportForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid.uuid4(), "version": case.version},
    )
    page_review_form = None
    saved_page = None
    saved_page_data = None
    if request.method == "POST" and request.POST.get("operation") == "save_page":
        form = PageReviewForm(request.POST, language=request.LANGUAGE_CODE)
    status = 400 if request.method == "POST" else 200
    source = None
    page_data = None
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            if values["operation"] == "save_page":
                from .rights_copy_page_review import record

                saved_page = record(
                    request.user,
                    case_id,
                    values["version"],
                    values["key"],
                    values["read_id"],
                    values["page_version"],
                    values["reason"],
                    values["entries"],
                )
                form = ExportForm(
                    language=request.LANGUAGE_CODE,
                    initial={"key": uuid.uuid4(), "version": case.version},
                )
                status = 200
            elif values["operation"] == "inspect_saved_page":
                from .rights_copy_page_review import inspect_saved

                saved_page_data = inspect_saved(
                    request.user,
                    case_id,
                    values["version"],
                    values["key"],
                    values["review_id"],
                    values["purpose"],
                )
                status = 200
            elif values["operation"] == "inspect_page":
                from .rights_copy_inspection import inspect_page

                page_data = inspect_page(
                    request.user,
                    case_id,
                    values["version"],
                    values["key"],
                    values["purpose"],
                    values["section"] or "revisions",
                    values["page"] or 1,
                    values["cursor"],
                )
                page_review_form = PageReviewForm(
                    language=request.LANGUAGE_CODE,
                    initial={
                        "key": uuid.uuid4(),
                        "version": case.version,
                        "operation": "save_page",
                        "read_id": page_data["read_id"],
                        "page_version": page_data["page_version"],
                        "entries": page_data["entries"],
                    },
                )
                status = 200
            elif values["operation"] in {"generate_pages", "generate_pages_with_information"}:
                from .rights_copy_page_review import generate_pages

                information_id = (
                    values["information_review_id"]
                    if values["operation"] == "generate_pages_with_information"
                    else None
                )
                if (
                    values["operation"] == "generate_pages_with_information"
                    and information_id is None
                ):
                    raise ValidationError("Information approval reference required")
                generate_pages(
                    request.user,
                    case_id,
                    values["version"],
                    values["key"],
                    values["reason"],
                    information_review_id=information_id,
                )
                return private(redirect("rights_inspect", case_id=case.pk))
            elif values["operation"] == "compile_pages":
                from .rights_copy_page_review import compile_pages

                source = compile_pages(
                    request.user, case_id, values["version"], values["key"], values["reason"]
                )
                status = 200
                form = ExportForm(
                    language=request.LANGUAGE_CODE,
                    initial={
                        "key": uuid.uuid4(),
                        "version": case.version,
                        "operation": "generate",
                        "copy": source,
                    },
                )
            elif values["operation"] == "preview":
                source = preview(request.user, case_id, values["version"], values["purpose"])
                status = 200
                form = ExportForm(
                    language=request.LANGUAGE_CODE,
                    initial={
                        "key": uuid.uuid4(),
                        "version": case.version,
                        "operation": "generate",
                        "copy": source,
                    },
                )
            else:
                generate(
                    request.user,
                    case_id,
                    values["key"],
                    values["version"],
                    values["reason"],
                    values["copy"],
                )
                return private(redirect("rights_inspect", case_id=case.pk))
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/rights_export.html",
            {
                "case": case,
                "form": form,
                "source": source,
                "page_data": page_data,
                "page_review_form": page_review_form,
                "saved_page": saved_page,
                "saved_page_data": saved_page_data,
                "source_photos": [
                    image for revision in source["revisions"] for image in revision["images"]
                ]
                if source
                else [],
            },
            status=status,
        )
    )


@require_POST
@sensitive_variables()
def download(request, case_id, secret, export_id, image_id=None, part_id=None):
    if not enabled():
        raise Http404
    with transaction.atomic():
        try:
            case, person, _ = locked_case(case_id)
        except (RightsRequest.DoesNotExist, ValidationError):
            raise Http404 from None
        if (
            len(secret) != 43
            or not constant_time_compare(case.receipt_digest, fingerprint(secret))
            or case.receipt_expires_at <= timezone.now()
        ):
            raise Http404
        export = (
            RightsExport.objects.select_for_update(of=("self",))
            .select_related("proof", "action")
            .filter(pk=export_id, action__request=case)
            .first()
        )
        now = timezone.now()
        scope_matches = False
        if export:
            if case.account_subject_id:
                from .rights_account_copy import scope_matches as account_scope_matches

                scope_matches = account_scope_matches(case, export)
            else:
                scope_matches = bool(
                    person
                    and not export.account_subject_id
                    and not export.proof.account_subject_id
                    and case.person_id == export.person_id == export.proof.person_id
                    and person.manager_version == export.manager_version == case.manager_version
                    and export.subject_snapshot == str(person.subject_id or "")
                    and export.proof.person_rights_version == person.rights_version
                    and export.proof.manager_version == export.manager_version
                )
        if case.kind == "access":
            from .rights_access_close import closure_for_export
        else:
            from .rights_portability_close import closure_for_export

        closure = closure_for_export(case, export) if export else None
        if (
            not export
            or not scope_matches
            or export.expires_at <= now
            or export.purged_at is not None
            or not export.encrypted_payload
            or (
                closure is None
                and (case.version != export.case_version or case.status != "reviewing")
            )
            or export.channel_digest != case.receipt_digest
            or export.proof.provider != "simulator"
            or export.proof.procedure != PROCEDURE
            or export.proof.status != "passed"
            or case.kind not in {"access", "portability"}
            or export.proof.scope != case.kind
            or export.proof.subject_id_snapshot != export.subject_snapshot
            or export.proof.channel_digest != export.channel_digest
            or export.proof.expires_at <= now
            or export.proof.case_version + 1 != export.case_version
            or (
                closure is None
                and case.proofs.order_by("-created_at", "-pk").first().pk != export.proof_id
            )
        ):
            raise Http404
        part = None
        if part_id:
            if image_id:
                raise Http404
            part = RightsExportPart.objects.filter(pk=part_id, export=export).first()
            if not part or not part.encrypted_content:
                raise Http404
        image = None
        if image_id:
            image = RightsExportImage.objects.filter(pk=image_id, export=export).first()
            if not image or not image.encrypted_content:
                raise Http404
        if limited(request, "rights-export-download", limit=30):
            return private(HttpResponse("Too many requests", status=429))
        try:
            key = forms.UUIDField().clean(request.POST.get("key"))
        except ValidationError:
            return private(HttpResponse("Invalid download key", status=400))
        with transaction.atomic():
            recorded, _ = RightsExportDownload.objects.get_or_create(
                key=key,
                defaults={
                    "export": export,
                    "image": image,
                    "part": part,
                    "actor": request.user if request.user.is_authenticated else None,
                },
            )
        if (
            recorded.part_id != part_id
            or recorded.image_id != image_id
            or recorded.export_id != export.pk
            or recorded.actor_id != (request.user.pk if request.user.is_authenticated else None)
        ):
            return private(HttpResponse("Conflicting download key", status=409))
        try:
            delivery_case = case
            final_body = None
            if closure is not None:
                from copy import copy

                if case.kind == "access":
                    from .rights_access_close import validate_closure
                else:
                    from .rights_portability_close import validate_closure

                final_body = validate_closure(closure, case, person)
                delivery_case = copy(case)
                delivery_case.version = export.case_version
                delivery_case.status = "reviewing"
            from .rights_information_export import validate_export_binding

            validate_export_binding(delivery_case, person, export)
            from .rights_portability_export import validate_export_binding as validate_portability

            validate_portability(delivery_case, person, export)
            if part:
                response = HttpResponse(
                    cipher().decrypt(part.encrypted_content.encode()),
                    content_type="application/zip",
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="rights-data-part-{part.position}.zip"'
                    if not part.attachments
                    else 'attachment; filename="rights-part.zip"'
                )
                return private(response)
            if image:
                response = HttpResponse(
                    cipher().decrypt(image.encrypted_content.encode()), content_type="image/webp"
                )
                response["Content-Disposition"] = 'attachment; filename="rights-image.webp"'
                return private(response)
            if case.kind == "access" and final_body is not None:
                from .rights_access_delivery import recipient_payload

                payload = recipient_payload(final_body)
            else:
                payload = unseal(export.encrypted_payload)
            if not isinstance(payload, dict):
                raise Http404
            response = HttpResponse(
                json.dumps(payload, ensure_ascii=False, indent=2),
                content_type="application/json; charset=utf-8",
            )
            response["Content-Disposition"] = (
                'attachment; filename="rights-account.json"'
                if case.account_subject_id
                else 'attachment; filename="rights-profile.json"'
            )
            return private(response)
        except (
            InvalidToken,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValidationError,
            PermissionDenied,
        ):
            raise Http404 from None


@sensitive_variables()
def image_content(person, photo_id):
    from apps.mediafiles.models import Blob, Photo

    photo = Photo.objects.filter(pk=photo_id, revision__listing__person=person).first()
    if not photo:
        raise Http404
    blob = Blob.objects.select_for_update().get(pk=photo.blob_id)
    photo = Photo.objects.select_for_update().get(pk=photo.pk)
    if photo.blob_id != blob.pk or blob.status != "ready" or not blob.derivative:
        raise ValidationError("Image unavailable for review / Imagen no disponible para revisión")
    try:
        with blob.derivative.open("rb") as stream:
            content = stream.read(10 * 1024 * 1024 + 1)
    except OSError:
        raise ValidationError(
            "Image unavailable for review / Imagen no disponible para revisión"
        ) from None
    if (
        len(content) > 10 * 1024 * 1024
        or not content.startswith(b"RIFF")
        or content[8:12] != b"WEBP"
    ):
        raise ValidationError("Image unavailable for review / Imagen no disponible para revisión")
    return photo, content


@login_required
@require_POST
@sensitive_post_parameters("purpose")
@sensitive_variables()
def inspect_image(request, case_id, photo_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    try:
        with transaction.atomic():
            case, person, _ = reviewer_case(request.user, case_id)
            can_prepare(request.user, case, person)
            purpose = request.POST.get("purpose", "")
            if not 10 <= len(purpose.strip()) <= 200:
                return private(HttpResponse("Purpose required", status=400))
            photo, content = image_content(person, photo_id)
            RightsImageAccess.objects.create(
                request=case,
                actor=request.user,
                photo=photo,
                case_version=case.version,
                content_digest=hashlib.sha256(content).hexdigest(),
                purpose=purpose,
            )
    except RightsRequest.DoesNotExist:
        raise Http404 from None
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    except ValidationError:
        return private(
            HttpResponse(
                "Review current scope and image first / Revisa el ámbito y la imagen actual",
                status=409,
            )
        )
    return private(HttpResponse(content, content_type="image/webp"))
