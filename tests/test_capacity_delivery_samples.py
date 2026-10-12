"""Finite sampling-contract guards; no HTTP, database or capacity workload."""

from threading import Barrier
from types import SimpleNamespace

import pytest
from capacity_delivery_flow import sampled


@pytest.mark.parametrize('diagnostic,native,enabled', [
    (False, False, False), (False, True, False), (True, True, False), (True, False, True),
])
def test_post_validation_profile_is_exclusively_legacy_diagnostic(monkeypatch, diagnostic, native, enabled):
    import capacity_delivery_flow as flow

    monkeypatch.setattr(flow.runtime_settings, 'CAPACITY_NATIVE_PROFILE', native, raising=False)
    calls = []
    monkeypatch.setattr(flow, 'validation_profile', lambda *args: calls.append(args) or {'legacy': True})
    result = flow.post_validation_profile('case', 'export', diagnostic=diagnostic)
    assert bool(calls) == enabled
    assert result == ({'legacy': True} if enabled else
                      {'status': 'disabled', 'reason': 'Only legacy diagnostic mode permits cProfile'})


@pytest.mark.parametrize('failure', [False, True])
def test_native_controller_timing_does_not_install_cprofile(monkeypatch, failure):
    import capacity_delivery_flow as flow

    monkeypatch.setattr(flow.runtime_settings, 'CAPACITY_NATIVE_PROFILE', True, raising=False)
    monkeypatch.setattr(flow.cProfile, 'Profile', lambda: pytest.fail('controller cProfile installed'))
    metrics = {'diagnostic': True}
    error = ValueError('operation failure')

    def operation():
        if failure:
            raise error
        return 'result'

    if failure:
        with pytest.raises(ValueError) as caught:
            flow.measured(metrics, 'operation', operation)
        assert caught.value is error
    else:
        assert flow.measured(metrics, 'operation', operation) == 'result'
    assert len(metrics['operation']) == 1 and 'profiles' not in metrics


def response(stages, cache_control="private, no-store"):
    return SimpleNamespace(status=200, seconds=.1, interval=[1, 1.1], body=b"synthetic",
                           stages=stages, headers={"Cache-Control": cache_control})


@pytest.mark.parametrize("profile", [False, True])
def test_proxy_client_allows_ordinary_save_without_delivery_redirect(monkeypatch, profile):
    result = response([{"method": "POST", "status": 200}])
    monkeypatch.setattr("capacity_delivery_flow.post", lambda *args, **kwargs: result)
    metrics = {}
    assert sampled(metrics, "binary_page_save", Barrier(1),
                   SimpleNamespace(private_delivery=object()), "http://own/save/", "csrf", {},
                   profile=profile) == b"synthetic"
    assert metrics["binary_page_save_profiled_seconds" if profile else "binary_page_save"] == [.1]


@pytest.mark.parametrize("profile", [False, True])
@pytest.mark.parametrize("stages,cache_control,allowed", [
    ([{"method": "POST", "status": 200}], "private, no-store", False),
    ([{"method": "POST", "status": 303}, {"method": "GET", "status": 200}], "public", False),
    ([{"method": "POST", "status": 303}, {"method": "GET", "status": 200}], "private, no-store", True),
])
def test_private_download_requires_redirect_eof_and_privacy(
    monkeypatch, profile, stages, cache_control, allowed
):
    result = response(stages, cache_control)
    monkeypatch.setattr("capacity_delivery_flow.post", lambda *args, **kwargs: result)
    args = ({}, "binary_download", Barrier(1), SimpleNamespace(private_delivery=object()),
            "http://own/part/", "csrf", {})
    if allowed:
        assert sampled(*args, profile=profile, require_private_delivery=True) == b"synthetic"
    else:
        with pytest.raises(AssertionError, match="binary_download"):
            sampled(*args, profile=profile, require_private_delivery=True)
