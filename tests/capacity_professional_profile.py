"""Isolated, bounded per-request allocation diagnostics; never capacity evidence."""

import importlib
import json
import os
import resource
import sys
import time
from collections import Counter
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path

MAX_TRACE_BYTES = 256 * 1024 * 1024
MAX_RECORDS = 2_000_000
APP_MODULES = ('numpy', 'orjson', 'cryptography')


def instrument(tools_venv):
    """Append tools after application sites and verify imports remain identical."""
    before = {name: (version(name), importlib.import_module(name).__file__) for name in APP_MODULES}
    site = Path(tools_venv) / 'lib/python3.12/site-packages'
    if not site.is_dir():
        raise RuntimeError('Isolated diagnostic site missing')
    if str(site) not in sys.path:
        sys.path.append(str(site))
    module = importlib.import_module('memray')
    if module.__version__ != '1.20.0' or not Path(module.__file__).resolve().is_relative_to(site.resolve()):
        raise RuntimeError('Memray frozen version or isolated provenance differs')
    after = {name: (version(name), importlib.import_module(name).__file__) for name in APP_MODULES}
    if before != after or any(Path(path).resolve().is_relative_to(site.resolve()) for _, path in after.values()):
        raise RuntimeError('Instrument displaced frozen application imports')
    return module, {'memray': module.__version__, 'application_imports': after,
                    'python_version': sys.version.split()[0], 'python_executable': sys.executable}


def summarize(reader):
    grouped = Counter()
    count = 0
    for record in reader.get_high_watermark_allocation_records(merge_threads=True):
        count += 1
        if count > MAX_RECORDS:
            raise RuntimeError('Allocation summary exceeded bounded record count')
        stack = record.stack_trace(max_stacks=12)
        frame = next((item for item in stack if '/apps/' in item[1]), stack[0] if stack else ('native', '', 0))
        grouped[tuple(frame)] += record.size
    churn = Counter()
    total_bytes = positive_records = scanned = 0
    # Frozen Memray AllocatorType: PYMALLOC_FREE=1, FREE=5, MUNMAP=15.
    for record in reader.get_allocation_records():
        scanned += 1
        if scanned > MAX_RECORDS:
            raise RuntimeError('Allocation churn summary exceeded bounded record count')
        if record.allocator in (1, 5, 15) or record.size <= 0:
            continue
        positive_records += 1
        total_bytes += record.size
        stack = record.stack_trace(max_stacks=12)
        frame = next((item for item in stack if '/apps/' in item[1]), stack[0] if stack else ('native', '', 0))
        churn[tuple(frame)] += record.size
    metadata = reader.metadata
    return {'total_positive_allocation_bytes': total_bytes, 'positive_allocation_records': positive_records,
            'allocation_records_scanned': scanned,
            'allocation_churn_top_frames': [{'function': k[0], 'file': k[1], 'line': k[2], 'bytes': v}
                                            for k, v in churn.most_common(30)],
            'peak_memory_bytes': metadata.peak_memory, 'total_allocations': metadata.total_allocations,
            'native_traces': metadata.has_native_traces, 'python_allocators': metadata.trace_python_allocators,
            'high_watermark_top_frames': [{'function': k[0], 'file': k[1], 'line': k[2], 'bytes': v}
                                          for k, v in grouped.most_common(30)],
            'summary_scope': 'Positive allocation/reallocation requested bytes (churn, not net/live or CPU cost); high-watermark outstanding bytes separately.'}


@contextmanager
def capture(stage):
    from django.conf import settings
    from django.db import connection

    if (settings.CAPACITY_PROFESSIONAL_PROFILE != 'memray'
            or getattr(settings, 'CAPACITY_NATIVE_PROFILE', False)
            or connection.settings_dict['HOST'] != 'pg'
            or connection.settings_dict['NAME'] != 'test_capacity_ci'):
        raise RuntimeError('Professional capture outside exclusive own synthetic topology')
    if stage not in ('coverage_page_read', 'instrument_probe', 'instrument_http_probe'):
        yield
        Path(f'/tmp/capacity-profile-{stage}-{os.getpid()}.txt').write_text(
            'Professional diagnostic: this stage was not profiled; captures limited to early/late coverage.\n')
        return
    module, provenance = instrument(settings.CAPACITY_DIAGNOSTIC_TOOLS_VENV)
    stem = Path(f'/tmp/capacity-professional-{stage}-{os.getpid()}-{time.monotonic_ns()}')
    trace = stem.with_suffix('.bin')
    report = {'schema': 'capacity-professional-v1', 'stage': stage, 'pid': os.getpid(),
              'instrument': provenance, 'errors': [], 'acceptance_eligible': False,
              'cpu_scope': 'Whole current worker process CPU across marked request plus Tracker startup/flush, including its threads; intrusive, not a CPU attribution profiler.',
              'trace_max_bytes': MAX_TRACE_BYTES}
    report['status'] = 'CAPTURE_STARTED'
    stem.with_suffix('.json').write_text(json.dumps(report, sort_keys=True))
    previous_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
    bounded_soft = MAX_TRACE_BYTES if previous_limit[0] == resource.RLIM_INFINITY else min(MAX_TRACE_BYTES, previous_limit[0])
    resource.setrlimit(resource.RLIMIT_FSIZE, (bounded_soft, previous_limit[1]))
    wall, cpu = time.monotonic_ns(), time.process_time_ns()
    try:
        with module.Tracker(str(trace), native_traces=True, trace_python_allocators=True):
            yield
        report['capture_wall_including_tracker_ns'] = time.monotonic_ns() - wall
        report['capture_process_cpu_including_tracker_ns'] = time.process_time_ns() - cpu
        report['trace_bytes'] = trace.stat().st_size
        if report['trace_bytes'] > MAX_TRACE_BYTES:
            raise RuntimeError('Memray trace exceeded diagnostic bound')
        report.update(summarize(module.FileReader(str(trace))))
        report['status'] = 'COMPLETE'
        trace.unlink()  # Successful bounded summary keeps traces from accumulating across stages.
    except BaseException as error:
        report['status'] = 'FAIL'
        report['errors'].append(type(error).__name__)
        report['trace_retained_on_failure'] = trace.exists()
        raise
    finally:
        resource.setrlimit(resource.RLIMIT_FSIZE, previous_limit)
        stem.with_suffix('.json').write_text(json.dumps(report, sort_keys=True))
        Path(f'/tmp/capacity-profile-{stage}-{os.getpid()}.txt').write_text(
            'Professional Memray diagnostic only; no cProfile, py-spy, SQL timing, phase spans or request timing.\n'
            'Structured bounded summary: ' + stem.with_suffix('.json').name + '\n')
