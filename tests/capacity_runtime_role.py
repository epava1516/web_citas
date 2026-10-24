"""Separate runtime LOGIN for owned capacity children; never changes normal services.

The pytest process remains the migrator. Its child settings read a private file,
so neither the child command nor its environment contains the runtime password.
"""

import io
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from secrets import token_urlsafe
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from psycopg import connect, sql


def _owned_database():
    database = connection.settings_dict
    if (
        connection.vendor != "postgresql"
        or settings.PRODUCTION
        or database["USER"] != "ci"
        or connection.in_atomic_block
    ):
        raise RuntimeError("Capacity runtime requires the own PostgreSQL migrator outside atomic")
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    if worker and not re.fullmatch(r"gw[0-9]+", worker):
        raise RuntimeError("Capacity runtime worker identity is invalid")
    if getattr(settings, "CAPACITY_ENVIRONMENT_VERIFIED", False):
        # The owned controller verifies the pg container label/network before
        # installing capacity_settings inside its isolated, read-only app container.
        if (
            database["NAME"] != ('test_promotion_gate_capacity_ci'
                                  if (getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False)
                                      or getattr(settings, 'CAPACITY_BETA_HTTP_SHORT', False)
                                      or getattr(settings, 'CAPACITY_BETA_HTTP_CONTRACTUAL', False))
                                  else 'test_capacity_ci')
            or database["HOST"] != "pg"
            or str(database["PORT"]) != "5432"
            or os.environ.get("DJANGO_SETTINGS_MODULE") != "capacity_settings"
        ):
            raise RuntimeError("Capacity runtime database differs from verified owned topology")
    else:
        # Finite N2 on the normal owned test runner: verify actual container/port,
        # not just a manually supplied database name or environment flag.
        from directory_snapshot import _verify_container

        name = os.environ.get("LOCAL_CI_POSTGRES_CONTAINER", "")
        match = re.fullmatch(r"web-modelos-ci-pg-(\d{8}-\d{6}-[a-f0-9]{8})", name)
        if (
            not match
            or os.environ.get("DJANGO_SETTINGS_MODULE") != "local_ci_settings"
            or database["NAME"] != "test_promotion_gate_ci" + ("_" + worker if worker else "")
            or database["HOST"] != "127.0.0.1"
        ):
            raise RuntimeError("Capacity runtime requires an owned disposable database")
        _verify_container(match[1], worker, database)
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user,current_database()")
        if cursor.fetchone() != ("ci", database["NAME"]):
            raise RuntimeError("Capacity runtime migrator identity differs from actual PostgreSQL")
    return database


def _private_write(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write(text)


@contextmanager
def runtime_role_environment(base_settings_module="capacity_gunicorn_settings"):
    """Yield child env overrides after provision and independent TCP role proof.

    Apply after the server's base settings/module environment. Close every child
    before exiting this context: credentials and role are removed on exit.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", base_settings_module):
        raise RuntimeError("Invalid capacity base settings module")
    database = _owned_database()
    role = "capacity_runtime_" + uuid4().hex[:16]
    secret = token_urlsafe(32)
    created = False
    private = tempfile.TemporaryDirectory(prefix="capacity-runtime-", dir="/tmp")
    try:
        # The migrator command is real; stdout/stderr are deliberately captured.
        # Secret values are never command arguments or inherited by children.
        output = io.StringIO()
        with patch.dict(
            os.environ, {"POSTGRES_RUNTIME_USER": role, "POSTGRES_RUNTIME_PASSWORD": secret}
        ):
            call_command("initialize_rights_runtime", stdout=output, stderr=output, verbosity=0)
        created = True
        if secret in output.getvalue():
            raise RuntimeError("Runtime provisioner emitted a private credential")
        credentials = {
            "NAME": database["NAME"],
            "HOST": database["HOST"],
            "PORT": database["PORT"],
            "USER": role,
            "PASSWORD": secret,
        }
        with connect(
            dbname=credentials["NAME"],
            host=credentials["HOST"],
            port=credentials["PORT"],
            user=role,
            password=secret,
            connect_timeout=10,
        ) as login:
            with login.cursor() as cursor:
                cursor.execute(
                    "SELECT current_user,current_database(),rolsuper,rolcreatedb,rolcreaterole,rolbypassrls "
                    "FROM pg_roles WHERE rolname=current_user"
                )
                if cursor.fetchone() != (role, database["NAME"], False, False, False, False):
                    raise RuntimeError(
                        "Independent capacity TCP connection is not the restricted runtime"
                    )
                cursor.execute(
                    "SELECT pg_has_role(current_user,pg_get_userbyid(relowner),'MEMBER') "
                    "FROM pg_class WHERE oid='public.safety_rightsevidencehead'::regclass"
                )
                if cursor.fetchone()[0]:
                    raise RuntimeError("Capacity runtime inherits evidence ownership")
        root = Path(private.name)
        credential_file = root / "database.json"
        _private_write(credential_file, json.dumps(credentials))
        module = "capacity_runtime_settings_" + uuid4().hex
        _private_write(
            root / (module + ".py"),
            f"from {base_settings_module} import *\n"
            "import json as _runtime_json, os as _runtime_os\n"
            'with open(_runtime_os.environ["RIGHTS_EVIDENCE_RUNTIME_CONFIG"]) as _runtime_file:\n'
            '    DATABASES["default"] = dict(DATABASES["default"], **_runtime_json.load(_runtime_file))\n'
            "RIGHTS_EVIDENCE_ENFORCED = True\n"
            "DEBUG = False\n",
        )
        yield {
            "DJANGO_SETTINGS_MODULE": module,
            "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", ""),
            "RIGHTS_EVIDENCE_RUNTIME_CONFIG": str(credential_file),
            "RIGHTS_EVIDENCE_ENFORCED": "1",
            "POSTGRES_USER": role,
            "POSTGRES_PASSWORD": "",
            "POSTGRES_RUNTIME_PASSWORD": "",
        }
    finally:
        # No backend termination: owned server/worker contexts must exit first.
        # Active connections prevent role deletion; a caller cannot hide leakage.
        if created:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE usename=%s", [role])
                if cursor.fetchone()[0]:
                    raise RuntimeError("Capacity runtime still has active child connections")
                cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
        private.cleanup()
