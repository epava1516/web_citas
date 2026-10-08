"""Conservative, current-statement positive proof for audited publication rules.

False is UNKNOWN, never a rejection. The caller evaluates unknown candidates
with the native guard before counting/paginating. Unsupported rule definitions
disable this path entirely. No result or authority is retained across requests.
"""

import json
from uuid import UUID

from django.core.exceptions import EmptyResultSet, ValidationError
from django.core.paginator import Page, Paginator
from django.db import connection
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Func,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
    Window,
)
from django.db.models.functions import Cast, RowNumber
from django.utils import timezone

from apps.catalog.models import PostalCode
from apps.core.models import LegalAcceptance, RepresentationAction, VerificationCheck
from apps.mediafiles.models import Match, Photo
from apps.safety.models import PrivacyPublicationHold, Restriction, RightsPhotoReintroduction

from . import moderation, submissions
from .forms import ContactsForm, DetailsForm
from .history import ordinary_matches, rectification_history_ids
from .models import Rate, Revision
from .public_validation import PublicationContext, publication_query, read_publication_values
from .text_proof import PlainTextProofV1 as PlainTextProof
from .text_proof import rate_text_unknown, revision_text_unknown


class SameNullable(Func):
    """Native Python equality for nullable foreign keys (NULL equals NULL)."""
    output_field = BooleanField()

    def as_sql(self, compiler, connection, **extra_context):
        left, lp = compiler.compile(self.source_expressions[0])
        right, rp = compiler.compile(self.source_expressions[1])
        return f"({left} IS NOT DISTINCT FROM {right})", [*lp, *rp]


class RowMembership(Func):
    """Tuple membership in a current uncorrelated relation, with bound values."""
    output_field = BooleanField()

    def as_sql(self, compiler, connection, **extra_context):
        columns, params = [], []
        for expression in self.source_expressions[:-1]:
            sql, values = compiler.compile(expression)
            columns.append(sql)
            params.extend(values)
        query, values = compiler.compile(self.source_expressions[-1])
        return f"(({', '.join(columns)}) IN {query})", [*params, *values]


class JSONChoicesProof(Func):
    """Only arrays of exact JSON strings from current audited choices.

    The CASE guards the set-returning function for every evaluation order.
    Containment alone is insufficient for checking nested shapes and types.
    """
    output_field = BooleanField()

    def __init__(self, expression, choices, *, json_path=True):
        self.json_path = json_path
        super().__init__(expression, *(Value(value) for value in choices))

    def as_sql(self, compiler, connection, **extra_context):
        value, vp = compiler.compile(self.source_expressions[0])
        if self.json_path:
            # Containment checks values but may accept nested containers. Strict
            # JSONPath checks each immediate element's type without lax unwrap.
            # Guard its input independently of boolean evaluation order.
            choices = [option.value for option in self.source_expressions[1:]]
            return (
                f"(jsonb_typeof({value}) = 'array' AND {value} <@ %s::jsonb "
                f"AND NOT jsonb_path_exists(CASE WHEN jsonb_typeof({value}) = 'array' "
                f"THEN {value} ELSE '[]'::jsonb END, %s::jsonpath))",
                [*vp, *vp, json.dumps(choices), *vp, *vp,
                 'strict $[*] ? (@.type() != "string")'],
            )
        options, params = [], []
        for expression in self.source_expressions[1:]:
            option, op = compiler.compile(expression)
            options.append(f"to_jsonb({option}::text)")
            params.extend(op)
        predicate = f"item NOT IN ({', '.join(options)})" if options else "TRUE"
        return (
            f"(jsonb_typeof({value}) = 'array' AND NOT EXISTS ("
            f"SELECT 1 FROM jsonb_array_elements(CASE WHEN jsonb_typeof({value}) = 'array' "
            f"THEN {value} ELSE '[]'::jsonb END) AS items(item) WHERE {predicate}))",
            [*vp, *vp, *vp, *params],
        )


