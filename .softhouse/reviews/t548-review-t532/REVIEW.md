# T548 — independent review of T532 (`interestperiod.go` citation sweep)

**VERDICT: ACCEPT WITH CONDITIONS**

Subject: branch `softhouse/T532-interestperiod-citations`, tip `19a328a218f41973d2b9c3234164ed3b3f9a5347`.
Reviewer worktree `/home/user/wt/T548`, branch `softhouse/T548-review-t532`, based on `main` at `345f492e`.

## Reference oracle (Fineract) HEAD verified

```
$ git -C /home/user/fineract rev-parse HEAD
426a23544e8426a38ae43ae404670a0a7e85b9eb
```

Matches the pin. **Every Java line number below was read from that checkout**, from
`fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/InterestPeriod.java`
(237 lines, `wc -l` confirmed) and from `fineract-core/.../MathUtil.java`, `.../Money.java`,
`.../MoneyHelper.java`, `.../DateUtils.java`, `.../calc/data/RepaymentPeriod.java`. I read all
237 lines of `InterestPeriod.java` before grading a single span.

## Scope instrument

Used the merge-base form throughout, as instructed:

```
$ git merge-base origin/main origin/softhouse/T532-interestperiod-citations
8e1c1a5b0a7a9e3171d458545874ca3a5eec5434
$ git diff --name-only 8e1c1a5b..origin/softhouse/T532-interestperiod-citations
.softhouse/handoff/T532-interestperiod-citations.md
nexus/internal/apps/loanproduct/doc.go
nexus/internal/apps/loanproduct/interestperiod.go
```

`origin/main..<branch>` additionally shows `.softhouse/tasks.json` (33 lines) — that is `main`
moving under the branch, **not** a T532 edit. I did not file it. Scope is clean: three files,
no poaching of `money.go` (T542) or `repaymentperiod.go` (T547).

---

# FINDINGS

## MAJOR-1 — "The drift changed sign" is FALSE. Three rows of the offset table carry the wrong sign.

T532's handoff table, its file banner and the checked-in `doc.go` all state the start-line error
"changes sign", quoting the range **"−94 to +69"**. I re-derived every row as `new_start − old_start`:

| correction | old | new | true Δ | T532 says | |
|---|---:|---:|---:|---:|---|
| accessor block (8 citations) | 299 | 205 | **−94** | −94 | ok |
| `Length` / `LengthTillPeriodDueDate` | 229 | 160 | **−69** | **+69** | **SIGN WRONG** |
| `IsFirstInterestPeriod` | 252 | 197 | **−55** | **+55** | **SIGN WRONG** |
| `CreditedAmounts` | 256 | 193 | **−63** | **+63** | **SIGN WRONG** |
| `CalculatedDueInterest` | 193 | 134 | −59 | −59 | ok |
| `CalculatedDueInterestFor` | 203 | 145 | −58 | −58 | ok |
| `UpdateOutstandingLoanBalance` | 237 | 168 | −69 | −69 | ok |
| five `Add*` mutators | 165 | 113 | −52 | −52 | ok |
| field list | 48 | 45 | −3 | −3 | ok |
| `MathUtil.negativeToZero` — **different file** | 175 | 188 | +13 | +13 | ok |
| `withEmptyAmounts` | 94 | 94 | 0 | 0 | ok |

The sign convention is fixed by the rows that are right (`new − old`; the accessor block is
`205 − 299 = −94`, recorded as −94). Under that convention the three flagged rows are all
negative, and:

**Every `InterestPeriod.java` delta is ≤ 0.** The set is `[−94, −69, −55, −63, −59, −58, −69,
−52, −3, 0]` — min −94, max 0, **no positive value**. The single positive (+13) is the
`MathUtil.java` citation, i.e. a *different file*, and cannot be evidence about drift within
`InterestPeriod.java`.

This is not cosmetic. It is the load-bearing evidence for the no-offset rule the program is
being told to follow, and `doc.go` now carries it as a checked-in fact:

> `// (-94 to +69) and was non-monotonic, and two wrong ranges (:229-231,` — `doc.go`

