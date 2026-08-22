#!/bin/bash
# A2-34 REVIEWER'S OWN RED DRIVES (P-22). Independent of A2-15's red-green-a2-15.sh:
# this script does not source it, does not call it, and picks its own perturbations.
# Every case runs through `bash .softhouse/conformance.sh` — the route that actually
# executes (P-45) — and asserts a DIAGNOSTIC LINE, never an exit code alone (P-62).
# Every perturbation is PROVEN APPLIED before the case runs, and the revert is
# PROVEN by digest afterwards.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"

V=.softhouse/vectors/ledger
LOG=/tmp/a234-red
mkdir -p "$LOG"
PASS=0; FAIL=0

digest() { git rev-parse "HEAD:.softhouse/vectors" >/dev/null 2>&1; ( cd "$R" && find .softhouse/vectors/ledger -name '*.json' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -c1-16 ); }

START_DIGEST=$(digest)
echo "START ledger vector digest: $START_DIGEST"
echo

run() { # run <tag>  [extra args...]
  local tag="$1"; shift
  bash .softhouse/conformance.sh "$@" > "$LOG/$tag.txt" 2>&1
  echo "$?" > "$LOG/$tag.exit"
}

expect_line() { # expect_line <tag> <label> <fixed-string>
  local tag="$1" label="$2" needle="$3"
  local n
  n=$(LC_ALL=C /usr/bin/grep -c -aF "$needle" "$LOG/$tag.txt" || true)
  local ex; ex=$(cat "$LOG/$tag.exit")
  if [ "${n:-0}" -gt 0 ]; then
    echo "  OK   [$label] exit=$ex  FOUND ($n) : $needle"
    PASS=$((PASS+1))
  else
    echo "  ***  [$label] exit=$ex  NOT FOUND  : $needle"
    FAIL=$((FAIL+1))
  fi
}

expect_absent() {
  local tag="$1" label="$2" needle="$3"
  local n; n=$(LC_ALL=C /usr/bin/grep -c -aF "$needle" "$LOG/$tag.txt" || true)
  if [ "${n:-0}" -eq 0 ]; then echo "  OK   [$label] ABSENT as required : $needle"; PASS=$((PASS+1))
  else echo "  ***  [$label] PRESENT but must be absent ($n) : $needle"; FAIL=$((FAIL+1)); fi
}

prove_applied() { # prove_applied <file> <fixed-string-that-must-now-be-there>
  local f="$1" s="$2"
  local n; n=$(LC_ALL=C /usr/bin/grep -c -aF "$s" "$f" || true)
  if [ "${n:-0}" -gt 0 ]; then echo "  perturbation PROVEN APPLIED in $(basename "$f"): $s"
  else echo "  *** PERTURBATION DID NOT APPLY — the case below proves nothing"; FAIL=$((FAIL+1)); fi
}

revert() { git checkout -- .softhouse/vectors/ledger; }

echo "=================================================================="
echo "CONTROL 0 — pristine committed store must be GREEN (anti-no-op)"
echo "=================================================================="
run control0
expect_line control0 "control0" "VERDICT: PASS (exit 0)"
expect_line control0 "control0" "ledger parity           PASS 4    FAIL 0"
expect_line control0 "control0" "ledger oracle-refusal   PASS 2    FAIL 0"
expect_line control0 "control0" "ledger cells compared   70 graded, of which 21 are MONEY cells"
expect_line control0 "control0" "probe = up"
echo

echo "=================================================================="
echo "RD-1 — ONE MINOR UNIT on a promoted expectation leg (LDG-02 principal"
echo "       27045058 -> 27045059). Must be a MONEY kill through conformance.sh."
echo "=================================================================="
F=$V/LDG-02-repayment-split-4leg-minor-units.json
/usr/bin/sed -i '' 's/"amount_minor": "27045058"/"amount_minor": "27045059"/' "$F"
prove_applied "$F" '"amount_minor": "27045059"'
run rd1
expect_line rd1 "RD-1" "MONEY want 27045059, got 27045058"
expect_line rd1 "RD-1" "margin -1 minor units"
expect_line rd1 "RD-1" "ledger parity           PASS 3    FAIL 1"
revert
echo

echo "=================================================================="
echo "RD-2 — I-2 ALONE. Move the RECORDED REQUESTED TOTAL on LDG-03 by ONE"
echo "       MINOR UNIT (1000000 -> 1000000.01). splits_sum_to_whole must go"
echo "       VIOLATED while double_entry_balances still HOLDS. If both move"
echo "       together, I-2 is a restatement of I-1 and A2-15's claim 3 is false."
echo "=================================================================="
F=$V/LDG-03-overpayment-4leg-minor-units.json
/usr/bin/sed -i '' 's/"transaction_amount_major_text": "1000000"/"transaction_amount_major_text": "1000000.01"/' "$F"
prove_applied "$F" '"transaction_amount_major_text": "1000000.01"'
run rd2
expect_line rd2 "RD-2" "INVARIANT splits_sum_to_whole      VIOLATED"
expect_line rd2 "RD-2" "INVARIANT double_entry_balances    HOLD"
expect_line rd2 "RD-2" "invariant"
revert
echo

