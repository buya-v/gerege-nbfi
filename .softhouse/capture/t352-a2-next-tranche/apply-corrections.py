#!/usr/bin/env python3
"""T352. Apply THREE text corrections to .softhouse/vectors/capabilities-ledger.json,
each keyed to an observation this task took from the live reference oracle this fire.

NO COUNT MOVES. Every edit is to an `evidence` string, which the report renders as the
"WHY NOT" prose. The exemption census pins (EXEMPTION_PIN_LEDGER_PARITY / _REFUSAL /
_MONEYCELLS in conformance.sh) read vector POPULATIONS and MONEY CELLS, none of which
this script touches. The T305-ACCEPTING-SIDE-GAP marker that guard_accepting_side_gap_
declared() greps for (conformance.sh:2313) is not in any string this script rewrites,
and the script asserts that it survives.

NO FLOAT IS PARSED OR EMITTED. This script reads and writes JSON that contains no
numeric money token; it edits strings only. json.load is called with parse_float set to
a raiser, so a float appearing anywhere in the file would abort rather than round-trip
through a binary double (P-25, the A2-11 / T163 resolve7.py defect).
"""
import json
import sys

PATH = ".softhouse/vectors/capabilities-ledger.json"


def _no_float(tok):
    raise SystemExit(
        "REFUSING: capabilities-ledger.json carries a JSON float token %r. This script "
        "will not round-trip a float through a binary double (P-25)." % tok)


RESIDUE = (
    " [CORRECTED BY OBSERVATION, T352, fire 20260828-140005. The sentence above -- 'no "
    "capture carries a NON-ZERO digit beyond two decimal places' -- WAS TRUE WHEN "
    "WRITTEN AND IS NOW FALSE. T352 posted one and the oracle TOOK IT. "
    "POST /journalentries with debit and credit legs of 100.125 MNT returned HTTP 200 "
    "[.softhouse/capture/t352-a2-next-tranche/out/T352-A01-residue-3dp.json, txn "
    "a29bca0816a7], and GET /journalentries read both legs back as amount 100.125000 "
    "[out/T352-A09-residue-3dp-readback-cited.json, sha256 7163378b...], with the "
    "response's own currency block still declaring MNT decimalPlaces 2. psql confirms "
    "the stored column: amount 100.125000, scale(amount) = 6 "
    "[out/T352-A06-residue-db.txt]. SO THE ORACLE NEITHER REFUSES A SUB-MINOR-UNIT "
    "RESIDUE NOR ROUNDS IT AWAY -- IT PERSISTS IT AND SERVES IT BACK. Three consequences, "
    "each stated separately because they are different claims. (1) money.go's trap-4 "
    "comment asks 'whether the oracle can produce one at all on a money column' and "
    "records it [UNVERIFIED]; it is now VERIFIED that the column can HOLD one and the "
    "reader SERVES one. What is still NOT observed is the oracle's own ARITHMETIC "
    "generating a residue -- T352 SUPPLIED the third decimal, it was not computed -- and "
    "those are different facts. (2) THE PORT AND THE ORACLE NOW DEMONSTRABLY DIVERGE ON "
    "THIS INPUT: MinorUnitsFromDecimalText('100.125000', 2) returns an error, so a Go "
    "port fed this oracle response FAILS where the oracle succeeded. The refusal is "
    "still the defensible default -- inventing 10012 or 10013 would invent money -- but "
    "it is no longer true that 'no captured vector establishes' the oracle's behaviour, "
    "which is the reason the error message itself gives. (3) THE VECTOR SCHEMA CANNOT "
    "REPRESENT THIS OBSERVATION AT ALL, and that was DRIVEN rather than argued: a "
    "candidate vector transcribing these bytes, with every other admission objection "
    "removed, comes back HARNESS-ERROR and the corpus exits 2 "
    "[red-drive/02-candidate-HARNESS-ERROR.log; the candidate is banked NOT-PROMOTED "
    "beside it]. expect.legs[].amount_minor requires an int64 count of minor units and "
    "no such integer equals 100.125. This capability therefore stays in the graded "
    "domain for the amounts it can express, and the store is now KNOWN to be silent on "
    "a shape the oracle really produces. Raised as FU-T352-1.]"
)

