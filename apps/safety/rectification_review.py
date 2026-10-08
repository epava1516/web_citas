"""Independent review of proposed changes; no mutation of profile/publication."""

import json
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsRectificationExecution,
    RightsRectificationProposal,
    RightsRectificationProposalRead,
    RightsRectificationReview,
    RightsRectificationSourceRead,
    RightsRequest,
)
from .rights import allowed, fingerprint
from .rights_rectification import source_snapshot, validate_copy, validated_changes
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private


def permission(user):
    if not user.mfa_enabled or not all(
        user.has_perm(value)
        for value in [
            "safety.review_rights_request",
            "safety.execute_rights_request",
            "safety.review_rectification",
        ]
    ):
        raise PermissionDenied


@sensitive_variables()
def current(user, case_id, proposal_id, version):
    permission(user)
    case, person, listing = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    proposal = (
        RightsRectificationProposal.objects.select_for_update()
        .filter(
            pk=proposal_id,
            action__request=case,
            person=person,
            account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if not proposal:
        raise ValidationError("Correction proposal unavailable / Propuesta no disponible")
    if proposal.action.actor_id == user.pk:
        raise PermissionDenied("Independent reviewer required")
    if (
        case.kind != "rectify"
        or case.version != version
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect current assigned correction case / Consulta el expediente asignado vigente"
        )
    latest = (
        RightsRectificationProposal.objects.filter(action__request=case)
        .order_by("-created_at", "-pk")
        .first()
    )
    proof = authorized_proof(case, person, "rectify")
    revision, source = source_snapshot(case, person, listing)
    # Source reads may wait on User/Revision/Blob; authority must still be current afterward.
    proof = authorized_proof(case, person, "rectify")
    digest = fingerprint(json.dumps(source, sort_keys=True))
    if (
        latest.pk != proposal.pk
        or proof.created_at <= proposal.created_at
        or digest != proposal.source_digest
        or not RightsRectificationSourceRead.objects.filter(
            request=case, actor=user, proof=proof, case_version=case.version, source_digest=digest
        ).exists()
    ):
        raise ValidationError(
            "Review current source with fresh scoped proof / Revisa la fuente vigente con nueva comprobación de ámbito"
        )
    changes = validated_changes(unseal(proposal.encrypted_changes), person, case)
    validate_copy(changes, revision, person, case)
    return case, proposal, proof, changes


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, proposal_id, version, purpose):
    case, proposal, proof, changes = current(user, case_id, proposal_id, version)
    if not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Access purpose required / Motivo de consulta obligatorio")
    RightsRectificationProposalRead.objects.create(
        proposal=proposal,
        actor=user,
        proof=proof,
        case_version=case.version,
        changes_digest=fingerprint(json.dumps(changes, sort_keys=True)),
        purpose=purpose,
    )
    return changes


@transaction.atomic
@sensitive_variables()
def review(user, case_id, proposal_id, key, version, outcome, reason):
    permission(user)
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    proposal = RightsRectificationProposal.objects.filter(
        pk=proposal_id,
        action__request=case,
        person=person,
        account_subject_id=case.account_subject_id,
    ).first()
    if not proposal or proposal.action.actor_id == user.pk:
        raise PermissionDenied
    signature = fingerprint(
        json.dumps(
            {"proposal": proposal_id, "version": version, "outcome": outcome, "reason": reason},
            sort_keys=True,
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "rectify_review"
            and previous.payload_digest == signature
        ):
            return RightsRectificationReview.objects.get(action=previous)
        raise ValidationError("Conflicting review key / Clave incompatible")
    case, proposal, proof, changes = current(user, case_id, proposal_id, version)
    digest = fingerprint(json.dumps(changes, sort_keys=True))
    if (
        outcome not in {"approved", "rejected"}
        or not 20 <= len(reason.strip()) <= 2000
        or RightsRectificationReview.objects.filter(proposal=proposal).exists()
        or not RightsRectificationProposalRead.objects.filter(
            proposal=proposal,
            actor=user,
            proof=proof,
            case_version=case.version,
            changes_digest=digest,
        ).exists()
    ):
        raise ValidationError(
            "Read proposed changes before motivated review / Consulta los cambios antes de revisión motivada"
        )
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_review",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = RightsRectificationReview.objects.create(
                proposal=proposal,
                action=action,
                proof=proof,
                outcome=outcome,
                changes_digest=digest,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting review / Revisión incompatible") from error
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return result


class ReviewForm(forms.Form):
    def __init__(self, *args, language="es", **kwargs):
        from .rectification_presentation import caption

        super().__init__(*args, **kwargs)
        self.fields["operation"].label = "Operation" if language == "en" else "Operación"
        self.fields["outcome"].label = "Outcome" if language == "en" else "Decisión"
        for field in self.fields.values():
            field.label = caption(field.label, language)
            if hasattr(field, "choices"):
                field.choices = [
                    (value, caption(label, language)) for value, label in field.choices
                ]

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar propuesta (auditoría) / Inspect proposal (audited)"),
            ("review", "Registrar revisión / Record review"),
            (
                "confirm_email",
                "Solicitar confirmación de nuevo correo / Request new email confirmation",
            ),
            ("notify", "Comunicar propuesta aprobada / Communicate approved proposal"),
            ("execute", "Ejecutar rectificación recibida / Execute received correction"),
        ]
    )
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[
            ("approved", "Aprobar para ejecución posterior / Approve for later execution"),
            ("rejected", "Rechazar propuesta / Reject proposal"),
        ],
    )
    reason = forms.CharField(
        required=False,
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )


