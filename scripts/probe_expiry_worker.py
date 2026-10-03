"""Docker-only synthetic worker probe; never run with production settings."""

import argparse
import os
import time
import uuid
from datetime import timedelta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--beat", action="store_true", help="Wait for Beat; do not dispatch any task"
    )
    options = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings
    from django.utils import timezone

    from apps.core.models import Person, User
    from apps.listings.models import LifecycleAction, Listing
    from apps.listings.tasks import expire_listings

    assert not settings.PRODUCTION, "Synthetic probe prohibited in production"
    user = User.objects.create_user(
        username="ops-expiry-" + uuid.uuid4().hex, email=uuid.uuid4().hex + "@example.invalid"
    )
    person = Person.objects.create(
        individual=user, subject=user, alias="Prueba técnica sintética de caducidad"
    )
    listing = Listing.objects.create(
        person=person,
        status="published",
        expires_at=timezone.now() - timedelta(minutes=1),
        available_until=timezone.now() + timedelta(hours=4),
    )
    # No approved revision; this operational record is never publicly eligible.
    start = time.monotonic()
    jobs = [] if options.beat else [expire_listings.delay(), expire_listings.delay()]
    deadline = time.monotonic() + (75 if options.beat else 20)
    while time.monotonic() < deadline:
        listing.refresh_from_db()
        if listing.status == "expired":
            break
        time.sleep(0.1)
    assert listing.status == "expired" and listing.available_until is None
    assert (
        LifecycleAction.objects.filter(
            listing=listing, operation="expire", actor__isnull=True
        ).count()
        == 1
    )
    assert LifecycleAction.objects.filter(listing=listing, operation="expire").count() == 1
    print(
        f"Real Redis/Celery expiry state passed in {time.monotonic() - start:.3f}s; no real identity or public content"
    )

    print(
        "Dispatched task IDs for independent worker-log verification:",
        ",".join(str(job.id) for job in jobs),
    )


if __name__ == "__main__":
    main()
