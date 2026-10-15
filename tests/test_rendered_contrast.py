"""Finite computed-style contrast measurements over native PostgreSQL HTTP pages."""

import json
import os
import re
import shutil
from pathlib import Path

import pytest
from django.core.management import call_command
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

pytestmark = pytest.mark.django_db(transaction=True)
STYLE = """element => {
  const style = getComputedStyle(element);
  const chain = [];
  for (let node=element; node; node=node.parentElement) {
    const s=getComputedStyle(node);
    chain.push({tag:node.tagName,id:node.id,background:s.backgroundColor,
      image:s.backgroundImage,opacity:s.opacity,filter:s.filter,blend:s.mixBlendMode});
  }
  return {color:style.color,font_size:style.fontSize,font_weight:style.fontWeight,
    outline_color:style.outlineColor,outline_style:style.outlineStyle,
    outline_width:style.outlineWidth,border_color:style.borderTopColor,
    border_style:style.borderTopStyle,border_width:style.borderTopWidth,chain};
}"""


def rgba(value):
    parts = [float(n) for n in re.findall(r"[\d.]+", value)]
    assert value.startswith(("rgb(", "rgba(")) and len(parts) in {3, 4}, value
    return parts[:3] + [parts[3] if len(parts) == 4 else 1]


def over(foreground, background):
    return [foreground[i] * foreground[3] + background[i] * (1 - foreground[3]) for i in range(3)]


def backdrop(chain):
    assert all(
        c["image"] == "none"
        and float(c["opacity"]) == 1
        and c["filter"] == "none"
        and c["blend"] == "normal"
        for c in chain
    ), "unsupported background: not_measured"
    colors = [rgba(c["background"]) for c in chain]
    opaque = next((i for i, c in enumerate(colors) if c[3] == 1), None)
    assert opaque is not None, "no observed opaque ancestor: not_measured"
    result = colors[opaque][:3]
    for color in reversed(colors[:opaque]):
        result = over(color, result)
    return result


def luminance(rgb):
    values = [c / 255 for c in rgb]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in values]
    return sum(v * w for v, w in zip(linear, [0.2126, 0.7152, 0.0722], strict=True))


def ratio(a, b):
    high, low = sorted([luminance(a), luminance(b)], reverse=True)
    return (high + 0.05) / (low + 0.05)


def measured(locator, selector, kind="text"):
    expect(locator).to_be_visible()
    style = locator.evaluate(STYLE)
    bg = backdrop(style["chain"])
    if kind == "text":
        fg = over(rgba(style["color"]), bg)
        size = float(style["font_size"][:-2])
        weight = int(style["font_weight"])
        threshold = 3 if size >= 24 or (size >= 14 * 96 / 72 and weight >= 700) else 4.5
    else:
        bg = backdrop(style["chain"][1:])
        key = "outline" if kind == "outline" else "border"
        assert style[key + "_style"] != "none" and float(style[key + "_width"][:-2]) > 0
        fg = over(rgba(style[key + "_color"]), bg)
        threshold = 3
    value = ratio(fg, bg)
    row = {
        "selector": selector,
        "kind": kind,
        "style": style,
        "foreground_effective_rgb": fg,
        "background_effective_rgb": bg,
        "ratio": value,
        "threshold": threshold,
        "verdict": "PASS" if value >= threshold else "FAIL",
    }
    return row


