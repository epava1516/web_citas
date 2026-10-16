"""Actual RR detail parity against the frozen pre-context native endpoint."""
import uuid

import pytest
from django.core import signing
from owned_detail_context import build_detail_context_prototype, patch_detail_view
from owned_detail_native_reference import build_native_detail_reference
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Listing, Rate, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_detail_context_parity(request, monkeypatch, record_property):
    client = request.getfixturevalue('directory')
    data = populate(80)
    listing = Listing.objects.select_related('approved_revision', 'person').get(pk=data['sample_ids'][1])
    revision = listing.approved_revision
    base = {key:getattr(revision,key) for key in ['phone','description','contact_exposure_accepted','telegram']}
    rate = revision.rates.first()
    manager, concept = listing.person.manager_version, rate.concept
    prototype = build_detail_context_prototype()
    native = build_native_detail_reference()
    # Fix only the signing timestamp component; native signature/payload stay real.
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: stamp)
    cases=[]
    for scenario in ['valid','phone','content','consent','rate','manager','normalization','foreign_revision','paused']:
        Revision.objects.filter(pk=revision.pk).update(**base)
        Listing.objects.filter(pk=listing.pk).update(status='published', approved_revision_id=revision.pk)
        Person.objects.filter(pk=listing.person_id).update(manager_version=manager)
        Rate.objects.filter(pk=rate.pk).update(concept=concept)
        if scenario == 'phone':
            Revision.objects.filter(pk=revision.pk).update(phone='invalid')
        elif scenario == 'content':
            Revision.objects.filter(pk=revision.pk).update(description='https://example.invalid')
        elif scenario == 'consent':
            Revision.objects.filter(pk=revision.pk).update(contact_exposure_accepted=False)
        elif scenario == 'rate':
            Rate.objects.filter(pk=rate.pk).update(concept='https://example.invalid')
        elif scenario == 'manager':
            Person.objects.filter(pk=listing.person_id).update(manager_version=manager+1)
        elif scenario == 'normalization':
            Revision.objects.filter(pk=revision.pk).update(telegram='@synthetic_user')
        elif scenario == 'foreign_revision':
            other = Listing.objects.exclude(pk=listing.pk).filter(status='published').first()
            Listing.objects.filter(pk=listing.pk).update(approved_revision_id=other.approved_revision_id)
        elif scenario == 'paused':
            Listing.objects.filter(pk=listing.pk).update(status='paused')
        for language in ['es','en']:
            path = f'/{language}/listing/{listing.pk}/'
            with monkeypatch.context() as patch:
                patch_detail_view(patch, native)
                reference = client.get(path)
            with monkeypatch.context() as patch:
                patch_detail_view(patch, prototype)
                candidate = client.get(path)
            expected = 200 if scenario in ['valid','normalization'] else 404
            assert candidate.status_code == reference.status_code == expected
            assert candidate.content == reference.content
            cases.append(dict(scenario=scenario,language=language,status=expected))
    for identity in [str(uuid.uuid4()), 'missing']:
        if identity == 'missing':
            continue  # UUID converter intentionally rejects non-UUID paths before this view.
        path=f'/es/listing/{identity}/'
        with monkeypatch.context() as patch:
            patch_detail_view(patch,native)
            reference=client.get(path)
        with monkeypatch.context() as patch:
            patch_detail_view(patch,prototype)
            candidate=client.get(path)
        assert reference.status_code == candidate.status_code == 404
        assert reference.content == candidate.content
    record_property('detail_context_parity', cases)
    record_property('limits','Native guard retained, own RR and inherited native fallback; sequential parity only. '
                    'No concurrency or performance claim from this file alone.')
