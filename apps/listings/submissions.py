from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.models import LegalDocument, RepresentationAction
from apps.core.verification import locked_manager_person
from apps.core.verification_services import publication_ready

from .forms import ContactsForm, DetailsForm, RateForm
from .models import Listing, Revision, Submission
from .revisions import is_rectification_history


def current_publishing_document():
    return (
        LegalDocument.objects.filter(active=True, slug="publishing")
        .order_by("-published_at", "-pk")
        .first()
    )


def validate_submission(revision, person):
    if (
        revision.status == "rights-stage"
        or revision.photos.filter(rectification_upload__isnull=False).exists()
    ):
        raise ValidationError(
            "Rights image preparation cannot publish / Preparación de imágenes de derechos no publicable"
        )

    from apps.safety.models import PrivacyPublicationHold, Restriction

    if is_rectification_history(revision):
        raise ValidationError(
            "Versión histórica rectificada; usa una nueva revisión / Corrected historical version; use a new revision"
        )
    if person.publication_erased_at:
        raise ValidationError("Publicación suprimida / Publication erased")
    if PrivacyPublicationHold.objects.filter(person=person, active=True).exists():
        raise ValidationError(
            "Publicación limitada por privacidad / Publication limited for privacy"
        )
    if Restriction.objects.filter(listing_id=revision.listing_id, active=True).exists():
        raise ValidationError("Restricción pendiente de revisión / Restriction awaiting review")
    if revision.manager_version != person.manager_version or not publication_ready(person):
        raise ValidationError(
            "Verifica edad, autorización y teléfono / Verify age, authorization and phone"
        )
    # Organization verification is a separate prerequisite, never implied by MFA.
    if person.agency_id and (
        person.agency.verification_status != "passed"
        or (settings.PRODUCTION and person.agency.verification_procedure == "simulator-v1")
    ):
        raise ValidationError("Comprobación de agencia pendiente / Agency review pending")
    document = current_publishing_document()
    acceptance = revision.publisher_acceptance
    if (
        not document
        or not acceptance
        or not acceptance.document.active
        or acceptance.document.slug != "publishing"
        or acceptance.document.version != document.version
        or acceptance.action != "publish"
        or acceptance.agency_id != person.agency_id
    ):
        raise ValidationError("Condiciones de publicación actualizadas / Publishing terms updated")
    if not RepresentationAction.objects.filter(
        person=person,
        subject_id=person.subject_id,
        manager_version=person.manager_version,
        manager_kind="agency" if person.agency_id else "individual",
        manager_id=str(person.agency_id or person.individual_id),
        action="grant",
        document__slug="publishing",
        document__version=document.version,
    ).exists():
        raise ValidationError("Renueva la autorización directa / Renew direct authorization")
    check = person.verificationcheck_set.order_by("-created_at").first()
    if (
        not check
        or check.status != "passed"
        or check.manager_version != person.manager_version
        or check.subject_id != person.subject_id
    ):
        raise ValidationError("Comprobación de edad pendiente / Age verification pending")
    if revision.phone != person.phone_claim.phone:
        raise ValidationError("El teléfono ha cambiado / Phone changed")
    city = revision.municipality
    if not city:
        raise ValidationError("Ciudad obligatoria / City required")
    data = {
        name: getattr(revision, name)
        for name in DetailsForm.Meta.fields
        if not Revision._meta.get_field(name).many_to_many
    }
    data.update(
        {
            name: list(getattr(revision, name).values_list("pk", flat=True))
            for name in ["categories", "services", "travel_areas"]
        }
    )
    data.update(
        region=city.province.region_id,
        province=city.province_id,
        municipality=city.pk,
        postal_code=revision.postal_code_id or "",
        zone=revision.zone_id or "",
    )
    form = DetailsForm(data, instance=revision)
    if not form.is_valid():
        raise ValidationError("Corrige datos y ubicación / Correct details and location")
    contacts = ContactsForm(
        {
            "whatsapp": revision.whatsapp,
            "telegram": revision.telegram,
            "contact_exposure_accepted": revision.contact_exposure_accepted,
            "accept_publishing": True,
            "legal_version": document.version,
        },
        instance=revision,
    )
    if not contacts.is_valid():
        raise ValidationError("Corrige los contactos / Correct contacts")
    rates = list(revision.rates.all())
    if len(rates) > 10 or any(
        not RateForm(
            {name: getattr(rate, name) for name in RateForm.Meta.fields}, instance=rate
        ).is_valid()
        for rate in rates
    ):
        raise ValidationError("Corrige las tarifas / Correct rates")
    photos = list(revision.photos.filter(removed_at__isnull=True).select_related("blob"))
    if not 1 <= len(photos) <= 8 or any(
        photo.blob.status != "ready" or not photo.comparison_complete for photo in photos
    ):
        raise ValidationError("Espera al procesamiento de las fotos / Wait for photo processing")
    return acceptance.document


@transaction.atomic
def submit(user, revision_id, edit_version, declared):
    initial = Revision.objects.get(pk=revision_id)
    person = locked_manager_person(user, initial.listing.person_id)
    listing = Listing.objects.select_for_update().get(pk=initial.listing_id)
    revision = Revision.objects.select_for_update().get(pk=revision_id)
    if revision.manager_version != person.manager_version:
        raise ValidationError("Gestor cambiado / Manager changed")
    if revision.status == "pending" and Submission.objects.filter(revision=revision).exists():
        return revision  # A browser retry never creates a second declaration or queue item.
    if revision.status != "draft" or str(revision.edit_version) != str(edit_version):
        raise ValidationError("Borrador cambiado; recarga / Draft changed; reload")
    if not declared:
        raise ValidationError("Confirma veracidad y derechos / Confirm accuracy and rights")
    document = validate_submission(revision, person)
    Submission.objects.create(
        revision=revision, actor=user, document=document, approved_base=listing.approved_revision
    )
    revision.status = "pending"
    revision.save(update_fields=["status", "updated_at"])
    if not listing.approved_revision_id:
        listing.status = "pending"
        listing.save(update_fields=["status"])
    return revision
