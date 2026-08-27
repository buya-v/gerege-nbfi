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

T309 -- TWO AUTHORITIES, NOT ONE, AND THEY FAIL IN OPPOSITE DIRECTIONS.
`caller_is_lock_holder()` used to answer a BOOLEAN, and its `claude`-in-ancestry leg
refused everything on the ground that "a driver or worker must not reconcile its own
siblings". True of LIVE siblings; FALSE of corpses -- and the guard had no notion of fire
identity, so it could not tell the two apart. On 2026-08-23 fire `20260823-140001` opened
on eight `in_progress` tasks belonging to the SIGTERMed `20260823-080004`, could not use
this tool (a driver is always inside a `claude`), and open-coded the demotion by hand.

So the predicate is SPLIT into a caller MODE and a per-task OWNERSHIP test:
  * `wrapper` mode (fire-program.sh, driver already dead, liveness established out of
    band by `foreign_live_session_in_repo()`): demotes EVERY `in_progress` task. It fails
    towards DEMOTING, which is right there -- the caller has positively established there
    is nothing live to destroy, and the cost of not demoting is the `in_progress` lie.
  * `in_session` mode (a driver or worker, a fire IS live): demotes ONLY tasks that were
    ALREADY claiming `in_progress` in the tasks.json committed when THIS fire took the
    lock -- i.e. dispatches it inherited, not ones it made. It fails towards REFUSING,
    which is right there -- the destructive error is demoting live work and it cannot be
    undone, while the non-destructive error leaves a lie that `wrapper` mode clears on
    the way out.
    ATTEMPT 1 OF T309 USED `task["fire"] != LOCK["fire"]` HERE AND IT WAS MEASURED WRONG:
    `fire` is stamped at first dispatch and never refreshed on re-dispatch, so on
    2026-08-27 all six live workers of fire `20260827-230001` still carried
    `"fire": "20260823-140001"` and that predicate would have demoted every one of them
    [.softhouse/capture/t309-sigterm-reconcile-bypass/stale-fire-RED.txt]. The field is
    still READ, but only as corroboration that is REPORTED when it disagrees.
These are the SAME repair with OPPOSITE polarity, deliberately, because the two call
sites have opposite worst cases. Widening one predicate to serve both is the shape
`P-91`/`T292` names, and it is not done here.

