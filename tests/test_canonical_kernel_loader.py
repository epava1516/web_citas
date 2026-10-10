"""Isolated native loading, immutable bytes, bounds and integrity failures."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "apps/safety/_canonical_native"


@pytest.fixture
def artifact(tmp_path):
    if not ARTIFACT.is_dir():
        pytest.skip("Actual native artifact required; fallback is not native evidence")
    directory = tmp_path / "apps/safety/_canonical_native"
    directory.parent.mkdir(parents=True)
    return Path(shutil.copytree(ARTIFACT, directory))


def child(directory, code):
    program = (
        "import sys,json,os,errno,fcntl,threading\n"
        "from pathlib import Path\n"
        "from apps.safety import canonical_kernel_loader as loader\n"
        "loader._directory=Path(sys.argv[1])\n" + code
    )
    result = subprocess.run([sys.executable, "-c", program, str(directory)],
                            cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def rejected(directory, *, retained_descriptor=False):
    return child(directory, "retained=" + str(int(retained_descriptor)) + "\n" + """
before=len(os.listdir('/proc/self/fd'))
try:
    loader.validated_kernel()
except loader.KernelIntegrityError:
    assert len(os.listdir('/proc/self/fd'))==before+retained
    print('rejected')
else:
    raise AssertionError('Invalid installed artifact accepted')
""")


def test_absent_build_uses_reference(tmp_path):
    assert child(tmp_path / "absent", "assert loader.validated_kernel() is None\nprint('reference')") == "reference"


def test_present_incomplete_build_fails_closed(tmp_path):
    assert rejected(tmp_path) == "rejected"


@pytest.mark.parametrize("field,value", [
    ("schema", 2), ("schema", True), ("module", "wrong.kernel"), ("python", "0.0.0"),
    ("cache_tag", "wrong"), ("extension_suffix", "../wrong.so"),
    ("machine", "wrong"), ("cython", "wrong"), ("flags", ["-ffast-math"]),
    ("source_sha256", "0" * 64), ("generated_c_sha256", "0" * 64),
    ("binary_sha256", "0" * 64), ("build_script_sha256", "0" * 64),
    ("compiler_version", ""),
])
def test_manifest_drift_is_rejected(artifact, field, value):
    path = artifact / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest[field] = value
    path.write_text(json.dumps(manifest))
    assert rejected(artifact) == "rejected"


@pytest.mark.parametrize("kind", ["manifest", "binary", "generated", "directory", "dangling"])
def test_symlinks_are_not_artifact_files(artifact, tmp_path, kind):
    if kind in ("directory", "dangling"):
        link = tmp_path / "link"
        link.symlink_to(artifact if kind == "directory" else tmp_path / "missing")
        assert rejected(link) == "rejected"
        return
    name = {"manifest": "manifest.json", "generated": "_canonical_kernel.c"}.get(kind)
    path = artifact / name if name else next(artifact.glob("*.so"))
    saved = tmp_path / "saved"
    path.rename(saved)
    path.symlink_to(saved)
    assert rejected(artifact) == "rejected"


def test_changed_binary_at_same_path_is_rejected(artifact):
    path = next(artifact.glob("*.so"))
    value = bytearray(path.read_bytes())
    value[-1] ^= 1
    path.write_bytes(value)
    assert rejected(artifact) == "rejected"


def test_matching_digest_of_non_extension_still_fails_closed(artifact):
    import hashlib

    path = next(artifact.glob("*.so"))
    path.write_bytes(b"not an ELF extension")
    manifest_path = artifact / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["binary_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    assert rejected(artifact, retained_descriptor=True) == "rejected"


def test_unknown_artifact_entry_is_rejected(artifact):
    (artifact / "extra").write_text("unexpected")
    assert rejected(artifact) == "rejected"


def test_oversized_artifact_is_rejected_before_read(artifact):
    with next(artifact.glob("*.so")).open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    assert rejected(artifact) == "rejected"


def test_invalid_manifest_json_is_rejected(artifact):
    (artifact / "manifest.json").write_text("{invalid")
    assert rejected(artifact) == "rejected"


def test_duplicate_manifest_fields_are_rejected(artifact):
    path = artifact / "manifest.json"
    content = path.read_text()
    path.write_text(content.replace('"schema": 1', '"schema": 1, "schema": 1'))
    assert rejected(artifact) == "rejected"


def test_loaded_native_identity_is_part_of_rule_version(monkeypatch):
    from apps.safety import rights_validation_seal as seals
    from apps.safety.canonical_kernel_loader import kernel_identity

    identity = kernel_identity()
    assert identity["mode"] == "native-sealed"
    original = seals.rule_version()
    changed = dict(identity, binary_sha256="0" * 64)
    with monkeypatch.context() as altered:
        altered.setattr(seals, "kernel_identity", lambda: changed)
        assert seals.rule_version() != original
    assert seals.rule_version() == original


@pytest.mark.parametrize("name", ["manifest.json", "_canonical_kernel.c", "binary"])
def test_fifo_is_rejected_without_blocking(artifact, name):
    import os

    path = next(artifact.glob("*.so")) if name == "binary" else artifact / name
    path.unlink()
    os.mkfifo(path)
    assert rejected(artifact) == "rejected"
    assert child(artifact, """
try: loader.artifact_fingerprints(loader._directory.parents[2])
except ValueError: print('rejected')
else: raise AssertionError('FIFO accepted')
""") == "rejected"


def test_preexisting_unverified_module_is_rejected(artifact):
    assert child(artifact, """
import types
sys.modules[loader.MODULE]=types.ModuleType(loader.MODULE)
try: loader.validated_kernel()
except loader.KernelIntegrityError: print('rejected')
else: raise AssertionError('Raw module accepted')
""") == "rejected"


def test_concurrent_load_is_single_and_sealed(artifact):
    assert child(artifact, """