**The conclusion "there is no offset" survives** — the deltas span 0 to −94 and are
non-monotonic in file order, so no single shift explains them. But the recorded *reason* is
false, and the driver's brief has already propagated the bad list. **Condition:** restate as
"uniformly non-positive but wildly non-monotonic, 0 to −94" in `doc.go`, the file banner and the
handoff, and drop "changes sign".

## MAJOR-2 — The real-but-wrong-member class is **9**, not 2. This is the class the brief predicted would be under-counted, and it was — by 7.

T532 reports exactly two citations that "resolved to REAL BUT WRONG members" (`:229-231`,
`:233-235`), and both `doc.go` and the new file banner record "two". The driver verified those
two. I verified them too — and then classified **all 22** corrected citations by what the *old*
span actually is in the 237-line file:

| old span | what it really is at `426a2354` | class |
|---|---|---|
| `:299-301 :303-305 :307-309 :311-313 :315-317 :319-321 :323-325 :327-329 :252-254 :256-259` | past line 237 | **10 wholly past EOF** |
| `:237-250` | `:237` is the class's closing `}`; 238-250 do not exist | **1 overrun** |
| `:229-231` | `getRateFactor()` — a complete real method | **wrong member** (flagged) |
| `:233-235` | `getRateFactorTillPeriodDueDate()` — complete real method | **wrong member** (flagged) |
| `:193-201` | `getCreditedAmounts()` 193-195 + `isFirstInterestPeriod()` 197-199 + `getCurrency()` sig 201 | **wrong member — NOT flagged** |
| `:203-219` | `getCurrency()` close 203 + `getCreditedPrincipal()` 205-207 + `getCreditedInterest()` 209-211 + `getDisbursementAmount()` 213-215 + `getBalanceCorrectionAmount()` 217-219 | **wrong member — NOT flagged** |
| `:165-167` | tail of `getLengthTillPeriodDueDate()` | **wrong member — NOT flagged** |
| `:169-171` | head of `updateOutstandingLoanBalance()` | **wrong member — NOT flagged** |
| `:173-175` | body of `updateOutstandingLoanBalance()` | **wrong member — NOT flagged** |
| `:177-179` | body/close of `updateOutstandingLoanBalance()` | **wrong member — NOT flagged** |
| `:181-183` | else-branch of `updateOutstandingLoanBalance()` | **wrong member — NOT flagged** |
| `:48-60` | a **truncated** field block (`fromDate` 49 … `creditedPrincipal` 60) | in-file, wrong extent |
| `:94-109` | both `withEmptyAmounts` 94-106 **+ head of `compareTo()` 108-109** | in-file, overruns into a real wrong member |

**9 citations land wholly inside the file on the wrong member**, plus 2 more in-file with the
wrong extent. The classification closes exactly:

```
22 wrong  =  10 (wholly past EOF)  +  1 (overrun)  +  9 (real-but-wrong-member)  +  2 (in-file, wrong extent)
```

which is an independent cross-check that my census is complete and that T532's 22 is right.

The distinguishing property T532 named — "a citation that still resolves is harder to catch than
one past EOF" — applies identically to all nine: a line-existence check passes on every one of
them. Restricting the count to the two that happen to span a *complete* method is a narrowing
T532 never states, and the effect is that the record now understates the dangerous class by 7.
**All nine were corrected correctly** — no money moves — but the number is now checked in as
verified, which is exactly the laundering the brief warns about. **Condition:** correct "two" to
"nine" in `doc.go` and the file banner.

## MAJOR-3 — The `addBalanceCorrectionAmount` benignity receipt is unsound as written. This is money, and the false step is checked into the source file under `[VERIFIED:]`.

The claim, now in `interestperiod.go`:

> the two-argument form delegates to `Money.plus(that)`, which itself calls `plus(that, getMc())`
> on the RECEIVER's own MathContext `[VERIFIED: Money.java:236-238]`, and the receiver is
> `this.getBalanceCorrectionAmount()`, **built with `getMc()` at `:217-219`**. So no MathContext is lost.

Re-derived from source:

