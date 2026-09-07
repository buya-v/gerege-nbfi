# T551 — apply T548's conditions on T532 (`interestperiod.go` citation record)

Branch `softhouse/T551-t548-conditions`, forked from `main` at `b09d2dcf`.
Reference oracle (Fineract) checkout `/home/user/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb` (read from `.git/HEAD`; the checkout's
revision was not changed by this task).
`InterestPeriod.java` measures **237 lines** there — `wc -l` confirmed before any
citation was graded.

The reference oracle SERVICE is unreachable from this sandbox. This task is
source-citation work and needed none; nothing below rests on a live oracle call.

Every condition applied here was a **wrong statement checked into the tree wearing
a `[VERIFIED]` badge**. In each case the *conclusion* was left standing and only
the *stated reason or count* was corrected — that distinction is the whole point of
this chain, and the opposite error (throwing out a true conclusion with a false
premise) would have been just as bad.

---

## Changes Made

Two files, **comments and citations only**. No Go statement, identifier, type,
constant, test or fixture changed — proven byte-identical below.

### `nexus/internal/apps/loanproduct/interestperiod.go`

1. **File banner, "THERE IS NO OFFSET" paragraph (MAJOR-1).** Retracted "the error
   … CHANGES SIGN across the file" and the quoted range "-94 to +69". Replaced with
   the measured table: eleven delta rows, every one `<= 0`, min `-94`, max `0`, no
   positive value; and an explicit statement that the `+13` the old wording folded
   in is a `MathUtil.java` citation — a different file — so mixing two files'
   deltas into one table is how the false claim was manufactured. **The no-offset
   conclusion is kept and re-grounded**: an offset is defeated by SPREAD and
   non-monotonicity (magnitudes 0, -3, -52, -55, -58, -59, -63, -69, -94, out of
   file order), not by a sign change, and T530's refutation of T526's "12-14 line
   offset" therefore stands unaffected.
2. **File banner, new partition block (MAJOR-2).** Added the closing decomposition
   `22 = 10 (past EOF) + 1 (overrun) + 9 (real but WRONG MEMBER) + 2 (wrong extent)`
   with every member of every class enumerated, plus a plain statement that the
   wrong-member class was **under-counted 4.5x** (two reported, nine real) by the
   sweep built to find it, that the two reported are only the two spanning a
   *complete* method — a narrowing T532 never states — and that this class is
   invisible to both a line-existence check and an offset check.
3. **File banner, "NO RANGE WAS REPOINTED" paragraph (MINOR-6).** "only the two …
   (DateUtils, MathUtil) were checked" corrected to **four** files with spans read
   directly (DateUtils, MathUtil, Money, MoneyHelper), and the unaudited
   enumeration completed from four families to **seven** — the old list omitted
   `ProgressiveLoanScheduleGenerator`, `ProgressiveLoanInterestScheduleModel` and
   `InterestScheduleModelRepositoryWrapperImpl`. Also notes that two of the three
   asymmetry receipts were rewritten here.
4. **`Length` doc comment (MAJOR-2, at the site).** Added that `:229-231` is one of
   **nine** such citations, not one of two, pointing at the banner's partition.
5. **`UpdateOutstandingLoanBalance`, asymmetry #2 (MINOR-4).** Retracted "The
   MathContext only ever reaches the ZERO that is substituted … never the value
   that is kept." The 2-arg `negativeToZero` passes `mc` to the **predicate** as
   well. Conclusion re-grounded on the mechanism: the predicate compares against
   `Money.zero(currency, mc)`, whose amount is zero under every rounding mode and
   precision, so both overloads compare against and floor at the same zero.
6. **`AddBalanceCorrectionAmount`, asymmetry #3 (MAJOR-3, MONEY).** Retracted the
   unsound receipt and replaced it with a sound one. Details in *Money-math notes*.

### `nexus/internal/apps/loanproduct/doc.go`

