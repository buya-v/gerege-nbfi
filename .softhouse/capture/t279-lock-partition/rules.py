#!/usr/bin/env python3
"""T279 — STEP 0 lock freshness rules, as EXECUTABLE PREDICATES.

T265 F-1 asserts that the four shipped rules do not partition the state space.  A table
derived by reading the rules is an opinion; this file turns each arm into a boolean
function so the table is derived by RUNNING them.

Transcription discipline: every arm below carries the literal sentence it came from, and
its condition uses ONLY the terms that sentence names.  Where a sentence names no term for
a dimension, the arm is silent on that dimension -- which is exactly how a rule set stops
partitioning, so the transcription must not "helpfully" add the missing conjunct.

THE STATE SPACE (5 dimensions, 192 states):

  lock      present | absent
  released  null    | set                 (`released_at` in the LOCK body)
  started   lt6     | b6_24 | ge24 | unreadable   (age of `started_at`)
  tip       lt6     | ge6   | unreadable          (age of newest commit on origin/main)
  pid       alive_here | dead_here | absent | other_host

`unreadable` is a first-class value, not an edge case: STEP 0 is read by an agent on a
fresh clone with a hand-written LOCK, and "I could not read that signal" is a state the
rule set must have a verdict for.  6h and 24h are the two thresholds the repaired rules
use; the shipped rules use only 6h, so `b6_24` and `ge24` are both "over 6h" to them.

VERDICTS: FREE (take it), TAKE (take it over), HELD (exit), NONE (no arm matched).
FREE and TAKE are distinguished because they mean different things to the operator, but
both are "may proceed"; the safety property is about HELD vs {FREE,TAKE}.
"""

import itertools

LOCK = ("present", "absent")
RELEASED = ("null", "set")
STARTED = ("lt6", "b6_24", "ge24", "unreadable")
TIP = ("lt6", "ge6", "unreadable")
PID = ("alive_here", "dead_here", "absent", "other_host")

DIMS = ("lock", "released", "started", "tip", "pid")


def states():
    for combo in itertools.product(LOCK, RELEASED, STARTED, TIP, PID):
        yield dict(zip(DIMS, combo))


def collapse(s):
    """Lock-absent states are degenerate: the other four dimensions are unobservable
    because there is no file to read them from.  Collapse them to one canonical state so
    the reported counts are counts of DISTINGUISHABLE situations."""
    if s["lock"] == "absent":
        return ("absent", "-", "-", "-", "-")
    return tuple(s[d] for d in DIMS)


# ---------------------------------------------------------------- helpers ---
def started_over_6h(s):
    return s["started"] in ("b6_24", "ge24")


def started_over_24h(s):
    return s["started"] == "ge24"


def tip_under_6h(s):
    return s["tip"] == "lt6"


def tip_over_6h(s):
    return s["tip"] == "ge6"


def dead_pid_here(s):
    return s["pid"] == "dead_here"


# =========================================================== OLD (shipped) ===
# `.claude/skills/softhouse-program/SKILL.md` STEP 0, "The test, in order:", as landed by
# commit 607252a and unchanged on main at 59fc41b4.
#
# NOTE the implicit arm 0.  STEP 0 says "If it is held and live and not yours ... exit.
# Otherwise write it", so "no LOCK file at all" is free.  It is transcribed as an arm
# because leaving it out would manufacture a hole that the prose does not have.

OLD_ARMS = [
    ("O0", "FREE",
     "(implicit) there is no LOCK file -> write it",
     lambda s: s["lock"] == "absent"),

    ("O1", "FREE",
     "1. `released_at` is non-null -> free. Take it.",
     lambda s: s["lock"] == "present" and s["released"] == "set"),

    ("O2", "HELD",
     "2. `origin/main`'s newest commit is under 6 h old AND `released_at` is null -> HELD",
     lambda s: s["lock"] == "present" and tip_under_6h(s) and s["released"] == "null"),

    ("O3", "TAKE",
     "3. Both `started_at` and the newest `origin/main` commit are over 6 h old -> stale",
     lambda s: s["lock"] == "present" and started_over_6h(s) and tip_over_6h(s)),

    ("O4", "TAKE",
     "4. The lock names a `pid` on THIS host and that pid is gone -> dead holder",
     lambda s: s["lock"] == "present" and dead_pid_here(s)),
]

# =========================================================== NEW (repaired) ==
# Each arm is written to be MUTUALLY EXCLUSIVE of every other arm, not merely
# first-match-wins.  That is the property T265 actually needs: a rule set whose answer
# depends on evaluation order is a rule set two orchestrators can read differently, which
# is the P-85 shape.  Exclusivity is asserted by enumeration in enumerate.py, not claimed.
#
# The exclusion prefix `held_unresolved` is the standing "none of the decisive arms fired"
# condition; writing it explicitly is what makes the arms disjoint.

def _lock_held(s):
    return s["lock"] == "present" and s["released"] == "null"


NEW_ARMS = [
    ("N0", "FREE",
     "0. No LOCK file -> free.",
     lambda s: s["lock"] == "absent"),

    ("N1", "FREE",
     "1. `released_at` non-null -> free.",
     lambda s: s["lock"] == "present" and s["released"] == "set"),

    ("N2", "TAKE",
     "2. DEAD HOLDER. LOCK names a pid on THIS host and it is gone -> take over, any age.",
     lambda s: _lock_held(s) and dead_pid_here(s)),

    ("N3", "TAKE",
     "3. CEILING. `started_at` over 24 h -> take over, however fresh the tip looks.",
     lambda s: _lock_held(s) and not dead_pid_here(s) and started_over_24h(s)),

    ("N4", "HELD",
     "4. LIVE. Newest origin/main commit under 6 h old -> HELD.",
     lambda s: _lock_held(s) and not dead_pid_here(s) and not started_over_24h(s)
     and tip_under_6h(s)),

    ("N5", "TAKE",
     "5. STALE. Newest origin/main commit over 6 h old AND `started_at` over 6 h -> stale.",
     lambda s: _lock_held(s) and not dead_pid_here(s) and not started_over_24h(s)
     and tip_over_6h(s) and started_over_6h(s)),

    ("N6", "HELD",
     "6. Anything else, including any signal you could not read -> HELD.",
     lambda s: not (
         s["lock"] == "absent"
         or (s["lock"] == "present" and s["released"] == "set")
         or (_lock_held(s) and dead_pid_here(s))
         or (_lock_held(s) and not dead_pid_here(s) and started_over_24h(s))
         or (_lock_held(s) and not dead_pid_here(s) and not started_over_24h(s)
             and tip_under_6h(s))
         or (_lock_held(s) and not dead_pid_here(s) and not started_over_24h(s)
             and tip_over_6h(s) and started_over_6h(s))
     )),
]


def matches(arms, s):
    return [(aid, verdict) for aid, verdict, _txt, pred in arms if pred(s)]
