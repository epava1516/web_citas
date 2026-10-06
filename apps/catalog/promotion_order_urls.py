from django.urls import path

from . import promotion_order_views as views

urlpatterns = [
    path("", views.orders, name="promotion_orders"),
    path("<uuid:order_id>/", views.detail, name="promotion_order_detail"),
]
