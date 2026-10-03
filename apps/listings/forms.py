import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.catalog.models import Category, Municipality, PostalCode, Province, Region, Service, Zone

from .models import Rate, Revision


class RelatedSelect(forms.Select):
    def __init__(self, parent_field, *args, **kwargs):
        self.parent_field = parent_field
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if hasattr(value, "instance"):
            instance = value.instance
            parents = (
                [city.pk for city in instance.municipalities.all()]
                if self.parent_field == "municipalities"
                else [getattr(instance, self.parent_field)]
            )
            option["attrs"]["data-parents"] = ",".join(str(pk) for pk in parents)
        return option


class DetailsForm(forms.ModelForm):
    description = forms.CharField(max_length=6000, widget=forms.Textarea(attrs={"rows": 6}))
    description_alternative = forms.CharField(
        max_length=6000, required=False, widget=forms.Textarea(attrs={"rows": 4})
    )
    region = forms.ModelChoiceField(queryset=Region.objects.all(), label="Comunidad / Region")
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        label="Provincia / Province",
        widget=RelatedSelect("region_id"),
    )
    content_language = forms.ChoiceField(choices=[("es", "Español"), ("en", "English")])
    profile_type = forms.ChoiceField(
        choices=[
            ("woman", "Mujer / Woman"),
            ("man", "Hombre / Man"),
            ("trans", "Trans"),
            ("other", "Otro / Other"),
        ]
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(active=True), widget=forms.CheckboxSelectMultiple
    )
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(active=True), widget=forms.CheckboxSelectMultiple
    )
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.filter(active=True),
        label="Ciudad / City",
        widget=RelatedSelect("province_id"),
    )
    postal_code = forms.ModelChoiceField(
        queryset=PostalCode.objects.prefetch_related("municipalities"),
        widget=RelatedSelect("municipalities"),
        required=False,
        label="Código postal / Postal code",
        help_text="Muy recomendado para ayudar a encontrar tu zona. Sin domicilio exacto / Strongly recommended to find your area. No exact address",
    )
    zone = forms.ModelChoiceField(
        queryset=Zone.objects.filter(active=True),
        required=False,
        label="Zona / Area",
        widget=RelatedSelect("municipality_id"),
    )
    spoken_languages = forms.MultipleChoiceField(
        choices=[
            ("es", "Español"),
            ("en", "English"),
            ("fr", "Français"),
            ("de", "Deutsch"),
            ("it", "Italiano"),
            ("pt", "Português"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    days = forms.MultipleChoiceField(
        choices=[(str(n), str(n)) for n in range(1, 8)],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    time_slot = forms.ChoiceField(
        choices=[
            ("", "Sin informar / Not specified"),
            ("morning", "Mañana / Morning"),
            ("afternoon", "Tarde / Afternoon"),
            ("evening", "Noche / Evening"),
        ],
        required=False,
    )

    class Meta:
        model = Revision
        fields = [
            "title",
            "description",
            "content_language",
            "description_alternative",
            "profile_type",
            "categories",
            "services",
            "municipality",
            "postal_code",
            "zone",
            "travel_areas",
            "spoken_languages",
            "days",
            "time_slot",
            "reception",
            "travel",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "description_alternative": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = True
        self.fields["description"].required = True
        self.fields["description"].max_length = 6000
        self.fields["description_alternative"].max_length = 6000
        if self.instance.municipality_id:
            city = self.instance.municipality
            self.initial.setdefault("province", city.province_id)
            self.initial.setdefault("region", city.province.region_id)

    def clean(self):
        data = super().clean()
        city, province, region = data.get("municipality"), data.get("province"), data.get("region")
        if province and region and province.region_id != region.pk:
            self.add_error("province", "Provincia incompatible / Incompatible province")
        if city and province and city.province_id != province.pk:
            self.add_error("municipality", "Ciudad incompatible / Incompatible city")
        postal = data.get("postal_code")
        if postal and city:
            if not postal.municipalities.filter(pk=city.pk).exists():
                self.add_error(
                    "postal_code", "CP no corresponde a la ciudad / Postal code does not match city"
                )
            elif not postal.public_safe:
                self.add_error(
                    "postal_code",
                    "Precisión restringida por privacidad / Precision restricted for privacy",
                )
        if data.get("zone") and city and data["zone"].municipality_id != city.pk:
            self.add_error("zone", "Zona incompatible / Incompatible area")
        categories = data.get("categories")
        if categories is not None and any(
            service.category_id not in {cat.pk for cat in categories}
            for service in data.get("services", [])
        ):
            self.add_error(
                "services", "Servicio fuera de las categorías / Service outside selected categories"
            )
        for field in ["description", "description_alternative", "title"]:
            if re.search(
                r"(?:https?://|www\.|@[\w]+|\+?\d[\d ()-]{7,})", data.get(field, ""), re.I
            ):
                self.add_error(
                    field, "Usa los campos de contacto autorizados / Use authorized contact fields"
                )
        return data


class ContactsForm(forms.ModelForm):
    contact_exposure_accepted = forms.BooleanField(
        label="Comprendo que teléfono y canales serán públicos y pueden copiarse / I understand contacts will be public and may be copied"
    )
    accept_publishing = forms.BooleanField(
        label="Acepto las obligaciones de publicación / I accept publishing obligations"
    )
    legal_version = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Revision
        fields = ["whatsapp", "telegram", "contact_exposure_accepted"]

    def clean_telegram(self):
        value = self.cleaned_data["telegram"].lstrip("@").strip()
        if value and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", value):
            raise ValidationError("Usuario Telegram no válido / Invalid Telegram username")
        return value


class RateForm(forms.ModelForm):
    class Meta:
        model = Rate
        fields = ["concept", "mode", "amount", "duration_minutes"]

    def clean_duration_minutes(self):
        value = self.cleaned_data.get("duration_minutes")
        if value is not None and not 1 <= value <= 10080:
            raise ValidationError(
                "Duración entre uno y 10080 minutos / Duration between one and 10080 minutes"
            )
        return value

    def clean(self):
        data = super().clean()
        if data.get("DELETE"):
            return data
        if data.get("mode") == "consult" and data.get("amount") is not None:
            self.add_error(
                "amount", "Consultar no requiere importe / Consult must not have an amount"
            )
        elif data.get("mode") in {"fixed", "from"} and (
            data.get("amount") is None or data["amount"] <= 0
        ):
            self.add_error("amount", "Importe positivo obligatorio / Positive amount required")
        return data


class AuthorizedRateFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            rate = form.cleaned_data.get("id")
            if rate and rate.revision_id != self.instance.pk:
                raise ValidationError("Tarifa de otra revisión / Rate belongs to another revision")


RateFormSet = inlineformset_factory(
    Revision,
    Rate,
    form=RateForm,
    formset=AuthorizedRateFormSet,
    extra=1,
    max_num=10,
    validate_max=True,
    can_delete=True,
)
