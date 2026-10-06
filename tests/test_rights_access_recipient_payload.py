from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights_access_delivery import recipient_payload


def final_body():
    return {
        "text": "Synthetic reviewed response",
        "simulation": True,
        "access_package": {
            "schema": "access-delivery-v1",
            "partial": False,
            "pending": [],
            "cutoff": "2026-10-06T12:00:00+00:00",
            "review_material": {"internal_original": "private-review-only"},
            "decisions": {"internal_assessment": "private-decision-only"},
            "source": "private-source-only",
            "copy": {
                "base": {"subject_account": {"email": "synthetic@example.invalid"}},
                "additional_records": [],
                "exclusions": [],
                "procedure": {},
                "sessions": [],
                "queued_processing": [],
                "infrastructure_assessment": {"status": "reviewed"},
            },
        },
    }


def synthetic_log_bundle(captured_at, content):
    import hashlib

    from scripts.collect_access_resource_logs import SERVICES

    return {
        "schema": "local-access-log-origins-v1",
        "project": "web-modelos",
        "captured_at": captured_at.isoformat(),
        "records": [
            {
                "service": service,
                "container": "synthetic-container-" + service,
                "image": "synthetic-image",
                "container_created_at": captured_at.isoformat(),
                "stdout": content if service == "app" else "",
                "stderr": "",
                "stdout_sha256": hashlib.sha256(
                    (content if service == "app" else "").encode()
                ).hexdigest(),
                "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            }
            for service in SERVICES
        ],
        "partial": True,
        "pending": [
            "subject_association_and_disclosure_review",
            "historical_or_removed_containers",
            "host_logs_and_mail_retention",
            "cache_and_backup_content_accounting",
        ],
    }


def test_recipient_projection_keeps_copy_without_private_review_envelope():
    body = final_body()
    original = deepcopy(body)
    payload = recipient_payload(body)
    assert payload["copy"] == body["access_package"]["copy"]
    assert payload["response"] == body["text"]
    assert "private-review-only" not in str(payload)
    assert "private-decision-only" not in str(payload)
    assert "private-source-only" not in str(payload)
    payload["copy"]["base"]["subject_account"]["email"] = "changed@example.invalid"
    assert body == original


@pytest.mark.parametrize("change", ["partial", "pending", "unknown_copy_member", "legacy"])
def test_recipient_projection_rejects_incomplete_or_unknown_copy(change):
    body = final_body()
    package = body["access_package"]
    if change == "partial":
        package["partial"] = True
    elif change == "pending":
        package["pending"] = ["infrastructure_content_accounting"]
    elif change == "unknown_copy_member":
        package["copy"]["review_material"] = {"private": "must not be delivered"}
    else:
        del body["access_package"]
    with pytest.raises(ValidationError, match="Complete validated recipient copy"):
        recipient_payload(body)


@pytest.mark.django_db(transaction=True)
def test_session_scope_reads_owned_records_without_exposing_authentication_material(settings):
    from datetime import timedelta

    from django.contrib.sessions.backends.db import SessionStore
    from django.db import connection
    from django.utils import timezone

    from apps.safety.rights_access_delivery import session_records

    assert connection.vendor == "postgresql"
    cutoff = timezone.now()

    def store(owner, **data):
        session = SessionStore()
        session["_auth_user_id"] = str(owner)
        session["_auth_user_hash"] = "synthetic-authentication-material"
        session.update(data)
        session.save()
        return session

    own = store(101, django_language="en", account_version=2, mfa_version=3)
    other = store(102, private_other_account="other-subject-only")
    expired = store(101, expired_subject_data="expired-only")
    expired.set_expiry(cutoff - timedelta(seconds=1))
    expired.save()
    captured = session_records(101, cutoff)
    assert not captured["blocked"]
    assert len(captured["copy"]) == len(captured["evidence"]) == 1
    assert captured["copy"][0]["language"] == "en"
    assert captured["copy"][0]["authenticated"] is True
    assert own.session_key not in str(captured)
    assert other.session_key not in str(captured)
    assert "synthetic-authentication-material" not in str(captured)
    assert "other-subject-only" not in str(captured)
    assert "expired-only" not in str(captured)
    previous = captured["evidence"][0]["content"]
    own["unknown_personal_data"] = "requires-an-adapter"
    own.save()
    changed = session_records(101, cutoff)
    assert changed["evidence"][0]["content"] != previous
    assert changed["blocked"][0]["fields"] == ["unknown_personal_data"]
    assert "requires-an-adapter" not in str(changed)
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
    assert session_records(101, cutoff)["blocked"] == [
        {"resource": "sessions", "reason": "unsupported_session_store"}
    ]


def test_broker_scope_reads_actual_owned_queued_and_reserved_messages_without_consuming(settings):
    from uuid import uuid4

    from kombu import Connection, Producer, Queue
    from redis import Redis

    from apps.safety.rights_access_delivery import broker_records
    from config.celery import app

    token = uuid4().hex
    prefix = "access_resource_" + token + ":"
    queue = "access_resource_" + token
    settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": prefix}
    settings.CELERY_TASK_DEFAULT_QUEUE = queue
    own, other = str(uuid4()), str(uuid4())
    broker = Connection(settings.CELERY_BROKER_URL, transport_options={"global_keyprefix": prefix})
    reserved = None
    try:
        Queue(queue)(broker.default_channel).declare()

        def publish(blob, priority=0):
            message = app.amqp.as_task_v2(
                str(uuid4()), "apps.mediafiles.tasks.process_blob", args=[blob]
            )
            Producer(broker).publish(
                message.body,
                headers=message.headers,
                serializer="json",
                exchange="",
                routing_key=queue,
                priority=priority,
                **message.properties,
            )

        publish(own)
        publish(other)
        publish(own, priority=3)
        with Redis.from_url(settings.CELERY_BROKER_URL) as client:
            key = prefix + queue
            before = client.lrange(key, 0, -1)
            priority_before = client.lrange(key + "\x06\x16" + "3", 0, -1)
            read = broker_records({own})
            assert not read["blocked"], read
            assert len(read["copy"]) == 2
            assert {row["state"] for row in read["copy"]} == {"queued"}
            assert own not in str(read) and other not in str(read)
            assert client.lrange(key, 0, -1) == before
            assert client.lrange(key + "\x06\x16" + "3", 0, -1) == priority_before
            reserved = broker.default_channel.basic_get(queue)
            assert reserved.payload[0] == [own]
            before_unacked = client.hgetall(prefix + "unacked")
            assert before_unacked
            second = broker_records({own})
            assert not second["blocked"], second
            assert len(second["copy"]) == 2
            assert {row["state"] for row in second["copy"]} == {"queued", "reserved"}
            assert client.hgetall(prefix + "unacked") == before_unacked
            assert len(second["evidence"]) == 2
            client.lpush(key, b"invalid-synthetic-message")
            assert broker_records({own})["blocked"][0]["reason"] == "unsupported_message"
            client.lpop(key)
            for _ in range(1001):
                client.lpush(key, b"synthetic-limit-marker")
            assert broker_records({own})["blocked"] == [
                {"resource": "queues", "reason": "bounded_read_limit"}
            ]
    finally:
        if reserved is not None:
            reserved.ack()
        broker.default_channel.queue_delete(queue)
        broker.release()
        with Redis.from_url(settings.CELERY_BROKER_URL) as client:
            remaining = list(client.scan_iter(match=prefix + "*"))
            if remaining:
                client.delete(*remaining)


def test_log_origin_reader_keeps_candidates_private_and_rejects_stale_or_altered_files(
    settings, tmp_path
):
    import hashlib
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.crypto import seal
    from apps.safety.rights_access_delivery import log_records
    from scripts.collect_access_resource_logs import write_bundle

    cutoff = timezone.now() - timedelta(seconds=2)
    own = "synthetic-subject@example.invalid"
    original = f"{cutoff.isoformat()} {own} sensitive-original-log-only\n"
    future = f"{(cutoff + timedelta(seconds=1)).isoformat()} {own} later-event-only\n"
    other = f"{cutoff.isoformat()} another-subject@example.invalid other-subject-only\n"
    body = synthetic_log_bundle(timezone.now(), original + future + other)
    tmp_path.chmod(0o700)
    path = write_bundle(tmp_path, body)
    settings.ACCESS_LOG_ORIGIN_BUNDLE = str(path)
    read = log_records({own}, cutoff)
    assert len(read["origins"]) == 6
    assert len(read["candidates"]) == 1
    assert read["pending"] == body["pending"]
    assert "sensitive-original-log-only" not in str(read)
    assert "later-event-only" not in str(read)
    assert "other-subject-only" not in str(read)
    assert own not in str(read)
    import json

    from scripts.collect_access_resource_logs import signed_subject_log_event

    event = signed_subject_log_event("account", "101", "profile_updated", "succeeded", cutoff)
    lines = [
        event,
        event,
        event | {"private_data": "unadapted-private-only"},
        event | {"operation": {}},
        event | {"schema": "subject-operation-v2"},
        event | {"signature": "invalid-synthetic-signature"},
        {key: value for key, value in event.items() if key != "signature"},
        event | {"subject_id": "102"},
    ]
    body["records"][0]["stdout"] += "".join(
        f"{cutoff.isoformat()} {json.dumps(item)}\n" for item in lines
    )
    body["records"][0]["stdout_sha256"] = hashlib.sha256(
        body["records"][0]["stdout"].encode()
    ).hexdigest()
    path.write_text(seal(body))
    typed = log_records({own}, cutoff, subjects={"account": {"101"}})
    assert len(typed["projected"]) == 2
    assert typed["projected"][0]["reference"] != typed["projected"][1]["reference"]
    assert len(typed["unprojected_candidates"]) == 6
    assert all(row["data"]["operation"] == "profile_updated" for row in typed["projected"])
    assert "unadapted-private-only" not in str(typed)
    assert "subject_id" not in str(typed["projected"][0]["data"])
    with pytest.raises(FileExistsError):
        write_bundle(tmp_path, body)
    path.chmod(0o644)
    with pytest.raises(ValidationError, match="origin unavailable"):
        log_records({own}, cutoff)
    path.chmod(0o600)
    body["captured_at"] = (cutoff - timedelta(seconds=1)).isoformat()
    path.write_text(seal(body))
    with pytest.raises(ValidationError, match="origin unavailable"):
        log_records({own}, cutoff)
    body["captured_at"] = timezone.now().isoformat()
    body["records"][0]["stdout"] += "changed-without-updating-origin-hash"
    path.write_text(seal(body))
    with pytest.raises(ValidationError, match="origin unavailable"):
        log_records({own}, cutoff)


def test_group_projection_preserves_unmodified_data_and_original_review_material():
    from apps.safety.rights_access_delivery import project_group

    rows = [
        {
            "reference": "own-record",
            "data": {
                "description": "Own text; third party",
                "phone": "synthetic-contact",
                "metadata": {"language": "es"},
            },
        }
    ]
    original = deepcopy(rows)
    reason = "Exclude synthetic third party details from the recipient copy"
    records, exclusions = project_group(
        "synthetic.Model",
        rows,
        {
            "status": "redacted",
            "reason": reason,
            "changes": {
                "own-record": {
                    "description": {
                        "status": "redacted",
                        "reason": reason,
                        "value": "Own text; [redacted]",
                    },
                    "phone": {"status": "omitted", "reason": reason},
                }
            },
        },
    )
    assert records[0]["data"] == {
        "description": "Own text; [redacted]",
        "metadata": {"language": "es"},
    }
    assert len(exclusions) == 2
    assert all("third party" not in str(row.get("value", "")) for row in exclusions)
    records[0]["data"]["metadata"]["language"] = "en"
    assert rows == original


@pytest.mark.parametrize("invalid", ["record", "field", "foreign_text", "unchanged", "numeric"])
def test_group_projection_rejects_changes_without_exact_origin(invalid):
    from apps.safety.rights_access_delivery import project_group

    reason = "Review synthetic group scope without inventing recipient content"
    rows = [{"reference": "own-record", "data": {"description": "Original own text", "amount": 42}}]
    changes = {
        "own-record": {
            "description": {"status": "redacted", "reason": reason, "value": "Original [redacted]"}
        }
    }
    if invalid == "record":
        changes["foreign-record"] = changes.pop("own-record")
    elif invalid == "field":
        changes["own-record"]["foreign-field"] = changes["own-record"].pop("description")
    elif invalid == "foreign_text":
        changes["own-record"]["description"]["value"] = "Invented disclosure [redacted]"
    elif invalid == "unchanged":
        changes["own-record"]["description"]["value"] = "Original own text"
    else:
        changes["own-record"]["amount"] = changes["own-record"].pop("description")
    with pytest.raises(ValidationError):
        project_group(
            "synthetic.Model", rows, {"status": "redacted", "reason": reason, "changes": changes}
        )


def test_mail_scope_accounts_for_owned_and_shared_messages_without_releasing_credentials(
    settings, mailoutbox
):
    from django.core.mail import EmailMessage

    from apps.safety.rights_access_delivery import mail_records

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    own = "synthetic-owner@example.invalid"
    message = EmailMessage(
        "Synthetic service notice", "https://example.invalid/reset/private-credential", to=[own]
    )
    message.attach("private.txt", "private-attachment-content", "text/plain")
    assert message.send() == 1
    EmailMessage("Other account", "other-subject-content", to=["other@example.invalid"]).send()
    EmailMessage(
        "Shared notice", "shared-message-content", to=[own], cc=["other@example.invalid"]
    ).send()
    read = mail_records(own.upper())
    assert len(read["records"]) == 2
    assert read["records"][0]["attachment_count"] == 1
    assert read["records"][1]["shared_recipients"] is True
    assert read["pending"] == ["mail_body_headers_and_attachments_projection"]
    assert "private-credential" not in str(read)
    assert "private-attachment-content" not in str(read)
    assert "other-subject-content" not in str(read)
    previous = read["records"][0]["content"]
    mailoutbox[0].body = "changed-owned-message"
    assert mail_records(own)["records"][0]["content"] != previous
    from email.mime.text import MIMEText

    mime_message = EmailMessage(
        "Synthetic MIME notice", "Own message", to=[f"Synthetic Owner <{own}>"]
    )
    mime_message.attach(MIMEText("private-mime-attachment"))
    mime_message.send()
    captured_mime = mail_records(own)
    assert len(captured_mime["records"]) == 3
    assert "private-mime-attachment" not in str(captured_mime)
    prior_mime = captured_mime["records"][-1]["content"]
    mailoutbox[-1].attachments[0].set_payload("changed-private-mime-attachment")
    assert mail_records(own)["records"][-1]["content"] != prior_mime
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    assert mail_records(own)["pending"] == ["mail_backend_content_accounting"]


@pytest.mark.django_db
def test_account_mail_projection_checks_database_owner_and_never_releases_link(
    settings, mailoutbox
):
    import hashlib
    from datetime import timedelta

    from django.core.mail import EmailMessage
    from django.utils import timezone

    from apps.core.models import AccountToken, User
    from apps.safety.rights_access_delivery import mail_records

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    owner = User.objects.create(username="mail-owner", email="mail-owner@example.invalid")
    other = User.objects.create(username="mail-other", email="mail-other@example.invalid")
    raw = "synthetic-private-capability"
    token = AccountToken.objects.create(
        user=owner,
        digest=hashlib.sha256(raw.encode()).hexdigest(),
        purpose="reset",
        expires_at=timezone.now() - timedelta(hours=1),
        used_at=timezone.now(),
    )
    prefix = "Enlace de un solo uso / Single-use link:\n"
    url = settings.PUBLIC_ORIGIN + f"/en/account/token/{token.pk}/{raw}/"
    EmailMessage(
        "Confirmación de cuenta / Account confirmation",
        prefix + url,
        settings.DEFAULT_FROM_EMAIL,
        [owner.email],
    ).send()
    read = mail_records(owner.email, owner=owner.pk)
    assert read["pending"] == []
    assert read["projected"][0]["data"]["body"] == prefix + "[redacted]"
    assert read["projected"][0]["data"]["purpose"] == "reset"
    assert raw not in str(read)
    assert str(token.pk) not in str(read)
    assert token.digest not in str(read)
    assert mail_records(owner.email, owner=other.pk)["projected"] == []
    original = mailoutbox[0].body
    for altered in [original + "?extra=data", original.replace(raw, "wrong-capability")]:
        mailoutbox[0].body = altered
        rejected = mail_records(owner.email, owner=owner.pk)
        assert rejected["projected"] == []
        assert rejected["pending"] == ["mail_body_headers_and_attachments_projection"]
    mailoutbox[0].body = original
    mailoutbox[0].cc = [other.email]
    assert mail_records(owner.email, owner=owner.pk)["projected"] == []
    mailoutbox[0].cc = []
    token.user = other
    token.save(update_fields=["user"])
    assert mail_records(owner.email, owner=owner.pk)["projected"] == []


def synthetic_resource_census(case, inventory, scope):
    """An explicit operator-origin fixture, never evidence of real host coverage."""
    from django.utils import timezone

    from apps.safety.rights import fingerprint
    from apps.safety.rights_access_delivery import RESOURCE_CATEGORIES
    from apps.safety.rights_exports import canonical

    sessions = {"copy": scope["sessions"], "evidence": scope["session_evidence"], "blocked": []}
    queues = {
        "copy": scope["queued_processing"],
        "evidence": scope["queue_evidence"],
        "blocked": [],
    }
    return {
        "schema": "access-retained-resources-v1",
        "request": str(case.pk),
        "inventory": inventory.pk,
        "source": inventory.source_digest,
        "cutoff": inventory.created_at.isoformat(),
        "captured_at": timezone.now().isoformat(),
        "dependencies": {
            "logs": fingerprint(canonical(scope["log_origins"])),
            "mail": fingerprint(canonical(scope["mail_scope"])),
            "sessions": fingerprint(canonical(sessions)),
            "queues": fingerprint(canonical(queues)),
        },
        "categories": {
            category: {
                "reason": "Synthetic bounded retention census for adapter verification only",
                "pending": [],
                "origins": [
                    {
                        "reference": "synthetic-source-" + category,
                        "method": "configuration_inspection",
                        "evidence": "Synthetic configured retention fixture; no external coverage accredited",
                        "records": [],
                        "records_digest": fingerprint(canonical([])),
                    }
                ],
            }
            for category in RESOURCE_CATEGORIES
        },
    }


def test_resource_census_binds_actual_required_records_and_rejects_scope_or_digest_changes(
    settings, tmp_path
):
    from types import SimpleNamespace

    from django.utils import timezone

    from apps.safety.crypto import seal
    from apps.safety.rights import fingerprint
    from apps.safety.rights_access_delivery import retained_resource_records
    from apps.safety.rights_exports import canonical

    case = SimpleNamespace(pk="synthetic-case", account_subject_id=101)
    inventory = SimpleNamespace(pk=12, source_digest="synthetic-source", created_at=timezone.now())
    scope = {
        "sessions": [],
        "session_evidence": [],
        "queued_processing": [],
        "queue_evidence": [],
        "mail_scope": {},
        "log_origins": {},
    }
    body = synthetic_resource_census(case, inventory, scope)
    row = {
        "subject_kind": "account",
        "subject_id": "101",
        "created_at": inventory.created_at.isoformat(),
        "content": "synthetic-own-event private-original",
        "source_reference": "known-log",
    }
    origin = body["categories"]["logs"]["origins"][0]
    origin["method"] = "structured_archive"
    origin["records"] = [
        row,
        row
        | {
            "subject_id": "102",
            "source_reference": None,
            "content": "synthetic-foreign-resource-private-content",
        },
    ]
    origin["records_digest"] = fingerprint(canonical(origin["records"]))
    path = tmp_path / "resource-census.encrypted"
    path.write_text(seal(body))
    path.chmod(0o600)
    settings.ACCESS_RESOURCE_ORIGIN_BUNDLE = str(path)
    required = {"logs": {"known-log": fingerprint(row["content"])}, "mail": {}}
    read = retained_resource_records(case, None, inventory, body["dependencies"], required)
    assert not read["pending"]
    assert len(read["groups"]) == 1
    assert read["groups"][0]["data"]["content"] == row["content"]
    assert "synthetic-foreign-resource-private-content" not in str(read)
    assert all("subject_id" not in item["data"] for item in read["groups"])
    assert len(read["origins"]) == 5
    origin["records"] = []
    origin["records_digest"] = fingerprint(canonical([]))
    path.write_text(seal(body))
    assert retained_resource_records(case, None, inventory, body["dependencies"], required)[
        "pending"
    ] == ["logs:unaccounted_retained_records"]
    body["request"] = "another-case"
    path.write_text(seal(body))
    with pytest.raises(ValidationError, match="census unavailable"):
        retained_resource_records(case, None, inventory, body["dependencies"], required)
    body["request"] = str(case.pk)
    origin["records"] = [row | {"content": "invented-other-content"}]
    origin["records_digest"] = fingerprint(canonical(origin["records"]))
    path.write_text(seal(body))
    with pytest.raises(ValidationError, match="census unavailable"):
        retained_resource_records(case, None, inventory, body["dependencies"], required)
    path.chmod(0o644)
    with pytest.raises(ValidationError, match="census unavailable"):
        retained_resource_records(case, None, inventory, body["dependencies"], required)


def test_resource_copy_never_delivers_unreviewed_originals_or_closes_on_generic_assessment():
    from types import SimpleNamespace

    from django.utils import timezone

    from apps.safety.rights_access_delivery import compile_package

    cutoff = timezone.now()
    inventory = SimpleNamespace(pk=12, created_at=cutoff)
    export = SimpleNamespace(pk="synthetic-export")
    reason = "Synthetic disclosure with an independently reviewed resource census"
    original = {
        "source": "synthetic-source",
        "groups": {
            "operations.RetainedResource": [
                {
                    "reference": "original-record",
                    "data": {"content": "Own event private-secret"},
                    "technical_fields_excluded": [],
                }
            ]
        },
        "blocked": [],
        "mail_scope": {"projected": []},
        "resource_scope": {"configured": True, "pending": [], "digest": "exact-census"},
        "infrastructure": {"storage": "local", "verification": "simulator", "production": False},
        "procedure": {},
        "sessions": [],
        "queued_processing": [],
    }
    decisions = {
        "models": {"operations.RetainedResource": {"status": "included", "reason": reason}},
        "resources": {"status": "reviewed", "reason": reason, "origin_digest": "exact-census"},
    }
    with pytest.raises(ValidationError, match="explicit redaction or omission"):
        compile_package(inventory, export, original, decisions, cutoff=cutoff, projected={})
    decisions["models"]["operations.RetainedResource"] = {
        "status": "redacted",
        "reason": reason,
        "changes": {
            "original-record": {
                "content": {
                    "status": "redacted",
                    "reason": reason,
                    "value": "Own event [redacted]",
                }
            }
        },
    }
    package = compile_package(inventory, export, original, decisions, cutoff=cutoff, projected={})
    assert package["partial"] is False
    assert package["pending"] == []
    assert "private-secret" not in str(package["copy"])
    assert "origin_digest" not in str(package["copy"])
    assert (
        original["groups"]["operations.RetainedResource"][0]["data"]["content"]
        == "Own event private-secret"
    )
    del decisions["resources"]["origin_digest"]
    assert compile_package(inventory, export, original, decisions, cutoff=cutoff, projected={})[
        "pending"
    ] == ["infrastructure_content_accounting"]


def test_private_resource_directory_retains_independent_origins_for_two_cases(settings, tmp_path):
    from types import SimpleNamespace
    from uuid import uuid4

    from django.utils import timezone

    from apps.safety.crypto import seal
    from apps.safety.rights_access_delivery import retained_resource_records
    from scripts.collect_access_resource_logs import scoped_origin_name

    tmp_path.chmod(0o700)
    settings.ACCESS_RESOURCE_ORIGIN_BUNDLE = str(tmp_path)
    scope = {
        "sessions": [],
        "session_evidence": [],
        "queued_processing": [],
        "queue_evidence": [],
        "mail_scope": {},
        "log_origins": {},
    }
    cases = [
        SimpleNamespace(pk=uuid4(), account_subject_id=101 + position) for position in range(2)
    ]
    inventories = [
        SimpleNamespace(
            pk=12 + position, source_digest="synthetic-source", created_at=timezone.now()
        )
        for position in range(2)
    ]
    artifacts = []
    for case, inventory in zip(cases, inventories, strict=True):
        body = synthetic_resource_census(case, inventory, scope)
        path = tmp_path / scoped_origin_name("resources", case.pk, inventory.pk)
        path.write_text(seal(body))
        path.chmod(0o600)
        artifacts.append((path, body))
    reads = [
        retained_resource_records(
            case, None, inventory, body["dependencies"], {"logs": {}, "mail": {}}
        )
        for case, inventory, (_, body) in zip(cases, inventories, artifacts, strict=True)
    ]
    assert all(not item["pending"] for item in reads)
    assert reads[0]["digest"] != reads[1]["digest"]
    second_path, second_body = artifacts[1]
    second_body["categories"]["backups"]["reason"] += " changed"
    second_path.write_text(seal(second_body))
    assert (
        retained_resource_records(
            cases[0],
            None,
            inventories[0],
            artifacts[0][1]["dependencies"],
            {"logs": {}, "mail": {}},
        )
        == reads[0]
    )
    first_path, first_body = artifacts[0]
    first_path.write_text(seal(second_body))
    with pytest.raises(ValidationError, match="census unavailable"):
        retained_resource_records(
            cases[0], None, inventories[0], first_body["dependencies"], {"logs": {}, "mail": {}}
        )
    tmp_path.chmod(0o750)
    with pytest.raises(ValidationError, match="Private scoped resource"):
        retained_resource_records(
            cases[0], None, inventories[0], first_body["dependencies"], {"logs": {}, "mail": {}}
        )
    with pytest.raises(ValueError):
        scoped_origin_name("resources", "../../untrusted", 12)


def test_private_log_directory_writes_scoped_immutable_archives(settings, tmp_path):
    from types import SimpleNamespace
    from uuid import uuid4

    from django.utils import timezone

    from apps.safety.rights_access_delivery import log_records
    from scripts.collect_access_resource_logs import write_bundle

    cutoff = timezone.now()
    tmp_path.chmod(0o700)
    settings.ACCESS_LOG_ORIGIN_BUNDLE = str(tmp_path)
    cases = [SimpleNamespace(pk=uuid4()) for _ in range(2)]
    inventories = [SimpleNamespace(pk=12 + position) for position in range(2)]
    paths = []
    for case, inventory in zip(cases, inventories, strict=True):
        own = str(case.pk) + "@example.invalid"
        content = cutoff.isoformat() + " " + own + " private-scoped-log\n"
        body = synthetic_log_bundle(timezone.now(), content)
        path = write_bundle(tmp_path, body, case_id=case.pk, inventory_id=inventory.pk)
        paths.append(path)
        read = log_records({own}, cutoff, case=case, inventory=inventory)
        assert len(read["candidates"]) == 1
        assert "private-scoped-log" not in str(read)
        with pytest.raises(FileExistsError):
            write_bundle(tmp_path, body, case_id=case.pk, inventory_id=inventory.pk)
    assert paths[0] != paths[1]
    with pytest.raises(ValidationError, match="Private scoped resource"):
        log_records({"unknown@example.invalid"}, cutoff)
