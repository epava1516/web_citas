"""Every application route is documented in a contract before GS01 (static check)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URLCONFS = ["apps/core/urls.py", "apps/safety/urls.py", "config/urls.py"]
EXCLUDED = {"admin/"}  # Django admin keeps its own permission model.


def routes():
    found = set()
    for name in URLCONFS:
        text = (ROOT / name).read_text()
        found |= set(re.findall(r"(?:re_)?path\(\s*[\"']([^\"']*)[\"']", text))
    return found - EXCLUDED


def documented(route, corpus):
    pattern = re.escape(re.sub(r"<[^>]+>", "\0", route)).replace("\x00", r"[^/\s`|]+")
    return re.search(pattern, corpus) is not None


def test_every_route_appears_in_a_contract_or_flow_document():
    paths = list((ROOT / "docs/contratos").glob("*.md")) + list((ROOT / "docs").glob("*.md"))
    corpus = "\n".join(path.read_text() for path in paths)
    found = routes()
    assert len(found) > 100  # The extraction itself still sees the URL configuration.
    assert sorted(route for route in found if not documented(route, corpus)) == []
