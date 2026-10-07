"""Finite query-growth diagnosis of the unchanged discovery HTTP path."""

import re
import time
from collections import Counter

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('count', [10, 100])
def test_discovery_full_visibility_query_growth(request, record_property, count):
    client = request.getfixturevalue('directory')
    populate(count)
    tables = Counter()
    queries = 0

    def counter(execute, sql, params, many, context):
        nonlocal queries
        queries += 1
        for table in re.findall(r'(?:FROM|JOIN)\s+"([a-z_]+)"', sql):
            tables[table] += 1
        return execute(sql, params, many, context)

    started = time.perf_counter()
    with connection.execute_wrapper(counter):
        response = client.get('/es/')
    elapsed = time.perf_counter()-started
    assert response.status_code == 200
    page = response.context['page']
    assert page.paginator.count == count and len(page.object_list) == min(count, 24)
    assert response['Cache-Control'] == 'no-store'
    record_property('dataset_published', count)
    record_property('http_status', response.status_code)
    record_property('http_seconds_instrumented', elapsed)
    record_property('sql_queries', queries)
    record_property('table_query_counts', repr(dict(tables)))
    record_property('scope', 'Django HTTP Client same view/real PostgreSQL; query-growth diagnosis, not TCP/Gunicorn load/p95/capacity. No SQL values logged.')
