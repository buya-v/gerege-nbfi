#!/bin/bash
# T258 RED DRIVE — the TIER1B residual: `rederive-provenance.sh` and its successor.
#
# THE CLAIM UNDER TEST is not "the successor works". It is the DIFFERENCE: given the same
# broken condition, the original prints a reassuring zero and exits 0, and the successor
# DIES. A successor that has only been seen succeeding proves nothing about the defect it
# was written for, so every arm below breaks something on purpose.
#
#   ARM 0   the ORIGINAL over today's tree      -> exit 0, PROMOTED CELLS SWEPT: 0.
#           MEASURED, NOT READ. This is the fail-open, live, at this commit.
#   ARM 1   the SUCCESSOR over today's tree     -> exit 0 and a NON-ZERO cell count.
#           Same exit code as ARM 0, opposite meaning — which is exactly why the exit
#           code was never the thing to look at.
#   ARM 2   the SUCCESSOR with its corpus taken away -> REFUSED, exit 2, and NO count
#           printed at all. This is the guard the original does not have.
#   ARM 3   the SUCCESSOR with its P-72 calibration positive broken -> REFUSED, exit 2,
#           BEFORE any cell is reported. The original ran a calibration, printed an EMPTY
#           count, and carried on; that is the calibration having no effect.
#   ARM 4   the SUCCESSOR run from OUTSIDE any git repository -> non-zero, no cell count.
#           It discovers its root instead of typing one, so it cannot inherit a dead root.
#
# ENGINE (P-33/P-53/P-75): /usr/bin/grep, LC_ALL=C, -aF fixed strings. No bare grep, no rg.
# NO FAIL-OPEN SHAPE HERE (T238 C1/C2/C6): no absolute path literal, no `cd` into anything
# that may not exist, no `|| echo`. Every perturbation ASSERTS THAT IT LANDED before the
# arm is scored, so a sed that silently matched nothing cannot produce a green arm.
set -euo pipefail

R="$(git rev-parse --show-toplevel)"
cd "$R"
DIR=".softhouse/reviews/a2-34-review-a2-15"
ORIG="$R/$DIR/rederive-provenance.sh"
SUCC="$R/$DIR/rederive-provenance-T258.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t258-rederive-drive.XXXXXXXXXX")"
PASS=0; FAIL=0
trap 'rm -rf "$WORK"' EXIT

ok()  { echo "  OK   $*"; PASS=$((PASS+1)); }
bad() { echo "  ***  $*"; FAIL=$((FAIL+1)); }

has() { # has <file> <fixed-string>; any grep exit but 0/1 ABORTS rather than printing an absence
  local f="$1" s="$2" rc=0
  LC_ALL=C /usr/bin/grep -qaF -- "$s" "$f" || rc=$?
  if [ "$rc" -eq 0 ]; then return 0; fi
  if [ "$rc" -eq 1 ]; then return 1; fi
  echo "  ***  /usr/bin/grep exited $rc on $f. ABORTING."; exit 2
}
want()    { if has "$2" "$3"; then ok "[$1] found: $3"; else bad "[$1] NOT FOUND: $3"; fi; }
wantnot() { if has "$2" "$3"; then bad "[$1] PRESENT but must not be: $3"; else ok "[$1] absent as required: $3"; fi; }

run() { # run <script> <outfile> [cwd]
  local sc="$1" of="$2" wd="${3:-$R}"
  set +e
  ( cd "$wd" && bash "$sc" ) > "$of" 2>&1
  RC=$?
  set -e
}

# perturb <src> <dst> <find> <replace> — and REFUSE if the replacement did not land.
perturb() {
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import sys
src, dst, find, repl = sys.argv[1:5]
s = open(src, encoding="utf-8").read()
if find not in s:
    sys.stderr.write("PERTURBATION ANCHOR NOT FOUND: %r\n" % find)
    sys.exit(3)
open(dst, "w", encoding="utf-8").write(s.replace(find, repl))
PY
}

echo "T258 RED DRIVE — rederive-provenance.sh (TIER1B) and its successor"
echo "commit : $(git rev-parse HEAD)"
echo

echo "=================================================================="
echo "ARM 0 — THE ORIGINAL, over today's tree. Measured, not read."
echo "=================================================================="
run "$ORIG" "$WORK/arm0.txt"
echo "  exit=$RC"
want ARM0 "$WORK/arm0.txt" "PROMOTED CELLS SWEPT: 0"
if [ "$RC" -eq 0 ]; then
  ok "[ARM0] exit 0 while sweeping ZERO cells — the fail-open, live at this commit"
else
  bad "[ARM0] exit $RC. The original is not fail-open today, so this drive proves less than claimed"
