"""Frozen-source experimental second stage; never installed into product here."""

import hashlib
import inspect

from apps.listings import publication_state

SOURCE_SHA = "35d6b1e9b8d7a9a04e1218263416cc6025173da55aee9d638dd67507a6e50010"
UNKNOWN_NEEDLE = '''    if len(unknown) > NATIVE_UNKNOWN_LIMIT:
        if observation is not None:
            observation.update(route="fallback", reason="state_unknown_over_limit")
        return None
'''
UNKNOWN_CANDIDATE = '''    extended_unknown = False
    if len(unknown) > NATIVE_UNKNOWN_LIMIT:
        if (trusted_snapshot and coverage_current
                and getattr(query, "_publication_state_population", None) is not None):
            unknown = list(unknown_query.values_list("pk", flat=True)[: DIRTY_LIMIT + 1])
            extended_unknown = len(unknown) <= DIRTY_LIMIT
        if not extended_unknown:
            if observation is not None:
                observation.update(route="fallback", reason="state_unknown_over_limit")
            return None
'''
OBSERVATION_NEEDLE = 'observation.update(route="state", reason="trusted_state", native_unknown=len(unknown),'
OBSERVATION_CANDIDATE = '''observation.update(route="state", reason=(
            "trusted_state_extended_unknown" if extended_unknown else "trusted_state"),
                           native_unknown=len(unknown),'''


def extended_unknown_candidate():
    path = inspect.getsourcefile(publication_state)
    with open(path, "rb") as source_file:
        source_sha = hashlib.sha256(source_file.read()).hexdigest()
    assert source_sha == SOURCE_SHA
    original = publication_state._state_page
    source = inspect.getsource(original)
    assert source.count(UNKNOWN_NEEDLE) == source.count(OBSERVATION_NEEDLE) == 1
    candidate = source.replace(UNKNOWN_NEEDLE, UNKNOWN_CANDIDATE).replace(
        OBSERVATION_NEEDLE, OBSERVATION_CANDIDATE,
    )
    namespace = vars(publication_state).copy()
    exec(compile(candidate, "<beta-extended-unknown-candidate>", "exec"), namespace)
    return original, namespace["_state_page"], {
        "source_sha256": source_sha,
        "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
        "native_unknown_limit": publication_state.NATIVE_UNKNOWN_LIMIT,
        "dirty_limit": publication_state.DIRTY_LIMIT,
    }
