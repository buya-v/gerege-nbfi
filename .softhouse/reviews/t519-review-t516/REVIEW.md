# T519 — independent review of T516

**Target:** branch `softhouse/T516-t514-conditions`, commit `709e51c3`.
**Stack:** `709e51c3` (T516) on `fc35f4eb` (T511) on `0b5e8b81` (T502) on merge-base `14cf6c1f`.
**Reviewer branch:** `softhouse/T519-review-t516`. Reviewer wrote only this file.
**Oracle:** Fineract at `/Users/buv/fineract` @ `426a23544` (`git log -1` confirms the pin).

**VERDICT: APPROVED.** Two MINOR findings (wording/nomenclature, non-blocking, no number and no
money logic touched by either). Two OBSERVATIONS attributed away from T516. Nothing blocking.

Everything below is per-commit. Where a defect belongs to `0b5e8b81` or to the pre-existing tree it
is said so explicitly — the false-accusation failure mode T512 was filed to stop is the one this
review was most careful to avoid.

**Note on the scope tool.** `.softhouse/bin/scope-check.sh` is NOT present at `main` in this
worktree, and its independent review (T517) rejected it for a trailing-slash matcher defect that
would have mis-scored T516's own `files_hint`. It was never run here. Scope was measured with
`git show --stat 709e51c3` and `git diff --stat 14cf6c1f..709e51c3` only.

---

## 0. What was checked, so silence is distinguishable from not looking

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Retirement-argument citations | opened every `file:line` in the pinned checkout | all correct |
| 2 | Is a principled backward stopping rule available? | constructed and tested three candidates | none survives; retirement justified |
| 3 | Was a falsifiable **test** removed? | `grep '^func Test'` on both trees + `go test -v` | no — 2 test funcs before, 2 after, 19 tests pass |
| 4 | LEG 2 adversarial: any read outside `loanproduct.calc`? | full-tree grep + hand-walk of all 6 `getSavedModel` consumers + the model→installment mapping | LEG 2 survives; one ambiguous clause (MINOR-1) |
| 5 | Is LEG 2 the column argument renamed? | compared claim shapes against T505's counterexample | no — different claim, independently verified |
| 6 | Falsification probe | re-applied the derive-on-read patch myself, ran the suite | reproduced 70000 vs 90000 exactly |
| 7 | Probe residue | AST-level identity proof + `git grep` over the whole commit tree | none |
| 8 | Zero executable change, per commit | go/parser + go/printer with all comment nodes nulled | byte-identical, all four files |
| 9 | Range-vs-commit difference | strip-diff at each stack level | fully explained by `0b5e8b81` |
| 10 | The citation correction | opened `:266`, `:267`, `:281`, `:282` on both Go trees and `InterestPeriod.java:178` | T516 is right, T514 was wrong |
| 11 | Guard census (7, not 4) | re-ran `ledgerguard --root` against the extracted T516 tree | exact line-for-line match |
| 12 | BAR | `go build`, `go vet ./...`, `gofmt -l`, `go test ./...` | green |
| 13 | Money non-negotiables | no float, no rename, no arithmetic, integer minor units | clean |

---

## 1. THE RETIREMENT ARGUMENT — RE-DERIVED, AND IT HOLDS

### 1.1 Every citation opened

