#!/usr/bin/env bash
# drive-sweep-failclosed.sh -- T371's RED DRIVE of the F2 repair to casualty-sweep.sh.
#
#   bash .softhouse/capture/t371-t367-conditions/instruments/drive-sweep-failclosed.sh [REF]
#
# REF defaults to HEAD. The instrument under test is EXTRACTED FROM GIT on every run (P-22), so
# this drive cannot silently grade a since-edited working copy. The BEFORE version is extracted
# from `main`, which is where T367 found the defect and where it still stands.
#
# WHAT IS BEING DRIVEN, in both directions, because a guard nobody has watched fail enforces
# nothing:
#
#   A  BEFORE (main)   malformed selector  vs  genuinely-empty selector  -> IDENTICAL output.
#                      This is the defect: a negative the instrument never measured.
#   B  AFTER  (REF)    malformed selector                -> "SELECTOR DID NOT RUN", exit 4
#   C  AFTER  (REF)    genuinely-empty selector          -> "MEASURED ZERO",         exit 0
#   D  raw `git grep` exit statuses for the three shapes, so the claim in A/B/C is checkable
#      against the engine itself and not only against my script.
#   E  AFTER  positive calibration made to miss        -> exit 3, and NOTHING is printed
#   F  AFTER  anti-calibration made to match           -> exit 3, and NOTHING is printed
#   G  AFTER  run outside any git work tree            -> exit 2 (corpus unusable, not "clean")
#   H  AFTER  unmodified, in the repo                  -> exit 0, and S12 SEES the F3 casualty
#
# It writes only under a mktemp directory. It reaches no network and no database.
set -uo pipefail
REF="${1:-HEAD}"
ROOT=$(git rev-parse --show-toplevel) || exit 2
cd "$ROOT" || exit 2
SUT='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
W=$(mktemp -d "${TMPDIR:-/tmp}/t371-drive-XXXXXX") || exit 2
trap 'rm -rf "$W"' EXIT

# A selector that is a MEASURED zero: composed at run time so it cannot exist in the corpus,
# and so that committing this file cannot turn it into a hit.
ABSENT="zzq-t371-drive-absent-$$-${RANDOM}-$(date -u +%s)"
# A selector that CANNOT RUN: an unterminated bracket expression is an invalid ERE.
BAD='['

echo "=================================================================="
echo "T371 RED DRIVE -- casualty-sweep.sh fail-open (T367 F2)"
echo "repo   : $(git rev-parse --short HEAD)   ref under test: $REF ($(git rev-parse --short "$REF"))"
echo "date   : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "workdir: $W"
echo "=================================================================="

git show "main:$SUT"  > "$W/BEFORE.sh" 2>/dev/null || { echo "cannot extract BEFORE from main"; exit 2; }
git show "$REF:$SUT"  > "$W/AFTER.sh"  2>/dev/null || { echo "cannot extract AFTER from $REF"; exit 2; }
printf '\nBEFORE sha256: %s\nAFTER  sha256: %s\n' \
  "$(shasum -a 256 "$W/BEFORE.sh" | awk '{print $1}')" \
  "$(shasum -a 256 "$W/AFTER.sh"  | awk '{print $1}')"
printf 'BEFORE reads git grep exit status? %s\n' \
  "$(grep -c 'rc=\$?' "$W/BEFORE.sh" | awk '{print ($1>0)?"yes":"NO -- this is the defect"}')"
printf 'AFTER  reads git grep exit status? %s\n' \
  "$(grep -c 'rc=\$?' "$W/AFTER.sh"  | awk '{print ($1>0)?"yes":"no"}')"

# mkvariant <src> <selector-args-literal> <dst>
# Injects ONE test selector ahead of the shipped ones and comments the shipped ones out, so the
# drive reads one selector's behaviour and not 11-16 selectors' noise.
mkvariant() {
  awk -v s="$2" '/^# ---- S1\.\.S3/ { print "sel \"TEST-SELECTOR\" " s } { print }' "$1" \
    | sed 's/^sel "S/#sel "S/' > "$3"
}

run() { # run <label> <script> [cwd]
  local label="$1" script="$2" cwd="${3:-$ROOT}" out rc
  out=$( cd "$cwd" && bash "$script" 2>&1 ); rc=$?
  printf '\n---------- %s\n' "$label"
  printf '%s\n' "$out" | grep -E 'TEST-SELECTOR|DID NOT RUN|MEASURED ZERO|hits total|SWEEP ABORT|CALIBRATE|SWEEP-RESULT' \
    | sed 's/^/    /' | head -20
  printf '    EXIT=%s\n' "$rc"
  printf '%s\n' "$rc" > "$W/rc-$label"
}

# ---------------------------------------------------------------- A: the defect, BEFORE
mkvariant "$W/BEFORE.sh" "-n -F '$ABSENT'" "$W/before-empty.sh"
mkvariant "$W/BEFORE.sh" "-n -E '$BAD'"    "$W/before-bad.sh"
echo
echo "########## A  BEFORE (main) -- the two facts that must differ, and do not"
run "A1-before-EMPTY-result" "$W/before-empty.sh"
run "A2-before-MALFORMED"    "$W/before-bad.sh"

