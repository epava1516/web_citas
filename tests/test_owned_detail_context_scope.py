"""The product detail owns RR only when it owns the transaction."""
from contextlib import nullcontext

import pytest
from django.db import connection, transaction
from owned_detail_context import build_detail_context_prototype, patch_detail_view
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import moderation_views
from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


def settings_now():
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('transaction_isolation'), "
                       "current_setting('transaction_read_only'), current_setting('jit'), "
                       "current_setting('join_collapse_limit')")
        return tuple(cursor.fetchone())


@pytest.mark.parametrize('mode', ['success', 'render_error', 'inherited_rc', 'inherited_rr'])
def test_detail_transaction_ownership_and_restore(request, monkeypatch, mode):
    client=request.getfixturevalue('directory')
    listing=Listing.objects.filter(status='published').first()
    before=settings_now()
    raw=connection.connection
    factory,threshold=raw.cursor_factory,raw.prepare_threshold
    prototype=build_detail_context_prototype()
    native=moderation_views._native_public_detail
    render=moderation_views.render
    seen=[]
    fallback=[]

    def observed_render(*args,**kwargs):
        seen.append(settings_now())
        if mode=='render_error':
            raise RuntimeError('owned-render-error')
        return render(*args,**kwargs)

    def native_fallback(*args,**kwargs):
        fallback.append(True)
        return native(*args,**kwargs)

    def forbidden_context(*args,**kwargs):
        raise AssertionError('Inherited transaction must retain native detail')

    inherited=mode.startswith('inherited_')
    with transaction.atomic() if inherited else nullcontext():
        if inherited:
            with connection.cursor() as cursor:
                if mode=='inherited_rr':
                    cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
                cursor.execute('SET LOCAL jit=on')
                cursor.execute('SET LOCAL join_collapse_limit=6')
        enclosing=settings_now()
        with monkeypatch.context() as patch:
            patch_detail_view(patch,prototype)
            patch.setattr(moderation_views,'render',observed_render)
            patch.setitem(prototype.__globals__,'_native_public_detail',native_fallback)
            if inherited:
                patch.setitem(prototype.__globals__,'PublicationContext',forbidden_context)
            if mode=='render_error':
                with pytest.raises(RuntimeError,match='owned-render-error'):
                    client.get(f'/es/listing/{listing.pk}/')
            else:
                assert client.get(f'/es/listing/{listing.pk}/').status_code==200
        assert moderation_views.render is render
        assert settings_now()==enclosing
        assert raw.cursor_factory is factory and raw.prepare_threshold==threshold
    assert settings_now()==before
    assert len(seen)==1
    assert seen[0][:2] == (enclosing[:2] if inherited else ('repeatable read','on'))
    assert len(fallback)==int(inherited)
