"""Synthetic stack gates; no monkeypatch of the interpreter's global sys."""

import sys
import weakref
from types import ModuleType, SimpleNamespace

import pytest

from apps.safety import fast_canonical as canonical


class Frame:
    def __init__(self, back, accesses):
        self.back = back
        self.accesses = accesses

    @property
    def f_back(self):
        self.accesses.append(1)
        return self.back


def install(monkeypatch, *, limit, length):
    accesses, roots, references, calls = [], [], [], []

    def getframe():
        roots.append(1)
        frame = None
        for _ in range(length):
            frame = Frame(frame, accesses)
            references.append(weakref.ref(frame))
        return frame

    monkeypatch.setattr(canonical, 'sys', SimpleNamespace(
        _getframe=getframe, getrecursionlimit=lambda: limit))
    loader = ModuleType('apps.safety.canonical_kernel_loader')

    def kernel(value, depth=0):
        return None

    def try_check(value, depth=0):
        calls.append('kernel')
        return True

    kernel.try_check = try_check

    def validated_kernel():
        calls.append('loader')
        return kernel

    loader.validated_kernel = validated_kernel
    monkeypatch.setitem(sys.modules, loader.__name__, loader)
    return accesses, roots, references, calls, loader


@pytest.mark.parametrize('limit,length', [
    (511, 100), (512, 100), (513, 1), (513, 2),
    (515, 2), (515, 3), (515, 100), (1000, 20),
])
def test_gate_matches_original_criterion_and_bounds_walk(monkeypatch, limit, length):
    accesses, roots, references, calls, loader = install(monkeypatch, limit=limit, length=length)
    canonical._check(None)
    eligible_original = limit - length > 512
    assert bool(calls) is eligible_original
    threshold = limit - 512
    assert len(roots) == (1 if threshold > 0 else 0)
    # Equality already proves fallback; the threshold-th frame's f_back need
    # never be fetched. Below threshold, traverse to None to establish length.
    expected_accesses = 0 if threshold <= 0 else min(length, threshold - 1)
    assert len(accesses) == expected_accesses
    assert all(reference() is None for reference in references)


def test_frame_not_retained_in_argument_error_traceback(monkeypatch):
    accesses, roots, references, calls, loader = install(monkeypatch, limit=515, length=100)
    with pytest.raises(TypeError, match='explicit JSON values') as captured:
        canonical._check(object())
    traceback = captured.value.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code is canonical._check.__code__:
            assert traceback.tb_frame.f_locals['frame'] is None
        traceback = traceback.tb_next
    assert all(reference() is None for reference in references)
    assert not calls


def test_eligible_loader_integrity_error_preserved_and_frames_released(monkeypatch):
    accesses, roots, references, calls, loader = install(monkeypatch, limit=1000, length=2)
    error = RuntimeError('integrity mismatch')

    def broken():
        raise error

    loader.validated_kernel = broken
    with pytest.raises(RuntimeError) as captured:
        canonical._check(None)
    assert captured.value is error
    assert all(reference() is None for reference in references)


def test_nonzero_depth_does_not_walk_or_dispatch(monkeypatch):
    accesses, roots, references, calls, loader = install(monkeypatch, limit=1000, length=2)
    canonical._check(None, 1)
    assert not accesses and not roots and not references and not calls


def test_f_back_error_does_not_retain_current_frame(monkeypatch):
    error = RuntimeError('synthetic stack accessor')
    references = []

    class BrokenFrame:
        @property
        def f_back(self):
            raise error

    def getframe():
        frame = BrokenFrame()
        references.append(weakref.ref(frame))
        return frame

    monkeypatch.setattr(canonical, 'sys', SimpleNamespace(
        _getframe=getframe, getrecursionlimit=lambda: 1000))
    with pytest.raises(RuntimeError) as captured:
        canonical._check(None)
    assert captured.value is error
    # The accessor traceback itself retains self; _check must not add retention.
    traceback = captured.value.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code is canonical._check.__code__:
            assert traceback.tb_frame.f_locals['frame'] is None
        traceback = traceback.tb_next
