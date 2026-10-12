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

    replacements = {
        'public.rights_evidence_row_hash(to_jsonb(s))': _SOURCE_HASH_SQL,
        'public.rights_evidence_link(request_id,sequence,kind,source_table,source_pk,\n'
        '                                      payload_digest,previous_digest,created_at)': _EVENT_LINK_SQL,
    }
    class Inline(ast.NodeTransformer):
        def __init__(self):
            self.replaced = 0

        def visit_Constant(self, node):
            if isinstance(node.value, str):
                for old, new in replacements.items():
                    if old in node.value:
                        node.value = node.value.replace(old, new)
                        self.replaced += 1
            return node
    namespace = vars(chain).copy()
    for function in (chain._source_statements, chain.validate_chain.__wrapped__):
        tree = ast.parse(inspect.getsource(function))
        transform = Inline()
        transform.visit(tree)
        assert transform.replaced == 1, 'Original reader changed; review candidate explicitly'
        exec(compile(ast.fix_missing_locations(tree), '<test-only-inline-reader>', 'exec'), namespace)
    return namespace['_source_statements'], namespace['validate_chain']


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