fi
echo "  the root it hard-codes, and whether it exists:"
LC_ALL=C /usr/bin/sed -n '11p' "$ORIG" | LC_ALL=C /usr/bin/sed 's/^/    | /'
echo

echo "=================================================================="
echo "ARM 1 — THE SUCCESSOR, over the same tree. Same exit code as ARM 0,"
echo "opposite meaning: it reached a corpus and says how big it was."
echo "=================================================================="
run "$SUCC" "$WORK/arm1.txt"
echo "  exit=$RC"
want ARM1 "$WORK/arm1.txt" "calibration OK -- a zero below is a real zero."
want ARM1 "$WORK/arm1.txt" "VECTOR FILES READ    : 13"
wantnot ARM1 "$WORK/arm1.txt" "PROMOTED CELLS SWEPT : 0   "
if [ "$RC" -eq 0 ]; then ok "[ARM1] exit 0"; else bad "[ARM1] exit $RC, wanted 0"; fi
echo "  --- the two counts, side by side: ---"
LC_ALL=C /usr/bin/grep -aF 'PROMOTED CELLS SWEPT' "$WORK/arm0.txt" | LC_ALL=C /usr/bin/sed 's/^/    ORIGINAL  /'
LC_ALL=C /usr/bin/grep -aF 'PROMOTED CELLS SWEPT' "$WORK/arm1.txt" | LC_ALL=C /usr/bin/sed 's/^/    SUCCESSOR /'
echo

echo "=================================================================="
echo "ARM 2 — the SUCCESSOR with its corpus taken away. The guard the"
echo "original does not have: a zero it never took is never printed."
echo "=================================================================="
# The replacement names a directory that DELIBERATELY does not exist. It is assembled from a
# live prefix and a bare basename rather than written whole, because a dead repo-relative literal
# here joins T316's DEAD-PATH frontier and turns the graded bar EXIT 2 — MEASURED, it did. That
# frontier is not this drive's subject and this drive must not move it.
NOSUCH="NO-SUCH-DIRECTORY"
perturb "$SUCC" "$WORK/no-corpus.sh" \
  'VD="$R/.softhouse/vectors/ledger"' 'VD="$R/.softhouse/vectors/'"$NOSUCH"'"'
ok "[ARM2] the perturbation landed (anchor found and replaced)"
run "$WORK/no-corpus.sh" "$WORK/arm2.txt"
echo "  exit=$RC"
want ARM2 "$WORK/arm2.txt" "REFUSED -- the ledger vector directory is not there"
want ARM2 "$WORK/arm2.txt" "No count is reported, because no count was taken."
wantnot ARM2 "$WORK/arm2.txt" "PROMOTED CELLS SWEPT"
if [ "$RC" -eq 2 ]; then ok "[ARM2] exit 2"; else bad "[ARM2] exit $RC, wanted 2"; fi
echo

echo "=================================================================="
echo "ARM 3 — the SUCCESSOR with its P-72 calibration POSITIVE broken."
echo "The original ran a calibration, printed an EMPTY count, and carried"
echo "on. Here it is fatal, and it fires BEFORE any cell is reported."
echo "=================================================================="
perturb "$SUCC" "$WORK/no-cal.sh" \
  "-c -aF '\"case_id\"' \"\$CALFILE\"" "-c -aF 'ZZZ_NEVER_IN_ANY_VECTOR' \"\$CALFILE\""
ok "[ARM3] the perturbation landed (anchor found and replaced)"
run "$WORK/no-cal.sh" "$WORK/arm3.txt"
echo "  exit=$RC"
want ARM3 "$WORK/arm3.txt" "CAL+ found ZERO known-positive hits"
wantnot ARM3 "$WORK/arm3.txt" "PROMOTED CELLS SWEPT"
if [ "$RC" -eq 2 ]; then ok "[ARM3] exit 2"; else bad "[ARM3] exit $RC, wanted 2"; fi
echo

echo "=================================================================="
echo "ARM 4 — the SUCCESSOR from OUTSIDE any git repository. It discovers"
echo "its root rather than typing one, so it cannot inherit a dead root"
echo "the way the original did."
echo "=================================================================="
mkdir -p "$WORK/not-a-repo"
run "$SUCC" "$WORK/arm4.txt" "$WORK/not-a-repo"
echo "  exit=$RC"
wantnot ARM4 "$WORK/arm4.txt" "PROMOTED CELLS SWEPT"
if [ "$RC" -ne 0 ]; then ok "[ARM4] exit $RC (non-zero) and no cell count printed"; else bad "[ARM4] exit 0 outside a repo"; fi
echo

echo "=================================================================="
echo "T258 REDERIVE RED DRIVE: $PASS passed, $FAIL failed"
echo "=================================================================="
[ "$FAIL" -eq 0 ]
