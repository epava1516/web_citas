"""VPS handoff: environment receipts around the existing owned synthetic runner."""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ['--selection-tcp', '--selection-concurrent', '--selection-gunicorn',
        '--database-heavy', '--object-delivery']


def command(mode, profiler, cpu_budget=4, professional_profile=None, tools_venv=None, sql_plan_target=None,
            app_image=None, territorial=False, service_resources=False, backlog=False, backlog_population=10, mixed_states=False, committed_mixed=False, committed_population=100, combined_filters=False, generator_diagnostic=False, combined_population=100):
    if combined_population not in (100, 1000, 10000) or (combined_population != 100 and not combined_filters):
        raise ValueError('Combined population requires combined filters and100/1000/10000')
    if generator_diagnostic and (not combined_filters or combined_population != 100 or mode != 'beta-http-functional'):
        raise ValueError('Generator diagnostic requires explicit combined-filter functional100')
    if combined_filters and (mode not in {'beta-http-functional', 'beta-http-short', 'beta-http-contractual'}
                             or mode in {'beta-http-short', 'beta-http-contractual'} and combined_population != 10000
                             or not territorial or service_resources or backlog or mixed_states or committed_mixed):
        raise ValueError('Combined filters require territorial functional or short/contractual10000 without observer or other mixtures')
    if committed_population not in (100, 1000, 10000) or (committed_population != 100 and not committed_mixed):
        raise ValueError('Committed population requires committed mixture and a supported scale')
    if committed_mixed and (mode not in {'beta-http-functional', 'beta-http-short', 'beta-http-contractual'} or not territorial or backlog or mixed_states
                            or mode in {'beta-http-short', 'beta-http-contractual'} and committed_population != 10000):
        raise ValueError('Committed mixture requires territorial functional or short/contractual10000 without backlog')
    if mixed_states and (not backlog or backlog_population not in (100, 1000, 10000)):
        raise ValueError('Mixed states require backlog with100,1000 or10000 profiles')
    if backlog_population not in (10, 100, 1000, 10000) or (backlog_population != 10 and not backlog):
        raise ValueError('Backlog population requires backlog and a supported scale')
    if backlog and (mode != 'beta-http-functional' or not territorial or not service_resources):
        raise ValueError('Backlog requires territorial functional with service resources')
    if service_resources and mode not in {'beta-http-functional', 'beta-http-short'}:
        raise ValueError('Service resources require functional or short diagnostic only')
    if territorial and (mode not in {'beta-http-functional', 'beta-http-short', 'beta-http-contractual'}
                        or mode == 'beta-http-contractual' and not (committed_mixed or combined_filters)):
        raise ValueError('Territorial mode permits functional or preregistered short; contractual requires committed or combined10000')
    if app_image is not None and not re.fullmatch(r'sha256:[0-9a-f]{64}', app_image):
        raise ValueError('Application image override requires a full immutable sha256 ID')
    if sql_plan_target is not None and (mode != 'diagnose' or professional_profile or sql_plan_target not in (64, 304)):
        raise ValueError('SQL plans require exclusive diagnose with a fixed history target')
    if professional_profile and (professional_profile not in ("memray", "scalene") or mode not in ("probe", "diagnose")):
        raise ValueError("Professional profiling requires separate probe or diagnose")
    if cpu_budget not in (4, 8):
        raise ValueError('Unsupported CPU budget')
    budget = ['--beta-http-territorial'] if territorial else []
    budget += ['--beta-http-combined-filters', '--beta-http-combined-population', str(combined_population)] if combined_filters else []
    budget += ['--beta-http-generator-diagnostic'] if generator_diagnostic else []
    budget += ['--beta-http-backlog', '--beta-http-backlog-population', str(backlog_population)] if backlog else []
    budget += ['--beta-http-mixed-states'] if mixed_states else []
    budget += ['--beta-http-committed-mixed', '--beta-http-committed-population', str(committed_population)] if committed_mixed else []
    budget += ['--beta-http-service-resources'] if service_resources else []
    budget += ['--cpu-budget', str(cpu_budget)] if cpu_budget != 4 else []
    if app_image is not None:
        budget += ['--app-image', app_image]
    if mode in {'beta-http-functional', 'beta-http-short', 'beta-http-contractual', 'beta-http-upload-calibration'}:
        if cpu_budget != 8:
            raise ValueError('Beta HTTP functional requires the authorized8CPU profile')
        flags = (['--beta-http-functional', '--beta-http-upload-calibration']
                 if mode == 'beta-http-upload-calibration' else ['--' + mode])
        return [sys.executable, str(ROOT / 'scripts/run_capacity_environment.py'),
                '--object-delivery', *flags, *budget]
    if mode == 'preflight':
        return [sys.executable, str(ROOT / 'scripts/run_capacity_environment.py'),
                '--object-delivery', '--preflight-only', *budget]
    args = [sys.executable, str(ROOT / 'scripts/run_capacity_environment.py'), *BASE, *budget]
    if mode == 'measure':
        return args + ['--delivery-complete']
    if sql_plan_target is not None:
        return args + ['--delivery-profile', '--delivery-profile-full', '--sql-plan-target', str(sql_plan_target)]
    if professional_profile:
        args += ['--delivery-profile', '--delivery-profile-full', '--professional-profile',
                 professional_profile, '--diagnostic-tools-venv', str(tools_venv)]
        return args + (['--professional-probe-only'] if mode == 'probe' else [])
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
    parser.add_argument('mode', choices=('preflight', 'probe', 'measure', 'diagnose', 'beta-http-functional', 'beta-http-short', 'beta-http-contractual', 'beta-http-upload-calibration'))
    default = Path(os.environ.get('WEB_CITAS_DIAGNOSTICS_VENV',
                   str(Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
                       / 'web-citas-diagnostics/venv')))
    parser.add_argument('--tools-venv', type=Path, default=default)
    parser.add_argument('--cpu-budget', type=int, choices=(4, 8), default=4,
                        help='Aggregate CPU ceiling; 8 is an explicit VPS comparison')
    parser.add_argument('--app-image', help='Existing local image identified by full immutable sha256 ID')
    parser.add_argument('--professional-profile', choices=('memray', 'scalene'))
    parser.add_argument('--sql-plan-target', type=int, choices=(64, 304),
                        help='Separate finite SQL plans; no profiler or acceptance measurement')
    parser.add_argument('--backlog', action='store_true', help='Native dirty-state scenario; functional only')
    parser.add_argument('--committed-mixed', action='store_true', help='Committed final mixture; territorial functional or short/contractual10000')
    parser.add_argument('--committed-population', type=int, choices=(100, 1000, 10000), default=100)
    parser.add_argument('--generator-diagnostic', action='store_true', help='Observed generator only with explicit combined functional100; never acceptance')
    parser.add_argument('--combined-population', type=int, choices=(100, 1000, 10000), default=100)
    parser.add_argument('--combined-filters', action='store_true', help='Territorial combined functional or short/contractual10000')
    parser.add_argument('--mixed-states', action='store_true', help='Mixed100/1000/10000 functional backlog only')
    parser.add_argument('--backlog-population', type=int, choices=(10, 100, 1000, 10000), default=10)
    parser.add_argument('--service-resources', action='store_true', help='Functional/short host observer; diagnostic only')
    parser.add_argument('--territorial', action='store_true', help='Two-city synthetic functional/short or committed contractual10000')
    parser.add_argument('--dry-run', action='store_true', help='Print argv; create no resources')
    args = parser.parse_args()
    profiler = args.tools_venv.resolve() / 'bin/py-spy'
    try:
        argv = command(args.mode, profiler, args.cpu_budget, args.professional_profile,
                       args.tools_venv.resolve(), args.sql_plan_target, args.app_image, args.territorial, args.service_resources, args.backlog, args.backlog_population, args.mixed_states, args.committed_mixed, args.committed_population, args.combined_filters, args.generator_diagnostic, args.combined_population)
    except ValueError as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps(argv))
        return 0
    if sys.platform != 'linux' or sys.version_info[:2] != (3, 12):
        parser.error('Requiere Linux y Python 3.12 del proyecto')
    if len(os.sched_getaffinity(0)) < args.cpu_budget:
        parser.error('El host no expone suficientes CPU para el perfil solicitado')
    if (args.mode in ('probe', 'diagnose') and not args.professional_profile
            and args.sql_plan_target is None and not profiler.is_file()):
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
                   'canonical_kernel': identity, 'professional_profile': args.professional_profile,
                   'sql_plan_target': args.sql_plan_target,
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
