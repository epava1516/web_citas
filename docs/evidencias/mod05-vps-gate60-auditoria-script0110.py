"""Read-only original-sample audit of the authorized VPS short gate."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1])
samples = json.loads((root / 'benchmark-samples.json').read_text())
summary = json.loads((root / 'load-summary.json').read_text())
rows = samples['dynamic']
assert len(rows) == 1200 and len({row['id'] for row in rows}) == 1200
assert all(row['id'] == f'd-{i}' and abs(row['scheduled_at'] - i / 20) < 1e-9 for i,row in enumerate(rows))
assert all(0 <= row['scheduled_at'] <= row['emitted_at'] < 60 for row in rows)
assert all(row['ended_at'] >= row['emitted_at'] for row in rows)

def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]

def family(row):
    return 'detail' if '/listing/' in row['path'] else 'search' if '?' in row['path'] else 'listing'

latency = [row['ended_at'] - row['emitted_at'] for row in rows]
delay = [row['emitted_at'] - row['scheduled_at'] for row in rows]
completed = [row for row in rows if row['ended_at'] <= 60]
errors = sum(row['unexpected'] or row['timeout'] for row in rows)
result = {
    'validity': 'VALID', 'gate': 'FAIL',
    'scheduled': len(rows), 'emitted': len(rows), 'not_emitted': 0,
    'final_success': sum(row['status'] == 200 and not row['unexpected'] for row in rows),
    'final_errors': errors, 'final_timeouts': sum(row['timeout'] for row in rows),
    'final_pending': 0, 'completed_during_emission': len(completed),
    'pending_at_window': len(rows)-len(completed), 'throughput_completed_per_second': len(completed)/60,
    'family_populations': dict(Counter(map(family, rows))),
    'completed_during_emission_by_family': dict(Counter(map(family, completed))),
    'http_latency_seconds': {'mean': sum(latency)/len(latency), 'p95': percentile(latency,.95), 'p99': percentile(latency,.99), 'max':max(latency)},
    'generator_delay_ms': {'p95':1000*percentile(delay,.95),'p99':1000*percentile(delay,.99),'max':1000*max(delay)},
    'drain_seconds': summary['actual_elapsed_seconds']-60,
    'upload': summary['uploads'],
    'not_measured':['current WSGI entry/exit per PID','pre-WSGI delay','D under this load','W under this load','application or PostgreSQL CPU','resource contention','independent access-log correlation: original log removed with owned pytest temporary files'],
    'decision':'No automatic repeat, resource increase or 900s. Current VPS gate fails; laptop PASS preserved in its distinct environment. Resource contention and service-vs-pre-WSGI decomposition remain unresolved.',
}
assert result['final_success'] == 1200 and errors == 0
assert result['family_populations'] == {'listing':400,'search':400,'detail':400}
assert result['pending_at_window'] == summary['window_close']['dynamic']['pending']
assert abs(result['http_latency_seconds']['p95'] - summary['observable_latency_seconds']['p95']) < 1e-9
assert all(result['generator_delay_ms'][k] <= limit for k,limit in [('p95',10),('p99',25),('max',100)])
assert result['drain_seconds'] <= 70 and len(summary['uploads']) == 1 and summary['uploads'][0]['status'] == 302
assert result['http_latency_seconds']['p95'] >= .8 and result['pending_at_window'] > 20
print(json.dumps(result,indent=2))
