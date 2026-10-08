"""Stored publication eligibility with trigger-maintained invalidation.

Exactness never depends on the refresher. A stored result is trusted only when the
listing is not dirty, the state was computed under the current rules version and for
the current approved revision. Every other candidate is evaluated with the native rule
inside the request. Database triggers on every table read by the native rule mark the
affected listings dirty in the same transaction as the change (migration 0015).
Expiry is time dependent and always evaluated in SQL by the caller's candidates().
"""

import hashlib
import os
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, connection, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.core.models import VerificationCheck
from apps.core.verification_services import real_checks

from .models import Listing, PublicationDirty, PublicationState
from .moderation import publicly_visible
from .public_validation import PublicationContext
from .submissions import validate_submission

NATIVE_UNKNOWN_LIMIT = 48
GUARD = os.environ.get("PUBLICATION_STATE_GUARD", "1") == "1"
CHECKS = ("age", "contact", "agency")


@lru_cache(maxsize=1)
def rules_version():
    """Code and configuration the stored result depends on; computed once per process."""
    from .projected_publication import definitions_digest

    material = "|".join(
        [definitions_digest(), str(settings.PRODUCTION), settings.VERIFICATION_PROVIDER]
    )
    return hashlib.sha256(material.encode()).hexdigest()


def eligible_ignoring_expiry(listing, context):
    """moderation.publicly_visible without its expiry comparison."""
    revision = listing.approved_revision
    if (
        listing.status != "published"
        or not revision
        or revision.listing_id != listing.pk
        or revision.status != "approved"
        or not listing.expires_at
    ):
        return False
    try:
        validate_submission(revision, listing.person, context=context)
    except ValidationError:
        return False
    return not context.row(revision)._pv_conflict


def refresh(limit=100):
    """Recompute a bounded batch of dirty listings; returns how many were processed."""
    version = rules_version()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT listing_id, generation FROM listings_publicationdirty "
                "ORDER BY generation LIMIT %s FOR UPDATE SKIP LOCKED",
                [limit],
            )
            claimed = cursor.fetchall()
        if not claimed:
            return 0
        ids = [row[0] for row in claimed]
        listings = Listing.objects.filter(pk__in=ids, approved_revision__isnull=False)
        context = PublicationContext(listings, page_read=True)
        # Same latest-check selection real_checks performs, batched for the claimed people.
        latest = {
            check.person_id: check
            for check in VerificationCheck.objects.filter(
                person_id__in=[row.person_id for row in context.rows]
            ).order_by("person_id", "-created_at").distinct("person_id")
        }
        now = timezone.now()
        states = {}
        for listing in context.rows:
            eligible = eligible_ignoring_expiry(listing, context)
            checks = (
                real_checks(listing.person, age=latest.get(listing.person_id)) if eligible else {}
            )
            states[listing.pk] = PublicationState(
                listing_id=listing.pk,
                eligible=eligible,
                revision_id=listing.approved_revision_id,
                rules_version=version,
                computed_at=now,
                **{"check_" + name: bool(checks.get(name)) for name in CHECKS},
            )
        existing = set(Listing.objects.filter(pk__in=ids).values_list("pk", flat=True))
        for listing_id in existing - set(states):
            states[listing_id] = PublicationState(
                listing_id=listing_id, eligible=False, revision_id=None,
                rules_version=version, computed_at=now,
            )
        PublicationState.objects.bulk_create(
            states.values(),
            update_conflicts=True,
            unique_fields=["listing"],
            update_fields=["eligible", "revision", "rules_version", "computed_at",
                           *("check_" + name for name in CHECKS)],
        )
        with connection.cursor() as cursor:
            # Only rows not re-marked since they were claimed; a concurrent change keeps it dirty.
            cursor.execute(
                "DELETE FROM listings_publicationdirty d USING unnest(%s::uuid[], %s::bigint[]) "
                "AS c(listing_id, generation) WHERE d.listing_id = c.listing_id "
                "AND d.generation = c.generation",
                [ids, [row[1] for row in claimed]],
            )
        return len(claimed)


def mark(listing_ids):
    with connection.cursor() as cursor:
        cursor.execute("SELECT listings_publication_mark(%s::uuid[])", [list(listing_ids)])


