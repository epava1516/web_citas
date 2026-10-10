"""Pure context guards with fake source/connection; NOT PostgreSQL verification."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from apps.safety import rights_inspection_source as module


@pytest.fixture
def state(monkeypatch):
    connection = SimpleNamespace(in_atomic_block=True)
    case = SimpleNamespace(pk=1, version=2, person_id=3, account_subject_id=None, manager_version=4)
    person = SimpleNamespace(pk=3)
    listing = SimpleNamespace(pk=5)
    rows = {"source": {"synthetic": ["original"]}, "calls": 0}

    def copy(*args):
        rows["calls"] += 1
        return deepcopy(rows["source"])

    def rows_fingerprint(*args):
        # Fake row versions: any change to the fake database rows changes the fingerprint.
        rows["fingerprints"] = rows.get("fingerprints", 0) + 1
        return repr(rows["source"])

    monkeypatch.setattr(module.transaction, "get_connection", lambda: connection)
    monkeypatch.setattr(module, "source_copy", copy)
    monkeypatch.setattr(module, "source_fingerprint", rows_fingerprint)
    return case, person, listing, rows, connection


def test_reuse_fresh_exit_and_expired_context(state):
    case, person, listing, rows, _ = state
    with module.inspection_source(person, listing, case) as context:
        for _ in range(8):
            assert module.shared_source(context, person, listing, case) == rows["source"]
        assert rows["calls"] == 1
    # Unchanged row versions: the exit needs no second full copy, only a second fingerprint.
    assert rows["calls"] == 1 and rows["fingerprints"] == 2
    with pytest.raises(ValidationError):
        module.shared_source(context, person, listing, case)


def test_changed_versions_with_identical_content_fall_back_to_full_comparison(state, monkeypatch):
    case, person, listing, rows, _ = state
    versions = iter(["before", "after"])
    monkeypatch.setattr(module, "source_fingerprint", lambda *args: next(versions))
    with module.inspection_source(person, listing, case):
        pass
    assert rows["calls"] == 2  # Fingerprint differed; the full copy proved equal content.


@pytest.mark.parametrize("change", ["database", "projection"])
def test_drift_or_projection_mutation_rejected_and_context_reset(state, change):
    case, person, listing, rows, _ = state
    with pytest.raises(ValidationError, match="changed before return"):
        with module.inspection_source(person, listing, case) as context:
            target = rows["source"] if change == "database" else context.source
            target["synthetic"].append("altered")
    with pytest.raises(ValidationError):
        module.shared_source(context, person, listing, case)


def test_wrong_scope_and_cross_thread_context_denied(state):
    from concurrent.futures import ThreadPoolExecutor

    case, person, listing, _, _ = state
    with module.inspection_source(person, listing, case) as context:
        other = SimpleNamespace(**(vars(case) | {"pk": 100}))
        with pytest.raises(ValidationError):
            module.shared_source(context, person, listing, other)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(module.shared_source, context, person, listing, case)
            with pytest.raises(ValidationError):
                future.result(timeout=5)


def test_exception_resets_context_without_turning_failure_into_success(state):
    case, person, listing, _, _ = state
    with pytest.raises(RuntimeError, match="Synthetic failure"):
        with module.inspection_source(person, listing, case) as context:
            raise RuntimeError("Synthetic failure")
    with pytest.raises(ValidationError):
        module.shared_source(context, person, listing, case)


def test_no_transaction_or_forged_context_rejected(state):
    case, person, listing, _, connection = state
    connection.in_atomic_block = False
    with pytest.raises(RuntimeError):
        with module.inspection_source(person, listing, case):
            pytest.fail("Unexpected context")
    with pytest.raises(ValidationError):
        module.shared_source(object(), person, listing, case)
