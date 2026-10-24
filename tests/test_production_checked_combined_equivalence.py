"""Local policy equivalence with synthetic proof metadata, never provider evidence."""

from urllib.parse import urlencode

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.core.models import Agency, Person, PhoneClaim, VerificationCheck
from apps.core.verification_services import real_checks
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('mode', ['normal', 'production'])
def test_combined_checked_native_pages_and_obsolete_proof(request, settings, record_property, mode):
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert not settings.RECOVERY_MODE
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    settings.PROMOTION_TEST_MODE = False
    client = request.getfixturevalue('directory')
    dataset = populate(100)  # Its nonproduction guard remains intact.
    assert dataset['synthetic'] and dataset['published'] == 100
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    assert len(cities) == 2
    rows = list(Listing.objects.filter(status='published').select_related('approved_revision')
                .order_by('pk'))
    assert len(rows) == 100
    for index, row in enumerate(rows):
        revision = row.approved_revision
        revision.municipality_id = cities[0] if index < 70 else cities[1]
        revision.postal_code_id = revision.zone_id = None
        revision.profile_type, revision.spoken_languages = 'woman', ['en']
    Revision.objects.bulk_update([row.approved_revision for row in rows],
                                ['municipality', 'postal_code', 'zone', 'profile_type', 'spoken_languages'])
    # Explicitly labelled local metadata, not calls to a real verification provider.
    settings.VERIFICATION_PROVIDER = 'synthetic-policy-fixture.invalid'
    checks = list(VerificationCheck.objects.filter(person_id__in=[r.person_id for r in rows]))
    assert len(checks) == 100
    obsolete_people = {row.person_id for index, row in enumerate(rows) if index % 5 == 0}
    for check in checks:
        check.provider = settings.VERIFICATION_PROVIDER
        check.procedure = '' if check.person_id in obsolete_people else 'age-v1'
    VerificationCheck.objects.bulk_update(checks, ['provider', 'procedure'])
    people = Person.objects.filter(pk__in=[row.person_id for row in rows])
    PhoneClaim.objects.filter(pk__in=people.values('phone_claim_id')).update(verification_procedure='sms-v1')
    Agency.objects.filter(pk__in=people.values('agency_id')).update(verification_procedure='organization-v1')
    settings.PRODUCTION = mode == 'production'
    publication_state.rules_version.cache_clear()
    reports = []
    target = rows[61]  # Off the first page in the majority city's native cohort.
    assert target.person_id not in obsolete_people
    try:
        publication_state.refresh_all()
        for phase in ('fresh', 'pending', 'repaired'):
            if phase == 'pending':
                check = VerificationCheck.objects.get(person_id=target.person_id)
                check.manager_version += 1
                # Keep PostgreSQL invalidation triggers, bypass the model signal
                # that would repair immediately under photo_environment's eager Celery.
                assert VerificationCheck.objects.filter(pk=check.pk).update(
                    manager_version=check.manager_version) == 1
            elif phase == 'repaired':
                publication_state.refresh_all()  # Manual only, no worker claim.
            marks = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
            assert len(marks) == (1 if phase == 'pending' else 0)
            if phase == 'pending':
                assert marks[0]['listing_id'] == target.pk
            for city in cities:
                native = reference_territorial_order(city, 'photography', promotions=False)
                people = {row.pk: row.person for row in Listing.objects.filter(pk__in=native)
                          .select_related('person__phone_claim', 'person__agency')}
                for checked in ((), ('age',), ('contact',), ('age', 'contact')):
                    expected = [pk for pk in native if not checked
                                or any(real_checks(people[pk])[key] for key in checked)]
                    # Selection has OR semantics for multiple specific checks.
                    expected_count = (56 if city == cities[0] else 24)
                    if mode == 'normal' and checked != ('age',):
                        expected_count = 70 if city == cities[0] else 30
                    # An obsolete manager proof invalidates native publication in
                    # both modes, including contact-only and unfiltered reads.
                    if phase != 'fresh' and city == cities[0]:
                        expected_count -= 1
                    assert len(expected) == expected_count
                    for locale in ('es', 'en'):
                        seen = []
                        for page_number in range(1, (len(expected) + 23) // 24 + 1):
                            params = {'city': city, 'profile': 'woman', 'language': 'en',
                                      'q': 'photography', 'checked': checked, 'page': page_number}
                            response = client.get('/'+locale+'/?'+urlencode(params, doseq=True))
                            assert response.status_code == 200
                            page = response.context['page']
                            actual = [row.pk for row in page.object_list]
                            assert actual == expected[(page_number-1)*24:page_number*24]
                            assert page.paginator.count == len(expected)
                            seen += actual
                            reports.append({'phase': phase, 'city': city, 'checked': checked,
                                            'locale': locale, 'page': page_number, 'count': len(expected)})
                        assert seen == expected and len(seen) == len(set(seen))
            assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == marks
        assert any(row['page'] == 3 for row in reports)
        record_property('production_checked_combined_equivalence', {
            'mode': mode, 'population': 100, 'geography': [70, 30], 'synthetic_metadata_only': True,
            'real_provider_credited': False, 'capacity_accepted': False, 'promotions': False,
            'manual_repair': True, 'worker_execution_credited': False, 'pending_marks': 1,
            'reads_do_not_repair': True, 'pages_checked': len(reports), 'observations': reports,
        })
    finally:
        publication_state.rules_version.cache_clear()
