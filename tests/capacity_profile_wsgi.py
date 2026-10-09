"""Optional diagnostic wrapper: profiles only explicitly marked extra requests."""

import cProfile
import io
import os
import pstats
from pathlib import Path

from config.wsgi import application as original


def application(environ, start_response):
    profile = cProfile.Profile() if environ.get('HTTP_X_CAPACITY_PROFILE') == '1' else None
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
            Path(f'/tmp/capacity-profile-{os.getpid()}.txt').write_text(output.getvalue())
