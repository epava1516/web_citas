from functools import reduce
from operator import or_

from django import forms
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Case, CharField, Q, Value, When
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from apps.catalog.models import Category, Municipality, PostalCode, Province, Region, Service, Zone

from .forms import DetailsForm, RelatedSelect
from .models import Listing
from .moderation import publicly_visible
from .presentation import describe


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
    reception = forms.BooleanField(required=False, label="Recepción / Reception")
    travel = forms.BooleanField(required=False, label="Desplazamiento / Travel")
    available = forms.BooleanField(required=False, label="Disponible ahora / Available now")

    def __init__(self, *args, english=False, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["category", "service"]:
            self.fields[name].english = english
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


def candidates(data):
    query = Listing.objects.filter(
        status="published", approved_revision__status="approved", expires_at__gt=timezone.now()
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
        primary = Case(
            When(approved_revision__content_language="en", then=Value("english")),
            default=Value("spanish"),
            output_field=CharField(),
        )
        alternative = Case(
            When(approved_revision__content_language="en", then=Value("spanish")),
            default=Value("english"),
            output_field=CharField(),
        )
        vector = (
            SearchVector("approved_revision__title", weight="A", config=primary)
            + SearchVector("approved_revision__description", weight="B", config=primary)
            + SearchVector(
                "approved_revision__description_alternative", weight="B", config=alternative
            )
        )
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
    return query.distinct()


def results(request):
    form = SearchForm(request.GET, english=request.LANGUAGE_CODE == "en")
    valid = form.is_valid()
    raw_page = request.GET.get("page", "1")
    if len(raw_page) > 6 or not raw_page.isdecimal() or not 1 <= int(raw_page) <= 100000:
        form.add_error(None, "Página inválida / Invalid page")
        valid = False
    number = int(raw_page) if valid else 1
    # Correct eligibility/counts first. Batch/index optimization is measured in B-B.
    visible = (
        [listing for listing in candidates(form.cleaned_data) if publicly_visible(listing)]
        if valid
        else []
    )
    try:
        page = Paginator(visible, 24).page(number)
    except EmptyPage as error:
        raise Http404 from error
    cards = []
    for listing in page.object_list:
        revision = listing.approved_revision
        description = (
            revision.description
            if revision.content_language == request.LANGUAGE_CODE
            or not revision.description_alternative
            else revision.description_alternative
        )
        public = describe(listing, request.LANGUAGE_CODE)
        cards.append(
            {
                "listing": listing,
                "revision": revision,
                "description": description,
                "public": public,
                "photo": revision.photos.filter(
                    approved=True, removed_at__isnull=True, blob__status="ready"
                ).first(),
            }
        )
    params = request.GET.copy()
    params.pop("page", None)
    response = render(
        request,
        "listings/results.html",
        {"form": form, "page": page, "cards": cards, "query_string": params.urlencode()},
        status=200 if valid else 400,
    )
    response["Cache-Control"] = "no-store"
    return response