class TelegramProof(Func):
    output_field = BooleanField()

    def as_sql(self, compiler, connection, **extra_context):
        value, vp = compiler.compile(self.source_expressions[0])
        return (
            f"({value} = '' OR (char_length({value}) BETWEEN 5 AND 32 "
            f"AND ({value} COLLATE \"C\") ~ %s AND ({value} COLLATE \"C\") !~ %s))",
            [*vp, *vp, *vp, "^[A-Za-z]", *vp, "[^A-Za-z0-9_]"],
        )


def authority_proof(document, *, bulk=False):
    """Fresh authority dependencies; failures remain native unknowns."""
    proof = Q(
        status="published", approved_revision__status="approved",
        approved_revision__listing_id=F("pk"), expires_at__gt=timezone.now(),
        person__publication_erased_at__isnull=True, person__consent_revoked_at__isnull=True,
        person__subject_id__isnull=False, person__age_status="passed",
        person__manager_review_status="approved", person__consent_version=F("person__manager_version"),
        approved_revision__manager_version=F("person__manager_version"),
        person__phone_claim__verified_at__isnull=False,
        approved_revision__phone=F("person__phone_claim__phone"),
    )
    if bulk:
        proof &= bulk_authority_membership(document)
    else:
        proof &= Q(_pv_grant=True, _pv_check_status="passed",
                   _pv_check_manager=F("person__manager_version"), _pv_check_subject=F("person__subject_id"))
        for name in ["history", "rectification_upload", "reintroduction", "hold", "restriction", "conflict"]:
            proof &= Q(**{"_pv_" + name: False})
    proof &= Q(SameNullable(F("person__phone_claim__individual_id"), F("person__individual_id")))
    proof &= Q(SameNullable(F("person__phone_claim__agency_id"), F("person__agency_id")))
    proof &= Q(person__agency_id__isnull=True) | Q(person__agency__verification_status="passed")
    if bulk:
        prefix = "approved_revision__publisher_acceptance__"
        proof &= Q(**{prefix + "document__active": True, prefix + "document__slug": "publishing",
                      prefix + "document__version": document.version, prefix + "action": "publish"})
        return proof & Q(SameNullable(F(prefix + "agency_id"), F("person__agency_id")))
    acceptance = LegalAcceptance.objects.filter(
        pk=OuterRef("approved_revision__publisher_acceptance_id"), document__active=True,
        document__slug="publishing", document__version=document.version, action="publish",
    ).filter(SameNullable(F("agency_id"), OuterRef("person__agency_id")))
    return proof & Q(Exists(acceptance))


def bulk_authority_membership(document):
    """Same dependencies as the native annotations, grouped inside one SELECT.

    No request/external memo. Ambiguous latest timestamps remain unknown so a
    different access plan cannot choose another native tie winner for us.
    """
    proof = ~Q(approved_revision_id__in=rectification_history_ids())
    proof &= ~Q(approved_revision_id__in=Photo.objects.filter(
        rectification_upload__isnull=False).values("revision_id"))
    proof &= ~Q(approved_revision_id__in=RightsPhotoReintroduction.objects.values("photo__revision_id"))
    proof &= ~Q(person_id__in=PrivacyPublicationHold.objects.filter(active=True).values("person_id"))
    proof &= ~Q(pk__in=Restriction.objects.filter(active=True).values("listing_id"))
    conflict = ordinary_matches(Match.objects.filter(
        Q(resolved_at__isnull=True) | Q(decision="conflict"),
        photo__removed_at__isnull=True, candidate__removed_at__isnull=True, decision="conflict",
    ))
    proof &= ~Q(approved_revision_id__in=conflict.values("photo__revision_id"))
    proof &= ~Q(approved_revision_id__in=conflict.values("candidate__revision_id"))
    grants = RepresentationAction.objects.filter(
        action="grant", document__slug="publishing", document__version=document.version,
    ).values("person_id", "subject_id", "manager_version", "manager_kind", "manager_id")
    kind = Case(When(person__agency_id__isnull=False, then=Value("agency")), default=Value("individual"))
    manager = Case(When(person__agency_id__isnull=False, then=Cast(F("person__agency_id"), CharField())),
                   default=Cast(F("person__individual_id"), CharField()))
    proof &= Q(RowMembership(F("person_id"), F("person__subject_id"), F("person__manager_version"),
                             kind, manager, Subquery(grants)))
    checks = VerificationCheck.objects.annotate(
        _position=Window(RowNumber(), partition_by=[F("person_id")], order_by=F("created_at").desc()),
        _ties=Window(Count("pk"), partition_by=[F("person_id"), F("created_at")]),
    ).filter(_position=1, _ties=1)
    # Keep status in the tuple. Filtering it before the window would select the
    # latest PASSED check rather than checking the actual latest check.
    proof &= Q(RowMembership(F("person_id"), F("person__subject_id"), F("person__manager_version"),
                             Value("passed"), Subquery(checks.values(
                                 "person_id", "subject_id", "manager_version", "status"))))
    return proof


