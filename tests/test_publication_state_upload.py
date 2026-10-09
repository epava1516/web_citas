"""Image processing ends with a signal-less update; it must still queue the state refresh."""

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401

from apps.core.models import Person, User
from apps.listings import publication_state, tasks
from apps.listings.models import PublicationDirty, Revision
from apps.mediafiles.models import Photo

pytestmark = pytest.mark.django_db(transaction=True)


def test_upload_processing_leaves_no_unrefreshed_mark(request, monkeypatch, client):
    request.getfixturevalue("directory")
    request.getfixturevalue("photo_environment")
    manager = User.objects.get(username="fixture-v1-individual")
    person = Person.objects.get(individual=manager)
    draft = Revision.objects.create(listing=person.listing, manager_version=person.manager_version)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    queued = []
    original = tasks.refresh_publication_state.delay
    monkeypatch.setattr(tasks.refresh_publication_state, "delay",
                        lambda *a, **k: queued.append(1) or original(*a, **k))
    client.force_login(manager)
    assert upload(client, draft, raw_image(782134)).status_code == 302
    photo = Photo.objects.get(revision=draft)
    assert photo.comparison_complete
    # Eager here: every queued refresh ran; the final comparison update was refreshed too.
    assert queued and not PublicationDirty.objects.exists()