7. **Citation-audit bullet (MAJOR-1 + MAJOR-2 + MINOR-5).** The false sign claim
   `"the drift changed sign (-94 to +69)"` retracted and restated as above;
   `"two wrong ranges … resolved to REAL BUT WRONG members"` corrected to **nine**
   with the closing partition recorded; `"the sixth surviving citation is the bare
   :151 … which carries no VERIFIED token"` corrected — **two** of the six
   survivors are untokened (`:65-66` and `:151`); and the reconstruction of how
   T530's "23" arose is now marked **conjecture**, with the arithmetic shown (both
   booked → 24 of 28, neither → 22, 23 needs exactly one, which is not a census
   anyone would deliberately run).

---

## Each condition, re-derived

All Java line numbers below were read from `/home/user/fineract` at `426a23544`.
Commands are given so each row can be re-run.

### Instruments

```
$ cat /home/user/fineract/.git/HEAD
426a23544e8426a38ae43ae404670a0a7e85b9eb
$ wc -l /home/user/fineract/fineract-progressive-loan/src/main/java/org/apache/\
fineract/portfolio/loanproduct/calc/data/InterestPeriod.java
237
$ git show 8e1c1a5b:nexus/internal/apps/loanproduct/interestperiod.go > old.go   # pre-sweep
```

I read all 237 lines of `InterestPeriod.java` before grading a single span, and
wrote my own multi-line-aware census (reconstructs contiguous `//` blocks, joins
them, regexes `InterestPeriod\.java:(\d+)(-(\d+))?` over the joined text, reports
whether each hit sits inside a balanced `[VERIFIED: … ]` token, and tags each with
the Go declaration the block annotates so old and new can be paired by anchor).

```
$ python3 census.py old.go
=== old.go: 28 mechanical, 26 inside VERIFIED, 2 bare
$ python3 census.py <current interestperiod.go>
=== 33 mechanical, 31 inside VERIFIED, 2 bare
```

28 / 26 / 2 on the pre-sweep file — I independently reproduce T532's and T548's
counts, and the two bare sites are `old.go:66` (`:65-66`) and `old.go:240`
(`:151`), matching T548 exactly.

### MAJOR-1 — the sign claim

Pairing old→new by Go declaration anchor, `Δ = new_start − old_start`:

| anchor (Go decl) | old start | new start | Δ | verified new span |
|---|---:|---:|---:|---|
| `CreditedPrincipal` | 299 | 205 | **−94** | `getCreditedPrincipal()` 205-207 |
| `CreditedInterest` | 303 | 209 | **−94** | 209-211 |
| `DisbursementAmount` | 307 | 213 | **−94** | 213-215 |
| `BalanceCorrectionAmount` | 311 | 217 | **−94** | 217-219 |
| `OutstandingLoanBalance` | 315 | 221 | **−94** | 221-223 |
| `CapitalizedIncomePrincipal` | 319 | 225 | **−94** | 225-227 |
| `RateFactorValue` | 323 | 229 | **−94** | `getRateFactor()` 229-231 |
| `RateFactorTillPeriodDueDateValue` | 327 | 233 | **−94** | 233-235 |
| `Length` | 229 | 160 | **−69** | `getLength()` 160-162 |
| `LengthTillPeriodDueDate` | 233 | 164 | **−69** | 164-166 |
| `UpdateOutstandingLoanBalance` | 237 | 168 | **−69** | 168-188 |
| `CreditedAmounts` | 256 | 193 | **−63** | `getCreditedAmounts()` 193-195 |
| `CalculatedDueInterest` | 193 | 134 | **−59** | 134-143 |
| `CalculatedDueInterestFor` | 203 | 145 | **−58** | 145-158 |
| `IsFirstInterestPeriod` | 252 | 197 | **−55** | `isFirstInterestPeriod()` 197-199 |
| five `Add*` mutators | 165/169/173/177/181 | 113/117/121/125/129 | **−52** each | 113-115 … 129-132 |
| field block | 48 | 45 | **−3** | 45-73 |
| `withEmptyInterestPeriod` | 94 | 94 | **0** | 94-106 (end moved 109→106) |

