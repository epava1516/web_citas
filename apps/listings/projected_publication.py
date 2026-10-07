"""Current-request value projection; unknown proofs retain the native guard.

Nothing is persisted. Authority predicates are checked per candidate. Native
content validation may be shared only for equal complete content inputs under
the explicitly audited definitions; titles retain their independent rules.
"""

import hashlib
import inspect
import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from types import CodeType
from uuid import UUID

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import connection
from django.db.migrations.serializer import serializer_factory
from django.db.models import prefetch_related_objects
from django.forms import models as model_forms
from django.utils import timezone
from django.utils.translation import get_language

from apps.catalog.promotion_exposure import enabled as promotions_enabled
from apps.core import verification_services
from apps.core.models import LegalAcceptance
from apps.mediafiles.models import Photo

from . import forms as listing_forms
from . import history, moderation, public_validation, submissions
from .forms import ContactsForm, DetailsForm, RateForm
from .models import Rate, Revision
from .public_validation import (
    PublicationContext,
    SnapshotChoice,
    SnapshotDetails,
    SnapshotMultipleChoice,
    publication_query,
)
from .uuid_batches import CapturedUUIDBatch


def code_signature(code):
    """Executed bytecode/constants, without deployment path or source line numbers.

    Source lookup and inspect.unwrap can hide replacement runtime implementations.
    Every wrapper layer remains in the signature, including functools.wraps layers.
    Profiling therefore observes calls without changing the callable chain.
    This is a reviewed change detector, not a sandbox for arbitrary Python code.
    """
    def constant(value):
        if isinstance(value, CodeType):
            return code_signature(value)
        if isinstance(value, frozenset):
            return ("frozenset", sorted((constant(item) for item in value), key=repr))
        if isinstance(value, tuple):
            return ("tuple", [constant(item) for item in value])
        return (type(value).__name__, repr(value))
    return (code.co_code.hex(), [constant(value) for value in code.co_consts],
            code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
            code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount,
            code.co_flags, code.co_exceptiontable.hex())


def definitions():
    """Serializable audited code/metadata, independent of DB values and locale.

    Actual callable layers are fingerprinted; wraps is not evidence of transparency. A new
    validator, widget/configuration, constraint or instance rule is unsupported.
    The expected digest is reviewed source data, not learnt from a new request.
    """
    classes = [DetailsForm, ContactsForm, RateForm, PublicationContext, SnapshotDetails, SnapshotChoice,
               SnapshotMultipleChoice, Revision, Rate, forms.Field, forms.CharField,
               forms.BooleanField, forms.ChoiceField, forms.MultipleChoiceField,
               forms.ModelChoiceField, forms.ModelMultipleChoiceField, forms.ModelForm,
               forms.TextInput, forms.Select, forms.CheckboxInput, forms.SelectMultiple]
    functions = [listing_forms.validate_listing_text, listing_forms.normalize_telegram,
                 submissions.validate_submission, moderation.validate_submission,
                 moderation.publicly_visible, verification_services.publication_ready,
                 submissions.publication_ready, submissions.current_publishing_document,
                 publication_query, public_validation.publication_query,
                 history.ordinary_matches, history.rectification_history_ids,
                 model_forms.construct_instance, model_forms.model_to_dict]
    for cls in classes:
        names = {"__init__", "clean", "full_clean", "clean_fields", "validate_unique",
                 "validate_constraints", "_get_unique_checks", "_perform_unique_checks",
                 "_perform_date_checks", "is_valid", "_clean_fields", "_clean_form",
                 "_post_clean", "_get_validation_exclusions", "_bound_items",
                 "__getitem__", "_clean_bound_field", "to_python", "validate",
                 "run_validators", "postal_matches", "_check_values", "value_from_datadict",
                 "details", "details_valid", "contacts_valid", "rate_valid", "row",
                 "_bound_validation", "_memoize_field_clean", "fields_for_catalog"}
        names.update(name for name in dir(cls) if name.startswith("clean_"))
        functions.extend(getattr(cls, name) for name in sorted(names)
                         if callable(getattr(cls, name, None)))
    for model in [Revision, Rate]:
        for field in model._meta.concrete_fields:
            functions.extend(getattr(field, name) for name in
                             ["clean", "validate", "to_python", "run_validators"])
            functions.extend(validator if inspect.isfunction(validator) else validator.__call__
                             for validator in field.validators)
    for cls in [DetailsForm, ContactsForm, RateForm]:
        for field in cls.base_fields.values():
            functions.extend(validator if inspect.isfunction(validator) else validator.__call__
                             for validator in field.validators)
    code = []
    for function in functions:
        layers = []
        seen = set()
        while True:
            function = getattr(function, "__func__", function)
            if id(function) in seen:
                raise ValueError("Cyclic callable wrapper")
            seen.add(id(function))
            layers.append(code_signature(function.__code__))
            if not hasattr(function, "__wrapped__"):
                break
            function = function.__wrapped__
        code.append(layers)
    field_options = []
    for cls in [DetailsForm, ContactsForm, RateForm]:
        field_options.append((cls.__name__, cls._meta.model._meta.label,
                              tuple(cls._meta.fields), cls._meta.exclude))
        for name, field in cls.base_fields.items():
            attrs = {key: value for key, value in vars(field).items()
                     if key not in {"label", "help_text", "error_messages", "widget",
                                    "creation_counter", "_choices", "_queryset"}}
            # Query predicates, not cached evaluation of the restricted queryset.
            if hasattr(field, "queryset"):
                attrs["queryset"] = field.queryset.query.sql_with_params()
            if hasattr(field, "choices") and not hasattr(field, "queryset"):
                attrs["choices"] = list(field.choices)
            attrs["widget"] = (type(field.widget).__module__, type(field.widget).__qualname__,
                               field.widget.attrs, getattr(field.widget, "allow_multiple_selected", None))
            # Migration serialization gives stable defaults, validators and types.
            field_options.append((cls.__name__, name, type(field).__module__,
                                  type(field).__qualname__, serializer_factory(attrs).serialize()[0]))
    models = []
    for model in [Revision, Rate]:
        models.append((model.__name__, [field.deconstruct() for field in model._meta.fields],
                       [field.deconstruct() for field in model._meta.many_to_many],
                       model._meta.unique_together,
                       [item.deconstruct() for item in model._meta.constraints]))
    return code, field_options, serializer_factory(models).serialize()[0]


