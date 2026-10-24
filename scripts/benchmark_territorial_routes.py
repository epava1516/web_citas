"""Explicit synthetic territorial route cycle; no capacity verdicts."""
from urllib.parse import parse_qs, urlencode, urlsplit


def territorial_routes(geography):
    """Return distinct city/text/page ES/EN paths from an audited census."""
    if (not isinstance(geography, dict) or len(geography) != 2
            or any(not isinstance(city, str) or not city.isascii() or not city.isdecimal()
                   or int(city) <= 0 or type(count) is not int or count <= 0
                   for city, count in geography.items())
            or len({int(city) for city in geography}) != 2):
        raise ValueError('Expected two distinct positive municipality IDs and counts')
    paths = []
    for city, count in sorted(geography.items(), key=lambda row: int(row[0])):
        last = (count + 23) // 24
        for text in ('', 'photography'):
            for page in sorted({1, (last + 1) // 2, last}):
                query = urlencode({'city': city, 'q': text, 'page': page})
                paths.extend('/' + language + '/?' + query for language in ('es', 'en'))
    return paths


def balanced_territorial_cycle(geography, base_routes):
    """Keep original six probes, then six-slot territorial blocks at equal thirds.

    Repeated detail paths are deliberate scheduling slots, not extra identities.
    Every six arrivals have two of each route kind and three of each language.
    """
    if (len(base_routes) != 6
            or not all(path.startswith('/' + ('es' if i % 2 == 0 else 'en') + '/')
                       for i, path in enumerate(base_routes))
            or any('/listing/' in path for path in base_routes[:4])
            or not all('/listing/' in path for path in base_routes[4:])):
        raise ValueError('Expected ES/EN listing, search and detail base pairs')
    for pair, expected in ((base_routes[:2], False), (base_routes[2:4], True)):
        if any(bool(parse_qs(urlsplit(path).query).get('q')) != expected for path in pair):
            raise ValueError('Base list/search pair does not match route kind')
    routes = territorial_routes(geography)
    listing = [path for path in routes if not parse_qs(urlsplit(path).query).get('q')]
    search = [path for path in routes if parse_qs(urlsplit(path).query).get('q')]
    assert len(listing) == len(search) and len(listing) % 2 == 0
    cycle = list(base_routes)
    for i in range(0, len(listing), 2):
        cycle.extend(listing[i:i + 2] + search[i:i + 2] + list(base_routes[4:]))
    return cycle
