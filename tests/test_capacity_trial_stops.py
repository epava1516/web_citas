import threading
from scripts.benchmark_async_transport import run_async_open_loop, POLICY
from scripts.benchmark_resource_probe import TrialLimits


def test_resource_stop_preserves_partial_ledger():
    stop = threading.Event()
    async def fetch(path, **kwargs):
        stop.set()
        return {'status': 200, 'unexpected': False, 'timeout': False}
    result = run_async_open_loop(fetch, ['/es/'], duration=.2, rps=20, upload_specs=[], stop_requested=stop)
    assert result['verdict'] == 'INVALID'
    assert 'trial_resource_stop' in result['invalid_reasons']
    assert result['counts']['reconciled'] and result['counts']['pending'] == 0
    assert result['counts']['emitted'] == 1 and result['counts']['not_emitted'] == 3
    assert result['policy']['request_timeout_seconds'] == 65


def test_limits_require_five_sustained_execution_samples_and_detect_new_oom():
    config = {'stop_mem_available_below_bytes': 2147483648,
              'stop_owned_trial_if_host_execution_CPU_cores_at_least': 7.6,
              'sustained_samples_for_CPU_stop': 5}
    limits = TrialLimits(config)
    def sample(second, oom=0):
        return {'monotonic': second, 'host_cpu_ticks': [800*second, 0, 0, 0, 0, 0, 0, 0],
                'meminfo': {'MemAvailable': 4*2147483648}, 'app_cgroups': {'.': {'memory.events': f'oom {oom}'}}, 'pg_cgroups': {}}
    for second in range(5):
        limits.observe(sample(second), 100)
        assert not limits.requested.is_set()
    limits.observe(sample(5), 100)
    assert limits.reason['reason'] == 'host_execution_CPU_sustained_limit'
    other = TrialLimits(config)
    other.observe(sample(0), 100)
    other.observe(sample(1, 1), 100)
    assert other.reason['reason'] == 'new_oom_event'
