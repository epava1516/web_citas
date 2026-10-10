"""Full native target flow with real HTTP samples; fixtures never invent read IDs."""

import cProfile
import hashlib
import io
import json
import math
import pstats
import time
import zipfile
from uuid import uuid4, uuid5

from capacity_delivery_http import open_client, operator, post
from django.contrib.auth.models import Permission
from django.db import transaction
from django.utils.crypto import salted_hmac
from test_capacity_selection_tcp import REASON
from test_rights_exports import url
from test_rights_portability_response_draft import TEXT
from test_rights_verification import read

from apps.core.models import RateWindow, User
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsAction,
    RightsPortabilityCoverage,
    RightsPortabilityCoverageRead,
    RightsPortabilityCoverageReview,
    RightsPortabilitySelection,
    RightsPortabilitySelectionReview,
)
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_coverage_pages import prepare_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_image_selection import prepare
from apps.safety.rights_portability_response_draft import prepare as prepare_response
from apps.safety.rights_portability_response_review import inspect, record
from apps.safety.rights_portability_selection import project_selected, row_reference
from apps.safety.rights_verification import receive_event, simulate_event, start

FACTS = {"status": "excluded", "basis": "other", "origin": "inferred",
         "automated": True, "subject_related": True, "third_party_reviewed": True,
         "reason": REASON, "evidence": "Synthetic declared exclusion; no production legal finding"}


def violation(metrics, name, value, maximum):
    # A valid limit breach is a FAIL, recorded so later stages are still measured, never NOT_PROVEN.
    metrics.setdefault("violations", []).append({"stage": name, "value": value, "maximum": maximum})


def measured(metrics, name, operation, *args, maximum=60, **kwargs):
    profile = None
    if metrics.get("diagnostic") and name not in metrics.setdefault("profiles", {}):
        profile = cProfile.Profile()
        profile.enable()
    begin = time.perf_counter()
    try:
        return operation(*args, **kwargs)
    finally:
        if profile is not None:
            profile.disable()
            output = io.StringIO()
            pstats.Stats(profile, stream=output).sort_stats("cumulative").print_stats(45)
            pstats.Stats(profile, stream=output).sort_stats("tottime").print_stats(30)
            metrics["profiles"][name] = output.getvalue()
        elapsed = time.perf_counter() - begin
        metrics.setdefault(name, []).append(elapsed)
        if elapsed > maximum:
            violation(metrics, name, elapsed, maximum)


def sampled(metrics, name, barrier, client, endpoint, csrf, values, profile=False):
    barrier.wait(timeout=120)
    if profile:
        # Diagnostic only: one extra server-profiled request, never part of the sample population.
        result = post(client, endpoint, csrf, values, headers={"X-Capacity-Profile": name})
        metrics.setdefault(name + "_profiled_seconds", []).append(result.seconds)
        assert result.status == 200, (name, result.status)
        return result.body
    result = post(client, endpoint, csrf, values)
    metrics.setdefault(name, []).append(result.seconds)
    metrics.setdefault(name + "_intervals", []).append(result.interval)
    metrics.setdefault(name + "_bytes", []).append(len(result.body))
    metrics.setdefault(name + "_http_stages", []).append(result.stages)
    if hasattr(client, "private_delivery"):
        assert [stage["status"] for stage in result.stages] == [303, 200]
        assert [stage["method"] for stage in result.stages] == ["POST", "GET"]
    assert result.status == 200, (name, result.status)
    assert "no-store" in result.headers.get("Cache-Control", "")
    return result.body


def gate(metrics, name, maximum, minimum=20):
    if metrics.get("diagnostic"):
        return  # Reduced diagnostic populations are never compared against limits.
    samples = metrics[name]
    assert len(samples) >= minimum, (name, len(samples), minimum)
    value = sorted(samples)[math.ceil(len(samples) * .95) - 1]
    metrics[name + "_p95"] = value
    if value > maximum:
        violation(metrics, name + "_p95", value, maximum)


