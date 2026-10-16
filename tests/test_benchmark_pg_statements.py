"""Protocol rejection tests only; no claim of real PostgreSQL verification."""
import pytest

from scripts.benchmark_pg_statements import PGStatementSampler


@pytest.mark.parametrize('case', ['normal_database', 'wrong_port', 'non_loopback'])
def test_sampler_rejects_unowned_database_before_connect(tmp_path, monkeypatch, case):
    run = {'id': '20261016-120000-abcdef12',
           'containers': ['web-modelos-ci-pg-20261016-120000-abcdef12']}
    inspection = {'Name': '/'+run['containers'][0],
                  'Config': {'Labels': {'web-modelos-local-ci-run': run['id']}},
                  'State': {'Running': True, 'Pid': 1234},
                  'NetworkSettings': {'Ports': {'5432/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '12345'}]}}}
    database = {'NAME': 'test_promotion_gate_example', 'HOST': '127.0.0.1', 'PORT': '12345'}
    if case == 'normal_database':
        database['NAME'] = 'normal'
    elif case == 'wrong_port':
        database['PORT'] = '12346'
    else:
        database['HOST'] = 'remote.example'

    def forbidden_connect(**kwargs):
        pytest.fail('Rejected configuration must never open a connection')

    monkeypatch.setattr('scripts.benchmark_pg_statements.psycopg.connect', forbidden_connect)
    with pytest.raises(ValueError):
        PGStatementSampler(tmp_path/'unused', run, inspection, database)
    assert not list(tmp_path.iterdir())
