#!/usr/bin/env python3
"""T307 instrument 20 -- BUILD LDG-REFUSE-06 from T287's committed A2-02 bytes.

NO ORACLE CONTACT. Every graded value is READ from
`.softhouse/capture/t287-closure-refusals/`, never typed. The probe is NOT re-fired
and MUST NOT BE: `guard-probe-expiry.sh` exits 1 today because the GLClosure that
made A2-02 a refusal was deleted in T287's own fire, so re-sending this balanced,
postable body would POST TWO JOURNAL ENTRIES THAT CANNOT BE DELETED (P-92: a probe
whose safety comes from an EXTERNAL PRECONDITION rather than from its own content
is a loaded weapon).

WHY A BUILDER AND NOT A HAND-WRITTEN FILE. A2-02 is being promoted for ONE reason:
it is the only capture in this corpus where the date the oracle ECHOED differs from
the date the caller SUBMITTED. If that were not true of the bytes, the vector would
be corpus inflation -- a second file no implementation could fail independently,
which is exactly what T295 refused to commit. So the builder REFUSES TO EMIT unless
it can re-derive that property from the bytes:

  G-1  digests match the vector's declared provenance (both artefacts)
  G-2  errors[0].args[0].value is a STRING, not an array   [the eligibility rule]
  G-3  that string EQUALS the closing date the rig created
  G-4  that string DIFFERS from the request's own transactionDate  [the whole point]
  G-5  the response body is byte-identical to A2-01's, so the three EXISTING cells
       provably cannot be what this vector adds
  G-6  transactionDate <= closingDate  (the :636 relation the refusal asserts)
  G-7  transactionDate <= businessDate (so :630 did not answer first)

A guard that cannot fail is worse than none, so each of the seven is printed with
the two values it compared.

EXIT: 0 vector written; 2 a guard refused. Never conflated (P-80).
"""
import hashlib
import json
import sys
from pathlib import Path

SOFTHOUSE = Path(__file__).resolve().parents[3]
RIG = SOFTHOUSE / "capture" / "t287-closure-refusals"
OUT = SOFTHOUSE / "vectors" / "ledger" / "LDG-REFUSE-06-preclosure-entry-before-closing-date-echoes-the-closing-date.json"

PROBE = "T307-BUILD:"

BODY = RIG / "out" / "A2-02-preclosure-before.json"
REQ = RIG / "out" / "A2-02-preclosure-before.req"
STATUS = RIG / "out" / "A2-02-preclosure-before.status"
SIBLING_BODY = RIG / "out" / "A2-01-preclosure-on-date.json"
CLOSURE_RECIPE = RIG / "req" / "a2-00-create-closure.json"

