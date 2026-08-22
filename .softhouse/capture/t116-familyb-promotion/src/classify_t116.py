#!/usr/bin/env python3
"""T116 — classify the capture and SCORE the registered prediction. Integer minor units only.

Reads ONLY the emitted capture JSON and prediction.json. Constructs no float anywhere: money is
parsed out of the decimal STRING the oracle emitted, by exact textual scaling to an integer count
of minor units, with an integrality assertion on every parse (P-25). `json.load` is called with
`parse_float=Decimal` so that a numeric money literal, if one ever appeared in the capture, could
not become a binary double. Nothing here divides.

Usage:  python3 classify_t116.py ../out/capture-t116-raw.json ../prediction.json
"""
import json
import sys
from decimal import Decimal

CAL = ("P-CAL-ZPA", "P-CAL-ZPB")


def minor(text):
    """Exact textual major -> integer minor units for MNT (2 dp). No float, ever."""
    if text is None:
        raise SystemExit("money field is null")
    text = str(text)
    neg = text.startswith("-")
    t = text.lstrip("-")
    whole, _, frac = t.partition(".")
    if len(frac) > 2 and set(frac[2:]) != {"0"}:
        raise SystemExit("OVER-SCALED money text %r: more fraction digits than MNT has" % text)
    frac = (frac + "00")[:2]
    v = int(whole or 0) * 100 + int(frac)
    return -v if neg else v


def load(path):
    with open(path) as fh:
        return json.load(fh, parse_float=Decimal)


rawp, predp = sys.argv[1], sys.argv[2]
doc = load(rawp)
pred = load(predp)["predictions"]

out = {"task": "T116", "gate": "G-8", "cases": {}, "predictionScore": {}}
held, refuted = [], []

for c in doc["captures"]:
    cid = c["id"]
    if cid in CAL:
        continue
    o, i = c["observed"], c["inputs"]
    disbursed = advanced = repaid = 0
    rows = 0
    rep_rows = 0
    balances = []
    interest_total = 0
    nonzero_principal_rows = []
    for p in o["periods"]:
        rows += 1
        bal = minor(p["balance"])
        balances.append(bal)
        if p["type"] == "DISBURSEMENT":
            advanced += minor(p["principal"])
            disbursed = minor(p["principal"])
        else:
            rep_rows += 1
            pr = minor(p["principal"])
            repaid += pr
            interest_total += minor(p["interest"])
            if pr != 0:
                nonzero_principal_rows.append(p["periodNumber"])
    final_balance = balances[-1]
    # FAMILY B, per gates.md's discriminator table: the principal column does NOT sum to the
    # disbursement. FAMILY A: it does sum, and only the balance column is stale.
    family = None
    if repaid != advanced:
        family = "B"
    elif final_balance != 0:
        family = "A"

    rec = {
        "n": i["numberOfRepayments"],
        "B_minor": minor(i["disbursementAmount"]),
        "annualRate": str(i["annualNominalInterestRate"]),
        "rowCount": rows,
        "repaymentRowCount": rep_rows,
        "principalAdvancedMinor": advanced,
        "principalRepaidMinor": repaid,
        "unamortizedResidualMinor": advanced - repaid,
        "finalRowBalanceMinor": final_balance,
        "balanceConstantOnEveryRow": len(set(balances)) == 1,
        "distinctBalanceValuesMinor": sorted(set(balances)),
        "repaymentRowsWithNonZeroPrincipal": nonzero_principal_rows[:8],
        "repaymentRowsWithNonZeroPrincipalCount": len(nonzero_principal_rows),
        "scheduledInterestMinor_sumOfRows": interest_total,
        "totalInterestAmountMinor": minor(o["totalInterestAmount"]),
        "totalPrincipalAmountMinor": minor(o["totalPrincipalAmount"]),
        "family": family,
    }
    out["cases"][cid] = rec

    p = pred[cid]

    def score(name, ok, detail):
        (held if ok else refuted).append("%s %s: %s" % (cid, name, detail))

    score("P1-rowcount", rep_rows == p["predictedRepaymentRowCount"],
          "%d REPAYMENT rows, predicted %d" % (rep_rows, p["predictedRepaymentRowCount"]))
    score("P2/P3-repaid", repaid == p["predictedPrincipalRepaidMinor"],
          "principal repaid %d minor, predicted %d" % (repaid, p["predictedPrincipalRepaidMinor"]))
    score("P2/P3-balance", final_balance == p["predictedFinalRowBalanceMinor"],
          "final balance %d minor, predicted %d" % (final_balance, p["predictedFinalRowBalanceMinor"]))
    score("family", (family == "B") == p["predictedFamilyB"],
          "observed family %r, predicted family B = %s" % (family, p["predictedFamilyB"]))
    if p["predictedFamilyB"]:
        score("P4-interest-on-unrepaid-principal",
              rec["totalPrincipalAmountMinor"] == 0 and rec["totalInterestAmountMinor"] > 0,
              "totalPrincipalAmount %d minor, totalInterestAmount %d minor"
              % (rec["totalPrincipalAmountMinor"], rec["totalInterestAmountMinor"]))

# P5 is an EXISTENCE claim over the population, so an EMPTY measurement REFUTES it rather than
# passing through it. That is the one-line cure for the P-22 vacuous-guard class (T114 follow-up 3).
fams = [r["family"] for r in out["cases"].values()]
p5 = ("B" in fams) and (None in fams)
(held if p5 else refuted).append(
    "POPULATION P5-existence: at least one family-B cell AND at least one clean cell — "
    "families observed %r over %d cases" % (fams, len(fams)))

out["predictionScore"] = {"held": len(held), "refuted": len(refuted),
                          "heldDetail": held, "refutedDetail": refuted}
json.dump(out, sys.stdout, indent=1, sort_keys=True)
sys.stdout.write("\n")
sys.stderr.write("HELD %d  REFUTED %d\n" % (len(held), len(refuted)))
sys.exit(1 if refuted else 0)
