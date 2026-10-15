"""Fresh page presentation reads, independent of publication eligibility.

Create only AFTER the publication guard/ranking/page selection. Each SELECT
uses current committed rows; never consume the guard's earlier prefetches.
Ties retain the ordinary per-card lookup rather than inventing a tie breaker.
"""
from collections import defaultdict

from django.db.models import F, Window
from django.db.models.functions import Rank

from apps.core.models import VerificationCheck
from apps.mediafiles.models import Photo

from .presentation import describe


class PagePresentation:
    def __init__(self, listings, *, grouped=True):
        self.photos = defaultdict(list)
        self.checks = defaultdict(list)
        self.stats = {"grouped": grouped, "photo_selected": 0, "photo_native": 0,
                      "check_selected": 0, "check_native": 0}
        if not grouped or not listings:
            return
        # All model fields remain available to callers, as on the native path.
        # Grouping removes queries; column reduction is a separate hypothesis.
        if tuple(Photo._meta.ordering or ()) == ("position", "created_at"):
            photos = Photo.objects.filter(
                revision_id__in={row.approved_revision_id for row in listings},
                approved=True, removed_at__isnull=True, blob__status="ready",
            ).annotate(_presentation_rank=Window(
                Rank(), partition_by=[F("revision_id")],
                order_by=[F("position").asc(), F("created_at").asc()],
            )).filter(_presentation_rank=1).order_by()
            for photo in photos:
                self.photos[photo.revision_id].append(photo)
        checks = VerificationCheck.objects.filter(
            person_id__in={row.person_id for row in listings},
        ).annotate(_presentation_rank=Window(
            Rank(), partition_by=[F("person_id")], order_by=F("created_at").desc(),
        )).filter(_presentation_rank=1).order_by()
        for check in checks:
            self.checks[check.person_id].append(check)

    def photo(self, listing):
        photos = self.photos[listing.approved_revision_id]
        if len(photos) == 1:
            self.stats["photo_selected"] += 1
            return photos[0]
        self.stats["photo_native"] += 1
        return listing.approved_revision.photos.filter(
            approved=True, removed_at__isnull=True, blob__status="ready",
        ).first()

    def describe(self, listing, language):
        # Preserve the guard snapshot for these relations, as the former
        # manager prefetch caches did. Photos/checks above stay fresh reads.
        revision = listing.approved_revision
        relations = {
            name: getattr(revision, "_pv_" + name)
            for name in ("categories", "services", "rates")
            if hasattr(revision, "_pv_" + name)
        }
        checks = self.checks[listing.person_id]
        if len(checks) == 1:
            self.stats["check_selected"] += 1
            return describe(listing, language, age=checks[0], relations=relations)
        self.stats["check_native"] += 1
        # Includes the native second lookup in real_checks when age is absent.
        return describe(listing, language, relations=relations)
