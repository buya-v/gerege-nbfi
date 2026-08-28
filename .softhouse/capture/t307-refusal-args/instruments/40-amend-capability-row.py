#!/usr/bin/env python3
"""T307 instrument 40 -- append T307's paragraph to capabilities-ledger.json.

WHY MECHANICALLY. That row's `evidence` field carries a sentence T307 makes false:

    "And T287's A1-01 and A2-02 are adjudicated NOT PROMOTABLE in that same file,
     by measurement rather than by preference: A2-02's captured response body is
     BYTE-IDENTICAL to A2-01's ... and A1-01 differs from A1-02 in no graded cell."

The FIRST half is now wrong -- A2-02 IS promoted -- and the SECOND half is still
right, and gets MORE right, because with the args cell wired A1-01 STILL adds no
kill. So the sentence is amended in place rather than deleted, and the run REFUSES
if it cannot find it: a caveat that outlives its defect is the A2-34 F-4 defect,
and a rewriter that silently finds nothing to rewrite is how one survives.

It also appends the T307 paragraph naming what is STILL not graded, because the
row's own convention is that every promotion states its remaining gaps in the same
diff.

EXIT: 0 amended; 2 a precondition failed.
"""
import json
import sys
from pathlib import Path

SOFTHOUSE = Path(__file__).resolve().parents[3]
REG = SOFTHOUSE / "vectors" / "capabilities-ledger.json"
ROW = "ledger.opening.balance.and.closure"
PROBE = "T307-CAPROW:"

STALE = (
    "And T287's A1-01 and A2-02 are adjudicated NOT PROMOTABLE in that same file, by measurement "
    "rather than by preference: A2-02's captured response body is BYTE-IDENTICAL to A2-01's (both "
    "sha256 c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2) despite a different "
    "transaction date, and A1-01 differs from A1-02 in no graded cell."
)

FRESH = (
    "And T287's A1-01 and A2-02 were adjudicated NOT PROMOTABLE in that same file, by measurement "
    "rather than by preference: A2-02's captured response body is BYTE-IDENTICAL to A2-01's (both "
    "sha256 c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2) despite a different "
    "transaction date, and A1-01 differs from A1-02 in no graded cell. [HALF SUPERSEDED BY T307, "
    "and left visible rather than deleted because the surviving half is what a reader needs. "
    "A2-02 IS NOW PROMOTED, as LDG-REFUSE-06 -- see the T307 paragraph at the end of this row. "
    "A1-01 IS STILL NOT PROMOTABLE and the arg cell does not change that: it echoes its OWN "
    "transaction date under the SAME selector A1-02 uses, so it adds a graded cell and NO kill, "
    "and this store's promotion test is the kill.]"
)

