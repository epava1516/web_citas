"""Symmetric source-only original/candidate aliases on owned sync workers."""
import ast
import inspect
import sys
from contextlib import ExitStack, contextmanager
from functools import lru_cache
from unittest.mock import patch


def original_tree():
    from apps.safety import rights_exports
    tree = ast.parse(inspect.getsource(rights_exports.source_copy))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'defer']
    assert len(calls) == 1 and calls[0].args[0].value == 'search_document'
    calls[0].args = [ast.Constant('search_document')]
    ast.fix_missing_locations(tree)
    return tree


@lru_cache(maxsize=1)
def original_source():
    from apps.safety import rights_exports
    tree = original_tree()
    namespace = dict(vars(rights_exports))
    exec(compile(tree, '<original-source-projection>', 'exec'), namespace)
    return namespace['source_copy']


@contextmanager
def variant(mode):
    from apps.safety import rights_exports
    assert mode in {'original', 'deferred'}
    target = rights_exports.source_copy
    baseline = original_source()
    replacement = baseline if mode == 'original' else target
    aliases = [(module, attr) for name, module in tuple(sys.modules.items())
               if name.startswith('apps.safety.') and module is not None
               for attr, value in tuple(vars(module).items()) if value is target]
    try:
        with ExitStack() as restore:
            for module, attr in aliases:
                restore.enter_context(patch.object(module, attr, replacement))
            yield
    finally:
        for name, module in tuple(sys.modules.items()):
            if name.startswith('apps.safety.') and module is not None:
                for attr, value in tuple(vars(module).items()):
                    if replacement is not target and value is replacement:
                        setattr(module, attr, target)
