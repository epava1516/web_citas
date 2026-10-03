from gunicorn.glogging import Logger


class SafeAccessLogger(Logger):
    def access(self, resp, req, environ, request_time):
        path = environ.get("PATH_INFO", "/")
        if (
            "/account/" in path
            or "/agency/" in path
            or "/admin/" in path
            or "/person/" in path
            or "/representation/" in path
            or "/phone/" in path
            or "/draft/" in path
            or "/photos/" in path
            or "/moderation/" in path
        ):
            path = "/private-operation/"
        self.access_log.info(
            "%s %s %s %.3fs",
            environ.get("REQUEST_METHOD", "-"),
            path,
            str(resp.status).split()[0],
            request_time.total_seconds(),
        )
