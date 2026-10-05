import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_selection import pointer_value


def test_catalog_paths_select_exact_scalars_including_escaped_keys():
    row = {"a/b": {"~name": ["first", {"": False}, None]}, "empty": {}, "list": []}
    choices = list(scalar_fields(row))
    assert choices == [
        {"path": "/a~1b/~0name/0", "value": "first"},
        {"path": "/a~1b/~0name/1/", "value": False},
        {"path": "/a~1b/~0name/2", "value": None},
    ]
    assert all(pointer_value(row, item["path"]) == item["value"] for item in choices)


@pytest.mark.parametrize("row", ["scalar", None, {1: "invalid object key"}])
def test_catalog_rejects_non_object_rows_and_non_string_keys(row):
    with pytest.raises(ValidationError):
        list(scalar_fields(row))
