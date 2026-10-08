"""Read-only1Hz resource snapshots for one owned local resource checkpoint.

No argv, environment, query text/parameters, usernames or real DB row values.
Process CPU uses /proc ticks; PG cgroup usage includes the shared service, so
it cannot all be attributed to this workload. Wait samples are observations,
never duration counters. Missing kernel interfaces are explicit.
"""

import json
import os
import threading
import time
from pathlib import Path

import psycopg


def optional_text(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, ValueError):
        return "not_measured"


def process_snapshot(pid):
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        name, rest = (
            text[text.index("(") + 1 : text.rindex(")")],
            text[text.rindex(")") + 2 :].split(),
        )
        membership = optional_text(f"/proc/{pid}/cgroup")
        group = next(
            (line[3:] for line in membership.splitlines() if line.startswith("0::")), "not_measured"
        )
        result = {
            "pid": pid,
            "comm": name,
            "ppid": int(rest[1]),
            "start_ticks": int(rest[19]),
            "cpu_ticks": int(rest[11]) + int(rest[12]),
            "rss_bytes": int(rest[21]) * os.sysconf("SC_PAGE_SIZE"),
            "cgroup": group,
        }
        if name == "postgres":
            status = optional_text(f"/proc/{pid}/status")
            result["namespace_pids"] = next(
                (
                    [int(n) for n in line.split()[1:]]
                    for line in status.splitlines()
                    if line.startswith("NSpid:")
                ),
                [],
            )
        return result
    except (OSError, ValueError, IndexError):
        return None


def cgroup_chain(group):
    if group == "not_measured":
        return {}
    base = Path("/sys/fs/cgroup")
    path = base / group.lstrip("/")
    result = {}
    while True:
        result[str(path.relative_to(base))] = {
            name: optional_text(path / name)
            for name in [
                "cpu.max",
                "cpu.stat",
                "cpu.weight",
                "cpuset.cpus.effective",
                "memory.max",
                "memory.high",
                "memory.current",
                "memory.events",
                "memory.swap.current",
                "memory.swap.max",
                "cpu.pressure",
                "memory.pressure",
                "io.pressure",
                "io.stat",
            ]
        }
        if path == base:
            return result
        path = path.parent


class TrialLimits:
    """Only an explicitly opted-in trial can request an emergency stop."""

    def __init__(self, limits):
        self.limits = limits
        self.requested = threading.Event()
        self.reason = None
        self.previous = None
        self.cpu_streak = 0
        self.oom_baseline = {}

    def observe(self, record, hz):
        reason = None
        available = record["meminfo"].get("MemAvailable")
        if available is not None and available < self.limits["stop_mem_available_below_bytes"]:
            reason = "MemAvailable_below_limit"
        for scope in ["app_cgroups", "pg_cgroups"]:
            chain = record[scope]
            if not isinstance(chain, dict):
                continue
            for path, values in chain.items():
                for line in values["memory.events"].splitlines():
                    parts = line.split()
                    if len(parts) == 2 and parts[0] in {"oom", "oom_kill", "oom_group_kill"}:
                        key = (scope, path, parts[0])
                        current = int(parts[1])
                        baseline = self.oom_baseline.setdefault(key, current)
                        if current > baseline:
                            reason = "new_oom_event"
        if self.previous is not None:
            dt = record["monotonic"] - self.previous["monotonic"]
            ticks = sum(record["host_cpu_ticks"][i] - self.previous["host_cpu_ticks"][i]
                        for i in [0, 1, 2, 5, 6])
            execution = ticks / hz / dt
            record["host_execution_cpu_cores_since_previous_sample"] = execution
            self.cpu_streak = (self.cpu_streak + 1 if execution >=
                self.limits["stop_owned_trial_if_host_execution_CPU_cores_at_least"] else 0)
            if self.cpu_streak >= self.limits["sustained_samples_for_CPU_stop"]:
                reason = "host_execution_CPU_sustained_limit"
        self.previous = record
        if reason and not self.requested.is_set():
            self.reason = {"reason": reason, "monotonic": record["monotonic"]}
            self.requested.set()
        record["trial_stop"] = self.reason


