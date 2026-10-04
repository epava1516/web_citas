from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.models import Person, User

from .models import Favorite, Listing
from .moderation import publicly_visible


@login_required
@require_GET
def index(request):
    favorites = Favorite.objects.filter(user=request.user).select_related(
        "listing__approved_revision", "listing__person__agency", "listing__person__phone_claim"
    )
    page = Paginator(favorites, 24).get_page(request.GET.get("page"))
    entries = [
        {"favorite": favorite, "visible": publicly_visible(favorite.listing)} for favorite in page
    ]
    response = render(request, "listings/favorites.html", {"entries": entries, "page": page})
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_POST
def add(request, listing_id):
    initial = get_object_or_404(Listing, pk=listing_id)
    with transaction.atomic():
        Person.objects.select_for_update().get(pk=initial.person_id)
        listing = Listing.objects.select_for_update().get(pk=listing_id)
        if not publicly_visible(listing):
            raise Http404
        actor = User.objects.select_for_update().get(pk=request.user.pk)
        if not actor.is_active or request.session.get("account_version") != actor.session_version:
            return HttpResponse(
                "Session changed; sign in again / Sesión cambiada; accede de nuevo", status=409
            )
        Favorite.objects.get_or_create(user=actor, listing=listing)
    return redirect("favorites")


@login_required
@require_POST
def remove(request, favorite_id):
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=request.user.pk)
        if not actor.is_active or request.session.get("account_version") != actor.session_version:
            return HttpResponse(
                "Session changed; sign in again / Sesión cambiada; accede de nuevo", status=409
            )
        favorite = get_object_or_404(Favorite, pk=favorite_id, user=actor)
        Favorite.objects.filter(pk=favorite.pk, user=actor).delete()
    return redirect("favorites")
