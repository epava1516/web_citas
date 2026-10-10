"""Finite own PostgreSQL integration; no capacity load or acceptance claim."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database, runtime_role_environment
from django.db import connection

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_runtime_child_login_acl_optin_and_private_cleanup(capsys):
    original = connection.settings_dict["USER"]
    with runtime_role_environment(os.environ["DJANGO_SETTINGS_MODULE"]) as overrides:
        private_file = Path(overrides["RIGHTS_EVIDENCE_RUNTIME_CONFIG"])
        private_root = private_file.parent
        secret = json.loads(private_file.read_text())["PASSWORD"]
        assert private_file.stat().st_mode & 0o777 == 0o600
        assert private_root.stat().st_mode & 0o777 == 0o700
        assert secret not in json.dumps(overrides)
        assert connection.settings_dict["USER"] == original == "ci"
        probe = """import django,json; django.setup()
from django.db import connection
from django.conf import settings
from apps.safety.evidence_chain import _runtime_is_trusted
with connection.cursor() as c:
 c.execute('SELECT current_user,current_database()'); identity=c.fetchone()
 trusted=_runtime_is_trusted(c)
print(json.dumps({'identity':identity,'trusted':trusted,'enforced':settings.RIGHTS_EVIDENCE_ENFORCED,'debug':settings.DEBUG}))
"""
        child = subprocess.run(
            [sys.executable, "-c", probe],
            env=os.environ | overrides,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert secret not in child.stdout + child.stderr
        report = json.loads(child.stdout)
        role = report["identity"][0]
        assert role == overrides["POSTGRES_USER"] and role != original
        assert report["identity"][1] == connection.settings_dict["NAME"]
        assert report["trusted"] and report["enforced"] and not report["debug"]
        assert secret not in "".join(capsys.readouterr())
    assert not private_root.exists()
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [role])
        assert cursor.fetchone() is None


def test_owned_context_rejects_unverified_alias_before_provision(monkeypatch):
    monkeypatch.setitem(connection.settings_dict, "NAME", "normal_database")
    with pytest.raises(RuntimeError, match="owned disposable"):
        _owned_database()
