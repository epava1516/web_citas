"""Dependency-free lifecycle proofs; no network/provider/capacity acceptance."""

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, get_ident

import pytest
from botocore.config import Config
from django.core.exceptions import ImproperlyConfigured

from apps.safety.object_storage import factory
from apps.safety.object_storage.read_clients import read_clients


def configured(settings):
    settings.RIGHTS_OBJECT_KEYS = json.dumps({"v1": base64.b64encode(b"k" * 32).decode()})
    settings.RIGHTS_OBJECT_ACTIVE_KEY = "v1"
    settings.RIGHTS_OBJECT_ENDPOINT = "http://127.0.0.1:1"
    settings.RIGHTS_OBJECT_REGION = "us-east-1"
    settings.RIGHTS_OBJECT_ACCESS_KEY = "synthetic-access"
    settings.RIGHTS_OBJECT_SECRET_KEY = "synthetic-secret"
    settings.RIGHTS_OBJECT_BUCKET = "synthetic-bucket"
    settings.SAFETY_ENCRYPTION_KEY = base64.urlsafe_b64encode(b"f" * 32).decode()
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True


def trap(*args, **kwargs):
    raise AssertionError("Shared default boto3.client must never be used")


def test_two_concurrent_constructions_have_distinct_sessions_and_exact_arguments(monkeypatch):
    barrier = Barrier(2, timeout=5)
    sessions = []

    class Session:
        def __init__(self):
            self.thread = get_ident()
            sessions.append(self)

        def client(self, *args, **kwargs):
            assert get_ident() == self.thread
            barrier.wait()
            return self, args, kwargs

    monkeypatch.setattr(factory.boto3.session, "Session", Session)
    monkeypatch.setattr(factory.boto3, "client", trap)
    config = Config(signature_version="s3v4", s3={"addressing_style": "path"},
                    connect_timeout=3, read_timeout=30, retries={"max_attempts": 2},
                    request_checksum_calculation="when_required",
                    response_checksum_validation="when_required")
    values = {"endpoint_url": "http://127.0.0.1:1", "region_name": "us-east-1",
              "aws_access_key_id": "synthetic-access", "aws_secret_access_key": "synthetic-secret",
              "config": config}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(factory._new_s3_client, "s3", **values) for _ in range(2)]
        results = [future.result() for future in futures]
    assert len(sessions) == 2 and sessions[0] is not sessions[1]
    assert len({session.thread for session in sessions}) == 2
    for session, args, kwargs in results:
        assert session in sessions and args == ("s3",) and kwargs == values
        assert kwargs["config"] is config


def test_repository_creates_sessions_only_for_actual_clients_and_keeps_crypto_fresh(settings, monkeypatch):
    configured(settings)
    sessions, clients = [], []

    class Client:
        closed = False

        def close(self):
            self.closed = True

    class Session:
        def __init__(self):
            sessions.append(self)

        def client(self, *args, **kwargs):
            result = Client()
            clients.append(result)
            return result

    monkeypatch.setattr(factory.boto3.session, "Session", Session)
    monkeypatch.setattr(factory.boto3, "client", trap)
    with read_clients():
        first, second = factory.repository(), factory.repository()
        assert first.client is second.client and len(sessions) == 1
        assert first.ring is not second.ring
        assert first.reference_cipher is not second.reference_cipher
        settings.RIGHTS_OBJECT_REGION = "changed-region"
        assert factory.repository().client is not first.client
        assert len(sessions) == 2
        with read_clients():
            assert factory.repository().client is not first.client
            assert len(sessions) == 3
    assert all(client.closed for client in clients)
    outside = [factory.repository(), factory.repository()]
    assert outside[0].client is not outside[1].client and len(sessions) == 5
    for repo in outside:
        repo.client.close()


@pytest.mark.parametrize("fallback", ["unsupported-type", "entry-cap"])
def test_native_fallback_always_constructs_fresh_session(settings, monkeypatch, fallback):
    configured(settings)
    sessions, clients = [], []

    class Client:
        closed = False

        def close(self):
            self.closed = True

    class Session:
        def __init__(self):
            sessions.append(self)

        def client(self, *args, **kwargs):
            result = Client()
            clients.append(result)
            return result

    monkeypatch.setattr(factory.boto3.session, "Session", Session)
    monkeypatch.setattr(factory.boto3, "client", trap)
    with read_clients():
        if fallback == "unsupported-type":
            class Keys(str):
                pass

            settings.RIGHTS_OBJECT_KEYS = Keys(settings.RIGHTS_OBJECT_KEYS)
        else:
            for index in range(4):
                settings.RIGHTS_OBJECT_REGION = str(index)
                factory.repository()
            settings.RIGHTS_OBJECT_REGION = "overflow"
        first, second = factory.repository(), factory.repository()
        assert first.client is not second.client
        assert sessions[-1] is not sessions[-2]
    assert not first.client.closed and not second.client.closed
    if fallback == "entry-cap":
        assert len(sessions) == 6 and all(client.closed for client in clients[:4])
    else:
        assert len(sessions) == 2
    first.client.close()
    second.client.close()


@pytest.mark.parametrize("failure", ["keys", "endpoint", "config"])
def test_original_settings_key_and_config_errors_precede_session_construction(settings, monkeypatch, failure):
    configured(settings)
    sessions = []
    monkeypatch.setattr(factory.boto3.session, "Session", lambda: sessions.append(True))
    monkeypatch.setattr(factory.boto3, "client", trap)
    if failure == "keys":
        settings.RIGHTS_OBJECT_KEYS = "invalid-json"
        expected = ImproperlyConfigured
    elif failure == "endpoint":
        class Settings:
            def __getattr__(self, name):
                if name == "RIGHTS_OBJECT_ENDPOINT":
                    raise RuntimeError("synthetic settings failure")
                return getattr(settings, name)

        monkeypatch.setattr(factory, "settings", Settings())
        expected = RuntimeError
    else:
        def failed_config(*args, **kwargs):
            raise TypeError("synthetic config failure")

        monkeypatch.setattr(factory, "Config", failed_config)
        expected = TypeError
    with pytest.raises(expected):
        factory.repository()
    assert not sessions
