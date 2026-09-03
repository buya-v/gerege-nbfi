# T505 — independent review of T502 (`softhouse/T502-loanproduct-i3`, `0b5e8b81`)

**Do I agree the four sites are not balance writes? YES — but not for the reason T502 gives, and
its proposed guard patch must not land, because I measured it amnestying a real savings balance
write via a one-directory refactor.**

**VERDICT: ACCEPT WITH CONDITIONS.**

Reviewed at oracle commit `426a23544` (`/Users/buv/fineract`). Every cited Java line was opened,
not trusted. Every count below was produced by running something, and the command is given (P-104).

---

## 0. The question, answered

T502 was offered (a) genuine ledger-balance writes → derive by summation, or (b) schedule
intermediates colliding with the guard's name pattern. It chose (b), renamed nothing, changed no
arithmetic, and left the bar RED.

**(b) is true.** The four cells are not ledger balances. But the failure mode the brief sent me to
hunt is present, in a specific place: **E-1 ("never a column") is a list of individually accurate
citations that does not entail its conclusion**, and it is the leg the guard patch is built on. The
conclusion is rescued by a different argument that T502 never states — that there is no posting
stream — and the patch is not rescued at all.

| Leg | Claim | My finding |
|---|---|---|
| E-1 | never a column, anywhere | citations TRUE, **conclusion NOT ESTABLISHED** — MAJOR-2 |
| E-2 | interest base, not an account balance | **TRUE**, exact |
| E-3 | signed delta, every caller negates | **TRUE**, all six; one line number off by one (MINOR-1) |
| E-4 | swept snapshot; derive-on-read = 900.00 → 700.00 | **REPRODUCED INDEPENDENTLY** |
| new test | driven RED against derive-on-read | **CONFIRMED FALSIFIABLE**, I drove it RED myself |
| §5 patch | reclassifies 4, keeps 3 savings refused | measurement HONEST, **design UNSAFE** — MAJOR-1 |
| §6 B-1 | identical write ships GREEN in `loanschedule` | **CONFIRMED IN FULL** — MAJOR-3 |

---

## 1. Scope and hygiene — verified, clean

```
$ git show --stat --format="" 0b5e8b81
 .softhouse/handoff/T502-loanproduct-i3.md              | 603 +
 nexus/internal/apps/loanproduct/doc.go                 |  76 +
 nexus/internal/apps/loanproduct/interestperiod.go      |  55 +-
 nexus/internal/apps/loanproduct/interestperiod_test.go | 108 +
 nexus/internal/apps/loanproduct/repaymentperiod.go     |  12 +-
$ git diff --stat main 0b5e8b81~1
 .softhouse/tasks.json ... | docs/incidents/2026-09-03-...md ...   (2 files, BEFORE its commit)
```

Exactly five files. The `tasks.json` / `docs/incidents` divergence is base-vs-main drift at
merge-base `14cf6c1f`, present before T502's commit exists — **not its writing**, as it said.
`.softhouse/guards/**` untouched on the branch. The code diff is comments plus one new test file:
**zero arithmetic changed, zero identifiers renamed**, confirmed by reading
`git diff 0b5e8b81~1..0b5e8b81` in full. The two `ip.outstandingLoanBalance =` and two
`ip.balanceCorrectionAmount =` statements are byte-identical to main.

Build / format / tests, re-run by me on a scratch tree carrying T502's five files:

```
$ go build ./...                          # clean
$ gofmt -l internal/apps/loanproduct/     # no output
$ go test ./internal/apps/loanproduct/    # ok
```

(Unrelated `financialactivity_test.go` failures appear only because my scratch tree sits in `/tmp`
and the capture directory resolves relative to the repo root. Not a T502 defect.)

Guard re-run by me, with `bash`:

```
$ bash .softhouse/guards/check-ledger-invariants.sh ; echo EXIT=$?
EXIT=1
  14 findings; the four loanproduct I3-FIELD-WRITE sites present at main's line numbers
  196:4 / 207:2 / 224:2 / 541:4
```

T502's transcript shows `236 / 247 / 273 / 551` — its own branch, +49 lines of comments above the
sites. Same four writes. **It did not clear its bar and it said so plainly.** That is the correct
behaviour and I want it on the record: a rename here would have turned the bar green while changing
nothing, and T502 refused to do it.

---

