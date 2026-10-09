"""Build the pinned RDB tools required by integration tests and export their hashes."""

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

PARSER_COMMIT = "bc5f295c98b40c2c33099d9d72ab30ce9e595dc7"
HIREDIS_COMMIT = "869f3d0ef1513dd0258ad7190c9914df16dcc4a4"


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()


def build(source, output):
    """Build in the supplied disposable checkout; never fetch or modify services."""
    source, output = source.resolve(), output.resolve()
    for checkout, expected in [(source, PARSER_COMMIT), (source / "deps/hiredis", HIREDIS_COMMIT)]:
        if git(checkout, "rev-parse", "HEAD") != expected:
            raise ValueError(f"Unexpected source revision: {checkout}")
        if git(checkout, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError(f"Modified tracked source: {checkout}")
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(["make", "clean"], cwd=source, check=True)
    subprocess.run(["make", "-j2"], cwd=source, check=True)
    shutil.copyfile(source / "bin/rdb-cli", output / "rdb-cli")
    project = Path(__file__).resolve().parents[1]
    compiler = shutil.which("cc")
    if compiler is None:
        raise RuntimeError("C compiler required")
    for name in ["aux", "metadata"]:
        subprocess.run(
            [
                compiler,
                "-std=c99",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-fstack-protector-all",
                "-I",
                str(source / "api"),
                str(project / f"scripts/native/retained_rdb_{name}.c"),
                str(source / "lib/librdb-ext.a"),
                str(source / "lib/librdb.a"),
                "-o",
                str(output / f"retained-rdb-{name}"),
            ],
            check=True,
        )
    values = {}
    for label, filename in [
        ("DECODER", "rdb-cli"),
        ("AUX", "retained-rdb-aux"),
        ("METADATA", "retained-rdb-metadata"),
    ]:
        binary = output / filename
        binary.chmod(0o755)
        values[f"RETAINED_RDB_{label}_BIN"] = str(binary)
        values[f"RETAINED_RDB_{label}_SHA256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "parser_commit": PARSER_COMMIT,
                "hiredis_commit": HIREDIS_COMMIT,
                "environment": values,
            },
            indent=2,
        )
        + "\n"
    )
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", required=True, type=Path, help="Disposable pinned librdb checkout"
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--env-file", required=True, type=Path, help="GitHub Actions environment file"
    )
    args = parser.parse_args()
    values = build(args.source, args.output)
    if any("\n" in value or "\r" in value for value in values.values()):
        raise ValueError("Environment values cannot contain newlines")
    with args.env_file.open("a") as stream:
        for key, value in values.items():
            stream.write(f"{key}={value}\n")
    print("Three native tools built; revisions, executable permissions and hashes recorded.")


if __name__ == "__main__":
    main()
