"""Test-only resolved annotation structure for exact page hydration inputs."""
import inspect
import textwrap
from dataclasses import dataclass
from functools import lru_cache

from apps.listings import public_validation, publication_state
from apps.listings.models import Listing


@dataclass(frozen=True)
class PageSeed:
    identifiers: tuple


def build_page_template():
    retained = []

    @lru_cache(maxsize=8)
    def template(version):
        query = Listing.objects.annotate(**public_validation._publication_annotations(version))
        retained.append(query)
        return query

    def resolved(query, document):
        if isinstance(query, PageSeed):
            return template(document.version if document else '').filter(pk__in=query.identifiers)
        return public_validation.publication_query(query, document)

    initializer = textwrap.dedent(inspect.getsource(public_validation.PublicationContext.__init__))
    before = 'publication_query(query, self.document)'
    assert initializer.count(before) == 1
    initializer = initializer.replace(before, 'resolved(query, self.document)')
    namespace = {**vars(public_validation), 'resolved': resolved}
    exec(compile(initializer, '<owned-page-template-context>', 'exec'), namespace)
    context = type('PageTemplateContext', (public_validation.PublicationContext,),
                   {'__init__': namespace['__init__']})
    source = textwrap.dedent(inspect.getsource(publication_state._state_page))
    for name in ('batch_ids', 'selected'):
        original = f'Listing.objects.filter(pk__in={name}), page_read=True, prepared_page=True'
        assert source.count(original) == 1
        source = source.replace(original, f'PageSeed(tuple({name})), page_read=True, prepared_page=True')
    namespace = {**vars(publication_state), 'PublicationContext': context, 'PageSeed': PageSeed}
    exec(compile(source, '<owned-page-query-template>', 'exec'), namespace)
    return namespace['_state_page'], template, retained