## 2. MAJOR-1 — the §5 guard patch amnesties a real balance write. MEASURED. It must not land.

This is the most serious finding in the review and it is against the patch, not against the code.

I rebuilt T502's scratch guard from `/tmp/t502guard/main.go` (still present; I diffed it against the
repo guard — 131 added lines, exactly the five pieces §5 describes, nothing else) and reproduced its
claimed output exactly: 4 loanproduct sites reclassified to `I3-FIELD-WRITE-NONPERSISTENT`, the
three `savings` sites still refused, exit 1. **The measurement in the handoff is honest.**

Then I built the counterexample the brief asked for — *a package with no db surface whose value is
persisted by a caller that has one.* I did not have to invent one. It is already in this tree.

`nexus/internal/apps/savings/summary.go:53` carries `s.AccountBalance += effect` — a genuine savings
account balance write, one of the three the patch claims "stay refused — nothing amnestied."

```
$ cp -R nexus /tmp/t505cx
$ cd /tmp/t505cx && mkdir -p internal/apps/savings/model
$ sed 's/^package savings$/package model/' internal/apps/savings/summary.go \
      > internal/apps/savings/model/summary.go && rm internal/apps/savings/summary.go
$ /tmp/t505-lg --root /tmp/t505cx
  [I3-FIELD-WRITE-NONPERSISTENT] internal/apps/savings/model/summary.go:53:2
  [I3-FIELD-WRITE]               internal/apps/savings/postgres.go:243:7
  [I3-FIELD-WRITE]               internal/apps/savings/postgres.go:302:5
```

**One `git mv` into a subdirectory moves a real account-balance write from REFUSES to
NEVER-REFUSES.** No rename, no arithmetic change, no code change of any kind — the file's bytes are
identical but for its `package` clause. And this is not an exotic move: `model/` or `domain/` next
to a `postgres.go` repository is the ordinary Go layering. The discriminator does not track "this
value reaches a balance column"; it tracks "this value happens to live in the same directory as a
string containing SQL."

Two aggravating facts:

- `CANNOT-CATCH` item 8 already advises a tripped author that *"the fix is a constructor, not an
  exemption"* — which B-2 shows defeats the guard. Item 9 would add a second sanctioned evasion:
  move it one directory down. The guard would ship advice for two ways around itself.
- T502 names this fail-open direction honestly in §5 and §7, and argues that printing the site by
  name is enough. **It is not, for a money non-negotiable.** The bar is the exit code. A class that
  prints and never sets `rc` is P-45's shape exactly: an enforcement that works only when someone
  remembers to read the output.

I also tested the milder attack and it FAILED, which is a point in T502's favour and I record it:
rewording the two English error strings in `savings/money.go` (which the patch's run reports as the
evidence marking `savings` persistent) does **not** flip the package — `postgres.go:42` carries real
SQL and marks it anyway.

```
$ sed -i '' 's/no integer digits before the decimal point/bad numeric text A/' .../savings/money.go
$ /tmp/t505-lg --root /tmp/t505cx
  persistent: internal/apps/savings — holds an SQL-shaped literal (internal/apps/savings/postgres.go:42:54)
```

So §5's "nothing was amnestied" is true of the tree as it stands. It is not a property of the
design, and it survives one refactor.

**Condition C-1: the §5 patch does not land in this form.** If a discriminator is wanted, it needs
to follow the type across the import graph — which means a type checker (`go/types`), not an
`ast.Inspect` over one directory. Until that exists, the honest position is T502's own fallback,
stated in its §7: *"these four sites stay red until a type-checker-based discriminator exists, and I
would rather ship that answer than a rename."* **That is the right answer and it should have been
the recommendation, not the alternative.**

---

## 3. MAJOR-2 — E-1's citations are true and do not entail its conclusion

Every fact in E-1 is correct. I opened all of them:

- `InterestPeriod.java:43` — `public class InterestPeriod implements Comparable<InterestPeriod>`,
  annotated `@Getter @ToString @EqualsAndHashCode @AllArgsConstructor`. **No `@Entity`, no `@Table`,
  no `@Column`.** Verified by `grep -n '@Entity\|@Table\|@Column'` — zero hits in the file.
- `ProgressiveLoanModel.java:33-58` — the column list is exactly `loan_id / json_model (text) /
  business_date / last_modified_on_utc / json_model_version`. No balance column. Exact.
