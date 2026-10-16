"""Observe actual draft upload invalidations versus native publication eligibility."""
import json
import os
from pathlib import Path

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401

from apps.core.models import User
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.public_validation import PublicationContext
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Match, Photo
from apps.mediafiles.services import process
from apps.mediafiles.tasks import process_blob
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_draft_upload_dependency(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_draft_upload_dependency.py' for x in request.config.args):
        pytest.skip('Explicit synthetic dependency audit only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    queued = []
    monkeypatch.setattr(process_blob, 'delay', lambda pk: queued.append(pk))
    populate(10000)
    user = User.objects.get(username='fixture-v1-individual')
    owner = Listing.objects.get(person__individual=user)
    client.force_login(user)
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists() and not Match.objects.exists()
    def native():
        context = PublicationContext(Listing.objects.filter(pk=owner.pk), page_read=True)
        assert len(context.rows) == 1
        return publication_state.eligible_ignoring_expiry(context.rows[0], context)
    def stats(cursor):
        cursor.execute('SELECT pg_stat_force_next_flush()')
        cursor.execute('SELECT pg_stat_clear_snapshot()')
        cursor.execute("SELECT funcname,calls,total_time FROM pg_stat_user_functions WHERE schemaname='public' AND (funcname LIKE 'lpd_%' OR funcname='listings_publication_mark')")
        return {name: {'calls':calls, 'ms':elapsed} for name,calls,elapsed in cursor.fetchall()}
    rows = []
    before_native = native()
    assert before_native
    with connection.cursor() as cursor:
        cursor.execute("SET track_functions='all'")
        try:
            for phase in ['ingest', 'process']:
                PublicationDirty.objects.all().delete()
                before = stats(cursor)
                if phase == 'ingest':
                    assert upload(client, draft, raw_image(782134)).status_code == 302
                    photo = Photo.objects.get(revision=draft)
                    assert len(queued) == 1 and str(photo.blob_id) == queued[0]
                else:
                    process(photo.blob_id)
                    photo.blob.refresh_from_db()
                    assert photo.blob.status == 'ready'
                after = stats(cursor)
                after_native = native()
                assert after_native == before_native
                assert not Match.objects.exists()
                dirty = set(PublicationDirty.objects.values_list('listing_id', flat=True))
                assert dirty == {owner.pk}
                changed = {name: {'calls':v['calls']-before.get(name,{}).get('calls',0),
                                  'ms':v['ms']-before.get(name,{}).get('ms',0)}
                           for name,v in after.items() if v['calls'] > before.get(name,{}).get('calls',0)}
                rows.append({'phase':phase, 'dirty_count':len(dirty), 'dirty_is_owner_only':True,
                             'native_eligible_unchanged':True, 'matches':0, 'functions':changed})
        finally:
            cursor.execute("SET track_functions='none'")
    record_property('draft_dependency', json.dumps(rows))
    record_property('limits', 'Real ingest and process with capacity seed782134/10k own synthetic PG; task dispatch recorded, process called sequentially without Celery/Beat. Native same one owner before/after, no Match. Demonstrates conservative invalidation for this fixture only; not proof that draft/photo/blob triggers may be removed generally, nor p95/capacity.')