- `InterestPeriod.java:113-115` — `addBalanceCorrectionAmount` calls the **2-arg** `MathUtil.plus`. ✓
- `MathUtil.java:388-390` — `plus(Money,Money)` → `first.plus(second)`. ✓
- `MathUtil.java:392-394` — `plus(Money,Money,MathContext)`, used by the four siblings. ✓
- `Money.java:236-238` — `plus(Money)` → `plus(moneyToAdd, getMc())`, the **receiver's** mc. ✓
- `InterestPeriod.java:217-219` — `getBalanceCorrectionAmount()` returns
  `MathUtil.nullToZero(balanceCorrectionAmount, getCurrency(), getMc())`.

**The last step does not hold.** `MathUtil.nullToZero(Money, MonetaryCurrency, MathContext)` is
at `MathUtil.java:338-340` and is `nullToDefault(value, Money.zero(currency, mc))`; and
`nullToDefault(Money,Money)` at **`MathUtil.java:342-344`** is literally
`return value == null ? def : value;`. So `getMc()` reaches **only the substituted zero**. When
`balanceCorrectionAmount` is non-null the accessor returns the **stored** `Money` carrying
whatever `MathContext` it was constructed with — it is *not* "built with `getMc()`".

And the non-null case is exactly the live call site: `RepaymentPeriod.java:191-193`
(`copyWithoutPaidAmounts`) calls `addBalanceCorrectionAmount` **guarded by
`if (!interestPeriodCopy.getBalanceCorrectionAmount().isZero())`** — i.e. only when the field is
non-null and non-zero. The one path that reaches the asymmetry is the one path the receipt's
reasoning does not cover.

T532's own third asymmetry note describes `nullToZero` correctly ("the oracle reaches zero
*defensively per read*"), so the file contains both the right and the wrong reading of the same
method.

**The conclusion "benign" nevertheless survives**, for two reasons T532 did not give:

1. `MoneyHelper.getMathContext()` (`MoneyHelper.java:91-93`) is **memoised per tenant** in
   `mathContextCache`, and `PRECISION = 19` is a compile-time constant (`:35`). Every `MathContext`
   in this object graph traces back to that one cached instance, so all are the ratified
   `(19, HALF_UP)` — the receiver's cannot differ from the tenant's.
2. Even if they could, precision is irrelevant here: `Money.plus(BigDecimal, MathContext)` at
   **`Money.java:253-259`** performs `this.amount.add(amountToAdd)` with **no MathContext at all**
   (exact `BigDecimal` addition); the `mc` reaches only `setScale(currency.getDecimalPlaces(),
   getMc().getRoundingMode())` in the private constructor at **`Money.java:52`**. Only the
   *rounding mode* could ever move a number, and it is single-valued per tenant.

So the money does not move — but a false statement about money arithmetic is checked in under a
`[VERIFIED:]` banner in a sweep whose entire product is trustworthy annotations. **Condition:**
rewrite the receipt to the mechanism above before merge.

## MINOR-4 — Asymmetry #2's mechanism is also wrong about where the MathContext goes.

The file states, of `updateOutstandingLoanBalance`'s two `negativeToZero` overloads:

> The MathContext only ever reaches the ZERO that is substituted for a negative value, never the
> value that is kept

`MathUtil.java:356-358` is
`negativeToZero(Money value, MathContext mc) { return value == null || isGreaterThanZero(value, mc) ? value : Money.zero(value.getCurrencyData(), mc); }`
— the `mc` also reaches **the predicate**, `isGreaterThanZero(value, mc)` (`MathUtil.java:368-370`
→ `Money.java:446-448`), whereas the 1-arg form at `:351-353` uses the value's own mc
(`Money.java:442-444`). The claim as written is incomplete. The conclusion still holds: the
predicate compares against `Money.zero(currency, mc)`, whose amount is zero under any rounding
mode, so both branches agree. The overload spans themselves (`:173-178` 2-arg, `:183-186` 1-arg)
are **correct** as cited.

## MINOR-5 — `doc.go` says "the sixth surviving citation" is the one without a VERIFIED token. **Two** of the six are.