def content_proof(*, bulk=False, json_path=True, legacy_text=True, text_membership=True):
    """Sufficient scalar/catalog/relationship proof under unchanged definitions."""
    prefix = "approved_revision__"
    proof = Q()
    if text_membership and legacy_text:
        unknown_text = Revision.objects.filter(revision_text_unknown()).values("pk")
        proof &= ~Q(approved_revision_id__in=unknown_text)
    else:
        for name, maximum, required in [("title", 120, True), ("description", 6000, True),
                                         ("description_alternative", 6000, False)]:
            proof &= Q(PlainTextProof(F(prefix + name), maximum, required, legacy=legacy_text))
    for name in ["content_language", "profile_type", "time_slot"]:
        proof &= Q(**{prefix + name + "__in": [key for key, _ in DetailsForm.base_fields[name].choices]})
    for name in ["spoken_languages", "days"]:
        proof &= Q(JSONChoicesProof(F(prefix + name), [key for key, _ in DetailsForm.base_fields[name].choices], json_path=json_path))
    # Raw canonical Telegram is a sufficient subset; stripping @/whitespace or
    # other inputs continues through the native path and native normalization.
    proof &= Q(approved_revision__contact_exposure_accepted=True)
    proof &= Q(TelegramProof(F(prefix + "telegram")))
    for name in ["municipality", "postal_code", "zone"]:
        member = Q(**{prefix + name + "_id__in": DetailsForm.base_fields[name].queryset.values("pk")})
        if name != "municipality":
            member |= Q(**{prefix + name + "_id__isnull": True})
        proof &= member
    postal = PostalCode.municipalities.through.objects.filter(
        postalcode_id=OuterRef(prefix + "postal_code_id"),
        municipality_id=OuterRef(prefix + "municipality_id"),
    )
    proof &= Q(approved_revision__postal_code_id__isnull=True) | (
        Q(approved_revision__postal_code__public_safe=True) & Q(Exists(postal)))
    proof &= Q(approved_revision__zone_id__isnull=True) | Q(
        approved_revision__zone__municipality_id=F(prefix + "municipality_id"))
    for name in ["categories", "services", "travel_areas"]:
        field = Revision._meta.get_field(name)
        target = field.m2m_reverse_field_name() + "_id"
        members = field.remote_field.through.objects.all()
        if not bulk:
            members = members.filter(revision_id=OuterRef(prefix + "id"))
        bad = members.exclude(**{target + "__in": DetailsForm.base_fields[name].queryset.values("pk")})
        proof &= ~Q(**{prefix + "id__in": bad.values("revision_id")}) if bulk else ~Q(Exists(bad))
        if DetailsForm.base_fields[name].required:
            proof &= Q(**{prefix + "id__in": members.values("revision_id")}) if bulk else Q(Exists(members))
    selected_categories = Revision.categories.through.objects.filter(
        revision_id=OuterRef("revision_id")).values("category_id")
    services = Revision.services.through.objects.all()
    if not bulk:
        services = services.filter(revision_id=OuterRef(prefix + "id"))
    bad_service = services.exclude(service__category_id__in=selected_categories)
    proof &= ~Q(**{prefix + "id__in": bad_service.values("revision_id")}) if bulk else ~Q(Exists(bad_service))

    rates = Rate.objects.all()
    if not bulk:
        rates = rates.filter(revision_id=OuterRef(prefix + "id"))
    if text_membership and legacy_text:
        good_rate = ~Q(pk__in=Rate.objects.filter(rate_text_unknown()).values("pk"))
    else:
        good_rate = Q(PlainTextProof(F("concept"), 80, True, legacy=legacy_text))
    good_rate &= Q(duration_minutes__isnull=True) | Q(duration_minutes__gte=1, duration_minutes__lte=10080)
    good_rate &= Q(mode="consult", amount__isnull=True) | Q(
        mode__in=["fixed", "from"], amount__gt=0, amount__lte=999999.99)
    if bulk:
        proof &= ~Q(**{prefix + "id__in": rates.exclude(good_rate).values("revision_id")})
        too_many = rates.values("revision_id").annotate(total=Count("pk")).filter(total__gt=10)
        proof &= ~Q(**{prefix + "id__in": too_many.values("revision_id")})
        photos = Photo.objects.filter(removed_at__isnull=True).values("revision_id").annotate(
            total=Count("pk"), bad=Count("pk", filter=~Q(blob__status="ready", comparison_complete=True)),
        ).filter(total__gte=1, total__lte=8, bad=0)
        return proof & Q(**{prefix + "id__in": photos.values("revision_id")})
    proof &= ~Q(Exists(rates.exclude(good_rate)))
    # OFFSET bounds avoid transferring all relationships; they count records,
    # not distinct values, and preserve zero rates as native-valid.
    proof &= ~Q(Exists(rates.order_by("pk")[10:11]))
    photos = Photo.objects.filter(revision_id=OuterRef(prefix + "id"), removed_at__isnull=True)
    proof &= Q(Exists(photos)) & ~Q(Exists(photos.order_by("pk")[8:9]))
    proof &= ~Q(Exists(photos.exclude(blob__status="ready", comparison_complete=True)))
    return proof


