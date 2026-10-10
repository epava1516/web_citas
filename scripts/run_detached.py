"""Start a long local verification in its own session, detached from the caller.

Closing the terminal or agent session that launched it signals that session's process
group; the detached run is not in it and keeps writing its own durable evidence. The
launch record names the exact process to supervise; no output is reconstructed later.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def process_start_ticks(pid):
    """Kernel start time of a process, so a reused PID is never mistaken for the run."""
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return int(fields[19])


def alive(pid, start_ticks):
    try:
        return process_start_ticks(pid) == start_ticks
    except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True, help="New file receiving all output")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- program arguments...")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("A command is required after --")
    if args.log.exists():
        parser.error("Refusing to append to an existing log")
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("xb") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    record = {
        "pid": process.pid,
        "start_ticks": process_start_ticks(process.pid),
        "session": os.getsid(process.pid),
        "command": command,
        "cwd": str(ROOT),
        "log": str(args.log.resolve()),
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    launch = args.log.with_name(args.log.name + ".launch.json")
    temporary = launch.with_name(launch.name + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    os.replace(temporary, launch)
    print(json.dumps(record), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
