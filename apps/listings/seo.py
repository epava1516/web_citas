"""Metadata derived only from already authorized public pages and revisions."""

from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.html import strip_tags


def plain(value):
    return " ".join(strip_tags(value).split())


def absolute(route, language, *, args=None, page=1):
    with translation.override(language):
        path = reverse(route, args=args)
    return settings.PUBLIC_ORIGIN + path + ("?" + urlencode({"page": page}) if page > 1 else "")


def directory_metadata(request, *, valid, page):
    english = request.LANGUAGE_CODE == "en"
    title = "Find professionals in Spain" if english else "Encuentra profesionales en España"
    description = (
        "Explore modeling, social companionship and nonsexual wellness listings by city and services."
        if english
        else "Encuentra anuncios de modelaje, acompañamiento social y bienestar no sexual por ciudad y servicios."
    )
    # Do not reflect free text, contact data or arbitrary query parameters into
    # indexable metadata. Filter combinations remain available for navigation.
    noindex = not valid or any(key != "page" for key in request.GET)
    return {
        "title": title,
        "description": description,
        "noindex": noindex,
        "canonical": absolute("home", request.LANGUAGE_CODE, page=page) if not noindex else "",
        "alternates": [(lang, absolute("home", lang, page=page)) for lang in ["es", "en"]]
        if not noindex
        else [],
    }


def listing_languages(revision):
    translated = bool(plain(revision.description_alternative)) and (
        plain(revision.description_alternative) != plain(revision.description)
    )
    return ["es", "en"] if translated else [revision.content_language]


def listing_metadata(request, listing):
    revision = listing.approved_revision
    primary = revision.content_language
    languages = listing_languages(revision)
    requested = request.LANGUAGE_CODE
    actual = requested if requested in languages else primary
    description = revision.description if actual == primary else revision.description_alternative
    metadata = {
        "title": plain(revision.title) + " · " + str(revision.municipality),
        "description": plain(description)[:160],
        "noindex": requested not in languages,
        "canonical": absolute("listing_detail", actual, args=[listing.pk]),
        "alternates": [
            (lang, absolute("listing_detail", lang, args=[listing.pk])) for lang in languages
        ],
    }

    if requested in languages:
        metadata["structured_data"] = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "url": metadata["canonical"],
            "name": metadata["title"],
            "description": metadata["description"],
            "inLanguage": actual,
            "about": {"@type": "Person", "name": listing.person.alias},
        }
    return metadata
