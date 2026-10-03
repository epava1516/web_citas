from django.db import DatabaseError, connection
from django.http import JsonResponse

from apps.listings.discovery import results


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def home(request):
    return results(request)
