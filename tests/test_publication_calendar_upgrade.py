"""Recover signed pre-calendar facts on nonempty PostgreSQL data."""

from datetime import timedelta
from io import StringIO
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.models import PrivacyPublicationHold
from apps.safety.publication_calendar_upgrade import restore_calendar
from apps.safety.publication_purpose_calendar import follow_up

pytestmark = pytest.mark.django_db(transaction=True)


def test_restore_missing_dates_events_and_reject_corruption(request, settings, monkeypatch):
    import apps.safety.publication_purpose_release as module

    original = module.inspect
    checked = []

    def recover(user, case_id, hold_id, key, version, reason):
        if not checked:
            checked.append(True)
            hold = PrivacyPublicationHold.objects.get(pk=hold_id)
            initial = hold.initial_purpose_review_on
            assert connection.vendor == "postgresql"

            def upgrade_from(target, expected_version):
                latest = [("safety", "0076_publicationcalendarevent")]
                executor = MigrationExecutor(connection)
                try:
                    executor.migrate([("safety", target)])
                    historical = executor.loader.project_state([("safety", target)]).apps
                    old_hold = historical.get_model("safety", "PrivacyPublicationHold").objects.get(
                        pk=hold_id
                    )
                    assert old_hold.active
                    if expected_version is None:
                        assert not hasattr(old_hold, "purpose_review_on")
                    else:
                        assert old_hold.version == expected_version
                        assert old_hold.initial_purpose_review_on == initial
                        assert old_hold.purpose_review_on == timezone.localdate() + timedelta(
                            days=15
                        )
                        old_action = historical.get_model("safety", "RightsAction")
                        assert (
                            old_action.objects.filter(
                                request_id=case_id, operation="pub_cal_follow"
                            ).count()
                            == 2
                        )
                    assert (
                        "safety_publicationcalendarevent"
                        not in connection.introspection.table_names()
                    )
                finally:
                    MigrationExecutor(connection).migrate(latest)

            upgrade_from("0074_privacyholdreleaseproposal_ground_and_more", None)
            hold.refresh_from_db()
            assert hold.initial_purpose_review_on is None and hold.purpose_review_on is None
            PrivacyPublicationHold.objects.filter(pk=hold_id).update(
                initial_purpose_review_on=None, purpose_review_on=None
            )
            output = StringIO()
            call_command("restore_publication_calendar", hold_id, stdout=output)
            assert '"applied": false' in output.getvalue()
            assert reason not in output.getvalue()
            hold.refresh_from_db()
            assert hold.initial_purpose_review_on is None and hold.purpose_review_on is None
            with pytest.raises(CommandError, match="no changes applied"):
                call_command("restore_publication_calendar", 9223372036854775807)
            assert restore_calendar(hold_id) == {"dates_restored": True, "events_restored": 0}
            assert restore_calendar(hold_id) == {"dates_restored": False, "events_restored": 0}
            user.user_permissions.add(Permission.objects.get(codename="review_purpose_calendar"))
            for index in range(2):
                follow_up(
                    user,
                    case_id,
                    hold_id,
                    uuid4(),
                    version,
                    index + 1,
                    reason,
                    timezone.localdate() + timedelta(days=14 + index),
                )
            hold.refresh_from_db()
            actions = [event.action for event in hold.calendar_events.order_by("pk")]
            timestamps = {action.pk: action.created_at for action in actions}
            upgrade_from("0075_privacypublicationhold_initial_purpose_review_on_and_more", 3)
            assert not hold.calendar_events.exists()
            PrivacyPublicationHold.objects.filter(pk=hold_id).update(
                initial_purpose_review_on=None, purpose_review_on=None
            )
            action = actions[-1]
            saved = action.payload_digest
            action.payload_digest = "0" * 64
            action.save(update_fields=["payload_digest"])
            with pytest.raises(ValidationError):
                restore_calendar(hold_id)
            with pytest.raises(CommandError, match="no changes applied"):
                call_command("restore_publication_calendar", hold_id, apply=True)
            hold.refresh_from_db()
            assert hold.initial_purpose_review_on is None and hold.purpose_review_on is None
            assert not hold.calendar_events.exists()
            action.payload_digest = saved
            action.save(update_fields=["payload_digest"])
            output = StringIO()
            call_command("restore_publication_calendar", hold_id, stdout=output)
            assert '"events_restored": 2' in output.getvalue()
            assert not hold.calendar_events.exists()
            hold.refresh_from_db()
            assert hold.purpose_review_on is None
            output = StringIO()
            call_command("restore_publication_calendar", hold_id, apply=True, stdout=output)
            assert '"applied": true' in output.getvalue()
            assert reason not in output.getvalue()
            assert restore_calendar(hold_id) == {"dates_restored": False, "events_restored": 0}
            hold.refresh_from_db()
            assert hold.active and hold.version == 3
            assert hold.initial_purpose_review_on == initial
            assert hold.purpose_review_on == timezone.localdate() + timedelta(days=15)
            assert {
                event.action_id: event.created_at for event in hold.calendar_events.all()
            } == timestamps
        return original(user, case_id, hold_id, key, version, reason)

    monkeypatch.setattr(module, "inspect", recover)
    run_flow(request, settings, monkeypatch, "restrict", mixed=False)
    assert checked == [True]
