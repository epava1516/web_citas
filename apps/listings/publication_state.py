"""Stored publication eligibility with trigger-maintained invalidation.

Exactness never depends on the refresher. A stored result is trusted only when the
listing is not dirty and the state was computed under the current rules version. Every
other candidate is evaluated with the native rule inside the request. Database triggers on every table read by the native rule mark the
affected listings dirty in the same transaction as the change (migration 0015).
Expiry is time dependent and always evaluated in SQL by the caller's candidates().
"""

import hashlib
import logging
import os
from datetime import timedelta
from functools import lru_cache

import django
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, connection, transaction
from django.db.models import Exists, F, OuterRef, Q
from django.utils import timezone

from apps.core.domain_signing import domain_signing_key
from apps.core.models import VerificationCheck
from apps.core.verification_services import real_checks

from .models import Listing, PublicationDirty, PublicationState
from .moderation import publicly_visible
from .public_validation import PublicationContext
from .submissions import validate_submission

logger = logging.getLogger(__name__)
NATIVE_UNKNOWN_LIMIT = 48
# Tables read by the native rule. Migration 0015 installs their invalidation triggers;
# tests compare this set with the installed triggers and with the tables actually read.
DEPENDENCY_TABLES = frozenset({
    "listings_listing", "listings_revision", "listings_revision_categories",
    "listings_revision_services", "listings_revision_travel_areas", "listings_rate",
    "mediafiles_photo", "mediafiles_blob", "mediafiles_match", "core_person", "core_phoneclaim",
    "core_agency", "core_legalacceptance", "core_legaldocument", "core_representationaction",
    "core_verificationcheck", "safety_privacypublicationhold", "safety_restriction",
    "safety_rightsphotoreintroduction", "safety_rightsphotoreintroductiondecision",
    "safety_rightsproof", "safety_rightsrectificationproposal",
    "safety_rightsrectificationreview", "safety_rightsrectificationnotification",
    "safety_rightsrectificationexecution", "safety_rightsrectificationphotoupload",
    "safety_rightsrectificationphotodisposition", "catalog_category", "catalog_service",
    "catalog_region", "catalog_province", "catalog_municipality", "catalog_postalcode",
    "catalog_postalcode_municipalities", "catalog_zone",
})
CHECKS = ("age", "contact", "agency")


# Source files that define the native rule (and the model/form metadata it validates).
# Any edit changes the version, so every stored result is recomputed with the new code.
RULE_SOURCES = (
    "apps/listings/moderation.py",
    "apps/listings/submissions.py",
    "apps/listings/profile_contract.py",
    "apps/listings/forms.py",
    "apps/listings/public_validation.py",
    "apps/listings/history.py",
    "apps/listings/models.py",
    "apps/listings/publication_state.py",
    "apps/catalog/models.py",
    "apps/core/models.py",
    "apps/core/verification_services.py",
    "apps/safety/photo_dispositions.py",
    "apps/safety/photo_reintroduction_review.py",
    "apps/core/domain_signing.py",
    "apps/safety/rights.py",
    "apps/safety/rights_operation_fingerprints.py",
    "apps/safety/rights_validation_seal.py",
)


def rules_version():
    """Fingerprint the current rule configuration, reusing unchanged source hashes."""
    return _rules_version(settings.PRODUCTION, settings.VERIFICATION_PROVIDER, settings.SECRET_KEY,
                          domain_signing_key())


@lru_cache(maxsize=1)
def _rules_version(production, provider, secret_key, domain_key):
    """Source text, Django version and configuration; cached per configuration.

    Hashing source rather than bytecode keeps the version stable across Python builds.
    """
    digest = hashlib.sha256()
    for name in RULE_SOURCES:
        digest.update(name.encode() + b"\0" + (settings.BASE_DIR / name).read_bytes() + b"\0")
    material = [django.get_version(), str(production), provider]
    digest.update("|".join(material).encode())
    # Conditional photo authority depends on the effective domain HMAC key.
    # A key rotation invalidates those decisions; never trust the previous result.
    digest.update(b"\0rights-fingerprint-key\0" + secret_key.encode())
    digest.update(b"\0domain-hmac-key\0" + domain_key.encode())
    return digest.hexdigest()


