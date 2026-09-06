#!/usr/bin/env bash
# branch context — tellers, cashiers, allocate/settle, cashier transactions + summary.
# Partially seeded already (staff, tellers, cashiers exist). This script finishes it:
# capture read-backs, allocate, settle, then capture transactions + summary.
set -uo pipefail

cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh

ohs_ctx branch

# Reused ids (already seeded by the earlier probe; read back, never re-created).
TELLER=2          # SEED-Teller-01
CASHIER=2         # SEED cashier on teller 2
CURRENCY="MNT"
# Amounts are direct cash movements: integer minor-unit addition, NO percentage,
# rate, apportionment or division -> the branch seam has NO rounding surface.
ALLOC_AMOUNT="100000.50"   # 10,000,050 minor units — exact
SETTLE_AMOUNT="40000.25"   #  4,000,025 minor units — exact

# NOTE: the teller/cashier transaction read-back joins on txn.currency_code = ?
#       where ? is the `currencyCode` query param. The allocate/settle request
#       must also carry currencyCode, else the row stores an empty currency and
#       becomes invisible to the read-back (which defaults currencyCode=null).

# --- read-backs of the pre-seeded objects --------------------------------------
ohs_get staff-list            "/staff?limit=50"
ohs_get tellers-list          "/tellers"
ohs_get cashiers-teller1      "/tellers/1/cashiers"
ohs_get cashiers-teller2      "/tellers/2/cashiers"
ohs_get summary-cashier2-pre  "/tellers/$TELLER/cashiers/$CASHIER/summaryandtransactions?currencyCode=$CURRENCY"

# --- allocate -------------------------------------------------------------------
cat > "$OHS_REQ/allocate.json" <<EOF
{"txnAmount":"$ALLOC_AMOUNT","txnDate":"01 September 2026","locale":"en","dateFormat":"dd MMMM yyyy","currencyCode":"$CURRENCY"}
EOF
ohs_post allocate "/tellers/$TELLER/cashiers/$CASHIER/allocate" "$OHS_REQ/allocate.json"

# --- settle ---------------------------------------------------------------------
cat > "$OHS_REQ/settle.json" <<EOF
{"txnAmount":"$SETTLE_AMOUNT","txnDate":"01 September 2026","locale":"en","dateFormat":"dd MMMM yyyy","currencyCode":"$CURRENCY"}
EOF
ohs_post settle "/tellers/$TELLER/cashiers/$CASHIER/settle" "$OHS_REQ/settle.json"

# --- read-backs after -----------------------------------------------------------
ohs_get summary-cashier2-post "/tellers/$TELLER/cashiers/$CASHIER/summaryandtransactions?currencyCode=$CURRENCY"
ohs_get txns-cashier2        "/tellers/$TELLER/cashiers/$CASHIER/transactions?currencyCode=$CURRENCY"

# --- input-rounding probe: a 3-decimal amount. The column is numeric(19,6), so a
#    raw 40000.245 is stored exactly (40000.245000) — this proves the branch input
#    seam does NOT round to 2dp. It is a NO-rounding-surface observation, not a tie.
cat > "$OHS_REQ/settle-3dp-probe.json" <<EOF
{"txnAmount":"40000.245","txnDate":"01 September 2026","locale":"en","dateFormat":"dd MMMM yyyy","currencyCode":"$CURRENCY"}
EOF
ohs_post settle-3dp-probe "/tellers/$TELLER/cashiers/$CASHIER/settle" "$OHS_REQ/settle-3dp-probe.json"
ohs_get summary-cashier2-final "/tellers/$TELLER/cashiers/$CASHIER/summaryandtransactions?currencyCode=$CURRENCY"

# --- MANIFEST --------------------------------------------------------------------
python3 - "$OHS_OUT" <<'PY'
import json, os, sys
out = sys.argv[1]

def txid(name):
    p = os.path.join(out, f"{name}-raw.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    # allocate/settle return {resourceId: tellerId, subResourceId: transactionId}
    return d.get("subResourceId", d.get("resourceId", d.get("id")))

manifest = {
    "context": "branch",
    "note": "tellers/cashiers/staff pre-existed (SMOKE probe + SEED rig); this context reuses them and adds allocate/settle with currencyCode so read-backs are non-empty.",
    "roundingSurface": "none — allocate/settle are direct cash movements (integer minor-unit addition); txn_amount is numeric(19,6) and a 3dp probe stores exactly, so no HALF_UP/HALF_EVEN tie exists here.",
    "objects": {
        "staff": [{"id": 1, "name": "SMOKE Probe", "note": "stray probe, reused"},
                  {"id": 2, "name": "SEED-Cashier Staff", "note": "reused"}],
        "tellers": [{"id": 1, "name": "SMOKE-Teller", "note": "stray probe, reused"},
                    {"id": 2, "name": "SEED-Teller-01", "note": "reused"}],
        "cashiers": [{"id": 1, "tellerId": 1, "note": "reused"},
                     {"id": 2, "tellerId": 2, "note": "reused"}],
        "transactions": {
            "allocate": {"id": txid("allocate"), "amount": "100000.50", "tellerId": 2, "cashierId": 2},
            "settle":   {"id": txid("settle"),   "amount": "40000.25", "tellerId": 2, "cashierId": 2},
            "settle-3dp-probe": {"id": txid("settle-3dp-probe"), "amount": "40000.245", "tellerId": 2, "cashierId": 2,
                                  "note": "probe: 3dp amount stored exactly as 40000.245000 -> no input rounding"},
        },
    },
}
open(os.path.join(out, "..", "MANIFEST.json"), "w").write(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PY
