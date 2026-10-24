"""Explicit synthetic20percent Top/Premium preparation, outside HTTP timing."""

import json
import os
from collections import Counter
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Count
from django.utils import timezone

from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.listings.models import Listing
from scripts.synthetic_load_dataset import populate


@transaction.atomic
def redistribute_promotional_geography(dataset, allocations):
    """Explicit synthetic preparation, never a nationally representative sample."""
    from apps.catalog.models import Municipality
    from apps.listings.models import Revision

    if (settings.PRODUCTION or settings.RECOVERY_MODE or not settings.PROMOTION_TEST_MODE
            or connection.vendor != 'postgresql'
            or not connection.settings_dict['NAME'].startswith('test_promotion_gate_')
            or not dataset.get('synthetic')
            or not dataset.get('promotions', {}).get('synthetic_only')):
        raise ValueError('Geography preparation requires a synthetic PostgreSQL test cohort')
    if (not isinstance(allocations, dict) or not 2 <= len(allocations) <= 32
            or any(type(k) is not int or type(v) is not int or k <= 0 or v <= 0
                   for k, v in allocations.items())
            or sum(allocations.values()) != dataset.get('published')):
        raise ValueError('Explicit positive municipality counts must cover the complete cohort')
    cities = Municipality.objects.filter(pk__in=allocations, active=True, source__synthetic=True)
    if cities.count() != len(allocations):
        raise ValueError('Every target municipality must be active and synthetic')
    revisions = list(Listing.objects.filter(status='published').order_by('pk')
                     .values_list('approved_revision_id', flat=True))
    if len(revisions) != dataset['published'] or len(set(revisions)) != len(revisions) or None in revisions:
        raise ValueError('Complete distinct approved revision cohort required')
    offset = 0
    for city, count in sorted(allocations.items()):
        Revision.objects.filter(pk__in=revisions[offset:offset + count]).update(
            municipality_id=city, postal_code=None, zone=None)
        offset += count
    census = {str(row['approved_revision__municipality_id']): row['total']
              for row in Listing.objects.filter(status='published')
              .values('approved_revision__municipality_id').annotate(total=Count('pk'))}
    if census != {str(k): v for k, v in allocations.items()}:
        raise ValueError('Post-mutation geography census mismatch')
    return dataset | {'geography': census,
                      'limits': dataset['limits'].replace('agency/photo/geography', 'agency/photo'),
                      'geography_distribution': 'Explicit synthetic municipality counts; not national representation',
                      'publication_refresh_required_after_geography': True}


def prepare_promotional_load(request, count):
    assert not settings.PRODUCTION and settings.PROMOTION_TEST_MODE and not settings.RECOVERY_MODE
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    request.getfixturevalue("directory")
    top = PromotionProductVersion.objects.create(
        product=PromotionProduct.objects.create(slug="beta_http_top", kind="top"),
        version=1, name_es="Prueba", name_en="Test", duration_days=10,
        amount=Decimal("12.00"), currency="EUR", tax_rate=Decimal("20"),
        published_at=timezone.now(), is_current=True,
    )
    dataset = populate(count)
    premium = PromotionProductVersion.objects.create(
        product=PromotionProduct.objects.create(slug="beta_http_premium", kind="premium"),
        version=1, name_es="Prueba", name_en="Test", duration_days=top.duration_days,
        amount=top.amount, currency=top.currency, tax_rate=top.tax_rate,
        published_at=timezone.now(), is_current=True,
    )
    rows = list(Listing.objects.filter(status="published", person__agency__isnull=False)
                .select_related("person__agency__owner", "approved_revision").order_by("pk"))
    promoted = rows[:count // 5]
    assert len(promoted) == count // 5 and promoted
    for index, listing in enumerate(promoted):
        buyer = listing.person.agency.owner
        buyer.mfa_enabled = True
        buyer.save(update_fields=["mfa_enabled"])
        credentials = {"mfa_version": buyer.mfa_version, "account_version": buyer.session_version}
        order = create_order(buyer, listing.pk, (premium if index % 3 == 0 else top).pk,
                             uuid4(), **credentials)
        payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid4())
        receive_event(buyer, payload, signature, **credentials)
    dataset["promotions"] = {
        "synthetic_only": True, "count": len(promoted), "share_of_published": 0.2,
        "premium": sum(index % 3 == 0 for index in range(len(promoted))),
        "top": sum(index % 3 != 0 for index in range(len(promoted))),
        "issuance": "Actual create_order and signed synthetic_event/receive_event services before timing",
        "autobump_rights": 0, "real_payments": False,
    }
    # The load population also contains an individual publication; the agency
    # selection above is only the commercial issuance cohort, not the census.
    dataset["geography"] = {
        str(row["approved_revision__municipality_id"]): row["published_count"]
        for row in Listing.objects.filter(status="published")
        .values("approved_revision__municipality_id")
        .annotate(published_count=Count("pk"))
    }
    dataset["geography_scope"] = "All published listings, including individual and agency profiles"
    assert sum(dataset["geography"].values()) == dataset["published"]
    dataset["limits"] += " Promotional cohort shares agency/photo/geography; no national distribution or real providers."
    return dataset


