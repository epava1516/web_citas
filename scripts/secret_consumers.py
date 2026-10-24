"""Resolved static HMAC call closure; never a key retirement authorization."""
import ast
import hashlib
import importlib.util
import json
from collections import defaultdict, deque
from pathlib import Path

ROOTS = ('apps.safety.crypto.digest', 'apps.safety.rights.fingerprint')


class Bindings(ast.NodeVisitor):
    def __init__(self, package):
        self.package, self.imports, self.shadowed = package, {}, set()

    def bind(self, name, target):
        if name in self.imports and self.imports[name] != target:
            self.imports[name] = None
        else:
            self.imports[name] = target

    def visit_ImportFrom(self, node):
        module = importlib.util.resolve_name('.' * node.level + (node.module or ''), self.package) if node.level else node.module
        for item in node.names:
            if item.name != '*':
                self.bind(item.asname or item.name, module + '.' + item.name)

    def visit_Import(self, node):
        for item in node.names:
            self.bind(item.asname or item.name.split('.')[0], item.name if item.asname else item.name.split('.')[0])

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.shadowed.add(node.id)

    def visit_FunctionDef(self, node):
        self.shadowed.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


class BodyCalls(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


def inventory(root, roots=ROOTS):
    root = Path(root)
    modules, functions, hashes = {}, {}, {}
    for path in sorted((root / 'apps').rglob('*.py')):
        relative = path.relative_to(root)
        if 'migrations' in relative.parts:
            continue
        module = '.'.join(relative.with_suffix('').parts)
        if module.endswith('.__init__'):
            module = module.removesuffix('.__init__')
            package = module
        else:
            package = module.rsplit('.', 1)[0]
        body = ast.parse(path.read_text(encoding='utf-8')).body
        bindings = Bindings(package)
        for node in body:
            bindings.visit(node)
        modules[module] = bindings
        hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

        def collect(nodes, owners=(), inherited=None):
            inherited = inherited or {}
            for node in nodes:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    qualified = module + '.' + '.'.join((*owners, node.name))
                    local = Bindings(package)
                    for child in node.body:
                        local.visit(child)
                    imports = {**inherited, **local.imports}
                    if not isinstance(node, ast.ClassDef):
                        params = {a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
                        params.update(a.arg for a in (node.args.vararg, node.args.kwarg) if a)
                        functions[qualified] = (module, relative.as_posix(), node, imports, local.shadowed | params, owners)
                    collect(node.body, (*owners, node.name), imports)
                else:
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            collect([child], owners, inherited)
        collect(body)
    if not set(roots) <= functions.keys():
        raise ValueError('HMAC consumer roots missing from source')

    def imported(target, seen=()):
        if not target or target in seen:
            return None
        if target in functions:
            return target
        parent, _, name = target.rpartition('.')
        if parent in modules and name not in modules[parent].shadowed:
            return imported(modules[parent].imports.get(name), (*seen, target))
        return None

    reverse, unresolved = defaultdict(set), 0
    for caller, (module, _, node, imports, shadowed, owners) in functions.items():
        calls = BodyCalls()
        for child in node.body:
            calls.visit(child)
        for call in calls.calls:
            expression, suffix = call.func, []
            while isinstance(expression, ast.Attribute):
                suffix.insert(0, expression.attr)
                expression = expression.value
            resolved = None
            if isinstance(expression, ast.Name):
                name = expression.id
                if name not in shadowed:
                    target = imports.get(name, modules[module].imports.get(name) if name not in modules[module].shadowed else None)
                    if target:
                        resolved = imported('.'.join([target, *suffix]))
                    elif not suffix:
                        for size in range(len(owners), -1, -1):
                            candidate = '.'.join([module, *owners[:size], name])
                            if candidate in functions:
                                resolved = candidate
                                break
            if resolved:
                reverse[resolved].add(caller)
            else:
                unresolved += 1
    paths = defaultdict(dict)
    for seed in roots:
        pending, visited = deque([(seed, [seed])]), {seed}
        while pending:
            target, path = pending.popleft()
            for caller in sorted(reverse[target]):
                if caller in visited:
                    continue
                visited.add(caller)
                route = [caller, *path]
                paths[caller][seed] = route
                pending.append((caller, route))
    rows = []
    for caller, routes in sorted(paths.items()):
        _, source, node, _, _, _ = functions[caller]
        rows.append({'consumer': caller, 'source': source, 'line': node.lineno, 'resolved_paths': dict(routes)})
    return {'schema_version': 1, 'scope': 'resolved_static_application_function_calls',
            'roots': list(roots), 'consumers': rows, 'unresolved_call_sites': unresolved,
            'source_sha256': hashes, 'complete_transitive_coverage': False,
            'retirement_authorized': False,
            'unmeasured': ['dynamic dispatch, callbacks, assigned aliases and reflection',
                           'framework internals, module initializers and external packages',
                           'runtime branch reachability and persisted historical values',
                           'consumer-specific revocation, revalidation and retention classification']}


if __name__ == '__main__':
    print(json.dumps(inventory(Path(__file__).resolve().parents[1]), sort_keys=True))
