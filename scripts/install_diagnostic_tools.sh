#!/usr/bin/env bash
# Isolated tools; no sudo, application dependency changes or host tuning.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
diagnostic_venv="${WEB_CITAS_DIAGNOSTICS_VENV:-${XDG_DATA_HOME:-$HOME/.local/share}/web-citas-diagnostics/venv}"
command -v uv >/dev/null || { echo 'Falta uv; consulta docs/mod08-vps-medicion.md' >&2; exit 1; }
if [[ "$(realpath -m -- "$diagnostic_venv")" == "$(realpath -m -- "$task_root/.venv")" ]]; then
    echo 'El venv de diagnóstico debe estar separado del venv de aplicación.' >&2
    exit 1
fi
if [[ ! -x "$diagnostic_venv/bin/python" ]]; then
    uv venv --python 3.12 "$diagnostic_venv"
fi
"$diagnostic_venv/bin/python" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Se requiere Python 3.12"'
uv pip sync --python "$diagnostic_venv/bin/python" --require-hashes --only-binary=:all: \
    "$task_root/scripts/diagnostics/requirements.lock"
"$diagnostic_venv/bin/python" - "$task_root/scripts/diagnostics/requirements.lock" <<'PY'
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

prefix = Path(sys.prefix)
lock = Path(sys.argv[1])
data = {
    'python': platform.python_version(), 'machine': platform.machine(),
    'requirements_sha256': hashlib.sha256(lock.read_bytes()).hexdigest(),
    'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
    'py_spy_sha256': hashlib.sha256((prefix / 'bin/py-spy').read_bytes()).hexdigest(),
}
(prefix / 'installation.json').write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps({k: data['packages'][k] for k in ('py-spy', 'memray', 'scalene', 'pyperf')}))
PY
"$diagnostic_venv/bin/py-spy" --version
"$diagnostic_venv/bin/python" -m memray --version
"$diagnostic_venv/bin/python" -m pyperf --help >/dev/null
echo "Instrumentos listos en $diagnostic_venv; ninguno queda ejecutándose."
