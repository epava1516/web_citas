"""Scalar selection presentation leaves shared consumers and lazy queries intact."""

from datetime import datetime
from types import SimpleNamespace

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import translation
from playwright.sync_api import expect

from apps.safety.models import RightsRequest
from apps.safety.rights_portability_coverage_views import Catalog, Save
from apps.safety.rights_portability_image_views import ImageCatalogForm
from apps.safety.rights_portability_prepare_selection_views import (
    CatalogForm,
    FieldDecisionForm,
    ResetForm,
    SaveForm,
)

pytestmark = pytest.mark.django_db


def catalog_captions(page, language):
    pairs = {
        "review": ("Evaluación aprobada", "Approved assessment"),
        "dataset": ("Conjunto de datos", "Dataset"),
        "row_number": ("Registro", "Record"),
        "field_page": ("Página de campos", "Field page"),
        "purpose": ("Motivo privado de consulta", "Private inspection purpose"),
    }
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    for option in page.locator("#id_review option").all():
        value = option.get_attribute("value")
        if value:
            assert option.inner_text().startswith(
                "Approved assessment " if language == "en" else "Evaluación aprobada "
            )


@pytest.mark.parametrize("language", ["es", "en"])
def test_optional_language_lazy_shared_and_literal_data(language):
    case = RightsRequest(pk=1234)
    obj = SimpleNamespace(pk=42, assessment=SimpleNamespace(version=3))
    with translation.override(language), CaptureQueriesContext(connection) as queries:
        catalog = CatalogForm(case=case, language=language)
        reset = ResetForm(case=case, language=language)
        assert len(queries) == 0
        sql_before, params_before = catalog.fields["review"].queryset.query.sql_with_params()
        sql_after, params_after = reset.fields["review"].queryset.query.sql_with_params()
        assert sql_before == sql_after and len(params_before) == len(params_after)
        for before, after in zip(params_before, params_after, strict=True):
            if isinstance(before, datetime):
                assert isinstance(after, datetime) and 0 <= (after - before).total_seconds() < 1
            else:
                assert before == after
        expected = "Approved assessment" if language == "en" else "Evaluación aprobada"
        assert catalog.fields["review"].label_from_instance(obj) == f"{expected} 42 · 3"
        assert reset.fields["review"].label_from_instance(obj) == f"{expected} 42 · 3"
        assert reset.fields["confirmed"].required
        assert reset.fields["confirmed"].widget.attrs["id"] == "reset_confirmed"
        original = CatalogForm(case=case)
        assert (
            original.fields["review"].label_from_instance(obj)
            == "Evaluación aprobada / Approved assessment 42 · 3"
        )
        for cls, kwargs in [
            (CatalogForm, {"case": case}),
            (ResetForm, {"case": case}),
            (SaveForm, {"paths": ["/literal~1raw_value"]}),
            (FieldDecisionForm, {}),
        ]:
            form = cls(**kwargs)
            for name, field in form.fields.items():
                if name in cls.base_fields:
                    assert field.label == cls.base_fields[name].label
        for form in [
            ImageCatalogForm(case=case),
            Catalog(case=case, actor=None),
            Save(paths=["/literal"]),
        ]:
            assert " / " in form.fields["review" if "review" in form.fields else "reason"].label
        save = SaveForm(
            {
                "operation": "save",
                "key": "33e6a17c-7f8f-4082-bc68-849e0d53b3c8",
                "token": "opaque",
                "reason": "Literal / unchanged selection reason",
                "paths": ["/literal~1raw_value"],
            },
            paths=["/literal~1raw_value"],
            language=language,
        )
        assert save.is_valid(), save.errors
        assert save.cleaned_data["paths"] == ["/literal~1raw_value"]
        assert save.cleaned_data["reason"] == "Literal / unchanged selection reason"
        assert list(save.fields["paths"].choices) == [("/literal~1raw_value", "literal/raw value")]
        assert len(queries) == 0
