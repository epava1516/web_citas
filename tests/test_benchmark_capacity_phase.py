"""Phase codec invariants; no Docker ownership or runtime claim."""

import json

import pytest

from scripts import benchmark_capacity_phase as phase

RUN = '20261022-010000-abcdef12'


def test_atomic_signal_retains_all_boundaries(monkeypatch, tmp_path):
    path = tmp_path / 'signal.json'
    monkeypatch.setattr(phase, 'PHASE_PATH', path)
    clock = iter([10., 20., 30., 40.])
    monkeypatch.setattr(phase.time, 'monotonic', lambda: next(clock))
    writer = phase.CapacityPhaseWriter(RUN)
    writer.advance('arrivals_and_drain')
    writer.advance('idle_after')
    result = phase.decode_phase(path.read_bytes(), RUN)
    assert [e['phase'] for e in result['events']] == list(phase.PHASES)
    assert [e['monotonic'] for e in result['events']] == [10., 20., 30.]
    with pytest.raises(ValueError):
        writer.advance('idle_after')
    assert phase.decode_phase(path.read_bytes(), RUN) == result
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize('defect', ['run', 'order', 'nan', 'negative', 'bool', 'extra', 'empty', 'oversize'])
def test_invalid_signal_rejected(defect):
    payload = {'run': RUN, 'events': [{'phase': 'before_arrivals', 'monotonic': 10.}]}
    if defect == 'run':
        payload['run'] = 'foreign'
    elif defect == 'order':
        payload['events'][0]['phase'] = 'idle_after'
    elif defect in {'nan', 'negative', 'bool'}:
        payload['events'][0]['monotonic'] = {'nan': float('nan'), 'negative': -2, 'bool': True}[defect]
    elif defect == 'extra':
        payload['extra'] = 'not allowed'
    elif defect == 'empty':
        payload['events'] = []
    data = json.dumps(payload).encode() if defect != 'oversize' else b'x' * (phase.MAX_BYTES + 1)
    with pytest.raises(ValueError):
        phase.decode_phase(data, RUN)


@pytest.mark.parametrize('symlink', [False, True])
def test_existing_signal_never_overwritten(monkeypatch, tmp_path, symlink):
    path = tmp_path / 'signal.json'
    target = tmp_path / 'target'
    target.write_text('preserve')
    if symlink:
        path.symlink_to(target)
    else:
        path.write_text('preserve')
    monkeypatch.setattr(phase, 'PHASE_PATH', path)
    with pytest.raises(ValueError, match='Fresh'):
        phase.CapacityPhaseWriter(RUN)
    assert target.read_text() == 'preserve' and path.read_text() == 'preserve'
