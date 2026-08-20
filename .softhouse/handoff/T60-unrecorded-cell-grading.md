# T60 — the rig disagreeing with its own README about `unrecorded_fields`

Branch: `softhouse/T60-unrecorded-cell-grading`
Closes: T58 finding **N-2**. Same class as driver finding **D-5** and pattern **P-8**.

---

## 0. Base verified (pattern P-5)

```
$ git log --oneline -3
67bee40 softhouse: local fire lock (20260820-080002)
08df356 softhouse: release local fire lock (20260819-200001)
71fb3d7 program: close fire 20260819-200001 (zero -> 29 parity vectors; all four known mutations dead)

$ ls .softhouse/vectors/loanschedule/ | wc -l
      33          # 29 P-* parity + 4 REFUSE-* contract-refusal
```

`git branch -a --contains HEAD` confirmed `67bee40` **is** `origin/main`. No rebase
was needed. The 29 promoted parity vectors and the T56/T58 harness work were all
present. Worktree was clean at start.

---

## 1. The code path, traced from decode to invariant

All paths under `nexus/internal/apps/loanschedule/conformance/`.

| # | Step | Location | What happens to an `unrecorded_fields` entry |
|---|---|---|---|
| 1 | **Decode** | `vector.go:340` | `ExpectPeriod.UnrecordedFields []string`, doc at `:323-340`. |
| 2 | **Admit** | `admit.go:697-704` | Validated first; must name one of `UnrecordablePeriodFields()` (`admit.go:976-981`) — `kind` is deliberately absent. |
| 3 | **Admit: "unrecorded means EMPTY"** | `admit.go:722-818` | A withdrawn date must be the **zero Date** (`:743-752`); a withdrawn `installment_number` must be **0** and only on a non-payable row (`:772-781`); a withdrawn money cell must be `""` (`:813-816`). Finding T9-F1a. |
| 4 | **Replay build** | `registry.go:145-171` | `replayMinorCell` (`:180-195`) returns **`0`** for a withdrawn money cell; dates/installment number are copied straight from the vector, so a withdrawn date becomes the **zero CivilDate `0000-00-00`**. |
| 5 | **Cell diff** | `grade.go:502-505, 506-510, 529-533` | `diffSchedule` **correctly skips** an unrecorded cell and counts it `ungraded`. This half always matched the README. |
| 6 | **Invariants** | `grade.go:463` → `invariants.go` `CheckInvariants` | **THE DEFECT.** `CheckInvariants(v, got)` was handed the *same* `got` — placeholder and all — with no way to know which cells were stand-ins. `invBalanceRollForward` (`invariants.go:~175`) then read `p.OutstandingPrincipalMinor` and graded the `0`. |
| 7 | **Report** | `report.go:70-74, 217` | Only `VIOLATED` was ever printed. A placeholder that happened to satisfy an invariant produced a **plain `HOLD`**, indistinguishable from a real one. |

**The root cause in one sentence:** `diffSchedule` is told which cells are
unrecorded and the invariants are not, even though both read the same schedule —
so the field's guarantee stopped exactly at the boundary between them.

---

## 2. Reproduction BEFORE the fix

Built a scratch test against the unfixed rig (deleted after; it was never
committed and is superseded by the permanent test in §4). It perturbs only the
hand-authored `_selftest/SELFTEST-01-two-period-zero-rate.json` in a **copy** of the
store, and each perturbation is an *honest* withdrawal — value emptied, major text
emptied, field named in `unrecorded_fields` — i.e. exactly what `admit.go` demands.

**No vector in `.softhouse/vectors/loanschedule/` was read, written, promoted,
demoted or deleted at any point in this task.**

The defect turned out to have **three** manifestations, not the one reported.

### A — the reported symptom: honesty penalised (FALSE RED)

Withdraw the DISBURSEMENT row's `outstanding_principal_minor`:

```
EXIT 1  invariantViolations=1
  SELFTEST-01 outcome=FAIL graded=20 ungraded=1
    balance_roll_forward   VIOLATED  row 0 DISBURSEMENT: outstanding 0 != principal advanced 100000
```

Verbatim N-2. This is the form T58 hit on all 14 T39 vectors.

### B — NOT in T58's report, and the worse half: silent FALSE GREEN

Withdraw the **final** row's `outstanding_principal_minor`:

