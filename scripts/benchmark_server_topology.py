"""Explicit own-CI-only alternative; deployed server configuration is untouched."""
import re


def server_topology(environment):
    mode = environment.get("WEB_MODELOS_BENCHMARK_GTHREAD")
    if mode is None:
        return {"worker_class": "sync", "workers": 4, "threads": 1}
    if mode != "1" or not re.fullmatch(
        r"web-modelos-ci-pg-\d{8}-\d{6}-[0-9a-f]{8}",
        environment.get("LOCAL_CI_POSTGRES_CONTAINER", ""),
    ):
        raise ValueError("Threaded candidate requires explicit owned CI PostgreSQL")
    return {"worker_class": "gthread", "workers": 4, "threads": 2}
