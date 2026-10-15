"""Exact shared count/page behavior at empty and out-of-range search boundaries."""

import pytest
from django.db import connection
from test_discovery import directory, multipage_directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state

pytestmark = pytest.mark.django_db(transaction=True)


def test_shared_search_count_matches_native_pages_and_empty_ranges(request, monkeypatch):
    client = request.getfixturevalue("multipage_directory")
    while publication_state.refresh(500):
        pass
    for query, page, status, count in [
        ("pagination", "1", 200, 25),
        ("pagination", "2", 200, 25),
        ("pagination", "3", 404, None),
        ("noexistingmatchingtoken", "1", 200, 0),
        ("noexistingmatchingtoken", "2", 404, None),
    ]:
        statements = []

        def capture(execute, sql, params, many, context):
            if '"listings_publicationstate"' in sql and '"eligible"' in sql:
                statements.append(sql)
            return execute(sql, params, many, context)

        with connection.execute_wrapper(capture):
            actual = client.get("/en/", {"q": query, "page": page})
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
            native = client.get("/en/", {"q": query, "page": page})
        assert actual.status_code == native.status_code == status
        assert actual.content == native.content
        assert actual.get("Cache-Control") == native.get("Cache-Control")
        assert any("COUNT(*) OVER ()" in sql for sql in statements)
        if status == 200:
            assert actual["Cache-Control"] == "no-store"
            assert actual.context["page"].paginator.count == count
            assert len(statements) == 1  # Exact count and selected IDs share one query.