def trusted_state(**extra):
    return PublicationState.objects.filter(
        listing_id=OuterRef("pk"),
        rules_version=rules_version(),
        # The approved revision is not compared here: changing it writes listings_listing,
        # whose trigger marks the listing dirty until the state is recomputed.
        **extra,
    )


DIRTY_LIMIT = 1000
READ_REPAIR = os.environ.get("PUBLICATION_STATE_READ_REPAIR", "1") == "1"
READ_REPAIR_LIMIT = 24


def repair():
    """Recompute a few pending listings before reading, so one request pays per change.

    Exactness does not depend on it: anything still dirty is evaluated natively below.
    Concurrent readers skip rows another reader is already recomputing.
    """
    if not PublicationDirty.objects.exists():
        return
    try:
        refresh(READ_REPAIR_LIMIT)
    except DatabaseError:
        pass


def state_page(query, number, *, checked=(), observation=None, guard=GUARD):
    """Exact page of the native population; None asks the caller for the native path.

    All reads share one REPEATABLE READ snapshot, so the dirty set, the stored state,
    the native evaluation of unknown rows, the count and the page are mutually consistent.
    """
    stale = []
    outermost = not connection.in_atomic_block
    if outermost and READ_REPAIR:
        repair()
    with transaction.atomic():
        if outermost:  # Only the first statement of a new transaction may set its isolation.
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        page = _state_page(query, number, checked, observation, guard, stale)
    if stale:
        mark(stale)
    return page


def _state_page(query, number, checked, observation, guard, stale):
    # The dirty set is small; read it once instead of a correlated anti-join per candidate,
    # whose plan degrades with the dead tuples a high-churn table accumulates.
    dirty = list(PublicationDirty.objects.values_list("listing_id", flat=True)[: DIRTY_LIMIT + 1])
    if len(dirty) > DIRTY_LIMIT:
        if observation is not None:
            observation.update(route="fallback", reason="state_dirty_over_limit")
        return None
    unknown = list(
        query.filter(~Exists(trusted_state()) | Q(pk__in=dirty)).values_list("pk", flat=True)[
            : NATIVE_UNKNOWN_LIMIT + 1
        ]
    )
    if len(unknown) > NATIVE_UNKNOWN_LIMIT:
        if observation is not None:
            observation.update(route="fallback", reason="state_unknown_over_limit")
        return None
    native = []
    if unknown:
        context = PublicationContext(query.filter(pk__in=unknown), page_read=True)
        native = [
            row.pk
            for row in context.rows
            if publicly_visible(row, context=context) and matches(row.person, checked)
        ]
    check_filter = Q()
    for name in checked:
        check_filter |= Q(**{"check_" + name: True})
    trusted_visible = Exists(trusted_state(eligible=True).filter(check_filter)) & ~Q(pk__in=dirty)
    # Narrow rows: identifiers plus the ordering columns the DISTINCT requires; the page
    # rows are hydrated afterwards through the native context of these 24 listings only.
    population = query.select_related(None).filter(trusted_visible | Q(pk__in=native))
    if not multiplies_rows(population):
        # DISTINCT only removes duplicates created by many-valued joins; none are present.
        population.query.distinct = False
    page = Paginator(population.values_list("pk", flat=True), 24).page(number)
    selected = list(page.object_list)
    if guard:
        context = PublicationContext(query.filter(pk__in=selected), page_read=True)
        rows = {row.pk: row for row in context.rows}
    else:
        rows = {row.pk: row for row in query.filter(pk__in=selected).order_by()}
    stale.extend(
        pk
        for pk in selected
        if pk not in rows or (guard and not publicly_visible(rows[pk], context=context))
    )
    if stale:
        if observation is not None:
            observation.update(route="fallback", reason="state_page_guard_changed")
        return None
    page.object_list = [rows[pk] for pk in selected]
    if observation is not None:
        observation.update(route="state", reason="trusted_state", native_unknown=len(unknown))
    return page


def multiplies_rows(queryset):
    queryset.query.get_compiler(using=queryset.db).setup_query()
    tables = {alias.table_name for alias in queryset.query.alias_map.values()}
    single = {"listings_listing", "listings_revision", "core_person", "core_agency",
              "core_phoneclaim", "catalog_municipality", "catalog_province", "catalog_region"}
    return not tables <= single


def matches(person, selected):
    if not selected:
        return True
    checks = real_checks(person)
    return any(checks[name] for name in selected)