@login_required
@sensitive_post_parameters("purpose", "reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, proposal_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    try:
        permission(request.user)
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    proposal = RightsRectificationProposal.objects.filter(
        pk=proposal_id, action__request=case
    ).first()
    if not case or not proposal:
        raise Http404
    if not permitted(request.user, case) or proposal.action.actor_id == request.user.pk:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ReviewForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid.uuid4(), "version": case.version},
    )
    changes = None
    photo_selection = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            data = form.cleaned_data
            if data["operation"] == "inspect":
                changes = inspect(
                    request.user, case_id, proposal_id, data["version"], data["purpose"]
                )
                if "photos" in changes:
                    photo_selection = changes["photos"]
                    changes = {
                        **changes,
                        "photos": (
                            (
                                "Selection shown below"
                                if request.LANGUAGE_CODE == "en"
                                else "Selección mostrada abajo"
                            )
                            if photo_selection
                            else (
                                "No photos" if request.LANGUAGE_CODE == "en" else "Sin fotografías"
                            )
                        ),
                    }
                if "location" in changes:
                    from .rectification_location import display

                    changes = {**changes, "location": display(changes["location"])}
                if "catalog" in changes:
                    from .rectification_catalog import display as display_catalog

                    changes = {
                        **changes,
                        "catalog": display_catalog(
                            changes["catalog"], request.LANGUAGE_CODE == "en"
                        ),
                    }
                if "rates" in changes:
                    from .rectification_rates import display as display_rates

                    changes = {
                        **changes,
                        "rates": display_rates(changes["rates"], request.LANGUAGE_CODE == "en"),
                    }
                if "contacts" in changes:
                    from .rectification_contacts import display as display_contacts

                    changes = {
                        **changes,
                        "contacts": display_contacts(
                            changes["contacts"], request.LANGUAGE_CODE == "en"
                        ),
                    }
                if "account" in changes:
                    from .rectification_account import display as display_account

                    changes = {
                        **changes,
                        "account": display_account(
                            changes["account"], request.LANGUAGE_CODE == "en"
                        ),
                    }
                if "details" in changes:
                    from .rectification_details import display as display_details

                    changes = {
                        **changes,
                        "details": display_details(changes["details"], request.LANGUAGE_CODE),
                    }
                status = 200
            elif data["operation"] == "confirm_email":
                from .account_email_confirmation import start

                start(
                    request.user,
                    case_id,
                    proposal_id,
                    data["key"],
                    data["version"],
                    data["reason"],
                    request.LANGUAGE_CODE,
                )
                return private(redirect("rights_inspect", case_id=case.pk))
            elif data["operation"] in {"notify", "execute"}:
                from .rectification_execution import execute, notify

                action = notify if data["operation"] == "notify" else execute
                action(
                    request.user, case_id, proposal_id, data["key"], data["version"], data["reason"]
                )
                return private(redirect("rights_inspect", case_id=case.pk))
            else:
                review(
                    request.user,
                    case_id,
                    proposal_id,
                    data["key"],
                    data["version"],
                    data["outcome"],
                    data["reason"],
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
            "safety/rectification_review.html",
            {
                "case": case,
                "form": form,
                "changes": changes,
                "photo_selection": photo_selection,
                "execution": RightsRectificationExecution.objects.filter(
                    notification__review__proposal=proposal
                )
                .only("pk")
                .first(),
            },
            status=status,
        )
    )