Set = `{−94×8, −69×3, −63, −59, −58, −55, −52×5, −3, 0}` → **min −94, max 0, no
positive value**. `[VERIFIED: InterestPeriod.java, whole file at 426a23544]`

**The three spans the driver verified independently, re-derived by me rather than
accepted — I agree with the driver on all three:**

- `isFirstInterestPeriod` is at **:197** (`public boolean isFirstInterestPeriod() {`),
  body :198, close :199. Old citation `:252-254`. `197 − 252 = −55`. ✔ agrees.
- `getLength` is at **:160** (`public long getLength() {`), body :161, close :162.
  Old citation `:229-231`. `160 − 229 = −69`. ✔ agrees.
- `getCreditedAmounts` is at **:193** (`public Money getCreditedAmounts() {`), body
  :194, close :195. Old citation `:256-259`. `193 − 256 = −63`. ✔ agrees.

No disagreement with the driver's measurements to report.

The `+13`: the pre-sweep file cited `MathUtil.java:175-178` for `ratNegativeToZero`;
the corrected span is `MathUtil.java:188-190`. `188 − 175 = +13`, and it is a
**different file**. Confirmed at source: `:175-177` is
`nullToZero(BigDecimal) → nullToDefault(value, BigDecimal.ZERO)` and `:188-190` is
`negativeToZero(BigDecimal) → isGreaterThanZero(value) ? value : BigDecimal.ZERO`
`[VERIFIED: MathUtil.java:175-177, 188-190]`. So the sign-change claim rested
entirely on mixing two files into one table.

**What I did NOT do:** I did not weaken "there is no offset". The measurement
supports it more strongly than the sign story did — nine distinct magnitudes over
a 94-line range, out of file order — and T530's refutation of T526's "12-14 line
offset" is untouched.

### MAJOR-2 — the wrong-member class is 9, and the partition closes

Each of the 22 pre-sweep spans classified by what it *actually is* in the 237-line
file. Every row below was read directly.

**10 wholly past EOF (> 237):** `:252-254 :256-259 :299-301 :303-305 :307-309
:311-313 :315-317 :319-321 :323-325 :327-329`.

**1 overrun:** `:237-250` — `:237` is the class's closing `}` (the file's last
code line); 238-250 do not exist.

**9 real-but-wrong-member, wholly in file:**

| span | what it really is | flagged by T532? |
|---|---|---|
| `:229-231` | `getRateFactor()` — complete method | yes |
| `:233-235` | `getRateFactorTillPeriodDueDate()` — complete method | yes |
| `:193-201` | `getCreditedAmounts()` 193-195 + `isFirstInterestPeriod()` 197-199 + `getCurrency()` signature 201 | **no** |
| `:203-219` | `getCurrency()` close 203 + `getCreditedPrincipal` 205-207 + `getCreditedInterest` 209-211 + `getDisbursementAmount` 213-215 + `getBalanceCorrectionAmount` 217-219 | **no** |
| `:165-167` | tail of `getLengthTillPeriodDueDate()` (`return DateUtils…` 165, `}` 166, blank 167) | **no** |
| `:169-171` | head of `updateOutstandingLoanBalance()` (`if (isFirstInterestPeriod())` 169, `Optional<RepaymentPeriod> previous…` 170, `if (…isPresent())` 171) | **no** |
| `:173-175` | body of `updateOutstandingLoanBalance()` (`this.outstandingLoanBalance = MathUtil.negativeToZero(…` 173, two `.plus(…)` 174-175) | **no** |
| `:177-179` | body/close (`.minus(…getDuePrincipal…)` 177, `.plus(…getPaidPrincipal…), getMc());` 178, `}` 179) | **no** |
| `:181-183` | else-branch (`int index = …indexOf(this);` 181, `…get(index - 1);` 182, `this.outstandingLoanBalance = MathUtil.negativeToZero(…` 183) | **no** |