# Updated only with a reviewed native rule/metadata change and equivalence gates.
EXPECTED_DEFINITIONS = "c77c9c8597f0b429d2f1cf7f1ce0e4b4fd522737243d8dd4e7d744c8d9ea41bd"


def definitions_digest():
    return hashlib.sha256(json.dumps(definitions(), sort_keys=True, default=str).encode()).hexdigest()


def supported(*, checked=False):
    if connection.vendor != "postgresql" or settings.PRODUCTION or checked or promotions_enabled():
        return False
    try:
        return definitions_digest() == EXPECTED_DEFINITIONS
    except (TypeError, ValueError, AttributeError, OSError):
        return False


def freeze(value):
    """Exact typed inputs; unsupported containers request native fallback."""
    if value is None or type(value) in (str, bool, int, float, Decimal, UUID, date, datetime):
        return (type(value), value)
    if type(value) in (list, tuple):
        return (type(value), tuple(freeze(item) for item in value))
    raise TypeError("Unknown publication input")


class ProjectedPublication:
    def __init__(self, query):
        self.document = submissions.current_publishing_document()
        scalar_fields = [field for field in Revision._meta.concrete_fields]
        columns = ["pk", "status", "person_id", "expires_at", "approved_revision_id"]
        columns += ["approved_revision__" + field.attname for field in scalar_fields]
        columns += ["person__" + field.attname for field in
                    query.model._meta.get_field("person").related_model._meta.concrete_fields]
        columns += ["person__phone_claim__" + name for name in
                    ["phone", "verified_at", "individual_id", "agency_id"]]
        columns += ["person__agency__verification_status"]
        columns += ["_pv_" + name for name in ["history", "rectification_upload", "reintroduction",
                    "hold", "restriction", "grant", "conflict", "check_status",
                    "check_manager", "check_subject"]]
        self.rows = list(publication_query(query, self.document).values(*columns))
        self.by_id = {row["pk"]: row for row in self.rows}
        revision_ids = [row["approved_revision_id"] for row in self.rows]
        revision_batch = CapturedUUIDBatch(revision_ids, mode="array")
        self.memberships = {name: defaultdict(list) for name in
                            ["categories", "services", "travel_areas", "rates", "photos"]}
        for name in ["categories", "services", "travel_areas"]:
            field = Revision._meta.get_field(name)
            through = field.remote_field.through
            pairs = revision_batch.filter(through.objects.all(), "revision_id").values_list(
                "revision_id", field.m2m_reverse_field_name() + "_id"
            )
            for revision_id, target_id in pairs:
                self.memberships[name][revision_id].append(target_id)
        for values in revision_batch.filter(Rate.objects.all(), "revision_id").values_list(
            "revision_id", *RateForm.Meta.fields
        ):
            self.memberships["rates"][values[0]].append(values[1:])
        for revision_id, ready, complete in revision_batch.filter(Photo.objects.filter(
            removed_at__isnull=True
        ), "revision_id").values_list("revision_id", "blob__status", "comparison_complete"):
            self.memberships["photos"][revision_id].append((ready, complete))
        self.acceptances = {
            obj.pk: obj for obj in LegalAcceptance.objects.filter(
                pk__in={row["approved_revision__publisher_acceptance_id"] for row in self.rows}
            ).select_related("document")
        }
        self.catalog = {}
        for name in ["categories", "services", "travel_areas", "municipality",
                     "province", "region", "postal_code", "zone"]:
            if name in self.memberships:
                identifiers = {value for values in self.memberships[name].values() for value in values}
            elif name in ["region", "province"]:
                # Filled below from the current municipality hierarchy.
                continue
            else:
                identifiers = {row["approved_revision__" + name + "_id"] for row in self.rows}
            items = DetailsForm.base_fields[name].queryset.filter(pk__in=identifiers)
            if name == "municipality":
                items = items.select_related("province__region")
            self.catalog[name] = {str(obj.pk): obj for obj in items}
        for name, identifiers in [
            ("province", {city.province_id for city in self.catalog["municipality"].values()}),
            ("region", {city.province.region_id for city in self.catalog["municipality"].values()}),
        ]:
            self.catalog[name] = {str(obj.pk): obj for obj in
                                  DetailsForm.base_fields[name].queryset.filter(pk__in=identifiers)}
        postals = list(self.catalog["postal_code"].values())
        prefetch_related_objects(postals, "municipalities")
        for postal in postals:
            postal._publication_cities = {city.pk for city in postal.municipalities.all()}
        self.prepared_fields = SnapshotDetails.fields_for_catalog(self.catalog)
        self.title_field = DetailsForm().fields["title"]
        self.memo = {name: {} for name in ["details", "contacts", "rates"]}
        self.stats = {"candidates": len(self.rows), "positive": 0, "native_fallback": 0,
                      "details_native": 0, "contacts_native": 0, "rates_native": 0}

    def authority(self, row):
        """Per-row fresh inputs, never a memoized authority result."""
        def person(name):
            return row["person__" + name]

        def revision(name):
            return row["approved_revision__" + name]
        if (row["status"] != "published" or revision("status") != "approved"
                or revision("listing_id") != row["pk"] or not row["expires_at"]
                or row["expires_at"] <= timezone.now()):
            return False
        if any(row["_pv_" + name] for name in
               ["history", "rectification_upload", "reintroduction", "hold", "restriction", "conflict"]):
            return False
        if (person("publication_erased_at") or person("consent_revoked_at")
                or not person("subject_id") or person("age_status") != "passed"
                or person("manager_review_status") != "approved"
                or person("consent_version") != person("manager_version")
                or revision("manager_version") != person("manager_version")):
            return False
        if (not person("phone_claim_id") or not row["person__phone_claim__verified_at"]
                or row["person__phone_claim__individual_id"] != person("individual_id")
                or row["person__phone_claim__agency_id"] != person("agency_id")
                or revision("phone") != row["person__phone_claim__phone"]):
            return False
        if person("agency_id") and row["person__agency__verification_status"] != "passed":
            return False
        document = self.document
        acceptance = self.acceptances.get(revision("publisher_acceptance_id"))
        if (not document or not acceptance or not acceptance.document.active
                or acceptance.document.slug != "publishing"
                or acceptance.document.version != document.version
                or acceptance.action != "publish" or acceptance.agency_id != person("agency_id")
                or not row["_pv_grant"] or row["_pv_check_status"] != "passed"
                or row["_pv_check_manager"] != person("manager_version")
                or row["_pv_check_subject"] != person("subject_id")):
            return False
        return True

    def native_content(self, kind, data, instance, factory):
        key = (get_language(), id(self.catalog), freeze(data))
        if key not in self.memo[kind]:
            self.stats[kind + "_native"] += 1
            # A full native clean (including model checks) for this input class.
            if not factory(data, instance).is_valid():
                return False  # Errors are never reused; native fallback owns them.
            self.memo[kind][key] = True
        return True

    def positive(self, row):
        """Sufficient proof only; False means native fallback, never hidden."""
        if not self.authority(row):
            return False
        revision_id = row["approved_revision_id"]
        city = self.catalog["municipality"].get(str(row["approved_revision__municipality_id"]))
        if city is None:
            return False
        values = {field.attname: row["approved_revision__" + field.attname]
                  for field in Revision._meta.concrete_fields}
        # No database identity in the audited, instance-independent content rules.
        values["id"] = None
        instance = Revision(**values)
        instance.municipality = city
        data = {name: values[name] for name in DetailsForm.Meta.fields
                if not Revision._meta.get_field(name).many_to_many
                and name not in {"municipality", "postal_code", "zone"}}
        for name in ["categories", "services", "travel_areas"]:
            data[name] = self.memberships[name][revision_id]
        data.update(region=city.province.region_id, province=city.province_id,
                    municipality=city.pk, postal_code=values["postal_code_id"] or "",
                    zone=values["zone_id"] or "")
        try:
            # Only title-dependent native rules are independent in audited clean.
            title = self.title_field.clean(data["title"])
            listing_forms.validate_listing_text(title)
            Revision._meta.get_field("title").clean(title, instance)
            data["title"] = "Projected validation title"
            if not self.native_content("details", tuple(data.items()), instance,
                                       lambda pairs, obj: SnapshotDetails(
                                           self.catalog, dict(pairs), instance=obj,
                                           prepared_fields=self.prepared_fields)):
                return False
            contacts = {"whatsapp": values["whatsapp"], "telegram": values["telegram"],
                        "contact_exposure_accepted": values["contact_exposure_accepted"],
                        "accept_publishing": True, "legal_version": self.document.version}
            if not self.native_content("contacts", tuple(contacts.items()), instance,
                                       lambda pairs, obj: ContactsForm(dict(pairs), instance=obj)):
                return False
            rates = self.memberships["rates"][revision_id]
            if len(rates) > 10:
                return False
            for rate in rates:
                if not self.native_content("rates", rate, Rate(**dict(zip(RateForm.Meta.fields, rate,
                                                                         strict=True))),
                                           lambda inputs, obj: RateForm(
                                               dict(zip(RateForm.Meta.fields, inputs, strict=True)),
                                               instance=obj)):
                    return False
            photos = self.memberships["photos"][revision_id]
            return 1 <= len(photos) <= 8 and all(status == "ready" and complete
                                                for status, complete in photos)
        except (ValidationError, TypeError):
            return False

    def visible_ids(self, query):
        if len({row["approved_revision_id"] for row in self.rows}) != len(self.rows):
            # A cross-listing approved pointer can collide in the native
            # context's by_revision map. Preserve native validation/errors for
            # that inconsistent population; a partial proof must not hide them.
            self.stats["native_fallback"] = len(self.rows)
            native = PublicationContext(query)
            return [row.pk for row in native.rows if moderation.publicly_visible(row, context=native)]
        positive = set()
        unknown = []
        for row in self.rows:
            if self.positive(row):
                positive.add(row["pk"])
                self.stats["positive"] += 1
            else:
                unknown.append(row["pk"])
        self.stats["native_fallback"] = len(unknown)
        if unknown:
            native = PublicationContext(query.filter(pk__in=unknown))
            positive.update(row.pk for row in native.rows if moderation.publicly_visible(row, context=native))
        return [row["pk"] for row in self.rows if row["pk"] in positive]


