"""Unit guards for mode separation and complete lifecycle; no runtime proof."""

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("check_capacity_environment"), importlib.import_module(
        "run_capacity_environment"
    )


def test_preflight_is_explicit_same_whole_budget_and_has_no_workload(modules):
    controller, _ = modules
    args, allocation, _ = controller.parse_options(
        ["--owned-controller", "--object-delivery", "--preflight-only"]
    )
    assert args.preflight_only and args.object_delivery
    assert sum(cpu for cpu, _ in allocation.values()) + 5000 == 400000
    assert sum(memory for _, memory in allocation.values()) + 128 == 8192
    assert set(allocation) == {"app", "pg", "redis", "objects", "caddy"}
    assert not any(
        (
            args.control,
            args.fixture_target,
            args.selection_tcp,
            args.delivery_complete,
            args.delivery_profile_full,
            args.source_profile,
        )
    )


@pytest.mark.parametrize(
    "flag",
    [
        "--control",
        "--diagnose",
        "--fixture-target",
        "--selection-tcp",
        "--selection-concurrent",
        "--selection-gunicorn",
        "--selection-profile",
        "--database-heavy",
        "--selection-complete",
        "--delivery-complete",
        "--delivery-profile",
        "--delivery-profile-full",
        "--source-profile",
    ],
)
def test_preflight_rejects_every_load_and_instrumentation_flag(modules, flag):
    controller, _ = modules
    with pytest.raises(SystemExit) as error:
        controller.parse_options(
            ["--owned-controller", "--object-delivery", "--preflight-only", flag]
        )
    assert error.value.code == 2


@pytest.mark.parametrize(
    "flags",
    [
        ["--preflight-only"],
        ["--owned-controller", "--preflight-only"],
        ["--object-delivery", "--preflight-only"],
        ["--owned-controller", "--object-delivery"],
    ],
)
def test_preflight_and_object_writer_cannot_bypass_owned_mode(modules, flags):
    with pytest.raises(SystemExit) as error:
        modules[0].parse_options(flags)
    assert error.value.code == 2


def test_invalid_launcher_flags_stop_before_output_or_docker(modules, monkeypatch):
    _, launcher = modules
    monkeypatch.setattr(sys, "argv", ["run_capacity_environment.py", "--preflight-only"])
    monkeypatch.setattr(
        launcher, "host_tools", lambda: pytest.fail("Invalid mode must not reach host tools")
    )
    with pytest.raises(SystemExit) as error:
        launcher.main()
    assert error.value.code == 2


@pytest.mark.parametrize("objects", [False, True])
def test_normal_and_recovery_inventory_names_all_own_resources(modules, objects):
    _, launcher = modules
    resources = launcher.owned_resources("synthetic-own", objects)
    roles = {name.rsplit("-", 1)[1] for name in resources["containers"]}
    assert roles == (
        {"controller", "app", "redis", "pg", "caddy", "objects"}
        if objects
        else {"controller", "app", "redis", "pg"}
    )
    assert resources["volumes"] == (
        ["web-modelos-capacity-synthetic-own-delivery"] if objects else []
    )
    assert resources["network"] == "web-modelos-capacity-synthetic-own-net"


def test_recovery_removes_proxy_objects_and_shared_volume_and_detects_leftover(
    modules, monkeypatch, tmp_path
):
    _, launcher = modules
    run = "synthetic-recovery"
    resources = launcher.owned_resources(run, True)
    output = tmp_path / "artifacts/capacity-environment" / run
    output.mkdir(parents=True)
    started = {
        "pid": 1,
        "start_ticks": 0,
        "controller": resources["containers"][0],
        "owned": resources["containers"],
        "volumes": resources["volumes"],
        "network": resources["network"],
    }
    (output / "launcher-started.json").write_text(json.dumps(started))
    (output / "controller.log").write_text("synthetic unit lifecycle")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "process_start_ticks", lambda pid: 1)
    monkeypatch.setattr(launcher, "extract", lambda archive, out: ({}, []))
    monkeypatch.setattr(launcher.shutil, "which", lambda name: "unit-docker")
    monkeypatch.setattr(launcher, "absent", lambda docker, kind, name: True)
    commands = []

    def command(argv, **kwargs):
        commands.append(argv)
        # Simulated leftover volume proves the recovery verdict stays fail closed.
        return SimpleNamespace(
            returncode=0,
            stdout="leftover-own-volume" if argv[1:3] == ["volume", "ls"] else "",
            stderr="",
        )

    monkeypatch.setattr(launcher.subprocess, "run", command)
    assert launcher.recover(run) == 1
    for container in resources["containers"]:
        assert ["unit-docker", "rm", "-fv", container] in commands
    assert ["unit-docker", "volume", "rm", resources["volumes"][0]] in commands
    recovered = json.loads((output / "launcher-recovered.json").read_text())
    assert recovered["cleanup"]["no_labelled_resources"] is False
    assert recovered["written_by"].startswith("run_capacity_environment.py --recover")
