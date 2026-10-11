"""Load an optional canonical validator from verified, sealed Linux bytes.

No compilation or downloads occur in application processes. An absent build uses
the Python reference. A present but invalid build fails closed.
"""

import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import platform
import stat
import sys
import sysconfig
import threading
from pathlib import Path

from scripts.canonical_artifacts import (
    BUILD_FLAGS,
    CYTHON_VERSION,
    MODULE,
    artifact_fingerprints,  # noqa: F401
)

MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
# Linux UAPI values. Some standalone CPython builds omit these names despite
# running on Linux; libc exposes memfd_create on the same deployed platform.
ADD_SEALS = getattr(fcntl, "F_ADD_SEALS", 1033)
GET_SEALS = getattr(fcntl, "F_GET_SEALS", 1034)
REQUIRED_SEALS = 0x0001 | 0x0002 | 0x0004 | 0x0008
_root = Path(__file__).resolve().parents[2]
_directory = Path(__file__).resolve().parent / "_canonical_native"
_lock = threading.RLock()
_state = None
_failure_message = None
_failed_descriptor = None


class KernelIntegrityError(RuntimeError):
    """An installed native validator cannot be trusted."""


def _read(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise KernelIntegrityError("Invalid canonical artifact file")
        chunks = []
        size = 0
        while chunk := os.read(descriptor, min(65536, limit + 1 - size)):
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise KernelIntegrityError("Canonical artifact exceeds bound")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise KernelIntegrityError("Duplicate canonical manifest field")
        value[key] = item
    return value


def _memfd():
    if hasattr(os, "memfd_create"):
        return os.memfd_create("rights-canonical", 0x0001 | 0x0002)
    import ctypes

    create = ctypes.CDLL(None, use_errno=True).memfd_create
    create.argtypes = (ctypes.c_char_p, ctypes.c_uint)
    create.restype = ctypes.c_int
    descriptor = create(b"rights-canonical", 0x0001 | 0x0002)
    if descriptor < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    return descriptor


def _load():
    global _failed_descriptor
    if MODULE in sys.modules:
        raise KernelIntegrityError("Unverified canonical module already loaded")
    if _directory.is_symlink():
        raise KernelIntegrityError("Invalid canonical artifact directory")
    if not _directory.exists():
        return (None, None, None, {"mode": "python-reference"}, None, None)
    if _directory.is_symlink() or not _directory.is_dir():
        raise KernelIntegrityError("Invalid canonical artifact directory")
    if sys.implementation.name != "cpython" or sys.platform != "linux":
        return (None, None, None, {"mode": "python-reference-unsupported"}, None, None)
    descriptor = None
    load_attempted = False
    try:
        manifest_bytes = _read(_directory / "manifest.json", 65536)
        manifest = json.loads(manifest_bytes, object_pairs_hook=_unique_object)
        suffix = sysconfig.get_config_var("EXT_SUFFIX")
        expected = {
            "schema": 1, "module": MODULE,
            "python": platform.python_version(),
            "cache_tag": sys.implementation.cache_tag,
            "extension_suffix": suffix, "machine": platform.machine(),
            "cython": CYTHON_VERSION, "flags": BUILD_FLAGS,
        }
        keys = set(expected) | {
            "source_sha256", "generated_c_sha256", "binary_sha256",
            "build_script_sha256", "compiler_version",
        }
        if type(manifest) is not dict or set(manifest) != keys:
            raise KernelIntegrityError("Invalid canonical manifest schema")
        if any(type(manifest.get(key)) is not type(value) or manifest.get(key) != value
               for key, value in expected.items()):
            raise KernelIntegrityError("Canonical manifest ABI/build mismatch")
        if type(manifest["compiler_version"]) is not str or not manifest["compiler_version"]:
            raise KernelIntegrityError("Missing canonical compiler identity")
        components = {
            "source_sha256": _read(_root / "apps/safety/_canonical_kernel.pyx", 65536),
            "generated_c_sha256": _read(_directory / "_canonical_kernel.c", MAX_ARTIFACT_BYTES),
            "build_script_sha256": _read(_root / "scripts/build_canonical_kernel.py", 65536),
            "binary_sha256": _read(_directory / ("_canonical_kernel" + suffix), MAX_ARTIFACT_BYTES),
        }
        if any(type(manifest[key]) is not str or _sha(data) != manifest[key]
               for key, data in components.items()):
            raise KernelIntegrityError("Canonical artifact digest mismatch")
        expected_names = {"manifest.json", "_canonical_kernel.c", "_canonical_kernel" + suffix}
        entries = set()
        for path in _directory.iterdir():
            entries.add(path.name)
            if len(entries) > 3:
                raise KernelIntegrityError("Unexpected canonical artifact entry")
        if entries != expected_names:
            raise KernelIntegrityError("Unexpected canonical artifact entry")
        descriptor = _memfd()
        binary = components["binary_sha256"]
        view = memoryview(binary)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise KernelIntegrityError("Cannot stage canonical artifact")
            view = view[written:]
        fcntl.fcntl(descriptor, ADD_SEALS, REQUIRED_SEALS)
        if fcntl.fcntl(descriptor, GET_SEALS) != REQUIRED_SEALS:
            raise KernelIntegrityError("Canonical artifact was not sealed")
        origin = f"/proc/self/fd/{descriptor}"
        loader = importlib.machinery.ExtensionFileLoader(MODULE, origin)
        spec = importlib.util.spec_from_file_location(MODULE, origin, loader=loader)
        load_attempted = True
        module = importlib.util.module_from_spec(spec)
        sys.modules[MODULE] = module
        loader.exec_module(module)
        check = getattr(module, "check", None)
        try_check = getattr(module, "try_check", None)
        if (module.__name__ != MODULE or module.__package__ != "apps.safety"
                or module.__file__ != origin or not callable(check)
                or not callable(try_check) or getattr(check, "try_check", None) is not try_check):
            raise KernelIntegrityError("Invalid loaded canonical module")
        identity = {"mode": "native-sealed", "manifest_sha256": _sha(manifest_bytes), **manifest}
        # The descriptor must remain open: dlopen can reuse a pathname, and the
        # immutable mapping must have a stable process-lifetime origin.
        return (check, module, origin, identity, descriptor, try_check)
    except Exception as error:
        sys.modules.pop(MODULE, None)
        if descriptor is not None:
            if load_attempted:
                # CPython/dlopen may retain a mapping even after initialization
                # failed. Reserve its pathname until process exit, including on
                # failure, so a new memfd cannot silently reuse an old mapping.
                _failed_descriptor = descriptor
            else:
                os.close(descriptor)
        if isinstance(error, KernelIntegrityError):
            raise
        raise KernelIntegrityError("Cannot verify/load canonical artifact") from error


def _validated_state():
    global _state, _failure_message
    if _state is None:
        with _lock:
            if _failure_message is not None:
                raise KernelIntegrityError(_failure_message)
            if _state is None:
                try:
                    _state = _load()
                except KernelIntegrityError as error:
                    # Never retry a failed native initialization in this process.
                    # Store only text, not a traceback retaining artifact buffers.
                    _failure_message = str(error)
                    raise
    check, module, origin, identity, descriptor, try_check = _state
    if module is not None and (
        sys.modules.get(MODULE) is not module or getattr(module, "check", None) is not check
        or getattr(module, "__file__", None) != origin
        or getattr(module, "__name__", None) != MODULE
        or getattr(module, "__package__", None) != "apps.safety"
        or getattr(module, "try_check", None) is not try_check
        or getattr(check, "try_check", None) is not try_check
    ):
        raise KernelIntegrityError("Loaded canonical validator changed")
    return _state


def validated_kernel():
    return _validated_state()[0]


def kernel_identity():
    # Return an independent copy; callers cannot alter the verified identity.
    return json.loads(json.dumps(_validated_state()[3], sort_keys=True))


def _after_fork():
    global _lock
    _lock = threading.RLock()


def _before_fork():
    _lock.acquire()


def _after_fork_parent():
    _lock.release()


os.register_at_fork(before=_before_fork, after_in_parent=_after_fork_parent,
                    after_in_child=_after_fork)
