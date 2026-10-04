from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.agencies import person_queryset
from apps.core.models import LegalAcceptance, LegalDocument
from apps.core.verification import locked_manager_person

from .forms import ContactsForm, DetailsForm, RateFormSet
from .models import Listing, Revision
from .revisions import create_draft, is_rectification_history
from .submissions import submit


class SubmissionForm(forms.Form):
    edit_version = forms.IntegerField(widget=forms.HiddenInput)
    declaration = forms.BooleanField(
        label="Confirmo datos veraces y derechos para publicar textos y fotos / I confirm accurate details and rights to publish texts and photos"
    )


@login_required
@require_POST
def send_for_review(request, revision_id):
    revision = get_object_or_404(
        Revision,
        pk=revision_id,
        listing__person__in=person_queryset(request.user),
        manager_version=F("listing__person__manager_version"),
    )
    form = SubmissionForm(request.POST)
    if form.is_valid():
        try:
            submit(
                request.user,
                revision.pk,
                form.cleaned_data["edit_version"],
                form.cleaned_data["declaration"],
            )
            return redirect("revision_status", revision_id=revision.pk)
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request, "listings/submission.html", {"revision": revision, "form": form}, status=400
    )


@login_required
def revision_status(request, revision_id):
    revision = get_object_or_404(
        Revision,
        pk=revision_id,
        listing__person__in=person_queryset(request.user),
        manager_version=F("listing__person__manager_version"),
    )
    if (
        is_rectification_history(revision)
        or revision.status == "rights-stage"
        or revision.photos.filter(rectification_upload__isnull=False).exists()
    ):
        return HttpResponse("Not found", status=404)
    return render(request, "listings/submission.html", {"revision": revision})


@login_required
@require_POST
def start(request, person_id):
    get_object_or_404(person_queryset(request.user), pk=person_id)
    with transaction.atomic():
        person = locked_manager_person(request.user, person_id)
        listing, _ = Listing.objects.get_or_create(person=person)
        listing = Listing.objects.select_for_update().get(pk=listing.pk)
        revision = (
            listing.revisions.filter(status="draft", manager_version=person.manager_version)
            .order_by("-created_at")
            .first()
        )
        if not revision:
            if (
                listing.revisions.filter(
                    status__in=["draft", "processing", "pending"],
                    manager_version=person.manager_version,
                ).count()
                >= 3
            ):
                return HttpResponse("Pending revision quota reached", status=409)
            revision = create_draft(listing, person)
    return redirect("draft_edit", revision_id=revision.pk, step=1)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, revision_id, step):
    revision = get_object_or_404(
        Revision.objects.select_related("listing__person", "municipality__province__region"),
        pk=revision_id,
        listing__person__in=person_queryset(request.user),
        manager_version=F("listing__person__manager_version"),
    )
    if step not in [1, 2, 3, 4]:
        return HttpResponse("Unknown step", status=404)
    if (
        is_rectification_history(revision)
        or revision.photos.filter(rectification_upload__isnull=False).exists()
    ):
        return HttpResponse("Not found", status=404)
    if (
        revision.status != "draft"
        or revision.manager_version != revision.listing.person.manager_version
    ):
        return HttpResponse("Revision obsolete or not editable", status=409)
    form, rates = None, None
    document = None
    if step == 1:
        form = DetailsForm(request.POST or None, instance=revision)
    elif step == 2:
        document = get_object_or_404(
            LegalDocument, slug="publishing", language=request.LANGUAGE_CODE, active=True
        )
        form = ContactsForm(
            request.POST or None, instance=revision, initial={"legal_version": document.version}
        )
        rates = RateFormSet(request.POST or None, instance=revision, prefix="rates")
    if request.method == "POST" and step in [1, 2]:
        valid = form.is_valid()
        if rates is not None:
            valid = rates.is_valid() and valid
        if step == 2:
            person = revision.listing.person
            claim = person.phone_claim
            if (
                not claim
                or not claim.verified_at
                or claim.individual_id != person.individual_id
                or claim.agency_id != person.agency_id
            ):
                form.add_error(
                    None, "Verifica antes el teléfono del gestor / Verify manager phone first"
                )
                valid = False
            if form.cleaned_data.get("legal_version") != document.version:
                form.add_error(None, "Condiciones actualizadas / Terms updated")
                valid = False
        if valid:
            with transaction.atomic():
                person = locked_manager_person(request.user, revision.listing.person_id)
                current = Revision.objects.select_for_update().get(pk=revision.pk)
                if (
                    current.status != "draft"
                    or current.manager_version != person.manager_version
                    or request.POST.get("edit_version") != str(current.edit_version)
                ):
                    return HttpResponse(
                        "Draft changed. Reload / Borrador cambiado. Recarga", status=409
                    )
                # Never overwrite another step with stale values from the form instance.
                for name in form._meta.fields:
                    if (
                        name in form.cleaned_data
                        and not Revision._meta.get_field(name).many_to_many
                    ):
                        setattr(current, name, form.cleaned_data[name])
                current.step = max(current.step, step + 1)
                current.edit_version += 1
                if step == 2:
                    document = LegalDocument.objects.select_for_update().get(pk=document.pk)
                    if not document.active:
                        return HttpResponse("Publishing terms changed", status=409)
                    claim = person.phone_claim
                    if (
                        not claim
                        or not claim.verified_at
                        or claim.individual_id != person.individual_id
                        or claim.agency_id != person.agency_id
                    ):
                        return HttpResponse("Contact changed", status=409)
                    current.phone = claim.phone
                    acceptance, _ = LegalAcceptance.objects.get_or_create(
                        user=request.user, document=document, action="publish", agency=person.agency
                    )
                    current.publisher_acceptance = acceptance
                current.save()
                for name in form._meta.fields:
                    if name in form.cleaned_data and Revision._meta.get_field(name).many_to_many:
                        getattr(current, name).set(form.cleaned_data[name])
                if rates is not None:
                    rates.instance = current
                    rates.save()
            return redirect("draft_edit", revision_id=current.pk, step=min(step + 1, 4))
    return render(
        request,
        "listings/draft.html",
        {
            "revision": revision,
            "step": step,
            "history_excluded": (
                revision.source_revision_id is None
                and revision.listing.approved_revision is not None
                and is_rectification_history(revision.listing.approved_revision)
            ),
            "form": form,
            "rates": rates,
            "document": document,
            "submission_form": SubmissionForm(initial={"edit_version": revision.edit_version}),
            "photos": revision.photos.filter(removed_at__isnull=True).select_related("blob"),
        },
        status=400 if request.method == "POST" and form is not None else 200,
    )