# Source edits still require explicit invalidation; configuration changes form
# part of the cache key automatically, including test override restoration.
rules_version.cache_clear = _rules_version.cache_clear


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


def expected_states(ids, version):
    """Native results for the given listings (existing ones only), as unsaved states."""
    listings = Listing.objects.filter(pk__in=ids, approved_revision__isnull=False)
    context = PublicationContext(listings, page_read=True)
    # Same latest-check selection real_checks performs, batched for these people.
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
        checks = real_checks(listing.person, age=latest.get(listing.person_id)) if eligible else {}
        states[listing.pk] = PublicationState(
            listing_id=listing.pk,
            eligible=eligible,
            revision_id=listing.approved_revision_id,
            rules_version=version,
            computed_at=now,
            expires_at=listing.expires_at,
            published_at=listing.published_at,
            search_document=listing.approved_revision.search_document,
            **{"check_" + name: bool(checks.get(name)) for name in CHECKS},
        )
    for row in Listing.objects.filter(pk__in=ids).values(
        "pk", "expires_at", "published_at",
    ):
        if row["pk"] in states:
            continue
        states[row["pk"]] = PublicationState(
            listing_id=row["pk"], eligible=False, revision_id=None,
            rules_version=version, computed_at=now,
            expires_at=row["expires_at"], published_at=row["published_at"], search_document=None,
        )
    return states


STATE_COLUMNS = ("eligible", "revision_id", "rules_version", "check_age", "check_contact",
                 "check_agency", "expires_at", "published_at", "search_document")


def store(states):
    """Upsert, rewriting only rows whose values changed (fewer dead tuples to vacuum)."""
    states = list(states)
    if not states:
        return
    columns = ("listing_id", *STATE_COLUMNS, "computed_at")
    rows = ", ".join(["(" + ", ".join(["%s"] * len(columns)) + ")"] * len(states))
    params = [getattr(state, column) for state in states for column in columns]
    assignments = ", ".join(f"{column} = EXCLUDED.{column}" for column in (*STATE_COLUMNS, "computed_at"))
    current = ", ".join(f"s.{column}" for column in STATE_COLUMNS)
    incoming = ", ".join(f"EXCLUDED.{column}" for column in STATE_COLUMNS)
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO listings_publicationstate AS s ({', '.join(columns)}) VALUES {rows} "
            f"ON CONFLICT (listing_id) DO UPDATE SET {assignments} "
            f"WHERE ({current}) IS DISTINCT FROM ({incoming})",
            params,
        )


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
        # State INSERTs check their foreign keys at commit. Never wait for those
        # references while holding dirty rows: a domain writer may hold Listing
        # and be waiting for its dirty marker. Keep the batch dirty for Beat.
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM listings_listing WHERE id=ANY(%s::uuid[]) "
                    "ORDER BY id FOR KEY SHARE NOWAIT", [ids],
                )
                cursor.execute(
                    "SELECT v.id FROM listings_revision v WHERE v.id IN "
                    "(SELECT approved_revision_id FROM listings_listing "
                    "WHERE id=ANY(%s::uuid[])) ORDER BY v.id FOR KEY SHARE NOWAIT",
                    [ids],
                )
        except DatabaseError as error:
            if getattr(error.__cause__, "sqlstate", None) != "55P03":
                raise
            return 0
        store(expected_states(ids, version).values())
        with connection.cursor() as cursor:
            # Only rows not re-marked since they were claimed; a concurrent change keeps it dirty.
            cursor.execute(
                "DELETE FROM listings_publicationdirty d USING unnest(%s::uuid[], %s::bigint[]) "
                "AS c(listing_id, generation) WHERE d.listing_id = c.listing_id "
                "AND d.generation = c.generation",
                [ids, [row[1] for row in claimed]],
            )
        return len(claimed)


