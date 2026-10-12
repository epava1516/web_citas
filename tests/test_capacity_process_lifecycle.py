"""Reaping races must be bounded, and genuine surviving processes must fail."""

from pathlib import Path

import capacity_gunicorn
import pytest


def test_observed_exit_waits_for_reaper(monkeypatch, tmp_path):
    process = tmp_path / '123'
    process.mkdir()
    (process / 'stat').write_text('123 (synthetic) Z')
    sleeps = []

    def reap(delay):
        sleeps.append(delay)
        (process / 'stat').unlink()
        process.rmdir()

    monkeypatch.setattr(capacity_gunicorn.time, 'sleep', reap)
    capacity_gunicorn.wait_observed_exit(['123'], proc=tmp_path)
    assert sleeps == [.05]


@pytest.mark.parametrize('state', ['S', 'Z'])
def test_observed_exit_rejects_live_process_and_unreaped_zombie(tmp_path, state):
    process = tmp_path / '123'
    process.mkdir()
    (process / 'stat').write_text(f'123 (synthetic) {state}')
    with pytest.raises(AssertionError, match=f'123 .* {state}'):
        capacity_gunicorn.wait_observed_exit(['123'], proc=Path(tmp_path), timeout=0)
