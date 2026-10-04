import io
import uuid
import zipfile

import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights_copy_parts import IMAGE_LIMIT, packages


def test_packages_fit_actual_zip_size_without_losing_or_duplicating_content():
    rows = [(uuid.uuid4(), bytes([value]) * 100) for value in range(5)]
    parts = list(packages(iter(rows), limit=538))
    assert len(parts) == 3 and all(len(part["content"]) <= 538 for part in parts)
    recovered = {}
    for part in parts:
        with zipfile.ZipFile(io.BytesIO(part["content"])) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == [
                identifier + ".webp" for identifier in part["attachments"]
            ]
            recovered.update({name[:-5]: archive.read(name) for name in archive.namelist()})
    assert recovered == {str(identifier): content for identifier, content in rows}
    assert list(packages(rows, limit=538)) == parts


@pytest.mark.parametrize(
    "identifier,content",
    [("../../secret", b"x"), (uuid.uuid4(), b""), (uuid.uuid4(), b"x" * (IMAGE_LIMIT + 1))],
)
def test_unsafe_or_oversized_snapshot_is_rejected(identifier, content):
    with pytest.raises(ValidationError):
        list(packages([(identifier, content)]))


def test_single_attachment_over_limit_and_duplicate_rejected():
    identifier = uuid.uuid4()
    with pytest.raises(ValidationError):
        list(packages([(identifier, b"x" * 100)], limit=200))
    with pytest.raises(ValidationError):
        list(packages([(identifier, b"x"), (identifier, b"y")]))
    assert list(packages([])) == []
