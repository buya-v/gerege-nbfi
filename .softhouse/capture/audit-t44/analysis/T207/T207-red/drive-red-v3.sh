#!/usr/bin/env bash
# T207 RED/GREEN BATTERY -- a SCRATCH, WIDENED copy of T175's
# `.softhouse/capture/audit-t44/analysis/T175-red/drive-red.sh`.
#
# T114: T175's `drive-red.sh` produced the committed transcript `T175-red/drive-red-output.txt`
# and is therefore COMMITTED EVIDENCE. It is left byte-identical. This is the scratch copy.
#
# T163's DISCIPLINE, ADOPTED: a widened prover that does not say what it widened is
# indistinguishable from a replaced one. Every widening is named W-n below. Nothing T175 proved
# is deleted; LEG 0-3 are its legs, re-run, so the transcripts stay comparable.
#
#   W1  THE DEFECT T175's BATTERY COULD NOT SEE. T175 drove the SKIP path red and the ZERO-INPUT
#       path red. It never fed either script a VALUE-CORRUPTED money literal, which is why
#       `_v2` shipped detecting value corruption and printing PASS (T185 F-1). LEG V is that
#       input, against BOTH `_v2` (must show the defect: exit 0) and `v3` (must refuse: exit 1).
#   W2  BOTH HALVES OF THE NEW GATE (P-50). LEG V-GREEN shows v3 still exits 0 on the
#       legitimate corpus and reports figures IDENTICAL to `_v2`'s and the original's, so the
#       gate is falsifiable toward the fix as well as toward the defect.
#   W3  THE TEXT/VALUE SEPARATION IS ASSERTED, not assumed: the legitimate corpus has 41
#       text-lossy literals and v3 exits 0 anyway. If v3 had "tightened" onto byte-fidelity it
#       would refuse the oracle's own DECIMAL(19,6) emissions (T186 A4) and this leg goes red.
#   W4  THE GUARD'S OWN SELFTEST IS RUN AND ITS COUNTS ASSERTED, so a selftest that stopped
#       exercising both directions cannot pass silently (P-22).
#   W5  F-3's `cells()` DROP COUNTER IS DRIVEN RED THROUGH THE REAL ENTRY POINT, on a planted
#       root whose MONEYISH leaves are bare JSON numbers -- the condition the real corpus does
#       not contain and which is why the committed 772 held "by corpus luck, not by check".
#   W6  ROOT DERIVED, NOT HARD-CODED (T163 W1: A2-11's prover hard-coded a worktree path that
#       no longer exists, so nobody could re-run it). Derived from BASH_SOURCE and verified.
#
# Run with bash, NEVER sh:   bash <this file>
# Exits 0 only if every leg behaved as predicted.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# T207-red -> T207 -> analysis -> audit-t44 -> capture -> .softhouse -> repo root (six levels)
ROOT="$(cd "$HERE/../../../../../.." && pwd)"
cd "$ROOT" || exit 9
[ -f "$ROOT/CLAUDE.md" ] || { echo "ROOT=$ROOT is not the repo root"; exit 9; }

ORIG=".softhouse/capture/audit-t44/analysis/t44_float_roundtrip.py"
V2=".softhouse/capture/audit-t44/analysis/t44_float_roundtrip_v2.py"
V3=".softhouse/capture/audit-t44/analysis/T207/t44_float_roundtrip_v3.py"
COMMITTED=".softhouse/capture/audit-t44/analysis/t44_float_roundtrip-output.txt"
CENSUS=".softhouse/capture/audit-t44/analysis/T175-red/census.py"
MOS2=".softhouse/capture/leapboundary/analysis/T207/measure-other-sites-v2.py"
PLANT="$HERE/plant-corrupt.py"

REAL_GLOBS=(
  '.softhouse/capture/periodratio/out/*.json'
  '.softhouse/capture/mathcontext/out/*.json'
  '.softhouse/capture/charges/out/fc/*.json'
  '.softhouse/capture/charges/out/attested/*.json'
)
CLEAN_GLOBS=(
  '.softhouse/capture/charges/out/fc/*.json'
  '.softhouse/capture/charges/out/attested/*.json'
)

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
rc=0
leg() { printf '\n======== %s ========\n' "$1"; }
check() { # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then
    printf '  AS PREDICTED      %s: %s\n' "$1" "$3"
  else
    printf '  NOT AS PREDICTED  %s: expected %s, got %s\n' "$1" "$2" "$3"; rc=1
  fi
}

echo "T207 red/green battery -- widened scratch copy of T175-red/drive-red.sh"
echo "  root      : $ROOT"
echo "  commit    : $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo '?')"
echo "  python    : $(python3 -VV | head -1)"
echo "  scratch   : $SCRATCH"

