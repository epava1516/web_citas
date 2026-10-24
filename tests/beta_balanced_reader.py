"""Finite balanced native-reader controls; caller owns explicit scope and parity."""

import hashlib
import itertools
import json
import statistics
import time
from pathlib import Path

from django.db import connection

from scripts.benchmark_owned_backend_cpu import backend_snapshot, owned_backend


def compare_records(records):
    comparisons = {}
    for route in sorted({r["route"] for r in records}):
        selected = [r for r in records if r["route"] == route]
        metrics = {}
        for arm in "ABC":
            rows = [r for r in selected if r["arm"] == arm]
            metrics[arm] = {
                "wall": statistics.median(s["wall_seconds"] for r in rows for s in r["samples"]),
                "app_cpu": statistics.median(s["thread_cpu_seconds"] for r in rows for s in r["samples"]),
                "pg_cpu_per_read": sum(r["backend_cpu_seconds"] for r in rows) / 18,
            }
        stable = all(abs(metrics["A"][key] / metrics["B"][key] - 1) <= 0.10 for key in metrics["A"])
        ratios = {key: metrics["C"][key] / ((metrics["A"][key] + metrics["B"][key]) / 2)
                  for key in metrics["A"]}
        nonregressing = 0
        for block in range(6):
            group = {r["arm"]: statistics.median(s["wall_seconds"] for s in r["samples"])
                     for r in selected if r["block"] == block}
            nonregressing += group["C"] <= (group["A"] + group["B"]) / 2
        comparisons[route] = {
            "metrics": metrics, "ratios_C_to_AB": ratios, "AA_stable": stable,
            "nonregressing_blocks": nonregressing,
            "eligible": stable and ratios["wall"] <= 0.90 and ratios["app_cpu"] <= 1.05
            and ratios["pg_cpu_per_read"] <= 1.05 and nonregressing >= 4,
        }
    return comparisons


def balanced_reads(routes, read, set_arm, runner, inspection):
    records, signatures = [], {}
    for route, path in routes:
        for block, order in enumerate(itertools.permutations("ABC")):
            for arm in order:
                set_arm(arm)
                connection.close()
                signature = read(path)  # One warm read per physical backend, outside controls.
                signatures.setdefault(route, signature)
                assert signature == signatures[route]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    sql_pid = cursor.fetchone()[0]
                identity = owned_backend(runner, inspection, sql_pid)

                def snapshot():
                    state = backend_snapshot(identity)
                    sched = list(map(int, Path(f"/proc/{identity['pid']}/schedstat").read_text().split()))
                    return state | {"runtime_ns": sched[0], "wait_ns": sched[1]}

                before = snapshot()
                samples = []
                for _ in range(3):
                    start, cpu = time.perf_counter(), time.thread_time()
                    actual = read(path)
                    wall, used_cpu = time.perf_counter() - start, time.thread_time() - cpu
                    assert actual == signature
                    samples.append({"wall_seconds": wall, "thread_cpu_seconds": used_cpu,
                                    "signature_sha256": hashlib.sha256(json.dumps(actual).encode()).hexdigest()})
                after = snapshot()
                assert after["runtime_ns"] >= before["runtime_ns"] > 0
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    assert cursor.fetchone()[0] == sql_pid
                records.append({"route": route, "block": block, "order": "".join(order), "arm": arm,
                                "samples": samples, "backend_identity": identity, "before": before, "after": after,
                                "backend_cpu_seconds": (after["runtime_ns"] - before["runtime_ns"]) / 1e9,
                                "backend_wait_seconds": (after["wait_ns"] - before["wait_ns"]) / 1e9})
    assert len(records) == 36 and sum(len(r["samples"]) for r in records) == 108
    return records, signatures, compare_records(records)
