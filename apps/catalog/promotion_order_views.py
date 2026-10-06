import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.agencies import person_queryset
from apps.safety.views import private

from .promotion_models import PromotionProductVersion
from .promotion_order_models import PromotionOrder
from .promotion_orders import actor, create_order, receive_event, synthetic_event, test_mode


class ProductChoice(forms.ModelChoiceField):
    def label_from_instance(self, item):
        return f"{item.name_es} / {item.name_en} · {item.amount} {item.currency}"


class ListingChoice(forms.ModelChoiceField):
    def label_from_instance(self, item):
        return item.person.alias


class OrderForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    listing = ListingChoice(queryset=None, label="Anuncio / Listing")
    product = ProductChoice(queryset=None, label="Producto de prueba / Test product")
    confirm = forms.BooleanField(
        label="Entiendo que es una simulación sin cobro / I understand this is a simulation with no charge"
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.listings.models import Listing

        self.fields["listing"].queryset = Listing.objects.filter(
            person__in=person_queryset(user), status="published"
        ).select_related("person")
        self.fields["product"].queryset = PromotionProductVersion.objects.filter(
            product__active=True,
            is_current=True,
            published_at__isnull=False,
            amount__gt=0,
            currency="EUR",
            tax_rate__isnull=False,
        ).select_related("product")


class SimulationForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("pending", "Pendiente / Pending"),
            ("failed", "Fallo / Failure"),
            ("succeeded", "Éxito simulado / Simulated success"),
        ]
    )
    confirm = forms.BooleanField(
        label="Solo simulación, sin pago real / Simulation only, no real payment"
    )


def credentials(request):
    test_mode()
    values = {
        "mfa_version": request.session.get("mfa_version"),
        "account_version": request.session.get("account_version"),
    }
    actor(request.user, **values)
    return values


@login_required
@require_http_methods(["GET", "POST"])
def orders(request):
    auth = credentials(request)
    form = OrderForm(request.POST or None, user=request.user, initial={"key": uuid.uuid4()})
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                row = create_order(
                    request.user,
                    form.cleaned_data["listing"].pk,
                    form.cleaned_data["product"].pk,
                    form.cleaned_data["key"],
                    **auth,
                )
            except ValidationError:
                form.add_error(
                    None,
                    "Configuración o publicación cambiada / Configuration or publication changed",
                )
                status = 409
            else:
                return private(redirect("promotion_order_detail", order_id=row.pk))
        else:
            status = 400
    page = Paginator(
        PromotionOrder.objects.filter(buyer=request.user)
        .select_related("product_version", "listing__person")
        .order_by("-created_at", "-pk"),
        25,
    ).get_page(request.GET.get("page"))
    return private(
        render(
            request, "catalog/promotion_orders.html", {"form": form, "page": page}, status=status
        )
    )


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, order_id):
    auth = credentials(request)
    order = get_object_or_404(
        PromotionOrder.objects.select_related(
            "product_version", "listing__person", "payment_attempt"
        ),
        pk=order_id,
        buyer=request.user,
    )
    form = SimulationForm(request.POST or None, initial={"key": uuid.uuid4()})
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                payload, signature = synthetic_event(
                    order.payment_attempt, form.cleaned_data["outcome"], form.cleaned_data["key"]
                )
                receive_event(request.user, payload, signature, **auth)
            except (ValidationError, PermissionDenied):
                form.add_error(
                    None,
                    "Simulación rechazada: publicación, sesión o estado cambiados / Simulation rejected: publication, session or state changed",
                )
                status = 409
            else:
                return private(redirect("promotion_order_detail", order_id=order.pk))
        else:
            status = 400
    return private(
        render(
            request,
            "catalog/promotion_order_detail.html",
            {"order": order, "form": form},
            status=status,
        )
    )
