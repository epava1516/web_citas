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


def reviewed_content_census(case, inventory, scope, material, source_reviews, history_review):
    """Bind an external operator census to actual private observations.

    This performs mechanical checks, not semantic approval. Root must inspect
    the encrypted originals and the named reviewers' reasons before acceptance.
    The application independently reviews the resulting exact delivery through
    its existing workflow; it does not audit this external inspection.
    """
    from scripts.owned_rights_resource_content import associated_content_records, process_inputs

    registration = material["registration"]
    sources = material["sources"]
    captured = datetime.fromisoformat(material["captured_at"])
    if (material["content_digest"] != fingerprint(canonical(sources))
            or captured.tzinfo is None or not inventory.created_at <= captured <= timezone.now()
            or registration["inputs"] != process_inputs()
            or registration["inputs"]["fixture_snapshots"]
            or any(registration["inputs"]["origin_inputs"].values())
            or registration.get("seed_execution", {}).get("branch") != "seed"
            or registration["seed_execution"].get("inputs") != registration["inputs"]):
        raise ValueError("Observed contents, cutoff or actual seed provenance changed")
    if not sources or len(sources) > 10000:
        raise ValueError("Bounded observed content sources required")
    references = {source["reference"] for source in sources}
    if len(references) != len(sources) or set(source_reviews) != references:
        raise ValueError("Every actual source requires an exact external inspection")
    categories = {category: {"reason": "Actual private producer contents with externally inspected source decisions; application review remains separate",
                             "pending": [], "origins": []} for category in RESOURCE_CATEGORIES}
    # Every legacy display pending maps to an explicit typed requirement.
    # Unknown pending names survive; no substring-based clearing is permitted.
    typed_pending = {"historical_dependency_provenance_requires_independent_review"}
    for source in sources:
        if source["reference"] == "django-locmem-cache" and source["content"]:
            typed_pending.add("caches:cache_value_producer_protocol_required")
        elif source["reference"] == "owned-redis-persistence" and source["content"]:
            typed_pending.add("backups:redis_persistence_existing_reader_and_review_required")
        elif source["reference"] == "owned-redis-all-databases":
            typed_pending.update(f"caches:redis_db_{row['database']}_producer_content_review_required"
                                 for row in source["content"] if row["records"])
        elif source["reference"].startswith("file:") and source["producer"].get("subject_binding") == "not_established":
            typed_pending.add("unlinked_records:unassociated_file:" + source["producer"]["relative_path"])
        elif source["reference"].startswith("container-log:"):
            typed_pending.add("logs:producer_content_classification_required:" + source["producer"]["container_id"])
    global_pending = [item for item in material["pending"] if item not in typed_pending]
    # A no-link classification is a reasoned external provenance decision, not
    # a deduction from a new PostgreSQL name or from the absence of a bundle.
    historical = registration["historical_origins"]
    expected_history = {row["ciphertext_sha256"] for row in historical}
    if (history_review.get("registration_digest") != fingerprint(canonical(registration))
            or set(history_review.get("origins", {})) != expected_history
            or not history_review.get("operator") or not history_review.get("reviewer")
            or history_review["operator"] == history_review["reviewer"]):
        global_pending.append("historical_dependency_provenance")
    else:
        for review in history_review["origins"].values():
            if (review.get("classification") != "no_link"
                    or not isinstance(review.get("reason"), str) or len(review["reason"].strip()) < 40
                    or set(review.get("evidence", {})) != {"producer_inputs", "creation_and_mounts", "seed_execution", "effective_settings", "no_restore_or_import"}
                    or any(not isinstance(value, str) or len(value.strip()) < 20 for value in review["evidence"].values())):
                global_pending.append("historical_dependency_provenance")
                break
    for source in sources:
        review = source_reviews[source["reference"]]
        if (set(review) != {"operator", "reviewer", "original_digest", "decision", "reason", "records", "records_digest"}
                or not review["operator"] or not review["reviewer"] or review["operator"] == review["reviewer"]
                or review["original_digest"] != fingerprint(canonical(source))
                or not isinstance(review["reason"], str) or not 40 <= len(review["reason"].strip()) <= 1200
                or review["records_digest"] != fingerprint(canonical(review["records"]))
                or review["decision"] not in {"included", "covered_by_existing_copy", "excluded_nonpersonal", "excluded_third_party", "observed_absence", "unresolved"}):
            raise ValueError("Exact original inspection by distinct external reviewers required")
        category = source["category"]
        records = deepcopy(review["records"])
        if category not in categories or not isinstance(records, list) or len(records) > 10000:
            raise ValueError("Invalid inspected source records")
        if review["decision"] == "observed_absence":
            content = source["content"]
            empty = content == [] or (source["reference"] == "owned-redis-all-databases"
                                      and all(row["records"] == [] for row in content))
            if not empty or records:
                raise ValueError("Absence must match the actual whole producer content")
        if review["decision"] in {"excluded_nonpersonal", "excluded_third_party", "covered_by_existing_copy", "unresolved"} and records:
            raise ValueError("Non-disclosure decision cannot inject recipient records")
        if review["decision"] == "included" and not records:
            raise ValueError("Included source requires actual associated content")
        if records:
            eligible = {canonical(row) for row in associated_content_records(source)}
            if any(canonical(row) not in eligible for row in records):
                raise ValueError("Reviewed content does not match its actual producer association/projection")
        for row in records:
            if (set(row) != {"subject_kind", "subject_id", "created_at", "content", "source_reference"}
                    or row["subject_kind"] not in {"account", "person"}
                    or not isinstance(row["subject_id"], str) or not row["subject_id"]
                    or not isinstance(row["content"], str)):
                raise ValueError("Reviewed producer association and content required")
            created = datetime.fromisoformat(row["created_at"])
            if created.tzinfo is None or created > inventory.created_at:
                raise ValueError("Reviewed content outside inventory cutoff")
        # Unsupported physical encodings require the existing real content
        # reader; an external digest/exclusion cannot turn unread bytes green.
        source_pending = []
        requirements = source.get("requirements")
        if not isinstance(requirements, list):
            source_pending.append("source_requirements_unknown")
            requirements = []
        for requirement in requirements:
            resolved = False
            if requirement == "content_classification":
                # Semantic truth is the external inspection obligation; this
                # binds its decision to the exact original, without assigning
                # unassociated infrastructure to a subject.
                resolved = review["decision"] in {"excluded_nonpersonal", "observed_absence"}
            elif requirement == "associated_content_disclosure_review":
                resolved = (source["producer"].get("subject_binding") in {
                    "explicit_database_relation", "explicit_seed_producer_mapping"}
                    and review["decision"] in {"included", "excluded_third_party", "covered_by_existing_copy"})
            elif requirement == "existing_copy_or_disclosure_review":
                resolved = review["decision"] in {"included", "covered_by_existing_copy", "excluded_third_party", "observed_absence"}
            # producer_association, typed_content_reader and any unknown
            # requirement cannot be waived by a long reason or distinct IDs.
            if not resolved:
                source_pending.append(source["reference"] + ":" + str(requirement))
        if review["decision"] == "unresolved":
            source_pending.append(source["reference"] + ":external_content_review_unresolved")
        categories[category]["pending"].extend(source_pending)
        evidence = canonical({"original": review["original_digest"], "operator": review["operator"],
                              "reviewer": review["reviewer"], "decision": review["decision"], "reason": review["reason"],
                              "external_history_review": fingerprint(canonical(history_review))})
        if len(evidence) > 2000:
            raise ValueError("Inspected source evidence exceeds application limit")
        categories[category]["origins"].append({"reference": fingerprint(source["reference"]),
            "method": "structured_archive", "evidence": evidence,
            "records": records, "records_digest": fingerprint(canonical(records))})
    for category, body in categories.items():
        if not body["origins"]:
            # Missing producer coverage is not fabricated as an empty origin.
            raise ValueError("Actual source observation missing for " + category)
        body["pending"] = sorted(set(body["pending"] + global_pending))
    return {"schema": "access-retained-resources-v1", "request": str(case.pk),
            "inventory": inventory.pk, "source": inventory.source_digest,
            "cutoff": inventory.created_at.isoformat(), "captured_at": captured.isoformat(),
            "dependencies": scope_dependencies(scope), "categories": categories}
