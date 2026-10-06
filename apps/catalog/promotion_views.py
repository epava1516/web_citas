from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.safety.views import private

from .promotion_forms import ProductForm, VersionForm
from .promotion_models import PromotionProduct, PromotionProductVersion
from .promotion_services import (
    EDITABLE,
    authority,
    create_product,
    create_version,
    publish_version,
    update_version,
)


def credentials(request):
    values = (
        request.user,
        request.session.get("mfa_version"),
        request.session.get("account_version"),
    )
    authority(*values)
    return values


@login_required
@require_http_methods(["GET", "POST"])
def products(request):
    auth = credentials(request)
    form = ProductForm(request.POST or None)
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                row = create_product(*auth, form.cleaned_data)
            except (ValidationError, IntegrityError):
                form.add_error(None, "Producto cambiado o inválido / Product changed or invalid")
                status = 409
            else:
                return private(
                    redirect(
                        "promotion_version_edit", product_id=row.product_id, number=row.version
                    )
                )
        else:
            status = 400
    page = Paginator(PromotionProduct.objects.all(), 50).get_page(request.GET.get("page"))
    return private(
        render(
            request, "catalog/promotion_products.html", {"form": form, "page": page}, status=status
        )
    )


@login_required
@require_http_methods(["GET", "POST"])
def versions(request, product_id):
    auth = credentials(request)
    product = get_object_or_404(PromotionProduct, pk=product_id)
    if request.method == "POST":
        row = create_version(*auth, product.pk)
        return private(
            redirect("promotion_version_edit", product_id=product.pk, number=row.version)
        )
    page = Paginator(product.versions.all(), 50).get_page(request.GET.get("page"))
    return private(
        render(request, "catalog/promotion_versions.html", {"product": product, "page": page})
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, product_id, number):
    auth = credentials(request)
    row = get_object_or_404(
        PromotionProductVersion.objects.select_related("product"),
        product_id=product_id,
        version=number,
    )
    form = VersionForm(request.POST or None, instance=row)
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                row = update_version(
                    *auth,
                    product_id,
                    number,
                    form.cleaned_data["edit_version"],
                    {name: form.cleaned_data[name] for name in EDITABLE},
                )
            except ValidationError as error:
                form.add_error(None, error)
                status = 409
            else:
                return private(
                    redirect("promotion_version_preview", product_id=product_id, number=number)
                )
        else:
            status = 400
    return private(
        render(request, "catalog/promotion_edit.html", {"form": form, "row": row}, status=status)
    )


@login_required
@require_http_methods(["GET", "POST"])
def preview(request, product_id, number):
    auth = credentials(request)
    row = get_object_or_404(
        PromotionProductVersion.objects.select_related("product"),
        product_id=product_id,
        version=number,
    )
    error = None
    if request.method == "POST":
        try:
            expected = int(request.POST.get("edit_version", ""))
            row = publish_version(*auth, product_id, number, expected)
        except (ValueError, ValidationError) as exception:
            error = str(exception)
        else:
            return private(
                redirect("promotion_version_preview", product_id=product_id, number=number)
            )
    return private(
        render(
            request,
            "catalog/promotion_preview.html",
            {"row": row, "error": error},
            status=409 if error else 200,
        )
    )
