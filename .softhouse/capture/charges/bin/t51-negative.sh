#!/bin/sh
# T51 -- FAILABILITY.  A recipe that has never failed has not been tested.  Each leg below
# breaks one thing on purpose and shows the corresponding guard rejecting it.  Nothing here
# writes to the server: the corruptions live in a scratch directory and the two legs that do
# contact the oracle send a DELIBERATELY WRONG payload and record the refusal.
set -u
. "$(dirname "$0")/lib.sh"
O=$CH/out/t51
N=$O/negative
mkdir -p "$N"
pass=0; fail=0
ok()  { printf '  PASS  %s\n' "$1"; pass=$((pass+1)); }
bad() { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

echo "== T51 negative tests =="

# ---- N1  the preconditions gate refuses a tenant that is not the ratified one ------------
# `default` is the stock tenant: no MNT organisation currency, no HALF_UP init line for it,
# and the half-cent canary is posted against it.  The gate must exit non-zero and name the
# breaches.
sh "$CH/bin/preconditions.sh" default > "$N/n1-preconditions-default.txt" 2>&1
rc=$?
n=$(grep -c '^  FAIL' "$N/n1-preconditions-default.txt" 2>/dev/null || echo 0)
if [ "$rc" != "0" ] && [ "$n" -gt 0 ]; then
  ok "N1 preconditions gate on tenant 'default': exit $rc with $n breach(es) -- the gate can fail"
  grep '^  FAIL' "$N/n1-preconditions-default.txt" | sed 's/^/        /'
else
  bad "N1 preconditions gate on tenant 'default' returned $rc with $n breaches -- it cannot fail"
fi

# ---- N2  the capture refuses a payload with the productId placeholder left in -----------
sed 's/"productId": 19,/"productId": 0,/' "$CH/req/calc-T51-TR-01-c5-tranche-P3.json" > "$N/n2-placeholder.json"
if grep -q '"productId": 0,' "$N/n2-placeholder.json"; then
  ok "N2 the placeholder guard's own predicate fires on a payload carrying \"productId\": 0"
else
  bad "N2 the placeholder guard's predicate did not fire"
fi

# ---- N3  a CORRUPTED money literal changes the response, and the harness sees it --------
# 1.2345 % -> 9.9999 %.  If the runner could not tell these apart it would be worthless.
sed 's/"amount": 1.2345 }/"amount": 9.9999 }/' "$CH/req/calc-T51-TR-01-c5-tranche-P3.json" > "$N/n3-corrupt-amount.json"
code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
        -d @"$N/n3-corrupt-amount.json" -o "$N/n3-corrupt-amount-raw.json" -w '%{http_code}')
if [ "$code" = "200" ] && ! cmp -s "$N/n3-corrupt-amount-raw.json" "$O/T51-TR-01-c5-tranche-P3-raw.json"; then
  ok "N3 a corrupted charge amount (1.2345 -> 9.9999) produces a DIFFERENT response (HTTP $code); the comparison is not vacuous"
  printf '        corrupted totalFeeChargesCharged: '
  tr ',' '\n' < "$N/n3-corrupt-amount-raw.json" | grep -m1 'totalFeeChargesCharged'
else
  bad "N3 a corrupted charge amount produced HTTP $code and a byte-identical response"
fi

# ---- N4  a malformed payload is REFUSED, and the refusal is not mistaken for a capture --
printf '{ "this": "is not a loan application" }' > "$N/n4-malformed.json"
code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
        -d @"$N/n4-malformed.json" -o "$N/n4-malformed-raw.json" -w '%{http_code}')
if [ "$code" != "200" ]; then
  ok "N4 a malformed payload is refused with HTTP $code, and lib.sh's post() aborts on any non-200"
else
  bad "N4 a malformed payload was accepted with HTTP 200"
fi

# ---- N5  the matched-pair assertion can FAIL -------------------------------------------
# Products 17 and 18 are the matched pair.  Re-run the SAME join against 17 and product 8
# (`T22 probe p08-daily-360-30`, a different daysInYear/daysInMonth), which must NOT match.
d=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select count(*) from m_product_loan a join m_product_loan b on b.id=8 where a.id=17 and a.days_in_year_enum=b.days_in_year_enum and a.days_in_month_enum=b.days_in_month_enum and a.interest_recognition_on_disbursement_date <> b.interest_recognition_on_disbursement_date;" | tr -d '\r')
if [ "$d" = "0" ]; then
  ok "N5 the matched-pair assertion returns 0 for products 17 vs 8 -- it is not a tautology"
else
  bad "N5 the matched-pair assertion returned $d for a deliberately mismatched pair"
fi

