#!/usr/bin/env python3
"""T349 -- THE CANDIDATE. A PreToolUse deny hook that would enforce push-before-spawn.

**NOT INSTALLED.** This file lives in a capture directory and is driven only against a
throwaway repo. Installing it means writing `.claude/settings.json`, which T349 was
explicitly forbidden to do, and which the recommendation in the handoff argues against
doing without the conditions listed there.

DESIGN, and every clause of it exists because a measurement forced it:

1. `agent_id` in the payload  =>  ALLOW.
   Measured: a driver's own tool call carries no `agent_id`; a SUBAGENT's tool call
   carries `agent_id` and `agent_type`. Without this clause the gate would deny every
   worker's own sub-spawn -- and workers are forbidden to push, so it would deny them
   forever. This is the clause that stops the hook bricking the fire.

2. The gated call paths are BOTH  `Task`/`Agent`  and  `Bash` containing `worktree add`.
   Measured (R4): with only the Agent path denied, the model routed around it by issuing
   `git worktree add` from Bash in the very next turn, unprompted.

3. The decision is a CONTENT question about origin/main, not an ancestry question about
   HEAD. Measured (replay E1): at the 2026-08-22 violation the dispatch record had not
   been COMMITTED yet, so local HEAD was clean and already published -- an ancestry gate
   allows the spawn while the record does not exist.

4. The hook owns its own network timeout. Measured (H1): when a PreToolUse hook exceeds
   the `timeout` in settings.json the harness FAILS OPEN and the tool runs. Measured
   (cost 3): `git ls-remote` to an unreachable host takes 75 s with no client timeout.
   A hook that leaves the timeout to the harness therefore cannot fail closed at all.
"""
import json
import os
import re
import subprocess
import sys
import time

MODE = os.environ.get("SOFTHOUSE_SPAWN_GATE", "enforce")   # enforce | warn | off
FAIL = os.environ.get("SOFTHOUSE_SPAWN_GATE_FAIL", "closed")  # closed | open
NET_TIMEOUT = float(os.environ.get("SOFTHOUSE_SPAWN_GATE_NET_TIMEOUT", "12"))
LOG = os.environ.get("SOFTHOUSE_SPAWN_GATE_LOG", "")

SPAWN_TOOLS = {"Task", "Agent"}
TASKID = [re.compile(r"handoff/[^/\s]+/(T\d+)\.md"),
          re.compile(r"===\s*TASK\s+(T\d+)"),
          re.compile(r"softhouse/(T\d+)-")]


def emit(decision, reason, detail):
    if LOG:
        try:
            with open(LOG, "a") as f:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "decision": decision, "reason": reason,
                                    "detail": detail}) + "\n")
        except Exception:
            pass
    if decision == "deny":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason}}))
    sys.exit(0)


def git(repo, *a, **kw):
    return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, text=True, **kw)


def main():
    payload = json.loads(sys.stdin.read() or "{}")
    tool = payload.get("tool_name")
    ti = payload.get("tool_input") or {}
    repo = payload.get("cwd") or os.getcwd()

    if MODE == "off":
        emit("allow", "", "gate off")
    # (1) a subagent's own tool call is never a batch dispatch
    if payload.get("agent_id"):
        emit("allow", "", "subagent call (agent_id=%s)" % payload.get("agent_id"))

    # (2) which call paths are gated
    if tool in SPAWN_TOOLS:
        text = json.dumps(ti)
    elif tool == "Bash" and re.search(r"worktree\s+add", str(ti.get("command", ""))):
        text = str(ti.get("command", ""))
    else:
        emit("allow", "", "not a spawn path")

    ids = []
    for rx in TASKID:
        ids += rx.findall(text)
    ids = sorted(set(ids))

    # (3+4) content question about origin/main, with the hook's OWN network timeout
    t0 = time.time()
    try:
        f = git(repo, "fetch", "--quiet", "origin", "main", timeout=NET_TIMEOUT)
        netrc, neterr = f.returncode, f.stderr.strip()
    except subprocess.TimeoutExpired:
        netrc, neterr = -9, "fetch exceeded %ss" % NET_TIMEOUT
    net_s = round(time.time() - t0, 2)

    if netrc != 0:
        d = "origin unreachable (%s) after %ss" % (neterr[:120], net_s)
        if FAIL == "open" or MODE == "warn":
            emit("allow", "", "UNDECIDABLE, failing open: " + d)
        emit("deny", "push-before-spawn gate: cannot reach origin, so it cannot be shown that "
                     "the dispatch record is published. " + d
                     + "  Set SOFTHOUSE_SPAWN_GATE_FAIL=open for this session if the network is "
                       "genuinely down and you accept dispatching blind.", d)

    head = git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()

    def at(path):
        r = git(repo, "show", "%s:%s" % (head, path))
        return r.stdout if r.returncode == 0 else None

    problems = []
    if at(".softhouse/LOCK") is None:
        problems.append("origin/main carries NO .softhouse/LOCK -- it says no fire is running")
    if at(".softhouse/RESUME.md") is None:
        problems.append("origin/main carries no in-flight .softhouse/RESUME.md")
    raw = at(".softhouse/tasks.json")
    tasks = {}
    if raw is None:
        problems.append("origin/main carries no .softhouse/tasks.json")
    else:
        try:
            d = json.loads(raw)
            ts = d["tasks"] if isinstance(d, dict) and "tasks" in d else d
            tasks = {t["id"]: t for t in ts if isinstance(t, dict) and "id" in t}
        except Exception as e:
            problems.append("origin/main's tasks.json does not parse: %s" % e)

    if not ids:
        # The prompt named no task. Every softhouse worker prompt is required to carry the
        # handoff path, so this is either a non-softhouse spawn or a malformed one.
        if FAIL == "open" or MODE == "warn":
            emit("allow", "", "no task id in the prompt; failing open")
        emit("deny", "push-before-spawn gate: this spawn's prompt names no task id "
                     "(expected `.softhouse/handoff/<run>/<Tnnn>.md`), so the gate cannot check "
                     "that its dispatch record is published.", "no task id")

    for tid in ids:
        t = tasks.get(tid)
        if t is None:
            problems.append("%s is absent from origin/main's tasks.json" % tid)
        elif t.get("status") in (None, "pending"):
            problems.append("%s reads status=%r on origin/main (not dispatched)" % (tid, t.get("status")))
        elif not t.get("branch"):
            problems.append("%s carries branch=%r on origin/main" % (tid, t.get("branch")))

    if problems:
        msg = ("push-before-spawn gate: origin/main does not yet show this batch as dispatched. "
               + "; ".join(problems)
               + ". Commit AND PUSH the LOCK, tasks.json and the in-flight RESUME.md, then spawn.")
        if MODE == "warn":
            emit("allow", "", "WARN-ONLY: " + msg)
        emit("deny", msg, "; ".join(problems))

    emit("allow", "", "published: %s (net %ss)" % (",".join(ids), net_s))


main()
