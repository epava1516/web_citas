"""Frozen pre-context public detail at e3fdb0e; test-only legacy reference."""
from apps.listings import moderation_views

SOURCE = r'''def public_detail(request, listing_id):
    from .public_validation import _prepared_page_binding
    from .seo import listing_metadata

    listing = get_object_or_404(
        Listing.objects.select_related("person__agency", "approved_revision"), pk=listing_id
    )
    # Only the native read guard; render and every other caller retain their
    # connection settings. get_object_or_404 above already connected this thread.
    with _prepared_page_binding(enabled=True):
        if not publicly_visible(listing):
            raise Http404
    response = render(
        request,
        "listings/public_detail.html",
        {
            "listing": listing,
            "seo": listing_metadata(request, listing),
            "revision": listing.approved_revision,
            "public": describe(listing, request.LANGUAGE_CODE),
            "report_target": signing.dumps(
                {"listing": str(listing.pk), "revision": str(listing.approved_revision_id)},
                salt="public-report-target-v1",
            ),
            "photos": listing.approved_revision.photos.filter(
                approved=True, removed_at__isnull=True
            ),
        },
    )
    response["Cache-Control"] = "no-store"
    return response
'''


def build_native_detail_reference():
    namespace = vars(moderation_views).copy()
    exec(compile(SOURCE, '<native-detail-reference>', 'exec'), namespace)
    return namespace['public_detail']
