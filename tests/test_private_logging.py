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
        "/en/listing/private-id/manage/",
        "/en/safety/receipt/private-id/private-secret/",
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


def test_django_http_warning_hides_report_receipt_secret():
    import logging

    from config.private_logging import PrivateRequestFilter

    record = logging.LogRecord(
        "django.request",
        logging.WARNING,
        __file__,
        1,
        "%s: %s",
        ("Not Found", "/en/safety/receipt/private-id/private-secret/"),
        None,
    )
    record.request = SimpleNamespace(path="/en/safety/receipt/private-id/private-secret/")
    record.status_code = 404
    assert PrivateRequestFilter().filter(record)
    assert "private-secret" not in record.getMessage() and "private-id" not in record.getMessage()
    assert record.request is None and "404" in record.getMessage()


def test_development_http_log_hides_report_capability():
    import logging

    from config.private_logging import PrivateRequestFilter

    record = logging.LogRecord(
        "django.server",
        logging.INFO,
        __file__,
        1,
        '"GET %s HTTP/1.1" 200',
        ("/en/safety/receipt/private-id/private-secret/",),
        None,
    )
    assert PrivateRequestFilter().filter(record)
    assert "private-secret" not in record.getMessage() and "private-id" not in record.getMessage()
