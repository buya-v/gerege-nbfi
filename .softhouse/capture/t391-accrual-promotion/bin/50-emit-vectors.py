#!/usr/bin/env python3
"""T391 -- emit the three accrual parity vectors.

WHAT THIS SCRIPT IS AND IS NOT
------------------------------
It is a TRANSCRIPTION ASSEMBLER, not a calculator. Every amount below -- both
the oracle's major-unit characters and the integer count of minor units -- is a
HAND-TYPED LITERAL. There is no arithmetic in this file: no float, no int(),
no Decimal, no multiplication by 100. Search it and you will find none.

WHY IT EXISTS AT ALL, since hand-typing is the discipline. Three vectors share
one 13-row chart, one 13-row mapping table and one long note. Typing those three
times is three chances to differ, and a reviewer then cannot tell a typo from a
claim. The DIFFERENCES between the three vectors are exactly the VECTORS list
below and nothing else, which is the property that makes the three readable
side by side.

THE INDEPENDENT CHECK ON THE MINOR-UNIT LITERALS, and it is not this script's
arithmetic. The reference oracle's OWN PostgreSQL engine summed them, in exact
`numeric` arithmetic, in out/T391-S03-slot-resolution-fixed.txt section 3:

    L29  debit_minor 2770000 = 2400000 + 250000 + 120000  difference_minor 0
    L30  debit_minor 2389538 = 2019538 + 250000 + 120000  difference_minor 0
    L32  debit_minor 1605634 = 1235634 + 250000 + 120000  difference_minor 0

So the per-leg integers typed below are corroborated by a computation performed
by the oracle, not by the promoter.
"""
import json
import os

OUT_DIR = ".softhouse/vectors/ledger"

# --- the chart, transcribed from out/T391-S03-slot-resolution-fixed.txt §1 ----
# All thirteen accounts, not only the six the legs land on. A mis-keying port
# that resolves a slot to the WRONG row must land on an account the chart
# carries, so the comparator reports a graded cell difference rather than the
# harness reporting a crash.
ACCOUNTS = [
    (35, "T388-1000", "T388 Accrual Fund Source"),
    (36, "T388-1100", "T388 Accrual Loan Portfolio"),
    (37, "T388-4000", "T388 Interest On Loans"),
    (38, "T388-4100", "T388 Income From Fees"),
    (39, "T388-4200", "T388 Income From Penalties"),
    (40, "T388-5000", "T388 Losses Written Off"),
    (41, "T388-1200", "T388 Interest Receivable"),
    (42, "T388-1300", "T388 Fees Receivable"),
    (43, "T388-1400", "T388 Penalties Receivable"),
    (44, "T388-1500", "T388 Transfers Suspense"),
    (45, "T388-2000", "T388 Overpayment Liability"),
    (46, "T388-4300", "T388 Income From Recovery"),
    (47, "T388-5100", "T388 Goodwill Credit"),
]

# --- product 63's COMPLETE acc_product_mapping, slot -> account ---------------
# Transcribed from GET /loanproducts/63 (out/T391-04-product63-mapping-rest.txt)
# and cross-checked against a read-only SELECT (out/T391-S03 §1). The two agree
# on all thirteen rows.
MAPPINGS = [
    (1, 35), (2, 36), (3, 37), (4, 38), (5, 39), (6, 40), (7, 41),
    (8, 42), (9, 43), (10, 44), (11, 45), (12, 46), (13, 47),
]

SLOT_NAMES = {
    3: "INTEREST_ON_LOANS",
    4: "INCOME_FROM_FEES",
    5: "INCOME_FROM_PENALTIES",
    7: "INTEREST_RECEIVABLE",
    8: "FEES_RECEIVABLE",
    9: "PENALTIES_RECEIVABLE",
}

