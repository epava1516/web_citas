"""Whole-source reads and chain revalidations per audited portability operation.

Counts are independent of case size, so a small real PostgreSQL case shows the multiplier
that a large case pays per operation.
"""

import sys
from contextlib import contextmanager
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_portability_covered_export_races import approved_coverage
from test_rights_portability_response_draft import REASON, TEXT, operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety import (
    rights_exports,
    rights_information_export,
    rights_portability_close,
    rights_portability_coverage,
    rights_portability_coverage_evidence,
    rights_portability_export,
    rights_portability_images,
    rights_portability_response_evidence,
    rights_portability_selection,
    rights_portability_selection_pages,
)
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_response_draft import prepare
from apps.safety.rights_portability_response_review import inspect, record
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def code(function):
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__
    return function.__code__


WATCHED = {
    "source_copy": code(rights_exports.source_copy),
    "image_content": code(rights_exports.image_content),
    "audited_images": code(rights_portability_images.audited_images),
    "portability_export_binding": code(rights_portability_export._validate_export_binding),
    "information_export_binding": code(rights_information_export.validate_export_binding),
    "coverage_pages": code(rights_portability_coverage_evidence.validate_coverage_pages),
    "compile_coverage": code(rights_portability_coverage.compile_coverage),
    "project_selected": code(rights_portability_selection.project_selected),
    "selection_pages": code(rights_portability_selection_pages.complete_pages),
    "final_review": code(rights_portability_response_evidence.validate_review),
    "closure": code(rights_portability_close.validate_closure),
}


@contextmanager
def counted(counts, operation):
    codes = {value: name for name, value in WATCHED.items()}
    observed = dict.fromkeys(WATCHED, 0)

    def hook(frame, event, arg):
        if event == "call" and frame.f_code in codes:
            observed[codes[frame.f_code]] += 1

    previous = sys.getprofile()
    sys.setprofile(hook)
    try:
        yield
    finally:
        sys.setprofile(previous)
        counts[operation] = {name: value for name, value in observed.items() if value}


def test_whole_source_reads_per_final_operation(request, settings, monkeypatch, record_property):
    counts = {}
    case, author, selection, selected, _, decision, reviewer, _, _, receipt = approved_coverage(
        request, settings, monkeypatch, False, binary=True
    )
    respond = Permission.objects.get(codename="respond_rights_request")
    author.user_permissions.add(respond)
    reviewer.user_permissions.add(respond, Permission.objects.get(codename="verify_rights_scope"))
    author, reviewer = User.objects.get(pk=author.pk), User.objects.get(pk=reviewer.pk)
    with counted(counts, "generation"):
        export = generate(author, case.pk, case.version, selection.pk, selected.pk, uuid4(), REASON,
                          coverage_review_id=decision.pk)
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
    with counted(counts, "final_preparation"):
        draft = prepare(author, case.pk, case.version, case.response_version, export.pk, uuid4(),
                        REASON, TEXT, True)
    read_key = uuid4()
    with counted(counts, "final_inspection"):
        inspect(reviewer, case.pk, case.version, draft.pk, read_key, REASON)
    from apps.safety.models import RightsAction

    with counted(counts, "final_approval"):
        final = record(reviewer, case.pk, case.version, draft.pk,
                       RightsAction.objects.get(key=read_key).pk, uuid4(), REASON, "approved")
    with counted(counts, "closure"):
        close(author, case.pk, case.version, case.response_version, final.pk, uuid4(), REASON)
    client = Client()
    with counted(counts, "json_download"):
        assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 200
    part = export.parts.exclude(attachments=[]).get()
    with counted(counts, "binary_part_download"):
        assert client.post(url(receipt, export) + f"part/{part.pk}/", {"key": uuid4()}).status_code == 200
    record_property("source_reads", repr(counts))
    # One full chain validation per audited operation; a repeat inside it adds no guarantee.
    for operation, observed in counts.items():
        assert observed.get("portability_export_binding", 0) <= 1, (operation, observed)
