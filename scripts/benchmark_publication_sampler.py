"""1 Hz sampler of MOD05 invalidation state in an owned synthetic database.

Records pending dirty marks, the age of the oldest one and the mark sequence (each mark or
re-mark draws one value), on the database clock. Read-only; samples are states, not
durations. Same instrument in every refresh scenario.
"""

import json
import threading
import time
from pathlib import Path

import psycopg


class PublicationSampler:
    def __init__(self, output, db, interval=1.0):
        self.output, self.db, self.interval = Path(output), dict(db), interval
        self.stop = threading.Event()
        self.phase = "idle_before"
        self.error = None
        self.timings = []

    def start(self):
        self.thread = threading.Thread(target=self.run, name="owned-publication-sampler", daemon=True)
        self.thread.start()

    def run(self):
        origin = time.monotonic()
        count = 0
        try:
            with psycopg.connect(dbname=self.db["NAME"], user=self.db["USER"],
                                 password=self.db["PASSWORD"], host=self.db["HOST"],
                                 port=self.db["PORT"], autocommit=True,
                                 application_name="owned_publication_sampler",
                                 options="-c statement_timeout=1000") as db, \
                    self.output.open("w") as stream:
                while not self.stop.is_set():
                    start = time.monotonic()
                    dirty, oldest, now = db.execute(
                        "SELECT count(*), extract(epoch from clock_timestamp() - min(marked_at)), "
                        "extract(epoch from clock_timestamp()) FROM listings_publicationdirty"
                    ).fetchone()
                    generation = db.execute(
                        "SELECT last_value FROM listings_publication_generation").fetchone()[0]
                    stream.write(json.dumps({
                        "monotonic": start, "phase": self.phase, "dirty": dirty,
                        "oldest_mark_age_seconds": None if oldest is None else float(oldest),
                        "db_epoch": float(now), "generation_last_value": generation,
                    }, separators=(",", ":")) + "\n")
                    stream.flush()
                    self.timings.append(time.monotonic() - start)
                    count += 1
                    self.stop.wait(max(0, origin + count * self.interval - time.monotonic()))
        except Exception as exc:
            self.error = type(exc).__name__

    def close(self):
        self.stop.set()
        self.thread.join(timeout=5)
        Path(str(self.output) + ".summary.json").write_text(json.dumps({
            "samples": len(self.timings), "error": self.error,
            "collection_seconds_max": max(self.timings, default=None),
            "collection_seconds_sum": sum(self.timings),
            "scope": "1 Hz state samples on the database clock; overhead of the collector "
                     "connection not causally quantified.",
        }, indent=2))
