"""Prepared finite framing/flag tests. Execution requires root-coordinated window."""
import io
import json
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def baseline_modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    import check_capacity_environment as controller
    import diagnostic_baseline_codec as codec
    return codec, controller


def test_aead_roundtrip_preserves_original_expiry_and_authenticated_end(baseline_modules):
    codec, _ = baseline_modules
    secret, metadata = b'k' * 32, {'valid_until': '2026-10-10T00:00:00+00:00', 'key_version': 'v1'}
    stored = io.BytesIO()
    payload = b'original synthetic binary\x00' * 300000
    codec.encode(io.BytesIO(payload), stored, metadata, secret)
    output = io.BytesIO()
    assert codec.decode(io.BytesIO(stored.getvalue()), output, secret) == metadata
    assert output.getvalue() == payload
    with pytest.raises(ValueError):
        codec.decode(io.BytesIO(stored.getvalue()[:-1]), io.BytesIO(), secret)
    with pytest.raises(ValueError, match='trailing data'):
        codec.decode(io.BytesIO(stored.getvalue() + b'trailing'), io.BytesIO(), secret)
    from cryptography.exceptions import InvalidTag
    corrupt = bytearray(stored.getvalue())
    corrupt[-20] ^= 1
    with pytest.raises(InvalidTag):
        codec.decode(io.BytesIO(corrupt), io.BytesIO(), secret)


@pytest.mark.parametrize('acceptance', ['--delivery-complete', '--preflight-only', '--selection-complete'])
def test_baseline_rejects_acceptance_before_resources(baseline_modules, acceptance):
    _, controller = baseline_modules
    with pytest.raises(SystemExit):
        controller.parse_options(['--owned-controller', '--object-delivery', '--delivery-profile',
            '--delivery-profile-full', '--selection-tcp', '--selection-concurrent',
            '--selection-gunicorn', '--database-heavy', '--diagnostic-baseline-capture',
            '--diagnostic-baseline-key', '/private/key', acceptance])


def test_baseline_index_stream_is_bounded_and_ordered(baseline_modules, tmp_path):
    codec, _ = baseline_modules
    from diagnostic_baseline_archive import Reader
    raw = io.BytesIO()
    codec.encode(io.BytesIO(b'binary' * 1000), raw, {'version': 1}, b'k' * 32)
    archive = tmp_path / 'artifacts.tar'
    with tarfile.open(archive, 'w') as tar:
        for name, value in [('baseline.index.json', json.dumps({'parts': ['baseline.0000.bin']}).encode()),
                            ('baseline.0000.bin', raw.getvalue())]:
            info = tarfile.TarInfo(name)
            info.size = len(value)
            tar.addfile(info, io.BytesIO(value))
    with Reader(archive) as source:
        output = io.BytesIO()
        assert codec.decode(source, output, b'k' * 32) == {'version': 1}
        assert output.getvalue() == b'binary' * 1000
