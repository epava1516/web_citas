"""Guard behaviour only; these unit tests do not verify S3 storage."""

import subprocess
from types import SimpleNamespace

import pytest

from scripts import local_ci_requirements as requirements


def test_unrelated_selection_never_inspects_docker(monkeypatch):
    def unexpected():
        raise AssertionError("Unrelated tests must not require Docker")

    monkeypatch.setattr(requirements, "require_object_store_image", unexpected)
    requirements.pytest_collection_modifyitems([SimpleNamespace(fixturenames=["directory"])])


def test_transitive_fixture_dependency_checked_once(monkeypatch):
    calls = []
    monkeypatch.setattr(requirements, "require_object_store_image", lambda: calls.append(True))
    requirements.pytest_collection_modifyitems(
        [
            SimpleNamespace(fixturenames=["repository", "object_store"]),
            SimpleNamespace(fixturenames=["object_store"]),
        ]
    )
    assert calls == [True]


@pytest.mark.parametrize(
    "failure", [1, FileNotFoundError(), subprocess.TimeoutExpired("docker", 10)]
)
def test_missing_dependency_is_error_without_daemon_output(monkeypatch, failure):
    def inspect(*args, **kwargs):
        if isinstance(failure, Exception):
            raise failure
        return SimpleNamespace(returncode=failure, stderr="PRIVATE_DAEMON_OUTPUT")

    monkeypatch.setattr(requirements.subprocess, "run", inspect)
    with pytest.raises(pytest.UsageError) as error:
        requirements.require_object_store_image()
    assert "PRIVATE_DAEMON_OUTPUT" not in str(error.value)


def test_available_image_check_is_read_only_and_bounded(monkeypatch):
    calls = []

    def inspect(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(requirements.subprocess, "run", inspect)
    requirements.require_object_store_image()
    command, options = calls.pop()
    assert command == [
        "docker",
        "image",
        "inspect",
        requirements.OBJECT_STORE_TEST_IMAGE,
        "--format",
        "{{.Id}}",
    ]
    assert options == {"capture_output": True, "text": True, "timeout": 10}
