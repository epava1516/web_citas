"""Image presentation preserves lazy assessments, controls and private literals."""

from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from playwright.sync_api import expect

from apps.safety.models import RightsRequest
from apps.safety.rights_portability_image_views import ImageCatalogForm, ImageSaveForm
from apps.safety.rights_portability_prepare_selection_views import FieldDecisionForm

pytestmark = pytest.mark.django_db


def image_catalog_captions(page, language):
    pairs = {
        "review": ("Evaluación aprobada", "Approved assessment"),
        "revision_number": ("Revisión", "Revision"),
        "image_number": ("Imagen", "Image"),
        "purpose": ("Motivo privado de consulta", "Private inspection purpose"),
    }
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    for option in page.locator("#id_review option").all():
        if option.get_attribute("value"):
            assert option.inner_text().startswith(
                "Approved assessment " if language == "en" else "Evaluación aprobada "
            )


def image_save_captions(page, language, facts=True):
    for name, pair in {
        "include": ("Incluir esta imagen", "Include this image"),
        "reason": ("Motivo privado del cambio", "Private change reason"),
    }.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    if facts:
        for name, pair in {
            "basis": ("Base jurídica", "Lawful basis"),
            "origin": ("Origen", "Origin"),
            "automated": ("Tratamiento automatizado", "Automated processing"),
            "subject_related": ("Datos del interesado", "Data concerning the subject"),
            "third_party_reviewed": ("Terceros revisados", "Third parties reviewed"),
            "reason": ("Justificación", "Justification"),
            "evidence": ("Evidencia", "Evidence"),
        }.items():
            expect(page.locator(f'label[for="id_image-{name}"]')).to_have_text(
                pair[language == "en"] + ":"
            )


@pytest.mark.parametrize("language", ["es", "en"])
def test_image_forms_schema_defaults_and_literal(language):
    with CaptureQueriesContext(connection) as queries:
        catalog = ImageCatalogForm(case=RightsRequest(pk=123), language=language)
        assert len(queries) == 0
        assert not {"dataset", "row_number", "field_page"} & catalog.fields.keys()
        for name in ["revision_number", "image_number"]:
            assert catalog.fields[name].min_value == 1
        for cls, kwargs in [
            (ImageCatalogForm, {"case": RightsRequest(pk=123)}),
            (ImageSaveForm, {}),
            (FieldDecisionForm, {}),
        ]:
            original = cls(**kwargs)
            for name, field in original.fields.items():
                if name in cls.base_fields:
                    assert field.label == cls.base_fields[name].label
        literal = "Literal / exact private image rationale"
        for included in [True, False]:
            form = ImageSaveForm(
                {
                    "operation": "save",
                    "key": uuid4(),
                    "token": "opaque",
                    "reason": literal,
                    "include": included,
                },
                language=language,
            )
            assert form.is_valid(), form.errors
            assert form.cleaned_data["include"] is included
            assert form.cleaned_data["reason"] == literal and form.cleaned_data["token"] == "opaque"
        assert ImageSaveForm.base_fields["reason"].max_length == 2000
        assert not ImageSaveForm.base_fields["include"].required
        assert len(queries) == 0
