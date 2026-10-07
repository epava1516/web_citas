"""Observe GC overlap during the existing control/rule profile, not change policy."""

import pytest
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_discovery_rule_profile import test_discovery_rule_profile_10000 as run_profile
from test_photos import photo_environment  # noqa: F401

from scripts.benchmark_gc_observer import GCObserver
from scripts.benchmark_rule_profile import RuleProfile

pytestmark = pytest.mark.django_db(transaction=True)


def test_discovery_gc_profile_10000(request, monkeypatch, record_property):
    profiles = []
    reports = []
    original_init = RuleProfile.__init__
    original_get = Client.get

    def initialized(profile, *args, **kwargs):
        original_init(profile, *args, **kwargs)
        profiles.append(profile)

    def active_rules():
        return tuple(frame["rule"] for frame in profiles[-1].stack.get()) if profiles else ()

    def get(client, path, *args, **kwargs):
        if path != "/es/":
            return original_get(client, path, *args, **kwargs)
        with GCObserver(rule_path=active_rules) as observer:
            response = original_get(client, path, *args, **kwargs)
        report = observer.report()
        assert report["policy_before"] == report["policy_after"]
        assert report["unfinished_events"] == 0
        assert sum(report["calls_by_generation"].values()) == sum(report["collections_stats_delta"])
        reports.append(report)
        return response

    monkeypatch.setattr(RuleProfile, "__init__", initialized)
    monkeypatch.setattr(Client, "get", get)
    run_profile(request, monkeypatch, record_property)
    assert len(reports) == 2
    record_property("gc_control", reports[0])
    record_property("gc_profiled", reports[1])
    record_property("gc_comparison_limit", "Added GC callbacks to the original 10k control/RuleProfile protocol. Control response/context retained as before. Callbacks are low-volume but causal overhead not_measured; observed intervals overlap caller timings, never discounted again. CPU belongs to collector thread, not PostgreSQL/Gunicorn/load client. This synchronous profile cannot explain prior generator stalls. No collector policy or application validation changed.")
