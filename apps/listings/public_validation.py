"""Current-request validation; no cross-request publication data/result cache."""

from contextlib import contextmanager
from copy import copy

from django import forms
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.backends.postgresql.base import ServerBindingCursor
from django.db.models import Case, CharField, Exists, OuterRef, Prefetch, Q, Subquery, Value, When
from django.db.models.functions import Cast
from django.forms.models import model_to_dict
from django.utils.translation import get_language
from psycopg import ClientCursor

from apps.catalog.models import Municipality
from apps.core.models import LegalAcceptance, RepresentationAction, VerificationCheck
from apps.mediafiles.models import Blob, Match, Photo
from apps.safety.models import PrivacyPublicationHold, Restriction, RightsPhotoReintroduction

from .forms import ContactsForm, DetailsForm, RateForm
from .history import ordinary_matches, rectification_history_ids
from .models import Revision
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


def publication_query(query, document):
    """Shared fresh authority/history annotations for both read representations."""
    grant = RepresentationAction.objects.filter(
        person_id=OuterRef("person_id"),
        subject_id=OuterRef("person__subject_id"),
        manager_version=OuterRef("person__manager_version"),
        action="grant",
        document__slug="publishing",
        document__version=document.version if document else "",
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
    return query.annotate(
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
    )


class _PageReadCursor(ServerBindingCursor):
    """Keep oversized SELECTs compatible even before domain validation.

    A selected page bounds listing IDs, but corrupt/excess child rows are
    rejected only after prefetch. Driver interpolation avoids the extended
    protocol's parameter ceiling without truncating data or skipping checks.
    """

    def execute(self, query, params=None, *, prepare=None, binary=None):
        # Atomic scopes issue uniquely named SAVEPOINT/RELEASE commands while
        # this cursor is active. They cannot be reused and must not evict reads
        # from the bounded prepared-statement cache. Unknown SQL objects also
        # keep native execution without preparation.
        is_select = (
            isinstance(query, str) and query.lstrip().upper().startswith("SELECT")
        ) or (
            isinstance(query, bytes) and query.lstrip().upper().startswith(b"SELECT")
        )
        if not is_select:
            prepare = False
        if params is not None and len(params) > 65535:
            with ClientCursor(self.connection) as native:
                query = native.mogrify(query, params)
            params, prepare = None, False
        return super().execute(query, params, prepare=prepare, binary=binary)


@contextmanager
def _prepared_page_binding(*, enabled):
    """Prepare explicit public-read SELECTs on this thread's physical connection.

    PostgreSQL caches query plans, never publication results. Each execution
    reads its current transaction snapshot. Restore cursor/threshold on every
    exit. Callers already connected and scope only the selected page or public
    detail guard; other reads, writes and schema keep their native binding.
    """
    if not enabled:
        yield
        return
    connection.validate_thread_sharing()
    raw = connection.connection  # The enclosing atomic block has connected.
    previous_factory, previous_threshold = raw.cursor_factory, raw.prepare_threshold
    try:
        raw.cursor_factory = _PageReadCursor
        if previous_threshold is None:
            # Avoid a second warmup before PostgreSQL starts its own auto-plan
            # selection. The driver cache remains bounded; no results are cached.
            raw.prepare_threshold = 0
        yield
    finally:
        raw.cursor_factory = previous_factory
        raw.prepare_threshold = previous_threshold


def read_publication_values(query, *, bounded_joins=False, prepared_page=False):
    """Materialize the captured scalar SELECT with a request-scoped JIT policy.

    Only the explicitly selected read uses jit=off; page hydration also bounds
    explicit join planning. Its SQL/parameters and READ COMMITTED statement
    semantics stay native. Page reads use scoped server binding/preparation;
    cursor configuration and planner settings are restored afterwards.
    Restore explicitly on success for an enclosing transaction. Atomic rollback
    restores the local setting/savepoint on errors, without querying a broken
    transaction. Callers perform authority checks/hydration outside this scope.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            if bounded_joins:
                cursor.execute("SELECT current_setting('jit'), current_setting('join_collapse_limit')")
                previous, previous_joins = cursor.fetchone()
                cursor.execute("SELECT set_config('jit', 'off', true), set_config('join_collapse_limit', '1', true)")
            else:
                cursor.execute("SHOW jit")
                previous = cursor.fetchone()[0]
                cursor.execute("SET LOCAL jit=off")
        with _prepared_page_binding(enabled=bounded_joins and prepared_page):
            rows = list(query)
        with connection.cursor() as cursor:
            if bounded_joins:
                cursor.execute("SELECT set_config('jit', %s, true), set_config('join_collapse_limit', %s, true)",
                               [previous, previous_joins])
            else:
                cursor.execute("SELECT set_config('jit', %s, true)", [previous])
        return rows



def memoize_publication_field_clean(field, stats):
    # Field.clean receives only value; instance/cross-field/model/authority
    # checks are outside it and still run for every fresh binding. Audited
    # field definitions/catalog/language are fixed in this prototype only.
    original = field.clean
    memo = {}

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

    field.clean = clean


def validate_publication_input_fields(form):
    """Audited Field._clean_bound_field scalar path without rendering BoundFields.

    Native widget extraction, prefix, Field.clean, clean_<name> and immediate
    add_error order remain unchanged. Disabled/custom bound fields stay native.
    """
    for name, field in form.fields.items():
        try:
            value = form._widget_data_value(field.widget, form.add_prefix(name))
            form.cleaned_data[name] = field.clean(value)
            cleaner = getattr(form, "clean_" + name, None)
            if cleaner is not None:
                form.cleaned_data[name] = cleaner()
        except ValidationError as error:
            form.add_error(name, error)


def validate_publication_value_fields(form):
    """Model field validation for the audited read-only Revision proof domain.

    Caller requires the unchanged rules fingerprint: Revision has default
    Model.clean, no constraints and no unique checks apart from excluded PK.
    SnapshotDetails already validates geo choices against its fresh catalog.
    Complete input keys prevent construct_instance's omitted-default branch.
    Writing, Rate and unaudited rules retain native model construction/clean.
    """
    excluded_geo = {"municipality", "postal_code", "zone"} if isinstance(form, SnapshotDetails) else set()
    errors = {}
    for field in Revision._meta.fields:
        name = field.name
        if (name not in form.fields or name in excluded_geo
                or (form._meta.fields and name not in form._meta.fields)
                or (form._meta.exclude and name in form._meta.exclude)
                or name in form._errors or field.generated):
            continue
        value = form.cleaned_data.get(name)
        form_field = form.fields[name]
        if not field.blank and not form_field.required and value in form_field.empty_values:
            continue
        if field.blank and value in field.empty_values:
            continue
        try:
            # Audited scalar model field implementations don't inspect instance.
            field.clean(value, None)
        except ValidationError as error:
            errors[name] = error.error_list
    if errors:
        form._update_errors(ValidationError(errors))


def validate_publication_binding(prototype, data, revision, *, value_model=False):
    """Run the native form/model rules on an independent validation-only binding.

    Default callers run the full native model path. Projection may opt into
    the separately audited scalar model field kernel. The caller owns audited form
    definitions, a request-local current catalog/language and all eligibility
    dependencies. Every call runs native full_clean; errors/results/BoundFields
    remain on the new binding. Editing/rendered forms keep normal construction.
    """
    form = copy(prototype)
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
    if needs_initial and isinstance(form, SnapshotDetails) and revision.municipality_id:
        city = revision.municipality
        form.initial.setdefault("province", city.province_id)
        form.initial.setdefault("region", city.province.region_id)
    form.fields = dict(form.fields)
    form._errors = None
    form._bound_fields_cache = {}
    form._validate_unique = False
    form.__dict__.pop("changed_data", None)
    form.__dict__.pop("cleaned_data", None)
    uses_value_kernel = False
    if value_model:
        if type(form) not in (SnapshotDetails, ContactsForm):
            raise ValueError("Value model kernel only supports audited Revision forms")
        # Unknown/omitted defaults, disabled and empty-permitted bindings use
        # the original model path. Normal projection provides every field key.
        complete = all(name in data for name in form.fields)
        normal_bound_fields = (
            form.bound_field_class in (None, forms.BoundField)
            and all(field.bound_field_class in (None, forms.BoundField)
                    for field in form.fields.values())
        )
        if not normal_bound_fields:
            return False  # Unknown binding semantics require the native eligibility guard.
        if complete and not needs_initial:
            uses_value_kernel = True
            form._clean_fields = lambda: validate_publication_input_fields(form)
            form._post_clean = lambda: validate_publication_value_fields(form)
    try:
        return form.is_valid()
    finally:
        # A BoundField points back to its form. These private bindings return
        # only a boolean and are never rendered; release their reverse cache
        # after native cleaning instead of leaving successful cycles for GC.
        form._bound_fields_cache.clear()
        if uses_value_kernel:
            # Private callbacks capture the binding; release their reverse refs
            # on success and exceptions, not only when cyclic GC eventually runs.
            form.__dict__.pop("_clean_fields", None)
            form.__dict__.pop("_post_clean", None)


class PublicationContext:
    def __init__(self, query, *, page_read=False, prepared_page=False):
        self.document = current_publishing_document()
        self.rate_checks = {}
        self._validation_prototypes = {}
        self.field_clean_cache_stats = {}
        query = publication_query(query, self.document).select_related(None).select_related(
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
        # Page hydration can trigger JIT for its correlated annotations even
        # with only 24 actual rows. Reuse the restoring local policy there;
        # ordinary native population reads retain their existing configuration.
        self.rows = (
            read_publication_values(query, bounded_joins=True, prepared_page=prepared_page)
            if page_read else list(query)
        )
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

    def _bound_validation(self, form_class, data, revision):
        """Share definitions and successful scalar field cleaning within a request.

        Key: form class, request-owned catalog identity, active language. The
        source-defined fields/options and restricted catalog belong to this
        context only. These two forms do not mutate field configuration while
        cleaning. Memo keys include the prototype's actual field configuration,
        validators, fresh catalog, language and exact typed input. Mutable result
        containers are copied; all form/model validation runs on a fresh binding.
        No representation, document, revocation or eligibility result is reused.
        """
        if form_class not in (SnapshotDetails, ContactsForm):
            raise ValueError("Only the audited stateless publication forms can share definitions")
        self.row(revision)
        key = (form_class, id(self.catalog), get_language())
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
        return validate_publication_binding(self._validation_prototypes[key], data, revision)

    def _memoize_field_clean(self, name, field):
        stats = self.field_clean_cache_stats.setdefault(
            name, {"calls": 0, "hits": 0, "misses": 0}
        )
        memoize_publication_field_clean(field, stats)

    def details_valid(self, data, revision):
        return self._bound_validation(SnapshotDetails, data, revision)

    def contacts_valid(self, data, revision):
        return self._bound_validation(ContactsForm, data, revision)

    def rate_valid(self, rate):
        # The existing rate constraint/form depends only on these primitive values.
        values = tuple(getattr(rate, name) for name in RateForm.Meta.fields)
        if values not in self.rate_checks:
            self.rate_checks[values] = RateForm(
                dict(zip(RateForm.Meta.fields, values, strict=True)), instance=rate
            ).is_valid()
        return self.rate_checks[values]
