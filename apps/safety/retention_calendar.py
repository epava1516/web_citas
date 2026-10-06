"""Bounded batches with fresh per-row authorization; cursors contain metadata only."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.core import signing
from django.db.models import Q

from .erasure_plans import LABELS
from .rights_scope import permitted

SALT = "safety.retention-calendar.v1"


@dataclass
class CalendarPage:
    object_list: list
    previous_cursor: str = ""
    next_cursor: str = ""

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self):
        return len(self.object_list)

    def has_previous(self):
        return bool(self.previous_cursor)

    def has_next(self):
        return bool(self.next_cursor)


def calendar_page(request, rows, attention):
    if request.GET.get("page", "1") != "1":
        raise ValueError("Numeric pagination no longer supported")
    token = request.GET.get("cursor", "")
    direction = "next"
    boundary = None
    if token:
        if len(token) > 1024:
            raise ValueError("Oversized cursor")
        try:
            payload = signing.loads(token, salt=SALT, max_age=1800)
            if (
                not isinstance(payload, list)
                or len(payload) != 6
                or payload[:3] != [1, str(request.user.pk), attention]
                or payload[3] not in {"next", "previous"}
            ):
                raise ValueError("Cursor scope mismatch")
            direction = payload[3]
            boundary = (date.fromisoformat(payload[4]), UUID(payload[5]))
        except (signing.BadSignature, TypeError, AttributeError, ValueError) as error:
            raise ValueError("Invalid cursor") from error
    reverse = direction == "previous"
    visible = []
    while len(visible) < 51:
        batch_query = rows
        if boundary:
            day, pk = boundary
            if reverse:
                batch_query = batch_query.filter(
                    Q(next_review_on__lt=day) | Q(next_review_on=day, pk__lt=pk)
                )
            else:
                batch_query = batch_query.filter(
                    Q(next_review_on__gt=day) | Q(next_review_on=day, pk__gt=pk)
                )
        order = ("-next_review_on", "-pk") if reverse else ("next_review_on", "pk")
        batch = list(batch_query.order_by(*order)[:100])
        if not batch:
            break
        for row in batch:
            boundary = (row.next_review_on, row.pk)
            if permitted(request.user, row.plan.action.request):
                row.purpose_label = LABELS.get(row.purpose, row.purpose)
                visible.append(row)
                if len(visible) == 51:
                    break
        if len(batch) < 100:
            break
    more = len(visible) > 50
    displayed = visible[:50]
    if reverse:
        displayed.reverse()
    page = CalendarPage(displayed)

    def cursor(row, move):
        return signing.dumps(
            [1, str(request.user.pk), attention, move, row.next_review_on.isoformat(), str(row.pk)],
            salt=SALT,
        )

    if displayed:
        if (reverse and more) or (not reverse and token):
            page.previous_cursor = cursor(displayed[0], "previous")
        if (not reverse and more) or (reverse and token):
            page.next_cursor = cursor(displayed[-1], "next")
    return page
