"""Opt-in detail-only resolved annotation template; no cached rows or authority."""
import inspect
import textwrap
from dataclasses import dataclass
from functools import lru_cache

from django.db.models import F

from apps.listings import moderation_views, public_validation
from apps.listings.models import Listing


@dataclass(frozen=True)
class DetailSeed:
    listing_id: object
    now: object


def build_detail_template_view():
    native_query = public_validation.publication_query
    retained = []

    @lru_cache(maxsize=8)
    def template(version):
        # The only retained variable is document.version; never a document object.
        class Version:
            pass
        document = Version()
        document.version = version
        query = native_query(Listing.objects.filter(
            status='published', approved_revision__status='approved',
            approved_revision__listing_id=F('pk'),
        ), document)
        retained.append(query)
        if len(retained) > 8:
            retained.pop(0)
        return query

    def resolved(seed, document):
        assert type(seed) is DetailSeed
        base = template(document.version if document else '')
        assert base._result_cache is None
        # filter() clones the unevaluated QuerySet. Current ID/clock are not retained.
        return base.filter(pk=seed.listing_id, expires_at__gt=seed.now)

    initializer = textwrap.dedent(inspect.getsource(public_validation.PublicationContext.__init__))
    before = 'publication_query(query, self.document)'
    assert initializer.count(before) == 1
    initializer = initializer.replace(before, 'resolved(query, self.document)')
    namespace = {**vars(public_validation), 'resolved': resolved}
    exec(compile(initializer, '<owned-detail-query-template-context>', 'exec'), namespace)
    context = type('TemplateContext', (public_validation.PublicationContext,),
                   {'__init__': namespace['__init__']})
    source = textwrap.dedent(inspect.getsource(moderation_views.public_detail))
    before = '''Listing.objects.filter(
                    pk=listing_id, status="published", expires_at__gt=timezone.now(),
                    approved_revision__status="approved", approved_revision__listing_id=F("pk"),
                )'''
    assert source.count(before) == 1
    source = source.replace(before, 'DetailSeed(listing_id, timezone.now())')
    namespace = {**vars(moderation_views), 'PublicationContext': context, 'DetailSeed': DetailSeed}
    exec(compile(source, '<owned-detail-query-template-view>', 'exec'), namespace)
    return namespace['public_detail'], template, retained
