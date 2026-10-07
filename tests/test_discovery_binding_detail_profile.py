"""Finite 10k attribution of native bindings/model metadata with GC overlap."""

import pytest
from django.forms import models as form_models
from django.forms.boundfield import BoundField
from django.forms.forms import BaseForm
from test_discovery import directory  # noqa: F401
from test_discovery_gc_profile import test_discovery_gc_profile_10000 as run_gc_profile
from test_photos import photo_environment  # noqa: F401

from apps.listings.forms import ContactsForm
from apps.listings.models import Revision
from apps.listings.public_validation import SnapshotDetails
from scripts.benchmark_rule_profile import RuleProfile

pytestmark = pytest.mark.django_db(transaction=True)


def test_discovery_binding_detail_profile_10000(request, monkeypatch, record_property):
    profiles = []
    original_init = RuleProfile.__init__
    targets = [(BoundField, "__init__"), (BaseForm, "_widget_data_value"),
               (form_models, "construct_instance")]
    for cls in [SnapshotDetails, ContactsForm]:
        targets.append((cls, "_get_validation_exclusions"))
    for name in ["full_clean", "clean_fields", "clean", "validate_unique",
                 "validate_constraints", "_get_unique_checks", "_perform_unique_checks",
                 "_perform_date_checks", "get_constraints"]:
        targets.append((Revision, name))

    def initialized(profile, *args, **kwargs):
        original_init(profile, *args, **kwargs)
        profiles.append(profile)
        for owner, name in targets:
            label = f"{owner.__name__}.{name}"
            monkeypatch.setattr(owner, name, profile.wrap(label, getattr(owner, name)))

    monkeypatch.setattr(RuleProfile, "__init__", initialized)
    run_gc_profile(request, monkeypatch, record_property)
    assert len(profiles) == 1
    rows = {row["rule"]: row for row in profiles[0].report()}
    assert rows["Revision.full_clean"]["calls"] == 20000
    assert rows["Revision.clean_fields"]["calls"] == 20000
    assert rows["BoundField.__init__"]["calls"] > 0
    assert rows["BaseForm._widget_data_value"]["calls"] >= 20000
    for row in rows.values():
        assert abs(row["inclusive_time"] - row["exclusive_time"]
                   - sum(row["instrumented_children"].values())) < 1e-7
        assert abs(row["inclusive_thread_cpu_time"] - row["exclusive_thread_cpu_time"]
                   - sum(row["instrumented_children_thread_cpu"].values())) < 1e-7
    record_property("binding_diagnostic_targets", [f"{owner.__name__}.{name}" for owner, name in targets])
    record_property("binding_diagnostic_scope", "Original 10k control/rule/GC protocol plus native BoundField construction, widget data extraction, model-form exclusions, construct_instance and model cleaning/metadata. No cProfile, arguments, SQL parameters or validation replacements. Child scopes are broader than prior rule profiles: parent exclusive times cannot be compared directly with those narrower reports. Direct children discounted once, not grandchildren; GC intervals overlap rules and are neither added nor discounted again. Native bound-field calls include forms rendered on the route, not only publication validation. Control response/context retained and wrappers add overhead: causal overhead not_measured; wall/thread CPU are synchronous request only, not concurrent capacity or DB CPU.")
