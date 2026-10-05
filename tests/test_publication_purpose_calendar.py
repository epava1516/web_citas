"""A calendar follow-up records history and leaves release conditions intact."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.models import PrivacyPublicationHold
from apps.safety.publication_purpose_calendar import follow_up

pytestmark = pytest.mark.django_db(transaction=True)


def test_follow_up_preserves_initial_date_active_measure_and_replays(
    request, settings, monkeypatch
):
    import apps.safety.publication_purpose_release as module

    original = module.inspect
    events = []

    def inspect_after_follow_up(user, case_id, hold_id, key, version, reason):
        if not events:
            user.user_permissions.add(Permission.objects.get(codename="review_purpose_calendar"))
            release_permission = Permission.objects.get(codename="release_purpose_restriction")
            user.user_permissions.remove(release_permission)
            hold = PrivacyPublicationHold.objects.get(pk=hold_id)
            initial = hold.initial_purpose_review_on
            event_key = uuid4()
            when = timezone.localdate() + timedelta(days=14)
            client = Client()
            client.force_login(user)
            session = client.session
            session["mfa_version"] = user.mfa_version
            session.save()
            path = reverse(
                "publication_purpose_release", kwargs={"case_id": case_id, "hold_id": hold_id}
            )
            queue_page = client.get(reverse("publication_calendar_queue"), {"attention": "all"})
            assert queue_page.status_code == 200
            assert [row.pk for row in queue_page.context["restrictions"]] == [hold_id]
            assert reason.encode() not in queue_page.content
            queue_path = reverse("publication_calendar_queue")
            due = client.get(queue_path, {"attention": "due"})
            assert due.status_code == 200 and not due.context["restrictions"]
            soon = client.get(queue_path, {"attention": "soon"})
            assert soon.status_code == 200
            assert [row.pk for row in soon.context["restrictions"]] == [hold_id]
            ceased = client.get(queue_path, {"attention": "all", "mode": "cease"})
            assert ceased.status_code == 200 and not ceased.context["restrictions"]
            assert client.get(queue_path, {"attention": "invalid"}).status_code == 400
            bad_cursor = client.get(queue_path, {"attention": "all", "cursor": "damaged-cursor"})
            assert bad_cursor.status_code == 400 and "no-store" in bad_cursor["Cache-Control"]
            assert client.post(queue_path, {}).status_code == 405
            calendar_permission = Permission.objects.get(codename="review_purpose_calendar")
            user.user_permissions.remove(calendar_permission)
            assert client.get(queue_path, {"attention": "all"}).status_code == 403
            user.user_permissions.add(calendar_permission)
            hold.refresh_from_db()
            assert hold.active and hold.purpose_review_on == initial
            from apps.safety.crypto import seal
            from apps.safety.models import ProcessingExecution, RightsAction

            original_execution = hold.purpose_execution
            clones = []
            # Synthetic queue projection fixtures, not 100 reviewed rights procedures.
            for _ in range(100):
                action_row = RightsAction.objects.create(
                    key=uuid4(),
                    request=hold.action.request,
                    actor=hold.action.actor,
                    expected_version=version,
                    operation="processing_execute",
                    payload_digest="0" * 64,
                    encrypted_reason=seal({"reason": "Synthetic queue fixture"}),
                )
                clone = PrivacyPublicationHold.objects.create(
                    action=action_row,
                    proof=hold.proof,
                    person=hold.person,
                    subject_snapshot=hold.subject_snapshot,
                    manager_version=hold.manager_version,
                    ground=hold.ground,
                    purpose_review_on=initial,
                    initial_purpose_review_on=initial,
                )
                execution_row = ProcessingExecution.objects.create(
                    action=action_row,
                    review=original_execution.review,
                    proof=hold.proof,
                    person=hold.person,
                    source_digest=original_execution.source_digest,
                    encrypted_result=original_execution.encrypted_result,
                    publication_hold=clone,
                )
                clones.append((execution_row, clone, action_row))
            first = client.get(queue_path, {"attention": "all"})
            assert first.status_code == 200 and len(first.context["restrictions"]) == 100
            token = first.context["next_cursor"]
            assert token
            second = client.get(queue_path, {"attention": "all", "cursor": token})
            assert second.status_code == 200 and len(second.context["restrictions"]) == 1
            assert second.context["next_cursor"] is None
            assert not {row.pk for row in first.context["restrictions"]} & {
                row.pk for row in second.context["restrictions"]
            }
            assert client.get(queue_path, {"attention": "soon", "cursor": token}).status_code == 400
            token_body = unseal(token)
            for field, invalid_value in [
                ("session", user.session_version + 1),
                ("mfa", user.mfa_version + 1),
                ("expires", (timezone.now() - timedelta(seconds=1)).isoformat()),
                ("pk", True),
            ]:
                crafted = seal(token_body | {field: invalid_value})
                assert (
                    client.get(queue_path, {"attention": "all", "cursor": crafted}).status_code
                    == 400
                )
            other_actor = hold.action.actor
            other_actor.user_permissions.add(calendar_permission)
            other_client = Client()
            other_client.force_login(other_actor)
            other_session = other_client.session
            other_session["mfa_version"] = other_actor.mfa_version
            other_session.save()
            assert other_client.get(queue_path, {"attention": "all"}).status_code == 200
            assert (
                other_client.get(queue_path, {"attention": "all", "cursor": token}).status_code
                == 400
            )
            subject_operator = hold.person.subject
            subject_operator.mfa_enabled = True
            subject_operator.save(update_fields=["mfa_enabled"])
            subject_operator.user_permissions.add(
                *Permission.objects.filter(
                    codename__in=[
                        "review_rights_request",
                        "execute_rights_request",
                        "review_purpose_calendar",
                    ]
                )
            )
            subject_client = Client()
            subject_client.force_login(subject_operator)
            subject_session = subject_client.session
            subject_session["mfa_version"] = subject_operator.mfa_version
            subject_session.save()
            hidden = subject_client.get(queue_path, {"attention": "all"})
            assert hidden.status_code == 200 and not hidden.context["restrictions"]
            assert (
                subject_client.post(
                    path, dict(key=uuid4(), version=version, operation="history", reason=reason)
                ).status_code
                == 403
            )
            for execution_row, clone, action_row in clones:
                execution_row.delete()
                clone.delete()
                action_row.delete()
            response = client.get(path)
            assert response.status_code == 200
            assert [item[0] for item in response.context["form"].fields["operation"].choices] == [
                "follow_up",
                "history",
            ]
            assert (
                client.post(
                    path,
                    dict(
                        key=uuid4(),
                        version=version,
                        operation="execute",
                        reason=reason,
                        proposal_id=1,
                    ),
                ).status_code
                == 403
            )
            assert (
                client.post(
                    path,
                    dict(
                        key=event_key,
                        version=version,
                        operation="follow_up",
                        hold_version=hold.version,
                        reason=reason,
                        next_review_on=when.isoformat(),
                    ),
                ).status_code
                == 200
            )
            from apps.safety.models import RightsAction

            event = RightsAction.objects.get(key=event_key)
            assert (
                follow_up(user, case_id, hold_id, event_key, version, hold.version, reason, when).pk
                == event.pk
            )
            hold.refresh_from_db()
            assert hold.active and hold.version == 2
            assert hold.initial_purpose_review_on == initial and hold.purpose_review_on == when
            assert unseal(event.encrypted_reason)["previous_version"] == 1
            assert hold.calendar_events.count() == 1
            assert hold.calendar_events.get().action_id == event.pk
            assert hold.calendar_events.get().expected_version == 1
            from apps.safety.publication_purpose_calendar import history

            gate = Barrier(2)
            expected_version = hold.version

            def competing_follow_up():
                close_old_connections()
                try:
                    with connections["default"].cursor() as cursor:
                        cursor.execute("SELECT pg_backend_pid()")
                        pid = cursor.fetchone()[0]
                    gate.wait(timeout=15)
                    try:
                        follow_up(
                            user,
                            case_id,
                            hold_id,
                            uuid4(),
                            version,
                            expected_version,
                            reason,
                            when + timedelta(days=1),
                        )
                        return pid, "applied"
                    except ValidationError:
                        return pid, "conflict"
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: competing_follow_up(), range(2)))
            assert len({pid for pid, _ in results}) == 2
            assert sorted(outcome for _, outcome in results) == ["applied", "conflict"]
            hold.refresh_from_db()
            assert hold.version == 3 and hold.calendar_events.count() == 2
            for offset in range(2, 52):
                follow_up(
                    user,
                    case_id,
                    hold_id,
                    uuid4(),
                    version,
                    hold.version,
                    reason,
                    when + timedelta(days=offset),
                )
                hold.refresh_from_db()
            assert hold.calendar_events.count() == 52 and hold.version == 53
            assert hold.initial_purpose_review_on == initial and hold.active
            from django.db import transaction

            from apps.safety.erasure_inventory import source_manifest
            from apps.safety.models import RightsRequest

            with transaction.atomic():
                manifest = source_manifest(hold.person, RightsRequest.objects.get(pk=case_id))
            projection = next(
                row
                for row in manifest["entries"]
                if row["model"] == "safety.PublicationCalendarEvent"
            )
            assert projection["count"] == 52
            assert reason not in str(manifest)
            latest_event = hold.calendar_events.select_related("action").latest("pk")
            cipher = latest_event.action.encrypted_reason
            RightsAction.objects.filter(pk=latest_event.action_id).update(
                encrypted_reason="damaged-event-cipher"
            )
            with transaction.atomic():
                changed = source_manifest(hold.person, RightsRequest.objects.get(pk=case_id))
            changed_projection = next(
                row
                for row in changed["entries"]
                if row["model"] == "safety.PublicationCalendarEvent"
            )
            assert changed_projection["state_digest"] != projection["state_digest"]
            assert "damaged-event-cipher" not in str(changed)
            RightsAction.objects.filter(pk=latest_event.action_id).update(encrypted_reason=cipher)
            signature = latest_event.action.payload_digest
            RightsAction.objects.filter(pk=latest_event.action_id).update(payload_digest="0" * 64)
            before_history_actions = RightsAction.objects.count()
            with pytest.raises(ValidationError, match="signature changed"):
                history(user, case_id, hold_id, uuid4(), version, reason)
            assert RightsAction.objects.count() == before_history_actions
            RightsAction.objects.filter(pk=latest_event.action_id).update(payload_digest=signature)
            read_key = uuid4()
            audit, result = history(user, case_id, hold_id, read_key, version, reason)
            assert len(result["rows"]) == 50 and result["next_cursor"]
            _, older = history(
                user, case_id, hold_id, uuid4(), version, reason, before=result["next_cursor"]
            )
            assert len(older["rows"]) == 2 and older["next_cursor"] is None
            assert not {row["id"] for row in result["rows"]} & {row["id"] for row in older["rows"]}
            action_count = RightsAction.objects.count()
            with pytest.raises(ValidationError, match="cursor"):
                history(user, case_id, hold_id, uuid4(), version, reason, before=-1)
            assert RightsAction.objects.count() == action_count
            assert result["rows"][0]["reason"] == reason
            assert history(user, case_id, hold_id, read_key, version, reason)[0].pk == audit.pk
            page = client.post(
                path, dict(key=uuid4(), version=version, operation="history", reason=reason)
            )
            assert page.status_code == 200
            assert len(page.context["history_result"]["rows"]) == 50
            page = client.post(
                path,
                dict(
                    key=uuid4(),
                    version=version,
                    operation="history",
                    reason=reason,
                    history_before=page.context["history_result"]["next_cursor"],
                ),
            )
            assert page.status_code == 200 and len(page.context["history_result"]["rows"]) == 2
            assert reason.encode() not in client.get(path).content
            user.user_permissions.add(release_permission)
            events.append(event)
        return original(user, case_id, hold_id, key, version, reason)

    monkeypatch.setattr(module, "inspect", inspect_after_follow_up)
    run_flow(request, settings, monkeypatch, "restrict", mixed=False)
    assert len(events) == 1