class ResourceProbe:
    def __init__(self, output, db, app_master, pg_pid, *, trial_limits=None):
        self.output = Path(output)
        self.db = dict(db)
        self.app_master, self.pg_pid = app_master, pg_pid
        self.stop = threading.Event()
        self.started = threading.Event()
        self.phase = "idle_before"
        self.error = None
        self.trial_limits = TrialLimits(trial_limits) if trial_limits else None

    def start(self):
        self.thread = threading.Thread(target=self.run, name="owned-resource-probe", daemon=True)
        self.thread.start()
        if not self.started.wait(5):
            raise RuntimeError("Resource sampler failed startup")
        if self.error:
            raise RuntimeError(self.error)

    def run(self):
        clock = time.monotonic()
        cpu_start = time.thread_time()
        count, timings, errors = 0, [], []
        try:
            with psycopg.connect(
                dbname=self.db["NAME"],
                user=self.db["USER"],
                password=self.db["PASSWORD"],
                host=self.db["HOST"],
                port=self.db["PORT"],
                autocommit=True,
                application_name="owned_resource_checkpoint",
                options="-c statement_timeout=1000",
            ) as db:
                collector_pid = db.info.backend_pid
                self.started.set()
                with self.output.open("w") as stream:
                    while not self.stop.is_set():
                        start = time.monotonic()
                        procs = [
                            p
                            for item in Path("/proc").iterdir()
                            if item.name.isdigit()
                            and (p := process_snapshot(int(item.name))) is not None
                        ]
                        app = next((p for p in procs if p["pid"] == self.app_master), None)
                        pg = next((p for p in procs if p["pid"] == self.pg_pid), None)
                        try:
                            activity = db.execute(
                                """SELECT pid,backend_type,datname=current_database(),
                                state,wait_event_type,wait_event FROM pg_stat_activity
                                WHERE pid <> %s""",
                                [collector_pid],
                            ).fetchall()
                        except psycopg.Error as exc:
                            activity = "not_measured"
                            errors.append(type(exc).__name__)
                        stat = optional_text("/proc/stat").splitlines()
                        meminfo = {
                            line.split(":")[0]: int(line.split()[1]) * 1024
                            for line in optional_text("/proc/meminfo").splitlines()
                            if line.startswith(
                                ("MemTotal:", "MemAvailable:", "SwapTotal:", "SwapFree:")
                            )
                        }
                        record = {
                            "monotonic": start,
                            "phase": self.phase,
                            "processes": procs,
                            "host_cpu_ticks": [int(v) for v in stat[0].split()[1:9]],
                            "host_tasks": {
                                line.split()[0]: int(line.split()[1])
                                for line in stat
                                if line.startswith(("procs_running ", "procs_blocked "))
                            },
                            "loadavg": optional_text("/proc/loadavg"),
                            "host_diskstats": optional_text("/proc/diskstats"),
                            "app_process_io": {
                                str(p["pid"]): optional_text(f"/proc/{p['pid']}/io")
                                for p in procs if p["pid"] == self.app_master or p["ppid"] == self.app_master
                            },
                            "postgres_process_io": {
                                str(p["pid"]): optional_text(f"/proc/{p['pid']}/io")
                                for p in procs if pg and p["cgroup"] == pg["cgroup"]
                            },
                            "meminfo": meminfo,
                            "host_pressure": {
                                n: optional_text("/proc/pressure/" + n)
                                for n in ["cpu", "memory", "io"]
                            },
                            "vmstat": {
                                line.split()[0]: int(line.split()[1])
                                for line in optional_text("/proc/vmstat").splitlines()
                                if line.startswith(
                                    (
                                        "pswpin ",
                                        "pswpout ",
                                        "pgmajfault ",
                                        "allocstall",
                                        "pgscan_",
                                        "pgsteal_",
                                    )
                                )
                            },
                            "app_cgroups": cgroup_chain(app["cgroup"]) if app else "not_measured",
                            "pg_cgroups": cgroup_chain(pg["cgroup"]) if pg else "not_measured",
                            "pg_activity": activity,
                            "collector_pg_pid": collector_pid,
                        }
                        if self.trial_limits:
                            self.trial_limits.observe(record, os.sysconf("SC_CLK_TCK"))
                        record["snapshot_collection_wall_seconds"] = time.monotonic() - start
                        stream.write(json.dumps(record, separators=(",", ":")) + "\n")
                        stream.flush()
                        timings.append(time.monotonic() - start)
                        count += 1
                        self.stop.wait(max(0, clock + count - time.monotonic()))
        except Exception as exc:
            self.error = type(exc).__name__ + ": resource probe failed"
            self.started.set()
        finally:
            Path(str(self.output) + ".summary.json").write_text(
                json.dumps(
                    {
                        "samples": count,
                        "elapsed": time.monotonic() - clock,
                        "collector_thread_cpu": time.thread_time() - cpu_start,
                        "sample_durations": timings,
                        "errors": errors,
                        "fatal_error": self.error,
                        "trial_stop": self.trial_limits.reason if self.trial_limits else None,
                        "clock_ticks_per_second": os.sysconf("SC_CLK_TCK"),
                        "app_master_pid": self.app_master,
                        "postgres_container_host_pid": self.pg_pid,
                        "scope": "shared host/service;1Hz state samples not wait durations; procCPU ticks and cgroupCPUcumulative counters; processRSS includes sharedpages, not additive physical memory; missingPSI explicit",
                    },
                    indent=2,
                )
                + "\n"
            )

    def close(self):
        self.stop.set()
        self.thread.join(5)
        if self.thread.is_alive():
            raise RuntimeError("Resource sampler did not stop")
