#!/usr/bin/env python3
"""T465 / C-T461-5 -- RE-MEASURE THE CHEAP-PATH COVERAGE CARDINALS.

    python3 50-coverage-remeasure.py [--ref origin/main] [--n 400]

WHAT IS BEING RE-DERIVED, and why the answer is a pair of figures rather than one. T453's gate
comment prices the `(h2)` exclusion at "27 entries" and its handoff prices the rejected
"exclude capture/** only" alternative at "~87 %". T461 measured 70 and 84.0 %. Neither figure
is inherited here: both are recomputed from the SAME window by the SAME selector, so the
DIFFERENCE between the two rules is a measurement and not a subtraction of two numbers taken
from two places (P-83 -- two independent movements of one pinned number reconcile by RUNNING).

THE SELECTOR, printed beside every figure:

    window   `git rev-list --no-merges --first-parent -n <N> <ref>`
    entries  `git show --name-status --format= -m --first-parent <sha>` for each commit
    STATE    the `state_path()` case from `<softhouse>/hooks/driver-push-gate.sh`, transcribed
             below as STATE_RULES and CHECKED against that file at run time -- if the shipped
             case block has changed shape, this instrument REFUSES rather than measuring a
             model of a rule that no longer exists.
    clause j deletions and renames take the FULL bar, so a commit carrying any status other
             than M or A is NOT cheap.

DECLARED LIMIT, and it is why the figures below are UPPER BOUNDS. Clause (k) -- "an addition is
admitted only if it cannot move the dead-path frontier" -- is decided at gate time by
`added-path-hazard.py` against the PUSHED TREE'S OWN PIN. It is not modelled here. A commit this
instrument calls cheap could still be sent to the full bar by (k). The limit applies EQUALLY to
every rule measured, which is what makes the COMPARISON between them sound even though each
absolute figure is a ceiling. Stated rather than buried: a figure whose limits are not printed
is a figure that will be quoted without them.

EXIT: 0 measured; 9x could not measure. Probe line `T465-COVERAGE:` on every path that reaches
figures, never on a refusal (P-84).
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

PROBE = "T465-COVERAGE:"
SH = "." + "softhouse"

# The shipped `state_path()` case arms, in order. TRANSCRIBED, and the transcription is CHECKED
# against the shipped file below -- a model that cannot notice its subject moved is worse than
# no model.
DENY_PREFIXES = [SH + "/vectors/", SH + "/guards/", SH + "/bin/", SH + "/toolchain/",
                 SH + "/capture/", SH + "/reviews/"]
DENY_EXACT = [SH + "/conformance.sh"]
ALLOW_EXACT = [SH + "/LOCK"]
ALLOW_SUFFIX = [".md", ".txt", ".json", ".log"]


def sh_out(*args):
    p = subprocess.run(list(args), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def state_path(path, exclude_reviews=True):
    """The shipped predicate. `exclude_reviews=False` is the REJECTED ALTERNATIVE: exclude
    `capture/**` but not `reviews/**`."""
    for pre in DENY_PREFIXES:
        if pre.endswith("reviews/") and not exclude_reviews:
            continue
        if path.startswith(pre):
            return False
    if path in DENY_EXACT:
        return False
    if "/req/" in path or path.startswith("req/"):
        return False
    if path in ALLOW_EXACT:
        return True
    if not path.startswith(SH + "/"):
        return False
    return any(path.endswith(s) for s in ALLOW_SUFFIX)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--n", type=int, default=400)
    args = ap.parse_args(argv)

    root = Path(__file__).resolve()
    while root != root.parent and not (root / ".git").exists():
        root = root.parent
    gate = root / (SH + "/hooks/driver-push-gate.sh")
    if not gate.is_file():
        print("ABORT(90): the gate is absent: %s" % gate, file=sys.stderr)
        return 90
    gsrc = gate.read_text(errors="replace")

    # --- the model is CHECKED against its subject -------------------------------------------
    missing = [p for p in DENY_PREFIXES if (p + "*") not in gsrc]
    if missing:
        print("ABORT(92): the shipped state_path() no longer denies %r. This instrument would be"
              % missing)
        print("measuring a rule that is not the rule. REFUSING rather than reporting a figure.")
        print("NO PROBE LINE IS PRINTED (P-84).", file=sys.stderr)
        return 92
    if (SH + "/LOCK) return 0") not in gsrc:
        print("ABORT(92): the shipped state_path() no longer admits the lock by name. REFUSING.")
        print("NO PROBE LINE IS PRINTED (P-84).", file=sys.stderr)
        return 92

    rc, out, err = sh_out("git", "-C", str(root), "rev-list", "--no-merges",
                          "--first-parent", "-n", str(args.n), args.ref)
    if rc != 0:
        print("ABORT(90): could not list %s: %s" % (args.ref, err.strip()), file=sys.stderr)
        return 90
    commits = [c for c in out.split() if c]
    if len(commits) < 2:
        print("ABORT(91): the window is %d commit(s). A coverage figure over that is not a"
              % len(commits))
        print("measurement (P-35). REFUSING.")
        print("NO PROBE LINE IS PRINTED (P-84).", file=sys.stderr)
        return 91

    stats = {"M": 0, "A": 0, "D": 0, "other": 0}
    seg = {"tasks.json": 0, "LOCK": 0, "RESUME.md": 0, "reviews/": 0,
           "program.json": 0, "capture/": 0}
    entries_total = 0
    cheap_chosen = 0      # (h2) as shipped: capture/ AND reviews/ excluded
    cheap_captureonly = 0  # the rejected alternative: capture/ excluded, reviews/ NOT

    for c in commits:
        rc, out, err = sh_out("git", "-C", str(root), "show", "--name-status",
                              "--format=", "-m", "--first-parent", c)
        if rc != 0:
            print("ABORT(90): git show failed on %s: %s" % (c, err.strip()), file=sys.stderr)
            return 90
        rows = []
        for ln in out.splitlines():
            if not ln.strip():
                continue
            parts = ln.split("\t")
            st = parts[0][:1]
            path = parts[-1]
            rows.append((st, path))
        if not rows:
            continue
        entries_total += len(rows)
        for st, path in rows:
            stats[st if st in ("M", "A", "D") else "other"] += 1
            for k in seg:
                if k.endswith("/"):
                    if path.startswith(SH + "/" + k):
                        seg[k] += 1
                elif path.endswith("/" + k) or path == SH + "/" + k:
                    seg[k] += 1
        statuses_ok = all(st in ("M", "A") for st, _ in rows)
        if statuses_ok and all(state_path(p, True) for _, p in rows):
            cheap_chosen += 1
        if statuses_ok and all(state_path(p, False) for _, p in rows):
            cheap_captureonly += 1

    n = len(commits)
    print("T465 -- CHEAP-PATH COVERAGE, RE-DERIVED")
    print("=" * 88)
    print("  window   : last %d non-merge first-parent commit(s) of %s" % (n, args.ref))
    print("  entries  : %d name-status entries; histogram M %d / A %d / D %d / other %d"
          % (entries_total, stats["M"], stats["A"], stats["D"], stats["other"]))
    print("  segments : " + "  ".join("%s=%d" % (k, v) for k, v in sorted(seg.items())))
    print("  MODEL CHECKED against the shipped state_path() before any figure was computed.")
    print("  LIMIT: clause (k) is NOT modelled, so both figures are UPPER BOUNDS. It applies")
    print("         equally to both rules, so their DIFFERENCE is the measurement that matters.")
    print()
    print("  RULE AS SHIPPED  (h2 excludes capture/ AND reviews/)  : %d/%d = %.1f%%"
          % (cheap_chosen, n, 100.0 * cheap_chosen / n))
    print("  REJECTED ALTERNATIVE (exclude capture/ ONLY)          : %d/%d = %.1f%%"
          % (cheap_captureonly, n, 100.0 * cheap_captureonly / n))
    print("  DIFFERENCE                                            : %d commit(s)"
          % (cheap_captureonly - cheap_chosen))
    print()
    print("  C-T461-5(b): the (h2) comment prices its exclusion at 'capture/' entries alone.")
    print("               MEASURED here: capture/=%d, reviews/=%d, TOTAL %d entries."
          % (seg["capture/"], seg["reviews/"], seg["capture/"] + seg["reviews/"]))
    print()
    print("%s window=%d entries=%d cheap_shipped=%d cheap_captureonly=%d "
          "captureEntries=%d reviewsEntries=%d"
          % (PROBE, n, entries_total, cheap_chosen, cheap_captureonly,
             seg["capture/"], seg["reviews/"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
