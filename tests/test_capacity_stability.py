"""Meaningful boundary controls for the reproducibility gate."""
import pytest

from tests.capacity_stability import gate, quantile


def samples(values):
    return [dict(tcp_ns=v, wsgi_thread_cpu_ns=v) for v in values]


def test_linear_quantiles_and_stable_control():
    assert quantile([0, 10, 20, 30], .1) == pytest.approx(3)
    assert gate(samples([100]*20))['passes']


def test_drift_and_spread_rejected():
    assert not gate(samples([100]*15+[120]*5))['passes']
    assert not gate(samples([80, 120]*10))['passes']


def test_exact_sample_budget():
    with pytest.raises(ValueError):
        gate(samples([100]*19))
