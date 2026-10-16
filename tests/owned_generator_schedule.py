"""Diagnostic-only asyncio loop attribution; never a clean acceptance emitter."""
import asyncio
import threading
import time
from pathlib import Path


def snapshot():
    fields = [int(x) for x in Path(f'/proc/self/task/{threading.get_native_id()}/schedstat').read_text().split()]
    assert len(fields) == 3
    return {'wall': time.monotonic(), 'cpu': time.thread_time(),
            'runtime_ns': fields[0], 'runqueue_ns': fields[1], 'slices': fields[2]}


def difference(before, after):
    return {'start': before['wall'], 'end': after['wall'],
            'wall': after['wall']-before['wall'], 'cpu': after['cpu']-before['cpu'],
            'runtime': (after['runtime_ns']-before['runtime_ns'])/1e9,
            'runqueue_wait': (after['runqueue_ns']-before['runqueue_ns'])/1e9}


class SelectorProbe:
    def __init__(self, selector):
        self.selector = selector
        self.last = None

    def __getattr__(self, name):
        return getattr(self.selector, name)

    def select(self, timeout=None):
        before = snapshot()
        events = self.selector.select(timeout)
        self.last = difference(before, snapshot()) | {'timeout': timeout, 'events': len(events)}
        return events


class ObservedLoop(asyncio.SelectorEventLoop):
    def __init__(self):
        super().__init__()
        self._selector = SelectorProbe(self._selector)
        self.observations = []
        self.iterations = 0
        self.maxima = dict(wall=0., cpu=0., runqueue_wait=0., selector_overshoot=0.)

    def _run_once(self):
        before = snapshot()
        super()._run_once()
        observed = difference(before, snapshot())
        selector = self._selector.last
        assert selector is not None
        overshoot = max(0., selector['wall']-max(0., selector['timeout'] or 0.))
        observed.update(selector=selector, selector_overshoot=overshoot,
                        callback_wall=max(0., observed['wall']-selector['wall']),
                        callback_cpu=max(0., observed['cpu']-selector['cpu']))
        self.iterations += 1
        for name in self.maxima:
            self.maxima[name] = max(self.maxima[name], observed[name])
        if max(observed['cpu'], observed['runqueue_wait'], overshoot, observed['callback_wall']) >= .02:
            # Bounded retention; no callback repr, headers, URI, body or credentials.
            self.observations.append(observed)
            self.observations.sort(key=lambda row: max(row['cpu'], row['runqueue_wait'], row['selector_overshoot'], row['callback_wall']), reverse=True)
            del self.observations[256:]

    def report(self):
        return {'iterations': self.iterations, 'maxima': self.maxima, 'events': self.observations,
                'limits': 'Diagnostic per-thread /proc schedstat and clocks; inclusive deltas overlap. '
                          'No exact cause assigned to unmatched off-CPU wall time. '
                          'Selector requested timeout is an upper bound before I/O readiness. '
                          'Observer overhead not causally measured; not clean acceptance timing.'}
