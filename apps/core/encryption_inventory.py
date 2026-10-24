"""Bounded private DB cipher census; never a key-retirement authorization."""
from cryptography.fernet import Fernet, InvalidToken
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError, connection, transaction
from django.db.models import Count, Func, IntegerField, Q
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.safety import crypto
from apps.safety.object_storage.repository import PREFIX

from . import mfa
from .encryption import encryption_cipher
from .encryption_inventory_registry import ENCRYPTED_COLUMNS

MAX_CIPHER_BYTES = 256 * 1024
CONFIGURATION = ('SECRET_KEY', 'PRODUCTION', 'SAFETY_ENCRYPTION_KEY',
                 'SAFETY_ENCRYPTION_KEY_FALLBACKS', 'MFA_ENCRYPTION_KEY', 'MFA_ENCRYPTION_KEY_FALLBACKS')
EXTERNAL_SCOPES = ('object_bytes_and_tombstones', 'retained_log_and_redis_origins',
                   'backups', 'external_recovery_ledger')


class InventoryUnavailable(Exception):
    """Sanitized administrative diagnostic, with no partial report."""


def checked_registry():
    observed = set()
    for model in apps.get_models():
        for field in model._meta.concrete_fields:
            if field.name.startswith('encrypted_') or field.name.endswith('_encrypted'):
                observed.add((model._meta.app_label, model.__name__, field.name))
    declared = [(app, model, field) for app, model, field, _, _ in ENCRYPTED_COLUMNS]
    if len(set(declared)) != len(declared) or set(declared) != observed:
        raise InventoryUnavailable('Encrypted column registry differs from current schema')
    return ENCRYPTED_COLUMNS


@sensitive_variables()
def _readers():
    readers = {}
    for family, factory in (('safety', crypto.cipher), ('mfa', mfa.cipher)):
        configured = factory()  # Validate complete configuration, including dev restrictions.
        name = family.upper() + '_ENCRYPTION_KEY'
        active = getattr(settings, name)
        previous = getattr(settings, name + '_FALLBACKS')
        primary = encryption_cipher(active) if active else configured
        readers[family] = [('active', primary)] + [
            (f'previous_{index}', Fernet(value.strip().encode('ascii')))
            for index, value in enumerate(previous.split(',') if previous else [], 1)]
    return readers


@sensitive_variables()
def _classify(value, readers, encoding):
    if type(value) is not str:
        return 'unreadable'
    if encoding == 'fernet_or_object_reference' and value.startswith(PREFIX):
        value = value[len(PREFIX):]
    try:
        token = value.encode('ascii')
    except UnicodeError:
        return 'unreadable'
    for label, cipher in readers:
        try:
            cipher.decrypt(token)
        except InvalidToken:
            continue
        return label
    return 'unreadable'


@sensitive_variables()
def collect_inventory(max_cells=1000):
    if type(max_cells) is not int or not 1 <= max_cells <= 10000:
        raise InventoryUnavailable('Cell budget must be between1and10000')
    if connection.vendor != 'postgresql' or connection.in_atomic_block:
        raise InventoryUnavailable('Key inventory requires its own PostgreSQL transaction')
    registry = checked_registry()
    initial = tuple(getattr(settings, name) for name in CONFIGURATION)
    try:
        if not connection.get_autocommit():
            raise InventoryUnavailable('Key inventory requires autocommit on entry')
        readers = _readers()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            remaining = max_cells
            fields = []
            totals = dict(nonempty=0, sampled=0, active=0, previous=0, unreadable=0,
                          oversized_unmeasured=0, not_sampled=0)
            for app, model, field, family, encoding in registry:
                if family not in readers or encoding not in ('fernet', 'fernet_or_object_reference'):
                    raise InventoryUnavailable('Encrypted column classification is invalid')
                query = apps.get_model(app, model)._base_manager.using(connection.alias).exclude(
                    Q(**{field: ''}) | Q(**{field + '__isnull': True})).annotate(
                        _cipher_bytes=Func(field, function='OCTET_LENGTH', output_field=IntegerField()))
                counts = query.aggregate(nonempty=Count('pk'), oversized=Count(
                    'pk', filter=Q(_cipher_bytes__gt=MAX_CIPHER_BYTES)))
                roles = {label: 0 for label, _ in readers[family]}
                roles['unreadable'] = 0
                if remaining and counts['nonempty'] > counts['oversized']:
                    for value in query.filter(_cipher_bytes__lte=MAX_CIPHER_BYTES).order_by('pk').values_list(
                            field, flat=True)[:remaining].iterator(chunk_size=50):
                        roles[_classify(value, readers[family], encoding)] += 1
                        remaining -= 1
                sampled = sum(roles.values())
                unscanned = counts['nonempty'] - counts['oversized'] - sampled
                fields.append({'model': app + '.' + model, 'field': field, 'key_family': family,
                               'encoding': encoding, 'nonempty': counts['nonempty'], 'sampled': sampled,
                               'roles': roles, 'oversized_unmeasured': counts['oversized'], 'not_sampled': unscanned})
                totals['nonempty'] += counts['nonempty']
                totals['sampled'] += sampled
                totals['active'] += roles['active']
                totals['previous'] += sum(n for label, n in roles.items() if label.startswith('previous_'))
                totals['unreadable'] += roles['unreadable']
                totals['oversized_unmeasured'] += counts['oversized']
                totals['not_sampled'] += unscanned
            # This JSON contains independently encrypted ledger records, not safety Fernet values.
            opaque = apps.get_model('safety', 'RecoveryOutbox')._base_manager.using(connection.alias).filter(encoded_record__isnull=False).count()
            if tuple(getattr(settings, name) for name in CONFIGURATION) != initial:
                raise InventoryUnavailable('Encryption configuration changed during inventory')
            return {'schema_version': 1, 'sampled_at': timezone.now().isoformat(),
                    'scope': 'current_database_encrypted_columns_only', 'retirement_authorized': False,
                    'cell_budget': max_cells, 'max_cipher_bytes': MAX_CIPHER_BYTES,
                    'database_scan_complete': not (totals['not_sampled'] or totals['oversized_unmeasured']),
                    'totals': totals, 'fields': fields,
                    'opaque_independent_ledger_records': opaque, 'external_scopes_unmeasured': list(EXTERNAL_SCOPES),
                    'limits': ['No keys, ciphertext, plaintext or row identifiers exported',
                               'Decryption success does not establish domain authority or semantic validity',
                               'Previous slots refer only to the configuration used for this invocation',
                               'Zero previous-key cells does not authorize retirement; external retention is unmeasured']}
    except (DatabaseError, ImproperlyConfigured):
        raise InventoryUnavailable('Key inventory could not read its configured scope') from None