def collect(page, language, width, state):
    color_scheme = (
        "dark" if page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches") else "light"
    )
    folder = os.environ.get("BF_SCREENSHOT_OUTPUT")
    if folder:
        target = Path(folder) / f"{language}-{color_scheme}-{width}-{state}.png"
        page.screenshot(path=str(target), full_page=True)
        target.chmod(0o600)
    rows = []
    for selector in [
        "h1",
        ".brand",
        "nav a",
        "aside.notice",
        "footer",
        "footer a",
        "main p",
        "label",
        "button",
        'input[name="email"]',
        "textarea",
        "select",
        ".errorlist li",
        ".helptext",
    ]:
        group = page.locator(selector)
        if not group.count():
            rows.append(
                {
                    "selector": selector,
                    "kind": "text",
                    "verdict": "not_measured",
                    "reason": "not_present_in_this_page",
                }
            )
            continue
        for index, node in enumerate(group.all()):
            if node.is_visible():
                rows.append(measured(node, f"{selector}[{index}]"))
    error = page.locator("main form .errorlist").first
    if error.count():
        expect(error).to_be_focused()
        rows.append(measured(error, ".errorlist:focus", "outline"))
    else:
        page.locator(".skip").focus()
        rows.append(measured(page.locator(".skip"), ".skip:focus", "outline"))
        rows.append(measured(page.locator(".skip"), ".skip:focus"))
    for selector in ['input[name="email"]', "textarea", "select"]:
        for index, node in enumerate(page.locator(selector).all()):
            rows.append(measured(node, f"{selector}[{index}]", "border"))
    for row in rows:
        row.update(language=language, width=width, state=state, color_scheme=color_scheme)
    return rows


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("color_scheme", ["light", "dark"])
def test_public_rendered_contrast(live_server, language, color_scheme, record_property):
    call_command("bootstrap")
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            for width, height in [(390, 844), (1280, 900)]:
                page = browser.new_page(
                    viewport={"width": width, "height": height}, color_scheme=color_scheme
                )
                response = page.goto(live_server.url + f"/{language}/account/login/")
                assert response.status == 200
                rows.extend(collect(page, language, width, "public_initial"))
                page.locator("form").evaluate("f=>f.noValidate=true")
                page.get_by_role(
                    "button", name="Continue" if language == "en" else "Continuar", exact=True
                ).focus()
                with page.expect_response(lambda r: r.request.method == "POST") as rejected:
                    page.keyboard.press("Enter")
                assert rejected.value.status == 400
                expect(page.locator(".errorlist").first).to_be_visible()
                page.wait_for_load_state("load")
                rows.extend(collect(page, language, width, "public_required_400"))
                page.close()
        finally:
            browser.close()
    record_property("contrast_measurements", json.dumps(rows))
    failures = [r for r in rows if r["verdict"] == "FAIL"]
    assert not failures, failures


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("color_scheme", ["light", "dark"])
def test_private_rendered_contrast(
    request, settings, live_server, language, color_scheme, record_property
):
    settings.DEBUG = True
    case, _, staff, _, _, _ = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            for width, height in [(390, 844), (1280, 900)]:
                context = browser.new_context(
                    viewport={"width": width, "height": height}, color_scheme=color_scheme
                )
                context.add_cookies(
                    [
                        {
                            "name": settings.SESSION_COOKIE_NAME,
                            "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                            "url": live_server.url,
                        }
                    ]
                )
                page = context.new_page()
                assert (
                    page.goto(
                        live_server.url + f"/{language}/moderation/rights/{case.pk}/export/"
                    ).status
                    == 200
                )
                page.locator("#id_operation").select_option("compile_pages")
                page.locator("#id_reason").fill("Synthetic / private contrast fixture reason")
                with page.expect_response(lambda r: r.request.method == "POST") as rejected:
                    page.get_by_role(
                        "button",
                        name="Record copy action"
                        if language == "en"
                        else "Registrar acción de copia",
                        exact=True,
                    ).click()
                assert (
                    rejected.value.status == 409
                    and "no-store" in rejected.value.headers["cache-control"]
                )
                rows.extend(collect(page, language, width, "private_409"))
                context.close()
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before
    record_property("contrast_measurements", json.dumps(rows))
    failures = [r for r in rows if r["verdict"] == "FAIL"]
    assert not failures, failures


def test_contrast_reference_pairs_and_alpha():
    assert ratio([0, 0, 0], [255, 255, 255]) == 21
    assert ratio([255, 255, 255], [255, 255, 255]) == 1
    assert 4.47 < ratio([119, 119, 119], [255, 255, 255]) < 4.5
    assert over([0, 0, 0, 0.5], [255, 255, 255]) == [127.5] * 3
