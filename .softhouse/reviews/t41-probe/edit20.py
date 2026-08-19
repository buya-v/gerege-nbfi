#!/usr/bin/env python3
"""T41 edit batch 20 — fold in T42, which landed on main after 4.1.2 was written.

T42 CONFIRMS 4.1.2's rule and CORRECTS one mechanism inside it, so leaving 4.1.2
as drafted would ship a known-wrong sentence in the ratification candidate.
"""
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


P = "docs/adr/DEC-1-schedule-generator-adapter.md"

patch(P, [
    # --- the rule's Path-B clause: WRONG mechanism, corrected -----------------
    ("> On the **Path-A embeddable seam** the arithmetic in force is the **`MathContext` threaded "
     "into\n> `generate(mc, modelData)`**. The **ambient** `MoneyHelper` context is in force only "
     "at the call\n> sites that construct or rescale a `Money` **without** an explicit "
     "`MathContext`, and inside the\n> graded domain no such call site is reached. Therefore, on "
     "Path A inside the graded domain, an\n> attestation of the ambient context is evidence about "
     "the **tenant configuration and the\n> provenance of the run** — never about the money. On "
     "the **Path-B running-server path** the\n> converse holds: nothing threads a context, "
     "`getMc()` takes its null branch, and the ambient\n> context **is** the arithmetic.",

     "> On the **Path-A embeddable seam** the arithmetic in force is the **`MathContext` threaded "
     "into\n> `generate(mc, modelData)`**. The **ambient** `MoneyHelper` context is in force only "
     "at the call\n> sites that construct or rescale a `Money` **without** an explicit "
     "`MathContext`, plus **one site\n> that is handed a context and ignores it** (below), and "
     "inside the graded domain **no such site\n> is reached**. Therefore, on Path A inside the "
     "graded domain, an attestation of the ambient\n> context is evidence about the **tenant "
     "configuration and the provenance of the run** — never\n> about the money.\n>\n> On the "
     "**Path-B running-server path the ambient reading IS evidence about the money, and the\n> "
     "reason is not that nothing is threaded — it is that the caller sources the threaded context "
     "FROM\n> the ambient one.** `LoanScheduleAssembler` does "
     "`final MathContext mc = MoneyHelper.getMathContext()` [`LoanScheduleAssembler.java:753`] and "
     "hands **that same object** to\n> `generate(mc, …)` [`:765`]. The two contexts are not merely "
     "equal on Path B; they are the same\n> reference.\n>\n> **The rule is therefore PER SITE, not "
     "a slogan.** \"The threaded context is what matters\" is\n> itself shape-dependent — see the "
     "inversion recorded below."),

    # --- correct the mechanism bullet list -----------------------------------
    ("- The ambient context is reached at exactly these call sites, all of them enumerated in §4.1: "
     "the\n  two-argument `Money.of` [`:102-104`, `:114-116`], `Money.zero(currency)` "
     "[`:118-120`], the static\n  `roundToMultiplesOf(BigDecimal, Integer)` [`:150-157`], "
     "`roundToMultiplesOf(Money, Integer)`\n  [`:159-161`] and the three-argument form's return "
     "path [`:163-170`, the two-argument `Money.of`\n  at `:169`], and `multipliedBy(double)` "
     "[`:372-378`, the two-argument `Money.of` at `:377`].\n  **Every one of them sits on the "
     "installment-multiple or `multipliedBy(double)` path, which the\n  graded domain excludes** "
     "(§4.7, `InstallmentRoundingMultipleMinor == 0`).",

     "- The ambient context is reached at exactly these call sites: the two-argument `Money.of` "
     "[`:102-104`, `:114-116`], `Money.zero(currency)` [`:118-120`], the static "
     "`roundToMultiplesOf(BigDecimal, Integer)` [`:150-157`, the `MoneyHelper.getRoundingMode()` "
     "at `:154`], `roundToMultiplesOf(Money, Integer)` [`:159-161`] and the three-argument form's "
     "return path [`:163-170`, the two-argument `Money.of` at `:169`], and `multipliedBy(double)` "
     "[`:372-378`, the two-argument `Money.of` at `:377`].\n"
     "- **And ONE site that is handed a `MathContext` and ignores it — revision 8 adds this from "
     "task T42, and revision 8's own §4.1.2 draft missed it.** `Money`'s constructor calls the "
     "**two-argument** `roundToMultiplesOf(BigDecimal, Integer)` at [`Money.java:50`], which "
     "hard-codes `MoneyHelper.getRoundingMode()` [`:154`] and never looks at the `mc` the "
     "constructor was given at `:42`. It is guarded by "
     "`currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 && inMultiplesOf > 0` "
     "[`Money.java:48-51`]. **`Currency.MinorUnitDigits == 2` is a graded-domain predicate (§3.1) "
     "and MNT has two decimal places, so a ratified MNT request never reaches it** — but the site "
     "is real, it is on the Path-A call graph, and T42 reached it by observation, catching an "
     "`IllegalStateException` from [`MoneyHelper.java:79`] with a stack trace naming "
     "`Money.roundToMultiplesOf(Money.java:154)` under `Money.<init>(Money.java:50)` under the "
     "**three-argument** `Money.of(Money.java:107)` [VERIFIED: task T42, "
     "`.softhouse/capture/mathcontext/analysis/discriminate-output.txt`]. **A Go port that threads "
     "its context correctly everywhere will be MORE consistent than the oracle and will diverge on "
     "a 0-decimal-place currency with an `inMultiplesOf`** — a port hazard, recorded rather than "
     "discovered later (§4.4, §8).\n"
     "- **Every remaining site sits on the installment-multiple or `multipliedBy(double)` path, "
     "which the graded domain excludes** (§4.7, `InstallmentRoundingMultipleMinor == 0`)."),

    # --- upgrade the falsification test with T42's actual results ------------
    ("**This rule is FALSIFIABLE, and task T42 owns the test.** T42 is investigating the same "
     "question\nin the same fire and this task does not have its results. The rule predicts, and "
     "T42 can confirm\nor refute, each of:",

     "**This rule was written FALSIFIABLE, and task T42 then ran the test. T42's results landed on "
     "`main` while revision 8 was being written, and revision 8 folds them in rather than shipping "
     "a prediction it could have checked** (`.softhouse/handoff/T42-mathcontext-inforce.md`, "
     "`.softhouse/capture/mathcontext/`). **The rule is CONFIRMED, one of its four predictions is "
     "strengthened from \"inert\" to \"provably never read\", one had its MECHANISM wrong (the "
     "Path-B clause above, now corrected), and one gained the exception above.** Predictions and "
     "outcomes:"),

    ("- **(P1)** Forcing the ambient mode alone moves **no** cell of **any** in-graded-domain "
     "Path-A\n  capture. *Status: observed on 16 shapes for the mode* [T39 N-3]; **not** tested "
     "for the ambient\n  **precision**, and not tested outside T39's sixteen. "
     "`[UNVERIFIED beyond those 16]`\n"
     "- **(P2)** Forcing the threaded mode moves cells wherever a tie occurs. *Status: observed, "
     "15 of\n  16* [T39 N-3]. The one that did not move is the shape with no tie at the minor "
     "unit, not a\n  counter-example.\n"
     "- **(P3)** On **Path B**, forcing the ambient mode alone **does** move money. *Status:* "
     "supported\n  only **indirectly** — by §4.1's two-tenant HALF_UP/HALF_EVEN pair and by T36's "
     "and T40's\n  half-cent canary, neither of which is a controlled single-variable negative "
     "test on a Path-B\n  **schedule**. `[UNVERIFIED as a controlled Path-B negative test]` "
     "**This is the cheapest gap\n  left in the rule and T42 should close it.**\n"
     "- **(P4)** No in-graded-domain Path-A call site reaches an ambient `Money` construction. "
     "*Status:\n  re-derived from source above; observationally consistent with (P1).* A single "
     "counter-example\n  — one in-graded-domain Path-A cell that moves under an ambient-only "
     "change — **falsifies this\n  whole subsection**, and every attestation sentence in §4.1 must "
     "then be re-scoped again.",

     "- **(P1) An ambient-only change moves no cell of any in-graded-domain Path-A capture.** "
     "**CONFIRMED AND STRENGTHENED.** T39 observed it inert on 16 shapes by a *difference* test; "
     "T42 replaced that with an **absence** test — give each case its own tenant and never call "
     "`initializeTenantRoundingMode` for it, so **any** ambient read throws "
     "[`MoneyHelper.java:79`] — and 11 of 13 shapes **generated fine**, which shows the ambient "
     "context is **provably never read**, not merely inert. **T42 is right that the difference "
     "test was weak evidence**: \"nothing moved\" is consistent with \"it was read and happened "
     "not to matter\", and revision 8 records that the stronger experiment is the absence one "
     "[VERIFIED: T42 E1, `.softhouse/capture/mathcontext/analysis/discriminate-output.txt`; the "
     "probe is proved live by negative leg N4, which inverts the canary's expectation and fires].\n"
     "- **(P2) A threaded change moves cells wherever a tie occurs.** **CONFIRMED.** 15 of 16 "
     "[T39]; T42 measured 18–24 cells per shape on 11 of its 13 [T42 E1].\n"
     "- **(P3) On Path B an ambient-only change DOES move money.** **CONFIRMED, and the mechanism "
     "is better than predicted.** T42 ran the two wirings side by side in one payload: at tenant "
     "ordinal 1 (`DOWN`) the Path-A wiring moves **0** cells and the Path-B wiring **23**; at "
     "ordinal 0 (`UP`), **0** against **22**; on T36's half-cent-tie shape `HALF_UP`→`HALF_EVEN` "
     "moves **0** against **28**, `140,457.89 → 140,457.88` — which independently reproduces the "
     "mechanism behind T36's `20925.05` / `20925.04` canary. The wiring itself was read off the "
     "**deployed bytecode of the running server**, not the repository "
     "[VERIFIED: T42 E2/E3, `.softhouse/capture/mathcontext/out/t42-pathb-wiring.txt`; "
     "`LoanScheduleAssembler.class` sha256 `d5ef398973…711ea`]. **This prediction is no longer the "
     "cheapest gap; it is closed.**\n"
     "- **(P4) No in-graded-domain Path-A site reaches an ambient `Money` construction.** "
     "**CONFIRMED INSIDE THE GRADED DOMAIN, and revision 8's own enumeration was incomplete "
     "outside it.** T42 found the one site — the constructor's two-argument `roundToMultiplesOf` "
     "[`Money.java:50`, `:154`] — which revision 8's draft did not list. It is gated on "
     "`decimalPlaces == 0`, and §3.1 pins `Currency.MinorUnitDigits == 2`, **so P4 stands as "
     "stated and §4.1's source argument stands** — but only because of a graded-domain predicate, "
     "which is a materially weaker reason than \"no such site exists\". The bullet above now "
     "states it.\n"
     "- **(P5, T42's own, and it inverts the rule) On a 0-dp / `inMultiplesOf` shape the THREADED "
     "mode is inert and the AMBIENT mode moves 23 cells** — the exact reverse of the graded "
     "domain's behaviour, because snapping to multiples of 100 swamps a 10⁻¹⁹-scale effect "
     "[VERIFIED: T42 N-2]. **So neither context is universally the answer**, and §4.1.2 is a "
     "per-site rule. Any future widening of `Currency.MinorUnitDigits` must re-run this "
     "subsection's test rather than inherit its conclusion."),

    # --- supersede N-4 --------------------------------------------------------
    ("Note separately, and do not confuse the two: T39 also\nfound that threaded precision "
     "**12 and 19 are indistinguishable on all sixteen of its shapes**\n"
     "[VERIFIED: T39 N-4, `out/t39-neg6.json`], so for that family `(19, HALF_UP)` is a "
     "**provenance**\nclaim, not a discrimination claim. §4.1's own 12-versus-19 pair — eighteen "
     "divergent rows on an\n18 × 18.5 % shape — shows the corpus is not blind to threaded "
     "precision *in general*; it is blind\nto it on T39's sixteen.",

     "Note separately, and do not confuse the two: T39 also found that threaded precision "
     "**12 and 19 are indistinguishable on all sixteen of its shapes** [VERIFIED: T39 N-4, "
     "`out/t39-neg6.json`]. **That finding is SUPERSEDED, not merely qualified** (revision 8, task "
     "T42): T42 swept 110 shapes to 360 periods and found separating ones, and they are ordinary "
     "Mongolian retail loans — **MNT 50,000,000 over 360 months at 21.6 %** gives total interest "
     "`274,527,298.56` at threaded precision 19 against `274,527,296.51` at 12, an **MNT 2.05** "
     "gap across **861 cells**, and **MNT 25,000,000 / 360 / 7.7 %** separates across 610 "
     "[VERIFIED: T42 §3, `.softhouse/capture/mathcontext/analysis/discriminate2-output.txt`]. "
     "**Separation is NOT monotone in the principal** — at 360 × 7.7 % MNT 25 M separates while "
     "30 M, 40 M, 50 M, 60 M and 70 M do not and 80 M does again — so **there is no threshold "
     "below which precision 12 is safe**, which is the same shape of conclusion §4.1 already "
     "reaches for loan size. T39's N-4 was **narrow, not wrong**: none of its sixteen shapes "
     "reaches the 360-period regime where the residual accumulates. **Buyan's ratified "
     "precision-19 parameter is therefore an OBSERVABLE parameter rather than a transcription "
     "claim**, and §8 records the vector that would make it falsifiable."),
])

print("\n".join(LOG))
