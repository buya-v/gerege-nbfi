#!/usr/bin/env python3
"""Build `predicted.json` for capture pass 3i — task T74.

Every number this writes is either (a) transcribed from an OBSERVATION somebody
else already made of the reference oracle (Fineract) and committed to `main`, or
(b) derived from the pinned Fineract source and labelled as derived. Nothing here
is an observation of pass 3i, which has not run when this file is written.

Sources, named per prediction so a reader can check each one separately:

  T21v2-B   `.softhouse/reviews/t21v2/t21v2-probe-oracle-out.txt` section B —
            MNT 5,000,000 / 18 x 18.5% at currencyDecimalPlaces 0,
            CurrencyData.inMultiplesOf null (arm A) vs 100 (arm B), at
            (19, HALF_UP), transcribed by extract-t21v2-AB.py.
  T21v2-2   `.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt` — the
            36 x 16.8% precision sweep, MNT, decimalPlaces 2, inMultiplesOf null.
  SOURCE    derived by reading the pinned Fineract checkout at
            426a23544e8426a38ae43ae404670a0a7e85b9eb. Cited inline.

Usage: python3 build-prediction.py <section-B.json> <predicted.json>
"""
import json
import sys

# T21v2-2, the 36 x 16.8% sweep. principal -> (p19 total interest, p12 total interest,
# p19 total repayment, p12 total repayment), exactly as that transcript printed them.
E_SWEEP = {
    "4":    ("1.14", "1.13", "5.14", "5.13"),
    "59":   ("16.51", "16.52", "75.51", "75.52"),
    "72":   ("20.14", "20.13", "92.14", "92.13"),
    "340":  ("95.15", "95.16", "435.15", "435.16"),
    "426":  ("119.18", "119.20", "545.18", "545.20"),
    "6940": ("1942.65", "1942.66", "8882.65", "8882.66"),
}
E_IDS = {"4": "T74-E-P4", "59": "T74-E-P59", "72": "T74-E-P72",
         "340": "T74-E-P340", "426": "T74-E-P426", "6940": "T74-E-P6940"}