n_requested=$(python3 "$CENSUS" --count-requested "${REAL_GLOBS[@]}")
n_unparseable=$(python3 "$CENSUS" --count-unparseable "${REAL_GLOBS[@]}")

# =========================================================================================
leg "LEG 0 (T175) -- the original's committed recipe still reproduces, so every leg is anchored"
python3 "$ORIG" "${REAL_GLOBS[@]}" > "$SCRATCH/orig-real.txt" 2>&1
if diff -q "$SCRATCH/orig-real.txt" "$COMMITTED" >/dev/null; then
  echo "  AS PREDICTED      the original re-run is BYTE-IDENTICAL to its committed output"
else
  echo "  NOT AS PREDICTED  the original no longer reproduces its committed output"; rc=1
fi
echo "  and the ORIGINAL has NO verdict machinery at all -- the PASS banner is NEW in _v2:"
# NOTE: the first draft of this leg asserted `grep -cE 'PASS|FAIL|sys.exit|^ *return'` == 0 and
# went RED against a CORRECT original -- `    return Decimal(s)` at :20 matched `^ *return`.
# The assertion was wrong, not the file. Recorded rather than quietly narrowed (honesty rule).
check "occurrences of PASS or FAIL anywhere in the ORIGINAL's source" "0" \
      "$(grep -cE 'PASS|FAIL' "$ORIG")"
check "occurrences of sys.exit / def main in the ORIGINAL's source" "0" \
      "$(grep -cE 'sys\.exit|def main' "$ORIG")"
check "occurrences of the word 'fail' in the ORIGINAL's committed transcript" "0" \
      "$(grep -ci 'fail\|pass' "$COMMITTED")"
check "occurrences of the PASS banner in _v2's source" "1" \
      "$(grep -c 'SUCCESSOR: PASS' "$V2")"
check "occurrences of failures.append in the ORIGINAL / in _v2" "0-5" \
      "$(grep -c 'failures.append' "$ORIG")-$(grep -c 'failures.append' "$V2")"
check "occurrences of lossy_value INSIDE a failures.append in _v2 (T185 F-1, the defect)" "0" \
      "$(grep -A3 'failures.append' "$V2" | grep -c 'lossy_value')"

# =========================================================================================
leg "LEG V-RED (W1) -- a VALUE-CORRUPTED money literal: the defect T185 raised as F-1"
python3 "$PLANT" "$SCRATCH/corrupt" corrupt > "$SCRATCH/plant.txt" 2>&1
sed 's/^/    planted: /' "$SCRATCH/plant.txt"
echo "  every literal below is a legal numeric(19,6) value -- the shape Fineract's own"
echo "  LoanProductRelatedDetail.java:61-62 (scale=6, precision=19) permits it to emit:"
sed 's/^/    | /' "$SCRATCH/corrupt/PLANTED-value-corrupt.json"

echo "  --- _v2 (the COMMITTED successor), same input:"
python3 "$V2" "$SCRATCH/corrupt/*.json" > "$SCRATCH/v2-corrupt.txt" 2>&1
v2rc=$?
check "_v2 exit status on a VALUE-CORRUPTED corpus (the DEFECT: it passes)" "0" "$v2rc"
check "_v2 DID detect it and print it under VALUE-lossy" "1" \
      "$(grep -c 'VALUE-lossy examples' "$SCRATCH/v2-corrupt.txt")"
check "_v2 nevertheless prints the PASS banner" "1" \
      "$(grep -c 'SUCCESSOR: PASS' "$SCRATCH/v2-corrupt.txt")"
echo "  --- _v2's own words, verbatim:"
grep -E 'VALUE != the decimal|SUCCESSOR: (PASS|FAILED)' "$SCRATCH/v2-corrupt.txt" | sed 's/^/    | /'

echo "  --- v3, same input:"
python3 "$V3" "$SCRATCH/corrupt/*.json" > "$SCRATCH/v3-corrupt.txt" 2>&1
v3rc=$?
check "v3 exit status on a VALUE-CORRUPTED corpus (must REFUSE)" "1" "$v3rc"
check "v3 prints no PASS banner" "0" "$(grep -c 'SUCCESSOR: PASS' "$SCRATCH/v3-corrupt.txt")"
check "v3 NAMES the corrupted literals and their residues" "1" \
      "$(grep -c 'VALUE-CORRUPTED MONEY LITERALS' "$SCRATCH/v3-corrupt.txt")"
echo "  --- v3's verdict block, verbatim:"
sed -n '/VALUE-CORRUPTED MONEY LITERALS/,$p' "$SCRATCH/v3-corrupt.txt" | sed 's/^/    | /'

