from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.listings.moderation import conflict_of_interest, reviewer_allowed

from .models import Agency, ManagerReview, Person


class ReviewForm(forms.Form):
    manager_version = forms.IntegerField(widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("", "Selecciona / Choose"),
            ("approved", "Aprobar / Approve"),
            ("failed", "Rechazar / Reject"),
        ]
    )
    reason = forms.CharField(max_length=1000, widget=forms.Textarea, label="Motivo / Reason")


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "core/manager_queue.html",
        {
            "people": Person.objects.filter(manager_review_status="pending").order_by("created_at")[
                :100
            ]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, person_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    person = get_object_or_404(Person, pk=person_id)
    if conflict_of_interest(request.user, person):
        return HttpResponse("Conflict of interest", status=403)
    form = ReviewForm(request.POST or None, initial={"manager_version": person.manager_version})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if person.agency_id:
                Agency.objects.select_for_update().get(pk=person.agency_id)
            person = Person.objects.select_for_update().get(pk=person.pk)
            if conflict_of_interest(request.user, person):
                return HttpResponse("Conflict of interest", status=403)
            if (
                person.manager_review_status != "pending"
                or form.cleaned_data["manager_version"] != person.manager_version
            ):
                return HttpResponse("Manager review changed", status=409)
            if form.cleaned_data["outcome"] == "approved" and (
                not person.subject_id
                or person.age_status != "passed"
                or person.consent_revoked_at
                or person.consent_version != person.manager_version
                or (person.agency_id and person.agency.verification_status != "passed")
            ):
                form.add_error(
                    None,
                    "Verifica edad y autorización directa / Verify age and direct authorization",
                )
            else:
                ManagerReview.objects.create(
                    person=person,
                    reviewer=request.user,
                    manager_version=person.manager_version,
                    outcome=form.cleaned_data["outcome"],
                    reason=form.cleaned_data["reason"],
                )
                person.manager_review_status = form.cleaned_data["outcome"]
                person.save(update_fields=["manager_review_status"])
                return redirect("manager_review", person_id=person.pk)
    return render(
        request,
        "core/manager_review.html",
        {"person": person, "form": form},
        status=400 if request.method == "POST" else 200,
    )
