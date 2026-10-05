"""Publication rights remain executable for a represented person without a subject account."""

import pytest
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("mode", ["restrict", "cease"])
def test_publication_and_release_without_subject_account(request, settings, monkeypatch, mode):
    import test_rights_exports

    original_link = test_rights_exports.link
    represented = []

    def without_account(staff, case, person):
        # Synthetic fixture setup before case linking and scoped verification.
        person.subject = None
        person.save(update_fields=["subject"])
        represented.append(person.pk)
        return original_link(staff, case, person)

    monkeypatch.setattr(test_rights_exports, "link", without_account)
    run_flow(request, settings, monkeypatch, mode, mixed=False)
    assert len(represented) == 1
    assert Person.objects.get(pk=represented[0]).subject_id is None
