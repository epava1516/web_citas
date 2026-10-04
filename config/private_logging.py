import logging


class PrivateRequestFilter(logging.Filter):
    def filter(self, record):
        request = getattr(record, "request", None)
        scopes = (
            "/safety/",
            "/moderation/reports/",
            "/moderation/rights/",
            "/moderation/complaints/",
        )
        if record.name == "django.server" and any(scope in record.getMessage() for scope in scopes):
            record.msg = "Private safety operation (development server)"
            record.args = ()
            record.request = None
        elif request is not None and any(scope in getattr(request, "path", "") for scope in scopes):
            record.msg = "Private safety operation returned HTTP %s"
            record.args = (getattr(record, "status_code", "-"),)
            record.request = None
        return True
