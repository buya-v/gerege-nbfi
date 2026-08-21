#!/usr/bin/env python3
"""A2-11 — verify A2-7's contract-shape claims from MY OWN re-observed bytes.

P-25: no floating point anywhere. Every json.load carries parse_float=Decimal.
Nothing here is synthesised; it only reads bytes the oracle returned.
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

OBS = Path(__file__).resolve().parent / "obs"

fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("  -- " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def load(name):
    with open(OBS / name, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"), parse_float=Decimal)


print("=== (a) write/read field-name asymmetry on GET /loanproducts/46 ===")
p46 = load("a2-11-get-loanproduct-46.json")
am = p46["accountingMappings"]
print("  accountingMappings keys:", sorted(am))

WRITE_TO_READ = {
    "fundSourceAccountId": "fundSourceAccount",
    "loanPortfolioAccountId": "loanPortfolioAccount",
    "transfersInSuspenseAccountId": "transfersInSuspenseAccount",
    "interestOnLoanAccountId": "interestOnLoanAccount",
    "incomeFromFeeAccountId": "incomeFromFeeAccount",
    "incomeFromPenaltyAccountId": "incomeFromPenaltyAccount",
    "incomeFromRecoveryAccountId": "incomeFromRecoveryAccount",
    "writeOffAccountId": "writeOffAccount",
    "overpaymentLiabilityAccountId": "overpaymentLiabilityAccount",
}
# the request bytes A2-7 actually POSTed
REQ = Path(__file__).resolve().parents[2] / "capture" / "tierA-a2" / "req" / "a2-7-prod-210-cash-nine-mandatory.json"
with open(REQ, "rb") as fh:
    req = json.loads(fh.read().decode("utf-8"), parse_float=Decimal)

check("all nine WRITE names present in the POST body and NONE of them in the read",
      all(w in req for w in WRITE_TO_READ) and not any(w in am for w in WRITE_TO_READ))
check("all nine READ names present in accountingMappings and NONE of them in the POST body",
      all(r in am for r in WRITE_TO_READ.values()) and not any(r in req for r in WRITE_TO_READ.values()))
for w, r in sorted(WRITE_TO_READ.items()):
    check(f"    {w} (write, id {req[w]}) -> {r} (read)", am[r]["id"] == req[w],
          f"read id={am[r]['id']}")

print()
print("=== the read value is an OBJECT with exactly {id,name,glCode} ===")
for k, v in sorted(am.items()):
    check(f"  {k} keys == {{id,name,glCode}}", isinstance(v, dict) and set(v) == {"id", "name", "glCode"},
          str(sorted(v)) if isinstance(v, dict) else repr(v))
check("no 'type' key anywhere in accountingMappings",
      not any("type" in v for v in am.values()))
check("no 'usage' key anywhere in accountingMappings",
      not any("usage" in v for v in am.values()))
check("no 'disabled' / 'manualEntriesAllowed' key anywhere in accountingMappings",
      not any(("disabled" in v or "manualEntriesAllowed" in v) for v in am.values()))

print()
print("=== unmapped optional slots are ABSENT, not null ===")
raw46 = (OBS / "a2-11-get-loanproduct-46.json").read_bytes().decode("utf-8")
for opt in ("goodwillCreditAccount", "chargeOffExpenseAccount"):
    check(f"  {opt} absent from accountingMappings", opt not in am)
    check(f"  {opt} does not occur in the raw bytes at all", opt not in raw46)
print("  ... while the COLLECTION-valued mapping fields are PRESENT with value null:")
for coll in ("paymentChannelToFundSourceMappings", "feeToIncomeAccountMappings", "penaltyToIncomeAccountMappings"):
    check(f"  {coll} present and null", coll in p46 and p46[coll] is None, repr(p46.get(coll, "<absent>")))

print()
print("=== product 22: sparse/slot-keyed, one extra key vs 46 ===")
p22 = load("a2-11-get-loanproduct-22.json")
am22 = p22["accountingMappings"]
print("  22 keys:", sorted(am22))
check("  22 == 46's keys plus exactly {goodwillCreditAccount}",
      set(am22) - set(am) == {"goodwillCreditAccount"} and set(am) - set(am22) == set())
check("  22 goodwillCreditAccount is gl 14 / glCode 50200",
      am22["goodwillCreditAccount"]["id"] == 14 and am22["goodwillCreditAccount"]["glCode"] == "50200",
      str(am22["goodwillCreditAccount"]))
check("  22 paymentChannelToFundSourceMappings is a non-empty LIST of {paymentType,fundSourceAccount}",
      isinstance(p22["paymentChannelToFundSourceMappings"], list)
      and len(p22["paymentChannelToFundSourceMappings"]) == 1
      and set(p22["paymentChannelToFundSourceMappings"][0]) == {"paymentType", "fundSourceAccount"},
      json.dumps(p22["paymentChannelToFundSourceMappings"]))
check("  22 DEFAULT fundSourceAccount is gl 2 (the retyped one), override is gl 16",
      am22["fundSourceAccount"]["id"] == 2
      and p22["paymentChannelToFundSourceMappings"][0]["fundSourceAccount"]["id"] == 16,
      f"default={am22['fundSourceAccount']}, override={p22['paymentChannelToFundSourceMappings'][0]['fundSourceAccount']}")

print()
print("=== product 28: accrual shape, thirteen keys, three receivables ===")
p28 = load("a2-11-get-loanproduct-28.json")
am28 = p28["accountingMappings"]
print("  28 keys (%d):" % len(am28), sorted(am28))
check("  28 accountingRule is accrual periodic",
      p28["accountingRule"]["id"] == 3 and p28["accountingRule"]["code"] == "accountingRuleType.accrual.periodic",
      str(p28["accountingRule"]))
check("  28 has exactly thirteen keys", len(am28) == 13, str(len(am28)))
check("  28 carries the three receivables",
      {"receivableInterestAccount", "receivableFeeAccount", "receivablePenaltyAccount"} <= set(am28))

print()
print("=== gl 2 is INCOME at the contract boundary, but products serve it silently ===")
gl2 = load("a2-11-get-glaccount-2.json")
check("  GET /glaccounts/2 glCode 10100, name 'Fund Source', type INCOME",
      gl2["glCode"] == "10100" and gl2["name"] == "Fund Source" and gl2["type"]["value"] == "INCOME",
      f"{gl2['glCode']} / {gl2['name']} / {gl2['type']}")
check("  nameDecorated is '....Fund Source' (four dots per level)",
      gl2.get("nameDecorated") == "....Fund Source", repr(gl2.get("nameDecorated")))
check("  the GL read DOES expose type and usage as {id,code,value} objects",
      set(gl2["type"]) == {"id", "code", "value"} and set(gl2["usage"]) == {"id", "code", "value"})
check("  'hierarchy' is NOT returned by the GL REST read", "hierarchy" not in gl2, str(sorted(gl2)))

print()
print("=== how many of the 26 products carry gl 2 in the DEFAULT FUND_SOURCE slot? ===")
plist = load("a2-11-get-loanproducts-list.json")
print("  product ids:", sorted(p["id"] for p in plist))
check("  the list holds 26 products, ids 1-24, 27, 28, 46",
      sorted(p["id"] for p in plist) == list(range(1, 25)) + [27, 28, 46],
      str(len(plist)) + " products")

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
