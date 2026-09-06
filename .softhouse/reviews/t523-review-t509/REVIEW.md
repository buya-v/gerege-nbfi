# T523 — INDEPENDENT REVIEW of T509 (`ledgerguard` / `guard_ledger_invariants`)

**Subject:** commit `23966a65` ("T509: close the under-match — balanceSynonymRe, plus a drive-red
control that works on a legitimately red tree"), author SoftFactory, 2026-09-04, ancestor of
`origin/main`. Originally filed against `857dd4d8` on `softhouse/T509-ledgerguard-blindspot`;
that sha does not exist (`git cat-file -t 857dd4d8` → `Not a valid object name`).

**Reviewer:** T523, isolated worktree at `origin/main` = `4b843787`.
**Reference oracle (Fineract): NOT CONSULTED.** Nothing in this review needed it; no claim below
depends on an oracle capture. Go 1.24.7 at `/usr/local/go/bin/go` (fallback toolchain, announced
by `go-env.sh` — not the pinned toolchain; acceptable for guards, and no parity claim is made).

Every script and every raw transcript cited here is committed under
`.softhouse/capture/t523-review-t509/`.

---

## VERDICT: **ACCEPT WITH CONDITIONS**

The four numeric claims reproduce **exactly**. The two controls T509 replaced genuinely bite —
I broke both and both failed. The `I3-SQL-BALANCE-TABLE` class and the wrapper-discovery
extension are real movements toward the PROPERTY.

It is not APPROVED because I measured **two undeclared FAIL-OPEN holes** in the OPAQUE-SQL
refusal path — one of which reopens precisely the `InsertReturningInt64` spliced-column scenario
the baseline asserts is "no longer built" — **one undeclared blind direction in the baseline
control**, and **six false-positive classes**, four of which have no repair path other than
renaming a field, which is the move T502 was sent to make and refused to make.

**Central question, answered plainly.** The repair is a MIXTURE, and it should not be recorded as
one thing:

| Change | Property or spelling? |
|---|---|
| `I3-SQL-BALANCE-TABLE` (table identity, not column names) | **PROPERTY.** Genuine — catches a stored balance table whose thirteen columns never say "balance". |
| Wrapper discovery → OPAQUE-SQL on tree-local wrappers | **PROPERTY**, then partially undone by two name-keyed carve-outs (C-1, C-2). |
| `I3-COMPOSITE-BALANCE` closing the "move it into a constructor" evasion | **PROPERTY** for the evasion it closes; **SPELLING** for the 6 live findings it actually produces, all of which are zero-init or copy constructors. |
| `balanceSynonymRe = (?i)outstanding` | **SPELLING**, widened. It fixes an *inconsistency* (two ports of one method decided by spelling), which is worth having; it does not move toward the property, and it now carries **24 of the 34 live refusals**. |

---

## 1. THE COUNT — SETTLED. Answer **(a)**.

**42 reproduces exactly, class-for-class, at the subject commit's tree.** 34 is the **same
denominator** measured on today's `main`, after the savings and working-capital repairs landed.
The republished commit **is** equivalent to what was graded.

```
$ git archive --format=tar 23966a65 nexus -o …/nexus-23966a65.tar   # extracted to …/t509tree
$ lg-head --root …/t509tree/nexus | grep -cE '^  \['
42
$ … | grep -oE '^  \[[A-Z0-9-]+\]' | sort | uniq -c
      6   [I3-COMPOSITE-BALANCE]
     26   [I3-FIELD-WRITE]
      1   [I3-SQL-BALANCE-TABLE]
      8   [I3-SQL-BALANCE]
      1   [OPAQUE-SQL]
```
Identical to the driver's recorded breakdown (26 / 8 / 6 / 1 / 1).
[VERIFIED: `.softhouse/capture/t523-review-t509/ledgerguard-tree-23966a65.out`]

Today's `main`: **34** findings, `6 I3-COMPOSITE-BALANCE / 23 I3-FIELD-WRITE / 5 I3-SQL-BALANCE`
[VERIFIED: `ledgerguard-main-HEAD.out`]. The `Findings: 34` the dispatching driver read off the
SQL-surface census line **is** the total finding count — `len(c.Findings)`
[VERIFIED: `main.go:1389-1394`], the same quantity as 42. Deterministic across three runs.

**The guard source is byte-identical between `23966a65` and HEAD**, so everything below is a
review of the subject commit's code:
```
$ git rev-parse 23966a65:…/main.go HEAD:…/main.go \
                23966a65:…/check-ledger-invariants.sh HEAD:…/check-ledger-invariants.sh \
                23966a65:…/drive-red-ledger-invariants.sh HEAD:…/drive-red-ledger-invariants.sh
fd83923…  fd83923…   1d952ed…  1d952ed…   291467f…  291467f…
```
Only `ledger-invariants.baseline` changed after (14 pairs → 9, in the commit that carried the
repairs), plus a new `ledger-invariants-compare.sh`. Both are later work, flagged where relevant.

**Re-runs, all green:**
- `check-ledger-invariants.sh --selftest` → exit 0, `24 cases, 19 RED, 5 GREEN` — **claim matches**.
- `check-ledger-invariants.sh --prove` → exit 0, HEAD PROOFS 1-6 all as designed.
- `check-ledger-invariants.sh` → exit 1 (expected; the tree is red by recorded decision).
- `drive-red-ledger-invariants.sh` → exit 0, 12 plants each fired **at their own path**, CONTROL A
  green, CONTROL B `baseline MATCHED exactly: 9 pairs, none added, none silenced`.

### MINOR-1 — the headline count is inflated ~12% by per-column reporting
34 findings are **30 distinct `(class, position)` sites**; 42 were **37**. One INSERT at
`internal/apps/investor/postgres.go:108:30` is reported **five times**, once per balance column.
Not wrong, but "42 findings" reads as 42 sites and is quoted that way in the record.

### MINOR-2 — `Findings: N` is printed on the line labelled "SQL surface"
It is the whole-run total. This is exactly what made the dispatching driver unsure whether 34 and
42 were the same denominator. Move it to its own line, or label it `Findings (all classes): N`.

---

## 2. THE NEW FINDINGS, SAMPLED ADVERSARIALLY (8 sampled, across every new class)

| # | Site | Class | My independent verdict |
|---|---|---|---|
| 1 | `workingcapital/postgres.go:379:30` (T509 tree) | `I3-SQL-BALANCE-TABLE` | **TRUE POSITIVE.** Upsert into `m_wc_loan_balance` — a per-account stored balance table. This is the class's whole point and it works. |
| 2 | `workingcapital/postgres.go:168:13` (T509 tree) | `OPAQUE-SQL` | **TRUE POSITIVE** (refusal-to-certify). T506 F-6's scenario, live. |
| 3 | `investor/postgres.go:108:30` ×5 | `I3-SQL-BALANCE` | **TRUE POSITIVE.** A real `INSERT INTO m_external_asset_owner_transfer_details (… principal_outstanding_derived, interest_outstanding_derived, fee_charges_outstanding_derived, penalty_charges_outstanding_derived, total_outstanding_derived …)`. Fineract `_derived` columns; a stored, written sum wearing a balance's name. Unlocked **only** by `balanceSynonymRe`. |
| 4 | `loan/charge.go:126,137,…` ×11 | `I3-FIELD-WRITE` | **TRUE POSITIVE by anticipation, not today.** `c.AmountOutstanding = 0 / = c.calculateAmountOutstanding()` on a 1:1 port of `LoanCharge.java`. Fineract persists this as `m_loan_charge.amount_outstanding_derived`, but **`amount_outstanding_derived` appears nowhere in `nexus/`** (`grep -rn` → empty), so today these are in-memory mutations of a not-yet-persisted domain object. Defensible, but it is the *name*, not a store, that is being refused. |
| 5 | `investor/postgres.go:199,202,205,208,211` ×5 | `I3-FIELD-WRITE` | **DERIVATIVE, not independent.** These are `d.PrincipalOutstanding, err = MinorUnitsFromDecimalText(…)` inside a **row-scan callback** — a decode on the way *in*. See FALSE-POSITIVE FP1 below: this contradicts the guard's own CANNOT-CATCH item 9 ("a read is not a write path") one layer down. They would vanish with the `:108` INSERT they mirror. |
| 6 | `loanschedule/emi.go:1720,1726` ×2 | `I3-FIELD-WRITE` | **CONSISTENCY, correctly achieved.** T509's own case. These are now treated the same as the four `loanproduct` sites. That is right — spelling must not decide — but note what it means: T509 did not prove `outstandingMinor` is a ledger balance, it made two identical things identically **refused pending a discriminator that does not exist**. |
| 7 | `loanschedule/conformance/exemption_test.go:1446` | `I3-FIELD-WRITE` | **FALSE POSITIVE on the property.** `got.Periods[len-1].OutstandingPrincipalMinor = 0` inside `t233DivergentImpl` — a deliberately-divergent conformance test double. Declared under CANNOT-CATCH item 8 ("tests are inspected, not exempted"), so it is honest; it is still a permanently-red site whose only repair is renaming a contract field. |
| 8 | `loanproduct/interestperiod.go:469,470,496,497`, `repaymentperiod.go:96,97` ×6 | `I3-COMPOSITE-BALANCE` | **FALSE POSITIVE on the property — all six.** See MAJOR-4. |

---

## 3. THE NEGATIVE CONTROL — **NOT VACUOUS**, tested by mutation. One residual.

I mutated a scratch copy of `testdata/cleantree`, nine real violations, one at a time. **All nine
trip it, each with the right class.** The fixture is a live control, not a pass-by-construction.

```
CONTROL  unmutated fixture copy            exit=0
MUT m1-alloc-composite         exit=1  [I3-COMPOSITE-BALANCE] present/present.go:51:30
MUT m2-field-write             exit=1  [I3-FIELD-WRITE]       present/present.go:51:2
MUT m3-update-journal          exit=1  [I4-DML]               store/store.go:80:21
MUT m4-pkg-state               exit=1  [I3-PKG-STATE]         ledger/derive.go:77:5
MUT m5-sql-balance-insert      exit=1  [I3-SQL-BALANCE-TABLE] [I3-SQL-BALANCE]
MUT m6-spliced-sql             exit=1  [OPAQUE-SQL]           store/store.go:81:9
MUT m7-hold-posted-balance     exit=1  [I6-HOLD-BALANCE]      ledger/derive.go:80:2
MUT m8-outstanding-field       exit=1  [I3-FIELD-WRITE]       ledger/derive.go:80:2
MUT m9-opaque-arg              exit=1  [OPAQUE-SQL]           store/store.go:81:9
MUT m10-GUTTED-members         exit=1  (P-35 zero-population gates: 0 funcs / 0 assignments /
                                        0 string literals / 0 composite literals → REFUSED)
```
[VERIFIED: `mutate-cleantree.sh` / `.out`]

The fixture also contains genuinely near-boundary GREEN constructs — a lawful
`INSERT INTO acc_gl_journal_entry`, a `SELECT … outstanding_loan_balance_derived` that must be
**named and not refused**, a by-value composite literal, a wrapper pass-through, a `ctxHolder`
field-context repository. It is a real over-match check. Case (n) additionally refuses a
**missing** member and a **missing** fixture rather than skipping (`main.go:1864-1880`).

### MINOR-3 — the member list pins PRESENCE, not CONTENT: partial erosion is silent
`m10` proves full gutting is caught. Partial erosion is not. Each of these keeps enough
population to clear P-35 and **silently removes a whole over-match check**:

```
ERODE e1-drop-byvalue-composite    exit=0   13 funcs   # the ONLY value/pointer line check
ERODE e2-drop-outstanding-green    exit=0   14 funcs   # the ONLY lawful balanceSynonymRe exercise
ERODE e3-drop-balance-read-select  exit=0   14 funcs   # the ONLY proof a balance READ is not refused
ERODE e4-drop-journal-insert       exit=0   13 funcs   # the ONLY proof appending to the journal is lawful
ERODE e5-drop-hold-green           exit=0   14 funcs   # the ONLY GREEN holdFuncRe exercise
```
[VERIFIED: `erode-cleantree.sh` / `.out`]

---

## 4. THE `drive-red` REPAIR — **VERIFIED, and T509 UNDERSTATED IT.**

Ran the guard over an **unplanted** copy of `nexus/` and evaluated both match forms for all
twelve plant paths.

```
PLANT 1  I3-FIELD-WRITE        OLD-form(class anywhere)=23 PASS(WRONG)  NEW-form(class@path)=0 fail(correct)
PLANT 5  I3-SQL-BALANCE        OLD-form=5  PASS(WRONG)                  NEW-form=0 fail(correct)
PLANT 10 I3-COMPOSITE-BALANCE  OLD-form=6  PASS(WRONG)                  NEW-form=0 fail(correct)
PLANT 11 I3-FIELD-WRITE        OLD-form=23 PASS(WRONG)                  NEW-form=0 fail(correct)
(plants 2,3,4,6,7,8,9,12: both forms correctly fail — those classes are absent from the tree)
```
[VERIFIED: `plant-deleted-control.sh` / `.out`]

The claim holds exactly: with its planted file deleted, the **old** form passes and the **new**
form fails. On **today's** tree four plants were vacuous. **At T509's own tree, six were** — the
class census there also carried `I3-SQL-BALANCE-TABLE` (1) and `OPAQUE-SQL` (1), so plants 9 and
12 were vacuous too. T509's write-up says "plants 1 and 5". That understates its own finding by
a factor of three. Not a defect in the fix; recorded because the record is quoted downstream.

---

## 5. `sqlArgOf` DIRECTION — **fails closed on the driver arm. TWO FAIL-OPEN HOLES ELSEWHERE.**

Structurally the driver arm is fail-closed: `readable := have && isPureStringLiteral(arg)`
(`main.go:1082`), so `have == false` → `OPAQUE-SQL`. Behaviourally confirmed on five constructed
unresolvable arguments, including an attack on the `ctx`-by-name widening itself:

```
S1-nonliteral-arg             want=REFUSE exit=1  [OPAQUE-SQL]
S2-var-arg                    want=REFUSE exit=1  [OPAQUE-SQL]
S3-too-few-args               want=REFUSE exit=1  [OPAQUE-SQL]
S4-field-holds-stmt           want=REFUSE exit=1  [OPAQUE-SQL]
S5-ctxnamed-field-holds-sql   want=REFUSE exit=1  [OPAQUE-SQL]
S8-CONTROL-readable-literal   want=PASS   exit=0
```
The direction is also **honestly recorded in the source** (`main.go:747-756`): T509 explicitly
writes that T503's "fail-CLOSED" was wrong and T506 F-5 is right. That is the right disposition.

But two shapes go **GREEN**:

```
S6-wrapper-param-reassigned   want=REFUSE exit=0   ← MAJOR-1
S7-select-prefix-splice       want=REFUSE exit=0   ← MAJOR-2
```
[VERIFIED: `sqlarg-direction.sh` / `.out`]

### **MAJOR-1 — the wrapper pass-through carve-out is defeated by reassigning the parameter, and the verdict is decided by the parameter's NAME**

`main.go:1115-1119` treats an argument that is the ident of the **enclosing function's SQL
parameter** as an unrefusable pass-through. It matches by **name** and never checks that the
ident is unassigned. Isolated by varying only the parameter name, everything else byte-identical:

```
A-param-named-sql-reassigned   exit=0   (nothing)
B-param-named-raw-reassigned   exit=1   [OPAQUE-SQL] probe/probe.go:19:9
C-newlocal-named-sql           exit=1   [OPAQUE-SQL] probe/probe.go:19:9
D-inline-splice-control        exit=1   [OPAQUE-SQL] probe/probe.go:19:9
```
[VERIFIED: `s6-mechanism.sh` / `.out`]

The GREEN body is:
```go
func Insert(ctx context.Context, db DB, sql string, cols string, a int64) (int64, error) {
    sql = "INSERT INTO m_loan_transaction (" + cols + ") VALUES ($1)"
    return InsertReturningInt64(ctx, db, sql, a)
}
```
This is **the exact T506 F-6 scenario** — a spliced column list routed through
`InsertReturningInt64` — which `ledger-invariants.baseline` asserts "is no longer built". It is
one assignment away from being buildable again, invisibly. And the mechanism is a **verdict
decided by spelling**, which is the precise defect T509 was dispatched to remove, reintroduced
one layer down.

### **MAJOR-2 — `readableVerbIsSelect` certifies a spliced statement on a literal PREFIX**

`main.go:667-679` concatenates only the **literal** fragments, and calls the whole statement
readable-and-clean if that text starts with `select` and carries no mutating verb. The spliced
segments are never seen.

```
P1-select-prefix-splice     "SELECT " + evil + " FROM x"        exit=0   ← waved through
P2-select-semicolon-splice  "SELECT 1;" + evil                  exit=0   ← waved through
P3-select-comment-splice    "SELECT 1 -- " + evil               exit=0   ← waved through
P4-select-calls-function    "SELECT apply_balance(" + evil + ")" exit=0  ← waved through
P5-CONTROL-update-prefix    "UPDATE " + evil + " SET amount = 1" exit=1  [OPAQUE-SQL]
P6-CONTROL-insert-prefix    "INSERT INTO " + evil + " VALUES (1)" exit=1 [OPAQUE-SQL]
P7-CONTROL-bare-splice      evil + " FROM x"                    exit=1  [OPAQUE-SQL]
```
[VERIFIED: `s7-select-prefix.sh` / `.out`]

**P2 is the one that matters.** `"SELECT 1;" + evil` under pgx's simple protocol executes both
statements; `evil` may be `UPDATE acc_gl_journal_entry SET …`. The guard certifies it. This is a
direct I-4 fail-open, and it is not in the CANNOT-CATCH list. The doctrine the guard states for
itself — "an unreadable statement is refused rather than assumed clean" — is not what this arm
does: it assumes the unread body is clean because the read prefix says SELECT.

---

## 6. THE BASELINE — both declared directions hold; **a third, undeclared direction is blind.**

**The exit-code claim is TRUE.** `ledgerguard/main.go` contains **no** reference to the baseline;
`check-ledger-invariants.sh` mentions it only in prose (lines 293, 303-304). Its sole functional
reader is `drive-red`'s CONTROL B. [VERIFIED: `grep -n -i baseline` on both files]

**Direction 1 — a new pair in a clean file → FAILS.** ✅
```
D1  new pair in an unlisted file    CONTROL-B=FAIL  findings=35
        + I3-FIELD-WRITE	internal/apps/ledger/t523_newpair.go
```

**Direction 2 — a vanished pair → FAILS.** ✅ (rename that silences without changing the write path)
```
D2a  emi.go balance field renamed out of the regex  CONTROL-B=FAIL  findings=32
        - I3-FIELD-WRITE	internal/apps/loanschedule/emi.go
D2b  investor/postgres.go renamed wholesale         CONTROL-B=FAIL  findings=24
        - I3-FIELD-WRITE	internal/apps/investor/postgres.go
        - I3-SQL-BALANCE	internal/apps/investor/postgres.go
```
[VERIFIED: `baseline-drive.sh`, `baseline-d2.sh`, and their `.out`]

*Honesty note on my own probe:* my first D2 attempt renamed `OutstandingMinor`; the real field is
`outstandingMinor`, lowercase, so it matched nothing and passed for the wrong reason. Both the
failed and the corrected probe are committed. A probe that silently matches nothing is the defect
this review grades elsewhere; it would have been dishonest to delete it.

### **MAJOR-3 — CONTROL B is blind to ANY change confined to a file it already lists, in BOTH directions**

The baseline records `(class, file)` pairs. Therefore:

```
REF   unmodified                                       CONTROL-B=PASS  findings=34
P1    ONE of emi.go's two findings renamed away        CONTROL-B=PASS  findings=33   ← silencing
P3    fresh balance write in an already-listed file    CONTROL-B=PASS  findings=35   ← new violation
P4    UPDATE of a balance column into a listed file    CONTROL-B=PASS  findings=35   ← new violation
B2    same tree vs a REGENERATED baseline              CONTROL-B=PASS  findings=35
      regenerated baseline row count: 9 (committed: 9)
```
[VERIFIED: `baseline-partial.sh` / `.out`, `baseline-drive.sh` / `.out`]

P4's payload is a textbook I-3 violation appended to `investor/postgres.go`:
```go
return db.Exec(ctx, `UPDATE m_savings_account SET account_balance_derived = $1 WHERE id = $2`, …)
```
CONTROL B passes. **No baseline edit is required, so there is nothing in any diff to review** —
this is cheaper and quieter than the regeneration channel the task asked me to look for. B2 shows
regeneration is worse than "visible": the regenerated file is **byte-identical in row count** to
the committed one, because the fresh violation left no row.

**How honest is the disclosure?** Half honest, and the half it omits is the load-bearing one.
The baseline header discloses the **additive** residual verbatim — *"a SECOND finding of an
already-listed class in an already-listed file does not move this set"* (present in the original
`23966a65` version, lines 20-28) — and points at the guard's own non-zero exit as the backstop.
That is a fair statement and it is the reason this is MAJOR and not CRITICAL: **no bar turns
green**; `ledgerguard` still exits 1 and prints P4's finding with its position.

