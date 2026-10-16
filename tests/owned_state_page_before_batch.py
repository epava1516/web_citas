"""Frozen pre-batch selection at bbb8fc6; test-only comparison, not product code."""
from apps.listings import publication_state

SOURCE = r'''def _state_page(query, number, checked, observation, stale, *, trusted_snapshot=False):
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
        page = Paginator(population.values_list("listing_id", flat=True), 24).page(number)
    else:
        page = Paginator(population.values_list("pk", flat=True), 24).page(number)
    selected = list(page.object_list)
    # Hydration through the native context doubles as the page guard. The rows were
    # already selected by the filters; the guard depends only on the listing itself.
    from .public_validation import _prepared_page_binding

    # Include this page's fresh catalog reads, not only its initial hydration.
    # The inner hydration scope nests/restores the same physical configuration.
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
        observation.update(route="state", reason="trusted_state", native_unknown=len(unknown),
                           population="projection" if projected else "native_query")
    return page

'''


def build_native_reference():
    namespace = vars(publication_state).copy()
    exec(compile(SOURCE, "<pre-batch-native-reference>", "exec"), namespace)
    return namespace["_state_page"]
