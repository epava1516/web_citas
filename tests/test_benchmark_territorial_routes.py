"""Route census, deep boundaries and invalid plans before native TCP calibration."""
from urllib.parse import parse_qs, urlsplit

import pytest

from scripts.benchmark_territorial_routes import balanced_territorial_cycle, territorial_routes


@pytest.mark.parametrize('counts,length,deepest', [((7, 3), 8, 1), ((700, 300), 24, 30), ((686, 300), 24, 29), ((56, 30), 20, 3), ((7000, 3000), 24, 292)])
def test_territorial_cycle_covers_languages_filters_and_boundaries(counts, length, deepest):
    routes = territorial_routes({'9': counts[1], '2': counts[0]})
    assert len(routes) == len(set(routes)) == length
    decoded = [(urlsplit(path).path, parse_qs(urlsplit(path).query, keep_blank_values=True)) for path in routes]
    assert max(int(query['page'][0]) for _, query in decoded) == deepest
    for city, count in zip(('2', '9'), counts):
        last = (count + 23) // 24
        for text in ('', 'photography'):
            for language in ('es', 'en'):
                pages = {int(q['page'][0]) for path, q in decoded
                         if path == '/' + language + '/' and q['city'] == [city] and q['q'] == [text]}
                assert pages == {1, (last + 1) // 2, last}
    assert all(routes[index].startswith('/es/') and routes[index + 1].startswith('/en/')
               for index in range(0, len(routes), 2))


@pytest.mark.parametrize('geography', [{}, {'1': 1}, {'1': True, '2': 2}, {'1': 0, '2': 2}, {'1': 1, '01': 2}, {'bad': 1, '2': 2}])
def test_invalid_territorial_census_rejected(geography):
    with pytest.raises(ValueError):
        territorial_routes(geography)


@pytest.mark.parametrize('counts', [(7, 3), (700, 300), (686, 300), (7000, 3000)])
@pytest.mark.parametrize('arrivals', [60, 1200, 18000])
def test_balanced_territorial_cycle_preserves_contract_mix(counts, arrivals):
    from collections import Counter

    base = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
            '/es/listing/first/', '/en/listing/last/']
    geography = {'2': counts[0], '9': counts[1]}
    cycle = balanced_territorial_cycle(geography, base)
    assert cycle[:6] == base
    assert set(cycle) == set(base) | set(territorial_routes(geography))
    assert len(cycle) == (18 if counts[0] == 7 else 42)
    observed = [cycle[i % len(cycle)] for i in range(arrivals)]
    kinds = Counter('detail' if '/listing/' in path else
                    'search' if parse_qs(urlsplit(path).query).get('q') else 'listing'
                    for path in observed)
    assert kinds == {'detail': arrivals // 3, 'search': arrivals // 3, 'listing': arrivals // 3}
    assert Counter(path.split('/')[1] for path in observed) == {'es': arrivals // 2, 'en': arrivals // 2}
    assert set(territorial_routes(geography)) <= set(observed)


@pytest.mark.parametrize('base', [[], ['/es/'] * 6,
    ['/es/?q=wrong', '/en/', '/es/?q=x', '/en/?q=x', '/es/listing/a/', '/en/listing/b/']])
def test_balanced_cycle_rejects_incompatible_base(base):
    with pytest.raises(ValueError):
        balanced_territorial_cycle({'1': 7, '2': 3}, base)
