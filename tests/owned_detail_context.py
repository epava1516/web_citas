"""Test-only fresh native context for public detail; no application changes."""
import inspect
import textwrap

from django.db import connection
from django.db.models import F
from django.urls import URLResolver, get_resolver
from django.utils import timezone

from apps.listings import moderation_views
from apps.listings.public_validation import PublicationContext


def build_detail_context_prototype():
    source = textwrap.dedent(inspect.getsource(moderation_views.public_detail))
    before = '''    listing = get_object_or_404(
        Listing.objects.select_related("person__agency", "approved_revision"), pk=listing_id
    )
    # Only the native read guard; render and every other caller retain their
    # connection settings. get_object_or_404 above already connected this thread.
    with _prepared_page_binding(enabled=True):
        if not publicly_visible(listing):
            raise Http404
'''
    after = '''    connection.ensure_connection()
    with _prepared_page_binding(enabled=True):
        context = PublicationContext(
            Listing.objects.filter(
                pk=listing_id, status="published", expires_at__gt=timezone.now(),
                approved_revision__status="approved", approved_revision__listing_id=F("pk"),
            ), page_read=True, prepared_page=True,
        )
        if not context.rows:
            raise Http404
        listing = context.rows[0]
        if not publicly_visible(listing, context=context):
            raise Http404
'''
    assert source.count(before) == 1
    namespace = vars(moderation_views).copy()
    namespace.update(connection=connection, F=F, timezone=timezone, PublicationContext=PublicationContext)
    exec(compile(source.replace(before, after), '<owned-detail-context>', 'exec'), namespace)
    return namespace['public_detail']


def patch_detail_view(patch, implementation):
    found = []

    def visit(patterns):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                visit(pattern.url_patterns)
            elif pattern.callback is moderation_views.public_detail:
                patch.setattr(pattern, 'callback', implementation)
                found.append(pattern)

    visit(get_resolver().url_patterns)
    assert len(found) == 1