What is **not** disclosed is the **subtractive** residual (P1). The same header claims direction 2
is *"the one that catches a rename that turns the bar green while changing nothing"*. P1 is
exactly that rename, applied to one finding instead of all of them, and it passes. The claim as
written is broader than what the mechanism does.

**Is it an exemption channel?** Not as built — it cannot clear the guard's exit code. But it is a
**no-silent-change check with a file-sized hole in it**, sitting on a money non-negotiable, and it
is described in terms that a later reader will take as stronger than it is.

---

## 7. `balanceSynonymRe = (?i)outstanding` — THE COST, MEASURED

Differential measurement: shipped guard vs a byte-identical build with the synonym regex replaced
by one that cannot match.

```
shipped guard findings:            34
same guard, synonym disabled:      10
attributable to (?i)outstanding:   24        ← 71% of every live refusal
```
[VERIFIED: `synonym-cost.sh` / `.out`]

`isBalanceName` (`main.go:340`) is `balanceNameRe || balanceSynonymRe` and is the **single
predicate** behind all six balance surfaces — Go identifier (`:888`, `:993`, `:1212`), SQL column
(`:501`, `:519`, `:555`) and, new in T509, **SQL table name** (`:477`). One regex now widens all
six at once.

**What it sweeps in.** The whole-tree census of identifiers matching `outstanding` and not
`balance` runs to 76 distinct names. These carry no money and would be refused wherever written:
`HasOutstanding` (18), `OutstandingInterestStrategy` (8), `WriteOffOutstanding` (8),
`OutstandingInterestStrategyKey` (4), `EventWriteOffOutstanding` (4), `noOutstanding` (6),
`OUTSTANDING_INTEREST_STRATEGY` (4), `TestWriteOffOutstanding`, `TotalOutstandingIsZero`,
`IsClosedRescheduleOutstandingAmount`, plus test-function names.