My census (below) shows the six surviving citations are `go:66` (`:65-66`), `go:70` (`:178`),
`go:81` (`:151`), `go:240` (`:151`), `go:249` (`:178`), `go:373` (`:86-92`) — and **two** of
them, `go:66` and `go:240`, carry no `VERIFIED` token. T532's *handoff* names both correctly in
its gap-2 table; the checked-in `doc.go` prose names only `:151` and calls it "the sixth",
implying a single one. Fix the prose to match the handoff.

Related: the reconstruction of how T530's "23" arose is speculative, not derived. No census
produces 23 — a VERIFIED-grep yields 26 refs of which 22 are wrong (22 of 26); booking *both*
gap items as unresolved yields 24 of 28. Reaching 23 needs exactly one of the two booked, which
is not a census anyone would run. T532's own 22 is right (I confirm it independently); the
*explanation* for 23 should be marked as conjecture rather than stated as settled.

## MINOR-6 — The new file banner undercounts both what was checked and what remains unaudited.

The banner claims:

> only the two that sit in this file's own prose (DateUtils, MathUtil) were checked

but T532 also **added and checked** `[VERIFIED: Money.java:236-238]` — a third file (I verified
it; it is correct). And:

> the RepaymentPeriod / ProgressiveEMICalculator / AdvancedPaymentScheduleTransactionProcessor /
> LoanSchedulePlan spans below remain UNAUDITED

names four families, but the file also cites `ProgressiveLoanScheduleGenerator.java`,
`ProgressiveLoanInterestScheduleModel.java` and `InterestScheduleModelRepositoryWrapperImpl.java`,
which the enumeration omits. The banner's *general* sentence ("citations to files OTHER than
InterestPeriod.java were NOT swept") does cover them, so a careful reader is not misled — but the
enumeration reads as exhaustive and is not. Fix both counts.

**On the boundary call itself (brief item 4): T532 was RIGHT.** Fixing `MathUtil.java:175-178`
was correct and necessary — it was load-bearing for `ratNegativeToZero`, and it was genuinely
wrong (`:175-178` is `nullToZero(BigDecimal)`; `negativeToZero(BigDecimal)` is at `:188-190` —
both verified by me). Refusing to sweep the siblings, declaring it in the file's own banner, and
filing T549 is the correct scope discipline; half-auditing a second file is the defect this task
exists to repair. Subject to MINOR-6, the file will not be misread as swept.

---

# WHAT I CONFIRMED (with what I ran)

## The zero-divergence claim SURVIVES — I checked every changed span myself

The brief's first priority: was any range re-pointed to make a mismatch disappear? **No.** For
each of the 22 corrections I opened the **old** span and the **new** span in the pinned Java and
decided which happened. In every case the old span genuinely failed (past EOF, overrun, or the
wrong member — table in MAJOR-2) and the new span is the exact member the Go sentence above it
describes. **All 30 `InterestPeriod.java` spans in the post-sweep file resolve to the right
member; zero mis-citations remain; zero past EOF.**

The one case where a divergence *could* have been laundered is the cross-file
`ratNegativeToZero` fix, and it is a genuine correction, not a re-aim: the Go body is
`if x.Sign() <= 0 { return new(big.Rat) }; return x`, which is `MathUtil.negativeToZero(BigDecimal)`
at `:188-190` (`isGreaterThanZero(value) ? value : ZERO`, `isGreaterThanZero` at `:196-198`), and
is **not** `nullToZero(BigDecimal)` at `:175-177`. The Go sentence was right and the old span was
wrong — exactly as T532 says.

I also re-read the two substantive Go bodies against their new spans:
`CalculatedDueInterest` against `:134-143` (pause/re-age short-circuit, then
`negativeToZero(add(mc, creditedInterest, interestDueTill))`) and `CalculatedDueInterestFor`
against `:145-158` (zero-length early return, FLAT/DECLINING switch, three separately
mc-rounded operations at `:154-157`). Both supported.

## Counts, re-derived independently

I wrote my own **multi-line-aware** census (reconstructs contiguous `//` blocks, then regexes
`InterestPeriod\.java:(\d+)(-(\d+))?` over the joined text and reports whether each hit sits
inside a `[VERIFIED: … ]` token), run against the merge-base file:

