"""Instrumentation contract: passthrough, privacy, exceptions and opt-in guards."""

import json
import subprocess
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from scripts.http_operation_metrics import measure_request, owned_run


def test_passthrough_records_only_safe_scalar_fields():
    sentinel = "private-token-password-subject"
    request = {"REQUEST_METHOD": "POST", "PATH_INFO": "/secret/" + sentinel, "body": sentinel}
    response = SimpleNamespace(status_code=302, wsgi_request=SimpleNamespace(
        resolver_match=SimpleNamespace(view_name="listing_lifecycle")))
    client = object()
    calls = []

    def original(actual_client, **kwargs):
        assert actual_client is client and kwargs == request
        return response

    clock = iter([10.0, 10.25]).__next__
    assert measure_request(original, client, request, calls,
                           sql_scope=lambda callback: nullcontext(), clock=clock) is response
    assert calls[0]["route_name"] == "listing_lifecycle"
    assert calls[0]["status"] == 302 and calls[0]["request_seconds_instrumented"] == .25
    assert sentinel not in json.dumps(calls) and "PATH_INFO" not in json.dumps(calls)


def test_exception_is_unchanged_and_its_message_is_never_recorded():
    error = ValueError("private credential payload")
    calls = []

    def original(client, **request):
        raise error

    with pytest.raises(ValueError) as caught:
        measure_request(original, object(), {"REQUEST_METHOD": "GET"}, calls,
                        sql_scope=lambda callback: nullcontext())
    assert caught.value is error
    assert calls[0]["exception_class"] == "ValueError" and calls[0]["status"] is None
    assert "private credential" not in json.dumps(calls)


def test_owner_guard_requires_matching_runner_identity():
    run = "20261025-000000-1234abcd"
    environment = {"LOCAL_CI_HTTP_OPERATION_RUN": run,
                   "LOCAL_CI_POSTGRES_CONTAINER": "web-modelos-ci-pg-" + run,
                   "LOCAL_CI_TELEGRAM_OWNER": "runner"}
    assert owned_run(environment) == run
    for field in environment:
        with pytest.raises(pytest.UsageError):
            owned_run({key: value for key, value in environment.items() if key != field})


@pytest.mark.parametrize("arguments", [
    ["--profile", "checks"],
    ["--profile", "focused", "--workers", "2"],
    ["--profile", "focused", "--workers", "1", "--benchmark-generator-freeze"],
])
def test_runner_rejects_incompatible_modes_before_creating_resources(arguments):
    result = subprocess.run([sys.executable, "scripts/run_local_ci.py",
                             "--observe-http-operations", *arguments],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert "requires serial focused tests without load observers" in result.stderr


def test_sql_parameters_are_passed_through_and_never_retained():
    from contextlib import contextmanager

    secret = "private-sql-value"
    seen = {}
    calls = []
    response = SimpleNamespace(status_code=200)

    @contextmanager
    def sql_scope(callback):
        seen["callback"] = callback
        yield

    def execute(sql, params, many, context):
        assert sql == "SELECT private_column" and params == [secret]
        return response

    def original(client, **request):
        assert seen["callback"](execute, "SELECT private_column", [secret], False, {}) is response
        return response

    clock = iter([10.0, 10.1, 10.2, 10.3]).__next__
    assert measure_request(original, object(), {"REQUEST_METHOD": "GET"}, calls,
                           sql_scope=sql_scope, clock=clock) is response
    assert calls[0]["sql_queries"] == 1
    assert calls[0]["sql_execute_seconds"] == pytest.approx(.1)
    assert secret not in json.dumps(calls) and "private_column" not in json.dumps(calls)


def test_call_hook_restores_client_even_if_test_raises():
    from django.test import Client

    from scripts.http_operation_metrics import pytest_runtest_call

    original = Client.request
    item = SimpleNamespace(user_properties=[])
    hook = pytest_runtest_call(item)
    next(hook)
    assert Client.request is not original
    with pytest.raises(RuntimeError, match="test sentinel"):
        hook.throw(RuntimeError("test sentinel"))
    assert Client.request is original
    assert dict(item.user_properties)["http_operation_count"] == 0
