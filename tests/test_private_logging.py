from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from config.gunicorn_logging import SafeAccessLogger


@pytest.mark.parametrize(
    "path",
    [
        "/es/draft/private-id/",
        "/en/photos/private-id/private/",
        "/en/favorites/private-id/remove/",
        "/es/listing/private-id/favorite/",
    ],
)
def test_photo_and_draft_access_logs_hide_private_identifiers(path):
    logger = SimpleNamespace(access_log=Mock())
    SafeAccessLogger.access(
        logger,
        SimpleNamespace(status="200 OK"),
        None,
        {"PATH_INFO": path, "REQUEST_METHOD": "GET", "QUERY_STRING": "token=secret"},
        timedelta(milliseconds=10),
    )
    arguments = logger.access_log.info.call_args.args
    assert arguments[2] == "/private-operation/"
    assert "private-id" not in str(arguments)
    assert "secret" not in str(arguments)
