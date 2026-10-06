"""Strict projections of complete console MIME messages in timestamped captures."""

from datetime import datetime
from email import policy
from email.parser import Parser

from django.core.mail import EmailMessage


def console_mail_projections(content, cutoff, *, owner, email):
    from .rights_access_delivery import account_mail_projection

    if not owner or not email:
        return {}
    result = {}
    block = []
    size = 0
    for position, line in enumerate(content.splitlines()):
        try:
            timestamp, raw = line.split(" ", 1)
            timestamp = datetime.fromisoformat(timestamp)
            if timestamp.tzinfo is None or timestamp > cutoff:
                block = []
                continue
        except ValueError:
            block = []
            continue
        if raw.startswith("Content-Type:"):
            block = []
            size = 0
        if raw == "-" * 79:
            if block:
                mime = Parser(policy=policy.default).parsestr("\n".join(x[1] for x in block))
                names = [name.lower() for name in mime.keys()]
                allowed = {
                    "content-type",
                    "mime-version",
                    "content-transfer-encoding",
                    "subject",
                    "from",
                    "to",
                    "date",
                    "message-id",
                }
                if (
                    not mime.defects
                    and not mime.is_multipart()
                    and set(names) == allowed
                    and len(names) == len(allowed)
                    and mime.get_content_type() == "text/plain"
                    and mime.get_content_charset() == "utf-8"
                    and not any(getattr(value, "defects", ()) for value in mime.values())
                ):
                    try:
                        body = mime.get_content().rstrip("\n")
                        message = EmailMessage(
                            str(mime["Subject"]), body, str(mime["From"]), [str(mime["To"])]
                        )
                        projected = account_mail_projection(message, owner=owner, email=email)
                    except (LookupError, UnicodeError, ValueError):
                        projected = None
                    if projected and datetime.fromisoformat(projected["created_at"]) <= timestamp:
                        for index, text in block:
                            if text.startswith("To:") and email in text:
                                result[index] = projected
            block = []
            size = 0
        elif block or raw.startswith("Content-Type:"):
            size += len(raw.encode())
            if size <= 262144:
                block.append((position, raw))
            else:
                block = []
    return result
