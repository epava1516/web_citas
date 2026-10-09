"""Check local documentation links and immutable historical copies, without Django."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def markdown_text(text, strip_inline=True):
    """Keep line numbers, but exclude fenced examples and inline code."""
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker and fence is None:
            fence = marker.group(1)
            lines.append("")
        elif fence and re.match(r"^\s{0,3}" + re.escape(fence[0]) + r"{" + str(len(fence))
                                + r",}\s*$", line):
            fence = None
            lines.append("")
        elif fence:
            lines.append("")
        else:
            lines.append(re.sub(r"(`+).*?\1", "", line) if strip_inline else line)
    return "\n".join(lines)


def destination(value):
    value = value.strip()
    if value.startswith("<"):
        return value[1:value.index(">")]
    return value.split()[0] if value else ""


def links(text):
    """Yield inline/image and explicit reference links; skip unresolved shorthand."""
    cleaned = markdown_text(text)
    definitions = {}
    for match in re.finditer(r"^ {0,3}\[([^\]\n]+)\]:\s*(.+)$", cleaned, re.M):
        definitions[match.group(1).casefold().strip()] = destination(match.group(2))
        yield cleaned.count("\n", 0, match.start()) + 1, destination(match.group(2))
    for match in re.finditer(r"!?\[[^\]\n]*\]\(", cleaned):
        start = match.end()
        depth = 1
        escaped = False
        end = start
        for end in range(start, len(cleaned)):
            char = cleaned[end]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if not depth:
                    break
        if not depth:
            yield cleaned.count("\n", 0, match.start()) + 1, destination(cleaned[start:end])
    for match in re.finditer(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]", cleaned):
        key = (match.group(2) or match.group(1)).casefold().strip()
        if key in definitions:
            yield cleaned.count("\n", 0, match.start()) + 1, definitions[key]
        else:
            yield cleaned.count("\n", 0, match.start()) + 1, "missing-reference:" + key


def anchors(text):
    """GitHub-style ATX heading slugs and explicit HTML anchors."""
    result = set()
    counts = {}
    # Keep inline code contents in headings: it contributes to the visible slug.
    text = markdown_text(text, strip_inline=False)
    for line in text.splitlines():
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if match:
            label = re.sub(r"<[^>]*>", "", match.group(1)).lower()
            slug = re.sub(r"[^\w\- ]", "", label).replace(" ", "-")
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            result.add(slug + ("-" + str(count) if count else ""))
    result.update(re.findall(r"\b(?:id|name)=[\"']([^\"']+)[\"']", text))
    return result


def check(root):
    root = root.resolve()
    manifest_path = root / "docs/historial-documentacion.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    copies = manifest["copias"]
    retired = manifest.get("codigo_retirado", {})
    redirects = manifest.get("anclas_historicas", [])
    errors = []
    for relative, meta in copies.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: falta la copia histórica registrada")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
            errors.append(f"{relative}: cambió la huella de la copia histórica")
    for path in (root / "docs/17-historial").glob("*.md"):
        if path.relative_to(root).as_posix() not in copies:
            errors.append(f"{path.relative_to(root)}: copia histórica sin registrar")

    verified_retired = {}

    def retired_source(relative):
        if relative in verified_retired:
            return verified_retired[relative]
        meta = retired[relative]
        commit = meta["commit_retirada"]
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            verified_retired[relative] = False
            return False
        result = subprocess.run(
            ["git", "show", f"{commit}^:{relative}"], cwd=root, capture_output=True, check=False,
        )
        valid = (result.returncode == 0
                 and hashlib.sha256(result.stdout).hexdigest() == meta["sha256_fuente_historica"])
        verified_retired[relative] = valid
        return valid

    files = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
    anchor_cache = {}
    count = historical = exceptions = historical_anchors = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        meta = copies.get(relative)
        base = root / meta["base_enlaces"] if meta else path.parent
        for line, target in links(path.read_text(encoding="utf-8")):
            if target.startswith("missing-reference:"):
                errors.append(f"{relative}:{line}: referencia sin definición: {target[18:]}")
                continue
            parts = urlsplit(target)
            if parts.scheme or parts.netloc:
                continue
            count += 1
            name = unquote(parts.path)
            endpoint = (base / name).resolve() if name else path
            if not endpoint.exists():
                key = endpoint.relative_to(root).as_posix() if endpoint.is_relative_to(root) else ""
                if meta and key in retired and retired_source(key):
                    exceptions += 1
                else:
                    errors.append(f"{relative}:{line}: destino local ausente: {target}")
                continue
            if meta and name:
                historical += 1
            fragment = unquote(parts.fragment)
            if fragment and endpoint.suffix.lower() == ".md":
                for redirect in redirects:
                    if (meta and redirect["documento"] == relative
                            and redirect["destino_original"] == target):
                        archived = root / redirect["copia_destino"]
                        if redirect["copia_destino"] not in copies:
                            errors.append(f"{relative}:{line}: redirección sin copia registrada")
                        elif archived.is_file():
                            endpoint = archived
                            historical_anchors += 1
                        break
                if endpoint not in anchor_cache:
                    anchor_cache[endpoint] = anchors(endpoint.read_text(encoding="utf-8"))
                if fragment not in anchor_cache[endpoint]:
                    errors.append(f"{relative}:{line}: ancla local ausente: {target}")
    return {
        "markdown_files": len(files), "local_links": count,
        "protected_copies": len(copies), "historical_links_resolved": historical,
        "historical_anchors_resolved": historical_anchors,
        "retired_source_references": exceptions, "errors": errors,
        "limits": "Local Markdown links/ATX anchors and registered copies; no HTTP or app checks.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Emit machine-readable results")
    args = parser.parse_args()
    try:
        result = check(args.root)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"ERROR: no se pudo comprobar la documentación: {error}\n")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in result["errors"]:
            print("ERROR:", error)
        verdict = "FAIL" if result["errors"] else "PASS"
        print(f"{verdict}: {result['markdown_files']} Markdown, {result['local_links']} enlaces, "
              f"{result['protected_copies']} copias registradas; "
              f"{result['historical_links_resolved']} enlaces históricos resueltos y "
              f"{result['retired_source_references']} referencias retiradas verificadas en Git "
              f"({result['historical_anchors_resolved']} anclas en su copia original).")
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
