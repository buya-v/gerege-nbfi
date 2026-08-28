# T406 — INDEPENDENT REVIEW OF T391 (THE ACCRUAL PROMOTION)

**VERDICT: `APPROVED WITH CONDITIONS`.**

Six conditions, all **MINOR**, each drivable, **none blocking the merge**. Nothing in the
money, the non-vacuity, the pins or the merge result is wrong. Every promoted value was
re-derived from the **live oracle by T406** and matched, cell for cell, with **zero
mismatches**. Both halves of the non-vacuity drive were **re-run by T406, not accepted from
T391's transcript**, and both reproduced. The merge onto current `main` is clean and its bar
is `exit 0` with the probe line present.

The conditions are all in the class T391 itself spent §5 policing in others: **a synthesised
provenance timestamp, a mis-attached source citation propagated seven times, two false
illustrative sentences inside promoted vectors, and two claims that are true but that the
corpus does not demonstrate** — including, awkwardly, T391's own new admission rules, which
ship with no drive at all while their own header invokes P-45.

---

## 0. WHEN I OBSERVED, AND AGAINST WHAT

The oracle **edits itself**, so every measurement below carries its instant.

| | |
|---|---|
| review branch | `softhouse/T406-review-t391` |
| T391 branch tip reviewed | `6f948940` (`softhouse/T391-accrual-promotion`) |
| `main` at the merge test | **`daf8e6fb`** — `main` moved **twice** while I worked (`b00b1959` → `cbcafcfe` → `8ae56886` → `daf8e6fb`) |
| merge commit produced | `2d81228f` (scratch worktree `/tmp/t406-merge`, **never pushed to `main`**) |
| host/container UTC at review | `2026-08-28T18:02Z` … `2026-08-28T18:16Z` = `2026-08-29 02:02…02:16 +08` Asia/Ulaanbaatar |
| oracle health | `{"status":"UP"}` at `https://localhost:8443/fineract-provider/actuator/health` |
| database | PostgreSQL 18.3, container `fineract-db-1`, `fineract_gerege`, tenant `gerege` |
| oracle counters at review | `m_portfolio_command_source` **379/379**, `acc_gl_journal_entry` **109/113**, `m_loan_transaction` **24/34** — identical to T391's post-scheduler figures, so **nothing moved between T391 and this review** |

Everything I quote as measured came from a `GET` I issued myself or a `SELECT` I ran myself.
I read T391's committed capture bodies **only to compare them against my own fetch**, never as
evidence.

---

## 1. EVERY PROMOTED VALUE, RE-DERIVED FROM THE LIVE ORACLE — **0 MISMATCHES**

`obs/decode.py`, `obs/crosscheck.py`, `obs/R01…R06`.

I fetched `GET /journalentries?transactionId={L29,L30,L32}&transactionDetails=true` myself
(HTTP 200 each) and read them with `parse_float=str` / `parse_int=str`, then converted to minor
units by **integer string surgery on the two decimal places** — never a multiplication, never a
float. Independently I ran a read-only `SELECT` over `acc_gl_journal_entry` and
`acc_product_mapping`.

### The re-derivation

```
L29  je 78 gl41 T388-1200 DEBIT  "24000.000000" -> 2400000
     je 79 gl37 T388-4000 CREDIT "24000.000000" -> 2400000
     je 80 gl38 T388-4100 CREDIT  "2500.000000" ->  250000
     je 81 gl42 T388-1300 DEBIT   "2500.000000" ->  250000
     je 82 gl39 T388-4200 CREDIT  "1200.000000" ->  120000
     je 83 gl43 T388-1400 DEBIT   "1200.000000" ->  120000
     debits 2770000 == credits 2770000                       BALANCED

L30  je 84/85 gl41/gl37 "20195.380000" -> 2019538   (residue 38)
     je 86/87 gl38/gl42  "2500.000000" ->  250000
     je 88/89 gl39/gl43  "1200.000000" ->  120000
     debits 2389538 == credits 2389538                       BALANCED

L32  je 96/97 gl41/gl37 "12356.340000" -> 1235634   (residue 34)
     je 98/99 gl38/gl42  "2500.000000" ->  250000
     je100/101 gl39/gl43 "1200.000000" ->  120000
     debits 1605634 == credits 1605634                       BALANCED
```

Every one of the 24 money cells, every `gl_account_id`, every `gl_account_code`, every
`entry_side`, both totals, `manualEntry false`, `transactionType.id 10` (Accrual), the leg
ORDER, and the entry-level `slot_code == 0` were compared against the vectors mechanically:

```
T406 CROSS-CHECK MISMATCHES: 0
```

