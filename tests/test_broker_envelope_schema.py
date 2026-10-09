import base64
import json

import pytest

from apps.safety.broker_message_projection import periodic_tasks, project_message

TASK = "apps.safety.tasks.purge_expired_access_response_drafts"


@pytest.mark.parametrize(
    "task",
    [
        "apps.listings.tasks.refresh_publication_state",
        "apps.listings.tasks.sweep_publication_state",
    ],
)
@pytest.mark.parametrize("state", ["queued", "reserved"])
@pytest.mark.parametrize(
    "args,kwargs", [([], {}), (["private-subject"], {}), ([], {"subject": "private"})]
)
def test_publication_maintenance_requires_an_argument_free_envelope(task, state, args, kwargs):
    raw = message()
    raw["headers"]["task"] = task
    raw["body"] = base64.b64encode(json.dumps([args, kwargs, {}]).encode()).decode()
    encoded = json.dumps([raw, "", "q"] if state == "reserved" else raw).encode()
    if args or kwargs:
        with pytest.raises(ValueError):
            project_message(encoded, set(), state, periodic_tasks(), queue="q")
    else:
        assert project_message(encoded, set(), state, periodic_tasks(), queue="q") is None


def message():
    return {
        "content-type": "application/json",
        "content-encoding": "utf-8",
        "properties": {"body_encoding": "base64"},
        "headers": {"task": TASK},
        "body": base64.b64encode(json.dumps([[], {}, {}]).encode()).decode(),
    }


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("headers", "private_contact", "private@example.invalid"),
        ("properties", "private_token", "PRIVATE CAPABILITY"),
        ("headers", "argsrepr", "PRIVATE ARGUMENT"),
        ("headers", "kwargsrepr", "PRIVATE KEYWORD"),
        ("headers", "stamps", {"private": "PRIVATE STAMP"}),
    ],
)
def test_unexamined_envelope_fields_are_rejected_before_periodic_exclusion(section, field, value):
    raw = message()
    raw[section][field] = value
    with pytest.raises(ValueError):
        project_message(json.dumps(raw).encode(), set(), "queued", {TASK})


def test_unknown_null_link_keys_cannot_hide_unexamined_information():
    raw = message()
    raw["body"] = base64.b64encode(
        json.dumps([[], {}, {"private@example.invalid": None}]).encode()
    ).decode()
    with pytest.raises(ValueError):
        project_message(json.dumps(raw).encode(), set(), "queued", {TASK})


def test_duplicate_json_keys_are_not_silently_discarded():
    raw = json.dumps(message()).replace(
        '"headers": {', '"headers": {"task": "PRIVATE SHADOW TASK", '
    )
    with pytest.raises(ValueError):
        project_message(raw.encode(), set(), "queued", {TASK})


@pytest.mark.parametrize(
    "field,value",
    [("retries", "PRIVATE"), ("eta", "PRIVATE"), ("origin", "private@example.invalid")],
)
def test_known_metadata_fields_require_their_native_types(field, value):
    raw = message()
    raw["headers"][field] = value
    with pytest.raises(ValueError):
        project_message(json.dumps(raw).encode(), set(), "queued", {TASK})


def test_untyped_blob_argument_is_not_mistaken_for_another_subject():
    raw = message()
    raw["headers"]["task"] = "apps.mediafiles.tasks.process_blob"
    raw["body"] = base64.b64encode(json.dumps([[{"private": "PRIVATE"}], {}, {}]).encode()).decode()
    with pytest.raises(ValueError):
        project_message(json.dumps(raw).encode(), set(), "queued", {TASK})


def test_large_time_limit_integer_is_rejected_without_numeric_overflow():
    raw = message()
    raw["headers"]["timelimit"] = [10**400, None]
    with pytest.raises(ValueError):
        project_message(json.dumps(raw).encode(), set(), "queued", {TASK})


@pytest.mark.parametrize("section", ["body", "envelope"])
def test_excessive_json_nesting_becomes_typed_rejection(section):
    deep = "[" * 2000 + "0" + "]" * 2000
    if section == "body":
        raw = message()
        raw["body"] = base64.b64encode(deep.encode()).decode()
        encoded = json.dumps(raw).encode()
    else:
        encoded = deep.encode()
    with pytest.raises(ValueError):
        project_message(encoded, set(), "queued", {TASK})
