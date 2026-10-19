import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.catalog.models import GeographicSource, Municipality, PostalCode, Region


def dataset():
    return {
        "source": {
            "key": "import-demo",
            "origin": "Project-owned synthetic fixture",
            "license": "Project-owned fixture",
            "version": "1",
            "synthetic": True,
        },
        "regions": [{"code": "imp-r", "name": "Demo region"}],
        "provinces": [{"code": "imp-p", "name": "Demo province", "region": "imp-r"}],
        "municipalities": [
            {"code": "imp-c1", "name": "Demo one", "province": "imp-p"},
            {"code": "imp-c2", "name": "Demo two", "province": "imp-p"},
        ],
        "postal_codes": [{"code": "01002", "municipalities": ["imp-c1", "imp-c2"]}],
    }


@pytest.mark.django_db
def test_import_idempotent_preserves_postal_correspondence_and_privacy(tmp_path):
    file = tmp_path / "dataset.json"
    file.write_text(json.dumps(dataset()))
    call_command("import_geography", str(file))
    city_id = Municipality.objects.get(code="imp-c1").pk
    call_command("import_geography", str(file))
    assert Municipality.objects.count() == 2
    assert Municipality.objects.get(code="imp-c1").pk == city_id
    postal = PostalCode.objects.get(code="01002")
    assert postal.municipalities.count() == 2 and not postal.public_safe
    source = GeographicSource.objects.get()
    assert source.synthetic and source.license == "Project-owned fixture"


@pytest.mark.django_db
def test_invalid_import_rolls_back_whole_dataset(tmp_path):
    data = dataset()
    data["municipalities"][1]["province"] = "unknown"
    file = tmp_path / "invalid.json"
    file.write_text(json.dumps(data))
    with pytest.raises(CommandError):
        call_command("import_geography", str(file))
    assert not GeographicSource.objects.exists() and not Region.objects.exists()
    data = dataset()
    del data["source"]["license"]
    file.write_text(json.dumps(data))
    with pytest.raises(CommandError):
        call_command("import_geography", str(file))
    assert not Region.objects.exists()


@pytest.mark.django_db
def test_versioned_update_preserves_ids_and_rejects_partial_replacement(tmp_path):
    file = tmp_path / "versioned.json"
    file.write_text(json.dumps(dataset()))
    call_command("import_geography", str(file))
    region_id = Region.objects.get(code="imp-r").pk
    city_id = Municipality.objects.get(code="imp-c1").pk
    postal_id = PostalCode.objects.get(code="01002").pk

    updated = dataset()
    updated["source"]["version"] = "2"
    updated["regions"][0]["name"] = "Renamed synthetic region"
    updated["municipalities"][0].update(name="Renamed synthetic city", active=False)
    updated["postal_codes"][0].update(municipalities=["imp-c2"], public_safe=True)
    file.write_text(json.dumps(updated))
    call_command("import_geography", str(file))

    assert Region.objects.get(code="imp-r").pk == region_id
    city = Municipality.objects.get(code="imp-c1")
    assert city.pk == city_id and city.name == "Renamed synthetic city" and not city.active
    postal = PostalCode.objects.get(code="01002")
    assert postal.pk == postal_id and postal.public_safe
    assert list(postal.municipalities.values_list("code", flat=True)) == ["imp-c2"]
    assert GeographicSource.objects.get(key="import-demo").version == "2"

    # A malformed later update must retain both provenance and the previous data.
    updated["source"]["version"] = "3"
    updated["regions"][0]["name"] = "Must roll back"
    updated["municipalities"][0]["province"] = "unknown"
    file.write_text(json.dumps(updated))
    with pytest.raises(CommandError):
        call_command("import_geography", str(file))
    assert GeographicSource.objects.get(key="import-demo").version == "2"
    region = Region.objects.get(code="imp-r")
    assert region.pk == region_id and region.name == "Renamed synthetic region"
    city.refresh_from_db()
    postal.refresh_from_db()
    assert city.name == "Renamed synthetic city" and not city.active
    assert postal.pk == postal_id and postal.public_safe
    assert list(postal.municipalities.values_list("code", flat=True)) == ["imp-c2"]
