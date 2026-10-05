"""Audited projection of independently approved selectors; no export or case closure."""

from .rights_portability_selection_store import inspect_selection


def consume_selected(user, case_id, version, selection_id, review_id, key, reason):
    return inspect_selection(
        user, case_id, version, selection_id, key, reason, approved_review_id=review_id
    )
