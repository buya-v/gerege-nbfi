#!/usr/bin/env python3
"""T307 instrument 10 -- amend the two COMMITTED date-refusal vectors in place.

WHAT IT DOES, AND WHY IT IS A SCRIPT RATHER THAN A HAND EDIT. Both vectors already
say, in their own `_note`, that `errors[0].args is NOT graded` and WHY. Those two
sentences are now FALSE, and a caveat outliving its defect is the A2-34 F-4 defect
this store has been bitten by before. So the amendment and the caveat retraction
happen in ONE mechanical pass, and the pass REFUSES if either sentence is missing
-- a rewriter that silently finds nothing to rewrite is how a stale caveat survives.

It adds:
  * expect.refusal.arg_echo -- the SELECTOR, never a date.
  * refusal.arg0_value to the graded_against divergent_cells of the mutant that
    returns a POSTED ENTRY where the vector expects a refusal. Both mutants here
    do exactly that, so all four cells diverge, not three.

NOTHING IN .softhouse/capture/t287-closure-refusals/ IS TOUCHED. This reads the
vector store only. NO ORACLE CONTACT.

EXIT: 0 both vectors amended; 2 a precondition failed. Never conflated.
"""
import json
import sys
from pathlib import Path

SOFTHOUSE = Path(__file__).resolve().parents[3]
STORE = SOFTHOUSE / "vectors" / "ledger"

PROBE = "T307-AMEND:"

# (file, arg_echo selector, the stale sentence that must be present, its replacement)
PLAN = [
    (
        "LDG-REFUSE-04-preclosure-entry-on-closing-date.json",
        "latest_closing_date",
        'errors[0].args is NOT graded: it carries "2026-01-31", which is the CLOSING date and not '
        "this request's transaction date (:637 constructs the exception with "
        "latestGLClosure.getClosingDate()), and the Refusal shape has three cells and no fourth. On "
        "THIS request the two dates coincide, so nothing is lost here; the capture that shows the "
        "asymmetry is A2-02, adjudicated NOT PROMOTABLE for exactly that reason.",
        "errors[0].args IS NOW GRADED, as expect.refusal.arg_echo -> the cell "
        "refusal.arg0_value [T307, closing T295 backlog B-3]. THE VECTOR DOES NOT CARRY THE DATE: "
        "it carries a SELECTOR naming which input it already declares the oracle echoed, and the "
        "comparator resolves it from request.latest_closing_date, so no calendar literal is graded "
        "and the claim survives re-capture on any dates. Here the selector is latest_closing_date "
        "because :637-638 constructs ACCOUNTING_CLOSED with latestGLClosure.getClosingDate(), where "
        ":631 five lines above constructs FUTURE_DATE with transactionDate -- THE SAME WIRE FIELD "
        "MEANS DIFFERENT THINGS IN THE TWO REFUSALS. ON THIS VECTOR THE CELL CANNOT DISCRIMINATE "
        "AND THAT IS STATED PLAINLY: A2-01 was posted ON the closing date, so transaction_date and "
        "latest_closing_date are EQUAL here and a port echoing either one passes. The capture that "
        "separates them is A2-02, now promoted as LDG-REFUSE-06, and it is what kills "
        "ledger-wrong-accounting-closed-echoes-transaction-date. THE ZONE IS SETTLED BEFORE THE "
        "CELL IS GRADED, per T329: GLClosure.closingDate is a LocalDate on @Column(closing_date) "
        "set by the same zone-free parse as any request date [GLClosure.java:53-54,70-72; "
        "JsonParserHelper.java:544-547,558-586], and ApiParameterError renders it with "
        "DateTimeFormatter(\"yyyy-MM-dd\").format(LocalDate) [ApiParameterError.java:97-99] -- NO "
        "ZoneId, NO Instant, NO clock, at any step. The two WALL-CLOCK dates in this arm, "
        "request.business_date and glclosures.createdDate, are NOT echoed into args by :637 and are "
        "graded by nothing. WHAT THE CELL DOES NOT RESCUE, so the promotion is not read as more "
        "than it is: OB-01's args stays UNGRADED on LDG-REFUSE-03, on two independent grounds now "
        "ENFORCED BY admit.go rather than remembered -- its args[0].value is a JSON ARRAY and the "
        "selector vocabulary admits only the two scalar dates, and "
        "request.posted_non_contra_transaction_ids was itself transcribed FROM that same wire "
        "field, so resolving a selector against it would compare the captured body with a copy of "
        "itself. T294's refusal is UPHELD, as a rule.",
    ),
    (
        "LDG-REFUSE-05-future-dated-entry-one-day-after-business-date.json",
        "transaction_date",
        'errors[0].args is NOT graded; it carries "2026-08-24", which on THIS refusal is the '
        "submitted transaction date (:631 constructs the exception with transactionDate) and NOT "
        "the closing date the sibling refusal echoes -- an asymmetry recorded in T287 §1 item 4 "
        "and re-measured by T295, and one the three-cell Refusal shape has no slot for.",
        "errors[0].args IS NOW GRADED, as expect.refusal.arg_echo -> the cell "
        "refusal.arg0_value [T307, closing T295 backlog B-3]. THE VECTOR DOES NOT CARRY THE DATE: "
        "it carries a SELECTOR, and the comparator resolves it from request.transaction_date, so "
        "the literal 2026-08-24 is graded by nothing and the claim survives re-capture on any "
        "dates. The selector is transaction_date because :631 constructs FUTURE_DATE with "
        "transactionDate -- and NOT with the business date it just compared against, which is the "
        "load-bearing fact for T329's hazard: the ONE quantity on this path that is derived from a "
        "WALL CLOCK (DateUtils.getLocalDateOfTenant, tenant zone Asia/Ulaanbaatar) NEVER REACHES "
        "THE WIRE. So this cell cannot pass or fail on the hour CI runs, and that is checkable at "
        ":631 rather than true-today. The render adds nothing either: "
        "DateTimeFormatter(\"yyyy-MM-dd\").format(LocalDate) over a java.time.LocalDate has no "
        "instant and no zone [ApiParameterError.java:97-99], and the inbound parse is "
        "LocalDateTime.parse(s, fmt).toLocalDate() with no ZoneId "
        "[JsonParserHelper.java:544-547,558-586]. WHAT THIS CELL DOES NOT ADD HERE: it does not "
        "make A1-01 promotable. A1-01 echoes its own transaction date too, under the same selector, "
        "so it still kills nothing A1-02 does not -- see T307's handoff for the one contrived "
        "predicate that would separate them and why it is not a defect shape. AND IT DOES NOT "
        "RESCUE OB-01: LDG-REFUSE-03's args stays UNGRADED, on two independent grounds now ENFORCED "
        "BY admit.go rather than remembered -- its args[0].value is a JSON ARRAY and the selector "
        "vocabulary admits only the two scalar dates, and "
        "request.posted_non_contra_transaction_ids was itself transcribed FROM that same wire "
        "field. T294's refusal is UPHELD, as a rule.",
    ),
]

