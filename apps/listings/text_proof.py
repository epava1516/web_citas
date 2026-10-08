"""Versioned sufficient text predicate for query and partial-index agreement.

V1 is migration data: preserve its SQL semantics. A new predicate requires a
new version and index migration; never silently change an installed predicate.
No publication authority or eligibility result is stored by these indexes.
"""
from django.db.models import BooleanField, F, Func, Q, Value


class PlainTextProofV1(Func):
    """A sufficient subset, NOT a PostgreSQL translation of Python re/strip.

    Explicit alphabet excludes @, colon, plus, Unicode digits and other unknown
    characters. WWW-dot and eight-digit/space/paren/hyphen runs are excluded.
    Thus no alternative of validate_listing_text can match. The only admitted
    whitespace is stripped identically by CharField; raw length bounds also
    bound the stripped value. All other text goes to the native validator.
    """
    output_field = BooleanField()

    def __init__(self, expression, maximum, required, *, legacy=True):
        self.legacy = legacy
        super().__init__(expression, Value(maximum), Value(required))

    def as_sql(self, compiler, connection, **extra_context):
        value, vp = compiler.compile(self.source_expressions[0])
        maximum, mp = compiler.compile(self.source_expressions[1])
        required, rp = compiler.compile(self.source_expressions[2])
        # A quoted whitelist, C collation, and bound patterns avoid relying on
        # locale-dependent character classes or PostgreSQL/Python Unicode parity.
        if not self.legacy:
            # The same sufficient alphabet and exclusions in one negative
            # predicate. ASCII W/w is exact under the admitted alphabet and C
            # collation; other Unicode remains UNKNOWN, as before.
            forbidden = "[^A-Za-z0-9 áéíóúüñÁÉÍÓÚÜÑ.,;!?()'\"\n\r\t-]|[wW]{3}[.]|[0-9][0-9 ()-]{7}"
            return (
                f"(char_length({value}) <= {maximum} "
                f"AND (NOT {required} OR btrim({value}, %s) <> '') "
                f"AND ({value} COLLATE \"C\") !~ %s)",
                [*vp, *mp, *rp, *vp, " \t\r\n", *vp, forbidden],
            )
        # Frozen equivalent control for the isolated performance comparison.
        whitelist = "^[A-Za-z0-9 áéíóúüñÁÉÍÓÚÜÑ.,;!?()'\"\n\r\t-]*$"
        expression = (
            f"(char_length({value}) <= {maximum} "
            f"AND (NOT {required} OR btrim({value}, %s) <> '') "
            f"AND ({value} COLLATE \"C\") ~ %s "
            f"AND lower({value} COLLATE \"C\") NOT LIKE %s "
            f"AND ({value} COLLATE \"C\") !~ %s)"
        )
        return expression, [*vp, *mp, *rp, *vp, " \t\r\n", *vp, whitelist,
                            *vp, "%www.%", *vp, "[0-9][0-9 ()-]{7}"]



class IsNotTrueV1(Func):
    output_field = BooleanField()

    def as_sql(self, compiler, connection, **extra_context):
        expression, params = compiler.compile(self.source_expressions[0])
        return f"({expression}) IS NOT TRUE", params


def revision_text_unknown():
    return Q(IsNotTrueV1(
        Q(PlainTextProofV1(F("title"), 120, True))
        & Q(PlainTextProofV1(F("description"), 6000, True))
        & Q(PlainTextProofV1(F("description_alternative"), 6000, False))
    ))


def rate_text_unknown():
    return Q(IsNotTrueV1(PlainTextProofV1(F("concept"), 80, True)))
