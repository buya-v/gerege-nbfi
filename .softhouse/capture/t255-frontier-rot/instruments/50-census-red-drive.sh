#!/bin/bash
# T258 RED DRIVE — the cardinal-restatement census, driven RED four ways.
#
# A census that has only ever been seen printing PIN MATCHED is a census nobody has
# watched refuse. T238's whole argument is that an unexercised guard is indistinguishable
# from a decorative one, so this drive perturbs the census in the four independent ways it
# is supposed to be sensitive to, and requires a DIFFERENT refusal from each:
#
#   RED-A  a NEW restatement appears in a tracked instrument   -> a '+' row, exit 1
#   RED-B  a pinned restatement is REPAIRED or DELETED         -> a '-' row, exit 1
#          (the frontier-not-amnesty direction, which most pins never test)
#   RED-C  the matcher is broken                               -> FATAL calibration, exit 2,
#          and NO hit list printed. This is the one that matters: a broken matcher must not
#          be able to report a clean tree.
#   RED-D  --against a graded run, with a punctuation-rotted literal -> STALE, exit 1.
#          This is the arm that catches a restatement whose NUMBER IS STILL RIGHT.
#
# ENGINE AND FLAGS (P-33/P-53/P-75): /usr/bin/grep by absolute path, LC_ALL=C, -aF fixed
# strings throughout. No bare `grep`, no `rg`, no `git grep -E`, so no \b/\d semantics.
# NO FAIL-OPEN SHAPE IN THIS FILE (T238 C1/C2/C6): the repo root comes from
# `git rev-parse --show-toplevel`, there is no absolute path literal anywhere, no `cd` into
# anything that might not exist, and no `|| echo` arm. Every grep's exit status is
# CLASSIFIED by an explicit `if`, never short-circuited into a print.
set -euo pipefail

R="$(git rev-parse --show-toplevel)"
cd "$R"

CENSUS="$R/.softhouse/capture/t255-frontier-rot/instruments/20-cardinal-restatement-census.py"
BAR="${1:-$R/.softhouse/capture/t255-frontier-rot/evidence/00-graded-run.txt}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t258-census-drive.XXXXXXXXXX")"
# T316's DEAD-PATH FRONTIER, which is NOT this drive's subject and must not be perturbed by it.
# The plant and the RED-B ghost row name files that DELIBERATELY do not exist, so writing either
# out whole would put a new dead repo-relative literal on that other frontier and turn the graded
# bar EXIT 2. MEASURED: they did, `T316-DEADPATH-FRONTIER: REFUSED rows=112 pinned=109 added=3`.
# Assembled from a directory that RESOLVES plus a bare basename, which is not a path at all. The
# perturbation is unchanged; only its spelling is. Same idiom and same reason as T243's plant.
PDIR=".softhouse/capture/t255-frontier-rot/evidence"
PNAME="planted-restatement"
GDIR=".softhouse/capture/t255-frontier-rot/instruments"
GNAME="ALREADY-REPAIRED"
PLANT="$R/$PDIR/$PNAME.sh"
PASS=0; FAIL=0

cleanup() {                 # P-54: the tree is restored on EVERY exit path
  git rm -q --cached --ignore-unmatch -- "$PLANT" >/dev/null 2>&1 || true
  rm -f "$PLANT"
  rm -rf "$WORK"
}
trap cleanup EXIT

ok()  { echo "  OK   $*"; PASS=$((PASS+1)); }
bad() { echo "  ***  $*"; FAIL=$((FAIL+1)); }

# has <file> <fixed-string> -> 0 found, 1 measured-absent; ANY other grep exit ABORTS,
# because an engine error printed as an absence is the class this whole capture is about.
has() {
  local f="$1" s="$2" rc=0
  LC_ALL=C /usr/bin/grep -qaF -- "$s" "$f" || rc=$?
  if [ "$rc" -eq 0 ]; then return 0; fi
  if [ "$rc" -eq 1 ]; then return 1; fi
  echo "  ***  /usr/bin/grep exited $rc on ${f}. ABORTING rather than printing an absence."
  exit 2
}