The slot **names** in my checker were **hand-transcribed from the pinned Fineract source**
(`AccountingConstants.AccrualAccountsForLoan`, `426a23544`, lines 95–122), not read from the Go
port — so the `slot_name` cells are graded against Java, not against the thing they grade.

### The provenance is real, not stale

* both digests on all three vectors **MATCH** their cited artefacts;
* the rig `MANIFEST.sha256` verifies, **82 files, 0 FAILED**;
* the committed capture bodies' graded projection is **identical to my own live fetch today** —
  so the artefact is a live snapshot, not a stale one.

### The "taken 2026-08-29, post-scheduler, live" claim: **TRUE, with one caveat**

The digest-pinned `.http` records carry `captured-at-utc` from **`2026-08-28T17:09:25Z` to
`17:53:37Z`** — i.e. `2026-08-29 01:09…01:53 +08` Ulaanbaatar, and **68 to 112 minutes AFTER**
the scheduler run I re-measured at `job_run_history` `2026-08-28 16:01:00.049 → .120`. So
**post-scheduler and live: confirmed.** The caveat is F-T406-1.

### The scheduler story reproduces exactly

```
job 22  Add Accrual Transactions For Loans With Income Posted As Transactions  16:01:00.002 -> .030
job  9  Update Accounting Running Balances                                     16:01:00.003 -> .048
job 11  Add Accrual Transactions                                               16:01:00.049 -> .120   <-- contains .100 .. .117
job 16  Add Periodic Accrual Transactions                                      16:02:00.002 -> .035
```

Journal entries 96–113 carry `created_on_utc` `.100`…`.117`, `created_by 2` (system), and
`m_portfolio_command_source` never moved. T391's interval argument is sound, and its statement
that it is **an interval argument and not evidence about job wiring** is the correct scoping —
no vector asserts it.

T391's corrections of the driver's own figures are also **CONFIRMED** by me:
`31 of 41` jobs `is_active = t` (not 19), and **281** base tables in `public` (not 280).

And its §10.5 DEC-2 I-5 measurement reproduces character for character:

```
modified/total  ALL 91/109   id<=75 71/71   76-95 20/20   96-113 0/18
```

The universality premise I-5 rests on **is now false**, and routing it as a `user` gate rather
than editing ratified DEC-2 was correct.

---

## 2. FLOAT SWEEP — **CLEAN**

`obs/floatsweep.sh`, `obs/R07`.

I swept the entire 6,909-line diff, not just the Go.

| sweep | result |
|---|---|
| added **non-comment** lines matching `float64\|float32\|big.Float\|strconv.ParseFloat\|FormatFloat\|%f\|Double\|math.Round` | **no hits** |
| all 36 added lines containing `float` (any case) | every one is either prose or `json.load(..., parse_float=str, parse_int=str)` |
| added non-comment lines in the four touched Go files containing `/`, `* <digit>` or e-notation | **none** (the only hits are slot names inside a string literal: `INTEREST_RECEIVABLE/FEES_RECEIVABLE/…`) |
| the three vectors parsed with Python's **default** decoder (a bare JSON number would become a `float`) | **0 float-typed JSON numbers**; every money field is a JSON **string** |
| third-decimal check on every amount token | `1200.000000`, `2500.000000`, `12356.340000`, `20195.380000`, `24000.000000` — **all zero beyond 2dp** |

My own converter **raises** on a non-zero third decimal and never fired. So the residues 38 and
34 are genuine **integer minor units**, not rounding artefacts, and **this is correctly not a
precision claim**: at `(19, HALF_UP)` or at 12, these six integers are the same. T391 said so in
every vector and it is right.

---

## 3. DOES IT GRADE THE SLOT, OR THE ACCOUNT? — **THE SLOT, GENUINELY**

**The legs really carry no account id.** All 18 request legs across the three vectors have
`gl_account_id: 0` and a non-zero `slot_code`; `admit.go` refuses a leg carrying both (I drove
that refusal, §7). The request carries product 63's **complete thirteen-row** mapping, which I
verified equals the **live** `acc_product_mapping` row for row.

**The resolution is genuinely the port's work.** `resolveLegAccount` (impl.go) builds a
`ledger.Resolver` over `ledger.InMemoryMappingStore` / `ledger.InMemoryAccountStore` from the
vector's transcribed rows and calls `ResolveLoanProductAccount`; the name comes from
`ledger.AccrualLoanSlotFromCode(...).Name()` in `nexus/internal/apps/ledger/slots.go`. Nothing
in the harness re-implements a mapping lookup, and on the `SlotCode != 0` path the leg's
`AccountID` is **never read**. No smuggling.

**The T242 trap is live and the vectors dodge it.** Measured by me today:

