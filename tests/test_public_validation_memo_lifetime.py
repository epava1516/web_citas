"""Request-local field memoization must not add an owner reference cycle."""

import gc
import weakref

from django import forms

from apps.listings.public_validation import memoize_publication_field_clean


def test_successful_field_memo_does_not_retain_its_owner_until_cyclic_gc():
    enabled = gc.isenabled()
    gc.disable()  # Deterministic lifetime assertion in this unit process only.
    try:
        native = forms.CharField()
        native_ref = weakref.ref(native)
        assert native.clean('synthetic') == 'synthetic'
        del native
        assert native_ref() is None

        field = forms.CharField()
        reference = weakref.ref(field)
        stats = dict(calls=0, hits=0, misses=0)
        memoize_publication_field_clean(field, stats)
        assert field.clean('synthetic') == field.clean('synthetic') == 'synthetic'
        assert stats == dict(calls=2, hits=1, misses=1)
        del field
        assert reference() is None, 'Memoizer adds field → closure → bound method → field cycle'
    finally:
        if enabled:
            gc.enable()
        gc.collect()


def test_unknown_callable_keeps_native_validation_without_memoization():
    field = forms.CharField()
    native = lambda value: value.upper()  # noqa: E731
    field.clean = native
    stats = dict(calls=0, hits=0, misses=0)
    memoize_publication_field_clean(field, stats)
    assert field.clean is native and field.clean('synthetic') == 'SYNTHETIC'
    assert stats == dict(calls=0, hits=0, misses=0)
