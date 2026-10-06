from django import forms

from .promotion_models import PromotionProduct, PromotionProductVersion
from .promotion_services import EDITABLE


class ProductForm(forms.ModelForm):
    class Meta:
        model = PromotionProduct
        fields = ["slug", "kind"]
        labels = {"slug": "Identificador / Identifier", "kind": "Tipo / Type"}


class VersionForm(forms.ModelForm):
    edit_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)

    class Meta:
        model = PromotionProductVersion
        fields = [*EDITABLE, "edit_version"]
        labels = {
            "name_es": "Nombre español / Spanish name",
            "name_en": "Nombre inglés / English name",
            "duration_days": "Duración en días / Duration in days",
            "amount": "Importe sin impuestos / Amount before tax",
            "currency": "Moneda / Currency",
            "tax_rate": "Impuesto porcentual / Tax percent",
            "bump_interval_minutes": "Intervalo de subida en minutos / Bump interval in minutes",
            "daily_bump_limit": "Cupo diario / Daily bump limit",
        }