```
gl 16 -> 21 journal entries;  gl 18 -> 0;  gl 22 -> 0
gl 16 is FUND_SOURCE (slot 1) on TEN CASH products (accounting_type 2):
        22, 23, 27, 46, 54, 55, 56, 57, 58, 60
   and PENALTIES_RECEIVABLE (slot 9) on ACCRUAL product 28 (which has zero loans)
```

One account, two slots — exactly the shape that made the harness print "gl 18, 22 and 16 carry
ZERO journal entries" for four fires. An account-level assertion would have been moved by the
overnight scheduler run; a slot-level one was not.

**The decode really is unambiguous here**, and I checked rather than assumed: product 63 has
`13 rows / 13 distinct accounts / 13 distinct slots` (a bijection) and **zero** other products
map any of accounts 35–47.

**But one half of the claim is not demonstrated by the corpus** — see F-T406-6.

---

## 4. NON-VACUITY — **BOTH HALVES RE-RUN BY T406, BOTH REPRODUCE**

### 4a. THE RED HALF, RE-DRIVEN RATHER THAN READ (`obs/R16`)

I did not accept T391's `3fa91e44` transcript. I withheld the three vectors from T391's own
tree and ran the kill test myself:

```
--- FAIL: TestEveryWrongImplementationIsKilled
    WRONG IMPLEMENTATION "ledger-wrong-slot-family-blind" SURVIVES THE COMMITTED CORPUS.
    14 registered wrong implementations, all 14 killed by the committed corpus
```

Restoring the three vectors, the same test is `ok`. **The claim holds: the corpus without them
cannot see this port.**

### 4b. THE GREEN HALF, AND IT DIES FOR EXACTLY ONE REASON (`obs/R08`)

```
-ledger-impl ledger-wrong-slot-family-blind, FULL committed corpus
    ledger parity PASS 7 FAIL 3 · inadmissible 0 · harness errors 0 · exit 1
```

The **entire** set of cell diffs in that run — I counted every `want … got` line in the whole
output — is **nine lines, and all nine are `slot_name`**:

```
legs[0].slot_name: want "INTEREST_RECEIVABLE",  got "CashAccountsForLoan(7)"
legs[3].slot_name: want "FEES_RECEIVABLE",      got "CashAccountsForLoan(8)"
legs[5].slot_name: want "PENALTIES_RECEIVABLE", got "CashAccountsForLoan(9)"
                                                    x3 vectors, and NOTHING ELSE
```

Every `gl_account_id`, every `gl_account_code`, every `entry_side` and **all 24 money cells are
CORRECT** under it. All seven pre-T391 parity vectors PASS, all six refusals PASS, the
divergence vector PASSes. **This is the measurement of the claim, and it survives.**

I also verified the source claim against the pinned oracle myself:
`CashAccountsForLoan` has **no 7, 8 or 9** and carries `FEES_RECEIVABLE(25)` /
`PENALTIES_RECEIVABLE(26)`; `AccrualAccountsForLoan` has 7/8/9 with the receivable names. True
— but cited from the wrong lines (F-T406-3).

### 4c. THE OTHER 14 STILL DIE, AND **NONE DIED FOR A NEW REASON** (`obs/R09`, `obs/R10`)

I built the harness from **both** trees and ran **every** registered wrong implementation on
**each**, then diffed the failure signatures.

```
MAIN wrong impls: 14      T391 wrong impls: 15      NEW: + ledger-wrong-slot-family-blind
```

Restricting to the pre-T391 vectors and diffing the **reason lines themselves**:

```
IDENTICAL  ledger-wrong-accounting-closed-echoes-transaction-date   (3)
IDENTICAL  ledger-wrong-closure-boundary-exclusive                  (7)
IDENTICAL  ledger-wrong-code-ignored                               (27)
IDENTICAL  ledger-wrong-date-rules-always-refusing                  (4)
IDENTICAL  ledger-wrong-future-date-ignored                         (7)
IDENTICAL  ledger-wrong-header-refusing                             (3)
IDENTICAL  ledger-wrong-manual-permission-ignored                   (6)
IDENTICAL  ledger-wrong-netting-totals                             (16)
IDENTICAL  ledger-wrong-openingbalance-always-refusing              (3)
IDENTICAL  ledger-wrong-openingbalance-no-contra                   (13)
IDENTICAL  ledger-wrong-openingbalance-posted-entries-ignored       (4)
IDENTICAL  ledger-wrong-residue-rounding                            (4)
IDENTICAL  ledger-wrong-split-drift                                 (6)
IDENTICAL  ledger-wrong-truncating                                 (44)
```

**Not one verdict and not one reason changed on any pre-existing vector.** The only movement is
the three new vectors' own verdicts.

