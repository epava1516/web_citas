"""Explicit isolated build; never invoked by application imports."""

import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

if __package__:
    from .canonical_artifacts import BUILD_FLAGS, CYTHON_VERSION, MODULE
else:
    from canonical_artifacts import BUILD_FLAGS, CYTHON_VERSION, MODULE

FLAGS = BUILD_FLAGS


def build():
    import Cython

    if Cython.__version__ != CYTHON_VERSION:
        raise RuntimeError("Build requires pinned Cython " + CYTHON_VERSION)
    if sys.implementation.name != "cpython" or sys.platform != "linux":
        raise RuntimeError("Native canonical build requires CPython/Linux")
    root = Path(__file__).resolve().parents[1]
    source = root / "apps/safety/_canonical_kernel.pyx"
    destination = root / "apps/safety/_canonical_native"
    if destination.exists():
        raise RuntimeError("Refusing to replace existing canonical build")
    compiler = shlex.split(sysconfig.get_config_var("CC"))
    compiler_version = subprocess.check_output(compiler + ["--version"], text=True).splitlines()[0]
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    with tempfile.TemporaryDirectory(prefix="canonical-build-", dir=source.parent) as temporary:
        work = Path(temporary)
        generated = work / "_canonical_kernel.c"
        binary = work / ("_canonical_kernel" + suffix)
        subprocess.run([sys.executable, "-m", "cython", "-3", "--module-name", MODULE,
                        str(source), "-o", str(generated)], check=True)
        subprocess.run(compiler + FLAGS + ["-I" + sysconfig.get_path("include"),
                        str(generated), "-o", str(binary)], check=True)
        manifest = {
            "schema": 1, "module": MODULE, "python": platform.python_version(),
            "cache_tag": sys.implementation.cache_tag, "extension_suffix": suffix,
            "machine": platform.machine(), "cython": CYTHON_VERSION,
            "flags": FLAGS, "compiler_version": compiler_version,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "generated_c_sha256": hashlib.sha256(generated.read_bytes()).hexdigest(),
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "build_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }
        (work / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        os.rename(work, destination)
    print(json.dumps({"module": MODULE, "binary_sha256": manifest["binary_sha256"]}))


if __name__ == "__main__":
    build()
