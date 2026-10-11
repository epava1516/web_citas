"""Finite host-only timing tests, not request capacity acceptance."""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests import capacity_request_timing as timing


class Response:
    def __init__(self, error=None, close_error=None):
        self.error = error
        self.close_error = close_error
        self.closed = 0

    def __iter__(self):
        yield b'first'
        if self.error:
            raise self.error
        yield b'last'

    def close(self):
        self.closed += 1
        if self.close_error:
            raise self.close_error


@pytest.mark.parametrize('value', [None, '', '0', '-1', '2049', '0001', '1x', '1\n', 1, True])
def test_invalid_ids(value):
    assert timing.sample_id(value) is None


@pytest.mark.parametrize('value', ['1', '2048'])
def test_valid_ids(value):
    assert timing.sample_id(value) == int(value)


def test_consumption_and_close_then_record(monkeypatch):
    events, records = [], []
    response = Response()
    original_close = response.close
    def close():
        events.append('close')
        original_close()
    response.close = close
    clock = iter([10, 30])
    cpu = iter([5, 12])
    monkeypatch.setattr(timing, 'perf_counter_ns', lambda: next(clock))
    monkeypatch.setattr(timing, 'thread_time_ns', lambda: next(cpu))
    def record(item):
        events.append('record')
        records.append(item)
    monkeypatch.setattr(timing, 'write_record', record)
    assert list(timing.observe(lambda env, start: response, {}, None, 2)) == [b'first', b'last']
    assert events == ['close', 'record']
    assert records == [{'id': 2, 'wall_ns': 20, 'thread_cpu_ns': 7, 'complete': 1}]


@pytest.mark.parametrize('where', ['application', 'iterate', 'close'])
def test_exact_domain_exception_and_incomplete_record(monkeypatch, where):
    error = ValueError('private error')
    records = []
    monkeypatch.setattr(timing, 'write_record', lambda record: records.append(record))
    response = Response(error=error if where == 'iterate' else None,
                        close_error=error if where == 'close' else None)
    def application(env, start):
        if where == 'application':
            raise error
        return response
    with pytest.raises(ValueError) as captured:
        list(timing.observe(application, {}, None, 1))
    assert captured.value is error
    assert records[0]['complete'] == 0
    assert 'private' not in str(records)


def test_partial_generator_close_records_incomplete(monkeypatch):
    records = []
    monkeypatch.setattr(timing, 'write_record', lambda record: records.append(record))
    response = Response()
    iterable = timing.observe(lambda env, start: response, {}, None, 1)
    assert next(iterable) == b'first'
    iterable.close()
    assert response.closed == 1
    assert records[0]['complete'] == 0


def test_record_failure_does_not_replace_result_or_error(monkeypatch):
    def fail(record):
        raise OSError('private recording failure')
    monkeypatch.setattr(timing, 'write_record', fail)
    assert list(timing.observe(lambda env, start: Response(), {}, None, 1)) == [b'first', b'last']
    error = ValueError('domain')
    with pytest.raises(ValueError) as captured:
        list(timing.observe(lambda env, start: Response(error=error), {}, None, 1))
    assert captured.value is error


def test_writer_reader_numeric_and_global_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(timing, 'DIRECTORY', tmp_path)
    record = {'id': 1, 'wall_ns': 10, 'thread_cpu_ns': 5, 'complete': 1}
    assert timing.write_record(record)
    monkeypatch.setattr(timing, 'MAX_RECORDS', 1)
    assert not timing.write_record({**record, 'id': 2})
    assert timing.collect(tmp_path)['records'] == [record]
    assert not timing.collect(tmp_path)['incomplete']
    assert all(path.stat().st_mode & 0o077 == 0 for path in tmp_path.iterdir())


def test_writer_io_failure_and_byte_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(timing, 'DIRECTORY', tmp_path)
    monkeypatch.setattr(timing, 'MAX_BYTES', 1)
    assert not timing.write_record({'id': 1, 'wall_ns': 1, 'thread_cpu_ns': 1, 'complete': 1})
    monkeypatch.setattr(timing, '_open', lambda path: (_ for _ in ()).throw(OSError()))
    assert not timing.write_record({'id': 1, 'wall_ns': 1, 'thread_cpu_ns': 1, 'complete': 1})


def test_concurrent_writers_stay_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(timing, 'DIRECTORY', tmp_path)
    monkeypatch.setattr(timing, 'MAX_RECORDS', 4)
    def write(identifier):
        return timing.write_record({'id': identifier, 'wall_ns': 1, 'thread_cpu_ns': 1, 'complete': 1})
    with ThreadPoolExecutor(max_workers=2) as executor:
        successes = list(executor.map(write, range(1, 20)))
    records = timing.collect(tmp_path)['records']
    assert 1 <= len(records) <= 4
    assert len(records) == sum(successes)


