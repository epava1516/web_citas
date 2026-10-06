"""Shared public response text checks; grants no access or closure authority."""

import re

from django.core.exceptions import ValidationError


def checked_response_text(reason, response, redaction_confirmed):
    if (
        not isinstance(reason, str)
        or not isinstance(response, str)
        or not 20 <= len(reason.strip()) <= 2000
        or not 50 <= len(response.strip()) <= 4000
        or redaction_confirmed is not True
    ):
        raise ValidationError(
            "Motivated reviewed response required / Respuesta motivada y revisada obligatoria"
        )
    if re.search(r"https?://|www\.|[\w.+-]+@[\w.-]+|(?:\d[\s().+-]*){7}", response, re.I):
        raise ValidationError(
            "Remove contact details and external references / Retira contactos y referencias externas"
        )
    return response