- `LoanRepaymentScheduleInstallment.java:60-162` — I listed all 33 `@Column` names. Not one contains
  "balance". Exact.
- `InterestScheduleModelRepositoryWrapperImpl.java:55-73` — serialises the model to a string and
  stores it in `jsonModel`. Exact.

**The load-bearing step fails.** The brief asked whether a value serialised into a JSON blob escapes
"balance column." It does not, and the file T502 cites proves it:

- `InterestPeriod` carries `@JsonExclude` on exactly two fields — `repaymentPeriod` (`:44`) and `mc`
  (`:68`). `balanceCorrectionAmount` (`:65`) and `outstandingLoanBalance` (`:66`) carry none, and
  `JsonExcludeAnnotationBasedExclusionStrategy` excludes only annotated fields. **Both cells are
  serialised into `m_loan_progressive_model.json_model`.**
- The blob is not write-only. `getSavedModel` reads it back through `extractModel` and, when the
  stored business date is stale, re-processes transactions **onto the loaded model** rather than
  rebuilding it (`InterestScheduleModelRepositoryWrapperImpl.java:110-128`). The stored value is
  starting state, not a discarded cache.

**Is this consistent with T501?** T501 was told the analogous thing about `account_balance_derived`
and answered:

> *"A decoded balance is a number this port did not derive, arriving through the `SELECT` instead of
> the `INSERT`, and landing in a field callers then treat as authoritative. A read-back satisfies
> 'not written' while defeating exactly that purpose."*

T501 deleted a **field**, not a column, on that reasoning. On T501's standard, *"it is a `text` blob
and not a typed column"* would not have survived — a stored balance is a stored balance, and T501
already ruled that the vehicle does not matter.

**The two conclusions are still reconcilable, but not on T502's ground.** What makes T501's site a
violation and T502's four sites lawful is not the presence or absence of a column. It is this:

> **I-3 governs ledger balances, and a ledger balance is defined by the posting stream it folds.
> `SavingsAccountSummary.AccountBalance` has one — the transaction stream — so the remedy "derive by
> summation over the postings" is available, and T501 applied it. `InterestPeriod.outstandingLoanBalance`
> has none. An amortisation schedule is a projection of the future; postings are records of the past.
> The guard's prescribed remedy is not inconvenient here, it is definitionally inapplicable: there is
> no posting to sum.**

That argument is sound, it survives T501's standard, and it does not depend on the column question
at all. It is also stronger than E-4: E-4 says deriving on read *changes the numbers*, which is a
parity argument; this says the derivation *does not exist*, which is a category argument.

I confirmed the category claim by tracing the whole downstream chain myself, which T502 did not do:

```
InterestPeriod.outstandingLoanBalance
  → InterestPeriod.java:151          the DECLINING_BALANCE interest base (E-2)
  → RepaymentPeriod.java:389-403     period-level balance, Memo'd with an invalidation key
  → ProgressiveLoanScheduleGenerator.java:132
       → LoanScheduleModelRepaymentPeriod.setOutstandingLoanBalance   (a DTO)
  → LoanSchedulePlan.java:65,77                                       (a DTO)
```

It terminates in response DTOs and the JSON blob. No journal entry is posted from it; no GL account
derives from it; `m_loan_repayment_schedule` drops it at the persistence boundary.

**Condition C-2: restate E-1 on the posting-stream ground.** `doc.go` and the three in-code comments
currently teach a later reader that *"never a database column"* is the test that makes a balance-named
write lawful. That is the wrong test, it contradicts T501, and the next author who applies it will
argue away a real balance write with it.

### MINOR-2 — the one column T502 did not check, and should have

`LoanTransaction.java:127` declares
`@Column(name = "outstanding_loan_balance_derived") private BigDecimal outstandingLoanBalance` — a
real stored balance column on `m_loan_transaction`, bearing **the same name as the cell under
review**. E-1's downstream check looked only at `m_loan_repayment_schedule` and missed it.

I traced it. It is written by `LoanBalanceService.updateLoanOutstandingBalances`
(`:174`, `:194`, `:203`) from a **separate** running accumulator over `LoanTransaction` amounts, not
from `InterestPeriod`. Two different quantities sharing a name across two packages
(`loanaccount.domain` vs `loanproduct.calc.data`). **T502's conclusion survives this**, but it
survives by luck rather than by the check it performed, and the near-miss belongs in the record —
this column is the `m_trial_balance` shape and whoever ports `LoanBalanceService` will meet it.

