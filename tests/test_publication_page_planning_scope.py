"""Request-local planner settings restore across success and database rollback."""
import pytest
from django.db import DatabaseError, connection, transaction
from django.db.models.expressions import RawSQL
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings.discovery import candidates
from apps.listings.public_validation import PublicationContext, read_publication_values

pytestmark = pytest.mark.django_db(transaction=True)


def settings_now():
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('jit'), current_setting('join_collapse_limit')")
        return cursor.fetchone()


@pytest.mark.parametrize("failure", [False, True])
def test_page_planning_policy_restores_enclosing_transaction(request, failure):
    request.getfixturevalue("directory")
    initial = settings_now()
    raw = connection.connection
    previous_factory, previous_threshold = raw.cursor_factory, raw.prepare_threshold
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL jit=on")
            cursor.execute("SET LOCAL join_collapse_limit=6")
        before = settings_now()
        if failure:
            query = candidates({}).annotate(diagnostic_failure=RawSQL("1/0", []))
            with pytest.raises(DatabaseError):
                read_publication_values(query, bounded_joins=True, prepared_page=True)
        else:
            ordinary = PublicationContext(candidates({}))
            scoped = PublicationContext(candidates({}), page_read=True, prepared_page=True)
            assert [(r.pk, r.approved_revision_id, r._pv_grant, r._pv_check_status,
                     r._pv_check_manager, r._pv_check_subject) for r in scoped.rows] == [
                        (r.pk, r.approved_revision_id, r._pv_grant, r._pv_check_status,
                         r._pv_check_manager, r._pv_check_subject) for r in ordinary.rows]
        assert raw.cursor_factory is previous_factory
        assert raw.prepare_threshold == previous_threshold
        assert settings_now() == before
    assert settings_now() == initial
