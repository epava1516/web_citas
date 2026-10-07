"""The delegation ledger exception never permits a dirty tested source."""

import hashlib

import pytest

from scripts import verify_promotion_catalogue as runner


def test_independent_task_ledger_is_hashed_without_mutating_it(tmp_path, monkeypatch):
    ledger = tmp_path / ".ai/tasks/desarrollo.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(b"Independent synthetic task update\n")
    original = ledger.read_bytes()
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *args, **kwargs:
                        b".ai/tasks/desarrollo.md\0")
    assert runner.unrelated_task_log(tmp_path) == {
        ".ai/tasks/desarrollo.md": hashlib.sha256(original).hexdigest()}
    assert ledger.read_bytes() == original


@pytest.mark.parametrize("changed", [b"apps/listings/discovery.py\0",
                                    b".ai/tasks/desarrollo.md\0scripts/verify_promotion_catalogue.py\0",
                                    b"docs/17-seguimiento-desarrollo.md\0"])
def test_any_other_tracked_change_blocks_even_with_ledger(changed, tmp_path, monkeypatch):
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *args, **kwargs: changed)
    with pytest.raises(ValueError, match="Commit the tested source"):
        runner.unrelated_task_log(tmp_path)
