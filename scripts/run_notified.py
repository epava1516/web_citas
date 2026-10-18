"""Run a non-pytest test command and notify Telegram after its terminal result."""
import argparse
import os
import subprocess
import time

from test_notifications import notify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("A test command is required after --")
    started = time.monotonic()
    code = 1
    try:
        code = subprocess.call(command, env={**os.environ, "LOCAL_CI_TELEGRAM_OWNER": "runner"})
        return code
    finally:
        receipt = notify(args.name, "PASS" if code == 0 else f"EXIT {code}",
                         seconds=time.monotonic() - started)
        if receipt["delivery"] != "sent":
            print("Telegram: envío fallido; recibo en artifacts/test-notifications", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