# --- the three transactions --------------------------------------------------
# legs are (slot_code, side, major_text, minor_text, resolved_gl_id, resolved_code)
# IN THE ORACLE'S OWN READ-BACK ORDER, which is stable by journal-entry id.
# resolved_gl_id / resolved_code are the EXPECTATION -- what the implementation
# must produce by keying MAPPINGS with slot_code -- and they are written out so a
# reader can check the resolution by eye against the table above.
VECTORS = [
    {
        "case_id": "LDG-ACC-01-accrual-six-slots-runaccruals-trigger",
        "transaction_id": "L29",
        "capture": "T391-A01-je-L29",
        "capture_sha256": "4ac271a907422f3432493b0d41da7fdba5d0540fb16aefd1665d8413f48cd3b4",
        "request_sha256": "e89ab942e7414ce58a1dc2b26754a181f0554b7175ff72be4db0275ce49d8db6",
        "trigger": (
            "POST /v1/runaccruals {\"tillDate\":\"15 April 2026\"} -- a HAND-FIRED "
            "trigger, m_portfolio_command_source row 379, Idempotency-Key "
            "T388-A01-runaccruals"
        ),
        "period": "period 1 of 6, entry date 2026-02-15",
        "money_shape": (
            "the interest leg is a WHOLE TUGRIK, 24000.000000. It is promoted "
            "BECAUSE it is round: with LDG-ACC-02 and LDG-ACC-03 beside it, the "
            "corpus carries the same six-slot shape at a round amount and at two "
            "amounts with minor-unit residue, so a port that is right only on "
            "round numbers has nowhere to hide"
        ),
        "legs": [
            (7, "DEBIT", "24000.000000", "2400000", 41, "T388-1200"),
            (3, "CREDIT", "24000.000000", "2400000", 37, "T388-4000"),
            (4, "CREDIT", "2500.000000", "250000", 38, "T388-4100"),
            (8, "DEBIT", "2500.000000", "250000", 42, "T388-1300"),
            (5, "CREDIT", "1200.000000", "120000", 39, "T388-4200"),
            (9, "DEBIT", "1200.000000", "120000", 43, "T388-1400"),
        ],
        "total_debits_minor": "2770000",
        "total_credits_minor": "2770000",
        "netting_margin_minor": "-2770000",
        "extra_graded_against": [],
    },
    {
        "case_id": "LDG-ACC-02-accrual-six-slots-minor-unit-residue",
        "transaction_id": "L30",
        "capture": "T391-A02-je-L30",
        "capture_sha256": "360ed3ebcb26d9961859c2320155ea9e8d18683905dd1f8de3a5e4d38e818eeb",
        "request_sha256": "d4eae8560d57ba25df3673a9b4f87b0472488fc5fec0226276d93f68ae133dbe",
        "trigger": (
            "POST /v1/runaccruals {\"tillDate\":\"15 April 2026\"} -- the SAME "
            "hand-fired trigger as LDG-ACC-01; one call produced L29, L30 and L31"
        ),
        "period": "period 2 of 6, entry date 2026-03-15",
        "money_shape": (
            "the interest leg is 20195.380000 -- 38 minor units that a port "
            "reading the major-unit text as a whole number LOSES. This is the "
            "shape DEC-2 section 5.0.1 says a whole-tugrik corpus cannot see"
        ),
        "legs": [
            (7, "DEBIT", "20195.380000", "2019538", 41, "T388-1200"),
            (3, "CREDIT", "20195.380000", "2019538", 37, "T388-4000"),
            (4, "CREDIT", "2500.000000", "250000", 38, "T388-4100"),
            (8, "DEBIT", "2500.000000", "250000", 42, "T388-1300"),
            (5, "CREDIT", "1200.000000", "120000", 39, "T388-4200"),
            (9, "DEBIT", "1200.000000", "120000", 43, "T388-1400"),
        ],
        "total_debits_minor": "2389538",
        "total_credits_minor": "2389538",
        "netting_margin_minor": "-2389538",
        "extra_graded_against": [
            {
                "impl": "ledger-wrong-truncating",
                "kind": "money",
                "margin_minor": "-38",
                "divergent_cells": [
                    "legs[].amount_minor",
                    "total_debits_minor",
                    "total_credits_minor",
                ],
                "note": (
                    "A port that reads the major-unit text as a whole number loses the 38 minor units on the two "
                    "interest legs and on both totals. It does NOT die on LDG-ACC-01, whose every amount is a whole tugrik -- which is the point DEC-2 section 5.0.1 makes about a whole-tugrik corpus, visible here inside one shape rather than across two."
                ),
            },
        ],
    },
    {
        "case_id": "LDG-ACC-03-accrual-six-slots-scheduled-job",
        "transaction_id": "L32",
        "capture": "T391-A04-je-L32",
        "capture_sha256": "d933e7a18de9af266e34761069e22e386983f390c5b5401c9a6d33404403a9bb",
        "request_sha256": "aaafcf8fa6427b19cca6eca3297abed7eee57152bb30353a388d7ef0d23cd0ff",
        "trigger": (
            "NO API CALL AT ALL. A SCHEDULED JOB wrote this transaction while "
            "nobody was watching: journal entries 96-101 carry created_on_utc "
            "2026-08-28 16:01:00.100 .. .107, m_portfolio_command_source did not "
            "move (379 before and after), and job_run_history puts job 11 'Add "
            "Accrual Transactions' at 16:01:00.049 -> .120, trigger_type cron -- "
            "an interval that STRICTLY CONTAINS every one of those timestamps, "
            "while job 22 ran .002 -> .030 and job 16 not until 16:02:00.002. "
            "T388 recorded the scheduler as the thing it could NOT capture; this "
            "is that observation, taken for free by waiting"
        ),
        "period": "period 4 of 6, entry date 2026-05-15",
        "money_shape": (
            "the interest leg is 12356.340000 -- 34 minor units of residue, and a "
            "DIFFERENT residue from LDG-ACC-02's 38, so a port that happened to "
            "match one of them has not matched a constant"
        ),
        "legs": [
            (7, "DEBIT", "12356.340000", "1235634", 41, "T388-1200"),
            (3, "CREDIT", "12356.340000", "1235634", 37, "T388-4000"),
            (4, "CREDIT", "2500.000000", "250000", 38, "T388-4100"),
            (8, "DEBIT", "2500.000000", "250000", 42, "T388-1300"),
            (5, "CREDIT", "1200.000000", "120000", 39, "T388-4200"),
            (9, "DEBIT", "1200.000000", "120000", 43, "T388-1400"),
        ],
        "total_debits_minor": "1605634",
        "total_credits_minor": "1605634",
        "netting_margin_minor": "-1605634",
        "extra_graded_against": [
            {
                "impl": "ledger-wrong-truncating",
                "kind": "money",
                "margin_minor": "-34",
                "divergent_cells": [
                    "legs[].amount_minor",
                    "total_debits_minor",
                    "total_credits_minor",
                ],
                "note": (
                    "A port that reads the major-unit text as a whole number loses the 34 minor units on the two "
                    "interest legs and on both totals. A DIFFERENT residue from LDG-ACC-02's 38, so the kill is not a constant this port could have matched by luck."
                ),
            },
        ],
    },
]

