"""Real owned PostgreSQL login rotation; no normal application role is touched."""
import copy
import secrets
import subprocess
import time
from uuid import uuid4

import psycopg
import pytest
from django.db import connections as django_connections
from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.utils import OperationalError as DjangoOperationalError
from psycopg import sql


def test_owned_login_rotation_requires_old_session_termination(record_property, django_db_blocker):
    name = 'b13-password-' + uuid4().hex[:16]
    admin_password, old_password, new_password = (secrets.token_urlsafe(32) for _ in range(3))
    connections = []
    wrapper = None

    def django_query():
        with django_db_blocker.unblock(), wrapper.cursor() as cursor:
            cursor.execute("SELECT * FROM public.synthetic_control")
            return cursor.fetchall()

    def docker(*args, required=True):
        result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=30)
        if required:
            assert result.returncode == 0, 'Owned PostgreSQL Docker action failed'
        return result

    try:
        docker('run', '-d', '--pull=never', '--name', name,
               '--label', 'web-modelos-b13=credential-rotation',
               '--memory', '512m', '--memory-swap', '512m', '--cpus', '1', '--pids-limit', '128',
               '--tmpfs', '/var/lib/postgresql/data', '-p', '127.0.0.1::5432',
               '-e', 'POSTGRES_DB=synthetic_rotation', '-e', 'POSTGRES_USER=synthetic_admin',
               '-e', 'POSTGRES_PASSWORD=' + admin_password, 'postgres:17-alpine')
        port = int(docker('port', name, '5432/tcp').stdout.strip().rsplit(':', 1)[1])
        base = {'host': '127.0.0.1', 'port': port, 'dbname': 'synthetic_rotation', 'connect_timeout': 2}
        deadline = time.monotonic() + 30
        while True:
            try:
                admin = psycopg.connect(**base, user='synthetic_admin', password=admin_password, autocommit=True)
                connections.append(admin)
                break
            except psycopg.OperationalError:
                assert time.monotonic() < deadline, 'Owned PostgreSQL readiness deadline exceeded'
                time.sleep(.1)
        admin.execute(sql.SQL('CREATE ROLE synthetic_runtime LOGIN PASSWORD {}').format(sql.Literal(old_password)))
        admin.execute('CREATE TABLE public.synthetic_control (id integer PRIMARY KEY, value text NOT NULL)')
        admin.execute("INSERT INTO public.synthetic_control VALUES (1, 'synthetic-preserved-value')")
        admin.execute('GRANT SELECT ON public.synthetic_control TO synthetic_runtime')
        old = psycopg.connect(**base, user='synthetic_runtime', password=old_password, autocommit=True)
        connections.append(old)
        old_pid = old.info.backend_pid
        before = old.execute('SELECT * FROM public.synthetic_control').fetchall()
        database = copy.deepcopy(django_connections.databases['default'])
        assert database['CONN_MAX_AGE'] == 60 and database['CONN_HEALTH_CHECKS'] is True
        assert not database['OPTIONS'].get('pool')
        database.update(NAME=base['dbname'], USER='synthetic_runtime', PASSWORD=old_password,
                        HOST=base['host'], PORT=port, OPTIONS={'connect_timeout': 2})
        wrapper = DatabaseWrapper(database, alias='owned_rotation_' + uuid4().hex)
        assert django_query() == before
        django_pid = wrapper.connection.info.backend_pid
        admin.execute(sql.SQL('ALTER ROLE synthetic_runtime PASSWORD {}').format(sql.Literal(new_password)))
        fresh = psycopg.connect(**base, user='synthetic_runtime', password=new_password, autocommit=True)
        connections.append(fresh)
        assert fresh.execute('SELECT * FROM public.synthetic_control').fetchall() == before
        with pytest.raises(psycopg.OperationalError) as rejected:
            psycopg.connect(**base, user='synthetic_runtime', password=old_password)
        assert 'password authentication failed' in str(rejected.value).lower()
        admin.execute('ALTER ROLE synthetic_runtime NOLOGIN')
        with pytest.raises(psycopg.OperationalError) as closed_login:
            psycopg.connect(**base, user='synthetic_runtime', password=new_password)
        assert 'not permitted to log in' in str(closed_login.value).lower()
        assert fresh.execute('SELECT * FROM public.synthetic_control').fetchall() == before
        # Credential replacement alone does not revoke sessions established earlier.
        assert old.execute('SELECT * FROM public.synthetic_control').fetchall() == before
        assert admin.execute('SELECT pg_terminate_backend(%s)', (old_pid,)).fetchone() == (True,)
        with pytest.raises(psycopg.OperationalError):
            old.execute('SELECT * FROM public.synthetic_control')
        assert fresh.execute('SELECT * FROM public.synthetic_control').fetchall() == before
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            fresh.execute("INSERT INTO public.synthetic_control VALUES (2, 'not permitted')")
        admin.execute('ALTER ROLE synthetic_runtime LOGIN')
        reopened = psycopg.connect(**base, user='synthetic_runtime', password=new_password, autocommit=True)
        connections.append(reopened)
        assert reopened.execute('SELECT * FROM public.synthetic_control').fetchall() == before
        assert django_query() == before and wrapper.connection.info.backend_pid == django_pid
        assert admin.execute('SELECT pg_terminate_backend(%s)', (django_pid,)).fetchone() == (True,)
        with django_db_blocker.unblock():
            wrapper.close_if_unusable_or_obsolete()
        with pytest.raises(DjangoOperationalError, match='password authentication failed'):
            django_query()
        wrapper.settings_dict['PASSWORD'] = new_password
        assert django_query() == before
        assert wrapper.connection.info.backend_pid != django_pid
        record_property('django_persistent_connection_survives_password_change', True)
        record_property('django_health_check_reconnect_with_stale_secret_fails', True)
        record_property('django_updated_secret_reconnects_with_data_preserved', True)
        flags = admin.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                              "FROM pg_roles WHERE rolname='synthetic_runtime'").fetchone()
        assert flags == (False,) * 5
        assert admin.execute('SELECT * FROM public.synthetic_control').fetchall() == before
        record_property('login_gate_rejects_new_connections_and_reopens', True)
        record_property('old_password_rejected_for_new_connections', True)
        record_property('old_session_survives_password_change', True)
        record_property('targeted_termination_revokes_old_session', True)
        record_property('new_session_and_acl_and_data_preserved', True)
    finally:
        if wrapper is not None:
            with django_db_blocker.unblock():
                wrapper.close()
        for connection in reversed(connections):
            connection.close()
        docker('rm', '-f', name, required=False)
        absent = docker('container', 'inspect', name, required=False)
        assert absent.returncode != 0 and 'no such' in absent.stderr.lower(), 'Owned PostgreSQL cleanup failed'
        record_property('owned_postgres_removed', True)
