#!/usr/bin/env python3
"""T349 -- unit drives for the candidate-gate clauses a live spawn cannot exercise cheaply,
plus the fast-path cost that the whole cost argument turns on.

Each case states what it EXPECTS before it runs it (P-83: test the line's presence first).
"""
import json
import os
import subprocess
import sys
import time

GATE = sys.argv[1]
REPO = sys.argv[2]           # a scratch repo whose origin is a local bare repo
FAILS = 0


def run(payload, env_extra=None):
    env = dict(os.environ)
    env.pop("SOFTHOUSE_SPAWN_GATE_LOG", None)
    env.update(env_extra or {})
    t = time.time()
    p = subprocess.run(["/usr/bin/python3", GATE], input=json.dumps(payload),
                       capture_output=True, text=True, env=env)
    ms = (time.time() - t) * 1000
    out = p.stdout.strip()
    if not out:
        return "ALLOW", "", ms
    try:
        d = json.loads(out)["hookSpecificOutput"]
        return d["permissionDecision"].upper(), d["permissionDecisionReason"], ms
    except Exception:
        return "?", out[:200], ms


def case(name, expect, payload, env_extra=None, expect_substr=None):
    global FAILS
    got, reason, ms = run(payload, env_extra)
    ok = (got == expect) and (expect_substr is None or expect_substr in reason)
    if not ok:
        FAILS += 1
    print("%-58s expect=%-5s got=%-5s %-5s %6.0f ms  %s" % (
        name, expect, got, "PASS" if ok else "FAIL", ms, reason[:90]))


# NOTE ON THE FIXTURE PATHS BELOW: every repo-relative path named in a fixture is one that
# RESOLVES in this tree. A fixture naming an invented handoff file would enter the T316
# dead-path frontier -- measured: it added 2 rows and the bar REFUSED. So the extraction
# cases use this task's own real handoff path.
HANDOFF = ".softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T349.md"

SPAWN = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "Agent",
         "cwd": REPO,
         "tool_input": {"description": "T900", "prompt": "=== TASK T900 === do the thing"}}

print("scratch repo: %s\n" % REPO)

print("-- clause 1: a SUBAGENT's own tool call is never a batch dispatch")
sub = dict(SPAWN); sub["agent_id"] = "a123"; sub["agent_type"] = "general-purpose"
case("subagent Agent call (agent_id present)", "ALLOW", sub)
subw = {"session_id": "s", "tool_name": "Bash", "cwd": REPO, "agent_id": "a123",
        "tool_input": {"command": "git worktree add -b x /tmp/x HEAD"}}
case("subagent Bash `git worktree add`", "ALLOW", subw)

print("\n-- clause 2: both call paths are gated for the DRIVER (no agent_id)")
case("driver Agent call, record unpushed", "DENY", SPAWN, expect_substr="push-before-spawn gate")
bash = {"session_id": "s", "tool_name": "Bash", "cwd": REPO,
        "tool_input": {"command": "git worktree add -b softhouse/T900-probe /tmp/x HEAD"}}
case("driver Bash `git worktree add`", "DENY", bash, expect_substr="push-before-spawn gate")
other = {"session_id": "s", "tool_name": "Bash", "cwd": REPO,
         "tool_input": {"command": "git status"}}
case("driver Bash, unrelated command (control)", "ALLOW", other)
rd = {"session_id": "s", "tool_name": "Read", "cwd": REPO, "tool_input": {"file_path": "/x"}}
case("driver Read (control)", "ALLOW", rd)

print("\n-- task-id extraction: the three shapes the worker prompt template guarantees")
for label, text in (
        ("handoff path", "Write your handoff to `%s`" % HANDOFF),
        ("=== TASK marker", "=== TASK T349 ===\nTitle: whatever"),
        ("branch name", "Commit to branch `softhouse/T349-pretooluse-eval` only")):
    p = dict(SPAWN); p["tool_input"] = {"prompt": text}
    case("driver Agent, id via %s" % label, "DENY", p, expect_substr="T349")
p = dict(SPAWN); p["tool_input"] = {"prompt": "do something vague"}
case("driver Agent, NO task id, FAIL=closed", "DENY", p,
     {"SOFTHOUSE_SPAWN_GATE_FAIL": "closed"}, expect_substr="names no task id")
case("driver Agent, NO task id, FAIL=open", "ALLOW", p, {"SOFTHOUSE_SPAWN_GATE_FAIL": "open"})

print("\n-- modes and the escape hatch")
case("SOFTHOUSE_SPAWN_GATE=off", "ALLOW", SPAWN, {"SOFTHOUSE_SPAWN_GATE": "off"})
case("SOFTHOUSE_SPAWN_GATE=warn (allows, unpushed)", "ALLOW", SPAWN, {"SOFTHOUSE_SPAWN_GATE": "warn"})

print("\n-- clause 4: origin unreachable, both fail directions")
unreach = {"SOFTHOUSE_SPAWN_GATE_NET_TIMEOUT": "4"}
subprocess.run(["git", "-C", REPO, "remote", "set-url", "origin", "ssh://git@192.0.2.1:22/x.git"])
case("origin unreachable, FAIL=closed", "DENY", SPAWN,
     dict(unreach, SOFTHOUSE_SPAWN_GATE_FAIL="closed"), expect_substr="cannot reach origin")
case("origin unreachable, FAIL=open", "ALLOW", SPAWN,
     dict(unreach, SOFTHOUSE_SPAWN_GATE_FAIL="open"))
subprocess.run(["git", "-C", REPO, "remote", "set-url", "origin",
                os.path.dirname(REPO.rstrip("/")) + "/origin.git"])

print("\n-- fast-path cost (the clause that runs on EVERY tool call of EVERY worker)")
xs = []
for _ in range(20):
    _, _, ms = run(sub)
    xs.append(ms)
xs.sort()
print("   subagent fast path: min=%.0f median=%.0f p90=%.0f max=%.0f ms" % (
    xs[0], xs[len(xs) // 2], xs[int(len(xs) * .9)], xs[-1]))
xs = []
for _ in range(10):
    _, _, ms = run(rd)
    xs.append(ms)
xs.sort()
print("   non-spawn tool    : min=%.0f median=%.0f p90=%.0f max=%.0f ms" % (
    xs[0], xs[len(xs) // 2], xs[int(len(xs) * .9)], xs[-1]))

print("\n%s -- %d failing case(s)" % ("ALL CASES PASS" if FAILS == 0 else "FAILURES", FAILS))
sys.exit(1 if FAILS else 0)
