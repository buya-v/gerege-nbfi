#!/usr/bin/env python3
"""Readiness resolver for /softhouse-program STEP 1 -- and, since T288, the repair
for the one claim it used to only publish.

WHY THIS EXISTS. The driver's readiness check used to resolve a task's dependencies
against `.softhouse/tasks.json` ALONE. Tasks that complete are archived into
`.softhouse/runs/<run-id>.tasks.json` and dropped from the current file, so a
dependency on a completed task from an earlier run resolves to NOTHING and the
dependent task reads as permanently blocked.

That is not hypothetical. `T116` -- the G-8 option (a) family-B vector promotion --
was carried across several fires under the recorded claim that its dependency `T114`
"has NO ENTRY in tasks.json and can never resolve". T114 is `done` in
`.softhouse/runs/2026-08-17-run1-harness-schedule-poc.tasks.json`, with its handoff
and its review both merged on main. Measured by local fire 20260822-000013: SEVEN
dependency edges in the current file point outside it, and ALL SEVEN resolve in the
archive. None was ever missing.

The defect class is this program's most common one: a check that stops checking and
says so nowhere. So this resolver prints, on every run, WHERE each edge resolved --
current file, archive, or genuinely absent -- rather than silently returning a
boolean. Read the UNRESOLVED section; an empty one is a claim, and the counts beside
it are what make the claim inspectable.

T288 -- `--reconcile`, AND WHY THE REPAIR LIVES IN THIS FILE.
The `IN PROGRESS -- ALREADY DISPATCHED, do not dispatch again` block printed below is
the sentence that made the 2026-08-22 incident expensive. Fire `20260822-140002` ended
its turn with four live workers (T271/T283/T285/T286); all four died with it, and all
four stayed `in_progress` across TWO further fires -- so this resolver told each
following orchestrator that work was happening when nothing was, and the fire that
finally noticed had to reconstruct the truth by hand from six `rescued-agent-*` branch
names and two log files.

`--reconcile` withdraws that claim. It is in the same file as the claim on purpose: the
component that publishes "already dispatched" is the component that must be able to take
it back. It rewrites every `in_progress` task to `needs_retry` with a `note` naming the
fire that killed it, whatever WIP was found (a swept `softhouse/rescued-agent-*` branch,
or commits on the task's own branch), and the fact that completeness is UNVERIFIED.
STEP 5.5 of the softhouse-program skill -- section "NEVER exit with live workers", item 4;
there is no STEP 5.4 and a reader who goes looking for one will not find it -- already
requires this OF THE DRIVER. The whole point of doing it here is that a DEAD driver cannot
do anything, and the wrapper that calls this outlives it.

  A killed worker is dead, not paused. `in_progress` for a dead worker is an active lie
  to the next orchestrator. The wrapper DETECTED that state for two fires running and
  only printed a WARN -- which is `P-45` ("a guard that only works when someone
  remembers to run it enforces nothing") wearing a different coat: it WAS run, every
  fire, and it still enforced nothing, because its only reader is a log file that the
  next fire never opens.

WHO MAY CALL `--reconcile`. It rewrites `tasks.json`, so it refuses unless it can
POSITIVELY establish that the caller is the current lock holder: `.softhouse/LOCK` must
either be absent, or name a `pid` that is an ANCESTOR of this process on this host. The
ancestry is walked out of /bin/ps, so a caller cannot merely assert it, and if /bin/ps
does not answer the call is REFUSED rather than allowed. It does NOT judge worker
liveness itself -- that is the wrapper's job (`foreign_live_session_in_repo()` in
fire-program.sh), because the wrapper is the thing that owns the process facts.

Usage:  python3 .softhouse/bin/ready-tasks.py [--json] [--repo <dir>]
        python3 .softhouse/bin/ready-tasks.py --reconcile --fire <fire-id>
                [--rescue <task-branch>=<rescue-branch>]... [--dry-run] [--repo <dir>]
Run it from the repo root (or pass --repo).

Exit codes:
  0   report printed / reconcile completed -- zero demotions is a completion too
  3   --reconcile could not READ or WRITE tasks.json. NOTHING was changed and the
      caller must not treat the state as truthful.
  4   --reconcile REFUSED: the caller is not the lock holder, or that could not be
      established. Fail-closed; nothing was changed.
  64  usage error
"""
import json
import glob
import os
import shutil
import subprocess
import textwrap
import sys