# ---------------------------------------------------------------- B/C: the repair, AFTER
mkvariant "$W/AFTER.sh" "-n -F '$ABSENT'" "$W/after-empty.sh"
mkvariant "$W/AFTER.sh" "-n -E '$BAD'"    "$W/after-bad.sh"
echo
echo "########## B/C  AFTER ($REF) -- the same two facts"
run "C-after-EMPTY-result" "$W/after-empty.sh"
run "B-after-MALFORMED"    "$W/after-bad.sh"

# ---------------------------------------------------------------- D: the engine itself
echo
echo "########## D  raw git grep exit statuses, so A/B/C is checkable against the engine"
git grep -n -F "$ABSENT" -- .softhouse/ >/dev/null 2>&1; printf '    git grep EMPTY-RESULT rc = %s\n' "$?"
git grep -n -E "$BAD"    -- .softhouse/ >/dev/null 2>&1; printf '    git grep MALFORMED    rc = %s\n' "$?"
git grep -n -F 'CASUALTY SWEEP for the T352' -- .softhouse/ >/dev/null 2>&1; printf '    git grep HITTING      rc = %s\n' "$?"
printf "    'git grep' occurrences in BEFORE: %s ; exit statuses inspected: %s\n" \
  "$(grep -c 'git grep' "$W/BEFORE.sh")" "$(grep -c 'rc=\$?' "$W/BEFORE.sh")"
printf "    'git grep' occurrences in AFTER : %s ; exit statuses inspected: %s\n" \
  "$(grep -c 'git grep' "$W/AFTER.sh")"  "$(grep -c 'rc=\$?' "$W/AFTER.sh")"

# ---------------------------------------------------------------- E/F: calibration
echo
echo "########## E/F  calibration -- prove the engine works BEFORE any zero is interpretable"
sed "s|^CALIB_POS_STR=.*|CALIB_POS_STR='zzq-t371-positive-calibration-broken-$$-$RANDOM'|" \
  "$W/AFTER.sh" > "$W/after-calibpos-broken.sh"
run "E-positive-calibration-MISSES" "$W/after-calibpos-broken.sh"
sed "s|^CALIB_NEG_STR=.*|CALIB_NEG_STR='CASUALTY SWEEP for the T352'|" \
  "$W/AFTER.sh" > "$W/after-calibneg-broken.sh"
run "F-anti-calibration-MATCHES" "$W/after-calibneg-broken.sh"

# ---------------------------------------------------------------- G: no corpus
echo
echo "########## G  corpus unusable -- outside any git work tree"
mkdir -p "$W/nogit"
run "G-no-git-work-tree" "$W/AFTER.sh" "$W/nogit"

# ---------------------------------------------------------------- H: green, and it SEES F3
echo
echo "########## H  AFTER, unmodified -- green, and S12 now sees the casualty T363's 11 missed"
h_out=$(bash "$W/AFTER.sh" 2>&1); h_rc=$?
printf '    EXIT=%s\n' "$h_rc"
printf '%s\n' "$h_out" | grep -E 'SWEEP-RESULT|CALIBRATE' | sed 's/^/    /'
printf '    S12/S13 hits on the F3 site (reference-oracle.md, the PROCESSED/ERROR split):\n'
printf '%s\n' "$h_out" | grep -n 'reference-oracle.md' | grep -E 'PROCESSED|split is' | sed 's/^/      /'
printf '    Same site under the BEFORE selectors S1..S11 only:\n'
b_out=$(bash "$W/BEFORE.sh" 2>&1)
printf '%s\n' "$b_out" | grep -c 'reference-oracle.md.*PROCESSED' | sed 's/^/      hits: /'

echo
echo "=================================================================="
echo "SUMMARY"
printf '  A1 before EMPTY      exit %s\n' "$(cat "$W/rc-A1-before-EMPTY-result")"
printf '  A2 before MALFORMED  exit %s   <- must be INDISTINGUISHABLE from A1 above. That is F2.\n' "$(cat "$W/rc-A2-before-MALFORMED")"
printf '  C  after  EMPTY      exit %s   <- a MEASURED zero\n' "$(cat "$W/rc-C-after-EMPTY-result")"
printf '  B  after  MALFORMED  exit %s   <- DID NOT RUN, and says so\n' "$(cat "$W/rc-B-after-MALFORMED")"
printf '  E  calibration+ red  exit %s\n' "$(cat "$W/rc-E-positive-calibration-MISSES")"
printf '  F  anti-calibration  exit %s\n' "$(cat "$W/rc-F-anti-calibration-MATCHES")"
printf '  G  no corpus         exit %s\n' "$(cat "$W/rc-G-no-git-work-tree")"
printf '  H  green             exit %s\n' "$h_rc"
echo "=================================================================="
