"""Finite complete write-plus-read ROI contrast; no concurrent capacity proof."""
import hashlib
import json
import os
import time
from contextlib import nullcontext
from pathlib import Path

import pytest
from django.test import Client
from private_draft_invalidation_candidate import fenced_installed as installed
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401

from apps.core.models import User
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Blob, Match, Photo
from apps.mediafiles.services import process
from apps.mediafiles.tasks import process_blob
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_private_draft_roi(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_private_draft_roi.py' for x in request.config.args):
        pytest.skip('Explicit bounded ROI contrast only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    monkeypatch.setattr(process_blob, 'delay', lambda pk: None)
    populate(10000)
    user = User.objects.get(username='fixture-v1-individual')
    owner = Listing.objects.get(person__individual=user)
    client.force_login(user)
    reader = Client()
    raw = raw_image(782134)
    prepare_static_structures()
    owned_drafts, owned_blobs = [], []
    def prepare():
        Photo.objects.filter(revision_id__in=owned_drafts).delete()
        Revision.objects.filter(pk__in=owned_drafts).delete()
        Blob.objects.filter(pk__in=owned_blobs).delete()
        owned_drafts.clear()
        owned_blobs.clear()
        draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
        owned_drafts.append(draft.pk)
        publication_state.refresh_all()
        assert not PublicationDirty.objects.exists() and not Match.objects.exists()
        return draft
    def write(draft):
        assert upload(client, draft, raw).status_code == 302
        photo = Photo.objects.get(revision=draft)
        owned_blobs.append(photo.blob_id)
        process(photo.blob_id)
        assert not Match.objects.exists()
    # Warm image imports/code before any measured arm; remove this private data.
    write(prepare())
    routes = ['/es/', '/en/?q=synthetic', '/es/?q=photography']
    publication_state.refresh_all()
    expected = {}
    for route in routes:
        response = reader.get(route)
        assert response.status_code == 200
        expected[route] = hashlib.sha256(response.content).hexdigest()
    records = []
    for block in range(3):
        for arm in (['current', 'candidate'] if block % 2 == 0 else ['candidate', 'current']):
            draft = prepare()
            with installed() if arm == 'candidate' else nullcontext():
                wall, cpu = time.perf_counter(), time.thread_time()
                write(draft)
                write_wall, write_cpu = time.perf_counter()-wall, time.thread_time()-cpu
                dirty = PublicationDirty.objects.count()
                assert dirty == (1 if arm == 'current' else 0)
                reads = []
                for repeat in range(2):
                    for case, route in enumerate(routes):
                        wall, cpu = time.perf_counter(), time.thread_time()
                        response = reader.get(route)
                        elapsed, used = time.perf_counter()-wall, time.thread_time()-cpu
                        assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                        assert hashlib.sha256(response.content).hexdigest() == expected[route]
                        reads.append({'repeat':repeat, 'case':case, 'wall_s':elapsed, 'cpu_s':used})
                records.append({'block':block, 'arm':arm, 'write_wall_s':write_wall, 'write_cpu_s':write_cpu,
                                'dirty':dirty, 'reads':reads,
                                'total_wall_s':write_wall+sum(r['wall_s'] for r in reads),
                                'total_cpu_s':write_cpu+sum(r['cpu_s'] for r in reads)})
            (out / 'private-draft-roi.json').write_text(json.dumps(records, indent=2))
    record_property('scope', 'Six ownPG10k AB/BA arms, same seed782134 and actual ingest/process plus six sequential list/search reads; private rows/blobs deleted and state refreshed outside timed arm, image stack warmed first. No profiler/Celery/Beat/socket/concurrency. Current dirty deliberately persists for six reads, not actual refresh cadence. Ordered listing row locks active for candidate. This can overestimate benefit; no p95/capacity or N3 acceptance. Exact bodies/status/no-store parity.')
