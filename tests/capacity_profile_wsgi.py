"""Optional diagnostic wrapper: profiles only explicitly marked extra requests."""

import cProfile
import io
import os
import pstats
import re
from pathlib import Path

from config.wsgi import application as original


def application(environ, start_response):
    stage = environ.get('HTTP_X_CAPACITY_PROFILE', '')
    stage = stage if re.fullmatch(r'[a-z_]{1,40}', stage) else ('selection' if stage == '1' else '')
    profile = cProfile.Profile() if stage else None
    response = None
    if profile:
        profile.enable()
    try:
        response = original(environ, start_response)
        yield from response
    finally:
        if response is not None:
            response.close()
        if profile:
            profile.disable()
            output = io.StringIO()
            pstats.Stats(profile, stream=output).sort_stats('cumulative').print_stats(45)
            pstats.Stats(profile, stream=output).sort_stats('tottime').print_stats(30)
            name = f'/tmp/capacity-profile-{os.getpid()}.txt' if stage == 'selection' else \
                f'/tmp/capacity-profile-{stage}-{os.getpid()}.txt'
            Path(name).write_text(output.getvalue())
