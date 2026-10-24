"""Native filtered census and HTTP oracle for the explicit owned multiscale calibration."""

import re
import urllib.request
from urllib.parse import urlencode
from uuid import UUID

from capacity_beta_http import verify_owned_fixture
from mixed_state_plan import native_sponsorships
from test_promotional_statistics_preparation import reference_territorial_order

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision


def distribute(dataset):
    verify_owned_fixture()
    count = dataset['published']
    assert dataset['synthetic'] and count in (100, 1000, 10000)
    assert sorted(dataset['geography'].values()) == [count*3//10, count*7//10]
    census = {}
    for city, count in dataset['geography'].items():
        rows = list(Revision.objects.filter(approved_for__status='published', municipality_id=city).order_by('pk'))
        assert len(rows) == count
        positive = dataset['published'] * (6 if count == dataset['published']*7//10 else 2) // 10
        for index, row in enumerate(rows):
            row.profile_type = 'woman' if index < positive else 'man'
            row.spoken_languages = ['en'] if index < positive else ['fr']
        Revision.objects.bulk_update(rows, ['profile_type', 'spoken_languages'])
        census[str(city)] = {'woman_en': positive, 'man_fr': count-positive, 'woman_fr': 0}
    return census


def cases(dataset):
    """Reference order uses native authority; filter membership uses native revisions."""
    assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
    revisions = {row.pk: row.approved_revision for row in Listing.objects.filter(status='published')
                 .select_related('approved_revision')}
    assert len(revisions) == dataset['published'] and dataset['published'] in (100, 1000, 10000)
    specs = []
    for city in dataset['geography']:
        for text in ('', 'photography', 'absent-combined-token'):
            native = reference_territorial_order(city, text, promotions=True)
            for profile, language in (('woman', 'en'), ('man', 'fr'), ('woman', 'fr')):
                expected = [pk for pk in native if revisions[pk].profile_type == profile
                            and language in revisions[pk].spoken_languages]
                assert bool(expected) == (text != 'absent-combined-token' and (profile, language) != ('woman', 'fr'))
                last = max(1, (len(expected)+23)//24)
                for number in sorted({1, (last+1)//2, last}):
                    for locale in ('es', 'en'):
                        path = '/'+locale+'/?'+urlencode({'city': city, 'profile': profile, 'language': language,
                                                        'q': text, 'page': number})
                        specs.append({'path': path, 'ids': list(map(str, expected[(number-1)*24:number*24])),
                                      'native_count': len(expected)})
    return specs


def plan(dataset, details):
    verify_owned_fixture()
    assert len(details) == 2 and details[0].startswith('/es/listing/') and details[1].startswith('/en/listing/')
    specs = cases(dataset)
    listings = [r['path'] for r in specs if 'q=&' in r['path']]
    searches = [r['path'] for r in specs if 'q=&' not in r['path']
                and ('absent-combined-token' not in r['path'] or 'profile=woman&language=en&' in r['path'])]
    # Schedule all positive-text pages and one absent-text pair per city.
    # Remaining negative combinations are verified by the independent HTTP oracle.
    assert listings and searches and len(listings) % 2 == len(searches) % 2 == 0
    assert len(listings) <= len(searches)
    cycle = []
    for index in range(0, len(searches), 2):
        offset = index % len(listings)
        cycle.extend(listings[offset:offset+2] + searches[index:index+2] + details)
    assert len(cycle) == 3*len(searches)
    assert len(cycle) <= (60 if dataset['published'] == 100 else 120)
    assert set(cycle) == set(listings+searches+details)
    return specs, cycle


def verify(endpoint, dataset, expected_plan):
    verify_owned_fixture()
    current = cases(dataset)
    assert current == expected_plan
    sponsors = native_sponsorships()
    checks = []
    for spec in current:
        with urllib.request.urlopen(endpoint.url+spec['path'], timeout=65) as response:
            body = response.read().decode()
            assert response.status == 200 and response.headers['Cache-Control'] == 'no-store'
        ids = re.findall(r'<h2><a href="/(?:es|en)/listing/([0-9a-f-]{36})/">', body)
        assert ids == spec['ids'] and len(ids) == len(set(ids))
        counts = re.findall(r'<p class="results-count" aria-live="polite">(\d+) (?:results|resultados)</p>', body)
        assert counts == [str(spec['native_count'])]
        cards = re.findall(r'<article class="card listing-card">(.*?)</article>', body, re.S)
        assert len(cards) == len(ids)
        labels = []
        for pk, card in zip(ids, cards, strict=True):
            expected = sponsors.get(UUID(pk))
            assert card.count('<p class="sponsored">') == int(expected is not None)
            actual = re.findall(r'<p class="sponsored">[^<]* · (premium|top)</p>', card)
            assert actual == ([expected] if expected else [])
            labels.append(expected)
        checks.append(spec | {'sponsorship': labels, 'status': 200})
    assert not PublicationDirty.objects.exists()
    return checks


def observe_generator(fetch, routes, *, proof, output=None, **kwargs):
    """Reuse the bounded loop observer; retain original transport validity gates."""
    import json
    from pathlib import Path

    from scripts.benchmark_generator_diagnostic import observed_transport

    target = Path(output) if output is not None else Path('/tmp/capacity-beta-generator.json')
    try:
        return observed_transport(fetch, routes, output=target, trace_scheduler=True, **kwargs)
    finally:
        proof['generator_diagnostic'] = json.loads(target.read_text())
