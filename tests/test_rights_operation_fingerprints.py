"""Pure operation HMAC reuse retains native semantics and real child audits."""

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from pathlib import Path
from uuid import uuid4

import pytest
from django.db import transaction
from django.utils.crypto import salted_hmac
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_evidence_chain import runtime, set_role  # noqa: F401

from apps.safety import rights_operation_fingerprints as memo
from apps.safety.rights import fingerprint

pytestmark = pytest.mark.django_db(transaction=True)


def native(value):
    return salted_hmac("rights-request-v1", value, algorithm="sha256").hexdigest()


@pytest.mark.parametrize("value", ["", "abc", "ñ😀\0", b"", b"abc\x00\xff"])
@pytest.mark.parametrize("secret", ["operation-secret", b"operation-secret"])
def test_exact_native_and_fresh_input_key(settings, value, secret):
    settings.SECRET_KEY = secret
    with transaction.atomic(), memo.operation_fingerprints():
        assert fingerprint(value) == fingerprint(value) == native(value)
        assert memo._current.get()["entries"]
        settings.SECRET_KEY = "changed-secret"
        assert fingerprint(value) == native(value)
        assert fingerprint("changed-input") == native("changed-input")
    assert memo._current.get() is None


def test_nested_exception_resets_and_thread_copied_context_falls_back():
    calls = []

    def counted(value):
        calls.append(value)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        outer = memo._current.get()
        memo.fingerprint("x", counted)
        with pytest.raises(RuntimeError, match="nested"):
            with memo.operation_fingerprints():
                memo.fingerprint("x", counted)
                raise RuntimeError("nested")
        assert memo._current.get() is outer
        memo.fingerprint("x", counted)
        context = copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(context.run, memo.fingerprint, "x", counted).result() == native("x")
        assert len(calls) == 3
    assert not outer["entries"]
    assert memo._current.get() is None


def test_limits_do_not_retain_over_budget(monkeypatch):
    monkeypatch.setattr(memo, "MAX_ENTRIES", 2)
    monkeypatch.setattr(memo, "MAX_INPUT_BYTES", 1024)
    with transaction.atomic(), memo.operation_fingerprints():
        for value in ["a", "b", "c", "huge" * 1024]:
            assert fingerprint(value) == native(value)
        assert len(memo._current.get()["entries"]) <= 2
        assert memo._current.get()["bytes"] <= 1024


def test_secret_drift_during_native_never_stores_under_old_key(settings):
    settings.SECRET_KEY = "before-native"
    calls = []

    def changing_native(value):
        calls.append(value)
        settings.SECRET_KEY = "during-native"
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        assert memo.fingerprint("x", changing_native) == native("x")
        assert not memo._current.get()["entries"]
        settings.SECRET_KEY = "before-native"
        assert memo.fingerprint("x", changing_native) == native("x")
        assert len(calls) == 2
        assert not memo._current.get()["entries"]


def test_repeated_oversized_input_always_calls_native(monkeypatch):
    monkeypatch.setattr(memo, "MAX_INPUT_BYTES", 1)
    calls = []

    def counted(value):
        calls.append(value)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        for _ in range(2):
            assert memo.fingerprint("oversized", counted) == native("oversized")
        assert len(calls) == 2
        assert not memo._current.get()["entries"]
        assert memo._current.get()["bytes"] == 0


def test_entry_cap_repeated_new_input_always_calls_native(monkeypatch):
    monkeypatch.setattr(memo, "MAX_ENTRIES", 1)
    calls = []

    def counted(value):
        calls.append(value)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        memo.fingerprint("retained", counted)
        calls.clear()
        for _ in range(2):
            assert memo.fingerprint("not-retained", counted) == native("not-retained")
        assert len(calls) == 2
        assert len(memo._current.get()["entries"]) == 1
        assert all(key[1] == "retained" for key in memo._current.get()["entries"])


def test_cross_connection_falls_back_without_consuming_existing_entry(monkeypatch):
    calls = []

    def counted(value):
        calls.append(value)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        memo.fingerprint("x", counted)
        state = memo._current.get()
        with monkeypatch.context() as patch:
            patch.setattr(memo.transaction, "get_connection", lambda: object())
            assert memo.fingerprint("x", counted) == native("x")
        assert len(calls) == 2
        assert len(state["entries"]) == 1