# =========================================================================================
leg "LEG V-GREEN (W2, P-50) -- v3 PASSES the legitimate corpus, with figures UNCHANGED"
python3 "$V3" "${CLEAN_GLOBS[@]}" > "$SCRATCH/v3-clean.txt" 2>&1
check "v3 exit status on the charges-only corpus" "0" "$?"
python3 "$V2" "${CLEAN_GLOBS[@]}" > "$SCRATCH/v2-clean.txt" 2>&1
for f in 'distinct bare non-integer literals' 'total occurrences' 'max decimal scale seen'; do
  a=$(grep "$f" "$SCRATCH/v2-clean.txt" | tr -dc '0-9')
  b=$(grep "$f" "$SCRATCH/v3-clean.txt" | tr -dc '0-9')
  check "v2 vs v3 agree on '$f'" "$a" "$b"
done
echo "  --- v3's headline figures on the legitimate corpus:"
grep -E 'files (REQUESTED|PARSED|SKIPPED)|distinct bare|total occurrences|repr\(\) != the text|VALUE != the decimal|T207 v3:' \
     "$SCRATCH/v3-clean.txt" | sed 's/^/    | /'

# =========================================================================================
leg "LEG T (W3) -- TEXT-loss must NOT gate: 41 text-lossy literals and v3 still exits 0"
n_textlossy=$(sed -n 's/.*repr() != the text *: *\([0-9]*\).*/\1/p' "$SCRATCH/v3-clean.txt")
check "text-lossy literals in the legitimate corpus (must be > 0 or this leg proves nothing)" \
      "41" "$n_textlossy"
check "v3's verdict on that same corpus" "1" \
      "$(grep -c 'NO VALUE CORRUPTION DETECTED' "$SCRATCH/v3-clean.txt")"
check "v3 states WHY text-loss does not fail, on every run" "1" \
      "$(grep -c 'WHY TEXT-LOSS DOES NOT FAIL THIS RUN' "$SCRATCH/v3-clean.txt")"

# =========================================================================================
leg "LEG S (T175 LEG 1/3/5, re-run) -- v3 keeps every skip behaviour _v2 introduced"
python3 "$V3" "${REAL_GLOBS[@]}" > "$SCRATCH/v3-real.txt" 2>&1
check "v3 on the real corpus ($n_unparseable unparseable, unacknowledged)" "1" "$?"
check "files v3 NAMES as unscanned" "$n_unparseable" \
      "$(grep -c '^  UNSCANNED ' "$SCRATCH/v3-real.txt")"
python3 "$V3" "${REAL_GLOBS[@]}" --expect-skips "$n_unparseable" > "$SCRATCH/v3-ack.txt" 2>&1
check "v3 with --expect-skips $n_unparseable" "0" "$?"
python3 "$V3" "${REAL_GLOBS[@]}" --expect-skips 17 > "$SCRATCH/v3-wrong.txt" 2>&1
check "v3 with a WRONG --expect-skips 17" "1" "$?"
python3 "$V3" "$SCRATCH/corrupt/*.nosuchextension" > "$SCRATCH/v3-empty.txt" 2>&1
check "v3 on a glob matching NOTHING (P-35)" "1" "$?"
echo "  --- and the 245/9122 figures are unchanged from the original's:"
grep -E 'distinct bare|total occurrences' "$SCRATCH/v3-ack.txt" | sed 's/^/    | /'

# =========================================================================================
leg "LEG X (W4) -- v3's own --selftest, and its counts asserted"
python3 "$V3" --selftest > "$SCRATCH/v3-selftest.txt" 2>&1
check "v3 --selftest exit status" "0" "$?"
check "selftest cases that fire the VALUE gate (a zero here means the gate is unfalsifiable)" \
      "4" "$(sed -n 's/.*cases that fired P3 *: *\([0-9]*\).*/\1/p' "$SCRATCH/v3-selftest.txt")"
check "selftest cases that fire the TEXT predicate" \
      "7" "$(sed -n 's/.*cases that fired P2 *: *\([0-9]*\).*/\1/p' "$SCRATCH/v3-selftest.txt")"
sed 's/^/    | /' "$SCRATCH/v3-selftest.txt"

# =========================================================================================
leg "LEG D-GREEN (W5) -- F-3's cells() drop counter on the REAL corpus"
python3 "$MOS2" "$ROOT" > "$SCRATCH/mos2-real.txt" 2>&1
check "measure-other-sites-v2 exit status on the real tree" "0" "$?"
check "it publishes the same 12 pairs T175 did" "2" \
      "$(grep -c 'pairs compared *: 12' "$SCRATCH/mos2-real.txt")"
check "it publishes the same 772 deltas T175 did" "2" \
      "$(grep -c 'money deltas CONSIDERED *: 772' "$SCRATCH/mos2-real.txt")"
