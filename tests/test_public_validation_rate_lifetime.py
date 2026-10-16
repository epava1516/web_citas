"""Rate validation keeps native rules while releasing private BoundField cycles."""
import gc
import weakref
from decimal import Decimal

import pytest

from apps.listings import public_validation
from apps.listings.forms import RateForm
from apps.listings.models import Rate, Revision

pytestmark = pytest.mark.django_db(transaction=True)


def context():
    value = public_validation.PublicationContext.__new__(public_validation.PublicationContext)
    value.rate_checks = {}
    return value


@pytest.mark.parametrize('values', [
    {'concept':'Synthetic session','mode':'consult','amount':None,'duration_minutes':60},
    {'concept':'Synthetic session','mode':'fixed','amount':Decimal('100.00'),'duration_minutes':60},
    {'concept':'Synthetic session','mode':'fixed','amount':None,'duration_minutes':60},
    {'concept':'https://example.invalid','mode':'consult','amount':None,'duration_minutes':60},
    {'concept':'Synthetic session','mode':'consult','amount':None,'duration_minutes':10081},
])
def test_private_rate_form_matches_native_and_releases_cycle(monkeypatch, values):
    native = RateForm(values, instance=Rate(revision=Revision()))
    expected = native.is_valid()
    assert native._bound_fields_cache
    assert any(field.form is native for field in native._bound_fields_cache.values())
    native._bound_fields_cache.clear()
    del native
    refs = []
    calls = []
    class TrackedRateForm(RateForm):
        def is_valid(self):
            result = super().is_valid()
            assert self._bound_fields_cache
            refs.append(weakref.ref(self))
            calls.append(True)
            return result
    monkeypatch.setattr(public_validation, 'RateForm', TrackedRateForm)
    validator = context()
    enabled = gc.isenabled()
    try:
        gc.disable()
        rate = Rate(revision=Revision(), **values)
        assert validator.rate_valid(rate) is expected
        assert refs[0]() is None, 'Private form retained after returning boolean'
        assert validator.rate_valid(rate) is expected
        assert len(calls)==1
    finally:
        if enabled:
            gc.enable()
        else:
            gc.disable()


def test_private_rate_binding_cleanup_on_exception(monkeypatch):
    retained = []
    class RaisingRateForm(RateForm):
        def is_valid(self):
            list(self)
            assert self._bound_fields_cache
            retained.append(self)
            raise RuntimeError('Synthetic validation failure')
    monkeypatch.setattr(public_validation, 'RateForm', RaisingRateForm)
    validator = context()
    with pytest.raises(RuntimeError, match='Synthetic validation failure'):
        validator.rate_valid(Rate(revision=Revision(), concept='Synthetic', mode='consult'))
    assert retained[0]._bound_fields_cache == {}
    assert validator.rate_checks == {}
