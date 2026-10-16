"""Test-only generic planning in new-detail hydration, using existing GUC queries."""
import inspect
import textwrap
from contextvars import ContextVar

from apps.listings import moderation_views, public_validation

_ACTIVE = ContextVar('owned_detail_generic', default=False)


def generic_active():
    return _ACTIVE.get()


def build_scoped_generic_context(counters=None, original=None):
    original = original or moderation_views.PublicationContext
    counters = counters if counters is not None else {'calls': 0}

    def context(*args, **kwargs):
        counters['calls'] += 1
        token = _ACTIVE.set(True)
        try:
            return original(*args, **kwargs)
        finally:
            _ACTIVE.reset(token)

    return context


def build_generic_reader():
    native = public_validation.read_publication_values
    source = textwrap.dedent(inspect.getsource(native))
    replacements = [
        ('cursor.execute("SELECT current_setting(\'jit\'), current_setting(\'join_collapse_limit\')")',
         'cursor.execute("SELECT current_setting(\'jit\'), current_setting(\'join_collapse_limit\'), "\n'
         '                               "current_setting(\'plan_cache_mode\')")'),
        ('previous, previous_joins = cursor.fetchone()',
         'previous, previous_joins, previous_plan = cursor.fetchone()'),
        ('cursor.execute("SELECT set_config(\'jit\', \'off\', true), set_config(\'join_collapse_limit\', \'1\', true)")',
         'cursor.execute("SELECT set_config(\'jit\', \'off\', true), "\n'
         '                               "set_config(\'join_collapse_limit\', \'1\', true), "\n'
         '                               "set_config(\'plan_cache_mode\', \'force_generic_plan\', true)")'),
        ('cursor.execute("SELECT set_config(\'jit\', %s, true), set_config(\'join_collapse_limit\', %s, true)",\n'
         '                               [previous, previous_joins])',
         'cursor.execute("SELECT set_config(\'jit\', %s, true), "\n'
         '                               "set_config(\'join_collapse_limit\', %s, true), "\n'
         '                               "set_config(\'plan_cache_mode\', %s, true)",\n'
         '                               [previous, previous_joins, previous_plan])'),
    ]
    for before, after in replacements:
        assert source.count(before) == 1, before
        source = source.replace(before, after)
    namespace = vars(public_validation).copy()
    exec(compile(source, '<owned-detail-generic-reader>', 'exec'), namespace)
    compiled = namespace['read_publication_values']

    def read(query, *, bounded_joins=False, prepared_page=False):
        implementation = compiled if _ACTIVE.get() and bounded_joins and prepared_page else native
        return implementation(query, bounded_joins=bounded_joins, prepared_page=prepared_page)

    return read