---

## 4. E-4 and the test — reproduced, and the test is genuinely falsifiable

I did not take the 900.00 → 700.00 number on trust. I copied T502's five files onto a scratch tree
and drove the derive-on-read shape in myself:

```go
func (ip *InterestPeriod) OutstandingLoanBalance() Money {
	ip.UpdateOutstandingLoanBalance()   // the shape (a) would require
	return ip.outstandingLoanBalance
}
```

```
$ go test ./internal/apps/loanproduct/ -run TestOutstandingLoanBalanceIsASweptSnapshot -v
--- FAIL: TestOutstandingLoanBalanceIsASweptSnapshot (0.00s)
    interestperiod_test.go:57: the cell is a SWEPT SNAPSHOT, not an on-demand derivation:
    reading it after a summand changed but before a sweep gave 70000 minor units, want the
    unchanged 90000.
```

Unpatched, both new tests PASS. **So the test is falsifiable in the direction of the defect, not a
test that cannot fail (P-45/P-22).** `900.00 → 700.00` is real: 90000 vs 70000 integer minor units,
no float anywhere in the path.

The divergence follows from staleness, not from a bug in my patch. The roll-forward at
`InterestPeriod.java:173-178` reads the **previous** segment's `balanceCorrectionAmount`; the fixture
mutates that summand and does not sweep; the oracle's stored cell therefore cannot move, while an
on-demand derivation must. Arithmetic checks out against the Java on both sides:
`0 + 1000.00 − 100.00 = 900.00`, and `0 + 1000.00 − 200.00 − 100.00 = 700.00`.

One nuance T502's account flattens, worth recording because it cuts against nothing but sharpens the
picture: at the *period* level the oracle **is** derive-on-read —
`RepaymentPeriod.getOutstandingLoanBalance()` (`:389-403`) recomputes through a `Memo` whose
invalidation key includes `interestPeriods`, and it adds the last segment's `balanceCorrectionAmount`
at read time. The snapshot semantics are a property of the **segment** cell specifically. T502's port
already makes exactly this distinction (it drops the `Memo` for the period cell and keeps the
snapshot for the segment cell), so the port is right; only the handoff's prose is coarse.

---

## 5. MAJOR-3 — B-1 confirmed in full, and it cuts both ways

Independently verified, exactly as T502 reported:

`nexus/internal/apps/loanschedule/emi.go:1688-1690`:
```go
// updateOutstandingBalances is calculateOutstandingBalance
// [VERIFIED: ProgressiveEMICalculator.java:1253-1255 ->
// InterestPeriod.updateOutstandingLoanBalance, InterestPeriod.java:166-186].
```
`emi.go:1720-1721, :1726`:
```go
s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor-due)
s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor)
```
`emi.go:62`: `// outstandingMinor is the balance carried INTO this segment.`

**Same oracle method. Same write. Its own comment calls the field "the balance." It ships GREEN, in a
merged, reviewed, vector-graded package, solely because the identifier is spelled `outstandingMinor`.**

Tree-wide census (run by me):

```
$ grep -rnE --include='*.go' '\.[a-zA-Z0-9_]*[Bb]alance[a-zA-Z0-9_]* *=[^=]' nexus/ | grep -vE '==|!=|:='
  4 hits — all in loanproduct (interestperiod.go:196,207,224; repaymentperiod.go:541)
$ grep -rn 'outstandingMinor *=' nexus/
  2 hits — loanschedule/emi.go:1720, :1726
```

**Six plain assignments to balance-in-substance fields exist in the tree; the guard reports four.**
The refusal list understates the tree, and the four it names are the ones that were named honestly.

This is the right conclusion to draw, and T502 draws it correctly: *"it means the guard's sample is
arbitrary, not that its target is wrong."* It does not license the four sites. It shows the guard is
not measuring what it claims to measure — which is an argument for a better discriminator, and
(given MAJOR-1) not for this one.

## 6. B-2 and B-3 — both confirmed, both real

**B-2 confirmed, count exact.** Six composite-literal assignments to the two refused fields, all in
`loanproduct`, none flagged:

