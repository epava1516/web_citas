"""Finite offline private-config guards; no connection or real SQL-plan evidence."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest
from capacity_fingerprint_profile import fingerprint_profile, private_credentials, scrub


@pytest.mark.parametrize('invalid', [None, 'mode', 'size', 'topology', 'symlink'])
def test_fingerprint_private_config_guards(invalid):
    credentials = {'NAME': 'test_capacity_ci', 'HOST': 'pg', 'PORT': '5432',
                   'USER': 'capacity_runtime_synthetic', 'PASSWORD': 'synthetic-private-secret'}
    with TemporaryDirectory(prefix='capacity-runtime-guard-', dir='/tmp') as root:
        path = Path(root) / 'database.json'
        if invalid == 'topology':
            credentials['HOST'] = 'normal-service.invalid'
        path.write_text(' ' * 4097 if invalid == 'size' else json.dumps(credentials))
        path.chmod(0o644 if invalid == 'mode' else 0o600)
        if invalid == 'symlink':
            link = Path(root) / 'link.json'
            link.symlink_to(path)
            path = link
        if invalid:
            with pytest.raises((RuntimeError, OSError)):
                private_credentials(str(path))
        else:
            assert private_credentials(str(path)) == credentials
            assert os.stat(path).st_mode & 0o777 == 0o600


def test_fingerprint_diagnostic_flags_and_secret_scrubbing():
    settings = SimpleNamespace(CAPACITY_ENVIRONMENT_VERIFIED=False,
                               CAPACITY_DELIVERY_PROFILE=True, CAPACITY_DELIVERY_PROFILE_FULL=True)
    with pytest.raises(RuntimeError, match='verified full diagnostic'):
        fingerprint_profile(settings, None, None, None)
    assert scrub({'Plan': [{'text': 'synthetic-private-secret role/path', 'loops': 2}]},
                 ['synthetic-private-secret', 'role/path']) == {
                     'Plan': [{'text': '[private] [private]', 'loops': 2}]}
