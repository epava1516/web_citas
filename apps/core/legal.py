from django.shortcuts import get_object_or_404, render

from .models import LegalDocument


def index(request):
    documents = LegalDocument.objects.filter(language=request.LANGUAGE_CODE, active=True).order_by(
        "slug"
    )
    return render(request, "core/legal_index.html", {"documents": documents})


def document(request, slug):
    doc = get_object_or_404(LegalDocument, slug=slug, language=request.LANGUAGE_CODE, active=True)
    return render(request, "core/legal.html", {"document": doc})
