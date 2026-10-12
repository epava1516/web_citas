"""Test-only client wall/thread CPU spans; no authority or returned data retained."""
import cProfile
import sys
from contextlib import ExitStack, contextmanager
from functools import wraps
from pathlib import Path
from time import thread_time
from unittest.mock import patch

from tests.capacity_chain_diagnostic import Collector


def observe(function, name, collector):
    @wraps(function)
    def measured(*args, **kwargs):
        with collector.span(name):
            return function(*args, **kwargs)
    measured.__source_diagnostic_original__ = function
    return measured


def iterated(function, collector):
    @wraps(function)
    def measured(*args, **kwargs):
        iterator = iter(function(*args, **kwargs))
        try:
            while True:
                with collector.span('batches_active_next'):
                    try:
                        row = next(iterator)
                    except StopIteration:
                        break
                yield row
        finally:
            iterator.close()
    return measured



def context_observed(function, collector):
    @contextmanager
    @wraps(function)
    def measured(*args, **kwargs):
        manager = function(*args, **kwargs)
        with collector.span('source_context_enter'):
            value = manager.__enter__()
        try:
            yield value
        except BaseException:
            with collector.span('source_context_exit'):
                suppressed = manager.__exit__(*sys.exc_info())
            if not suppressed:
                raise
        else:
            with collector.span('source_context_exit'):
                manager.__exit__(None, None, None)
    measured.__source_diagnostic_original__ = function
    return measured


def profile_report(profile):
    root = Path(__file__).resolve().parents[1]
    rows = []
    for item in profile.getstats():
        code = item.code
        if isinstance(code, str):
            location, name, line = '<native>', code, 0
        else:
            path = Path(code.co_filename)
            location = str(path.relative_to(root)) if path.is_relative_to(root) else '<library>/' + path.name
            name, line = code.co_name, code.co_firstlineno
        rows.append(dict(location=location, name=name, line=line, calls=item.callcount,
                         recursive_calls=item.reccallcount, own_cpu_seconds=item.inlinetime,
                         total_cpu_seconds=item.totaltime))
    return sorted(rows, key=lambda item: item['own_cpu_seconds'], reverse=True)[:100]


@contextmanager
def scope():
    from django.db import connection
    from django.db.models.query import QuerySet
    from django.shortcuts import render

    from apps.safety import (
        evidence_chain,
        fast_canonical,
        rights,
        rights_copy_revision_batches,
        rights_exports,
        rights_inspection_source,
    )

    collector = Collector()
    profile = cProfile.Profile(timer=thread_time)
    targets = [
        (rights_exports.source_copy, 'source_copy'),
        (rights_inspection_source.source_fingerprint, 'source_fingerprint'),
        (fast_canonical.canonical_bytes, 'canonical_bytes'),
        (rights.fingerprint, 'fingerprint'),
        (render, 'render'),
        (evidence_chain.validate_chain, 'validate_chain'),
    ]
    context_wrapper = context_observed(rights_inspection_source.inspection_source, collector)
    targets.append((rights_inspection_source.inspection_source, 'context'))
    aliases = [(module, attr, context_wrapper if name == 'context' else observe(function, name, collector))
               for module_name, module in list(sys.modules.items())
               if module_name.startswith(('apps.', 'django.shortcuts'))
               for attr, value in list(vars(module).items())
               for function, name in targets if value is function]
    original_fetch = QuerySet._fetch_all

    def fetch(queryset):
        model = queryset.model._meta.label
        if model in {'catalog.Category', 'catalog.Service', 'catalog.Municipality', 'listings.Rate', 'mediafiles.Photo'}:
            with collector.span('related_materialize_' + model):
                return original_fetch(queryset)
        return original_fetch(queryset)

    def execute(function, sql, params, many, context):
        with collector.span('sql_execute_driver'):
            return function(sql, params, many, context)

    with ExitStack() as stack:
        for module, attr, function in aliases:
            stack.enter_context(patch.object(module, attr, function))
        stack.enter_context(patch.object(rights_copy_revision_batches, 'batches',
                                        iterated(rights_copy_revision_batches.batches, collector)))
        stack.enter_context(patch.object(rights_inspection_source._InspectionSource, '__init__',
                                        observe(rights_inspection_source._InspectionSource.__init__, 'source_init', collector)))
        stack.enter_context(patch.object(QuerySet, '_fetch_all', fetch))
        stack.enter_context(connection.execute_wrapper(execute))
        profile.enable()
        try:
            yield collector
        finally:
            profile.disable()
            collector.cpu_profile = profile_report(profile)
            for module_name, module in list(sys.modules.items()):
                if module_name.startswith('apps.'):
                    for attr, value in list(vars(module).items()):
                        original = getattr(value, '__source_diagnostic_original__', None)
                        if original is not None:
                            setattr(module, attr, original)
