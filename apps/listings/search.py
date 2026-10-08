"""The weighted bilingual document shared by stored and computed search."""
from django.contrib.postgres.search import SearchVector
from django.db.models import Case, CharField, When
from django.db.models.expressions import RawSQL


def revision_search_vector(prefix=""):
    # Constants are typed before CASE, so the generated expression contains no
    # runtime text-to-regconfig catalog lookup (PostgreSQL requires IMMUTABLE).
    primary = Case(
        When(**{prefix + "content_language": "en"}, then=RawSQL("'english'::regconfig", [])),
        default=RawSQL("'spanish'::regconfig", []), output_field=CharField(),
    )
    alternative = Case(
        When(**{prefix + "content_language": "en"}, then=RawSQL("'spanish'::regconfig", [])),
        default=RawSQL("'english'::regconfig", []), output_field=CharField(),
    )
    return (
        SearchVector(prefix + "title", weight="A", config=primary)
        + SearchVector(prefix + "description", weight="B", config=primary)
        + SearchVector(prefix + "description_alternative", weight="B", config=alternative)
    )
