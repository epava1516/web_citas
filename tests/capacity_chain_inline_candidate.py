"""Rejected read-side candidate, kept only for exact reproducible diagnostics."""
import ast
import inspect
import sys
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

_UTC_FORMAT = 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
_SOURCE_HASH_SQL = (
    "pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
    "pg_catalog.jsonb_set(pg_catalog.to_jsonb(s),'{created_at}',"
    "pg_catalog.to_jsonb(pg_catalog.to_char(s.created_at AT TIME ZONE 'UTC',"
    f"'{_UTC_FORMAT}')))::text,'UTF8')),'hex')"
)
_EVENT_LINK_SQL = (
    "pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
    "pg_catalog.jsonb_build_array('rights-evidence-chain-v1',request_id::text,"
    "sequence,kind,source_table,source_pk,payload_digest,previous_digest,"
    f"pg_catalog.to_char(created_at AT TIME ZONE 'UTC','{_UTC_FORMAT}'))"
    "::text,'UTF8')),'hex')"
)




def candidate_functions():
    from apps.safety import evidence_chain as chain

    class Inline(ast.NodeTransformer):
        def __init__(self):
            self.replaced = 0

        def visit_Name(self, node):
            if node.id == 'EVENT_QUERY':
                from apps.safety.evidence_chain_sql_v1 import EVENT
                self.replaced += 1
                return ast.copy_location(ast.Constant(
                    'SELECT sequence,kind,source_table,source_pk,payload_digest,'
                    'previous_digest,digest,created_at,' + _EVENT_LINK_SQL +
                    f' FROM public."{EVENT}" WHERE request_id=%s ORDER BY sequence'), node)
            return node

    namespace = vars(chain).copy()
    for function in (chain.validate_chain.__wrapped__,):
        tree = ast.parse(inspect.getsource(function))
        transform = Inline()
        transform.visit(tree)
        assert transform.replaced == 1, 'Original reader changed; review candidate explicitly'
        exec(compile(ast.fix_missing_locations(tree), '<test-only-inline-reader>', 'exec'), namespace)
    def source_statements(request):
        from apps.safety.evidence_chain_sql_v1 import TABLES
        return [(f'SELECT s.id::text,{_SOURCE_HASH_SQL} FROM public."{table}" s '
                 'JOIN public.safety_rightsaction a ON a.id=s.action_id WHERE a.request_id=%s',
                 [request]) for table in TABLES]
    return source_statements, namespace['validate_chain']


@contextmanager
def scope():
    from apps.safety import evidence_chain as chain

    source, validate = candidate_functions()
    original_validate = chain.validate_chain
    with ExitStack() as stack:
        # Patch builders/functions, never driver SQL or transaction boundaries.
        stack.enter_context(patch.object(chain, '_source_statements', source))
        for module_name, module in list(sys.modules.items()):
            if module_name.startswith('apps.') and getattr(module, 'validate_chain', None) is original_validate:
                stack.enter_context(patch.object(module, 'validate_chain', validate))
        yield
