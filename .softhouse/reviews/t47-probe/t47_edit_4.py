#!/usr/bin/env python3
"""T47 edit 4 - finding 3 (N46-1): the CHARGE rounding mode is AMBIENT, and it
is reachable at MNT's two decimal places."""
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
        sys.exit("edit4: expected 1 occurrence, found %d for: %.100s" % (n, old))
    s = s.replace(old, new)


# ==========================================================================
# 4a. §4.1.2 — the per-construction rule, stated so it needs no enumeration
# ==========================================================================
rep("**This is the stronger form of the argument and revision 9 adopts it "
    "deliberately**, because the enumeration has now had to widen twice — once from "
    "T42 (`Money.java:50`) and once from re-review T43 (`:130-132`, `:224-234`, "
    "`:261-267`) — and a claim that has been wrong twice should not be load-bearing a "
    "third time.",

    "**This is the stronger form of the argument and revision 9 adopts it "
    "deliberately**, because the enumeration has now had to widen twice — once from "
    "T42 (`Money.java:50`) and once from re-review T43 (`:130-132`, `:224-234`, "
    "`:261-267`) — and a claim that has been wrong twice should not be load-bearing a "
    "third time.\n"
    "\n"
    "- **It has now been wrong a THIRD time, and revision 10 replaces the shape of the "
    "rule rather than adding a fourth entry** (task T46's finding **N46-1**). The "
    "omission is not in `Money.java` at all: it is the **charge** arithmetic in "
    "`ProgressiveLoanScheduleGenerator`, which computes a percentage under the "
    "**threaded** `mc` and then wraps the result in a `Money` factory overload that "
    "carries none — §4.5.1's *Which `MathContext` rounds a charge* block has the "
    "detail and the two observed ties. Revision 10 therefore states the governing rule "
    "**as a property of each construction, which is checkable at that construction and "
    "true without any list being complete**:\n"
    "\n"
    "  > **WHICH `MathContext` scales a value to the currency's decimal places is "
    "decided by the CONSTRUCTION, never by the arithmetic that produced the value.** "
    "Every `Money` is scaled at [`Money.java:52`], "
    "`amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())`; "
    "`getMc()` [`Money.java:494-496`] returns the **instance's own** `mc` when it is "
    "non-null and `MoneyHelper.getMathContext()` — the **ambient** context — when it is "
    "null; and the instance's `mc` is exactly what the constructing call passed "
    "[`Money.java:40`, assigned at `:42`]. **Therefore a value computed under a threaded "
    "`MathContext` and then handed to a `Money.of` / `Money.zero` overload that does not "
    "carry one is rounded to the currency's scale under the AMBIENT rounding mode, "
    "whatever context produced it.** [VERIFIED: all four lines re-opened in the pinned "
    "checkout by this task.]\n"
    "\n"
    "  **That form is deliberate and revision 10 states why.** It is a rule a porter "
    "applies at a call site, not a claim about a program; it cannot be falsified by a "
    "site nobody listed, which is how the previous three forms failed; and it makes the "
    "hazard list above what it already says it is — **a porter's hazard list, not an "
    "inventory**. **Nothing about Path A changes.** The charge locus is not on the "
    "Path-A call graph with a charge to round, because the embeddable seam's request "
    "record carries no charge at all (§2.2, §4.5), and T42's **absence** test is the "
    "positive evidence: it gave each Path-A shape an uninitialised tenant so that any "
    "ambient read anywhere throws [`MoneyHelper.java:79`], and 11 of 13 shapes generated "
    "fine — had the charge construction been reached, it must have thrown. **P4, and "
    "§4.1's conclusion, stand exactly as revision 9 states them.**\n"
    "\n"
    "- **A second family of ambient-mode reads outside `Money.java`, recorded so the "
    "next reader does not re-derive it** (task T46's `T46-N1`; `[VERIFIED as source "
    "with file:line by this task; UNVERIFIED as behaviour]`). "
    "`MathUtil.percentageOf(BigDecimal, BigDecimal, int)` builds "
    "`new MathContext(precision, MoneyHelper.getRoundingMode())` "
    "[`MathUtil.java:472-473`], so a caller passing a **literal** precision pins the "
    "precision and still takes the **ambient** rounding mode. **Six loan-path sites pass "
    "a literal `19`**, and all six are down-payment computations: "
    "[`AbstractCumulativeLoanScheduleGenerator.java:1897`], [`:2060`], "
    "[`LoanApplicationTerms.java:866`], [`LoanDownPaymentHandlerServiceImpl.java:198`], "
    "[`LoanWritePlatformServiceJpaRepositoryImpl.java:448`] and [`:3538`] [VERIFIED: "
    "enumerated by grep over the pinned checkout's main sources by this task and each "
    "line re-opened]. **None is inside the Run-1 graded domain** — `DownPaymentPercentage` "
    "is pinned to `Rate{0, 1}` (§4.4, §5) and none of the six is on the progressive "
    "seam's call graph — but they are the **same class of leak as N46-1**: a rounding "
    "mode taken from the ambient context on a path a porter would thread. They are "
    "recorded here, not admitted; the down-payment vectors of §8 item 4 must exercise "
    "them before any of that path is ported.")

