"""Presentation retains approved selection/coverage and partial/covered export semantics."""

import shutil
from datetime import datetime
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test.utils import CaptureQueriesContext
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability_covered_export_races import approved_coverage
from test_rights_portability_response_draft import operator

from apps.core.models import User
from apps.safety import rights_portability_jobs as jobs
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsExport,
    RightsExportPortabilityBinding,
    RightsPortabilityExportJob,
    RightsRequest,
)
from apps.safety.rights_portability_export_views import ExportForm

pytestmark = pytest.mark.django_db(transaction=True)
HELP = {
    "es": "Selecciona la cobertura para una entrega completa; sin ella se crea una copia parcial.",
    "en": "Select coverage for a complete delivery; otherwise the copy is partial.",
}
REASON = "Literal / private approved synthetic delivery rationale"


def export_captions(page, language):
    for name, pair in {
        "review": ("Selección aprobada", "Approved selection"),
        "coverage_review": ("Cobertura aprobada", "Approved coverage"),
        "reason": ("Motivo privado de entrega", "Private delivery reason"),
    }.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    expect(page.locator("#id_coverage_review_helptext")).to_have_text(HELP[language])


@pytest.mark.parametrize("language", ["es", "en"])
def test_export_default_queries_and_help(language):
    case = RightsRequest(pk=123)
    actor = User(pk=456)
    with CaptureQueriesContext(connection) as queries:
        plain = ExportForm(case=case, actor=actor)
        form = ExportForm(case=case, actor=actor, language=language)
        for name in plain.fields:
            assert plain.fields[name].label == ExportForm.base_fields[name].label
        assert (
            plain.fields["coverage_review"].help_text
            == ExportForm.base_fields["coverage_review"].help_text
        )
        assert form.fields["coverage_review"].help_text == HELP[language]
        for name in ["review", "coverage_review"]:
            first, params = plain.fields[name].queryset.query.sql_with_params()
            other, values = form.fields[name].queryset.query.sql_with_params()
            assert first == other and len(params) == len(values)
            for before, after in zip(params, values, strict=True):
                if isinstance(before, datetime):
                    assert isinstance(after, datetime) and 0 <= (after - before).total_seconds() < 1
                else:
                    assert before == after
        assert form.fields["review"].required and not form.fields["coverage_review"].required
        obj = SimpleNamespace(
            selection_id=7,
            selection=SimpleNamespace(version=2),
            coverage_id=8,
            coverage=SimpleNamespace(version=3),
        )
        assert form.fields["review"].label_from_instance(obj) == "7 · 2"
        assert form.fields["coverage_review"].label_from_instance(obj) == "8 · 3"
        assert form.fields["reason"].clean(REASON) == REASON
        assert form.fields["reason"].max_length == 200
        assert len(queries) == 0


@pytest.mark.parametrize("language", ["es", "en"])
def test_native_covered_export_captions_privacy_and_permission(
    request, settings, monkeypatch, live_server, language
):
    settings.DEBUG = True
    case, author, selection, selected, coverage, decision, _, _, _, _ = approved_coverage(
        request, settings, monkeypatch, False
    )
    monkeypatch.setattr(jobs, "dispatch", lambda job_id: True)
    staff = operator(author)
    original = (case.version, case.status, case.initial_due_at)
    path = f"/{language}/moderation/rights/{case.pk}/portability/export/"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            assert page.goto(live_server.url + path).status == 200
            export_captions(page, language)
            page.locator("#id_review").select_option(str(selected.pk))
            page.locator("#id_coverage_review").select_option(str(decision.pk))
            page.locator("#id_reason").fill("short")
            page.locator("form").evaluate("form=>form.noValidate=true")
            button = (
                "Create approved private copy"
                if language == "en"
                else "Crear copia privada aprobada"
            )
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.get_by_role("button", name=button, exact=True).click()
            assert invalid.value.status == 400
            export_captions(page, language)
            assert db_sync(lambda: RightsExport.objects.filter(action__request=case).count()) == 0
            page.locator("#id_reason").fill(REASON)
            with page.expect_response(lambda r: r.request.method == "POST") as saved:
                page.get_by_role("button", name=button, exact=True).click()
            assert saved.value.status == 302
            expect(page.get_by_role("status")).to_contain_text(
                "Waiting to generate" if language == "en" else "Esperando para generar"
            )
            job_id = db_sync(lambda: RightsPortabilityExportJob.objects.get(request=case).pk)
            db_sync(lambda: jobs.run(job_id))
            expect(page.get_by_role("status")).to_contain_text(
                "Private copy created" if language == "en" else "Copia privada creada"
            )
            page.goto(live_server.url + path)
            page.reload()
            export_captions(page, language)
            assert page.locator("#id_reason").input_value() == "" and REASON not in page.content()
            csrf = page.locator("[name=csrfmiddlewaretoken]").input_value()
            db_sync(
                lambda: author.user_permissions.remove(
                    Permission.objects.get(codename="execute_rights_request")
                )
            )
            response = page.goto(live_server.url + path)
            assert response.status == 403 and page.locator("body").inner_text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = context.request.post(
                live_server.url + path, form={"csrfmiddlewaretoken": csrf}
            )
            assert response.status == 403 and response.text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
        finally:
            browser.close()
    export = RightsExport.objects.get(action__request=case)
    payload = unseal(export.encrypted_payload)
    assert payload["partial"] is False and payload["export_schema"] == "covered-portability-v1"
    assert payload["simulation"] is True and payload["pending_review"] == ["final_response"]
    binding = RightsExportPortabilityBinding.objects.get(export=export)
    assert binding.coverage_review_id == decision.pk and binding.review_id == selected.pk
    assert unseal(export.action.encrypted_reason)["reason"] == REASON
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == (original[0] + 1, *original[1:])