before=len(os.listdir('/proc/self/fd'))
kernels=[]
threads=[threading.Thread(target=lambda:kernels.append(loader.validated_kernel())) for _ in range(8)]
for thread in threads: thread.start()
for thread in threads: thread.join()
assert len(kernels)==8 and all(k is kernels[0] for k in kernels)
assert len(os.listdir('/proc/self/fd'))==before+1
fd=loader._state[4]
assert fcntl.fcntl(fd,loader.GET_SEALS)==loader.REQUIRED_SEALS
assert not os.get_inheritable(fd)
for operation in [lambda:os.write(fd,b'x'),lambda:os.ftruncate(fd,0)]:
    try: operation()
    except OSError as error: assert error.errno==errno.EPERM
    else: raise AssertionError('Sealed bytes mutated')
kernels[0]({'fresh':[1,True,None]},0)
assert kernels[0].try_check({'fresh':[1,True,None]},0) is True
assert kernels[0].try_check(object(),0) is False
identity=loader.kernel_identity();identity['mode']='wrong'
assert loader.kernel_identity()['mode']=='native-sealed'
print('sealed')
""") == "sealed"


def test_loaded_bytes_survive_disk_replacement_and_freeze_detects_it(artifact):
    assert child(artifact, """
import hashlib
kernel=loader.validated_kernel();identity=loader.kernel_identity()
freeze_before=loader.artifact_fingerprints(loader._directory.parents[2])
path=next(loader._directory.glob('*.so'))
old=path.read_bytes();changed=bytearray(old);changed[-1]^=1;path.write_bytes(changed)
kernel({'x':[1,2]},0)
assert loader.kernel_identity()==identity
os.lseek(loader._state[4],0,os.SEEK_SET)
assert hashlib.sha256(os.read(loader._state[4],len(old))).hexdigest()==identity['binary_sha256']
assert hashlib.sha256(path.read_bytes()).hexdigest()!=identity['binary_sha256']
assert loader.artifact_fingerprints(loader._directory.parents[2])!=freeze_before
print('immutable')
""") == "immutable"


def test_loaded_callable_replacement_is_rejected(artifact):
    assert child(artifact, """
loader.validated_kernel();loader._state[1].check=lambda *args:None
try: loader.validated_kernel()
except loader.KernelIntegrityError: print('rejected')
else: raise AssertionError('Changed callable accepted')
""") == "rejected"


def test_loaded_fast_path_replacement_is_rejected(artifact):
    assert child(artifact, """
loader.validated_kernel();loader._state[0].try_check=lambda *args:True
try: loader.validated_kernel()
except loader.KernelIntegrityError: print('rejected')
else: raise AssertionError('Changed fast path accepted')
""") == "rejected"


def test_failed_initialization_never_retries_or_reuses_an_old_mapping(artifact):
    assert child(artifact, """
import hashlib
from importlib.machinery import ExtensionFileLoader
original=ExtensionFileLoader.exec_module
def failed(self,module):
    original(self,module)
    raise RuntimeError('synthetic post-load failure')
ExtensionFileLoader.exec_module=failed
try: loader.validated_kernel()
except loader.KernelIntegrityError: pass
else: raise AssertionError('Initialization fault accepted')
ExtensionFileLoader.exec_module=original
descriptor=loader._failed_descriptor
assert descriptor is not None
before=len(os.listdir('/proc/self/fd'))
binary=next(loader._directory.glob('*.so'))
changed=bytearray(binary.read_bytes());changed[-1]^=1;binary.write_bytes(changed)
path=loader._directory/'manifest.json';manifest=json.loads(path.read_text())
manifest['binary_sha256']=hashlib.sha256(changed).hexdigest();path.write_text(json.dumps(manifest))
for attempt in range(3):
    try: loader.validated_kernel()
    except loader.KernelIntegrityError: pass
    else: raise AssertionError('Failed native initialization retried')
assert len(os.listdir('/proc/self/fd'))==before
assert loader._failed_descriptor==descriptor
assert loader.MODULE not in sys.modules
assert fcntl.fcntl(descriptor,loader.GET_SEALS)==loader.REQUIRED_SEALS
print('failure-sticky')
""") == "failure-sticky"


def test_fork_preserves_verified_binary_and_reinitializes_lock(artifact):
    assert child(artifact, """
kernel=loader.validated_kernel();identity=loader.kernel_identity()
pid=os.fork()
if pid==0:
    try:
        loader.validated_kernel()({'child':True},0)
        assert loader.kernel_identity()==identity
    except BaseException: os._exit(1)
    os._exit(0)
assert os.waitpid(pid,0)[1]==0
assert loader.validated_kernel() is kernel
print('forked')
""") == "forked"


def test_fork_waits_for_initial_load_in_another_thread(artifact):
    assert child(artifact, """
from importlib.machinery import ExtensionFileLoader
entered=threading.Event();release=threading.Event()
original=ExtensionFileLoader.exec_module
def delayed(self,module):
    entered.set();assert release.wait(5);return original(self,module)
ExtensionFileLoader.exec_module=delayed
thread=threading.Thread(target=loader.validated_kernel);thread.start()
assert entered.wait(5)
timer=threading.Timer(.05,release.set);timer.start()
pid=os.fork()
if pid==0:
    try: loader.validated_kernel()({'child':True},0)
    except BaseException: os._exit(1)
    os._exit(0)
thread.join();timer.join();assert os.waitpid(pid,0)[1]==0
assert loader.kernel_identity()['mode']=='native-sealed'
print('forked')
""") == "forked"
