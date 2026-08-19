#!/usr/bin/env python3
"""T41 edit batch 21 — T42 leak closure: 4.1, 4.4, 5, 8, 9, contract.go, history."""
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
G = "nexus/internal/apps/loanschedule/contract/contract.go"

patch(P, [
    # --- 4.1's "no size threshold" paragraph gains T42's precision result ----
    ("**There is no size threshold.** *Observed*: the oracle's own 12-vs-19 pair diverges at a "
     "principal of **4.00** on a 36-period 16.8 % shape and is **identical** at 50,000,000 on that "
     "same shape and at 87,654,321 on a 6-period 7.0 % shape. Sensitivity is a rounding-boundary "
     "property of the `(principal, term, rate)` triple, not a magnitude property of the principal. "
     "All four MNT captures in the corpus are 12/19-identical, so nothing in the corpus shows "
     "Mongolian sizes are precision-sensitive either. **Any implementation shortcut justified by "
     "loan size is unfounded.**",

     "**There is no size threshold.** *Observed*: the oracle's own 12-vs-19 pair diverges at a "
     "principal of **4.00** on a 36-period 16.8 % shape and is **identical** at 50,000,000 on that "
     "same shape and at 87,654,321 on a 6-period 7.0 % shape. Sensitivity is a rounding-boundary "
     "property of the `(principal, term, rate)` triple, not a magnitude property of the principal. "
     "**Revision 8 upgrades the last clause from a corpus limitation to a MEASUREMENT** (task "
     "T42): the four MNT captures of the Run-1 corpus are 12/19-identical, but a 110-shape sweep "
     "to 360 periods found separating ones and they are **ordinary Mongolian retail loans** — MNT "
     "**50,000,000 / 360 × 21.6 %** differs by **MNT 2.05** in total interest across **861 cells**, "
     "MNT **25,000,000 / 360 × 7.7 %** across 610 — and **separation is not monotone in the "
     "principal**, so 25 M separates while 30–70 M do not and 80 M does again [VERIFIED: task T42, "
     "`.softhouse/capture/mathcontext/analysis/discriminate2-output.txt`]. **Any implementation "
     "shortcut justified by loan size is unfounded, and that is now observed at both ends of the "
     "scale rather than argued.**"),

    # --- 4.4's currency.inMultiplesOf row ------------------------------------
    ("| `currency.inMultiplesOf` | `null` | Inert because the oracle applies it only when the "
     "currency has **zero** decimal places [`Money.java:48-51`] and MNT has two. *Observed* at "
     "zero decimal places it moves money (total interest 763,994 versus 764,100 on an 18 × 18.5 % "
     "MNT 5,000,000 loan), which is a second reason `Currency.MinorUnitDigits == 2` is in the "
     "graded domain. It is a **different thing** from `InstallmentRoundingMultipleMinor`, which is "
     "the loan-product rounding and *is* in the contract. |",

     "| `currency.inMultiplesOf` | `null` | Inert because the oracle applies it only when the "
     "currency has **zero** decimal places [`Money.java:48-51`] and MNT has two. *Observed* at "
     "zero decimal places it moves money (total interest 763,994 versus 764,100 on an 18 × 18.5 % "
     "MNT 5,000,000 loan), which is a second reason `Currency.MinorUnitDigits == 2` is in the "
     "graded domain. **Revision 8 adds a THIRD reason, and it is the sharpest** (task T42): that "
     "same guard is the **only** gate on the one Path-A site where the AMBIENT `MoneyHelper` "
     "context reaches the money — `Money`'s constructor calls the two-argument "
     "`roundToMultiplesOf` at [`Money.java:50`], which hard-codes `MoneyHelper.getRoundingMode()` "
     "[`:154`] and ignores the `MathContext` the constructor was handed. *Observed*: on a 0-dp / "
     "`inMultiplesOf` 100 shape the **ambient** mode moves 23 cells and the **threaded** mode "
     "moves **none** — the exact inversion of the graded domain's behaviour [VERIFIED: task T42, "
     "`.softhouse/capture/mathcontext/analysis/discriminate-output.txt`]. So admitting a 0-dp "
     "currency would not merely switch on a second rounding channel; it would change **which "
     "`MathContext` governs** (§4.1.2), and §4.1.2's whole argument would have to be re-run rather "
     "than inherited. It is a **different thing** from `InstallmentRoundingMultipleMinor`, which "
     "is the loan-product rounding and *is* in the contract. |"),

    # --- section 8 item 1: the attestation block gains T42's rule ------------
    ("**Revision 8 adds one more field to that machine-readable block**: the **threaded** "
     "`MathContext` and the **ambient** `MoneyHelper` context as two separately labelled values, "
     "never one conflated \"captured at (19, HALF_UP)\" — §4.1.2.",

     "**Revision 8 adds two more requirements to that machine-readable block, both from task T42's "
     "attestation rule.** (i) The **threaded** `MathContext` and the **ambient** `MoneyHelper` "
     "context as two separately labelled values, never one conflated \"captured at "
     "(19, HALF_UP)\"; the threaded value must be echoed **off the object handed to the callee**, "
     "not off the intent. (ii) The **WIRING**, per capture path — on **Path B** the ambient "
     "reading *is* the threaded context and the record must cite "
     "[`LoanScheduleAssembler.java:753`, `:765`]; on **Path A** the two are independent variables "
     "and the ambient reading witnesses the tenant configuration only. A **behavioural canary** "
     "must accompany whichever context the record claims governs — a configuration echo is not a "
     "discriminator (§4.1.2). **Revision 8 also records that three committed attestations need "
     "re-wording and none needs re-capturing**: T35's and T37's \"the `MathContext` in force\" "
     "phrasing reads the ambient context and is wrong about Path A; T36's is substantially sound, "
     "because on Path B it is right by the wiring. **No committed value changes** — every one of "
     "those captures echoed and asserted its threaded context separately [VERIFIED: task T42 §4]."),

    # --- section 8 item 6: add the precision vector --------------------------
    ("6. **Vectors for the uncaptured frequency and cardinality corners**: `FrequencyDays`, "
     "`FrequencyWeeks`, `RepaymentEvery > 1`, zero interest rate, `HALF_EVEN`.",

     "6. **Vectors for the uncaptured frequency and cardinality corners**: `FrequencyDays`, "
     "`FrequencyWeeks`, `RepaymentEvery > 1`, zero interest rate, `HALF_EVEN`.\n"
     "   **6c. A vector that discriminates threaded PRECISION 19 from 12** — added in revision 8 "
     "from task T42, superseding T39's N-4. Until T42 no captured shape could tell the ratified "
     "precision from any other, so `SignificantDigits == 19` was a **transcription** claim wearing "
     "a graded-domain predicate. T42 found separating shapes and they are ordinary: **MNT "
     "50,000,000 / 360 × 21.6 %** (MNT 2.05 in total interest, 861 cells) and **MNT 25,000,000 / "
     "360 × 7.7 %** (610 cells), with separation **not monotone in the principal** [VERIFIED: "
     "`.softhouse/capture/mathcontext/analysis/discriminate2-output.txt`]. Promote one 360-period "
     "shape **once G-1 closes**, labelled as the precision-discriminating vector, alongside a "
     "`(12, HALF_UP)` sibling kept explicitly as a **discrimination probe and never a parity "
     "vector**. **That pair is the only thing in this program that would make Buyan's ratified "
     "precision-19 parameter falsifiable**, and until it is promoted §5's `SignificantDigits` row "
     "grades the parameter on one 18 × 18.5 % shape and nothing Mongolian-sized."),
])