def test_unsupported_secret_stays_native(settings):
    class Secret(str):
        pass

    settings.SECRET_KEY = Secret("subclass-secret")
    with transaction.atomic(), memo.operation_fingerprints():
        assert fingerprint("x") == native("x")
        assert not memo._current.get()["entries"]


def test_unsupported_types_and_errors_stay_native():
    class Broken:
        def __str__(self):
            raise ValueError("original conversion error")

    class Text(str):
        pass

    with transaction.atomic(), memo.operation_fingerprints():
        for value in [Text("subclass"), 123, None]:
            assert fingerprint(value) == native(value)
        assert not memo._current.get()["entries"]
        with pytest.raises(ValueError, match="original conversion error"):
            fingerprint(Broken())


def test_outside_context_uses_native_and_nonatomic_context_rejected():
    assert fingerprint("x") == native("x")
    with pytest.raises(RuntimeError, match="atomic"):
        with memo.operation_fingerprints():
            pass


@pytest.mark.parametrize("corrupt", [False, True])
@pytest.mark.parametrize("enforced", [False, True])
def test_real_four_child_audits_physical_bytes_and_late_rollback(
    request, settings, monkeypatch, corrupt, enforced
):
    from test_rights_portability_batch_projection import REASON, prepared

    from apps.safety import rights_exports
    from apps.safety import rights_portability_coverage_batch as batch
    from apps.safety.models import (
        RightsAction,
        RightsPortabilityCoverageRead,
        RightsPortabilitySelectionRead,
    )

    case, _, coverage, reviewer = prepared(request, settings, monkeypatch, binary=True)
    if enforced:
        # Provision after fixture snapshots, which may replace the worker DB.
        role = request.getfixturevalue("runtime")
        settings.RIGHTS_EVIDENCE_ENFORCED = True
        set_role(role)
    native_read = rights_exports._read_image_blob
    reads = []
    changed = []

    def physical(blob):
        content = native_read(blob)
        reads.append(blob.pk)
        if corrupt and not changed:
            path = Path(blob.derivative.path)
            changed.append((path, path.read_bytes()))
            path.write_bytes(content[:-1] + bytes([content[-1] ^ 1]))
        return content

    monkeypatch.setattr(rights_exports, "_read_image_blob", physical)
    counts = (
        RightsAction.objects.count(),
        RightsPortabilityCoverageRead.objects.count(),
        RightsPortabilitySelectionRead.objects.count(),
    )
    try:
        args = (reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions")
        if corrupt:
            from django.core.exceptions import ValidationError

            with pytest.raises(ValidationError):
                batch.inspect_batch(*args)
            assert counts == (
                RightsAction.objects.count(),
                RightsPortabilityCoverageRead.objects.count(),
                RightsPortabilitySelectionRead.objects.count(),
            )
            assert len(reads) >= 2
        else:
            assert len(batch.inspect_batch(*args)) == 4
            assert len(reads) == 4
            assert RightsPortabilityCoverageRead.objects.count() == counts[1] + 4
            assert RightsPortabilitySelectionRead.objects.count() == counts[2] + 4
    finally:
        for path, content in changed:
            path.write_bytes(content)
    assert memo._current.get() is None


@pytest.mark.parametrize("kind", [str, bytes])
def test_large_index_collision_requires_full_input_and_secret_equality(settings, kind):
    def convert(value):
        return value if kind is str else value.encode()

    first = convert("a" * 32 + "x" * (memo.LARGE_INPUT + 1) + "z" * 32)
    second = convert("a" * 32 + "y" * (memo.LARGE_INPUT + 1) + "z" * 32)
    settings.SECRET_KEY = convert("p" * 32 + "k" * (memo.LARGE_INPUT + 1) + "s" * 32)
    calls = []

    def counted(value):
        calls.append(True)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        assert memo.fingerprint(first, counted) == native(first)
        assert memo.fingerprint(second, counted) == native(second)
        assert memo.fingerprint(first, counted) == native(first)
        assert len(calls) == 2
        settings.SECRET_KEY = convert("p" * 32 + "l" * (memo.LARGE_INPUT + 1) + "s" * 32)
        assert memo.fingerprint(first, counted) == native(first)
        assert len(calls) == 3
        state = memo._current.get()
        assert len(state["entries"]) == 3
        assert len(state["buckets"]) == 1
        bucket = next(iter(state["buckets"].values()))
        assert type(bucket) is dict and len(bucket) == 3
        assert bucket[(first, settings.SECRET_KEY)] in state["entries"]
    assert not state["entries"] and not state["buckets"]


def test_large_index_overhead_counts_against_same_budget(settings, monkeypatch):
    value = "x" * (memo.LARGE_INPUT + 1)
    settings.SECRET_KEY = "small"
    payload_charge = 4 * (len(value) + len(settings.SECRET_KEY))
    monkeypatch.setattr(memo, "MAX_INPUT_BYTES", payload_charge + memo.INDEX_OVERHEAD - 1)
    calls = []

    def counted(value):
        calls.append(True)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        assert memo.fingerprint(value, counted) == native(value)
        assert memo.fingerprint(value, counted) == native(value)
        assert len(calls) == 2
        assert not memo._current.get()["entries"]
        assert not memo._current.get()["buckets"]
        assert memo._current.get()["bytes"] == 0


def test_large_index_secret_drift_during_native_keeps_no_bucket(settings):
    settings.SECRET_KEY = "before"
    value = "x" * (memo.LARGE_INPUT + 1)

    def changing(value):
        settings.SECRET_KEY = "after"
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        assert memo.fingerprint(value, changing) == native(value)
        assert not memo._current.get()["entries"]
        assert not memo._current.get()["buckets"]


@pytest.mark.parametrize("kind", [str, bytes])
def test_index_exact_threshold_uses_original_small_key_then_bucket(kind):
    def value(size):
        result = "x" * size
        return result if kind is str else result.encode()

    with transaction.atomic(), memo.operation_fingerprints():
        small, large = value(memo.LARGE_INPUT), value(memo.LARGE_INPUT + 1)
        assert fingerprint(small) == native(small)
        state = memo._current.get()
        assert not state["buckets"]
        assert any(key[1] == small for key in state["entries"])
        assert fingerprint(large) == native(large)
        assert len(state["buckets"]) == 1
        assert fingerprint(small) == native(small)
        assert fingerprint(large) == native(large)
        assert len(state["entries"]) == 2


@pytest.mark.parametrize("kind", [str, bytes])
def test_late_collision_promotes_only_retained_entry_and_keeps_exact_hits(settings, kind, monkeypatch):
    def convert(value):
        return value if kind is str else value.encode()

    first = convert("a" * (memo.LARGE_INPUT + 1) + "0" + "z" * 32)
    second = convert("a" * (memo.LARGE_INPUT + 1) + "1" + "z" * 32)
    calls = []

    def counted(value):
        calls.append(True)
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        assert memo.fingerprint(first, counted) == native(first)
        state = memo._current.get()
        index = next(iter(state["buckets"]))
        assert type(state["buckets"][index]) is list
        monkeypatch.setattr(memo, "MAX_ENTRIES", 1)
        assert memo.fingerprint(second, counted) == native(second)
        assert type(state["buckets"][index]) is list
        assert len(state["entries"]) == 1
        monkeypatch.setattr(memo, "MAX_ENTRIES", 128)
        assert memo.fingerprint(second, counted) == native(second)
        bucket = state["buckets"][index]
        assert type(bucket) is dict and len(bucket) == 2
        assert set(bucket) == {(first, settings.SECRET_KEY), (second, settings.SECRET_KEY)}
        assert memo.fingerprint(first, counted) == native(first)
        assert memo.fingerprint(second, counted) == native(second)
        assert len(calls) == 3


def test_native_secret_drift_does_not_promote_existing_bucket(settings):
    first = "a" * (memo.LARGE_INPUT + 1) + "0" + "z" * 32
    second = "a" * (memo.LARGE_INPUT + 1) + "1" + "z" * 32
    settings.SECRET_KEY = "before"

    def changing(value):
        settings.SECRET_KEY = "after"
        return native(value)

    with transaction.atomic(), memo.operation_fingerprints():
        assert fingerprint(first) == native(first)
        state = memo._current.get()
        index = next(iter(state["buckets"]))
        assert memo.fingerprint(second, changing) == native(second)
        assert len(state["entries"]) == 1
        assert type(state["buckets"][index]) is list
        settings.SECRET_KEY = "before"
        assert fingerprint(first) == native(first)
        assert type(state["buckets"][index]) is list
