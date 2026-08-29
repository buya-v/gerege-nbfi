# T422 — INDEPENDENT review of T416 (`softhouse/T416-t405-conditions`)

STATUS: IN PROGRESS — committed incrementally. The VERDICT section is written last.

Reviewer: T422, branch `softhouse/T422-review-t416`.
Subject: `softhouse/T416-t405-conditions`, 10 commits, tip `9f4fc247`, merge-base current `main` (`e13966dc`).
Scratch tree for every drive: `/tmp/t422/t416` (a `git clone --shared` of the repo, checked out at
T416's tip) — **outside the repository**, as T422's brief requires, so
`guard_no_narrow_catch_in_capture_rigs`'s recursive walk cannot see it.

Honesty convention: every material claim below is marked `[VERIFIED: …]` with the command or source
that produced it, or `[UNVERIFIED]`. Nothing here is inherited from T416's handoff without being
re-run.

---

## 1. F-T405-5 — THE MONEY VERDICT SENTENCE. CAUSE RE-DERIVED INDEPENDENTLY.

### 1.1 The cause, derived from source before reading T416's account of it

`ExitCode()` is `nexus/internal/apps/loanschedule/conformance/grade.go:288`. On `main` it reaches 1
through **two** structurally separate arms [VERIFIED: `grade.go:289-302` on `main`]:

```go
if s.ParityFail+s.ContractFail+s.SelfTestFail > 0 || s.InvariantViolations > 0 { return 1 }
...
if s.Ledger != nil {
    if s.Ledger.ParityFail+s.Ledger.RefusalFail > 0 || s.Ledger.InvariantViolations > 0 { return 1 }
```

The exit-1 verdict sentence on `main` is `report.go:621-622` and reads **only the first arm's
fields** [VERIFIED: `main:report.go:620-622`]:

```go
case code == 1:
    p("VERDICT: FAIL (exit 1) — %d mismatched vector(s), %d invariant violation(s).",
        s.ParityFail+s.ContractFail+s.SelfTestFail, s.InvariantViolations)
```

`s.Ledger.ParityFail`, `s.Ledger.RefusalFail` and `s.Ledger.InvariantViolations` contribute to none
of those four terms, and nothing else in the arm mentions the ledger. So any run reaching exit 1
**solely** through the ledger arm printed `— 0 mismatched vector(s), 0 invariant violation(s)`.
**T416's stated cause is correct and I re-derived it from the two files without using its account.**

### 1.2 The `:595` / `:592` line-number adjudication — CONFIRMED

`[VERIFIED: git show f952b5d2^:nexus/internal/apps/loanschedule/conformance/report.go]` — on
**pre-T397** `main` (T397 is `f952b5d2`):

| line | content |
|---|---|
| **592** | `p("         This means \"matches the reference oracle …\")` — the **exit-0** prose line, which is what T397 was tasked with and what T397 fixed |
| **594** | `case code == 1:` |
| **595** | the defective `VERDICT: FAIL (exit 1) — %d mismatched vector(s)…` sentence |

So the defect site is `:595`, not `:592`, on the tree those numbers were taken from, and T398's
attachment of the symptom to `:592` was wrong. **T405's correction and T416's confirmation of it both
hold.** T416 additionally declines to hard-code the number in the code comment and cites the site by
name (`the case code == 1: arm of WriteReport's verdict switch`) — correct, because on **today's**
`main` the same line is `:621-622`, i.e. the number has already moved twice
[VERIFIED: `main:report.go:620-622`]. Nothing in the T416 diff cites a line number that has rotted.

### 1.3 The corpus drive, re-run from scratch

Two binaries built by me in `/tmp/t422/t416`, differing **only** in `report.go`
(`/tmp/t422/conf-after` from T416's tip; `/tmp/t422/conf-before` from the same tree with
`git checkout main -- …/report.go` and nothing else — `git status --porcelain` showed exactly that
one file modified, and the tree was restored clean afterwards). Correct `ledger-go` port, **no
`-ledger-impl` flag**, `-oracle-probe=up`. Script: `/tmp/t422/drive.sh`. Store reverted with
`git checkout -- .softhouse/vectors` between arms; `store clean: 0 dirty` at the end.

**Unmutated control — both binaries green** `[VERIFIED: /tmp/t422/out/control-{BEFORE,AFTER}.log]`:

```
BEFORE  exit=0   ledger parity PASS 10 FAIL 0  | VERDICT: PASS (exit 0) — 46 parity vectors …, 7884 cells compared.
AFTER   exit=0   ledger parity PASS 10 FAIL 0  | VERDICT: PASS (exit 0) — 46 parity vectors …, 7884 cells compared.
```

**T416's three mutation classes, reproduced exactly** `[VERIFIED: /tmp/t422/out/{glcode,amountminor,totals}-{BEFORE,AFTER}.log]`:

| mutated cell | class | ledger census | BEFORE | AFTER |
|---|---|---|---|---|
| `legs[0].gl_account_code` 10300→10399 | structural | `parity PASS 9 FAIL 1` | `exit 1 — 0 mismatched vector(s)` | `exit 1 — 1 mismatched vector(s)` |
| `legs[0].amount_minor` 10000025→10000026 | **MONEY, −1 minor unit** | `parity PASS 9 FAIL 1` | `exit 1 — 0 mismatched vector(s)` | `exit 1 — 1 mismatched vector(s)` |
| `total_debits_minor` 12500062→12500063 | **MONEY, −1 minor unit** | `parity PASS 9 FAIL 1` | `exit 1 — 0 mismatched vector(s)` | `exit 1 — 1 mismatched vector(s)` |

The AFTER report on the money arm names the cell with its margin
`[VERIFIED: /tmp/t422/out/amountminor-AFTER.log]`:

```
LDG-01-manual-je-3leg-minor-units   parity   ledger_rest_posting   FAIL   18 cells (5 money)
    legs[0].amount_minor: MONEY want 10000026, got 10000025 (margin -1 minor units)
```

T416's post-merge census figures (`PASS 9 FAIL 1`, control `PASS 10 FAIL 0`) reproduce exactly.

### 1.4 THE CENTRAL CHECK — IS THE COUNT RIGHT, OR MERELY NON-ZERO?

This is the check T422 exists to perform, and T416 did **not** perform it: every one of its corpus
arms mutates exactly one vector, so "1" is indistinguishable from a hard-coded 1 or from `min(n,1)`.
I mutated **two** and then **three** money cells in **distinct** vectors, one minor unit each
`[VERIFIED: /tmp/t422/drive.sh PART B, /tmp/t422/out/{two_money,three_money}-{BEFORE,AFTER}.log]`:

| mutation | true count | census | BEFORE says | AFTER says |
|---|---|---|---|---|
| `LDG-01.legs[0].amount_minor` +1 | 1 | `ledger parity PASS 9 FAIL 1` | `0` | **`1`** |
| + `LDG-02.legs[0].amount_minor` 27045058→27045059 | 2 | `ledger parity PASS 8 FAIL 2` | `0` | **`2`** |
| + `LDG-03.legs[0].amount_minor` 88954942→88954943 | 3 | `ledger parity PASS 7 FAIL 3` | `0` | **`3`** |

and the per-vector rows in the n=3 report name all three
`[VERIFIED: /tmp/t422/out/three_money-AFTER.log]`:

```
LDG-01-manual-je-3leg-minor-units        parity  ledger_rest_posting  FAIL  18 cells (5 money)
LDG-02-repayment-split-4leg-minor-units  parity  ledger_rest_posting  FAIL  23 cells (6 money)
LDG-03-overpayment-4leg-minor-units      parity  ledger_rest_posting  FAIL  23 cells (6 money)
ledger parity           PASS 7    FAIL 3
```

**The reported count equals the true count at n = 1, 2 and 3, and equals the census's own
`FAIL` figure in each case. It is not merely non-zero.**

### 1.5 The ADDS-not-REPLACES claim, checked at CORPUS level as well as unit level

T416's control for "adds rather than replaces" is four loanschedule-only **unit** arms. That is a
weaker control than it sounds, because those arms construct a `Summary` by hand. I drove it on the
**real corpus** instead `[VERIFIED: /tmp/t422/mixed2.sh, /tmp/t422/out/{lsonly2,mixed2,noledger2}-*.log]`.

To produce a genuine loanschedule parity FAIL I had to mutate `P-00.expect.periods[1]` **consistently**
— `interest_minor`, `interest_major_text`, `observed_total_due_minor` and
`observed_total_interest_minor` together. My first attempt moved only `interest_minor` and the
harness correctly refused it as **INADMISSIBLE**, not FAIL:
`expect.periods[1].interest_minor is 59 minor units but the oracle's wire text "0.58" converts to 58:
a transcription error` `[VERIFIED: /tmp/t422/out/lsonly-AFTER.log]`. That is an unlooked-for but real
piece of evidence that the loanschedule admission path is doing its job, and it is recorded here
because it changed my method.

| arm | true state | BEFORE | AFTER |
|---|---|---|---|
| **A** loanschedule-only, 1 vector | LS 1 mismatch + 1 invariant, LEDGER 0 | `— 1 mismatched vector(s), 1 invariant violation(s).` | `— 1 mismatched vector(s), 1 invariant violation(s).`<br>`LEDGER 0 mismatch(es), 0 invariant violation(s) \| LOAN SCHEDULE 1 mismatch(es), 1 invariant violation(s).` |
| **B** MIXED: 1 loanschedule + 2 ledger | LS 1 + LEDGER 2 = **3** | `— 1 mismatched vector(s)` ← **undercount by 2** | `— 3 mismatched vector(s), 1 invariant violation(s).`<br>`LEDGER 2 mismatch(es), 0 invariant violation(s) \| LOAN SCHEDULE 1 mismatch(es), 1 invariant violation(s).` |
| **C** 2 loanschedule, `-context=loanschedule` (no ledger half) | LS 2, ledger absent | `— 2 mismatched vector(s), 2 invariant violation(s).` | `— 2 mismatched vector(s), 2 invariant violation(s).`<br>`no ledger half ran in this configuration, so this counts LOAN SCHEDULE only.` |

**Arm A is the control T416's unit arms were reaching for and it holds on the real corpus: the
loanschedule figure is byte-identical BEFORE and AFTER, so the ledger figures were ADDED, not
substituted.** Arm B is the arm nobody drove: the total is the **sum** of both halves and the split
line attributes each to the correct half, including the invariant-violation column
(`LS 1, LEDGER 0`). Arm C confirms the nil-ledger branch prints the "did not run" sentence rather
than a silent zero, and does not change the loanschedule count.

**No defect found in this area.** The count is right at every n I could construct, the split is
right, and the nil case is distinguished from the zero case.
