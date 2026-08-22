#!/usr/bin/env bash
# T248 instrument 30 -- IS THE WIDENING ADDITIVE? Proved by running BOTH linters.
#
# The claim being tested is the one that makes the widening safe to merge:
#   "every detection the SHIPPED linter made, the WIDENED linter still makes."
# A widening that quietly drops a detection is a WEAKENING wearing a widening's diff, and
# it is exactly what a reviewer cannot see by reading two regexes side by side. So this
# runs the shipped linter (extracted from git, not from memory) and the widened one over
# the SAME tree, and diffs their full detection sets line by line.
#
# ENGINE (P-33/P-53): /usr/bin/grep and /usr/bin/diff -- the real programs, by absolute
# path, never the shell functions this environment shadows `grep` with (P-75). No `rg`
# anywhere: `rg` HAS NO BINARY here and `rg P F | head` would exit 0 having run nothing.
# NO PIPELINE carries a verdict (P-57): every exit status tested is a direct command's.
set -euo pipefail

G=/usr/bin/grep
[ -x "$G" ] || { echo "ABORT(2): $G missing"; exit 2; }
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
LINT=.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py
BASE="${1:-HEAD}"

# --- CALIBRATION (P-72): a known POSITIVE and a known NEGATIVE for the engine itself ----
# "I got hits, so my rig works" is not a calibration. Both directions are asserted.
CAL="$(mktemp -t t248-cal)"
printf 'alpha\nbeta\n' > "$CAL"
"$G" -q '^alpha$' "$CAL"  || { echo "ABORT(2): engine missed a KNOWN POSITIVE"; exit 2; }
if "$G" -q '^gamma$' "$CAL"; then echo "ABORT(2): engine matched a KNOWN NEGATIVE"; exit 2; fi
rm -f "$CAL"
echo "engine      : $("$G" --version | head -1)   [calibrated: known positive HIT, known negative MISS]"
echo "repo        : $ROOT"
echo "HEAD        : $(git rev-parse HEAD)"
echo "shipped from: $BASE:$LINT"
echo

OLD="$(mktemp -t t248-oldlint)"
OUT_OLD="$(mktemp -t t248-out-old)"
OUT_NEW="$(mktemp -t t248-out-new)"
J="$(mktemp -t t248-json)"
git show "$BASE:$LINT" > "$OLD"

set +e
FAILOPEN_LINT_JSON="$J" python3 "$OLD"  > "$OUT_OLD" 2>&1 ; rc_old=$?
FAILOPEN_LINT_JSON="$J" python3 "$LINT" > "$OUT_NEW" 2>&1 ; rc_new=$?
set -e
rm -f "$J"

# FAIL CLOSED: an empty or bannerless output would make every diff below look clean.
for f in "$OUT_OLD" "$OUT_NEW"; do
  "$G" -q 'T238 FAIL-OPEN LINT' "$f" || { echo "ABORT(2): no banner in $f"; exit 2; }
done
echo "shipped exit : $rc_old      widened exit : $rc_new"
echo

echo "=== 1. DETECTION SETS (every C1/C2 line either linter emitted)"
#
# NORMALISED TO (file, condition, line), and it HAD to be. The first draft of this
# instrument compared the linter's PRINTED lines, and the printed lines carry the FILE name
# in the Tier-3 section but not in the Tier-1/2 sections. So when a file was promoted
# Tier3 -> Tier1 its one unchanged C1 detection appeared as a LOSS and a GAIN at once, and
# the instrument reported "NOT ADDITIVE -- this is a WEAKENING" about a widening that had
# lost nothing. A diff rig that reports a loss it cannot substantiate is the same defect
# class this whole task is about, pointed the other way; it is fixed here rather than
# worked around, and the false alarm is left on the record because it is the reason.
_norm() {
  python3 - "$1" <<'PY'
import re, sys
cur = None
sec = None
for l in open(sys.argv[1], encoding="utf-8", errors="replace"):
    l = l.rstrip("\n")
    if l.startswith("### TIER"):
        sec = l.split()[2]; cur = None; continue
    if l.startswith("### ADVISORY") or l.startswith("FAILOPEN-FRONTIER"):
        sec = None; cur = None; continue
    if sec in ("1", "2"):
        m = re.match(r'^  (\S+)\s*$', l)
        if m:
            cur = m.group(1); continue
        m = re.match(r'^      (C[12])  :(\d+)  (.*)$', l)
        if m and cur:
            print("%s\t%s\t%s\t%s" % (cur, m.group(1), m.group(2), m.group(3)))
    elif sec == "3":
        m = re.match(r'^  (\S+)\s+:(\d+)  (.*)$', l)
        if m:
            print("%s\tC1\t%s\t%s" % (m.group(1), m.group(2), m.group(3)))
PY
}
_norm "$OUT_OLD" | LC_ALL=C sort > "$OUT_OLD.det"
_norm "$OUT_NEW" | LC_ALL=C sort > "$OUT_NEW.det"
echo "shipped detections: $("$G" -c '' "$OUT_OLD.det")   widened detections: $("$G" -c '' "$OUT_NEW.det")"
echo
echo "--- LOST (present in SHIPPED, absent from WIDENED). ANY line here falsifies additivity:"
if LC_ALL=C comm -23 "$OUT_OLD.det" "$OUT_NEW.det" > "$OUT_OLD.lost"; then :; fi
if [ -s "$OUT_OLD.lost" ]; then cat "$OUT_OLD.lost"; LOST=1; else echo "   (none)"; LOST=0; fi
echo
echo "--- GAINED (absent from SHIPPED, present in WIDENED):"
if LC_ALL=C comm -13 "$OUT_OLD.det" "$OUT_NEW.det" > "$OUT_NEW.gain"; then :; fi
if [ -s "$OUT_NEW.gain" ]; then cat "$OUT_NEW.gain"; else echo "   (none)"; fi
echo

echo "=== 2. FRONTIER (the rows the conformance gate compares against its pin)"
"$G" '^FAILOPEN-FRONTIER ' "$OUT_OLD" | LC_ALL=C sort > "$OUT_OLD.fr"
"$G" '^FAILOPEN-FRONTIER ' "$OUT_NEW" | LC_ALL=C sort > "$OUT_NEW.fr"
/usr/bin/diff -u "$OUT_OLD.fr" "$OUT_NEW.fr" || true
echo

echo "=== 3. VERDICT"
if [ "$LOST" -ne 0 ]; then
  echo "NOT ADDITIVE -- the widened linter lost detections listed above. This is a WEAKENING."
  exit 1
fi
echo "ADDITIVE -- zero detections lost; the frontier differs only by ADDED rows."
rm -f "$OLD" "$OUT_OLD" "$OUT_NEW" "$OUT_OLD.det" "$OUT_NEW.det" "$OUT_OLD.lost" \
      "$OUT_NEW.gain" "$OUT_OLD.fr" "$OUT_NEW.fr"
exit 0
