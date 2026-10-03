from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

from apps.core.views import health, home

urlpatterns = [path("health/", health, name="health")]
urlpatterns += i18n_patterns(
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
)
