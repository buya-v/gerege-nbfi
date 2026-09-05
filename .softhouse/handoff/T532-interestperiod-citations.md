# T532 — `interestperiod.go` citation sweep

Fire `cloud-20260905-1200`. Branch `softhouse/T532-interestperiod-citations`, based on `main` at `8e1c1a5b`.

## Reference oracle (Fineract) HEAD verified

```
$ git -C /home/user/fineract rev-parse HEAD
426a23544e8426a38ae43ae404670a0a7e85b9eb
```

Matches the pin. Every line number below was read from that checkout.

```
$ wc -l .../portfolio/loanproduct/calc/data/InterestPeriod.java
237
```

`InterestPeriod.java` is **237 lines** — driver's lead confirmed independently.

## The two counts, and the gap

| Census | Count |
|---|---|
| **MECHANICAL** — every `InterestPeriod.java:<spec>` occurrence in the file, regardless of surrounding text | **28** |
| **GREP** — only those on a source line that also contains the token `VERIFIED` | **26** |
| **GAP — citations a VERIFIED-grep misses** | **2** |

The two missed citations are both on comment continuation lines with no `VERIFIED` token:

- `interestperiod.go:66` — `// (no @JsonExclude on InterestPeriod.java:65-66) and ARE read back as`
- `interestperiod.go:240` — `// downstream reach is InterestPeriod.java:151 (the declining-balance interest`

**I could not reproduce the brief's "missed five".** For *this* file the gap is **2**, not 5; the "five" is T530's measurement on the file *it* was sweeping. Both of the two missed here turn out to be **correct citations**, which is the sharper point: a grep-only census both misses them and, if it then books them as unresolved, **overstates the failure count**. That is exactly how the brief's lead of "23 of 28 fail" arises against my measured **22 of 28**.

Method: mechanical spans were derived by **brace counting** `InterestPeriod.java` with block comments, line comments, string literals and char literals stripped *before* any brace was counted (so a `{` inside `"Method not implemented: "` or inside the Apache licence header cannot shift the depth). Script: `spans.py`; citation census: `cites.py`. The derived member table reproduced my independent hand-read of all 237 lines with no discrepancy.

## EOF counts — I agree with T540/T539, exactly

Derived independently, before reading their numbers into my own count:

- **10** citations lie **wholly past** the end of the 237-line file: `:252-254`, `:256-259`, `:299-301`, `:303-305`, `:307-309`, `:311-313`, `:315-317`, `:319-321`, `:323-325`, `:327-329`
- **1** more, `:237-250`, starts on the file's **last** line (the class's closing brace) and **overruns** it
- **= 11 total** citing at least one line that does not exist

**This reproduces T540 and T539 exactly (10 + 1 = 11). I do not disagree.** T538's brief ("11 that overrun") remains wrong: only one overruns; ten are wholly past.

## No offset exists — confirmed, and I did not look for one

I read every range individually. The start-line error, per corrected citation:

| Correction | Δ (old start → new start) |
|---|---|
| accessor block (8 citations) | **−94** |
| `Length`, `LengthTillPeriodDueDate` | **+69** |
| `IsFirstInterestPeriod` | **+55** |
| `CreditedAmounts` | **+63** |
| `CalculatedDueInterest` | −59 |
| `CalculatedDueInterestFor` | −58 |
| `UpdateOutstandingLoanBalance` | −69 |
| five `Add*` mutators | −52 |
| field list | −3 |
| `MathUtil.negativeToZero` | **+13** |
| `withEmptyAmounts` | 0 (start right, end wrong) |

The error **changes sign** and is non-monotonic, spanning −94 to +69. **T526's "12–14 line offset" is false and, as T530 argued, actively harmful** — it would have "explained" the block and left it unread.

Two failures were worse than an EOF overrun and an offset theory hides them completely: **`:229-231` and `:233-235` resolved to REAL BUT WRONG members** (`getRateFactor()` and `getRateFactorTillPeriodDueDate()`) while the Go sentences above them described `getLength()` and `getLengthTillPeriodDueDate()`. A citation that still resolves is harder to catch than one past EOF. Both are now annotated in place so a future reader knows why the span moved.

## Every citation: old span → correct span

`InterestPeriod.java` unless noted. "Supports?" = does the Java at the **correct** span support the Go sentence above it.

