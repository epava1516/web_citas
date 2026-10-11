"""Real RustFS checks that worker observation preserves authentication guards."""

import io
import threading

import pytest
from cryptography.fernet import InvalidToken
from test_rights_object_store import object_store as real_object_store
from test_rights_object_verification_parallel import real_settings

from apps.safety import rights_object_content
from apps.safety.object_storage.factory import repository
from tests.capacity_worker_profile import scope

object_store = real_object_store


def test_real_workers_authenticate_all_objects_with_fresh_phase_counts(
    settings, object_store, record_property
):
    real_settings(settings, object_store)
    writer = repository()
    objects = [
        (writer.write(io.BytesIO(b'synthetic diagnostic' * 12000), f'own/{index}'.encode()),
         f'own/{index}'.encode())
        for index in range(28)
    ]
    previous = threading.getprofile()
    with scope() as collector:
        rights_object_content._verify_objects_in_order(iter(objects))
    assert threading.getprofile() is previous
    result = collector.snapshot()
    assert result['status'] == 'complete' and not result['incomplete']
    assert len(result['workers']) == 2
    phases = {}
    for worker in result['workers']:
        for name, counters in worker['phases'].items():
            phases[name] = phases.get(name, 0) + counters['segments']
    assert phases['object_verify'] == phases['repository_verify'] == 28
    # Crypto/repository creation remains fresh per object; transport is borrowed
    # only within each of the two worker-owned operation scopes.
    assert phases['factory_repository'] == phases['read_client'] == 28
    assert phases['factory_new_s3_client'] == 2
    assert phases['descriptor'] == phases['codec_verify'] == 28
    assert phases['authenticate_frames'] == phases['header'] == 28
    assert phases['tombstone'] == 56
    assert phases['ciphertext_finish'] == 28
    # Every object fetches ciphertext and reaches EOF. Adapter calls can also
    # observe an EOF already reached by the codec; these are execution segments,
    # not counts of physical S3 reads or the former generator's resumes.
    assert phases['ciphertext_fetch'] >= 56
    assert 'ciphertext_segments' not in phases
    # Counts prove observation, not production latency; no object data recorded.
    record_property('worker_observation_object_count', 28)
    record_property('worker_observation_phase_counts', str(phases))


@pytest.mark.parametrize('failure', ['context', 'physical_ciphertext'])
def test_real_authentication_failure_is_preserved_with_observation(
    settings, object_store, failure
):
    real_settings(settings, object_store)
    writer = repository()
    reference = writer.write(io.BytesIO(b'synthetic private content'), b'own')
    owner = b'other' if failure == 'context' else b'own'
    if failure == 'physical_ciphertext':
        writer.client.put_object(
            Bucket=writer.bucket, Key=writer.descriptor(reference)['key'], Body=b'corrupt')
    with pytest.raises(InvalidToken) as baseline:
        rights_object_content._verify_objects_in_order(iter([(reference, owner)]))
    previous = threading.getprofile()
    with scope() as collector:
        with pytest.raises(InvalidToken) as observed:
            rights_object_content._verify_objects_in_order(iter([(reference, owner)]))
    assert type(observed.value.__cause__) is type(baseline.value.__cause__)
    assert str(observed.value.__cause__) == str(baseline.value.__cause__)
    assert threading.getprofile() is previous
    assert collector.snapshot()['status'] == 'complete'
    assert not collector.snapshot()['incomplete']
