#!/usr/bin/env python3
"""T217 follow-up 2 -- measure how long a REAL `claude -p` process takes to
exit after SIGTERM, so DRIVER_STOP_GRACE_SECS can be set from a measurement
instead of a guess (T211 calibrated it against a `/bin/sleep` stand-in that
dies instantly, which cannot answer this question by construction).

Spawns the real claude binary (same one CLAUDE_BIN defaults to in
fire-program.sh: $HOME/.local/bin/claude), own session, default signal
dispositions (the same P-55 control T211's spawn.py used), sends SIGTERM at a
chosen delay, and reports signal-to-exit latency. Every trial makes one real
API call -- cost and trial count are kept deliberately small.

usage: calibrate-grace.py <label> <delay_secs> <prompt>
"""
import os
import signal
import subprocess
import sys
import time

CLAUDE_BIN = os.path.expanduser("~/.local/bin/claude")

label, delay, prompt = sys.argv[1], float(sys.argv[2]), sys.argv[3]
cwd = "/tmp/t217-scratch/claude-cwd"
os.makedirs(cwd, exist_ok=True)

t_start = time.time()
p = subprocess.Popen(
    [CLAUDE_BIN, "-p", prompt, "--model", "haiku", "--output-format", "text"],
    cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    start_new_session=True, restore_signals=True,
)
time.sleep(delay)
still_alive_at_signal = p.poll() is None
if not still_alive_at_signal:
    t_end = time.time()
    print(f"{label} delay={delay}s ALREADY-EXITED before signal could be sent "
          f"(natural runtime < {delay}s) rc={p.returncode} elapsed={t_end-t_start:.3f}s")
    sys.exit(0)

t_sig = time.time()
os.kill(p.pid, signal.SIGTERM)
deadline = t_sig + 30.0
while p.poll() is None and time.time() < deadline:
    time.sleep(0.01)
hung = p.poll() is None
if hung:
    os.killpg(p.pid, signal.SIGKILL)
    p.wait()
t_end = time.time()
print(f"{label} delay={delay}s SIGTERM-to-exit={t_end-t_sig:.3f}s "
      f"hung_past_30s={hung} rc={p.returncode}")