# ==========================================================================
# 4b. §4.5.1 fact 4 — the rounding locus and the two ties
# ==========================================================================
rep("**Consequence for §4.5's response shape, and it is a confirmation rather than a "
    "change.**",

    "##### Which `MathContext` rounds a CHARGE — the second ambient leak, and the first "
    "one reachable at MNT's scale (added in revision 10 from task T46's finding N46-1)\n"
    "\n"
    "Fact 4 says the rounding locus is observable. **It does not say which `MathContext` "
    "governs it, and the answer is the AMBIENT one.** Re-derived to its locus by task "
    "T46 and re-opened line by line in the pinned checkout by this task:\n"
    "\n"
    "1. `calculateInstallmentCharge` multiplies and divides under the **threaded** `mc` "
    "— `amount.multiply(loanCharge.getPercentage()).divide(BigDecimal.valueOf(100), mc)` "
    "[`ProgressiveLoanScheduleGenerator.java:445-446`]; the specified-due-date arm does "
    "the same at [`:464-465`]. At the production precision 19 this step is exact for the "
    "observed inputs and rounds nothing.\n"
    "2. The result is wrapped by the **two-argument** "
    "`Money.of(MonetaryCurrency, BigDecimal)` [`Money.java:114-116`], which supplies "
    "**`MoneyHelper.getMathContext()` — the ambient context** [`:115`]. The threaded "
    "`mc` is in scope at [`:445`] and is **not** passed.\n"
    "3. The scale-2 rounding then happens in the constructor at [`Money.java:52`], under "
    "**that** context's rounding mode, by §4.1.2's per-construction rule.\n"
    "\n"
    "**Two exact half-cent ties were OBSERVED on this locus, and that is what makes it "
    "more than a reading of the source.** A percent-of-interest instalment fee of "
    "`0.021875 %` on a period-1 interest of `21,600.00` is exactly **`4.725`** and the "
    "oracle returned **`4.73`**; `0.009375 %` on the same interest is exactly **`2.025`** "
    "and the oracle returned **`2.03`**. Both are `HALF_UP`; `HALF_EVEN` would have given "
    "`4.72` and `2.02` [VERIFIED: captures `T46-CH-03` and `T46-CH-04`, "
    "`.softhouse/capture/charges/req/calc-T46-CH-03-tie-pctinterest-4725.json` and "
    "`out/t46/T46-CH-03-tie-pctinterest-4725-raw.json`, and the `-2025` pair; read as "
    "exact wire text — `\"feeChargesDue\": 4.73` and `2.03` on period 1 — re-read by this "
    "task]. The arithmetic in exact integers: `2,160,000` minor units × `21,875` ÷ "
    "`10^6` ÷ `100` = `472,500,000` ÷ `10^8` = `4.725` exactly, and `× 9,375` gives "
    "`202,500,000` ÷ `10^8` = `2.025` exactly. No floating point anywhere, in the "
    "oracle's arithmetic or in this check.\n"
    "\n"
    "**Why this leak is worse than the `inMultiplesOf` one §4.4 records, and revision 10 "
    "says so plainly.** The other Path-A ambient site — the constructor's two-argument "
    "`roundToMultiplesOf` [`Money.java:50`, `:154`] — is gated on "
    "`currency.getDecimalPlaces() == 0` [`Money.java:48-51`], which §3.1's "
    "`Currency.MinorUnitDigits == 2` excludes, so **MNT can never reach it**. **This one "
    "has no such gate: it is reached at exactly two decimal places, which is MNT's, and "
    "the two ties above are it firing.** A Go port that threads one `MathContext` "
    "everywhere gets the interest right and the charge ties wrong.\n"
    "\n"
    "**What no capture in this program can tell you about it, stated so the observation "
    "is not read as more than it is.** On Path B the caller **sources** the threaded "
    "context from the ambient one — `final MathContext mc = MoneyHelper.getMathContext()` "
    "[`LoanScheduleAssembler.java:753`] handed to `generate(mc, …)` [`:765`] — so the two "
    "contexts are **one reference** (§4.1.2) and every charge capture in the corpus has "
    "them equal. **Not one capture the program holds can detect which of the two the "
    "scale-2 rounding read**, because none has them disagreeing; the two ties are "
    "consistent with `HALF_UP` and inconsistent with `HALF_EVEN` and isolate no "
    "mechanism. Separating them needs the tenant rounding mode written to differ from "
    "the threaded one on a running server, which is a tenant write. **`TO_BE_CAPTURED`** "
    "(§8 item 9(h)). `[VERIFIED as source and as two observed ties; UNVERIFIED as a "
    "controlled experiment isolating the context.]`\n"
    "\n"
    "**Nothing here moves the contract**, on the same argument as the rest of §4.5.1: "
    "`GenerateRequest` carries no charge, so this binds a future port and nothing today.\n"
    "\n"
    "**Consequence for §4.5's response shape, and it is a confirmation rather than a "
    "change.**")

io.open(DOC, "w", encoding="utf-8").write(s)
print("edit4: ok")
