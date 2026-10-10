"""Finite sampling-contract guards; no HTTP, database or capacity workload."""

from threading import Barrier
from types import SimpleNamespace

import pytest
from capacity_delivery_flow import sampled


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
