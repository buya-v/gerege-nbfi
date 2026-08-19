#!/usr/bin/env python3
"""T47 edit 3 - finding 2: installmentAmountInMultiplesOf is honoured or lost
BY CALLER, not by the field."""
import io
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DOC = os.path.join(W, "docs/adr/DEC-1-schedule-generator-adapter.md")
s = io.open(DOC, encoding="utf-8").read()


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("edit3: expected 1 occurrence, found %d for: %.100s" % (n, old))
    s = s.replace(old, new)


# --- §2.2 table row --------------------------------------------------------
rep("| `installmentAmountInMultiplesOf` | The field exists "
    "[`LoanApplicationTerms.java:217`] but the `Builder` has **no setter for it at "
    "all**; the only assignment is in a positional constructor [`:828`] this path never "
    "reaches. Structurally unreachable, not merely unset. |",

    "| `installmentAmountInMultiplesOf` | The field exists "
    "[`LoanApplicationTerms.java:217`] but the `Builder` has **no setter for it at "
    "all**; the only assignment is in a positional constructor [`:828`] this path never "
    "reaches. Structurally unreachable **through this assembler**, not merely unset — "
    "and **not** a property of the field, which another caller honours; see the "
    "per-caller statement below (revision 10). |")

# --- §2.2 consequence paragraph -------------------------------------------
rep("**Consequence, and it is the reason revision 1 was rejected:** for those two "
    "inputs the seam-captured corpus has **zero discriminating power**. A Go port that "
    "honours them and one that ignores them score identically. A contract frozen in a "
    "form that assumes \"vectors pass\" implies \"the contract is covered\" would be "
    "frozen around a hole.",

    "**Whose blind spot this is — stated PER CALLER, because that is what it is a "
    "property of** (added in revision 10 from task T46's finding M-4, which capture "
    "audit T44 raised and T46 closed by re-derivation and by counter-observation). The "
    "table above is a statement about **`LoanApplicationTerms.assembleFrom("
    "LoanRepaymentScheduleModelData, MathContext)`** [`LoanApplicationTerms.java:579-606`] "
    "— the assembler the Path-A embeddable seam runs through — and about **every** "
    "caller that reaches the generator that way, not about the field:\n"
    "\n"
    "| caller | `installmentAmountInMultiplesOf` | evidence |\n"
    "|---|---|---|\n"
    "| the Path-A embeddable seam (this contract's capture path, §3.2) | **LOST** | the "
    "assembler at [`LoanApplicationTerms.java:579-606`] contains **zero** occurrences of "
    "`MultiplesOf` [VERIFIED: the range re-opened and grepped in the pinned checkout by "
    "this task] |\n"
    "| `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` | "
    "**LOST — for the same reason, and it is worth naming because it LOOKS wired** | it "
    "reads the ambient context at [`LoanScheduleGeneratorServiceImpl.java:44`], puts "
    "`loanProductRelatedDetail.getInstallmentAmountInMultiplesOf()` into the "
    "`LoanRepaymentScheduleModelData` at [`:56`], and calls "
    "`scheduleGenerator.generate(mc, modelData)` at [`:63`] — the value travels the "
    "whole way and is then dropped by the assembler above [VERIFIED: all three lines "
    "re-opened in the pinned checkout by this task] |\n"
    "| the REST `calculateLoanSchedule` path via `LoanScheduleAssembler` (Path B, §4.7) "
    "| **HONOURED** | *observed*: capture `B-02` (`installmentAmountInMultiplesOf = 100`) "
    "returns period-1 `totalInstallmentAmountForPeriod` **112,100.00** where the `B-01` "
    "baseline returns **112,082.37** [VERIFIED: task T46, "
    "`.softhouse/capture/mathcontext/out/control/B-02-multiplesof100-raw.json`; the same "
    "four Path-B captures §4.7 already cites] |\n"
    "\n"
    "**So DEC-1 must never state this field's behaviour unconditionally, and revision "
    "10 removes the last place it did.** A capture seam's blind spot is a property of "
    "the **caller**, not of the field — the same field is money-moving one call away. "
    "That is exactly why §4.7 keeps the field in the contract and refuses it for Run 1 "
    "rather than declaring it inert, and why §3.2's \"the seam's blind spot is empty\" "
    "is scoped to the seam in the sentence that states it.\n"
    "\n"
    "**Consequence, and it is the reason revision 1 was rejected:** for those two "
    "inputs the **seam-captured** corpus has **zero discriminating power**. A Go port "
    "that honours them and one that ignores them score identically **on that corpus**. "
    "A contract frozen in a form that assumes \"vectors pass\" implies \"the contract is "
    "covered\" would be frozen around a hole.")

# --- §3.2 ------------------------------------------------------------------
rep("**Therefore, inside the graded domain, the seam's blind spot is empty:** every "
    "admissible request is faithfully rendered, and a Path-A capture grades everything "
    "the request carries. That is what licenses freezing this contract on a "
    "seam-captured corpus.",

    "**Therefore, inside the graded domain, the seam's blind spot is empty:** every "
    "admissible request is faithfully rendered, and a Path-A capture grades everything "
    "the request carries. That is what licenses freezing this contract on a "
    "seam-captured corpus. **\"The seam's\" is load-bearing in that sentence and "
    "revision 10 says so rather than leaving it to the possessive** (§2.2, task T46's "
    "M-4): `installmentAmountInMultiplesOf` is dropped by **this assembler and by every "
    "caller that uses it**, and is **honoured** by the REST `calculateLoanSchedule` "
    "path, where a multiple of 100 major units is *observed* to move period 1 from "
    "112,082.37 to 112,100.00 (§4.7, capture `B-02`). The pin is safe because the "
    "graded domain pins the contract field to 0, **not** because the oracle ignores the "
    "input.")

# --- §4.7 disposition ------------------------------------------------------
rep("**Disposition for Run 1: launch WITHOUT it.** Products ship with no installment "
    "rounding; a non-zero value is refused with `ErrNoDiscriminatingVector`. Rounding to "
    "whole 100 ₮ is a legitimate Mongolian feature, but the seam this corpus is captured "
    "through cannot grade it (§2.2), and shipping it now would mean shipping an "
    "unvectored money path.",

    "**Disposition for Run 1: launch WITHOUT it.** Products ship with no installment "
    "rounding; a non-zero value is refused with `ErrNoDiscriminatingVector`. Rounding to "
    "whole 100 ₮ is a legitimate Mongolian feature, but the seam this corpus is captured "
    "through cannot grade it — **and that is a fact about the seam and about every "
    "caller that shares its assembler, not about the oracle, which honours the field on "
    "the REST path** (§2.2's per-caller table, added in revision 10 from task T46's "
    "M-4) — and shipping it now would mean shipping an unvectored money path.")

io.open(DOC, "w", encoding="utf-8").write(s)
print("edit3: ok")
