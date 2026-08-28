#!/usr/bin/env python3
"""T145 -- CONFIRMATION LEG for the 13 DIFFERS, run SERIALLY with a determinism control.

The wide sweep ran 6-way parallel and several of these scripts write into shared capture
directories, so a raw A!=B there is NOT yet attributable to parse_float. This leg re-runs
each candidate THREE times, serially:

    A   clean
    A'  clean again          <-- the DETERMINISM CONTROL
    B   with parse_float=Decimal injected by PYTHONPATH sitecustomize

and attributes the difference only when   A == A'   AND   A != B.
Without the A' control every temp-directory name and every timeout would be reported as a
money finding -- which is the P-72 failure ("the control failed, so no negative below is
trustworthy") that this program has already paid for once.

VERDICTS
  NONDETERMINISTIC       A != A'.  The wide sweep's diff is an artefact. NOT attributable.
  ATTRIBUTABLE           A == A' and A != B.  parse_float genuinely moves this output.
  IDENTICAL-ON-RERUN     A == A' == B.  the wide sweep's diff was a parallelism race.
"""
import os
import subprocess
import sys

TIMEOUT = int(os.environ.get("T145_TIMEOUT", "120"))

CANDIDATES = [
    ".softhouse/capture/charges/bin/t48-analyse.py",
    ".softhouse/capture/charges/bin/t51-analyse2.py",
    ".softhouse/capture/pathb/t22-probe/mkcalc.py",
    ".softhouse/capture/pathb/t22-probe/mkreq.py",
    ".softhouse/capture/t290-review-t271/guard_rvpa_floor_t290.py",
    ".softhouse/capture/t290-review-t271/probe_t286_rule_t290.py",
    ".softhouse/capture/t290-review-t271/prove_repair_inert.py",
    ".softhouse/capture/t290-review-t271/red/drive-red-t290.py",
    ".softhouse/capture/t330-reconcile-merged-work/e2e.py",
    ".softhouse/reviews/t262-verdict-predicate/attack_rvpa_t262.py",
    ".softhouse/reviews/t262-verdict-predicate/pin_test_t262.py",
    ".softhouse/reviews/t45-probe/t45_extra.py",
    ".softhouse/reviews/t47-probe/t47_extra.py",
]


def run(rel, root, env):
    cwd = os.path.dirname(os.path.join(root, rel)) or root
    try:
        p = subprocess.run([sys.executable, os.path.basename(rel)], cwd=cwd, env=env,
                           capture_output=True, text=True, timeout=TIMEOUT, errors="replace")
        return (p.returncode, p.stdout, p.stderr)
    except subprocess.TimeoutExpired:
        return ("TIMEOUT", "", "")


def restore(root):
    out = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                         capture_output=True, text=True).stdout.strip().split("\n")
    touched = []
    for line in out:
        if not line.strip() or "t145-analysis-float" in line:
            continue
        st, path = line[:2], line[3:].strip()
        touched.append(line)
        if st.strip() == "??":
            subprocess.run(["rm", "-rf", os.path.join(root, path)])
        else:
            subprocess.run(["git", "checkout", "--", path], cwd=root, capture_output=True)
    return touched


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    here = os.path.dirname(os.path.abspath(__file__))
    env_a = dict(os.environ); env_a["PYTHONDONTWRITEBYTECODE"] = "1"
    env_b = dict(env_a); env_b["PYTHONPATH"] = here + os.pathsep + env_a.get("PYTHONPATH", "")

    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True).stdout.strip()
    print("SELECTOR: the 13 files the wide sweep reported as DIFFERS, re-run SERIALLY")
    print("          three times each (A, A', B) with A' as the determinism control.")
    print("REV: %s   TIMEOUT: %ds   serial, no thread pool" % (rev, TIMEOUT))
    print()

    tally = {"NONDETERMINISTIC": [], "ATTRIBUTABLE": [], "IDENTICAL-ON-RERUN": []}
    for rel in CANDIDATES:
        A = run(rel, root, env_a); t1 = restore(root)
        A2 = run(rel, root, env_a); t2 = restore(root)
        B = run(rel, root, env_b); t3 = restore(root)
        if A != A2:
            v = "NONDETERMINISTIC"
        elif A == B:
            v = "IDENTICAL-ON-RERUN"
        else:
            v = "ATTRIBUTABLE"
        tally[v].append(rel)
        print("%-20s %s" % (v, rel))
        print("      exit  A=%r  A'=%r  B=%r" % (A[0], A2[0], B[0]))
        print("      tree writes restored: A=%d A'=%d B=%d" % (len(t1), len(t2), len(t3)))
        if v == "ATTRIBUTABLE":
            la, lb = A[1].split("\n"), B[1].split("\n")
            n = 0
            for i in range(max(len(la), len(lb))):
                x = la[i] if i < len(la) else "<EOF>"
                y = lb[i] if i < len(lb) else "<EOF>"
                if x != y:
                    print("      L%-4d A: %s" % (i + 1, x[:150]))
                    print("           B: %s" % y[:150])
                    n += 1
                    if n >= 6:
                        print("      ... further differences suppressed")
                        break
            if A[2] != B[2]:
                ea = [l for l in A[2].strip().split("\n") if l.strip()]
                eb = [l for l in B[2].strip().split("\n") if l.strip()]
                print("      stderr A: %s" % (ea[-1][:150] if ea else "<empty>"))
                print("      stderr B: %s" % (eb[-1][:150] if eb else "<empty>"))
        if v == "NONDETERMINISTIC":
            la, la2 = A[1].split("\n"), A2[1].split("\n")
            for i in range(max(len(la), len(la2))):
                x = la[i] if i < len(la) else "<EOF>"
                y = la2[i] if i < len(la2) else "<EOF>"
                if x != y:
                    print("      A  vs A' first divergence, L%d:" % (i + 1))
                    print("           A : %s" % x[:150])
                    print("           A': %s" % y[:150])
                    break
        print()

    print("==== CONFIRMATION RESULT ====")
    for k in ("ATTRIBUTABLE", "NONDETERMINISTIC", "IDENTICAL-ON-RERUN"):
        print("%-20s : %d" % (k, len(tally[k])))
        for r in tally[k]:
            print("      %s" % r)
    left = restore(root)
    print()
    print("FINAL TREE CHECK: %d entries outside this task's capture dir (0 == clean)" % len(left))
    return 0


sys.exit(main())