| # | Go line (pre-edit) | Subject | Old | Correct | Supports? |
|---|---|---|---|---|---|
| 1 | 29 | struct field list | `:48-60` | **`:45-73`** | yes |
| 2 | 66 | no `@JsonExclude` on the two cells | `:65-66` | `:65-66` **(already right)** | yes |
| 3 | 70 | folds previous `PaidPrincipal` | `:178` | `:178` **(already right)** | yes |
| 4 | 81 | declining-balance interest base | `:151` | `:151` **(already right)** | yes |
| 5 | 102 | `CreditedPrincipal` | `:299-301` | **`:205-207`** | yes |
| 6 | 106 | `CreditedInterest` | `:303-305` | **`:209-211`** | yes |
| 7 | 110 | `DisbursementAmount` | `:307-309` | **`:213-215`** | yes |
| 8 | 114 | `BalanceCorrectionAmount` | `:311-313` | **`:217-219`** | yes |
| 9 | 118 | `OutstandingLoanBalance` | `:315-317` | **`:221-223`** | yes |
| 10 | 122 | `CapitalizedIncomePrincipal` | `:319-321` | **`:225-227`** | yes |
| 11 | 126 | `RateFactorValue` | `:323-325` | **`:229-231`** | yes |
| 12 | 136 | `RateFactorTillPeriodDueDateValue` | `:327-329` | **`:233-235`** | yes |
| 13 | 144 | `Length` | `:229-231` *(wrong member)* | **`:160-162`** | yes |
| 14 | 150 | `LengthTillPeriodDueDate` | `:233-235` *(wrong member)* | **`:164-166`** | yes |
| 15 | 156 | `IsFirstInterestPeriod` | `:252-254` | **`:197-199`** | yes |
| 16 | 163 | `CalculatedDueInterest` | `:193-201` | **`:134-143`** | yes |
| 17 | 179 | `CalculatedDueInterestFor` | `:203-219` | **`:145-158`** | yes |
| 18 | 211 | `ratNegativeToZero` | `MathUtil.java:175-178` *(= `nullToZero`)* | **`MathUtil.java:188-190`** | yes |
| 19 | 221 | `UpdateOutstandingLoanBalance` | `:237-250` | **`:168-188`** | yes |
| 20 | 240 | downstream reach | `:151` | `:151` **(already right)** | yes |
| 21 | 249 | folds `PaidPrincipal` | `:178` | `:178` **(already right)** | yes |
| 22 | 295 | `CreditedAmounts` | `:256-259` | **`:193-195`** | yes |
| 23 | 303 | `AddBalanceCorrectionAmount` | `:165-167` | **`:113-115`** | yes |
| 24 | 331 | `AddDisbursementAmount` | `:169-171` | **`:117-119`** | yes |
| 25 | 337 | `AddCreditedPrincipalAmount` | `:173-175` | **`:121-123`** | yes |
| 26 | 343 | `AddCreditedInterestAmount` | `:177-179` | **`:125-127`** | yes |
| 27 | 349 | `AddCapitalizedIncomePrincipalAmount` | `:181-183` | **`:129-132`** (4 lines, not 3) | yes |
| 28 | 373 | `copy` | `:86-92` | `:86-92` **(already right)** | yes |
| 29 | 397 | `withEmptyAmounts` ×2 | `:94-109` | **`:94-106`** | yes |

