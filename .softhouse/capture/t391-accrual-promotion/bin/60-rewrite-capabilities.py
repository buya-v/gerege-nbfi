#!/usr/bin/env python3
"""T391 -- rewrite `ledger.accrual.entry`, and move product 28's unposted slots
to the row that is still false.

WHY A SCRIPT RATHER THAN A HAND EDIT: the two rows are long, the file is one
line per value, and a reviewer must be able to see EXACTLY which keys changed.
This script asserts the OLD text before replacing it, so it cannot be run twice,
cannot be run against a drifted file, and cannot silently rewrite the wrong row.
It carries no observation of its own -- every measurement it writes was taken by
capsql-readonly.sh and capget.sh and is committed under out/.

THE FOUR FALSE SENTENCES, and what replaces each:

  1. "the observations do not exist"                    -> they exist: 36 legs,
     18 of them through a receivable slot, on six transactions L29..L34.
  2. "Product 28 is the only ACCRUAL_PERIODIC product"  -> 28 AND 63.
  3. "NOT ONE JOURNAL ENTRY IN THIS TENANT ARRIVED
     THROUGH A RECEIVABLE SLOT"                         -> EIGHTEEN did.
  4. "An accrual vector needs a NEW accrual product
     on clean accounts PLUS a job run"                  -> both already exist.

  AND THE SENTENCE THAT SURVIVES BY BEING NARROWED, exactly as T388 recommended
  and T389 confirmed: "not one entry in this CORPUS". It was true when T388
  wrote it and this task is what makes it false, so it is not deleted -- it is
  carried forward as the history of the row and marked as superseded ON THE
  RECORD rather than removed from it.
"""
import json
import sys

PATH = ".softhouse/vectors/capabilities-ledger.json"

ACCRUAL_EVIDENCE = (
    "GRADED, AS OF T391, BY THREE VECTORS -- LDG-ACC-01, LDG-ACC-02 and LDG-ACC-03 -- AND THE "
    "ROW BELOW IS A REWRITE OF ONE THE HARNESS PRINTED EVERY RUN WHILE FOUR OF ITS SENTENCES "
    "WERE FALSE. Read the correction before the claim, because this row has now been wrong twice "
    "and both times the harness printed the error as measured fact. "
    "WHAT IS GRADED. Six-leg accrual journal transactions on loan 8 (client 3, product 63, "
    "ACCRUAL_PERIODIC, MNT, thirteen mappings onto thirteen clean accounts 35-47), read back at "
    "the contract boundary through GET /journalentries. Each vector grades THE SLOT: its legs "
    "carry a slot code and NO account id, the request carries product 63's complete thirteen-row "
    "acc_product_mapping table, and gl_account_id, gl_account_code and slot_name are OUTPUTS the "
    "implementation resolves. Slots 7 INTEREST_RECEIVABLE, 8 FEES_RECEIVABLE and 9 "
    "PENALTIES_RECEIVABLE on the debit side; 3 INTEREST_ON_LOANS, 4 INCOME_FROM_FEES and 5 "
    "INCOME_FROM_PENALTIES on the credit side. "
    "WHAT IS STILL NOT GRADED, and it is most of the class: ACCRUAL_UPFRONT (accounting_type 4) "
    "-- no product in this tenant uses it and no capture exists at accountingRule = 4; "
    "ACCRUAL_ACTIVITY_POSTING and the COB path -- jobs 33 and 34 are INACTIVE with a null "
    "previous_run_start_time; accrual REVERSAL; and product 63's five UNPOSTED accrual slots 6, "
    "10, 11, 12 and 13, which are recorded as structured data on ledger.slot.resolution below and "
    "printed by the harness every run. "
    "THIS IS NOT A PRECISION CLAIM. Every amount observed here is exact at two decimal places and "
    "NOT ONE LEG CARRIES A NON-ZERO THIRD DECIMAL [T391, read-only SELECT, "
    ".softhouse/capture/t391-accrual-promotion/out/T391-S01-slot-resolution.txt section 6, ZERO "
    "rows]. The production MathContext is (19, HALF_UP) and this tenant runs at the ratified "
    "HALF_UP, but nothing in these captures DISCRIMINATES precision: a port at precision 12 "
    "produces the same integers. T388 said so first and was right. "
    "[FOUR SENTENCES OF THIS ROW WERE FALSE AND ARE CORRECTED HERE, T391, from T388's observations "
    "and T391's own read-only re-measurement of the live PostgreSQL reference oracle. The harness "
    "printed all four on every run, pass or fail, as measured fact. (1) 'the observations do not "
    "exist' -- FALSE: thirty-six legs on six accrual transactions L29..L34 exist, and eighteen of "
    "them arrived through a RECEIVABLE slot. (2) 'Product 28 is the only ACCRUAL_PERIODIC product "
    "... the ONLY row with that value' -- FALSE: there are TWO, 28 with zero loans and 63 with one "
    "[T391-S01 section 9]. (3) 'NOT ONE JOURNAL ENTRY IN THIS TENANT ARRIVED THROUGH A RECEIVABLE "
    "SLOT' -- FALSE: eighteen did, six through each of slots 7, 8 and 9, all on product 63 "
    "[T391-S01 section 10]. (4) 'An accrual vector needs a NEW accrual product on clean accounts "
    "PLUS a job run' -- FALSE as a statement of remaining COST: T388 built the product and the "
    "accruals are already posted. THE COST ESTIMATE WAS ALSO WRONG IN THE OTHER DIRECTION and "
    "T352 had already said so: the periodic accrual job was ACTIVE the whole time, so no job "
    "wiring was ever needed.] "
    "[THE SENTENCE THAT SURVIVED BY BEING NARROWED, and it is now false too -- deliberately, "
    "because making it false is what this task was for. T388 promoted nothing, so it recommended "
    "keeping 'NOT ONE ENTRY IN THIS CORPUS ARRIVED THROUGH A RECEIVABLE SLOT', which was TRUE of "
    "the promoted store on 28 August 2026 and which T389 independently confirmed. T391 promoted "
    "three vectors carrying NINE receivable-slot legs, so the corpus sentence is spent. It is "
    "recorded here rather than deleted because a reader who meets it in T388's handoff or T389's "
    "review must be able to find what became of it.] "
    "[AND THE OLDER CORRECTION STILL STANDS AND IS THE REASON THESE VECTORS GRADE THE SLOT. T242, "
    "A2-34 F-4: this row once asserted 'gl 18, 22 and 16 carry ZERO journal entries' and the "
    "harness printed it every run while gl 16 had SIXTEEN. ONE GL ACCOUNT BACKS SEVERAL SLOTS. "
    "Re-measured live by T391: gl 18 -> 0, gl 22 -> 0, gl 16 -> TWENTY-ONE, and gl 16 is "
    "FUND_SOURCE (slot 1) on TEN cash products -- 22, 23, 27, 46, 54, 55, 56, 57, 58, 60 -- as "
    "well as PENALTIES_RECEIVABLE (slot 9) on accrual product 28, with ZERO of its rows arriving "
    "through product 28 at all [T391-S01 sections 4c and 8]. Note that these counts are PROSE IN "
    "THIS FILE, not values the harness re-derives at report time, which is exactly why they go "
    "stale; the SLOT rows below are the part the harness does re-derive.]"
)

