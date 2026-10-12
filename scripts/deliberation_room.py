#!/usr/bin/env python3
"""Local, bounded review room. External opinions never authorize code execution."""

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOMS = ROOT / ".ai" / "rooms"
POLICY = (
    "Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, "
    "ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. "
    "Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, "
    "omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. "
    "Propón una decisión finita y señala contraejemplos. Máximo 900 palabras."
)


def now():
    return dt.datetime.now(dt.UTC).isoformat()


def room_path(name):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", name):
        raise ValueError("Invalid room ID")
    path = ROOMS / name
    if path.resolve().parent != ROOMS.resolve():
        raise ValueError("Room must remain under .ai/rooms")
    return path


def load_events(path):
    return [json.loads(line) for line in (path / "events.jsonl").read_text().splitlines()]


def render(path):
    config = json.loads((path / "room.json").read_text())
    lines = [f"# {config['title']}", "", POLICY, ""]
    for event in load_events(path):
        lines.extend([
            f"## {event['sequence']} · {event['speaker']} · {event['kind']}",
            "", f"UTC: {event['time']}", "",
        ])
        body = event["text"]
        fence = "`" * (max([len(x) for x in re.findall(r"`+", body)] + [2]) + 1)
        lines.extend([fence + "text", body, fence, ""])
    target = path / "transcript.md"
    temporary = path / "transcript.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(target)


