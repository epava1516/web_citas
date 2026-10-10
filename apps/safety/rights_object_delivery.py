"""Verify once for staging; fresh domain authorization on each proxy request."""

import hashlib
import json
import os
import re
import stat
from copy import copy
from datetime import UTC, timedelta
from pathlib import Path
from uuid import uuid4

from celery import shared_task
from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone

from .models import RightsExport, RightsExportDownload, RightsRequest
from .rights_object_models import RightsObjectDelivery
from .rights_portability_export import one_export_validation
from .rights_scope import locked_case
from .rights_verification import PROCEDURE, enabled

SALT = "rights-object-delivery-v1"
NAME = re.compile(r"^[0-9a-f]{32}$")
MAX_DELIVERY = 8 * 1024 * 1024
ALLOWED_TYPES = {"application/json; charset=utf-8", "application/zip", "image/webp"}


def _directory():
    root = Path(settings.RIGHTS_DELIVERY_ROOT)
    root.mkdir(parents=True, exist_ok=True, mode=0o750)
    if root.is_symlink():
        raise ValidationError("Delivery directory cannot be a symlink")
    return root


def _path(name):
    if not NAME.fullmatch(name):
        raise ValidationError("Invalid object name")
    return _directory() / name


def _binding(case, export, download):
    # Current encrypted bytes, object identity, channel and versions; not authority.
    selected = download.part if download.part_id else download.image
    facts = [
        str(case.pk),
        case.version,
        case.receipt_digest,
        str(export.pk),
        export.case_version,
        export.channel_digest,
        export.encrypted_payload,
        str(download.part_id or ""),
        str(download.image_id or ""),
        selected.encrypted_content if selected else "",
    ]
    return hashlib.sha256(json.dumps(facts, separators=(",", ":")).encode()).hexdigest()


def _grant_digest(row):
    facts = [
        str(row.pk),
        str(row.download_id),
        row.generation,
        row.object_name,
        row.content_sha256,
        row.content_bytes,
        row.content_type,
        row.filename,
        row.binding_digest,
        row.expires_at.astimezone(UTC).isoformat(),
    ]
    return hashlib.sha256(json.dumps(facts, separators=(",", ":")).encode()).hexdigest()


def _fresh(export_id):
    initial = RightsExport.objects.select_related("action").get(pk=export_id)
    case, person, _ = locked_case(initial.action.request_id)
    export = (
        RightsExport.objects.select_for_update(of=("self",))
        .select_related("proof", "action")
        .get(pk=export_id)
    )
    now = timezone.now()
    if case.account_subject_id:
        from .rights_account_copy import scope_matches

        scope = scope_matches(case, export)
    else:
        scope = bool(
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
        from .rights_access_close import closure_for_export, validate_closure
    else:
        from .rights_portability_close import closure_for_export, validate_closure
    closure = closure_for_export(case, export)
    if (
        not enabled()
        or not scope
        or case.kind not in {"access", "portability"}
        or case.receipt_expires_at <= now
        or export.expires_at <= now
        or export.purged_at is not None
        or not export.encrypted_payload
        or export.channel_digest != case.receipt_digest
        or export.proof.provider != "simulator"
        or export.proof.procedure != PROCEDURE
        or export.proof.status != "passed"
        or export.proof.scope != case.kind
        or export.proof.subject_id_snapshot != export.subject_snapshot
        or export.proof.channel_digest != export.channel_digest
        or export.proof.expires_at <= now
        or export.proof.case_version + 1 != export.case_version
        or (closure is None and (case.version != export.case_version or case.status != "reviewing"))
        or (
            closure is None
            and case.proofs.order_by("-created_at", "-pk").first().pk != export.proof_id
        )
    ):
        raise Http404
    validation_case = case
    if closure is not None:
        validate_closure(closure, case, person)
        validation_case = copy(case)
        validation_case.version = export.case_version
        validation_case.status = "reviewing"
    from .rights_information_export import validate_export_binding
    from .rights_portability_export import validate_export_binding as validate_portability

    validate_export_binding(validation_case, person, export)
    validate_portability(validation_case, person, export)
    return case, export


def stage_delivery(export, recorded_download, content, content_type, filename):
    """Called inside the existing download transaction after all byte guards.

    Keep the original direct response when disabled or package exceeds 8MiB.
    Returns a short relative URL, never a filesystem path. Caller redirects 303.
    """
    if not settings.RIGHTS_PROXY_DELIVERY_ENABLED:
        return None
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Delivery staging requires download transaction")
    if not isinstance(content, bytes) or len(content) > MAX_DELIVERY:
        return None
    if content_type not in ALLOWED_TYPES or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}", filename):
        raise ValidationError("Invalid delivery metadata")
    if recorded_download.export_id != export.pk:
        raise ValidationError("Foreign recorded download")
    # Stage follows domain validation; no second expensive derivation here.
    download = RightsExportDownload.objects.select_related("part", "image").get(
        pk=recorded_download.pk, export=export
    )
    case = RightsRequest.objects.get(pk=export.action.request_id)
    expiry = min(
        timezone.now() + timedelta(seconds=30),
        export.expires_at,
        case.receipt_expires_at,
        export.proof.expires_at,
    )
    if expiry <= timezone.now():
        raise Http404
    existing = RightsObjectDelivery.objects.filter(download=download).first()
    if existing:
        if (
            existing.generation == settings.RIGHTS_DELIVERY_GENERATION
            and not existing.consumed_at
            and not existing.purged_at
            and existing.expires_at > timezone.now()
            and existing.binding_digest == _binding(case, export, download)
            and existing.content_sha256 == hashlib.sha256(content).hexdigest()
        ):
            return _signed_url(existing)
        # Preserve idempotent direct-response replay; never issue another byte grant.
        return None
    name = uuid4().hex
    path = _path(name)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        row = RightsObjectDelivery.objects.create(
            download=download,
            generation=settings.RIGHTS_DELIVERY_GENERATION,
            object_name=name,
            content_sha256=hashlib.sha256(content).hexdigest(),
            content_bytes=len(content),
            content_type=content_type,
            filename=filename,
            binding_digest=_binding(case, export, download),
            expires_at=expiry,
        )
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return _signed_url(row)


