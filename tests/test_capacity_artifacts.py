"""Real bounded artifact writes reject byte/count overflow and foreign targets."""

import hashlib
import resource
import subprocess
import sys
import tarfile

import pytest

from scripts import capacity_artifacts as artifacts


def test_artifact_limits_count_utf8_bytes_and_allow_replacing_owned_file(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "MAX_FILE_BYTES", 4)
    monkeypatch.setattr(artifacts, "MAX_FILES", 3)  # One slot stays reserved for report.json.
    artifacts.write_artifact(tmp_path, "a", "éé")
    artifacts.write_artifact(tmp_path, "b", "next")
    artifacts.write_artifact(tmp_path, "a", "same")
    assert (tmp_path / "a").read_bytes() == b"same"
    with pytest.raises(ValueError, match="file ceiling"):
        artifacts.write_artifact(tmp_path, "a", "ééé")
    with pytest.raises(ValueError, match="count"):
        artifacts.write_artifact(tmp_path, "c", "x")
    assert (tmp_path / "a").read_bytes() == b"same" and not (tmp_path / "c").exists()


@pytest.mark.parametrize("name", ["../foreign", "/tmp/foreign", "sub/file", "", ".", ".."])
def test_artifact_cannot_escape_owned_directory(tmp_path, name):
    with pytest.raises(ValueError, match="filename"):
        artifacts.write_artifact(tmp_path, name, "x")


def test_artifact_does_not_follow_existing_symlink(tmp_path):
    foreign = tmp_path / "foreign"
    foreign.write_text("preserve")
    (tmp_path / "link").symlink_to(foreign)
    with pytest.raises(ValueError, match="symlink"):
        artifacts.write_artifact(tmp_path, "link", "replace")
    assert foreign.read_text() == "preserve"


def test_artifact_returns_fingerprint_and_reserves_report_slot(tmp_path, monkeypatch):
    assert artifacts.write_artifact(tmp_path, "a", "é") == {
        "bytes": 2, "sha256": hashlib.sha256("é".encode()).hexdigest()}
    monkeypatch.setattr(artifacts, "MAX_FILES", 2)
    with pytest.raises(ValueError, match="count"):
        artifacts.write_artifact(tmp_path, "b", "x")
    artifacts.write_artifact(tmp_path, "report.json", "{}")


def test_archive_sink_needs_existing_file_and_records_members(tmp_path, monkeypatch):
    with pytest.raises(FileNotFoundError):
        artifacts.ArchiveSink(tmp_path / "missing.tar")
    path = tmp_path / "artifacts.tar"
    path.touch()
    monkeypatch.setattr(artifacts, "MAX_FILES", 3)
    sink = artifacts.ArchiveSink(path)
    assert sink.write("a.log", "é")["sha256"] == hashlib.sha256("é".encode()).hexdigest()
    sink.write("a.log", "again")
    sink.write("b.log", "x")
    with pytest.raises(ValueError, match="count"):
        sink.write("c.log", "x")
    with pytest.raises(ValueError, match="filename"):
        sink.write("../escape", "x")
    sink.write("report.json", "{}")
    sink.close()
    with tarfile.open(path) as archive:
        assert [member.name for member in archive] == ["a.log", "a.log", "b.log", "report.json"]


def test_archive_explicit_ceiling_survives_default_changes(tmp_path, monkeypatch):
    path = tmp_path / "explicit.tar"
    path.touch()
    monkeypatch.setattr(artifacts, "MAX_FILES", 1)
    sink = artifacts.ArchiveSink(path, max_files=3)
    try:
        sink.write("a", "x")
        monkeypatch.setattr(artifacts, "MAX_FILES", 100)
        sink.write("b", "x")
        with pytest.raises(ValueError, match="count"):
            sink.write("c", "x")
        sink.write("report.json", "{}")
    finally:
        sink.close()


@pytest.mark.parametrize("ceiling", [0, 257, True, "3"])
def test_artifact_invalid_runtime_default_is_rejected(tmp_path, monkeypatch, ceiling):
    monkeypatch.setattr(artifacts, "MAX_FILES", ceiling)
    with pytest.raises(ValueError, match="1..256"):
        artifacts.write_artifact(tmp_path, "a", "x")
    path = tmp_path / "invalid.tar"
    path.touch()
    with pytest.raises(ValueError, match="1..256"):
        artifacts.ArchiveSink(path)
    assert path.read_bytes() == b""


def test_archive_ceiling_is_enforced_by_kernel_rlimit(tmp_path):
    path = tmp_path / "artifacts.tar"
    path.touch()
    code = (
        "import resource, sys\n"
        "sys.path.insert(0, 'scripts')\n"
        "import capacity_artifacts as artifacts\n"
        "resource.setrlimit(resource.RLIMIT_FSIZE, (65536, resource.getrlimit(resource.RLIMIT_FSIZE)[1]))\n"
        f"sink = artifacts.ArchiveSink({str(path)!r})\n"
        "try:\n"
        "    sink.write('big.log', 'x' * 200000)\n"
        "except OSError as error:\n"
        "    print('errno', error.errno)\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "errno 27"  # EFBIG from the kernel, not a program check.
    assert path.stat().st_size <= 65536
    assert resource.getrlimit(resource.RLIMIT_FSIZE)[0] != 65536


MOUNTINFO = (
    "100 90 0:50 / / ro,relatime master:1 - overlay overlay rw,lowerdir=/l,upperdir=/u,workdir=/w\n"
    "101 100 0:51 / /tmp rw,nosuid,nodev - tmpfs tmpfs rw,size=1048576k,uid=1002\n"
    "102 100 0:52 / /dev rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755\n"
    "103 100 0:53 / /dev/shm rw,nosuid - tmpfs shm rw,size=16384k\n"
    "104 100 0:54 / /proc rw,nosuid - proc proc rw\n"
    "105 100 0:55 / /proc/acpi ro,relatime - tmpfs tmpfs ro,size=4k\n"
    "106 100 253:0 /var/lib/docker/containers/x/hosts /etc/hosts rw,relatime - xfs /dev/root rw\n"
    "107 100 253:0 /home/u/out.tar /home/u/out.tar rw,relatime - xfs /dev/root rw\n"
    "108 105 0:52 /null /proc/kcore rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755\n"
    "109 100 0:26 /docker.sock /run/docker.sock rw,nosuid - tmpfs tmpfs rw,size=4752188k\n"
)


def test_writable_storage_bounds_tmpfs_once_per_device_and_flags_unexpected_writes():
    mounts = artifacts.parse_mountinfo(MOUNTINFO)
    bounded, unbounded = artifacts.writable_storage(mounts, allowed={"/run/docker.sock"})
    # /proc/kcore is a file bind from /dev's tmpfs: same device, counted once.
    assert bounded == {"/tmp": 1024 ** 3, "/dev": 64 * 1024 ** 2, "/dev/shm": 16 * 1024 ** 2}
    assert unbounded == ["/home/u/out.tar"]
    assert artifacts.writable_storage(mounts, allowed={"/home/u/out.tar", "/run/docker.sock"})[1] == []
    assert "/run/docker.sock" in artifacts.writable_storage(mounts)[0]  # Never silently excluded.


def test_writable_root_and_unsized_tmpfs_are_rejected():
    rw_root = MOUNTINFO.replace("/ / ro,", "/ / rw,")
    assert "/" in artifacts.writable_storage(artifacts.parse_mountinfo(rw_root))[1]
    with pytest.raises(ValueError, match="size"):
        artifacts.writable_storage(artifacts.parse_mountinfo("1 0 0:1 / /x rw - tmpfs tmpfs rw\n"))
