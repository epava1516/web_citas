"""Constant-size request timing diagnostics, independent of application state."""
import fcntl
import json
import os
import re
import stat
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

MAX_ID = 2048
MAX_RECORDS = 2048
MAX_BYTES = 8 * 1024 * 1024
MAX_LINE = 16 * 1024
MAX_FILES = 8
MAX_NS = 600_000_000_000
HEADER = 'X-Capacity-Listing-Sample'
ENV_HEADER = 'HTTP_X_CAPACITY_LISTING_SAMPLE'
DIRECTORY = Path('/tmp')
PHASE_NAMES = (
    'batch', 'page', 'record', 'baseline', 'unseal', 'source', 'compile',
    'authorize', 'validate_selection', 'validate_assessment', 'assessment_evidence',
    'selection_evidence', 'audited_images', 'checked_images', 'read_image_blob',
    'content_digest', 'batch_projection', 'canonical_bytes', 'fingerprint',
)
COUNTER_NAMES = ('calls', 'wall_ns', 'thread_cpu_ns', 'exclusive_wall_ns',
                 'exclusive_thread_cpu_ns', 'sql_count', 'sql_wall_ns', 'sql_thread_cpu_ns')
SCHEMA = 2
STATUS_CODES = {'inactive': 0, 'active': 1, 'complete': 2, 'incomplete': 3, 'declined': 4}


def compact(snapshot):
    """Fixed numeric schema only; no diagnostic free text is serialized."""
    def matrix(phases):
        return [[phases[name][counter] for counter in COUNTER_NAMES] for name in PHASE_NAMES]
    return {'v': SCHEMA, 'sql': [snapshot['sql_count'], snapshot['sql_totals']['wall_ns'],
                                snapshot['sql_totals']['thread_cpu_ns']], 'phase_status': STATUS_CODES[snapshot['status']], 'phases': matrix(snapshot['phases']),
            'pages': [matrix(page) for page in snapshot['pages']],
            'phase_complete': int(snapshot['status'] == 'complete' and not snapshot['incomplete']
                                  and not snapshot['missing_phases'] and not snapshot['omitted_phases']),
            'phase_missing': sum(1 << index for index, name in enumerate(PHASE_NAMES)
                                 if name in snapshot['missing_phases']),
            'phase_omitted': sum(1 << index for index, name in enumerate(PHASE_NAMES)
                                 if name in snapshot['omitted_phases'])}



def sample_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]{0,3}', value):
        return None
    number = int(value)
    return number if number <= MAX_ID else None


def _open(path):
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        os.close(descriptor)
        raise OSError('Invalid diagnostic file')
    return descriptor


def _matrix_valid(matrix):
    if type(matrix) is not list or len(matrix) != len(PHASE_NAMES):
        return False
    for row in matrix:
        if type(row) is not list or len(row) != len(COUNTER_NAMES):
            return False
        if any(type(value) is not int or not 0 <= value <= MAX_NS for value in row):
            return False
        if row[0] > 100_000 or row[5] > 100_000 or row[3] > row[1] or row[4] > row[2]:
            return False
    return True


def _valid(record):
    basic = {'id', 'wall_ns', 'thread_cpu_ns', 'complete'}
    extra = {'v', 'sql', 'phase_status', 'phases', 'pages', 'phase_complete', 'phase_missing', 'phase_omitted'}
    if type(record) is not dict or set(record) not in (basic, basic | extra):
        return False
    if (any(type(record[name]) is not int for name in basic)
            or not 1 <= record['id'] <= MAX_ID or record['complete'] not in (0, 1)
            or not 0 <= record['wall_ns'] <= MAX_NS
            or not 0 <= record['thread_cpu_ns'] <= MAX_NS):
        return False
    if set(record) == basic:  # Read prior diagnostic artifacts explicitly.
        return True
    return (type(record['v']) is int and record['v'] == SCHEMA
            and type(record['phase_status']) is int and record['phase_status'] in STATUS_CODES.values()
            and type(record['phase_complete']) is int and record['phase_complete'] in (0, 1)
            and all(type(record[name]) is int and 0 <= record[name] < 1 << len(PHASE_NAMES)
                    for name in ('phase_missing', 'phase_omitted'))
            and type(record['sql']) is list and len(record['sql']) == 3
            and all(type(value) is int and 0 <= value <= MAX_NS for value in record['sql'])
            and record['sql'][0] <= 100_000
            and (not record['phase_complete'] or (record['phase_status'] == 2
                 and record['phase_missing'] == 0 and record['phase_omitted'] == 0))
            and _matrix_valid(record['phases']) and type(record['pages']) is list
            and len(record['pages']) <= 4 and all(_matrix_valid(page) for page in record['pages']))