@pytest.mark.parametrize('raw', [b'private malformed\n', b'x' * 1000,
    b'{"id":true,"wall_ns":1,"thread_cpu_ns":1,"complete":1}\n'])
def test_reader_rejects_without_raw_text(tmp_path, raw):
    (tmp_path / 'capacity-request-timing-1.jsonl').write_bytes(raw)
    result = timing.collect(tmp_path)
    assert result['incomplete']
    assert 'private' not in str(result)


def test_reader_duplicate_ids_incomplete(tmp_path):
    record = {'id': 1, 'wall_ns': 1, 'thread_cpu_ns': 1, 'complete': 1}
    (tmp_path / 'capacity-request-timing-1.jsonl').write_text((json.dumps(record) + '\n') * 2)
    assert timing.collect(tmp_path)['incomplete']


@pytest.mark.parametrize('identifier', [None, '', '0', '2049', 'bad'])
def test_wsgi_unmarked_invalid_no_observer_or_headers(monkeypatch, identifier):
    import capacity_profile_wsgi as wrapper
    response = Response()
    headers = [('Cache-Control', 'no-store')]
    seen = []
    def application(env, start):
        start('200 OK', headers)
        return response
    monkeypatch.setattr(wrapper, 'original', application)
    monkeypatch.setattr(wrapper, 'observe', lambda *args: pytest.fail('observer invoked'))
    environment = {} if identifier is None else {timing.ENV_HEADER: identifier}
    assert list(wrapper.application(environment, lambda status, values: seen.append(values))) == [b'first', b'last']
    assert seen == [headers]
    assert response.closed == 1


def test_wsgi_marked_no_phase_or_worker_profile(monkeypatch):
    import capacity_profile_wsgi as wrapper
    import capacity_request_timing as deployed_timing
    records = []
    response = Response()
    monkeypatch.setattr(deployed_timing, 'write_record', lambda record: records.append(record))
    monkeypatch.setattr(wrapper, 'original', lambda env, start: response)
    monkeypatch.setattr(wrapper, 'phase_scope', lambda **kwargs: pytest.fail('phase observer invoked'))
    monkeypatch.setattr(wrapper, 'scope', lambda: pytest.fail('worker profile invoked'))
    assert list(wrapper.application({timing.ENV_HEADER: '2048'}, None)) == [b'first', b'last']
    assert response.closed == 1 and records[0]['id'] == 2048
    assert records[0]['complete'] == 1


def test_client_pair_ids_align_with_tcp_samples_and_exclude_profiled():
    import ast
    from pathlib import Path
    from types import SimpleNamespace

    # Compile only the client sampling function; no fixture/application imports.
    tree = ast.parse(Path(__file__).with_name('capacity_delivery_flow.py').read_text())
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == 'sampled')
    namespace = {'HEADER': timing.HEADER}
    seen = []
    def post(client, endpoint, csrf, values, headers):
        seen.append(headers)
        return SimpleNamespace(seconds=1.5, interval=[10, 11.5], body=b'ok', status=200,
                               headers={'Cache-Control': 'no-store'}, stages=[])
    namespace['post'] = post
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<sampled-client-test>', 'exec'), namespace)
    barrier = SimpleNamespace(wait=lambda **kwargs: None)
    metrics = {}
    for identifier, profile in [(1, False), (2, True), (3, False)]:
        assert namespace['sampled'](metrics, 'coverage_page_read', barrier, None, '', '', {},
                                    profile=profile, request_id=identifier) == b'ok'
    assert metrics['coverage_page_read_request_ids'] == [1, 3]
    assert len(metrics['coverage_page_read']) == len(metrics['coverage_page_read_request_ids']) == 2
    assert seen == [{timing.HEADER: '1'}, {'X-Capacity-Profile': 'coverage_page_read'},
                    {timing.HEADER: '3'}]


def test_writer_rejects_non_numeric_extra_fields_before_file_work(tmp_path, monkeypatch):
    monkeypatch.setattr(timing, 'DIRECTORY', tmp_path)
    assert not timing.write_record({'id': 1, 'private': 'never serialize'})
    assert not list(tmp_path.iterdir())


def test_reader_incomplete_response_marked_incomplete(tmp_path):
    record = {'id': 1, 'wall_ns': 1, 'thread_cpu_ns': 1, 'complete': 0}
    (tmp_path / 'capacity-request-timing-1.jsonl').write_text(json.dumps(record) + '\n')
    assert timing.collect(tmp_path)['incomplete']