BALANCE = (
    " [T352 ALSO OBSERVED WHAT THE BALANCE CHECK COMPARES, because a residue makes the "
    "question answerable for the first time. Debits of 0.125 + 0.125 against a single "
    "credit of 0.25 were ACCEPTED, HTTP 200, txn a29bca9bf813 "
    "[out/T352-A03-residue-balance-scale.json; psql shows 0.125000 + 0.125000 = 0.250000 "
    "in out/T352-A06-residue-db.txt]. Had the oracle rounded each leg to the currency's "
    "minor unit before summing, HALF_UP would have given 0.13 + 0.13 = 0.26 against 0.25 "
    "and the entry would have been REFUSED as a sum mismatch. SO THE DOUBLE-ENTRY "
    "BALANCE CHECK RUNS AT FULL SCALE ON THE UNROUNDED AMOUNTS. That agrees with source: "
    "checkDebitAndCreditAmounts sums the raw BigDecimals and compares with compareTo, "
    "with no setScale and no currency rounding anywhere on the path [VERIFIED: "
    "JournalEntryWritePlatformServiceJpaRepositoryImpl.java:306-326; and `grep -rn "
    "'setScale\\|RoundingMode' fineract-provider/src/main/java/org/apache/fineract/"
    "accounting/journalentry/` returns NOTHING at the pinned commit]. A SEPARATE "
    "OBSERVATION, AND ITS ATTRIBUTION STATED RATHER THAN ASSUMED: a leg posted at SEVEN "
    "decimal places, 100.1234565, was accepted and stored as 100.123457 "
    "[out/T352-A04-overscale-7dp.json / out/T352-A05-overscale-readback.json, txn "
    "a29bcaa6a41b]. That is round-half-UP into the column's scale 6; HALF_EVEN and "
    "truncation both give 100.123456. IT MAY NOT BE CITED AS WITNESSING MoneyHelper's "
    "ratified HALF_UP. The JE write path applies no Java-side rounding at all (the grep "
    "above), so the rounding observed here is PostgreSQL's numeric(19,6) coercion, whose "
    "half-away-from-zero coincides with Java HALF_UP for positive amounts. The two "
    "cannot be separated by a positive-amount probe, and this corpus posts no negative "
    "leg. Recorded as an observation of the SYSTEM's behaviour at the contract boundary, "
    "not of the tenant rounding mode.]"
)

MULTICCY = (
    " [CORRECTED BY OBSERVATION AND BY SOURCE, T352, fire 20260828-140005. Two things "
    "above need separating, because they are not the same claim and only one of them "
    "survives. (1) 'There is NO OBSERVATION of a multi-currency entry' -- still true, "
    "and now known to be true FOR A STRUCTURAL REASON rather than for want of a probe. "
    "A journal-entry LEG HAS NO CURRENCY FIELD: SingleDebitOrCreditEntryCommand carries "
    "exactly glAccountId, amount and comments [VERIFIED: "
    "SingleDebitOrCreditEntryCommand.java:33-35 at 426a23544], and currencyCode is a "
    "single scalar on the enclosing JournalEntryCommand [:40]. AN ENTRY WHOSE LEGS ARE "
    "DENOMINATED IN MORE THAN ONE CURRENCY IS NOT EXPRESSIBLE AT THE ledger_rest_posting "
    "SEAM AT ALL. So this capability is not merely unexercised, it names a shape this "
    "seam cannot produce, and no capture campaign will ever close it here. (2) 'Every "
    "journal entry in the corpus is MNT' -- still true of the CORPUS, but it is a fact "
    "about the PROBES and NOT about the oracle, and T352 measured the difference. The "
    "tenant has TWO selected currencies, MNT and USD [out/T352-P01-currencies.json], "
    "and a journal entry posted in USD on the same two GL accounts was ACCEPTED, HTTP "
    "200, txn a29bcb5d6fcf, read back with currency USD decimalPlaces 2 and amount "
    "12.340000 [out/T352-A07-usd-entry.json, out/T352-A08-usd-readback.json]. THE "
    "LEDGER IS CURRENCY-GENERAL; THE STORE IS NOT. G-07's MNT pin is therefore a STORE "
    "POLICY enforced at admit.go:156-162, not a constraint the oracle imposes, and the "
    "sentence 'there is NO OBSERVATION ... so G-07 pins MNT' inverts that: the pin came "
    "first. Whether to widen G-07 is a schema question and a DEC-2 amendment, not a "
    "capture question. Raised as FU-T352-2. This capability stays out of the graded "
    "domain, with a corrected reason.]"
)

