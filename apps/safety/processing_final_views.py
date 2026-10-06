"""Shared response screen with restriction/objection-specific evidence and permission."""

from django import forms

from . import processing_final
from .erasure_final_views import FinalForm
from .erasure_final_views import final as response_screen
from .models import ProcessingExecution


class ProcessingForm(FinalForm):
    execution = forms.IntegerField(required=False, min_value=1, label="Ejecución / Execution")


def final(request, case_id):
    return response_screen(
        request,
        case_id,
        backend=processing_final,
        kinds=("restriction", "object"),
        execution_model=ProcessingExecution,
        form_class=ProcessingForm,
        template="safety/processing_final.html",
        prefix="process",
    )
