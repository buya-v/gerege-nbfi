#!/usr/bin/env bash
# T259 -- drive R-VPA RED, on shapes it was NOT designed around (P-76).
#
# A rule that only catches the three rows that prompted it is not a rule, it is a hard-coded
# assertion with extra steps. Every RED leg below uses a container key, an id key, a predicate
# number, a verdict key and a verdict word that DO NOT APPEAR in classify-t229.json.
#
# P-80: exit codes are classified, never conflated. 0 GREEN, 1 REAL MEASURED REFUSAL, 2 ERROR.
# A leg that expects 1 and gets 2 FAILS -- "it exited non-zero" is evidence of nothing.
# P-83: the probe line's PRESENCE is asserted before any of its VALUES is read.
# P-75: never bare `grep`, never `rg`. /usr/bin/grep only, and its exit status is classified.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$DIR/../../.." && pwd)"
CHK="$DIR/check_verdict_predicate_agreement.py"
FIX="$HERE/fixtures"
REAL="$ROOT/.softhouse/capture/t229-g8-site3/out/classify-t229.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0
FAIL=0

say() { printf '%s\n' "$*"; }

# grep_count <pattern> <file> -- echoes the count; ABORTS on a real grep error (P-80).
grep_count() {
  local n rc
  # The abort is disarmed for exactly ONE line so the status can be CAPTURED and then CLASSIFIED
  # four lines below: 0 and 1 are BOTH real measurements, >1 aborts the whole battery. Nothing is
  # swallowed here; the shape P-80 bans is the one that prints a zero over an error instead.
  # lint-failopen: ok -- status captured into $rc and classified immediately; >1 aborts (P-80)
  set +e
  n="$(/usr/bin/grep -c -- "$1" "$2")"
  rc=$?
  set -e
  if [ "$rc" -gt 1 ]; then
    say "*** GREP ERROR rc=$rc on pattern [$1] file [$2] -- ABORTING; an error is not a zero."
    exit 9
  fi
  printf '%s' "$n"
}

# leg <name> <expected-rc> <comma-separated probe assertions, or -> -- <argv for python3...>
leg() {
  local name="$1"; shift
  local want_rc="$1"; shift
  local asserts="$1"; shift
  if [ "$1" != "--" ]; then say "BATTERY BUG: missing -- in leg $name"; exit 9; fi
  shift
  local out="$TMP/$name.out"
  local rc=0
  python3 "$@" >"$out" 2>&1 || rc=$?

  say ""
  say "--- LEG $name"
  say "    argv          : $*"
  say "    exit expected : $want_rc"
  say "    exit actual   : $rc"

  local ok=1
  if [ "$rc" != "$want_rc" ]; then
    ok=0
    say "    *** EXIT MISMATCH"
  fi

  # P-83: PRESENCE first, VALUE second.
  local nprobe
  nprobe="$(grep_count '^T259-VPA:' "$out")"
  local probe=""
  if [ "$nprobe" -ge 1 ]; then
    probe="$(/usr/bin/grep -m1 '^T259-VPA:' "$out")"
    say "    probe line    : PRESENT ($nprobe)"
    say "    probe         : $probe"
  elif [ "$want_rc" = "2" ]; then
    say "    probe line    : ABSENT -- expected, an ERROR exits before the probe is reached"
  else
    ok=0
    say "    *** PROBE LINE ABSENT on a leg that should have reached it"
  fi

  if [ -n "$probe" ] && [ "$asserts" != "-" ]; then
    local a n2
    local _A=()
    IFS=',' read -ra _A <<<"$asserts"
    for a in "${_A[@]}"; do
      printf '%s' "$probe" >"$TMP/.probe"
      n2="$(grep_count " $a" "$TMP/.probe")"
      if [ "$n2" -ge 1 ]; then
        say "    assert OK     : $a"
      else
        ok=0
        say "    *** ASSERT FAILED: expected ' $a' in the probe line"
      fi
    done
  fi

  say "    ---- the instrument's own words:"
  sed -n '1,120p' "$out" | sed 's/^/    | /'

  if [ "$ok" = "1" ]; then
    PASS=$((PASS + 1)); say "    LEG $name: PASS"
  else
    FAIL=$((FAIL + 1)); say "    LEG $name: FAIL"
  fi
}

say "================================================================================"
say "T259 R-VPA RED/GREEN BATTERY"
say "checker      : $CHK"
say "real evidence: $REAL"
say "sha256(real) : $(shasum -a 256 "$REAL" | awk '{print $1}')"
say "HEAD         : $(git -C "$ROOT" rev-parse HEAD)"
say "vector store : $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
say "================================================================================"

# ---------------------------------------------------------------------------------
# RED legs on FRESH shapes -- nothing here resembles a T229 row.
# ---------------------------------------------------------------------------------
leg R1-fresh-predicate-fresh-verdict-word 1 \
  "REFUSED,rows=1,predicates=2,disagreements=1,acknowledged=0,unacknowledged=1,unclassifiedKeys=0,unclassifiedVerdicts=0" \
  -- "$CHK" "$FIX/R1-fresh-predicate-fresh-verdict-word.json"

leg R2-unclassified-verdict-word 1 \
  "REFUSED,rows=1,disagreements=0,unclassifiedVerdicts=1" \
  -- "$CHK" "$FIX/R2-unclassified-verdict-word.json"

leg R3-unclassified-boolean-key 1 \
  "REFUSED,rows=1,disagreements=0,unclassifiedKeys=1" \
  -- "$CHK" "$FIX/R3-unclassified-boolean-key.json"

leg N1-nil-coverage 1 \
  "REFUSED,rows=0,nilCoverage=1" \
  -- "$CHK" "$FIX/N1-nil-coverage.json"

