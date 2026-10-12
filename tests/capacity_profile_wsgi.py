"""Optional diagnostic wrapper: profiles only explicitly marked extra requests."""

import cProfile
import io
import json
import os
import pstats
import re
from contextlib import nullcontext
from pathlib import Path

from capacity_phase_spans import scope as phase_scope
from capacity_request_timing import ENV_HEADER, observe, sample_id
from capacity_worker_profile import scope
from django.conf import settings

from config.wsgi import application as original


def application(environ, start_response):
    native_mode = getattr(settings, 'CAPACITY_NATIVE_PROFILE', False)
    identifier = sample_id(environ.get(ENV_HEADER))
    if identifier is not None and not environ.get('HTTP_X_CAPACITY_PROFILE') and not native_mode:
        def observation():
            from django.db import connection
            return phase_scope(sql_context=connection.execute_wrapper)
        yield from observe(original, environ, start_response, identifier, observation=observation)
        return
    stage = environ.get('HTTP_X_CAPACITY_PROFILE', '')
    stage = stage if re.fullmatch(r'[a-z_]{1,40}', stage) else ('selection' if stage == '1' else '')
    listing_phases = stage == 'coverage_page_read' and not native_mode
    native_enabled = stage and native_mode
    profile = cProfile.Profile() if stage and not listing_phases and not native_enabled else None
    response = None
    if profile:
        profile.enable()
    collector = None
    phase_collector = None
    native = nullcontext()
    if native_enabled:
        from capacity_native_profile import capture
        native = capture(stage)
    if listing_phases:
        from django.db import connection
        observation = phase_scope(sql_context=connection.execute_wrapper)
    else:
        observation = scope() if profile else nullcontext()
    try:
        with native, observation as observed:
            if listing_phases:
                phase_collector = observed
            else:
                collector = observed
            try:
                response = original(environ, start_response)
                yield from response
            finally:
                if response is not None:
                    response.close()
    finally:
        if native_enabled:
            Path(f'/tmp/capacity-profile-{stage}-{os.getpid()}.txt').write_text(
                'Native diagnostic only; cProfile and worker profile hooks disabled. '
                'Phase spans and request timing disabled. '
                'Structured results are in capacity-native-*.json.\n')
        if listing_phases:
            output = '\nCapacity listing phase diagnostic JSON:\n'
            output += json.dumps(phase_collector.snapshot(), sort_keys=True) + '\n'
            Path(f'/tmp/capacity-profile-{stage}-{os.getpid()}.txt').write_text(output)
        if profile:
            profile.disable()
            output = io.StringIO()
            pstats.Stats(profile, stream=output).sort_stats('cumulative').print_stats(45)
            pstats.Stats(profile, stream=output).sort_stats('tottime').print_stats(30)
            name = f'/tmp/capacity-profile-{os.getpid()}.txt' if stage == 'selection' else \
                f'/tmp/capacity-profile-{stage}-{os.getpid()}.txt'
            if collector is not None:
                output.write('\nCapacity worker diagnostic JSON:\n')
                output.write(json.dumps(collector.snapshot(), sort_keys=True) + '\n')
            Path(name).write_text(output.getvalue())
