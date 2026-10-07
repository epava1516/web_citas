"""A changed native callback alias must invalidate the positive proof domain."""

from apps.listings import projected_publication, submissions
from apps.listings.public_validation import PublicationContext


def test_changed_submission_authority_alias_is_unsupported(monkeypatch):
    before = projected_publication.definitions_digest()
    monkeypatch.setattr(submissions, "publication_ready", lambda person: False)
    assert projected_publication.definitions_digest() != before


def test_changed_context_contacts_callback_is_unsupported(monkeypatch):
    before = projected_publication.definitions_digest()
    monkeypatch.setattr(PublicationContext, "contacts_valid", lambda *args: False)
    assert projected_publication.definitions_digest() != before


def test_wraps_does_not_certify_transparency(monkeypatch):
    from functools import wraps

    from apps.listings.models import Revision

    before = projected_publication.definitions_digest()
    original = Revision.clean

    @wraps(original)
    def forwarding(instance):
        return original(instance)

    # Even a forwarding wrapper is unknown to the reviewed rule set. Profiling
    # must use non-wrapping events; wraps alone cannot authorize a skipped layer.
    monkeypatch.setattr(Revision, "clean", forwarding)
    assert projected_publication.definitions_digest() != before


def test_fingerprint_stable_across_python_hash_seeds():
    import os
    import subprocess
    import sys

    command = [sys.executable, '-c',
               'import django; django.setup(); '
               'from apps.listings.projected_publication import definitions_digest; '
               'print(definitions_digest())']
    hashes = [subprocess.check_output(command, env={**os.environ, 'PYTHONHASHSEED': seed},
                                      text=True).strip() for seed in ['11', '29']]
    assert hashes[0] == hashes[1] == projected_publication.EXPECTED_DEFINITIONS
