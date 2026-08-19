#!/usr/bin/env python3
"""T41 edit batch 2 — insert section 4.1.2 (ambient vs threaded MathContext)."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()

ANCHOR = "### 4.2 Dates: civil dates, one named zone, and a month-end rule anchored to the disbursement"
if s.count(ANCHOR) != 1:
    sys.exit("anchor count %d" % s.count(ANCHOR))

NEW = r"""#### 4.1.2 WHICH `MathContext` is in force — ambient versus threaded (normative; P1-T39-1, added in revision 8)

Revision 7 cited T35, T36 and T37 attestations for the production `MathContext`, and several of
those sentences rested wholly or partly on **`MoneyHelper`**. Task T39 then ran the negative test
nobody had run, and it separates the two contexts:

| forced change | `MoneyHelper.getMathContext()` on the oracle's own testimony | observed capture blocks that moved |
|---|---|---|
| tenant `RoundingMode` ordinal → `1` (`DOWN`) | changed to `precision=19 roundingMode=DOWN` | **0 of 16 — byte-identical** |
| **threaded** `MathContext` rounding mode → `DOWN` | unchanged | **15 of 16** (e.g. `T39-CTL-Q0a` total interest `76,723.70` → `76,723.65`) |

[VERIFIED: task T39, `.softhouse/capture/periodratio/out/t39-neg5.json` and `out/t39-neg7.json`
against `out/t39-periodratio.json`; `.softhouse/capture/periodratio/NEGATIVE-TESTS.md`. Both are
**observations**, taken on the pinned reference oracle by T39, quoted here with their ids and
taken by nobody else.]

**The rule (normative, ENGINEERING, `chosen_by: agent`).**

> On the **Path-A embeddable seam** the arithmetic in force is the **`MathContext` threaded into
> `generate(mc, modelData)`**. The **ambient** `MoneyHelper` context is in force only at the call
> sites that construct or rescale a `Money` **without** an explicit `MathContext`, and inside the
> graded domain no such call site is reached. Therefore, on Path A inside the graded domain, an
> attestation of the ambient context is evidence about the **tenant configuration and the
> provenance of the run** — never about the money. On the **Path-B running-server path** the
> converse holds: nothing threads a context, `getMc()` takes its null branch, and the ambient
> context **is** the arithmetic.

**The mechanism, re-derived by this task from the pinned checkout — the observation above is
exactly what the source predicts.** Revision 7 wrote that the `Money` constructor "reads only the
rounding mode from `getMc()` [`Money.java:52`]" and cited `:52` among the tenant-global sources.
That is imprecise, and the imprecision is the whole of T39's N-3:

- `Money` holds its own `MathContext` field [`Money.java:32`], assigned in the constructor at
  [`:42`] **before** the currency-scale `setScale` at [`:52`] runs.
- `getMc()` is an **instance** method: `return mc != null ? mc : MoneyHelper.getMathContext();`
  [`Money.java:494-496`]. It is the ambient context **only on the null branch**.
- Every `Money` this seam builds comes through the three-argument `Money.of(currency, amount, mc)`
  [`Money.java:106-108`, `:110-112`] carrying the threaded context, so `getMc()` on it — including
  at `:52` — is the **threaded** context.
- The ambient context is reached at exactly these call sites, all of them enumerated in §4.1: the
  two-argument `Money.of` [`:102-104`, `:114-116`], `Money.zero(currency)` [`:118-120`], the static
  `roundToMultiplesOf(BigDecimal, Integer)` [`:150-157`], `roundToMultiplesOf(Money, Integer)`
  [`:159-161`] and the three-argument form's return path [`:163-170`, the two-argument `Money.of`
  at `:169`], and `multipliedBy(double)` [`:372-378`, the two-argument `Money.of` at `:377`].
  **Every one of them sits on the installment-multiple or `multipliedBy(double)` path, which the
  graded domain excludes** (§4.7, `InstallmentRoundingMultipleMinor == 0`).

