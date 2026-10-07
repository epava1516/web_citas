"""Single owned population: change description and Telegram axes separately."""
import copy
import hashlib
import json
import time

import pytest
from django.apps import apps
from django.db.models.signals import post_init
from django.forms import models as model_forms
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha, targets

from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.benchmark_call_profile import CallProfile
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def fixed_population():
    """Hashes only; never export identities, values or content from synthetic rows."""
    result = {}
    for model in apps.get_models():
        if model._meta.app_label not in {'listings', 'core', 'catalog', 'mediafiles'}:
            continue
        fields = [field.attname for field in model._meta.concrete_fields
                  if not (model is Revision and field.name in
                          {'description', 'description_alternative', 'telegram'})]
        rows = model.objects.order_by('pk').values_list(*fields)
        digest = hashlib.sha256()
        count = 0
        for row in rows.iterator():
            digest.update(json.dumps(row, default=str, ensure_ascii=True).encode())
            digest.update(b'\n')
            count += 1
        result[model._meta.label] = {'rows': count, 'fixed_fields_sha256': digest.hexdigest()}
    return result


def test_projection_controlled_content_axes(request, record_property):
    client = request.getfixturevalue('directory')
    populate(10000)
    assert projection.supported()
    rows = list(Revision.objects.filter(status='approved').order_by('pk'))
    originals = [(row.description, row.description_alternative, row.telegram) for row in rows]
    fixed = fixed_population()
    reports = []
    for descriptions_unique, contacts_unique in [(False, False), (True, False),
                                                 (False, True), (True, True)]:
        for index, (row, original) in enumerate(zip(rows, originals, strict=True)):
            row.description, row.description_alternative, row.telegram = original
            suffix = alpha(index)
            if descriptions_unique:
                row.description += ' ' + suffix
                if row.description_alternative:
                    row.description_alternative += ' ' + suffix
            if contacts_unique:
                row.telegram = 'bench' + suffix
        Revision.objects.bulk_update(rows, ['description', 'description_alternative', 'telegram'])
        assert fixed_population() == fixed
        start = time.perf_counter()
        control = client.get('/es/')
        control_seconds = time.perf_counter() - start
        assert control.status_code == 200
        assert control.context['page'].paginator.count == 10000
        observer = CallProfile(targets() + [copy.deepcopy, model_forms.model_to_dict,
                                           model_forms.construct_instance])
        post_init.connect(observer.objects, weak=False)
        try:
            start = time.perf_counter()
            with observer:
                measured = client.get('/es/')
            elapsed = time.perf_counter() - start
        finally:
            post_init.disconnect(observer.objects)
        assert measured.content == control.content
        assert measured.wsgi_request._publication_route == control.wsgi_request._publication_route
        assert observer.projection_stats[0]['positive'] == 10000
        assert observer.projection_stats[0]['native_fallback'] == 0
        rules = observer.report()
        for rule in rules:
            rule['instrumented_children'] = dict(rule['instrumented_children'])
        reports.append({'descriptions_unique': descriptions_unique, 'contacts_unique': contacts_unique,
                        'description_pairs': len({(r.description, r.description_alternative) for r in rows}),
                        'telegram_values': len({r.telegram for r in rows}),
                        'request_seconds': elapsed, 'control_request_seconds': control_seconds,
                        'route': measured.wsgi_request._publication_route,
                        'projection_stats': observer.projection_stats,
                        'materialized': dict(observer.materialized), 'rules': rules})
    record_property('controlled_content_profile', {
        'fixed_population': fixed, 'reports': reports,
        'scope': 'One PG population10000; only descriptions/alternative descriptions and Telegram change. All other concrete fields/counts of listings/core/catalog/mediafiles hashed before and after each variant. Controls precede profiler; one sample, warmed caches, no causal overhead estimate. Nonwrapping synchronous sys.setprofile including deepcopy/model_to_dict/construct_instance; exclusive discounts direct observed children once, unobserved SQL/lazy work remains inside parent. Same body/route/count for control versus profile, not native eligibility equivalence or capacity gate.',
        'not_measured': 'SQL time/normalized SQL; DB CPU; SQL rows; native full-population equivalence; causal overhead; worker queue; concurrent capacity',
    })