Constructed and measured — **six false-positive classes, with the true-positive control still
firing** so the CLEAN results are not an artefact of a dead binary:

```
FP FP1-readonly-decode           want=CLEAN  exit=1  [I3-FIELD-WRITE]
FP FP2-boolean-hasoutstanding    want=CLEAN  exit=1  [I3-FIELD-WRITE]
FP FP3-outstanding-request-count want=CLEAN  exit=1  [I3-FIELD-WRITE]
FP FP4-zero-init-constructor     want=CLEAN  exit=1  [I3-COMPOSITE-BALANCE]
FP FP5-copy-constructor          want=CLEAN  exit=1  [I3-COMPOSITE-BALANCE]
FP FP6-strategy-enum             want=CLEAN  exit=1  [I3-FIELD-WRITE]
   TP1-CONTROL-stored-balance    want=REFUSE exit=1  [I3-SQL-BALANCE]
```
[VERIFIED: `false-positive-probes.sh` / `.out`]

`l.HasOutstanding = true` on a `bool`, `q.OutstandingRequests++` on an `int`, and
`c.OutstandingInterestStrategy = s` on a `string` are all refused as balance writes. The guard has
no types, so the name is all it has — which is CANNOT-CATCH item 2, and item 2 **does say so**:
*"T509 WIDENED THE NAME, IT DID NOT FIX THE CLASS."* That sentence is the most honest line in the
commit and it is why this section is graded MINOR rather than MAJOR.

