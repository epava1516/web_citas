"""Withdraw 0021: expanded Listing locks deadlock with prelocked domain writers.

Restore 0020 invalidation and original dependency triggers. This intentionally
retains independent-draft invalidations until a safe optimization is proven.
"""
from importlib import import_module

from django.db import migrations

rejected = import_module('apps.listings.migrations.0021_private_draft_publication_dependencies')


class Migration(migrations.Migration):
    dependencies = [('listings', '0021_private_draft_publication_dependencies')]
    operations = [migrations.RunSQL(rejected.REVERSE, rejected.FORWARD)]