# The mutant on each of these two vectors returns a POSTED ENTRY where a refusal was
# expected, so the args cell diverges too -- diffRefusal's got==nil arm compares it
# against the empty string. Named explicitly because a divergent_cells entry the
# comparator does not emit is INADMISSIBLE (T9-F1b), and so is one it emits and the
# vector under-reports.
NEW_CELL = "refusal.arg0_value"


def main() -> int:
    bad = []
    for name, selector, stale, replacement in PLAN:
        p = STORE / name
        if not p.is_file():
            bad.append(f"{name}: NOT FOUND at {p}")
            continue
        d = json.loads(p.read_text())
        ref = d["expect"]["refusal"]
        if ref.get("arg_echo"):
            bad.append(f"{name}: already carries arg_echo {ref['arg_echo']!r}; refusing to rewrite")
            continue
        ref["arg_echo"] = selector

        note = d["_note"]
        if stale not in note:
            bad.append(
                f"{name}: the stale sentence {stale!r} is NOT in _note. This instrument exists to "
                "retract it in the same pass that makes it false; finding nothing to retract means "
                "the note was edited underneath it and the retraction must be re-derived by hand"
            )
            continue
        d["_note"] = note.replace(stale, replacement, 1)

        for cf in d["graded_against"]:
            if NEW_CELL not in cf["divergent_cells"]:
                cf["divergent_cells"].append(NEW_CELL)
            cf["note"] += (
                " [T307] The kill is now FOUR cells, not three: this port returned a POSTED ENTRY "
                "where an oracle refusal was expected, and refusal.arg0_value is compared on that "
                "arm too -- the comparator names and counts every refusal cell when the shape "
                "itself is wrong, rather than skipping them."
            )

        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
        print(f"{PROBE} amended {name} arg_echo={selector} +{NEW_CELL}")

    if bad:
        for b in bad:
            print(f"{PROBE} FATAL {b}", file=sys.stderr)
        return 2
    print(f"{PROBE} VERDICT OK 2 vectors amended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