**Grade on the review's own terms.** It moved toward the **PROPERTY** in exactly one respect: it
removed a case where **two identical acts got opposite verdicts because of spelling**, and that
inconsistency was worse than over-refusal. It did **not** move toward the property in any other
respect, and it is now the sole cause of 71% of the refusals. B-11 / P-104's diagnosis — *"the
float guard matches a WORD LIST, and that is why it fails"* — applies unchanged: this guard
matches a two-word list. The score is 2 words instead of 1, on a surface the guard's own item 2
admits is unbounded.

### **MAJOR-4 — `I3-COMPOSITE-BALANCE` produces six live findings and all six are constructors with no repair path**

Every one of the six:
```
interestperiod.go:469  &InterestPeriod{balanceCorrectionAmount: ip.BalanceCorrectionAmount()}  in func copy
interestperiod.go:470  &InterestPeriod{outstandingLoanBalance:  ip.OutstandingLoanBalance()}   in func copy
interestperiod.go:496  &InterestPeriod{balanceCorrectionAmount: zero}   in func withEmptyInterestPeriod
interestperiod.go:497  &InterestPeriod{outstandingLoanBalance:  zero}   in func withEmptyInterestPeriod
repaymentperiod.go:96  &InterestPeriod{balanceCorrectionAmount: moneyZero(…)} in func NewInterestPeriod
repaymentperiod.go:97  &InterestPeriod{outstandingLoanBalance:  moneyZero(…)} in func NewInterestPeriod
```
Two are a **deep copy constructor** (a 1:1 port of `InterestPeriod.java:86-92`); four are
**zero-initialising constructors**. Neither act writes a balance in any sense the non-negotiable
means. Note that four of the six fire on `balanceCorrectionAmount`, which matches
`balanceNameRe` — so this is **not** a synonym artefact; it is the class itself.

