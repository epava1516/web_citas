"""Optional pinned domain HMAC key; empty retains exact legacy signing semantics."""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.debug import sensitive_variables


@sensitive_variables()
def validate_domain_key(value):
    if type(value) is not str or (value and (len(value) < 50 or value.isspace())):
        raise ImproperlyConfigured('Domain HMAC key must be empty or an explicit strong string')
    return value


@sensitive_variables()
def domain_signing_key():
    return validate_domain_key(getattr(settings, 'SAFETY_HMAC_KEY', '')) or settings.SECRET_KEY