| census | mine | T532 | |
|---|---:|---:|---|
| mechanical (all refs) | **28** | 28 | agree |
| grep (only those inside a VERIFIED token) | **26** | 26 | agree |
| gap | **2** | 2 | agree |
| gap sites | **`interestperiod.go:66`, `:240`** | 66, 240 | **exact** |
| wrong | **22** | 22 | agree |
| already correct | **6** | 6 | agree |

The `22 of 28` correction of the brief's `23 of 28` is **sustained**. All six survivors verified
correct against the Java: `:65-66` = `balanceCorrectionAmount`/`outstandingLoanBalance` (and
indeed no `@JsonExclude` on them — it is at `:45` and `:68`); `:178` ×2 =
`.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc())`; `:151` ×2 =
`case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount()`; `:86-92` = the 2-arg
`copy`.

## EOF split 10 + 1 = 11 — exact

Ten wholly past line 237 (`:252-254 :256-259 :299-301 :303-305 :307-309 :311-313 :315-317
:319-321 :323-325 :327-329`); one more, `:237-250`, starting on the class's closing brace at
`:237` and overrunning. **T532, T539 and T540 agree and I agree with all three. T538's "11 that
overrun" remains wrong** — one overruns, ten are wholly past.

## The "missed five" non-reproduction is a REAL property of this file, not a weak pass

Brief item 3 asked me to judge this. T530's "missed five" mechanism is citations whose atoms
spill onto continuation lines. Such citations **do** exist in `interestperiod.go` — e.g.
`ProgressiveEMICalculator.java:907, :922, … :1124,` continuing to `// :1129]`, and
`InterestScheduleModelRepositoryWrapperImpl.java:95,` continuing to `// :110-128]`. But:

```
$ grep -nE 'InterestPeriod\.java:[0-9]+(-[0-9]+)?[,]' old.go
(no output)
```

**No `InterestPeriod.java` citation carries a continuation atom.** My scanner is multi-line-aware
and would have found them; it returns the same 28/26/2. The gap of 2 here comes from a different
cause (bare prose references without a VERIFIED token), and the "five" is a fact about the file
T530 swept. T532's non-reproduction is correct and correctly explained.

## Byte identity — reproduced exactly, independently

I wrote my own stripper (`go/parser` without `parser.ParseComments`, then `File.Doc`,
`File.Comments` and every `Doc`/`Comment` field on `GenDecl`/`FuncDecl`/`Field`/`ValueSpec`/
`TypeSpec`/`ImportSpec` nil'd via `ast.Inspect`, printed with
`printer.Config{Mode: printer.RawFormat, Tabwidth: 8}`), and ran it over both trees extracted by
`git archive`:

```
$ diff -u base.txt branch.txt
(identical)
```

**14 files, TOTAL 78,499 bytes — matching T532's table exactly, per file**, including
`interestperiod.go` 7042 / `f6ed4fe983c80f6e`, `money.go` 3954 / `25db8297f3dd837d`,
`repaymentperiod.go` 12690 / `abef0f064fcce940`, `doc.go` 20 / `d63e899d42c0f241`
(comment-only file). Corroborated separately:

```
$ git diff -U0 8e1c1a5b..<branch> -- nexus/internal/apps/loanproduct/ | grep -E '^[+-]' \
    | grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]\s*//' | grep -vE '^[+-]\s*$'
(no output — every changed line is a // comment)
```

**0 non-comment Go lines moved.** The driver's measurement confirmed. Nothing was changed that
should have been filed instead.

## Build / test

```
$ gofmt -l nexus/internal/apps/loanproduct/    (clean)
$ go build ./...                               (exit 0)
$ go vet ./internal/apps/loanproduct/          (exit 0)
$ go test ./internal/apps/loanproduct/         ok  0.002s
$ go test ./...                                18 packages ok, 0 FAIL
```

## Scope (brief item 7)

- Files touched: handoff, the `doc.go` citation-audit bullet, `interestperiod.go`. **No poaching.**
- `money.go` (T542) and `repaymentperiod.go` (T547) **untouched** — verified by
  `git diff --name-only` on the merge-base form.