def sweep(batch=500):
    """Re-verify every trusted state against the native rule; mark any divergence.

    Bounds a rule-behaviour change that no versioned source, setting or data write
    captured (MOD-05 invariant). It never writes state itself: a marked listing goes
    through the normal refresh, so a concurrent change cannot be overwritten.
    """
    version = rules_version()
    fields = STATE_COLUMNS
    divergent, last = [], None
    while True:
        page = Listing.objects.order_by("pk")
        if last is not None:
            page = page.filter(pk__gt=last)
        ids = list(page.values_list("pk", flat=True)[:batch])
        if not ids:
            break
        last = ids[-1]
        dirty = set(PublicationDirty.objects.filter(listing_id__in=ids).values_list(
            "listing_id", flat=True))
        stored = {state.listing_id: state for state in PublicationState.objects.filter(
            listing_id__in=ids, rules_version=version)}
        with transaction.atomic():
            expected = expected_states(ids, version)
        for listing_id, state in stored.items():
            if listing_id in dirty:
                continue
            fresh = expected.get(listing_id)
            if fresh is None or any(getattr(fresh, f) != getattr(state, f) for f in fields):
                divergent.append(listing_id)
    if divergent:
        mark(divergent)
        logger.warning("publication_state_divergence", extra={"listings": len(divergent)})
    return len(divergent)


def refresh_all(batch=500):
    """Recompute every pending listing; inside a caller's transaction it commits atomically."""
    total = 0
    while processed := refresh(batch):
        total += processed
    return total


def mark_stale():
    """Mark listings without state or computed under another rules version (deploys)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT listings_publication_mark(ARRAY(SELECT l.id FROM listings_listing l "
            "LEFT JOIN listings_publicationstate s ON s.listing_id = l.id "
            "WHERE s.listing_id IS NULL OR s.rules_version <> %s))",
            [rules_version()],
        )


def mark_all():
    with connection.cursor() as cursor:
        cursor.execute("SELECT listings_publication_mark(ARRAY(SELECT id FROM listings_listing))")


def mark(listing_ids):
    with connection.cursor() as cursor:
        cursor.execute("SELECT listings_publication_mark(%s::uuid[])", [list(listing_ids)])


def all_state_current(*, trusted_snapshot=False):
    """Every listing has a state computed under the current rules version.

    Only our new READ ONLY snapshot contains committed FK-consistent rows with
    no caller writes. There, non-null unique state.listing_id and its FK imply
    that equal cardinalities mean complete coverage. Other callers retain the
    join: deferred FK violations in inherited write transactions can otherwise
    let an orphan cancel a missing state in the counts.
    """
    with connection.cursor() as cursor:
        if trusted_snapshot:
            cursor.execute(
                "SELECT NOT EXISTS (SELECT 1 FROM listings_publicationstate "
                "WHERE rules_version <> %s) AND "
                "(SELECT COUNT(*) FROM listings_publicationstate) = "
                "(SELECT COUNT(*) FROM listings_listing)",
                [rules_version()],
            )
        else:
            cursor.execute(
                "SELECT NOT EXISTS (SELECT 1 FROM listings_listing l LEFT JOIN "
                "listings_publicationstate s ON s.listing_id = l.id "
                "WHERE s.listing_id IS NULL OR s.rules_version <> %s)",
                [rules_version()],
            )
        return cursor.fetchone()[0]


def trusted_state(**extra):
    return PublicationState.objects.filter(
        listing_id=OuterRef("pk"),
        rules_version=rules_version(),
        # The approved revision is not compared here: changing it writes listings_listing,
        # whose trigger marks the listing dirty until the state is recomputed.
        **extra,
    )


DIRTY_LIMIT = 1000
# Off by default (user decision): the refresh worker keeps marks clear. Opt in with
# PUBLICATION_STATE_READ_REPAIR=1 as resilience if the worker may be unavailable.
READ_REPAIR = os.environ.get("PUBLICATION_STATE_READ_REPAIR", "0") == "1"
READ_REPAIR_LIMIT = 24
READ_REPAIR_AFTER_SECONDS = 2


def repair():
    """Resilience when the refresh worker lags: recompute a few old marks before reading.

    With the worker keeping up (measured), marks clear within milliseconds and reads never
    write. If marks age (worker down or backlogged), one request pays per change instead
    of every request evaluating it natively. Exactness does not depend on it.
    """
    lagging = timezone.now() - timedelta(seconds=READ_REPAIR_AFTER_SECONDS)
    if not PublicationDirty.objects.filter(marked_at__lte=lagging).exists():
        return  # Nothing pending, or the worker is keeping up: no writes in GET requests.
    try:
        refresh(READ_REPAIR_LIMIT)
    except DatabaseError:
        pass


def state_page(query, number, *, checked=(), observation=None, promotion_order=None):
    """Exact page of the native population; None asks the caller for the native path.

    When opening the transaction, all reads share one REPEATABLE READ snapshot.
    Inside an existing transaction we retain the original candidate predicates;
    its caller controls isolation, so the sibling population shortcut is disabled.
    """
    stale = []
    outermost = not connection.in_atomic_block
    if outermost and READ_REPAIR:
        repair()
    with transaction.atomic():
        if outermost:  # Only the first statement of a new transaction may set its isolation.
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        options = {"trusted_snapshot": outermost}
        if promotion_order is not None:
            options["promotion_order"] = promotion_order
        page = _state_page(query, number, checked, observation, stale, **options)
    if stale:
        mark(stale)
    return page


def _first_page_clean_preview(query, dirty):
    """Bounded ID preview in the caller's own trusted snapshot, never a population."""
    expires_after, text = query._publication_projection
    clean = PublicationState.objects.filter(
        eligible=True, rules_version=rules_version(), expires_at__gt=expires_after,
    ).exclude(listing_id__in=dirty)
    if text:
        search = SearchQuery(text, config="spanish", search_type="websearch") | SearchQuery(
            text, config="english", search_type="websearch",
        )
        clean = clean.filter(search_document=search).annotate(
            relevance=SearchRank(F("search_document"), search),
        ).order_by("-relevance", "-published_at", "listing_id")
    else:
        clean = clean.order_by("-published_at", "listing_id")
    return list(clean.values_list("listing_id", flat=True)[:24])


