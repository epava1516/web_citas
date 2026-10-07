"""Synthetic out-of-page probes for the observed rule fingerprint boundary."""
from functools import wraps

import pytest
from django.core.exceptions import ValidationError
from django.forms import models as model_forms
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("mutation", ["semantic_wrap", "construct_instance"])
def test_out_of_page_runtime_rule_probe(request, monkeypatch, record_property, mutation):
    client = request.getfixturevalue("directory")
    populate(50)
    query = candidates({})
    baseline = native_ids(query)
    target = query.get(pk=baseline[-1]).approved_revision_id
    assert len(baseline) == 50
    assert baseline.index(query.get(approved_revision_id=target).pk) == 49
    before = projection.definitions_digest()
    if mutation == "semantic_wrap":
        original = Revision.clean

        @wraps(original)
        def changed(instance):
            original(instance)
            if instance.pk == target:
                raise ValidationError("Synthetic PK-dependent rule")

        monkeypatch.setattr(Revision, "clean", changed)
    else:
        original = model_forms.construct_instance

        def changed(form, instance, *args, **kwargs):
            if instance.pk == target:
                raise ValidationError("Synthetic helper rule")
            return original(form, instance, *args, **kwargs)

        monkeypatch.setattr(model_forms, "construct_instance", changed)
    native = native_ids(candidates({}))
    projected = projection.ProjectedPublication(candidates({})).visible_ids(candidates({}))
    observed = client.get("/es/")
    record_property("runtime_probe", {
        "mutation": mutation, "target_position": 49,
        "fingerprint_changed": projection.definitions_digest() != before,
        "supported": projection.supported(), "native_count": len(native),
        "projected_count": len(projected),
        "served_count": observed.context["page"].paginator.count,
        "page1_order_equal": [row.pk for row in observed.context["page"]] == native[:24],
        "eligibility_equal": projected == native,
    })
    # Initial reproduction: replace by the regression contract after correction.
    assert len(native) == 49 and len(projected) == 50
    assert projection.definitions_digest() == before and projection.supported()
    assert observed.context["page"].paginator.count == 50
    assert [row.pk for row in observed.context["page"]] == native[:24]
