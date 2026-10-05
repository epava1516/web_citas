"""Reconstruct a private multipart copy locally using only Python's standard library."""

import argparse
import codecs
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

MAX_FRAGMENT = 64 * 1024 * 1024


def integer(value, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError("Invalid manifest size or position")
    return value


def reconstruct(manifest_path, package_directory, output_path):
    manifest_path, package_directory, output_path = map(
        Path, [manifest_path, package_directory, output_path]
    )
    if manifest_path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Manifest exceeds size limit")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "rights-data-manifest-v1":
        raise ValueError("Invalid manifest")
    if manifest.get("encoding") != "utf-8" or not isinstance(manifest.get("data_parts"), list):
        raise ValueError("Invalid manifest encoding or fragments")
    expected_total = integer(manifest.get("size"))
    fragments = manifest["data_parts"]
    if not fragments or any(not isinstance(f, dict) for f in fragments):
        raise ValueError("Invalid manifest fragments")
    if sum(integer(f.get("size")) for f in fragments) != expected_total:
        raise ValueError("Invalid fragment sizes")
    if output_path.exists():
        raise FileExistsError("Output already exists")
    decoder = codecs.getincrementaldecoder("utf-8")()
    total_hash = hashlib.sha256()
    total = 0
    positions = set()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output_path.parent, prefix=".rights-copy-", delete=False
        ) as output:
            temporary = Path(output.name)
            for sequence, fragment in enumerate(fragments, 1):
                position = integer(fragment.get("position"))
                if position in positions or integer(fragment.get("fragment_position")) != sequence:
                    raise ValueError("Invalid fragment order")
                positions.add(position)
                name = f"data-{sequence:08d}.json.fragment"
                if fragment.get("filename") != name:
                    raise ValueError("Invalid fragment filename")
                size = integer(fragment.get("size"))
                if size > MAX_FRAGMENT:
                    raise ValueError("Fragment exceeds size limit")
                package_path = package_directory / f"rights-data-part-{position}.zip"
                if package_path.stat().st_size > MAX_FRAGMENT:
                    raise ValueError("Package exceeds size limit")
                part_hash = hashlib.sha256()
                part_size = 0
                with zipfile.ZipFile(package_path) as package:
                    if package.namelist() != [name]:
                        raise ValueError("Invalid package entries")
                    entry = package.getinfo(name)
                    if entry.file_size != size or entry.compress_type != zipfile.ZIP_STORED:
                        raise ValueError("Invalid package content size or compression")
                    with package.open(entry) as stream:
                        while chunk := stream.read(64 * 1024):
                            decoder.decode(chunk)
                            output.write(chunk)
                            total_hash.update(chunk)
                            part_hash.update(chunk)
                            part_size += len(chunk)
                            total += len(chunk)
                if part_size != size or part_hash.hexdigest() != fragment.get("sha256"):
                    raise ValueError("Fragment integrity check failed")
            decoder.decode(b"", final=True)
            if total != expected_total or total_hash.hexdigest() != manifest.get("sha256"):
                raise ValueError("Document integrity check failed")
            output.flush()
            os.fsync(output.fileno())
        # Atomic creation without overwriting even if another writer raced the initial check.
        os.link(temporary, output_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("package_directory")
    parser.add_argument("output")
    args = parser.parse_args()
    try:
        size = reconstruct(args.manifest, args.package_directory, args.output)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        parser.exit(1, "Copy reconstruction failed; check manifest and packages.\n")
    print(f"Private copy reconstructed locally ({size} bytes).")


if __name__ == "__main__":
    main()