The finding text advises *"Derive by summation over the postings"* and adds *"moving the write
into a constructor does NOT clear this."* **For a zero-initialiser there is nothing to derive and
no constructor to move to.** The only exits are renaming the field — the T502 move — or a DEC-2
exemption. This is the reviewer's stated fear realised in miniature: refusals that cannot be
cleared. They are currently parked in the `loanproduct` known-red block, but the recorded
argument for that block (T516 LEG 1 parity / LEG 2 reachability, awaiting a `go/types`
discriminator) is about **schedule intermediates**, not about **allocation-time zero values** —
a much simpler argument that would clear four of them without any type checker.

CANNOT-CATCH item 10 declares the class's **under**-match residual. It says nothing about this
**over**-match.

### MINOR-4 — FP1 contradicts CANNOT-CATCH item 9 one layer down
Item 9 states the doctrine that *"a read is not a write path"* and refuses to raise balance READs
to findings, correctly routing that as a DEC-2 amendment (a `user` gate). But the **decode** of a
read balance into a struct field **is** refused as `I3-FIELD-WRITE` — FP1, and the five live
`investor/postgres.go:199-211` findings. A read-only projection repository is refused today. The
guard should either say so in item 9, or not do it.

---

## 8. PARTIALS AND DEFERRALS — **honestly named. Four omissions.**

