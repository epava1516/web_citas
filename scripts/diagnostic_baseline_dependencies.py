"""Deterministic runtime/dependency identity without installation paths or URLs."""
import hashlib
import importlib.metadata
import json
import platform
import re
import sys


def fingerprint(root, *, distributions=None, runtime=None):
    files = {}
    for name in ('uv.lock', 'pyproject.toml'):
        path = root / name
        if not path.is_file():
            raise ValueError('Diagnostic dependency manifest missing: ' + name)
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    installed = {}
    for distribution in (importlib.metadata.distributions() if distributions is None else distributions):
        name = distribution.metadata.get('Name')
        version = distribution.version
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name):
            raise ValueError('Diagnostic distribution name metadata missing or invalid')
        if not isinstance(version, str) or not version.strip():
            raise ValueError('Diagnostic distribution version metadata missing')
        normalized = re.sub(r'[-_.]+', '-', name).lower()
        if normalized in installed and installed[normalized] != version:
            raise ValueError('Diagnostic distribution version metadata ambiguous')
        installed[normalized] = version
    if not installed:
        raise ValueError('Diagnostic installed distribution metadata missing')
    if runtime is None:
        runtime = (platform.python_implementation(), platform.python_version(), sys.implementation.cache_tag)
    if len(runtime) != 3 or any(not isinstance(value, str) or not value for value in runtime):
        raise ValueError('Diagnostic Python runtime metadata missing')
    identity = {'files': files, 'installed': sorted(installed.items()), 'python': list(runtime)}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