SLOT_EVIDENCE = (
    "PARTIALLY GRADED SINCE T391, AND THE ROW STAYS FALSE BECAUSE THE PART THAT IS GRADED IS THE "
    "SMALLER PART. What IS graded now: the (product, slot) -> GL account resolution on the ACCRUAL "
    "family, for slot codes 3, 4, 5, 7, 8 and 9 on product 63, keyed through that product's own "
    "observed thirteen-row acc_product_mapping table, plus the DECODE of each code to its "
    "AccrualAccountsForLoan name. LDG-ACC-01/02/03 assert it, and ledger-wrong-slot-family-blind "
    "-- a port that decodes every code through CashAccountsForLoan whatever the accounting rule "
    "says -- dies to it on legs[i].slot_name while producing the RIGHT account on every leg. "
    "WHAT IS STILL UNGRADED, and it is why in_graded_domain stays FALSE: (a) THE PAYMENT-TYPE "
    "PRECEDENCE CHAIN -- product 63 has NO paymentChannelToFundSourceMappings, "
    "feeToIncomeAccountMappings or penaltyToIncomeAccountMappings at all [T391, GET "
    "/loanproducts/63, out/T391-04-product63-mapping-rest.txt], so STEP 2 of "
    "resolveProductAccount is never entered and G-06's contested null-payment-type question is "
    "untouched; (b) THE CASH FAMILY -- no cash-based accounting-path vector exists; (c) the "
    "financial-activity STEP 0 branch, which no loan placeholder code reaches; (d) the charge and "
    "reason precedence levels. A vector claiming THIS capability would be claiming all of that, "
    "so it is still refused. The accrual vectors claim `ledger.accrual.entry` instead, which is "
    "scoped to what they actually exercised. "
    "[T391 MOVED unposted_slots ONTO THIS ROW. It used to hang off ledger.accrual.entry, which is "
    "now in the graded domain -- and the harness prints the SLOT lines only for rows marked "
    "in_graded_domain false, so leaving them there would have SILENTLY STOPPED PRINTING a "
    "measurement that has already been wrong once in this file's history. They belong here on the "
    "merits too: an unposted slot is a gap in SLOT RESOLUTION coverage. Nothing else about them "
    "changed. THE THREE PRODUCT-28 ROWS ARE UNCHANGED AND STILL TRUE, re-measured live by T391: "
    "slot 7 -> gl 18 (0 rows), slot 8 -> gl 22 (0 rows), slot 9 -> gl 16 (21 rows on the ACCOUNT "
    "and ZERO through product 28) [out/T391-S01-slot-resolution.txt section 8]. THE FIVE PRODUCT-63 "
    "ROWS ARE NEW and are the five accrual slots T388 left unposted and T391 DELIBERATELY DID NOT "
    "POST: 6 LOSSES_WRITTEN_OFF -> gl 40, 10 TRANSFERS_SUSPENSE -> gl 44, 11 OVERPAYMENT -> gl 45, "
    "12 INCOME_FROM_RECOVERY -> gl 46, 13 GOODWILL_CREDIT -> gl 47, all five reading ZERO journal "
    "entries [T391-S01 section 7]. They need a write-off, a transfer, an overpayment, a recovery "
    "and a goodwill credit respectively -- five further MOVES OF SHARED ORACLE STATE, each with "
    "its own blast radius, while T388's twenty command-source rows are STILL UNATTRIBUTED in "
    "PROBES.tsv (T390's open obligation). Declaring them here costs nothing and makes the gap "
    "print on every run; posting them would have deepened an open obligation to buy evidence this "
    "task did not need.]"
)


