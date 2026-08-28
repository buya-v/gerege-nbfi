#!/usr/bin/env python3
"""T349 probe PreToolUse hook. SCRATCH ONLY -- never installed in this repo.

Reads the PreToolUse payload on stdin, appends one JSON line to $T349_LOG, and then
decides according to $T349_MODE:

  log                 allow everything (the CONTROL -- proves the instrument works)
  deny-agent          deny tool_name in {Task, Agent} via permissionDecision=deny
  deny-agent-exit2    deny the same set via exit code 2 + stderr
  deny-bash-worktree  deny Bash whose command contains 'worktree add'
  push-gate           the REAL candidate: allow unless this is a spawn and the
                      dispatch record is not on origin/main.

Every branch logs, so an absent log line is distinguishable from an allow (P-83).
"""
import json
import os
import subprocess
import sys
import time

LOG = os.environ.get("T349_LOG", "/tmp/t349-hook.log")
MODE = os.environ.get("T349_MODE", "log")
t0 = time.time()

raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    payload = {"_unparsed": raw[:2000]}

tool = payload.get("tool_name")
ti = payload.get("tool_input") or {}


def log(**kw):
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 4),
        "mode": MODE,
        "tool_name": tool,
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "cwd": payload.get("cwd"),
        "permission_mode": payload.get("permission_mode"),
        "tool_input_keys": sorted(ti.keys()) if isinstance(ti, dict) else None,
        "tool_input": json.dumps(ti)[:600] if isinstance(ti, dict) else str(ti)[:600],
        "payload_keys": sorted(payload.keys()),
    }
    rec.update(kw)
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def deny(reason):
    log(decision="deny", reason=reason)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def allow(why="allow"):
    log(decision=why)
    sys.exit(0)


SPAWN_TOOLS = {"Task", "Agent"}

if MODE == "log":
    allow("log-only")

elif MODE == "hang":
    # Q3 sub-question: when the hook exceeds its configured `timeout`, does the harness
    # fail OPEN (tool proceeds) or CLOSED (tool refused)? Sleep past the timeout, then
    # try to deny. If a deny still lands, the harness waited; if the tool ran, it did not.
    if tool in SPAWN_TOOLS:
        log(decision="hang-start", hang_s=float(os.environ.get("T349_HANG", "20")))
        time.sleep(float(os.environ.get("T349_HANG", "20")))
        deny("T349 HANG DRIVE: deny emitted AFTER the configured hook timeout.")
    allow("not-a-spawn")

elif MODE == "deny-agent":
    if tool in SPAWN_TOOLS:
        deny("T349 RED DRIVE: spawn refused by PreToolUse deny.")
    allow()

elif MODE == "deny-agent-exit2":
    if tool in SPAWN_TOOLS:
        log(decision="deny-exit2")
        sys.stderr.write("T349 RED DRIVE (exit 2): spawn refused by PreToolUse.\n")
        sys.exit(2)
    allow()

elif MODE == "deny-bash-worktree":
    if tool == "Bash" and "worktree add" in str(ti.get("command", "")):
        deny("T349 RED DRIVE: `git worktree add` refused by PreToolUse deny.")
    allow()

elif MODE == "push-gate":
    if tool not in SPAWN_TOOLS:
        allow("not-a-spawn")
    repo = os.environ.get("T349_REPO", payload.get("cwd") or ".")
    net0 = time.time()
    try:
        p = subprocess.run(["git", "-C", repo, "ls-remote", "origin", "refs/heads/main"],
                           capture_output=True, text=True,
                           timeout=float(os.environ.get("T349_NET_TIMEOUT", "10")))
        rc, out, err = p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        rc, out, err = -9, "", "TIMEOUT"
    net_ms = round((time.time() - net0) * 1000, 1)
    if rc != 0 or not out:
        # UNDECIDABLE. Which way this falls is the whole of Q3.
        fail = os.environ.get("T349_FAIL", "open")
        if fail == "closed":
            log(decision="deny-undecidable", net_ms=net_ms, rc=rc, err=err[:200])
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": "T349 push-gate: origin unreachable; cannot prove the dispatch record is published.",
            }}))
            sys.exit(0)
        log(decision="allow-undecidable", net_ms=net_ms, rc=rc, err=err[:200])
        sys.exit(0)
    remote_sha = out.split()[0]
    local = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                           capture_output=True, text=True).stdout.strip()
    anc = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", local, remote_sha],
                         capture_output=True, text=True).returncode
    if anc != 0:
        log(decision="deny-unpushed", net_ms=net_ms, local=local[:12], remote=remote_sha[:12])
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": "T349 push-gate: HEAD %s is not on origin/main (%s). Push the dispatch record before spawning." % (local[:12], remote_sha[:12]),
        }}))
        sys.exit(0)
    log(decision="allow-pushed", net_ms=net_ms, local=local[:12], remote=remote_sha[:12])
    sys.exit(0)

else:
    allow("unknown-mode")