```
EXIT 0  invariantViolations=0
  SELFTEST-01 outcome=PASS
    principal_amortizes_to_zero  HOLD  final outstanding == 0
    balance_roll_forward         HOLD  every row's outstanding balance follows from the previous row...
```

The placeholder is `0`, and `0` is precisely the value `principal_amortizes_to_zero`
looks for — so the check **agreed with the stand-in it was handed** and reported a
clean HOLD. A check quietly passing on a number nobody observed is strictly worse
than the red in case A, and it was invisible.

### C — never confined to one invariant, or to money

Withdraw a REPAYMENT row's `due_date` (zero date, as `admit.go` requires):

```
EXIT 1  invariantViolations=2
    monotonic_due_dates    VIOLATED  row 2 REPAYMENT window [2026-02-01, 0000-00-00) is empty or inverted
    contract_row_ordering  VIOLATED  row 0 should be row 0 under the contract's window-key ordering
```

Two more invariants red on a calendar date the rig itself invented.

---

## 3. Option (a) — fix the rig — and why it was affordable

**Chose (a): make the code match the README.** (b) was rejected because the README's
promise is the *correct* behaviour; documenting the defect would have written the
disincentive against honest withdrawal permanently into the contract, which is the
opposite of what `unrecorded_fields` exists to do.

The brief's condition on (a) — *prefer it iff it does not weaken a check that
currently passes* — is met, and two design properties are what make it met.

### 3.1 The line between an answer and a placeholder

`registry.go`, `contractFixesCellAtZero`. A withdrawn cell is a placeholder **except**
where the frozen contract fixes it at `0` for that row kind as a **constant**:

* `contract.go:1509-1510` — a DISBURSEMENT row's *"InterestMinor is 0, and its
  InstallmentNumber is 0 because it is not payable"* (`:1532` likewise for
  DOWN_PAYMENT).

This is not an optimisation. **All 29 promoted parity vectors withdraw exactly
`installment_number` and `interest_minor` on their DISBURSEMENT row** (Path A prints
neither). Had I treated every withdrawn cell as a placeholder,
`splits_sum_to_whole`'s interest-column total would have become a **no-op across the
whole corpus** — the precise weakening the brief forbids. `admit.go:772-778` had
already ratified this same argument for `installment_number` (finding T9-F1c); I
state it once and extend it to interest, citing the contract.

