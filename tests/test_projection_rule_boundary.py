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