ACCRUAL = (
    " [REASON CORRECTED BY MEASUREMENT, T352, fire 20260828-140005; the CONCLUSION "
    "stands and the COST ESTIMATE does not. (a) 'no accrual or COB job has ever run' is "
    "FALSE. Three accrual jobs are ACTIVE and ran the day before this fire: 'Add Accrual "
    "Transactions' (id 11) and 'Add Accrual Transactions For Loans With Income Posted As "
    "Transactions' (id 22) at 2026-08-27 16:01, and 'Add Periodic Accrual Transactions' "
    "(id 16) at 2026-08-27 16:02 [out/T352-A10-accrual-reachability.txt]. They post "
    "nothing because there is nothing to post, which is a different fact and the one "
    "that actually carries the conclusion. The COB half of the sentence IS right: 'Loan "
    "COB' (id 34) and 'Increase COB Date by 1 day' (id 33) are both INACTIVE with a null "
    "previous_run_start_time. (b) 'An accrual vector needs a NEW accrual product on clean "
    "accounts PLUS a job run' OVERSTATES THE COST. Product 28 is ACCRUAL_PERIODIC and "
    "its mapping is COMPLETE -- all thirteen financial_account_type slots 1..13 are "
    "mapped, including 7 -> gl 18, 8 -> gl 22 and 9 -> gl 16 [same capture]. The single "
    "missing ingredient is A LOAN: product 28 has zero, re-confirmed by a LEFT JOIN over "
    "every product [same capture]. The periodic accrual job is already active, so a loan "
    "on product 28, approved and disbursed, would be accrued by the next scheduled run "
    "with no new product and no job wiring. (c) WHY T352 STILL DID NOT TAKE IT, stated "
    "rather than left as a gap: slot 9 resolves to gl 16, which is a PROMOTED LEG of "
    "LDG-01, LDG-02 and LDG-03, and A2-314/403 already hold product 28's mapping "
    "inadmissible -- so the cheap route posts accrual rows into an account three graded "
    "vectors read, through a mapping the store refuses. That is a deliberate change to "
    "shared oracle state for evidence that CANNOT BE PROMOTED anyway while this "
    "capability is out of the graded domain. The expensive route -- a new "
    "ACCRUAL_PERIODIC product on clean accounts -- remains the right one, and is now "
    "known to need no job work. Raised as FU-T352-3.] "
    "[COUNT RESTATED, T352: T242's 'gl 16 -> SIXTEEN' above was measured in its own fire "
    "and T352 MOVED IT. This fire posted four further legs on gl 16 (probe transactions "
    "a29bca0816a7, a29bca9bf813, a29bcaa6a41b, a29bcb5d6fcf), so the live count is now "
    "TWENTY, gl 17 is FIVE and gl 21 is TWELVE [out/T352-A10-accrual-reachability.txt]. "
    "gl 18 -> 0 and gl 22 -> 0 are UNCHANGED, which is the pair this row's argument "
    "actually rests on. The oracle-state move is recorded in "
    ".softhouse/capture/t352-a2-next-tranche/ORACLE-STATE-MOVED-BY-T352.md. Note that "
    "these counts are PROSE IN THIS FILE, not values the harness re-derives at report "
    "time, which is exactly why they go stale and why T242 had to correct them once "
    "already.]"
)

EDITS = {
    "ledger.money.minor.unit.conversion": [RESIDUE, BALANCE],
    "ledger.multi.currency.entry": [MULTICCY],
    "ledger.accrual.entry": [ACCRUAL],
}

with open(PATH) as fh:
    doc = json.load(fh, parse_float=_no_float)

before = json.dumps(doc, sort_keys=True)
# POLARITY, MEASURED RATHER THAN GUESSED. guard_accepting_side_gap_declared()
# (conformance.sh:2311-2352) goes RED in BOTH directions: red if no accepting
# opening-balance vector exists AND the token is absent, and red if such a vector
# DOES exist and the token is STILL present (a caveat outliving its defect, the
# A2-34 F-4 shape). LDG-05-openingbalance-accepted-empty-ledger closed that hole,
# so the correct state today is TOKEN ABSENT -- and this script's job is to leave
# it absent. The first draft of this check asserted the opposite and fired; the
# guard caught the script, which is the point of writing it.
if "T305-ACCEPTING-SIDE-GAP" in before:
    sys.exit("REFUSING: the T305-ACCEPTING-SIDE-GAP token is present. LDG-05 closed the "
             "accepting-side hole, so guard_accepting_side_gap_declared() is ALREADY red "
             "on the stale-declaration arm and this script must not be blamed for it.")

seen = set()
for cap in doc["capabilities"]:
    name = cap["name"]
    if name not in EDITS:
        continue
    seen.add(name)
    for chunk in EDITS[name]:
        marker = chunk[:60]
        if marker in cap["evidence"]:
            sys.exit("REFUSING: %s already carries this T352 correction. This script is "
                     "not idempotent by appending twice." % name)
        cap["evidence"] = cap["evidence"] + chunk

missing = set(EDITS) - seen
if missing:
    sys.exit("REFUSING: capabilities not found in the file: %s" % sorted(missing))

# graded-domain flags must NOT move: every one of these stays exactly as it was.
flags = {c["name"]: c["in_graded_domain"] for c in doc["capabilities"]}
assert flags["ledger.money.minor.unit.conversion"] is True
assert flags["ledger.multi.currency.entry"] is False
assert flags["ledger.accrual.entry"] is False

out = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
if "T305-ACCEPTING-SIDE-GAP" in out:
    sys.exit("REFUSING: this write would INTRODUCE the T305-ACCEPTING-SIDE-GAP token and "
             "make guard_accepting_side_gap_declared() red on the stale-declaration arm.")
with open(PATH, "w") as fh:
    fh.write(out)
print("T352: applied %d correction(s) across %d capabilities; no flag and no count moved."
      % (sum(len(v) for v in EDITS.values()), len(EDITS)))
