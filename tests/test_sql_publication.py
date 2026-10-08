"""Conservative SQL proof must preserve the complete native population."""

from functools import wraps

import pytest
from django.db import connection
from django.utils.translation import override
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import projected_publication as projection
from apps.listings import sql_publication
from apps.listings.discovery import candidates
from apps.listings.models import Rate, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_sql_proof_and_unknowns_match_complete_native_population(request, record_property):
    client = request.getfixturevalue("directory")
    assert connection.vendor == "postgresql" and projection.supported()
    populate(50)
    expected = native_ids(candidates({}))
    target = candidates({}).get(pk=expected[25]).approved_revision
    original = {f.attname: getattr(target, f.attname) for f in Revision._meta.concrete_fields}
    assert target.listing_id not in expected[:24]
    baseline = sql_publication.SQLPublication(candidates({}))
    assert baseline.visible_ids(candidates({})) == expected
    assert baseline.stats["positive"] == 50 and baseline.stats["native_fallback"] == 0
    row_proof = sql_publication.SQLPublication(candidates({}), setwise=False, bulk=False)
    assert row_proof.visible_ids(candidates({})) == expected
    changes = [
        {"description": ""}, {"description": " \n\t "},
        {"description": "www.example.invalid"}, {"description": "https://example.invalid"},
        {"description": "@contact"}, {"description": "1234 5678"},
        {"description": "١٢٣٤٥٦٧٨٩"}, {"description": "Texto 😀 válido"},
        {"description": "e\u0301"}, {"description": "a" * 6001},
        {"description": "\u2003Descripción válida\u2003"},
        {"title": ""}, {"title": "\n"}, {"title": " www.x "},
        {"content_language": "xx"}, {"profile_type": "unknown"},
        {"description_alternative": "@hidden"},
        {"telegram": " @Valid_name "}, {"telegram": "valid_name\n"},
        {"telegram": "éxxxx"}, {"telegram": "bad!name"},
        {"contact_exposure_accepted": False},
        {"spoken_languages": ["es", "en", "es"]},
        {"spoken_languages": [["es"]]}, {"spoken_languages": {"es": True}},
        {"spoken_languages": [True]}, {"spoken_languages": "es"},
        {"days": [1]}, {"days": ["1", "8"]}, {"days": []},
        {"municipality_id": None}, {"manager_version": 123},
    ]
    observations = []
    for index, change in enumerate(changes):
        Revision.objects.filter(pk=target.pk).update(**change)
        native = native_ids(candidates({}))
        current = sql_publication.SQLPublication(candidates({}))
        assert current.visible_ids(candidates({})) == native, change.keys()
        row_proof = sql_publication.SQLPublication(candidates({}), setwise=False, bulk=False)
        assert row_proof.visible_ids(candidates({})) == native, change.keys()
        # False SQL proof remains native, including VALID but unknown Unicode,
        # whitespace normalization and form conversions of numeric JSON choices.
        # Every mutation compares ALL ordered IDs; representative invalid,
        # valid-unknown, normalization and authority cases also exercise every
        # page and locale through the public adapter.
        for lang in (["es", "en"] if index in {0, 7, 18, 31} else []):
            with override(lang):
                for number in [1, 2, 3]:
                    page = projection.projected_page(candidates({}), number)
                    assert page.paginator.count == len(native)
                    assert [row.pk for row in page] == native[(number - 1)*24:number*24]
        observations.append({"fields": sorted(change), "eligible": len(native),
                             "positive": current.stats["positive"],
                             "fallback": current.stats["native_fallback"]})
        Revision.objects.filter(pk=target.pk).update(**{k: original[k] for k in change})
    response = client.get("/es/")
    assert response.wsgi_request._publication_route["candidate_stats"]["proof_strategy"] == "sql_bulk_dependencies"
    record_property("sql_proof_mutations", observations)


def test_sql_helper_semantic_wrapper_disables_public_projection(request, monkeypatch):
    client = request.getfixturevalue("directory")
    assert projection.supported()
    original = sql_publication.content_proof

    @wraps(original)
    def changed():
        from django.db.models import Q
        return Q(pk__isnull=False)

    monkeypatch.setattr(sql_publication, "content_proof", changed)
    assert not projection.supported()
    result = client.get("/es/")
    assert result.wsgi_request._publication_route["route"] == "fallback"
    assert [row.pk for row in result.context["page"]] == native_ids(candidates({}))


