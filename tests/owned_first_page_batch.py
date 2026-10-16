"""Test-only batching of pending rows and a bounded clean first-page preview."""
import inspect
import textwrap

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F

from apps.listings import publication_state
from apps.listings.models import PublicationState


def build_first_page_batch_prototype(counters):
    def clean_preview(query, dirty):
        expires_after, text = query._publication_projection
        clean = PublicationState.objects.filter(
            eligible=True, rules_version=publication_state.rules_version(),
            expires_at__gt=expires_after,
        ).exclude(listing_id__in=dirty)
        if text:
            search = SearchQuery(text, config='spanish', search_type='websearch') | SearchQuery(
                text, config='english', search_type='websearch',
            )
            clean = clean.filter(search_document=search).annotate(
                relevance=SearchRank(F('search_document'), search),
            ).order_by('-relevance', '-published_at', 'listing_id')
        else:
            clean = clean.order_by('-published_at', 'listing_id')
        return list(clean.values_list('listing_id', flat=True)[:24])

    source = textwrap.dedent(inspect.getsource(publication_state._state_page))
    native = '''    native = []
    if unknown:
        context = PublicationContext(query.filter(pk__in=unknown), page_read=True)
'''
    assert source.count(native) == 1
    source = source.replace(native, '''    batch_context = None
    if (unknown and trusted_snapshot and coverage_current and number == 1 and not checked
            and getattr(query, "_publication_projection", None) is not None):
        from .public_validation import _prepared_page_binding

        preview = _owned_clean_preview(query, dirty)
        batch_ids = set(unknown) | set(preview)
        assert len(batch_ids) <= NATIVE_UNKNOWN_LIMIT + 24
        with _prepared_page_binding(enabled=True):
            batch_context = PublicationContext(
                Listing.objects.filter(pk__in=batch_ids), page_read=True, prepared_page=True,
            )
        _owned_batch_counts["batch_contexts"] += 1
        _owned_batch_counts["batch_sizes"].append(len(batch_ids))
    native = []
    if unknown:
        context = batch_context or PublicationContext(query.filter(pk__in=unknown), page_read=True)
''')
    validation = '            if publicly_visible(row, context=context) and matches(row.person, checked)\n'
    assert source.count(validation) == 1
    source = source.replace(validation, '            if row.pk in unknown and publicly_visible(row, context=context) and matches(row.person, checked)\n')
    hydration = '''    with _prepared_page_binding(enabled=True):
        context = PublicationContext(
            Listing.objects.filter(pk__in=selected), page_read=True, prepared_page=True,
        )
'''
    assert source.count(hydration) == 1
    source = source.replace(hydration, '''    if batch_context is not None and set(selected) <= {row.pk for row in batch_context.rows}:
        context = batch_context
        _owned_batch_counts["page_reuses"] += 1
    else:
        if batch_context is not None:
            _owned_batch_counts["missing_selected_fallbacks"] += 1
        with _prepared_page_binding(enabled=True):
            context = PublicationContext(
                Listing.objects.filter(pk__in=selected), page_read=True, prepared_page=True,
            )
''')
    namespace = vars(publication_state).copy()
    namespace.update(_owned_clean_preview=clean_preview, _owned_batch_counts=counters)
    exec(compile(source, '<owned-first-page-batch>', 'exec'), namespace)
    return namespace['_state_page']
