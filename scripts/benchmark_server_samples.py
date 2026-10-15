"""Retain synthetic identity/status/duration only; never raw access-log paths."""

import math
import re

_ID = re.compile(r'd-[0-9]{1,6}\Z')


def parse_service_samples(lines):
    samples, errors, seen = [], [], set()
    for index, line in enumerate(lines):
        fields = line.split()
        if len(fields) != 4 or not _ID.fullmatch(fields[3]):
            continue  # Health, cold probes, uploads and unknown IDs are not dynamic.
        identity = fields[3]
        try:
            status, seconds = int(fields[0]), float(fields[1])
            if not 100 <= status <= 599 or not math.isfinite(seconds) or seconds < 0:
                raise ValueError
            if identity in seen:
                errors.append({'line': index, 'reason': 'duplicate_dynamic_id'})
                continue
        except ValueError:
            errors.append({'line': index, 'reason': 'invalid_status_or_duration'})
            continue
        seen.add(identity)
        samples.append({'id': identity, 'status': status, 'service_seconds': seconds})
    return {'samples': samples, 'parse_errors': errors,
            'scope': 'Synthetic dynamic log rows only; request service excludes admission/HTTP parsing. '
                     'No URI/SQL/headers; not exact socket queue. Retained after temporary cleanup.'}