check "it now also prints the drop counter T175 omitted" "2" \
      "$(grep -c 'SILENTLY DROPPED before any delta' "$SCRATCH/mos2-real.txt")"
echo "  --- LEG A vs LEG B (does removing the float hazard move any published number?):"
sed -n '/LEG A vs LEG B/,/^$/p' "$SCRATCH/mos2-real.txt" | sed 's/^/    | /'

# =========================================================================================
leg "LEG D-RED (W5) -- the SAME counter, on a planted root whose money leaves are BARE NUMBERS"
FAKE="$SCRATCH/fakeroot"
mkdir -p "$FAKE/.softhouse/capture/leapboundary/analysis" \
         "$FAKE/.softhouse/capture/actualactual/pathb/out" \
         "$FAKE/.softhouse/capture/charges/out/fc"
cp "$ROOT/CLAUDE.md" "$FAKE/CLAUDE.md"
cp "$ROOT/.softhouse/capture/leapboundary/analysis/t55-analyse.py" \
   "$FAKE/.softhouse/capture/leapboundary/analysis/t55-analyse.py"
# One pair from the hard-coded PAIRS list. The money leaves are BARE JSON NUMBERS, which is
# exactly what cells() discards -- and exactly what the real corpus happens never to contain.
cat > "$FAKE/.softhouse/capture/actualactual/pathb/out/T48B-PUREB-p7-exact.json" <<'JSON'
{"periods": [{"period": 1, "principalDue": 1200000.00, "interestDue": 13158.10}],
 "totalPrincipalDisbursed": 1162502.50, "currency": {"code": "MNT"}}
JSON
cat > "$FAKE/.softhouse/capture/actualactual/pathb/out/T48B-PUREB-p4-exact.json" <<'JSON'
{"periods": [{"period": 1, "principalDue": 1200000.01, "interestDue": 13158.11}],
 "totalPrincipalDisbursed": 1162502.51, "currency": {"code": "MNT"}}
JSON
python3 "$MOS2" "$FAKE" > "$SCRATCH/mos2-planted.txt" 2>&1
check "measure-other-sites-v2 exit status on the planted root (must REFUSE)" "1" "$?"
check "it reports a NONZERO drop and says so LOUDLY" "1" \
      "$(grep -c 'DISCARDED BY cells() BEFORE the delta' "$SCRATCH/mos2-planted.txt")"
check "it states NIL-COVERAGE for the empty t46 population it was handed" "1" \
      "$(grep -c 'NIL-COVERAGE' "$SCRATCH/mos2-planted.txt")"
echo "  --- the planted run's LEG A drop block, verbatim:"
sed -n '/---- LEG A /,/---- LEG B /p' "$SCRATCH/mos2-planted.txt" | sed 's/^/    | /'
echo "  --- and its findings:"
grep -E '^  FINDING |^T207 measure-other-sites-v2' "$SCRATCH/mos2-planted.txt" | sed 's/^/    | /'
echo "  NOTE: the committed T175-red/measure-other-sites.py has NO drop counter at all, so on"
echo "  this same planted root it reports 'money deltas CONSIDERED : 0' and exits 0 in silence:"
python3 "$ROOT/.softhouse/capture/leapboundary/analysis/T175-red/measure-other-sites.py" "$FAKE" \
        > "$SCRATCH/mos1-planted.txt" 2>&1
check "the COMMITTED tool's exit status on the planted root (the F-3 defect)" "0" "$?"
# NOTE: the first draft asserted `grep -ci drop` == 0 and went red -- the committed tool DOES
# say "drop", in its header and in "DROPS N file(s) TODAY", both about the t46 FILE-skip site,
# not about cells() leaves. The assertion was wrong, not the file. Narrowed to the thing F-3
# actually names, and the wrong first draft is recorded rather than deleted (honesty rule).
check "the COMMITTED tool counts MONEYISH LEAVES anywhere" "0" \
      "$(grep -ci 'leaves\|DROPPED before any delta' "$SCRATCH/mos1-planted.txt")"
check "the COMMITTED tool's own delta count on a pair that differs in EVERY money cell" "0" \
      "$(sed -n 's/.*money deltas CONSIDERED *: *\([0-9]*\).*/\1/p' "$SCRATCH/mos1-planted.txt")"
echo "  ^ 1 pair compared, every money cell different, 0 deltas counted, exit 0, no word said."
grep -E 'pairs compared|money deltas' "$SCRATCH/mos1-planted.txt" | sed 's/^/    | /'

printf '\n======== VERDICT ========\n'
if [ "$rc" -eq 0 ]; then echo "  ALL LEGS AS PREDICTED"; else echo "  SOME LEG NOT AS PREDICTED"; fi
exit "$rc"