def _state_page(query, number, checked, observation, stale, *, trusted_snapshot=False,
                promotion_order=None):
    # The dirty set is small; read it once instead of a correlated anti-join per candidate,
    # whose plan degrades with the dead tuples a high-churn table accumulates.
    dirty = list(PublicationDirty.objects.values_list("listing_id", flat=True)[: DIRTY_LIMIT + 1])
    if len(dirty) > DIRTY_LIMIT:
        if observation is not None:
            observation.update(route="fallback", reason="state_dirty_over_limit")
        return None
    unknown = []
    # Only our own repeatable-read snapshot can reuse a complete census for
    # the next statement. In inherited READ COMMITTED, rows may change between
    # statements: retain the original global unknown query and its cost there.
    coverage_current = (
        all_state_current(trusted_snapshot=trusted_snapshot)
        if trusted_snapshot or not dirty else False
    )
    complete = not dirty and coverage_current
    if not complete:
        unknown_query = (
            query.filter(pk__in=dirty)
            if trusted_snapshot and coverage_current
            else query.filter(~Exists(trusted_state()) | Q(pk__in=dirty))
        )
        unknown = list(unknown_query.values_list("pk", flat=True)[: NATIVE_UNKNOWN_LIMIT + 1])
    extended_unknown = False
    if len(unknown) > NATIVE_UNKNOWN_LIMIT:
        if (trusted_snapshot and coverage_current
                and getattr(query, "_publication_state_population", None) is not None):
            unknown = list(unknown_query.values_list("pk", flat=True)[: DIRTY_LIMIT + 1])
            extended_unknown = len(unknown) <= DIRTY_LIMIT
        if not extended_unknown:
            if observation is not None:
                observation.update(route="fallback", reason="state_unknown_over_limit")
            return None
    batch_context = None
    if (unknown and trusted_snapshot and coverage_current and number == 1 and not checked
            and getattr(query, "_publication_projection", None) is not None):
        from .public_validation import _prepared_page_binding

        # Every selected clean row lies in the clean prefix24; every selected
        # unknown is already in unknown. Selection/count remain native below.
        # This may hydrate off-page clean relations; it never caches across requests.
        preview = _first_page_clean_preview(query, dirty)
        batch_ids = set(unknown) | set(preview)
        with _prepared_page_binding(enabled=True):
            batch_context = PublicationContext(
                Listing.objects.filter(pk__in=batch_ids), page_read=True, prepared_page=True,
            )
    native = []
    if unknown:
        context = batch_context or PublicationContext(query.filter(pk__in=unknown), page_read=True)
        native = [
            row.pk
            for row in context.rows
            if row.pk in unknown and publicly_visible(row, context=context) and matches(row.person, checked)
        ]
    check_filter = Q()
    for name in checked:
        check_filter |= Q(**{"check_" + name: True})
    # Independent membership lets PostgreSQL read the eligible state set once even
    # when the native-ID OR prevents pulling a correlated EXISTS into a semi-join.
    # listing_id is a non-null unique key; version/checks/dirty remain exact in the
    # same snapshot. This changes neither the native set nor the final ordering.
    eligible_ids = PublicationState.objects.filter(
        eligible=True, rules_version=rules_version()
    ).filter(check_filter).values_list("listing_id", flat=True)
    trusted_visible = Q(pk__in=eligible_ids) & ~Q(pk__in=dirty)
    # Narrow rows: identifiers plus the ordering columns the DISTINCT requires; the page
    # rows are hydrated afterwards through the native context of these 24 listings only.
    # Current eligible state already attests the approved revision's status;
    # dirty/unknown native IDs passed the original candidate predicate above.
    # Keep expiry and all user filters in the exact sibling built by candidates.
    population_query = (
        getattr(query, "_publication_state_population", query) if trusted_snapshot else query
    )
    population = population_query.select_related(None).filter(trusted_visible | Q(pk__in=native))
    if not multiplies_rows(population):
        # DISTINCT only removes duplicates created by many-valued joins; none are present.
        population.query.distinct = False
    projection = getattr(query, "_publication_projection", None)
    projected = trusted_snapshot and complete and not checked and projection is not None
    if projected:
        expires_after, text = projection
        population = PublicationState.objects.filter(
            eligible=True, rules_version=rules_version(), expires_at__gt=expires_after,
        )
        if text:
            search = SearchQuery(text, config="spanish", search_type="websearch") | SearchQuery(
                text, config="english", search_type="websearch"
            )
            population = population.filter(search_document=search).annotate(
                relevance=SearchRank(F("search_document"), search),
            ).order_by("-relevance", "-published_at", "listing_id")
        else:
            population = population.order_by("-published_at", "listing_id")
    identifier = "listing_id" if projected else "pk"
    if promotion_order is not None:
        # Commercial authority is selected in the same snapshot as membership,
        # count and the native page guard. It cannot add publication candidates.
        population = promotion_order(population, identifier, trusted_snapshot=trusted_snapshot)
        page = Paginator(population.values_list(identifier, "_promotion_priority"), 24).page(number)
        selected_rights = list(page.object_list)
        selected = [pk for pk, _ in selected_rights]
        page.sponsorship = {
            pk: ("premium" if priority == 0 else "top")
            for pk, priority in selected_rights if priority < 2
        }
    else:
        page = Paginator(population.values_list(identifier, flat=True), 24).page(number)
        selected = list(page.object_list)
    # Hydration through the native context doubles as the page guard. The rows were
    # already selected by the filters; the guard depends only on the listing itself.
    from .public_validation import _prepared_page_binding

    # Include this page's fresh catalog reads, not only its initial hydration.
    # The inner hydration scope nests/restores the same physical configuration.
    if batch_context is not None and set(selected) <= {row.pk for row in batch_context.rows}:
        context = batch_context
    else:
        # Retain native hydration if future ordering/protocol changes invalidate
        # prefix containment. The final guard still checks every selected row.
        with _prepared_page_binding(enabled=True):
            context = PublicationContext(
                Listing.objects.filter(pk__in=selected), page_read=True, prepared_page=True,
            )
    rows = {row.pk: row for row in context.rows}
    stale.extend(
        pk for pk in selected if pk not in rows or not publicly_visible(rows[pk], context=context)
    )
    if stale:
        if observation is not None:
            observation.update(route="fallback", reason="state_page_guard_changed")
        return None
    page.object_list = [rows[pk] for pk in selected]
    if observation is not None:
        observation.update(route="state", reason=(
            "trusted_state_extended_unknown" if extended_unknown else "trusted_state"),
                           native_unknown=len(unknown),
                           population="projection" if projected else "native_query")
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