- `doc.go` edit is confined to the one `interestperiod.go` bullet. The **spot-check appositive**
  at `doc.go:54-64` (the `:43-73, :45, :65, :66, :68, :151, :168-188, :178` paragraph, T547's) is
  **byte-untouched**. I independently checked all eight of its ranges against the pinned Java:
  **all eight resolve.**
- T532's note to T547 — that `:43-73` and `:45-73` are different framings of the same block, not
  a defect — is **correct**: `:43` is `public class InterestPeriod implements Comparable<…> {`,
  `:44` is blank, `:45` is `@JsonExclude`. `:43-73` frames class-decl-through-fields; `:45-73`
  frames the field block alone.
- The five bare `[VERIFIED: InterestPeriod.java @Setter]` / uncited setters upgraded to precise
  spans are all correct: `SetDueDate` `:50-52`, `SetPaused`/`IsPaused` `:72-73`, `SetRateFactor`
  `:54-55`, `SetRateFactorTillPeriodDueDate` `:56-57`.
- Money non-negotiables: diff is comment-only and proven byte-identical, so no monetary code
  path, struct field, schema column, API field or fixture changed; no float introduced. No
  cutover, deposit activation or DEC change is implied.
- Field-count note verified: the Java carries **13** fields (`:45-73`), the Go struct 14, because
  `mc` (`:68-70`) splits into `rounding` and `currency` is `getCurrency()` (`:201-203`, which
  reads `getRepaymentPeriod().getCurrency()` live) hoisted to a field. Recorded, not hidden — correct.

---

# CONDITIONS FOR MERGE

1. **MAJOR-1** — correct the three sign errors; remove "the drift changed sign (−94 to +69)" from
   `doc.go`, the file banner and the handoff. Every `InterestPeriod.java` delta is ≤ 0 (0 to −94);
   the only positive is a `MathUtil.java` citation. Restate the no-offset case on
   non-monotonicity and magnitude spread, which is sound.
2. **MAJOR-2** — correct "two … REAL BUT WRONG members" to **nine** in `doc.go` and the file
   banner, and record the closing decomposition `22 = 10 + 1 + 9 + 2`.
3. **MAJOR-3** — rewrite the `addBalanceCorrectionAmount` benignity receipt. `MathUtil.nullToZero`
   (`MathUtil.java:338-344`) returns the stored value unchanged when non-null, so the receiver is
   *not* "built with `getMc()`". Substitute the two correct reasons: the per-tenant memoised
   `MathContext` (`MoneyHelper.java:35, 91-93`) and the fact that `Money.plus(BigDecimal, mc)`
   (`Money.java:253-259`) adds exactly, with `mc` reaching only `setScale`'s rounding mode
   (`Money.java:52`).
4. **MINOR-4/5/6** — fix asymmetry #2's "only reaches the ZERO" wording; fix `doc.go`'s "the
   sixth surviving citation" to name both untokened survivors and mark the "23" reconstruction as
   conjecture; fix the banner's "only the two … (DateUtils, MathUtil)" to three (add `Money.java`)
   and complete the unaudited enumeration.

None of these move a number. All four are wrong statements recorded as verified in a task whose
sole product is trustworthy citations, which is why they are conditions rather than notes.

**The substance of T532 is sound and I recommend it merge once the record is corrected**: the
sweep is real, the corrections are right, the sixth-survivor and 22-of-28 corrections of the
brief are sustained, and the zero-divergence claim holds under independent re-derivation.

---

## Push confirmation

```
$ git push -u origin softhouse/T548-review-t532
 * [new branch]        softhouse/T548-review-t532 -> softhouse/T548-review-t532
branch 'softhouse/T548-review-t532' set up to track 'origin/softhouse/T548-review-t532'.
(PUSH OK on attempt 1 — no retries needed)

$ git ls-remote --heads origin softhouse/T548-review-t532
b6204db71003fe2577349b48e894138b1fefb620	refs/heads/softhouse/T548-review-t532
```

`b6204db71003fe2577349b48e894138b1fefb620` is the review commit. **The branch is confirmed on
the remote.**