# The business date T289 derived and T295 carried into LDG-REFUSE-04 and -05. It is
# NOT re-derived here and it is NOT read from a clock: it is the value the sibling
# vector already declares, so this vector and that one cannot drift apart.
SIBLING_VECTOR = SOFTHOUSE / "vectors" / "ledger" / "LDG-REFUSE-04-preclosure-entry-on-closing-date.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    fails = []

    def guard(name: str, ok: bool, detail: str) -> bool:
        print(f"{PROBE} {'ok  ' if ok else 'FAIL'} {name}: {detail}")
        if not ok:
            fails.append(f"{name}: {detail}")
        return ok

    body_raw = BODY.read_bytes()
    body = json.loads(body_raw)
    req = json.loads(REQ.read_bytes())
    status = STATUS.read_text().strip()
    closure = json.loads(CLOSURE_RECIPE.read_bytes())
    sibling = json.loads(SIBLING_VECTOR.read_text())

    body_digest = sha256(BODY)
    req_digest = sha256(REQ)
    guard(
        "G-1 digests",
        body_digest == "c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2"
        and req_digest == "6d1ca1e11a48154212bfac97df9b5c697142337644735a471f5894a5dd9ce3ea",
        f"body {body_digest[:16]}… req {req_digest[:16]}…",
    )

    err = body["errors"][0]
    args = err["args"]
    arg0 = args[0].get("value") if args else None
    guard(
        "G-2 args[0].value is a SCALAR STRING",
        isinstance(arg0, str),
        f"type={type(arg0).__name__} value={arg0!r}; args has {len(args)} member(s), "
        f"the 2nd and 3rd being the two nulls :637-638 passes",
    )

    closing = closure["closingDate"]
    txn = req["transactionDate"]
    business = sibling["request"]["business_date"]

    guard("G-3 echo == CLOSING date", arg0 == closing, f"args[0].value {arg0!r} vs closingDate {closing!r}")
    guard(
        "G-4 echo != SUBMITTED date  <-- THE REASON THIS VECTOR EXISTS",
        arg0 != txn,
        f"args[0].value {arg0!r} vs transactionDate {txn!r}",
    )
    guard(
        "G-5 body byte-identical to A2-01",
        body_raw == SIBLING_BODY.read_bytes(),
        "so the three EXISTING refusal cells provably add nothing here",
    )
    guard("G-6 txn <= closing (:636 refuses)", txn <= closing, f"{txn!r} <= {closing!r}")
    guard("G-7 txn <= business (:630 did not answer first)", txn <= business, f"{txn!r} <= {business!r}")
    guard("G-8 status", status == "403", f"status file reads {status!r}")

    if fails:
        for f in fails:
            print(f"{PROBE} FATAL {f}", file=sys.stderr)
        return 2

    note = (
        "WHAT THIS VECTOR GRADES, AND IT IS EXACTLY ONE THING NO OTHER VECTOR IN THIS STORE CAN: "
        "that the ACCOUNTING_CLOSED refusal echoes the CLOSING date and NOT the submitted "
        "transaction date. :637-638 constructs the exception with latestGLClosure.getClosingDate(); "
        ":631, five lines above and in the same method, constructs FUTURE_DATE with transactionDate. "
        "THE SAME WIRE FIELD MEANS DIFFERENT THINGS IN THE TWO REFUSALS, and A2-02 is the only "
        "capture in this corpus that separates them -- it posted " + txn + " against a closure "
        "dated " + closing + " and the oracle answered " + arg0 + ". "
        "WHY IT WAS NOT PROMOTABLE BEFORE, MEASURED RATHER THAN ASSERTED: its captured response "
        "body is BYTE-IDENTICAL to A2-01's (both sha256 " + body_digest + "), so on the three cells "
        "the Refusal shape had -- http_status, code, message -- it is indistinguishable from "
        "LDG-REFUSE-04 and no implementation in this harness could fail it independently. T295 "
        "adjudicated it NOT PROMOTABLE for that reason and filed the fix as backlog B-3. T307 is "
        "that fix. "
        "THE VECTOR DOES NOT GRADE A DATE LITERAL, AND THAT IS THE WHOLE FORMULATION. "
        "expect.refusal.arg_echo is a SELECTOR -- 'latest_closing_date' -- naming which input the "
        "vector ALREADY declares the oracle echoed; the comparator resolves it from "
        "request.latest_closing_date at grading time. So no calendar appears in any expectation, "
        "the claim survives re-capture on any dates whatsoever, and the cell asserts a RELATION in "
        "exactly the sense T289's date strategy (c) requires of request.business_date and "
        "request.latest_closing_date. "
        "WHY OB-01's args IS STILL NOT GRADED, so T294's deliberate refusal is UPHELD rather than "
        "quietly overturned, and now as a RULE admit.go enforces rather than a judgement a reader "
        "must remember: (1) STRUCTURAL -- errors[0].args[0].value is a JSON STRING here and a JSON "
        "ARRAY on OB-01, because ApiParameterError special-cases exactly one type, rendering a "
        "LocalDate as yyyy-MM-dd and handing everything else to Gson as-is "
        "[ApiParameterError.java:95-105], and :815 passes a List<String> as one vararg Object. The "
        "selector vocabulary is CLOSED to the two scalar date inputs, so OB-01's claim cannot be "
        "written down in this schema at all. (2) PROVENANCE -- LDG-REFUSE-03's "
        "request.posted_non_contra_transaction_ids was itself TRANSCRIBED FROM "
        "errors[0].args[0].value, so resolving a selector against it would compare the captured "
        "body with a copy of itself, which is the circularity registry.go refuses; and it is "
        "tenant-mutable, so any unrelated posting to the tenant would turn the claim red. Both "
        "selectors this schema admits fail neither test: request.transaction_date comes from the "
        "caller's own committed .req wire bytes and request.latest_closing_date from "
        "req/a2-00-create-closure.json, confirmed in the database by out/M-09-state-during-closure.txt. "
        "THE ZONE AND CLOCK OF THE GRADED DATE, DETERMINED BEFORE THE CELL WAS WIRED because T329 "
        "measured that two Fineract fields spelled the same can be different quantities on "
        "different clocks: GLClosure.closingDate is a java.time.LocalDate on "
        "@Column(name='closing_date') [GLClosure.java:53-54], set from the create-closure request "
        "by JsonParserHelper's LocalDateTime.parse(s, fmt).toLocalDate() -- no ZoneId, no Instant "
        "[JsonParserHelper.java:544-547, 558-586] -- and rendered by "
        "DateTimeFormatter('yyyy-MM-dd').format(LocalDate) [ApiParameterError.java:97-99], which "
        "over a LocalDate is a pure field render. NO CLOCK IS READ AT ANY STEP. The two "
        "WALL-CLOCK-derived dates in this arm -- request.business_date "
        "(DateUtils.getLocalDateOfTenant, tenant zone) and glclosures.createdDate (audit insert, "
        "JVM zone, T329) -- are NOT what :637 passes, so this cell cannot pass or fail on the hour "
        "CI runs, and that is checkable at :637 rather than merely true today. "
        "WHAT THIS VECTOR DOES NOT SETTLE. It says nothing about the BOUNDARY: " + txn + " is "
        "strictly before " + closing + ", so it is refused under BOTH the inclusive reading the "
        "code implements and the exclusive reading the message describes, and it pins neither. "
        "LDG-REFUSE-04 is the vector that pins the boundary, and the two are complementary rather "
        "than redundant -- 04 has equal dates and can grade the boundary but not the echo, 06 has "
        "differing dates and can grade the echo but not the boundary. It also does not settle the "
        "PRECEDENCE between :630 and :636 (FU-T328-6): this request violates only the closure rule. "
        "NO LEGS AND NO TOTALS ARE ASSERTED -- the request was refused, so no entry exists and no "
        "amount was observed; the two amount_major_text tokens are the CALLER'S OWN characters from "
        "the committed .req wire bytes (the integer token `1000000`, no decimal point, denoting MNT "
        "1,000,000.00 = 100000000 minor units) and are graded by nothing. cmpMoney is unreachable "
        "from diffRefusal [grade.go], so this vector contributes ZERO money cells, exactly as the "
        "five refusal vectors before it do. "
        "NO BALANCE IS GRADED. acc_gl_journal_entry carries office_running_balance and "
        "organization_running_balance and GATE G-12 IS OPEN on exactly them: A2-29 MEASURED them to "
        "be a SECOND SOURCE OF TRUTH rather than a cache. This vector's schema has NO FIELD for "
        "either column. Balances are DERIVED, never written, and never read back."
    )

    rerun = (
        "THIS VECTOR IS GRADED BY REPLAY AGAINST A PORT AND MUST NEVER BE RE-FIRED AT THE ORACLE, "
        "and the reason is the same one LDG-REFUSE-04 states -- read it before anything else here. "
        "A2-02's body is a VALID, BALANCED, POSTABLE manual journal entry: GL 4 and GL 2 are both "
        "manual_journal_entries_allowed = t, disabled = f, account_usage = 1 (DETAIL), debits equal "
        "credits, and " + txn + " is in the past. THE ONLY THING THAT REFUSED IT WAS A GLClosure "
        "THAT NO LONGER EXISTS -- T287 created it (id 1) to take this capture and DELETED it in the "
        "same fire, so acc_gl_closure is empty and re-sending this body TODAY POSTS TWO JOURNAL "
        "ENTRIES INTO THE REFERENCE ORACLE. A POSTED JOURNAL ENTRY CANNOT BE DELETED: GLClosure has "
        "no @SQLDelete and deleteGLClosure is a hard delete (:135), while the only 'undo' for a "
        "journal entry is posting more entries. guard-probe-expiry.sh measures the precondition, "
        "fails closed, and exits 1 today. "
        "THE RELATION THIS VECTOR ASSERTS, which no calendar can falsify: given office 1, a latest "
        "GLClosure closing on request.latest_closing_date, and a transaction dated "
        "request.transaction_date with transaction_date <= latest_closing_date AND transaction_date "
        "<= business_date, the answer is HTTP 403 error.msg.glJournalEntry.invalid.accounting.closed "
        "WITH errors[0].args[0].value EQUAL TO request.latest_closing_date. "
        "WHAT WOULD MAKE IT FALSE: a change at :637-638 to construct the exception with a different "
        "date, or a change to GlJournalEntryInvalidReason.ACCOUNTING_CLOSED's code or message. Both "
        "are oracle-SOURCE changes, found by re-reading the pinned commit and NOT by re-posting. "
        "THE ANSWER IN THAT CASE IS RE-CAPTURE, NOT EXEMPTION: this schema admits no "
        "invariant_exemptions at all."
    )

    citation = (
        "T307, promoting T287's A2-02 bytes under T295 backlog B-3 and T289's date rule. NO PROBE "
        "WAS FIRED and nothing in out/ was rewritten; MANIFEST.sha256 verifies 87/87 unchanged, "
        "re-checked by T307 before transcription. HTTP status " + status + " read from "
        "out/A2-02-preclosure-before.status. code and message read from errors[0] of the captured "
        "response body (userMessageGlobalisationCode and defaultUserMessage, byte-identical to "
        "developerMessage on this error). THE ARG ECHO IS OBSERVED, NOT INFERRED: "
        "errors[0].args[0].value reads " + arg0 + " while the same body's request carried "
        "transactionDate " + txn + " -- the builder that emitted this file "
        "(.softhouse/capture/t307-refusal-args/instruments/20-build-ldg-refuse-06.py) REFUSES to "
        "write unless it can re-derive that inequality from the bytes, so the one property this "
        "vector is promoted for cannot be asserted without being measured. request.transaction_date, "
        "office_id and the two amount tokens are read from the committed .req wire-bytes artefact. "
        "request.latest_closing_date is read from req/a2-00-create-closure.json's closingDate and "
        "confirmed against out/M-09-state-during-closure.txt (acc_gl_closure id 1, office 1, "
        "closing_date 2026-01-31), with out/M-12-state-after-delete.txt showing it gone afterwards. "
        "request.business_date is COPIED FROM THE SIBLING VECTOR LDG-REFUSE-04 rather than "
        "re-derived, so the two cannot drift; it is DERIVED, not read from an endpoint, and T329 "
        "records that as an ambiguity this vector inherits and does not fix (FU-T328-3, "
        "FU-T307-2) -- it is inert for the graded cell here, which resolves latest_closing_date. "
        "The chart rows in request.accounts are DATA (DEC-2 §4.5), transcribed unchanged from "
        "LDG-REFUSE-04, which recorded them from T287's handoff §2 and T289-CORRECTIONS.md §1 "
        "(GL 4 and GL 2 on tenant gerege both manual_journal_entries_allowed = t, disabled = f, "
        "account_usage = 1 DETAIL)."
    )

    vector = {
        "schema": "gerege.ledger.vector/v1",
        "case_id": "LDG-REFUSE-06-preclosure-entry-before-closing-date-echoes-the-closing-date",
        "context": "ledger",
        "class": "oracle-refusal",
        "title": (
            "THE ACCOUNTING_CLOSED REFUSAL QUOTES THE CLOSING DATE BACK, NOT THE DATE YOU SENT. "
            "A2-02 posted a balanced manual journal entry dated " + txn + " to office 1 while that "
            "office's latest GLClosure closed " + closing + " -- THE TWO DIFFERENT -- and the "
            "oracle returned HTTP 403 error.msg.glJournalEntry.invalid.accounting.closed with "
            "errors[0].args[0].value = " + arg0 + ", the CLOSING date. :637-638 constructs the "
            "exception with latestGLClosure.getClosingDate() while :631, five lines above, "
            "constructs FUTURE_DATE with transactionDate: the same wire field means different "
            "things in the two refusals. This capture's response body is BYTE-IDENTICAL to A2-01's, "
            "so it can add nothing on http_status, code or message -- the whole of its content is "
            "in the fourth cell, and until T307 the Refusal shape had no fourth cell."
        ),
        "dec2_revision": sibling["dec2_revision"],
        "_note": note,
        "capabilities_required": ["ledger.refusal.parity", "ledger.opening.balance.and.closure"],
        "provenance": {
            "kind": "capture",
            "capture_ref": ".softhouse/capture/t287-closure-refusals/out/A2-02-preclosure-before.json",
            "capture_sha256": body_digest,
            "capture_case_id": "A2-02-preclosure-before",
            "request_capture_ref": ".softhouse/capture/t287-closure-refusals/out/A2-02-preclosure-before.req",
            "request_capture_sha256": req_digest,
            "request_capture_case_id": "A2-02-preclosure-before",
            "rerun_invariant": rerun,
            "citation": citation,
        },
        "oracle": {
            "fineract_commit": sibling["oracle"]["fineract_commit"],
            "seam": "ledger_rest_posting",
            "captured_at": "2026-08-23T00:17:56Z",
        },
        "request": {
            "product_id": 0,
            "product_type": "",
            "accounting_rule": "",
            "slot_family": "",
            "slot_code": 0,
            "payment_type_id": None,
            "seam": "ledger_rest_posting",
            "office_id": req["officeId"],
            "currency": {"code": req["currencyCode"], "minor_unit_digits": 2},
            "transaction_id": "",
            "manual_entry": True,
            "transaction_date": txn,
            "business_date": business,
            "latest_closing_date": closing,
            "transaction_amount_major_text": "",
            "accounts": sibling["request"]["accounts"],
            "legs": [
                {
                    "gl_account_id": req["debits"][0]["glAccountId"],
                    "entry_side": "DEBIT",
                    "amount_major_text": str(req["debits"][0]["amount"]),
                },
                {
                    "gl_account_id": req["credits"][0]["glAccountId"],
                    "entry_side": "CREDIT",
                    "amount_major_text": str(req["credits"][0]["amount"]),
                },
            ],
        },
        "expect": {
            "kind": "refusal",
            "http_status": int(status),
            "legs": [],
            "total_debits_minor": "",
            "total_credits_minor": "",
            "refusal": {
                "http_status": int(status),
                "code": err["userMessageGlobalisationCode"],
                "message": err["defaultUserMessage"],
                "arg_echo": "latest_closing_date",
            },
        },
        "graded_against": [
            {
                "impl": "ledger-wrong-accounting-closed-echoes-transaction-date",
                "kind": "structural",
                "margin_minor": "0",
                "divergent_cells": ["refusal.arg0_value"],
                "note": (
                    "ONE CELL, AND THAT IS THE POINT. This port gets the closure BOUNDARY exactly "
                    "right -- it refuses precisely the requests the oracle refuses, with the "
                    "oracle's status, code and message -- and quotes back the date the caller SENT "
                    "instead of the date the period CLOSED. On LDG-REFUSE-04 it is "
                    "INDISTINGUISHABLE from the reference implementation, because A2-01 was posted "
                    "ON the closing date and the two dates are equal there; it dies here alone, "
                    "where they differ by 16 days. It is the natural port: an error that quotes the "
                    "input it rejected is what a reader of :631 -- the OTHER date refusal, five "
                    "lines up, which does exactly that -- would write."
                ),
            }
        ],
        "invariant_exemptions": [],
    }

    OUT.write_text(json.dumps(vector, indent=2, ensure_ascii=False) + "\n")
    print(f"{PROBE} VERDICT OK wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
