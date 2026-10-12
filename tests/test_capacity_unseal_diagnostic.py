"""Finite PostgreSQL batch diagnostic, synthetic size probe; no capacity acceptance."""
import json
import sys
import types
from time import perf_counter_ns, thread_time_ns
from uuid import uuid4

import pytest
from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_evidence_chain import runtime, set_role  # noqa: F401
from test_rights_portability_coverage_batch import REASON, prepared

from apps.safety import crypto
from apps.safety import rights_portability_coverage_batch as batch
from apps.safety.models import RightsAction, RightsPortabilityCoverageRead
from tests import capacity_unseal_diagnostic as diagnostic

pytestmark = pytest.mark.django_db(transaction=True)


def timed(call):
    wall, cpu = perf_counter_ns(), thread_time_ns()
    result = call()
    return result, {'wall_ns': perf_counter_ns() - wall, 'cpu_ns': thread_time_ns() - cpu}


def test_real_runtime_batch_unseal_breakdown(request, settings, monkeypatch, record_property):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    role = request.getfixturevalue('runtime')
    settings.RIGHTS_EVIDENCE_ENFORCED = True
    set_role(role)
    args = reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, 'revisions'
    expected, control = timed(lambda: batch.inspect_batch(*args))
    original = crypto.unseal
    with diagnostic.scope() as collector:
        actual, observed = timed(lambda: batch.inspect_batch(*args))
    assert crypto.unseal is original and not collector.retained
    assert [(read.pk, page) for read, page in actual] == [(read.pk, page) for read, page in expected]
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == len(expected)
    report = collector.snapshot()
    assert report['calls'] > 0 and report['failures'] == 0
    assert any(row['calls'] > 1 for row in report['groups'])
    report.update(pages=len(actual), control_replay_difference='control creates audits; observed is replay',
                  control=control, observed=observed, runtime_enforced=True)
    record_property('unseal_diagnostic', json.dumps(report))


def test_failure_restores_aliases_and_batch_rollback(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    role = request.getfixturevalue('runtime')
    settings.RIGHTS_EVIDENCE_ENFORCED = True
    set_role(role)
    original_page = batch.inspect_page
    count = 0

    def fail_second(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            raise ValidationError('Synthetic later-page failure')
        return original_page(*args, **kwargs)

    monkeypatch.setattr(batch, 'inspect_page', fail_second)
    key, original = uuid4(), crypto.unseal
    with pytest.raises(ValidationError, match='later-page'):
        with diagnostic.scope() as collector:
            batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, key, REASON, 'revisions')
    assert crypto.unseal is original and not collector.retained
    assert not RightsAction.objects.filter(key=key).exists()
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()


def test_fresh_crypto_result_is_never_shared_and_invalid_token_is_rechecked():
    value = {'synthetic': ['unchanged']}
    payload = crypto.seal(value)
    original = crypto.unseal
    with diagnostic.scope() as collector:
        first = crypto.unseal(payload)
        first['synthetic'].append('local mutation')
        assert crypto.unseal(payload) == value
        with pytest.raises(InvalidToken):
            crypto.unseal('invalid-synthetic-token')
    assert collector.calls == 3 and collector.failures == 1
    assert crypto.unseal is original and not collector.retained


@pytest.mark.parametrize('size', [4096, 1024 * 1024, 16 * 1024 * 1024])
def test_synthetic_size_probe(size, record_property):
    # Independent repeated authenticated decrypt outputs, never request-capacity evidence.
    payload = crypto.seal({'synthetic': 'x' * size})
    with diagnostic.scope() as collector:
        for _ in range(4):
            assert len(crypto.unseal(payload)['synthetic']) == size
    report = collector.snapshot()
    assert len(report['groups']) == 1 and report['groups'][0]['calls'] == 4
    record_property('unseal_size_probe', json.dumps(report))


def test_scope_bounds_and_late_alias_restoration(monkeypatch):
    monkeypatch.setattr(diagnostic, 'MAX_BYTES', 1)
    original = crypto.unseal
    late = types.ModuleType('apps.safety.synthetic_diagnostic_alias')
    monkeypatch.setitem(sys.modules, late.__name__, late)
    payload = crypto.seal({'synthetic': 'untracked'})
    with diagnostic.scope() as collector:
        late.unseal = crypto.unseal
        assert late.unseal(payload) == {'synthetic': 'untracked'}
        assert not collector.retained and collector.untracked_calls == 1
        with pytest.raises(RuntimeError, match='already active'):
            with diagnostic.scope():
                pass
    assert late.unseal is original and crypto.unseal is original
    assert collector.snapshot()['groups'] == []