TERMINAL = {"done", "approved", "merged"}
NOT_RUNNABLE = {"done", "approved", "merged", "parked", "rejected",
                "cancelled", "superseded", "closed_as_obligation"}

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo = os.path.dirname(root)


def set_repo(path):
    """Point this resolver at a repo other than the one holding the script.

    NEEDED because fire-program.sh runs `$SCRIPT_DIR/ready-tasks.py` -- the same bytes
    the fire runs, per T213's rule -- while operating on `$REPO`, which is an
    environment variable and is NOT always the checkout the script itself lives in.
    Deriving the root from `__file__` alone would have made the reconciler edit the
    WRONG tasks.json in exactly the case a fixture drive exercises. Also what makes
    this reconciler drivable end to end against a scratch repo.
    """
    global root, repo
    repo = os.path.abspath(path)
    root = os.path.join(repo, ".softhouse")


def load():
    cur = {}
    with open(os.path.join(root, "tasks.json")) as fh:
        for t in json.load(fh)["tasks"]:
            cur[t["id"]] = t
    arch = {}
    for path in sorted(glob.glob(os.path.join(root, "runs", "*.json"))):
        with open(path) as fh:
            try:
                doc = json.load(fh)
            except ValueError:
                continue
        for t in doc.get("tasks", []):
            # First archive wins only if the later one is not terminal; a task
            # re-run in a later run should be judged on its latest recorded state.
            prev = arch.get(t["id"])
            if prev is None or prev[1] not in TERMINAL:
                arch[t["id"]] = (os.path.basename(path), t.get("status"))
    return cur, arch


def resolve(dep, cur, arch):
    """Return (met, where). `where` always says how the edge was decided."""
    if dep in cur:
        return cur[dep].get("status") in TERMINAL, "tasks.json (%s)" % cur[dep].get("status")
    if dep in arch:
        name, status = arch[dep]
        return status in TERMINAL, "archive %s (%s)" % (name, status)
    return False, "NOT FOUND in tasks.json or any .softhouse/runs/*.json"


# --------------------------------------------------------------- T288 reconcile ---
# PROGRAMS ARE NAMED (P-58: name the program you ran, not the verb). `git` is resolved
# through shutil.which and the resolved path is PRINTED in the reconcile report, so the
# evidence says which binary answered rather than leaving it to $PATH at read time.
GIT = shutil.which("git")


