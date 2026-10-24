"""Owned Redis ACL rotation preserves pending Kombu messages and peer keys."""
import secrets
import subprocess
import time
from uuid import uuid4

import pytest
import redis
from kombu import Connection, Producer, Queue


def test_owned_redis_rotation_preserves_pending_queue_and_requires_client_replacement(record_property):
    name = 'b13-redis-password-' + uuid4().hex[:12]
    prefix = 'rotation' + uuid4().hex + ':'
    old_password, new_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    clients, brokers = [], []

    def docker(*args, required=True):
        result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=30)
        if required:
            assert result.returncode == 0, 'Owned Redis Docker action failed'
        return result

    try:
        docker('run', '-d', '--pull=never', '--name', name,
               '--label', 'web-modelos-b13=broker-credential-rotation',
               '--memory', '128m', '--memory-swap', '128m', '--cpus', '1', '--pids-limit', '64',
               '-p', '127.0.0.1::6379', 'redis:7.4-alpine',
               'redis-server', '--save', '', '--appendonly', 'no')
        port = int(docker('port', name, '6379/tcp').stdout.strip().rsplit(':', 1)[1])
        base = {'host': '127.0.0.1', 'port': port, 'socket_connect_timeout': 2, 'socket_timeout': 2}
        admin = redis.Redis(**base)
        clients.append(admin)
        deadline = time.monotonic() + 20
        while True:
            try:
                assert admin.ping()
                break
            except redis.exceptions.ConnectionError:
                assert time.monotonic() < deadline
                time.sleep(.1)
        admin.execute_command('ACL', 'SETUSER', 'synthetic_broker', 'on', '>' + old_password,
                              'resetkeys', '~' + prefix + '*', 'resetchannels', '&' + prefix + '*',
                              '+@read', '+@write', '+@connection', '+@transaction', '+@scripting',
                              '+@pubsub', '-@dangerous', '-@admin', '+info')
        permissions = admin.acl_getuser('synthetic_broker')
        old = redis.Redis(**base, username='synthetic_broker', password=old_password,
                          single_connection_client=True)
        clients.append(old)
        key, foreign_key = prefix + 'control', 'foreign-project:control'
        old.set(key, 'synthetic-preserved')
        old_id = old.client_id()
        admin.set(foreign_key, 'synthetic-peer-preserved')
        queue = 'pending'

        def broker(password):
            connection = Connection(f'redis://synthetic_broker:{password}@127.0.0.1:{port}/0',
                                    transport_options={'global_keyprefix': prefix}, connect_timeout=2)
            brokers.append(connection)
            return connection

        producer = broker(old_password)
        Queue(queue)(producer.default_channel).declare()
        Producer(producer).publish({'synthetic': 'before-rotation'}, exchange='',
                                   routing_key=queue, serializer='json')
        admin.execute_command('ACL', 'SETUSER', 'synthetic_broker', '>' + new_password, '<' + old_password)
        fresh = redis.Redis(**base, username='synthetic_broker', password=new_password,
                            single_connection_client=True)
        clients.append(fresh)
        assert fresh.get(key) == old.get(key) == b'synthetic-preserved'
        rejected = redis.Redis(**base, username='synthetic_broker', password=old_password)
        clients.append(rejected)
        with pytest.raises(redis.exceptions.AuthenticationError):
            rejected.ping()
        assert old.client_id() == old_id  # ACL password removal did not revoke the connection.
        assert admin.client_kill_filter(_id=old_id) == 1
        with pytest.raises(redis.exceptions.AuthenticationError):
            old.get(key)  # Reconnection with its cached old password is rejected.
        producer.release()
        consumer = broker(new_password)
        Producer(consumer).publish({'synthetic': 'after-rotation'}, exchange='',
                                   routing_key=queue, serializer='json')
        channel = consumer.default_channel
        for label in ('before-rotation', 'after-rotation'):
            message = channel.basic_get(queue)
            assert message is not None and message.payload == {'synthetic': label}
            message.ack()
        assert channel.basic_get(queue) is None
        assert fresh.get(key) == b'synthetic-preserved'
        with pytest.raises(redis.exceptions.NoPermissionError):
            fresh.get(foreign_key)
        with pytest.raises(redis.exceptions.NoPermissionError):
            fresh.flushdb()
        assert admin.get(foreign_key) == b'synthetic-peer-preserved'
        current = admin.acl_getuser('synthetic_broker')
        assert all(current[field] == permissions[field] for field in ('commands', 'keys', 'channels'))
        record_property('old_password_rejected_new_password_accepted', True)
        record_property('old_client_survives_until_targeted_kill', True)
        record_property('cached_old_secret_cannot_reconnect', True)
        record_property('real_kombu_queue_preserved_across_rotation', True)
        record_property('peer_keys_and_acl_preserved', True)
    finally:
        for connection in reversed(brokers):
            connection.release()
        for client in reversed(clients):
            client.close()
        docker('rm', '-f', name, required=False)
        absent = docker('container', 'inspect', name, required=False)
        assert absent.returncode != 0 and 'no such' in absent.stderr.lower(), 'Owned Redis cleanup failed'
        record_property('owned_redis_removed', True)
