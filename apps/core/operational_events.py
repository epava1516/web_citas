"""Fixed-vocabulary operational events. Never pass request/task payloads to logging."""
import json
import logging
import time

logger = logging.getLogger("operational.events")
TASK_NAMES = frozenset(
(
    "apps.catalog.tasks.bump_promotions",
    "apps.listings.tasks.expire_listings",
    "apps.listings.tasks.refresh_publication_state",
    "apps.listings.tasks.sweep_publication_state",
    "apps.mediafiles.tasks.process_blob",
    "apps.mediafiles.tasks.recover_media_jobs",
    "apps.mediafiles.tasks.erase_media_files",
    "apps.mediafiles.tasks.cleanup_prepared_media",
    "apps.safety.rights_object_content.purge_orphan_export_objects",
    "apps.safety.rights_object_delivery.purge_object_deliveries",
    "apps.safety.tasks.deliver_safety_notices",
    "apps.safety.tasks.reconcile_urgent_report_alerts",
    "apps.safety.tasks.purge_expired_exports",
    "apps.safety.tasks.purge_expired_account_confirmation_delivery",
    "apps.safety.tasks.reconcile_retention_reviews",
    "apps.safety.tasks.purge_expired_copy_page_reviews",
    "apps.safety.tasks.purge_expired_copy_information",
    "apps.safety.tasks.purge_expired_portability_assessments",
    "apps.safety.tasks.purge_expired_portability_selections",
    "apps.safety.tasks.purge_expired_portability_coverage",
    "apps.safety.tasks.purge_expired_portability_response_drafts",
    "apps.safety.tasks.purge_expired_access_response_drafts",
    "apps.safety.tasks.purge_expired_access_coverage",
    "apps.safety.tasks.purge_expired_access_scope_inventory",
    "apps.safety.tasks.purge_expired_access_field_decision",
    "apps.safety.tasks.generate_portability_export",
    "apps.safety.tasks.reconcile_portability_export_jobs",
)
)
ROUTES = frozenset(("state", "fallback"))
REASONS = frozenset((
    "invalid_search", "state_dirty_over_limit", "state_unknown_over_limit",
    "state_page_guard_changed", "trusted_state", "trusted_state_extended_unknown",
))
OUTCOMES = frozenset(("succeeded", "failed", "retry", "ignored"))


def _allowed(value, choices):
    return value if type(value) is str and value in choices else "other"


def _emit(event, **values):
    # Delivery failure cannot change publication or task authority/results.
    # These are best-effort local log events, not a durable audit ledger.
    try:
        logger.info(json.dumps({"schema_version": 1, "event": event,
                               "timestamp_seconds": int(time.time()), **values},
                              sort_keys=True, separators=(",", ":"), allow_nan=False))
    except Exception:
        pass


def publication_read(observation, status):
    observation = observation if type(observation) is dict else {}
    status_class = f"{status // 100}xx" if type(status) is int and 100 <= status <= 599 else "other"
    _emit("publication_read", route=_allowed(observation.get("route"), ROUTES),
          reason=_allowed(observation.get("reason"), REASONS), status_class=status_class)


def task_result(name, outcome, result=None):
    values = {"task": _allowed(name, TASK_NAMES), "outcome": _allowed(outcome, OUTCOMES)}
    if name == "apps.safety.tasks.deliver_safety_notices" and type(result) is dict:
        values["delivery_counts"] = {
            key: result[key] if type(result.get(key)) is int and 0 <= result[key] <= 100 else None
            for key in ("processed", "simulated", "retry", "failed")
        }
        values["processor_disabled"] = result.get("disabled") if type(result.get("disabled")) is bool else None
    _emit("task_result", **values)


class PublicationEventsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        observation = getattr(request, "_publication_route", None)
        if observation is not None:
            publication_read(observation, response.status_code)
        return response