want() { # want <file> <label> <fixed-string>
  if has "$2" "$3"; then ok "[$1] found: $3"; else bad "[$1] NOT FOUND: $3"; fi
}
wantnot() { # wantnot <tag> <file> <label> <fixed-string>
  if has "$2" "$3"; then bad "[$1] PRESENT but must not be: $3"; else ok "[$1] absent as required: $3"; fi
}

runcensus() { # runcensus <script> <outfile> [extra args...]
  local sc="$1" of="$2"; shift 2
  set +e
  python3 "$sc" "$@" > "$of" 2>&1
  RC=$?
  set -e
}

echo "T258 RED DRIVE — the cardinal-restatement census"
echo "commit : $(git rev-parse HEAD)"
echo "census : $CENSUS"
echo "graded run used for the --against arm: $BAR"
echo

echo "=================================================================="
echo "CONTROL — the census over the delivered tree."
echo "=================================================================="
runcensus "$CENSUS" "$WORK/control.txt"
echo "  exit=$RC"
want CONTROL "$WORK/control.txt" "calibration OK"
want CONTROL "$WORK/control.txt" "PIN MATCHED"
if [ "$RC" -eq 0 ]; then ok "[CONTROL] exit 0"; else bad "[CONTROL] exit $RC, wanted 0"; fi
echo

echo "=================================================================="
echo "RED-A — a NEW restatement appears in a tracked instrument."
echo "=================================================================="
# ASSEMBLED, NOT PASTED, for the same reason T243's plant is: if the cardinal sentence
# appeared literally in THIS file, the census would flag this drive as a restatement and
# would be measuring itself. It is literal only in the GENERATED file, which is never
# committed. The plant carries NO dead path and NO printing failure arm, so it cannot move
# T238's fail-open frontier — this drive perturbs one census and not the other.
N='11'
{
  printf '%s\n' '#!/bin/sh'
  printf '%s\n' '# A DELIBERATELY TYPED FRONTIER CARDINAL, planted by T258 RED DRIVE. Removed by the'
  printf '%s\n' '# script that plants it; it must never be committed.'
  printf 'echo "frontier == pinned (all %s rows, by path)."\n' "$N"
} > "$PLANT"
chmod +x "$PLANT"
git add -f -- "$PLANT"
runcensus "$CENSUS" "$WORK/redA.txt"
echo "  exit=$RC"
want RED-A "$WORK/redA.txt" "+R1 $PDIR/$PNAME.sh"
want RED-A "$WORK/redA.txt" "DERIVE the count from the pin at run time; do not type it."
want RED-A "$WORK/redA.txt" "REFUSED"
wantnot RED-A "$WORK/redA.txt" "PIN MATCHED"
if [ "$RC" -eq 1 ]; then ok "[RED-A] exit 1"; else bad "[RED-A] exit $RC, wanted 1"; fi
cleanup_plant() { git rm -q --cached --ignore-unmatch -- "$PLANT" >/dev/null 2>&1 || true; rm -f "$PLANT"; }
cleanup_plant
echo

echo "=================================================================="
echo "RED-B — a PINNED restatement is repaired or deleted. The pin must"
echo "notice it LOSING a row, not only gaining one: a pin that only ever"
echo "grows is an amnesty."
echo "=================================================================="
# A scratch copy of the census with one extra row in its pin — equivalent to a site having
# been repaired while the pin still excuses it.
ANCHOR="R1 .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh"
GHOSTROW="R9 $GDIR/$GNAME.sh"
LC_ALL=C /usr/bin/sed "s#^${ANCHOR}\$#${ANCHOR}\\
${GHOSTROW}#" "$CENSUS" > "$WORK/census-extra-pin.py"
if LC_ALL=C /usr/bin/grep -qaF -- "$GHOSTROW" "$WORK/census-extra-pin.py"; then
  ok "[RED-B] the extra pin row landed in the scratch copy (the perturbation is real)"
else
  bad "[RED-B] the extra pin row did NOT land, so this arm proves nothing"
