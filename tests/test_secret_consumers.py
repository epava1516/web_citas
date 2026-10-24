"""Call closure witnesses and deliberate unresolved cases; no runtime secrets."""
from pathlib import Path

import pytest

from scripts.secret_consumers import inventory


def project(tmp_path, body, helper=''):
    folder = tmp_path / 'apps'
    folder.mkdir()
    (folder / '__init__.py').write_text('')
    (folder / 'root.py').write_text('def sign(value): return value\n' + helper)
    (folder / 'consumer.py').write_text(body)
    return inventory(tmp_path, roots=('apps.root.sign',))


def test_current_closure_contains_report_receipts_and_rights_operations():
    result = inventory(Path(__file__).resolve().parents[1])
    consumers = {row['consumer'] for row in result['consumers']}
    assert 'apps.safety.views.receipt' in consumers
    assert 'apps.safety.views.submit' in consumers
    assert any(name.startswith('apps.safety.rights_rectification.') for name in consumers)
    assert result['retirement_authorized'] is result['complete_transitive_coverage'] is False
    assert result['unresolved_call_sites'] > 0 and result['unmeasured']


@pytest.mark.parametrize('imports,call', [
    ('from .root import sign as signing', 'signing(value)'),
    ('from . import root as module', 'module.sign(value)'),
    ('import apps.root as module', 'module.sign(value)'),
])
def test_relative_module_and_named_aliases_are_resolved(tmp_path, imports, call):
    result = project(tmp_path, imports + '\ndef entry(value): return ' + call + '\n')
    assert result['consumers'][0]['resolved_paths']['apps.root.sign'] == ['apps.consumer.entry', 'apps.root.sign']


def test_wrapper_paths_and_cycles_are_finite(tmp_path):
    result = project(tmp_path, 'from .root import wrapper\ndef entry(x): return wrapper(x)\n',
                     'def wrapper(x):\n sign(x)\n return recursive(x)\ndef recursive(x): return wrapper(x)\n')
    rows = {r['consumer']: r for r in result['consumers']}
    assert rows['apps.consumer.entry']['resolved_paths']['apps.root.sign'] == [
        'apps.consumer.entry', 'apps.root.wrapper', 'apps.root.sign']
    assert len(rows) == 3


def test_parameter_shadowing_does_not_invent_a_crypto_call(tmp_path):
    result = project(tmp_path, 'from .root import sign\ndef entry(sign): return sign("x")\n')
    assert result['consumers'] == [] and result['unresolved_call_sites'] == 1


def test_assigned_alias_is_explicitly_outside_supported_resolution(tmp_path):
    result = project(tmp_path, 'from .root import sign\ndef entry(x):\n alias=sign\n return alias(x)\n')
    assert result['consumers'] == [] and not result['complete_transitive_coverage']


def test_missing_root_is_not_silently_a_success(tmp_path):
    (tmp_path / 'apps').mkdir()
    with pytest.raises(ValueError, match='roots missing'):
        inventory(tmp_path, roots=('apps.missing.sign',))


def test_module_rebinding_does_not_invent_a_crypto_dependency(tmp_path):
    result = project(tmp_path, 'from .root import sign\nsign=lambda x:x\ndef entry(x): return sign(x)\n')
    assert result['consumers'] == []


def test_reexport_is_followed_without_importing_project_code(tmp_path):
    project(tmp_path, 'from .bridge import forwarded\ndef entry(x): return forwarded(x)\n')
    (tmp_path / 'apps' / 'bridge.py').write_text(
        'from .root import sign as forwarded\nraise RuntimeError("never execute inventory input")\n')
    result = inventory(tmp_path, roots=('apps.root.sign',))
    assert result['consumers'][0]['consumer'] == 'apps.consumer.entry'


def test_inventory_does_not_emit_source_literals(tmp_path):
    import json
    result = project(tmp_path, 'from .root import sign\ndef entry(): return sign("synthetic-hidden-value-2387")\n')
    assert 'synthetic-hidden-value-2387' not in json.dumps(result)
