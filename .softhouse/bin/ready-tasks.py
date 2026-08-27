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
  * `in_session` mode (a driver or worker, a fire IS live): demotes ONLY tasks that pass
    THREE conjunctive terms (see `task_is_demotable_in_session`). It fails towards
    REFUSING, which is right there -- the destructive error is demoting live work and it
    cannot be undone, while the non-destructive error leaves a lie that `wrapper` mode
    clears on the way out.
These are the SAME repair with OPPOSITE polarity, deliberately, because the two call
sites have opposite worst cases. Widening one predicate to serve both is the shape
`P-91`/`T292` names, and it is not done here.

T319 -- THE IN-SESSION DISCRIMINATOR AGAIN, BECAUSE T309's REPLACEMENT HAD THE SAME
SHAPE AS THE THING IT REPLACED. T309 attempt 1 keyed demotion on `task["fire"] !=
LOCK["fire"]` and would have demoted six live workers. T309 attempt 2 replaced it with
"was this id `in_progress` at the lock commit?" -- and T302 drove THAT against the real
history of fire `20260823-140001`, which took its lock at 14:00:08 with eight inherited
`in_progress` claims and at 14:05:01 DISPATCHED EIGHT WORKERS ONTO SEVEN OF THE SAME
IDS. Same direction, same magnitude: 7 demotable, every one a live worker
[VERIFIED: .softhouse/reviews/T302/a2/out-f5-cell.txt, cell B'].
The broken inference in both is "state at instant t0 settles ownership for all t > t0".
A fire that RE-DISPATCHES is the normal case here, not an exotic one. So the predicate
now asks three questions, all of which must hold, and the second is the one that closes
this: `inherited at the lock commit` AND `record NOT rewritten by this fire since` AND
`named by the caller with --corpse`. The matrix that graded T309 could not have caught
it -- its only advancing-clock cell was a fire that dispatched fresh ids, and its other
cells pass ONE commit as both the lock and the state under test, freezing the clock.
`.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.zsh` fixes the matrix as
well as the code, and CELL B' is permanent.

T319 also: `--corpse` is REQUIRED in-session (P-91 burden inversion), the lock-commit
anchor is no longer a commit-MESSAGE search (F6), a missing `.softhouse/LOCK` REFUSES
rather than granting `wrapper` authority (F7), `merged` is distinguished from
`never-committed` (F1), and NOTHING reads `task["fire"]` or `task["dispatched_at"]`.

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

WHO MAY CALL `--reconcile`, RESTATED AFTER T319. It rewrites tasks.json, so it refuses
unless it can POSITIVELY establish authority. `.softhouse/LOCK` must be on disk and name
a `pid` (> 1) that is an ANCESTOR of this process on this host. A MISSING lock file is
now a REFUSAL, not a licence: absence of the lock FILE is not absence of a fire, this
module has no liveness check of its own, and the caller that HAS run one must say so with
`--no-live-session-established-out-of-band`. (Before T319 the missing-lock leg returned
`wrapper` -- the demote-everything authority -- to anybody at all.)

Usage:  python3 .softhouse/bin/ready-tasks.py [--json] [--repo <dir>]
        python3 .softhouse/bin/ready-tasks.py --reconcile --fire <fire-id>
                [--rescue <task-branch>=<rescue-branch>]... [--corpse <task-id>]...
                [--no-live-session-established-out-of-band]
                [--dry-run] [--repo <dir>] [--deadline-secs <n>]
Run it from the repo root (or pass --repo).

`--corpse <task-id>` is REQUIRED, once per task, for anything an `in_session` caller
wants demoted. It is the third term of the in-session predicate and it is a NARROWING:
an id nobody named is never touched, whatever the git evidence says. `wrapper` mode does
not use it (the wrapper's authority is established out of band, and it demotes the whole
set by design).

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
      established as the lock holder at all (including: no LOCK on disk and no
      `--no-live-session-established-out-of-band`), or it is `in_session` and no
      `in_progress` task passed all three ownership terms. Fail-closed in every case.
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

# T319 -- the wrapper's lock-take subject, as one constant used by BOTH the parser and
# every message that quotes it, so the two cannot drift. The RELEASE subject
# ("softhouse: release local fire lock (...)") deliberately does not start with this.
LOCK_SUBJECT_OPEN = "softhouse: local fire lock ("

# T319 -- F7. `wrapper` mode demotes EVERY in_progress task, so it is the destructive
# authority, and it must never be handed out by DEFAULT. `caller_is_lock_holder()` used
# to grant it to any caller the instant `.softhouse/LOCK` was not on disk, justified by a
# liveness check that lives in a DIFFERENT FILE (fire-program.sh's
# `foreign_live_session_in_repo()`) and is enforced by exactly ONE of the callers this
# module's own usage string publishes. T302 drove it: no LOCK, eight live workers in
# tasks.json, `mode: wrapper`, "8 task(s) WOULD be demoted"
# [VERIFIED: .softhouse/reviews/T302/a2/out-f7-nolock.txt, cell 1]. This module contains
# no liveness check of its own -- its /bin/ps use is all `ps_ancestors()`, which answers
# "who am I", never "is anyone else alive in this checkout".
# So the precondition is now something the caller must STATE, in a form only a caller
# that has actually run the probe would think to state, and the absent-lock leg REFUSES
# without it. This is P-91's escape applied to an authority instead of a document:
# "INVERTING THE BURDEN -- require the document to POSITIVELY DEMONSTRATE coverage in a
# form the rule CONSTRUCTS rather than RECOGNISES" [VERIFIED: .softhouse/patterns.md,
# P-91].
NO_LOCK_FLAG = "--no-live-session-established-out-of-band"
LIVENESS_ESTABLISHED_OUT_OF_BAND = False


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
        # T319 -- F7. THIS LEG USED TO RETURN "wrapper" AND THAT WAS A DESTRUCTIVE
        # AUTHORITY GRANTED FOR FREE. The reasoning was "no lock => no live fire => nobody
        # to protect". Absence of a lock FILE is not absence of a fire, and the windows
        # are recorded, not hypothetical: P-85's two-orchestrator day ("TWO ORCHESTRATORS
        # HELD THE LOCK AT ONCE, AND THE CAUSE WAS AN UNPUSHED IN-FLIGHT STATE"
        # [VERIFIED: .softhouse/patterns.md, P-85]); any hand invocation between fires
        # while a session is working; and the wrapper's own `cat > "$LOCK"` whose rc is
        # not read. The one caller that HAS established liveness must say so.
        if LIVENESS_ESTABLISHED_OUT_OF_BAND:
            return "wrapper", ("no .softhouse/LOCK on disk, AND the caller passed %s, "
                               "asserting it ran a liveness probe of this checkout "
                               "itself. This module has no liveness check of its own, so "
                               "that assertion is the whole basis for the authority and "
                               "it is the CALLER's to justify." % NO_LOCK_FLAG), None
        return "refused", ("no .softhouse/LOCK on disk. Absence of the lock FILE is not "
                           "absence of a live fire, and this module cannot tell them "
                           "apart -- it has no liveness check, only ancestry. REFUSING. "
                           "A caller that has independently established no live session "
                           "owns this checkout (fire-program.sh does, with "
                           "`foreign_live_session_in_repo()`) must pass %s."
                           % NO_LOCK_FLAG), None
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
    # T319 -- T302's minor finding on this line, closed. `ps_ancestors` walks up to and
    # INCLUDING pid 1, so a LOCK naming pid 1 passed the ancestry test for every process
    # on the machine [VERIFIED: .softhouse/reviews/T302/a2/out-f7-nolock.txt, cell 2
    # reached `in_session` rather than `refused`]. pid 1 is launchd; it is nobody's fire.
    # Low severity today because the wrapper writes `"pid": $$`, but the check read
    # stronger than it behaved, and a check believed to be stronger than it is is P-22:
    # "A guard, a canary, or a control that cannot fail is worse than none -- because it
    # is believed" [VERIFIED: .softhouse/patterns.md, P-22].
    if pid <= 1:
        return "refused", ("LOCK records pid %d, which is not a fire -- pid 1 is the init "
                           "process and is an ancestor of everything on this host. "
                           "REFUSING." % pid), lock_fire
    ancestor_pids = [p for p, _ in anc if p > 1]
    if pid != os.getpid() and pid not in ancestor_pids:
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


def _parse_lock_subject(subject):
    """The fire id inside a wrapper lock-take subject, or None if this is not one.

    The wrapper writes exactly `softhouse: local fire lock (<STAMP>)`
    [VERIFIED: fire-program.sh, the `git commit -q -m` beside the LOCK heredoc].
    Its RELEASE commit says `softhouse: release local fire lock (<STAMP>)`, which does
    not match this shape -- and that difference is load-bearing below.
    """
    s = (subject or "").strip()
    if not s.startswith(LOCK_SUBJECT_OPEN) or not s.endswith(")"):
        return None
    fid = s[len(LOCK_SUBJECT_OPEN):-1].strip()
    return fid or None


def this_fires_lock_commit(lock_fire):
    """(sha, fire_id, reason) -- the commit in which the fire now holding the lock took
    it. sha is None when that could not be established, and then NOTHING may be demoted.

    T319 -- F6, AND WHY THE ANCHOR IS NO LONGER A MESSAGE SEARCH.

    T309 anchored with `git log -1 --fixed-strings --grep "softhouse: local fire lock
    (<id>)"`. `--grep` matches the WHOLE commit message, subject AND body, and `-1`
    returns the NEWEST match -- so the anchor was not "the wrapper's lock commit", it was
    "the most recent commit that mentions that string anywhere". T302 drove it: a later
    review commit whose BODY quotes the subject with a real fire id moves the anchor past
    this fire's dispatch and raises the demotion count from 7 to 8
    [VERIFIED: .softhouse/reviews/T302/a2/out-f6-grep.txt, cells 2 and 3]. The docstring
    it replaces reasoned only about ABSENCE ("this stops finding the commit and REFUSES")
    and said nothing about MULTIPLICITY, which fails the other way -- toward demoting.

    THE REPLACEMENT ASKS FOR SOMETHING A COMMIT MESSAGE CANNOT IMITATE: the anchor must
    be the newest commit that actually TOUCHED `.softhouse/LOCK`, and its SUBJECT (`%s`,
    not the message) must be the lock-take form. Taking the lock is writing that file;
    a reviewer quoting the subject does not write it, and a worker is forbidden to. So
    the evidence is again DERIVED FROM DOING THE WORK rather than asserted in prose --
    the same property the LOCK's own comment prefers for liveness, "because push recency
    is DERIVED from doing the work rather than maintained beside it, and so cannot
    silently fall behind the truth the way a remembered field can (P-45, five recorded
    times)" [VERIFIED: fire-program.sh, the P-85/STEP 0 comment above the LOCK heredoc].

    AND IT REMOVES A SECOND DEPENDENCE. T309's anchor needed `LOCK["fire"]` to build the
    search string, so when that field is missing the whole capability is inert: T302
    measured the LIVE lock of fire 20260827-230001 carrying no `fire` key at all, which
    made in_session mode 100% dead on the machine it shipped to [VERIFIED:
    .softhouse/reviews/T302/a2/out-f10-liveskew.txt]. Here the fire id is READ OFF the
    anchor commit's own subject, so it works with or without the field, and the field --
    when present -- is only a cross-check that REFUSES on disagreement.

    FAIL-CLOSED AT EVERY LEG. git not answering, no commit ever touching the path, a
    newest-touch that is a RELEASE rather than a take, an unparseable subject, or a LOCK
    whose `fire` disagrees with the subject: all return sha=None, and the caller demotes
    nothing. "I could not tell" is never spelled like "these are corpses".
    """
    rc, out, err = _run([GIT, "log", "-1", "--format=%H%x09%s", "--",
                         ".softhouse/LOCK"])
    if rc is None:
        return None, None, ("could not run git to find the newest commit touching "
                            ".softhouse/LOCK (%s) -- REFUSING" % err)
    if rc != 0:
        return None, None, ("git log exited %d looking for the newest commit touching "
                            ".softhouse/LOCK (%s) -- REFUSING" % (rc, err))
    if not out:
        return None, None, ("no commit reachable from HEAD has ever touched "
                            ".softhouse/LOCK, so the instant this fire took the lock is "
                            "UNKNOWN -- REFUSING (fail-closed)")
    sha, _, subject = out.splitlines()[0].partition("\t")
    sha = sha.strip()
    fire_id = _parse_lock_subject(subject)
    if not fire_id:
        return None, None, ("the newest commit touching .softhouse/LOCK is %s %r, which "
                            "is NOT a lock-take (`%s<id>)`). A LOCK is on disk but the "
                            "committed history does not show it being taken -- the two "
                            "disagree, and this refuses rather than choosing one."
                            % (sha[:9], subject.strip(), LOCK_SUBJECT_OPEN))
    if lock_fire and lock_fire != fire_id:
        return None, None, ("the LOCK on disk records fire %r but the newest lock-take "
                            "commit %s is fire %r -- the on-disk lock and the committed "
                            "history disagree about who holds this repo. REFUSING."
                            % (lock_fire, sha[:9], fire_id))
    corrob = ("; the LOCK's own `fire` field agrees" if lock_fire else
              "; the LOCK on disk records no `fire` field, so the id is taken from the "
              "commit subject alone -- which is why this no longer depends on that field")
    return sha, fire_id, ("this fire's lock commit is %s, the newest commit that TOUCHED "
                          ".softhouse/LOCK, and its SUBJECT is the lock-take form for "
                          "fire %s%s" % (sha[:9], fire_id, corrob))


def lock_commit_records(sha):
    """(records, in_progress_ids, reason) -- every task's record as committed at `sha`.

    `records` maps task id -> the task object exactly as it stood at that commit;
    `in_progress_ids` is the subset claiming `in_progress` there. Both are None when the
    blob could not be read, and then NOTHING may be demoted.
    """
    rc, blob, err = _run([GIT, "show", "%s:.softhouse/tasks.json" % sha])
    if rc is None:
        return None, None, ("could not run git to read tasks.json at the lock commit %s "
                            "(%s) -- REFUSING" % (sha[:9], err))
    if rc != 0 or not blob:
        return None, None, ("tasks.json is not readable at the lock commit %s (git rc=%s,"
                            " %s) -- REFUSING" % (sha[:9], rc, err))
    try:
        prior = json.loads(blob)["tasks"]
    except (ValueError, KeyError, TypeError) as exc:
        return None, None, ("tasks.json at the lock commit %s did not parse (%s) -- "
                            "REFUSING" % (sha[:9], exc))
    records, ids = {}, set()
    for t in prior:
        tid = t.get("id")
        if not tid:
            continue
        records[tid] = t
        if t.get("status") == "in_progress":
            ids.add(tid)
    return records, ids, ("at that commit %d task(s) already claimed in_progress: %s"
                          % (len(ids), ", ".join(sorted(ids)) if ids else "none"))


def _canon(obj):
    """A task record reduced to comparable bytes. Key order is normalised so a rewrite
    that only reorders keys is not read as a change; nothing else is normalised, and no
    field is INTERPRETED -- see term 2 below for why that is the point."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _changed_keys(then, now):
    return sorted(k for k in set(then) | set(now) if then.get(k) != now.get(k))


def task_is_demotable_in_session(t, fire_id, prior, named_corpses):
    """(ok, reason) -- may an IN-SESSION caller demote this `in_progress` task?

    `prior` is (records, in_progress_ids) from the lock commit, or None when that could
    not be established. `named_corpses` is the set given by `--corpse`.

    ===================================================================================
    T319 -- F5. WHY T309's SINGLE TERM WAS WRONG, AND WHAT REPLACES IT.
    ===================================================================================

    T309 asked ONE question: "was this id `in_progress` in the tasks.json committed when
    this fire took the lock?" Its argument was that at that instant the fire has
    dispatched nothing, so everything `in_progress` there is inherited. The FIRST half is
    true. The second does not follow, and the counter-example is the very incident T309
    was written about:

        14:00:08  5428c0a4  fire 20260823-140001 takes its lock; 8 tasks already
                            in_progress -- the corpses 20260823-080004 left.
        14:05:01  5964ab54  "DISPATCH fire 20260823-140001 batch 1 -- 8 workers,
                            PUSHED BEFORE SPAWN (P-85)" -- and SEVEN of the ids it
                            dispatches are ids from that same set.
        14:24:27  ab9b3b68  a commit by a LIVE worker of that fire, on one of them.

    Run T309's own cell shape with the clock advanced five minutes and it reports
    "7 demotable", every one a live worker of the lock-holding fire
    [VERIFIED: .softhouse/reviews/T302/a2/out-f5-cell.txt, cell B'].

    "State at instant t0 determines ownership for all t > t0" is the broken inference,
    and RE-DISPATCH is not exotic here: it is the documented reason the driver opens on
    inherited `in_progress` tasks at all. This program re-dispatches parked and
    needs_retry tasks constantly.

    THREE TERMS NOW, ALL REQUIRED, EACH FAIL-CLOSED ON ITS OWN.

    TERM 1 -- INHERITED. The id was `in_progress` at this fire's lock commit. T309's
      term, kept: it is necessary. It is no longer sufficient and is no longer asked
      alone.

    TERM 2 -- UNTOUCHED SINCE. The task's record is byte-identical to its record at the
      lock commit. This is the term F5 is about, and it is MEASURED rather than reasoned
      [VERIFIED: .softhouse/capture/t319-reconciler-f5/out-objdiff.txt]. At 5964ab54 all
      seven re-dispatched ids differ from their lock-commit records in `attempts` (0->1),
      `fire` and `note`; ZERO survive term 2, which is the correct answer.

      WHY A WHOLE-RECORD COMPARISON AND NOT A FIELD. Reading a named field is the shape
      that has now failed three times in a row -- `task["fire"]` (T309 attempt 1, six
      live workers), `dispatched_at` (stale by four days, absent on batch-2 tasks), and
      `task["branch"]` (stale after a rename, T302 F9). Each is a value someone must
      REMEMBER to refresh, which is P-45 -- "a guard that only works when someone
      remembers to run it enforces nothing" [VERIFIED: .softhouse/patterns.md, P-45] --
      with the verb changed. Term 2 interprets NO field. It asks only whether the fire
      holding the lock has written to this task's record since it took it, and DISPATCH
      IS A WRITE: the driver's own dispatch commit message is "record PUSHED BEFORE
      SPAWN (P-85)". So the deletion of `fire` and `dispatched_at` recommended by T302
      does not weaken this at all -- `attempts` and `note` still move, and even a bulk
      deletion of those keys from every record would make every record DIFFER from the
      lock blob, withholding everything, which is the safe direction.

      RESIDUAL RISK, STATED AND NOT PAPERED OVER: term 2 detects a re-dispatch because a
      re-dispatch writes the record. A fire that spawned a worker onto an already-
      `in_progress` task while writing NOTHING would be invisible to it. That would
      violate P-85 ("record PUSHED BEFORE SPAWN"), it is not a shape this repo has
      recorded, and it is exactly what term 3 exists to backstop.

    TERM 3 -- POSITIVELY NAMED. The caller passed `--corpse <id>` for this id. This is
      the burden inversion, not another pattern: P-91 -- "a guard phrased as a STRUCTURAL
      PATTERN over the shape of its input can always be re-nested one level out ... The
      escape is not a better pattern: it is INVERTING THE BURDEN -- require the document
      to POSITIVELY DEMONSTRATE coverage in a form the rule CONSTRUCTS rather than
      RECOGNISES" [VERIFIED: .softhouse/patterns.md, P-91]. Terms 1 and 2 are both
      derivations over history: if a future edit gets a derivation wrong, term 3 still
      caps the blast radius at the ids the caller enumerated by hand. An in-session
      caller that names nothing demotes nothing, whatever the git evidence says.

      This is NOT the "remembered obligation" P-45 forbids, and the difference is the
      direction: forgetting to pass `--corpse` leaves an `in_progress` lie, which the
      wrapper's exit-path clears; there is no way to forget it INTO destroying work.

    FAIL-CLOSED DIRECTION AT THIS CALL SITE, AND IT IS THE OPPOSITE OF THE WRAPPER'S ON
    PURPOSE. In-session a live fire IS running, so the destructive error is demoting live
    work and it is irreversible. The non-destructive error leaves an `in_progress` lie
    standing, which is recoverable. Widening one predicate to serve both call sites is
    the shape T292/P-91 names and it is deliberately not done.

    ONE HONEST QUALIFICATION TO THAT ARGUMENT, WHICH T309 STATED UNCONDITIONALLY: the
    lie's second reader is the wrapper's own exit path in `wrapper` mode, and that path
    only runs when `foreign_live_session_in_repo()` returns 1. T302 F11 showed it returns
    0 -- REFUSE -- while any `claude` sits in the repo root, which is the documented
    interactive entry point. So the lie is recoverable in the normal case and can persist
    across a fire in the interactive case. It is still the cheaper error by a wide margin.
    """
    tid = t.get("id")
    if prior is None:
        return False, ("the state at this fire's lock commit could not be established -- "
                       "REFUSING (fail-closed; demoting a live worker cannot be undone)")
    records, predating = prior

    # TERM 1 -- inherited?
    if tid not in predating:
        return False, ("TERM 1 FAILS: it was NOT claiming in_progress when fire %s took "
                       "the lock, so THIS fire dispatched it: it is a LIVE sibling. "
                       "REFUSING." % fire_id)

    # TERM 2 -- untouched since? THIS IS THE F5 FIX.
    then = records.get(tid)
    if then is None:
        return False, ("TERM 2 FAILS: no record for this id exists at the lock commit, so "
                       "its history since cannot be compared. REFUSING.")
    if _canon(then) != _canon(t):
        keys = _changed_keys(then, t)
        return False, ("TERM 2 FAILS: it WAS in_progress at the lock commit, but fire %s "
                       "has REWRITTEN its record since -- %s changed. A dispatch is a "
                       "write (the driver's own commits say 'record PUSHED BEFORE SPAWN "
                       "(P-85)'), so this reads as a RE-DISPATCH by the fire holding the "
                       "lock: a LIVE worker. REFUSING. [This is the case that made T309's "
                       "single term demote seven live workers on 2026-08-23.]"
                       % (fire_id, ", ".join("`%s`" % k for k in keys) or "some key"))

    # TERM 3 -- positively named by the caller?
    if tid not in named_corpses:
        return False, ("TERM 3 FAILS: no `--corpse %s` was passed. An in-session caller "
                       "must NAME each dispatch it claims is dead; this tool will not "
                       "sweep a set nobody enumerated. REFUSING." % (tid or "<id>"))

    return True, ("ALL THREE TERMS HOLD: it was already claiming in_progress at fire %s's "
                  "lock commit (inherited), its record has NOT been rewritten since (so "
                  "this fire has not re-dispatched it), and the caller named it with "
                  "`--corpse`. The dispatch belongs to an earlier fire that is over; "
                  "WHICH earlier fire is not established here." % fire_id)


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
        # T319 -- F1, the pruned half. A merged-and-then-pruned branch is byte-identical
        # to a branch that never existed, and this used to assert the flattering one.
        return "absent", ("Its recorded branch %s does not exist in this repo. THIS IS "
                          "NOT EVIDENCE THAT NOTHING WAS DONE: a branch that was MERGED "
                          "INTO main AND THEN PRUNED -- this repo's stated habit -- looks "
                          "exactly the same from here, and so does a branch that was "
                          "RENAMED (T302 measured one: T299's recorded name was stale "
                          "after a rename and the live branch was elsewhere). Provenance "
                          "UNVERIFIED; check `git log --all --grep` for the task id before "
                          "treating this as unstarted." % branch)
    if rc != 0:
        return "unverified", ("git rev-parse on %s exited %d (%s) -- WIP state "
                              "UNVERIFIED, NOT assumed empty." % (branch, rc, err))
    # T319 -- F1, THE HALF THAT LANDED ON REAL DATA. `rev-list --count main..B` is B
    # minus everything reachable from main, so a branch that was MERGED gives ZERO --
    # BECAUSE THE WORK LANDED. This function read that zero as "nothing was ever
    # committed to it", demoted the task to `needs_retry` (the status that OFFERS a task
    # for re-dispatch) and invited the next fire to redo work already on main. T302 drove
    # it against a clone carrying all 528 real heads and the real corpse blob: THREE OF
    # THE EIGHT real corpses -- T297, T298, T308 -- are MERGED into main and got that
    # sentence [VERIFIED: .softhouse/reviews/T302/a2/out-f9-realcorpses.txt].
    # The discriminator was always available one command away.
    rc2, count, err2 = _run([GIT, "rev-list", "--count", "main.." + branch])
    if rc2 != 0 or not count.isdigit():
        return "unverified", ("Branch %s exists at %s but its commit count vs main "
                              "could not be read (git rc=%s) -- UNVERIFIED."
                              % (branch, sha[:9], rc2))
    n = int(count)
    if n > 0:
        # n > 0 means at least one commit is NOT reachable from main, so the branch cannot
        # be an ancestor of main and the merged question does not arise. The extra git
        # call below is therefore spent ONLY on the ambiguous zero -- which keeps this
        # function at two git calls in the healthy case, the figure T302's budget
        # measurement was taken against (0.0679 s per task, crossover with the ~7 s signal
        # budget at N ~ 100) [VERIFIED: .softhouse/reviews/T302/a2/out-f8b-realgit.txt].
        return "commits", ("Its branch %s has %d commit(s) ahead of main, head %s."
                           % (branch, n, sha[:9]))
    # n == 0. THIS IS THE AMBIGUOUS ZERO AND IT IS THE WHOLE OF F1: "merged" and "nothing
    # was ever committed" produce the SAME zero, and this function used to print the
    # second one. Ask the question that separates them.
    rcm, _, errm = _run([GIT, "merge-base", "--is-ancestor", sha, "main"])
    if rcm == 0:
        return "merged", ("!! Its branch %s exists at %s and IS MERGED INTO main -- every "
                          "commit on it is reachable from main. The work LANDED. Do NOT "
                          "read this as an unstarted task and do NOT re-dispatch it "
                          "without reading that history first; `needs_retry` here means "
                          "'somebody must adjudicate', not 'do it again'." % (branch, sha[:9]))
    if rcm != 1:
        return "unverified", ("Its branch %s exists at %s and has no commit ahead of main, "
                              "but `git merge-base --is-ancestor` could not answer (rc=%s, "
                              "%s) -- so MERGED and NEVER-COMMITTED cannot be told apart "
                              "here. UNVERIFIED, not empty."
                              % (branch, sha[:9], rcm, errm))
    return "absent", ("Its branch %s exists at %s, has NO commit ahead of main, and is NOT "
                      "an ancestor of main -- so nothing was ever committed to it. (The "
                      "merged case was checked for and excluded; this is a measurement, "
                      "not the default reading of a zero.)" % (branch, sha[:9]))


def reconcile(fire, rescue_map, named_corpses, dry_run=False):
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
    prior, fire_id = None, lock_fire
    if mode == "in_session":
        # T319: still ONE git derivation for the whole run -- three `git` calls total
        # (the anchor, the blob, and nothing per task) -- so the wall-clock budget cannot
        # be spent proportionally to the number of corpses.
        sha, fire_id, anchor_why = this_fires_lock_commit(lock_fire)
        print("  in-session anchor: %s" % anchor_why)
        if sha:
            records, predating, blob_why = lock_commit_records(sha)
            print("  in-session evidence: %s" % blob_why)
            if records is not None:
                prior = (records, predating)
        if not named_corpses:
            print("  in-session `--corpse`: NONE PASSED. Term 3 will fail for every task; "
                  "an in-session caller must NAME each dispatch it claims is dead.")
        else:
            print("  in-session `--corpse`: %s" % ", ".join(sorted(named_corpses)))
    for t in live:
        if mode == "wrapper":
            demote.append(t)
            continue
        ok, reason = task_is_demotable_in_session(t, fire_id, prior, named_corpses)
        (demote if ok else withheld).append((t, reason))

    if mode == "in_session":
        print("  IN-SESSION authority: %d demotable, %d WITHHELD (a live fire is running; "
              "a task may be touched only if it was inherited at the lock commit, has NOT "
              "been rewritten by this fire since, AND was named with `--corpse`)"
              % (len(demote), len(withheld)))
        for t, reason in withheld:
            print("  %-8s WITHHELD  %s" % (t.get("id", "?"), reason))
        demote = [t for t, _ in demote]
        if not demote:
            print("  RESULT: REFUSED -- nothing this caller is authorised to repair; "
                  "tasks.json was NOT modified. The wrapper's exit-path reconcile runs "
                  "in `wrapper` mode and clears what is left -- but only when "
                  "`foreign_live_session_in_repo()` returns 1, which it does not while "
                  "any `claude` sits in the repo root (T302 F11). If that is the case "
                  "here, the `in_progress` lines are still a lie and somebody must say "
                  "so by hand.")
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
        # T309 attempt 1 wrote `t["fire"]` in here as the killing fire; T309 attempt 2
        # demoted it to "corroboration" and printed it anyway. T319 DELETES IT. T302
        # adjudicated the field: `dispatched_at` is four days stale on the tasks that
        # carry it and absent entirely on the ones dispatched in batch 2, the writer that
        # produces the staleness is unchanged, and only 12 of 203 tasks carry `fire` at
        # all [VERIFIED: .softhouse/reviews/T302/REVIEW-A2.md, "adjudicating T309's own
        # follow-ups (a)"]. A field printed beside real evidence is read as evidence.
        # P-22: "A guard, a canary, or a control that cannot fail is worse than none --
        # because it is believed" [VERIFIED: .softhouse/patterns.md, P-22]; a FACT that
        # cannot be right is the same trade. So neither field is read anywhere in this
        # module now, and the note says what each mode actually established:
        #   wrapper mode    -- the driver that just died IS this fire's; naming `--fire`
        #                      is an observation, not a guess.
        #   in_session mode -- three terms held (inherited at the lock commit, not
        #                      rewritten since, named by the caller). That establishes the
        #                      dispatch is INHERITED, never WHICH earlier fire made it.
        if mode == "wrapper":
            killer = ("fire %s -- OBSERVED: this wrapper stopped its own driver and is "
                      "reconciling its own dispatches." % fire)
        else:
            killer = ("an EARLIER fire -- established, not guessed: this task was already "
                      "claiming in_progress in the tasks.json committed when fire %s took "
                      "the lock, its record has NOT been rewritten since, and the caller "
                      "named it as a corpse. So the dispatch predates %s. WHICH earlier "
                      "fire is NOT established, and no field on this task is trusted to "
                      "say." % (fire_id or fire, fire_id or fire))
        merged_clause = ""
        if kind.startswith("merged"):
            merged_clause = (" !! READ THIS BEFORE RE-DISPATCHING: its branch is MERGED "
                             "INTO main. `needs_retry` here means SOMEBODY MUST "
                             "ADJUDICATE, not 'do it again' -- re-running merged work is "
                             "the concrete cost T302 measured on 3 of 8 real corpses.")
        note = ("worker killed mid-flight by %s -- the fire ended while this task "
                "was still in_progress, and a killed worker is dead, not paused "
                "(softhouse-program STEP 5.5, 'NEVER exit with live workers', item 4). "
                "%s%s Completeness UNVERIFIED: no handoff "
                "was signed off and no reviewer saw this. Reconciled by fire %s in `%s` "
                "mode." % (killer, " ".join(clauses), merged_clause, fire, mode))
        prior_note = t.get("note")
        if prior_note:
            note += "  [prior note: %s]" % prior_note
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
    # T319 -- `fire` AND `dispatched_at` ARE NO LONGER PRINTED, AND NOTHING READS THEM.
    # T309 attempt 2 printed both with a disclaimer attached. T302 then measured what the
    # disclaimer was disclaiming: `dispatched_at` four days stale where present and
    # ABSENT on the tasks dispatched in batch 2, `fire` on 12 of 203 tasks, and the WRITER
    # unchanged, so the next re-dispatch reproduces the staleness exactly [VERIFIED:
    # .softhouse/reviews/T302/REVIEW-A2.md, "adjudicating T309's own follow-ups (a)"].
    # A wrong field printed at STEP 0, under a caveat, is still read as a fact by the
    # third reader -- P-22, "A guard, a canary, or a control that cannot fail is worse
    # than none -- because it is believed" [VERIFIED: .softhouse/patterns.md, P-22].
    # DECISION (T319, agent-decidable per CLAUDE.md "Answering gates": ENGINEERING):
    # DELETE THEM. This file no longer reads either field for any purpose. The orchestrator
    # must (a) stop WRITING them at dispatch and (b) strip them from tasks.json, which is
    # owned by the live fire and which this worker must not edit -- see the handoff.
    # `--reconcile` term 2 is unaffected: it compares WHOLE RECORDS and interprets no
    # field, so removing these keys leaves `attempts` and `note` moving on every
    # dispatch, and a one-off bulk strip would make every record differ from its
    # lock-commit form -- withholding everything, which is the safe direction.
    if live:
        # T319 -- F4. THIS PARAGRAPH USED TO PROMISE A REPAIR ON PATHS WHERE IT DOES NOT
        # HAPPEN, printed UNCONDITIONALLY, in the tool a driver reads at STEP 0 to decide
        # what to dispatch. That is P-45 -- "a guard that only works when someone
        # remembers to run it enforces nothing" [VERIFIED: .softhouse/patterns.md, P-45]
        # -- in the fix for P-45: a guard ASSERTED to run, in prose, to the only reader
        # that matters. The three false paths T302 named are all still real: a REFUSE
        # from `foreign_live_session_in_repo()` (which returns 0 = REFUSE while ANY
        # `claude` sits in the repo root, the documented interactive entry point), a
        # REFUSE from `caller_is_lock_holder()`, and a signal-path budget too small to
        # run the reconcile at all. So the promise is now a CONDITIONAL, and it names
        # what it cannot promise.
        print("  ^ If no fire is running right now, every line above is a DEAD dispatch")
        print("    and this section is lying to you. fire-program.sh runs")
        print("    `ready-tasks.py --reconcile` on its way out and rewrites these to")
        print("    needs_retry with the evidence in a note -- BUT ONLY IF: it exits")
        print("    normally or with enough signal budget left; no live `claude` is")
        print("    working in this checkout (an idle interactive session in the repo")
        print("    root also counts, and REFUSES); and the lock-holder check passes.")
        print("    On any of those the lines above STAND, unrepaired. Do not read their")
        print("    survival as proof a fire is running.")
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
    global LIVENESS_ESTABLISHED_OUT_OF_BAND
    args = list(argv)
    fire, rescue_map, do_reconcile, dry = None, {}, False, False
    named_corpses = set()
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--reconcile":
            do_reconcile = True
        elif a == "--dry-run":
            dry = True
        elif a == NO_LOCK_FLAG:
            # T319 -- F7. Deliberately long, deliberately ugly, and deliberately NOT
            # spelled `--force`. It is not a permission to override a check; it is the
            # caller SUPPLYING a fact this module cannot measure, and the spelling is the
            # documentation. Only fire-program.sh has run the probe that makes it true.
            LIVENESS_ESTABLISHED_OUT_OF_BAND = True
        elif a == "--json":
            pass                                    # handled inside main()
        elif a in ("--fire", "--repo", "--rescue", "--deadline-secs", "--corpse"):
            if i + 1 >= len(args):
                print("usage error: %s needs a value" % a, file=sys.stderr)
                return 64
            i += 1
            if a == "--fire":
                fire = args[i]
            elif a == "--corpse":
                # T319 -- term 3. Repeatable; one task id per occurrence.
                tid = args[i].strip()
                if not tid:
                    print("usage error: --corpse wants a task id, got %r" % args[i],
                          file=sys.stderr)
                    return 64
                named_corpses.add(tid)
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
        return reconcile(fire, rescue_map, named_corpses, dry_run=dry)
    if named_corpses or LIVENESS_ESTABLISHED_OUT_OF_BAND:
        print("usage error: --corpse and %s are only meaningful with --reconcile"
              % NO_LOCK_FLAG, file=sys.stderr)
        return 64
    return main()


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
