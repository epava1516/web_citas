"""Finite beta HTTP inside the official bounded topology; no global capacity acceptance."""

import http.cookies
import json
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

import pytest
from beta_promotional_load_fixture import finalize_promotional_statistics, prepare_promotional_load
from capacity_beta_http import owned_broker, verify_owned_fixture
from capacity_gunicorn import server
from django.conf import settings as runtime_settings
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image  # noqa: F401
from test_worker_capacity_comparison import BEAT_PHASE_SECONDS, beat_refresh_publishes

from apps.core.models import User
from apps.listings import publication_state
from apps.listings.models import PublicationDirty, Revision
from apps.mediafiles.models import Photo, UploadAttempt
from scripts.benchmark_async_transport import POLICY, fetch_http, run_async_open_loop
from scripts.benchmark_gc_observer import GCObserver, prepare_generator_gc

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not (getattr(runtime_settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False)
         or getattr(runtime_settings, 'CAPACITY_BETA_HTTP_SHORT', False)
         or getattr(runtime_settings, 'CAPACITY_BETA_HTTP_CONTRACTUAL', False)),
    reason='Requires exclusive owned8CPU beta HTTP functional controller')]


def test_owned_beta_http_calibration(request, settings, record_property):
    committed = getattr(settings, 'CAPACITY_BETA_HTTP_COMMITTED_MIXED', False)
    combined = getattr(settings, 'CAPACITY_BETA_HTTP_COMBINED_FILTERS', False)
    generator_diagnostic = getattr(settings, 'CAPACITY_BETA_HTTP_GENERATOR_DIAGNOSTIC', False)
    assert not generator_diagnostic or combined
    backlog = getattr(settings, 'CAPACITY_BETA_HTTP_BACKLOG', False)
    mixed = getattr(settings, 'CAPACITY_BETA_HTTP_MIXED_STATES', False)
    assert not mixed or (backlog and getattr(settings, 'CAPACITY_BETA_HTTP_BACKLOG_POPULATION', None) in (100, 1000, 10000))
    assert not backlog or (getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False)
                           and getattr(settings, 'CAPACITY_BETA_HTTP_TERRITORIAL', False)
                           and getattr(settings, 'CAPACITY_RESOURCE_RUN_ID', None))
    territorial = getattr(settings, 'CAPACITY_BETA_HTTP_TERRITORIAL', False)
    short = getattr(settings, 'CAPACITY_BETA_HTTP_SHORT', False)
    contractual = getattr(settings, 'CAPACITY_BETA_HTTP_CONTRACTUAL', False)
    upload_calibration = getattr(settings, 'CAPACITY_BETA_HTTP_UPLOAD_CALIBRATION', False)
    assert not upload_calibration or (not short and not contractual
                                      and getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False))
    assert not territorial or (not upload_calibration and (not contractual or committed or combined))
    duration, population = ((900, 10000) if contractual else (60, 10000) if short
                            else (15, 10) if upload_calibration else (3, 10))
    if backlog:
        population = getattr(settings, 'CAPACITY_BETA_HTTP_BACKLOG_POPULATION', 10)
        assert population in (10, 100, 1000, 10000)
    assert not committed or ((getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False) or short or contractual)
                             and territorial and not backlog and not mixed
                             and not upload_calibration)
    if committed:
        population = getattr(settings, 'CAPACITY_BETA_HTTP_COMMITTED_POPULATION', 100)
        assert population in (100, 1000, 10000)
        assert not (short or contractual) or population == 10000
    assert not combined or ((getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False) or short or contractual)
                            and territorial and not any((committed, backlog, mixed, upload_calibration))
                            and not getattr(settings, 'CAPACITY_RESOURCE_RUN_ID', None))
    if combined:
        population = getattr(settings, 'CAPACITY_BETA_HTTP_COMBINED_POPULATION', 100)
        assert population in (100, 1000, 10000)
        assert not generator_diagnostic or (population == 100 and not short and not contractual)
        assert not (short or contractual) or population == 10000
        if not (short or contractual):
            duration = 3 if population == 100 else 6
    upload_count = 15 if contractual or upload_calibration else 1
    upload_interval = 1 if upload_calibration else 60
    proof = {'scope': 'Owned fifteen upload calibration only' if upload_calibration else 'Owned beta contractual HTTP only' if contractual else 'Owned beta short diagnostic' if short else 'Owned beta functional calibration',
             'duration_seconds': duration, 'population': population,
             'capacity_accepted': False}
    broker = None
    try:
        preparation_started = time.monotonic()
        proof['fixture_context'] = verify_owned_fixture()
        proof['planned_uploads'] = upload_count
        proof['upload_interval_seconds'] = upload_interval
        proof['upload_calibration'] = upload_calibration
        proof['distinct_draft_uploads'] = True
        proof['owned_fixture_verified'] = True
        broker = owned_broker()
        broker.flushdb()  # This verified disposable broker belongs to this run alone.
        request.getfixturevalue('directory')
        dataset = prepare_promotional_load(request, population)
        if territorial:
            from beta_promotional_load_fixture import redistribute_promotional_geography

            from apps.catalog.models import Municipality

            cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                          .order_by('pk').values_list('pk', flat=True)[:2])
            assert len(cities) == 2
            first = population * 7 // 10
            dataset = redistribute_promotional_geography(
                dataset, {cities[0]: first, cities[1]: population - first},
            )
        if combined:
            from capacity_combined_filters import distribute

            proof['combined_filters'] = {'distribution': distribute(dataset)}
        proof['territorial_enabled'] = territorial
        publication_state.refresh_all()
        stats = finalize_promotional_statistics(dataset)
        assert len(stats['tables']) == 8 and stats['owned_synthetic_postgresql_verified']
        proof['statistics_finalized'] = True
        assert sum(dataset['geography'].values()) == dataset['published'] == population
        assert dataset['promotions']['count'] == population // 5 and not PublicationDirty.objects.exists()
        proof['complete_geography'] = True
        proof['dataset'] = dataset
        manager = User.objects.get(username='fixture-v1-individual')
        drafts = [Revision.objects.create(listing=manager.individual_person.listing,
                                         manager_version=manager.individual_person.manager_version)
                  for _ in range(upload_count)]
        publication_state.refresh_all()
        browser = Client()
        browser.force_login(manager)
        broker.flushdb()  # Explicit refresh supersedes synthetic setup messages.
        assert broker.dbsize() == 0
        settings.CELERY_TASK_ALWAYS_EAGER = False
        backlog_plan = None
        route_geography = dataset['geography']
        committed_plan = None
        if committed:
            from capacity_committed_mixed import prepare as prepare_committed

            committed_plan = prepare_committed(dataset)
            route_geography = committed_plan['route_geography']
            proof['committed_mixed'] = {
                'population': population, 'visible_after': population-14,
                'active_sponsorships': len(committed_plan['sponsorships']),
                'route_geography': route_geography, 'counterfactual_rollback_used': False,
                'manual_refresh_before_server': True, 'statistics_after_mutation': True,
                'excluded': [str(v['id']) for v in committed_plan['mutations']],
                'inactive_profiles': list(map(str, committed_plan['inactive_profiles'])),
                'protected_details': [dataset['sample_ids'][0], dataset['sample_ids'][-1]],
            }
        if mixed:
            from capacity_mixed_backlog import prepare_backlog as prepare_mixed_backlog

            backlog_plan = prepare_mixed_backlog(dataset)
            route_geography = backlog_plan['route_geography']
            proof['route_geography'] = route_geography
            proof['route_geography_scope'] = 'Counterfactual native post-mutation census; fresh full boundaries remain in independent page oracle'
        routes = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
                  '/es/listing/' + dataset['sample_ids'][0] + '/',
                  '/en/listing/' + dataset['sample_ids'][-1] + '/']
        if territorial:
            from scripts.benchmark_territorial_routes import balanced_territorial_cycle

            routes = balanced_territorial_cycle(route_geography, routes)
        if combined:
            from capacity_combined_filters import plan

            combined_plan, routes = plan(dataset, routes[4:6])
        proof['routes'] = routes
        proof['mix'] = {'listing': '1/3', 'search': '1/3', 'detail': '1/3',
                        'languages': 'ES/EN alternating'}
        with server(settings, record_property) as endpoint:
            assert len(endpoint.beta_worker_pids) == 4
            proof['four_workers'] = True
            phase_signal = None
            if getattr(settings, 'CAPACITY_RESOURCE_RUN_ID', None) and not backlog and not committed:
                from scripts.benchmark_capacity_phase import CapacityPhaseWriter

                phase_signal = CapacityPhaseWriter(settings.CAPACITY_RESOURCE_RUN_ID)
            cold = []
            for path in routes:
                with urllib.request.urlopen(endpoint.url + path, timeout=65) as response:
                    body = response.read()
                    assert response.status == 200 and response.headers['Cache-Control'] == 'no-store'
                    cold.append({'status': response.status, 'bytes': len(body)})
                    if path in routes[:2] and not combined:
                        assert b'Patrocinado' in body or b'Sponsored' in body
            proof['cold_probes'] = cold
            if combined:
                from capacity_combined_filters import verify

                proof['combined_filters']['before'] = verify(endpoint, dataset, combined_plan)
            cookies = http.cookies.SimpleCookie()
            with urllib.request.urlopen(endpoint.url + '/es/account/login/', timeout=65) as response:
                for value in response.headers.get_all('Set-Cookie', []):
                    cookies.load(value)
            csrf = cookies[settings.CSRF_COOKIE_NAME].value
            cookie = (f'{settings.SESSION_COOKIE_NAME}={browser.cookies[settings.SESSION_COOKIE_NAME].value}; '
                      f'{settings.CSRF_COOKIE_NAME}={csrf}')
            boundary = 'synthetic-' + uuid4().hex
            payload = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; '
                       'filename="synthetic.jpg"\r\nContent-Type: image/jpeg\r\n\r\n').encode()
            payload += raw_image(782134) + f'\r\n--{boundary}--\r\n'.encode()
            uploads = [{'at': minute * upload_interval, 'path': f'/es/draft/{draft.pk}/photos/upload/', 'data': payload,
                      'headers': {'Cookie': cookie, 'X-CSRFToken': csrf, 'Referer': endpoint.url + '/es/',
                                  'Content-Type': 'multipart/form-data; boundary=' + boundary}, 'expected': 302}
                       for minute, draft in enumerate(drafts)]

            async def fetch(path, **kwargs):
                return await fetch_http(endpoint.url, path,
                                        timeout_seconds=POLICY['request_timeout_seconds'], **kwargs)

            if committed:
                from capacity_committed_mixed import verify as verify_committed

                proof['committed_mixed']['before'] = verify_committed(endpoint, dataset, committed_plan)
                proof['committed_mixed']['preparation_finished_monotonic'] = time.monotonic()
                proof['resource_preparation_excluded'] = {
                    'started_monotonic': preparation_started,
                    'finished_monotonic': proof['committed_mixed']['preparation_finished_monotonic'],
                    'scope': 'Committed fixture, native oracle, refresh, statistics and cold probes outside capture; '
                             'no resource attribution for that preparation. Final native oracle follows idle_after.',
                }
                if getattr(settings, 'CAPACITY_RESOURCE_RUN_ID', None):
                    from scripts.benchmark_capacity_phase import CapacityPhaseWriter

                    phase_signal = CapacityPhaseWriter(settings.CAPACITY_RESOURCE_RUN_ID)
            tick_floor = -1
            if backlog:
                if mixed:
                    from capacity_mixed_backlog import (
                        create_backlog,
                        prepare_backlog,
                        verify_pages,
                        verify_pending,
                        verify_repaired,
                    )
                else:
                    from capacity_backlog import (
                        create_backlog,
                        prepare_backlog,
                        verify_pages,
                        verify_pending,
                        verify_repaired,
                    )
                from capacity_backlog import events as backlog_events

                proof['backlog'] = {'fresh_pages': verify_pages(endpoint, dataset)}
                if not mixed:
                    backlog_plan = prepare_backlog(dataset)
                proof['backlog']['preparation_finished_monotonic'] = time.monotonic()
                # Capture the unchanged workload, not the expensive native preparation.
                # Keep cold probes and both independent oracles; disclose the excluded span.
                from scripts.benchmark_capacity_phase import CapacityPhaseWriter

                phase_signal = CapacityPhaseWriter(settings.CAPACITY_RESOURCE_RUN_ID)
                proof['resource_preparation_excluded'] = {
                    'started_monotonic': preparation_started,
                    'finished_monotonic': proof['backlog']['preparation_finished_monotonic'],
                    'scope': 'Backlog only: fixture/native setup, cold probes, fresh page oracle '
                             'and mutation plan precede host resource capture; no resource '
                             'attribution for that excluded preparation. Independent repaired '
                             'oracle follows idle_after and is outside capture too.',
                }
                tick_floor = time.monotonic()
            until = time.monotonic() + 45
            while not (ticks := [tick for tick in beat_refresh_publishes(endpoint.celery_events) if tick > tick_floor]):
                assert time.monotonic() < until, 'No owned Beat refresh observed'
                time.sleep(.2)
            target = ticks[-1] + BEAT_PHASE_SECONDS
            while target < time.monotonic() + 1:
                target += 30
            if backlog:
                # Wait for this real tick's empty refresh to finish before bulk marks.
                from scripts.benchmark_refresh_intervals import refresh_intervals

                while not any(row['publisher_role'] == 'beat' and row['state'] == 'SUCCESS'
                              and row['published_monotonic'] == ticks[-1]
                              for row in refresh_intervals(backlog_events(endpoint.celery_events))['matched']):
                    assert time.monotonic() < target - 2, 'Fresh Beat refresh did not finish in preparation slot'
                    time.sleep(.05)
                proof['backlog'].update(create_backlog(dataset, backlog_plan))
                proof['backlog']['mutation_finished_monotonic'] = time.monotonic()
                verify_pending(endpoint, dataset, proof['backlog'], backlog_plan)
                assert time.monotonic() < target, 'Backlog probes exceeded preregistered Beat preparation slot'
            proof['beat_alignment'] = {'observed_tick_monotonic': ticks[-1],
                                       'load_start_target': target, 'phase_seconds': BEAT_PHASE_SECONDS}
            time.sleep(target - time.monotonic())
            proof['dirty_before_load'] = PublicationDirty.objects.count()
            proof['client_gc_preparation'] = prepare_generator_gc()
            assert proof['client_gc_preparation']['policy_before'] == proof['client_gc_preparation']['policy_after']
            assert not proof['client_gc_preparation']['frozen_after_collect']
            if phase_signal:
                phase_signal.advance('arrivals_and_drain')
            with GCObserver(monotonic_clock=time.monotonic) as gc_observer:
                if generator_diagnostic:
                    from capacity_combined_filters import observe_generator

                    result = observe_generator(fetch, routes, proof=proof, duration=duration, rps=20,
                                               upload_specs=uploads)
                else:
                    result = run_async_open_loop(fetch, routes, duration=duration, rps=20,
                                                 upload_specs=uploads, trace_scheduler=backlog or combined)
            if phase_signal:
                proof['resource_phase_signal'] = phase_signal.advance('idle_after')
                time.sleep(2)  # Functional observer gets a terminal sample before cleanup.
            proof['client_gc'] = gc_observer.report()
            assert proof['client_gc_preparation']['completed_at_monotonic'] <= result['monotonic_origin_seconds']
            assert proof['client_gc']['policy_before'] == proof['client_gc']['policy_after']
            assert proof['client_gc']['unfinished_events'] == 0
            assert result['counts']['scheduled'] == duration * 20
            proof['all_dynamic_successful'] = result['counts']['successful'] == duration * 20
            proof['outcome'] = result
            if backlog:
                verify_repaired(endpoint, dataset, proof['backlog'], endpoint.celery_events)
            if combined:
                proof['combined_filters']['after'] = verify(endpoint, dataset, combined_plan)
                assert proof['combined_filters']['before'] == proof['combined_filters']['after']
            if committed:
                proof['committed_mixed']['after'] = verify_committed(endpoint, dataset, committed_plan)
                assert proof['committed_mixed']['before'] == proof['committed_mixed']['after']
            assert all(Photo.objects.filter(revision=draft).count() == 1 for draft in drafts)
            assert all(UploadAttempt.objects.filter(revision=draft, user=manager,
                                                   result__in=(['accepted', 'duplicate'] if contractual or upload_calibration
                                                               else ['accepted', 'duplicate', 'repeat'])).count() == 1
                       for draft in drafts)
            proof['upload_persisted'] = True
            if short or contractual:
                checks = {
                    'validity': result['verdict'] != 'INVALID',
                    'latency_and_errors': result['verdict'] == 'PASS',
                    'emitted': result['counts']['emitted'] == duration * 20 and result['counts']['not_emitted'] == 0,
                    'window_pending': result['window_close']['dynamic']['pending'] <= 20,
                    'final_pending': result['counts']['pending'] == 0,
                    'accounting': result['counts']['reconciled'] and result['final_upload_counts']['reconciled'],
                    'upload': result['final_upload_counts']['successful'] == upload_count,
                    'timeout_policy': result['policy']['request_timeout_seconds'] == 65,
                    'drain': result['actual_elapsed_seconds'] <= duration + 70,
                }
                proof['workload_checks' if contractual else 'short_checks'] = checks
                proof['transport_verdict'] = result['verdict']
                proof['verdict'] = ('INVALID' if result['verdict'] == 'INVALID'
                                    else 'PASS' if all(checks.values()) else 'FAIL')
                assert proof['verdict'] == 'PASS', checks
            else:
                assert proof['all_dynamic_successful']
                assert all(result['counts'][key] == 0 for key in ('failed', 'pending', 'not_emitted'))
                assert result['counts']['reconciled'] and result['verdict'] != 'INVALID'
                assert result['final_upload_counts']['successful'] == upload_count
                assert result['final_upload_counts']['reconciled']
    finally:
        if broker is not None:
            broker.flushdb()
            proof['broker_empty_after'] = broker.dbsize() == 0
        events = Path('/tmp/capacity-beta-celery')
        proof['celery_events'] = [json.loads(line) for path in events.glob('*.jsonl')
                                 for line in path.read_text().splitlines()] if events.exists() else []
        record_property('beta_http_contractual' if contractual else 'beta_http_short' if short else 'beta_http_calibration', json.dumps(proof))
