"""Pure projections reused only inside one atomic coverage batch's source context.

No authority, signature, approved decision, image metadata or physical image read is cached.
The caller has freshly decrypted and validated every input before calling project().
"""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from django.conf import settings
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

_current = ContextVar('coverage_batch_pure_projection', default=None)
_VALIDATED_ONLY = object()


@contextmanager
@sensitive_variables()
def batch_projection(source, user, case, proof):
    connection = transaction.get_connection()
    if not connection.in_atomic_block or source.connection is not connection:
        raise RuntimeError('Batch projection requires the active atomic inspection source')
    state = {'source': source, 'connection': connection, 'actor': user.pk,
             'session': user.session_version, 'mfa': user.mfa_version,
             'case': case.pk, 'proof': proof.pk, 'entries': {}}
    token = _current.set(state)
    try:
        yield
    finally:
        state['entries'].clear()
        _current.reset(token)


@sensitive_variables()
def project(source_context, user, case, proof, row, review, source, assessment, binding, operation, *, _audit_only=False):
    """Reuse computation after fresh validation; return an independent mutable projection."""
    if type(_audit_only) is not bool:
        raise ValueError('Invalid audit projection mode')
    state = _current.get()
    if (state is None or source_context is not state['source']
            or transaction.get_connection() is not state['connection']
            or not state['connection'].in_atomic_block
            or source is not source_context.source
            or (user.pk, user.session_version, user.mfa_version, case.pk, proof.pk) != (
                state['actor'], state['session'], state['mfa'], state['case'], state['proof'])):
        value = operation(source, assessment, binding['selection'],
                          field_evidence=binding.get('field_evidence'))
        return None if _audit_only else value
    # Ciphertext equality binds the freshly validated/decrypted declarations. Guards,
    # expiry, original signatures, latest approval and audited images still run per child.
    key = (case.version, case.kind, case.status, case.person_id, case.account_subject_id,
           case.manager_version, source_context.digest, proof.status, proof.expires_at,
           row.pk, row.version, row.actor_id, row.proof_id, row.assessment_review_id,
           row.source_digest, row.selection_digest, row.assessment_digest, row.inspection_digest,
           row.decision_digest, row.original_session_version, row.original_mfa_version,
           row.expires_at, row.purged_at, row.encrypted_selection, review.pk,
           review.assessment.encrypted_assessment, review.action.payload_digest,
           review.read.action.payload_digest, settings.SECRET_KEY, settings.SAFETY_ENCRYPTION_KEY,
           settings.PRODUCTION, operation)
    entries = state['entries']
    if key in entries and _audit_only:
        return None
    if key not in entries or entries[key] is _VALIDATED_ONLY:
        value = operation(source, assessment, binding['selection'],
                          field_evidence=binding.get('field_evidence'))
        # At most one entry per individually audited child; never grows across a request.
        if len(entries) >= 4:
            return None if _audit_only else value
        entries[key] = _VALIDATED_ONLY if _audit_only else deepcopy(value)
        return None if _audit_only else value
    return deepcopy(entries[key])
