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
MAX_BYTES = 256 * 1024
MAX_LINE = 160
MAX_FILES = 8
MAX_NS = 600_000_000_000
HEADER = 'X-Capacity-Listing-Sample'
ENV_HEADER = 'HTTP_X_CAPACITY_LISTING_SAMPLE'
DIRECTORY = Path('/tmp')


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


def _valid(record):
    return (type(record) is dict and set(record) == {'id', 'wall_ns', 'thread_cpu_ns', 'complete'}
            and all(type(value) is int for value in record.values())
            and 1 <= record['id'] <= MAX_ID and record['complete'] in (0, 1)
            and 0 <= record['wall_ns'] <= MAX_NS
            and 0 <= record['thread_cpu_ns'] <= MAX_NS)


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


def observe(application, environ, start_response, identifier):
    """Times consumption and close; returns and raises exactly as the domain does."""
    start = None
    response = None
    complete = 0
    try:
        start = (perf_counter_ns(), thread_time_ns())
    except BaseException:
        pass
    try:
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
            if start is not None:
                try:
                    wall, cpu = perf_counter_ns() - start[0], thread_time_ns() - start[1]
                    if 0 <= wall <= MAX_NS and 0 <= cpu <= MAX_NS:
                        write_record({'id': identifier, 'wall_ns': wall,
                                      'thread_cpu_ns': cpu, 'complete': complete})
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
        except (OSError, ValueError, TypeError):
            incomplete = True
    identifiers = [record['id'] for record in records]
    incomplete |= len(set(identifiers)) != len(identifiers)
    incomplete |= any(record['complete'] != 1 for record in records)
    return {'records': records, 'incomplete': incomplete,
            'semantics': 'WSGI consumption and close; TCP difference does not identify network time'}
