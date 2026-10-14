"""Connect actual owned producers to a deliberately incomplete rights census.

Observation is not disclosure approval or proof of exhaustive retained coverage.
No encrypted original is read here. Existing rights review remains mandatory.
"""
from copy import deepcopy
from datetime import datetime

from django.utils import timezone

from apps.safety.rights import fingerprint
from apps.safety.rights_access_delivery import RESOURCE_CATEGORIES
from apps.safety.rights_exports import canonical


def scope_dependencies(scope):
    if scope.get("blocked"):
        raise ValueError("Blocked scope cannot be represented by observed census dependencies")
    sessions = {"copy": scope["sessions"], "evidence": scope["session_evidence"], "blocked": []}
    queues = {"copy": scope["queued_processing"], "evidence": scope["queue_evidence"], "blocked": []}
    return {
        "logs": fingerprint(canonical(scope["log_origins"])),
        "mail": fingerprint(canonical(scope["mail_scope"])),
        "sessions": fingerprint(canonical(sessions)),
        "queues": fingerprint(canonical(queues)),
        **({"redis_history": fingerprint(canonical(scope["redis_history"]))}
           if scope.get("redis_history", {}).get("configured") else {}),
    }


def producer_records(observation, inventory, *, case):
    """Cross-check observed media/seed identities against their actual ORM producer.

    Only sanitized provenance metadata is retained as review material, not image
    bodies or password/TOTP. Dates come from producer rows, never a fabricated
    inventory timestamp. Concurrent changes fail or remain outside this cutoff.
    """
    from apps.core.models import User
    from apps.mediafiles.models import Photo

    records = []
    seen = set()
    for item in observation["files"]:
        for reference in item.get("database_references", []):
            photo = Photo.objects.select_related("blob", "revision__listing__person").get(pk=reference["photo"])
            person = photo.revision.listing.person
            if (str(photo.blob_id) != reference["blob"]
                    or str(photo.revision_id) != reference["revision"]
                    or str(person.pk) != reference["person"]
                    or person.subject_id != reference["account_subject"]
                    or reference["field"] not in {"original", "derivative"}):
                raise ValueError("Observed producer relationship changed")
            if reference["field"] == "original" and photo.blob.sha256 != item["sha256"]:
                raise ValueError("Observed producer content hash changed")
            key = ("photo", str(photo.pk), reference["field"])
            if key in seen:
                raise ValueError("Repeated observed producer reference")
            seen.add(key)
            if photo.created_at > inventory.created_at:
                continue
            records.append({"subject_kind": "person", "subject_id": str(person.pk),
                            "created_at": photo.created_at.isoformat(), "source_reference": None,
                            "content": canonical({"producer": "Photo.blob", "photo": str(photo.pk),
                                                  "field": reference["field"], "bytes": item["size"],
                                                  "sha256": item["sha256"],
                                                  "content_scope": "provenance metadata only; disclosure review pending"})})
        if item.get("subject_binding") == "explicit_seed_producer_mapping":
            for subject in item["account_subjects"]:
                user = User.objects.get(pk=subject)
                key = ("seed", user.pk)
                if key in seen:
                    raise ValueError("Repeated observed producer reference")
                seen.add(key)
                if user.date_joined > inventory.created_at:
                    continue
                records.append({"subject_kind": "account", "subject_id": str(user.pk),
                                "created_at": user.date_joined.isoformat(), "source_reference": None,
                                "content": canonical({"producer": item["producer_source"],
                                                      "producer_sha256": item["producer_sha256"],
                                                      "artifact_sha256": item["sha256"],
                                                      "excluded_fields": item["excluded_fields"],
                                                      "content_scope": "producer binding only; credentials not disclosed"})})
    # Account-only requests can link an actual account created after seed_demo.
    # Its source is the persisted request relation, not the seed credentials file.
    if case.account_subject_id and not any(
        row["subject_kind"] == "account" and row["subject_id"] == str(case.account_subject_id)
        for row in records
    ):
        from apps.safety.models import RightsRequest

        persisted = RightsRequest.objects.get(pk=case.pk)
        if persisted.account_subject_id != case.account_subject_id:
            raise ValueError("Observed request account relationship changed")
        user = User.objects.get(pk=persisted.account_subject_id)
        if user.date_joined <= inventory.created_at:
            records.append({"subject_kind": "account", "subject_id": str(user.pk),
                            "created_at": user.date_joined.isoformat(), "source_reference": None,
                            "content": canonical({"producer": "RightsRequest.account_subject -> core.User",
                                                  "request": str(persisted.pk), "account": user.pk,
                                                  "observed_at": timezone.now().isoformat(),
                                                  "content_scope": "persisted account relationship metadata only; disclosure pending"})})
    if not records:
        raise ValueError("Observed census requires actual bounded producer records")
    return records


def build_census(case, inventory, scope, observation, records):
    """Assemble exact adapter bindings; deliberately never remove pending scopes."""
    captured = datetime.fromisoformat(observation["captured_at"])
    if (observation.get("schema") != "owned-scenario-observation-v1"
            or observation.get("coverage_complete") is not False
            or not observation.get("pending") or not observation.get("run")
            or not observation.get("containers") or not observation.get("files")
            or captured.tzinfo is None or not inventory.created_at <= captured <= timezone.now()):
        raise ValueError("Owned observation scope or capture time invalid")
    if not records or len(records) > 10000:
        raise ValueError("Observed census requires bounded producer records")
    for row in records:
        if (set(row) != {"subject_kind", "subject_id", "created_at", "content", "source_reference"}
                or row["subject_kind"] not in {"person", "account"}
                or not isinstance(row["subject_id"], str) or not row["subject_id"]
                or not isinstance(row["content"], str) or row["source_reference"] is not None):
            raise ValueError("Invalid observed producer record")
        created = datetime.fromisoformat(row["created_at"])
        if created.tzinfo is None or created > inventory.created_at:
            raise ValueError("Observed producer record outside inventory cutoff")
    evidence = "Owned observation digest " + fingerprint(canonical(observation))
    missing = {
        "logs": ["captured_content_and_subject_review", "historical_dependency_provenance"],
        "mail": ["retained_bodies_headers_attachments_review"],
        "caches": ["cache_values_and_other_redis_databases_review"],
        "backups": ["backup_and_persistence_content_inventory"],
        "unlinked_records": ["producer_content_and_disclosure_review", "unlinked_resource_exhaustiveness"],
    }
    categories = {}
    for category in sorted(RESOURCE_CATEGORIES):
        rows = deepcopy(records) if category == "unlinked_records" else []
        categories[category] = {
            "reason": "Actual owned producer observation; remaining contents, association and disclosure are not accredited",
            "pending": missing[category],
            "origins": [{"reference": "owned-observation-" + category,
                         "method": "configuration_inspection", "evidence": evidence,
                         "records": rows, "records_digest": fingerprint(canonical(rows))}],
        }
    return {"schema": "access-retained-resources-v1", "request": str(case.pk),
            "inventory": inventory.pk, "source": inventory.source_digest,
            "cutoff": inventory.created_at.isoformat(), "captured_at": captured.isoformat(),
            "dependencies": scope_dependencies(scope), "categories": categories}


def capture_census(case, inventory, scope, runner_path, roots, *, seed_credentials):
    from scripts.owned_scenario_inventory import capture

    observation = capture(runner_path, roots, seed_credentials=seed_credentials)
    records = producer_records(observation, inventory, case=case)
    return build_census(case, inventory, scope, observation, records), observation