**22 of 28 wrong; 6 already correct** (#2, #3, #4, #20, #21, #28). Note #18 is a `MathUtil.java` citation, not an `InterestPeriod.java` one — it sits in my file so I fixed it, and it is counted in neither the 28 nor the 22. Counting it, 23 of 29 spans in this file were wrong.

Citations **upgraded from bare to precise** (previously `[VERIFIED: InterestPeriod.java @Setter]`, no line spec — a citation that cannot be checked):

- `SetDueDate` → `:50-52` (`@Setter` / `@NotNull` / `dueDate`)
- `SetPaused` → `:72-73`
- `IsPaused` → `:72-73` (was uncited)
- `SetRateFactor` → `:54-55` (was uncited)
- `SetRateFactorTillPeriodDueDate` → `:56-57` (was uncited)

**Driver's `:47-52` correction confirmed.** My brace-count independently derives `fromDate` at `:47-49` and `dueDate` at `:50-52`; `:45` is `@JsonExclude` and `:46` is `private final RepaymentPeriod repaymentPeriod;`. And per the no-offset rule I did **not** assume that off-by-two generalises — it does not appear anywhere else in this file.

Post-edit census: **33** citations (28 + 5 newly precise/added), **all 33 land inside the file**, 0 past EOF, and each was cross-checked line-by-line against the brace-counted member table.

## DIVERGENCES: none — 0

At **every** corrected span the Java supports the Go sentence above it. **No range was repointed to make a mismatch disappear**, and no divergence was converted into a quiet correction — there was no divergence to convert. Reporting zero here is the finding, not an omission: this block was mis-*cited*, not mis-*ported*. The Go sentences were written by someone who had read the right code and recorded the wrong coordinates.

Three **oracle asymmetries** were found, checked, and are **benign**. They are recorded at their sites in the code rather than smoothed over, because each is a real difference in the oracle's source that a reader would otherwise rediscover:

1. **`addBalanceCorrectionAmount` alone calls the 2-arg `MathUtil.plus(Money, Money)`** (`MathUtil.java:388-390`); its four siblings pass `getMc()` to the 3-arg overload (`:392-394`). Benign, and *not* by luck: the 2-arg form delegates to `Money.plus(that)`, which calls `plus(that, getMc())` on the **receiver's own** MathContext (`Money.java:236-238`), and the receiver is `this.getBalanceCorrectionAmount()`, built with `getMc()` at `:217-219`. No MathContext is lost.
2. **`updateOutstandingLoanBalance` floors its two branches with different overloads** — `negativeToZero(Money, mc)` at `:173-178`, `negativeToZero(Money)` at `:183-186`. Benign: the MathContext only ever reaches the substituted ZERO, never the kept value.
3. **The Go accessors do not replicate `MathUtil.nullToZero`.** The oracle reaches zero defensively per read; this port reaches it by construction (both constructors seed all six `Money` cells with `moneyZero`, and the fields are unexported so no third construction path exists). Same observable, different mechanism — now stated in the code.

**One port decision worth a reviewer's eye, recorded not hidden:** the Go struct carries 14 fields to the oracle's 13, because the oracle's single `mc` (`:68-70`) becomes `rounding`, and `currency` is the oracle's `getCurrency()` (`:201-203`, which reads `getRepaymentPeriod().getCurrency()` **live**) hoisted to a stored field. That hoist is behaviour-preserving only while a model's currency is fixed after construction — which it is on every path in this package. Filed, not treated as a defect.

## Behaviour unmoved — byte-identity proof

Both trees rendered through `go/parser` + `go/printer` with **all** comment material discarded: parsed *without* `parser.ParseComments` (so no `CommentGroup` is ever attached), then `File.Doc`, `File.Comments` and every `Doc`/`Comment` field on `GenDecl`, `FuncDecl`, `Field`, `ValueSpec`, `TypeSpec` and `ImportSpec` nil'd via `ast.Inspect`, then printed with `printer.Config{Mode: printer.RawFormat, Tabwidth: 8}`. Tool: `scratchpad/stripper/main.go` (stdlib only).

```
$ git merge-base HEAD main
8e1c1a5b0a7a9e3171d458545874ca3a5eec5434
$ go run . <baseline>   # package as of merge-base
$ go run . /home/user/wt/T532/nexus/internal/apps/loanproduct
$ diff -u base.txt branch.txt
BYTE-IDENTITY PROOF: PASS — comment-free renderings are identical
```

Per-file, **both sides**:

| file | bytes | sha256[:16] |
|---|---|---|
| calculator.go | 12782 | `665317b475b19206e6f3e170bcec4553` |
| calculator_test.go | 8015 | `9c874d14de9a8c92a17abba9bea8c137` |
| dates.go | 2664 | `29719c1bc18b23a847015cc30f9a2500` |
| doc.go | 20 | `d63e899d42c0f241661f173650010bbb` |
| frequency.go | 5175 | `aa8c26304726cfda7a2392a8925970bc` |
| **interestperiod.go** | **7042** | `f6ed4fe983c80f6ef2800929d22df489` |
| interestperiod_test.go | 2698 | `ea6ee116c67c49fdb3f2e36dbcc25b28` |
| interestrate.go | 242 | `27b23b972437eed6ea9d47a731211bb2` |
| method.go | 5518 | `81ae4a6a5559a28809336058e638bd37` |
| method_test.go | 4576 | `2b6eb64000a50f71efa8705574cf6ffc` |
| money.go | 3954 | `25db8297f3dd837d71da0b41bef61755` |
| relateddetail.go | 1733 | `07a739515d417900b112eda45f179763` |
| repaymentperiod.go | 12690 | `abef0f064fcce94009e6b1d24107a74d` |
| schedulemodel.go | 11390 | `364faec750348c164232c4bc742dc98b` |
| **TOTAL** | **78499** | 14 files |

`doc.go` renders to 20 bytes both sides because it is comment-only (`package loanproduct`) — the expected result, and it is why the diff to `doc.go` cannot move behaviour.

Independent corroboration — every changed line in the diff is a `//` comment:

```
$ git diff -U0 -- nexus/internal/apps/loanproduct/ | grep -E '^[+-]' \
    | grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]\s*//' | grep -vE '^[+-]\s*$'
(none — every changed line is a // comment)
```

No executable line changed, so nothing needed to be stopped-and-filed on that account.

## Verification

```
$ gofmt -l nexus/internal/apps/loanproduct/
(empty — clean)

$ cd nexus && go build ./...
(exit 0)

$ go vet ./internal/apps/loanproduct/
(exit 0)

$ go test ./internal/apps/loanproduct/
ok   github.com/gerege/nexus/internal/apps/loanproduct   0.003s

$ go test ./...
all packages ok (incl. ledger/conformance 1.931s, loanschedule/conformance 10.182s)
```

Money non-negotiables: the diff is comment-only, so no monetary code path, struct field, schema column, API field or fixture changed; no float was introduced.

## `doc.go` — the minimal edit, declared

I edited **one bullet** of `doc.go`'s citation-audit banner: the `interestperiod.go` entry that said `UNSWEPT … T530 measured 23 of 28 failing to resolve` and named T532 as owner. It now reads SWEPT, carries my measured **22 of 28** with the reason it differs from 23, keeps the 10 + 1 = 11 EOF split verbatim, and records the sign-change and the two real-but-wrong-member cases.

**I did not touch** the spot-check appositive at `doc.go:50-60` (the `:43-73, :45, :65, :66, :68, :151, :168-188, :178` paragraph) — that belongs to **T547**. Noted for T547: those eight ranges all resolve against my table, and `:43-73` is a legitimately different framing from my `:45-73` (`:43` is the `class` declaration line, `:44` blank), so it is not a defect — but T547 should decide whether the two spellings should be reconciled.

## Ownership respected

- Touched only `nexus/internal/apps/loanproduct/interestperiod.go`, the one `doc.go` bullet, and this handoff.
- **`money.go` — NOT touched** (T542). Confirming its lead in passing: `money.go:133` cites `InterestPeriod.java:215` for `baseAmount.multiply(rateFactorTillPeriodDueDate, mc)`; the real expression is at **`:155`**, and `:215` is the closing brace of `getDisbursementAmount()`. **T540's finding is correct.** I read the file but changed nothing.
- **`repaymentperiod.go` — NOT touched** (T547).
- Nothing under `nexus/internal/apps/savings/`, `conformance.sh`, `.softhouse/guards/ledgerguard/`, `.softhouse/tasks.json`, `LOCK`, `RESUME.md`, `program.json`.

## What I could NOT do

1. **Could not reproduce "missed five".** For this file the mechanical-vs-grep gap is **2**. I looked at every line of `interestperiod.go` matching `InterestPeriod\.java:` with a regex that also accepts comma-continuation lists and `:NNN` continuation atoms; I found no citation whose atoms spill onto a following line. The "five" is a statement about the file T530 swept, not this one.
2. **Did not sweep the other-file citations in `interestperiod.go`** — `RepaymentPeriod.java:389-403`, `:405-407`, `:173-198`, `:192-194`; `ProgressiveEMICalculator.java:907, :922, :946, :952, :1124, :1129, :421, :1254-1256, :1647, :1654, :1667`; `AdvancedPaymentScheduleTransactionProcessor.java:929, :967, :2912`; `ProgressiveLoanScheduleGenerator.java:132`; `LoanSchedulePlan.java:65, :77`; `ProgressiveLoanInterestScheduleModel.java:257, :290`; `InterestScheduleModelRepositoryWrapperImpl.java:95, :110-128`. **These remain UNAUDITED and I say so in the file's own audit banner.** Half-auditing a second file is the precise defect this task exists to repair, and `RepaymentPeriod.java` spans are T547's. I checked only the two that sit in this file's own prose (`DateUtils`, `MathUtil`) because one of them, `MathUtil.java:175-178`, was load-bearing for `ratNegativeToZero` — and it was wrong. **That is a live signal that the other-file spans in this file are also suspect; they should be given a task.**
3. **No golden-vector / conformance run against a live oracle instance** beyond the checked-in suites above. The diff is comment-only and proven byte-identical, so parity cannot have moved; no cutover, activation or DEC change is implied by this task.