```
$ grep -rnE --include='*.go' '^[[:space:]]*(balanceCorrectionAmount|outstandingLoanBalance)[[:space:]]*:' nexus/
  interestperiod.go:281,282,306,307   repaymentperiod.go:96,97      (count: 6)
```
(On main. On T502's branch these are `330-331 / 355-356 / 96-97` — the +49 comment lines. T502's
numbers are right for its own branch; I note this so a later reader does not score it as an error.)

`writeTarget` is applied only to `*ast.AssignStmt` and `*ast.IncDecStmt`, so a `KeyValueExpr` is
invisible. **The guard objects to the statement form, not the concept** — and `CANNOT-CATCH` item 8
actively recommends the constructor, i.e. the form that defeats it. This is a live hole and item 8 is
currently bad advice.

**B-3 confirmed.** `repaymentperiod.go:486 func (p *RepaymentPeriod) SetReAgedEarlyRepaymentHolder`.
`…Holder` is a third `holdFuncRe` over-match; item 7 lists two. Harmless (it cannot produce a finding
alone) but item 7's whole purpose is completeness.

**B-4** — I agree the three `savings` sites are genuine I-3 violations, and T501 has since repaired
them by deleting the write paths and the fields. Out of scope for this review; graded only insofar as
MAJOR-1 shows T502's patch would un-repair one of them after a refactor.

---

## 7. Minor findings

- **MINOR-1.** E-3 and the commit message cite `ProgressiveEMICalculator.java:906` for the
  self-negation form. The actual site is **`:907`**. `:922`, `:946`, `:952`, `:1124`, `:1129` are all
  exact. The substance — every oracle caller adds a negated amount — is verified TRUE at all six.
- **MINOR-2.** `m_loan_transaction.outstanding_loan_balance_derived` — see §3.
- **MINOR-3.** §5's "two things whoever lands this must do" item 2 calls the `sqlShapedRe`
  over-match *"fail-CLOSED … the safe side."* Directionally right, but T502 never checked whether the
  over-match was load-bearing for the packages it needs to stay refused. I checked (§2): it is not,
  for `savings`. The claim holds; the check that should have supported it was not performed.
- **MINOR-4.** The handoff's §E-4 prose describes the cell as having "no invalidation key at all"
  without distinguishing the segment cell from the period cell, which does have one. The *port* makes
  the distinction correctly; only the prose is coarse. See §4.

---

## 8. Verdict and conditions

**ACCEPT WITH CONDITIONS.**

T502 was asked to choose (a) or (b) with oracle evidence, not to rename, and not to fake green. It
did all three. Its arithmetic is untouched and byte-identical, its new test is real and I drove it
RED myself, its headline measurement reproduces exactly, and it declared its own red bar rather than
dressing it up. **The four sites are not ledger balance writes and must not be "derived by summation"
— there is nothing to sum.** Refusing to rename was the right call and the single most valuable thing
in this branch.

The defects are in one leg of the argument and in a patch that has not landed — neither is shipped
code.

**C-1 (blocking, MAJOR-1). The §5 guard patch must not land as written.** Measured: a real savings
account-balance write is amnestied by moving one file into a subdirectory. Adopt T502's own §7
fallback instead — these four sites stay RED until a `go/types`-based discriminator can follow the
value across the import graph. Record the counterexample in §2 alongside the proposal so it is not
re-proposed.

**C-2 (blocking, MAJOR-2). Restate E-1 on the posting-stream ground** in `doc.go` and the three
in-code comments. The operative test is *"no posting stream exists, so 'derive by summation over the
postings' names no computation"* — not *"it never becomes a database column."* The column test
contradicts T501's ratified standard and would license a real balance write in the hands of a later
author. Note in the same place that both cells **are** serialised into
`m_loan_progressive_model.json_model` (no `@JsonExclude`) and read back as starting state, so nobody
rediscovers that as a contradiction.

**C-3 (non-blocking). Carry MAJOR-3, B-2, B-3 and MINOR-2 forward as guard backlog** — the
`loanschedule` GREEN twin, the composite-literal hole together with the `CANNOT-CATCH` item 8 advice
that points at it, the `…Holder` over-match, and `m_loan_transaction.outstanding_loan_balance_derived`.

**C-4 (non-blocking). Fix MINOR-1** (`:906` → `:907`).

**The bar stays RED for these four sites, and that is the correct state.** It should be recorded as a
known, argued, test-pinned red — not cleared by a rename, and not cleared by this patch.
