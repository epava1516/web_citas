"""Protected per-person authority; ordinary matching must not expose these rows."""

from django.db.models import Exists, OuterRef, Q

from .models import RightsRectificationPhotoDisposition


def active_withdrawals(person_id):
    rows = RightsRectificationPhotoDisposition.objects.filter(
        execution__notification__review__proposal__person_id=person_id
    )
    newer = rows.filter(blob_id=OuterRef("blob_id")).filter(
        Q(created_at__gt=OuterRef("created_at"))
        | Q(created_at=OuterRef("created_at"), pk__gt=OuterRef("pk"))
    )
    return rows.annotate(_superseded=Exists(newer)).filter(outcome="withdrawn", _superseded=False)
