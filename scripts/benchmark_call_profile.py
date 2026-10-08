"""Non-wrapping synchronous Python call observer, exclusive to observed children."""
import sys
import time
from collections import Counter


class CallProfile:
    def __init__(self, targets):
        self.targets = {}
        for function in targets:
            function = getattr(function, '__func__', function)
            name = function.__module__ + '.' + function.__qualname__
            existing = self.targets.get(function.__code__)
            if existing is not None and existing != name:
                raise ValueError(
                    'Ambiguous profile code shared by ' + existing + ' and ' + name
                )
            self.targets[function.__code__] = name
        self.stack = []
        self.rules = {}
        self.projection_stats = []
        self.materialized = Counter()
        self.provenance = Counter()

    def event(self, frame, event, arg):
        name = self.targets.get(frame.f_code)
        if name is None:
            return
        if event == 'call':
            self.stack.append({'frame': frame, 'name': name, 'wall': time.perf_counter(),
                               'cpu': time.thread_time(), 'children': Counter(), 'cpu_children': Counter()})
        elif event == 'return' and self.stack and self.stack[-1]['frame'] is frame:
            current = self.stack.pop()
            wall = time.perf_counter() - current['wall']
            cpu = time.thread_time() - current['cpu']
            exclusive = max(0, wall - sum(current['children'].values()))
            cpu_exclusive = max(0, cpu - sum(current['cpu_children'].values()))
            bucket = self.rules.setdefault(name, {'calls': 0, 'inclusive_time': 0., 'exclusive_time': 0.,
                'max_exclusive_time': 0., 'inclusive_thread_cpu_time': 0., 'exclusive_thread_cpu_time': 0.,
                'instrumented_children': Counter()})
            bucket['calls'] += 1
            bucket['inclusive_time'] += wall
            bucket['exclusive_time'] += exclusive
            bucket['max_exclusive_time'] = max(bucket['max_exclusive_time'], exclusive)
            bucket['inclusive_thread_cpu_time'] += cpu
            bucket['exclusive_thread_cpu_time'] += cpu_exclusive
            bucket['instrumented_children'].update(current['children'])
            if self.stack:
                self.stack[-1]['children'][name] += wall
                self.stack[-1]['cpu_children'][name] += cpu
            if (name.endswith('ProjectedPublication.page') or
                    (name.endswith('ProjectedPublication.visible_ids') and not any(
                        parent['name'].endswith('ProjectedPublication.page') for parent in self.stack))):
                self.projection_stats.append(dict(frame.f_locals['self'].stats))

    def objects(self, sender, **kwargs):
        label = sender._meta.label
        self.materialized[label] += 1
        self.provenance[(self.stack[-1]['name'] if self.stack else 'other') + ':' + label] += 1

    def __enter__(self):
        self.previous = sys.getprofile()
        if self.previous is not None:
            raise RuntimeError('Existing profiler cannot be replaced')
        sys.setprofile(self.event)
        return self

    def __exit__(self, *args):
        sys.setprofile(self.previous)

    def report(self):
        return [{'rule': name, **values,
                 'mean_exclusive_time': values['exclusive_time'] / values['calls']}
                for name, values in sorted(self.rules.items(), key=lambda item: item[1]['exclusive_time'], reverse=True)]