There is **no T509 handoff** anywhere on `origin/main`: `ls .softhouse/handoff/ | grep -iE
't509|ledgerguard'` → empty; `.softhouse/reviews/` carries no T509 entry. It was lost in the
republish (the driver's commit message records that the work was produced under a CLASSIFY-ONLY
brief and kept anyway). So the declared-limits artefact is the **CANNOT-CATCH list the guard
prints on every run, pass or fail** — which is a better place for it than a handoff.

**Judged on honesty, it is exemplary**, and I say so as the finding rather than as a courtesy:
- item 2 states outright *"T509 WIDENED THE NAME, IT DID NOT FIX THE CLASS"*;
- item 7 names **three measured over-matches** including one (`...Holder`) the list previously omitted, and explains that an incomplete list was itself the defect;
- item 8 records that the guard's **own former advice was evasion advice** and deletes it;
- items 10, 11, 12 scope the composite residual, the wrapper-discovery limits, and the four `loanproduct` sites.

**The four known-red `loanproduct` sites are still refused and NOT absorbed** — present in today's
34 at `interestperiod.go:338:4`, `:349:2`, `:404:2` and `repaymentperiod.go:688:4`
[VERIFIED: `ledgerguard-main-HEAD.out`], and the baseline's first block carries their argument
unchanged.

