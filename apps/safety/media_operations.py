"""Case-scoped operational recovery; never exposes file paths or deletes in HTTP."""

import uuid

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.models import User
from apps.mediafiles.models import Blob, MediaErasure, MediaErasureRecovery

from .crypto import seal
from .erasure_inventory import canonical
from .models import RightsAction, RightsRequest
from .rights import allowed, fingerprint
from .rights_scope import locked_profile_case as locked_case
from .rights_scope import permitted
from .views import private


def can_recover(user):
    return (
        user.mfa_enabled
        and user.has_perm("safety.review_rights_request")
        and user.has_perm("mediafiles.manage_media_erasure")
    )


def current_recovery_actor(user, session_version, mfa_version):
    actor = User.objects.filter(pk=user.pk).first()
    if (
        actor is None
        or not actor.is_active
        or actor.account_erased_at is not None
        or not actor.mfa_enabled
        or actor.session_version != session_version
        or actor.mfa_version != mfa_version
        or not can_recover(actor)
    ):
        raise PermissionDenied
    return actor


@transaction.atomic
@sensitive_variables()
def requeue(user, case_id, job_id, key, version, reason):
    session_version, mfa_version = user.session_version, user.mfa_version
    user = current_recovery_actor(user, session_version, mfa_version)
    case, _, _ = locked_case(case_id, allow_version_change=True)
    if not permitted(user, case):
        raise PermissionDenied
    initial = MediaErasure.objects.filter(pk=job_id, execution__action__request=case).first()
    if not initial:
        raise Http404
    blob = Blob.objects.select_for_update().get(pk=initial.blob_id)
    job = MediaErasure.objects.select_for_update().select_related("execution__proof").get(pk=job_id)
    user = current_recovery_actor(user, session_version, mfa_version)
    if not permitted(user, case):
        raise PermissionDenied
    signature = fingerprint(canonical({"job": job_id, "version": version, "reason": reason}))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "media_recover"
            and previous.payload_digest == signature
        ):
            return MediaErasureRecovery.objects.get(action=previous)
        raise ValidationError("Conflicting action key / Clave incompatible")
    if settings.PRODUCTION and job.execution.proof.provider == "simulator":
        raise ValidationError("Simulated execution cannot authorize production recovery")
    if (
        job.recovery_version != version
        or job.status != "failed"
        or job.attempts < 5
        or blob.status != "erasing"
        or not job.encrypted_paths
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Review current exhausted job / Revisa trabajo agotado vigente")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=case.version,
                operation="media_recover",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            recovery = MediaErasureRecovery.objects.create(
                job=job,
                action=action,
                previous_version=job.recovery_version,
                previous_attempts=job.attempts,
            )
            job.recovery_version += 1
            job.status = "queued"
            job.attempts = 0
            job.error_code = ""
            job.next_attempt_at = timezone.now()
            job.save(
                update_fields=[
                    "recovery_version",
                    "status",
                    "attempts",
                    "error_code",
                    "next_attempt_at",
                ]
            )
            return recovery
    except IntegrityError as error:
        raise ValidationError("Recovery conflict / Conflicto de recuperación") from error


class RecoveryForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo operativo minimizado / Minimized operational reason",
    )


def authorized_case(request, case_id):
    if not allowed(request) or not can_recover(request.user):
        raise PermissionDenied
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        raise PermissionDenied
    return case


@login_required
@require_GET
def queue(request, case_id):
    case = authorized_case(request, case_id)
    page = Paginator(
        MediaErasure.objects.filter(execution__action__request=case).order_by("-created_at", "-pk"),
        50,
    ).get_page(request.GET.get("page"))
    return private(render(request, "safety/media_jobs.html", {"case": case, "page": page}))


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def recover(request, case_id, job_id):
    case = authorized_case(request, case_id)
    job = MediaErasure.objects.filter(pk=job_id, execution__action__request=case).first()
    if not job:
        raise Http404
    form = RecoveryForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": job.recovery_version}
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            requeue(request.user, case.pk, job.pk, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return redirect("media_erasure_jobs", case_id=case.pk)
    return private(
        render(
            request,
            "safety/media_recover.html",
            {
                "case": case,
                "job": job,
                "form": form,
                "exhausted": job.status == "failed" and job.attempts >= 5,
            },
            status=status,
        )
    )
