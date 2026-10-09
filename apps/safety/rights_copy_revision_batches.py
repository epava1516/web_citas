"""Exact PostgreSQL UUID batches for locked copy rows and their relations."""

from itertools import islice

from django.db.models import F
from django.db.models.expressions import RawSQL

from apps.catalog.models import Category, Municipality, Service
from apps.listings.models import Rate
from apps.mediafiles.models import Photo


def batches(records, size):
    rows = records.iterator(chunk_size=size)
    while batch := list(islice(rows, size)):
        # IDs originate in the locked revision cursor; no SQL text interpolation.
        ids = RawSQL("SELECT unnest(%s::uuid[])", [[row.pk for row in batch]])
        specs = [
            ("copy_categories", Category.objects.order_by("slug"), "revision__pk"),
            ("copy_services", Service.objects.order_by("slug"), "revision__pk"),
            ("copy_travel_areas", Municipality.objects.order_by("code"), "travel_revisions__pk"),
            ("copy_rates", Rate.objects.order_by("pk"), "revision_id"),
            ("copy_photos", Photo.objects.select_related("blob").order_by("created_at", "pk"), "revision_id"),
        ]
        for attribute, queryset, relation in specs:
            grouped = {row.pk: [] for row in batch}
            for item in queryset.filter(**{relation + "__in": ids}).annotate(copy_parent=F(relation)):
                grouped[item.copy_parent].append(item)
            for row in batch:
                setattr(row, attribute, grouped[row.pk])
        yield from batch
