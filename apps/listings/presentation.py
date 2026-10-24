from django.utils import timezone

from apps.core.verification_services import real_checks

_UNSET = object()


def describe(listing, language, *, age=_UNSET):
    revision = listing.approved_revision
    english = language == "en"
    translated = revision.content_language != language and bool(revision.description_alternative)
    description = revision.description_alternative if translated else revision.description
    description_language = language if translated else revision.content_language

    def names(items):
        return [item.name_en if english else item.name_es for item in items]

    profile_names = {
        "": ("Sin indicar", "Not specified"),
        "woman": ("Mujer", "Woman"),
        "man": ("Hombre", "Man"),
        "trans": ("Trans", "Trans"),
        "other": ("Otro", "Other"),
    }
    language_names = {
        "es": ("Español", "Spanish"),
        "en": ("Inglés", "English"),
        "fr": ("Francés", "French"),
        "de": ("Alemán", "German"),
        "it": ("Italiano", "Italian"),
        "pt": ("Portugués", "Portuguese"),
    }
    day_names = [
        ("Lunes", "Monday"),
        ("Martes", "Tuesday"),
        ("Miércoles", "Wednesday"),
        ("Jueves", "Thursday"),
        ("Viernes", "Friday"),
        ("Sábado", "Saturday"),
        ("Domingo", "Sunday"),
    ]
    slots = {
        "morning": ("Mañana", "Morning"),
        "afternoon": ("Tarde", "Afternoon"),
        "evening": ("Noche", "Evening"),
    }
    if age is _UNSET:
        age = listing.person.verificationcheck_set.order_by("-created_at").first()
    age_simulated = bool(age and (age.provider == "simulator" or age.procedure == "simulator-v1"))
    checked = real_checks(listing.person, age)
    phone_procedure = listing.person.phone_claim.verification_procedure
    checks = [
        ("Edad: simulada", "Age: simulated")
        if age_simulated
        else ("Edad comprobada", "Age checked")
        if checked["age"]
        else ("Edad: comprobación sin acreditar", "Age: check not accredited")
    ]
    checks.append(
        ("Contacto: simulado", "Contact: simulated")
        if phone_procedure == "simulator-v1"
        else ("Control del contacto confirmado", "Contact control confirmed")
        if checked["contact"]
        else ("Contacto: comprobación sin acreditar", "Contact: check not accredited")
    )
    if listing.person.agency_id:
        procedure = listing.person.agency.verification_procedure
        checks.append(
            ("Agencia: comprobación simulada", "Agency: simulated check")
            if procedure == "simulator-v1"
            else ("Comprobación de agencia", "Agency check")
            if checked["agency"]
            else ("Agencia: comprobación sin acreditar", "Agency: check not accredited")
        )
    postal = revision.postal_code
    return {
        "description": description,
        "description_language": description_language,
        "profile_type": profile_names[revision.profile_type][int(english)],
        "trans_label": revision.show_trans_label and revision.profile_type != "trans",
        "categories": names(revision.categories.all()),
        "languages": [language_names[value][int(english)] for value in revision.spoken_languages],
        "days": [day_names[int(value) - 1][int(english)] for value in revision.days],
        "time_slot": slots.get(revision.time_slot, ("", ""))[int(english)],
        "postal_code": postal.code if postal and postal.public_safe else "",
        "checks": [pair[int(english)] for pair in checks],
        "available": bool(listing.available_until and listing.available_until > timezone.now()),
        "whatsapp_url": "https://wa.me/" + revision.phone.lstrip("+") if revision.whatsapp else "",
        "telegram_url": "https://t.me/" + revision.telegram.lstrip("@").strip()
        if revision.telegram
        else "",
    }