### 4d. THE DECLARED SECONDARY KILLS, RE-MEASURED

| declared by T391 | measured by T406 |
|---|---|
| `ledger-wrong-truncating` now fails **9**, up from 7, and **does not die on LDG-ACC-01** | **CONFIRMED** — `PASS 1 FAIL 9`; the one PASS is LDG-ACC-01 |
| margins **−38** on ACC-02 and **−34** on ACC-03 | **CONFIRMED**, verbatim: `MONEY want 2019538, got 2019500 (margin -38 minor units)` and `want 1235634, got 1235600 (margin -34)` |
| `ledger-wrong-netting-totals` a **money** kill with margin −2770000 on ACC-01, where LDG-01 calls it structural/0 | **CONFIRMED**: `total_debits_minor: MONEY want 2770000, got 0 (margin -2770000)`. **T391's label is the correct one and LDG-01's is the weaker of two descriptions of one behaviour.** Declaring the discrepancy rather than silently re-labelling LDG-01 was right |
| `ledger-wrong-netting-totals` and `ledger-wrong-code-ignored` fail all 10 | **CONFIRMED** |

**LDG-ACC-01's `graded_against` correctly does NOT claim the truncating kill.** That is the
honest thing to do and T391 did it.

---

## 5. THE THREE PIN MOVES — **REGENERATED BY RUNNING, IN ONE COMMIT, BY NAME**

### Values confirmed by RUNNING on the MERGE RESULT, not by arithmetic (P-83)

```
conformance:   exemption census READ: LEDGER parity vectors        = 10 == pinned 10
conformance:   exemption census READ: LEDGER money cells compared  = 63 == pinned 63
conformance:   exemption census READ: LEDGER oracle-refusal vector = 6  == pinned 6
conformance:   exemption census READ: LEDGER declared exemptions   = 0  == pinned 0
conformance: CENSUS wrong ledger implementations — discovered 15 registered as DELIBERATELY
conformance:   WRONG from the binary's own -list-implementations; pinned at 15.
conformance:   all 15 wrong ledger implementations DIED through this harness, not by hand.
```

### One commit (P-83)

`git show 25a8b7de` carries **all five** restatements together with the vectors and the wrong
implementation: `EXEMPTION_PIN_LEDGER_PARITY 7→10`, `EXEMPTION_PIN_LEDGER_MONEYCELLS 39→63`,
`EXEMPTION_PIN_LEDGER_WRONGIMPLS 14→15` in `conformance.sh`, and `ParityPass 7→10` (two sites)
plus `MoneyCells 39→63` in `divergence_test.go`. `DivergencePinCount` did not move and is still
1, correctly.

### By NAME, not by line

The `conformance.sh` diff is exactly **3 insertions, 3 deletions**, each an anchored
`^SYMBOL=value$` replacement with the surrounding comment blocks untouched.
`EXEMPTION_PIN_LEDGER_REFUSAL` (6) and `EXEMPTION_PIN_LEDGER_DECLARED` (0) are untouched, and no
registration-guard region was read or reflowed.

**One correction to the brief, for the record.** The brief says
`EXEMPTION_PIN_LEDGER_WRONGIMPLS` "moved to `conformance.sh:4551` under T404". **T404 is not
merged**; on `main` today the symbol is at **`:4476`**, and on the merge result it is still at
`:4476`. So a by-line patch would *not* have hit an unrelated line **on this merge** — but it
would on a later merge with T404, and T391's by-name approach is correct regardless and needs no
resequencing now.

---

## 6. THE SECOND CONTENTION (T397) — **NO CONFLICT, MERGE-RESULT BAR GREEN**

Merged `softhouse/T391-accrual-promotion` onto **`main` at `daf8e6fb`** in the scratch worktree
`/tmp/t406-merge` → merge commit `2d81228f`. **`main` was never touched.**

```
git merge --no-edit softhouse/T391-accrual-promotion    -> clean, NO CONFLICT
git status --porcelain                                   -> EMPTY
```

Both changes are present and are at distant, non-interacting regions of `admit.go`:

* **T391** at `:990` — `if l.SlotCode == 0 && !chart[l.AccountID]`
* **T397** at `:1339–:1480` — the token-bounded `verbatimInCapture` / `tokenBoundedIndex`

T391 did **not** touch `verbatimInCapture` and did **not** touch `report.go`, as declared.

**The interaction that actually mattered** — whether T397's *token-bounded* matcher would now
refuse T391's amounts — I tested **directly** as well as through the bar. Every amount token in
every ACC vector occurs in its cited artefact **token-bounded**, not merely as a bare substring:

```
24000.000000 / 20195.380000 / 12356.340000 / 2500.000000 / 1200.000000
    bare_substring=True    token_bounded=True     (all nine, all three vectors)
```

### THE BAR ON THE MERGE RESULT

```
bash .softhouse/conformance.sh          -> EXIT 0
grep -c 'probe = '                      -> 1        (P-84: PRESENCE before value)
conformance: reference oracle (https://localhost:8443/.../actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
    ledger parity PASS 10 FAIL 0 · oracle-refusal PASS 6 FAIL 0 · inadmissible 0 · harness errors 0
    divergence PASS 1 FAIL 0 · loanschedule PASS 46 / 7,884 cells · deadOccurrences 108
    8 SLOT product … lines printed (3 on product 28, 5 on product 63)
```

`bash`, never `sh`; from a clean tree; probe presence tested before value. Full transcript at
`obs/R11-merge-result-bar.txt`.

---

## 7. NO ORACLE STATE MOVED — **CONFIRMED**, AND DECLINING WAS RIGHT

**T391 moved nothing, and I verified this structurally rather than on its word:**

* `capget.sh` has no method parameter and hard-codes `curl … -X GET`. A grep of the whole rig
  for `-X POST|-X PUT|-X DELETE|--data|-d @` returns **nothing**. The only other `curl` in the
  rig is a health probe.
* `capsql-readonly.sh` scans the executable text and exits 2 before `psql` is invoked.
* Live counters today are **identical** to T391's post-scheduler figures: command source
  **379/379**, journal entries **109/113**, loan transactions **24/34**. **Not one row moved.**
* No promoted account moved: gl 41/42/43 and 37/38/39 carry exactly the six legs each that the
  vectors assert, gl 18 and gl 22 still 0, gl 16 still 21, gl 40/44/45/46/47 still 0.

**Declining to post the five remaining accrual slots was RIGHT, and for a better reason than
T391 gives.** Its stated reason (T388's 20 command-source rows are still unattributed in
`PROBES.tsv`, and T390 owns that) is sound on its own. But the *stronger* reason is the one
T391's own §1a(2) argues: **each of those five is a MOVE OF SHARED STATE that buys nothing this
task's vectors needed**, and a task that moves the oracle to widen coverage it will not promote
in the same fire has converted a review problem into a casualty-sweep problem. Declaring them
so the harness prints the gap on **every run** is strictly better than a sentence in a handoff
— and I confirmed the harness does print all eight SLOT lines on the merge result. This is the
right call and should not be re-litigated.

---

## 8. THE `capabilities-ledger.json` REWRITE — **THE ROW NOW TELLS THE TRUTH**

I re-measured **every** re-measurable claim in the rewritten rows, live:

| claim | measured by T406 |
|---|---|
| TWO `ACCRUAL_PERIODIC` products, 28 (0 loans) and 63 (1 loan) | **TRUE** |
| **EIGHTEEN** journal entries through a receivable slot, six each through 7/8/9, all product 63 | **TRUE** |
| gl 18 → 0, gl 22 → 0, gl 16 → **21** on the ACCOUNT and **0** through product 28 | **TRUE** |
| gl 16 is FUND_SOURCE (slot 1) on **TEN** cash products: 22, 23, 27, 46, 54, 55, 56, 57, 58, 60 | **TRUE, and the row lists exactly the right ten** |
| product 63's five unposted slots 6/10/11/12/13 → gl 40/44/45/46/47, all reading zero | **TRUE** |
| product 63 has **no** payment-channel / fee / penalty mappings, so STEP 2 is never entered | **TRUE** — `0` rows with a non-null `payment_type` or `charge_id` |
| product 63's mapping is a bijection, 13/13/13 | **TRUE** |

**The knowingly-false sentence is NOT a defect, and leaving it was the right call.** Reading the
file rather than the handoff: the retired `"NOT ONE ENTRY IN THIS CORPUS ARRIVED THROUGH A
RECEIVABLE SLOT"` appears **only inside a bracket that opens by declaring it false and spent**,
alongside why it was true on 28 August and what superseded it. It is **quoted as a superseded
recommendation, never asserted**. A reader who meets it in T388's handoff or T389's review can
now find what became of it. Deleting it would have destroyed that trail.

**One nuance the handoff does not state, and a reviewer should.** `ledger.accrual.entry` moved
to `in_graded_domain: true`, and the renderer prints **only** `false` rows — so the four false
sentences stop printing because **the row left the printed set entirely**, not because the
printed text was corrected. That is a fine outcome (the falsehoods no longer print), and T391
**spotted the mirror risk and handled it**: it moved `unposted_slots` onto
`ledger.slot.resolution` precisely so the SLOT measurement keeps printing. The printed
not-graded list correctly shrank from 7 rows to 6. This is careful work and it is the part of
§5 I would most want kept.