**Not declared anywhere:** MAJOR-1 (wrapper pass-through reassignment), MAJOR-2
(`readableVerbIsSelect` prefix), MAJOR-3's subtractive half, MAJOR-4 (composite over-match).

---

## CONDITIONS — filable verbatim

**C-1 (MAJOR, fail-open, money non-negotiable).** Close the wrapper pass-through carve-out at
`ledgerguard/main.go:1115-1119`. The ident equal to the enclosing SQL parameter's name must only
be treated as a pass-through when that parameter is **not assigned anywhere in the function
body**; otherwise refuse `OPAQUE-SQL`. Regression: `s6-mechanism.sh` variant A must go to exit 1
and match variants B/C/D. Add a selftest case in both polarities.

**C-2 (MAJOR, fail-open, money non-negotiable).** `readableVerbIsSelect`
(`ledgerguard/main.go:667-679`) must not certify a statement whose literal text is **incomplete**.
Minimum: refuse when `concatLiterals` reported `opaque == true` **and** the literal text contains
a `;` or ends mid-clause. Regression: `s7-select-prefix.sh` P1-P4 must all go to exit 1 while
S8/P5-P7 keep their current verdicts. Call out the pgx simple-protocol multi-statement shape (P2)
in the case comment.

**C-3 (MAJOR, control blindness).** Either (a) extend `ledger-invariants.baseline` rows to
`(class, file, count)` so CONTROL B fails in both directions on any count change inside a listed
file; or (b) if the drift cost is judged too high, amend the baseline header to state the
**subtractive** residual alongside the additive one, and withdraw the claim that direction 2
"catches a rename that turns the bar green" — it catches one only when it silences a file
entirely. (a) is preferred; the drift argument covers line numbers, not counts. Regression:
`baseline-partial.sh` P1, P3 and P4 must all report `CONTROL-B=FAIL`.

**C-4 (MAJOR, false positives with no repair path).** `I3-COMPOSITE-BALANCE` must not fire on a
composite literal that is the entire return value of a constructor and whose balance-named keys
are (i) a zero value, or (ii) a same-named field read from a receiver of the same type. Both are
syntactically decidable without `go/types`. If the class is kept as-is instead, the six
`loanproduct` sites need their **own** recorded argument in the baseline — the T516 schedule-
intermediate argument does not cover allocation-time zero values — and the finding text must stop
prescribing a remedy ("derive by summation") that does not exist for a zero-initialiser.

