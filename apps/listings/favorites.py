from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.models import Person, User
from apps.safety.purpose_restrictions import blocked_response, restricted

from .models import Favorite, Listing
from .moderation import publicly_visible
from .public_validation import PublicationContext


@login_required
@require_GET
@transaction.atomic
def index(request):
    actor = User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
    if not actor.is_active or request.session.get("account_version") != actor.session_version:
        return HttpResponse(
            "Session changed; sign in again / Sesión cambiada; accede de nuevo", status=409
        )
    if restricted(actor, "account_preferences"):
        return blocked_response()
    favorites = Favorite.objects.filter(user=request.user).select_related(
        "listing__approved_revision", "listing__person__agency", "listing__person__phone_claim"
    )
    page = Paginator(favorites, 24).get_page(request.GET.get("page"))
    page_favorites = list(page)
    if len(page_favorites) > 1:
        context = PublicationContext(
            Listing.objects.filter(
                pk__in=[favorite.listing_id for favorite in page_favorites],
                approved_revision__isnull=False,
            ),
            page_read=True,
        )
        listings = {listing.pk: listing for listing in context.rows}
        entries = []
        for favorite in page_favorites:
            listing = listings.get(favorite.listing_id)
            if listing is not None:
                # Render the same fresh relation instance that was validated.
                favorite.listing = listing
            entries.append({
                "favorite": favorite,
                "visible": listing is not None and publicly_visible(listing, context=context),
            })
    else:
        entries = [
            {"favorite": favorite, "visible": publicly_visible(favorite.listing)}
            for favorite in page_favorites
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
        if restricted(actor, "account_preferences"):
            return blocked_response()
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
        if restricted(actor, "account_preferences"):
            return blocked_response()
        favorite = get_object_or_404(Favorite, pk=favorite_id, user=actor)
        Favorite.objects.filter(pk=favorite.pk, user=actor).delete()
    return redirect("favorites")
