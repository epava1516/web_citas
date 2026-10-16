"""Test-only counters around the actual integrated first-page implementation."""
import inspect
import textwrap

from apps.listings import publication_state


def build_first_page_batch_prototype(counters):
    # Keep the historical entrypoint for existing controls. The executed source
    # is now the product function, with counters only; no second implementation.
    source = textwrap.dedent(inspect.getsource(publication_state._state_page))
    source = source.replace('_first_page_clean_preview', '_owned_clean_preview')
    construction = '''            batch_context = PublicationContext(
                Listing.objects.filter(pk__in=batch_ids), page_read=True, prepared_page=True,
            )
'''
    assert source.count(construction) == 1
    source = source.replace(construction, construction + '''        _owned_batch_counts["batch_contexts"] += 1
        _owned_batch_counts["batch_sizes"].append(len(batch_ids))
''')
    reuse = '        context = batch_context\n'
    assert source.count(reuse) == 1
    source = source.replace(reuse, reuse + '        _owned_batch_counts["page_reuses"] += 1\n')
    fallback = '''    else:
        # Retain native hydration'''
    assert source.count(fallback) == 1
    source = source.replace(fallback, '''    else:
        if batch_context is not None:
            _owned_batch_counts["missing_selected_fallbacks"] += 1
        # Retain native hydration''')
    namespace = vars(publication_state).copy()
    namespace.update(_owned_clean_preview=publication_state._first_page_clean_preview,
                     _owned_batch_counts=counters)
    exec(compile(source, '<owned-first-page-batch>', 'exec'), namespace)
    return namespace['_state_page']
