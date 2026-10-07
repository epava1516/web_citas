"""Predicate over UUIDs already captured by one request; never a live subquery."""
from uuid import UUID

from django.db import connection
from django.db.models import BooleanField, F, Func, Value


class UUIDArrayMatch(Func):
    output_field = BooleanField()

    def as_sql(self, compiler, connection, **extra_context):
        left, left_params = compiler.compile(self.source_expressions[0])
        right, right_params = compiler.compile(self.source_expressions[1])
        return f'({left} = ANY({right}::uuid[]))', [*left_params, *right_params]


class CapturedUUIDBatch:
    def __init__(self, identifiers, *, mode='in'):
        self.identifiers = tuple(identifiers)
        if any(type(identifier) is not UUID for identifier in self.identifiers):
            raise TypeError('Captured UUID batches require UUID values')
        if mode not in ('in', 'array'):
            raise ValueError('Unknown captured UUID predicate')
        self.mode = mode
        # Canonical UUIDs contain no array syntax or quotes. The full array is
        # still a bound parameter, never interpolated into SQL. Encode once and
        # reuse for each relation of this same captured population.
        self.encoded = ('{' + ','.join(str(identifier) for identifier in self.identifiers) + '}') if mode == 'array' else None

    def filter(self, query, field):
        if not self.identifiers:
            return query.none()
        if self.mode == 'in' or connection.vendor != 'postgresql':
            return query.filter(**{field + '__in': self.identifiers})
        return query.filter(UUIDArrayMatch(F(field), Value(self.encoded)))