def _signed_url(row):
    token = signing.dumps(
        {"id": str(row.pk), "generation": row.generation, "descriptor": _grant_digest(row)},
        salt=SALT,
    )
    return "/private-deliveries/" + token


def proxy_or_direct(export, recorded_download, response):
    """Compatibility hook: opt-in POST303; direct bytes retained as fallback."""
    from django.http import HttpResponse

    from .views import private

    disposition = response["Content-Disposition"]
    found = re.fullmatch(r'attachment; filename="([a-zA-Z0-9_.-]{1,80})"', disposition)
    if not found:
        return private(response)
    location = stage_delivery(
        export, recorded_download, response.content, response["Content-Type"], found.group(1)
    )
    if location is None:
        return private(response)
    return private(HttpResponse(status=303, headers={"Location": location}))


@one_export_validation
def authorize_token(token):
    # Closure and delivery share one locked export validation in this operation;
    # the decorator resets on every return/error, never retaining request state.
    if not settings.RIGHTS_PROXY_DELIVERY_ENABLED or settings.RECOVERY_MODE:
        raise Http404
    try:
        facts = signing.loads(token, salt=SALT, max_age=30)
        if facts["generation"] != settings.RIGHTS_DELIVERY_GENERATION:
            raise Http404
        # Lock domain first, matching existing downloads/purge; grant lock last.
        initial = RightsObjectDelivery.objects.select_related("download").get(pk=facts["id"])
        with transaction.atomic():
            case, export = _fresh(initial.download.export_id)
            row = (
                RightsObjectDelivery.objects.select_for_update(of=("self",))
                .select_related("download__part", "download__image")
                .get(pk=initial.pk)
            )
            if (
                row.expires_at <= timezone.now()
                or facts.get("descriptor") != _grant_digest(row)
                or row.consumed_at
                or row.purged_at
                or row.generation != settings.RIGHTS_DELIVERY_GENERATION
                or row.download.export_id != export.pk
                or row.binding_digest != _binding(case, export, row.download)
            ):
                raise Http404
            path = _path(row.object_name)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as source:
                info = os.fstat(source.fileno())
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_size != row.content_bytes
                    or hashlib.file_digest(source, "sha256").hexdigest() != row.content_sha256
                ):
                    raise Http404
            row.consumed_at = timezone.now()
            row.save(update_fields=["consumed_at"])
            return row
    except (
        signing.BadSignature,
        ValueError,
        KeyError,
        OSError,
        ValidationError,
        PermissionDenied,
        RightsObjectDelivery.DoesNotExist,
        RightsExport.DoesNotExist,
        RightsRequest.DoesNotExist,
    ):
        raise Http404 from None


def purge_export_deliveries(exports):
    """Called with export locks by expiry/erasure/recovery before clearing refs."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Delivery purge requires export transaction")
    rows = RightsObjectDelivery.objects.select_for_update(of=("self",)).filter(
        download__export__in=exports, purged_at__isnull=True
    )
    now = timezone.now()
    for row in rows:
        _path(row.object_name).unlink(missing_ok=True)
        row.purged_at = now
        row.save(update_fields=["purged_at"])


@shared_task
def purge_object_deliveries():
    """Worker removes expired/revoked bytes, keeps the minimal access audit."""
    now = timezone.now()
    with transaction.atomic():
        rows = list(
            RightsObjectDelivery.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(purged_at__isnull=True)
            .filter(
                Q(expires_at__lte=now)
                | ~Q(generation=settings.RIGHTS_DELIVERY_GENERATION)
                | Q(download__export__purged_at__isnull=False)
                | Q(download__export__expires_at__lte=now)
            )[:1000]
        )
        for row in rows:
            _path(row.object_name).unlink(missing_ok=True)
            row.purged_at = now
            row.save(update_fields=["purged_at"])
    # Crashes/transaction rollback can orphan staged files; bounded expiry cleanup.
    retained = set(
        RightsObjectDelivery.objects.filter(purged_at__isnull=True).values_list(
            "object_name", flat=True
        )
    )
    for path in _directory().iterdir():
        if (
            NAME.fullmatch(path.name)
            and path.name not in retained
            and path.lstat().st_mtime <= now.timestamp() - 30
        ):
            path.unlink(missing_ok=True)
    return len(rows)


def invalidate_restored_deliveries():
    """Mandatory recovery pre-exposure: revoke every grant and remove stage bytes."""
    with transaction.atomic():
        rows = RightsObjectDelivery.objects.select_for_update().filter(purged_at__isnull=True)
        for row in rows:
            _path(row.object_name).unlink(missing_ok=True)
        rows.update(purged_at=timezone.now())
    for path in _directory().iterdir():
        if NAME.fullmatch(path.name):
            path.unlink(missing_ok=True)
