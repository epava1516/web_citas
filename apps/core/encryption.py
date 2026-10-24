"""Bounded Fernet transition: encrypt with active key, read retained predecessors."""
from cryptography.fernet import Fernet, MultiFernet
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.debug import sensitive_variables

MAX_PREVIOUS_KEYS = 3


@sensitive_variables()
def encryption_cipher(active_key, previous_keys=''):
    """No caching, network, plaintext migration, implicit retirement or key logging."""
    try:
        if type(previous_keys) is not str or type(active_key) not in (str, bytes):
            raise ValueError
        previous = [key.strip() for key in previous_keys.split(',')] if previous_keys else []
        if len(previous) > MAX_PREVIOUS_KEYS:
            raise ValueError
        active = active_key.encode('ascii') if type(active_key) is str else active_key
        encoded = [active, *(key.encode('ascii') for key in previous)]
        if len(set(encoded)) != len(encoded):
            raise ValueError
        readers = [Fernet(key) for key in encoded]
    except (TypeError, ValueError, UnicodeError):
        raise ImproperlyConfigured('Invalid encryption key configuration') from None
    return readers[0] if len(readers) == 1 else MultiFernet(readers)
