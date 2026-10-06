"""Scoped access record/field census. Digests never release original field values."""

from decimal import Decimal
from functools import lru_cache
from uuid import UUID

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.views.decorators.debug import sensitive_variables

from .rights import fingerprint
from .rights_exports import canonical


@lru_cache(maxsize=None)
def current_case_paths(label):
    """Forward FK ownership only; never traverse reverse subject collections."""
    start = apps.get_model(label)
    if start._meta.label_lower == "safety.rightsrequest":
        return ("pk",)
    found = []
    queue = [(start, "", {start._meta.label_lower})]
    while queue:
        model, prefix, seen = queue.pop()
        for field in model._meta.concrete_fields:
            if not field.is_relation or not (field.many_to_one or field.one_to_one):
                continue
            target = field.related_model
            path = prefix + field.name
            if target._meta.label_lower == "safety.rightsrequest":
                found.append(path)
            elif target._meta.label_lower not in seen and path.count("__") < 4:
                queue.append((target, path + "__", seen | {target._meta.label_lower}))
    return tuple(sorted(found))


def normalized(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, (bytes, memoryview)):
        return bytes(value).hex()
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(item) for item in value]
    return value


@sensitive_variables()
def source(case, person):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Access scope inventory requires canonical transaction")
    if (
        case.kind != "access"
        or (case.account_subject_id and person is not None)
        or (not case.account_subject_id and (not person or case.person_id != person.pk))
    ):
        raise ValidationError("Exact account/profile access subject required")
    entries = []

    @sensitive_variables()
    def capture(label, purpose, queryset, fields):
        model = queryset.model
        # Deduplicate matching joins before locking; PG forbids FOR UPDATE DISTINCT.
        queryset = model.objects.filter(pk__in=queryset.values("pk"))
        excluded = Q()
        for path in current_case_paths(model._meta.label):
            excluded |= Q(**{path: case.pk})
        if excluded:
            queryset = queryset.exclude(excluded)
        names = [field.attname for field in model._meta.concrete_fields]
        rows = list(queryset.select_for_update(of=("self",)).order_by("pk").values(*names))
        records = []
        for row in rows:
            reference = fingerprint(
                canonical({"model": label, "pk": normalized(row[model._meta.pk.attname])})
            )
            facts = {
                field.attname: {
                    "digest": fingerprint(canonical(normalized(row[field.attname]))),
                    "type": field.get_internal_type(),
                }
                for field in model._meta.concrete_fields
            }
            records.append({"reference": reference, "fields": facts})
        entries.append(
            {
                "model": label,
                "purpose": purpose,
                "count": len(records),
                "fields": {
                    field.attname: field.get_internal_type()
                    for field in model._meta.concrete_fields
                },
                "records": records,
                "digest": fingerprint(canonical(records)),
            }
        )
        return rows

    from .erasure_inventory import source_manifest

    baseline = source_manifest(person, case, capture=capture)
    subject = case.account_subject if case.account_subject_id else person.subject
    if subject:
        for name in ["groups", "user_permissions"]:
            relation = apps.get_model("core.User")._meta.get_field(name)
            through = relation.remote_field.through
            capture(
                "core.User." + name,
                "account_authority",
                through.objects.filter(user_id=subject.pk),
                None,
            )
    from apps.mediafiles.models import Blob

    if person:
        capture(
            "mediafiles.Blob",
            "media",
            Blob.objects.filter(photos__revision__listing__person=person),
            None,
        )
    manifest = {
        "schema": "access-scope-inventory-v1",
        "person": str(person.pk) if person else None,
        "account_subject": str(
            case.account_subject_id or (person.subject_id if person else "") or ""
        ),
        "manager_version": case.manager_version,
        "entries": entries,
        "shared_phone": baseline["shared_phone"],
        "account_has_other_responsibilities": baseline["account_has_other_responsibilities"],
        "media": baseline["media"],
        "current_procedure_excluded": True,
        "pending": [
            "current_procedure_records",
            "sessions_logs_caches_queues_backups",
            "unlinked_or_external_subject_records",
            "per_record_field_decisions",
        ],
    }
    manifest["digest"] = fingerprint(canonical(manifest))
    return manifest