**2 in-file with the wrong extent:**

- `:48-60` — a **truncated** field block: `@NotNull` 48 … `creditedPrincipal` 60.
  The real block is `:45-73`.
- `:94-109` — both `withEmptyAmounts` overloads (94-99, 101-106) **plus** `@Override`
  108 and `public int compareTo(…)` 109, i.e. it overruns into a real wrong member.

```
22 = 10 + 1 + 9 + 2      ✔ closes exactly
```

`[VERIFIED: InterestPeriod.java:43-237, read in full]` I confirm T548's partition
independently. **Said plainly in the banner and here: the class that a citation
sweep exists to catch — a citation that still resolves, on a real member, and so
passes every line-existence and offset check — was under-counted by a factor of
4.5 by that very sweep.** All nine were corrected correctly; no number moved. What
was wrong is the count, and the count was checked in as verified.

### MAJOR-3 — the benignity receipt (MONEY; see also *Money-math notes*)

T548's premise re-derived at source, and it holds:

- `InterestPeriod.java:113-115` — `addBalanceCorrectionAmount` calls the **2-arg**
  `MathUtil.plus`. `[VERIFIED]`
- `MathUtil.java:388-390` — `plus(Money, Money) → first.plus(second)`. `[VERIFIED]`
- `MathUtil.java:392-394` — `plus(Money, Money, MathContext)`, used by the four
  siblings. `[VERIFIED]`
- `Money.java:236-238` — `plus(Money) → plus(moneyToAdd, getMc())`, the
  **receiver's** mc. `[VERIFIED]`
- `InterestPeriod.java:217-219` — `getBalanceCorrectionAmount()` returns
  `MathUtil.nullToZero(balanceCorrectionAmount, getCurrency(), getMc())`. `[VERIFIED]`
- `MathUtil.java:338-340` — `nullToZero(Money, currency, mc) → nullToDefault(value,
  Money.zero(currency, mc))`. `[VERIFIED]`
- `MathUtil.java:342-344` — `nullToDefault(Money, Money)` is literally
  `return value == null ? def : value;`. `[VERIFIED]`

**So `getMc()` reaches only the substituted zero.** When the field is non-null the
accessor returns the **stored** `Money` with whatever `MathContext` it was built
with — it is **not** "built with `getMc()`", and the old receipt's load-bearing
step is false. The guarded oracle call site confirms the non-null case is live:
`RepaymentPeriod.java:190-194` copies the interest period and calls the method only
inside `if (!interestPeriodCopy.getBalanceCorrectionAmount().isZero())`. `[VERIFIED]`

### MINOR-4 — asymmetry #2's mechanism

- `MathUtil.java:356-358` — 2-arg: `value == null || isGreaterThanZero(value, mc)
  ? value : Money.zero(value.getCurrencyData(), mc)`. The `mc` reaches the
  **predicate** too. `[VERIFIED]`
- `MathUtil.java:368-370` → `Money.java:446-448` — `isGreaterThanZero(mc)` is
  `isGreaterThan(Money.zero(getCurrencyData(), mc))`. `[VERIFIED]`
- `MathUtil.java:351-353` → `Money.java:442-444` — 1-arg uses the value's own mc.
  `[VERIFIED]`
- `Money.java:126-128` → `Money.java:40-53` — `Money.zero`'s amount is
  `BigDecimal.ZERO` through the private constructor's
  `setScale(decimalPlaces, roundingMode)`, i.e. zero under every mode and
  precision. `[VERIFIED]` — so both branches agree and the conclusion survives.

