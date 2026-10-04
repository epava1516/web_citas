"""Docker-only synthetic probe of Redis/worker or Beat; no identity assertions."""

import argparse
import json
import os
import time
import uuid
from datetime import timedelta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--beat", action="store_true", help="Observe Beat without dispatching a task"
    )
    options = parser.parse_args()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings
    from django.db import transaction
    from django.utils import timezone

    from apps.core.models import Person, User
    from apps.safety.crypto import seal
    from apps.safety.models import RightsAction, RightsExport, RightsProof, RightsRequest
    from apps.safety.rights import fingerprint
    from apps.safety.tasks import purge_expired_exports

    assert not settings.PRODUCTION, "Operational synthetic probe prohibited in production"
    marker = uuid.uuid4().hex
    now = timezone.now()
    with transaction.atomic():
        user = User.objects.create_user(
            username="ops-copy-" + marker, email=marker + "@example.invalid"
        )
        person = Person.objects.create(
            individual=user, subject=user, alias="Synthetic copy retention probe"
        )
        case = RightsRequest.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest=fingerprint(marker),
            payload_digest=fingerprint(marker),
            encrypted_payload=seal(
                {"explanation": "Synthetic operational probe, not a rights decision"}
            ),
            kind="access",
            person=person,
            manager_version=1,
            reported_individual=user,
            reported_subject=user,
            received_at=now,
            initial_due_at=now + timedelta(days=1),
            receipt_expires_at=now + timedelta(days=1),
        )
        proof = RightsProof.objects.create(
            key=uuid.uuid4(),
            request=case,
            person=person,
            initiated_by=user,
            case_version=1,
            manager_version=1,
            subject_id_snapshot=str(user.pk),
            scope="access",
            channel_digest=case.receipt_digest,
            provider="simulator",
            procedure="rights-simulator-v1",
            payload_digest=fingerprint(marker),
            encrypted_reason=seal({"reason": "Synthetic task fixture only"}),
            expires_at=now + timedelta(hours=1),
        )
        # Pending proof, no Listing and no usable receipt: never eligible for disclosure.
        copies = []
        for expired in [True, False]:
            action = RightsAction.objects.create(
                key=uuid.uuid4(),
                request=case,
                actor=user,
                expected_version=1,
                operation="export",
                payload_digest=fingerprint(marker + str(expired)),
                encrypted_reason=seal({"reason": "Synthetic retention fixture"}),
            )
            copies.append(
                RightsExport.objects.create(
                    action=action,
                    proof=proof,
                    person=person,
                    case_version=1,
                    manager_version=1,
                    subject_snapshot=str(user.pk),
                    channel_digest=case.receipt_digest,
                    encrypted_payload=seal({"synthetic_only": True, "marker": marker}),
                    expires_at=now + timedelta(seconds=-1 if expired else 3600),
                )
            )
    expired, live = copies
    start = time.monotonic()
    jobs = [] if options.beat else [purge_expired_exports.delay(), purge_expired_exports.delay()]
    print(
        json.dumps(
            {"mode": "beat" if options.beat else "worker", "task_ids": [job.id for job in jobs]}
        ),
        flush=True,
    )
    deadline = start + (75 if options.beat else 20)
    while time.monotonic() < deadline:
        expired.refresh_from_db()
        if expired.purged_at:
            break
        time.sleep(0.1)
    assert expired.purged_at and not expired.encrypted_payload, "Expired copy not purged by worker"
    live.refresh_from_db()
    assert live.purged_at is None and live.encrypted_payload, "Live copy altered"
    assert (
        RightsAction.objects.filter(request=case).count() == 2
        and RightsProof.objects.filter(pk=proof.pk).exists()
    )
    print(
        json.dumps(
            {
                "passed": True,
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "expired_content_removed": True,
                "live_copy_preserved": True,
                "identity_verified": False,
            }
        ),
        flush=True,
    )
    with transaction.atomic():
        RightsExport.objects.filter(action__request=case).delete()
        RightsAction.objects.filter(request=case).delete()
        proof.delete()
        case.delete()
        person.delete()
        user.delete()
    print("Synthetic operational fixture removed; existing application data preserved", flush=True)


if __name__ == "__main__":
    main()
