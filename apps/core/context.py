from django.conf import settings


def environment(request):
    return {
        "promotion_test_mode": settings.PROMOTION_TEST_MODE,
        "development": not settings.PRODUCTION,
        "english": request.LANGUAGE_CODE == "en",
    }
