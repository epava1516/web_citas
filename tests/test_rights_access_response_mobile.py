"""Real Chromium mobile preparation/review with synthetic identity evidence."""

import json
import shutil
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_access_response_draft import REASON, TEXT
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import RightsAccessResponseDraft, RightsAccessResponseReview
from apps.safety.rights_exports import generate, preview
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_mobile_final_response_preparation_and_independent_decision(
    live_server, request, settings, monkeypatch, tmp_path, language, account_only, metadata=False
):
    settings.DEBUG = True
    case, author, _, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    respond = Permission.objects.get(codename="respond_rights_request")
    author.user_permissions.add(respond)
    reviewer.user_permissions.add(respond, Permission.objects.get(codename="verify_rights_scope"))
    author, reviewer = User.objects.get(pk=author.pk), User.objects.get(pk=reviewer.pk)
    source_copy = preview(author, case.pk, case.version, REASON)
    export = generate(
        author,
        case.pk,
        uuid4(),
        case.version,
        REASON,
        source_copy,
        information_review_id=decision.pk,
    )
    case.refresh_from_db()
    staff, other = operator(author), operator(reviewer)
    read(staff, case)
    proof = start(author, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    read(other, case)
    receive_event(reviewer, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(staff, case)
    read(other, case)
    original = case.version, case.response_version, case.status, case.initial_due_at
    inventory = None
    if metadata:
        from retained_rdb_fixture import aux_decoder, capture, metadata_decoder, native_decoder
        from test_redis_history_scope import message

        from apps.safety.crypto import seal, unseal
        from apps.safety.rights import fingerprint
        from apps.safety.rights_access_coverage import UNPROJECTED
        from apps.safety.rights_access_coverage_review import inspect as inspect_coverage
        from apps.safety.rights_access_coverage_review import record as record_coverage
        from apps.safety.rights_access_coverage_store import required_references, save
        from apps.safety.rights_access_scope_store import inspect
        from apps.safety.rights_copy_inspection import SECTIONS
        from apps.safety.rights_exports import canonical
        from apps.safety.rights_portability_selection import row_reference
        from scripts.scope_retained_redis_origin import prepare_origins

        delivered = unseal(export.encrypted_payload)
        declarations = {
            "sections": {
                section: [{"row": row_reference(section, index, row), "delivered_index": index, "decisions": {}}
                          for index, row in enumerate(project(source_copy))]
                for section, project in SECTIONS.items()
            },
            "boundaries": {name: {"status": "excluded", "reason": REASON, "evidence": "Synthetic referenced information review; no real identity or legal approval"}
                           for name in set(source_copy["pending_review"]) | set(delivered["pending_review"]) | UNPROJECTED},
        }
        action = decision.action
        reference = {"action": action.pk, "request": str(action.request_id), "actor": action.actor_id,
                     "version": action.expected_version, "operation": action.operation,
                     "payload": action.payload_digest, "reason_ciphertext": fingerprint(action.encrypted_reason)}
        refs = {label: {"action": action.pk, "digest": fingerprint(canonical(reference))}
                for label in required_references(declarations)}
        coverage = save(author, case.pk, case.version, case.response_version, export.pk, uuid4(), REASON,
                        delivered, declarations, refs, fingerprint(canonical(source_copy)), fingerprint(canonical(delivered)))
        _, _, coverage_read = inspect_coverage(reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON)
        coverage_review = record_coverage(reviewer, case.pk, case.version, coverage.pk, coverage_read.pk, uuid4(), REASON, "approved")

        inventory, _ = inspect(author, case.pk, case.version, case.response_version, uuid4(), REASON)
        manifest = unseal(inventory.encrypted_inventory)
        blob = manifest["media"][0]["blob"] if manifest["media"] else str(uuid4())
        body, _ = capture(tmp_path / "native", inventory.created_at, [message(blob)])
        source = tmp_path / "snapshot.encrypted"
        source.write_text(seal(body))
        source.chmod(0o600)
        folder = tmp_path / "origins"
        folder.mkdir(mode=0o700)
        decoder, digest = native_decoder()
        if metadata == "physical":
            aux, aux_hash = metadata_decoder()
            options = {"metadata_decoder": aux, "metadata_decoder_sha256": aux_hash}
        else:
            aux, aux_hash = aux_decoder()
            options = {"aux_decoder": aux, "aux_decoder_sha256": aux_hash}
        prepare_origins([source], folder, inventory, decoder=decoder, decoder_sha256=digest, **options)
        settings.ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE = str(folder)
        settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": "fixture:"}
        settings.CELERY_TASK_DEFAULT_QUEUE = "q"
    cookies = [
        client.cookies[django_settings.SESSION_COOKIE_NAME].value for client in (staff, other)
    ]
    base = live_server.url + f"/{language}/moderation/rights/{case.pk}/"
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            contexts = [
                browser.new_context(viewport={"width": 390, "height": 844}) for _ in cookies
            ]
            for context, cookie in zip(contexts, cookies, strict=True):
                context.add_cookies(
                    [
                        {
                            "name": django_settings.SESSION_COOKIE_NAME,
                            "value": cookie,
                            "url": live_server.url,
                        }
                    ]
                )
            page = contexts[0].new_page()
            page.goto(base + "access/response/")
            page.locator("#id_export").select_option(str(export.pk))
            page.locator("#id_reason").fill(REASON)
            page.locator("#id_response").fill(TEXT)
            page.locator("#id_redaction_confirmed").check()
            if metadata:
                page.locator("#id_scope_inventory").select_option(str(inventory.pk))
                page.locator("#id_coverage_review").select_option(str(coverage_review.pk))
                page.get_by_role("button", name="Inspect access package" if english else "Consultar paquete de acceso", exact=True).click()
                expect(page.locator(".rights-access-coverage")).to_contain_text("metadata_review")
                decisions = json.loads(page.locator("#id_delivery_decisions").input_value())
                assert decisions["resources"]["status"] == "pending"
                assert len(decisions["resources"]["redis_metadata_digest"]) == 64
                for decision in decisions["models"].values():
                    decision.update(status="omitted", reason=REASON)
                decisions["resources"].update(status="reviewed", reason=REASON)
                page.locator("#id_delivery_decisions").fill(json.dumps(decisions))
            page.get_by_role(
                "button",
                name="Save response draft" if english else "Guardar borrador de respuesta",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Final response draft prepared"
                if english
                else "Borrador de respuesta final preparado"
            )
            assert TEXT not in page.locator("body").inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page = contexts[1].new_page()
            page.goto(base)
            page.get_by_role(
                "link", name="Review response" if english else "Revisar respuesta"
            ).click()
            assert TEXT not in page.locator("body").inner_text()
            page.locator("#id_reason").fill(REASON)
            page.get_by_role(
                "button",
                name="Inspect response draft" if english else "Consultar borrador de respuesta",
                exact=True,
            ).click()
            expect(page.locator("body")).to_contain_text(TEXT)
            if metadata:
                expect(page.locator(".rights-access-coverage")).to_contain_text("snapshot_metadata_scope_review")
                expect(page.locator(".rights-access-coverage")).to_contain_text("infrastructure_scope_unreviewed")
            page.locator("#decision_reason").fill(REASON)
            page.locator("#decision_outcome").select_option("approved")
            page.get_by_role(
                "button",
                name="Record independent decision"
                if english
                else "Registrar decisión independiente",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text("approved")
            assert TEXT not in page.locator("body").inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.goto(page.url)
            assert TEXT not in page.locator("body").inner_text()
        finally:
            browser.close()
    draft = RightsAccessResponseDraft.objects.get(request=case)
    review = RightsAccessResponseReview.objects.get(draft=draft)
    assert review.outcome == "approved" and review.action.actor_id == reviewer.pk
    assert draft.actor_id == author.pk and draft.proof_id == proof.pk
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_aux_inspection_requires_exact_metadata_review_and_stays_partial(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    test_mobile_final_response_preparation_and_independent_decision(
        live_server, request, settings, monkeypatch, tmp_path, language, False, metadata=True
    )


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_physical_census_uses_existing_review_and_independent_decision(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    test_mobile_final_response_preparation_and_independent_decision(
        live_server, request, settings, monkeypatch, tmp_path, language, False, metadata="physical"
    )
