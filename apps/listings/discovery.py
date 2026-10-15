from functools import reduce
from operator import or_

from django import forms
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.paginator import EmptyPage, Paginator
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from apps.catalog.models import Category, Municipality, PostalCode, Province, Region, Service, Zone
from apps.core.verification_services import real_checks

from .forms import DetailsForm, RelatedSelect
from .models import Listing
from .moderation import publicly_visible
from .presentation_reads import PagePresentation
from .search import revision_search_vector
from .seo import directory_metadata


def _attrs(attrs):
    """django/forms/widgets/attrs.html, rendered without the template engine."""
    return "".join(
        f" {conditional_escape(name)}"
        + ("" if value is True else f'="{conditional_escape(str(value))}"')
        for name, value in attrs.items()
        if value is not False
    )


class FastSelectRender:
    """Same markup as django/forms/widgets/select.html and select_option.html.

    The widget context (choices, selection, attributes and option hooks such as
    RelatedSelect.create_option) is Django's own; only the per-option template
    rendering is replaced. tests/test_search_form_render.py compares both outputs.
    """

    def render(self, name, value, attrs=None, renderer=None):
        widget = self.get_context(name, value, attrs)["widget"]
        parts = [f'<select name="{conditional_escape(widget["name"])}"{_attrs(widget["attrs"])}>']
        for group_name, group_choices, _ in widget["optgroups"]:
            if group_name:
                parts.append(f'\n  <optgroup label="{conditional_escape(group_name)}">')
            for option in group_choices:
                parts.append(
                    f'\n  <option value="{conditional_escape(str(option["value"]))}"'
                    f'{_attrs(option["attrs"])}>{conditional_escape(option["label"])}</option>\n'
                )
            if group_name:
                parts.append("\n  </optgroup>")
        parts.append("\n</select>")
        return mark_safe("".join(parts))


_FAST_WIDGETS = {}


def fast_widget_class(cls):
    if cls not in _FAST_WIDGETS:
        _FAST_WIDGETS[cls] = type("Fast" + cls.__name__, (FastSelectRender, cls), {})
    return _FAST_WIDGETS[cls]


class CatalogChoices(forms.ModelMultipleChoiceField):
    def label_from_instance(self, item):
        return getattr(item, "name_en" if self.english else "name_es")


class RelatedMultipleSelect(RelatedSelect, forms.SelectMultiple):
    pass


