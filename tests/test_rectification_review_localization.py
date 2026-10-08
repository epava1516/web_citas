"""Review presentation preserves audit/privacy/current permission and raw proposed data."""

import shutil
from copy import deepcopy

import pytest
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_rectification_review import independent_case
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.models import RightsAction, RightsRectificationProposalRead
from apps.safety.rectification_details import Editor, display, validate

pytestmark = pytest.mark.django_db(transaction=True)


def assert_form(page, language):
    en = language == "en"
    for field, pair in {
        "operation": ("Operación", "Operation"),
        "purpose": ("Motivo de consulta", "Access purpose"),
        "outcome": ("Decisión", "Outcome"),
        "reason": ("Motivo privado", "Private reason"),
    }.items():
        expect(page.locator(f'label[for="id_{field}"]')).to_have_text(pair[en] + ":")
    for field, pairs in {
        "operation": [
            ("inspect", "Consultar propuesta (auditoría)", "Inspect proposal (audited)"),
            ("review", "Registrar revisión", "Record review"),
            (
                "confirm_email",
                "Solicitar confirmación de nuevo correo",
                "Request new email confirmation",
            ),
            ("notify", "Comunicar propuesta aprobada", "Communicate approved proposal"),
            ("execute", "Ejecutar rectificación recibida", "Execute received correction"),
        ],
        "outcome": [
            ("approved", "Aprobar para ejecución posterior", "Approve for later execution"),
            ("rejected", "Rechazar propuesta", "Reject proposal"),
        ],
    }.items():
        assert page.locator(f"[name={field}] option").evaluate_all(
            "nodes=>nodes.map(n=>[n.value,n.textContent])"
        ) == [[key, en_caption if en else es_caption] for key, es_caption, en_caption in pairs]


@pytest.mark.parametrize("language", ["es", "en"])
def test_review_error_audit_raw_value_and_revoked_permission(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    raw = "Synthetic / raw proposed alias"
    case, reviewer, client, _, proposal, path = independent_case(
        request, settings, monkeypatch, changes={"alias": raw}
    )
    # Native guard requires a current source audit by the new reviewer after handoff.
    from apps.safety.rights_rectification import preview

    preview(
        reviewer,
        case.pk,
        case.version,
        "Inspect current source before independent proposed data audit",
    )
    encrypted = proposal.encrypted_changes
    reads = RightsRectificationProposalRead.objects.count()
    client.get(f"/{language}/account/")
    token = client.cookies.get("csrftoken")
    assert token is not None
    path = path.replace("/en/", f"/{language}/", 1)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    },
                    {"name": "csrftoken", "value": token.value, "url": live_server.url},
                ]
            )
            page = context.new_page()
            url = live_server.url + path
            assert page.goto(url).status == 200
            assert raw not in page.content()
            assert_form(page, language)
            page.locator("[name=purpose]").fill("short")
            page.evaluate("document.querySelector('form').noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as pending:
                page.locator("button[type=submit]").click()
            assert pending.value.status == 400
            expect(page.locator(".errorlist")).to_be_visible()
            assert_form(page, language)
            assert db_sync(lambda: RightsRectificationProposalRead.objects.count()) == reads
            page.locator("[name=purpose]").fill(
                "Audit exact proposed raw data before independent review"
            )
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_text(
                    ("Profile name" if language == "en" else "Nombre del perfil") + ": " + raw,
                    exact=True,
                )
            ).to_be_visible()
            assert_form(page, language)
            assert db_sync(lambda: RightsRectificationProposalRead.objects.count()) == reads + 1
            # Reloading an audited POST repeats that POST; test a real GET then its GET reload.
            response = page.goto(url)
            assert response.request.method == "GET" and response.status == 200
            assert raw not in page.content()
            reloaded = page.reload()
            assert reloaded.request.method == "GET" and reloaded.status == 200
            assert raw not in page.content()
            assert db_sync(lambda: RightsRectificationProposalRead.objects.count()) == reads + 1

            def snapshot():
                case.refresh_from_db()
                return (
                    case.version,
                    case.status,
                    case.initial_due_at,
                    RightsAction.objects.count(),
                    RightsRectificationProposalRead.objects.count(),
                )

            before = db_sync(snapshot)
            db_sync(lambda: reviewer.user_permissions.clear())
            response = page.goto(url)
            expected = "Forbidden" if language == "en" else "Acceso denegado"
            assert response.status == 403 and page.locator("body").inner_text() == expected
            posted = page.request.post(
                url, form={"csrfmiddlewaretoken": token.value}, headers={"Referer": url}
            )
            assert posted.status == 403 and posted.text() == expected
            for item in [response, posted]:
                assert item.headers["cache-control"] == "private, no-store"
                assert item.headers["x-robots-tag"] == "noindex, nofollow"
            assert db_sync(snapshot) == before
        finally:
            browser.close()
    proposal.refresh_from_db()
    assert proposal.encrypted_changes == encrypted


@pytest.mark.parametrize("language", ["es", "en"])
def test_display_preserves_data_native_validation_and_unknown_raw_values(language):
    value = {
        "content_language": "en",
        "profile_type": "other",
        "spoken_languages": ["en"],
        "days": ["2"],
        "time_slot": "evening",
        "reception": True,
        "travel": False,
        "travel_areas": [],
    }
    original = deepcopy(value)
    before = validate(value)
    labels = {name: field.label for name, field in Editor.base_fields.items()}
    shown = display(value, language)
    assert ("Profile type: Other" if language == "en" else "Tipo de perfil: Otro") in shown
    assert ("Reception: Yes" if language == "en" else "Recepción: Sí") in shown
    assert ("Cities: " if language == "en" else "Ciudades: ") in shown
    assert value == original and validate(value) == before
    assert {name: field.label for name, field in Editor.base_fields.items()} == labels
    assert "Tipo de perfil / Profile type" in display(value)
    raw = "Unknown / untouched raw value"
    assert raw in display(value | {"profile_type": raw}, language)
