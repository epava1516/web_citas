"""Durable private generation jobs. Domain generation remains the single authority."""

import logging
import re
from datetime import timedelta
from uuid import uuid4

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsPortabilityExportJob, RightsPortabilitySelectionReview, RightsRequest
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case
from .rights_portability_export import generate

MAX_ATTEMPTS = 3
LEASE = timedelta(minutes=10)
# Worker limits sit above the 120 s generation objective; the objective is measured by
# acceptance, not enforced by killing valid generations. Both stay below the lease.
SOFT_TIME_LIMIT = 240
TIME_LIMIT = 300
DISPATCH_INTERVAL = timedelta(minutes=1)
logger = logging.getLogger(__name__)


def failure_location(error):
    """Last code location only; never an exception message, source line or locals."""
    trace = error.__traceback__
    if trace is None:
        return "unknown"
    while trace.tb_next is not None:
        trace = trace.tb_next
    module = trace.tb_frame.f_globals.get("__name__", "unknown")
    name = trace.tb_frame.f_code.co_name
    if not isinstance(module, str) or not re.fullmatch(r"[A-Za-z0-9_.]{1,120}", module):
        module = "external"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,79}", name):
        name = "operation"
    return f"{module}.{name}:{trace.tb_lineno}"


def original_actor(job):
    actor = User.objects.get(pk=job.actor_id)
    # generate receives the original credentials, never newly refreshed versions.
    actor.session_version = job.session_version
    actor.mfa_version = job.mfa_version
    return actor


def check_authority(user, case):
    fresh_authority(user, case, user.session_version, user.mfa_version)
    if not user.is_active or case.assigned_to_id != user.pk:
        raise PermissionDenied


@transaction.atomic
@sensitive_variables()
def enqueue(
    user, case_id, version, selection_id, review_id, key, reason, *, coverage_review_id=None
):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Portability export reason required")
    # Check before canonical locks, and again after any wait.
    check_authority(user, RightsRequest.objects.get(pk=case_id))
    case, person, _ = reviewer_case(user, case_id)
    check_authority(user, case)
    digest = fingerprint(
        canonical(
            {
                "actor": user.pk,
                "case": str(case_id),
                "version": version,
                "selection": selection_id,
                "review": review_id,
                "coverage": coverage_review_id,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "reason": reason,
            }
        )
    )
    previous = RightsPortabilityExportJob.objects.filter(key=key).first()
    if previous:
        if previous.input_digest != digest:
            raise ValidationError("Conflicting portability export key")
        return previous
    if case.kind != "portability" or case.status != "reviewing" or case.version != version:
        raise ValidationError("Current portability request required")
    proof = can_prepare(user, case, person)
    decision = (
        RightsPortabilitySelectionReview.objects.select_related("selection")
        .filter(
            pk=review_id,
            outcome="approved",
            selection_id=selection_id,
            selection__request=case,
            selection__actor=user,
            selection__proof=proof,
            selection__purged_at__isnull=True,
            selection__expires_at__gt=timezone.now(),
        )
        .first()
    )
    if decision is None:
        raise ValidationError("Current approved selection required")
    expiry = decision.selection.expires_at
    if coverage_review_id is not None:
        from .models import RightsPortabilityCoverageReview

        coverage = (
            RightsPortabilityCoverageReview.objects.select_related("coverage")
            .filter(
                pk=coverage_review_id,
                outcome="approved",
                coverage__request=case,
                coverage__actor=user,
                coverage__selection_review=decision,
                coverage__purged_at__isnull=True,
                coverage__expires_at__gt=timezone.now(),
            )
            .first()
        )
        if coverage is None:
            raise ValidationError("Current approved coverage required")
        expiry = min(expiry, coverage.coverage.expires_at)
    check_authority(user, case)
    # Proof freshness is checked again immediately before durable publication.
    if can_prepare(user, case, person).pk != proof.pk:
        raise ValidationError("Identity proof changed")
    job = RightsPortabilityExportJob.objects.create(
        key=key,
        request=case,
        actor=user,
        proof=proof,
        review=decision,
        coverage_review_id=coverage_review_id,
        expected_version=version,
        session_version=user.session_version,
        mfa_version=user.mfa_version,
        input_digest=digest,
        encrypted_reason=seal({"reason": reason}),
        expires_at=expiry,
    )
    transaction.on_commit(lambda: dispatch(job.pk), robust=True)
    return job


def dispatch(job_id):
    """Best effort: beat resends durable pending rows after broker/process outages."""
    from .tasks import generate_portability_export

    try:
        generate_portability_export.apply_async(args=[str(job_id)], ignore_result=True)
    except Exception:
        # No payload/error logging: the durable row is the recovery source.
        return False
    RightsPortabilityExportJob.objects.filter(pk=job_id, state="queued").update(
        dispatched_at=timezone.now()
    )
    return True


