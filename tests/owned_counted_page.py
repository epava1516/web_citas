"""Test-only exact first-page count window; product population and guard unchanged."""
import inspect
import textwrap

from django.db.models import Count, Window

from apps.listings import publication_state


def build_counted_page_prototype(counters=None):
    counters = counters if counters is not None else {'windows': 0}
    source = textwrap.dedent(inspect.getsource(publication_state._state_page))
    before = '''    else:
        page = Paginator(population.values_list("pk", flat=True), 24).page(number)
    selected = list(page.object_list)
'''
    after = '''    else:
        if (trusted_snapshot and coverage_current and number == 1 and not checked
                and projection is not None and not multiplies_rows(population)):
            pairs = list(population.annotate(_owned_total=_owned_Window(_owned_Count("*")))
                         .values_list("pk", "_owned_total")[:24])
            paginator = Paginator([pk for pk, total in pairs], 24)
            paginator.count = pairs[0][1] if pairs else 0
            page = paginator.page(number)
            _owned_counters["windows"] += 1
        else:
            page = Paginator(population.values_list("pk", flat=True), 24).page(number)
    selected = list(page.object_list)
'''
    assert source.count(before) == 1
    namespace = vars(publication_state).copy()
    namespace.update(_owned_Count=Count, _owned_Window=Window, _owned_counters=counters)
    exec(compile(source.replace(before, after), '<owned-counted-page>', 'exec'), namespace)
    return namespace['_state_page']