def reset_preparation_broker(phase):
    """Owned single-run preparation only; no message bodies/names or execution credit."""
    assert phase in {"before_directory_bootstrap", "after_explicit_publication_refresh"}
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    from test_worker_capacity_comparison import owned_redis

    broker = owned_redis()  # Checks run identity, Docker label, localhost port and DB0.
    entries = [(key, broker.type(key)) for key in broker.scan_iter(count=1000)]
    state = {
        "phase": phase, "keys_removed": len(entries),
        "key_types": dict(Counter(kind.decode("ascii") for _, kind in entries)),
        "list_elements_observed": sum(broker.llen(key) for key, kind in entries if kind == b"list"),
        "owned_instance_verified": True, "before_runtime_processes": True,
        "after_explicit_state_refresh": phase == "after_explicit_publication_refresh",
        "scope": "Owned synthetic setup only; keys/list elements are not task execution credit",
    }
    if entries:
        broker.delete(*(key for key, _ in entries))
    assert broker.dbsize() == 0, "Owned preparation reset must leave an empty runtime broker"
    state["empty_after_reset"] = True
    folder = settings.BASE_DIR / "artifacts" / "local-ci" / os.environ["LOCAL_CI_BENCHMARK_RUN"]
    assert folder.is_dir()
    with (folder / "benchmark-preparation-broker.jsonl").open("a") as stream:
        stream.write(json.dumps(state, ensure_ascii=False) + "\n")
    return state


def finalize_promotional_statistics(dataset):
    """Finish planner preparation only in this runner's disposable synthetic DB."""
    import re
    import subprocess
    import time

    from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
    from apps.core.models import Person, RepresentationAction, User, VerificationCheck
    from apps.listings.models import PublicationDirty, PublicationState, Revision
    from apps.listings.publication_state import all_state_current

    if (getattr(settings, 'CAPACITY_BETA_HTTP_FUNCTIONAL', False)
            or getattr(settings, 'CAPACITY_BETA_HTTP_SHORT', False)
            or getattr(settings, 'CAPACITY_BETA_HTTP_CONTRACTUAL', False)):
        from capacity_beta_http import verify_owned_fixture

        verify_owned_fixture()
    else:
        run = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN') or os.environ.get('LOCAL_CI_BENCHMARK_RUN', '')
        database = connection.settings_dict
        if (settings.PRODUCTION or settings.RECOVERY_MODE or not settings.PROMOTION_TEST_MODE
                or connection.in_atomic_block or not connection.get_autocommit() or not re.fullmatch(r'\d{8}-\d{6}-[0-9a-f]{8}', run)
                or database['ENGINE'] != 'django.db.backends.postgresql'
                or not database['NAME'].startswith('test_promotion_gate_')
                or database['USER'] != 'ci' or database['HOST'] != '127.0.0.1'):
            raise ValueError('Promotional statistics require disposable runner autocommit database')
        name = os.environ.get('LOCAL_CI_POSTGRES_CONTAINER', '')
        if name != 'web-modelos-ci-pg-' + run:
            raise ValueError('Promotional statistics require the exact owned PostgreSQL container')
        inspection = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))
        if (len(inspection) != 1 or inspection[0]['Name'] != '/' + name
                or inspection[0]['Config']['Labels'].get('web-modelos-local-ci-run') != run
                or not inspection[0]['State']['Running']
                or inspection[0]['NetworkSettings']['Ports'].get('5432/tcp') != [
                    {'HostIp': database['HOST'], 'HostPort': str(database['PORT'])}]):
            raise ValueError('Promotional statistics PostgreSQL ownership or port mismatch')
    if (not dataset.get('synthetic') or not dataset.get('promotions', {}).get('synthetic_only')
            or Listing.objects.filter(status='published').count() != dataset.get('published')
            or PromotionEntitlement.objects.count() != dataset.get('promotions', {}).get('count')):
        raise ValueError('Promotional statistics require the declared complete synthetic cohort')
    if PublicationDirty.objects.exists() or not all_state_current():
        raise ValueError('Promotional statistics require clean and current publication state')
    models = [User, Person, RepresentationAction, VerificationCheck, PromotionOrder,
              PromotionEntitlement, PublicationState, Revision.categories.through]
    tables = sorted(model._meta.db_table for model in models)
    started = time.perf_counter()
    for table in tables:
        with connection.cursor() as cursor:
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    return {'method': 'Explicit ANALYZE after promotional issuance and publication refresh',
            'tables': tables, 'seconds': time.perf_counter() - started,
            'owned_synthetic_postgresql_verified': True,
            'domain_rows_mutated': False, 'request_policy_changed': False}
