"""Private path-only walk for complete coverage; public scalar catalog stays unchanged."""

from django.core.exceptions import ValidationError


def _scalar_paths(value, prefix=""):
    """Mirror scalar_fields traversal without allocating an unused leaf dictionary.

    Keep recursion, lazy iteration, subclass handling and failures aligned with the
    public oracle. Permanent differential tests cover their shared path semantics.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid portability object key")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from _scalar_paths(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _scalar_paths(child, prefix + "/" + str(index))
    elif prefix:
        yield prefix
    else:
        raise ValidationError("Portability row requires an object or list")