class CapturedSQLRead:
    """A bound SELECT consumed inside the existing restoring read scope."""
    def __init__(self, sql, params):
        self.sql, self.params = sql, params

    def __iter__(self):
        with connection.cursor() as cursor:
            cursor.execute(self.sql, self.params)
            names = [column.name for column in cursor.description]
            for values in cursor.fetchall():
                yield dict(zip(names, values, strict=True))


def compact_order(query, page_number):
    """Only the two explicit public orders have an audited outer ordering."""
    ordering = tuple(query.query.order_by)
    if (type(page_number) is not int or page_number < 1 or query.query.is_sliced
            or query.query.combinator or query.query.extra_order_by or query.query.extra_select
            or set(query.query.annotations) - {"search_vector", "relevance"}):
        return None
    if ordering == ("-published_at", "pk"):
        return ["published_at"], '"published_at" DESC, "pk" ASC'
    if ordering == ("-relevance", "-published_at", "pk"):
        return ["relevance", "published_at"], '"relevance" DESC, "published_at" DESC, "pk" ASC'
    return None


def read_certified_page(query, page_number, ordering):
    """Evaluate every proof first; transfer a page only if ALL are sufficient.

    DISTINCT remains inside the materialized population, before row_number.
    Summary/duplicate checks consume that full population in the same statement.
    One unknown or duplicate pointer returns ALL rows in their original order.
    No OFFSET/LIMIT is applied to unevaluated or residually unknown candidates.
    """
    fields, order_sql = ordering
    source = query.values("pk", "approved_revision_id", "_sql_publication_positive", *fields)
    try:
        inner_sql, params = source.query.get_compiler(connection=connection).as_sql()
    except EmptyResultSet:
        return [], {"position": 0, "total": 0, "unknown": 0, "unique_revisions": 0}, 0
    statement = f'''
        WITH "_publication_certified" AS MATERIALIZED ({inner_sql}),
        "_publication_summary" AS (
            SELECT count(*) AS total,
                   count(*) FILTER (WHERE NOT "_sql_publication_positive") AS unknown,
                   count(DISTINCT "approved_revision_id") AS unique_revisions
            FROM "_publication_certified"
        ), "_publication_ordered" AS (
            SELECT "pk", "approved_revision_id", "_sql_publication_positive",
                   row_number() OVER (ORDER BY {order_sql}) AS position
            FROM "_publication_certified"
        )
        SELECT NULL::uuid AS pk, NULL::uuid AS approved_revision_id,
               NULL::boolean AS _sql_publication_positive, 0::bigint AS position,
               total, unknown, unique_revisions
        FROM "_publication_summary"
        UNION ALL
        SELECT p.pk, p.approved_revision_id, p._sql_publication_positive, p.position,
               s.total, s.unknown, s.unique_revisions
        FROM "_publication_ordered" p CROSS JOIN "_publication_summary" s
        WHERE s.unknown > 0 OR s.unique_revisions <> s.total
              OR p.position BETWEEN %s AND %s
        ORDER BY position
    '''
    offset = (page_number - 1)*24
    fetched = read_publication_values(CapturedSQLRead(statement, [*params, offset+1, offset+24]))
    # Explicit fetch cardinality for THIS statement only; header is an auxiliary
    # row, never a listing or a global rows_scanned/ORM-materialization metric.
    returned_sql_rows = len(fetched)
    summary, *rows = fetched
    assert summary["position"] == 0
    return rows, summary, returned_sql_rows