| claim | citation | verdict |
|---|---|---|
| `principal_outstanding_derived` is a persisted column | `LoanSummary.java:62` = `@Column(name = "principal_outstanding_derived", scale = 6, precision = 19)`, `:63` = `private BigDecimal totalPrincipalOutstanding;` | [VERIFIED — exact] |
| it is derived from `calculateTotalPrincipalRepaid` | `LoanSummary.java:203` = `this.totalPrincipalOutstanding = principal.plus(capitalizedIncome).plus(this.totalPrincipalAdjustments)`, `:204` = `.minus(this.totalPrincipalRepaid).minus(this.totalPrincipalWrittenOff).getAmount();` | [VERIFIED — exact] |
| which folds **schedule installments**, not postings | `LoanSummary.java:339-346` — the loop body is `for (final LoanRepaymentScheduleInstallment installment : repaymentScheduleInstallments) { total = total.plus(installment.getPrincipalCompleted(currency)); }` | [VERIFIED — exact] |
| the column really is persisted | `LoanSummary.java:36` = `@Embeddable`, embedded into `m_loan`; the column is also selected by name in the tenant report changelogs (`0125_…xml:691`, `0150_…xml:156`) | [VERIFIED] |
| the transitive reading condemns it correctly | `LoanRepaymentScheduleInstallment.java:72-73` = `@Column(name = "principal_completed_derived")` / `private BigDecimal principalCompleted;`; written by `payPrincipalComponent` at `:672`, whose body calls `setPrincipalCompleted(...)` from a transaction amount | [VERIFIED — exact] |
| …and condemns the four sites too | `InterestPeriod.java:178` = `.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc())`; `RepaymentPeriod.java:405-407` = `addPaidPrincipalAmount`; `ProgressiveEMICalculator.java:421` = `repaymentPeriod.ifPresent(rp -> rp.addPaidPrincipalAmount(finalPrincipalAmount));`; `AdvancedPaymentScheduleTransactionProcessor.java:929, :967` = `emiCalculator.payPrincipal(model, currentInstallment.getFromDate(), …)`, `:2912` = `emiCalculator.payPrincipal(model, installment.getFromDate(), …, paidPortion)` with `paidPortion` from `processPaymentAllocation(…, loanTransaction, …)` at `:2908` | [VERIFIED — all seven lines opened] |

Also re-verified, because they carry the same argument elsewhere in the package:
`ProgressiveEMICalculator.java:907, :922, :946, :952, :1124, :1129` are all `addBalanceCorrectionAmount(… .negated())`; `:922` is `effectivePaidPrincipal.negated()` and `:952` is
`paidPrincipal.negated()` — so "a negated paid principal at 2 of its 6 sites" is exact, not
rounded. [VERIFIED]

`InterestPeriod.java:43-73` counted field by field: `:45` and `:68` are the only `@JsonExclude`
(on `repaymentPeriod` and `mc`); `:65` is `private Money balanceCorrectionAmount;` and `:66` is
`private Money outstandingLoanBalance;`, both unannotated. `JsonExcludeAnnotationBasedExclusionStrategy.java:31-34` (in `.../serialization/gson/`) skips
only annotated fields. `InterestScheduleModelRepositoryWrapperImpl.java:95` is `extractModel`,
`:110-128` is `getSavedModel`, and `:122` is `recalculateInterestForDate(businessDate, ctx)` on the
**loaded** model. `ProgressiveLoanModel.java:34-55` carries exactly `loan_id`, `json_model` (text),
`business_date`, `last_modified_on_utc`, `json_model_version`. All [VERIFIED].

### 1.2 Is there a principled stopping rule that would rescue the posting-stream test?

I tried to build one. Three candidates, all fail:

1. **"Stop at the first persisted artifact upstream."** Fails to separate. For
   `principal_outstanding_derived` the upstream chain is `principal_completed_derived` (persisted) ←
   `LoanTransaction` (persisted). For `outstandingLoanBalance` it is `paidPrincipal` (persisted
   inside `json_model`) ← `LoanTransaction`. Both terminate at a persisted transaction.
2. **"Stop at the first JPA-annotated type."** This *does* separate — `InterestPeriod` carries no
   `@Entity`/`@Table`/`@Column` [VERIFIED: `InterestPeriod.java:43-73`], `LoanSummary` is
   `@Embeddable`. But it separates them **by persistence annotation**, which is exactly RETIRED 1,
   the column argument T505 already defeated on `json_model`. Bolting it on does not rescue the
   posting-stream test as a distinct criterion; it collapses it into the other dead one.
3. **"Count aggregate hops."** Not defined in Fineract at all, and the calc object graph is a
   single non-entity graph, so the hop count is not a property of the code.

I could not construct a fourth. **The retirement is justified.** T516's stated reason — that
neither reading is well-defined at the boundary and rewording the premise cannot supply a stopping
rule — reproduces under independent attempt. [VERIFIED by construction; a negative existence claim,
so recorded as reasoning rather than as a source citation.]

### 1.3 IMPORTANT — no falsifiable test was removed

The brief warned that "removing a falsifiable test is a serious act". It did not happen, and this
should be stated plainly so the record is not misread later:

- `grep '^func Test'` on `fc35f4eb`'s `interestperiod_test.go` returns
  `TestOutstandingLoanBalanceIsASweptSnapshot`, `TestBalanceCorrectionAmountIsASignedDelta`.
  The same two, on `709e51c3`. [VERIFIED]
