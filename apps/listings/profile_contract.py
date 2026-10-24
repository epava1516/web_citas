"""Versioned public profile policy; legacy records remain private evidence."""

from django.core.exceptions import ValidationError

CURRENT_CONTRACT = "romantic-v1"
LEGACY_CONTRACT = "legacy-professional-v1"
ROMANTIC_CATEGORY = "romantic-dating"
PROFESSIONAL_FIELDS = frozenset({
    "categories", "services", "travel_areas", "reception", "travel",
})


def rejects_professional_input(data):
    return any(
        name in PROFESSIONAL_FIELDS or name.startswith("rates-") for name in data
    )


def set_profile_catalog(revision):
    from apps.catalog.models import Category

    category = Category.objects.filter(slug=ROMANTIC_CATEGORY, active=True, version=1).first()
    if category is None:
        raise ValidationError("Catálogo no disponible / Profile catalogue unavailable")
    revision.categories.set([category])


def validate_profile_contract(revision, *, context=None):
    if revision.content_contract != CURRENT_CONTRACT:
        raise ValidationError(
            "Crea una nueva revisión de perfil romántico / Create a new romantic profile revision"
        )
    categories = revision._pv_categories if context else list(revision.categories.all())
    if len(categories) != 1 or not (
        categories[0].slug == ROMANTIC_CATEGORY and categories[0].active
        and categories[0].version == 1
    ):
        raise ValidationError("Catálogo de perfil inválido / Invalid profile catalogue")
    if (
        revision.reception or revision.travel
        or (revision._pv_services if context else revision.services.exists())
        or (revision._pv_travel_areas if context else revision.travel_areas.exists())
        or (revision._pv_rates if context else revision.rates.exists())
    ):
        raise ValidationError(
            "El perfil no admite servicios ni tarifas / Services and rates are not profile fields"
        )
