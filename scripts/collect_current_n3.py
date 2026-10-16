"""Explicit collection-only inventory plugin; not a functional verification gate."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

COLLECTION_REPORTS = []


def pytest_addoption(parser):
    parser.addoption('--owned-n3-collection-output', required=True)


def pytest_configure(config):
    if not config.option.collectonly:
        raise pytest.UsageError('N3 inventory plugin requires --collect-only')
    COLLECTION_REPORTS.clear()


def pytest_collectreport(report):
    # Terminal status is also retained in the official collection log.
    if report.failed or report.skipped:
        COLLECTION_REPORTS.append({'nodeid': report.nodeid, 'outcome': report.outcome,
                                   'reason_preview': str(report.longrepr)[:1000]})


def pytest_collection_finish(session):
    output = Path(session.config.getoption('--owned-n3-collection-output'))
    nodes = [item.nodeid for item in session.items]
    assert len(nodes) == len(set(nodes)), 'Duplicate selected nodeids'
    by_file = Counter(node.split('::', 1)[0] for node in nodes)
    archive = output.with_suffix('.nodeids.json.gz')
    with gzip.open(archive, 'wt') as handle:
        json.dump(nodes, handle)
    session.config._owned_n3_inventory = {
        'scope': 'COLLECTION ONLY; no executed test or N3 acceptance',
        'selected_nodes': len(nodes), 'selected_files': len(by_file),
        'per_file': dict(sorted(by_file.items())),
        'nodeids_archive': archive.name,
        'nodeids_archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'full_nodeids_retained_compressed': True,
    }


def pytest_sessionfinish(session, exitstatus):
    output = Path(session.config.getoption('--owned-n3-collection-output'))
    inventory = getattr(session.config, '_owned_n3_inventory', {'scope': 'Collection incomplete'})
    inventory['pytest_exit'] = int(exitstatus)
    inventory['nonpassed_collection_reports'] = COLLECTION_REPORTS
    output.write_text(json.dumps(inventory, indent=2)+'\n')
