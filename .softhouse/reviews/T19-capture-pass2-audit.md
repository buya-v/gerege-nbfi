# T19 — independent audit of capture pass 2

**Auditor:** T19 reviewer (isolated worktree), 2026-08-18
**Under audit:** `.softhouse/capture/PASS2-REPORT.md`, `src/Capture2.java`, `out/capture-tenant-raw.json`,
`out/capture-tenant-log.txt`, `out/capture-tenant-stderr.txt`, `README-pass2.md` — committed on `main` at `2f61d29`.
**Reference:** pinned Fineract `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (read-only, unmodified),
image `fineract:latest`.
**Scratch:** all reruns written to `/tmp/t19/**`. No file under `.softhouse/capture/` was modified.

---

## VERDICT: ACCEPTED WITH REQUIRED CHANGES

Every *observation* in pass 2 survives audit. I re-ran `Capture2.java` unmodified inside the pinned image and the
output is **byte-identical** to the committed `capture-tenant-raw.json`
[VERIFIED: `diff /tmp/t19/rerun/out/capture.json .softhouse/capture/out/capture-tenant-raw.json` → no output, 48868 bytes
both]. The harness synthesises nothing, the tenant cache is correctly partitioned, the controls hold digit-for-digit,
provenance checks out, and all four money invariants hold on all 13 captures. Finding 2's **conclusion** — that
`installmentAmountInMultiplesOf` is accepted by the seam and silently discarded — is not merely supported, it is
**proved outright**: I assembled `LoanApplicationTerms` through the seam's own overload and read the field
reflectively — it is `null` [VERIFIED: `/tmp/t19/src/Verify.java` PROBE 1 → `terms.getInstallmentAmountInMultiplesOf() = null`].

The changes are required because the *reasoning* the report uses to reach that conclusion contains two errors, both
in the section the report itself calls "the most consequential result of the fire". First, the report's headline
argument — "a 17.01 EMI rounded to multiples of 100 cannot possibly be a no-op" — is **false**:
`ProgressiveEMICalculator.safeRoundingForEMI` deliberately returns the *unrounded* EMI when rounding would zero it,
and `roundToMultiplesOf(17.01, 100)` is exactly zero, so at C-00 inputs an honoured parameter is a *guaranteed*
no-op. Two of the four rows in Finding 2's evidence table are therefore non-probative; only `T-IM1-he` and the
`T-MNT5M` pair actually discriminate. Second, "the harness supplied the value through both available channels …
neither moved a single figure" is false: the `CurrencyData.inMultiplesOf` channel is gated on
`currency.getDecimalPlaces() == 0`, and the harness hard-codes 2 decimal places in every case, so that channel was
structurally inert and corroborates nothing. Beyond those, the report misses a **second silently dropped input**
(`daysInYearCustomStrategy`), cites the wrong generator family for "the server path honours it", and nowhere states
that all 13 captures sit at threaded `MathContext(12, HALF_UP)` — which the same-day ratification in `CLAUDE.md`
classifies as probes, not parity vectors. The document must be corrected before anything downstream leans on it.

---

## 1. Synthesis check — PASS

**No expected value is computed, asserted, predicted or massaged anywhere in `Capture2.java`.** I read all 256 lines.

- The only arithmetic in the file is `BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0`
  [VERIFIED: `Capture2.java:172,200`], which derives the `downPaymentEnabled` *input* flag from the input percentage.
  It is passed into the record and echoed identically into the JSON, so the emitted input block cannot disagree with
  what the generator received.
- Every `observed` figure is read straight off the returned `LoanSchedulePlan` / period objects with no
  post-processing [VERIFIED: `Capture2.java:221-249` — pure `.append(getter())`].
- No comparison, no tolerance, no assertion, no golden value, no hard-coded schedule appears in the file
  [VERIFIED: `grep -c "assert\|expect" Capture2.java` → 0 outside the header comment].
- Errors are captured, not swallowed or reshaped: `catch (RuntimeException e)` writes `observed: null` plus the
  class name and message [VERIFIED: `Capture2.java:213-219`].

**Strongest evidence: the run is bit-reproducible.** I copied `Capture2.java` and the seam class unmodified to
`/tmp/t19/rerun/src`, compiled and ran them inside `fineract:latest` with the README's exact classpath recipe, and
diffed:

- JSON → **byte-identical** to the committed file [VERIFIED: `diff` → no output].
- `MoneyHelper` log lines → identical modulo timestamps, same 12 lines in the same order
  [VERIFIED: `diff` of timestamp-stripped logs → no output].
- stderr → 0 bytes in both [VERIFIED: `wc -c` → 0].

Hand-editing of the committed outputs is therefore excluded.

**Tenant setup does not distort the run.** `MoneyHelper.roundingModeCache` / `mathContextCache` are static
`ConcurrentHashMap`s keyed by **tenant identifier string**, not by numeric id
[VERIFIED: `MoneyHelper.java:37-38` declarations; `:60` `roundingModeCache.put(tenantIdentifier, …)`; `:76`, `:93`
lookups via `getTenantIdentifier()`; `:173-180` `getTenantIdentifier()` returns `tenant.getTenantIdentifier()`].
The harness passes its per-case string as the *second* constructor argument, which is `tenantIdentifier`
[VERIFIED: `FineractPlatformTenant.java:35-39` field order `id, tenantIdentifier, name, timezoneId, connection`
under `@RequiredArgsConstructor`; `Capture2.java:155-156`]. All 12 tenant ids are distinct
[VERIFIED: `capture-tenant-log.txt` — 12 distinct `Initialized rounding mode for tenant \`…\`` lines], so no cache
entry is shared. The numeric id is `1L` for every case, which would have been a defect had the cache keyed on it;
it does not.

`initializeTenantRoundingMode` also evicts the stale `MathContext` for that key on every call
[VERIFIED: `MoneyHelper.java:62`], so even a repeated id could not have carried a stale mode. The no-tenant control
uses `ThreadLocalContextUtil.reset()`, which does clear `tenantContext`
[VERIFIED: `ThreadLocalContextUtil.java:121-127`], and it runs first, so it cannot be contaminated either way.

**One presentational weakness, not synthesis.** The JSON emits `currencyInMultiplesOf` and
`installmentAmountInMultiplesOf` from the *same* field `c.installmentMultiplesOf()`
[VERIFIED: `Capture2.java:196,202`]. The two channels are genuinely distinct in Fineract and behave differently
(§5); the JSON cannot express varying one without the other. A future harness must separate them.

---

## 2. Provenance — PASS

| Fact | Result |
|---|---|
| Image digest | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` — matches the report [VERIFIED: `docker image inspect fineract:latest --format '{{.Id}}'`] |
| Image created | `2026-08-17T11:29:56.52027346Z` — matches [VERIFIED: same command, `.Created`] |
| JVM | `openjdk 21.0.11 2026-04-21 LTS`, `Zulu21.50+19-CA (build 21.0.11+10-LTS)` — matches [VERIFIED: `docker run --rm --entrypoint sh fineract:latest -c 'java -version'`] |
| Pinned commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean [VERIFIED: `git rev-parse HEAD`, `git status -s` → empty] |
| Seam class byte-identity | identical [VERIFIED: `diff` → no output; `shasum -a 256` → `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` on both copies] |
| Prohibited DB engines | none [VERIFIED: `ls /work/jar/BOOT-INF/lib/ \| grep -iE "ojdbc\|oracle\|mysql\|mariadb"` → `NONE`; the only JDBC driver on the classpath is `postgresql-42.7.11.jar`] |
| Database touched | none — `Capture2.java` imports no JDBC/JPA type and opens no connection [VERIFIED: import block `Capture2.java:32-53`]; stderr 0 bytes, no connection attempt logged |

The PostgreSQL-only non-negotiable is not weakened: the classpath carries only the Postgres driver, and this seam
reaches no database at all. The report's provenance table is accurate as written.

---

## 3. Controls — PASS, digit-for-digit

Compared the full `observed` object (loan term, three totals, and every column of every period), not just totals
[VERIFIED: Python structural comparison over `capture-raw.json` and `capture-tenant-raw.json`]:

| Pair | Result |
|---|---|
| pass-1 `C-00` vs `T-00-notenant` | **IDENTICAL** (all 7 periods, all 6 columns) |
| `T-00-notenant` vs `T-00-he` | **IDENTICAL** |
| `T-00-he` vs `T-00-hu` | **IDENTICAL** |
| pass-1 `C-00` vs `T-00-hu` | **IDENTICAL** |

A **fourth control the report does not claim** also holds and strengthens it: `T-04f-big` reproduces pass-1 `D-01`
exactly — the two input blocks differ only in the three tenant fields pass 1 did not have, and the observed
schedules are identical across all 19 periods [VERIFIED: structural comparison; totals `13393481.05` / `101047802.05`
on both]. The report should cite it.

The ambient context materialised as claimed: `moneyHelperPrecision: 19` at the top of the JSON, and
`precision=19 roundingMode=HALF_EVEN` / `…HALF_UP` per case [VERIFIED: `capture-tenant-raw.json`]. This is
`MoneyHelper.PRECISION = 19` [VERIFIED: `MoneyHelper.java:35`] composed by
`new MathContext(PRECISION, getRoundingMode())` [VERIFIED: `MoneyHelper.java:93`]. The `6 → HALF_EVEN`, `4 → HALF_UP`
mapping is `RoundingMode.valueOf(int)` over the validated 0..6 range [VERIFIED: `MoneyHelper.java:182-189`], and the
oracle's own log lines independently corroborate the mode each tenant received
[VERIFIED: `capture-tenant-log.txt`, 12 lines].

Controls hold, so downstream comparisons are meaningful.

---

## 4. Finding 1 — `allowFullTermForTranche` — SUBSTANTIALLY CORRECT, warrant should be restated

### (a) "Live, and reaches a different code path" — TRUE, and provable more directly than the report does

The report's warrant is inferential: `true` died on `MoneyHelper` in pass 1, therefore it must take a different
path. That is a valid but weak absence-of-evidence argument. **The direct source proof exists and should be used
instead:**

```
ProgressiveEMICalculator.java:142   if (scheduleModel.loanProductRelatedDetail().isAllowFullTermForTranche() && numberOfRepayments > 0
ProgressiveEMICalculator.java:144       addFullTermTrancheDisbursement(scheduleModel, operation);
```
[VERIFIED: `grep -n`]. The `true` branch calls `addFullTermTrancheDisbursement` (`:155`); the `false` branch calls
`changeOutstandingBalanceAndUpdateInterestPeriods` + `calculateEMIValueAndRateFactors`. These are different methods.
The branch is real independent of any exception.

I also identified **exactly why `true` reaches `MoneyHelper`**, which the report leaves unexplained:

```
ProgressiveEMICalculator.java:182   .seedDate(...).inArrearsTolerance(Money.zero(loanProductRelatedDetail.getCurrencyData()))
```
This is the **one-argument** `Money.zero(CurrencyData)` overload, which resolves its `MathContext` from the ambient
tenant: `Money.java:130-132` → `MoneyHelper.getMathContext()` → `getTenantIdentifier()` → throw
[VERIFIED: `Money.java:130-132`; `MoneyHelper.java:91-94,173-180`]. Every other `Money` construction on the entry
path threads an explicit `mc`. So pass-1 `D-04`'s exception is precisely this call site.

**Verdict on (a):** the conclusion is right; the report's stated warrant licenses only "the `true` path executes at
least one statement the `false` path does not". Replace it with the source citations above, which license the
stronger claim outright.

### (b) "Schedule-neutral on single-disbursement loans" — TRUE, verified independently and extended

| Pair | Result |
|---|---|
| `T-04f` vs `T-04t` | **IDENTICAL**, all 7 periods, every column [VERIFIED] |
| `T-04f-big` vs `T-04t-big` | **IDENTICAL**, all 19 periods, every column [VERIFIED] |

I extended the test to the **production** `MathContext(19, HALF_UP)`, which pass 2 never used, at MNT scale:
`true` and `false` are still identical (`int=763994.33 rep=5763994.33` both)
[VERIFIED: `/tmp/t19/src/Verify.java` PROBE 6 → `equal ? true`]. The neutrality claim therefore survives outside the
precision-12 probe regime.

### (c) "The seam cannot express multi-disbursement" — TRUE

`assembleFrom` passes a fresh empty list [VERIFIED: `LoanApplicationTerms.java:600`
`.inArrearsTolerance(Money.zero(modelData.currency(), mc)).disbursementDatas(new ArrayList<>())`], and I confirmed
at runtime that the assembled terms carry `disbursementDatas = []`
[VERIFIED: PROBE 1 → `terms.disbursementDatas (reflect) = []`]. The record has no disbursement-list component at all
[VERIFIED: `LoanRepaymentScheduleModelData.java:32-39`], so this is structural, not a harness choice.
`TO_BE_CAPTURED` through a different path is the correct disposition.

---

## 5. Finding 2 — the dropped input — CONCLUSION UPHELD, REASONING PARTLY WRONG, SCOPE INCOMPLETE

### 5.1 The record has 19 components — CONFIRMED

Counted by hand from the declaration [VERIFIED: `LoanRepaymentScheduleModelData.java:32-39`]:
`scheduleGenerationStartDate, currency, disbursementAmount, disbursementDate, numberOfRepayments, repaymentFrequency,
repaymentFrequencyType, annualNominalInterestRate, downPaymentEnabled, daysInMonth, daysInYear,
downPaymentPercentage, installmentAmountInMultiplesOf, fixedLength, interestRecognitionOnDisbursementDate,
daysInYearCustomStrategy, interestMethod, allowPartialPeriodInterestCalculation, allowFullTermForTranche` = **19**.
(The report cites `:32-40`; the components end at `:39` and `:40` is the closing brace. Cosmetic.)

### 5.2 `assembleFrom` reads exactly 18, omitting only `installmentAmountInMultiplesOf` — CONFIRMED

[VERIFIED: `sed -n '579,607p' LoanApplicationTerms.java | grep -o 'modelData\.[a-zA-Z]*()' | sort -u | wc -l` → **18**]
The 18 are exactly the list above minus `installmentAmountInMultiplesOf`; `modelData.installmentAmountInMultiplesOf()`
appears nowhere in the method. The method spans `:579-607` (the report says `:579-606`; `.build();` is at `:606`,
brace at `:607`. Cosmetic.)

### 5.3 The seam routes through that overload and no other — CONFIRMED

The seam class exposes one method, which delegates once [VERIFIED:
`EmbeddableProgressiveLoanScheduleGenerator.java:45-47`], into
`ProgressiveLoanScheduleGenerator.java:82  LoanApplicationTerms loanApplicationTerms = LoanApplicationTerms.assembleFrom(modelData, mc);`
[VERIFIED: `grep -n`]. There is no second entry point.

### 5.4 The field is null on the seam path — PROVED DIRECTLY (stronger than the report)

The report infers this. I observed it. Assembling through the seam's own overload with
`installmentAmountInMultiplesOf = 100` and `currency.inMultiplesOf = 100`:

```
modelData.installmentAmountInMultiplesOf() = 100
terms.getInstallmentAmountInMultiplesOf()  = null
terms.installmentAmountInMultiplesOf (reflect) = null
```
[VERIFIED: `/tmp/t19/src/Verify.java` PROBE 1, run inside `fineract:latest`]

The mechanism is that the `Builder`-based private constructor never assigns the field
[VERIFIED: `LoanApplicationTerms.java:304-351` — no `this.installmentAmountInMultiplesOf =` anywhere in it], and the
`Builder` has no setter for it at all. Consequently
`ProgressiveLoanScheduleGenerator.java:110  …generatePeriodInterestScheduleModel(…, loanApplicationTerms.getInstallmentAmountInMultiplesOf(), mc)`
passes `null`, `applyInstallmentAmountInMultiplesOf` short-circuits on its own null guard
[VERIFIED: `ProgressiveEMICalculator.java:1761-1766`], and `safeRoundingForEMI` (`:1770-1776`) is never entered.
The down-payment rounding at `ProgressiveLoanScheduleGenerator.java:335-337` and
`LoanApplicationTerms.java:333-334` is dead for the same reason.

### 5.5 The server path honours it — CONFIRMED, but the report cites the wrong generator

Confirmed [VERIFIED: `LoanScheduleAssembler.java:557` passes
`loanProduct.getLoanProductRelatedDetail().getInstallmentAmountInMultiplesOf()` into the big `assembleFrom` overload
(`LoanApplicationTerms.java:625` signature), whose private constructor does assign it at `:828`].

But the report's evidence citations — `LoanApplicationTerms.java:1301-1305, 1617-1618` — are on the **cumulative /
declining-balance** generator family (`AbstractCumulativeLoanScheduleGenerator`), not the progressive generator this
program is porting. They prove Fineract honours the parameter *somewhere*; they do not prove the **same generator**
honours it. The correct progressive-path citations are `ProgressiveLoanScheduleGenerator.java:110`,
`ProgressiveEMICalculator.java:1761-1776`, `ProgressiveLoanScheduleGenerator.java:335-337`, and
`LoanScheduleAssembler.java:557`. `Money.java:154` is correctly cited (the `BigDecimal` overload consulting
`MoneyHelper.getRoundingMode()`).

### 5.6 The report's central argument is FALSE — REQUIRED CORRECTION

> "On a 100-unit loan with EMI `17.01`, rounding to multiples of 100 cannot possibly be a no-op."

It can, and by design it *must* be:

```java
// ProgressiveEMICalculator.java:1768-1776
// Rounds EMI to multiplesOf; falls back to currency precision when that would zero a positive EMI,
private Money safeRoundingForEMI(final Money unRoundedEMI, final Integer multiplesOf) {
    final Money roundedEMI = Money.roundToMultiplesOf(unRoundedEMI, multiplesOf);
    if (roundedEMI.isZero() && unRoundedEMI.isGreaterThanZero()) {
        return unRoundedEMI;
    }
    return roundedEMI;
}
```
[VERIFIED: source] and at runtime `roundToMultiplesOf(17.01, 100) = 0.00`
[VERIFIED: PROBE 2, HALF_EVEN tenant]. So an *honoured* `installmentAmountInMultiplesOf = 100` at C-00's inputs
returns the unrounded 17.01 and produces a byte-identical schedule. **Rows 1 and 3 of Finding 2's evidence table
(`T-00-he` vs `T-IM100-he`, `T-IM100-he` vs `T-IM100-hu`) are therefore consistent with the parameter being honoured
and prove nothing.**

The finding survives on the other two rows, which I checked are genuinely discriminating:

- `T-IM1-he`: `roundToMultiplesOf(17.01, 1) = 17.00` — non-zero, so no fallback; an honoured parameter would emit
  `17.00`, not `17.01` [VERIFIED: PROBE 2]. Output was identical to null. **Decisive.**
- `T-MNT5M-he` vs `T-MNT5M-plain-he`: EMI ≈ `320,221.91`; `roundToMultiplesOf(320221.91, 100) = 320200.00`
  [VERIFIED: PROBE 2]. Output identical across all 19 periods. **Decisive.**

The report must retire the 17.01 argument and lead with `T-IM1-he`, the MNT pair, and the direct reflective
observation in §5.4.

### 5.7 "Wiring ruled out — both available channels" is FALSE — REQUIRED CORRECTION

The `CurrencyData.inMultiplesOf` channel is gated:

```java
// Money.java:48-51
if (currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 && currency.getInMultiplesOf() > 0
        && MathUtil.isGreaterThanZero(amountScaled)) {
    amountScaled = roundToMultiplesOf(amountScaled, currency.getInMultiplesOf());
}
```
`Capture2.tenantCase` hard-codes `currencyDigits = 2` in **every** case [VERIFIED: `Capture2.java:77`], so
`decimalPlaces == 0` is never satisfied and the second channel was **structurally incapable** of moving a figure.
It corroborates nothing.

Worse for the report's framing, that channel **does** work when the gate is met. At `decimalPlaces = 0`, MNT
5,000,000 / 18 / 18.5 %:

```
decimals=0, currency.inMultiplesOf=100  → int=764100  rep=5764100
decimals=0, currency.inMultiplesOf=null → int=763994  rep=5763994
```
[VERIFIED: PROBE 4 → `d0==d0n ? false`]. So **multiples-of rounding is reachable through this seam** — just not the
`installmentAmountInMultiplesOf` component's semantics, which stay dead even at `decimalPlaces = 0`
[VERIFIED: PROBE 5 → record `multiplesOf=100` vs `null` at `decimals=0`, `equal ? true`].

This does not rescue the parameter, but it narrows the report's "uncapturable through this seam" claim, which as
written reads as though *no* multiples-of behaviour can be captured here. Precision matters: what is uncapturable
is `LoanRepaymentScheduleModelData.installmentAmountInMultiplesOf` and everything downstream of
`safeRoundingForEMI`; what *is* capturable is the `Money`-constructor currency rounding at zero decimal places.

### 5.8 A SECOND dropped input the report missed — `daysInYearCustomStrategy` — NEW FINDING

`installmentAmountInMultiplesOf` is the sole component `assembleFrom` never *reads*, which is what the report says.
But being read is not enough. `daysInYearCustomStrategy` **is** read
[VERIFIED: `LoanApplicationTerms.java:604 .daysInYearCustomStrategy(modelData.daysInYearCustomStrategy())`], is
stored on the `Builder` [VERIFIED: `:567-569`], and is then **never copied out of the builder by the constructor**
[VERIFIED: `:304-351` contains no `builder.daysInYearCustomStrategy`; mechanical diff of builder setters against
constructor reads leaves exactly this one]. Net effect is identical to Finding 2's:

```
modelData.daysInYearCustomStrategy() = FULL_LEAP_YEAR
terms.daysInYearCustomStrategy (reflect) = null
terms.toLoanConfigurationDetails().getDaysInYearCustomStrategy() = null
```
[VERIFIED: PROBE 1]

And it is empirically inert, tested where it should bite hardest — `DaysInYearType.ACTUAL` over leap-year 2024, MNT
5,000,000 / 18 / 18.5 % at `MathContext(19, HALF_UP)`:

```
FULL_LEAP_YEAR    : int=752235.66  rep=5752235.66
FEB_29_PERIOD_ONLY: int=752235.66  rep=5752235.66
null              : int=752235.66  rep=5752235.66
```
[VERIFIED: PROBE 3 → `FULL==FEB29 ? true   FULL==null ? true`]

`FEB_29_PERIOD_ONLY` vs `FULL_LEAP_YEAR` is a 365-vs-366 day-count switch — a money-moving input on `ACTUAL`
day-count products. **Two of nineteen contract inputs are silently discarded by the capture seam, not one.** The
report's claim that `installmentAmountInMultiplesOf` is "the sole component never read" is literally true and
materially misleading; the class of defect is bigger than it states.

### 5.9 Alternative explanations considered and eliminated

- *Builder defaults it from elsewhere?* No — the `Builder` has no such setter and the constructor never assigns the
  field [VERIFIED: `:304-351`, `:353-570`].
- *`CurrencyData.inMultiplesOf` consumed on an unexercised path?* It **is** consumed — it survives into the schedule
  model's currency [VERIFIED: PROBE 1 → `toLoanConfigurationDetails().getCurrencyData().getInMultiplesOf() = 100`] and
  bites at `decimalPlaces == 0` (§5.7). It is a different mechanism from the record component and does not restore it.
- *Applied but coincidentally invisible at these inputs?* True for `T-IM100-*` (§5.6), false for `T-IM1-he` and the
  MNT pair, and refuted outright by the reflective read (§5.4).
- *Ambient rounding mode changed the fallback?* No — `T-IM100-he` and `T-IM100-hu` are identical, and both would
  round 17.01 to zero either way [VERIFIED: PROBE 2].

### 5.10 Is it "rejection-grade for DEC-1"?

**Yes on substance, with the label sharpened.** The demonstrated defect is: DEC-1's grading path accepts contract
inputs it cannot honour, so a Go port that honours them and one that discards them are indistinguishable by the
corpus. Two inputs are affected today, and the mechanism (a hand-maintained `Builder` copy-constructor that silently
skips fields) means there is no structural guarantee a third does not exist in a future Fineract revision. For an
NBFI selling MNT loans where "round the installment to the nearest 100 ₮" is an ordinary product term, certifying
"silently ignore it" as correct is a real money risk. That is enough to block freezing DEC-1 in a form that implies
seam-captured vectors are sufficient. It is **not** enough to reject the seam as a capture mechanism for the inputs
it *does* honour, and the report does not claim otherwise. The report is not overstating the severity; it is
under-stating the scope and over-stating one piece of its evidence.

---

## 6. Finding 3 — the rounding-mode null result — CORRECT, WARNING SOUND, ONE COVERAGE HOLE (now closed by me)

The observation holds: `T-00-he`/`T-00-hu`, `T-IM100-he`/`T-IM100-hu`, `T-MNT5M-he`/`T-MNT5M-hu` are identical in
every column [VERIFIED: structural comparison — all 13 captures collapse into exactly **3** distinct observed
schedules, grouped `{T-00-notenant, T-00-he, T-00-hu, T-04f, T-04t, T-IM100-he, T-IM100-hu, T-IM1-he}`,
`{T-04f-big, T-04t-big}`, `{T-MNT5M-he, T-MNT5M-hu, T-MNT5M-plain-he}`].

**The narrow reading is correct, and the mechanism is cleaner than the report states.** `Money` resolves its context
as `mc != null ? mc : MoneyHelper.getMathContext()` [VERIFIED: `Money.java:494-496`], and the seam threads an
explicit `mc` through essentially every construction, so the ambient context is consulted only at the mc-less
factories and at `Money.roundToMultiplesOf(Money, Integer)` / `(BigDecimal, Integer)`
[VERIFIED: `Money.java:103,115,119,131,154,160`]. Those are exactly the sites the seam does not reach.

**The report's supporting citation is inaccurate, though.** It leans on "T17's finding that `ProgressiveEMICalculator`
contains zero `MoneyHelper` references". Textually true, but the class reaches `MoneyHelper` *indirectly* through
mc-less `Money` factories at `:182`, `:1630`, `:1638`, `:1661`, `:2191` and through
`Money.roundToMultiplesOf(Money, Integer)` at `:1771` [VERIFIED: `grep -n "MoneyHelper\|Money.zero(\|Money.of("`].
A textual grep is the wrong instrument here and should not be the stated basis.

**Coverage hole the report did not notice.** `ProgressiveEMICalculator.java:182` sits on the
`allowFullTermForTranche = true` path and *does* consult the ambient `MathContext` (§4a) — it is the only path in
the whole capture set that provably does. Pass 2 ran both tranche cases (`T-04t`, `T-04t-big`) under `HALF_EVEN(6)`
**only** [VERIFIED: `Capture2.java:104,109`], so the one path that touches `MoneyHelper` was never differentially
tested against `HALF_UP`. I closed it: MNT 5,000,000 / 18 / 18.5 %, `allowFullTermForTranche = true`, ambient
`HALF_UP` vs `HALF_EVEN` → identical [VERIFIED: PROBE 7 → `equal ? true`]. Unsurprising, since the value being
constructed is zero, but it should not have been left as an assumption.

**Is the warning strong enough?** Yes, and it is the best-argued paragraph in the report — it correctly refuses to
answer G-1 decision 6 and correctly identifies that the two consuming paths are the two the seam cannot reach. One
addition is needed: it should note that under the ratified `HALF_UP` tenant setting the ambient mode *would* bite on
the server path via `Money.java:154`/`:160` in `safeRoundingForEMI`, so the null result must never be cited as
evidence that the tenant mode is a free choice.

---

## 7. Finding 4 — MNT scale — invariants HOLD

Checked as observations, not re-derived as expectations. Across **all 13** captures [VERIFIED: Python over
`capture-tenant-raw.json` with `decimal.Decimal`]:

| Invariant | Result |
|---|---|
| Σ period principal == total disbursed (principal amortizes to zero) | holds, 13/13 |
| final `balance` == 0 and final `totalOutstandingBalance` == 0 | holds, 13/13 |
| per period `principal + interest == total` (splits sum to whole) | holds, 13/13 |
| Σ period interest == `totalInterestAmount` | holds, 13/13 |
| Σ period total == `totalRepaymentAmount` | holds, 13/13 |
| `totalRepaymentAmount == totalDisbursedAmount + totalInterestAmount` | holds, 13/13 |
| balance recursion `bal_i == bal_{i-1} − principal_i` from the disbursed amount | holds, 13/13 |
| balances strictly decreasing | holds, 13/13 |

For `T-MNT5M-*`: `5,000,000.00` disbursed, `763,994.33` interest, `5,763,994.33` repayment, 19 periods
[VERIFIED]. No invariant violation anywhere in the set.

The report's caveat that the currency code is inert is verified from pass-1 data: `D-01` (usd) and `D-01-mnt` (MNT),
identical inputs at 2 dp / precision 12, are identical in every column [VERIFIED: structural comparison]. So
"MNT-scale" here means "a 5,000,000-magnitude principal at two decimal places", not anything MNT-specific — the
report says as much and is right to.

---

## 8. Overclaim sweep

### Claimed but not established by the captures

1. **"a 17.01 EMI rounded to multiples of 100 cannot possibly be a no-op"** — false; `safeRoundingForEMI`
   guarantees it *is* a no-op at those inputs (§5.6). Load-bearing error in the report's headline finding.
2. **"supplied the value through both available channels simultaneously … neither moved a single figure"** — the
   second channel was gated off by `decimalPlaces == 2` and could not have moved anything (§5.7).
3. **"setting it `true` demonstrably takes a different code path, because that path reaches `MoneyHelper` and pass 1
   died there"** — the conclusion is true but the warrant is inference from an exception; the branch is directly
   visible at `ProgressiveEMICalculator.java:142-144` (§4a). Also, "a **third independent** confirmation … the first
   from the running oracle" oversells a null-differential plus an absence-of-tenant error as an independent
   confirmation.
4. **"the server path does honour the parameter (`LoanApplicationTerms.java:1301-1305, 1617-1618`)"** — those lines
   are the cumulative generator, not the progressive one being ported (§5.5). The claim is true; the citation does
   not support it for the relevant generator.
5. **"the *sole* component never read"** — true of `assembleFrom` in isolation, misleading as a statement about what
   the seam drops (§5.8).
6. **"it is uncapturable through this seam"** — true of the record component, too broad as stated about multiples-of
   rounding generally (§5.7).
7. Minor: `safeRoundingForEMI` is cited at `:1763-1764`, which is its *call site* inside
   `applyInstallmentAmountInMultiplesOf`; the method is at `:1770-1776`.
8. Minor: `LoanRepaymentScheduleModelData.java:32-40` → components end at `:39`;
   `LoanApplicationTerms.java:579-606` → method ends at `:607`.

### Established but not claimed

9. **`daysInYearCustomStrategy` is a second silently dropped input**, proved reflectively and by differential
   (§5.8). The most important omission.
10. **`CurrencyData.inMultiplesOf` is honoured through the seam at `decimalPlaces == 0`** (§5.7) — a capturable
    multiples-of behaviour the corpus could and should discriminate.
11. **`T-04f-big` reproduces pass-1 `D-01` exactly** — a fourth cross-pass control (§3).
12. **The mechanism of the pass-1 `D-04` exception** is `Money.zero(CurrencyData)` at
    `ProgressiveEMICalculator.java:182` (§4a).
13. **`safeRoundingForEMI`'s fallback semantics** are themselves a contract behaviour a Go port must reproduce
    (round to multiple, unless that zeroes a positive EMI, in which case keep the unrounded EMI). Nothing in the
    corpus pins it.
14. **The down-payment multiples-of rounding paths** (`LoanApplicationTerms.java:333-334`,
    `ProgressiveLoanScheduleGenerator.java:335-337`) are dead through the seam for the same reason, and every
    capture has `downPaymentPercentage = 0`, so they are doubly untested.

### The largest omission of all

15. **Every one of the 13 captures runs at threaded `MathContext(12, HALF_UP)`** — `precision` and `mode` are
    hard-coded in `Capture2.tenantCase` [VERIFIED: `Capture2.java:76-79`, and `mathContextPrecision: 12` in all 13
    JSON input blocks]. Under the tenant parameters ratified the same day (`CLAUDE.md` "Ratified tenant parameters",
    commit `5443fe0`, the direct parent of `2f61d29`), production is `(19, HALF_UP)` and precision-12 captures are
    **discrimination probes, not parity vectors**. This is not academic: pass-1 `D-01` (precision 12) and `D-01-p19`
    (precision 19) differ on identical inputs — `13393481.05` vs `13393481.04` [VERIFIED]. The report's
    "Does not: license any vector into the store" covers this procedurally but never states the substantive reason,
    and a reader could reasonably take `T-MNT5M-*` for a production-shaped MNT vector. It is not one.

### Inherited, not re-verified here

- "null at all 97 in-seam occurrences" and "the largest principal carrying a literal schedule … is 245,000" are
  T17's claims restated. **UNVERIFIED** in this audit; out of T19's scope.

---

## Required changes

Priority order. Items 1–4 must land before `PASS2-REPORT.md` is cited by any downstream task.

1. **Retract the 17.01 argument in Finding 2.** Replace with: (a) the direct reflective observation that
   `assembleFrom` yields `installmentAmountInMultiplesOf = null`, and (b) `T-IM1-he` and the `T-MNT5M` pair as the
   discriminating captures. State explicitly that `T-00-he`/`T-IM100-he` and `T-IM100-he`/`T-IM100-hu` are
   **non-probative**, because `ProgressiveEMICalculator.safeRoundingForEMI` (`:1770-1776`) returns the unrounded EMI
   when rounding would zero it.
2. **Retract "wiring ruled out — both channels".** State that `CurrencyData.inMultiplesOf` is gated on
   `currency.getDecimalPlaces() == 0` (`Money.java:48-51`), that the harness fixed decimals at 2, and that the
   channel therefore contributed no evidence. Add that at `decimalPlaces == 0` the channel *does* move the schedule
   (`763994 → 764100` at MNT 5,000,000).
3. **Add `daysInYearCustomStrategy` as a second dropped input**, with the mechanism (read by `assembleFrom` at
   `:604`, stored on the `Builder`, never copied by the constructor at `:304-351`) and the differential
   (`FULL_LEAP_YEAR` == `FEB_29_PERIOD_ONLY` == `null` at `DaysInYearType.ACTUAL` over leap-year 2024). Reframe the
   finding as a defect **class** — an unchecked hand-maintained builder copy — not a single field.
4. **State that all 13 captures are precision-12 probes**, not parity vectors, per the ratified `(19, HALF_UP)`
   production `MathContext`, and cite pass-1 `D-01` vs `D-01-p19` as proof that precision moves money at these
   inputs.
5. **Fix the server-path citations** in Finding 2 to the progressive generator: `ProgressiveLoanScheduleGenerator.java:110`,
   `ProgressiveEMICalculator.java:1761-1776`, `ProgressiveLoanScheduleGenerator.java:335-337`,
   `LoanScheduleAssembler.java:557`. Keep `Money.java:154` and mark `LoanApplicationTerms.java:1301-1305, 1617-1618`
   as the cumulative-generator family.
6. **Restate Finding 1's warrant** as the direct source branch (`ProgressiveEMICalculator.java:142-144`) rather than
   inference from pass 1's exception, and name `Money.zero(CurrencyData)` at `:182` as the exception's cause. Drop
   or soften "third independent confirmation".
7. **Correct the `ProgressiveEMICalculator` / `MoneyHelper` citation in Finding 3** — the class reaches `MoneyHelper`
   indirectly at `:182`, `:1630`, `:1638`, `:1661`, `:1771`, `:2191`. Add that the ambient mode *would* bite on the
   server path through `Money.java:154`/`:160`, so the null result never licenses leaving the tenant mode unset.
8. **Add the missing controls and gaps to the record:** `T-04f-big` == pass-1 `D-01`; the tranche path was never run
   under `HALF_UP` in pass 2 (PROBE 7 shows no difference, but the report should say pass 2 did not test it); the
   down-payment multiples-of paths are untested at `downPaymentPercentage = 0`; `safeRoundingForEMI`'s
   zero-fallback is itself unpinned contract behaviour.
9. **Fix the cosmetic line references** (`:32-40` → `:32-39`; `:579-606` → `:579-607`; `safeRoundingForEMI`
   `:1763-1764` → `:1770-1776`).
10. **Separate the two multiples-of fields in any future harness.** `Capture2.java:196,202` emit
    `currencyInMultiplesOf` and `installmentAmountInMultiplesOf` from one variable, so the JSON cannot represent
    varying them independently.

---

## What pass 2 does and does not license us to conclude about gate G-1

*My own reading, derived from the source and the reruns above — not a restatement of the report.*

**It licenses these, and only these.**

The capture environment is trustworthy and reproducible. The oracle image, JVM and seam class are the pinned ones;
the harness invents nothing; the committed outputs regenerate byte-for-byte; the tenant machinery is correctly
partitioned; the base schedule is unaffected by supplying a tenant; and every capture satisfies the money invariants
G-1 would grade against. If we later disagree about a number, we can settle it by re-running, which is the property
that actually matters for a vector store.

Pass 2 also settles one narrow behavioural question: on a single-disbursement loan, `allowFullTermForTranche` does
not move the emitted schedule — at precision 12, and (my extension) at production `(19, HALF_UP)` and at MNT scale.
Pinning it to `false` in DEC-1 is behaviourally safe *for that loan shape*, though the flag's whole purpose is the
shape the seam cannot express.

Most importantly, pass 2 — corrected and extended by this audit — establishes a **structural property of the
grading path**, which is a stronger and more useful result than any individual number it produced. The embeddable
seam accepts a 19-component contract and honours 17 of them. `installmentAmountInMultiplesOf` and
`daysInYearCustomStrategy` are taken in and discarded before any arithmetic sees them, and `disbursementDatas` is
forced empty. For those inputs the corpus has **zero discriminating power**: a Go implementation that honours them
and one that ignores them produce identical vectors and both pass. That is a defect in the *conformance rig*, not in
either implementation, and it is the second time this program has found one of its kind (after T5's
precision-vs-scale). It is a sufficient reason not to freeze DEC-1 in any form that treats seam-captured vectors as
adequate coverage of the contract's input domain.

**It licenses none of these.**

No vector may enter the store from this pass. Not because the audit failed — the observations are sound — but
because every capture ran at threaded `MathContext(12, HALF_UP)` while production is `(19, HALF_UP)`, and pass 1
already showed a one-cent divergence between those two settings on identical inputs. All 13 are discrimination
probes. `T-MNT5M-*` in particular is not a Mongolian parity vector; it is a magnitude probe that happens to carry
the string `MNT`, and pass 1 established the currency code is inert at equal decimal places.

No G-1 decision is answered. Decision 6 (tenant rounding mode) is *specifically* unanswered: the null result is real
but vacuous, because the only two paths that consult the ambient `MathContext` — multiples-of rounding and
multi-disbursement tranching — are precisely the two this seam cannot exercise. The one path in the capture set that
does touch `MoneyHelper` (`Money.zero(CurrencyData)` on the tranche branch) constructs a zero, so it could not have
discriminated anything. Reading "the mode didn't matter" out of this pass would be an error, and the report is right
to say so.

Nothing is licensed about multi-disbursement behaviour, down-payment rounding, `safeRoundingForEMI`'s zero-fallback,
or day-count custom strategies. Each is either structurally unreachable through the seam or fixed at a neutral value
in all 13 cases.

**What follows for the gate.** G-1 should not be closed on the premise that Tier 0's embeddable seam is a sufficient
grading path. Two concrete things must precede it: a capture route that exercises the dropped inputs — realistically
the running Fineract server's schedule-preview API against PostgreSQL, a materially larger rig than Tier 0 assumed —
and a per-input honoured/dropped table in DEC-1 itself, mechanically derived rather than hand-written, since the
defect found here is exactly a hand-maintained field copy that silently skipped two entries. Until both exist,
"vectors pass" cannot mean "the contract is covered", and the cutover gate must not be approached on that basis.
