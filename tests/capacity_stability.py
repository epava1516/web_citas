"""Predeclared linear-quantile reproducibility heuristics, not hypothesis tests."""
from statistics import median


def quantile(values, fraction):
    ordered = sorted(values)
    location = (len(ordered) - 1) * fraction
    low = int(location)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (location - low)


def gate(samples):
    if len(samples) != 20:
        raise ValueError('Gate requires exactly twenty measured controls')
    result = {}
    for key in ('tcp_ns', 'wsgi_thread_cpu_ns'):
        values = [sample[key] for sample in samples]
        middle = median(values)
        spread = quantile(values, .9) - quantile(values, .1)
        drift = abs(median(values[:5]) - median(values[-5:]))
        result[key] = dict(median=middle, p10=quantile(values, .1), p90=quantile(values, .9),
                           minimum=min(values), maximum=max(values), spread_fraction=spread/middle,
                           drift_fraction=drift/middle, passes=spread <= .1*middle and drift <= .1*middle)
    return dict(metrics=result, passes=all(item['passes'] for item in result.values()),
                semantics='predeclared_10percent_spread_and_drift_heuristic_not_contractual_p95')
