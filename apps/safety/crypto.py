import base64
import hashlib
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables

from apps.core.domain_signing import domain_signing_key
from apps.core.encryption import encryption_cipher


def cipher():
    key = settings.SAFETY_ENCRYPTION_KEY
    if not key:
        if settings.SAFETY_ENCRYPTION_KEY_FALLBACKS:
            raise ImproperlyConfigured("Explicit active encryption key required with fallbacks")
        if settings.PRODUCTION:
            raise ValueError("Safety encryption key required")
        key = base64.urlsafe_b64encode(
            hashlib.sha256((settings.SECRET_KEY + ":dev-safety-v1").encode()).digest()
        )
    return encryption_cipher(key, settings.SAFETY_ENCRYPTION_KEY_FALLBACKS)


@sensitive_variables()
def seal(payload):
    return (
        cipher().encrypt(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).decode()
    )


def digest(value):
    return salted_hmac("safety-report-v1", value, algorithm="sha256", secret=domain_signing_key()).hexdigest()


@sensitive_variables()
def unseal(payload):
    return json.loads(cipher().decrypt(payload.encode()).decode())
