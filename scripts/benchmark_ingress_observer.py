"""Isolated WSGI/SQL/GC observation without eager application-handler imports."""

import os
from pathlib import Path

from scripts.benchmark_worker_observer import WorkerObserver, worker_exit  # noqa: F401


def post_worker_init(worker):
    from django.db import connection

    folder = os.environ.get('WEB_MODELOS_BENCHMARK_OBSERVER_DIR')
    if (not folder or not Path(folder).is_dir() or connection.vendor != 'postgresql'
            or not connection.settings_dict['NAME'].startswith('test_promotion_gate_')):
        raise RuntimeError('Ingress observer requires owned synthetic PostgreSQL runner')
    observer = WorkerObserver(folder, observe_gc=True)
    worker._benchmark_observer = observer
    connection.execute_wrappers.append(observer.sql)
    worker.wsgi = observer.wsgi(worker.wsgi)
