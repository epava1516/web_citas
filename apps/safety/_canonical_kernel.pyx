# cython: language_level=3
"""Strict canonical validator only; caller loads through verified native manifest.

All Python objects stay boxed. GIL stays held; depth bounds precede leaf checks.
Explicit iterators preserve Python mutation/error ordering instead of PyDict_Next.
"""
import math
from types import BuiltinFunctionType

cdef extern from *:
    """
    #include <Python.h>
    static int canonical_python_budget(void) {
    #if PY_VERSION_HEX >= 0x030C0000 && PY_VERSION_HEX < 0x030E0000
        return PyThreadState_Get()->py_recursion_remaining;
    #else
        return 0;
    #endif
    }
    """
    int canonical_python_budget()


cdef bint _pure(object value, int depth) except *:
    cdef object kind, key, item
    if depth > 200:
        return True
    kind = type(value)
    if value is None or kind is str or kind is bool or kind is int or kind is float:
        return True
    if kind is dict:
        for key, item in value.items():
            if type(key) is not str:
                # Builtin invalid keys have no metaclass callbacks either.
                if type(type(key)) is not type:
                    return False
                return True
            if not _pure(item, depth + 1):
                return False
        return True
    if kind is list or kind is tuple:
        for item in value:
            if not _pure(item, depth + 1):
                return False
        return True
    return False


def try_check(value, depth=0):
    # No callbacks or error effects are allowed before declining to Python.
    if type(depth) is not int or depth < 0 or depth > 200:
        return False
    if canonical_python_budget() <= 256:
        return False
    finite = math.isfinite
    if (type(finite) is not BuiltinFunctionType or
            finite.__self__ is not math or finite.__name__ != 'isfinite'):
        return False
    if not _pure(value, depth):
        return False
    _walk(value, depth)
    return True


cdef void _walk(object value, int depth) except *:
    cdef object kind, key, item, iterator
    if depth > 200:
        raise ValueError("Canonical JSON exceeds maximum nesting")
    kind = type(value)
    if value is None or kind in (str, bool, int):
        return
    if kind is float:
        if not math.isfinite(value):
            raise ValueError("Canonical JSON requires finite numbers")
        return
    if kind is dict:
        iterator = iter(value.items())
        for key, item in iterator:
            if type(key) is not str:
                raise TypeError("Canonical JSON requires string keys")
            _walk(item, depth + 1)
        return
    if kind in (list, tuple):
        iterator = iter(value)
        for item in iterator:
            _walk(item, depth + 1)
        return
    raise TypeError("Canonical JSON requires explicit JSON values")


def check(value, depth=0):
    if try_check(value, depth):
        return
    from .fast_canonical import reference_check
    return reference_check(value, depth)


# The verified loader exports this callable, never a raw extension import.
check.try_check = try_check
