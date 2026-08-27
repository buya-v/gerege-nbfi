"""T309 attempt 2, patch 11 -- stop the other three sites trusting the stale `fire` field.

Patch 10 removed `task["fire"]` from the AUTHORITY. Three sites still treated it as
truth: the module docstring, the note written onto a demoted task (a FALSE ATTRIBUTION
in money-adjacent state), and the `main()` report's advice. Refuses on any missing anchor.
"""
import io
import sys

P = ".softhouse/bin/ready-tasks.py"
s = io.open(P, encoding="utf-8").read()
subs = []

# ---------------------------------------------------------------- module docstring ---
subs.append((
'''  * `in_session` mode (a driver or worker, a fire IS live): demotes ONLY tasks whose
    recorded `fire` differs from the fire id on `.softhouse/LOCK`. It fails towards
    REFUSING, which is right there -- the destructive error is demoting live work and it
    cannot be undone, while the non-destructive error leaves a lie that `wrapper` mode
    clears on the way out.
''',
'''  * `in_session` mode (a driver or worker, a fire IS live): demotes ONLY tasks that were
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
'''))

# ------------------------------------------------------------------ the demotion note ---
subs.append((
'''        # T309: name the fire that ACTUALLY dispatched it when the task records one. The
        # pre-T309 note always named `--fire`, i.e. the RECONCILING fire -- which was
        # right only when the corpse belonged to the fire doing the reconciling, and was
        # a false attribution in exactly the 2026-08-23 case (fire 20260823-140001
        # clearing fire 20260823-080004's dispatches).
        owner = t.get("fire")
        owner = owner.strip() if isinstance(owner, str) else ""
        if owner:
            killer = ("fire %s (the owning fire recorded on the task at dispatch)"
                      % owner)
        else:
            killer = ("fire %s -- INFERRED, not observed: this task recorded no owning "
                      "fire, so this is the RECONCILING fire's id and may not be the "
                      "fire that actually dispatched it" % fire)
''',
'''        # WHICH FIRE KILLED IT -- SAY ONLY WHAT THE EVIDENCE SUPPORTS.
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
'''))

# ----------------------------------------------------------------- the main() report ---
subs.append((
'''        # T309: the owning fire is the discriminator `--reconcile` needs in `in_session`
        # mode, and a task that carries none is UNCLEARABLE from inside a live fire. That
        # is a defect in whoever dispatched it, so it is PRINTED rather than left to be
        # discovered at reconcile time -- an omission that announces itself is not a
        # remembered obligation (P-45: "a guard that only works when someone remembers to
        # run it enforces nothing").
        owner = t.get("fire")
        owner = owner.strip() if isinstance(owner, str) else ""
        if owner:
            print("           owning fire: %s" % owner)
        else:
            print("           owning fire: NONE RECORDED -- whoever dispatched this did "
                  "not stamp a fire id, so a LIVE driver cannot prove it is a corpse and "
                  "`--reconcile` will WITHHOLD it. Only the wrapper's exit path clears it.")
''',
'''        # T309 attempt 2: PRINT the `fire` field and its dispatch stamp, and say plainly
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
'''))

for old, new in subs:
    if old not in s:
        sys.exit("ANCHOR NOT FOUND:\\n%s" % old[:160])
    s = s.replace(old, new, 1)

io.open(P, "w", encoding="utf-8").write(s)
print("patched %s -- %d substitutions" % (P, len(subs)))
