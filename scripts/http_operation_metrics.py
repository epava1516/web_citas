"""Opt-in synthetic Client.request measurements; never request bodies or QA duration."""

import json
import os
import re
import time

import pytest
from django.db import connection
from django.test import Client


def owned_run(environment):
    run = environment.get("LOCAL_CI_HTTP_OPERATION_RUN", "")
    if (not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[a-f0-9]{8}", run)
            or environment.get("LOCAL_CI_POSTGRES_CONTAINER") != "web-modelos-ci-pg-" + run
            or environment.get("LOCAL_CI_TELEGRAM_OWNER") != "runner"):
        raise pytest.UsageError("HTTP operation observation requires the owned local CI runner")
    return run


def measure_request(original, client, request, observations, *, sql_scope=None, clock=None):
    """Pass arguments/results/exceptions through; retain only safe scalar metadata."""
    clock = clock or time.perf_counter
    sql_scope = sql_scope or connection.execute_wrapper
    totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}
    response = None
    exception = None

    def timed(execute, sql, params, many, context):
        totals["sql_queries"] += 1
        started = clock()
        try:
            return execute(sql, params, many, context)
        finally:
            totals["sql_execute_seconds"] += clock() - started

    started = clock()
    try:
        with sql_scope(timed):
            response = original(client, **request)
        return response
    except BaseException as error:
        exception = type(error).__name__
        raise
    finally:
        elapsed = clock() - started
        method = request.get("REQUEST_METHOD", "UNKNOWN")
        if not isinstance(method, str) or method not in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"}:
            method = "UNKNOWN"
        route = "unresolved"
        status = None
        observer_error = None
        try:
            match = getattr(getattr(response, "wsgi_request", None), "resolver_match", None)
            name = getattr(match, "view_name", None)
            if isinstance(name, str) and re.fullmatch(r"[a-zA-Z0-9_.:-]{1,120}", name):
                route = name
            value = getattr(response, "status_code", None)
            if isinstance(value, int):
                status = value
        except Exception as error:
            # Metadata must not mask the original response/error. The audit rejects this sample.
            observer_error = type(error).__name__
        observations.append({
            "method": method, "route_name": route, "status": status,
            "request_seconds_instrumented": elapsed, **totals,
            "exception_class": exception, "observer_error_class": observer_error,
        })


def pytest_configure(config):
    owned_run(os.environ)
    if config.getoption("numprocesses", default=None) not in (None, 0):
        raise pytest.UsageError("HTTP operation observation requires serial tests")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    observations = []
    original = Client.request

    def measured(client, **request):
        if (connection.vendor != "postgresql"
                or not connection.settings_dict["NAME"].startswith("test_promotion_gate_")):
            raise RuntimeError("HTTP operation observation requires the owned PostgreSQL test database")
        return measure_request(original, client, request, observations)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Client, "request", measured)
        try:
            yield
        finally:
            item.user_properties.append(("http_operation_samples", json.dumps(observations, sort_keys=True)))
            item.user_properties.append(("http_operation_count", len(observations)))
            item.user_properties.append(("http_operation_scope", "Django Client.request call phase only; ordinary setup, assertions, direct services, browser/TCP, async work and load excluded; Client requests from fixtures dynamically requested during call are included. Expected denials remain functional outcomes, not a load error rate."))
