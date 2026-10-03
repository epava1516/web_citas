import logging


class PrivateRequestFilter(logging.Filter):
    def filter(self, record):
        request = getattr(record, "request", None)
        if record.name == "django.server" and "/safety/" in record.getMessage():
            record.msg = "Private safety operation (development server)"
            record.args = ()
            record.request = None
        elif request is not None and "/safety/" in getattr(request, "path", ""):
            record.msg = "Private safety operation returned HTTP %s"
            record.args = (getattr(record, "status_code", "-"),)
            record.request = None
        return True