So the source says an ambient-only change must be inert on Path A inside the graded domain, and
T39 observed it inert on 16 of 16. **This is a re-derivation that explains an observation; the
observation outranks any re-derivation of the same question, and here the two agree.**

**What the ambient reading IS still evidence of — stated so this correction does not overshoot.**
Four things, each of which the program still needs:

1. **The tenant configuration**, i.e. what `MoneyHelper.getMathContext()` returns
   [`MoneyHelper.java:91-93`]. That is what pins the Gerege tenant to the ratified ordinal 4.
2. **That the run would not throw.** Every ambient call site throws `IllegalStateException` on an
   uninitialised tenant [`MoneyHelper.java:74-82`]. Attesting the ambient mode is what proves the
   adapter obligation in §4.1 was met.
3. **The arithmetic on Path B**, where nothing threads a context — which is why §4.1's
   HALF_UP-versus-HALF_EVEN observation (`20,925.05` versus `20,925.04`) and T36's and T40's
   behavioural canary are real arithmetic evidence, on that path.
4. **`MoneyHelper.PRECISION = 19` as a property of the deployed binary** [`MoneyHelper.java:35`],
   read by `javap` from the jar inside the container. That constant is not tenant state and the
   negative test does not touch it.

**What it is NOT evidence of:** the `MathContext` that produced any Path-A capture. That must be
attested **separately, by the harness, as the value it threaded** — which T39's, T37's and T35's
attestations do, and which every future capture must continue to do.

**This rule is FALSIFIABLE, and task T42 owns the test.** T42 is investigating the same question
in the same fire and this task does not have its results. The rule predicts, and T42 can confirm
or refute, each of:

- **(P1)** Forcing the ambient mode alone moves **no** cell of **any** in-graded-domain Path-A
  capture. *Status: observed on 16 shapes for the mode* [T39 N-3]; **not** tested for the ambient
  **precision**, and not tested outside T39's sixteen. `[UNVERIFIED beyond those 16]`
- **(P2)** Forcing the threaded mode moves cells wherever a tie occurs. *Status: observed, 15 of
  16* [T39 N-3]. The one that did not move is the shape with no tie at the minor unit, not a
  counter-example.
- **(P3)** On **Path B**, forcing the ambient mode alone **does** move money. *Status:* supported
  only **indirectly** — by §4.1's two-tenant HALF_UP/HALF_EVEN pair and by T36's and T40's
  half-cent canary, neither of which is a controlled single-variable negative test on a Path-B
  **schedule**. `[UNVERIFIED as a controlled Path-B negative test]` **This is the cheapest gap
  left in the rule and T42 should close it.**
- **(P4)** No in-graded-domain Path-A call site reaches an ambient `Money` construction. *Status:
  re-derived from source above; observationally consistent with (P1).* A single counter-example
  — one in-graded-domain Path-A cell that moves under an ambient-only change — **falsifies this
  whole subsection**, and every attestation sentence in §4.1 must then be re-scoped again.

**Consequence for the capture programme (§8 item 1).** Every attestation must record the ambient
context and the threaded context as **two labelled fields**, and any claim of the form "captured
at `(19, HALF_UP)`" must say which. T39 already does this; earlier attestations conflate them and
should be read with this subsection in hand. Note separately, and do not confuse the two: T39 also
found that threaded precision **12 and 19 are indistinguishable on all sixteen of its shapes**
[VERIFIED: T39 N-4, `out/t39-neg6.json`], so for that family `(19, HALF_UP)` is a **provenance**
claim, not a discrimination claim. §4.1's own 12-versus-19 pair — eighteen divergent rows on an
18 × 18.5 % shape — shows the corpus is not blind to threaded precision *in general*; it is blind
to it on T39's sixteen.

"""

s = s.replace(ANCHOR, NEW + ANCHOR)
io.open(P, "w", encoding="utf-8").write(s)
print("inserted 4.1.2")