- `go test -v ./internal/apps/loanproduct/` on the extracted T516 tree: **19 `--- PASS`, 0 FAIL.**
  [VERIFIED — measured]
- What T516 retired is a **prose criterion** in a doc comment. It was never executable, and
  nothing executable was deleted. The executable test was *strengthened* — its doc comment now
  names both dead arguments with their counterexamples inline.

This is MINOR-2 below: calling a prose criterion "the test" inside a package that also holds a Go
test about the same cell is a nomenclature hazard, and it already mis-set the review brief.

---

## 2. LEG 2 — IS IT THE COLUMN ARGUMENT RENAMED? NO, AND I TRIED HARD TO MAKE IT ONE

The instruction was: find any read of those cells from outside `loanproduct/calc`; if one exists,
LEG 2 falls. I found reads outside `loanproduct.calc`, and LEG 2 still stands — because the reads
are not of the thing the closed-loop claim is about, and because none of them reaches a balance.
Here is the full walk.

### 2.1 Every non-test read of the two accessors in the oracle

`grep -rn 'getOutstandingLoanBalance()\|getBalanceCorrectionAmount()' --include='*.java'`, excluding
`/src/test/` and `/build/`, by file [VERIFIED — measured]:

| file | hits | package | status |
|---|---|---|---|
| `loanproduct/calc/data/InterestPeriod.java` | 12 | `loanproduct.calc.data` | inside |
| `loanproduct/calc/ProgressiveEMICalculator.java` | 10 | `loanproduct.calc` | inside |
| `loanproduct/calc/data/RepaymentPeriod.java` | 6 | `loanproduct.calc.data` | inside |
| `loanaccount/loanschedule/data/LoanSchedulePlan.java` | 2 | `loanaccount.loanschedule.data` | **outside** |
| `…embeddable-schedule-generator/misc/Main.java` | 2 | demo printer | outside, non-production |
| `loanaccount/loanschedule/domain/ProgressiveLoanScheduleGenerator.java` | 1 | `loanaccount.loanschedule.domain` | **outside** |
| `LoanProductTrancheDetailsUpdateUtil`, `LoanChargeWritePlatformServiceImpl`, `ClientCollateralManagementReadServiceImpl`, `SmsCampaignDomainServiceImpl`, `LoanProduct.java`, `LoanAccountData.java` | 1 each | various | different receivers — `LoanTransaction.getOutstandingLoanBalance()` and `LoanProduct`'s tranche cap, not these cells |

So two production reads sit outside `loanproduct.calc`, and doc.go's own evidence item 1 already
cites both.

### 2.2 Do they reach a balance? Independently walked. No.

- `ProgressiveLoanScheduleGenerator.java:132` = `repaymentPeriod.setOutstandingLoanBalance(interestRepaymentPeriod.getOutstandingLoanBalance());`
  — the receiver is a `calc.data.RepaymentPeriod`, the target is `LoanScheduleModelRepaymentPeriod`,
  which carries **zero** `@Entity`/`@Table`/`@Column` [VERIFIED: measured 0].
- `LoanSchedulePlan.java:65` and `:77` read it back off those DTOs into `LoanSchedulePlanDownPaymentPeriod` /
  `LoanSchedulePlanRepaymentPeriod`. `LoanSchedulePlan.java` carries **zero** JPA annotations
  [VERIFIED: measured 0].
- **The model→installment mapping drops the cell.** `LoanScheduleComponent.java:45-51` builds each
  `LoanRepaymentScheduleInstallment` from `periodNumber, periodFromDate, periodDueDate, principalDue,
  interestDue, feeChargesDue, penaltyChargesDue, isRecalculatedInterestComponent, compounding
  details, rescheduleInterestPortion, isDownPaymentPeriod` — `outstandingLoanBalance` is not among
  them. [VERIFIED — opened]
- **And there is no column for it to land in anyway.** `LoanRepaymentScheduleInstallment.java`
  declares exactly **34** `@Column`s; I listed all 34 by name and **none** contains `balance` or
  `outstanding`. [VERIFIED — measured, `grep -c` = 34 and the name-filtered grep returns empty]
- **`calc` emits no accounting.** Over the 20 `.java` files under
  `fineract-progressive-loan/.../loanproduct/calc/`: `JournalEntry` = **0** hits,
  `@Entity|@Table|@Column` = **0** hits. [VERIFIED — measured]
