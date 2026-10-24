"""Owned-resource guards plus real child process identity; TCP checked separately."""

import os
import subprocess
import sys

import pytest

from scripts import benchmark_owned_services as resources


def test_owned_tree_retains_real_child_identity_and_rejects_pid_reuse():
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    try:
        identity = resources.process_row(child.pid)
        rows = resources.owned_tree(identity)
        assert len(rows) == 1 and rows[0]['pid'] == child.pid
        assert rows[0]['ppid'] == os.getpid() and rows[0]['rss_bytes'] >= 0
        assert resources.descendant(child.pid, os.getpid())
        with pytest.raises(ValueError, match='PID reused'):
            resources.owned_tree(identity | {'start_ticks': identity['start_ticks'] + 1})
    finally:
        child.terminate()
        child.wait(timeout=5)


@pytest.mark.parametrize('defect', ['name', 'label', 'stopped'])
def test_foreign_container_rejected_before_reading_process(monkeypatch, defect):
    run = {'id': '20261021-180000-abcdef12',
           'containers': ['web-modelos-ci-pg-20261021-180000-abcdef12']}
    inspection = {'Name': '/web-modelos-ci-pg-' + run['id'],
                  'Config': {'Labels': {'web-modelos-local-ci-run': run['id']}},
                  'State': {'Running': True}}
    if defect == 'name':
        inspection['Name'] = '/foreign'
    elif defect == 'label':
        inspection['Config']['Labels']['web-modelos-local-ci-run'] = 'foreign'
    else:
        inspection['State']['Running'] = False

    def unexpected(*args):
        raise AssertionError('Foreign process must never be read')

    monkeypatch.setattr(resources, 'process_row', unexpected)
    with pytest.raises(ValueError, match='container mismatch'):
        resources.verify_container(run, inspection, 'postgres')


def test_sampler_output_and_limit_path_guards(tmp_path):
    with pytest.raises(ValueError, match='resource output'):
        resources.OwnedServiceSampler(tmp_path / 'foreign.jsonl',
                                     {'id': '20261021-180000-abcdef12'}, {}, {})
    with pytest.raises(ValueError, match='cgroup path'):
        resources.limit_chain(tmp_path)