def write_record(record):
    """Global record/byte reservation; no waiting on a diagnostic lock.

    Failed reservations consume budget conservatively. Missing records make the
    paired diagnostic incomplete, never change domain success/failure.
    """
    budget = output = None
    try:
        if not _valid(record):
            return False
        payload = (json.dumps(record, separators=(',', ':')) + '\n').encode('ascii')
        if len(payload) > MAX_LINE:
            return False
        budget = _open(DIRECTORY / 'capacity-request-timing-budget')
        fcntl.flock(budget, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raw = os.read(budget, 64)
        count, size = map(int, raw.decode('ascii').split(',')) if raw else (0, 0)
        if not 0 <= count < MAX_RECORDS or not 0 <= size <= MAX_BYTES - len(payload):
            return False
        os.lseek(budget, 0, os.SEEK_SET)
        state = f'{count + 1},{size + len(payload)}'.encode('ascii')
        os.write(budget, state)
        os.ftruncate(budget, len(state))
        output = _open(DIRECTORY / f'capacity-request-timing-{os.getpid()}.jsonl')
        os.lseek(output, 0, os.SEEK_END)
        return os.write(output, payload) == len(payload)
    except BaseException:
        return False
    finally:
        for descriptor in (output, budget):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException:
                    pass


def observe(application, environ, start_response, identifier, *, observation=None):
    """Times consumption and close; returns and raises exactly as the domain does."""
    start = None
    response = None
    complete = 0
    manager = collector = None
    try:
        start = (perf_counter_ns(), thread_time_ns())
    except BaseException:
        pass
    try:
        if observation is not None:
            try:
                manager = observation()
                collector = manager.__enter__()
            except BaseException:
                pass  # Diagnostics cannot prevent the domain call.
        response = application(environ, start_response)
        yield from response
        complete = 1
    finally:
        try:
            if response is not None:
                response.close()
        except BaseException:
            complete = 0
            raise
        finally:
            if manager is not None:
                try:
                    import sys
                    manager.__exit__(*sys.exc_info())
                except BaseException:
                    collector = None
            if start is not None:
                try:
                    wall, cpu = perf_counter_ns() - start[0], thread_time_ns() - start[1]
                    if 0 <= wall <= MAX_NS and 0 <= cpu <= MAX_NS:
                        record = {'id': identifier, 'wall_ns': wall,
                                  'thread_cpu_ns': cpu, 'complete': complete}
                        if collector is not None:
                            record.update(compact(collector.snapshot()))
                        elif observation is not None:
                            record.update({'v': SCHEMA, 'sql': [0, 0, 0], 'phase_status': 3, 'phases': [[0] * 8 for _ in PHASE_NAMES],
                                           'pages': [], 'phase_complete': 0,
                                           'phase_missing': (1 << len(PHASE_NAMES)) - 1,
                                           'phase_omitted': 0})
                        write_record(record)
                except BaseException:
                    pass


def collect(directory=DIRECTORY):
    """Strict bounded reader; no raw malformed input is copied into evidence."""
    records = []
    incomplete = False
    total_bytes = 0
    files = sorted(directory.glob('capacity-request-timing-*.jsonl'))
    if len(files) > MAX_FILES:
        incomplete = True
    for path in files[:MAX_FILES]:
        try:
            if not re.fullmatch(r'capacity-request-timing-[1-9][0-9]{0,9}\.jsonl', path.name):
                raise ValueError
            with path.open('rb') as stream:
                while raw := stream.readline(MAX_LINE + 1):
                    total_bytes += len(raw)
                    if (len(raw) > MAX_LINE or total_bytes > MAX_BYTES
                            or len(records) >= MAX_RECORDS):
                        raise ValueError
                    item = json.loads(raw)
                    if not _valid(item):
                        raise ValueError
                    records.append(item)
        except (OSError, ValueError, TypeError, RecursionError, OverflowError):
            incomplete = True
    identifiers = [record['id'] for record in records]
    incomplete |= len(set(identifiers)) != len(identifiers)
    incomplete |= any(record['complete'] != 1 for record in records)
    record_incomplete = incomplete
    phase_incomplete = any(record.get('v') == SCHEMA and (not record['phase_complete']
                           or record['phase_missing'] or record['phase_omitted']) for record in records)
    incomplete = bool(record_incomplete or phase_incomplete)
    return {'records': records, 'incomplete': incomplete,
            'record_incomplete': bool(record_incomplete), 'phase_incomplete': bool(phase_incomplete),
            'phase_schema': SCHEMA, 'phase_names': list(PHASE_NAMES),
            'counter_names': list(COUNTER_NAMES), 'phase_status_codes': dict(STATUS_CODES),
            'phase_semantics': 'Fixed surveyed Python caller aliases only; exclusive includes SQL and unobserved work, not native-only CPU',
            'semantics': 'WSGI consumption, close and observer restoration; TCP difference does not identify network time'}
