from django.urls import path

from .rights_object_views import authorize

urlpatterns = [
    path("internal/rights-objects/authorize/", authorize, name="rights_object_authorize")
]
