"""Public-detail-only preparation preserves the fresh native guard."""

import json
import re
from contextlib import nullcontext
from urllib.parse import quote, unquote

import pytest
from django.core import signing
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import moderation_views, public_validation
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible
from scripts.benchmark_owned_backend_cpu import statement_family
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def canonical_body(response, listing):
    if response.status_code == 404:
        return response.content
    body = response.content
    matches = list(re.finditer(rb'([?&]target=)([^&"]+)', body))
    assert len(matches) == 1
    decoded = signing.loads(unquote(matches[0].group(2).decode()),
                           salt='public-report-target-v1', max_age=7200)
    assert decoded == {'listing': str(listing.pk), 'revision': str(listing.approved_revision_id)}
    token = quote(json.dumps(decoded, sort_keys=True)).encode()
    return re.sub(rb'([?&]target=)([^&"]+)', lambda m: m.group(1) + token, body)


def test_prepared_detail_guard_parity_freshness_and_callsite_scope(request, monkeypatch):
    client = request.getfixturevalue('directory')
    dataset = populate(50)
    ids = dataset['sample_ids'][:2]
    connection.close()
    connection.ensure_connection()
    raw = connection.connection
    factory, threshold = raw.cursor_factory, raw.prepare_threshold
    guard_reads, outside_reads = [], []
    inside = False
    native_guard = moderation_views.publicly_visible

    def guard(listing):
        nonlocal inside
        inside = True
        try:
            return native_guard(listing)
        finally:
            inside = False

    def observe(execute, sql, params, many, context):
        if sql.lstrip().upper().startswith('SELECT'):
            prepared = isinstance(context['cursor'].cursor, public_validation._PageReadCursor)
            (guard_reads if inside else outside_reads).append((statement_family(sql), prepared))
        return execute(sql, params, many, context)

    monkeypatch.setattr(moderation_views, 'publicly_visible', guard)
    for index in range(14):
        with connection.execute_wrapper(observe):
            response = client.get(f"/{'es' if index % 2 else 'en'}/listing/{ids[index % 2]}/")
        assert response.status_code == 200
        assert raw.cursor_factory is factory and raw.prepare_threshold == threshold
    assert {'catalog', 'media', 'rights'} <= {family for family, _ in guard_reads}
    assert guard_reads and all(prepared for _, prepared in guard_reads)
    assert outside_reads and not any(prepared for _, prepared in outside_reads)
    with connection.cursor() as cursor:
        cursor.execute('SELECT count(*), COALESCE(sum(generic_plans),0) FROM pg_prepared_statements')
        count, generic = cursor.fetchone()
    assert count > 0 and generic > 0

    def compare(expected_status):
        for language in ('es', 'en'):
            for pk in ids:
                path = f'/{language}/listing/{pk}/'
                listing = Listing.objects.get(pk=pk)
                prepared = client.get(path)
                with monkeypatch.context() as patch:
                    patch.setattr(public_validation, '_prepared_page_binding', lambda **kwargs: nullcontext())
                    native = client.get(path)
                assert prepared.status_code == native.status_code == expected_status
                assert canonical_body(prepared, listing) == canonical_body(native, listing)
                if expected_status == 200:
                    assert prepared['Cache-Control'] == native['Cache-Control'] == 'no-store'
                assert raw.cursor_factory is factory and raw.prepare_threshold == threshold

    compare(200)
    listing = Listing.objects.get(pk=ids[0])
    category = listing.approved_revision.categories.first()
    type(category).objects.filter(pk=category.pk).update(active=False)
    compare(404)
    type(category).objects.filter(pk=category.pk).update(active=True)
    compare(200)
    blob = listing.approved_revision.photos.first().blob
    type(blob).objects.filter(pk=blob.pk).update(status='pending')
    compare(404)
    type(blob).objects.filter(pk=blob.pk).update(status='ready')
    compare(200)

    # The same native function outside the explicit view retains client binding.
    reads = []

    def direct(execute, sql, params, many, context):
        reads.append(isinstance(context['cursor'].cursor, public_validation._PageReadCursor))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(direct):
        assert publicly_visible(Listing.objects.get(pk=ids[0]))
    assert reads and not any(reads)
