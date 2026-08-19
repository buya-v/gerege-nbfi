#!/usr/bin/env python3
"""T46 -- read the A-3 / A-5 captures and say which input supplied the money.

Reads ONLY committed raw response bytes.  Every number is parsed with
`json.load(..., parse_float=Decimal)`, so the wire text is preserved digit for digit and no
binary float is ever constructed (T44 finding T44-X1).

No expected value is authored here.  The two candidate readings for each capture are stated
by `bin/t46-mkcalcs.py` BEFORE the run; this script computes each reading exactly from
already-observed quantities (the definition's `m_charge.amount`, transcribed from
`out/attested/attestation.json`, and the period's own observed interest / principal) and
reports which one the oracle's own output matches.
"""
import json
import pathlib
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

CH = pathlib.Path(__file__).resolve().parent.parent
OUT = CH / "out" / "t46"
REQ = CH / "req"
ATT = CH / "out" / "attested" / "attestation.json"


def load(p):
    return json.loads(pathlib.Path(p).read_text(), parse_float=Decimal)


def defs():
    a = load(ATT)
    return {c["id"]: c for c in a["charges_as_persisted"]}


def req_amount(cid):
    """The request's charge amount, as EXACT TEXT off the request bytes."""
    text = (REQ / f"calc-{cid}.json").read_text()
    doc = json.loads(text, parse_float=Decimal)
    return doc["charges"][0]["chargeId"], doc["charges"][0]["amount"]


def main():
    definitions = defs()
    files = sorted(OUT.glob("T46-CH-*-raw.json"))
    print("T46 -- A-3: which input supplies the charge money?  (request vs m_charge definition)")
    print()

    for f in files:
        cid = f.name[: -len("-raw.json")]
        charge_id, r_amt = req_amount(cid)
        d_amt = Decimal(definitions[charge_id]["amount"])
        calc = definitions[charge_id]["charge_calculation_enum"]
        time_enum = definitions[charge_id]["charge_time_enum"]
        is_pen = definitions[charge_id]["is_penalty"]
        doc = load(f)

        disb = doc["periods"][0]
        p1 = doc["periods"][1]
        interest1 = p1["interestDue"]
        principal = disb["principalDisbursed"]

        print(f"== {cid}")
        print(f"   charge id {charge_id}  (time_enum {time_enum}, calc_enum {calc}, "
              f"penalty {is_pen})")
        print(f"   definition m_charge.amount : {d_amt}")
        print(f"   request    charges[0].amount: {r_amt}")

        # --- the two readings, each computed from OBSERVED quantities only
        if calc == 1:            # FLAT
            base, base_label = Decimal(1), "flat"
            pred_def = d_amt
            pred_req = r_amt
        elif calc == 2:          # PERCENT OF AMOUNT
            base, base_label = principal, "principal disbursed"
            pred_def = base * d_amt / Decimal(100)
            pred_req = base * r_amt / Decimal(100)
        elif calc == 3:          # PERCENT OF AMOUNT PLUS INTEREST
            base = p1["principalDue"] + interest1
            base_label = "period-1 principal + interest"
            pred_def = base * d_amt / Decimal(100)
            pred_req = base * r_amt / Decimal(100)
        elif calc == 4:          # PERCENT OF INTEREST
            base, base_label = interest1, "period-1 interest"
            pred_def = base * d_amt / Decimal(100)
            pred_req = base * r_amt / Decimal(100)
        else:
            raise SystemExit(f"unhandled calc enum {calc}")

        if time_enum == 1:       # DISBURSEMENT: the money lands on the disbursement row
            observed = disb.get("feeChargesDue")
            where = "disbursement row feeChargesDue"
        elif is_pen:
            observed = p1.get("penaltyChargesDue")
            where = "period-1 penaltyChargesDue"
        else:
            observed = p1.get("feeChargesDue")
            where = "period-1 feeChargesDue"

        print(f"   base ({base_label}) : {base}")
        print(f"   if DEFINITION governs -> {pred_def}")
        print(f"   if REQUEST    governs -> {pred_req}")
        print(f"   OBSERVED {where} : {observed}")

        def matches(pred):
            return (observed == pred
                    or observed == pred.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    or observed == pred.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))

        m_def, m_req = matches(pred_def), matches(pred_req)
        if m_req and not m_def:
            verdict = "REQUEST governs"
        elif m_def and not m_req:
            verdict = "DEFINITION governs"
        elif m_def and m_req:
            verdict = "INDISTINGUISHABLE (the two readings coincide -- this shape grades nothing)"
        else:
            verdict = "NEITHER reading reproduces the observation -- investigate"
        print(f"   VERDICT: {verdict}")

        # --- A-5: is this a half-cent tie, and which way did it go?
        exact = pred_req if m_req or not m_def else pred_def
        scaled = exact * 1000
        if scaled == scaled.to_integral_value() and int(scaled) % 10 == 5:
            hu = exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            he = exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
            print(f"   HALF-CENT TIE: exact value {exact} "
                  f"| HALF_UP -> {hu} | HALF_EVEN -> {he} | OBSERVED {observed} "
                  f"=> {'HALF_UP' if observed == hu else 'HALF_EVEN' if observed == he else 'NEITHER'}")
        print()

    print("Every number above is either a raw response leaf, a transcribed m_charge row, or an")
    print("exact Decimal computation over those two.  No float was constructed.")


if __name__ == "__main__":
    main()
