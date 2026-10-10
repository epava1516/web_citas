"""One source per enclosing audited inspection; mandatory fresh check before return.

No cache survives the context. Only the matching active context may defer nested
source reads. The caller must enclose this context in its atomic transaction.
"""

from contextlib import contextmanager
from contextvars import ContextVar

from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .rights import fingerprint
from .rights_exports import canonical, source_copy

_current = ContextVar("rights_inspection_source", default=None)


def scope(person, listing, case):
    return (
        case.pk,
        case.version,
        case.person_id,
        case.account_subject_id,
        case.manager_version,
        person.pk if person else None,
        listing.pk if listing else None,
    )


class _InspectionSource:
    @sensitive_variables()
    def __init__(self, person, listing, case):
        self.scope = scope(person, listing, case)
        self.connection = transaction.get_connection()
        self.source = source_copy(person, listing, case)
        self.digest = fingerprint(canonical(self.source))
        self.row_references = {}

    @sensitive_variables()
    def get(self, person, listing, case):
        if (
            _current.get() is not self
            or transaction.get_connection() is not self.connection
            or not self.connection.in_atomic_block
            or scope(person, listing, case) != self.scope
        ):
            raise ValidationError("Inspection source context is unavailable or outside its scope")
        return self.source


@sensitive_variables()
def shared_source(context, person, listing, case):
    if not isinstance(context, _InspectionSource):
        raise ValidationError("Invalid inspection source context")
    return context.get(person, listing, case)


def shared_row_reference(dataset, index, row, compute):
    """Reuse a row reference only for a row object of the active shared source.

    The reference is a pure digest of the row; the shared source cannot change without the
    context exit rejecting the transaction, so one computation per row and request suffices.
    """
    from .rights_copy_inspection import SECTIONS

    context = _current.get()
    if context is None or dataset not in SECTIONS:
        return compute()
    rows = SECTIONS[dataset](context.source)
    if not isinstance(index, int) or not 0 <= index < len(rows) or rows[index] is not row:
        return compute()
    key = (dataset, index)
    if key not in context.row_references:
        context.row_references[key] = compute()
    return context.row_references[key]


@sensitive_variables()
def source_digest(context, person, listing, case, source=None):
    """Digest of the active shared source, computed once at its fresh read; without a
    context, of ``source`` or of a fresh copy. Mutation or DB drift of the shared source is
    still rejected by the context exit inside the caller's transaction."""
    if context is not None:
        shared_source(context, person, listing, case)
        return context.digest
    return fingerprint(canonical(source if source is not None else source_copy(person, listing, case)))


@contextmanager
@sensitive_variables()
def inspection_source(person, listing, case):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Inspection source requires an enclosing atomic transaction")
    context = _InspectionSource(person, listing, case)
    token = _current.set(context)
    try:
        yield context
        context.get(person, listing, case)
        # Detect accidental mutation of the shared projection as well as DB drift.
        if (
            fingerprint(canonical(context.source)) != context.digest
            or fingerprint(canonical(source_copy(person, listing, case))) != context.digest
        ):
            raise ValidationError("Inspection source changed before return")
    finally:
        _current.reset(token)
