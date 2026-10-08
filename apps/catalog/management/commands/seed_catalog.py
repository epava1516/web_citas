from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import (
    Category,
    GeographicSource,
    Municipality,
    PostalCode,
    Province,
    Region,
    Service,
    Zone,
)
from apps.listings.publication_state import refresh_all


class Command(BaseCommand):
    help = "Seed initial service catalog and explicitly synthetic geography"

    def handle(self, *args, **options):
        if settings.PRODUCTION:
            raise CommandError("Synthetic geography prohibited in production")
        catalog = [
            (
                "modeling",
                "Modelaje",
                "Modeling",
                [
                    ("photography", "Fotografía", "Photography"),
                    ("model-events", "Eventos de modelaje", "Modeling events"),
                ],
            ),
            (
                "social",
                "Acompañamiento social",
                "Social companionship",
                [
                    ("conversation", "Conversación", "Conversation"),
                    ("dinner", "Cena o evento", "Dinner or event"),
                    ("culture", "Planes culturales", "Cultural activities"),
                ],
            ),
            (
                "wellness",
                "Masajes de bienestar",
                "Wellness massage",
                [
                    ("relaxation", "Masaje relajante", "Relaxation massage"),
                    ("sports", "Deportivo no clínico", "Nonclinical sports massage"),
                ],
            ),
        ]
        for slug, es, en, services in catalog:
            category, _ = Category.objects.get_or_create(
                slug=slug, defaults={"name_es": es, "name_en": en}
            )
            for tag, tag_es, tag_en in services:
                Service.objects.get_or_create(
                    slug=tag, defaults={"category": category, "name_es": tag_es, "name_en": tag_en}
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
