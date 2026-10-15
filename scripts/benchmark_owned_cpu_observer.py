"""Opt-in counters for an exact owned CI PostgreSQL and controller cgroup.

No process enumeration, SQL, credentials, normal services or cgroup writes.
CPU counters describe execution/quota, never per-request waiting or causality.
"""

import json
import os
import re
import threading
import time
from pathlib import Path

COUNTERS = ("usage_usec", "user_usec", "system_usec", "nr_periods", "nr_throttled", "throttled_usec")


def owned_pg_pid(run, inspection):
    if not re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{8}", run["id"]):
        raise ValueError("Exact owned run required")
    name = "web-modelos-ci-pg-" + run["id"]
    if (name not in run["containers"] or inspection["Name"] != "/" + name
            or inspection["Config"]["Labels"].get("web-modelos-local-ci-run") != run["id"]
            or not inspection["State"]["Running"]):
        raise ValueError("Owned PostgreSQL identity mismatch")
    pid = inspection["State"]["Pid"]
    if type(pid) is not int or pid <= 1:
        raise ValueError("Live owned PostgreSQL PID required")
    return pid


def cpu_counters(text):
    values = {}
    for line in text.splitlines():
        key, value = line.split()
        if key in COUNTERS:
            if key in values or not value.isdecimal():
                raise ValueError("Invalid CPU counter")
            values[key] = int(value)
    if "usage_usec" not in values:
        raise ValueError("CPU usage missing")
    return values


def cpu_delta(before, after):
    dt = after["monotonic"] - before["monotonic"]
    a, b = before["cpu_stat"], after["cpu_stat"]
    if dt <= 0 or any(b.get(k, -1) < v for k, v in a.items()):
        raise ValueError("CPU counter reset or invalid interval")
    delta = {k: b[k] - v for k, v in a.items()}
    return {"elapsed_seconds": dt, "execution_cpu_cores": delta["usage_usec"] / 1e6 / dt,
            "counter_delta": delta}


def group_path(pid):
    membership = Path(f"/proc/{pid}/cgroup").read_text().strip()
    lines = [line[3:] for line in membership.splitlines() if line.startswith("0::")]
    if len(lines) != 1 or lines[0] == "/" or ".." in Path(lines[0]).parts:
        raise ValueError("Exact cgroup v2 membership required")
    return Path("/sys/fs/cgroup") / lines[0].lstrip("/")


def read_group(path):
    # Only fixed files in the two verified leaf groups, never their ancestors.
    result = {"monotonic": time.monotonic(),
              "cpu_stat": cpu_counters((path / "cpu.stat").read_text())}
    for name in ("cpu.max", "cpuset.cpus.effective", "memory.events"):
        try:
            result[name] = (path / name).read_text().strip()
        except FileNotFoundError:
            result[name] = "not_exposed"
    return result


class OwnedCPUObserver:
    def __init__(self, output, run, inspection):
        pg_pid = owned_pg_pid(run, inspection)
        if run["pid"] != os.getpid():
            raise ValueError("Observer must run in its owned controller")
        fields = Path(f"/proc/{run['pid']}/stat").read_text().rsplit(")", 1)[1].split()
        if int(fields[19]) != run["start_ticks"]:
            raise ValueError("Controller PID was reused")
        self.groups = {"controller": group_path(run["pid"]), "postgres": group_path(pg_pid)}
        if (not self.groups["controller"].name.startswith("cr09-owned-cpu-diagnose-")
                or inspection["Id"] not in str(self.groups["postgres"])):
            raise ValueError("Dedicated diagnostic cgroups required")
        self.output = Path(output)
        self.stop = threading.Event()
        self.summary = {"run": run["id"], "samples": 0, "error_type": None,
                        "groups": {k: str(v) for k, v in self.groups.items()},
                        "scope": "Own leaf cgroups only; controller includes generator/pytest/Celery/app/collector. No request attribution or causal profiling overhead measured."}

    def start(self):
        if self.output.exists():
            raise ValueError("Fresh diagnostic output required")
        for path in self.groups.values():
            read_group(path)
        self.thread = threading.Thread(target=self.run, daemon=True, name="owned-cpu-counters")
        self.thread.start()

    def run(self):
        begin = time.thread_time()
        try:
            with self.output.open("x") as stream:
                for _ in range(1200):
                    record = {name: read_group(path) for name, path in self.groups.items()}
                    stream.write(json.dumps(record) + "\n")
                    stream.flush()
                    self.summary["samples"] += 1
                    if self.stop.wait(1):
                        break
                else:
                    raise RuntimeError("Bounded CPU observation exceeded")
        except Exception as error:
            self.summary["error_type"] = type(error).__name__
        finally:
            self.summary["collector_thread_cpu_seconds"] = time.thread_time() - begin
            self.output.with_suffix(".summary.json").write_text(json.dumps(self.summary, indent=2) + "\n")

    def close(self):
        self.stop.set()
        self.thread.join(5)
        if self.thread.is_alive():
            raise RuntimeError("Owned CPU observer did not stop")