fi
runcensus "$WORK/census-extra-pin.py" "$WORK/redB.txt"
echo "  exit=$RC"
want RED-B "$WORK/redB.txt" "-$GHOSTROW"
want RED-B "$WORK/redB.txt" "IT IS A FRONTIER, NOT AN AMNESTY."
if [ "$RC" -eq 1 ]; then ok "[RED-B] exit 1"; else bad "[RED-B] exit $RC, wanted 1"; fi
echo

echo "=================================================================="
echo "RED-C — the MATCHER is broken. The census must DIE on its own"
echo "calibration and print NO hit list at all. A broken matcher that"
echo "reports a clean tree is the exact defect this capture is about."
echo "=================================================================="
LC_ALL=C /usr/bin/sed 's#r"all\\s+\[0-9\]+\\s+rows"#r"ZZZ_THIS_MATCHES_NOTHING_ZZZ"#g' \
  "$CENSUS" > "$WORK/census-broken.py"
if LC_ALL=C /usr/bin/grep -qaF 'ZZZ_THIS_MATCHES_NOTHING_ZZZ' "$WORK/census-broken.py"; then
  ok "[RED-C] the matcher really was broken in the scratch copy (the perturbation landed)"
else
  bad "[RED-C] the perturbation did NOT land, so this arm proves nothing"
fi
runcensus "$WORK/census-broken.py" "$WORK/redC.txt"
echo "  exit=$RC"
want RED-C "$WORK/redC.txt" "the known-positive calibration line was NOT matched"
wantnot RED-C "$WORK/redC.txt" "PIN MATCHED"
wantnot RED-C "$WORK/redC.txt" "MEASURED restatements"
if [ "$RC" -eq 2 ]; then ok "[RED-C] exit 2 — corpus/trust refusal, distinct from a pin mismatch"; else bad "[RED-C] exit $RC, wanted 2"; fi
echo

echo "=================================================================="
echo "RED-D — the SECOND ARM, over a real graded run. This is the arm"
echo "that catches a restatement whose NUMBER IS STILL CORRECT and whose"
echo "SENTENCE has moved. No search for a number can find these."
echo "=================================================================="
if [ ! -f "$BAR" ]; then
  bad "[RED-D] the graded transcript is not there: $BAR — this arm is NOT RUN, which is not a pass"
else
  runcensus "$CENSUS" "$WORK/redD.txt" --against "$BAR"
  echo "  exit=$RC"
  want RED-D "$WORK/redD.txt" "SECOND ARM"
  want RED-D "$WORK/redD.txt" "STALE     .softhouse/capture/t252-tier3/instruments/50-conformance-red-drive.py"
  want RED-D "$WORK/redD.txt" "STALE     .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh"
  want RED-D "$WORK/redD.txt" "by-design .softhouse/capture/t300-census-cardinal/instruments/10-cardinal-sweep.sh"
  if [ "$RC" -eq 1 ]; then ok "[RED-D] exit 1"; else bad "[RED-D] exit $RC, wanted 1"; fi
  echo "  --- the stale literals, verbatim: ---"
  LC_ALL=C /usr/bin/grep -aF 'STALE' "$WORK/redD.txt" | LC_ALL=C /usr/bin/sed 's/^/    /'
fi
echo

echo "=================================================================="
echo "GREEN AGAIN — nothing planted, nothing perturbed."
echo "=================================================================="
runcensus "$CENSUS" "$WORK/green.txt"
echo "  exit=$RC"
want GREEN "$WORK/green.txt" "PIN MATCHED"
if [ "$RC" -eq 0 ]; then ok "[GREEN] exit 0"; else bad "[GREEN] exit $RC, wanted 0"; fi
echo "  tree check: files git still tracks under the plant path: $(git ls-files -- "$PLANT" | LC_ALL=C /usr/bin/grep -ac '' || true)"
echo

echo "=================================================================="
echo "T258 CENSUS RED DRIVE: $PASS passed, $FAIL failed"
echo "=================================================================="
[ "$FAIL" -eq 0 ]
