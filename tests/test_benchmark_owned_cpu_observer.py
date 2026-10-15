"""Pure counter/ownership controls, not resource or capacity evidence."""
from copy import deepcopy

import pytest

from scripts.benchmark_owned_cpu_observer import cpu_counters, cpu_delta, owned_pg_pid, read_group


def fixture():
    run = {"id": "20261015-120000-deadbeef", "containers": ["web-modelos-ci-pg-20261015-120000-deadbeef"]}
    info = {"Name": "/" + run["containers"][0],
            "Config": {"Labels": {"web-modelos-local-ci-run": run["id"]}},
            "State": {"Pid": 123, "Running": True}}
    return run, info


@pytest.mark.parametrize("change", ["normal_name", "foreign_label", "stopped", "bad_pid", "bad_run"])
def test_rejects_unowned_or_nonlive_postgres(change):
    run, info = fixture()
    assert owned_pg_pid(run, info) == 123
    info = deepcopy(info)
    if change == "normal_name":
        info["Name"] = "/web-modelos-db-1"
    elif change == "foreign_label":
        info["Config"]["Labels"]["web-modelos-local-ci-run"] = "other"
    elif change == "stopped":
        info["State"]["Running"] = False
    elif change == "bad_pid":
        info["State"]["Pid"] = True
    else:
        run["id"] = "../other"
    with pytest.raises(ValueError):
        owned_pg_pid(run, info)


def test_cpu_delta_uses_elapsed_and_cumulative_counters_without_counting_wait_as_cpu():
    before = {"monotonic": 10, "cpu_stat": cpu_counters("usage_usec 100\nnr_throttled 2\nthrottled_usec 900\n")}
    after = {"monotonic": 12, "cpu_stat": cpu_counters("usage_usec 1000100\nnr_throttled 4\nthrottled_usec 4000900\n")}
    result = cpu_delta(before, after)
    assert result["execution_cpu_cores"] == 0.5
    assert result["counter_delta"]["throttled_usec"] == 4000000
    with pytest.raises(ValueError):
        cpu_delta(after, before)
    with pytest.raises(ValueError):
        cpu_delta(before, before)
    with pytest.raises(ValueError):
        cpu_counters("usage_usec 1\nusage_usec 2")


def test_missing_optional_controller_interfaces_stay_explicit(tmp_path):
    (tmp_path / "cpu.stat").write_text("usage_usec 100\nuser_usec 80\nsystem_usec 20\n")
    snapshot = read_group(tmp_path)
    assert snapshot["cpu_stat"]["usage_usec"] == 100
    assert snapshot["cpu.max"] == "not_exposed"
    assert snapshot["cpuset.cpus.effective"] == "not_exposed"
    assert snapshot["memory.events"] == "not_exposed"
    (tmp_path / "cpu.stat").unlink()
    with pytest.raises(FileNotFoundError):
        read_group(tmp_path)
