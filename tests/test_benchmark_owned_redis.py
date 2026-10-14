"""Unit guards reject unrelated brokers before any Redis connection or cleanup."""

import json

import pytest
import redis
import test_worker_capacity_comparison as benchmark


@pytest.mark.parametrize("damage", [
    None, "run", "name", "label", "port", "host", "database", "stopped",
    "unscoped", "missing_override", "credentials", "query",
])
def test_ci_broker_identity_is_checked_before_redis_client(monkeypatch, damage):
    run = "20261014-120000-12345678"
    name = f"web-modelos-ci-redis-{run}"
    url = "redis://127.0.0.1:34567/0"
    info = {
        "State": {"Running": True},
        "Config": {"Labels": {"web-modelos-local-ci-run": run}},
        "NetworkSettings": {"Ports": {
            "6379/tcp": [{"HostIp": "127.0.0.1", "HostPort": "34567"}]
        }},
    }
    if damage == "label":
        info["Config"]["Labels"]["web-modelos-local-ci-run"] = "other"
    elif damage == "port":
        info["NetworkSettings"]["Ports"]["6379/tcp"][0]["HostPort"] = "56379"
    elif damage == "stopped":
        info["State"]["Running"] = False
    elif damage == "host":
        url = "redis://localhost:34567/0"
    elif damage == "database":
        url = "redis://127.0.0.1:34567/15"
    elif damage == "credentials":
        url = "redis://user:synthetic@127.0.0.1:34567/0"
    elif damage == "query":
        url = "redis://127.0.0.1:34567/0?db=15"
    monkeypatch.setenv("LOCAL_CI_BENCHMARK_RUN", "invalid" if damage == "run" else run)
    monkeypatch.setenv("LOCAL_CI_BENCHMARK_REDIS_CONTAINER", "normal-redis" if damage == "name" else name)
    monkeypatch.setenv("WEB_MODELOS_BENCHMARK_OWNED_REDIS_URL", url)
    if damage == "unscoped":
        monkeypatch.delenv("LOCAL_CI_BENCHMARK_RUN")
    elif damage == "missing_override":
        monkeypatch.delenv("WEB_MODELOS_BENCHMARK_OWNED_REDIS_URL")
    monkeypatch.setattr(benchmark, "OWNED_REDIS", url)
    inspected, connected = [], []

    def inspect(command, **kwargs):
        inspected.append(command)
        return json.dumps([info])

    sentinel = object()

    def client(value):
        connected.append(value)
        return sentinel

    monkeypatch.setattr(benchmark.subprocess, "check_output", inspect)
    monkeypatch.setattr(redis.Redis, "from_url", client)
    if damage is None:
        assert benchmark.owned_redis() is sentinel
        assert inspected == [["docker", "inspect", name]]
        assert connected == [url]
    else:
        with pytest.raises(AssertionError):
            benchmark.owned_redis()
        assert connected == []