class SearchForm(forms.Form):
    q = forms.CharField(max_length=200, required=False, label="Texto / Text")
    profile = forms.MultipleChoiceField(
        required=False, choices=DetailsForm.base_fields["profile_type"].choices
    )
    category = CatalogChoices(required=False, queryset=Category.objects.filter(active=True))
    service = CatalogChoices(
        required=False, queryset=Service.objects.filter(active=True, category__active=True)
    )
    services_mode = forms.ChoiceField(
        required=False, choices=[("any", "Cualquiera / Any"), ("all", "Todos / All")]
    )
    region = forms.ModelMultipleChoiceField(required=False, queryset=Region.objects.all())
    province = forms.ModelMultipleChoiceField(
        required=False, queryset=Province.objects.all(), widget=RelatedMultipleSelect("region_id")
    )
    city = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Municipality.objects.filter(active=True).select_related("province"),
        widget=RelatedMultipleSelect("province_id"),
    )
    zone = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Zone.objects.filter(active=True, municipality__active=True),
        widget=RelatedMultipleSelect("municipality_id"),
    )
    postal_code = forms.ModelMultipleChoiceField(
        required=False,
        queryset=PostalCode.objects.filter(public_safe=True).prefetch_related("municipalities"),
        widget=RelatedMultipleSelect("municipalities"),
        help_text="Solo códigos con exposición pública permitida / Publicly allowed postal codes only",
    )
    language = forms.MultipleChoiceField(
        required=False, choices=DetailsForm.base_fields["spoken_languages"].choices
    )
    day = forms.MultipleChoiceField(required=False, choices=DetailsForm.base_fields["days"].choices)
    time_slot = forms.MultipleChoiceField(
        required=False, choices=DetailsForm.base_fields["time_slot"].choices[1:]
    )
    channel = forms.MultipleChoiceField(
        required=False,
        choices=[("phone", "Teléfono / Phone"), ("whatsapp", "WhatsApp"), ("telegram", "Telegram")],
    )
    checked = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("age", "Edad / Age"),
            ("contact", "Control del contacto / Contact control"),
            ("agency", "Agencia / Agency"),
        ],
    )
    reception = forms.BooleanField(required=False, label="Recepción / Reception")
    travel = forms.BooleanField(required=False, label="Desplazamiento / Travel")
    available = forms.BooleanField(required=False, label="Disponible ahora / Available now")

    def __init__(self, *args, english=False, fast_render=True, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["category", "service"]:
            self.fields[name].english = english
        if fast_render:
            for field in self.fields.values():
                if isinstance(field.widget, forms.Select):
                    field.widget.__class__ = fast_widget_class(type(field.widget))
        labels = {
            "q": ("Texto", "Text"),
            "profile": ("Tipo de perfil", "Profile type"),
            "category": ("Categorías", "Categories"),
            "service": ("Servicios", "Services"),
            "services_mode": ("Servicios: cualquiera o todos", "Services: any or all"),
            "region": ("Comunidades", "Regions"),
            "province": ("Provincias", "Provinces"),
            "city": ("Ciudades", "Cities"),
            "zone": ("Zonas", "Areas"),
            "postal_code": ("Códigos postales", "Postal codes"),
            "language": ("Idiomas", "Languages"),
            "day": ("Días", "Days"),
            "time_slot": ("Horario", "Time slots"),
            "channel": ("Contacto", "Contact"),
            "checked": ("Comprobaciones reales específicas", "Specific real checks"),
        }
        for name, labels_for_field in labels.items():
            self.fields[name].label = labels_for_field[int(english)]

    def clean(self):
        data = super().clean()
        regions, provinces, cities = data.get("region"), data.get("province"), data.get("city")
        if regions and provinces and provinces.exclude(region__in=regions).exists():
            self.add_error("province", "Ubicación incompatible / Incompatible location")
        if provinces and cities and cities.exclude(province__in=provinces).exists():
            self.add_error("city", "Ubicación incompatible / Incompatible location")
        if regions and cities and cities.exclude(province__region__in=regions).exists():
            self.add_error("city", "Ubicación incompatible / Incompatible location")
        if cities and data.get("zone") and data["zone"].exclude(municipality__in=cities).exists():
            self.add_error("zone", "Ubicación incompatible / Incompatible location")
        compatible = Municipality.objects.filter(active=True)
        if regions:
            compatible = compatible.filter(province__region__in=regions)
        if provinces:
            compatible = compatible.filter(province__in=provinces)
        if cities:
            compatible = compatible.filter(pk__in=cities)
        zones = data.get("zone")
        if zones and zones.exclude(municipality__in=compatible).exists():
            self.add_error("zone", "Ubicación incompatible / Incompatible location")
        postals = data.get("postal_code")
        if postals:
            for postal in postals:
                if not postal.municipalities.filter(pk__in=compatible).exists():
                    self.add_error("postal_code", "Ubicación incompatible / Incompatible location")
                    break
        return data


def candidates(data, *, stored_search=True):
    query = Listing.objects.filter(
        status="published", expires_at__gt=timezone.now()
    ).select_related("approved_revision__municipality", "person__agency", "person__phone_claim")
    paths = {
        "profile": "profile_type__in",
        "category": "categories__in",
        "region": "municipality__province__region__in",
        "province": "municipality__province__in",
        "city": "municipality__in",
        "zone": "zone__in",
        "postal_code": "postal_code__in",
        "time_slot": "time_slot__in",
    }
    for name, path in paths.items():
        if data.get(name):
            query = query.filter(**{"approved_revision__" + path: data[name]})
    if data.get("service"):
        if data.get("services_mode") == "all":
            for service in data["service"]:
                query = query.filter(approved_revision__services=service)
        else:
            query = query.filter(approved_revision__services__in=data["service"])
    for name, path in [("language", "spoken_languages"), ("day", "days")]:
        if data.get(name):
            query = query.filter(
                reduce(
                    or_,
                    [
                        Q(**{"approved_revision__" + path + "__contains": [value]})
                        for value in data[name]
                    ],
                )
            )
    for name in ["reception", "travel"]:
        if data.get(name):
            query = query.filter(**{"approved_revision__" + name: True})
    if data.get("available"):
        query = query.filter(available_until__gt=timezone.now())
    if data.get("channel"):
        conditions = {
            "phone": ~Q(approved_revision__phone=""),
            "whatsapp": Q(approved_revision__whatsapp=True),
            "telegram": ~Q(approved_revision__telegram=""),
        }
        query = query.filter(reduce(or_, [conditions[value] for value in data["channel"]]))
    if data.get("q"):
        vector = (F("approved_revision__search_document") if stored_search
                  else revision_search_vector("approved_revision__"))
        search = SearchQuery(data["q"], config="spanish", search_type="websearch") | SearchQuery(
            data["q"], config="english", search_type="websearch"
        )
        query = (
            query.annotate(search_vector=vector, relevance=SearchRank(vector, search))
            .filter(search_vector=search)
            .order_by("-relevance", "-published_at", "pk")
        )
    else:
        query = query.order_by("-published_at", "pk")
    population = query.distinct()
    native = population.filter(approved_revision__status="approved")
    # A sibling query with identical filters, timestamps and ordering. The state
    # path may omit the revision-status join only after exact trusted/native
    # membership. Unknown rows and every fallback still use `native` below.
    # QuerySet cloning drops this hint: further caller filters safely retain the
    # full native predicate rather than reusing an unfiltered sibling.
    native._publication_state_population = population
    return native


def matches_checks(person, selected):
    if not selected:
        return True
    checks = real_checks(person)
    return any(checks[name] for name in selected)


def results(request):
    form = SearchForm(request.GET, english=request.LANGUAGE_CODE == "en")
    valid = form.is_valid()
    raw_page = request.GET.get("page", "1")
    if len(raw_page) > 6 or not raw_page.isdecimal() or not 1 <= int(raw_page) <= 100000:
        form.add_error(None, "Página inválida / Invalid page")
        valid = False
    number = int(raw_page) if valid else 1
    from apps.catalog.promotion_exposure import enabled as promotions_enabled

    from .public_validation import PublicationContext
    from .publication_state import state_page

    request._publication_route = {"route": "fallback", "reason": "invalid_search"}
    try:
        page = None
        if not valid:
            pass
        elif promotions_enabled():
            request._publication_route.update(reason="synthetic_promotions")
        else:
            page = state_page(candidates(form.cleaned_data), number,
                              checked=form.cleaned_data.get("checked") or (),
                              observation=request._publication_route)
        sponsorship = {}
        if page is None:
            # The complete native population; its correlated read runs without JIT.
            context = (
                PublicationContext(candidates(form.cleaned_data), page_read=True)
                if valid else None
            )
            visible = (
                [listing for listing in context.rows
                 if publicly_visible(listing, context=context)
                 and matches_checks(listing.person, form.cleaned_data.get("checked"))]
                if context else []
            )
            from apps.catalog.promotion_exposure import ranked

            visible, sponsorship = ranked(visible, text_search=bool(form.cleaned_data.get("q")))
            page = Paginator(visible, 24).page(number)
    except EmptyPage as error:
        raise Http404 from error
    presentation = PagePresentation(page.object_list)
    request._presentation_reads = presentation.stats
    cards = []
    for listing in page.object_list:
        revision = listing.approved_revision
        description = (
            revision.description
            if revision.content_language == request.LANGUAGE_CODE
            or not revision.description_alternative
            else revision.description_alternative
        )
        public = presentation.describe(listing, request.LANGUAGE_CODE)
        cards.append(
            {
                "sponsorship": sponsorship.get(listing.pk),
                "listing": listing,
                "revision": revision,
                "description": description,
                "public": public,
                "photo": presentation.photo(listing),
            }
        )
    params = request.GET.copy()
    params.pop("page", None)
    response = render(
        request,
        "listings/results.html",
        {
            "form": form,
            "page": page,
            "cards": cards,
            "query_string": params.urlencode(),
            "seo": directory_metadata(request, valid=valid, page=page.number),
        },
        status=200 if valid else 400,
    )
    response["Cache-Control"] = "no-store"
    return response