def _run(argv, timeout=20):
    """Run argv. Return (rc, stdout, note). rc is None when the program did not answer.

    POLARITY: fail-CLOSED. A missing binary, a timeout or an OSError all come back as
    rc=None with the reason in `note`, and every caller renders that as UNVERIFIED --
    never as the reassuring answer. This is the shape that `wc -l` printing `0` on
    failure got wrong in the wrapper's worktree sweep (T202) and it is not repeated here.
    """
    if not argv[0]:
        return None, "", "program not found on PATH"
    try:
        p = subprocess.run(argv, cwd=repo, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "", "timed out after %ds" % timeout
    except OSError as exc:
        return None, "", "OSError: %s" % exc
    return p.returncode, p.stdout.strip(), (p.stderr.strip().splitlines() or [""])[0]


def ps_ancestors(pid=None):
    """Ancestors of `pid` as [(pid, command), ...], or None if /bin/ps did not answer.

    ONE snapshot of the whole table, walked upward -- not a `ps -o ppid= -p X` per
    level, because each of those sees a different instant and a process that exits
    between two of them makes the chain silently end early. A chain that ends early
    here would read as "the lock holder is not my ancestor", i.e. a REFUSAL, which is
    the safe direction, but a single snapshot cannot tear that way at all.
    """
    rc, out, _ = _run(["/bin/ps", "-Ao", "pid=,ppid=,command="], timeout=10)
    if rc != 0 or not out:
        return None
    parent, cmd = {}, {}
    for line in out.splitlines():
        f = line.split(None, 2)
        if len(f) < 2:
            continue
        try:
            p, pp = int(f[0]), int(f[1])
        except ValueError:
            continue
        parent[p] = pp
        cmd[p] = f[2] if len(f) > 2 else ""
    if len(parent) < 2:                      # a one-line process table is not a table
        return None
    chain, seen, cur = [], set(), (pid if pid is not None else os.getpid())
    for _ in range(64):                      # cap: a cyclic table must not spin
        nxt = parent.get(cur)
        if nxt is None or nxt in seen or nxt == 0:
            break
        seen.add(nxt)
        chain.append((nxt, cmd.get(nxt, "")))
        cur = nxt
    return chain


def caller_is_lock_holder():
    """(allowed, reason). Fail-CLOSED: anything unestablished returns False.

    `--reconcile` rewrites tasks.json, so the one thing that must never happen is a
    hand-run rewriting state out from under a LIVE fire. The lock already records the
    holder's `host` and `pid`; this asks whether that pid is an ANCESTOR of this
    process. It is unfakeable by the caller (walked from /bin/ps, not passed in as an
    argument) and it needs nobody to remember anything -- the wrapper is the parent of
    the python it invokes, by construction, whenever it is the wrapper doing the call.
    """
    lock = os.path.join(root, "LOCK")
    if not os.path.exists(lock):
        return True, "no .softhouse/LOCK on disk -- nobody holds this repo"
    try:
        with open(lock, encoding="utf-8") as fh:
            body = json.load(fh)
    except (IOError, ValueError) as exc:
        return False, "LOCK exists but could not be read as JSON (%s) -- REFUSING" % exc
    pid, host = body.get("pid"), body.get("host")
    if not isinstance(pid, int):
        return False, "LOCK records no integer pid (%r) -- REFUSING" % (pid,)
    rc, myhost, _ = _run(["/bin/hostname", "-s"], timeout=10)
    if rc != 0:
        return False, "could not read this host's name -- REFUSING to judge a lock"
    if host != myhost:
        return False, ("LOCK is held on host %r, this is %r -- REFUSING to touch "
                       "another machine's state" % (host, myhost))
    anc = ps_ancestors()
    if anc is None:
        return False, "/bin/ps did not answer -- ancestry UNESTABLISHED, REFUSING"
    if pid != os.getpid() and pid not in [p for p, _ in anc]:
        return False, ("LOCK is held by pid %d, which is NOT an ancestor of this "
                       "process (pid %d) -- a live fire may own these tasks. REFUSING."
                       % (pid, os.getpid()))
    # ANCESTRY IS NOT ENOUGH, and this was MEASURED rather than reasoned: run from a
    # worker agent inside a live fire, the check above PASSED -- because a worker is a
    # descendant of the very wrapper that holds the lock. So being inside the holder's
    # tree does not make you the holder. The wrapper reaches this script through
    # zsh only; anything routed through a `claude` is a driver or a worker, i.e. code
    # running WHILE the fire is live, which is exactly who must not demote in_progress.
    for apid, acmd in anc:
        if os.path.basename((acmd.split() or [""])[0]) == "claude":
            return False, ("invoked from INSIDE a live session -- ancestor pid %d is "
                           "`claude`. A driver or worker must not reconcile its own "
                           "siblings; only the wrapper, after the driver is dead, may. "
                           "REFUSING." % apid)
    return True, ("lock holder pid %d is an ancestor of this process and no `claude` "
                  "is in the chain" % pid)


def branch_wip(branch):
    """What WIP exists for a task branch. Returns (kind, human_text).

    kind is one of: none / absent / commits / unverified.
    """
    if not branch:
        return "none", ("No branch was recorded for this task -- suspect an isolation "
                        "violation; no WIP could be looked for.")
    rc, sha, err = _run([GIT, "rev-parse", "--verify", "--quiet", branch + "^{commit}"])
    if rc is None:
        return "unverified", ("Could not run git to inspect branch %s (%s) -- WIP "
                              "state UNVERIFIED." % (branch, err))
    if rc == 1 and not sha:
        return "absent", ("Its recorded branch %s does not exist in this repo -- no "
                          "WIP was found under that name." % branch)
    if rc != 0:
        return "unverified", ("git rev-parse on %s exited %d (%s) -- WIP state "
                              "UNVERIFIED, NOT assumed empty." % (branch, rc, err))
    rc2, count, err2 = _run([GIT, "rev-list", "--count", "main.." + branch])
    if rc2 != 0 or not count.isdigit():
        return "unverified", ("Branch %s exists at %s but its commit count vs main "
                              "could not be read (git rc=%s) -- UNVERIFIED."
                              % (branch, sha[:9], rc2))
    n = int(count)
    if n == 0:
        return "absent", ("Its branch %s exists at %s but has NO commit ahead of main "
                          "-- nothing was ever committed to it." % (branch, sha[:9]))
    return "commits", ("Its branch %s has %d commit(s) ahead of main, head %s."
                       % (branch, n, sha[:9]))


def reconcile(fire, rescue_map, dry_run=False):
    """Rewrite every `in_progress` task to `needs_retry`, with the evidence in a note.

    THE CONTRACT WITH THE CALLER: the caller has already established that no live
    session owns these tasks. fire-program.sh does that with
    `foreign_live_session_in_repo()` and does not call this otherwise. This function
    re-checks only what it can check by itself -- lock ancestry, above.

    WHY REPAIR AND NOT REFUSE: see the wrapper's own comment at the call site. Briefly,
    a refusal has nowhere to be heard. The wrapper's only reader is a log file, the next
    fire reads tasks.json, and two fires in a row proved that a correct warning printed
    to the log changes nothing at all.
    """
    print("RECONCILE -- fire %s" % fire)
    print("  git:  %s" % (GIT or "NOT FOUND ON PATH -- WIP evidence will be UNVERIFIED"))
    print("  repo: %s" % repo)
    allowed, why = caller_is_lock_holder()
    print("  lock: %s" % why)
    if not allowed:
        print("  RESULT: REFUSED -- tasks.json was NOT modified.")
        return 4

    path = os.path.join(root, "tasks.json")
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
        doc = json.loads(raw)
        tasks = doc["tasks"]
    except (IOError, ValueError, KeyError, TypeError) as exc:
        print("  ERROR: could not read %s (%s)." % (path, exc))
        print("  RESULT: REFUSED -- nothing was changed, and this state is NOT truthful.")
        return 3

    live = [t for t in tasks if t.get("status") == "in_progress"]
    print("  in_progress tasks found: %d  (out of %d in tasks.json -- every task was "
          "read to get this count, it is not a default)" % (len(live), len(tasks)))
    if not live:
        print("  RESULT: nothing to repair. tasks.json claims no dispatched work.")
        return 0

    for t in live:
        branch = t.get("branch") or ""
        kind, text = branch_wip(branch)
        rescued = rescue_map.get(branch)
        clauses = [text]
        if rescued:
            clauses.append("Uncommitted WIP left in its worktree was swept onto %s by "
                           "this fire's worktree sweep." % rescued)
        note = ("worker killed mid-flight by fire %s -- the fire ended while this task "
                "was still in_progress, and a killed worker is dead, not paused "
                "(softhouse-program STEP 5.5, 'NEVER exit with live workers', item 4). "
                "%s Completeness UNVERIFIED: no handoff "
                "was signed off and no reviewer saw this. Reconciled by the "
                "fire-program.sh exit guard, NOT by a driver -- the driver was already "
                "gone." % (fire, " ".join(clauses)))
        prior = t.get("note")
        if prior:
            note += "  [prior note: %s]" % prior
        print("  %-8s %-42s %s" % (t.get("id", "?"),
                                   branch or "(NO BRANCH RECORDED)",
                                   "WIP=%s%s" % (kind, "+rescued" if rescued else "")))
        print("           in_progress -> needs_retry")
        if not dry_run:
            t["status"] = "needs_retry"
            t["note"] = note

    if dry_run:
        print("  RESULT: DRY RUN -- %d task(s) WOULD be demoted; tasks.json untouched."
              % len(live))
        return 0

    # Preserve the file's own serialisation so the diff is the demotions and nothing
    # else. The canonical form on disk is json.dumps(indent=2, ensure_ascii=False) with
    # no trailing newline; that is MEASURED from the bytes here rather than assumed, and
    # a mismatch is REPORTED instead of silently reflowing 792 KB.
    tail = "\n" if raw.endswith("\n") else ""
    if json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + tail != raw:
        print("  NOTE: tasks.json is not in this writer's canonical form "
              "(indent=2, ensure_ascii=False); the rewrite will REFLOW it. Read the "
              "diff before trusting it.")
    body = json.dumps(doc, indent=2, ensure_ascii=False) + tail
    tmp = path + ".t288.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, path)
    except (IOError, OSError) as exc:
        print("  ERROR: could not write %s (%s)." % (path, exc))
        try:
            os.unlink(tmp)
        except OSError:
            pass
        print("  RESULT: REFUSED -- nothing was changed, and this state is NOT truthful.")
        return 3
    print("  RESULT: WROTE %s -- %d task(s) demoted in_progress -> needs_retry."
          % (path, len(live)))
    return 0


def main():
    cur, arch = load()
    ready, blocked, unresolved, live = [], [], [], []
    for tid, t in cur.items():
        if t.get("status") in NOT_RUNNABLE:
            continue
        if t.get("status") == "in_progress":
            live.append((tid, t))
            continue
        edges = [(d,) + resolve(d, cur, arch) for d in t.get("dependencies", [])]
        for dep, met, where in edges:
            if where.startswith("NOT FOUND"):
                unresolved.append((tid, dep))
        unmet = [(d, w) for d, m, w in edges if not m]
        (blocked if unmet else ready).append((tid, t, unmet, edges))

    if "--json" in sys.argv:
        json.dump({"ready": [r[0] for r in ready],
                   "in_progress": [l[0] for l in live],
                   "blocked": {b[0]: [u[0] for u in b[2]] for b in blocked},
                   "unresolved_edges": unresolved}, sys.stdout, indent=2)
        print()
        return 0

    print("IN PROGRESS -- ALREADY DISPATCHED, do not dispatch again (%d)" % len(live))
    # T288. THIS CLAIM IS ONLY TRUE WHILE THE DISPATCHING FIRE IS ALIVE. On 2026-08-22
    # it was false for four tasks across two fires, and it read exactly the same. So
    # every line now carries the WIP evidence beside the claim: a task whose branch has
    # no commit and whose worker is gone is a dead dispatch, not a busy one.
    #   `t.get("branch", <default>)` was ALSO a fail-open of the P-77 shape: the default
    #   applies only when the KEY IS ABSENT, so `"branch": null` printed the string
    #   "None" and read as a branch name. A missing branch is now spelled the same way
    #   whether the key is absent, null or empty.
    for tid, t in sorted(live):
        branch = t.get("branch") or ""
        kind, text = branch_wip(branch)
        print("  %-8s %s" % (tid, branch or "NO BRANCH RECORDED -- suspect an isolation violation"))
        print("           WIP: %s  %s" % (kind.upper(), text))
    if live:
        print("  ^ If no fire is running right now, every line above is a DEAD dispatch")
        print("    and this section is lying to you. The wrapper repairs it on the way")
        print("    out: fire-program.sh runs `ready-tasks.py --reconcile` at fire exit,")
        print("    which rewrites these to needs_retry with the evidence in a note.")
    print()
    print("READY (%d)" % len(ready))
    for tid, t, _, edges in sorted(ready):
        via = " via archive" if any("archive" in e[2] for e in edges) else ""
        print("  %-8s %-6s %-7s %s%s" % (tid, t.get("model", "?"),
                                         t.get("target", "?"), t.get("title", "")[:78], via))
    print("\nBLOCKED (%d)" % len(blocked))
    for tid, t, unmet, _ in sorted(blocked):
        print("  %-8s waiting on: %s" % (tid, ", ".join("%s [%s]" % u for u in unmet)))
    # READY here means TASK dependencies are met. It does NOT mean a gate permits the
    # work. A task can be dependency-ready and still forbidden -- e.g. writing vectors
    # in a context whose DEC-n is unratified. The driver decides that; this only warns.
    try:
        with open(os.path.join(root, "program.json")) as fh:
            gates = json.load(fh).get("gates_pending", [])
    except (IOError, ValueError):
        gates = []
    # SELECTOR FAIL-OPEN, found by T249. `g.get("class") == "CONTRACT"` SILENTLY DROPS
    # any gate carrying no `class` key at all -- and G-13 is exactly that shape
    # [VERIFIED at HEAD: G-13 has class=None]. An unclassified gate that was OPEN would
    # therefore be INVISIBLE here, which is the failure mode this whole section exists to
    # prevent. Select CONTRACT gates, but count and SHOW unclassified open gates too
    # rather than letting them vanish. See P-77.
    def _is_open(g):
        return "OPEN" in str(g.get("state", "")).upper()
    contract_open = [g for g in gates
                     if g.get("class") == "CONTRACT" and _is_open(g)]
    unclassified_open = [g for g in gates
                         if not isinstance(g.get("class"), str) and _is_open(g)]
    print("\nOPEN CONTRACT GATES -- READY above is about DEPENDENCIES, not permission (%d)"
          % len(contract_open))
    if not contract_open:
        print("  NONE open. Every gate id in program.json.gates_pending was inspected.")
    for g in contract_open:
        print("  %s  %s" % (g.get("id"), g.get("state")))
        print("      context %s / slice %s" % (g.get("context"), g.get("slice")))
        print("      %s" % str(g.get("title", ""))[:100])
        # A gate's SCOPE is a property of that gate, not of its class. Until 2026-08-22
        # the two lines below were printed UNCONDITIONALLY for every open CONTRACT gate,
        # which silently asserted the G-11 prohibition (contract UNRATIFIED, shape under
        # negotiation) over gates that block nothing of the kind -- e.g. G-14, a
        # stale-evidence correction to an ALREADY-RATIFIED DEC-2, for which gates.md's
        # authoritative register records "Blocks nothing today". Print what the gate
        # itself records; fall back to the conservative blanket text ONLY when the gate
        # has recorded no scope, and SAY that is what happened. See P-77.
        # FAIL-OPEN INTRODUCED BY THE DRIVER 2026-08-22 AND CAUGHT BY T249 THE SAME FIRE.
        # This read `str(g.get("blocks", "")).strip()`, so the FIVE most likely encodings
        # of "no value" -- None, False, 0, [], {} -- all stringify TRUTHY ("None",
        # "False", "0", "[]", "{}"), suppressed the conservative fallback, and printed
        # under "SCOPE RECORDED ON THIS GATE". `blocks: null` rendered as
        # "SCOPE RECORDED ... None", which READS AS "nothing is blocked". The pre-patch
        # code was fail-CLOSED; the patch made it fail-OPEN -- a fresh P-45 instance
        # created in the very commit that filed P-77 about unenforced permission
        # surfaces. Only a genuine non-empty STRING counts as a recorded scope; anything
        # else falls back AND is reported as MALFORMED, because a malformed scope is a
        # defect to surface, not a value to silently treat as absent.
        raw = g.get("blocks", None)
        blocks = raw.strip() if isinstance(raw, str) else ""
        malformed = raw is not None and not isinstance(raw, str)
        if malformed:
            print("      => !! MALFORMED `blocks` ON THIS GATE: type %s, value %r."
                  % (type(raw).__name__, raw))
            print("         NOT treated as a recorded scope. Falling back to conservative.")
        if blocks:
            print("      => SCOPE RECORDED ON THIS GATE (program.json .blocks):")
            for line in textwrap.wrap(blocks, 84):
                print("         %s" % line)
            if g.get("blocks_decided_by"):
                print("         [decided by: %s]" % g["blocks_decided_by"])
            if g.get("blocks_reviewed_by"):
                print("         [reviewed by: %s]" % g["blocks_reviewed_by"])
        else:
            print("      => NO SCOPE RECORDED ON THIS GATE. Falling back to the CONSERVATIVE")
            print("         default, which is an assumption and not a measurement:")
            print("         no task may write Go under nexus/ or store a CONTRACT-SHAPED vector")
            print("         for this context until it closes. Raw observed capture IS permitted.")
            print("         The driver MUST decide this gate's real scope and record it in")
            print("         program.json gates_pending[].blocks rather than inherit this text.")

    if unclassified_open:
        print("\n  !! OPEN GATES WITH NO `class` KEY (%d) -- these are INVISIBLE to the"
              % len(unclassified_open))
        print("     CONTRACT selector above and could carry an unread prohibition:")
        for g in unclassified_open:
            print("       %s  %s" % (g.get("id"), str(g.get("state", ""))[:70]))

    print("\nDEPENDENCY EDGES THAT RESOLVE NOWHERE (%d)" % len(unresolved))
    if not unresolved:
        print("  NONE. Every edge was decided against tasks.json or an archived run file,")
        print("  and this line is printed only after checking both -- it is not a default.")
    for tid, dep in unresolved:
        print("  %s -> %s" % (tid, dep))
    return 0


def cli(argv):
    """Hand-rolled, because the whole surface is five flags and argparse would print a
    usage string on an unknown one and exit 2 -- a code this program already spends on
    'the reference oracle is down'. An unknown flag exits 64 and SAYS which flag."""
    args = list(argv)
    fire, rescue_map, do_reconcile, dry = None, {}, False, False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--reconcile":
            do_reconcile = True
        elif a == "--dry-run":
            dry = True
        elif a == "--json":
            pass                                    # handled inside main()
        elif a in ("--fire", "--repo", "--rescue"):
            if i + 1 >= len(args):
                print("usage error: %s needs a value" % a, file=sys.stderr)
                return 64
            i += 1
            if a == "--fire":
                fire = args[i]
            elif a == "--repo":
                set_repo(args[i])
            else:
                # <task-branch>=<rescue-branch>, produced by the wrapper's worktree
                # sweep, which knows both and used to throw the pairing away.
                if "=" not in args[i]:
                    print("usage error: --rescue wants <task-branch>=<rescue-branch>, "
                          "got %r" % args[i], file=sys.stderr)
                    return 64
                k, _, v = args[i].partition("=")
                if k:
                    rescue_map[k] = v
        else:
            print("usage error: unknown argument %r" % a, file=sys.stderr)
            return 64
        i += 1
    if do_reconcile:
        if not fire:
            print("usage error: --reconcile requires --fire <fire-id>; the note it "
                  "writes must name the fire that killed the worker", file=sys.stderr)
            return 64
        return reconcile(fire, rescue_map, dry_run=dry)
    return main()


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