def main():
    with open(PATH, encoding="utf-8") as fh:
        doc = json.load(fh)

    accrual = None
    slotres = None
    for c in doc["capabilities"]:
        if c["name"] == "ledger.accrual.entry":
            accrual = c
        elif c["name"] == "ledger.slot.resolution":
            slotres = c
    if accrual is None or slotres is None:
        sys.exit("REFUSING: one of the two rows this script rewrites is absent.")

    # --- assert the PRE-state, so this cannot run twice or against drift -----
    for probe in (
        "the observations do not exist",
        "NOT ONE JOURNAL ENTRY IN THIS TENANT ARRIVED THROUGH A RECEIVABLE SLOT",
        "Product 28 is the only ACCRUAL_PERIODIC product",
        "An accrual vector needs a NEW accrual product on clean accounts PLUS a job run",
    ):
        if probe not in accrual["evidence"]:
            sys.exit("REFUSING: ledger.accrual.entry no longer contains %r, so this script is "
                     "not looking at the row it was written for." % probe)
    if accrual["in_graded_domain"] is not False:
        sys.exit("REFUSING: ledger.accrual.entry is already in the graded domain.")
    if "unposted_slots" not in accrual:
        sys.exit("REFUSING: ledger.accrual.entry carries no unposted_slots to move.")
    if "unposted_slots" in slotres:
        sys.exit("REFUSING: ledger.slot.resolution already carries unposted_slots.")

    moved = accrual.pop("unposted_slots")
    if moved != [
        {"product_id": 28, "accounting_rule": "accrual", "slot_code": 7, "gl_account_id": 18},
        {"product_id": 28, "accounting_rule": "accrual", "slot_code": 8, "gl_account_id": 22},
        {"product_id": 28, "accounting_rule": "accrual", "slot_code": 9, "gl_account_id": 16},
    ]:
        sys.exit("REFUSING: the unposted_slots rows are not the three this script verified.")

    accrual["description"] = (
        "An accrual journal entry -- INTEREST_RECEIVABLE, FEES_RECEIVABLE or PENALTIES_RECEIVABLE "
        "on the debit side against INTEREST_ON_LOANS, INCOME_FROM_FEES or INCOME_FROM_PENALTIES on "
        "the credit side -- produced by the oracle's own loan accounting rather than by a manual "
        "posting, and GRADED ON THE SLOT IT ARRIVED THROUGH rather than on the account it landed on."
    )
    accrual["in_graded_domain"] = True
    accrual["evidence"] = ACCRUAL_EVIDENCE

    slotres["evidence"] = SLOT_EVIDENCE
    slotres["unposted_slots"] = moved + [
        {"product_id": 63, "accounting_rule": "accrual", "slot_code": 6, "gl_account_id": 40},
        {"product_id": 63, "accounting_rule": "accrual", "slot_code": 10, "gl_account_id": 44},
        {"product_id": 63, "accounting_rule": "accrual", "slot_code": 11, "gl_account_id": 45},
        {"product_id": 63, "accounting_rule": "accrual", "slot_code": 12, "gl_account_id": 46},
        {"product_id": 63, "accounting_rule": "accrual", "slot_code": 13, "gl_account_id": 47},
    ]

    for seam in doc["seams"]:
        if seam["name"] == "ledger_rest_posting":
            if "ledger.accrual.entry" in seam["status"]:
                sys.exit("REFUSING: ledger_rest_posting already declares ledger.accrual.entry.")
            seam["status"]["ledger.accrual.entry"] = "exercised"

    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("rewrote", PATH)


if __name__ == "__main__":
    main()
