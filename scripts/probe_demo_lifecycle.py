"""Synthetic Docker demo only: reversible favorite/availability/pause/resume actions."""

import json
import shutil
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    credentials = json.loads(Path(".ai/demo-credentials.json").read_text())
    assert credentials.get("synthetic_only") is True
    origin = "http://localhost:18080"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            visitor = browser.new_page(viewport={"width": 390, "height": 844})
            owner = browser.new_page(viewport={"width": 390, "height": 844})
            for page, role in [(visitor, "visitor"), (owner, "individual")]:
                page.goto(origin + "/en/account/login/")
                page.locator("[name=email]").fill(credentials["accounts"][role]["email"])
                page.locator("[name=password]").fill(credentials["password"])
                page.locator("button[type=submit]").click()
                expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            visitor.goto(origin + "/en/favorites/")
            expect(visitor.get_by_text("You have no favorites yet.", exact=True)).to_be_visible()
            visitor.goto(origin + "/en/")
            visitor.locator("article.card h2 a").filter(has_text="individual").click()
            public_url = visitor.url
            visitor.get_by_role("button", name="Save private favorite", exact=True).click()
            expect(
                visitor.get_by_role("button", name="Remove favorite", exact=True)
            ).to_be_visible()
            visitor.reload()
            expect(
                visitor.get_by_role("button", name="Remove favorite", exact=True)
            ).to_be_visible()
            owner.goto(origin + "/en/person/create/")
            owner.get_by_role("link", name="Manage publication", exact=True).click()
            expect(owner.get_by_text("published", exact=True)).to_be_visible()
            for operation, status in [
                ("available", "published"),
                ("pause", "paused"),
                ("resume", "published"),
                ("unavailable", "published"),
            ]:
                owner.locator("[name=operation]").select_option(operation)
                owner.get_by_role("button", name="Apply action", exact=True).click()
                expect(owner.get_by_text(status, exact=True)).to_be_visible()
                owner.reload()
                expect(owner.get_by_text(status, exact=True)).to_be_visible()
                if operation == "pause":
                    assert visitor.request.get(public_url).status == 404
                    visitor.reload()
                    expect(visitor.get_by_text("Listing unavailable", exact=True)).to_be_visible()
                elif operation == "resume":
                    assert visitor.request.get(public_url).status == 200
            visitor.reload()
            visitor.get_by_role("button", name="Remove favorite", exact=True).click()
            expect(visitor.get_by_text("You have no favorites yet.", exact=True)).to_be_visible()
            print(
                "Docker Chromium CR08: login/private favorite/unavailable entry/availability/pause/resume/reload passed; sample restored published"
            )
        except Exception as error:
            raise RuntimeError(
                f"Private Docker probe failed ({type(error).__name__}); inspect local state before retrying."
            ) from None
        finally:
            browser.close()


if __name__ == "__main__":
    main()
