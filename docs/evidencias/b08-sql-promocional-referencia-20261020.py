"""Fresh commercial ordering over an already authoritative publication population."""

from datetime import UTC

from django.db.models import (
    BinaryField,
    Case,
    CharField,
    F,
    Func,
    IntegerField,
    OuterRef,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat
from django.utils import timezone

from .promotion_exposure import enabled, live_entitlements


def order_population(query, listing_field, *, text_search=False, now=None):
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
