"""Whole-source reads per audited portability operation; counts are independent of case size."""

import sys
from contextlib import contextmanager
from uuid import uuid4

import pytest
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_portability_response_draft import REASON
from test_rights_portability_response_races import ready_final_draft

from apps.safety import rights_exports, rights_portability_images
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record

pytestmark = pytest.mark.django_db(transaction=True)

WATCHED = {
    "source_copy": rights_exports.source_copy.__wrapped__.__code__,
    "image_content": rights_exports.image_content.__wrapped__.__code__,
    "audited_images": rights_portability_images.audited_images.__wrapped__.__code__,
}


@contextmanager
def counted(counts, operation):
    codes = {code: name for name, code in WATCHED.items()}
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
        counts[operation] = observed


def test_whole_source_reads_per_final_operation(request, settings, monkeypatch, record_property):
    counts = {}
    case, author, reviewer, _, _, draft, read_action, receipt = ready_final_draft(
        request, settings, monkeypatch, with_receipt=True, account_only=False, binary=True
    )
    with counted(counts, "final_approval"):
        decision = record(
            reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved"
        )
    with counted(counts, "closure"):
        close(author, case.pk, case.version, case.response_version, decision.pk, uuid4(), REASON)
    export, client = draft.export, Client()
    with counted(counts, "json_download"):
        assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 200
    part = export.parts.exclude(attachments=[]).get()
    with counted(counts, "binary_part_download"):
        assert client.post(url(receipt, export) + f"part/{part.pk}/", {"key": uuid4()}).status_code == 200
    record_property("source_reads", repr(counts))
    print("SOURCE_READS", counts)