**C-5 (MINOR, internal inconsistency).** Reconcile FP1 with CANNOT-CATCH item 9: a decode of a
balance column into a struct field is currently `I3-FIELD-WRITE` while the SELECT that fetched it
is named-not-refused. Decide which side the read/write line falls on and record it in one place.

**C-6 (MINOR, spelling cost).** Add to CANNOT-CATCH item 2 the measured non-monetary sweep of
`(?i)outstanding` — bool, int counter and string-enum fields are refused (FP2, FP3, FP6) — and the
measured share: **24 of 34 live refusals**. Optionally gate the synonym on a monetary-looking
suffix (`Minor`, `_derived`, `Amount`), which is the cheapest available step from spelling toward
property.

**C-7 (MINOR, control erosion).** Pin the negative control's **content**, not only its members:
have case (n) assert a minimum count of the constructs it exists to protect (allocated-vs-value
composites, a lawful journal INSERT, a balance-naming SELECT, a hold-named function, a lawful
`outstanding` accumulator), so `erode-cleantree.sh` e1-e5 fail.

**C-8 (MINOR, reporting).** Move `Findings: N` off the "SQL surface" census line, and state
whether N counts findings or distinct sites (today: 34 findings = 30 distinct `(class, position)`
sites; 42 = 37).

**C-9 (MINOR, record accuracy).** Correct the drive-red header: at T509's own tree **six** of
twelve plants would have passed with their planted file deleted (1, 5, 9, 10, 11, 12), not two.

**No condition touches the frozen adapter contract, `nexus/`, or any DEC-n.** `23966a65` modifies
only `.softhouse/guards/**`; the guard is a separate Go module and `nexus/`'s build and tests are
untouched by it.

---

## What I checked and found nothing to report

- **Determinism**: three consecutive full runs, 34 each time.
- **Baseline exit-code independence**: `ledgerguard/main.go` has zero occurrences of "baseline";
  `check-ledger-invariants.sh` mentions it only in comments. Claim holds.
- **`--prove` falsifiability**: HEAD PROOFS 1-4 refuse a zero-file census, a missing census, a
  zero-case selftest and a never-RED selftest; PROOF 5 accepts the real guard on the fixture;
  PROOF 6 refuses it on the real tree. Both polarities present.
- **Plant path-matching regex**: `grep -c "\[$want\] $relpath:"` — the `.` in a filename is an
  unescaped metacharacter but cannot produce a cross-path match here; not worth a finding.
- **`sqlKeywordNotATableRe`** (the upsert `on table "set"` repair) behaved correctly on the
  `m5-sql-balance-insert` mutation and on every DML-classified literal in the census.
- **CLAUDE.md non-negotiables in the diff**: no float, no `first_name`/`last_name`, no US rails,
  no MySQL/MariaDB/Oracle driver or dialect, no port 1521, no deposit-insurance language.
  `git show 23966a65` touches guard tooling only.
- **Fixture money discipline**: `testdata/cleantree` is integer minor units throughout, as its
  README claims.

## What I could NOT verify

- **Whether the republished commit is byte-equivalent to `857dd4d8`.** `857dd4d8` does not exist
  on any ref reachable from this worktree, so no diff is possible.
  [UNVERIFIED: object absent]. What I *can* say is stronger than a hash comparison for this
  purpose: **the artefact at `23966a65` reproduces the driver's recorded measurement exactly** —
  42 findings, 26/8/6/1/1, 24 selftest cases, 19 RED, 5 GREEN, 12 plants, 2 controls. On the
  evidence the grading was performed against, the republished commit and the graded one are
  behaviourally the same artefact. That is a finding **for** the republish, not against it.
- **Any Fineract behaviour.** The reference oracle is unreachable (HTTP 000) and I did not need
  it; no claim here rests on a capture. Where I cite Fineract (`LoanCharge.java:108`,
  `InterestPeriod.java:86-92`) I am quoting the Go file's own `[VERIFIED: …]` annotation, not
  re-deriving it. [UNVERIFIED: oracle_unreachable]
- **Whether `m_loan_charge.amount_outstanding_derived` will be persisted by the Go port.** It
  appears nowhere in `nexus/` today (`grep -rn 'amount_outstanding_derived' nexus/` → empty).
  Whether the 11 `charge.go` findings become true stored-balance writes depends on work not yet
  done.