# --- contract.go: the ambient-site enumeration and the Path-B mechanism -----
patch(G, [
    ("	// Every one of those sits on the installment-multiple or\n"
     "	// multipliedBy(double) path, which the graded domain excludes.\n"
     "	// Independently settable modes would admit combinations no deployment can\n"
     "	// produce and would double the vector matrix.",

     "	// Every one of those sits on the installment-multiple or\n"
     "	// multipliedBy(double) path, which the graded domain excludes -- AND ONE\n"
     "	// MORE SITE THAT IS HANDED A CONTEXT AND IGNORES IT (revision 8, task\n"
     "	// T42): Money's constructor calls the TWO-argument roundToMultiplesOf at\n"
     "	// Money.java:50, which hard-codes MoneyHelper.getRoundingMode()\n"
     "	// (Money.java:154) and never looks at the mc assigned at :42. It is gated\n"
     "	// on currency.getInMultiplesOf() != null && getDecimalPlaces() == 0 &&\n"
     "	// inMultiplesOf > 0 (Money.java:48-51). Currency.MinorUnitDigits == 2 is a\n"
     "	// graded-domain predicate and MNT has two decimal places, so a ratified\n"
     "	// request NEVER reaches it -- but a Go port that threads its context\n"
     "	// correctly everywhere will be MORE consistent than the reference oracle\n"
     "	// and WILL DIVERGE on a 0-decimal-place currency with an inMultiplesOf.\n"
     "	// Observed, not read: T42 reached it by giving the tenant no rounding mode\n"
     "	// and catching the IllegalStateException from MoneyHelper.java:79.\n"
     "	// Independently settable modes would admit combinations no deployment can\n"
     "	// produce and would double the vector matrix."),

    ("	// converse holds -- nothing threads a context, getMc() takes its null\n"
     "	// branch, and the ambient mode IS the arithmetic, which is why the same\n"
     "	// request on two tenants differing only in mode returns 20,925.05 under\n"
     "	// HALF_UP and 20,925.04 under HALF_EVEN. A CAPTURE ATTESTATION MUST\n"
     "	// RECORD THE TWO CONTEXTS AS TWO LABELLED FIELDS; \"captured at\n"
     "	// (19, HALF_UP)\" does not say which, and on Path A only the threaded one\n"
     "	// is evidence about the money.",

     "	// converse holds, and the reason is NOT that nothing is threaded: the\n"
     "	// caller SOURCES the threaded context from the ambient one.\n"
     "	// LoanScheduleAssembler does\n"
     "	//     final MathContext mc = MoneyHelper.getMathContext();   (:753)\n"
     "	// and hands THAT SAME OBJECT to generate(mc, ...) (:765), so on Path B the\n"
     "	// two contexts are one reference -- which is why the same request on two\n"
     "	// tenants differing only in mode returns 20,925.05 under HALF_UP and\n"
     "	// 20,925.04 under HALF_EVEN. Task T42 read that wiring off the DEPLOYED\n"
     "	// bytecode of the running server and measured it: an ambient-only change\n"
     "	// moves 0 cells on the Path A wiring and 22-28 on the Path B wiring, in\n"
     "	// one payload. A CAPTURE ATTESTATION MUST RECORD THE TWO CONTEXTS AS TWO\n"
     "	// LABELLED FIELDS AND THE WIRING; \"captured at (19, HALF_UP)\" does not\n"
     "	// say which, and on Path A only the threaded one is evidence about the\n"
     "	// money. The rule is PER SITE, not a slogan: on a 0-dp / inMultiplesOf\n"
     "	// shape it inverts -- the ambient mode moves 23 cells and the threaded\n"
     "	// mode moves none."),
])

print("\n".join(LOG))