# ---------------------------------------------------------------------------------
# GREEN controls -- a rule that is always red is also not a rule.
# ---------------------------------------------------------------------------------
leg G1-false-predicate-negative-verdict 0 \
  "GREEN,rows=1,predicates=1,disagreements=0" \
  -- "$CHK" "$FIX/G1-false-predicate-negative-verdict.json"

leg G2-all-true-affirmative-verdict 0 \
  "GREEN,rows=1,predicates=2,disagreements=0" \
  -- "$CHK" "$FIX/G2-all-true-affirmative-verdict.json"

# ---------------------------------------------------------------------------------
# The real, committed evidence: GREEN, and STILL LOUD.
# ---------------------------------------------------------------------------------
leg L1-real-evidence-green 0 \
  "GREEN,rows=11,predicates=24,disagreements=3,acknowledged=3,unacknowledged=0" \
  -- "$CHK" "$REAL"

say ""
say "--- LEG L2-loudness: a GREEN run must STILL PRINT every disagreement"
say "    (an acknowledgement changes the EXIT CODE only -- never the noise)"
python3 "$CHK" "$REAL" >"$TMP/L2.out"
L2N="$(grep_count '\*\*\* DISAGREEMENT' "$TMP/L2.out")"
say "    DISAGREEMENT blocks printed on the GREEN run: $L2N (expected 3)"
if [ "$L2N" = "3" ]; then
  PASS=$((PASS + 1)); say "    LEG L2-loudness: PASS"
else
  FAIL=$((FAIL + 1)); say "    LEG L2-loudness: FAIL"
fi

# ---------------------------------------------------------------------------------
# T114/T176 enforced BY THE INSTRUMENT: acknowledgements are pinned to BYTES.
# Both legs write their scratch copy OUTSIDE the repo. The real evidence is never written to.
# ---------------------------------------------------------------------------------
REALSHA="$(shasum -a 256 "$REAL" | awk '{print $1}')"
python3 "$HERE/make_scratch_ack.py" "$TMP/Va-ack.json" "$TMP/Va.json" "$REALSHA"

# V-a: WHITESPACE-ONLY mutation. Content-identical, bytes different.
cp "$REAL" "$TMP/Va.json"
printf '\n' >>"$TMP/Va.json"
leg Va-byte-pin-whitespace-only-mutation 1 \
  "REFUSED,rows=11,disagreements=3,acknowledged=0,unacknowledged=3" \
  -- "$CHK" "$TMP/Va.json" --acknowledgements "$TMP/Va-ack.json"

# V-b: SEMANTIC mutation -- flip the ONE true P2 to false, on T229-R36p0-N1400-B150, a row
# deliberately NOT in the acknowledgement list. Two independent alarms must fire.
python3 "$HERE/mutate_one_predicate.py" "$REAL" "$TMP/Vb.json" \
  T229-R36p0-N1400-B150 P2_totalInterestEqualsNEplusB
python3 "$HERE/make_scratch_ack.py" "$TMP/Vb-ack.json" "$TMP/Vb.json" "$REALSHA"
leg Vb-byte-pin-semantic-mutation 1 \
  "REFUSED,rows=11,disagreements=4,acknowledged=0,unacknowledged=4" \
  -- "$CHK" "$TMP/Vb.json" --acknowledgements "$TMP/Vb-ack.json"

# ---------------------------------------------------------------------------------
# ERROR path -- exit 2 must never be reachable by an absence, and 1 must never be an error.
# ---------------------------------------------------------------------------------
leg E1-missing-target 2 "-" -- "$CHK" "$TMP/does-not-exist.json"
leg E2-unreadable-register 2 "-" -- "$CHK" "$REAL" --register "$TMP/no-such-register.json"

# ---------------------------------------------------------------------------------
# P-80 SELF-CHECK. Last fire THREE workers put fail-opens into the instruments written to
# enforce the rule they broke. Check MY OWN instruments first.
# ---------------------------------------------------------------------------------
say ""
say "--- LEG S-self-failopen-lint: my own instruments"
SRC=0
python3 "$DIR/lint_failopen_t259.py" "$DIR" >"$TMP/lint.out" 2>&1 || SRC=$?
sed -n '1,200p' "$TMP/lint.out" | sed 's/^/    | /'
say "    lint exit: $SRC"
if [ "$SRC" = "0" ]; then
  PASS=$((PASS + 1)); say "    LEG S-self-failopen-lint: PASS"
else
  FAIL=$((FAIL + 1)); say "    LEG S-self-failopen-lint: FAIL"
fi

# The lint must itself be falsifiable: plant a fail-open and prove it goes RED.
say ""
say "--- LEG S2-lint-driven-red: plant a fail-open, the lint must catch it"
mkdir -p "$TMP/planted"
python3 "$HERE/plant_failopen.py" "$TMP/planted/planted.sh"
SRC2=0
python3 "$DIR/lint_failopen_t259.py" "$TMP/planted" >"$TMP/lint2.out" 2>&1 || SRC2=$?
sed -n '1,60p' "$TMP/lint2.out" | sed 's/^/    | /'
say "    lint exit on planted tree: $SRC2 (expected 1)"
if [ "$SRC2" = "1" ]; then
  PASS=$((PASS + 1)); say "    LEG S2-lint-driven-red: PASS"
else
  FAIL=$((FAIL + 1)); say "    LEG S2-lint-driven-red: FAIL"
fi

say ""
say "================================================================================"
say "BATTERY: $PASS passed, $FAIL failed"
say "vector store at end: $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
say "sha256(real) at end: $(shasum -a 256 "$REAL" | awk '{print $1}')"
say "================================================================================"
if [ "$FAIL" != "0" ]; then
  exit 1
fi
