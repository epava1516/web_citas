"""Fail before execution when selected real object-storage tests cannot start."""

import subprocess

import pytest

OBJECT_STORE_TEST_IMAGE = (
    "rustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c"
)


def require_object_store_image():
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", OBJECT_STORE_TEST_IMAGE, "--format", "{{.Id}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise pytest.UsageError(
            "Cannot check the pinned RustFS test image: Docker unavailable or timed out."
        ) from exc
    if result.returncode:
        raise pytest.UsageError(
            "Selected object_store tests require an available Docker daemon and local image "
            f"{OBJECT_STORE_TEST_IMAGE}. Prepare it with docker pull before retrying. "
            "No tests were executed by this worker; storage tests are never skipped."
        )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    if any("object_store" in getattr(item, "fixturenames", ()) for item in items):
        require_object_store_image()
