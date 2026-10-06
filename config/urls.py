from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

from apps.core import sitemaps
from apps.core.views import health, home

urlpatterns = [
    path("health/", health, name="health"),
    path("robots.txt", sitemaps.robots, name="robots"),
    path("sitemap.xml", sitemaps.index, name="sitemap_index"),
    path("sitemaps/directory.xml", sitemaps.directory, name="sitemap_directory"),
    path("sitemaps/listings/<int:page>.xml", sitemaps.listings, name="sitemap_listings"),
]
urlpatterns += i18n_patterns(
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("account/test-promotions/", include("apps.catalog.promotion_order_urls")),
    path("operations/promotion-products/", include("apps.catalog.promotion_urls")),
    path("", include("apps.core.urls")),
)