def append(path, speaker, kind, body, **metadata):
    events = load_events(path)
    event = dict(sequence=len(events) + 1, time=now(), speaker=speaker,
                 kind=kind, text=body, **metadata)
    with (path / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    render(path)
    return event


@contextlib.contextmanager
def locked(path):
    with (path / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def execute(command, prompt, timeout):
    start = time.monotonic()
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=ROOT, start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(prompt, timeout=timeout)
    except BaseException:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    return process.returncode, stdout, stderr, time.monotonic() - start


def ask(path, config, args):
    if config.get("closed"):
        raise ValueError("Room is closed; create a new room for another deliberation")
    events = load_events(path)
    requests = [event for event in events if event["kind"] == "request"]
    if len(requests) >= config["max_external_turns"]:
        raise ValueError("External turn limit reached; no automatic retries")
    if args.speaker == "claude" and not config.get("claude_exception"):
        raise ValueError("Claude requires the recorded user exception; adapter unavailable")
    web = getattr(args, "web_research", False)
    if web and (args.speaker != "claude" or not config.get("claude_web_exception")):
        raise ValueError("Web research requires explicit recorded Claude web-only authorization")
    policy = POLICY.replace("Sin herramientas, ", "Sólo WebSearch/WebFetch públicos; sin herramientas locales, ") if web else POLICY
    question = Path(args.file).read_text(encoding="utf-8")
    # The coordinator selects context explicitly: never silently ingest credentials or repo files.
    prompt = policy + "\n\n" + question
    if len(prompt) > 12000:
        raise ValueError("Prompt exceeds this room's local 12000-character safety bound")
    turn = len(requests) + 1
    prompt_name = f"turn-{turn:02d}-{args.speaker}-prompt.txt"
    (path / prompt_name).write_text(prompt, encoding="utf-8")
    request = append(path, "codex", "request", prompt, target=args.speaker,
                     prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
    if args.speaker == "notebook":
        command = ["nlm", "notebook", "query", config["notebook_id"], prompt,
                   "--json", "--timeout", str(args.timeout)]
        prior = [event.get("conversation_id") for event in events
                 if event["speaker"] == "notebook" and event.get("conversation_id")]
        command += ["--conversation-id", prior[-1]] if prior else ["--new-conversation"]
        stdin = None
    else:
        command = ["claude", "--print", "--output-format", "json", "--tools", "WebSearch,WebFetch" if web else "",
                   "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--disable-slash-commands", "--no-session-persistence", "--safe-mode",
                   "--setting-sources", "", "--system-prompt", policy]
        if web:
            command += ["--allowedTools", "WebSearch,WebFetch", "--permission-mode", "dontAsk"]
        stdin = prompt
        with (ROOT / ".ai/tasks/desarrollo.md").open("a", encoding="utf-8") as stream:
            stream.write(f"\n{now()}: Claude sala {path.name}, turno {turn}, "
                         f"CLI {'sólo web pública' if web else 'sin herramientas'} autorizado por excepción expresa; "
                         "invocación iniciada, tokens/coste pendientes. Sin retry automático.\n")
    try:
        code, stdout, stderr, elapsed = execute(command, stdin, args.timeout + 15)
    except BaseException as error:
        append(path, args.speaker, "error", type(error).__name__, request=request["sequence"])
        if args.speaker == "claude":
            with (ROOT / ".ai/tasks/desarrollo.md").open("a", encoding="utf-8") as stream:
                stream.write(f"\nClaude sala {path.name}, turno {turn}: "
                             f"{type(error).__name__}; consumo desconocido, no estimado.\n")
        raise
    raw_name = f"turn-{turn:02d}-{args.speaker}-response.json"
    (path / raw_name).write_text(stdout, encoding="utf-8")
    (path / f"turn-{turn:02d}-{args.speaker}-stderr.txt").write_text(stderr, encoding="utf-8")
    metadata = dict(exit_code=code, duration_s=elapsed, raw=raw_name,
                    request=request["sequence"], verified=False)
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        append(path, args.speaker, "error", "Response is not JSON; inspect raw artifact", **metadata)
        if args.speaker == "claude":
            with (ROOT / ".ai/tasks/desarrollo.md").open("a", encoding="utf-8") as stream:
                stream.write(f"\nClaude sala {path.name}, turno {turn}: JSON inválido, "
                             f"exit {code}, {elapsed:.3f}s; consumo desconocido.\n")
        raise ValueError("Invalid response JSON") from None
    if args.speaker == "claude":
        metadata.update(usage=data.get("usage"), model_usage=data.get("modelUsage"),
                        reported_cost_usd=data.get("total_cost_usd"))
        consumption = {"room": path.name, "time": now(), **metadata}
        with (ROOT / ".ai/tasks/desarrollo.md").open("a", encoding="utf-8") as stream:
            stream.write("\nSala local Claude (revisión sin herramientas; consumo declarado "
                         "por CLI, no factura): " + json.dumps(consumption, ensure_ascii=False)
                         + "\n")
        body = data.get("result", "")
        failed = code != 0 or data.get("is_error", False)
    else:
        metadata["conversation_id"] = data.get("conversation_id")
        body = data.get("answer", "")
        failed = code != 0
    if not isinstance(body, str) or not body:
        failed, body = True, "Empty answer; inspect raw artifact"
    append(path, args.speaker, "error" if failed else "opinion", body, **metadata)
    if failed:
        raise ValueError("External review failed; no automatic retry")
    print(json.dumps({"speaker": args.speaker, "duration_s": elapsed,
                      "response": str(path / raw_name)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("room")
    init.add_argument("--title", required=True)
    init.add_argument("--notebook-id", required=True)
    init.add_argument("--max-external-turns", type=int, default=4, choices=range(1, 9))
    for name in ("add", "authorize-claude", "ask", "show", "close"):
        cmd = sub.add_parser(name)
        cmd.add_argument("room")
        if name in {"ask", "authorize-claude"}:
            cmd.add_argument("--web-research", action="store_true",
                             help="Explicitly authorized public WebSearch/WebFetch only (Claude)")
        if name in {"add", "authorize-claude", "ask", "close"}:
            cmd.add_argument("--file", required=True)
        if name in {"add", "ask"}:
            cmd.add_argument("--speaker", required=True,
                             choices=("codex", "user") if name == "add"
                             else ("claude", "notebook"))
        if name == "add":
            cmd.add_argument("--kind", choices=("context", "opinion", "decision"),
                             default="opinion")
        if name == "ask":
            cmd.add_argument("--timeout", type=int, default=180, choices=range(30, 601))
    args = parser.parse_args()
    path = room_path(args.room)
    if args.command == "init":
        path.mkdir(parents=True, exist_ok=False)
        config = dict(title=args.title, notebook_id=args.notebook_id,
                      max_external_turns=args.max_external_turns, created=now())
        (path / "room.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        (path / "events.jsonl").touch()
        render(path)
        print(path)
        return
    if args.command == "show":
        # Readers can open the last complete transcript while an external turn is pending.
        print(path / "transcript.md")
        return
    with locked(path):
        config = json.loads((path / "room.json").read_text())
        if args.command == "add":
            append(path, args.speaker, args.kind, Path(args.file).read_text(encoding="utf-8"))
        elif args.command == "authorize-claude":
            text = Path(args.file).read_text(encoding="utf-8")
            append(path, "user", "authorization", text)
            config["claude_exception"] = text
            if args.web_research:
                config["claude_web_exception"] = text
            (path / "room.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        elif args.command == "ask":
            ask(path, config, args)
        elif args.command == "close":
            append(path, "codex", "decision", Path(args.file).read_text(encoding="utf-8"))
            config["closed"] = now()
            (path / "room.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
