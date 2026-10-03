import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import GeographicSource, Municipality, PostalCode, Province, Region, Zone


class Command(BaseCommand):
    help = "Import a licensed, versioned local geographic JSON dataset atomically"

    def add_arguments(self, parser):
        parser.add_argument("dataset")

    def handle(self, *args, **options):
        path = Path(options["dataset"])
        if path.stat().st_size > 20 * 1024 * 1024:
            raise CommandError("Dataset exceeds 20 MiB")
        try:
            data = json.loads(path.read_text())
            metadata = data["source"]
            for key in ["key", "origin", "license", "version"]:
                if not isinstance(metadata.get(key), str) or not metadata[key].strip():
                    raise ValueError("Source metadata missing: " + key)
            if type(metadata.get("synthetic")) is not bool:
                raise ValueError("Explicit synthetic true/false required")
            if settings.PRODUCTION and metadata["synthetic"]:
                raise ValueError("Synthetic geography prohibited in production")
            with transaction.atomic():
                source, _ = GeographicSource.objects.update_or_create(
                    key=metadata["key"],
                    defaults={
                        key: metadata[key] for key in ["origin", "license", "version", "synthetic"]
                    },
                )
                for row in data["regions"]:
                    Region.objects.update_or_create(
                        code=row["code"], defaults={"name": row["name"], "source": source}
                    )
                for row in data["provinces"]:
                    Province.objects.update_or_create(
                        code=row["code"],
                        defaults={
                            "name": row["name"],
                            "source": source,
                            "region": Region.objects.get(code=row["region"]),
                        },
                    )
                for row in data["municipalities"]:
                    Municipality.objects.update_or_create(
                        code=row["code"],
                        defaults={
                            "name": row["name"],
                            "source": source,
                            "province": Province.objects.get(code=row["province"]),
                            "active": row.get("active", True),
                        },
                    )
                for row in data.get("postal_codes", []):
                    code = row["code"]
                    if (
                        not isinstance(code, str)
                        or len(code) != 5
                        or not code.isascii()
                        or not code.isdigit()
                    ):
                        raise ValueError("Spanish postal code must be five ASCII digits")
                    cities = [
                        Municipality.objects.get(code=value) for value in row["municipalities"]
                    ]
                    if not cities:
                        raise ValueError("Postal code needs municipality correspondence")
                    postal, _ = PostalCode.objects.update_or_create(
                        code=code,
                        defaults={"source": source, "public_safe": row.get("public_safe", False)},
                    )
                    postal.municipalities.set(cities)
                for row in data.get("zones", []):
                    Zone.objects.update_or_create(
                        code=row["code"],
                        defaults={
                            "name": row["name"],
                            "source": source,
                            "municipality": Municipality.objects.get(code=row["municipality"]),
                            "active": row.get("active", True),
                        },
                    )
        except (
            ValueError,
            KeyError,
            TypeError,
            Region.DoesNotExist,
            Province.DoesNotExist,
            Municipality.DoesNotExist,
        ) as error:
            raise CommandError(f"Geography import rolled back: {error}") from error
        self.stdout.write(
            "Geography imported. Metadata does not establish legal approval or full coverage."
        )
