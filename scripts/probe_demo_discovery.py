"""Read-only Chromium smoke check for the initial synthetic Docker demo (two public listings)."""

import shutil

from playwright.sync_api import expect, sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
    )
    try:
        page = browser.new_page(viewport={"width": 390, "height": 844})
        response = page.goto("http://localhost:18080/en/?q=photography")
        assert response.status == 200
        expect(page.get_by_text("2 results", exact=True)).to_be_visible()
        expect(page.locator("article.card")).to_have_count(2)
        page.locator("[name=checked]").select_option("age")
        page.get_by_role("button", name="Search", exact=True).click()
        expect(page.get_by_text("0 results", exact=True)).to_be_visible()
        page.reload()
        expect(page.locator("[name=checked]")).to_have_values(["age"])
        page.locator("[name=checked]").select_option([])
        page.get_by_role("button", name="Search", exact=True).click()
        expect(page.get_by_text("2 results", exact=True)).to_be_visible()
        regions = page.locator("[name=region] option").evaluate_all(
            "items => items.map(item => item.value)"
        )
        assert len(regions) == 2
        page.locator("[name=region]").select_option(regions[0])
        assert page.locator("[name=city] option").count() == 1
        page.locator("[name=region]").select_option([])
        assert page.locator("[name=city] option").count() == 2
        page.locator("article.card h2 a").first.click()
        expect(page.get_by_role("heading", name="Rates", exact=True)).to_be_visible()
        expect(page.get_by_text("Age: simulated", exact=True)).to_be_visible()
        image = page.get_by_role("img").first
        expect(image).to_be_visible()
        assert image.evaluate("img => img.complete && img.naturalWidth > 0")
        assert (
            page.request.get("http://localhost:18080/private-media/demo-credentials.json").status
            == 404
        )
        assert page.request.get("http://localhost:18080/static/search-geography.js").status == 200
        print(
            "Docker Chromium CR07: search/filter/reload/geography/detail/derivative/private-file checks passed"
        )
    finally:
        browser.close()
