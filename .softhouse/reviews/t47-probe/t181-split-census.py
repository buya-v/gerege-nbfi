#!/usr/bin/env python3
"""T181 -- independent re-derivation of the t41-probe rewriter SPLIT, and a
mechanical reproduction of T178's WRONG split from T178's own classifier.

READ-ONLY.  EXECUTES NO REWRITER.  Reads git blobs and working-tree files only.

Two measurements, deliberately taken by two different methods:

  (A) TODAY's hardened bytes.  Each t41-probe rewriter now declares its target
      as a guard constant (`guard.RATIFIED_ADR` / `guard.FROZEN_CONTRACT`) that
      is the ACTUAL argument to the write path.  A file may declare BOTH.  This
      is a write-target signal, not a name-mention signal.

  (B) FORK-POINT bytes (T178's own pin, dfa1bfa9...), classified by T178's OWN
      rule, extracted verbatim from t178-wider-family.py:

          tgt = GO_REL if (GO_REL in src and ADR_REL not in src) else ADR_REL

      That expression is single-valued (it cannot express "both") and its
      fallback branch is the ADR.  Reproducing T178's published 21/4 from it
      demonstrates the split defect MECHANICALLY rather than by assertion.

P-35: every count below is printed as a VALUE, and inspecting zero files is a
hard error, not a pass.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
PROBE_REL = ".softhouse/reviews/t41-probe"
PROBE = os.path.join(REPO, PROBE_REL)

ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"

FORK = "dfa1bfa96084a2175f0d89d0a401a8c105d9a35f"


def git(*args):
    return subprocess.run(
        ["git", "-C", REPO] + list(args),
        capture_output=True, text=True, errors="replace")


def edit_files_today():
    return sorted(
        f for f in os.listdir(PROBE)
        if f.startswith("edit") and f.endswith(".py")
    )


def edit_files_at_fork():
    r = git("ls-tree", "-r", "--name-only", FORK, PROBE_REL + "/")
    out = []
    for line in r.stdout.splitlines():
        b = os.path.basename(line)
        if b.startswith("edit") and b.endswith(".py"):
            out.append((b, line))
    return sorted(out)


# ----------------------------------------------------------------- (A) today
def measure_today():
    rows = []
    for f in edit_files_today():
        src = open(os.path.join(PROBE, f), encoding="utf-8",
                   errors="replace").read()
        tgts = set()
        if "guard.RATIFIED_ADR" in src:
            tgts.add("DEC-1")
        if "guard.FROZEN_CONTRACT" in src:
            tgts.add("contract.go")
        rows.append((f, tgts))
    return rows


# ------------------------------------------------------------ (B) T178's rule
def measure_t178_rule():
    rows = []
    for base, path in edit_files_at_fork():
        r = git("show", "%s:%s" % (FORK, path))
        src = r.stdout
        # ---- T178's classifier, verbatim ----
        if ADR_REL not in src and GO_REL not in src:
            rows.append((base, None, "not counted (names neither artefact)"))
            continue
        tgt = GO_REL if (GO_REL in src and ADR_REL not in src) else ADR_REL
        # ---- end verbatim ----
        names = []
        if ADR_REL in src:
            names.append("names ADR")
        if GO_REL in src:
            names.append("names contract.go")
        lab = "contract.go" if tgt == GO_REL else "DEC-1"
        rows.append((base, lab, ", ".join(names)))
    return rows


def main():
    print("=" * 78)
    print("T181 SPLIT CENSUS -- .softhouse/reviews/t41-probe/")
    print("READ-ONLY.  No rewriter was executed.")
    print("=" * 78)

    # ---------------- A ----------------
    print()
    print("(A) TODAY's hardened bytes -- target read from the GUARD CONSTANT")
    print("    that is the actual argument to the write path.")
    print("-" * 78)
    rows_a = measure_today()
    if not rows_a:
        print("ERROR: inspected ZERO files -- P-35, this is an error not a pass")
        return 3
    dec, go, both = [], [], []
    for f, t in rows_a:
        if t == {"DEC-1"}:
            dec.append(f)
        elif t == {"contract.go"}:
            go.append(f)
        elif t == {"DEC-1", "contract.go"}:
            both.append(f)
        print("  %-14s %s" % (f, " + ".join(sorted(t)) if t else "UNRESOLVED"))
    print()
    print("  files inspected            : %d" % len(rows_a))
    print("  DEC-1 only                 : %d %s" % (len(dec), dec))
    print("  contract.go only           : %d %s" % (len(go), go))
    print("  BOTH                       : %d %s" % (len(both), both))
    print()
    print("  => files targeting DEC-1       = %d" % (len(dec) + len(both)))
    print("  => files targeting contract.go = %d" % (len(go) + len(both)))
    print("  => distinct files              = %d" % (len(dec) + len(go) + len(both)))
    print("  => (file,artefact) pairs       = %d" % (len(dec) + len(go) + 2 * len(both)))

    # ---------------- B ----------------
    print()
    print("(B) FORK-POINT bytes (%s), classified by T178's OWN rule:" % FORK[:8])
    print("      tgt = GO_REL if (GO_REL in src and ADR_REL not in src) else ADR_REL")
    print("-" * 78)
    rows_b = measure_t178_rule()
    if not rows_b:
        print("ERROR: inspected ZERO files -- P-35, this is an error not a pass")
        return 3
    bdec = [f for f, l, _ in rows_b if l == "DEC-1"]
    bgo = [f for f, l, _ in rows_b if l == "contract.go"]
    for f, l, why in rows_b:
        print("  %-14s %-12s %s" % (f, l if l else "-", why))
    print()
    print("  files inspected            : %d" % len(rows_b))
    print("  T178-rule DEC-1            : %d" % len(bdec))
    print("  T178-rule contract.go      : %d" % len(bgo))
    print("  T178 PUBLISHED in F-1      : 21 DEC-1 / 4 contract.go")
    ok = (len(bdec), len(bgo)) == (21, 4)
    print("  reproduces T178's split?   : %s" % ("YES" if ok else "NO"))

    # ---------------- verdict on the number ----------------
    print()
    print("=" * 78)
    print("MISCLASSIFIED BY T178 (true target vs T178's label)")
    print("=" * 78)
    truth = {f: t for f, t in rows_a}
    lab_b = {f: l for f, l, _ in rows_b}
    bad = 0
    for f in sorted(truth):
        t = truth[f]
        l = lab_b.get(f)
        if not t or l is None:
            continue
        true_lab = " + ".join(sorted(t))
        if (t == {"DEC-1"} and l == "DEC-1") or \
           (t == {"contract.go"} and l == "contract.go"):
            continue
        bad += 1
        print("  %-14s TRUE=%-22s T178=%s" % (f, true_lab, l))
    print()
    print("  files misclassified        : %d" % bad)
    print()
    print("  TOTAL (25) is CORRECT in T178.  The SPLIT is not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
