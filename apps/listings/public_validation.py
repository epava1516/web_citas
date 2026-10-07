"""Current-request publication validation; no persistent or cross-request cache."""

from copy import copy
from functools import wraps

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Case, CharField, Exists, OuterRef, Prefetch, Q, Subquery, Value, When
from django.db.models.functions import Cast
from django.forms.models import model_to_dict
from django.utils.translation import get_language

from apps.catalog.models import Municipality
from apps.core.models import LegalAcceptance, RepresentationAction, VerificationCheck
from apps.mediafiles.models import Blob, Match, Photo
from apps.safety.models import PrivacyPublicationHold, Restriction, RightsPhotoReintroduction

from .contact_validation import (
    MODEL_NAMES,
    contact_success_key,
    form_fields_signature,
    form_methods_supported,
)
from .forms import ContactsForm, DetailsForm, RateForm
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
        self._validation_prototypes = {}
        self.field_clean_cache_stats = {}
        self._contact_successes = {}
        self.contact_validation_stats = {"calls": 0, "hits": 0, "misses": 0, "fallbacks": 0}
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
        ).select_related(None).select_related(
            "approved_revision", "person__phone_claim",
        ).prefetch_related(
            "person__agency",
            Prefetch(
                "approved_revision__publisher_acceptance",
                queryset=LegalAcceptance.objects.select_related("document"),
            ),
            Prefetch(
                "approved_revision__municipality",
                queryset=Municipality.objects.select_related("province__region"),
            ),
        )
        for name in ["categories", "services", "travel_areas", "rates"]:
            query = query.prefetch_related(Prefetch("approved_revision__" + name))
        query = query.prefetch_related(
            Prefetch(
                "approved_revision__photos",
                queryset=Photo.objects.filter(removed_at__isnull=True)
                .prefetch_related(Prefetch(
                    "blob", queryset=Blob.objects.defer("signature", "regional_hashes")
                )),
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

    def _validation_prototype(self, form_class, data, revision):
        key = (form_class, id(self.catalog), get_language())
        if form_class is ContactsForm:
            # A changed base definition gets a new request-local prototype. An
            # unknown configuration cannot reuse a previously validated result.
            key += (form_fields_signature(ContactsForm.base_fields),)
        if key not in self._validation_prototypes:
            prototype = (
                self.details(data, revision)
                if form_class is SnapshotDetails
                else form_class(data, instance=revision)
            )
            for name, field in prototype.fields.items():
                if name != "title":
                    self._memoize_field_clean(form_class.__name__ + "." + name, field)
            self._validation_prototypes[key] = prototype
        return self._validation_prototypes[key]

    def _bound_validation(self, form_class, data, revision, *, native_fields=False):
        """Share definitions and successful scalar field cleaning within a request.

        Key: form class, request-owned catalog identity, active language. The
        source-defined fields/options and restricted catalog belong to this
        context only. These two forms do not mutate field configuration while
        cleaning. Memo keys include the prototype's actual field configuration,
        validators, fresh catalog, language and exact typed input. Mutable result
        containers are copied; native validation runs on every uncached binding.
        Contact success reuse is separately gated by its complete dependency key.
        No representation, document, revocation or eligibility result is reused.
        """
        if form_class not in (SnapshotDetails, ContactsForm):
            raise ValueError("Only the audited stateless publication forms can share definitions")
        self.row(revision)
        form = copy(self._validation_prototype(form_class, data, revision))
        form.instance = revision
        form.data = data
        # These private, bound forms are validated, never rendered or used for
        # changed_data. Native cleaning reads initial only for disabled fields
        # or empty_permitted/has_changed; retain native initial for those cases.
        needs_initial = form.empty_permitted or any(field.disabled for field in form.fields.values())
        form.initial = (
            model_to_dict(revision, form._meta.fields, form._meta.exclude)
            if needs_initial else {}
        )
        if needs_initial and form_class is SnapshotDetails and revision.municipality_id:
            city = revision.municipality
            form.initial.setdefault("province", city.province_id)
            form.initial.setdefault("region", city.province.region_id)
        form.fields = dict(form.fields)
        if native_fields:
            form.fields = {name: copy(field) for name, field in form.fields.items()}
            for field in form.fields.values():
                native = (field._publication_native_clean
                          if field.clean is getattr(field, "_publication_memo_clean", None)
                          else field.clean)
                if hasattr(native, "__func__"):
                    field.clean = native.__func__.__get__(field, type(field))
        form._errors = None
        form._bound_fields_cache = {}
        form._validate_unique = False
        form.__dict__.pop("changed_data", None)
        form.__dict__.pop("cleaned_data", None)
        try:
            return form.is_valid()
        finally:
            # A BoundField points back to its form. These private bindings return
            # only a boolean and are never rendered; release their reverse cache
            # after native cleaning instead of leaving successful cycles for GC.
            form._bound_fields_cache.clear()

    def _memoize_field_clean(self, name, field):
        # Field.clean receives only value; instance/cross-field/model/authority
        # checks are outside it and still run for every fresh binding. Audited
        # field definitions/catalog/language are fixed in this prototype only.
        original = field.clean
        memo = {}
        stats = self.field_clean_cache_stats.setdefault(name, {"calls": 0, "hits": 0, "misses": 0})

        def freeze(value):
            if value is None or type(value) in (str, bool, int):
                return (type(value), value)
            if type(value) in (list, tuple):
                return (type(value), tuple(freeze(item) for item in value))
            raise TypeError("Unsupported field input remains natively validated")

        def independent(value):
            if isinstance(value, list):
                return list(value)
            if hasattr(value, "all"):
                # Optional empty ModelMultipleChoice returns a native QuerySet.
                return value.all()
            return value

        @wraps(original)
        def clean(value):
            stats["calls"] += 1
            try:
                key = freeze(value)
            except TypeError:
                stats["misses"] += 1
                return original(value)
            if key in memo:
                stats["hits"] += 1
                return independent(memo[key])
            stats["misses"] += 1
            # Errors are never cached or shared; native exception data stays local.
            cleaned = original(value)
            memo[key] = cleaned
            return independent(cleaned)

        field._publication_native_clean = original
        field._publication_memo_clean = clean
        field.clean = clean

    def details_valid(self, data, revision):
        return self._bound_validation(SnapshotDetails, data, revision)

    def contacts_valid(self, data, revision):
        self.row(revision)
        stats = self.contact_validation_stats
        stats["calls"] += 1
        if (not form_methods_supported()
                or form_fields_signature(ContactsForm.base_fields) is None):
            stats["fallbacks"] += 1
            form = ContactsForm(data, instance=revision)
            try:
                return form.is_valid()
            finally:
                form._bound_fields_cache.clear()
        prototype = self._validation_prototype(ContactsForm, data, revision)
        key = contact_success_key(prototype, data, revision, get_language())
        if key is None:
            stats["fallbacks"] += 1
            return self._bound_validation(ContactsForm, data, revision, native_fields=True)
        if key in self._contact_successes:
            stats["hits"] += 1
            for name, value in zip(MODEL_NAMES, self._contact_successes[key], strict=True):
                setattr(revision, name, value)
            return True
        stats["misses"] += 1
        valid = self._bound_validation(ContactsForm, data, revision)
        if valid:
            self._contact_successes[key] = tuple(getattr(revision, name) for name in MODEL_NAMES)
        return valid

    def rate_valid(self, rate):
        # The existing rate constraint/form depends only on these primitive values.
        values = tuple(getattr(rate, name) for name in RateForm.Meta.fields)
        if values not in self.rate_checks:
            self.rate_checks[values] = RateForm(
                dict(zip(RateForm.Meta.fields, values, strict=True)), instance=rate
            ).is_valid()
        return self.rate_checks[values]
