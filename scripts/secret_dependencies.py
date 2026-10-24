"""Static direct HMAC producer inventory; no settings imports or runtime values."""
import ast
import hashlib
import json
from pathlib import Path

HMAC_RULES = {
    ('apps/core/accounts.py', 'limited', 'rate-window'): ('RateWindow.key', 'rate_limits_change_namespace'),
    ('apps/core/accounts.py', 'token_user_state', 'account-token-state'): ('AccountToken.user_state', 'revoke_and_reissue_live_account_tokens'),
    ('apps/core/mfa.py', 'recovery_digest', 'mfa-recovery'): ('RecoveryCode.digest', 'reissue_recovery_codes_after_fresh_mfa'),
    ('apps/core/verification.py', 'phone_start', 'phone-otp'): ('PhoneChallenge.digest', 'restart_pending_phone_challenges'),
    ('apps/core/verification.py', 'phone_confirm', 'phone-otp'): ('PhoneChallenge.digest', 'restart_pending_phone_challenges'),
    ('apps/catalog/promotion_orders.py', 'synthetic_signature', 'promotion-synthetic-event-v1'): ('synthetic_payment_signature', 'do_not_accept_old_synthetic_events'),
    ('apps/safety/crypto.py', 'digest', 'safety-report-v1'): ('domain_receipts_and_audit_digests', 'inventory_transitive_consumers_before_rotation'),
    ('apps/safety/rights.py', 'fingerprint', 'rights-request-v1'): ('rights_approvals_bindings_and_evidence', 'no_blind_rehash_of_immutable_evidence'),
}


class DependencyInventoryError(Exception):
    pass


def inventory(root, rules=None):
    root = Path(root)
    rules = HMAC_RULES if rules is None else rules
    rows, seen, hashes = [], set(), {}
    for path in sorted((root / 'apps').rglob('*.py')):
        if 'migrations' in path.relative_to(root).parts:
            continue
        tree = ast.parse(path.read_text())
        aliases = {'salted_hmac'}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'django.utils.crypto':
                aliases.update(n.asname or n.name for n in node.names if n.name == 'salted_hmac')
        relative = path.relative_to(root).as_posix()
        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.owners = []
            def visit_FunctionDef(self, node):
                self.owners.append(node.name)
                self.generic_visit(node)
                self.owners.pop()
            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            def visit_Call(self, node):
                fn = node.func
                hmac = ((isinstance(fn, ast.Name) and fn.id in aliases)
                        or (isinstance(fn, ast.Attribute) and fn.attr == 'salted_hmac'))
                if hmac:
                    if not node.args or not isinstance(node.args[0], ast.Constant) or type(node.args[0].value) is not str:
                        raise DependencyInventoryError('Unclassified HMAC producer')
                    key = relative, '.'.join(self.owners), node.args[0].value
                    domain_key = key[0:2] in {('apps/safety/crypto.py', 'digest'), ('apps/safety/rights.py', 'fingerprint')}
                    secrets = [k.value for k in node.keywords if k.arg == 'secret']
                    explicit_domain = (domain_key and len(secrets) == 1 and isinstance(secrets[0], ast.Call)
                                       and isinstance(secrets[0].func, ast.Name)
                                       and secrets[0].func.id == 'domain_signing_key'
                                       and not secrets[0].args and not secrets[0].keywords)
                    if key not in rules or key in seen or (secrets and not explicit_domain) or (domain_key and not explicit_domain):
                        raise DependencyInventoryError('Unclassified HMAC producer')
                    seen.add(key)
                    target, response = rules[key]
                    rows.append({'source': relative, 'line': node.lineno, 'producer': key[1],
                                 'purpose': key[2], 'key_family': 'SAFETY_HMAC_KEY_or_legacy_DJANGO_SECRET_KEY' if explicit_domain else 'DJANGO_SECRET_KEY',
                                 'stored_or_derived_scope': target, 'response': response})
                    hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
                self.generic_visit(node)
        Visitor().visit(tree)
    provider = root / 'apps/core/domain_signing.py'
    if any(row['key_family'].startswith('SAFETY_HMAC_KEY') for row in rows):
        if not provider.is_file():
            raise DependencyInventoryError('Domain HMAC key provider missing')
        hashes['apps/core/domain_signing.py'] = hashlib.sha256(provider.read_bytes()).hexdigest()
    if seen != set(rules):
        raise DependencyInventoryError('HMAC registry differs from source producers')
    return {'schema_version': 1, 'scope': 'direct_application_hmac_producers_only',
            'retirement_authorized': False, 'producers': rows, 'source_sha256': hashes,
            'unmeasured': ['Django and third-party signing internals',
                           'Complete transitive domain-consumer and historical-data census']}


if __name__ == '__main__':
    print(json.dumps(inventory(Path(__file__).resolve().parents[1]), sort_keys=True))