`ledger.slot.resolution` **correctly stays `false`**, for a **named, measured** reason (the
payment-type precedence chain, which product 63 structurally cannot exercise) rather than a
vague one. That is the right scoping: the vectors claim `ledger.accrual.entry`, which is what
they exercised, and not `ledger.slot.resolution`, which they did not.

---

## FINDINGS

### F-T406-1 — **MINOR** — `oracle.captured_at` is a SYNTHESISED round hour, ~16 h after the real capture, and still in the future

All three vectors carry:

```json
"oracle": { "captured_at": "2026-08-29T09:00:00Z" }
```

The digest-pinned artefacts they cite carry the **real** instants:

```
T391-A01-je-L29.http   captured-at-utc: 2026-08-28T17:10:23Z
T391-A04-je-L32.http   captured-at-utc: 2026-08-28T17:10:28Z
(the rig's eleven capture timestamps span 2026-08-28T17:09:25Z .. 17:53:37Z)
```

`2026-08-29T09:00:00Z` is **~16 hours after** the capture and was **still in the future** when I
reviewed (host UTC `2026-08-28T18:16Z`). It is not the UTC instant, and it is not the
Ulaanbaatar instant either (`+08` would make the capture `2026-08-29T01:10+08`, i.e.
`09:00 +08` would be sixteen hours late as well). It is a stamped value.

**It also breaks the store's convention.** Every other ledger vector carries a second-precision
real instant (`2026-08-22T02:21:18Z`, `2026-08-23T00:17:56Z`, `2026-08-28T06:59:25Z`, …).
T391's three are the only round-hour values in the store.

Nothing downstream grades this field, no money cell is affected, and the substantive claim
("post-scheduler, live") is **TRUE** — which is why this is MINOR and not MAJOR. But it is the
one field in the provenance block of the program's **first accrual vectors** that is not an
observation while sitting among fields that are.

**DRIVE:** set each vector's `oracle.captured_at` to its own artefact's `captured-at-utc`
(`2026-08-28T17:10:23Z` for LDG-ACC-01, `…:17:10:2xZ` for the others, read from the `.http`
records, which are digest-pinned). Re-run the bar from a clean tree; the value is ungraded so
no pin moves.

---

### F-T406-2 — **MINOR** — T391's own new default-deny admission rules ship with **ZERO drives**

`admit.go` gains **ten** new refusal branches (leg carries both / neither / negative slot code;
slot legs with no mapping table; entry-level `slot_code` set alongside per-leg codes; slot legs
with no `product_id`; a mapping table no leg resolves through; a duplicate `slot_code`; a
non-positive mapping `slot_code`; a mapping row off the chart). **Not one is driven by a test.**
T391's diff touches only `notgraded_test.go` and `divergence_test.go`, and both edits are
re-pointings, not drives.

This contradicts three things T391 itself invokes:

* it explicitly models these rules on **T294's opening-balance inputs**, and
  `openingbalance_test.go` carries **16** `Admit(` drives for exactly that shape;
* its own `capsql-readonly.sh` header invokes **P-45** — *"a guard nobody has watched fail
  enforces nothing"* — and then drives that guard RED;
* the whole registered-wrong-implementation apparatus (**P-10**) exists because a rule nothing
  executes is decoration.

**I drove all ten myself** (`obs/t406_admit_probe_test.go.txt`) and **all ten fire correctly**:

```
=== RUN   TestT406SlotAdmissionBranches
    both id and slot: REFUSED as designed
    neither id nor slot: REFUSED as designed
    negative slot code: REFUSED as designed
    slot legs, no mapping table: REFUSED as designed
    entry-level slot_code set too: REFUSED as designed
    slot legs, no product id: REFUSED as designed
    duplicate slot in mapping table: REFUSED as designed
    mapping row off the chart: REFUSED as designed
    mapping row with slot_code 0: REFUSED as designed
--- PASS
=== RUN   TestT406MappingTableOnAManualVectorIsRefused
    REFUSED as designed
--- PASS
```

So the rules are **CORRECT**. The defect is that **the corpus does not know that**, and the next
refactor of `admit.go` has nothing holding these ten branches in place.

**DRIVE:** commit the test. `obs/t406_admit_probe_test.go.txt` in this review is a working
version against the committed store and can be adopted as-is or rewritten; either way the
condition is "ten branches, ten drives".

---

### F-T406-3 — **MINOR** — a source citation attached to the wrong line range, propagated to **seven** places (five of them committed artefacts)

The claim, repeated across the vectors and the Go:

> *"CashAccountsForLoan has no 7, 8 or 9 at all, and carries the names FEES_RECEIVABLE and
> PENALTIES_RECEIVABLE at 25 and 26 instead [VERIFIED: `AccountingConstants.java:79-89` and
> `:95-122` at `426a23544`]"*

**The substance is TRUE — I verified it at the pinned sha.** The *range* is wrong. At
`426a23544`:

```
:37-62    public enum CashAccountsForLoan { ... FEES_RECEIVABLE(25), PENALTIES_RECEIVABLE(26) }   <-- the constants
:79-89    private static final Map<...> intToEnumMap ... public static CashAccountsForLoan fromInt(int i)
:95-122   public enum AccrualAccountsForLoan { ... INTEREST_RECEIVABLE(7), FEES_RECEIVABLE(8), PENALTIES_RECEIVABLE(9) }   <-- correct
```

`:79-89` is the `intToEnumMap` / `fromInt` block and **contains no enum constant at all**. The
second half of the pair (`:95-122`) is correct.

**Where it came from, which is why this is easy to fix and easy to repeat.** `slots.go:170`
already carried `[VERIFIED: AccountingConstants.java:79-89 ...]` — and **there it is correct**,
because it cites `CashAccountsForLoan.fromInt`. T391 copied the range and re-attached it to a
claim about the constants.

Occurrences (`git grep 'AccountingConstants.java:79-89' softhouse/T391-accrual-promotion`):

```
.softhouse/vectors/ledger/LDG-ACC-01…03*.json        (3 promoted vectors, in _note)
nexus/internal/apps/ledger/conformance/impl.go:1384  (slotFamilyBlindPoster doc)
nexus/internal/apps/ledger/conformance/vector.go:685 (ExpectLeg.SlotName doc)
.softhouse/handoff/T391-accrual-promotion.md:228
.softhouse/capture/t391-accrual-promotion/bin/50-emit-vectors.py:236
nexus/internal/apps/ledger/slots.go:170              (PRE-EXISTING and CORRECT — do not touch)
```

**DRIVE:** in the five T391-authored places, change the first range to **`:38-61`** (or
`:37-62`) and leave `:95-122` and `slots.go:170` alone. `50-emit-vectors.py` and the rig
`MANIFEST.sha256` move together if the emitter is corrected.

---

### F-T406-4 — **MINOR** — a false illustrative sentence in two promoted vectors (copy-paste)

`LDG-ACC-02` and `LDG-ACC-03` both carry, in `provenance.citation`:

> *"the `amount` tokens are **20195.380000**, … — scale 6, exactly as the oracle emitted them;
> a JSON reader that decodes them through a float prints **24000.0** and is not what was read"*

The `24000.0` is LDG-ACC-01's number, left behind by a copy-paste. Measured:

```
float("20195.380000") -> 20195.38      float("12356.340000") -> 12356.34      float("24000.000000") -> 24000.0
```

So the sentence, read as being about *those* tokens, is **false**. It is prose, nothing grades
it, and the point it makes is still correct — but a false sentence inside a promoted vector is
exactly the category T391 spent §5 correcting in others, and a reader checking the claim will
find it does not hold.

**DRIVE:** substitute each vector's own float rendering (`20195.38`, `12356.34`).

---

### F-T406-5 — **MINOR** — "TEN cash products" with an **eleven**-item list, in all three vectors

The `_note` of all three vectors reads:

> *"gl 16 is PENALTIES_RECEIVABLE (slot 9) on accrual product 28 AND FUND_SOURCE (slot 1) on
> **TEN cash products** [re-measured live by T391, out/T391-S01 section 4c: products **22, 23,
> 27, 28, 46, 54, 55, 56, 57, 58, 60**]"*

That list has **eleven** ids and includes **28**, which is the accrual product where gl 16 is
slot 9, not FUND_SOURCE. Measured by me live:

```
gl16 mapped by: 22 23 27 46 54 55 56 57 58 60   (accounting_type 2, slot 1)  = TEN cash products
            and 28                              (accounting_type 3, slot 9)
```

The list is faithfully the eleven rows `T391-S01 §4c` prints, so this is a citation attached to
the wrong clause rather than an invented number — and **`capabilities-ledger.json` states the
same fact correctly**, listing exactly the ten and excluding 28. It reads as a contradiction
inside the vector text, and the vectors are the artefact that outlives the handoff.

**DRIVE:** drop `28` from the bracketed list, or reword to *"[…§4c lists all eleven products
mapping gl 16: the ten cash ones above plus accrual product 28]"*.

---

### F-T406-6 — **MINOR** — the claim that `gl_account_id` / `gl_account_code` are now **OUTPUTS** is TRUE but **not demonstrated by the corpus**

