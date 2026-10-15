"""Real keyboard path through the shared ES/EN shell, on PostgreSQL HTTP."""
import json
import shutil

import pytest
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401, F811
from test_photos import photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_skip_link_moves_focus_and_navigation_is_localized(directory, live_server, language, record_property):  # noqa: F811
    assert connection.vendor == 'postgresql'
    measurements = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which('chromium-browser'), args=['--no-sandbox']
        )
        try:
            for width, height in [(320, 800), (390, 844), (1280, 900)]:
                context = browser.new_context(viewport={'width': width, 'height': height})
                page = context.new_page()
                for path, first_field in [(f'/{language}/', 'q'), (f'/{language}/account/login/', 'email')]:
                    response = page.goto(live_server.url + path)
                    assert response.status == 200
                    assert page.request.get(live_server.url + '/static/app.css').status == 200
                    skip = page.get_by_role('link', name='Skip to content' if language == 'en' else 'Saltar al contenido', exact=True)
                    page.keyboard.press('Tab')
                    expect(skip).to_be_focused()
                    expect(skip).to_be_in_viewport()
                    assert skip.evaluate("e => getComputedStyle(e).outlineStyle") != 'none'
                    page.keyboard.press('Enter')
                    main = page.get_by_role('main')
                    expect(main).to_be_focused()
                    page.keyboard.press('Tab')
                    if first_field == 'q':
                        expect(page.get_by_role('link', name='Publish or manage your listing' if language == 'en' else 'Publicar o gestionar tu anuncio', exact=True)).to_be_focused()
                        page.keyboard.press('Tab')
                    expect(page.locator(f'[name="{first_field}"]')).to_be_focused()
                    expect(page.get_by_role('navigation', name='Main' if language == 'en' else 'Principal', exact=True)).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                    page.reload()
                    assert page.evaluate('document.activeElement === document.body')
                    page.keyboard.press('Tab')
                    expect(skip).to_be_focused()
                    measurements.append({'language': language, 'viewport': [width, height], 'path': path, 'skip_focus': True, 'main_focus': True, 'next_field': first_field, 'reload_restores_navigation': True, 'horizontal_overflow': False})
                context.close()
        finally:
            browser.close()
    record_property('keyboard_navigation', json.dumps(measurements))
