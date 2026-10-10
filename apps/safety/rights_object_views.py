"""Internal Caddy authorization endpoint; bearer never grants authority alone."""

import re

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_GET

from .rights_object_delivery import authorize_token
from .views import private


@require_GET
@sensitive_variables()
def authorize(request):
    secret = settings.RIGHTS_DELIVERY_PROXY_SECRET
    if (
        len(secret) < 32
        or not constant_time_compare(request.headers.get("X-Rights-Proxy", ""), secret)
        or request.headers.get("X-Forwarded-Method") != "GET"
        or request.headers.get("X-Forwarded-Range", "")
    ):
        raise Http404
    uri = request.headers.get("X-Forwarded-Uri", "")
    found = re.fullmatch(r"/private-deliveries/([A-Za-z0-9_:.-]{1,512})", uri)
    if not found:
        raise Http404
    row = authorize_token(found.group(1))
    response = private(HttpResponse(status=200))
    response["X-Delivery-Object"] = row.object_name
    response["X-Delivery-Type"] = row.content_type
    response["X-Delivery-Disposition"] = f'attachment; filename="{row.filename}"'
    return response
