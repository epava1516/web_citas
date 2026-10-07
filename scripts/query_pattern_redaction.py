"""Redact SQL constants and group bind-list lengths without storing parameters."""

import re


def query_pattern(sql):
    tokens = r"/\*.*?\*/|--[^\n]*|\$(\w*)\$.*?\$\1\$|(?:E|U&)?'(?:''|\\.|[^'])*'"
    text = re.sub(
        tokens,
        lambda match: " " if match.group().startswith(("/*", "--")) else "?",
        str(sql),
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"(?<![\w])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w])", "?", text)
    text = re.sub(r"\(\s*(?:%s\s*,\s*)+%s\s*\)", "(%s[*])", text)
    return " ".join(text.split())