NOTE = (
    "WHAT THIS VECTOR GRADES, AND WHY IT GRADES THE SLOT RATHER THAN THE ACCOUNT. "
    "This is the first vector in this program to assert a journal entry the oracle's own LOAN "
    "ACCOUNTING produced rather than one a caller posted by hand, and the first to populate the "
    "ledger schema's SLOT fields at all. The choice it embodies was forced by T242's correction "
    "(A2-34 F-4): the harness printed 'gl 18, 22 and 16 carry ZERO journal entries' on every run, "
    "pass or fail, as measured fact, while gl 16 had SIXTEEN -- because ONE GL ACCOUNT BACKS "
    "SEVERAL SLOTS. gl 16 is PENALTIES_RECEIVABLE (slot 9) on accrual product 28 AND FUND_SOURCE "
    "(slot 1) on TEN cash products [re-measured live by T391, out/T391-S01 section 4c: products "
    "22, 23, 27, 28, 46, 54, 55, 56, 57, 58, 60], and every one of its rows arrives through the "
    "latter. A vector that graded the ACCOUNT would reproduce exactly that error. So this vector's "
    "legs carry a SLOT CODE AND NO ACCOUNT ID, the request carries product 63's COMPLETE "
    "thirteen-row acc_product_mapping table, and expect.legs[].gl_account_id, "
    "expect.legs[].gl_account_code and expect.legs[].slot_name are all OUTPUTS the implementation "
    "must produce by keying that table with the slot code and decoding the code on the family the "
    "product's accounting rule selects. "
    "WHY THE DECODE IS UNAMBIGUOUS HERE, CHECKED AND NOT ASSUMED. Product 63's mapping is a "
    "BIJECTION -- 13 mappings, 13 distinct accounts, 13 distinct slots [T391-S01 section 4a] -- and "
    "NO OTHER PRODUCT MAPS ANY OF ACCOUNTS 35-47 [T391-S01 section 4b, ZERO rows]. So on this "
    "product gl_account_id -> financial_account_type really is a function. That is a property of "
    "how T388 built the product, not a property of Fineract, and it is why the accounts were "
    "created clean. "
    "THE DEFECT THIS SHAPE CATCHES AND THE OLD SHAPE COULD NOT. acc_product_mapping is keyed on "
    "(product_id, product_type, financial_account_type) and THE ACCOUNTING RULE IS NOT IN THE KEY, "
    "so a port that decodes every code through CashAccountsForLoan resolves the RIGHT ACCOUNT and "
    "names the WRONG SLOT: CashAccountsForLoan has no 7, 8 or 9 at all, and carries the names "
    "FEES_RECEIVABLE and PENALTIES_RECEIVABLE at 25 and 26 instead [VERIFIED: "
    "AccountingConstants.java:79-89 and :95-122 at 426a23544; ported at "
    "nexus/internal/apps/ledger/slots.go]. That port is registered as "
    "ledger-wrong-slot-family-blind, it is BYTE-IDENTICAL to ledger-go on all seven parity vectors "
    "that predate T391 and on this vector's three INCOME legs, and legs[i].slot_name is the ONLY "
    "cell it dies on. "
    "GL_ACCOUNT_TYPE IS EXCLUDED ON EVERY LEG, for LDG-01's reason unchanged: glAccountType in a "
    "/journalentries response projects the ACCOUNT'S CURRENT classification, not the entry's, and "
    "A2-26 observed the identical row rendering ASSET and then INCOME with no entry edited. The "
    "classification rendered at capture time is recorded here and graded by nothing: the three "
    "receivable legs (gl 41, 42, 43) rendered ASSET and the three income legs (gl 37, 38, 39) "
    "rendered INCOME. "
    "NO BALANCE IS GRADED. GATE G-12 is open on acc_gl_journal_entry's running-balance columns "
    "(A2-29 measured them to be a second source of truth, not a cache) and this schema has no "
    "field for either. "
    "THIS IS NOT A PRECISION CLAIM, and T388 said so first. The production MathContext is "
    "(19, HALF_UP) and this tenant runs at the ratified HALF_UP, but NOTHING IN THIS CAPTURE "
    "DISCRIMINATES PRECISION: every amount the oracle emitted here is exact at two decimal places "
    "and no leg carries a non-zero third decimal [T391-S01 section 6, ZERO rows]. A port running at "
    "precision 12 would produce these same six integers. Read this vector as evidence about ACCRUAL "
    "AND SLOT RESOLUTION and about nothing else; the (19, HALF_UP) question is untouched by it. "
    "AND IT IS NOT EVIDENCE ABOUT WHICH JOB RUNS WHEN. `job` and `job_run_history` record WHEN a "
    "job ran, not WHICH ROWS it wrote, and no foreign key joins a journal entry to a job. What is "
    "graded here is the ENTRY. The trigger is recorded in provenance.citation because it is a fact "
    "about how the observation was obtained, and it is graded by nothing."
)


