"""Bounded, atomic phase signal shared through the owned app's private /tmp.

The host must verify the app container identity before and after reading through
its init PID root. This codec alone does not establish container ownership.
"""

import json
import math
import os
import re
import time
from pathlib import Path

PHASE_PATH = Path('/tmp/capacity-beta-resource-phase.json')
PHASES = ('before_arrivals', 'arrivals_and_drain', 'idle_after')
MAX_BYTES = 2048


def validate_phase(payload, run_id):
    if not re.fullmatch(r'\d{8}-\d{6}-[a-f0-9]{8}', run_id):
        raise ValueError('Exact capacity run required')
    if set(payload) != {'run', 'events'} or payload['run'] != run_id:
        raise ValueError('Phase signal run mismatch')
    events = payload['events']
    if not isinstance(events, list) or not 1 <= len(events) <= len(PHASES):
        raise ValueError('Bounded phase history required')
    previous = -1
    for index, event in enumerate(events):
        if (not isinstance(event, dict) or set(event) != {'phase', 'monotonic'}
                or event['phase'] != PHASES[index]
                or type(event['monotonic']) not in (float, int)
                or not math.isfinite(event['monotonic'])
                or event['monotonic'] < 0 or event['monotonic'] <= previous):
            raise ValueError('Ordered finite phase boundaries required')
        previous = event['monotonic']
    return payload


def decode_phase(data, run_id):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        raise ValueError('Bounded phase bytes required')
    return validate_phase(json.loads(data), run_id)


class CapacityPhaseWriter:
    def __init__(self, run_id):
        self.payload = {'run': run_id, 'events': []}
        self.path = PHASE_PATH
        if self.path.exists() or self.path.is_symlink():
            raise ValueError('Fresh private phase signal required')
        self.advance('before_arrivals')

    def advance(self, phase):
        events = self.payload['events'] + [{'phase': phase, 'monotonic': time.monotonic()}]
        payload = validate_phase({'run': self.payload['run'], 'events': events}, self.payload['run'])
        data = json.dumps(payload, allow_nan=False).encode()
        if len(data) > MAX_BYTES:
            raise ValueError('Phase signal exceeds bound')
        temporary = self.path.with_suffix('.tmp')
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
                stream.flush()
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
        self.payload = payload
        return payload
