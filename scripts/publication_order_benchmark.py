"""Frozen ordering reference for sequential synthetic TCP diagnostics only."""
import hashlib
from pathlib import Path

from django.conf import settings
from django.db import connection

from apps.listings import publication_state


def compatible_order_reference(reference):
    """Keep the frozen five-argument reference intact after the snapshot guard."""
    def call(query, number, checked, observation, stale, *, trusted_snapshot=False):
        return reference(query, number, checked, observation, stale)
    return call


class OrderVariantMiddleware:
    def __init__(self, get_response):
        if not connection.settings_dict['NAME'].startswith('test_promotion_gate_'):
            raise RuntimeError('Own synthetic database required')
        source = Path(settings.PUBLICATION_ORDER_REFERENCE).read_bytes()
        if hashlib.sha256(source).hexdigest() != settings.PUBLICATION_ORDER_REFERENCE_SHA256:
            raise RuntimeError('Frozen reference digest mismatch')
        namespace = vars(publication_state).copy()
        exec(compile(source, settings.PUBLICATION_ORDER_REFERENCE, 'exec'), namespace)
        self.variants = {'before':compatible_order_reference(namespace['_ordered_reference']), 'after':publication_state._state_page}
        self.get_response = get_response

    def __call__(self, request):
        variant = request.headers.get('X-Order-Variant')
        if variant not in self.variants:
            return self.get_response(request)
        # Only the opted-in own four sync workers use this middleware. Each restores
        # its function before serving another request; no source or rule mutation.
        request.META["_publication_order_variant"] = variant
        previous = publication_state._state_page
        publication_state._state_page = self.variants[variant]
        try:
            return self.get_response(request)
        finally:
            publication_state._state_page = previous