T307_PARA = (
    " ***** THE ACCOUNTING_CLOSED REFUSAL'S ECHOED DATE IS NOW GRADED, AND T294's REFUSAL TO GRADE "
    "ITS OWN args IS UPHELD IN THE SAME DIFF. [T307, closing T295 backlog B-3 with NO ORACLE "
    "CONTACT.] ***** WHAT WAS MISSING AND WHY IT MATTERED, MEASURED BEFORE IT WAS FIXED: "
    "ledger-wrong-accounting-closed-echoes-transaction-date -- a port that implements the closure "
    "boundary EXACTLY RIGHT, returns the oracle's status, globalisation code and message, and "
    "quotes back the SUBMITTED transactionDate where :637-638 constructs ACCOUNTING_CLOSED with "
    "latestGLClosure.getClosingDate() -- was run against the store as it stood WITHOUT "
    "LDG-REFUSE-06 and SURVIVED: ledger oracle-refusal PASS 5 FAIL 0 "
    "[.softhouse/capture/t307-refusal-args/out/20-armB-mutant-without-LDG-REFUSE-06.txt]. It is "
    "INDISTINGUISHABLE from a correct port on LDG-REFUSE-04, because A2-01 was posted ON the "
    "closing date and the two dates are EQUAL there. WHAT CLOSED IT: LDG-REFUSE-06, promoted from "
    "T287's A2-02 -- transaction 2026-01-15 against a closure dated 2026-01-31, oracle echoed "
    "2026-01-31 -- which kills it on ONE cell, refusal.arg0_value, and on nothing else "
    "[out/10-armA-mutant-full-store.txt]. NO PROBE WAS FIRED; the bytes have been on disk since "
    "2026-08-23 and MANIFEST.sha256 verifies 87/87. THE CELL IS A SELECTOR, NOT A DATE, and that "
    "is the whole formulation: expect.refusal.arg_echo names WHICH declared input the oracle "
    "echoed ('latest_closing_date' at :637-638, 'transaction_date' at :631) and the comparator "
    "RESOLVES it from the request, so no calendar literal is ever an expectation and the claim "
    "survives re-capture on any dates. Refusal.Arg0Value carries json:\"-\", so a vector CANNOT "
    "write a date literal there even deliberately -- it dies at strict decode. WHY OB-01 STAYS "
    "UNGRADED, on two grounds admit.go now ENFORCES rather than a reader remembering: its "
    "args[0].value is a JSON ARRAY of 26 LIVE TRANSACTION IDS (ApiParameterError special-cases "
    "LocalDate into a yyyy-MM-dd STRING and hands everything else to Gson as-is, "
    "ApiParameterError.java:95-105) and the vocabulary is CLOSED to the two scalar dates; and "
    "request.posted_non_contra_transaction_ids was itself transcribed FROM that same wire field, "
    "so a selector resolving against it would compare the captured body with a copy of itself. "
    "THE ZONE WAS DETERMINED BEFORE THE CELL WAS WIRED, per T329: both graded dates are "
    "java.time.LocalDates parsed by LocalDateTime.parse(s, fmt).toLocalDate() with no ZoneId "
    "[JsonParserHelper.java:544-547,558-586] and rendered by "
    "DateTimeFormatter('yyyy-MM-dd').format(LocalDate) [ApiParameterError.java:97-99] -- NO CLOCK "
    "AT ANY STEP -- and the two WALL-CLOCK dates in this arm, request.business_date "
    "(getLocalDateOfTenant) and glclosures.createdDate (JVM zone, T329), are NOT what :631 or :637 "
    "pass. WHAT IS STILL NOT GRADED AFTER T307: the two REVERSAL items above are untouched; "
    "T296's ARM B is still unkilled; and the refusal PRECEDENCE between :630 and :636 is STILL "
    "graded by nothing (FU-T328-6) -- the arg cell does NOT make it observable, because refusal.code "
    "and refusal.message already discriminate the two guards and what is missing is a CAPTURE of a "
    "request violating both rules, not a cell."
)


def main() -> int:
    d = json.loads(REG.read_text())
    rows = [c for c in d["capabilities"] if c["name"] == ROW]
    if len(rows) != 1:
        print(f"{PROBE} FATAL {len(rows)} rows named {ROW}, want 1", file=sys.stderr)
        return 2
    row = rows[0]
    ev = row["evidence"]
    if T307_PARA.strip() in ev:
        print(f"{PROBE} FATAL the T307 paragraph is already present; refusing to duplicate", file=sys.stderr)
        return 2
    if STALE not in ev:
        print(f"{PROBE} FATAL the sentence T307 supersedes is NOT in this row's evidence. It reads:",
              file=sys.stderr)
        print(f"{PROBE}   {STALE}", file=sys.stderr)
        print(f"{PROBE} This instrument exists to amend it in the same pass that makes half of it "
              f"false; finding nothing to amend means the row was edited underneath it and the "
              f"amendment must be re-derived by hand.", file=sys.stderr)
        return 2
    row["evidence"] = ev.replace(STALE, FRESH, 1) + T307_PARA
    REG.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
    print(f"{PROBE} VERDICT OK amended {ROW}: stale half superseded, T307 paragraph appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
