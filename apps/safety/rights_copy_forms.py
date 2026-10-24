"""Copy presentation forms; domain authority and delivery stay in their services."""

from django import forms

from .rectification_presentation import caption


class ReviewedCopyField(forms.JSONField):
    def prepare_value(self, value):
        return "" if value is None else super().prepare_value(value)


class CopyPresentationForm(forms.Form):
    """Static captions only; legacy constructors and JSON contents remain unchanged."""

    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, **kwargs)
        if language is not None:
            for field in self.fields.values():
                field.label = caption(field.label, language)
                if hasattr(field, "choices") and not hasattr(field, "queryset"):
                    field.choices = [
                        (value, caption(label, language)) for value, label in field.choices
                    ]
            for name, pair in {
                "operation": ("Operación", "Operation"),
                "section": ("Sección", "Section"),
                "page": ("Página", "Page"),
            }.items():
                if name in self.fields:
                    self.fields[name].label = pair[language == "en"]
            if "section" in self.fields:
                names = {
                    "profile": ("Perfil", "Profile"),
                    "subject_account": ("Cuenta del titular", "Subject account"),
                    "revisions": ("Revisiones", "Revisions"),
                    "legal_acceptances": ("Aceptaciones legales", "Legal acceptances"),
                    "favorites": ("Favoritos", "Favorites"),
                    "personal_contacts": ("Contactos personales", "Personal contacts"),
                    "agency_relationships": ("Relaciones con agencias", "Agency relationships"),
                    "verifications": ("Verificaciones", "Verifications"),
                    "representation_history": (
                        "Historial de representación",
                        "Representation history",
                    ),
                }
                self.fields["section"].choices = [
                    (value, names[value][language == "en"])
                    for value, _ in self.fields["section"].choices
                ]


class PageReviewForm(CopyPresentationForm):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.CharField(initial="save_page", widget=forms.HiddenInput)
    read_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    page_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado de revisión / Private review reason",
    )
    entries = ReviewedCopyField(
        widget=forms.Textarea, label="Entradas revisadas / Reviewed entries"
    )


class ExportForm(CopyPresentationForm):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("preview", "Consultar copia (auditoría) / Preview copy (audited)"),
            ("inspect_page", "Consultar sección por páginas / Inspect section pages"),
            ("inspect_saved_page", "Consultar decisiones guardadas / Inspect saved decisions"),
            ("compile_pages", "Compilar páginas revisadas / Compile reviewed pages"),
            ("generate_pages", "Generar desde páginas revisadas / Generate from reviewed pages"),
            (
                "generate_pages_with_information",
                "Generar páginas con información aprobada / Generate pages with approved information",
            ),
            ("generate", "Crear copia revisada / Create reviewed copy"),
        ]
    )
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )
    reason = forms.CharField(
        required=False,
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado de entrega / Private release reason",
    )
    section = forms.ChoiceField(
        required=False,
        choices=[
            (name, name)
            for name in [
                "profile",
                "subject_account",
                "revisions",
                "legal_acceptances",
                "favorites",
                "personal_contacts",
                "agency_relationships",
                "verifications",
                "representation_history",
            ]
        ],
    )
    page = forms.IntegerField(required=False, min_value=1, initial=1)
    information_review_id = forms.IntegerField(
        required=False,
        min_value=1,
        label="Referencia de aprobación de información / Information approval reference",
    )
    review_id = forms.IntegerField(
        required=False, min_value=1, label="Referencia de revisión / Review reference"
    )
    cursor = forms.CharField(required=False, max_length=2000, widget=forms.HiddenInput)
    copy = ReviewedCopyField(
        required=False,
        widget=forms.Textarea,
        label="Copia revisada; redacta datos ajenos / Reviewed copy; redact other people's data",
    )