This is the headline structural claim of the promotion, stated in `vector.go`, in `impl.go`, in
all three `_note`s and in the handoff:

> *"a port that resolves slot 8 to the wrong account now differs from the expectation; before
> this field existed it could not, because the vector handed it the answer"*

**No registered wrong implementation exercises it.** I measured the account-id cell diff across
every wrong implementation on both trees:

* `ledger-wrong-slot-family-blind` — the new one — **deliberately gets every account RIGHT**;
  that is its whole point.
* `ledger-wrong-code-ignored` blanks `gl_account_code` on **every** vector, manual ones
  included, so it demonstrates nothing about *resolution*.
* the only `gl_account_id: want … got …` lines anywhere in the matrix come from
  `ledger-wrong-openingbalance-no-contra` on `LDG-05`, a different path.

So `gl_account_id` on an accounting-path leg is graded by **nothing that has ever been watched
to fail** — the same gap `RegisterWrong` / P-10 exist to close, one field over.

**I drove it and the claim is TRUE.** A throwaway
`t406-probe-mapping-first-row` (resolves every accounting-path leg to the **first** mapping
row's account instead of keying by slot — the exact mis-keying `admit.go`'s own comment says
would "fail as a graded cell difference") produces:

```
ledger parity PASS 7 FAIL 3          <-- all seven pre-T391 vectors untouched
LDG-ACC-01/02/03:
  legs[0].gl_account_id:   want 41, got 35        legs[0].gl_account_code: want "T388-1200", got "T388-1000"
  legs[1].gl_account_id:   want 37, got 35        legs[1].gl_account_code: want "T388-4000", got "T388-1000"
  … all six legs, all three vectors — 12 account-id cells and 12 code cells
```

The cells work. The corpus just does not say so.

**DRIVE:** register a sixteenth wrong implementation of this shape and move
`EXEMPTION_PIN_LEDGER_WRONGIMPLS` **15 → 16** *in the same commit* (P-83), regenerating the
value by running the bar. My probe body is at `obs/t406_probe_impl.go.txt` and can be adopted
directly; it needs a real name (`ledger-wrong-mapping-key-ignored`) and a `graded_against` row
on each ACC vector.

---

### INFORMATIONAL — not conditions

* **The printed READ-BUT-NOT-GRADED numeric census moved and the handoff does not say so.** The
  merge-result bar prints `104 of them are NOT byte-preserved`, now including
  `T391-A01-je-L29.json x6`, `T391-A02-je-L30.json x6`, `T391-A04-je-L32.json x6` — i.e. the
  three cited bodies added 18. This is a **READ**, explicitly *"floor DERIVED, not pinned"*, so
  nothing goes red and it is the inherent consequence of citing a scale-6 oracle body (T186 §7
  A4 forbids re-scaling one). Recorded because a figure that moved silently is worth naming.
* **The brief's `conformance.sh:4551` premise is stale** — see §5. T404 is unmerged; the symbol
  is at `:4476` on `main` and on the merge result. No action needed for *this* merge.
* **`T391-A03-je-L31` and `T391-A05/A06`** are captured but not promoted, consistent with
  T391's stated "three of six is the discriminating set". I agree: one round amount, two
  distinct residues, both trigger paths. Promoting all six would triple one shape.

---

## WHAT I DID NOT DO

* **I moved no oracle state.** Eight `GET`s and read-only `SELECT`s only. Counters unchanged.
* **I did not merge to `main`.** The merge test lives in a detached scratch worktree.
* **I did not edit T391's branch or any file outside my grant.** My two probes
  (`t406_probe_impl.go`, `t406_admit_probe_test.go`) were written into a **scratch** worktree,
  run, saved into this review as `.txt`, and **deleted**; that scratch tree is clean.
* **I did not re-litigate DEC-2 I-5.** T391 is right that it has moved again and right that
  amending ratified DEC-2 is a `user` gate.

## EVIDENCE

All under `.softhouse/reviews/t406-review-t391/obs/`:
`R01` live legs · `R02` my own oracle GETs · `R03` re-derivation · `R04` live product-63 mapping
· `R05` counters · `R06` cross-check (0 mismatches) · `R07` float sweep · `R08` slot-family-blind
arm · `R09`+`R10` wrong-implementation signature matrix, both trees · `R11` **merge-result bar
(exit 0)** · `R12` capabilities claims · `R13` provenance/manifest/token-boundary · `R14`
mapping-first-row probe · `R15` DEC-2 I-5 · `R16` **RED half, wrong impl survives** ·
`sig-main/` + `sig-t391/` per-implementation signatures · the scripts that produced them.
