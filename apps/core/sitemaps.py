"""Public crawl documents, bounded by candidate pages and existing visibility rules."""

from math import ceil
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_safe

from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext
from apps.listings.seo import absolute, listing_languages

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML = "http://www.w3.org/1999/xhtml"
PAGE_SIZE = 100
MAX_INDEX_ENTRIES = 50000


def candidates():
    return (
        Listing.objects.filter(
            status="published", approved_revision__status="approved", expires_at__gt=timezone.now()
        )
        .select_related("person__agency", "approved_revision")
        .order_by("pk")
    )


def xml_response(root):
    response = HttpResponse(
        tostring(root, encoding="utf-8", xml_declaration=True), content_type="application/xml"
    )
    response["Cache-Control"] = "no-store"
    if not settings.PRODUCTION:
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def add_urls(root, versions):
    for _, address in versions:
        node = SubElement(root, "url")
        SubElement(node, "loc").text = address
        for language, alternative in versions:
            SubElement(
                node, f"{{{XHTML}}}link", rel="alternate", hreflang=language, href=alternative
            )


@require_safe
def index(request):
    if request.GET:
        raise Http404
    pages = ceil(candidates().count() / PAGE_SIZE)
    if pages + 1 > MAX_INDEX_ENTRIES:
        response = HttpResponse(status=503)
        response["Cache-Control"] = "no-store"
        response["Retry-After"] = "60"
        return response
    root = Element("sitemapindex", xmlns=NS)
    for route, args in [("sitemap_directory", None)] + [
        ("sitemap_listings", [page]) for page in range(1, pages + 1)
    ]:
        node = SubElement(root, "sitemap")
        SubElement(node, "loc").text = settings.PUBLIC_ORIGIN + reverse(route, args=args)
    return xml_response(root)


@require_safe
def directory(request):
    if request.GET:
        raise Http404
    root = Element("urlset", xmlns=NS)
    add_urls(root, [(lang, absolute("home", lang)) for lang in ["es", "en"]])
    return xml_response(root)


@require_safe
def listings(request, page):
    if request.GET or page < 1:
        raise Http404
    queryset = candidates()
    count = queryset.count()
    if page > ceil(count / PAGE_SIZE):
        raise Http404
    offset = (page - 1) * PAGE_SIZE
    selected = queryset[offset : page * PAGE_SIZE]
    context = (
        PublicationContext(selected, page_read=True)
        if min(PAGE_SIZE, count - offset) > 1 else None
    )
    root = Element("urlset", xmlns=NS)
    for listing in context.rows if context is not None else selected:
        if publicly_visible(listing, context=context):
            versions = [
                (lang, absolute("listing_detail", lang, args=[listing.pk]))
                for lang in listing_languages(listing.approved_revision)
            ]
            add_urls(root, versions)
    return xml_response(root)


@require_safe
def robots(request):
    if not settings.PRODUCTION:
        body = "User-agent: *\nDisallow: /\n"
    else:
        private = [
            "account",
            "admin",
            "agency",
            "moderation",
            "rights",
            "safety",
            "person",
            "draft",
            "photos",
            "phone",
            "representation",
        ]
        lines = ["User-agent: *"]
        lines.extend(f"Disallow: /{lang}/{prefix}/" for lang in ["es", "en"] for prefix in private)
        lines.append("Sitemap: " + settings.PUBLIC_ORIGIN + reverse("sitemap_index"))
        body = "\n".join(lines) + "\n"
    response = HttpResponse(body, content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "no-store"
    if not settings.PRODUCTION:
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response
