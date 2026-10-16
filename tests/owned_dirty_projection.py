"""Test-only exact union of clean projection and freshly validated dirty rows."""
import inspect
import textwrap

from apps.listings import publication_state


def build_dirty_projection_prototype():
    source = textwrap.dedent(inspect.getsource(publication_state._state_page))
    condition = 'projected = trusted_snapshot and complete and not checked and projection is not None'
    assert source.count(condition) == 1
    source = source.replace(condition, 'projected = trusted_snapshot and coverage_current and not checked and projection is not None')
    selection = '        page = Paginator(population.values_list("listing_id", flat=True), 24).page(number)\n'
    assert source.count(selection) == 1
    source = source.replace(selection, '''        if dirty:
            population = population.exclude(listing_id__in=dirty)
        if native:
            # Dirty rows were fully validated above from this same RR snapshot.
            # Their current source values supply ordering/search, never stale copies.
            state_columns = ["listing_id", "published_at"]
            native_columns = ["pk", "published_at"]
            ordering = ["-published_at", "listing_id"]
            if text:
                state_columns.append("relevance")
                native_columns.append("relevance")
                ordering.insert(0, "-relevance")
            clean_rows = population.order_by().values_list(*state_columns)
            native_rows = query.filter(pk__in=native).select_related(None).order_by().values_list(*native_columns)
            population = clean_rows.union(native_rows, all=True).order_by(*ordering)
            page = Paginator(population, 24).page(number)
            page.object_list = [row[0] for row in page.object_list]
        else:
            page = Paginator(population.values_list("listing_id", flat=True), 24).page(number)
''')
    namespace = vars(publication_state).copy()
    exec(compile(source, '<owned-dirty-projection>', 'exec'), namespace)
    return namespace['_state_page']
