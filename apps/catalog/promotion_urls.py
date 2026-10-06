from django.urls import path

from . import promotion_views as views

urlpatterns = [
    path("", views.products, name="promotion_products"),
    path("<uuid:product_id>/", views.versions, name="promotion_product_versions"),
    path("<uuid:product_id>/versions/<int:number>/", views.edit, name="promotion_version_edit"),
    path(
        "<uuid:product_id>/versions/<int:number>/preview/",
        views.preview,
        name="promotion_version_preview",
    ),
]