- **The real same-named ledger cell is a separate accumulator.**
  `LoanBalanceService.java:174, :194, :203` are all
  `loanTransaction.updateOutstandingLoanBalance(MathUtil.negativeToZero(outstanding.getAmount()))`,
  folded over the loan's transactions; that file contains no read of the calc cell. [VERIFIED]

### 2.3 The `json_model` closed loop — tested against every consumer

`getSavedModel` has exactly six production call sites [VERIFIED — full-tree grep]:

| consumer | package | what it does with the loaded model |
|---|---|---|
| `ProgressiveLoanScheduleGenerator.java:200` | `loanaccount.loanschedule.domain` | `emiCalculator.getOutstandingAmountsTillDate(model, …)` only |
| `ProgressiveLoanScheduleGenerator.java:252` | same | same shape; the file's only `getOutstandingLoanBalance()` read is `:132`, which is on a *different* model |
| `ProgressiveLoanSummaryDataProvider.java:94` | `loanaccount.service` (provider) | `getOutstandingAmountsTillDate`, takes `getOutstandingInterest()` |
| `LoanTransactionProcessingServiceImpl.java:206` | provider | hands the model back into `calc` |
| `ReprocessLoanTransactionsServiceImpl.java:95, :127` | provider | hands the model back into `calc` |

And `getOutstandingAmountsTillDate` does **not** read the cell:
`ProgressiveEMICalculator.java:628-632` computes `totalOutstandingPrincipal` from
`scheduleModelCopy.getTotalDuePrincipal().minus(scheduleModelCopy.getTotalPaidPrincipal())` and the
interest likewise. [VERIFIED — opened]

Decisively: **the model `ProgressiveLoanScheduleGenerator` reads the cell from at `:132` is freshly
built, not reloaded.** `:108` = `emiCalculator.generatePeriodInterestScheduleModel(expectedRepaymentPeriods, …)`, on the path that
reaches `:132`. The `getSavedModel` calls at `:200`/`:252` are in different methods. [VERIFIED]

**Conclusion.** LEG 2 is not RETIRED 1 wearing a new name. RETIRED 1 claimed *never stored* and was
killed by `json_model`. LEG 2 concedes storage and claims *never reaches an aggregate that reads it
as an account balance* — a different claim, and one I verified independently along every path I
could find: DTO terminals with no JPA surface, a model→installment mapping that drops the cell, a
schedule table with no balance column, a `calc` package with no journal entry, and a same-named
ledger cell fed by a separate accumulator. **LEG 2 survives.**

### MINOR-1 (wording, non-blocking) — the closed-loop clause has an unpinned antecedent

