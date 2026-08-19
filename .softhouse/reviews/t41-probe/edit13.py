#!/usr/bin/env python3
"""T41 edit batch 13 — section 8 item 9 (charges backlog); section 9 obligations."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- section 8: new item 9 ---------------------------------------------------
sub(
    "8. **`fixedLength`**, **flat interest**, **holiday / non-working-day due-date adjustment**, "
    "and a **finer error taxonomy** — each a new field or member and each a gate, none required by "
    "any product today.",

    "8. **`fixedLength`**, **flat interest**, **holiday / non-working-day due-date adjustment**, "
    "and a **finer error taxonomy** — each a new field or member and each a gate, none required by "
    "any product today.\n"
    "9. **Charge captures — the corpus's oldest blind spot, now partly closed** (added in "
    "revision 8 from task T40). Twenty-one non-zero-charge schedules exist on the running-server "
    "path at attested `MathContext(19, HALF_UP)`, behind a passing preconditions script and a "
    "byte-identical zero-charge control [`.softhouse/capture/charges/`]. **They are attested raw "
    "observations, not admissible vectors, and nothing here is promoted** — item 1's rule "
    "applies. They are also **not** vectors *of this contract*: DEC-1 carries no charge field, so "
    "they grade the oracle's behaviour and the decisions in §4.5.1, not a port of `Generate`. "
    "**What they closed:** that a charge sits alongside the EMI and never inside it, that the "
    "principal split is untouched by a charge, that fee and penalty columns are separate and "
    "additive, that the per-instalment total is the sum of the rounded parts, that the charge "
    "membership rule is §4.3.2's **M4**, and the two silent-loss paths behind decision C-2. "
    "**What remains `TO_BE_CAPTURED`, in the order it is worth doing:** (a) "
    "`chargeTimeType = OVERDUE_INSTALLMENT` — the classic penalty, the most operationally "
    "important type, and entirely ungraded; it needs a persisted, disbursed loan and a "
    "business-date advance, so it belongs to a task that owns the server and can afford state; "
    "(b) charge `minCap` / `maxCap`, the most plausible remaining rounding-and-clamping defect "
    "home; (c) tranche charges — `TRANCHE_DISBURSEMENT` and `PERCENT_OF_DISBURSEMENT_AMOUNT` — "
    "which need `multiDisburseLoan = true` and belong in their own task because they change the "
    "schedule shape; (d) the whole set repeated against the **cumulative** generator, since "
    "decision C-1 rests on the two generators disagreeing and only the progressive side is "
    "observed; (e) `taxGroupId`, `glAccountId`, `chargePaymentMode = ACCOUNT_TRANSFER`, "
    "`feeFrequency` / `feeInterval`, waiver and payment; and (f) a percentage landing on an exact "
    "half-cent tie, which would pin the rounding mode inside the charge arithmetic specifically. "
    "**Path A can never discharge any of these** — the embeddable seam's request record carries "
    "no charges (§2.2, §4.5).",
)

# --- section 9: the multiplier obligation's blindness claim -----------------
sub(
    "**A port that writes `RepaymentEvery` on the interest call site returns different money on "
    "100 % of the shapes swept** — 480 of 480, worst total-interest gap MNT 398,967.73 (§4.1.1; a "
    "re-derivation, not an observation) — **and no capture in the corpus can detect it** (0 of 21 "
    "committed captures, 0 of 13 observations). That is why §8 item **3e** exists and why the "
    "binding is six vectors. All of it exact; no `float32`/`float64`/`big.Float` on this path.",

    "**A port that writes `RepaymentEvery` on the interest call site returns different money on "
    "100 % of the shapes swept** — 480 of 480, worst total-interest gap MNT 398,967.73 (§4.1.1; "
    "that sweep is a re-derivation) — **and revision 8 replaces revision 7's \"no capture can "
    "detect it\" with an observation**: task T39 captured 8 drift shapes and the oracle agrees "
    "with `periodRatio` on **415 of 415** discriminating cells and with `RepaymentEvery` on "
    "**0 of 415**, the worst gap observed at exactly the re-derived **MNT 398,967.73** "
    "[VERIFIED: captures `T39-P0-A`…`T39-P0-H`, "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. The 21 captures of the "
    "pre-T39 era still cannot see it, which is why the captures had to be taken. **The Go module "
    "must additionally reproduce (f) §4.1.1 step B's month-end special case** "
    "[`ProgressiveEMICalculator.java:1426-1436`, predicate at `:1432`, effect at `:1433`]: "
    "omitting those four lines roughly doubles `periodRatio` on alternate periods and overcharges "
    "by an observed **MNT 83,959.76** on one six-month MNT 3.9 M loan, refuted on 116 of 116 "
    "discriminating cells [VERIFIED: captures `T39-ME-A`…`T39-ME-D`]. That is why §8 has items "
    "**3e** and **3f** — the two questions are disjoint in shape space and no single vector "
    "grades both — and why the binding is **seven** vectors. All of it exact; no "
    "`float32`/`float64`/`big.Float` on this path.",
)

# --- section 9: totalOutstandingAmount obligation gains a sibling -----------
sub(
    "It is not a balance; no consumer may read meaning into it, and no scale-discipline invariant "
    "may be applied to it without deciding that case explicitly (§4.5).",

    "It is not a balance; no consumer may read meaning into it, and no scale-discipline invariant "
    "may be applied to it without deciding that case explicitly (§4.5).\n"
    "- The **Fineract-JVM adapter** must also **discard** the oracle plan's "
    "`totalRepaymentExpected` (added in revision 8, §4.5.1 decision C-1). On the progressive path "
    "it is seeded with the disbursement charges alone [`LoanScheduleParams.java:211`, `:246`], "
    "accumulates only principal + interest per period "
    "[`ProgressiveLoanScheduleGenerator.java:137`], and is **never** raised by "
    "`applyChargesForCurrentPeriod` [`:367-382`] — while the cumulative generator does raise it "
    "[`AbstractCumulativeLoanScheduleGenerator.java:504`], so the two generators disagree and the "
    "field has no single meaning. *Observed*: `totalRepaymentExpected == Σ totalDueForPeriod` "
    "**fails on 15 of 21** charge-bearing captures, with MNT 51,900 of one capture's charges "
    "visible in the rows and absent from the total [VERIFIED: "
    "`.softhouse/capture/charges/out/INVARIANTS.md`, C5]. **Neither the adapter, nor a harness, "
    "nor a conformance check may assert that this field equals the sum of the rows**: the "
    "assertion passes today only because the graded domain has no charges, and the day it fails "
    "it will be wrong about the **oracle**, not about the port. A caller wanting a total "
    "repayable sums the rows (§4.5).",
)

# --- section 9: capture-programme obligation --------------------------------
sub(
    "It must also carry, with any promoted record and as machine-readable data, what that record "
    "**cannot** grade: `installmentAmountInMultiplesOf`, `daysInYearCustomStrategy`, **fees and "
    "penalties** (every one in the Path-A corpus is `0.00`, observed), multi-disbursement, and "
    "**`periodRatio`** (§8 item 3e). A green conformance run over a corpus with a named blind "
    "spot is not evidence about that blind spot.",

    "It must also carry, with any promoted record and as machine-readable data, what that record "
    "**cannot** grade: `installmentAmountInMultiplesOf`, `daysInYearCustomStrategy`, **fees and "
    "penalties** (every one in the Path-A corpus is `0.00`, observed, and the seam's request "
    "record carries no charge at all, so no Path-A record can ever grade one), "
    "multi-disbursement, and — for any record taken before task T39 — **`periodRatio`** and "
    "**§4.1.1 step B's month-end special case** (§8 items 3e, 3f). **It must record the THREADED "
    "`MathContext` and the AMBIENT `MoneyHelper` context as two separately labelled fields** "
    "(§4.1.2); a record saying only \"captured at (19, HALF_UP)\" does not say which, and on "
    "Path A only the threaded one is evidence about the money. **Revision 8 adds a fourth "
    "closed prerequisite and a new open one:** task T39 closed §8 items 3e and 3f by capture and "
    "task T40 closed the charge blind spot for the progressive endpoint by capture (§8 item 9), "
    "while `chargeTimeType = OVERDUE_INSTALLMENT`, charge caps, tranche charges and the "
    "cumulative generator remain `TO_BE_CAPTURED`. A green conformance run over a corpus with a "
    "named blind spot is not evidence about that blind spot.",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
