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


def test_ustar_many_regular_logs_and_extended_header_rejected_before_payload(baseline_modules, tmp_path):
    codec, _ = baseline_modules
    from diagnostic_baseline_archive import Reader
    raw = io.BytesIO()
    codec.encode(io.BytesIO(b'original'), raw, {'version': 1}, b'k' * 32)
    archive = tmp_path / 'many.tar'
    with tarfile.open(archive, 'w', format=tarfile.USTAR_FORMAT) as tar:
        records = [(f'log-{number}.txt', b'log') for number in range(120)]
        records += [('baseline.index.json', json.dumps({'parts': ['baseline.0000.bin']}).encode()), ('baseline.0000.bin', raw.getvalue())]
        for name, value in records:
            info = tarfile.TarInfo(name)
            info.size = len(value)
            tar.addfile(info, io.BytesIO(value))
    with Reader(archive) as source:
        output = io.BytesIO()
        codec.decode(source, output, b'k' * 32)
        assert output.getvalue() == b'original'
    # Deliberately claim a huge extended-header payload without providing it.
    # The fixed header must be rejected before any tar/PAX parser reads it.
    info = tarfile.TarInfo('pax')
    info.type, info.size = tarfile.XHDTYPE, 300 * 1024 ** 2
    malformed = tmp_path / 'pax.tar'
    malformed.write_bytes(info.tobuf(format=tarfile.USTAR_FORMAT))
    with pytest.raises(ValueError, match='simple regular USTAR'):
        Reader(malformed)


def test_reader_constructor_closes_file_when_index_missing(baseline_modules, tmp_path, monkeypatch):
    import builtins

    from diagnostic_baseline_archive import Reader
    path = tmp_path / 'empty.tar'
    with tarfile.open(path, 'w', format=tarfile.USTAR_FORMAT):
        pass
    opened, actual = [], builtins.open
    def tracked(*args, **kwargs):
        stream = actual(*args, **kwargs)
        opened.append(stream)
        return stream
    monkeypatch.setattr(builtins, 'open', tracked)
    with pytest.raises(KeyError):
        Reader(path)
    assert opened and all(stream.closed for stream in opened)


def test_private_input_ram_reserves_full_rounded_bytes_without_changing_cpu(baseline_modules, tmp_path):
    from diagnostic_baseline_budget import reserve_private_inputs
    allocations = {'pg': (150000, 3072), 'redis': (10000, 384), 'app': (175000, 3968),
                   'objects': (50000, 512), 'caddy': (10000, 128)}
    key, source = tmp_path / 'key', tmp_path / 'input'
    key.write_bytes(b'k' * 32)
    source.touch()
    key.chmod(0o600)
    source.chmod(0o600)
    with source.open('wb') as stream:
        stream.truncate(256 * 1024 ** 2)
    changed, reserved = reserve_private_inputs(allocations, source, key)
    assert reserved == 257
    assert changed['app'] == (175000, 3968 - 257)
    assert sum(value[1] for value in changed.values()) + 128 + reserved == 8192
    assert sum(value[0] for value in changed.values()) + 5000 == 400000
    with source.open('wb') as stream:
        stream.truncate(256 * 1024 ** 2 + 1)
    with pytest.raises(ValueError):
        reserve_private_inputs(allocations, source, key)
    assert reserve_private_inputs(allocations, None, key)[1] == 1


@pytest.mark.parametrize('flag', ['CAPACITY_DELIVERY_COMPLETE', 'CAPACITY_SELECTION_COMPLETE', 'CAPACITY_PREFLIGHT_ONLY'])
def test_helper_acceptance_guard_precedes_owned_database(flag):
    from types import SimpleNamespace

    from diagnostic_baseline_guards import require_diagnostic
    called = []
    def database_spy():
        called.append(True)
        pytest.fail('Acceptance reached the database ownership guard')
    with pytest.raises(ValueError, match='acceptance or preflight'):
        require_diagnostic(SimpleNamespace(**{flag: True}), database_spy)
    assert not called


@pytest.mark.parametrize(('full', 'profile'), [(False, False), (True, False), (False, True)])
def test_verified_helper_requires_both_diagnostic_flags_before_database(full, profile):
    from types import SimpleNamespace

    from diagnostic_baseline_guards import require_diagnostic
    called = []
    with pytest.raises(ValueError, match='full diagnostic'):
        require_diagnostic(SimpleNamespace(CAPACITY_ENVIRONMENT_VERIFIED=True,
                           CAPACITY_DELIVERY_PROFILE_FULL=full, CAPACITY_DELIVERY_PROFILE=profile),
                           lambda: called.append(True))
    assert not called


def test_local_owned_n2_and_full_diagnostic_reach_ownership_guard():
    from types import SimpleNamespace

    from diagnostic_baseline_guards import require_diagnostic
    calls = []
    def owned():
        calls.append(True)
        return 'verified-own-context'
    assert require_diagnostic(SimpleNamespace(), owned) == 'verified-own-context'
    assert require_diagnostic(SimpleNamespace(CAPACITY_ENVIRONMENT_VERIFIED=True,
                              CAPACITY_DELIVERY_PROFILE_FULL=True, CAPACITY_DELIVERY_PROFILE=True), owned) == 'verified-own-context'
    assert calls == [True, True]



def test_capture_archive_expanded_count_remains_finite_and_normal_default(baseline_modules, tmp_path):
    from capacity_artifacts import ArchiveSink
    path = tmp_path / 'capture.tar'
    path.touch(mode=0o600)
    sink = ArchiveSink(path, max_files=256, format=tarfile.USTAR_FORMAT)
    try:
        for number in range(255):
            sink.write(f'log-{number}.txt', 'tiny')
        sink.write('report.json', '{}')
        with pytest.raises(ValueError, match='count exceeds'):
            sink.write('overflow.txt', 'tiny')
    finally:
        sink.close()
    with tarfile.open(path, 'r:') as archive:
        assert len(archive.getmembers()) == 256
    normal = tmp_path / 'normal.tar'
    normal.touch(mode=0o600)
    sink = ArchiveSink(normal)
    try:
        assert sink.max_files == 100
    finally:
        sink.close()
    with pytest.raises(ValueError, match='within1..256'):
        ArchiveSink(normal, max_files=257)


@pytest.mark.parametrize('active,value', [('missing', 'invalid'), ('v1', 'invalid'), ('v1', 'AAAA')])
def test_header_bad_keyring_rejected_before_object_bootstrap(baseline_modules, active, value):
    codec, _ = baseline_modules
    with pytest.raises(ValueError):
        codec.importable_header({'format': 'mod08-approved-diagnostic-v1',
                                 'objects': {'active_key': active, 'keyring': json.dumps({'v1': value})}})


def test_controller_error_scrubs_timeout_command_secrets(baseline_modules):
    import subprocess
    _, controller = baseline_modules
    sentinel = 'private-sentinel-password'
    keyring = '{"original": "private-sentinel-key"}'
    exc = subprocess.TimeoutExpired(['docker', '-e', 'POSTGRES_PASSWORD=' + sentinel,
                                     '-e', 'RIGHTS_OBJECT_KEYS=' + keyring], 180)
    error = controller.scrub_private(f'{type(exc).__name__}: {exc}', {sentinel, keyring})
    assert sentinel not in error
    assert 'private-sentinel-key' not in error
    assert 'TimeoutExpired' in error
