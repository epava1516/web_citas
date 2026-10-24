from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import (
    Category,
    GeographicSource,
    Municipality,
    PostalCode,
    Province,
    Region,
    Zone,
)
from apps.listings.publication_state import refresh_all


class Command(BaseCommand):
    help = "Seed initial service catalog and explicitly synthetic geography"

    def handle(self, *args, **options):
        if settings.PRODUCTION:
            raise CommandError("Synthetic geography prohibited in production")
        Category.objects.get_or_create(
            slug="romantic-dating",
            defaults={"name_es": "Citas románticas", "name_en": "Romantic dating", "version": 1},
        )
        source, _ = GeographicSource.objects.get_or_create(
            key="synthetic-v1",
            defaults={
                "origin": "Project-generated synthetic fixture",
                "license": "Project-owned synthetic data; no national coverage",
                "version": "1",
                "synthetic": True,
            },
        )
        for code, label, cp in [
            ("demo-north", "Ciudad Demo Norte", "01001"),
            ("demo-south", "Ciudad Demo Sur", "29001"),
        ]:
            region, _ = Region.objects.get_or_create(
                code=code, defaults={"name": "Comunidad " + label, "source": source}
            )
            province, _ = Province.objects.get_or_create(
                code=code,
                defaults={"name": "Provincia " + label, "region": region, "source": source},
            )
            city, _ = Municipality.objects.get_or_create(
                code=code, defaults={"name": label, "province": province, "source": source}
            )
            postal, _ = PostalCode.objects.get_or_create(
                code=cp, defaults={"source": source, "public_safe": True}
            )
            postal.municipalities.add(city)
            Zone.objects.get_or_create(
                code=code + "-center",
                defaults={"name": "Zona Demo Centro", "municipality": city, "source": source},
            )
        # Global rule dependencies changed: recompute stored publication state now.
        refresh_all()
        self.stdout.write("Catalog seeded; geography is synthetic and limited")
