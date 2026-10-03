import pytest
from django.db import connection


@pytest.mark.django_db
def test_health_uses_postgresql(client):
    assert connection.vendor == "postgresql"
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["es", "en"])
def test_local_home_security_and_language(client, language):
    response = client.get(f"/{language}/")
    assert response.status_code == 200
    assert f'lang="{language}"'.encode() in response.content
    assert b"noindex,nofollow" in response.content
    assert response["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]
