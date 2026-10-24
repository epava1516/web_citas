"""Finite owned real-pipe/fork probes; no HTTP capacity or external delivery."""
import argparse
import json
import os
import select
import signal
import subprocess
import sys
import threading
from pathlib import Path

CHILD = r'''
import json,logging.config,os,sys,threading,time,warnings
from config.settings import LOGGING
logging.config.dictConfig(LOGGING)
from apps.core import operational_events as events
from apps.core.operational_event_handler import NonBlockingOperationalHandler
handler=events.logger.handlers[0]
assert isinstance(handler,NonBlockingOperationalHandler) and not events.logger.propagate
assert os.get_blocking(2)
def say(stage,**values):print(json.dumps(dict(stage=stage,**values)),flush=True)
def emit():events.publication_read({'route':'state','reason':'trusted_state'},200)
def until(predicate):
 end=time.monotonic()+3
 while time.monotonic()<end:
  if predicate():return
  time.sleep(.005)
 raise AssertionError('Owned transport observation timed out')
say('ready')
scenario=sys.argv[1]
if scenario=='retirement-fork':
 emit();until(lambda:handler.transport_status()['written']==1)
 fd=handler._fd;real_close=os.close;retired=threading.Event();release=threading.Event();fork_done=threading.Event();first=[True]
 def held_close(value):
  if value==fd and first[0]:
   first[0]=False;real_close(value)
   replacement=os.open('/dev/null',os.O_RDONLY)
   if replacement!=fd:os.dup2(replacement,fd);real_close(replacement)
   retired.set()
   assert release.wait(3)
  else:real_close(value)
 os.close=held_close
 try:
  handler.close();assert retired.wait(3)
  def forked():
   with warnings.catch_warnings():
    warnings.simplefilter('ignore',DeprecationWarning);pid=os.fork()
   if pid==0:
    try:
     handler.close();os.fstat(fd);say('race_child_ok')
    except BaseException:os._exit(2)
    os._exit(0)
   _,status=os.waitpid(pid,0);assert os.waitstatus_to_exitcode(status)==0
   fork_done.set()
  thread=threading.Thread(target=forked);thread.start()
  time.sleep(.15);assert not fork_done.is_set()
  release.set();thread.join(3);assert not thread.is_alive() and fork_done.is_set()
  handler._thread.join(3);assert not handler._thread.is_alive()
  say('race_done',reused_descriptor_survived=True)
 finally:
  release.set();os.close=real_close
  real_close(fd)
else:
 start=time.monotonic()
 for _ in range(1000):emit()
 elapsed=time.monotonic()-start
 status=handler.transport_status()
 assert status['queued']<=256 and status['dropped']>=743 and status['inflight']<=1
 assert os.get_blocking(2)
 say('producer_returned',elapsed=elapsed,status=status)
 if scenario=='blocked-close':
  start=time.monotonic();handler.close();say('closed',elapsed=time.monotonic()-start)
 else:
  until(lambda:handler.transport_status()['inflight']==1)
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',DeprecationWarning);pid=os.fork()
  if pid==0:
   emit();state=handler.transport_status()
   assert state['dropped']==0 and state['queued']<=1 and state['written']==0
   say('fork_child_reset');os._exit(0)
  _,status=os.waitpid(pid,0);assert os.waitstatus_to_exitcode(status)==0
  say('fork_done')
  assert sys.stdin.readline()=='drain\n'
  until(lambda:handler.transport_status()['queued']==0 and handler.transport_status()['inflight']==0)
  say('drained',status=handler.transport_status())
  handler.close();handler._thread.join(3);assert not handler._thread.is_alive()
  say('closed',elapsed=0)
'''


def run_probe(scenario):
    read_fd, write_fd = os.pipe()
    filled = 0
    if scenario != "retirement-fork":
        os.set_blocking(write_fd, False)
        while True:
            try:
                filled += os.write(write_fd, b"x" * 4096)
            except BlockingIOError:
                break
        os.set_blocking(write_fd, True)
    process = subprocess.Popen(
        [sys.executable, "-c", CHILD, scenario], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=write_fd, bufsize=0, start_new_session=True,
    )
    os.close(write_fd)
    drained_chunks, reader_errors = [], []
    reader = None
    def collect_sink():
        try:
            total = 0
            while True:
                part = os.read(read_fd, 65536)
                if not part:
                    return
                total += len(part)
                assert total <= 1024 * 1024
                drained_chunks.append(part)
        except Exception as error:
            reader_errors.append(type(error).__name__)
    def receive(timeout=3):
        assert select.select([process.stdout], [], [], timeout)[0], "Owned child observation timed out"
        line = process.stdout.readline()
        assert line, "Owned child terminated before observation"
        return json.loads(line)
    try:
        assert receive(10)["stage"] == "ready"
        if scenario == "retirement-fork":
            assert receive()["stage"] == "race_child_ok"
            assert receive()["stage"] == "race_done"
            proof = {"scenario": scenario, "reused_descriptor_survived": True}
        else:
            returned = receive()
            assert returned["stage"] == "producer_returned" and returned["elapsed"] < 1
            proof = {"scenario": scenario, "filled_pipe_bytes": filled,
                     "producer_seconds": returned["elapsed"], "saturated_status": returned["status"]}
            if scenario == "recovery-fork":
                assert receive()["stage"] == "fork_child_reset"
                assert receive()["stage"] == "fork_done"
                remaining = filled
                while remaining:
                    remaining -= len(os.read(read_fd, remaining))
                reader = threading.Thread(target=collect_sink, daemon=True)
                reader.start()
                process.stdin.write(b"drain\n")
                drained = receive()
                assert drained["stage"] == "drained"
                proof.update(fork_child_reset=True, drained_status=drained["status"])
            closed = receive()
            assert closed["stage"] == "closed" and closed["elapsed"] < 1
        assert process.wait(timeout=3) == 0
        if scenario == "recovery-fork":
            reader.join(3)
            assert not reader.is_alive() and not reader_errors
            rows = [json.loads(line) for line in b"".join(drained_chunks).splitlines()]
            received = sum(row.get("event") == "publication_read" for row in rows)
            assert received == proof["drained_status"]["written"] == 1000 - proof["saturated_status"]["dropped"]
            proof["received_publication_events"] = received
            assert any(row.get("event") == "transport_gap" and row["dropped_events"] >= 743 for row in rows)
            proof["transport_gap_seen"] = True
        proof.update(child_terminal=True, scope="owned_real_pipe_not_HTTP_capacity")
        return proof
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)
        process.stdin.close()
        process.stdout.close()
        if reader is not None:
            reader.join(3)
        os.close(read_fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=("recovery-fork", "blocked-close", "retirement-fork"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    proof = run_probe(options.scenario)
    options.output.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof))


if __name__ == "__main__":
    main()
