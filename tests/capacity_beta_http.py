"""Fixture ownership boundary for the exclusive quota-verified beta HTTP mode."""

import os
from pathlib import Path
from urllib.parse import urlsplit

import redis
from django.conf import settings
from django.db import connection


def verify_owned_fixture():
    if (not (getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False)
             or getattr(settings, 'CAPACITY_BETA_HTTP_SHORT', False)
             or getattr(settings, 'CAPACITY_BETA_HTTP_CONTRACTUAL', False))
            or not getattr(settings, 'CAPACITY_ENVIRONMENT_VERIFIED', False)
            or not getattr(settings, 'CAPACITY_OBJECT_DELIVERY', False)
            or getattr(settings, 'CAPACITY_CPU_BUDGET', None) != 8
            or not settings.PROMOTION_TEST_MODE
            or settings.PRODUCTION or settings.RECOVERY_MODE
            or connection.in_atomic_block or not connection.get_autocommit()
            or os.environ.get('DJANGO_SETTINGS_MODULE') != 'capacity_settings'):
        raise ValueError('Exclusive verified owned beta HTTP environment required')
    from capacity_runtime_role import _owned_database

    _owned_database()  # Exact migrator/DB/host/port installed after controller label checks.
    if connection.settings_dict['NAME'] != 'test_promotion_gate_capacity_ci':
        raise ValueError('Exact owned beta test database required')
    expected = {'cpu.max': '350000 100000', 'memory.max': str(3968 * 1024**2), 'memory.swap.max': '0'}
    observed = {name: (Path('/sys/fs/cgroup') / name).read_text().strip() for name in expected}
    if observed != expected:
        raise ValueError('Owned beta application kernel quota mismatch')
    target = urlsplit(settings.CELERY_BROKER_URL)
    if (target.scheme != 'redis' or target.hostname != 'redis' or target.port != 6379
            or target.path != '/0' or target.username or target.password or target.query or target.fragment):
        raise ValueError('Exact owned beta broker required')
    return {'app_controls': observed, 'database': 'owned_beta_test', 'broker': 'owned_redis_db0'}


def owned_broker():
    verify_owned_fixture()
    return redis.Redis.from_url(settings.CELERY_BROKER_URL)
