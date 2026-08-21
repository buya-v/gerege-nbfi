#!/usr/bin/env bash
# T175 RED PROBE -- t44_float_roundtrip.py:29
#
# P-22: ship no guard you have not personally driven RED.  P-50: drive BOTH halves -- show the
# successor REFUSES the input the original swallows, AND show it still PASSES the clean corpus,
# so it is falsifiable toward the fix as well as toward the defect.
#
# Run from anywhere with bash (never sh):   bash <this file>
# Exits 0 only if every leg behaved as predicted.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# T175-red -> analysis -> audit-t44 -> capture -> .softhouse -> repo root  (five levels)
ROOT="$(cd "$HERE/../../../../.." && pwd)"
cd "$ROOT" || exit 9
# Fail loudly rather than silently misbehaving if the layout ever moves.
[ -f "$ROOT/CLAUDE.md" ] || { echo "ROOT=$ROOT is not the repo root"; exit 9; }

ORIG=".softhouse/capture/audit-t44/analysis/t44_float_roundtrip.py"
SUCC=".softhouse/capture/audit-t44/analysis/t44_float_roundtrip_v2.py"
COMMITTED=".softhouse/capture/audit-t44/analysis/t44_float_roundtrip-output.txt"

# The recipe that reproduces the ORIGINAL's committed output byte-for-byte.
REAL_GLOBS=(
  '.softhouse/capture/periodratio/out/*.json'
  '.softhouse/capture/mathcontext/out/*.json'
  '.softhouse/capture/charges/out/fc/*.json'
  '.softhouse/capture/charges/out/attested/*.json'
)
# The subset with no unparseable member: the "clean corpus" leg.
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

n_requested=$(python3 "$HERE/census.py" --count-requested "${REAL_GLOBS[@]}")
n_unparseable=$(python3 "$HERE/census.py" --count-unparseable "${REAL_GLOBS[@]}")

# ---------------------------------------------------------------------------------------
leg "LEG 0 -- the original's committed recipe reproduces, so every leg below is about THAT run"
python3 "$ORIG" "${REAL_GLOBS[@]}" > "$SCRATCH/orig-real.txt" 2>&1
if diff -q "$SCRATCH/orig-real.txt" "$COMMITTED" >/dev/null; then
  echo "  AS PREDICTED      the original re-run is BYTE-IDENTICAL to its committed output"
else
  echo "  NOT AS PREDICTED  the original no longer reproduces its committed output"; rc=1
fi

# ---------------------------------------------------------------------------------------
leg "LEG 1 -- REAL corpus: the ORIGINAL swallows real committed files and says nothing"
echo "  files handed to it   : $n_requested"
echo "  of which UNPARSEABLE : $n_unparseable"
n_mentions=$(grep -ci 'skip\|unparse\|unscanned\|error\|fail' "$SCRATCH/orig-real.txt" || true)
check "words skip/unparse/unscanned/error/fail anywhere in the ORIGINAL's output" "0" "$n_mentions"
if grep -q '=> no literal changes VALUE' "$SCRATCH/orig-real.txt"; then
  echo "  AS PREDICTED      the ORIGINAL still prints its clean-bill-of-health sentence"
else
  echo "  NOT AS PREDICTED  clean-bill sentence absent"; rc=1
fi

echo "  --- the SAME input through the SUCCESSOR:"
python3 "$SUCC" "${REAL_GLOBS[@]}" > "$SCRATCH/succ-real.txt" 2>&1
check "SUCCESSOR exit status on the real corpus (must REFUSE)" "1" "$?"
check "files the SUCCESSOR NAMES as unscanned" "$n_unparseable" \
      "$(grep -c '^  UNSCANNED ' "$SCRATCH/succ-real.txt")"
echo "  first three named:"
grep '^  UNSCANNED ' "$SCRATCH/succ-real.txt" | head -3 | sed 's/^/    /'

# ---------------------------------------------------------------------------------------
leg "LEG 2 -- PLANTED input: a file that is not JSON at all, alone in a directory"
mkdir -p "$SCRATCH/plant"
printf 'this is not json\n' > "$SCRATCH/plant/PLANTED-not-json.json"
python3 "$ORIG" "$SCRATCH/plant/*.json" > "$SCRATCH/orig-plant.txt" 2>&1
echo "  --- ORIGINAL output, verbatim:"
sed 's/^/    | /' "$SCRATCH/orig-plant.txt"
check "ORIGINAL's reported distinct literals (0 = it scanned NOTHING)" "0" \
      "$(sed -n 's/.*distinct bare non-integer literals: *//p' "$SCRATCH/orig-plant.txt")"
