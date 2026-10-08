"""Read-only offline verification. Argument: extracted/raw experiment directory.

No DB, HTTP, environment secrets, workload, source mutation or live cleanup.
The original independent live review is archived; this recalculates arithmetic.
"""
import collections
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

out = Path(sys.argv[1])
result = json.loads((out / 'result.json').read_text())
for name, digest in result['artifact_sha256'].items():
    assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest, name


def family(path):
    return 'search' if '?q=' in path else 'detail' if '/listing/' in path else 'listing'


def percentile(values, ratio):
    return sorted(values)[max(0, math.ceil(len(values) * ratio) - 1)]


def numbers(value):
    return {line.split()[0]: int(line.split()[1]) for line in value.splitlines()
            if len(line.split()) == 2 and line.split()[1].isdigit()}


blocks = []
for folder in sorted(out.glob('block-*')):
    summary = json.loads((folder / 'load-summary.json').read_text())
    raw = json.loads((folder / 'benchmark-samples.json').read_text())
    events = json.loads((folder / 'benchmark-worker-events.json').read_text())
    probe = json.loads((folder / 'resource-samples.jsonl.summary.json').read_text())
    snapshots = [json.loads(line) for line in (folder / 'resource-samples.jsonl').read_text().splitlines()]
    ends = {}
    for event in events['events']:
        if event['event'] == 'wsgi_end':
            assert event['id'] not in ends
            ends[event['id']] = event
    rows = raw['dynamic']
    assert len(rows) == len({r['id'] for r in rows}) == 600
    assert collections.Counter(family(r['path']) for r in rows) == {'listing': 200, 'search': 200, 'detail': 200}
    assert all(r['emitted_at'] is not None and r['ended_at'] is not None for r in rows)
    assert all(r['id'] in ends for r in rows)
    delay = [r['emitted_at'] - r['scheduled_at'] for r in rows]
    valid = percentile(delay, .95) <= .01 and percentile(delay, .99) <= .025 and max(delay) <= .1
    means = {f: statistics.mean(ends[r['id']]['wall'] for r in rows if family(r['path']) == f)
             for f in ['listing', 'search', 'detail']}
    D = sum(means.values()) / 3
    upload = raw['uploads'][0]
    assert len(raw['uploads']) == 1 and upload['status'] == 302
    W = 20 * D + ends[upload['id']]['wall'] / 60
    success_window = sum(r['ended_at'] <= 30 and not r['unexpected'] for r in rows)
    origin = summary['monotonic_origin_seconds']
    window = [s for s in snapshots if origin <= s['monotonic'] <= origin + 30]
    a, b = window[0], window[-1]
    dt = b['monotonic'] - a['monotonic']
    hz, master = probe['clock_ticks_per_second'], probe['app_master_pid']
    pa = {p['pid']: p for p in a['processes']}
    client = pa[master]['ppid']
    runner = pa[client]['ppid']
    app_cpu = own_cpu = 0
    for x, y in zip(window, window[1:]):
        first, last = {p['pid']: p for p in x['processes']}, {p['pid']: p for p in y['processes']}
        for pid, p in first.items():
            q = last.get(pid)
            if not q or p['start_ticks'] != q['start_ticks']:
                continue
            cpu = (q['cpu_ticks'] - p['cpu_ticks']) / hz
            if pid == master or p['ppid'] == master:
                app_cpu += cpu
            elif pid in {client, runner}:
                own_cpu += cpu
    def pg_cpu(sample):
        return numbers(next(iter(sample['pg_cgroups'].values()))['cpu.stat'])['usage_usec'] / 1e6
    shared_pg_cpu = pg_cpu(b) - pg_cpu(a)
    host_cpu = sum(b['host_cpu_ticks'][i] - a['host_cpu_ticks'][i] for i in [0, 1, 2, 5, 6]) / hz
    external = (host_cpu - app_cpu - shared_pg_cpu - own_cpu) / dt
    p95 = percentile([r['ended_at'] - r['emitted_at'] for r in rows], .95)
    block = dict(index=summary['index'], workers=summary['workers'], success_window=success_window,
                 pending_window=600-success_window, p95=p95, errors=sum(r['unexpected'] for r in rows)/600,
                 D=D, W20_upload_contractual=W, external_CPU=external, generator_valid=valid)
    prior = json.loads((folder / 'analysis.json').read_text())
    assert success_window == prior['window']['counts']['successful']
    for observed, expected in [(D, prior['cohort']['D_worker_seconds_per_request']),
                               (W, prior['cohort']['W20_contractual_including_upload']),
                               (p95, prior['cohort']['observable_latency_seconds']['p95']),
                               (external, prior['window']['resources']['unrelated_host_residual_mean_CPU_cores'])]:
        assert abs(observed - expected) < 1e-9
    assert valid and p95 >= .8 and block['errors'] == 0
    blocks.append(block)
assert [b['workers'] for b in blocks] == [4, 6, 6, 4]
spread = max(b['external_CPU'] for b in blocks) - min(b['external_CPU'] for b in blocks)
pairs = []
for four, six in [(blocks[0], blocks[1]), (blocks[3], blocks[2])]:
    pairs.append(dict(completion_improvement=six['success_window']/four['success_window']-1,
                      D_ratio=six['D']/four['D'],
                      prefixed_effect_pass=six['success_window'] >= 1.1*four['success_window']
                      and six['p95'] < four['p95'] and six['errors'] <= four['errors']
                      and six['D'] <= 1.1*four['D']))
print(json.dumps(dict(blocks=blocks, pairs=pairs, host_competition_range=spread,
                     causal='INCONCLUSIVE' if spread > .5 else 'WITHIN_HOST_BOUND',
                     block_verdicts=['FAIL']*4, no_load_executed=True), indent=2))