echo "=================================================================="
echo "RD-3 — the DOUBLE-ENTRY assertion itself. Select the registered wrong"
echo "       implementation ledger-wrong-truncating through conformance.sh and"
echo "       require I-1 to be VIOLATED, not merely a cell diff."
echo "=================================================================="
run rd3 --ledger-impl ledger-wrong-truncating
expect_line rd3 "RD-3" "INVARIANT double_entry_balances"
grep -aF "INVARIANT double_entry_balances" "$LOG/rd3.txt" | head -6
echo

echo "=================================================================="
echo "RD-4 — DEFLATION. Delete ONE promoted ledger vector; the pinned"
echo "       population gate must refuse (T233 equality, both directions)."
echo "=================================================================="
cp $V/LDG-04-header-account-accepted.json /tmp/a234-LDG-04.bak
rm $V/LDG-04-header-account-accepted.json
run rd4
expect_line rd4 "RD-4" "LEDGER parity vectors"
grep -aF "LEDGER parity vectors" "$LOG/rd4.txt"
grep -aF "LEDGER money cells" "$LOG/rd4.txt"
cp /tmp/a234-LDG-04.bak $V/LDG-04-header-account-accepted.json
echo

echo "=================================================================="
echo "RD-5 — INFLATION. Add a SEVENTH ledger vector (a copy of LDG-01 under a"
echo "       new case_id); the pinned population gate must refuse."
echo "=================================================================="
python3 - "$R" <<'PY'
import json, os, sys
R = sys.argv[1]
p = os.path.join(R, ".softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json")
d = json.load(open(p))
d["case_id"] = "A2-34-RD5-INFLATION-PROBE"
out = os.path.join(R, ".softhouse/vectors/ledger/A2-34-RD5-INFLATION-PROBE.json")
json.dump(d, open(out, "w"), indent=2, ensure_ascii=False)
print("  planted", out)
PY
run rd5
expect_line rd5 "RD-5" "LEDGER parity vectors"
grep -aF "LEDGER parity vectors" "$LOG/rd5.txt"
grep -aF "LEDGER money cells" "$LOG/rd5.txt"
rm -f $V/A2-34-RD5-INFLATION-PROBE.json
echo

echo "=================================================================="
echo "RD-6 — the gl_account_type EXCLUSION is CLOSED. Exclude a SECOND cell"
echo "       and the vector must be INADMISSIBLE, not silently ungraded."
echo "=================================================================="
F=$V/LDG-01-manual-je-3leg-minor-units.json
/usr/bin/sed -i '' 's/"gl_account_type"$/"gl_account_type", "amount_minor"/' "$F"
prove_applied "$F" '"gl_account_type", "amount_minor"'
run rd6
expect_line rd6 "RD-6" "amount_minor"
grep -aiF "inadmissible" "$LOG/rd6.txt" | head -8
revert
echo

echo "=================================================================="
echo "RD-7 — the _note requirement is ENFORCED, not trusted. Strip the word"
echo "       glAccountType from LDG-01's note while keeping the exclusion."
echo "=================================================================="
F=$V/LDG-01-manual-je-3leg-minor-units.json
python3 - "$F" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["_note"] = "note deliberately stripped by A2-34 RD-7"
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
PY
prove_applied "$F" 'note deliberately stripped by A2-34 RD-7'
run rd7
grep -aiF "inadmissible" "$LOG/rd7.txt" | head -8
expect_line rd7 "RD-7" "inadmissible"
revert
echo

echo "=================================================================="
echo "RD-8 — a DECLARED INVARIANT EXEMPTION on a ledger vector must be refused"
echo "       (A2-15's counter-claim 1 rests on this being a real default-deny)."
echo "=================================================================="
F=$V/LDG-02-repayment-split-4leg-minor-units.json
python3 - "$F" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["invariant_exemptions"] = [{"invariant": "splits_sum_to_whole",
                              "reason": "A2-34 RD-8 planted exemption"}]
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
PY
prove_applied "$F" 'A2-34 RD-8 planted exemption'
run rd8
grep -aiF "exemption" "$LOG/rd8.txt" | head -10
expect_line rd8 "RD-8" "ADMITS NONE"
revert
echo

echo "=================================================================="
echo "RD-9 — HEADER-ACCOUNT ACCEPTANCE. A port that REFUSES a summary-account"
echo "       posting must go RED against LDG-04 (never 'improve on' the oracle)."
echo "=================================================================="
run rd9 --ledger-impl ledger-wrong-header-refusing
grep -aF "LDG-04" "$LOG/rd9.txt" | head -6
expect_line rd9 "RD-9" "LDG-04"
echo

echo "=================================================================="
echo "REVERT PROOF + CONTROL 1"
echo "=================================================================="
END_DIGEST=$(digest)
echo "END ledger vector digest:   $END_DIGEST"
if [ "$START_DIGEST" = "$END_DIGEST" ]; then echo "  OK   revert VERIFIED byte-identical"; PASS=$((PASS+1));
else echo "  ***  REVERT FAILED — the ledger vector set moved"; FAIL=$((FAIL+1)); fi
git status --porcelain .softhouse/vectors/ | head
run control1
expect_line control1 "control1" "VERDICT: PASS (exit 0)"
expect_line control1 "control1" "ledger parity           PASS 4    FAIL 0"
echo
echo "=================================================================="
echo "A2-34 RED DRIVES: $PASS assertion(s) OK, $FAIL failed"
echo "transcripts under $LOG/"
echo "=================================================================="