if grep -q '=> no literal changes VALUE' "$SCRATCH/orig-plant.txt"; then
  echo "  AS PREDICTED      the ORIGINAL certifies 'no committed charges number is corrupted"
  echo "                    TODAY' having successfully read ZERO files -- the vacuous pass"
else
  echo "  NOT AS PREDICTED  no clean-bill sentence"; rc=1
fi

python3 "$SUCC" "$SCRATCH/plant/*.json" > "$SCRATCH/succ-plant.txt" 2>&1
check "SUCCESSOR exit status on the planted file" "1" "$?"
check "SUCCESSOR names the planted file by path" "1" \
      "$(grep -c 'PLANTED-not-json.json' "$SCRATCH/succ-plant.txt")"
echo "  --- SUCCESSOR verdict lines:"
grep -E '^  FAIL |^  files (REQUESTED|PARSED|SKIPPED)' "$SCRATCH/succ-plant.txt" | sed 's/^/    /'

# ---------------------------------------------------------------------------------------
leg "LEG 3 -- PLANTED input: a glob matching NOTHING (zero inspected must be an ERROR, P-35)"
python3 "$ORIG" "$SCRATCH/plant/*.nosuchextension" > "$SCRATCH/orig-empty.txt" 2>&1
echo "  --- ORIGINAL output, verbatim:"
sed 's/^/    | /' "$SCRATCH/orig-empty.txt"
if grep -q '=> no literal changes VALUE' "$SCRATCH/orig-empty.txt"; then
  echo "  AS PREDICTED      the ORIGINAL gives a clean bill of health for an EMPTY file set"
else
  echo "  NOT AS PREDICTED"; rc=1
fi
python3 "$SUCC" "$SCRATCH/plant/*.nosuchextension" > "$SCRATCH/succ-empty.txt" 2>&1
check "SUCCESSOR exit status on an empty file set" "1" "$?"
if grep -q 'inspects nothing is an ERROR' "$SCRATCH/succ-empty.txt"; then
  echo "  AS PREDICTED      the SUCCESSOR calls zero-inspected an ERROR (P-35)"
else
  echo "  NOT AS PREDICTED"; rc=1
fi

# ---------------------------------------------------------------------------------------
leg "LEG 4 -- the OTHER half (P-50): the SUCCESSOR PASSES the legitimate corpus"
python3 "$SUCC" "${CLEAN_GLOBS[@]}" > "$SCRATCH/succ-clean.txt" 2>&1
check "SUCCESSOR exit status on the charges-only corpus (0 unparseable)" "0" "$?"
check "SUCCESSOR skip count there" "0" \
      "$(sed -n 's/.*files SKIPPED *: *\([0-9]*\).*/\1/p' "$SCRATCH/succ-clean.txt")"
echo "  --- its headline figures:"
grep -E 'files (REQUESTED|PARSED|SKIPPED)|distinct bare|total occurrences|VALUE != the decimal|T175 SUCCESSOR' \
     "$SCRATCH/succ-clean.txt" | sed 's/^/    /'

# ---------------------------------------------------------------------------------------
leg "LEG 5 -- an EXPLICITLY acknowledged, exactly-matching skip count is accepted; a wrong one is not"
python3 "$SUCC" "${REAL_GLOBS[@]}" --expect-skips "$n_unparseable" > "$SCRATCH/succ-ack.txt" 2>&1
check "SUCCESSOR exit with --expect-skips $n_unparseable" "0" "$?"
check "the count is still printed prominently, never as zero" "1" \
      "$(grep -c "files SKIPPED       : $n_unparseable" "$SCRATCH/succ-ack.txt")"
python3 "$SUCC" "${REAL_GLOBS[@]}" --expect-skips 17 > "$SCRATCH/succ-wrong.txt" 2>&1
check "SUCCESSOR exit with a WRONG --expect-skips 17 (must still refuse)" "1" "$?"
echo "  --- the 245/9122/0 figures are UNCHANGED from the original's, so this is a fix, not a rewrite:"
grep -E 'distinct bare|total occurrences|VALUE != the decimal' "$SCRATCH/succ-ack.txt" | sed 's/^/    /'

printf '\n======== VERDICT ========\n'
if [ "$rc" -eq 0 ]; then echo "  ALL LEGS AS PREDICTED"; else echo "  SOME LEG NOT AS PREDICTED"; fi
exit "$rc"
