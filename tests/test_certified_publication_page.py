"""Complete population proof precedes reduced page transfer; unknowns stay whole."""
from functools import wraps

import pytest
from django.core.paginator import EmptyPage
from django.utils.translation import override
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import projected_publication as projection
from apps.listings import sql_publication
from apps.listings.discovery import candidates
from apps.listings.models import Listing, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_certified_page_counts_full_population_and_unknowns_before_pagination(request, record_property):
    client = request.getfixturevalue('directory')
    populate(50)
    expected = native_ids(candidates({}))
    target = Listing.objects.get(pk=expected[25]).approved_revision
    initial = target.description
    observations = []
    for text, compact in [(initial, True), ('Texto válido 😀', False), ('www.example.invalid', False)]:
        Revision.objects.filter(pk=target.pk).update(description=text)
        for search in ['', 'photography']:
            data = {'q':search} if search else {}
            query = candidates(data)
            native = native_ids(query)
            for language in ['es','en']:
                with override(language):
                    for number in [1,2,3]:
                        proof = sql_publication.SQLPublication(query, page_number=number)
                        assert proof.compact is compact
                        if compact:
                            page = proof.certified_page(query,number)
                            assert proof.population_count==50
                            assert len(proof.rows)==len(native[(number-1)*24:number*24])
                            assert proof.stats['certified_statement_rows_returned_including_header']==1+len(proof.rows)
                        else:
                            assert len(proof.rows)==50
                            assert proof.visible_ids(query)==native
                        served = projection.projected_page(query,number,compact=True)
                        assert served.paginator.count==len(native)
                        assert [row.pk for row in served]==native[(number-1)*24:number*24]
            observations.append({'text_case': len(observations)//2,'search':bool(search),
                'eligible':len(native),'compact':compact,'captured_id_rows':len(proof.rows)})
    Revision.objects.filter(pk=target.pk).update(description=initial)
    for query in [candidates({'q':'no_matching_token_zyx'}), candidates({}).none()]:
        page = projection.projected_page(query,1,compact=True)
        assert page.paginator.count==0 and list(page)==[]
    with pytest.raises(EmptyPage):
        projection.projected_page(candidates({}),4,compact=True)
    with pytest.raises(EmptyPage):
        projection.projected_page(candidates({}),0,compact=True)
    query = candidates({}).order_by('pk')
    p = sql_publication.SQLPublication(query,page_number=1)
    assert not p.compact and p.visible_ids(query)==native_ids(query)
    response = client.get('/es/')
    stats = response.wsgi_request._publication_route['candidate_stats']
    assert stats['candidates']==stats['positive']==50
    assert stats['captured_id_rows']==50 and not stats['compact_certified_page']
    record_property('certified_page_cases',observations)


def test_duplicate_pointer_and_changed_page_helper_cannot_certify_a_partial_population(request,monkeypatch):
    request.getfixturevalue('directory')
    populate(50)
    expected = native_ids(candidates({}))
    source, target = Listing.objects.get(pk=expected[-2]), Listing.objects.get(pk=expected[-1])
    original_revision = target.approved_revision_id
    Listing.objects.filter(pk=target.pk).update(approved_revision_id=source.approved_revision_id)
    p = sql_publication.SQLPublication(candidates({}),page_number=1)
    assert not p.compact and len(p.rows)==50
    with pytest.raises(ValueError,match='requires its own current revision instance'):
        projection.projected_page(candidates({}),1)
    Listing.objects.filter(pk=target.pk).update(approved_revision_id=original_revision)
    original = sql_publication.read_certified_page
    @wraps(original)
    def changed(*args,**kwargs):
        raise AssertionError('Changed helper must never execute in public projected route')
    monkeypatch.setattr(sql_publication,'read_certified_page',changed)
    assert not projection.supported()
    assert projection.projected_page(candidates({}),1) is None