The call-site spans `InterestPeriod.java:173-178` (2-arg) and `:183-186` (1-arg)
are **correct as cited** — I re-read them: `:178` ends
`.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc()), getMc());`
(the trailing `getMc()` is `negativeToZero`'s second argument), while `:186` ends
`.plus(previousInterestPeriod.getDisbursementAmount(), getMc()));` with no such
argument. `[VERIFIED: InterestPeriod.java:168-188]`

### MINOR-5 — "the sixth surviving citation"

The six survivors and their tokens, from my census of the pre-sweep file:

| site | span | inside `[VERIFIED: … ]`? |
|---|---|---|
| `old.go:66` | `:65-66` | **NO** |
| `old.go:70` | `:178` | yes |
| `old.go:81` | `:151` | yes |
| `old.go:240` | `:151` | **NO** |
| `old.go:249` | `:178` | yes |
| `copy` block | `:86-92` | yes |

**Two**, not one. `doc.go`'s prose named only `:151` and called it "the sixth",
implying a single untokened survivor; corrected to name both.

The "23" arithmetic, now recorded as conjecture: mechanical 28, tokened 26, wrong
22 → a grep census reports **22 of 26**. Booking both untokened items as unresolved
gives **24 of 28**; booking neither gives **22**. **23 requires exactly one of the
two booked** — not a census anyone would deliberately run. No derivation produces
23, so the explanation is conjecture and is now labelled as such.

### MINOR-6 — the banner's counts

```
$ grep -oE '[A-Za-z]+\.java:[0-9]' interestperiod.go | sed 's/:.*//' | sort | uniq -c
     33 InterestPeriod.java          5 RepaymentPeriod.java
      5 ProgressiveEMICalculator.java 4 MathUtil.java
      2 ProgressiveLoanScheduleGenerator.java
      2 LoanSchedulePlan.java         2 DateUtils.java
      1 ProgressiveLoanInterestScheduleModel.java
      1 Money.java
      1 InterestScheduleModelRepositoryWrapperImpl.java
      1 AdvancedPaymentScheduleTransactionProcessor.java
```

Ten non-`InterestPeriod` files are cited. Checked-with-spans-read: DateUtils and
MathUtil (T532; I re-read all four MathUtil spans), Money (T532 added `:236-238`;
I re-read it and added six more spans), MoneyHelper (added by me) — **four**, not
two. Genuinely unaudited: **seven** families, three of which the old enumeration
omitted. Both counts corrected.

### Byte identity — reproduced, and the baseline matches

Stripper: `go/parser` **without** `parser.ParseComments`, then `File.Doc`,
`File.Comments` and every `Doc`/`Comment` field on `GenDecl`/`FuncDecl`/`Field`/
`ValueSpec`/`TypeSpec`/`ImportSpec` nil'd via `ast.Inspect`, printed with
`printer.Config{Mode: printer.RawFormat, Tabwidth: 8}`. Run over the base tree
(`git archive b09d2dcf`) and over my working tree.

```
calculator.go                 12782      interestperiod_test.go     2698
calculator_test.go             8015      interestrate.go             242
dates.go                       2664      method.go                  5518
doc.go                           20      method_test.go             4576
frequency.go                   5175      money.go                   3954
interestperiod.go              7042      relateddetail.go           1733
                                         repaymentperiod.go        12690
                                         schedulemodel.go          11390
TOTAL                         78499  (14 files)

$ diff -u base.txt branch.txt
(identical)
```

**14 files, TOTAL 78,499 bytes — matching T532's and T548's baseline exactly**,
per file, including `interestperiod.go` 7042, `money.go` 3954,
`repaymentperiod.go` 12690, `doc.go` 20. (My FNV digests differ from T548's
because the hash implementation differs; the byte counts, which are the claim,
match.) Corroborated:

```
$ git diff -U0 -- nexus/internal/apps/loanproduct/ | grep -E '^[+-]' \
    | grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]\s*//' | grep -vE '^[+-]\s*$'
(no output — every changed line is a // comment)
```

### Build / test

```
$ gofmt -l nexus/internal/apps/loanproduct/     (clean)
$ go build ./...                                exit 0
$ go vet ./internal/apps/loanproduct/           exit 0
$ go test ./internal/apps/loanproduct/          ok 0.005s
$ go test ./...                                 all packages ok, 0 FAIL
```

Go 1.24.7 at `/usr/local/go/bin/go`. No test was weakened, skipped or edited —
the diff contains no test file at all.

---

## Money-math notes

The only money-touching change is the `AddBalanceCorrectionAmount` receipt
(MAJOR-3). **No arithmetic changed** — the diff is comment-only and proven
byte-identical, so the Go body
`ip.balanceCorrectionAmount = ip.BalanceCorrectionAmount().plus(additional)` is
untouched. What changed is the *argument* for why it matches the oracle.

**Why the old argument was unsound:** it claimed the receiver of Fineract's 2-arg
`MathUtil.plus` is "built with `getMc()` at `:217-219`". It is not —
`nullToZero → nullToDefault` returns the stored value **unchanged** when non-null
`[VERIFIED: MathUtil.java:338-340, 342-344]`, so `getMc()` reaches only the
substituted zero, and the non-null case is precisely what the guarded call site
reaches `[VERIFIED: RepaymentPeriod.java:190-194]`.

**The sound argument that replaces it, and it needs no assumption about which
MathContext the receiver carries.** Following the 2-arg path to the bottom:

| step | source | what it does |
|---|---|---|
| `MathUtil.plus(Money, Money)` | `MathUtil.java:388-390` | `first.plus(second)` |
| `Money.plus(Money)` | `Money.java:236-238` | `plus(that, getMc())` — receiver's mc |
| `Money.plus(Money, mc)` | `Money.java:240-247` | `this.plus(toAdd.getAmount(), mc)` |
| `Money.plus(BigDecimal, mc)` | `Money.java:253-259` | `this.amount.add(amountToAdd)` — **no MathContext argument**, exact BigDecimal addition — then `Money.of(currency, sum, mc)` |
| `Money.of(CurrencyData, BigDecimal, mc)` | `Money.java:106-108` | `new Money(...)` |
| `private Money(currency, amount, mc)` | `Money.java:40-53` | `this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())` (`:52`) |

All six rows `[VERIFIED]` against `426a23544`.

1. **Precision never participates.** The addition is exact `BigDecimal.add` with no
   `MathContext`. The `mc` reaches exactly one place — the *rounding mode* argument
   of that one `setScale`. So `MoneyHelper.PRECISION = 19` vs anything else cannot
   move this number, and the ratified `(19, HALF_UP)` is not load-bearing here.
2. **The rounding mode cannot bite either.** Every `Money`'s `amount` was itself set
   to `currency.getDecimalPlaces()` scale by that same constructor line, so the sum
   of two amounts at that scale is already at that scale and `setScale` to the same
   scale is a no-op — **no rounding occurs at all**. Caveat recorded in the file:
   `Money.isSameCurrency` compares only the currency **CODE**
   `[VERIFIED: Money.java:324-326]`, so this step assumes both operands carry the
   same `CurrencyData` decimal places; a single schedule model carries a single
   currency, so they do on every path in this package.

**On T548's first suggested reason, which I have hedged rather than adopted
wholesale.** T548 wrote that `MoneyHelper.getMathContext()` is memoised per tenant
`[VERIFIED: MoneyHelper.java:35, :91-93 — confirmed:
mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION,
getRoundingMode()))]` and concluded "**Every** `MathContext` in this object graph
traces back to that one cached instance." That last step is **not** structurally
guaranteed, and I found a counterexample in the same Gradle module:
`new MathContext(MoneyHelper.getMathContext().getPrecision(), RoundingMode.DOWN)`
`[VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:2845]` — a
`MathContext` that is not the cached instance and carries a **different rounding
mode**. Whether a `Money` carrying it can reach this receiver I did **not**
establish `[UNVERIFIED]`. So the file records the memoisation as a *production
configuration fact, explicitly not load-bearing*, and rests the receipt on the
structural argument, which does not care. Writing T548's stronger claim in as
verified would have repeated exactly the defect this task is fixing.

Non-negotiables: no float anywhere (diff is comment-only and byte-identical); no
schema, API field or fixture touched; no ledger write, no `Idempotency-Key`
surface, no contract change, no cutover or deposit-activation implication.

---

## Unverified

- `[UNVERIFIED]` Whether a `Money` carrying the `RoundingMode.DOWN` `MathContext`
  built at `AdvancedPaymentScheduleTransactionProcessor.java:2845` can reach
  `InterestPeriod.balanceCorrectionAmount`. I did not trace it; the receipt is
  written so the answer does not matter. Tracing it is a follow-up, not a blocker.
- `[UNVERIFIED: oracle_unreachable]` No live reference-oracle call was made. None
  was needed — every claim here is a source-citation claim graded against the
  pinned checkout. No golden vector was captured, compared or relied on.
- `DateUtils.java:319-321` and `:308-313` are recorded in the banner as checked
  **by T532**. I did not re-read them; the banner attributes them to T532, not to
  me. Everything I attribute to T551 I read myself.
- I did not re-audit the 30 post-sweep `InterestPeriod.java` spans end to end.
  T548 did that and reports all resolve; I re-derived only the spans this task's
  conditions turn on (listed above) plus the full old→new delta pairing.

---

## Blockers

None. All six conditions (MAJOR-1/2/3, MINOR-4/5/6) are applied within
`nexus/internal/apps/loanproduct/`. Build, vet, gofmt and the full test suite are
green, and the comment-only byte-identity proof reproduces T532's baseline exactly.

---

## Follow-ups

Backlog — discovered in scope, deliberately **not** edited because they fall
outside my `files_hint`:

1. **`.softhouse/handoff/T532-interestperiod-citations.md`** still carries the
   false sign table ("−94 to +69", "changes sign") and the "two REAL BUT WRONG
   members" count. T548's condition 1 names the handoff explicitly. It is another
   worker's artifact and outside my scope; someone should correct it or record it
   as superseded by this handoff. **Do not rewrite git history** — commit
   `345f492e` propagated the same list and the driver has corrected the record
   separately.
2. **Trace the `RoundingMode.DOWN` MathContext.** `AdvancedPaymentScheduleTransaction\
   Processor.java:2845` constructs a non-cached `MathContext`. Establishing whether
   a `Money` carrying it can reach the progressive-loan `InterestPeriod` graph would
   either retire the caveat above or turn up a genuine rounding-mode divergence
   worth a vector. Worth a small dedicated task.
3. **The seven unaudited cited files** (`RepaymentPeriod`, `ProgressiveEMICalculator`,
   `AdvancedPaymentScheduleTransactionProcessor`, `LoanSchedulePlan`,
   `ProgressiveLoanScheduleGenerator`, `ProgressiveLoanInterestScheduleModel`,
   `InterestScheduleModelRepositoryWrapperImpl`) remain the cross-file citation
   population T549 owns. The banner now enumerates all seven so T549's scope is
   readable from the file.
4. **Generalise the count-the-class rule.** The lesson worth adding to
   `.softhouse/patterns.md` (not edited — outside scope): *count a mis-citation
   class by "does the span resolve to the member named above it", never by "is the
   span a whole method"* — the narrowing is what hid seven of nine here, and it
   would hide them again in any other file. Likewise: *never build an offset/drift
   table across more than one source file* — that single mistake manufactured the
   false sign claim.

---

**Honesty statement.** Every Java line number in this handoff and in the two edited
files was read by me from `/home/user/fineract` at `426a23544`. Where I could not
establish something I wrote `[UNVERIFIED]` and said where I looked. I re-derived
the three spans the driver had verified independently rather than accepting them,
and I agree with the driver on all three. No claim here rests on a value I did not
measure.
