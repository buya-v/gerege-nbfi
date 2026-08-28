#!/usr/bin/env bash
# T389 -- RE-ISSUE of T388's recorded recipes (the T276/T289 discipline: a reviewer of a
# capture RE-ISSUES rather than reads).
#
# WHAT IS AND IS NOT RE-ISSUED, AND WHY.
#
# T388 recorded 27 HTTP exchanges. 20 of them are state-moving POSTs (13 POST /glaccounts,
# POST /loanproducts, POST /clients, 2x POST /loans, approve, disburse, POST /runaccruals).
# RE-ISSUING ANY OF THOSE WOULD MOVE THE SHARED ORACLE A SECOND TIME and would corrupt the
# very evidence this review exists to verify. They are therefore NOT re-issued; they are
# verified by READ-BACK against the live PostgreSQL database (see
# out/T389-P0-contamination.txt and out/T389-SLOT-decode.txt), which is the stronger check
# anyway because it reads what the oracle actually PERSISTED rather than what it echoed.
#
# The 7 GETs carry no side effect and ARE re-issued here, byte-for-byte on the recorded
# method+path, against the live oracle, and diffed against the recorded .json.
#
# ONE OF THE SEVEN CANNOT MATCH, BY CONSTRUCTION, AND THAT IS NOT A DEFECT:
#   T388-P08-loan-readback-before-accrual is a POINT-IN-TIME observation taken BEFORE
#   POST /runaccruals ran. The accrual has since happened and is permanent. Re-issuing
#   GET /loans/8 today necessarily returns the AFTER state. The correct control for P08
#   is T388-A07 (the same GET taken AFTER accrual), and the test is that TODAY'S response
#   matches A07, not P08. That is asserted explicitly below rather than waved away.
set -u
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
REC=/tmp/t389scratch/.softhouse/capture/t388-accrual-capture/out
OUT="$(cd "$(dirname "$0")" && pwd)/out/reissue"
mkdir -p "$OUT"

pass=0; fail=0; expected_diff=0

# reissue NAME  "PATH"  COMPARE_AGAINST  MODE
#   MODE=must-match      : today's body must equal the recorded body
#   MODE=must-differ-ok  : a difference is EXPECTED and explained
reissue() {
  name="$1"; rpath="$2"; cmp="$3"; mode="$4"; why="${5-}"
  body="$OUT/$name.today.json"
  code=$(curl -sk -X GET "$B$rpath" -H "$A" -H "$T" -o "$body" -w '%{http_code}')
  echo "===================================================================="
  echo "RECIPE   : $name"
  echo "RE-ISSUED: GET $rpath"
  echo "HTTP     : $code   (recorded: $(cat "$REC/$name.status" 2>/dev/null))"
  echo "COMPARED : against recorded $cmp.json"
  # Normalise only key ORDER and whitespace, never values -- a value difference must show.
  python3 -c "
import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
sa=json.dumps(a,sort_keys=True,ensure_ascii=False)
sb=json.dumps(b,sort_keys=True,ensure_ascii=False)
print('IDENTICAL' if sa==sb else 'DIFFERENT')
" "$body" "$REC/$cmp.json" > "$OUT/$name.verdict" 2>&1
  v=$(cat "$OUT/$name.verdict")
  echo "VERDICT  : $v"
  if [ "$mode" = "must-match" ]; then
    if [ "$v" = "IDENTICAL" ]; then echo "RESULT   : OK -- recipe re-issues"; pass=$((pass+1))
    else echo "RESULT   : *** FAIL -- recipe did NOT re-issue ***"; fail=$((fail+1)); fi
  else
    echo "WHY      : $why"
    if [ "$v" = "DIFFERENT" ]; then echo "RESULT   : EXPECTED DIFFERENCE (declared, not hidden)"; expected_diff=$((expected_diff+1))
    else echo "RESULT   : OK -- matched anyway"; pass=$((pass+1)); fi
  fi
}

echo "T389 RE-ISSUE OF T388's 7 READ-ONLY RECIPES"
echo "oracle: $B"
echo "date  : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

# The three contract-boundary accrual readbacks -- the load-bearing ones.
reissue T388-A03-je-readback-L29 "/journalentries?transactionId=L29&transactionDetails=true" T388-A03-je-readback-L29 must-match
reissue T388-A04-je-readback-L30 "/journalentries?transactionId=L30&transactionDetails=true" T388-A04-je-readback-L30 must-match
reissue T388-A05-je-readback-L31 "/journalentries?transactionId=L31&transactionDetails=true" T388-A05-je-readback-L31 must-match

# Product and loan readbacks taken AFTER accrual -- these are steady-state and must match.
reissue T388-A06-loanproduct-63-readback "/loanproducts/63" T388-A06-loanproduct-63-readback must-match
reissue T388-A07-loan-8-readback-after-accrual "/loans/8?associations=all" T388-A07-loan-8-readback-after-accrual must-match

# The tenant business date.
reissue T388-P01-businessdate "/businessdate" T388-P01-businessdate must-match

# P08: recorded BEFORE the accrual. Compared FIRST against its own record (expected to
# differ, because the accrual is permanent), then against A07 (expected to match, because
# A07 is the same GET after the accrual).
reissue T388-P08-loan-readback-before-accrual "/loans/8?associations=all" T388-P08-loan-readback-before-accrual must-differ-ok \
  "P08 was captured BEFORE POST /runaccruals; the accrual is permanent, so this GET cannot return the pre-accrual body again. Control: the same GET must now match A07 (post-accrual), asserted above."

echo "===================================================================="
echo "RE-ISSUED OK        : $pass"
echo "EXPECTED DIFFERENCES: $expected_diff (declared)"
echo "UNEXPECTED FAILURES : $fail"
if [ "$fail" -ne 0 ]; then exit 1; fi
exit 0
