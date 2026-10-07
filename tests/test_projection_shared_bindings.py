"""Independent content bindings and demand-driven materialization with native oracle."""
from collections import Counter

import pytest
from django.db.models.signals import post_init
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids
from test_projection_cost_cycle import alpha

from apps.listings import projected_publication as projection
from apps.listings import public_validation
from apps.listings.discovery import candidates
from apps.listings.models import Rate, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_repeated_content_does_not_construct_models_before_a_real_validation(request, record_property):
    request.getfixturevalue('directory')
    populate(100)
    assert projection.supported()
    expected = native_ids(candidates({}))
    constructed = Counter()

    def observe(sender, **kwargs):
        if sender in (Revision, Rate):
            constructed[sender.__name__] += 1

    post_init.connect(observe, weak=False)
    try:
        context = projection.ProjectedPublication(candidates({}))
        observed = context.visible_ids(candidates({}))
    finally:
        post_init.disconnect(observe)
    assert observed == expected and len(observed) == 100
    assert context.stats['native_fallback'] == 0
    # This bound detects the demonstrated eager-per-candidate mechanism; it is
    # not a SQL rows metric or an exact constructor implementation assertion.
    assert constructed['Revision'] < 10 and constructed['Rate'] < 10
    record_property('demand_materialization', {'candidates': 100,
        'constructed_objects': dict(constructed), 'stats': context.stats,
        'scope': 'Projection scalar snapshot/validation only, before page hydration; signal constructions are not SQL rows.'})


def test_unique_bindings_and_out_of_page_invalid_content_preserve_population(request, record_property):
    client = request.getfixturevalue('directory')
    populate(50)
    ordered = list(candidates({}).values_list('approved_revision_id', flat=True))
    for index, pk in enumerate(ordered):
        Revision.objects.filter(pk=pk).update(
            description='Synthetic professional photography content ' + alpha(index),
            telegram='bench' + alpha(index))
    # A rejected binding precedes subsequent valid bindings and is outside the
    # first24: errors must not poison the shared prototype or a later instance.
    Revision.objects.filter(pk=ordered[25]).update(telegram='a')
    expected = native_ids(candidates({}))
    assert len(expected) == 49
    assert projection.supported()
    constructed = Counter()
    def observe(sender, **kwargs):
        if sender is Revision:
            constructed["Revision"] += 1
    post_init.connect(observe, weak=False)
    try:
        context = projection.ProjectedPublication(candidates({}))
        assert context.visible_ids(candidates({})) == expected
    finally:
        post_init.disconnect(observe)
    assert constructed["Revision"] < 10
    assert context.stats['native_fallback'] == 1
    shared = context.field_clean_cache_stats
    assert shared and sum(stats['hits'] for stats in shared.values()) > 0
    assert all(stats['calls'] == stats['hits'] + stats['misses'] for stats in shared.values())
    assert all(form._errors is None and not hasattr(form, 'cleaned_data')
               for form in context.validation_prototypes.values())
    for language in ['es', 'en']:
        for number in [1, 2, 3]:
            response = client.get(f'/{language}/', {'page': number})
            assert response.status_code == 200
            assert response.context['page'].paginator.count == 49
            assert [row.pk for row in response.context['page']] == expected[(number-1)*24:number*24]
    record_property('independent_unique_bindings', {'count': 49, 'invalid_original_position': 25,
        'ordered_population_equal': True, 'pages_ES_EN': [1, 2, 3],
        'stats': context.stats, 'prototype_errors_cleaned_data_absent': True})


def test_shared_binding_helper_is_part_of_the_rule_footprint(monkeypatch):
    assert projection.supported()
    before = projection.definitions_digest()
    monkeypatch.setattr(public_validation, 'validate_publication_binding', lambda *args: True)
    assert projection.definitions_digest() != before
    assert not projection.supported()
