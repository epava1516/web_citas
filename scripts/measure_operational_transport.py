"""Paced local emitter measurement; real drained pipe, no HTTP/capacity claim."""
import argparse
import hashlib
import json
import logging
import os
import resource
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

from apps.core import operational_events as events
from apps.core.operational_event_handler import NonBlockingOperationalHandler


def rss_bytes():
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1]) * 1024
    raise RuntimeError('Linux RSS observation unavailable')


def sample(mode):
    handler = NonBlockingOperationalHandler() if mode == 'transport' else logging.NullHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    events.logger.handlers = [handler]
    events.logger.setLevel(logging.INFO)
    events.logger.propagate = False
    before_rss = rss_bytes()
    started = time.perf_counter_ns()
    events.publication_read({'route': 'state', 'reason': 'trusted_state'}, 200)
    cold_ns = time.perf_counter_ns() - started
    if mode == 'transport':
        deadline = time.monotonic() + 5
        while handler.transport_status()['written'] != 1:
            if time.monotonic() >= deadline:
                raise RuntimeError('Warmup drain deadline exceeded')
            time.sleep(.001)
    warm_rss = rss_bytes()
    durations = []
    late = []
    start = time.perf_counter()
    cpu = time.process_time()
    for index in range(100):
        due = start + index / 20
        time.sleep(max(0, due - time.perf_counter()))
        late.append(max(0, time.perf_counter() - due))
        tick = time.perf_counter_ns()
        events.publication_read({'route': 'state', 'reason': 'trusted_state'}, 200)
        durations.append(time.perf_counter_ns() - tick)
    if mode == 'transport':
        deadline = time.monotonic() + 5
        while True:
            state = handler.transport_status()
            if state['written'] == 101 and state['queued'] == state['inflight'] == 0:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Measured drain deadline exceeded')
            time.sleep(.001)
        assert state['dropped'] == state['write_errors'] == state['queued'] == state['inflight'] == 0
    else:
        state = None
    cpu_seconds = time.process_time() - cpu
    elapsed = time.perf_counter() - start
    end_rss = rss_bytes()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    handler.close()
    if mode == 'transport':
        handler._thread.join(timeout=2)
        assert not handler._thread.is_alive()
    events.logger.handlers = []
    return {'mode': mode, 'events': 100, 'warmup_events': 1, 'rate': 20,
            'cold_call_ns': cold_ns, 'producer_call_ns': durations,
            'producer_p50_ns': statistics.median(durations),
            'producer_p95_ns': sorted(durations)[94], 'producer_max_ns': max(durations),
            'cpu_seconds_with_writer_and_drain': cpu_seconds, 'wall_seconds': elapsed,
            'pacing_max_lateness_seconds': max(late),
            'rss_before_bytes': before_rss, 'rss_after_warmup_bytes': warm_rss,
            'rss_after_measurement_bytes': end_rss, 'process_peak_rss_bytes': peak_rss,
            'transport_status': state}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', choices=['null', 'transport'])
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if options.child:
        print(json.dumps(sample(options.child)))
        return
    if options.output is None or options.output.exists():
        parser.error('A fresh --output artifact is required')
    results = []
    # Fresh interpreters in an explicit balanced order. No simultaneous writers.
    for mode in ['null', 'transport', 'transport', 'null', 'null', 'transport']:
        process = subprocess.Popen(
            [sys.executable, '-m', 'scripts.measure_operational_transport', '--child', mode],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        )
        received = []
        errors = []

        def drain():
            try:
                for line in process.stderr:
                    if len(line) > 2048 or len(received) >= 102:
                        raise RuntimeError('Unexpected event volume')
                    received.append(json.loads(line))
            except Exception as exc:
                errors.append(type(exc).__name__)

        collector = threading.Thread(target=drain, daemon=True)
        collector.start()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, 9)
            process.wait(timeout=5)
            raise
        finally:
            collector.join(timeout=3)
        assert not collector.is_alive() and not errors and process.returncode == 0
        result = json.loads(process.stdout.read())
        process.stdout.close()
        process.stderr.close()
        assert len(received) == (101 if mode == 'transport' else 0)
        assert all(row == {
            'schema_version': 1, 'event': 'publication_read',
            'timestamp_seconds': row['timestamp_seconds'], 'route': 'state',
            'reason': 'trusted_state', 'status_class': '2xx',
        } for row in received)
        result['received_events'] = len(received)
        results.append(result)
    sources = ['scripts/measure_operational_transport.py', 'apps/core/operational_events.py',
               'apps/core/operational_event_handler.py']
    proof = {'scope': 'paced emitter only; not HTTP SLO, PostgreSQL or capacity',
             'order': [row['mode'] for row in results], 'samples': results,
             'source_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
             'baseline': 'Same serialization/logger INFO; NullHandler versus bounded transport',
             'limits': ['Three fresh processes per arm, no general reproducibility claim',
                        'RSS before/after are sampled; ru_maxrss is whole process high water',
                        'Paced20events/s, not overload or normal HTTP end-to-end',
                        'No adoption of alert budget or B12 acceptance']}
    options.output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({'result': 'MEASUREMENT_INTEGRITY_PASS', 'samples': len(results),
                      'output': str(options.output)}))


if __name__ == '__main__':
    main()
