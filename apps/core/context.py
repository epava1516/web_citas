from django.conf import settings


def environment(request):
    return {"development": not settings.PRODUCTION, "english": request.LANGUAGE_CODE == "en"}
