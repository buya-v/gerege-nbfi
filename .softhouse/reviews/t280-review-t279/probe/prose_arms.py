#!/usr/bin/env python3
"""T280 — transcribe the SHIPPED SKILL.md STEP 0 arms LITERALLY and enumerate.

T279 proved a partition over `rules.py:NEW_ARMS`.  Those predicates carry exclusion
conjuncts (`_lock_held(s)` = present AND released==null; `not dead_pid_here(s)`;
`not started_over_24h(s)`) that make disjointness true BY CONSTRUCTION.  The question
this file asks is the one that matters to an agent reading STEP 0: are the arms
DISJOINT AS WRITTEN IN THE SHIPPED PROSE?

Transcription discipline is `rules.py`'s own, quoted from its docstring:
    "Where a sentence names no term for a dimension, the arm is silent on that
     dimension -- which is exactly how a rule set stops partitioning, so the
     transcription must not 'helpfully' add the missing conjunct."

Every arm below quotes the literal sentence from
`.claude/skills/softhouse-program/SKILL.md` STEP 0 and uses ONLY terms that sentence
names.  Two textual priority markers ARE honoured because they are in the text:
  arm 2 "...whatever every other signal says"   -> arm 2 outranks 3,4,5,6
  arm 4 "...(short of arm 3)"                   -> arm 4 excludes arm 3
Nothing else in the prose excludes anything.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "capture", "t279-lock-partition"))
import rules
from rules import DIMS

P = lambda s: s["lock"] == "present"
REL = lambda s: s["released"] == "set"
DEAD = lambda s: s["pid"] == "dead_here"
S24 = lambda s: s["started"] == "ge24"
S6 = lambda s: s["started"] in ("b6_24", "ge24")
T6L = lambda s: s["tip"] == "lt6"
T6G = lambda s: s["tip"] == "ge6"

PROSE_ARMS = [
    ("P0", "FREE", '0. **No `LOCK` file.** -> **free.** Write it.',
     lambda s: s["lock"] == "absent"),

    ("P1", "FREE", '1. `released_at` is **non-null** -> **free.** Take it.',
     lambda s: P(s) and REL(s)),

    ("P2", "TAKE", '2. The lock names a `pid` on **this** host and that pid is gone -> '
                   'DEAD HOLDER. Take over immediately, whatever every other signal says.',
     lambda s: P(s) and DEAD(s)),

    ("P3", "TAKE", '3. **CEILING.** `started_at` is over **24 h** old -> **stale.** '
                   'Take it over, however fresh `origin/main` looks.',
     lambda s: P(s) and S24(s)),

    # "(short of arm 3)" is the ONLY exclusion this sentence carries.  It says nothing
    # about released_at and nothing about the pid.
    ("P4", "HELD", "4. `origin/main`'s newest commit is under 6 h old -> **HELD, WHATEVER "
                   "`started_at` SAYS (short of arm 3).** Print it and exit.",
     lambda s: P(s) and T6L(s) and not S24(s)),

    ("P5", "TAKE", "5. `origin/main`'s newest commit is over 6 h old **and** `started_at` "
                   "is over 6 h old -> **stale.**",
     lambda s: P(s) and T6G(s) and S6(s)),
]

# arm 2's "whatever every other signal says" is a priority marker: where arm 2 fires it
# outranks arms 3,4,5,6.  It is NOT a marker against arm 1 (arm 1 is above it and says
# nothing about yielding).  Model it by suppressing 3/4/5 where 2 fires.
PRIORITY_SUPPRESSED_BY_P2 = {"P3", "P4", "P5"}


def matches(s, honour_arm2_priority=True):
    m = [(a, v) for a, v, _t, p in PROSE_ARMS if p(s)]
    if honour_arm2_priority and any(a == "P2" for a, _ in m):
        m = [(a, v) for a, v in m if a not in PRIORITY_SUPPRESSED_BY_P2]
    return m


def run(honour, label):
    zero, multi, conflict = [], [], []
    seen = set()
    for s in rules.states():
        key = rules.collapse(s)
        if key in seen:
            continue
        seen.add(key)
        m = matches(s, honour)
        if not m:
            zero.append(key)          # -> arm 6 (default) catches these; fine
        elif len(m) > 1:
            multi.append((key, m))
            if len({v for _a, v in m}) > 1:
                conflict.append((key, m))
    print(f"===== {label} =====")
    print(f"distinguishable states: {len(seen)}")
    print(f"A. matched ZERO decisive arms (-> arm 6 default, by design): {len(zero)}")
    print(f"B. matched MORE THAN ONE arm (order-dependent): {len(multi)}")
    for key, m in multi:
        vs = {v for _a, v in m}
        flag = "   <-- ARMS DISAGREE" if len(vs) > 1 else ""
        print("     " + " ".join(f"{d}={v}" for d, v in zip(DIMS, key))
              + "   " + ",".join(f"{a}={v}" for a, v in m) + flag)
    print(f"C. of those, OPPOSITE verdicts: {len(conflict)}")
    for key, m in conflict:
        print("     " + " ".join(f"{d}={v}" for d, v in zip(DIMS, key))
              + "   " + "  ".join(f"{a}={v}" for a, v in m))
    verdict = "PARTITION" if not multi else "NOT A PARTITION"
    print(f"VERDICT: {verdict}  (multi={len(multi)}, conflicting={len(conflict)})")
    print()
    return multi, conflict


if __name__ == "__main__":
    print("SHIPPED PROSE: .claude/skills/softhouse-program/SKILL.md STEP 0, arms 0-6.")
    print("SKILL.md's own claim under test:")
    print('  "Read every arm; the answer is the one that matches, and **exactly one')
    print('   always matches.** The arms are written to be **mutually exclusive**, not')
    print('   merely first-match-wins, so reading them out of order cannot change the')
    print('   answer."')
    print()
    run(True, "PROSE AS WRITTEN, honouring arm 2's textual priority marker")
    run(False, "PROSE AS WRITTEN, taking every arm as a bare predicate (no priority)")

    print("===== the state that breaks the claim, spelled out =====")
    s = dict(lock="present", released="set", started="lt6", tip="lt6", pid="absent")
    print(f"  {s}")
    for a, v, t, p in PROSE_ARMS:
        if p(s):
            print(f"    {a} -> {v}   {t}")
    print("  There is NO textual tiebreak between arm 1 and arm 4.")
    print("  Reading arm 1 first -> take the lock.  Reading arm 4 first -> exit.")
    print()
    print("  rules.py NEW_ARMS on the same state (the model T279 proved a partition over):")
    print("   ", rules.matches(rules.NEW_ARMS, s))
    print("  It answers uniquely ONLY because N4 carries `_lock_held(s)`, i.e. the")
    print("  conjunct `released_at is null`, which the prose sentence does not contain.")
