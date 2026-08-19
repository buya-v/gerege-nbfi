#!/usr/bin/env python3
"""T41 edit batch 18 — F-1/F-2 leak closure: contract.go, section 9, revision history."""
import io
import sys

LOG = []


def patch(path, pairs):
    s = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        c = s.count(old)
        if c != 1:
            sys.exit("FAIL in %s: found %d for:\n%s" % (path, c, old[:240]))
        s = s.replace(old, new)
        LOG.append("ok %s: %s" % (path.rsplit('/', 1)[-1], old[:60].replace("\n", " ")))
    io.open(path, "w", encoding="utf-8").write(s)


# --- contract.go -------------------------------------------------------------
patch("nexus/internal/apps/loanschedule/contract/contract.go", [
    ("""	//	k     := whole months from seed to FromDate, EXCEPT that when FromDate is
	//	         the last day of its month and seed's day > FromDate's day, it is
	//	         measured to FromDate.plusDays(1)               (:1430-1433)""",
     """	//	k     := MONTHS.between(seed, FromDate)  -- Java LocalDate.monthsUntil,
	//	         i.e. packed = (year*12 + month-1)*32 + day; k = (p2-p1)/32
	//	         truncated toward zero (DateUtils.java:308-317).  THIS IS NOT
	//	         "the largest k with seed + k months <= FromDate": the two differ
	//	         exactly when plusMonths would have CLAMPED, which is exactly the
	//	         condition the special case below tests, so they coincide WHILE the
	//	         special case is present and part company the moment it is dropped.
	//	         EXCEPT that when FromDate is the last day of its month and seed's
	//	         day > FromDate's day, k is measured to FromDate.plusDays(1)
	//	                                                        (:1426-1436, :1432)
	//	         Implement the packed rule WITH the special case, or the
	//	         clamped-step rule WITHOUT it; the packed rule minus the special
	//	         case DOUBLE-CHARGES alternate periods (an observed MNT 83,959.76
	//	         on one six-month MNT 3,924,149 loan)."""),
])

# --- DEC-1 section 9 obligation (c) -----------------------------------------
patch("docs/adr/DEC-1-schedule-generator-adapter.md", [
    ("the month-end special case in the whole-period offset [`:1430-1433`], the forward walk and "
     "its fractional branch [`:1441-1458`], with the **division at `:1453` as the only "
     "`MathContext`-rounded step** and the addition at `:1454` **exact**;",

     "the whole-period offset `k` as **`ChronoUnit.MONTHS.between`'s packed rule** "
     "[`:1435`, `DateUtils.java:308-317`] **together with** the month-end special case "
     "[`:1426-1436`, predicate at `:1432`, effect at `:1433`] — the two must be implemented as a "
     "pair, because the packed rule without the special case double-charges alternate periods "
     "and the clamped-step reading of \"whole months\" silently absorbs the special case (§4.1.1 "
     "step B, finding F-1); the forward walk and its fractional branch [`:1441-1458`], with the "
     "**division at `:1453` as the only `MathContext`-rounded step** and the addition at `:1454` "
     "**exact**;"),

    # revision-history: record the probe's own two findings
    ("  **What revision 8 does NOT do.** It does not admit charges to the contract,",

     "  **Two findings revision 8's OWN spec-check probe produced, recorded because a probe that "
     "finds nothing has not been run** (`.softhouse/reviews/t41-probe/`). **F-1 (§4.1.1 step B, "
     "§9, `contract.go`):** \"whole months, truncated toward zero\" names **two** functions — "
     "`ChronoUnit.MONTHS.between`'s packed rule and \"the largest `k` with seed + k months ≤ "
     "FromDate\" — which differ exactly when `plusMonths` would have clamped, i.e. exactly where "
     "the month-end special case fires. They therefore coincide **while the special case is "
     "present** and diverge the instant it is dropped, so a model built on the wrong one "
     "reproduces every committed cell *and reports the special case as inert*. This task's first "
     "transcription did exactly that. Step B now pins the packed rule with its citation and says "
     "the two must be implemented as a pair. **F-2 (§4.1.1 step B, §4.3.1, §4.3.2, §8 item 3f):** "
     "the pre-T39 corpus was **never blind** to the month-end special case — the omitted reading "
     "fails `P-02`, `P-02b` and `T37-3b-2` as well as T39's four, so **seven** committed captures "
     "separate it, more than any other binding item, and it is *still* undischarged because none "
     "is promoted.\n"
     "  **Spec-check result.** A model transcribed from revision 8's text alone reproduces "
     "**4,578 cells** across four corpora — the 13 observation triples, the 11 Path-A pass-3 "
     "captures (712 cells), the 10 T37 binding captures (776 cells), the 15 parity-setting T39 "
     "captures (1,224 cells, full-cell including fee, penalty and `totalOutstandingBalance`) and "
     "the schedule core of all 21 T40 charge captures (1,827 cells) — with **zero mismatches**, "
     "and it discriminates every known corpus-invisible wrong reading plus the three revision 8 "
     "adds. **The T40 result is the executable form of decision C-1/C-2's premise**: a model that "
     "computes no charge at all reproduces the principal split, the interest, the outstanding "
     "principal and the level installment of twenty-one charge-bearing schedules exactly.\n"
     "  **What revision 8 does NOT do.** It does not admit charges to the contract,"),
])

print("\n".join(LOG))