def terminal(job, state):
    job.state = state
    job.finished_at = timezone.now()
    job.encrypted_reason = ""
    job.lease_until = None
    job.save(update_fields=["state", "finished_at", "encrypted_reason", "lease_until"])


def claim(job_id):
    with transaction.atomic():
        job = (
            RightsPortabilityExportJob.objects.select_for_update(skip_locked=True)
            .filter(pk=job_id)
            .first()
        )
        now = timezone.now()
        if job is None or job.state not in {"queued", "running"}:
            return None
        if job.available_at > now or (job.state == "running" and job.lease_until > now):
            return None
        if job.expires_at <= now or job.attempts >= MAX_ATTEMPTS:
            terminal(job, "failed")
            return None
        job.state = "running"
        job.attempts += 1
        job.attempt_token = uuid4()
        job.lease_until = now + LEASE
        job.save(update_fields=["state", "attempts", "attempt_token", "lease_until"])
        return job.attempt_token


@sensitive_variables()
def run(job_id):
    token = claim(job_id)
    if token is None:
        return
    try:
        with transaction.atomic():
            job = RightsPortabilityExportJob.objects.select_for_update().get(pk=job_id)
            if job.state != "running" or job.attempt_token != token:
                return
            actor = original_actor(job)
            before = RightsRequest.objects.get(pk=job.request_id)
            check_authority(actor, before)
            # Non-consuming preflight before canonical waits. The authoritative
            # scope/proof check remains can_prepare under canonical locks below.
            current = (
                before.proofs.order_by("-created_at", "-pk")
                .values_list("pk", "status", "expires_at")
                .first()
            )
            if (
                not current
                or current[0] != job.proof_id
                or current[1] != "passed"
                or current[2] <= timezone.now()
            ):
                raise ValidationError("Identity proof changed or expired")
            case, person, _ = reviewer_case(actor, job.request_id)
            check_authority(actor, case)
            if (
                job.expires_at <= timezone.now()
                or can_prepare(actor, case, person).pk != job.proof_id
            ):
                raise ValidationError("Identity proof changed or job expired")
            reason = unseal(job.encrypted_reason)["reason"]
            export = generate(
                actor,
                job.request_id,
                job.expected_version,
                job.review.selection_id,
                job.review_id,
                job.key,
                reason,
                coverage_review_id=job.coverage_review_id,
            )
            check_authority(actor, case)
            job.export = export
            job.state = "succeeded"
            job.finished_at = timezone.now()
            job.encrypted_reason = ""
            job.lease_until = None
            job.save(
                update_fields=["export", "state", "finished_at", "encrypted_reason", "lease_until"]
            )
    except (PermissionDenied, ValidationError, InvalidToken, KeyError, User.DoesNotExist) as error:
        # Class name only: messages may carry private case data.
        logger.warning("Portability export job %s [%s] rejected: %s",
                       job_id, failure_location(error), type(error).__name__)
        finish_attempt(job_id, token, rejected=True)
    except Exception as error:
        # Rollback includes the export and all its domain actions; replay is safe.
        logger.warning("Portability export job %s [%s] attempt failed: %s",
                       job_id, failure_location(error), type(error).__name__)
        finish_attempt(job_id, token, rejected=False)


def finish_attempt(job_id, token, *, rejected):
    with transaction.atomic():
        job = RightsPortabilityExportJob.objects.select_for_update().get(pk=job_id)
        if job.attempt_token != token or job.state != "running":
            return
        if rejected or job.attempts >= MAX_ATTEMPTS:
            terminal(job, "rejected" if rejected else "failed")
        else:
            job.state = "queued"
            job.lease_until = None
            job.dispatched_at = None
            job.available_at = timezone.now() + timedelta(seconds=30 * job.attempts)
            job.save(update_fields=["state", "lease_until", "dispatched_at", "available_at"])


def reconcile():
    now = timezone.now()
    with transaction.atomic():
        expired = (
            RightsPortabilityExportJob.objects.select_for_update(skip_locked=True)
            .filter(state__in=["queued", "running"], expires_at__lte=now)
            .order_by("created_at")[:100]
        )
        for job in expired:
            terminal(job, "rejected")
    from django.db.models import Q

    ids = list(
        RightsPortabilityExportJob.objects.filter(
            Q(state="queued", available_at__lte=now)
            & (Q(dispatched_at__isnull=True) | Q(dispatched_at__lte=now - DISPATCH_INTERVAL))
            | Q(state="running", lease_until__lte=now)
        )
        .order_by("created_at")
        .values_list("pk", flat=True)[:100]
    )
    return sum(dispatch(job_id) for job_id in ids)
