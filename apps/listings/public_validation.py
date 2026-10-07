"""Current-request publication validation; no persistent or cross-request cache."""

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Case, CharField, Exists, OuterRef, Prefetch, Q, Subquery, Value, When
from django.db.models.functions import Cast

from apps.core.models import RepresentationAction, VerificationCheck
from apps.mediafiles.models import Match, Photo
from apps.safety.models import PrivacyPublicationHold, Restriction, RightsPhotoReintroduction

from .forms import DetailsForm, RateForm
from .history import ordinary_matches, rectification_history_ids
from .submissions import current_publishing_document


class SnapshotChoice(forms.Field):
    """Validation-only scalar choice against the current request's catalog.

    No QuerySet is needed or copied: catalog construction already applied the
    original restricted queryset. Editing forms keep native ModelChoiceField.
    """

    widget = forms.Select
    default_error_messages = forms.ModelChoiceField.default_error_messages

    def __init__(self, *, queryset, to_field_name=None, **kwargs):
        # queryset is accepted for the common field factory, never evaluated or
        # retained. Membership comes exclusively from the fresh catalog snapshot.
        self.to_field_name = to_field_name
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if hasattr(value, "_meta"):
            return value.serializable_value(self.to_field_name) if self.to_field_name else value.pk
        return super().prepare_value(value)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            return self.snapshot[str(value)]
        except (KeyError, TypeError):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            ) from None


class SnapshotMultipleChoice(forms.ModelMultipleChoiceField):
    def _check_values(self, value):
        try:
            return [self.snapshot[str(item)] for item in frozenset(value)]
        except (KeyError, TypeError):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            ) from None


class SnapshotDetails(DetailsForm):
    @classmethod
    def fields_for_catalog(cls, catalog):
        fields = dict(cls.base_fields)
        for name, snapshot in catalog.items():
            original = fields[name]
            kind = (
                SnapshotMultipleChoice
                if isinstance(original, forms.ModelMultipleChoiceField)
                else SnapshotChoice
            )
            replacement = kind(
                queryset=original.queryset,
                required=original.required,
                validators=original.validators,
                error_messages=original.error_messages,
                to_field_name=original.to_field_name,
            )
            replacement.snapshot = snapshot
            fields[name] = replacement
        return fields

    def __init__(self, catalog, *args, prepared_fields=None, **kwargs):
        self.catalog = catalog
        # BaseForm deep-copies these fields: widgets, errors and validators remain
        # independent per form. Only the fresh request-local catalog is shared.
        self.base_fields = (
            prepared_fields if prepared_fields is not None else self.fields_for_catalog(catalog)
        )
        super().__init__(*args, **kwargs)

    def _get_validation_exclusions(self):
        # These FK targets were checked against fresh restricted querysets above.
        return super()._get_validation_exclusions() | {"municipality", "postal_code", "zone"}

    def postal_matches(self, postal, city):
        return city.pk in postal._publication_cities


