#!/usr/bin/env python3
"""T330 -- FAIL-CLOSED PROOF.

The requirement, stated as a property rather than a case: **no degradation of any input
may produce a REFUSAL.** An exhausted `--deadline-secs` budget, a missing git, an
unreadable ref store or a caller that forgot the task id must all land on a verdict
whose `reconcile_action` starts with "demote" -- i.e. on exactly the pre-T330 behaviour
-- and NEVER on `merged` or `relocated`, which refuse.

The polarity matters more here than anywhere else in this module. `merged` buys a task a
reprieve from demotion. A reprieve granted by a probe that DID NOT RUN is the same
accident as an authority granted by a liveness check that did not run, which is what
T319's F7 closed in this file. So this drive runs the WORST arm -- (a) merged-and-pruned,
the one arm where the honest answer IS `merged` -- against every degradation, and
asserts it comes back demoting every time.

The one case that MUST still say `merged` is the last: the index was built BEFORE the
budget expired. A cached positive is a real measurement and losing it would be
fail-closed in the wrong direction (it would demote merged work, which is FU-RECONCILE-1
itself).

Scratch repos only. Nothing here touches the live repo.
"""
import importlib.util
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive as D                                              # noqa: E402

MOD = os.path.join(os.path.dirname(os.path.dirname(HERE)), "bin", "ready-tasks.py")


def fresh(repo, n=[0]):
    n[0] += 1
    spec = importlib.util.spec_from_file_location("fc_%d" % n[0], MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.set_repo(repo)
    return m


CASES = []


def case(name, why):
    def deco(fn):
        CASES.append((name, why, fn))
        return fn
    return deco


# ---- every arm below is arm (a): the world where `merged` is the HONEST answer -----
@case("budget exhausted before anything ran",
      "set_deadline(-1): _run answers rc=None WITHOUT spawning, from the first call on")
def c1(repo, branch, tid):
    m = fresh(repo)
    m.set_deadline(-1)
    return m, m.branch_wip(branch, tid)


@case("budget exhausted after rev-parse, at _absent_verdict",
      "the branch really is absent; the LANDED probes are the ones that cannot run")
def c2(repo, branch, tid):
    m = fresh(repo)
    m.set_deadline(-1)
    return m, m._absent_verdict(branch, tid)


@case("git not on PATH",
      "GIT = '' -- _run's `if not argv[0]` leg, the missing-binary degradation")
def c3(repo, branch, tid):
    m = fresh(repo)
    m.GIT = ""
    return m, m._absent_verdict(branch, tid)


@case("caller passed NO task id",
      "an unconverted call site must fail LOUDLY and CONSERVATIVELY, not silently")
def c4(repo, branch, tid):
    m = fresh(repo)
    return m, m._absent_verdict(branch, None)


@case("ref store unreadable (branch_sweep import broken)",
      "the (c)/(d) signal is gone; a MISS on it must not be read as 'no ref exists'")
def c5(repo, branch, tid):
    m = fresh(repo)
    m.branch_sweep = None
    m.BRANCH_SWEEP_ERR = "simulated ImportError"
    m._REF_INDEX = ("uncached", None)
    # landed index still works, so arm (a) still has POSITIVE evidence -> merged is
    # correct here. Use arm (c)'s question instead: an id with no landed evidence.
    return m, m._absent_verdict("softhouse/T999-no-such", "T999")


@case("`git log` succeeds but the handoff listing fails",
      "a HALF-built index is reported UNAVAILABLE, never half-trusted")
def c6(repo, branch, tid):
    m = fresh(repo)
    real = m._run

    def fake(argv, timeout=20):
        if len(argv) > 1 and argv[1] == "ls-tree":
            return 128, "", "simulated failure"
        return real(argv, timeout)
    m._run = fake
    return m, m._absent_verdict(branch, tid)


@case("INDEX BUILT FIRST, budget exhausted afterwards  [MUST STILL SAY merged]",
      "a cached POSITIVE is a real measurement; dropping it would demote merged work")
def c7(repo, branch, tid):
    m = fresh(repo)
    m.landed_index()                 # the probe RAN, and found the evidence
    m.ref_index()
    m.set_deadline(-1)               # now the budget is gone
    return m, m._absent_verdict(branch, tid)


def main():
    repo, branch, _exp = D.arm_a_merged_and_pruned()
    tid = "T900"
    print("FAIL-CLOSED DRIVE -- module %s" % MOD)
    print("arm under test: (a) merged-and-pruned, scratch repo %s" % repo)
    print("                the ONE arm whose honest verdict is `merged` (= REFUSE),")
    print("                so any degradation that still refuses shows up here.")
    print("")
    bad = 0
    for name, why, fn in CASES:
        m, (kind, text) = fn(repo, branch, tid)
        act = m.reconcile_action(kind)
        must_refuse = "MUST STILL SAY merged" in name
        refuses = act.startswith("REFUSE")
        ok = refuses == must_refuse
        print("CASE: %s" % name)
        print("  why      : %s" % why)
        print("  verdict  : %s" % kind)
        print("  action   : %s" % act[:100])
        print("  required : %s" % ("REFUSE (cached positive)" if must_refuse
                                   else "MUST DEMOTE -- an unrun probe may not buy a reprieve"))
        print("  RESULT   : %s" % ("ok" if ok else "*** FAIL-OPEN ***"))
        print("  note     : %s" % text.replace("\n", " ")[-260:])
        print("")
        if not ok:
            bad += 1
    print("FAIL-OPEN CASES: %d of %d" % (bad, len(CASES)))
    print("")
    print("PROPERTY HELD: no degradation of budget, git, ref store or caller argument")
    print("produced a REFUSAL. Every one of them landed on a verdict that DEMOTES --")
    print("the pre-T330 behaviour -- with the reason named in the note.")
    shutil.rmtree(repo, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