def read_ordered_scalar_population(query, ordering):
    """Capture EVERY proof in native order, without decoding unused sort values.

    DISTINCT/order expressions remain inside SQL. The outer order is explicit;
    timestamps/rank never cross the wire. Canonical UUID text avoids constructing
    UUID instances until an ID is actually consumed. This changes representation,
    never which candidates are evaluated or when eligibility/count are resolved.
    """
    fields, order_sql = ordering
    source = query.values("pk", "approved_revision_id", "_sql_publication_positive", *fields)
    try:
        inner_sql, params = source.query.get_compiler(connection=connection).as_sql()
    except EmptyResultSet:
        return []
    qualified_order = ", ".join('"_publication_scalar_population".' + item
                                for item in order_sql.split(", "))
    statement = f'''
        SELECT pk::text AS pk, approved_revision_id::text AS approved_revision_id,
               "_sql_publication_positive"
        FROM ({inner_sql}) AS "_publication_scalar_population"
        ORDER BY {qualified_order}
    '''
    return read_publication_values(CapturedSQLRead(statement, params))


class SQLPublication:
    """Capture the complete ordered population as IDs and a sufficient proof."""

    def __init__(self, query, *, setwise=False, bulk=True, json_path=True, page_number=None, legacy_text=True, text_membership=True, scalar_capture=True):
        document = submissions.current_publishing_document()
        try:
            if not document:
                raise ValidationError("No current document")
            ContactsForm.base_fields["legal_version"].clean(document.version)
        except ValidationError:
            proof = Q(pk__isnull=True)
            prepared = query
        else:
            prepared = query if bulk else publication_query(query, document)
            proof = authority_proof(document, bulk=bulk) & content_proof(bulk=bulk, json_path=json_path, legacy_text=legacy_text, text_membership=text_membership)
            if setwise and not bulk:
                # Put proof predicates in WHERE so PostgreSQL can plan semi/anti
                # joins as sets, instead of running correlated CASE subplans per
                # candidate. The outer query still captures EVERY candidate;
                # nonmembers remain unknown, not excluded. One SQL snapshot.
                positives = prepared.filter(proof).order_by().values("pk")
                prepared = query
                proof = Q(pk__in=positives)
        # Keep the complete native order/filters and DISTINCT before reducing
        # the transferred rows of a completely certified population.
        prepared = prepared.annotate(
            _sql_publication_positive=Case(When(proof, then=Value(True)), default=Value(False),
                                           output_field=BooleanField()))
        ordering = compact_order(query, page_number)
        self.compact = False
        scalar_ordering = compact_order(query, 1) if scalar_capture and ordering is None else None
        self.scalar_capture = scalar_ordering is not None
        summary = None
        returned_sql_rows = "not_measured"
        if ordering is not None:
            self.rows, summary, returned_sql_rows = read_certified_page(prepared, page_number, ordering)
            self.compact = summary["unknown"] == 0 and summary["unique_revisions"] == summary["total"]
        elif self.scalar_capture:
            self.rows = read_ordered_scalar_population(prepared, scalar_ordering)
        else:
            self.rows = read_publication_values(prepared.values(
                "pk", "approved_revision_id", "_sql_publication_positive"))
        self.population_count = summary["total"] if summary else len(self.rows)
        self.by_id = {row["pk"]: row for row in self.rows}
        self.stats = {"scalar_capture": self.scalar_capture,
                      "scalar_statement_rows_returned": len(self.rows) if self.scalar_capture else "not_measured",
                      "text_membership": text_membership and legacy_text, "text_proof_strategy": "legacy" if legacy_text else "single_negative",
                      "json_choices_strategy": "strict_path" if json_path else "elements",
                      "candidates": self.population_count, "positive": self.population_count if self.compact else 0, "native_fallback": 0,
                      "details_native": 0, "contacts_native": 0, "rates_native": 0,
                      "compact_certified_page": self.compact, "captured_id_rows": len(self.rows),
                      "certified_statement_rows_returned_including_header": returned_sql_rows,
                      "proof_strategy": "sql_bulk_dependencies" if bulk else
                          "sql_sufficient_current_values" if setwise else "sql_row_proof"}

    def certified_page(self, query, number):
        assert self.compact
        # Keep a real, lazy ID queryset as the paginator's population. The count
        # and this page's IDs were already captured together; no second query is
        # executed by this method. Page links continue to make fresh requests.
        paginator = Paginator(query.values_list("pk", flat=True), 24)
        paginator.count = self.population_count
        return Page([row["pk"] for row in self.rows], paginator.validate_number(number), paginator)

    def visible_ids(self, query):
        keys = self.visible_keys(query)
        return [UUID(key) for key in keys] if self.scalar_capture else keys

    def scalar_page(self, query, number):
        assert self.scalar_capture
        # Full residual validation precedes count and slicing. Only consumed
        # page IDs need Python UUID objects; the public page still exposes UUIDs.
        page = Paginator(self.visible_keys(query), 24).page(number)
        page.object_list = [UUID(key) for key in page.object_list]
        return page

    def captured_revision(self, listing_id):
        key = str(listing_id) if self.scalar_capture else listing_id
        value = self.by_id[key]["approved_revision_id"]
        return UUID(value) if self.scalar_capture and value is not None else value

    def visible_keys(self, query):
        if self.compact:
            raise ValueError("Compact proof contains only a page; use certified_page")
        if len({row["approved_revision_id"] for row in self.rows}) != len(self.rows):
            # Preserve the native context's behavior on inconsistent pointers.
            unknown = [row["pk"] for row in self.rows]
            positive = set()
        else:
            positive = {row["pk"] for row in self.rows if row["_sql_publication_positive"]}
            unknown = [row["pk"] for row in self.rows if not row["_sql_publication_positive"]]
        self.stats.update(positive=len(positive), native_fallback=len(unknown))
        if unknown:
            native = PublicationContext(query.filter(pk__in=unknown))
            positive.update((str(row.pk) if self.scalar_capture else row.pk)
                            for row in native.rows if moderation.publicly_visible(row, context=native))
        return [row["pk"] for row in self.rows if row["pk"] in positive]
