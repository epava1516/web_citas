def _ordered_reference(query, number, checked, observation, stale):
    # The dirty set is small; read it once instead of a correlated anti-join per candidate,
    # whose plan degrades with the dead tuples a high-churn table accumulates.
    dirty = list(PublicationDirty.objects.values_list("listing_id", flat=True)[: DIRTY_LIMIT + 1])
    if len(dirty) > DIRTY_LIMIT:
        if observation is not None:
            observation.update(route="fallback", reason="state_dirty_over_limit")
        return None
    unknown = []
    if dirty or not all_state_current():
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
    # Hydration through the native context doubles as the page guard. The rows were
    # already selected by the filters; the guard depends only on the listing itself.
    context = PublicationContext(Listing.objects.filter(pk__in=selected), page_read=True)
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
        observation.update(route="state", reason="trusted_state", native_unknown=len(unknown))
    return page
