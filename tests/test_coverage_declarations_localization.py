"""Coverage presentation retains raw omission paths and typed exclusion decisions."""

from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from playwright.sync_api import expect

from apps.core.models import User
from apps.safety.models import RightsRequest
from apps.safety.rights_portability_coverage_views import (
    Catalog,
    Decision,
    Decisions,
    ImageCatalog,
    Save,
)

pytestmark = pytest.mark.django_db


def catalog_captions(page, language, images):
    pairs = {
        "review": ("Selección aprobada", "Approved selection"),
        "purpose": ("Motivo privado de consulta", "Private inspection purpose"),
        "field_page": ("Página de imágenes", "Image page")
        if images
        else ("Página de campos", "Field page"),
    }
    if not images:
        pairs.update(
            {"dataset": ("Conjunto de datos", "Dataset"), "row_number": ("Registro", "Record")}
        )
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")


def declaration_captions(page, language):
    expect(page.locator('label[for="id_reason"]')).to_have_text(
        ("Private coverage reason" if language == "en" else "Motivo privado de cobertura") + ":"
    )
    expect(page.locator("#id_paths")).to_be_visible()
    # CheckboxSelectMultiple uses a group label without a for attribute.
    expect(
        page.get_by_text(
            "Justified omissions on this page:"
            if language == "en"
            else "Omisiones justificadas en esta página:",
            exact=True,
        )
    ).to_be_visible()
    for row in page.locator("fieldset").all():
        for name, pair in {
            "basis": ("Base jurídica", "Lawful basis"),
            "origin": ("Origen", "Origin"),
            "automated": ("Tratamiento automatizado", "Automated processing"),
            "subject_related": ("Datos del interesado", "Data concerning the subject"),
            "third_party_reviewed": ("Terceros revisados", "Third parties reviewed"),
            "reason": ("Justificación", "Justification"),
            "evidence": ("Evidencia", "Evidence"),
        }.items():
            expect(row.locator(f'label[for$="-{name}"]')).to_have_text(pair[language == "en"] + ":")


@pytest.mark.parametrize("language", ["es", "en"])
def test_coverage_defaults_lazy_paths_and_exclusion(language):
    case = RightsRequest(pk=123)
    actor = User(pk=456)
    with CaptureQueriesContext(connection) as queries:
        for cls in [Catalog, ImageCatalog]:
            form = cls(case=case, actor=actor, language=language)
            legacy = cls(case=case, actor=actor)
            assert form.fields["review"].label == (
                "Approved selection" if language == "en" else "Selección aprobada"
            )
            assert legacy.fields["review"].label == "Selección aprobada / Approved selection"
        assert (
            ImageCatalog(case=case, actor=actor).fields["field_page"].label
            == "Página de imágenes / Image page"
        )
        paths = ["/literal~1raw_value"]
        form = Save(
            {
                "operation": "save",
                "key": uuid4(),
                "token": "opaque",
                "reason": "Literal / private exclusion reason",
                "paths": paths,
            },
            paths=paths,
            language=language,
        )
        assert (
            form.is_valid() and form.cleaned_data["reason"] == "Literal / private exclusion reason"
        )
        assert form.cleaned_data["paths"] == paths and list(form.fields["paths"].choices) == [
            (paths[0], "literal/raw value")
        ]
        legacy = Save(paths=paths)
        assert (
            legacy.fields["reason"].label == "Motivo privado de cobertura / Private coverage reason"
        )
        assert (
            legacy.fields["paths"].label
            == "Omisiones justificadas en esta página / Justified omissions on this page"
        )
        assert legacy.fields["reason"].max_length == 200
        decision = Decision(
            {
                "path": paths[0],
                "basis": "other",
                "origin": "inferred",
                "automated": "yes",
                "subject_related": "yes",
                "third_party_reviewed": "yes",
                "reason": "Literal / justified synthetic exclusion",
                "evidence": "Literal / synthetic evidence",
            },
            selected_paths=paths,
            language=language,
        )
        assert decision.is_valid(), decision.errors
        assert (
            decision.cleaned_data["automated"] is True
            and decision.cleaned_data["evidence"] == "Literal / synthetic evidence"
        )
        assert not {"dataset", "status"} & decision.fields.keys()
        assert (Decisions.max_num, Decisions.absolute_max, Decisions.validate_max) == (50, 50, True)
        assert len(queries) == 0
