"""Finite real PostgreSQL observation equivalence, not capacity acceptance."""

import sys
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_coverage_batch import REASON, prepared

from apps.safety import rights_portability_coverage_batch as batch
from apps.safety.models import RightsAction, RightsPortabilityCoverageRead
from tests import capacity_phase_spans as spans

pytestmark = pytest.mark.django_db(transaction=True)


def test_real_listing_phases_preserve_pages_audits_and_idempotent_results(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    args = reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions'
    expected = batch.inspect_batch(*args)
    originals = {name: getattr(sys.modules[module], name)
                 for module, name in spans.PHASE_TARGETS.values()}
    with spans.scope(sql_context=connection.execute_wrapper) as collector:
        actual = batch.inspect_batch(*args)
    assert [(read.pk, page) for read, page in actual] == [(read.pk, page) for read, page in expected]
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == len(expected)
    observed = collector.snapshot()
    assert observed['status'] == 'complete' and not observed['incomplete']
    assert observed['phases']['batch']['calls'] == 1
    assert observed['phases']['page']['calls'] == len(expected)
    assert len(observed['pages']) == len(expected)
    assert observed['phases']['source']['calls'] == 1
    assert observed['phases']['compile']['calls'] == 1
    assert observed['phases']['record']['calls'] == len(expected)
    assert observed['sql_count'] > 0
    assert not connection.execute_wrappers
    assert all(getattr(sys.modules[module], name) is originals[name]
               for module, name in spans.PHASE_TARGETS.values())


def test_real_listing_observation_retains_exact_failure_and_atomic_rollback(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    original = batch.inspect_page
    error = ValidationError('Synthetic second-page failure')
    calls = []

    def fail_second(*args, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            raise error
        return original(*args, **kwargs)

    monkeypatch.setattr(batch, 'inspect_page', fail_second)
    key = uuid4()
    with pytest.raises(ValidationError) as captured:
        with spans.scope(sql_context=connection.execute_wrapper) as collector:
            batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, key, REASON, 'revisions')
    assert captured.value is error and len(calls) == 2
    assert batch.inspect_page is fail_second
    assert not connection.execute_wrappers
    assert collector.snapshot()['status'] == 'complete'
    assert not RightsAction.objects.filter(key=key).exists()
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
