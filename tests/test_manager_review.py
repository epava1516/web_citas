import pytest
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import ManagerReview
from apps.core.verification_services import publication_ready


@pytest.mark.django_db(transaction=True)
def test_transfer_requires_current_human_review_before_readiness(request):
    person, owner, _, _, reviewer = request.getfixturevalue("pending")
    phone = person.phone_claim
    assert owner.post(f"/es/person/{person.pk}/transfer/", {"confirm": "on"}).status_code == 302
    person.refresh_from_db()
    assert person.manager_review_status == "pending" and not publication_ready(person)
    path = f"/es/moderation/managers/{person.pk}/"
    data = {
        "manager_version": person.manager_version,
        "outcome": "approved",
        "reason": "Cambio sintético autorizado y revisado",
    }
    assert owner.get(path).status_code == 403
    assert reviewer.post(path, data).status_code == 400
    assert (
        owner.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "dev-1"}
        ).status_code
        == 302
    )
    assert owner.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 302
    person.refresh_from_db()
    person.phone_claim = phone
    person.save(update_fields=["phone_claim"])
    assert not publication_ready(person)
    assert reviewer.post(path, data).status_code == 302
    person.refresh_from_db()
    assert publication_ready(person) and ManagerReview.objects.count() == 1
    assert reviewer.post(path, data).status_code == 409
