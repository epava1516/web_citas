"""Source projection: full payload/SQL and alias restoration, PostgreSQL evidence."""
import ast
import subprocess

import pytest
from django.db import connection, transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_source_fingerprint import complete_subject

from apps.core.models import Person
from apps.listings.models import Listing, Revision
from apps.safety import rights_exports
from tests.capacity_revision_candidate import original_tree, variant


def test_original_ast_matches_frozen_git_function():
    baseline = original_tree()
    calls = [node for node in ast.walk(baseline) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'defer']
    calls[0].args = [ast.Constant('search_document')]
    old = ast.parse(subprocess.check_output(['git','show','HEAD:apps/safety/rights_exports.py'], text=True))
    old = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == 'source_copy')
    assert ast.dump(baseline.body[0], include_attributes=False) == ast.dump(old, include_attributes=False)


def test_original_alias_restored_on_failure():
    original = rights_exports.source_copy
    with pytest.raises(ValueError, match='probe'):
        with variant('original'):
            assert rights_exports.source_copy is not original
            raise ValueError('probe')
    assert rights_exports.source_copy is original


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures('directory')
def test_complete_source_same_output_queries_and_unmodified_rows():
    person, listing = complete_subject()
    before = list(Revision.objects.filter(listing=listing).order_by('pk').values_list('pk','updated_at'))
    results, queries = [], []
    for mode in ('original','deferred'):
        fresh_person = Person.objects.select_related('phone_claim').get(pk=person.pk)
        fresh_listing = Listing.objects.get(pk=listing.pk)
        seen = []
        def capture(execute, sql, params, many, context):
            seen.append((sql, params))
            return execute(sql, params, many, context)
        with transaction.atomic(), variant(mode), connection.execute_wrapper(capture):
            results.append(rights_exports.source_copy(fresh_person, fresh_listing))
        queries.append(seen)
    assert rights_exports.canonical(results[0]) == rights_exports.canonical(results[1])
    assert before == list(Revision.objects.filter(listing=listing).order_by('pk').values_list('pk','updated_at'))
    assert len(queries[0]) == len(queries[1])
    changed = []
    for index, ((old, old_params), (new, new_params)) in enumerate(zip(*queries, strict=True)):
        assert old_params == new_params
        if old != new:
            changed.append(index)
            assert 'FROM "listings_revision"' in old and 'FOR UPDATE OF "listings_revision"' in old
            assert old[old.index(' FROM '):] == new[new.index(' FROM '):]
    assert len(changed) == 1
