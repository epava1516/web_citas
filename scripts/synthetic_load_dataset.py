"""Synthetic read-load fixtures in runner-owned PostgreSQL test databases only."""

from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.core.models import Person, RepresentationAction, User, VerificationCheck
from apps.listings.models import Listing, Rate, Revision
from apps.listings.moderation import publicly_visible
from apps.mediafiles.models import Photo


def clone(row, **changes):
    values = {
        field.attname: getattr(row, field.attname)
        for field in row._meta.concrete_fields
        if not field.primary_key and not getattr(field, "auto_now", False)
        and not getattr(field, "auto_now_add", False)
    }
    return type(row)(**(values | changes))


@transaction.atomic
def populate(count):
    if settings.PRODUCTION or not connection.settings_dict['NAME'].startswith('test_promotion_gate_'):
        raise ValueError('Load fixtures require runner-owned synthetic test database')
    baseline = Listing.objects.filter(status='published', person__agency__isnull=False).select_related('person', 'approved_revision').first()
    assert baseline and publicly_visible(baseline)
    existing = Listing.objects.filter(status='published').count()
    amount = count - existing
    assert amount >= 0
    users = User.objects.bulk_create([
        User(username=f'load-subject-{index}', email=f'load-{index}@example.invalid', password='!')
        for index in range(amount)
    ], batch_size=250)
    people = Person.objects.bulk_create([
        clone(baseline.person, alias=f'Synthetic load profile {index}', subject_id=user.pk,
              assigned_editor_id=None)
        for index, user in enumerate(users)
    ], batch_size=250)
    document = baseline.approved_revision.publisher_acceptance.document
    RepresentationAction.objects.bulk_create([
        RepresentationAction(person=person, subject_id=person.subject_id, manager_version=person.manager_version,
                             manager_kind='agency', manager_id=str(person.agency_id), action='grant', document=document)
        for person in people
    ], batch_size=250)
    check = baseline.person.verificationcheck_set.latest('created_at')
    VerificationCheck.objects.bulk_create([
        clone(check, person_id=person.pk, subject_id=person.subject_id) for person in people
    ], batch_size=250)
    listings = Listing.objects.bulk_create([
        Listing(person=person, status='published', published_at=timezone.now()-timedelta(days=index % 30),
                expires_at=timezone.now()+timedelta(days=30))
        for index, person in enumerate(people)
    ], batch_size=250)
    revisions = Revision.objects.bulk_create([
        clone(baseline.approved_revision, listing_id=listing.pk,
              title=f'Synthetic photography load {index}', source_revision_id=None)
        for index, listing in enumerate(listings)
    ], batch_size=250)
    photo = baseline.approved_revision.photos.first()
    Photo.objects.bulk_create([clone(photo, revision_id=revision.pk) for revision in revisions], batch_size=250)
    Rate.objects.bulk_create([Rate(revision=revision, concept='Synthetic session', mode='consult') for revision in revisions], batch_size=250)
    for name in ['categories', 'services']:
        relation = getattr(Revision, name).through
        field = 'category_id' if name == 'categories' else 'service_id'
        ids = list(getattr(baseline.approved_revision, name).values_list('pk', flat=True))
        relation.objects.bulk_create([
            relation(**{'revision_id': revision.pk, field: value}) for revision in revisions for value in ids
        ], batch_size=250)
    for listing, revision in zip(listings, revisions, strict=True):
        listing.approved_revision = revision
    Listing.objects.bulk_update(listings, ['approved_revision'], batch_size=250)
    assert Listing.objects.filter(status='published').count() == count
    for listing in [baseline, *listings[:1], *listings[-1:]]:
        assert publicly_visible(Listing.objects.select_related('person', 'approved_revision').get(pk=listing.pk))
    return {'published': count, 'synthetic': True, 'shared_synthetic_photo_fixture': True,
            'sample_ids': [str(listing.pk) for listing in [baseline, *listings[:20]]],
            'limits': 'State fixtures cloned from native seed_demo publication; shared synthetic media, no claim of10k native moderation or duplicate calibration.'}
