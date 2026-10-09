"""Validate actual target data in PostgreSQL; does not approve or deliver a case."""

import hashlib
import json
import time

import pytest
from capacity_target_fixture import PATHS, candidate, populate
from django.db import connection, transaction
from test_photos import photo_environment  # noqa: F401
from test_rights_portability import assessment

from apps.listings.forms import validate_listing_text
from apps.safety.rights_exports import canonical, source_copy
from apps.safety.rights_portability_selection import project_selected, row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.usefixtures("photo_environment")
def test_two_target_subjects_have_real_complete_disjoint_candidates(record_property):
    assert connection.vendor == "postgresql"
    manifests, identifiers = [], []
    for identity in ["capacity-subject-a", "capacity-subject-b"]:
        started = time.perf_counter()
        person, listing, rows, manifest = populate(identity)
        assert listing.revisions.count() == 1500
        assert len({row["description"] for row in rows}) == 1500
        assert len({row["description_alternative"] for row in rows}) == 1500
        for row in rows:
            for field in ["title", "description", "description_alternative"]:
                validate_listing_text(row[field])
            assert max(len(row["description"]), len(row["description_alternative"])) <= 6000
        with transaction.atomic():
            source = source_copy(person, listing)
        assert len(source["revisions"]) == 1500
        assert sum(len(row["images"]) for row in source["revisions"]) == 16
        facts = assessment()  # Unexamined datasets stay pending: not a coverage approval.
        facts["revisions"].update(
            status="eligible", basis="contract", origin="provided", automated=True,
            subject_related=True, third_party_reviewed=True,
            reason="Synthetic target text was created exclusively for this subject",
            evidence="Own deterministic generator; no third party text or actual legal decision",
        )
        selection = {"revisions": [
            {"row": row_reference("revisions", index, row), "fields": PATHS}
            for index, row in enumerate(source["revisions"])
        ]}
        projected = project_selected(source, facts, selection)
        assert projected == candidate(rows)
        encoded = canonical(projected).encode()
        assert abs(len(encoded) - 16 * 1024 * 1024) / (16 * 1024 * 1024) <= 0.01
        peer = "capacity-subject-b" if identity.endswith("a") else "capacity-subject-a"
        assert peer.encode() not in encoded
        revision_ids = {row["revision"] for row in source["revisions"]}
        blob_ids = {row["blob"] for row in manifest["originals"]}
        identifiers.append((revision_ids, blob_ids))
        manifest.update(subject=str(person.pk), listing=str(listing.pk), revisions=1500,
                        candidate_sha256=hashlib.sha256(encoded).hexdigest(),
                        candidate_bytes=len(encoded), build_seconds=time.perf_counter() - started,
                        synthetic_unapproved_fixture=True)
        manifests.append(manifest)
    assert identifiers[0][0].isdisjoint(identifiers[1][0])
    assert identifiers[0][1].isdisjoint(identifiers[1][1])
    assert {x["sha256"] for x in manifests[0]["originals"]}.isdisjoint(
        {x["sha256"] for x in manifests[1]["originals"]}
    )
    record_property("target_fixture_manifest", json.dumps(manifests))
    record_property("scope", "Target population/size and exact native projection only; no cases, authority, approved coverage, parallel HTTP or capacity claim")