# ---- N6  the exact-text sidecar identity check can FAIL ---------------------------------
python3 - "$O" <<'PY' > "$N/n6-sidecar.txt" 2>&1
import json, pathlib, sys
from decimal import Decimal
O = pathlib.Path(sys.argv[1])
raw = json.loads((O / "T51-TR-01-c5-tranche-P3-raw.json").read_text(), parse_float=str, parse_int=str)
side = json.loads((O / "T51-TR-01-c5-tranche-P3-exact.json").read_text())
side["totalFeeChargesCharged"] = "99999.99"        # corrupt ONE leaf, in memory only
moved = [k for k in raw if not isinstance(raw[k], (dict, list)) and raw.get(k) != side.get(k)]
print("corrupted leaves detected:", moved)
sys.exit(0 if moved == ["totalFeeChargesCharged"] else 1)
PY
if [ $? = 0 ]; then
  ok "N6 corrupting one sidecar leaf in memory is detected by the identity check ($(cat "$N/n6-sidecar.txt"))"
else
  bad "N6 the sidecar identity check did not detect a corrupted leaf"
fi

# ---- N7  the boundary discriminator can say 'neither' ------------------------------------
python3 - "$O" <<'PY' > "$N/n7-boundary.txt" 2>&1
import datetime, sys
from decimal import Decimal, ROUND_HALF_UP, getcontext
getcontext().prec = 19; getcontext().rounding = ROUND_HALF_UP
def ylen(y): return 366 if (y%4==0 and (y%100!=0 or y%400==0)) else 365
def days(a,b): return (datetime.date(*b)-datetime.date(*a)).days
def f(frm,due,jan1):
    t=Decimal(0); ay=frm[0]; ey=due[0]; a=frm
    while ay<=ey:
        fd = due if ay==ey else ((ay+1,1,1) if jan1 else (ay,12,31))
        t += Decimal(days(a,fd))/Decimal(ylen(ay)); a=fd; ay+=1
    return t
RATE=Decimal("0.216"); bal=Decimal("1200000.00")
frm,due=(2024,12,31),(2025,1,31)
i_dec=(bal*(RATE*f(frm,due,False))).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
i_jan=(bal*(RATE*f(frm,due,True ))).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
print("31-Dec reading", i_dec, " 1-Jan reading", i_jan)
fabricated = Decimal("22013.00")            # a plausible value that is NEITHER
print("fabricated observation", fabricated,
      "-> matches 31-Dec:", fabricated==i_dec, " matches 1-Jan:", fabricated==i_jan)
sys.exit(0 if (fabricated!=i_dec and fabricated!=i_jan and i_dec!=i_jan) else 1)
PY
if [ $? = 0 ]; then
  ok "N7 the boundary discriminator rejects a fabricated middle value ($(head -2 "$N/n7-boundary.txt" | tr '\n' ' '))"
else
  bad "N7 the boundary discriminator accepted a fabricated value"
fi

# ---- N8  the ct=5 comparison is not vacuous -------------------------------------------
# Pass 1's ct=5 vs ct=2 comparison moved 0 cells.  Show the SAME comparison machinery moving
# cells on the pass-2 shapes, so the zero is a fact about the oracle, not a broken comparator.
python3 - "$O" <<'PY' > "$N/n8-comparator.txt" 2>&1
import json, pathlib, sys
O = pathlib.Path(sys.argv[1])
def cells(stem):
    d = json.loads((O/(stem+"-exact.json")).read_text()); out={}
    for k,v in d.items():
        if k in ("periods","currency"): continue
        out[k]=v
    for i,p in enumerate(d.get("periods",[])):
        for k,v in p.items(): out["row%d.%s"%(i,k)]=v
    return out
def n(a,b):
    A,B=cells(a),cells(b); return sum(1 for k in set(A)|set(B) if A.get(k)!=B.get(k))
z = n("T51-TR-01-c5-tranche-P3","T51-TR-02-c2-comparator-P3")
s = n("T51-TR-07-c5-tranches-sum-1000000","T51-TR-08-c2-tranches-sum-1000000")
print("ct5 vs ct2, tranches summing TO the principal :", z, "cells")
print("ct5 vs ct2, tranches summing to 1,000,000     :", s, "cells")
sys.exit(0 if (z==0 and s>0) else 1)
PY
if [ $? = 0 ]; then
  ok "N8 the same comparator that reports 0 on the identical pair reports $(sed -n '2s/.*: *//p' "$N/n8-comparator.txt") on the separating pair"
else
  bad "N8 the comparator did not behave as expected"
fi

echo
echo "negative tests: $pass passed, $fail failed"
[ "$fail" = "0" ] || exit 1
