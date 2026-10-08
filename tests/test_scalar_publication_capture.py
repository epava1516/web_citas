"""Full scalar capture preserves ordered population/count/pages and fresh guard."""
from uuid import UUID

import pytest
from django.core.paginator import EmptyPage
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Listing, Revision
from apps.listings.sql_publication import SQLPublication
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_scalar_ids_omit_sort_fields_preserve_full_native_population_and_pages(request, record_property):
    request.getfixturevalue('directory')
    populate(50)
    expected = native_ids(candidates({}))
    target = Listing.objects.get(pk=expected[25]).approved_revision
    assert target.listing_id not in expected[:24]
    initial = target.description
    observations = []
    # Equal timestamps and NULL timestamp keep PostgreSQL's existing ordering;
    # the outer order uses INNER UUID columns, never text output aliases.
    Listing.objects.filter(pk__in=expected[30:32]).update(published_at=None)
    for text in [initial, 'Texto válido 😀', 'www.example.invalid']:
        Revision.objects.filter(pk=target.pk).update(description=text)
        for data in [{}, {'q':'photography'}]:
            query = candidates(data)
            native = native_ids(query)
            for indexed in [False, True]:
                scalar = SQLPublication(query, scalar_capture=True, text_membership=indexed)
                old = SQLPublication(query, scalar_capture=False, text_membership=indexed)
                assert scalar.scalar_capture and not old.scalar_capture
                assert scalar.visible_ids(query)==old.visible_ids(query)==native
                assert len(scalar.rows)==50
                assert all(set(row)=={'pk','approved_revision_id','_sql_publication_positive'} for row in scalar.rows)
                assert all(type(row['pk']) is str for row in scalar.rows)
                assert [(UUID(r['pk']), UUID(r['approved_revision_id']),r['_sql_publication_positive'])
                        for r in scalar.rows]==[(r['pk'],r['approved_revision_id'],r['_sql_publication_positive'])
                                               for r in old.rows]
                for number in [1,2,3]:
                    page=scalar.scalar_page(query,number)
                    assert page.paginator.count==len(native)
                    assert list(page)==native[(number-1)*24:number*24]
                    for pk in page:
                        assert type(pk) is UUID
                        assert scalar.captured_revision(pk)==old.captured_revision(pk)
                observations.append({'search':bool(data),'indexed':indexed,'count':len(native),
                    'returned_sql_rows':scalar.stats['scalar_statement_rows_returned']})
    Revision.objects.filter(pk=target.pk).update(description=initial)
    observation = {}
    public_page = projection.projected_page(candidates({}),1,observation=observation)
    assert public_page is not None, observation
    assert public_page.paginator.count==50
    for query in [candidates({}).none(), candidates({'q':'no_matching_token_zyx'})]:
        scalar=SQLPublication(query,scalar_capture=True)
        assert scalar.scalar_page(query,1).paginator.count==0
    with pytest.raises(EmptyPage):
        SQLPublication(candidates({})).scalar_page(candidates({}),4)
    # Unreviewed ordering takes the ordinary ORM path without changing it.
    query=candidates({}).order_by('pk')
    scalar=SQLPublication(query,scalar_capture=True)
    assert not scalar.scalar_capture and scalar.visible_ids(query)==native_ids(query)
    record_property('scalar_capture_equivalence',observations)


def test_combined_default_http_keeps_native_bodies_all_pages_and_unknowns(request, monkeypatch, record_property):
    client = request.getfixturevalue('directory')
    populate(50)
    expected = native_ids(candidates({}))
    target = Listing.objects.get(pk=expected[25]).approved_revision
    initial = target.description
    observations = []
    for text in [initial, 'Texto válido 😀', 'www.example.invalid']:
        Revision.objects.filter(pk=target.pk).update(description=text)
        for language in ['es', 'en']:
            for suffix in ['', '?q=photography']:
                path = '/'+language+'/'+suffix
                for number in [1,2,3]:
                    url = path+('&' if suffix else '?')+'page='+str(number)
                    current = client.get(url)
                    route = current.wsgi_request._publication_route
                    assert route['route']=='projection'
                    assert route['candidate_stats']['scalar_capture'] is True
                    assert route['candidate_stats']['text_membership'] is True
                    with monkeypatch.context() as patch:
                        patch.setattr(projection,'supported',lambda **kwargs:False)
                        native = client.get(url)
                    assert current.status_code==native.status_code==200
                    assert current.content==native.content
                    assert [r.pk for r in current.context['page']]==[r.pk for r in native.context['page']]
                    assert current.context['page'].paginator.count==native.context['page'].paginator.count
                observations.append({'language':language,'search':bool(suffix),
                    'native_count':native.context['page'].paginator.count,
                    'candidate_stats':route['candidate_stats']})
    record_property('combined_default_public_equivalence',observations)
