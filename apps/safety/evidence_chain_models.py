"""Append-only hash metadata; never retains the original private payload."""

from django.db import models


class RightsEvidenceHead(models.Model):
    request = models.OneToOneField(
        "safety.RightsRequest", primary_key=True, on_delete=models.PROTECT
    )
    sequence = models.PositiveBigIntegerField(default=0)
    digest = models.CharField(max_length=64)


class RightsEvidenceEvent(models.Model):
    request = models.ForeignKey("safety.RightsRequest", on_delete=models.PROTECT)
    sequence = models.PositiveBigIntegerField()
    kind = models.CharField(max_length=12)
    source_table = models.CharField(max_length=100)
    source_pk = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    previous_digest = models.CharField(max_length=64)
    digest = models.CharField(max_length=64)
    created_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "sequence"], name="rights_chain_sequence_once"
            ),
            models.UniqueConstraint(
                fields=["source_table", "source_pk"],
                condition=models.Q(kind="row"),
                name="rights_chain_source_once",
            ),
            models.CheckConstraint(
                condition=models.Q(sequence__gte=1), name="rights_chain_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=["row", "tombstone"]), name="rights_chain_kind"
            ),
        ]