def account_rows():
    return [
        {
            "id": i,
            "gl_code": code,
            "name": name,
            "usage": "DETAIL",
            "manual_entries_allowed": True,
            "disabled": False,
        }
        for (i, code, name) in ACCOUNTS
    ]


def mapping_rows():
    return [{"slot_code": s, "gl_account_id": a} for (s, a) in MAPPINGS]


def build(v):
    legs_req = []
    legs_exp = []
    for (slot, side, major, minor, gl, code) in v["legs"]:
        legs_req.append({
            "gl_account_id": 0,
            "entry_side": side,
            "amount_major_text": major,
            "slot_code": slot,
        })
        legs_exp.append({
            "gl_account_id": gl,
            "gl_account_code": code,
            "entry_side": side,
            "amount_minor": minor,
            "amount_major_text": major,
            "slot_name": SLOT_NAMES[slot],
            "excluded_fields": ["gl_account_type"],
        })
    ref = ".softhouse/capture/t391-accrual-promotion/out/" + v["capture"]
    return {
        "schema": "gerege.ledger.vector/v1",
        "case_id": v["case_id"],
        "context": "ledger",
        "class": "parity",
        "title": (
            "AN ACCRUAL JOURNAL TRANSACTION, SIX LEGS ACROSS SIX SLOTS, GRADED ON THE SLOT AND NOT "
            "ON THE ACCOUNT. Transaction " + v["transaction_id"] + " on loan 8 (client 3, product 63, "
            "ACCRUAL_PERIODIC, MNT), " + v["period"] + ": DEBIT INTEREST_RECEIVABLE (slot 7), "
            "FEES_RECEIVABLE (8) and PENALTIES_RECEIVABLE (9) against CREDIT INTEREST_ON_LOANS (3), "
            "INCOME_FROM_FEES (4) and INCOME_FROM_PENALTIES (5), read back at the contract boundary "
            "through GET /journalentries?transactionId=" + v["transaction_id"] + ". " + v["money_shape"] + "."
        ),
        "dec2_revision": 5,
        "_note": NOTE,
        "capabilities_required": [
            "ledger.journal.entry.readback",
            "ledger.money.minor.unit.conversion",
            "ledger.accrual.entry",
        ],
        "provenance": {
            "kind": "capture",
            "capture_ref": ref + ".json",
            "capture_sha256": v["capture_sha256"],
            "capture_case_id": v["capture"],
            "request_capture_ref": ref + ".http",
            "request_capture_sha256": v["request_sha256"],
            "request_capture_case_id": v["capture"],
            "rerun_invariant": (
                "Re-issuing GET /journalentries?transactionId=" + v["transaction_id"] +
                "&transactionDetails=true against tenant `gerege` must return SIX legs whose amounts are "
                + ", ".join(l[2] for l in v["legs"]) +
                " at the oracle's scale of 6, on GL 41/37/38/42/39/43 in that order, DEBIT/CREDIT/"
                "CREDIT/DEBIT/CREDIT/DEBIT, every one manualEntry false with transactionDetails."
                "transactionType.id 10 (Accrual) on loan 8. AND, SEPARATELY, product 63's "
                "acc_product_mapping must still map slot 7 -> 41, 8 -> 42, 9 -> 43, 3 -> 37, 4 -> 38 and "
                "5 -> 39: this vector's expectation is the RESOLUTION of those slots, so a re-mapped "
                "product falsifies it even if the stored journal entries never move. A journal entry "
                "cannot be deleted and the accrual is permanent, so the entry half of this invariant is "
                "re-checkable forever WITHOUT re-firing anything at the oracle -- it is a GET. If the "
                "mapping half ever fails, the answer is RE-CAPTURE, not exemption (P-8)."
            ),
            "citation": (
                "T391, promoting T388's accrual observations. Legs read from the RAW BYTES of the "
                "cited response (the `amount` tokens are " + ", ".join(l[2] for l in v["legs"]) +
                " -- scale 6, exactly as the oracle emitted them; a JSON reader that decodes them "
                "through a float prints 24000.0 and is not what was read). The slot decode is a join "
                "through product 63's acc_product_mapping, recorded read-only in "
                ".softhouse/capture/t391-accrual-promotion/out/T391-S03-slot-resolution-fixed.txt and "
                "cross-checked at the contract boundary in T391-A07-loanproduct-63.json. HOW THE "
                "TRANSACTION CAME TO EXIST: " + v["trigger"] + "."
            ),
        },
        "oracle": {
            "fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb",
            "seam": "ledger_rest_posting",
            "captured_at": "2026-08-29T09:00:00Z",
        },
        "request": {
            "product_id": 63,
            "product_type": "LOAN",
            "accounting_rule": "ACCRUAL_PERIODIC",
            "slot_family": "AccrualLoanSlot",
            "slot_code": 0,
            "payment_type_id": None,
            "seam": "ledger_rest_posting",
            "office_id": 1,
            "currency": {"code": "MNT", "minor_unit_digits": 2},
            "transaction_id": v["transaction_id"],
            "manual_entry": False,
            "transaction_amount_major_text": "",
            "accounts": account_rows(),
            "legs": legs_req,
            "product_mappings": mapping_rows(),
        },
        "expect": {
            "kind": "journal-entry",
            "http_status": 200,
            "legs": legs_exp,
            "total_debits_minor": v["total_debits_minor"],
            "total_credits_minor": v["total_credits_minor"],
            "refusal": {"http_status": 0, "code": "", "message": ""},
        },
        "graded_against": [
            {
                "impl": "ledger-wrong-slot-family-blind",
                "kind": "structural",
                "margin_minor": "0",
                "divergent_cells": ["legs[].slot_name"],
                "note": (
                    "THE KILL THIS VECTOR EXISTS FOR. A port that decodes every placeholder through "
                    "CashAccountsForLoan resolves the RIGHT ACCOUNT on all six legs -- the mapping key "
                    "does not carry the accounting rule -- and names the right slot on the three INCOME "
                    "legs, because both enums call 3, 4 and 5 INTEREST_ON_LOANS, INCOME_FROM_FEES and "
                    "INCOME_FROM_PENALTIES. It dies on the three RECEIVABLE legs alone, because "
                    "CashAccountsForLoan has no 7, 8 or 9. Every account cell, every code cell, every "
                    "side and every money cell it produces is correct: this is the measurement of the "
                    "claim that the SLOT and the ACCOUNT are different things."
                ),
            },
            {
                "impl": "ledger-wrong-code-ignored",
                "kind": "structural",
                "margin_minor": "0",
                "divergent_cells": ["legs[].gl_account_code"],
                "note": "A port carrying account ids and never joining the chart.",
            },
            {
                "impl": "ledger-wrong-netting-totals",
                "kind": "money",
                "margin_minor": v["netting_margin_minor"],
                "divergent_cells": ["total_debits_minor", "total_credits_minor"],
                "note": (
                    "Netting credits against debits makes both totals 0 while every per-leg cell still "
                    "matches, so I-1 would hold by construction. A six-leg entry is the shape where that "
                    "matters most. DECLARED AS A **MONEY** KILL, WHERE LDG-01 DECLARES THE SAME "
                    "IMPLEMENTATION AS STRUCTURAL WITH MARGIN 0, and the difference is stated rather "
                    "than left for a reader to trip over: total_debits_minor and total_credits_minor go "
                    "through cmpMoney, not cmpStr, so a wrong value there IS a money divergence and it "
                    "has a margin -- here the whole transaction, " + v["netting_margin_minor"] + " minor "
                    "units. LDG-01's label is the weaker of the two descriptions of one behaviour; "
                    "nothing about the implementation differs between the two vectors."
                ),
            },
        ] + v["extra_graded_against"],
        "invariant_exemptions": [],
    }


def main():
    for v in VECTORS:
        doc = build(v)
        path = os.path.join(OUT_DIR, doc["case_id"] + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("wrote", path)


if __name__ == "__main__":
    main()
