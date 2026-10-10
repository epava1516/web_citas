"""Pure helper boundary: acceptance/preflight can never consume approved caches."""


def require_diagnostic(settings, owned_database):
    if any(getattr(settings, name, False) for name in (
        'CAPACITY_DELIVERY_COMPLETE', 'CAPACITY_SELECTION_COMPLETE', 'CAPACITY_PREFLIGHT_ONLY',
    )):
        raise ValueError('Diagnostic baseline cannot run in acceptance or preflight')
    if getattr(settings, 'CAPACITY_ENVIRONMENT_VERIFIED', False) and not all(
        getattr(settings, name, False) for name in ('CAPACITY_DELIVERY_PROFILE_FULL', 'CAPACITY_DELIVERY_PROFILE')
    ):
        raise ValueError('Verified capacity baseline requires the full diagnostic profile')
    return owned_database()
