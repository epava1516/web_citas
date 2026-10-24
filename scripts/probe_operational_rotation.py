"""Owned Docker JSON-file rotation/follow probe; no daemon log-file access."""
import argparse
import io
import json
import subprocess
import threading
import time
from pathlib import Path
from uuid import uuid4

from apps.core.operational_window import summarize_window

TOTAL = 50000
TASK = 'apps.listings.tasks.refresh_publication_state'


def docker(*args, timeout=30):
    return subprocess.check_output(['docker', *args], timeout=timeout, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    if options.output.exists() or not options.output.parent.is_dir():
        parser.error('Fresh output in an existing owned artifact directory required')
    config = json.loads(docker('compose', 'config', '--no-env-resolution', '--format', 'json'))
    logging_config = {'driver': 'json-file', 'options': {'max-size': '1m', 'max-file': '3'}}
    assert all(config['services'][name]['logging'] == logging_config for name in ('app', 'worker', 'beat'))
    # Resolve the existing local image ID and prohibit any registry pull.
    image = docker('image', 'inspect', 'postgres:17-alpine', '--format', '{{.Id}}').strip()
    token = uuid4().hex
    name = 'b12-rotation-' + token
    label = 'web-modelos-b12-rotation=' + token
    script = r'''echo '{"schema_version":1,"event":"publication_read","timestamp_seconds":0,"route":"state","reason":"trusted_state","status_class":"2xx"}'
while [ ! -e /tmp/go ]; do sleep 0.05; done
awk 'BEGIN { for(i=1;i<=50000;i++) {
 if(i==50000) printf("{\"schema_version\":1,\"event\":\"task_result\",\"timestamp_seconds\":%d,\"task\":\"apps.listings.tasks.refresh_publication_state\",\"outcome\":\"failed\"}\n",i);
 else printf("{\"schema_version\":1,\"event\":\"publication_read\",\"timestamp_seconds\":%d,\"route\":\"%s\",\"reason\":\"%s\",\"status_class\":\"2xx\"}\n",i,i%10==0?"fallback":"state",i%10==0?"invalid_search":"trusted_state");
}}' '''
    follower = None
    collector = None
    observed = {'count': 0, 'last': -1, 'errors': [], 'sequence_failure': None}
    tail = []
    created = False
    proof = None
    try:
        # Inspect/clean up by owned label even if docker run itself times out.
        created = True
        docker('run', '-d', '--name', name, '--label', label, '--pull=never',
               '--network=none', '--read-only', '--tmpfs', '/tmp:rw,size=1m',
               '--tmpfs', '/var/lib/postgresql/data:rw,size=1m',
               '--cap-drop=ALL', '--security-opt=no-new-privileges', '--memory=64m', '--cpus=1',
               '--log-driver=json-file', '--log-opt=max-size=1m', '--log-opt=max-file=3',
               '--entrypoint=sh', image, '-c', script)
        metadata = json.loads(docker('inspect', name))[0]
        assert not [mount for mount in metadata['Mounts'] if mount['Type'] in ('volume', 'bind')]
        assert metadata['HostConfig']['LogConfig'] == {'Type': 'json-file', 'Config': logging_config['options']}
        follower = subprocess.Popen(['docker', 'logs', '--follow', name],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        def receive():
            try:
                for line in follower.stdout:
                    if len(line) > 2048:
                        raise ValueError('Oversize synthetic event')
                    row = json.loads(line)
                    stamp = row['timestamp_seconds']
                    if type(stamp) is not int or stamp != observed['last'] + 1:
                        observed['sequence_failure'] = {
                            'expected': observed['last'] + 1,
                            'received': stamp if type(stamp) is int and 0 <= stamp <= TOTAL else None,
                        }
                        raise ValueError('Missing or repeated synthetic event')
                    observed['last'] = stamp
                    observed['count'] += 1
                    if stamp >= TOTAL - 359:
                        tail.append(line)
            except Exception as error:
                observed['errors'].append(type(error).__name__)

        collector = threading.Thread(target=receive, daemon=True)
        collector.start()
        deadline = time.monotonic() + 10
        while observed['count'] == 0:
            assert follower.poll() is None and not observed['errors']
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned follower readiness deadline')
            time.sleep(.01)
        # First observed event proves the reader is attached before the burst.
        docker('exec', name, 'sh', '-c', 'touch /tmp/go')
        assert docker('wait', name, timeout=60).strip() == '0'
        deadline = time.monotonic() + 15
        while observed['count'] != TOTAL + 1:
            if observed['errors']:
                raise RuntimeError('Owned follower sequence validation failed')
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned follower drain deadline exceeded')
            time.sleep(.01)
        if follower.poll() is None:
            follower.terminate()
        try:
            follower.wait(timeout=5)
        except subprocess.TimeoutExpired:
            follower.kill()
            follower.wait(timeout=5)
        collector.join(timeout=5)
        assert not collector.is_alive() and not observed['errors'] and follower.poll() is not None
        assert follower.stderr.read() == b''
        assert observed['count'] == TOTAL + 1 and observed['last'] == TOTAL
        retained = docker('logs', name).encode()
        assert 0 < len(retained) <= 8 * 1024 * 1024
        stamps = [json.loads(line)['timestamp_seconds'] for line in retained.splitlines()]
        assert 0 < stamps[0] < TOTAL and stamps[-1] == TOTAL
        assert stamps == list(range(stamps[0], TOTAL + 1))
        start, end = TOTAL - 359, TOTAL + 1
        followed = summarize_window(io.BytesIO(b''.join(tail)), start, end)
        reread = summarize_window(io.BytesIO(retained), start, end)
        for key in ('fallback_fraction_observed', 'publication_reasons_observed', 'task_outcomes_observed'):
            assert followed[key] == reread[key]
        assert followed['counts']['publication_observed'] == reread['counts']['publication_observed'] == 359
        assert reread['task_outcomes_observed'][TASK]['failed'] == 1
        assert reread['counts']['malformed_or_unrecognized'] == 0
        proof = {'result': 'PASS_OWNED_ROTATION_AND_FOLLOW_NOT_DEPLOYED_OPERATION',
                 'container': name, 'label': label, 'image_id': image,
                 'docker_server_version': docker('version', '--format', '{{.Server.Version}}').strip(),
                 'runtime_logging': metadata['HostConfig']['LogConfig'],
                 'synthetic_events_generated': TOTAL + 1, 'follow_received': observed['count'],
                 'retained_events': len(stamps), 'retained_first_timestamp': stamps[0],
                 'retained_last_timestamp': stamps[-1], 'retained_api_bytes': len(retained),
                 'last_window_report': reread,
                 'reader_attachment_before_burst_observed': True,
                 'reader_stop': 'explicit_after_expected_events',
                 'limits': ['Synthetic generator, not app/worker/Beat deployment',
                            'No daemon file access or measured physical disk ceiling',
                            'Runtime log options verified; old lines missing after rotation',
                            'One owned burst and receiver; no universal completeness guarantee',
                            'Operational report retains unverified coverage and unknown health',
                            'No receiver restart/backpressure recovery, alert routing or B12 acceptance']}
    finally:
        if follower is not None and follower.poll() is None:
            follower.terminate()
            try:
                follower.wait(timeout=5)
            except subprocess.TimeoutExpired:
                follower.kill()
                follower.wait(timeout=5)
        if collector is not None:
            collector.join(timeout=5)
        if follower is not None:
            follower.stdout.close()
            follower.stderr.close()
        if created:
            probe = subprocess.run(['docker', 'container', 'inspect', name], capture_output=True)
            if probe.returncode == 0:
                labels = json.loads(probe.stdout)[0]['Config']['Labels']
                assert labels.get('web-modelos-b12-rotation') == token
                docker('rm', '-f', '-v', name)
            else:
                assert b'No such' in probe.stderr
            probe = subprocess.run(['docker', 'container', 'inspect', name], capture_output=True)
            assert probe.returncode != 0 and b'No such' in probe.stderr
        if proof is None:
            options.output.write_text(json.dumps({
                'result': 'FAIL_OWNED_ROTATION_PROBE', 'container': name,
                'observed': observed, 'owned_container_absence_verified': True,
                'reader_terminal': follower is None or follower.poll() is not None,
                'collector_terminal': collector is None or not collector.is_alive(),
            }, indent=2) + '\n')
    assert proof is not None
    proof['owned_container_removed'] = True
    options.output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({'result': proof['result'], 'received': observed['count'],
                      'retained': proof['retained_events'], 'owned_container_removed': True}))


if __name__ == '__main__':
    main()