def field_values(prefix, facts):
    return {prefix + key: "yes" if value is True else "no" if value is False else value
            for key, value in facts.items() if key != "status"}


def run_case(index, target, context, server, settings, barrier, metrics, diagnostic=False,
             full=False):
    case, selection, reviewer_client, _, csrf, *_ = target
    metrics["diagnostic"] = diagnostic
    writes = 4 if diagnostic else 20  # Diagnostic: three plain requests plus one profiled.
    author, reviewer = context["author"], context["reviewer"]
    metrics.update(binary_preparation=context["binary_preparation_operations"], case=str(case.pk))
    author_http = open_client(settings, server,
        f"/en/moderation/rights/{case.pk}/portability/images/", actor=author)
    metrics.setdefault("first_open_seconds", {})["images"] = author_http.first_open_seconds
    # Twenty actual writes of an included image preserve the other15images/all scalar fields.
    metrics["selection_versions"] = []
    first_image = context["binary_preparation_operations"][0]
    for attempt in range(writes):
        page = measured(metrics, "image_catalog_preparation", prepare, author, case.pk,
                        case.version, selection.assessment_review_id, uuid4(), REASON,
                        first_image["revision_index"], first_image["image_index"])
        values = {"operation": "save", "key": str(uuid4()), "token": page["token"],
                  "include": "on", "reason": REASON,
                  **field_values("image-", {**page["conditions"], "path": page["declaration"]["path"]})}
        sampled(metrics, "binary_page_save", barrier, author_http.client,
                server.url + f"/en/moderation/rights/{case.pk}/portability/images/",
                author_http.csrf, values, profile=diagnostic and attempt == writes - 1)
        selection = RightsPortabilitySelection.objects.filter(request=case, actor=author).latest("version")
        metrics["selection_versions"].append(selection.pk)
        binding = unseal(selection.encrypted_selection)
        assert len(binding["images"]) == 16 and len(binding["selection"]["revisions"]) == 1500
    assert len(set(metrics["selection_versions"])) == writes
    gate(metrics, "binary_page_save", 5)
    endpoint = server.url + f"/en/moderation/rights/{case.pk}/portability/selection/{selection.pk}/review/"
    for page in range(1, 32):
        body = sampled(metrics, "selection_page_read", barrier, reviewer_client, endpoint, csrf,
            {"operation": "inspect", "key": str(uuid4()), "version": case.version,
             "reason": REASON, "page": page}, profile=diagnostic and page == 2)
        assert ("capacity-subject-b" if index == 0 else "capacity-subject-a").encode() not in body
        if page == 1:
            rejected = post(reviewer_client, endpoint, csrf,
                {"operation": "review", "key": str(uuid4()), "version": case.version,
                 "reason": REASON, "outcome": "approved"})
            assert rejected.status == 409
            assert not RightsPortabilitySelectionReview.objects.filter(selection=selection).exists()
    gate(metrics, "selection_page_read", 2)
    binding = unseal(selection.encrypted_selection)
    for position in range(17 if diagnostic else 20):
        image = binding["images"][position % 16]
        body = sampled(metrics, "binary_inspection", barrier, reviewer_client,
            server.url + f"/en/moderation/rights/{case.pk}/portability/selection/{selection.pk}/image/{image['photo']}/",
            csrf, {"key": str(uuid4()), "version": case.version, "reason": REASON},
            profile=diagnostic and position == 16)
        assert hashlib.sha256(body).hexdigest() == image["content_digest"]
    gate(metrics, "binary_inspection", 2)
    decision_key = uuid4()
    sampled(metrics, "selection_final_decision", barrier, reviewer_client, endpoint, csrf,
        {"operation": "review", "key": str(decision_key), "version": case.version,
         "reason": REASON, "outcome": "approved"})
    selected = RightsPortabilitySelectionReview.objects.get(action__key=decision_key)
    assert len(selected.page_reads) == 31 and len(selected.image_reads) == 16
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    expected = project_selected(source,
        unseal(selection.assessment_review.assessment.encrypted_assessment),
        binding["selection"], field_evidence=binding.get("field_evidence"))
    omissions = {name: {} for name in SECTIONS}
    for dataset, reader in SECTIONS.items():
        choices = {item["row"]: set(item["fields"]) for item in binding["selection"].get(dataset, [])}
        for number, row in enumerate(reader(source)):
            reference = row_reference(dataset, number, row)
            if any(item["path"] not in choices.get(reference, set()) for item in scalar_fields(row)):
                omissions[dataset][reference] = {"all": FACTS}
    coverage = measured(metrics, "coverage_initial_preparation", save_coverage,
        author, case.pk, case.version, selected.pk, uuid4(), 0, REASON, omissions, {})
    coverage_path = f"/en/moderation/rights/{case.pk}/portability/coverage/"
    editor = open_client(settings, server, coverage_path, actor=author)
    metrics.setdefault("first_open_seconds", {})["coverage"] = editor.first_open_seconds
    metrics["coverage_versions"] = []
    for number in range(writes):
        page = measured(metrics, "coverage_page_preparation", prepare_page, author, case.pk,
                        case.version, selected.pk, uuid4(), REASON, "revisions", number, 1)
        fields = page["fields"]
        assert len(fields) <= 50
        values = {"operation": "save", "key": str(uuid4()), "token": page["token"],
                  "reason": REASON, "paths": list(page["decisions"]),
                  "fields-TOTAL_FORMS": len(fields), "fields-INITIAL_FORMS": len(fields),
                  "fields-MIN_NUM_FORMS": 0, "fields-MAX_NUM_FORMS": 50}
        for field_index, field in enumerate(fields):
            values.update(field_values(f"fields-{field_index}-",
                {**page["decisions"][field["path"]], "path": field["path"]}))
        sampled(metrics, "coverage_page_save", barrier, editor.client,
                server.url + coverage_path, editor.csrf, values,
                profile=diagnostic and number == writes - 1)
        coverage = RightsPortabilityCoverage.objects.filter(request=case, actor=author).latest("version")
        metrics["coverage_versions"].append(coverage.pk)
    assert len(set(metrics["coverage_versions"])) == writes
    gate(metrics, "coverage_page_save", 5)
    endpoint = server.url + f"/en/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/"
    required = required_pages(source)
    metrics["required_coverage_pages"] = len(required)
    metrics["coverage_batch_pages"] = []
    for number, group in enumerate(coverage_batches(required)):
        dataset, row, page, binary = group[0]
        key = uuid4()
        body = sampled(metrics, "coverage_page_read", barrier, reviewer_client, endpoint, csrf,
            {"operation": "inspect", "key": str(key), "version": case.version, "reason": REASON,
             "dataset": "binary" if binary else dataset, "row_number": row + 1,
             "field_page": page, "page_count": len(group)},
            profile=diagnostic and number == 3)
        for position, coordinates in enumerate(group):
            page_key = key if len(group) == 1 else uuid5(key, f"coverage-batch-page:{position}")
            evidence = RightsPortabilityCoverageRead.objects.get(action__key=page_key)
            assert (evidence.dataset, evidence.row_index, evidence.field_page, evidence.binary) == coordinates
        metrics["coverage_batch_pages"].append(len(group))
        assert ("capacity-subject-b" if index == 0 else "capacity-subject-a").encode() not in body
        if number == 0:
            rejected = post(reviewer_client, endpoint, csrf,
                {"operation": "review", "key": str(uuid4()), "version": case.version,
                 "reason": REASON, "outcome": "approved"})
            assert rejected.status == 409
            assert not RightsPortabilityCoverageReview.objects.filter(coverage=coverage).exists()
        if diagnostic and not full and number == 3:
            metrics["diagnostic_stopped_after"] = "coverage_page_read"
            return
    gate(metrics, "coverage_page_read", 2)
    decision_key = uuid4()
    sampled(metrics, "coverage_final_decision", barrier, reviewer_client, endpoint, csrf,
        {"operation": "review", "key": str(decision_key), "version": case.version,
         "reason": REASON, "outcome": "approved"})
    coverage_review = RightsPortabilityCoverageReview.objects.get(coverage=coverage, action__key=decision_key)
    assert len(coverage_review.read_ids) == len(required)
    finish(index, case, author, reviewer, selection, selected, coverage_review,
           context["receipt"], server, settings, barrier, metrics, expected)