`doc.go` (T516's text) reads:

> It claims their persistence is a CLOSED LOOP — json_model is written by the projection and read
> back as the same projection's starting state, and nothing outside loanproduct.calc reads a balance
> out of it.

"it" is ambiguous, and the two readings do not have the same truth value:

- **"out of `json_model`"** — **TRUE**, and I verified it exhaustively in §2.3: all six
  `getSavedModel` consumers either re-enter `calc` or read only `OutstandingDetails`, which is
  computed from due/paid principal and not from `outstandingLoanBalance`.
- **"out of the cells"** — **FALSE**, and refuted by doc.go's *own* evidence item 1 six paragraphs
  above: `ProgressiveLoanScheduleGenerator.java:132` is package
  `org.apache.fineract.portfolio.loanaccount.loanschedule.domain`, which is outside
  `loanproduct.calc`, and it reads `getOutstandingLoanBalance()`.

Mitigating, and why this is MINOR rather than a repeat of the MAJOR-1 genre: the **very next
sentence** supplies the correct formulation — *"'never reaches an aggregate that reads it as an
account balance' is what item 1's trace establishes."* So the document self-corrects immediately,
and the load-bearing claim is the correct one. The exposure is that the loose clause is quotable on
its own, in a package whose whole recent history is arguments quoted out of the evidence that
refutes them.

**Recommended (not required):** pin the antecedent — "…nothing outside `loanproduct.calc` reads a
balance out of **the reloaded model**". Comment-only; no number, no money logic. Deliberately not
applied here: this reviewer's write scope is this file alone.

---

## 3. THE FOUR SITES ARE STILL RED, AND THE TEST IS STILL FALSIFIABLE — RE-RUN, NOT ACCEPTED

The transcript was not taken on trust. Method: `git archive 709e51c3 nexus` into a clean temp tree,
symlinked `.softhouse` for the capture fixtures the conformance tests require, and ran everything
there.

**Probe, applied by me.** Patched `OutstandingLoanBalance()` to
`if ip.repaymentPeriod != nil { ip.UpdateOutstandingLoanBalance() }` before the return — the
derive-on-read shape the guard prescribes:

```
--- FAIL: TestOutstandingLoanBalanceIsASweptSnapshot (0.00s)
    interestperiod_test.go:74: the cell is a SWEPT SNAPSHOT, not an on-demand derivation:
    reading it after a summand changed but before a sweep gave 70000 minor units,
    want the unchanged 90000.
```

**70000 vs 90000, reproduced exactly.** [VERIFIED — executed]

I also checked something the handoff did not claim: under the probe, that test is the **only**
failure in the package (19 pass → 1 fail, 18 pass). It is a specific sentinel, not a test that
happens to trip on any perturbation. [VERIFIED — measured]

The arithmetic checks out independently against the oracle formula
(`InterestPeriod.java:173-178`): `0 + 100000 disbursed + 0 + 0 − 10000 due principal + 0 paid =
90000`; after the `−20000` correction, `0 + 100000 − 20000 − 10000 = 70000`. All integer minor
units.

Probe reverted by re-extracting from `709e51c3`; `go test ./internal/apps/loanproduct/` → `ok`.

**Guard, re-run by me** (`ledgerguard --root <extracted T516 tree>`):

```
[I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:277:4
[I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:288:2
[I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:327:2
[I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:562:4
[I3-FIELD-WRITE] internal/apps/savings/postgres.go:243:7
[I3-FIELD-WRITE] internal/apps/savings/postgres.go:302:5
[I3-FIELD-WRITE] internal/apps/savings/summary.go:53:2
```

**Seven findings, line for line identical to the handoff's transcript.** The four loanproduct sites
are still RED. Census header: `inspected 211 Go files / 20 packages / 1767 funcs`. [VERIFIED —
executed]

**Probe residue: none.** `git grep -i 'FALSIFICATION PROBE' 709e51c3` returns exactly two hits, both
prose in `.softhouse/handoff/T516-t514-conditions.md` (`:227`, `:236`). No Go file matches. This is
not merely a grep result — §4's AST identity proof makes residue in the four touched Go files
*impossible*, and `709e51c3` touches no other Go file. The T347-on-T336 failure mode is absent.
[VERIFIED]

---

## 4. ZERO EXECUTABLE CHANGE — PROVED PER COMMIT, AT AST LEVEL

A line filter that drops `//`-leading lines is not a proof (a line can carry code *and* a comment).
So I proved it structurally: for each of the four files at `fc35f4eb` and at `709e51c3`, parsed with
`go/parser` (comments not retained), nulled `File.Comments` and every `Doc`/`Comment` node on
`FuncDecl`/`GenDecl`/`Field`/`ValueSpec`/`TypeSpec`/`File`, and reprinted with `go/printer`.

| file | `fc35f4eb` vs `709e51c3`, comments stripped |
|---|---|
| `doc.go` | **byte-identical** |
| `interestperiod.go` | **byte-identical** |
| `interestperiod_test.go` | **byte-identical** |
| `repaymentperiod.go` | **byte-identical** |

[VERIFIED — measured]. The claim is stronger than "zero non-comment lines changed": the two trees
are the *same program*.

**The range difference is fully explained by the stack, and none of it is T516's.** Same method
applied at `14cf6c1f` → `0b5e8b81` → `709e51c3`:

- `interestperiod.go`: the only structural delta over the whole range is a gofmt realignment of the
  `creditedPrincipal` / `creditedInterest` / `disbursementAmount` field block plus one blank line —
  and the `14cf6c1f`→`0b5e8b81` strip-diff is **exactly that same delta**, while
  `0b5e8b81`→`709e51c3` is empty. It is T502's, caused by T502 inserting a comment into the struct.
  [VERIFIED]
- `repaymentperiod.go`: strip-identical across the entire range. [VERIFIED]
- `interestperiod_test.go`: `git cat-file -e 14cf6c1f:…interestperiod_test.go` **fails** — the file
  does not exist at the merge base. The "whole test function" in the range diff was created by
  `0b5e8b81` (T502). [VERIFIED]

Nothing was slipped in.

**Scope.** `git show --stat 709e51c3` = `doc.go`, `interestperiod.go`, `interestperiod_test.go`,
`repaymentperiod.go` (all under `nexus/internal/apps/loanproduct/`) + `.softhouse/handoff/T516-t514-conditions.md`. Nothing under `.softhouse/guards/**`,
`nexus/internal/apps/savings/**` or `nexus/internal/apps/ledger/**`. Within permit. [VERIFIED]

---

## 5. THE CITATION CORRECTION — T516 IS RIGHT, T514 WAS WRONG

The oracle line first: `InterestPeriod.java:178` =
`.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc()), getMc());//` [VERIFIED — opened].

The Go fold, by `grep -n` on each tree [VERIFIED — measured]:

| tree | `minus(previous.DuePrincipal())` | `plus(previous.PaidPrincipal())` |
|---|---|---|
| `fc35f4eb` (T511) | **266** | **267** |
| `709e51c3` (T516) | **281** | **282** |

T514 cited `interestperiod.go:266` for the fold. On T511's own tree `:266` is the `minus(DuePrincipal)`
line; the fold is `:267`. **T516's correction is exact on both trees**, and its decision to cite the
*expression* rather than the line — with the line flagged drift-prone — is the right call for a
package whose line numbers move every time a comment is edited. A wrong correction would have been
worse than the original error; this one is right.

---

## 6. THE GUARD CENSUS CORRECTION — VERIFIED, INCLUDING THE ACCUSATION AGAINST T511

T516 accuses T511 of two wrong numbers. Both accusations check out, and I confirmed them from the
branch rather than from T516's summary:

- `git show fc35f4eb:.softhouse/handoff/T511-t505-conditions.md` prints a **seven-line**
  `I3-FIELD-WRITE` transcript at `:145-151`, and its prose at `:217` reads *"6 balance-in-substance
  assignments exist in the tree; the guard reports 4."* The prose contradicts the transcript eleven
  lines above it. [VERIFIED — both opened]
- Re-running T511's own census greps on the T516 tree [VERIFIED — measured]: its pattern returns
  **4**; T516's widened pattern returns **6**, recovering `savings/summary.go:53`
  (`s.AccountBalance += effect`, a compound assignment the original pattern cannot match); the
  `outstandingMinor` grep returns **2** (`loanschedule/emi.go:1720, :1726`, both
  `s.outstandingMinor = maxInt64(0, …)`); the guard returns **7**. The floor `7 + 2 = 9` is
  arithmetically right, and `savings/postgres.go:243` / `:302` are indeed the `, err =` multi-value
  forms neither pattern can reach.

T516 correcting T511's numbers *in its own handoff*, rather than editing a merged historical record,
is the right disposition and is disclosed in its follow-ups.

---

## 7. BAR

Run against the extracted `709e51c3` tree (with `.softhouse` on the search path so the capture-graded
tests actually grade rather than skip):

| check | result |
|---|---|
| `go build ./...` | **PASS** (exit 0) |
| `go vet ./...` | **PASS** (no output) |
| `go test -count=1 ./...` | **PASS** — 18 packages `ok`, zero failures |
| `go test -v ./internal/apps/loanproduct/` | **19 PASS, 0 FAIL** |
| `gofmt -l ./internal/apps/loanproduct/` | **clean** |
| `gofmt -l .` (whole module) | 4 files listed — **all pre-existing**, see OBS-3 |
| `ledgerguard` | fails as designed; the four sites RED |

**Money non-negotiables.** No executable line changed, so no float could be introduced; verified
anyway that the test constants (`90000`, `70000`, `-20000`, `100000`, `10000`, `-25000`, `-5000`) are
integer minor units and no `float`/`float64` appears in the package. No field or accessor renamed —
`OutstandingLoanBalance()` / `BalanceCorrectionAmount()` still mirror the oracle method names, which
is what keeps every `[VERIFIED:]` citation auditable. No arithmetic changed. Ledger append-only,
holds, `Idempotency-Key`, MNT, timezone and Postgres rules are all untouched by this diff.

---

## FINDINGS

### MINOR-1 — the closed-loop clause has an unpinned antecedent, and one reading is refuted by doc.go's own item 1
**Severity: MINOR. Non-blocking. Attributed to `709e51c3` (T516).**
Detail and the verified truth values in §2, "MINOR-1" (after §2.3). On the `json_model` reading it is true; on the "the
cells" reading `ProgressiveLoanScheduleGenerator.java:132` (package `loanaccount.loanschedule.domain`)
refutes it, and doc.go cites that very line as evidence. The next sentence supplies the correct
formulation, and the substantive leg verified clean along every path I walked, which is why this is
MINOR and not blocking. Suggested wording: "…reads a balance out of **the reloaded model**."

### MINOR-2 — "the posting-stream test" names a prose criterion, in a package that also holds a Go test about the same cell
**Severity: MINOR. Non-blocking. Attributed to `709e51c3` (T516), inherited from `fc35f4eb`.**
Nothing executable was retired — both test functions survive and 19 tests pass (§1.3). But the word
"test" is doing two jobs in one package, and the cost is already measurable: the brief for this very
review was written warning that "removing a falsifiable test is a serious act", which is not what
happened. Suggested: call it the posting-stream **criterion** and reserve "test" for the Go test.

### OBS-3 — three out-of-scope observations, none attributable to T516

1. **Two stale `[VERIFIED:]` citations in `repaymentperiod.go`, pre-existing at the merge base.**
   `:342` cites `RepaymentPeriod.java:377-389` for `OutstandingLoanBalance`; the oracle method is at
   `:389-403` (`:377-389` lands on `getUnrecognizedInterest` / `getCreditedAmounts`). `:354` cites
   `:391-393` for `AddPaidPrincipalAmount`; the oracle's `addPaidPrincipalAmount` is at `:405-407`.
   Both citations are present verbatim at `14cf6c1f` [VERIFIED: `git show 14cf6c1f:…repaymentperiod.go`],
   so they belong to neither T502, T511 nor T516. Worth noting because doc.go now cites the *correct*
   lines for the same two methods, so the package contradicts itself on line numbers. Follow-up, not
   a finding.
2. **`doc.go`'s "genuine … real balance write" describing `savings/summary.go:53` is loose, and is
   T511's text, untouched by T516.** It sits at `fc35f4eb:doc.go:204, :206` and moved unchanged to
   `709e51c3:doc.go:302, :304` [VERIFIED — both opened]. The write is
   `func (s SavingsAccountSummary) Add(effect MinorUnits) SavingsAccountSummary { s.AccountBalance += effect; return s }`
   — a **value** receiver returning a copy, i.e. a pure fold over postings, which is the shape I-3
   *prescribes* rather than a stored-balance write. The C-1 guard-withdrawal argument is unaffected
   (its point is only that the guard classes it `I3-FIELD-WRITE` and a file move would reclassify
   it), but the adjective overstates. T514's C-1 was explicitly outside T516's remit, so this is not
   T516's to have fixed.
3. **`gofmt -l` over the whole module lists four files** — `internal/apps/loanschedule/contract/contract.go`,
   `internal/apps/parties/client.go`, `internal/apps/parties/group.go`,
   `internal/apps/parties/legalform.go`. All four are listed identically by `gofmt -l` on `main`'s
   tree [VERIFIED — run on both]. Pre-existing; T516 touched none of them, and its own package is
   clean.

---

## VERDICT

**APPROVED.**

T516 was asked to fix three findings and instead widened its remit to retire a criterion. Graded as
if wrong, it survives: every citation in the retirement argument is exact against the pinned
checkout; no principled backward stopping rule exists that separates the counterexample from the
four sites without collapsing into the already-dead column argument; LEG 2 is a genuinely different
claim from RETIRED 1 and holds along every reachability path I could construct, including the
`json_model` loop, the model→installment mapping and the schedule table's 34 columns; the parity leg
is executable and I reproduced its failure myself at 70000 vs 90000; the guard census reproduces
line for line; the citation correction against T514 is right on both trees; and the commit is
provably the same program as its parent at AST level, with the range-vs-commit difference fully
attributed to T502.

The two MINOR findings are wording and nomenclature in comments. Neither touches a number, an
arithmetic expression, a field name or a test. Neither justifies blocking a commit that changes zero
executable lines and leaves a knowingly-red bar honestly red.
