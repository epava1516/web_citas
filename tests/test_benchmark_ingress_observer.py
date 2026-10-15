import builtins
from types import SimpleNamespace

from django.db import connection

from scripts.benchmark_ingress_observer import post_worker_init, worker_exit
from scripts.benchmark_server_samples import parse_service_samples


def test_ingress_hook_avoids_eager_handlers_and_restores_callback_resources(tmp_path, monkeypatch):
    monkeypatch.setenv('WEB_MODELOS_BENCHMARK_OBSERVER_DIR', str(tmp_path))
    monkeypatch.setitem(connection.settings_dict, 'NAME', 'test_promotion_gate_own_control')
    original_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert not name.startswith('apps.'), 'Diagnostic must not eagerly load handlers'
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', guarded)
    worker = SimpleNamespace(wsgi=lambda *args: [])
    before = list(connection.execute_wrappers)
    try:
        post_worker_init(worker)
        assert len(connection.execute_wrappers) == len(before) + 1
        assert worker._benchmark_observer.gc_observer.policy_before['enabled']
    finally:
        if hasattr(worker, '_benchmark_observer'):
            worker_exit(None, worker)
        connection.execute_wrappers[:] = before


def test_service_ledger_preserves_ids_and_rejects_duplicates_nonfinite_without_paths():
    result = parse_service_samples([
        '200 0.31 /private-secret?token=secret d-1',
        '200 0.12 /secret -',
        '200 0.45 /secret d-1',
        '200 nan /secret d-2',
        '200 -1 /secret d-3',
        '302 0.20 /secret u-0',
        '999 0.20 /secret d-4',
        '200 0.21 /secret d-5',
    ])
    assert result['samples'] == [dict(id='d-1', status=200, service_seconds=.31),
                                 dict(id='d-5', status=200, service_seconds=.21)]
    assert len(result['parse_errors']) == 4
    assert 'secret' not in str(result)
