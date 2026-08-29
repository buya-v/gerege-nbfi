#!/usr/bin/env python3
"""T471 -- an INDEPENDENT re-derivation of C-T461-5's four cardinals.

T465 reports, over a 400-commit window:
    entries=630  cheap_shipped=335 (83.8%)  cheap_captureonly=336 (84.0%)
    captureEntries=27  reviewsEntries=43   (27+43 = 70)

This does not read T465's instrument. It reads the SHIPPED `state_path()` case block out of the
gate file at the rev under test, PARSES the arms out of it rather than transcribing them, and
applies them with `fnmatch`, which is the closest available model of bash `case` globbing (`*`
crosses `/` in both). Parsing rather than transcribing is the point: a transcription can agree
with a stale copy of the rule; a parse cannot.

DECLARED LIMITS, printed with the figures:
  * clause (k) -- "an addition is admitted only if it cannot move the dead-path frontier" -- is
    decided at gate time against the pushed tree's own pin and is NOT modelled. Every figure
    here is therefore an UPPER BOUND, equally for both rules compared.
  * `fnmatch` is not bash `case`. The two agree on `*`, `?` and `[...]`; they differ on
    locale-collating classes, which none of these arms use.
  * the WINDOW MOVES. A figure over "the last 400 commits" is a fact about a tip, so the tip is
    printed beside it.

NO REAL REPO PATH IS SPELT HERE (P-103): assembled from $S.
EXIT 0 measured; 9x could not measure. Probe: T471-COVERAGE:
"""
import argparse
import fnmatch
import re
import subprocess
import sys

PROBE = "T471-COVERAGE:"
S = "." + "softhouse"


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if p.returncode != 0:
        print("ABORT(90): git %s -> %d: %s" % (" ".join(args), p.returncode, p.stderr.strip()),
              file=sys.stderr)
        raise SystemExit(90)
    return p.stdout


def parse_state_path(src):
    """Pull the arms out of the shipped `state_path()` case block. Returns an ordered list of
    (patterns, verdict) where verdict is True for `return 0` (a STATE path) and False otherwise."""
    m = re.search(r"^state_path\(\) \{(.*?)^\}", src, re.S | re.M)
    if not m:
        print("ABORT(91): no state_path() in the gate. REFUSING to measure a rule I cannot read.",
              file=sys.stderr)
        raise SystemExit(91)
    body = m.group(1)
    c = re.search(r"case \"\$1\" in(.*?)esac", body, re.S)
    if not c:
        print("ABORT(91): state_path() has no `case \"$1\" in` block. REFUSING.", file=sys.stderr)
        raise SystemExit(91)
    arms = []
    for line in c.group(1).split("\n"):
        line = line.strip()
        mm = re.match(r"^(.*?)\)\s*return\s+([01])\s*;;", line)
        if not mm:
            continue
        pats = [p.strip() for p in mm.group(1).split("|") if p.strip()]
        arms.append((pats, mm.group(2) == "0"))
    if len(arms) < 4:
        print("ABORT(91): parsed only %d arms out of state_path(). The block's shape changed;"
              " REFUSING rather than measuring a model of a rule that no longer exists." % len(arms),
              file=sys.stderr)
        raise SystemExit(91)
    return arms


def make_pred(arms, drop_reviews_arm=False):
    """drop_reviews_arm models the REJECTED alternative `exclude capture/** only`: the
    `<S>/reviews/*` pattern is removed from whichever deny arm carries it."""
    use = []
    for pats, verdict in arms:
        p2 = [p for p in pats if not (drop_reviews_arm and p == S + "/reviews/*")]
        if p2:
            use.append((p2, verdict))

    def pred(path):
        for pats, verdict in use:
            for p in pats:
                if fnmatch.fnmatchcase(path, p):
                    return verdict
        return False
    return pred


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--gate-rev", required=True, help="rev whose gate file supplies the rule")
    ap.add_argument("--ref", required=True)
    ap.add_argument("--n", type=int, default=400)
    a = ap.parse_args()

    src = git(a.repo, "show", "%s:%s/hooks/driver-push-gate.sh" % (a.gate_rev, S))
    arms = parse_state_path(src)
    shipped = make_pred(arms, drop_reviews_arm=False)
    captureonly = make_pred(arms, drop_reviews_arm=True)

    tip = git(a.repo, "rev-parse", a.ref).strip()
    shas = [x for x in git(a.repo, "rev-list", "--no-merges", "--first-parent",
                           "-n", str(a.n), a.ref).split() if x]

    entries = 0
    cheap_s = cheap_c = 0
    cap_entries = rev_entries = lock_entries = 0
    nonMA = 0
    for sha in shas:
        out = git(a.repo, "show", "--name-status", "--format=", "-m", "--first-parent", sha)
        rows = []
        for line in out.split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            rows.append((parts[0], parts[-1]))
        entries += len(rows)
        ok_s = ok_c = bool(rows)
        for st, path in rows:
            if path.startswith(S + "/capture/"):
                cap_entries += 1
            if path.startswith(S + "/reviews/"):
                rev_entries += 1
            if path == S + "/LOCK":
                lock_entries += 1
            if st[:1] not in ("M", "A"):
                nonMA += 1
                ok_s = ok_c = False
                continue
            if not shipped(path):
                ok_s = False
            if not captureonly(path):
                ok_c = False
        cheap_s += 1 if ok_s else 0
        cheap_c += 1 if ok_c else 0

    print("ARMS PARSED OUT OF THE SHIPPED state_path():")
    for pats, verdict in arms:
        print("    %-70s -> %s" % ("|".join(pats), "STATE" if verdict else "not-state"))
    print()
    print("window ref   : %s  tip=%s" % (a.ref, tip))
    print("window size  : %d commit(s) requested, %d resolved" % (a.n, len(shas)))
    print("gate rule    : read out of %s" % a.gate_rev)
    print("LIMIT        : clause (k) is NOT modelled -- both coverage figures are CEILINGS.")
    print()
    print("  entries (name-status rows, all commits)   = %d" % entries)
    print("  entries under capture/                    = %d" % cap_entries)
    print("  entries under reviews/                    = %d" % rev_entries)
    print("  entries that are the fire lock            = %d" % lock_entries)
    print("  entries whose status is neither M nor A   = %d" % nonMA)
    print("  commits CHEAP under the rule AS SHIPPED   = %d / %d = %.1f%%"
          % (cheap_s, len(shas), 100.0 * cheap_s / max(1, len(shas))))
    print("  commits CHEAP excluding capture/** ONLY   = %d / %d = %.1f%%"
          % (cheap_c, len(shas), 100.0 * cheap_c / max(1, len(shas))))
    print("  difference between the two rules          = %d commit(s)" % (cheap_c - cheap_s))
    print()
    print("%s ref=%s tip=%s window=%d entries=%d cheapShipped=%d cheapCaptureOnly=%d "
          "captureEntries=%d reviewsEntries=%d capturePlusReviews=%d lockEntries=%d"
          % (PROBE, a.ref, tip[:8], len(shas), entries, cheap_s, cheap_c,
             cap_entries, rev_entries, cap_entries + rev_entries, lock_entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