T312 -- THE BRANCH CASE-VARIANT FLAG, AND WHY THE EXISTING CHECK PASSED CLEANLY.
This resolver flags "`in_progress` with no `branch`" as a suspected isolation violation.
On 2026-08-27 six tasks passed that check while their branches were case-shadowing each
other: a branch WAS recorded, it DID resolve, and it had commits, while a differently
cased sibling held a diverged line no name reached. `git branch --list` globbing is
case-SENSITIVE and `packed-refs` is a case-SENSITIVE text file, but this filesystem is
not -- so a loose ref of one case hides a packed ref of another and the hidden value stays
a live object. The driver's hand-typed lowercase glob read that as "gone or empty" and
six tasks were re-dispatched as fresh attempts over 73 surviving commits.
So `branch_wip` now also asks "does a case-variant of this name exist", via
`branch_sweep.py` (imported, NOT reimplemented -- T213's rule) and suffixes its verdict
`/CASE-VARIANT`. When the check could not run it says `/CASE-UNCHECKED` instead, because
a silent absence of warning is what this file exists to stop being possible.

Usage:  python3 .softhouse/bin/ready-tasks.py [--json] [--repo <dir>]
        python3 .softhouse/bin/ready-tasks.py --reconcile --fire <fire-id>
                [--rescue <task-branch>=<rescue-branch>]... [--dry-run] [--repo <dir>]
                [--deadline-secs <n>]
Run it from the repo root (or pass --repo).

`--deadline-secs <n>` installs ONE monotonic wall-clock budget for the whole process and
clamps every subprocess timeout to what is left of it. It exists because T309 wires
`--reconcile` into fire-program.sh's SIGNAL handler, which is racing launchd's ~20s
SIGTERM->SIGKILL grace; without it, two `git` calls per in_progress task at `timeout=20`
is an unbounded budget in aggregate.

Exit codes:
  0   report printed / reconcile completed -- zero demotions is a completion too
  3   --reconcile could not READ or WRITE tasks.json. NOTHING was changed and the
      caller must not treat the state as truthful.
  4   --reconcile REFUSED and NOTHING was changed. Either the caller could not be
      established as the lock holder at all, or it is `in_session` and no `in_progress`
      task could be proven to belong to a dead fire. Fail-closed in both cases.
  64  usage error
"""
import json
import glob
import os
import shutil
import subprocess
import textwrap
import time
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


# T309 -- A WALL-CLOCK BUDGET, BECAUSE THIS NOW RUNS INSIDE A SIGNAL HANDLER.
# `--reconcile` used to be reachable only from the wrapper's NORMAL tail, where nothing
# was waiting on it. T309 wires it into fire-program.sh's on_signal() as well, and that
# handler is racing launchd's SIGTERM->SIGKILL grace (~20s, and the wrapper's own T211/
# T217 comments already spend most of it). The per-call `timeout=20` below was therefore
# an UNBOUNDED budget in aggregate: this program makes two `git` calls per in_progress
# task, so the eight corpses of fire 20260823-080004 would have been 16 x 20s = 320s of
# worst case inside a 20s window.
#
# `--deadline-secs N` installs ONE monotonic deadline for the whole process. Every
# subprocess timeout is clamped to what is left of it, and once it is gone `_run`
# answers rc=None WITHOUT spawning anything.
#
# POLARITY, and it differs by caller on purpose:
#   * for WIP EVIDENCE (branch_wip) an exhausted budget degrades the note to UNVERIFIED
#     and the demotion still happens -- the demotion is the repair, the branch sha is
#     colour. Failing closed on the EVIDENCE while still telling the truth about the
#     STATUS is the useful direction here.
#   * for AUTHORITY (caller_is_lock_holder) an exhausted budget is a REFUSAL, because a
#     rewrite authorised by a check that never ran is exactly the accident this whole
#     file exists to prevent.
DEADLINE = None          # monotonic instant, or None for "no budget"
BUDGET_NOTE = ""         # set when the budget was actually exhausted, for the report


# ------------------------------------------------------------ T312: case variants ---
# This file already flags "`in_progress` with no `branch`" as a suspected isolation
# violation.  On 2026-08-27 that check passed CLEANLY on six tasks whose branches were
# case-shadowing each other, which is why nothing caught it: a branch WAS recorded, it
# DID resolve, and it had commits -- while a differently-cased sibling held a diverged
# line that no name reached.  So `branch_wip` now asks the second question too.
#
# The index comes from branch_sweep.py rather than being reimplemented here.  T213's
# rule: the fixture and the fire must run the SAME bytes, not a copy that drifts.  It is
# pure filesystem (os.walk over refs/heads + a parse of packed-refs), so it costs NO
# subprocess and cannot eat the --deadline-secs budget.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import branch_sweep
    BRANCH_SWEEP_ERR = None
except Exception as _exc:                                       # noqa: BLE001
    branch_sweep = None
    BRANCH_SWEEP_ERR = "%s: %s" % (type(_exc).__name__, _exc)

_REF_INDEX = ("uncached", None)


def ref_index():
    """(index_or_None, note).  Cached for the process; a run lasts seconds and the
    refs it reads are not rewritten by this program."""
    global _REF_INDEX
    if _REF_INDEX[0] != "uncached":
        return _REF_INDEX
    if branch_sweep is None:
        _REF_INDEX = (None, "branch_sweep.py could not be imported (%s), so NO case-"
                            "variant check ran -- absence of a warning below means "
                            "NOTHING was looked at" % BRANCH_SWEEP_ERR)
        return _REF_INDEX
    common, note = branch_sweep.common_dir_of(repo)
    if common is None:
        _REF_INDEX = (None, "could not locate the git common dir (%s), so NO case-"
                            "variant check ran" % note)
        return _REF_INDEX
    idx = branch_sweep.RefIndex(common)
    _REF_INDEX = (idx, "loose refs walked from %s/refs/heads and packed entries parsed "
                       "from %s/packed-refs%s"
                       % (common, common,
                          ("; UNREAD: " + "; ".join(idx.errors)) if idx.errors else ""))
    return _REF_INDEX


def case_variants(branch):
    """(variants, note).  `variants` is every EXISTING ref name that case-folds to the
    same string as `branch` but is spelled differently.  `note` always states how the
    question was answered, including when it was not."""
    idx, note = ref_index()
    if idx is None:
        return None, note
    return branch_sweep.shadow_conflicts(branch, idx), note


def set_deadline(secs):
    global DEADLINE
    DEADLINE = time.monotonic() + secs


def _remaining():
    """Seconds left, or None when no budget was installed."""
    if DEADLINE is None:
        return None
    return DEADLINE - time.monotonic()


def _run(argv, timeout=20):
    """Run argv. Return (rc, stdout, note). rc is None when the program did not answer.

    POLARITY: fail-CLOSED. A missing binary, a timeout, an exhausted wall-clock budget
    or an OSError all come back as rc=None with the reason in `note`, and every caller
    renders that as UNVERIFIED -- never as the reassuring answer. This is the shape that
    `wc -l` printing `0` on failure got wrong in the wrapper's worktree sweep (T202) and
    it is not repeated here.
    """
    global BUDGET_NOTE
    if not argv[0]:
        return None, "", "program not found on PATH"
    left = _remaining()
    if left is not None:
        if left <= 0.05:
            BUDGET_NOTE = "the --deadline-secs budget was exhausted"
            return None, "", ("wall-clock budget exhausted before %s could be run"
                              % os.path.basename(argv[0]))
        timeout = min(timeout, left)
    try:
        p = subprocess.run(argv, cwd=repo, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        if left is not None:
            BUDGET_NOTE = "the --deadline-secs budget was exhausted"
        return None, "", "timed out after %.2fs" % timeout
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
    """(mode, reason, lock_fire). Fail-CLOSED: anything unestablished is "refused".

    `--reconcile` rewrites tasks.json, so the one thing that must never happen is a
    rewrite that destroys LIVE work. The lock already records the holder's `host` and
    `pid`; this asks whether that pid is an ANCESTOR of this process. It is unfakeable by
    the caller (walked from /bin/ps, not passed in as an argument) and it needs nobody to
    remember anything -- the wrapper is the parent of the python it invokes, by
    construction, whenever it is the wrapper doing the call.

    T309 -- WHY THIS RETURNS A MODE AND NOT A BOOLEAN.
    Until T309 the `claude`-in-ancestry leg below was a flat REFUSAL, on the stated
    ground that "a driver or worker must not reconcile its own siblings". That ground is
    SOUND FOR LIVE SIBLINGS AND WRONG FOR CORPSES, and the difference cost a fire: on
    2026-08-23 the `20260823-140001` driver opened on eight `in_progress` tasks left by
    `20260823-080004` -- four branches at the dispatch commit with zero commits ahead of
    main, four never created at all -- and could not use this tool to clear them, because
    a driver is by definition running inside a `claude`. It open-coded the demotion by
    hand, which is precisely the hand-repair this tool exists to replace.

    The boolean was ONE PREDICATE SERVING TWO PURPOSES, which is the shape `P-91` /
    `T292` names: "a guard phrased as a STRUCTURAL PATTERN over the shape of its input
    can always be re-nested one level out ... The escape is not a better pattern: it is
    INVERTING THE BURDEN -- require the document to POSITIVELY DEMONSTRATE coverage in a
    form the rule CONSTRUCTS rather than RECOGNISES" [VERIFIED: .softhouse/patterns.md
    P-91, this checkout]. So the predicate is SPLIT, and the second half moves onto the
    TASK rather than onto the caller: see `task_is_demotable_in_session`. The caller no
    longer asks "am I allowed to rewrite this file", it asks, once per task, "can I
    POSITIVELY show this dispatch belongs to a fire that is not the one holding the lock".

    Modes:
      "wrapper"     the lock holder is an ancestor and NO `claude` is in the chain. This
                    is fire-program.sh itself, after its driver has been waited on or
                    killed. It may demote every `in_progress` task.
      "in_session"  the lock holder is an ancestor but a `claude` IS in the chain: a
                    driver or a worker, i.e. code running WHILE a fire is live. It may
                    demote ONLY tasks positively attributed to a DIFFERENT fire.
      "refused"     nothing may be rewritten.
    """
    lock = os.path.join(root, "LOCK")
    if not os.path.exists(lock):
        # No lock => no live fire owns this repo => nobody's siblings are at risk. The
        # `claude` leg below is about protecting a LIVE fire's workers; with no lock
        # there is no live fire to protect, so this is "wrapper", not "in_session".
        return "wrapper", "no .softhouse/LOCK on disk -- nobody holds this repo", None
    try:
        with open(lock, encoding="utf-8") as fh:
            body = json.load(fh)
    except (IOError, ValueError) as exc:
        return "refused", "LOCK exists but could not be read as JSON (%s) -- REFUSING" % exc, None
    pid, host = body.get("pid"), body.get("host")
    lock_fire = body.get("fire")
    lock_fire = lock_fire.strip() if isinstance(lock_fire, str) else None
    if not isinstance(pid, int):
        return "refused", "LOCK records no integer pid (%r) -- REFUSING" % (pid,), lock_fire
    rc, myhost, _ = _run(["/bin/hostname", "-s"], timeout=10)
    if rc != 0:
        return "refused", "could not read this host's name -- REFUSING to judge a lock", lock_fire
    if host != myhost:
        return "refused", ("LOCK is held on host %r, this is %r -- REFUSING to touch "
                           "another machine's state" % (host, myhost)), lock_fire
    anc = ps_ancestors()
    if anc is None:
        return "refused", "/bin/ps did not answer -- ancestry UNESTABLISHED, REFUSING", lock_fire
    if pid != os.getpid() and pid not in [p for p, _ in anc]:
        return "refused", ("LOCK is held by pid %d, which is NOT an ancestor of this "
                           "process (pid %d) -- a live fire may own these tasks. REFUSING."
                           % (pid, os.getpid())), lock_fire
    # ANCESTRY IS NOT ENOUGH, and this was MEASURED rather than reasoned: run from a
    # worker agent inside a live fire, the check above PASSED -- because a worker is a
    # descendant of the very wrapper that holds the lock. So being inside the holder's
    # tree does not make you the holder. The wrapper reaches this script through
    # zsh only; anything routed through a `claude` is a driver or a worker, i.e. code
    # running WHILE the fire is live. Until T309 that ended the call; now it selects the
    # NARROW authority instead of ending it.
    for apid, acmd in anc:
        if os.path.basename((acmd.split() or [""])[0]) == "claude":
            return "in_session", ("invoked from INSIDE a live session -- ancestor pid %d "
                                  "is `claude`. NARROW authority: this caller may demote "
                                  "only dispatches positively attributed to a fire other "
                                  "than the lock holder's (%s)."
                                  % (apid, lock_fire or "NONE RECORDED ON THE LOCK")), lock_fire
    return "wrapper", ("lock holder pid %d is an ancestor of this process and no `claude` "
                       "is in the chain" % pid), lock_fire


def dispatches_predating_this_fire(lock_fire):
    """(ids, reason) -- the set of task ids ALREADY claiming `in_progress` at the instant
    this fire took the lock. `ids` is None when that could not be established.

    T309 ATTEMPT 2 -- THE `task["fire"]` DISCRIMINATOR WAS ARMED AND WRONG, AND THIS IS
    WHAT REPLACES IT.

    Attempt 1 of this task made in-session demotion turn on `task["fire"] != LOCK["fire"]`,
    arguing from the lock's exclusivity: at most one fire holds `.softhouse/LOCK`, so a
    task stamped with a different fire id belongs to a fire that is over. THE PREMISE IS
    SOUND. THE DATA IS NOT. `fire` is written onto a task by the DRIVER at dispatch, and
    it is NOT refreshed when a task is re-dispatched -- so a task retried by a later fire
    keeps the ORIGINAL fire's id and reads, to that test, as a corpse.

    MEASURED, not reasoned [VERIFIED: this checkout, 2026-08-27]:
      * fire `20260827-230001` took its lock in commit `558ef32` at 23:00:08 and marked
        six workers `in_progress` in `39d2156` (23:03:45) and a seventh in `5d2164e`
        (23:07:24, T305 `needs_retry -> in_progress`);
      * every one of those tasks still carries `"fire": "20260823-140001"` -- a fire that
        ended four days earlier -- and `"dispatched_at": "2026-08-23T03:57:24Z"`;
      * driven against that real state, attempt 1's predicate reported
        `IN-SESSION authority: 6 demotable` and would have demoted six LIVE workers of
        the fire holding the lock, T309 among them
        [.softhouse/capture/t309-sigterm-reconcile-bypass/stale-fire-RED.txt].
    That is the DESTRUCTIVE direction: an in-session reconcile that runs too eagerly
    destroys live work, and unlike the `in_progress` lie it cannot be undone.

    THE REPLACEMENT IS DERIVED FROM DOING THE WORK, NOT MAINTAINED BESIDE IT. The wrapper
    commits `.softhouse/tasks.json` as it stood the moment it took the lock, under the
    subject `softhouse: local fire lock (<fire id>)`. At that instant this fire has
    dispatched NOTHING -- so every task claiming `in_progress` in THAT blob is a claim
    inherited from an earlier fire, and every task claiming `in_progress` NOW but not
    THEN was dispatched by this fire and is live. The question "is this dispatch mine?"
    becomes a read of two committed blobs.

    This is the same property `.softhouse/LOCK`'s own comment already prefers for
    liveness: push-recency over a `heartbeat` field, "because push recency is DERIVED
    from doing the work rather than maintained beside it, and so cannot silently fall
    behind the truth the way a remembered field can (P-45, five recorded times)"
    [VERIFIED: fire-program.sh, the P-85/STEP 0 comment above the LOCK heredoc]. P-45 is
    "a guard that only works when someone remembers to run it enforces nothing"
    [VERIFIED: .softhouse/patterns.md, P-45]; `task["fire"]` is its field-shaped twin --
    a guard that only works when someone remembers to REFRESH it -- and the measurement
    above is that nobody did.

    REJECTED ALTERNATIVES, and why:
      * `task["fire"]` (attempt 1) -- measured wrong, above. It is still READ here, but
        only as corroboration to be REPORTED when it disagrees, never as the authority.
      * fixing the staleness at the source, i.e. having the driver re-stamp `fire` on
        every dispatch -- that lives in the softhouse-program SKILL, outside this task's
        files_hint, and it would still be a remembered obligation. Raised as a follow-up.
      * process liveness per task -- there IS no process per task. Measured on this host
        during a live fire with six workers dispatched: a subagent is in-process inside
        ONE `claude` [VERIFIED: fire-program.sh's own foreign_live_session_in_repo()
        comment, which records the /bin/ps and lsof evidence]. Any design looking for a
        process per task finds nothing and demotes everything.
      * branch WIP ("no commits => dead") -- INVERTED for exactly the case that matters.
        A live worker in its first minutes has no commits and would be demoted; a dead
        worker that committed once would be spared. The 2026-08-23 corpses had zero
        commits AND were dead; that correlation is an accident of the incident.
      * a `--force`/`--foreign-only` flag -- a remembered obligation, P-45 again.

    FAIL-CLOSED DIRECTION HERE: every leg that does not answer returns None, and the
    caller renders None as "demote nothing". A missing lock commit, an unreadable blob,
    unparseable JSON and an exhausted wall-clock budget are all None. "I could not tell"
    is never spelled like "nobody owns these".

    RESIDUAL RISK, STATED: this trusts that the wrapper's lock commit is reachable from
    HEAD and that its subject is the one the wrapper writes. If the wrapper's commit
    subject is ever changed, this stops finding the commit and REFUSES -- which is the
    safe direction, and it is why the subject is quoted rather than pattern-matched. It
    also inherits the assumption that one fire holds the lock at a time; P-85 records a
    day when two did [VERIFIED: .softhouse/patterns.md, P-85]. That assumption is not
    made worse here and it is not eliminated; no claim is made that it is.
    """
    if not lock_fire:
        return None, ("the LOCK records no `fire` id, so this fire's lock commit cannot "
                      "be found -- REFUSING (fail-closed)")
    subject = "softhouse: local fire lock (%s)" % lock_fire
    rc, sha, err = _run([GIT, "log", "-1", "--format=%H", "--fixed-strings",
                         "--grep", subject])
    if rc is None:
        return None, ("could not run git to find this fire's lock commit (%s) -- "
                      "REFUSING" % err)
    if rc != 0:
        return None, ("git log exited %d looking for the lock commit %r (%s) -- REFUSING"
                      % (rc, subject, err))
    if not sha:
        return None, ("no commit reachable from HEAD has the subject %r, so the instant "
                      "this fire took the lock is UNKNOWN -- REFUSING. (A fire whose "
                      "lock commit was never made, or was made on another branch, cannot "
                      "prove which dispatches predate it.)" % subject)
    sha = sha.splitlines()[0].strip()
    rc2, blob, err2 = _run([GIT, "show", "%s:.softhouse/tasks.json" % sha])
    if rc2 is None:
        return None, ("could not run git to read tasks.json at the lock commit %s (%s) "
                      "-- REFUSING" % (sha[:9], err2))
    if rc2 != 0 or not blob:
        return None, ("tasks.json is not readable at the lock commit %s (git rc=%s, %s) "
                      "-- REFUSING" % (sha[:9], rc2, err2))
    try:
        prior = json.loads(blob)["tasks"]
    except (ValueError, KeyError, TypeError) as exc:
        return None, ("tasks.json at the lock commit %s did not parse (%s) -- REFUSING"
                      % (sha[:9], exc))
    ids = set()
    for t in prior:
        if t.get("status") == "in_progress" and t.get("id"):
            ids.add(t["id"])
    return ids, ("at this fire's lock commit %s (%r) %d task(s) already claimed "
                 "in_progress: %s. Anything in_progress NOW but not in that set was "
                 "dispatched by THIS fire and is live."
                 % (sha[:9], subject, len(ids),
                    ", ".join(sorted(ids)) if ids else "none"))


def task_is_demotable_in_session(t, lock_fire, predating):
    """(ok, reason) -- may an IN-SESSION caller demote this `in_progress` task?

    `predating` is the set from dispatches_predating_this_fire(), or None when that
    could not be established.

    FAIL-CLOSED DIRECTION AT THIS CALL SITE, AND IT IS THE OPPOSITE OF THE WRAPPER'S ON
    PURPOSE. In-session, a live fire IS running, so the destructive error is demoting
    live work -- irreversible. The non-destructive error is leaving an `in_progress` lie
    standing, and that lie has a second reader: the wrapper's own exit path, which runs
    in `wrapper` mode with liveness established out of band by
    `foreign_live_session_in_repo()` and clears whatever is left. So this site refuses on
    every doubt and the OTHER site is where the lie dies. Widening one predicate to serve
    both is the shape T292/P-91 names, and it is deliberately not done.
    """
    if predating is None:
        return False, ("which dispatches predate this fire could not be established -- "
                       "REFUSING (fail-closed; demoting a live worker cannot be undone)")
    tid = t.get("id")
    owner = t.get("fire")
    owner = owner.strip() if isinstance(owner, str) else ""
    if tid not in predating:
        extra = ""
        if owner and owner != lock_fire:
            extra = (" (its `fire` field says %s, which is STALE -- `fire` is stamped at "
                     "first dispatch and not refreshed on re-dispatch, so it is reported "
                     "here and NOT used as the authority)" % owner)
        return False, ("it was NOT claiming in_progress when fire %s took the lock, so "
                       "THIS fire dispatched it: it is a LIVE sibling. REFUSING.%s"
                       % (lock_fire, extra))
    corroboration = ""
    if owner:
        corroboration = (" Its `fire` field says %s%s." %
                         (owner, "" if owner != lock_fire else
                          " -- which is THIS fire, disagreeing with the git evidence; "
                          "the field is stale-prone and the git evidence is authoritative"))
    return True, ("it was ALREADY claiming in_progress at fire %s's lock commit, before "
                  "this fire had dispatched anything, so the dispatch belongs to an "
                  "earlier fire that is over.%s" % (lock_fire, corroboration))


def _case_clause(branch):
    """The T312 flag, appended to every verdict below.

    It is appended rather than branched on deliberately: a case-variant is orthogonal to
    whether the named branch has commits.  The 2026-08-27 shadows sat on branches that
    reported `commits` -- the healthiest verdict this function has -- so hiding the
    warning behind an unhealthy one would have printed nothing on exactly those six.
    Returns ("", "") when there is nothing to say.
    """
    variants, note = case_variants(branch)
    if variants is None:
        return "/CASE-UNCHECKED", ("  CASE-VARIANT CHECK DID NOT RUN: %s." % note)
    if not variants:
        return "", ""
    return "/CASE-VARIANT", (
        "  !! CASE-VARIANT: %d other spelling(s) of this branch exist -- %s.  On a "
        "case-insensitive filesystem a loose ref shadows a packed one of different "
        "case, git resolves loose first, and the shadowed value stays a live object "
        "that no name reaches: that hid 4 committed commits on T297 and 8 on T305 at "
        "fire 20260827-230001.  Run `python3 .softhouse/bin/branch_sweep.py sweep "
        "--pattern '%s' --counts` BEFORE treating this task's branch as authoritative, "
        "and do NOT delete either spelling."
        % (len(variants), ", ".join(branch_sweep.short(v) for v in variants), branch))


def branch_wip(branch):
    """What WIP exists for a task branch. Returns (kind, human_text).

    kind is one of: none / absent / commits / unverified -- each optionally suffixed
    `/CASE-VARIANT` or `/CASE-UNCHECKED` by T312.  Nothing in this program COMPARES
    kind; it is printed, so the suffix is safe to carry.
    """
    kind, text = _branch_wip_core(branch)
    if not branch:
        return kind, text
    case_kind, case_text = _case_clause(branch)
    return kind + case_kind, text + case_text


def _branch_wip_core(branch):
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
    """Rewrite `in_progress` tasks to `needs_retry`, with the evidence in a note.

    THE CONTRACT WITH THE CALLER: in "wrapper" mode the caller has already established
    that no live session owns these tasks. fire-program.sh does that with
    `foreign_live_session_in_repo()` and does not call this otherwise. This function
    re-checks only what it can check by itself -- lock ancestry, above -- and, in
    "in_session" mode, per-task fire ownership.

    WHY REPAIR AND NOT REFUSE: see the wrapper's own comment at the call site. Briefly,
    a refusal has nowhere to be heard. The wrapper's only reader is a log file, the next
    fire reads tasks.json, and two fires in a row proved that a correct warning printed
    to the log changes nothing at all.
    """
    print("RECONCILE -- fire %s" % fire)
    print("  git:  %s" % (GIT or "NOT FOUND ON PATH -- WIP evidence will be UNVERIFIED"))
    print("  repo: %s" % repo)
    left = _remaining()
    if left is not None:
        print("  budget: %.1fs of wall clock for this whole run (--deadline-secs); every "
              "subprocess timeout is clamped to what is left of it" % left)
    mode, why, lock_fire = caller_is_lock_holder()
    print("  lock: %s" % why)
    print("  mode: %s   (lock fire id: %s)" % (mode, lock_fire or "NONE RECORDED"))
    if mode == "refused":
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

    # T309 -- THE AUTHORITY SPLIT, PER TASK. "wrapper" mode keeps the pre-T309 behaviour
    # exactly: every in_progress task is a corpse, because the caller established that
    # out of band before calling. "in_session" mode must show its work per task.
    demote, withheld = [], []
    predating = None
    if mode == "in_session":
        # T309 attempt 2: ONE git derivation for the whole run, not one per task -- two
        # `git` calls total, so the wall-clock budget cannot be spent proportionally to
        # the number of corpses.
        predating, predating_why = dispatches_predating_this_fire(lock_fire)
        print("  in-session evidence: %s" % predating_why)
    for t in live:
        if mode == "wrapper":
            demote.append(t)
            continue
        ok, reason = task_is_demotable_in_session(t, lock_fire, predating)
        (demote if ok else withheld).append((t, reason))

    if mode == "in_session":
        print("  IN-SESSION authority: %d demotable, %d WITHHELD (a live fire is running; "
              "only dispatches that PREDATE this fire's lock commit may be touched)"
              % (len(demote), len(withheld)))
        for t, reason in withheld:
            print("  %-8s WITHHELD  %s" % (t.get("id", "?"), reason))
        demote = [t for t, _ in demote]
        if not demote:
            print("  RESULT: REFUSED -- nothing this caller is authorised to repair; "
                  "tasks.json was NOT modified. The wrapper's exit-path reconcile runs "
                  "in `wrapper` mode and clears what is left.")
            return 4

    for t in demote:
        branch = t.get("branch") or ""
        kind, text = branch_wip(branch)
        rescued = rescue_map.get(branch)
        clauses = [text]
        if rescued:
            clauses.append("Uncommitted WIP left in its worktree was swept onto %s by "
                           "this fire's worktree sweep." % rescued)
        # WHICH FIRE KILLED IT -- SAY ONLY WHAT THE EVIDENCE SUPPORTS.
        # Attempt 1 of T309 wrote `t["fire"]` into this note as the killing fire, on the
        # ground that the pre-T309 note always named the RECONCILING fire and that was a
        # false attribution when one fire cleared another's corpses. The diagnosis was
        # right; the substitute is a field that is measurably stale (see
        # dispatches_predating_this_fire), so it swapped one false attribution for
        # another -- and a confident invention in the record this program reads back is
        # exactly what the honesty rule forbids. So the note now states the mode's
        # evidence and marks the field as corroboration:
        #   wrapper mode    -- the driver that just died IS this fire's; naming `--fire`
        #                      is an observation, not a guess.
        #   in_session mode -- the demotion was authorised by "already in_progress at
        #                      this fire's lock commit", which establishes the dispatch
        #                      is INHERITED but not WHICH earlier fire made it. Say that.
        owner = t.get("fire")
        owner = owner.strip() if isinstance(owner, str) else ""
        if owner:
            field = (" The task's own `fire` field says %s; that field is stamped at "
                     "first dispatch and is NOT refreshed on re-dispatch, so treat it as "
                     "corroboration, not as the identity of the killing fire." % owner)
        else:
            field = (" The task carries no `fire` field at all, so nothing corroborates "
                     "the attribution.")
        if mode == "wrapper":
            killer = ("fire %s -- OBSERVED: this wrapper stopped its own driver and is "
                      "reconciling its own dispatches.%s" % (fire, field))
        else:
            killer = ("an EARLIER fire -- established, not guessed: this task was already "
                      "claiming in_progress in the tasks.json committed when fire %s took "
                      "the lock, so the dispatch predates %s. WHICH earlier fire is NOT "
                      "established.%s" % (fire, fire, field))
        note = ("worker killed mid-flight by %s -- the fire ended while this task "
                "was still in_progress, and a killed worker is dead, not paused "
                "(softhouse-program STEP 5.5, 'NEVER exit with live workers', item 4). "
                "%s Completeness UNVERIFIED: no handoff "
                "was signed off and no reviewer saw this. Reconciled by fire %s in `%s` "
                "mode." % (killer, " ".join(clauses), fire, mode))
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

    if BUDGET_NOTE:
        print("  NOTE: %s -- some WIP evidence above is UNVERIFIED for that reason, not "
              "because the branches were inspected and found empty. The DEMOTIONS are "
              "unaffected: a dead dispatch is dead whether or not git answered."
              % BUDGET_NOTE)

    if dry_run:
        print("  RESULT: DRY RUN -- %d task(s) WOULD be demoted; tasks.json untouched."
              % len(demote))
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
    print("  RESULT: WROTE %s -- %d task(s) demoted in_progress -> needs_retry%s."
          % (path, len(demote),
             ", %d WITHHELD" % len(withheld) if withheld else ""))
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
        # T309 attempt 2: PRINT the `fire` field and its dispatch stamp, and say plainly
        # that neither is authoritative. This is not decoration -- the staleness only
        # became visible because somebody printed the field beside the truth, and an
        # omission that announces itself is not a remembered obligation (P-45: "a guard
        # that only works when someone remembers to run it enforces nothing"
        # [VERIFIED: .softhouse/patterns.md, P-45]).
        owner = t.get("fire")
        owner = owner.strip() if isinstance(owner, str) else ""
        when = t.get("dispatched_at") or "none"
        if owner:
            print("           `fire` field: %s   `dispatched_at`: %s   -- BOTH are "
                  "stamped at FIRST dispatch and are not refreshed on re-dispatch, so a "
                  "retried task carries the ORIGINAL fire's id. NOT authoritative; "
                  "`--reconcile` decides ownership from the tasks.json committed at this "
                  "fire's lock commit." % (owner, when))
        else:
            print("           `fire` field: NONE RECORDED   `dispatched_at`: %s   -- "
                  "harmless: `--reconcile` does not depend on this field." % when)
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
        elif a in ("--fire", "--repo", "--rescue", "--deadline-secs"):
            if i + 1 >= len(args):
                print("usage error: %s needs a value" % a, file=sys.stderr)
                return 64
            i += 1
            if a == "--fire":
                fire = args[i]
            elif a == "--repo":
                set_repo(args[i])
            elif a == "--deadline-secs":
                # T309. Rejected rather than clamped: a budget this program cannot parse
                # is a caller bug, and silently substituting a default would give a
                # signal handler a bound nobody chose.
                try:
                    secs = float(args[i])
                except ValueError:
                    print("usage error: --deadline-secs wants a number of seconds, got "
                          "%r" % args[i], file=sys.stderr)
                    return 64
                if secs <= 0:
                    print("usage error: --deadline-secs must be > 0, got %r" % args[i],
                          file=sys.stderr)
                    return 64
                set_deadline(secs)
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