def main(sectionb_path, out_path):
    ab = json.load(open(sectionb_path, encoding='utf-8'))

    pred = {
        "schema": "gerege.capture.prediction/v1",
        "pass": "3i",
        "task": "T74",
        "registered_before_capture": True,
        "note": (
            "REGISTERED BEFORE THE CAPTURE RAN — pattern P-9. This file and PREDICTION.md were "
            "committed to branch softhouse/T74-pathA-multiplesof one commit BEFORE "
            "run-pass3i.sh was executed. check-prediction.py grades the capture against it and "
            "reports every mismatch. A refuted prediction is a RESULT, not a failure, and the "
            "handoff reports it as one."),

        # ---------------------------------------------------------------------------
        # 1. IDENTITIES. `observed` blocks that must be equal cell for cell.
        # ---------------------------------------------------------------------------
        "identities": [
            {"case": "T74-A2-DP0-INST100", "equals": "T74-A0-DP0-NONE",
             "basis": "SOURCE",
             "why": "LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext) "
                    "at LoanApplicationTerms.java:579-607 builds exclusively through Builder and "
                    "contains ZERO occurrences of 'MultiplesOf'; the Builder has no setter for "
                    "installmentAmountInMultiplesOf and the field's only assignment is at :828, in "
                    "a positional constructor this path never reaches. So the model's "
                    "installmentAmountInMultiplesOf is null whatever the caller passes, "
                    "applyInstallmentAmountInMultiplesOf (ProgressiveEMICalculator.java:1763) "
                    "returns its argument unchanged, and channel 2 is INERT on the Path A seam."},
            {"case": "T74-A3-DP0-BOTH100", "equals": "T74-A1-DP0-CUR100",
             "basis": "SOURCE",
             "why": "same reason: adding the installment field on top of the currency field adds "
                    "nothing, because the installment field never arrives."},
            {"case": "T74-B1-DP2-CUR100", "equals": "P-CAL-MNT5M",
             "basis": "SOURCE",
             "why": "Money.java:48 requires currency.getDecimalPlaces() == 0. MNT is minor unit 2, "
                    "so channel 1 is shut and CurrencyData.inMultiplesOf is inert at production."},
            {"case": "T74-B2-DP2-INST100", "equals": "P-CAL-MNT5M",
             "basis": "SOURCE",
             "why": "channel 2 inert (the seam drops the field) AND channel 1 shut (dp = 2). "
                    "This is the arm that says the PRODUCTION corpus grades neither input."},
            {"case": "T74-B3-DP2-BOTH100", "equals": "P-CAL-MNT5M",
             "basis": "SOURCE", "why": "both channels off, for the two reasons above."},
            {"case": "T74-C1-DP0-CUR1", "equals": "T74-A0-DP0-NONE",
             "basis": "SOURCE",
             "why": "the gate opens (1 > 0) and roundToMultiplesOf(x, 1) is "
                    "x.divide(1, 0, HALF_UP).multiply(1) = round(x) at scale 0 — and the "
                    "constructor's next statement is setScale(0, ...) anyway, so rounding to "
                    "multiples of one is arithmetically inert at zero decimal places."},
            {"case": "T74-C2-DP0-CUR0", "equals": "T74-A0-DP0-NONE",
             "basis": "SOURCE",
             "why": "third conjunct of Money.java:48, currency.getInMultiplesOf() > 0, is false."},
            {"case": "T74-C3-DP0-CURNEG", "equals": "T74-A0-DP0-NONE",
             "basis": "SOURCE",
             "why": "same conjunct on the negative side; Money.java:153 is a second guard behind it."},
            {"case": "T74-D2-DP0-SMALL-INST1000", "equals": "T74-D0-DP0-SMALL-NONE",
             "basis": "SOURCE",
             "why": "channel 2 inert on this seam, so safeRoundingForEMI's zero-guard "
                    "(ProgressiveEMICalculator.java:1770-1776) is never reached at all."},
        ],

        # ---------------------------------------------------------------------------
        # 2. DIFFERENCES. `observed` blocks that must NOT be equal.
        # ---------------------------------------------------------------------------
        "differences": [
            {"case": "T74-A1-DP0-CUR100", "differsFrom": "T74-A0-DP0-NONE", "basis": "T21v2-B",
             "why": "channel 1 fires: dp = 0, inMultiplesOf = 100 > 0."},
            {"case": "T74-C4-DP0-CUR7", "differsFrom": "T74-A0-DP0-NONE", "basis": "SOURCE"},
            {"case": "T74-C5-DP0-CUR1000", "differsFrom": "T74-A0-DP0-NONE", "basis": "SOURCE"},
            {"case": "T74-D1-DP0-SMALL-CUR1000", "differsFrom": "T74-D0-DP0-SMALL-NONE",
             "basis": "SOURCE"},
            {"case": "T74-A0-DP0-NONE", "differsFrom": "P-CAL-MNT5M", "basis": "SOURCE",
             "why": "same request but currencyDecimalPlaces 0 against 2 — different quantization "
                    "scale, so this pair is expected to differ for a reason that has nothing to "
                    "do with either multiples-of input."},
        ],

        # ---------------------------------------------------------------------------
        # 3. FULL SCHEDULES, cell for cell. Both arms of T21's section B.
        #    This is the sharp half: if pass 3i reproduces them with the two fields
        #    SEPARATED, then T21's observation is confirmed AND attributed.
        # ---------------------------------------------------------------------------
        "full_schedules": {
            "T74-A0-DP0-NONE": {"basis": "T21v2-B arm A", "observed": ab["A"]},
            "T74-A1-DP0-CUR100": {"basis": "T21v2-B arm B", "observed": ab["B"]},
        },

        # ---------------------------------------------------------------------------
        # 4. MULTIPLE-OF STRUCTURE. Every money cell of these cases must be an exact
        #    multiple of the modulus. This is what separates channel 1 from channel 2
        #    by SCOPE: channel 1 sits in the Money constructor and therefore quantizes
        #    principal, interest, balance and totals; channel 2 touches the EMI alone
        #    and could never make the INTEREST column a multiple of anything.
        # ---------------------------------------------------------------------------
        "money_cells_are_multiples_of": [
            {"case": "T74-A1-DP0-CUR100", "modulus": 100, "basis": "SOURCE"},
            {"case": "T74-A3-DP0-BOTH100", "modulus": 100, "basis": "SOURCE"},
            {"case": "T74-C4-DP0-CUR7", "modulus": 7, "basis": "SOURCE"},
            {"case": "T74-C5-DP0-CUR1000", "modulus": 1000, "basis": "SOURCE"},
            {"case": "T74-D1-DP0-SMALL-CUR1000", "modulus": 1000, "basis": "SOURCE"},
        ],

        # ---------------------------------------------------------------------------
        # 5. TOTALS. Group E, from T21's own precision sweep.
        # ---------------------------------------------------------------------------
        "totals": {},

        # ---------------------------------------------------------------------------
        # 6. SHARP CLAIMS — each one wrong on its own if the prediction is wrong.
        # ---------------------------------------------------------------------------
        "sharp_claims": [
            {"id": "S1",
             "case": "T74-D1-DP0-SMALL-CUR1000",
             "claim": "totalInterestAmount == '0' and every REPAYMENT row's interest == '0'",
             "basis": "SOURCE",
             "derivation":
                 "Period-1 interest on MNT 1,000 at a 30/360 monthly factor of 0.216/12 = 0.018 is "
                 "18 currency units. Money's constructor quantizes it: 18/1000 = 0.018, "
                 "divide(1000, 0, HALF_UP) = 0, times 1000 = 0 [Money.java:150-157]. Every later "
                 "period's interest is smaller still."},
            {"id": "S2",
             "case": "T74-D1-DP0-SMALL-CUR1000",
             "claim": "exactly ONE repayment row carries non-zero principal, and it is period 6 "
                      "with principal '1000', interest '0', total '1000' and balance '0'; "
                      "periods 1..5 each carry principal '0', interest '0', total '0' and "
                      "balance '1000'",
             "basis": "SOURCE",
             "derivation":
                 "The level installment is ~177.5, which quantizes to 0 under channel 1 and has NO "
                 "safeRoundingForEMI fallback, so every EMI starts at 0 and duePrincipal = "
                 "EMI - dueInterest = 0 [RepaymentPeriod.java:345-350]. All six periods are then "
                 "vacuously isFullyPaid, so calculateLastUnpaidRepaymentPeriodEMI takes the "
                 ":1178-1181 fallback branch (no unpaid period AND totalPaidPrincipal zero) and "
                 "picks the LAST period, whose outstanding balance is 1,000 > 0. diff = 1000 + 0 "
                 "+ 0 + 0 - 0 = 1000, so its EMI becomes 1000 [:1202-1210]. The smoothing loop "
                 "then does not fire: getEmiAdjustment scans for a pair in which NEITHER period is "
                 "fully paid [:1779-1787], the only not-fully-paid period is the last one, so the "
                 "scan falls through to the :1788 fallback whose emiDifference is zero and "
                 "shouldBeAdjusted() is false [EmiAdjustment.java:32-35]."},
            {"id": "S3",
             "case": "T74-D1-DP0-SMALL-CUR1000",
             "claim": "at least five of the six mechanism rows report emi == '0.00' or '0' — the "
                      "safeRoundingForEMI zero-guard does NOT protect them",
             "basis": "SOURCE",
             "derivation":
                 "That guard is channel 2's (ProgressiveEMICalculator.java:1770-1776) and the Path "
                 "A seam never delivers the field that reaches it. Channel 1, in the Money "
                 "constructor, has no equivalent. THIS IS THE OBSERVATION THAT TELLS THE TWO "
                 "MECHANISMS APART: if the operative rounding were channel 2's, a positive EMI "
                 "could not round to zero."},
            {"id": "S4",
             "case": "ALL",
             "claim": "pathIdentity.identical is true on all 36 cases, and every case's "
                      "ambientMoneyHelperPrecision is 19 with rounding-mode ordinal 4",
             "basis": "SOURCE",
             "derivation":
                 "MoneyHelper.PRECISION = 19 is a compile-time constant and getMathContext() "
                 "returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35,91-93]; "
                 "every case initialises its tenant at ordinal 4."},
            {"id": "S5",
             "case": "T74-A1-DP0-CUR100",
             "claim": "period 1 interest is '77100', not '77083' — the value channel 1 produces "
                      "by rounding 77,083.33 to the NEAREST multiple of 100 under HALF_UP, not by "
                      "flooring it",
             "basis": "T21v2-B + SOURCE",
             "derivation":
                 "5,000,000 x 0.185/12 = 77,083.33; 77083.33/100 = 770.8333, HALF_UP at scale 0 is "
                 "771, times 100 is 77,100. A port that FLOORED would emit 77,000 and a port that "
                 "used HALF_EVEN would still emit 77,100 here — so this cell separates "
                 "nearest-vs-floor but NOT HALF_UP-vs-HALF_EVEN, and the prediction claims only "
                 "the first."},
            {"id": "S6",
             "case": "T74-E-*",
             "claim": "all six group-E production-precision cases differ from their precision-12 "
                      "companion in at least one money cell",
             "basis": "T21v2-2",
             "derivation":
                 "T21's sweep recorded DIFFERENT on all six, at principals from MNT 4.00 upward. "
                 "If any pair comes back IDENTICAL, T21 section 6.2's refutation of the "
                 "size-threshold claim is weakened and the handoff must say so."},
        ],
    }

    for principal, (i19, i12, r19, r12) in E_SWEEP.items():
        pid = E_IDS[principal]
        pred["totals"][pid] = {"basis": "T21v2-2",
                               "totalInterestAmount": i19, "totalRepaymentAmount": r19}
        pred["totals"][pid + "-p12"] = {"basis": "T21v2-2",
                                        "totalInterestAmount": i12, "totalRepaymentAmount": r12}

    json.dump(pred, open(out_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print("wrote %s: %d identities, %d differences, %d full schedules, %d multiple-of claims, "
          "%d totals, %d sharp claims"
          % (out_path, len(pred["identities"]), len(pred["differences"]),
             len(pred["full_schedules"]), len(pred["money_cells_are_multiples_of"]),
             len(pred["totals"]), len(pred["sharp_claims"])))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
