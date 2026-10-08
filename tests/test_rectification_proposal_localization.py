"""Proposal screen presentation with equivalent native changes, identifiers and photo order."""

from copy import deepcopy
from uuid import uuid4

import pytest
from playwright.sync_api import expect
from test_reset_localization import db_sync

from apps.safety import rectification_details, rectification_photos, rectification_rates
from apps.safety.models import RightsAction
from apps.safety.rectification_presentation import editors
from apps.safety.rights_rectification import ProposalForm

pytestmark = pytest.mark.django_db(transaction=True)


def assert_screen(page, language):
    en = language == "en"
    captions = {
        "operation": ("Operación", "Operation"),
        "purpose": ("Motivo de consulta", "Access purpose"),
        "fields": ("Campos que se propone corregir", "Fields proposed for correction"),
        "account_first_name": ("Nombre de cuenta", "Account first name"),
        "account_last_name": ("Apellidos de cuenta", "Account last name"),
        "account_email": ("Correo de cuenta", "Account email"),
        "alias": ("Nombre del perfil", "Profile name"),
        "title": ("Título", "Title"),
        "description": ("Descripción", "Description"),
        "description_alternative": ("Descripción alternativa", "Alternative description"),
        "municipality": ("Ciudad", "City"),
        "postal_code": ("Código postal", "Postal code"),
        "zone": ("Zona", "Area"),
        "categories": ("Categorías", "Categories"),
        "services": ("Servicios", "Services"),
        "phone": ("Teléfono ya verificado", "Already verified phone"),
        "whatsapp": ("WhatsApp", "WhatsApp"),
        "telegram": ("Telegram", "Telegram"),
        "reason": ("Motivo privado", "Private reason"),
        "content_language": ("Idioma del contenido", "Content language"),
        "profile_type": ("Tipo de perfil", "Profile type"),
        "spoken_languages": ("Idiomas hablados", "Spoken languages"),
        "days": ("Días", "Days"),
        "time_slot": ("Horario", "Time slot"),
        "reception": ("Recepción", "Reception"),
        "travel": ("Desplazamiento", "Travel"),
        "travel_areas": ("Ciudades de desplazamiento", "Travel cities"),
    }
    for pair in captions.values():
        expect(page.get_by_text(pair[en] + ":", exact=True).first).to_be_visible()
    assert page.locator("[name=operation] option").evaluate_all(
        "nodes=>nodes.map(n=>[n.value,n.textContent])"
    ) == [
        ["preview", "Inspect source (audited)" if en else "Consultar fuente (auditoría)"],
        ["propose", "Record proposal" if en else "Registrar propuesta"],
    ]
    expect(
        page.get_by_text(
            "Recommended; no street address" if en else "Recomendado; sin domicilio", exact=True
        )
    ).to_be_visible()
    for label in page.locator("[name=fields]").evaluate_all(
        "nodes=>nodes.map(n=>n.closest('label').textContent)"
    ):
        assert " / " not in label
    for name, pair in {
        "concept": ("Concepto", "Concept"),
        "mode": ("Modalidad", "Mode"),
        "amount": ("Importe", "Amount"),
        "duration_minutes": ("Duración en minutos", "Duration in minutes"),
        "DELETE": ("Eliminar", "Delete"),
    }.items():
        expect(page.locator(f'label[for="id_rates-0-{name}"]')).to_have_text(pair[en] + ":")
    assert page.locator("[name=rates-0-mode] option").evaluate_all(
        "nodes=>nodes.filter(n=>n.value).map(n=>[n.value,n.textContent])"
    ) == [
        ["fixed", "Fixed" if en else "Fijo"],
        ["from", "From" if en else "Desde"],
        ["consult", "Consult" if en else "Consultar"],
    ]
    for field in page.locator("[name^=photos-][name$=-position]").all():
        prefix = field.get_attribute("name").removesuffix("position")
        for name, pair in {
            "position": ("Orden", "Order"),
            "state": ("Estado", "State"),
            "DELETE": ("Eliminar", "Delete"),
        }.items():
            expect(page.locator(f'label[for="id_{prefix}{name}"]')).to_have_text(pair[en] + ":")
        assert " / " not in page.locator(f'[name="{prefix}state"]').input_value()


def assert_if_present(page, language):
    if page.locator("[name=fields]").count():
        assert_screen(page, language)


def check_missing_selection(page, language, case_id):
    before = db_sync(lambda: RightsAction.objects.filter(request_id=case_id).count())
    page.locator("[name=operation]").select_option("propose")
    with page.expect_response(lambda response: response.request.method == "POST") as pending:
        page.locator("button[type=submit]").click()
    assert pending.value.status == 400
    expect(page.locator(".errorlist")).to_have_text(
        "Select fields proposed for correction"
        if language == "en"
        else "Selecciona los campos que se propone corregir"
    )
    assert_screen(page, language)
    assert db_sync(lambda: RightsAction.objects.filter(request_id=case_id).count()) == before
    page.locator("[name=operation]").select_option("preview")


@pytest.mark.parametrize("language", ["es", "en"])
def test_localization_preserves_proposal_changes_and_photo_selection(language):
    native = rectification_details.Editor.base_fields["profile_type"].label
    data = {
        "key": str(uuid4()),
        "version": 1,
        "operation": "propose",
        "fields": ["alias"],
        "alias": "Synthetic proposed alias",
        "reason": "Independent synthetic reason for a scoped proposed change",
    }
    form = ProposalForm(data, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["changes"] == {"alias": "Synthetic proposed alias"}
    assert rectification_details.Editor.base_fields["profile_type"].label == native
    assert " / " in native
    ids = [str(uuid4()), str(uuid4())]
    initial = [
        {"photo_id": ids[0], "position": 1, "state": "Ready / Preparada"},
        {"photo_id": ids[1], "position": 0, "state": "Failed / Fallida"},
    ]
    values = {
        "photos-TOTAL_FORMS": 2,
        "photos-INITIAL_FORMS": 2,
        "photos-MIN_NUM_FORMS": 0,
        "photos-MAX_NUM_FORMS": 8,
        "photos-0-photo_id": ids[0],
        "photos-0-position": 1,
        "photos-1-photo_id": ids[1],
        "photos-1-position": 0,
    }
    before = rectification_photos.Editor(values, initial=deepcopy(initial), prefix="photos")
    after = rectification_photos.Editor(values, initial=deepcopy(initial), prefix="photos")
    rates = rectification_rates.Editor(prefix="rates")
    original_modes = [v for v, _ in rates.forms[0].fields["mode"].choices]
    editors(rates, after, language)
    assert before.is_valid() and after.is_valid()
    assert (
        rectification_photos.changes(before)
        == rectification_photos.changes(after)
        == [ids[1], ids[0]]
    )
    assert [v for v, _ in rates.forms[0].fields["mode"].choices] == original_modes
    assert after.forms[0].fields["state"].disabled
    assert after.forms[0].initial["state"] == ("Ready" if language == "en" else "Preparada")
