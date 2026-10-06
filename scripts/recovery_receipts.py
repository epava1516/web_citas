"""Typed validation before any recovery effect. Does not grant resource ownership."""

import re
from uuid import UUID

from .recovery_ledger import LedgerIntegrityError

PURPOSES = {
    "account",
    "authentication",
    "account_preferences",
    "transient_copy",
    "profile",
    "publication",
    "contact",
    "representation",
    "shared_contact_review",
    "media",
}


def require(condition):
    if not condition:
        raise LedgerIntegrityError("Invalid typed recovery receipt")


def identifier(value):
    require(isinstance(value, str) and len(value) <= 64)
    if re.fullmatch(r"[1-9][0-9]{0,18}", value):
        require(int(value) <= 9223372036854775807)
    else:
        try:
            require(str(UUID(value)) == value)
        except ValueError as error:
            raise LedgerIntegrityError("Invalid resource identifier") from error


def _validate_receipt(value):
    require(
        isinstance(value, dict)
        and set(value)
        == {"schema", "execution", "scope", "subject", "purposes", "pending_purposes", "references"}
    )
    require(value["schema"] == "recovery-execution-receipt-v1")
    require(value["scope"] in {"account", "person"})
    identifier(value["execution"])
    require(str(UUID(value["execution"])) == value["execution"])
    identifier(value["subject"])
    purposes = value["purposes"]
    require(
        isinstance(purposes, list)
        and purposes
        and all(isinstance(p, str) and p in PURPOSES for p in purposes)
    )
    require(purposes == sorted(set(purposes)))
    pending = value["pending_purposes"]
    require(
        isinstance(pending, list)
        and all(isinstance(p, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", p) for p in pending)
    )
    require(pending == sorted(set(pending)))
    selected = set(purposes)
    require(selected.intersection(pending) <= {"media"})
    if value["scope"] == "account":
        require(selected <= {"account", "authentication", "account_preferences", "transient_copy"})
    if "profile" in selected:
        require("publication" in selected)
    refs = value["references"]
    require(isinstance(refs, dict) and refs.get("schema") == "recovery-resource-references-v1")
    require(set(refs) <= {"schema", "resources", "account", "person", "media_jobs"})
    resources = refs.get("resources")
    require(isinstance(resources, dict))
    expected = set()
    for purpose, names in {
        "authentication": {"tokens", "recovery_codes"},
        "account_preferences": {"favorites"},
        "contact": {"phone_challenges"},
        "representation": {"representation_invitations", "listings"},
        "publication": {"listings", "revisions"},
        "shared_contact_review": {"listings", "revisions"},
        "transient_copy": {"exports"},
        "media": {"photos", "media_operation"},
    }.items():
        if purpose in selected:
            expected.update(names)
    require(set(resources) == expected)
    for name in expected - {"photos", "media_operation"}:
        values = resources[name]
        require(isinstance(values, list) and len(values) == len(set(values)))
        for resource in values:
            identifier(resource)
    if value["scope"] == "person":
        require(
            isinstance(refs.get("person"), dict) and refs["person"].get("id") == value["subject"]
        )
    else:
        require("person" not in refs)
        if "account" in refs:
            require(
                isinstance(refs["account"], dict) and refs["account"].get("id") == value["subject"]
            )
    for name, fields in {
        "account": {"minimum_session_version", "minimum_mfa_version"},
        "person": {"minimum_rights_version", "minimum_manager_version"},
    }.items():
        if name not in refs:
            continue
        scope = refs[name]
        require(
            isinstance(scope, dict)
            and set(scope) == fields | {"id"} | ({"anonymize"} if name == "account" else set())
        )
        identifier(scope["id"])
        require(
            all(type(scope[field]) is int and 1 <= scope[field] <= 2147483647 for field in fields)
        )
        if name == "account":
            require(
                type(scope["anonymize"]) is bool and scope["anonymize"] == ("account" in selected)
            )
    if selected & {"account", "authentication", "account_preferences"}:
        require("account" in refs)
    if "media" not in selected:
        require("media_jobs" not in refs)
    else:
        require(
            resources["media_operation"]
            in {"erase_exclusive", "detach_shared_and_review_exclusive"}
        )
        require(isinstance(resources["photos"], list) and isinstance(refs.get("media_jobs"), list))
        seen = set()
        for photo in resources["photos"]:
            require(
                isinstance(photo, dict)
                and set(photo)
                in ({"photo", "blob", "shared"}, {"photo", "blob", "shared", "replacement"})
            )
            identifier(photo["photo"])
            identifier(photo["blob"])
            require(type(photo["shared"]) is bool and photo["photo"] not in seen)
            if "replacement" in photo:
                require(
                    photo["shared"]
                    and resources["media_operation"] == "detach_shared_and_review_exclusive"
                )
                require(str(UUID(photo["replacement"])) == photo["replacement"])
                require(all(row["blob"] != photo["replacement"] for row in resources["photos"]))
            seen.add(photo["photo"])
        seen_jobs, seen_blobs = set(), set()
        for job in refs["media_jobs"]:
            require(isinstance(job, dict) and set(job) == {"job", "blob", "paths"})
            identifier(job["job"])
            identifier(job["blob"])
            require(job["job"] not in seen_jobs and job["blob"] not in seen_blobs)
            require(
                any(
                    photo["blob"] == job["blob"] and not photo["shared"]
                    for photo in resources["photos"]
                )
            )
            require(
                not any(
                    photo["blob"] == job["blob"] and photo["shared"]
                    for photo in resources["photos"]
                )
            )
            seen_jobs.add(job["job"])
            seen_blobs.add(job["blob"])
            paths = job["paths"]
            require(isinstance(paths, dict) and set(paths) == {"original", "derivative"})
            for path in paths.values():
                require(
                    isinstance(path, str)
                    and len(path) <= 4096
                    and "\x00" not in path
                    and "\\" not in path
                    and not path.startswith("/")
                    and all(part not in {".", ".."} for part in path.split("/"))
                )
    if "media" in selected.intersection(pending):
        require(resources["media_operation"] == "detach_shared_and_review_exclusive")
    return value


def validate_receipt(value):
    try:
        return _validate_receipt(value)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise LedgerIntegrityError("Invalid typed recovery receipt") from error