def test_bulk_latest_check_ties_and_relationship_counts(request, record_property):
    from datetime import timedelta

    from apps.core.models import VerificationCheck
    from apps.mediafiles.models import Blob, Photo
    from scripts.synthetic_load_dataset import clone

    request.getfixturevalue("directory")
    populate(50)
    target = candidates({}).last()
    revision = target.approved_revision
    original = target.person.verificationcheck_set.latest("created_at")
    later = clone(original, status="failed")
    later.save()
    VerificationCheck.objects.filter(pk=later.pk).update(created_at=original.created_at + timedelta(seconds=1))

    def equal():
        native = native_ids(candidates({}))
        current = sql_publication.SQLPublication(candidates({}))
        assert current.visible_ids(candidates({})) == native
        return native, current.stats

    native, stats = equal()
    assert target.pk not in native and stats["native_fallback"] >= 1
    VerificationCheck.objects.filter(pk=later.pk).update(created_at=original.created_at)
    _, stats = equal()
    assert stats["native_fallback"] >= 1  # Do not choose a different winner for a native tie.
    VerificationCheck.objects.filter(pk=later.pk).delete()
    assert target.pk in equal()[0]
    Rate.objects.filter(revision=revision).delete()
    for count in [0, 10, 11]:
        Rate.objects.filter(revision=revision).delete()
        Rate.objects.bulk_create([Rate(revision=revision, concept="Session", mode="consult") for _ in range(count)])
        assert (target.pk in equal()[0]) == (count <= 10)
    Rate.objects.filter(revision=revision).delete()
    photo = revision.photos.get()
    extra = []
    for index in range(8):
        blob = Blob.objects.create(sha256=f"sql-proof-photo-{index}", status="ready")
        extra.append(Photo.objects.create(revision=revision, blob=blob, comparison_complete=True))
        assert (target.pk in equal()[0]) == (index < 7)
    Photo.objects.filter(pk__in=[p.pk for p in extra]).delete()
    photo.comparison_complete = False
    photo.save(update_fields=["comparison_complete"])
    assert target.pk not in equal()[0]
    record_property("bulk_dependency_boundaries", {
        "latest_failed_overrides_previous_passed": True, "latest_ties_native_unknown": True,
        "rates_zero_ten_eleven": True, "photos_one_through_nine_and_invalid": True,
        "target_outside_first_page": True,
    })


def normalized_detail_body(response):
    """Verify signed target binding; mask only its per-response signature/time."""
    from urllib.parse import quote
    from django.core import signing

    token = response.context["report_target"]
    listing = response.context["listing"]
    expected = {"listing": str(listing.pk), "revision": str(listing.approved_revision_id)}
    assert signing.loads(token, salt="public-report-target-v1", max_age=60) == expected
    encoded = quote(token, safe="/").encode()
    assert response.content.count(encoded) == 1
    return response.content.replace(encoded, b"VERIFIED_SIGNED_REPORT_TARGET"), expected


def test_detail_response_signed_target_comparison(request, monkeypatch, record_property):
    import time
    from django.core import signing

    client = request.getfixturevalue("directory")
    listing = candidates({}).first()
    path = f"/es/listing/{listing.pk}/"
    now = int(time.time())
    with monkeypatch.context() as patch:
        patch.setattr(signing.TimestampSigner, "timestamp", lambda self: signing.b62_encode(now - 1))
        first = client.get(path)
    with monkeypatch.context() as patch:
        patch.setattr(signing.TimestampSigner, "timestamp", lambda self: signing.b62_encode(now))
        second = client.get(path)
    assert first.status_code == second.status_code == 200
    assert first.content != second.content
    assert normalized_detail_body(first) == normalized_detail_body(second)
    record_property("detail_comparison", {"different_signing_seconds": True,
        "raw_equal": False, "only_verified_signed_target_differs": True,
        "binding_checked": "listing and currently approved revision; signature max_age60s"})