class PublicationContext:
    def __init__(self, query):
        self.document = current_publishing_document()
        self.rate_checks = {}
        grant = RepresentationAction.objects.filter(
            person_id=OuterRef("person_id"),
            subject_id=OuterRef("person__subject_id"),
            manager_version=OuterRef("person__manager_version"),
            action="grant",
            document__slug="publishing",
            document__version=self.document.version if self.document else "",
            manager_kind=Case(
                When(person__agency_id__isnull=False, then=Value("agency")),
                default=Value("individual"),
            ),
            manager_id=Case(
                When(
                    person__agency_id__isnull=False,
                    then=Cast(OuterRef("person__agency_id"), CharField()),
                ),
                default=Cast(OuterRef("person__individual_id"), CharField()),
            ),
        )
        latest = VerificationCheck.objects.filter(person_id=OuterRef("person_id")).order_by(
            "-created_at"
        )
        conflict = ordinary_matches(
            Match.objects.filter(
                Q(photo__revision_id=OuterRef("approved_revision_id"))
                | Q(candidate__revision_id=OuterRef("approved_revision_id")),
                Q(resolved_at__isnull=True) | Q(decision="conflict"),
                photo__removed_at__isnull=True,
                candidate__removed_at__isnull=True,
                decision="conflict",
            )
        )
        query = query.annotate(
            _pv_history=Exists(
                rectification_history_ids().filter(pk=OuterRef("approved_revision_id"))
            ),
            _pv_rectification_upload=Exists(
                Photo.objects.filter(
                    revision_id=OuterRef("approved_revision_id"), rectification_upload__isnull=False
                )
            ),
            _pv_reintroduction=Exists(
                RightsPhotoReintroduction.objects.filter(
                    photo__revision_id=OuterRef("approved_revision_id")
                )
            ),
            _pv_hold=Exists(
                PrivacyPublicationHold.objects.filter(person_id=OuterRef("person_id"), active=True)
            ),
            _pv_restriction=Exists(
                Restriction.objects.filter(listing_id=OuterRef("pk"), active=True)
            ),
            _pv_grant=Exists(grant),
            _pv_conflict=Exists(conflict),
            _pv_check_status=Subquery(latest.values("status")[:1]),
            _pv_check_manager=Subquery(latest.values("manager_version")[:1]),
            _pv_check_subject=Subquery(latest.values("subject_id")[:1]),
        ).select_related(
            "approved_revision__publisher_acceptance__document",
            "approved_revision__municipality__province__region",
        )
        for name in ["categories", "services", "travel_areas", "rates"]:
            query = query.prefetch_related(Prefetch("approved_revision__" + name))
        query = query.prefetch_related(
            Prefetch(
                "approved_revision__photos",
                queryset=Photo.objects.filter(removed_at__isnull=True)
                .select_related("blob")
                .defer("blob__signature", "blob__regional_hashes"),
                to_attr="_pv_photos",
            )
        )
        self.rows = list(query)
        self.by_revision = {row.approved_revision_id: row for row in self.rows}
        ids = {
            name: set()
            for name in [
                "categories",
                "services",
                "travel_areas",
                "municipality",
                "province",
                "region",
                "postal_code",
                "zone",
            ]
        }
        for row in self.rows:
            revision = row.approved_revision
            for relation in ["categories", "services", "travel_areas", "rates"]:
                setattr(revision, "_pv_" + relation, list(getattr(revision, relation).all()))
            for name in ["categories", "services", "travel_areas"]:
                ids[name].update(item.pk for item in getattr(revision, "_pv_" + name))
            city = revision.municipality
            if city:
                ids["municipality"].add(city.pk)
                ids["province"].add(city.province_id)
                ids["region"].add(city.province.region_id)
            for name in ["postal_code", "zone"]:
                if getattr(revision, name + "_id"):
                    ids[name].add(getattr(revision, name + "_id"))
        self.catalog = {}
        for name, values in ids.items():
            catalog_query = DetailsForm.base_fields[name].queryset.filter(pk__in=values)
            if name == "municipality":
                catalog_query = catalog_query.select_related("province__region")
            self.catalog[name] = {str(item.pk): item for item in catalog_query}
        postals = list(self.catalog["postal_code"].values())
        if postals:
            from django.db.models import prefetch_related_objects

            prefetch_related_objects(postals, "municipalities")
            for postal in postals:
                postal._publication_cities = {city.pk for city in postal.municipalities.all()}
        self.details_fields = SnapshotDetails.fields_for_catalog(self.catalog)

    def row(self, revision):
        row = self.by_revision[revision.pk]
        if row.approved_revision is not revision:
            raise ValueError("Publication context requires its own current revision instance")
        return row

    def details(self, data, revision):
        self.row(revision)
        return SnapshotDetails(
            self.catalog, data, instance=revision, prepared_fields=self.details_fields
        )

    def rate_valid(self, rate):
        # The existing rate constraint/form depends only on these primitive values.
        values = tuple(getattr(rate, name) for name in RateForm.Meta.fields)
        if values not in self.rate_checks:
            self.rate_checks[values] = RateForm(
                dict(zip(RateForm.Meta.fields, values, strict=True)), instance=rate
            ).is_valid()
        return self.rate_checks[values]
