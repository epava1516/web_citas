"""A shared SQL classification of revisions retained after correction."""

from django.db.models import Exists, OuterRef, Q

from .models import Revision


def rectification_history_ids():
    from apps.safety.models import RightsRectificationExecution

    executions = (
        RightsRectificationExecution.objects.filter(
            notification__review__proposal__person_id=OuterRef("listing__person_id")
        )
        .exclude(corrected_revision_id=OuterRef("pk"))
        .filter(
            Q(notification__review__proposal__source_revision_id=OuterRef("pk"))
            | Q(created_at__gt=OuterRef("created_at"))
        )
    )
    return (
        Revision.objects.annotate(_rights_history=Exists(executions))
        .filter(_rights_history=True)
        .values("pk")
    )


def is_rectification_history(revision):
    return rectification_history_ids().filter(pk=revision.pk).exists()


def ordinary_matches(queryset):
    return (
        queryset.exclude(photo__revision_id__in=rectification_history_ids())
        .exclude(candidate__revision_id__in=rectification_history_ids())
        .exclude(photo__revision__status="rights-stage")
        .exclude(candidate__revision__status="rights-stage")
        .exclude(photo__rectification_upload__isnull=False)
        .exclude(candidate__rectification_upload__isnull=False)
    )
