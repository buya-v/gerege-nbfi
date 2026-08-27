"""T309 attempt 2, patch 10 -- replace the in_session ownership discriminator.

READ AND REPORT ONLY on ratified artefacts; this writes exactly one path, the resolver
under .softhouse/bin/, which is in this task's files_hint. It refuses if the anchor text
is not found byte-for-byte, so it cannot half-apply.
"""
import io
import sys

P = ".softhouse/bin/ready-tasks.py"
s = io.open(P, encoding="utf-8").read()

OLD_HEAD = '''def task_is_demotable_in_session(t, lock_fire):
    """(ok, reason) -- may an IN-SESSION caller demote this `in_progress` task?

    T309. THE DISCRIMINATOR IS THE OWNING FIRE ID, AND THE ARGUMENT FOR IT IS THE LOCK'S
    EXCLUSIVITY, NOT A REMEMBERED FIELD.
'''

OLD_TAIL = '''    if not lock_fire:
        return False, ("the LOCK records no `fire` id, so 'is this dispatch mine?' "
                       "cannot be decided -- REFUSING (fail-closed)")
    owner = t.get("fire")
    owner = owner.strip() if isinstance(owner, str) else ""
    if not owner:
        return False, ("no `fire` recorded on this task, so it cannot be shown to belong "
                       "to a DEAD fire -- REFUSING. Whoever dispatched it did not stamp "
                       "an owner; the wrapper's exit-path reconcile will clear it.")
    if owner == lock_fire:
        return False, ("dispatched by fire %s, which is the fire holding the lock RIGHT "
                       "NOW -- this is a LIVE sibling. REFUSING." % owner)
    return True, ("dispatched by fire %s; the lock is held by fire %s, and only one fire "
                  "holds it at a time, so %s is over."
                  % (owner, lock_fire, owner))
'''

NEW = '''def dispatches_predating_this_fire(lock_fire):
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
'''

if OLD_HEAD not in s:
    sys.exit("ANCHOR NOT FOUND: task_is_demotable_in_session header")
start = s.index(OLD_HEAD)
if OLD_TAIL not in s:
    sys.exit("ANCHOR NOT FOUND: task_is_demotable_in_session body")
end = s.index(OLD_TAIL) + len(OLD_TAIL)
if end <= start:
    sys.exit("ANCHORS OUT OF ORDER")
s = s[:start] + NEW + s[end:]

# --- call site -------------------------------------------------------------------
OLD_CALL = '''    demote, withheld = [], []
    for t in live:
        if mode == "wrapper":
            demote.append(t)
            continue
        ok, reason = task_is_demotable_in_session(t, lock_fire)
        (demote if ok else withheld).append((t, reason))

    if mode == "in_session":
        print("  IN-SESSION authority: %d demotable, %d WITHHELD (a live fire is running; "
              "only dispatches proven to belong to another fire may be touched)"
              % (len(demote), len(withheld)))
'''
NEW_CALL = '''    demote, withheld = [], []
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
'''
if OLD_CALL not in s:
    sys.exit("ANCHOR NOT FOUND: reconcile() call site")
s = s.replace(OLD_CALL, NEW_CALL, 1)

io.open(P, "w", encoding="utf-8").write(s)
print("patched %s" % P)