def projected_page(query, number, *, checked=False, observation=None):
    """None asks the caller for the complete native path, including ranking."""
    if observation is not None:
        observation.update(route="fallback", reason="unsupported_definitions_or_mode")
    if not supported(checked=checked):
        return None
    projection = ProjectedPublication(query)
    ids = projection.visible_ids(query)
    if observation is not None:
        observation.update(candidate_stats=dict(projection.stats))
    if not supported(checked=checked):
        if observation is not None:
            observation["reason"] = "definitions_changed_during_request"
        return None  # A rule/configuration changed during this request.
    page = Paginator(ids, 24).page(number)
    selected = list(page.object_list)
    native = PublicationContext(query.filter(pk__in=selected))
    rows = {row.pk: row for row in native.rows}
    for listing_id in selected:
        row = rows.get(listing_id)
        if (row is None or row.approved_revision_id != projection.by_id[listing_id]["approved_revision_id"]
                or not moderation.publicly_visible(row, context=native)):
            # Confirmed change between projection and hydration: recompute native
            # population/count/order, rather than expose a stale/substituted row.
            if observation is not None:
                observation["reason"] = "native_page_guard_changed"
            return None
    if observation is not None:
        observation.update(route="projection", reason="audited_current_values",
                           hydrated_count=len(selected))
    page.object_list = [rows[listing_id] for listing_id in selected]
    return page
