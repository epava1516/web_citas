"""Fresh commercial ordering over an already authoritative publication population."""

import hashlib
from datetime import UTC

from django.db.models import (
    BinaryField,
    Case,
    CharField,
    F,
    Func,
    IntegerField,
    JSONField,
    OuterRef,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat
from django.utils import timezone

from .promotion_exposure import enabled, live_entitlements


def _sql_order_population(query, listing_field, *, text_search=False, now=None):
    """Annotate only ranking values; membership remains publication_state's authority.

    The caller holds its publication snapshot through count, selection and native
    page guard. No limits are applied to rights or candidates before ordering.
    PostgreSQL's built-in sha256(bytea) matches the reference's byte digest.
    """
    if not enabled():
        return query.annotate(_promotion_priority=Value(2, output_field=IntegerField()))
    now = now or timezone.now()
    rights = live_entitlements(now).filter(order__listing_id=OuterRef(listing_field))
    priority = rights.filter(order__kind__in=["premium", "top"]).annotate(
        _priority=Case(When(order__kind="premium", then=Value(0)), default=Value(1)),
    ).order_by("_priority", "pk").values("_priority")[:1]
    query = query.annotate(
        _promotion_priority=Coalesce(Subquery(priority, output_field=IntegerField()), Value(2)),
    )
    digest = Func(
        Cast(Concat(Value(now.astimezone(UTC).date().isoformat() + ":"),
                    Cast(F(listing_field), CharField())), BinaryField()),
        function="sha256", output_field=BinaryField(),
    )
    query = query.annotate(
        _promotion_rotation=Case(
            When(_promotion_priority__lt=2, then=digest),
            default=Value(b"", output_field=BinaryField()), output_field=BinaryField(),
        ),
        _promotion_tie=Case(
            When(_promotion_priority__lt=2, then=Cast(F(listing_field), CharField())),
            default=Value(""), output_field=CharField(),
        ),
    )
    ordering = ["_promotion_priority", "_promotion_rotation", "_promotion_tie"]
    if not text_search:
        bumped = rights.filter(
            order__kind="autobump", last_bumped_at__isnull=False,
        ).order_by("-last_bumped_at").values("last_bumped_at")[:1]
        query = query.annotate(_promotion_bumped_at=Subquery(bumped))
        ordering.append(F("_promotion_bumped_at").desc(nulls_last=True))
    return query.order_by(*ordering, *query.query.order_by)


def _snapshot_order_population(query, listing_field, *, text_search=False, now=None):
    """Transient rank values from the caller's own repeatable-read snapshot only.

    Read narrow compatible rights once; publication membership stays in SQL.
    No arbitrary candidate limit and no authorization/ordering result survives
    the request. Equal bump timestamps retain the original organic ordering.
    """
    now = now or timezone.now()
    rights = live_entitlements(now).filter(
        order__listing_id__in=query.order_by().values(listing_field),
    ).values_list("order__listing_id", "order__kind", "last_bumped_at")
    promotions, bumps = {}, {}
    priorities = {"premium": 0, "top": 1}
    for pk, kind, bumped_at in rights.iterator(chunk_size=500):
        if kind in priorities:
            if pk not in promotions or priorities[kind] < priorities[promotions[pk]]:
                promotions[pk] = kind
        elif kind == "autobump" and bumped_at and not text_search:
            bumps[pk] = max(bumps.get(pk, bumped_at), bumped_at)
    day = now.astimezone(UTC).date().isoformat()
    sponsored = sorted(promotions, key=lambda pk: (
        priorities[promotions[pk]], hashlib.sha256((day + ":" + str(pk)).encode()).digest(), str(pk),
    ))
    positions = {str(pk): index for index, pk in enumerate(sponsored)}
    premium_count = sum(kind == "premium" for kind in promotions.values())
    stamps = sorted({stamp.timestamp() for pk, stamp in bumps.items() if pk not in promotions}, reverse=True)
    bump_positions = {stamp: len(sponsored) + index for index, stamp in enumerate(stamps)}
    for pk, stamp in bumps.items():
        if pk not in promotions:
            positions[str(pk)] = bump_positions[stamp.timestamp()]
    if not positions:
        return query.annotate(_promotion_priority=Value(2, output_field=IntegerField()))
    position = Coalesce(Cast(Func(
        Value(positions, output_field=JSONField()), Cast(F(listing_field), CharField()),
        function="jsonb_extract_path_text", output_field=CharField(),
    ), IntegerField()), Value(len(sponsored) + len(stamps)))
    query = query.annotate(_promotion_position=position).annotate(
        _promotion_priority=Case(
            When(_promotion_position__lt=premium_count, then=Value(0)),
            When(_promotion_position__lt=len(sponsored), then=Value(1)), default=Value(2),
        ),
    )
    return query.order_by("_promotion_position", *query.query.order_by)


def order_population(query, listing_field, *, text_search=False, now=None, trusted_snapshot=False):
    if not enabled():
        return query.annotate(_promotion_priority=Value(2, output_field=IntegerField()))
    if trusted_snapshot:
        return _snapshot_order_population(query, listing_field, text_search=text_search, now=now)
    # An inherited transaction may be READ COMMITTED. Never reuse a previously
    # read authority map across its statements; retain statement-local SQL there.
    return _sql_order_population(query, listing_field, text_search=text_search, now=now)