def finish(index, case, author, reviewer, selection, selected, coverage_review,
           receipt, server, settings, barrier, metrics, expected):
    permissions = Permission.objects.filter(codename__in=["respond_rights_request", "verify_rights_scope"])
    author.user_permissions.add(*permissions)
    reviewer.user_permissions.add(*permissions)
    author, reviewer = User.objects.get(pk=author.pk), User.objects.get(pk=reviewer.pk)
    barrier.wait(timeout=120)
    export = measured(metrics, "generation", generate, author, case.pk, case.version,
        selection.pk, selected.pk, uuid4(), REASON, coverage_review_id=coverage_review.pk, maximum=120)
    case.refresh_from_db()
    staff, other = operator(author), operator(reviewer)
    read(staff, case)
    proof = start(author, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    read(other, case)
    receive_event(reviewer, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(staff, case)
    read(other, case)
    barrier.wait(timeout=120)
    draft = measured(metrics, "final_preparation", prepare_response, author, case.pk,
        case.version, case.response_version, export.pk, uuid4(), REASON, TEXT, True, maximum=30)
    key = uuid4()
    measured(metrics, "final_inspection", inspect, reviewer, case.pk,
             case.version, draft.pk, key, REASON, maximum=30)
    action = RightsAction.objects.get(key=key)
    decision = measured(metrics, "final_approval", record, reviewer, case.pk, case.version,
                        draft.pk, action.pk, uuid4(), REASON, "approved", maximum=30)
    measured(metrics, "closure", close, author, case.pk, case.version,
             case.response_version, decision.pk, uuid4(), REASON, maximum=30)
    case.refresh_from_db()
    assert case.status == "resolved"
    digests = {item["photo"]: item["content_digest"]
               for item in unseal(selection.encrypted_selection)["images"]}
    expected_images = {str(row.pk): (str(row.photo_id), digests[str(row.photo_id)])
                       for row in export.images.all()}
    assert len(expected_images) == 16
    manifest_client = open_client(settings, server, receipt)
    endpoint = server.url + url(receipt, export)
    response = post(manifest_client.client, endpoint, manifest_client.csrf, {"key": str(uuid4())})
    assert response.status == 200
    metrics["manifest_http_stages"] = response.stages
    if getattr(settings, "CAPACITY_OBJECT_DELIVERY", False):
        assert [stage["status"] for stage in response.stages] == [303, 200]
        assert export.images.filter(encrypted_content__startswith="wmblob1:").count() == 16
        assert not export.parts.exclude(encrypted_content__startswith="wmblob1:").exists()
    manifest = json.loads(response.body)
    assert manifest["schema"] == "rights-data-manifest-v1"
    assert abs(manifest["size"] / (16 * 1024 ** 2) - 1) <= .01
    metrics["delivered_json_bytes"] = manifest["size"]
    metrics["delivered_json_sha256"] = manifest["sha256"]
    fragments, recovered = {}, {}
    for variant, parts in [("json", manifest["data_parts"]), ("binary", manifest["parts"])]:
        assert 0 < len(parts) <= 20
        address = "127.0.0." + str(2 + 2 * index + (variant == "binary"))
        client = open_client(settings, server, receipt, source_address=address)
        metrics[variant + "_source_address"] = address
        # Diagnostic: every part once plus one profiled repeat; never compared to limits.
        downloads = len(parts) + 1 if metrics.get("diagnostic") else 20
        for number in range(downloads):
            part = parts[number % len(parts)]
            body = sampled(metrics, variant + "_download", barrier, client.client,
                endpoint + f"part/{part['id']}/", client.csrf, {"key": str(uuid4())},
                profile=bool(metrics.get("diagnostic")) and number == downloads - 1)
            assert len(body) <= 8 * 1024 ** 2
            with zipfile.ZipFile(io.BytesIO(body)) as package:
                assert package.testzip() is None
                if variant == "json":
                    names = package.namelist()
                    assert len(names) == 1
                    fragment = package.read(names[0])
                    assert hashlib.sha256(fragment).hexdigest() == part["sha256"]
                    fragments[part["fragment_position"]] = fragment
                else:
                    for name in package.namelist():
                        identifier = name[:-5]
                        assert hashlib.sha256(package.read(name)).hexdigest() == expected_images[identifier][1]
                        recovered[identifier] = expected_images[identifier]
        assert client.handler.observed_addresses == [address] * (downloads + 1)  # Receipt GET+POSTs.
        rate_key = salted_hmac("rate-window", "rights-export-download:" + address,
                               algorithm="sha256").hexdigest()
        attempts = RateWindow.objects.get(key=rate_key).attempts
        assert attempts == downloads
        metrics[variant + "_rate_attempts"] = attempts
        gate(metrics, variant + "_download", 5)
    data = b"".join(fragments[number] for number in range(1, len(fragments) + 1))
    assert len(data) == manifest["size"] and hashlib.sha256(data).hexdigest() == manifest["sha256"]
    projected = json.loads(data)
    assert len(projected["datasets"]["revisions"]) == 1500
    assert projected["datasets"] == expected["datasets"]
    assert recovered == expected_images
    metrics["success"] = not metrics.get("violations")
    # Diagnostic only, after every sample: attribute the download validation chain in-process
    # inside a rolled-back transaction; never a measured stage.
    metrics["post_validation_profile"] = validation_profile(case, export)


def validation_profile(case, export):
    from copy import copy

    from apps.safety.rights_exports import locked_case
    from apps.safety.rights_information_export import validate_export_binding as information
    from apps.safety.rights_portability_close import closure_for_export, validate_closure
    from apps.safety.rights_portability_export import validate_export_binding as portability

    profile = cProfile.Profile()
    with transaction.atomic():
        locked, person, _ = locked_case(case.pk)
        closure = closure_for_export(locked, export)
        profile.enable()
        begin = time.perf_counter()
        validate_closure(closure, locked, person)
        delivery = copy(locked)
        delivery.version, delivery.status = export.case_version, "reviewing"
        information(delivery, person, export)
        portability(delivery, person, export)
        elapsed = time.perf_counter() - begin
        profile.disable()
        transaction.set_rollback(True)
    output = io.StringIO()
    pstats.Stats(profile, stream=output).sort_stats("cumulative").print_stats(60)
    pstats.Stats(profile, stream=output).sort_stats("tottime").print_stats(30)
    return {"seconds_with_profiler": elapsed, "profile": output.getvalue()}


def coverage_batches(required, maximum=4):
    """Consecutive required coordinates, bounded and confined to one dataset/type.

    Every page still gets its own real audited POST evidence; the measured interval
    is the entire batch HTTP response and keeps the original two-second threshold.
    """
    if type(maximum) is not int or not 1 <= maximum <= 4:
        raise ValueError("Invalid diagnostic batch size")
    group = []
    for coordinate in required:
        if group and (len(group) == maximum or
                      (coordinate[0], coordinate[3]) != (group[0][0], group[0][3])):
            yield group
            group = []
        group.append(coordinate)
    if group:
        yield group
