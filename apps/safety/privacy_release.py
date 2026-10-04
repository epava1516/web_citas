"""Independent, notified release of one publication hold; never republishes."""

import json
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .crypto import seal
from .models import PrivacyHoldReleaseProposal, PrivacyPublicationHold, RightsAction, RightsRequest
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read, issue
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private


def source(case, person, listing, hold):
    return fingerprint(
        json.dumps(
            {
                "case": str(case.pk),
                "kind": case.kind,
                "payload": case.encrypted_payload,
                "messages": list(
                    case.messages.order_by("pk").values_list("pk", "encrypted_payload")
                ),
                "manager": person.manager_version,
                "subject": str(person.subject_id or ""),
                "rights_version": person.rights_version,
                "channel": case.receipt_digest,
                "hold": hold.pk,
                "revisions": list(
                    listing.revisions.order_by("pk").values_list("pk", "edit_version", "status")
                )
                if listing
                else [],
                "active": hold.active,
                "ground": hold.ground,
                "listing": None
                if not listing
                else [
                    str(listing.pk),
                    listing.status,
                    listing.lifecycle_version,
                    str(listing.approved_revision_id or ""),
                ],
            },
            sort_keys=True,
            default=str,
        )
    )


def actor_check(user, case, hold):
    if (
        not all(
            user.has_perm("safety." + p)
            for p in [
                "review_rights_request",
                "execute_rights_request",
                "review_privacy_hold",
                "respond_rights_request",
            ]
        )
        or not user.mfa_enabled
        or not permitted(user, case)
    ):
        raise PermissionDenied
    if user.pk == hold.action.actor_id:
        raise PermissionDenied("Independent reviewer required")


def current(user, case, person, hold, version):
    if (
        case.version != version
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or not person
        or case.kind not in {"restriction", "object", "rectify"}
        or hold.proof.scope != case.kind
        or hold.subject_snapshot != str(person.subject_id or "")
        or case.manager_version != person.manager_version
        or hold.person_id != person.pk
        or not hold.active
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect the current assigned request and active hold / Consulta la solicitud asignada y medida vigentes"
        )
    return authorized_proof(case, person, case.kind)


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, key, version, reason):
    case, person, listing = locked_case(case_id, lock_listing=True, allow_version_change=True)
    hold = (
        PrivacyPublicationHold.objects.select_for_update()
        .select_related("action")
        .filter(action__request=case)
        .first()
    )
    if not hold:
        raise ValidationError("Hold unavailable / Medida no disponible")
    actor_check(user, case, hold)
    signature = fingerprint(json.dumps({"version": version, "reason": reason}, sort_keys=True))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "hold_release_plan"
            and previous.payload_digest == signature
        ):
            return PrivacyHoldReleaseProposal.objects.get(action=previous)
        raise ValidationError("Conflicting action key")
    proof = current(user, case, person, hold, version)
    if not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reviewed reason required")
    # Fixed minimized notification: no internal grounds, identifiers or third-party details.
    text = "Se propone levantar la cautela sobre publicación tras revisión independiente. La medida sigue activa hasta nueva comprobación y ejecución. El anuncio permanecerá pausado. Simulación de desarrollo; identidad no comprobada. / Release of the publication hold is proposed after independent review. The hold remains active pending a fresh check and execution. The listing will remain paused. Development simulation; identity not verified."
    try:
        with transaction.atomic():
            response = issue(
                user,
                case.pk,
                uuid.uuid4(),
                case.version,
                case.response_version,
                "progress",
                reason,
                text,
                True,
            )
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="hold_release_plan",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = PrivacyHoldReleaseProposal.objects.create(
                hold=hold,
                action=action,
                proof=proof,
                response=response,
                source_digest=source(case, person, listing, hold),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key") from error
    case.refresh_from_db()
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return result


@transaction.atomic
@sensitive_variables()
def execute(user, case_id, key, version, proposal_id, reason):
    case, person, listing = locked_case(case_id, lock_listing=True, allow_version_change=True)
    proposal = (
        PrivacyHoldReleaseProposal.objects.select_for_update()
        .select_related("hold__action", "response")
        .filter(pk=proposal_id, action__request=case)
        .first()
    )
    if not proposal:
        raise ValidationError("Proposal unavailable")
    hold = (
        PrivacyPublicationHold.objects.select_for_update()
        .select_related("action")
        .get(pk=proposal.hold_id)
    )
    actor_check(user, case, hold)
    signature = fingerprint(
        json.dumps({"version": version, "proposal": proposal_id, "reason": reason}, sort_keys=True)
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "hold_release"
            and previous.payload_digest == signature
        ):
            return PrivacyHoldReleaseProposal.objects.get(released_action=previous)
        raise ValidationError("Conflicting action key")
    proof = current(user, case, person, hold, version)
    ack = getattr(proposal.response, "receipt_acknowledgement", None)
    latest = hold.release_proposals.order_by("-pk").first()
    if (
        proposal.released_at
        or proposal.action.actor_id != user.pk
        or latest.pk != proposal.pk
        or proposal.source_digest != source(case, person, listing, hold)
        or case.response_version != proposal.response.response_version
        or not ack
        or ack.channel_digest != case.receipt_digest
        or proof.pk == proposal.proof_id
        or proof.created_at <= proposal.created_at
        or proof.created_at <= ack.created_at
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError(
            "Current reviewed proposal, prior receipt and fresh check required / Propuesta vigente, recepción previa y nueva comprobación obligatorias"
        )
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="hold_release",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key") from error
    hold.active = False
    hold.save(update_fields=["active"])
    proposal.released_action = action
    proposal.released_proof = proof
    proposal.released_at = timezone.now()
    proposal.save(update_fields=["released_action", "released_proof", "released_at"])
    if listing:
        if listing.status == "published":
            listing.status = "paused"
        listing.available_until = None
        listing.lifecycle_version += 1
        listing.save(update_fields=["status", "available_until", "lifecycle_version"])
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return proposal


class ReleaseForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("propose", "Proponer y comunicar / Propose and notify"),
            ("execute", "Ejecutar propuesta recibida / Execute received proposal"),
        ]
    )
    proposal_id = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, label="Propuesta / Proposal"
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo revisado privado / Private reviewed reason",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review(request, case_id):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + p)
        for p in ["execute_rights_request", "review_privacy_hold", "respond_rights_request"]
    ):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    hold = (
        PrivacyPublicationHold.objects.select_related("action").filter(action__request=case).first()
    )
    if not hold:
        return private(HttpResponse("Hold unavailable", status=409))
    try:
        actor_check(request.user, case, hold)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    form = ReleaseForm(request.POST or None, initial={"key": uuid.uuid4(), "version": case.version})
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        operation = values.pop("operation")
        proposal_id = values.pop("proposal_id")
        try:
            if operation == "propose":
                propose(request.user, case.pk, **values)
            else:
                execute(request.user, case.pk, proposal_id=proposal_id, **values)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("privacy_hold_release", case_id=case.pk))
    proposals = Paginator(
        hold.release_proposals.select_related("response__receipt_acknowledgement").order_by("-pk"),
        50,
    ).get_page(request.GET.get("page"))
    return private(
        render(
            request,
            "safety/privacy_release.html",
            {"case": case, "hold": hold, "proposals": proposals, "form": form},
            status=status,
        )
    )
