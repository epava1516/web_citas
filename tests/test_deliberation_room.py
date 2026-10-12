"""Room controls with service doubles; no claim of external-model verification."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "deliberation_room", Path(__file__).resolve().parents[1] / "scripts/deliberation_room.py"
)
room = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(room)


class RoomControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        (self.path / "events.jsonl").touch()
        self.config = {"title": "Test", "notebook_id": "test", "max_external_turns": 2}
        (self.path / "room.json").write_text(json.dumps(self.config))
        self.prompt = self.path / "question.txt"
        self.prompt.write_text("Review only")

    def args(self, speaker="notebook"):
        return type("Args", (), {"speaker": speaker, "file": str(self.prompt), "timeout": 30})()

    def test_invalid_room_paths(self):
        for name in ("../other", "/tmp/room", "a/b", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                room.room_path(name)

    def test_claude_requires_recorded_exception(self):
        with patch.object(room, "execute") as execute, self.assertRaises(ValueError):
            room.ask(self.path, self.config, self.args("claude"))
        execute.assert_not_called()
        self.assertEqual(room.load_events(self.path), [])

    def test_failed_requests_also_count_toward_bound(self):
        for _ in range(2):
            room.append(self.path, "codex", "request", "failed request")
        with patch.object(room, "execute") as execute, self.assertRaises(ValueError):
            room.ask(self.path, self.config, self.args())
        execute.assert_not_called()

    def test_conversation_is_reused_and_opinion_is_unverified(self):
        room.append(self.path, "notebook", "opinion", "prior", conversation_id="conversation")
        response = json.dumps({"answer": "Do not apply yet", "conversation_id": "conversation"})
        with patch.object(room, "execute", return_value=(0, response, "", 1.25)) as execute:
            room.ask(self.path, self.config, self.args())
        command = execute.call_args.args[0]
        self.assertEqual(command[-2:], ["--conversation-id", "conversation"])
        event = room.load_events(self.path)[-1]
        self.assertFalse(event["verified"])
        self.assertEqual(event["text"], "Do not apply yet")
        self.assertTrue((self.path / event["raw"]).is_file())

    def test_invalid_response_is_preserved_without_retry(self):
        with patch.object(room, "execute", return_value=(1, "not JSON", "failed", 0.5)) as call:
            with self.assertRaises(ValueError):
                room.ask(self.path, self.config, self.args())
        self.assertEqual(call.call_count, 1)
        self.assertEqual(room.load_events(self.path)[-1]["kind"], "error")
        self.assertEqual((self.path / "turn-01-notebook-response.json").read_text(), "not JSON")

    def test_claude_command_disables_tools_and_logs_reported_usage(self):
        self.config["claude_exception"] = "Explicit user authorization"
        tasks = self.path / ".ai/tasks"
        tasks.mkdir(parents=True)
        log = tasks / "desarrollo.md"
        log.write_text("Historical consumption\n")
        response = json.dumps({"result": "Opinion", "usage": {"output_tokens": 12},
                               "modelUsage": {"model": {}}, "total_cost_usd": 0.01})
        with patch.object(room, "ROOT", self.path), patch.object(
            room, "execute", return_value=(0, response, "", 1.0)
        ) as execute:
            room.ask(self.path, self.config, self.args("claude"))
        command = execute.call_args.args[0]
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--mcp-config") + 1], '{"mcpServers":{}}')
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--safe-mode", command)
        self.assertEqual(room.load_events(self.path)[-1]["usage"], {"output_tokens": 12})
        self.assertTrue(log.read_text().startswith("Historical consumption\n"))

    def test_web_research_requires_separate_explicit_authorization(self):
        self.config["claude_exception"] = "Previous tool-free review authorization"
        args = self.args("claude")
        args.web_research = True
        with patch.object(room, "execute") as execute, self.assertRaises(ValueError):
            room.ask(self.path, self.config, args)
        execute.assert_not_called()
        self.assertEqual(room.load_events(self.path), [])

    def test_web_command_enables_only_public_web_and_keeps_mcp_empty(self):
        self.config.update(claude_exception="Review", claude_web_exception="User asks each to research online")
        tasks = self.path / ".ai/tasks"
        tasks.mkdir(parents=True)
        (tasks / "desarrollo.md").write_text("Historical consumption\n")
        args = self.args("claude")
        args.web_research = True
        response = json.dumps({"result": "Opinion with links", "usage": {}})
        with patch.object(room, "ROOT", self.path), patch.object(
            room, "execute", return_value=(0, response, "", 1.0)
        ) as execute:
            room.ask(self.path, self.config, args)
        command = execute.call_args.args[0]
        self.assertEqual(command[command.index("--tools")+1], "WebSearch,WebFetch")
        self.assertEqual(command[command.index("--allowedTools")+1], "WebSearch,WebFetch")
        self.assertEqual(command[command.index("--permission-mode")+1], "dontAsk")
        self.assertEqual(command[command.index("--mcp-config")+1], '{"mcpServers":{}}')
        self.assertIn("--safe-mode", command)
        self.assertNotIn("Sin herramientas,", execute.call_args.args[1])

    def test_room_lock_serializes_writers(self):
        with room.locked(self.path):
            with self.assertRaises(BlockingIOError), room.locked(self.path):
                self.fail("Concurrent writer must not enter")

    def test_closed_room_rejects_new_external_calls(self):
        self.config["closed"] = "done"
        with patch.object(room, "execute") as execute, self.assertRaises(ValueError):
            room.ask(self.path, self.config, self.args())
        execute.assert_not_called()

    def test_timeout_reaps_local_process(self):
        pid_file = self.path / "pid"
        code = ("import os,sys,time; from pathlib import Path; "
                "Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(30)")
        with self.assertRaises(subprocess.TimeoutExpired):
            room.execute([sys.executable, "-c", code, str(pid_file)], None, 0.5)
        pid = int(pid_file.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)


if __name__ == "__main__":
    unittest.main()
