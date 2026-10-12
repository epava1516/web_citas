"""VPS handoff: environment receipts around the existing owned synthetic runner."""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ['--selection-tcp', '--selection-concurrent', '--selection-gunicorn',
        '--database-heavy', '--object-delivery']


def command(mode, profiler, cpu_budget=4):
    if cpu_budget not in (4, 8):
        raise ValueError('Unsupported CPU budget')
    budget = ['--cpu-budget', str(cpu_budget)] if cpu_budget != 4 else []
    if mode == 'preflight':
        return [sys.executable, str(ROOT / 'scripts/run_capacity_environment.py'),
                '--object-delivery', '--preflight-only', *budget]
    args = [sys.executable, str(ROOT / 'scripts/run_capacity_environment.py'), *BASE, *budget]
    if mode == 'measure':
        return args + ['--delivery-complete']
    args += ['--delivery-profile', '--delivery-profile-full', '--native-profile', str(profiler)]
    return args + (['--native-probe-only'] if mode == 'probe' else [])


def snapshot():
    data = {'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'platform': platform.platform(), 'machine': platform.machine(),
            'python': platform.python_version(), 'cpu_count': os.cpu_count(),
            'affinity': sorted(os.sched_getaffinity(0)),
            'disk_free_bytes': shutil.disk_usage(ROOT).free, 'files': {}}
    # Bounded metadata only: no environment variables, SQL, credentials or process arguments.
    names = ['/proc/stat', '/proc/loadavg', '/proc/meminfo', '/proc/pressure/cpu',
             '/proc/pressure/memory', '/sys/firmware/acpi/platform_profile']
    for pattern in ('/sys/class/power_supply/*/online', '/sys/class/power_supply/*/capacity',
                    '/sys/class/power_supply/*/status',
                    '/sys/devices/system/cpu/cpufreq/policy*/energy_performance_preference'):
        names.extend(str(p) for p in Path('/').glob(pattern.lstrip('/')))
    for name in names:
        try:
            with Path(name).open() as stream:
                data['files'][name] = stream.read(16384)
        except OSError:
            pass
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'probe', 'measure', 'diagnose'))
    default = Path(os.environ.get('WEB_CITAS_DIAGNOSTICS_VENV',
                   str(Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
                       / 'web-citas-diagnostics/venv')))
    parser.add_argument('--tools-venv', type=Path, default=default)
    parser.add_argument('--cpu-budget', type=int, choices=(4, 8), default=4,
                        help='Aggregate CPU ceiling; 8 is an explicit VPS comparison')
    parser.add_argument('--dry-run', action='store_true', help='Print argv; create no resources')
    args = parser.parse_args()
    profiler = args.tools_venv.resolve() / 'bin/py-spy'
    argv = command(args.mode, profiler, args.cpu_budget)
    if args.dry_run:
        print(json.dumps(argv))
        return 0
    if sys.platform != 'linux' or sys.version_info[:2] != (3, 12):
        parser.error('Requiere Linux y Python 3.12 del proyecto')
    if len(os.sched_getaffinity(0)) < args.cpu_budget:
        parser.error('El host no expone suficientes CPU para el perfil solicitado')
    if args.mode in ('probe', 'diagnose') and not profiler.is_file():
        parser.error('Instala los instrumentos antes del diagnóstico')
    if not Path('/var/run/docker.sock').exists():
        parser.error('Requiere el Docker local del ejecutor existente')
    identity = json.loads(subprocess.check_output([
        sys.executable, '-c', 'import json; from apps.safety.canonical_kernel_loader '
        'import kernel_identity; print(json.dumps(kernel_identity()))'], cwd=ROOT, text=True))
    if identity.get('mode') != 'native-sealed':
        parser.error('Falta kernel canónico nativo validado; consulta el procedimiento VPS')
    receipts = ROOT / 'artifacts/vps-measurements'
    receipts.mkdir(parents=True, exist_ok=True)
    with (receipts / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Ya hay una medición VPS de este lanzador en curso')
        active = subprocess.check_output(['docker', 'ps', '--filter',
                 'label=web-modelos-capacity-run', '--format', '{{.Names}}'], text=True).strip()
        if active:
            parser.error('Otro entorno de capacidad está activo; no superponer cargas')
        folder = receipts / (time.strftime('%Y%m%d-%H%M%S', time.gmtime()) + '-' + uuid.uuid4().hex[:8])
        folder.mkdir()
        before = set((ROOT / 'artifacts/capacity-environment').glob('*'))
        receipt = {'mode': args.mode, 'argv': argv, 'start': snapshot(),
                   'cpu_budget_cores': args.cpu_budget,
                   'original_four_cpu_profile': args.cpu_budget == 4,
                   'canonical_kernel': identity,
                   'acceptance_measurement': args.mode == 'measure'}
        if profiler.is_file():
            receipt['profiler_sha256'] = hashlib.sha256(profiler.read_bytes()).hexdigest()
        def save():
            (folder / 'environment.json').write_text(json.dumps(receipt, indent=2) + '\n')
        save()
        print(f'Registro de entorno: {folder}', flush=True)
        try:
            result = subprocess.run(argv, cwd=ROOT, check=False)
            receipt['exit_code'] = result.returncode
        finally:
            receipt['end'] = snapshot()
            receipt['capacity_runs'] = sorted(p.name for p in
                set((ROOT / 'artifacts/capacity-environment').glob('*')) - before)
            save()
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