**Deliberately excluded:** `outstanding_principal_minor` on a DISBURSEMENT row, even
though `contract.go:1512-1513` fixes it too — because it is fixed *as a function of
another cell of the same schedule* ("the amount advanced, equal to this row's
`PrincipalMinor`"), which is **verbatim what `balance_roll_forward` asserts**.
Supplying it would make the invariant check the rig's own derivation and hold every
time. That is the same circularity `vector.go:329-336` already forbids a promotion
task from committing to the store, one layer down. I followed T56's precedent: a
**documented sentinel with a cited rule**, not a quiet relaxation.

### 3.2 The invariants degrade per row, not all at once

`balance_roll_forward`'s running balance follows the **principal** column, which the
capture *does* record — so withdrawing the disbursement row's balance costs exactly
**one** assertion and both repayment rows are still checked on observed numbers. The
balance is tracked as a value **and** a known-flag, so an unobserved outstanding on a
row that *sets* the balance makes it unknown until the next observed outstanding
re-establishes it, rather than silently poisoning the rest.

`contract_row_ordering` has **no** partial form — one unkeyable row makes the whole
ordering unkeyable — so it reports `N/A`, never a HOLD over a half-fabricated schedule.

### 3.3 What I refused to weaken

* **`balance_roll_forward` is not exempted and not a no-op.** It still reports
  `hold 30, violated 0, not-asserted 0` on the committed corpus — byte-identical
  coverage to before this change.
* **No invariant was deleted, and none was added to `invariant_exemptions`.**
* **No vector was touched.** `git diff --stat` covers only the rig and the README.
* **Grading a real port is entirely unaffected.** `PlaceholderReporter` is an
  *optional* interface; a plain `contract.ScheduleGenerator` does not satisfy it, so
  a Go port declares nothing and every invariant runs in full. Sub-test **F** asserts
  this, so a future port cannot accidentally excuse an invariant.
* **A skipped assertion can never be silent.** `InvariantResult.NotAsserted` names
  row, cells and reason; a HOLD carrying one is a *partial* hold and says so in its
  detail; an invariant that could assert nothing returns `N/A` with a reason; the
  report has a dedicated `INVARIANT ASSERTIONS THAT COULD NOT RUN` section and a
  summary counter. On the committed corpus that section reads **NONE** and the
  counter is **0**.

### 3.4 Files changed

| File | Change |
|---|---|
| `conformance/invariants.go` | `PlaceholderCells`, `PlaceholderReporter`, `Field*` constants, `InvariantResult.NotAsserted`; all six invariants made placeholder-aware. |
| `conformance/registry.go` | replay declares its placeholders; `contractFixesCellAtZero`. |
| `conformance/grade.go` | plumbs placeholders into `CheckInvariants`; `Result.PlaceholderCells`, `Summary.InvariantAssertionsNotRun`. |
| `conformance/report.go` | `not-asserted` column, new section, summary line. |
| `conformance/structural_test.go` | permanent regression test, 6 sub-tests. |
| `.softhouse/vectors/README.md` | §5. |

---

## 4. Permanent regression test, proven to discriminate

`TestT60UnrecordedCellIsNeverGradedByAnInvariant` in `conformance/structural_test.go`
— A/B/C are the three reproductions above; **D** is the anti-weakening guard
(a contract-fixed cell stays graded); **E** asserts the committed corpus skips zero
assertions; **F** asserts a plain generator is not a `PlaceholderReporter`.

The brief's real requirement is that this test *can fail*, so I mutated the fix twice:

| Mutation | Effect | Result |
|---|---|---|
| Never declare a placeholder (reverts the behavioural core) | restores the old rig | **A, B, C FAIL** |
| `contractFixesCellAtZero` → always `false` (over-broad; would no-op checks corpus-wide) | over-corrects | **D, E FAIL** |

Both mutations were reverted; the file was restored from a byte copy and the full
suite re-run green. The guard against *over*-correcting is as load-bearing as the
guard against under-correcting, which is why D and E exist.

---

## 5. README corrections (`.softhouse/vectors/README.md`)

Two corrections. **No promotion rule was changed** — only statements of fact about
the store's contents, plus the paragraph documenting the behaviour I fixed.

1. **The false claim about the store's contents.** The class section ended with
   *"**Everything in this store is unpromoted today.** The store holds one self-test
   fixture and four contract-refusal vectors. `conformance.sh` therefore exits **2**
   with `NO PARITY VECTOR WAS GRADED`…"* — false since the 29 promotions. Replaced
   with a **"What the store actually holds today"** section carrying the measured
   figures (29 parity / 4 refusal / 1 self-test, 34 files, exit 0, 2,354 graded,
   58 ungraded), an explicit note that this paragraph is a *fact* that goes stale on
   every promotion and **must be updated in the same commit**, and a clarification
   that the `NO PARITY VECTOR WAS GRADED` fatal reason is **still live and still
   correct** — it just no longer fires on the default run. (Deleting the mechanism's
   description along with the stale fact would have been its own error.)

2. **The `unrecorded_fields` section**, which promised behaviour the rig did not
   have. Added *"The property invariants honour it too, and say what they could not
   check"*: both failure directions with their verbatim messages, the four rules now
   in force, and the contract-fixed-at-zero exemption with its citation and its
   deliberate exclusion of `outstanding_principal_minor`.

**Checked and found still accurate, so left alone:** the ACT/ACT paragraphs
("refused today… nothing is promoted") — verified `daycount.actual.actual` is still
`in_graded_domain: false` in `capabilities.json`, along with every capability except
`schedule.core` and `monthend.reanchor`; the pass-3 candidate list (a fact about the
capture corpus, not the store); the exit-code contract; the MathContext paragraphs.
The only numeric store claim in the file is now the one I wrote.

---

## 6. Verification — verbatim, as observed

```
$ . .softhouse/bin/go-env.sh; cd nexus
$ go build ./...      →  BUILD EXIT=0
$ go vet ./...        →  VET   EXIT=0
$ go test ./...       →  TEST  EXIT=0
ok  	github.com/gerege/nexus/internal/apps/loanschedule	(cached)
ok  	github.com/gerege/nexus/internal/apps/loanschedule/conformance	(cached)
?   	github.com/gerege/nexus/internal/apps/loanschedule/conformance/cmd/conformance	[no test files]
?   	github.com/gerege/nexus/internal/apps/loanschedule/contract	[no test files]

$ gofmt -l nexus/internal/
nexus/internal/apps/loanschedule/contract/contract.go        # G-3: expected, and the ONLY entry
```

```
$ .softhouse/conformance.sh          →  CONFORMANCE EXIT=0

--- INVARIANT COVERAGE (checked against what the implementation RETURNED) ---
    principal_portions_sum_to_disbursed    hold 30   violated 0    exempt 0    n/a 0    not-asserted 0
    principal_amortizes_to_zero            hold 30   violated 0    exempt 0    n/a 0    not-asserted 0
    balance_roll_forward                   hold 30   violated 0    exempt 0    n/a 0    not-asserted 0
    splits_sum_to_whole                    hold 30   violated 0    exempt 0    n/a 0    not-asserted 0
    monotonic_due_dates                    hold 30   violated 0    exempt 0    n/a 0    not-asserted 0
    contract_row_ordering                  hold 30   violated 0    exempt 0    n/a 0    not-asserted 0

--- INVARIANT ASSERTIONS THAT COULD NOT RUN (a cell the capture never recorded) ---
    [...]
    NONE — every invariant assertion ran, on cells somebody actually observed.

--- SUMMARY ---
    parity vectors          PASS 29   FAIL 0
    contract-refusal        PASS 4    FAIL 0   (derived from the ratified contract, NOT oracle-observed)
    self-test fixtures      PASS 1    FAIL 0   (hand-authored; EXCLUDED from the parity count)
    refused                 0   (no discriminating vector / seam blind — not a pass, not a failure)
    inadmissible            0
    harness errors          0
    cells compared          2354 graded, 58 ungraded (never recorded by the capture)
    kills named             86 money, 7 structural (zero-margin by construction, never merged)
    recorded, never graded  0 rate factors (TRANSCRIBED-ROUNDED), 0 declared over-scaled money cells
    invariant violations    0
    invariant assertions    0 NOT RUN (a cell nobody observed; listed above, never inferred)

VERDICT: PASS (exit 0) — 29 parity vectors match the pinned reference oracle, 2354 cells compared.
```

```
$ .softhouse/conformance.sh --prove       →  PROVE EXIT=0
=======================================================================
PROOFS: 20 passed, 0 failed
=======================================================================

$ .softhouse/conformance.sh --self-test   →  SELFTEST EXIT=0
    parity vectors          PASS 29   FAIL 0
    invariant violations    0
    invariant assertions    0 NOT RUN (a cell nobody observed; listed above, never inferred)
VERDICT: SELF-TEST PASS (exit 0). The harness grades correctly. NOT a conformance PASS.
```

**`balance_roll_forward` is unchanged at `hold 30, violated 0` with `not-asserted 0`.**
That line is the direct evidence that the fix removed a false signal and not a check.

---

## 7. Backlog — out of scope for T60, not acted on

1. **`--prove` does not cover the placeholder path.** All 20 proofs are green, but
   none perturbs a vector into an honest withdrawal of a *non*-contract-fixed cell.
   The Go test does (six sub-tests, two mutations), so the property is proven —
   but `conformance.sh --prove` is the artefact the driver re-runs independently, and
   this class of defect has now escaped twice. Worth a 21st proof.
2. **`Result.PlaceholderCells` is populated but never printed.** I added the summary
   counter (`InvariantAssertionsNotRun`) and the per-vector section, which is what the
   brief required; the per-vector placeholder *count* has no column in the table.
   Deliberate — the table is already 118 characters wide and the information is in
   the `UNGRADED` column.
3. **`DOWN_PAYMENT` rows remain unasserted by `balance_roll_forward`** (pre-existing,
   documented in the invariant, no capture has ever produced such a row). Untouched.
4. **Pattern candidate for `.softhouse/patterns.md`** (I did not edit it — out of
   scope): *a guarantee enforced at one consumer of a data structure and not at
   another is not a guarantee.* `unrecorded_fields` was honoured by `diffSchedule`
   and ignored by six invariants reading the same schedule. This is the third
   appearance of the family (T9-F1, D-5, T58-N2), and the generalisation is stronger
   than any of the three individually.
5. **The stale-fact problem is structural, not textual.** I corrected the README's
   count and added a "update this in the same commit" instruction, but nothing
   *enforces* it — the next promotion can falsify it again silently. A cheap fix
   exists: have the harness emit the counts and have a test assert the README's
   figures match. Not done here (it would be a new rule, and the brief scoped me to
   statements of fact).
