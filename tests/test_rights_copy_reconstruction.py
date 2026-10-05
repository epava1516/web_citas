import hashlib
import importlib.util
import json

import pytest

from apps.safety.rights_data_parts import data_packages

spec = importlib.util.spec_from_file_location("reconstruct", "scripts/reconstruct_rights_copy.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def files(tmp_path):
    data = json.dumps({"text": "🙂á漢字" * 200}, ensure_ascii=False).encode()
    entries = []
    for part in data_packages(data, limit=256):
        position = part["position"] + 2  # Existing image packages precede data packages.
        (tmp_path / f"rights-data-part-{position}.zip").write_bytes(part["content"])
        entries.append(
            {key: part[key] for key in ["filename", "size", "sha256"]}
            | {"position": position, "fragment_position": part["position"]}
        )
    manifest = {
        "schema": "rights-data-manifest-v1",
        "encoding": "utf-8",
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "data_parts": entries,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, manifest, data


def test_offline_reconstruction_is_exact_private_and_does_not_overwrite(tmp_path):
    path, _, data = files(tmp_path)
    output = tmp_path / "copy.json"
    assert module.reconstruct(path, tmp_path, output) == len(data)
    assert output.read_bytes() == data and output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        module.reconstruct(path, tmp_path, output)
    assert output.read_bytes() == data and not list(tmp_path.glob(".rights-copy-*"))


@pytest.mark.parametrize("damage", ["digest", "filename", "order", "size", "missing"])
def test_invalid_copy_leaves_no_output_or_temporary_file(tmp_path, damage):
    path, manifest, _ = files(tmp_path)
    if damage == "missing":
        (tmp_path / "rights-data-part-3.zip").unlink()
    else:
        key, value = {
            "digest": ("sha256", "0" * 64),
            "filename": ("filename", "../secret"),
            "order": ("fragment_position", True),
            "size": ("size", 1),
        }[damage]
        manifest["data_parts"][0][key] = value
        path.write_text(json.dumps(manifest))
    output = tmp_path / "copy.json"
    with pytest.raises((OSError, ValueError)):
        module.reconstruct(path, tmp_path, output)
    assert not output.exists() and not list(tmp_path.glob(".rights-copy-*"))


def test_cli_reconstructs_without_network_or_application_runtime(tmp_path):
    import subprocess
    import sys

    path, _, data = files(tmp_path)
    output = tmp_path / "cli-copy.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/reconstruct_rights_copy.py",
            str(path),
            str(tmp_path),
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and output.read_bytes() == data
    assert "🙂" not in result.stdout and not result.stderr


def test_malformed_fragment_collection_is_controlled(tmp_path):
    path, manifest, _ = files(tmp_path)
    manifest["data_parts"] = [None]
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        module.reconstruct(path, tmp_path, tmp_path / "copy.json")
