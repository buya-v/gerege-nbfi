# T391 — THE ACCRUAL PROMOTION: three parity vectors, four false sentences repaired, one wrong implementation killed

**Branch:** `softhouse/T391-accrual-promotion`.
**Grant written:** `.softhouse/vectors/`, `.softhouse/capture/t391-accrual-promotion/`,
`.softhouse/conformance.sh` (three pinned-count assignment lines, by name), and
`nexus/internal/apps/ledger/conformance/` — the last is **outside the files_hint and is
declared, not hidden**; see § 8, it collides with T397.
**Fire** `20260828-140005` iteration 4, tenant `gerege`, database `fineract_gerege`,
PostgreSQL 18.3, reference oracle (Fineract) pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb`,
health probed UP.

**NO ENTITY IN THE REFERENCE ORACLE WAS CREATED, MODIFIED OR DELETED BY THIS TASK.** Every
HTTP exchange is a `GET` (`capget.sh` has no method argument — there is nothing to pass it
that would make it POST) and every SQL statement is a `SELECT` (`capsql-readonly.sh` refuses
the file before `psql` is invoked). See § 6 for both guards, including the one that fired on
this task's own file.

---

## 1. THE RESULT IN FIVE LINES

| | before | after |
|---|---|---|
| ledger parity | PASS 7 FAIL 0 | **PASS 10 FAIL 0** |
| ledger oracle-refusal | PASS 6 FAIL 0 | PASS 6 FAIL 0 — unmoved |
| ledger inadmissible | 0 | 0 — unmoved |
| ledger cells / money cells | 144 / 39 | **268 / 63** |
| registered wrong ledger implementations | 14, all killed | **15, all killed** |
| loanschedule | PASS 46, 7,884 cells | PASS 46, 7,884 cells — unmoved |

**THE BRIEF'S BASELINE FIGURE FOR CELLS WAS STALE AND IS CORRECTED HERE.** The brief said
`142 cells / 39 money`. The measured baseline on this worktree's `main` (`1eacb63e`), taken
before any edit, was **144 / 39** — T360's `LDG-DIV-01` added two divergence cells and
`tasks.json`'s own T360 entry already says `cells 142->144`. The parity/refusal/inadmissible
figures in the brief were correct. Baseline transcript: the first run recorded in § 7.

---

## 2. WHAT I MEASURED FROM THE ORACLE — INCLUDING SOMETHING T388 SAID IT COULD NOT

### 2.1 THE SCHEDULED JOB FIRED. T388's capture is now a strict subset of the tenant.

T388's § 8 item 1 named this as the thing it could not capture: *"the SCHEDULED job (id 16)
firing on its own … its next run is `2026-08-28 16:02`; waiting for it was not compatible
with this fire."* **A scheduled job fired at `2026-08-28 16:01:00` and wrote three more
accrual transactions** — `L32`/`L33`/`L34`, loan transactions 32/33/34, journal entries
96–113, **nine more receivable-slot legs**. `m_portfolio_command_source` is **still 379/379**,
identical to T388's after-state, so **no API call produced them**.

**WHICH JOB, and the limit on that claim.** `job_run_history` [`out/T391-S05-job-run-history.txt`]:

| job | window | trigger |
|---|---|---|
| 22 `Add Accrual Transactions For Loans With Income Posted As Transactions` | `16:01:00.002 → .030` | cron |
| **11 `Add Accrual Transactions`** | **`16:01:00.049 → .120`** | **cron** |
| 16 `Add Periodic Accrual Transactions` | `16:02:00.002 → .035` | cron |

The eighteen journal entries carry `created_on_utc` `16:01:00.100` … `.117` — **strictly
inside job 11's window and strictly outside the other two**. **STATED AS A LIMIT AND NOT
PROMOTED AS A CLAIM:** `job` and `job_run_history` record *when* a job ran, not *which rows
it wrote*, and there is no foreign key from a journal entry to a job. This is an interval
argument that eliminates two candidates. **It is not evidence about job wiring and no vector
asserts it.**

Note what this does to T388's own careful sentence. T388 argued `/runaccruals` ≡ job **16**
and refused to call its capture evidence about the scheduler. That refusal was right — and
the job that actually fired was **11**, not 16, so the equivalence T388 established is not
the one that produced `L32`–`L34`.

### 2.2 THE TENANT, RE-MEASURED READ-ONLY

* **EIGHTEEN** journal entries arrived through a RECEIVABLE slot — six through each of slots
  7, 8 and 9, all on product 63 [`out/T391-S01-slot-resolution.txt` §10]. T388 observed nine.
* **TWO** `ACCRUAL_PERIODIC` products: 28 (zero loans) and 63 (one loan) [§9].
* Product 63's mapping is a **BIJECTION** — 13 mappings, 13 distinct accounts, 13 distinct
  slots [§4a] — and **NO OTHER PRODUCT MAPS ANY OF ACCOUNTS 35–47** [§4b, zero rows]. So on
  this product `gl_account_id → financial_account_type` really is a function, checked rather
  than assumed.
* **The T242 trap, live, for contrast** [§4c]: gl 16 is `FUND_SOURCE` (slot 1) on **TEN** cash
  products — 22, 23, 27, 46, 54, 55, 56, 57, 58, 60 — and `PENALTIES_RECEIVABLE` (slot 9) on
  accrual product 28, carrying **21** rows of which **ZERO** arrive through product 28 [§8].
* **Double entry holds in integer minor units on all six accruals**, difference `0`, computed
  by the oracle's own PostgreSQL `numeric` arithmetic [§3 of `T391-S03`]:
  `L29 2770000`, `L30 2389538`, `L31 2001467`, `L32 1605634`, `L33 1201885`, `L34 790061`.
* **NO LEG CARRIES A NON-ZERO THIRD DECIMAL** [`T391-S01` §6, zero rows]. This is why nothing
  here is a precision claim.
* **THE FORBIDDEN SET IS UNMOVED.** `{1,2,4,6,8,10,15,16,17,18,21,22}` read
  `3/3/12/1/2/1/0/21/5/0/13/0` today — identical to T388's after-table. The scheduled run
  touched only 37/38/39/41/42/43.
* **T388's three captured bodies re-issued and BYTE-IDENTICAL** (key-order-normalised only;
  values compared as the oracle's characters, `parse_float=str`, so a scale change would show)
  [`out/T391-03-reissue-vs-t388.txt`, `verdict rc=0`].

---

## 3. WHAT I PROMOTED, AND WHAT IT GRADES

Three `class: parity` vectors under `.softhouse/vectors/ledger/`, each SIX legs across SIX
slots on one journal transaction:

| case_id | txn | how it came to exist | interest leg |
|---|---|---|---|
| `LDG-ACC-01-accrual-six-slots-runaccruals-trigger` | `L29` | hand-fired `POST /v1/runaccruals` (command-source 379) | `24000.000000` — a WHOLE TUGRIK |
| `LDG-ACC-02-accrual-six-slots-minor-unit-residue` | `L30` | the same hand-fired call | `20195.380000` — **38 minor units of residue** |
| `LDG-ACC-03-accrual-six-slots-scheduled-job` | `L32` | **the SCHEDULED job, no API call** | `12356.340000` — **34 minor units, a DIFFERENT residue** |

Legs, in the oracle's own read-back order (stable by journal-entry id): DEBIT slot 7
`INTEREST_RECEIVABLE` → gl 41; CREDIT 3 `INTEREST_ON_LOANS` → 37; CREDIT 4
`INCOME_FROM_FEES` → 38; DEBIT 8 `FEES_RECEIVABLE` → 42; CREDIT 5 `INCOME_FROM_PENALTIES`
→ 39; DEBIT 9 `PENALTIES_RECEIVABLE` → 43.

### THE DECISION: AN ACCRUAL VECTOR GRADES **THE SLOT**, NOT THE ACCOUNT

**Each leg carries a SLOT CODE AND NO ACCOUNT ID.** The request carries product 63's
**complete thirteen-row** `acc_product_mapping` table. `expect.legs[].gl_account_id`,
`expect.legs[].gl_account_code` and the new `expect.legs[].slot_name` are **OUTPUTS** the
implementation must produce by keying that table with the slot code and decoding the code on
the family the product's accounting rule selects.

That is T242's correction (A2-34 F-4) built into the schema instead of written in prose. A
vector that graded the ACCOUNT would reproduce exactly the error the harness printed every
run for four fires: *"gl 18, 22 and 16 carry ZERO journal entries"* while gl 16 had sixteen.

**Non-circularity, the same argument the money cells rest on.** The vector supplies the
CHARACTERS (the amount) and the CODE (the slot); the implementation supplies the INTEGER and
the NAME and the RESOLVED ACCOUNT. `slot_code` is deliberately **not** graded — grading the
input would be grading the vector against itself.

**Why the decode is unambiguous here**, checked and not assumed: the bijection and the
no-shared-account result in § 2.2. That is a property of how T388 built the product, not of
Fineract, and it is why the accounts were created clean.

### THE SCHEMA FIELDS, POPULATED FOR THE FIRST TIME

| field | file | what it is |
|---|---|---|
| `RequestLeg.SlotCode` | `vector.go` | the slot PER LEG. `Request.SlotCode` names ONE slot and an accrual transaction spans SIX — the exact obstruction `capabilities-ledger.json`'s `ledger.slot.resolution` row already named. Kept, unrepurposed, and required to be 0 where per-leg codes are used |
| `Request.ProductMappings` | `vector.go` | the product's OBSERVED mapping table. The WHOLE table, not the six rows the answer needs — a table containing only the rows the answer needs is not a lookup, it is the answer |
| `ExpectLeg.SlotName` | `vector.go` | **the graded slot cell**, compared on EVERY leg of EVERY parity vector. `""` on a manual leg is an ASSERTION that no slot took part, not an ungraded blank |
| `PostedLeg.SlotName` | `impl.go` | the implementation's answer |

Resolution uses **the port's own `ledger.Resolver`** over `ledger.InMemoryMappingStore` and
`ledger.InMemoryAccountStore`, for the reason `GoPoster`'s own doc comment gives about the
arithmetic: a resolver living inside the harness would be a resolver grading resolvers.
Nothing in the harness re-implements a mapping lookup.

**Admissibility, default-deny in both directions** (`admit.go`): a leg carries an account id
**or** a slot code and never both (both would hand the implementation the answer) and never
neither; a slot code with no mapping table REFUSES; a mapping table no leg resolves through
REFUSES; the entry-level `slot_code` must be 0 where per-leg codes are used; every mapping
row's account must be in the chart, so a **mis-keying** port lands on a real account and fails
as a **graded cell difference** rather than as a harness crash; a duplicate `slot_code`
REFUSES (the oracle's own lookup is `getSingleResult()`, where a duplicate is an error).

---

## 4. NON-VACUITY — THE FIFTEENTH WRONG IMPLEMENTATION, DRIVEN IN BOTH DIRECTIONS

**`ledger-wrong-slot-family-blind`** — *decodes every placeholder code through
`CashAccountsForLoan` whatever the product's accounting rule says.*

`acc_product_mapping` is keyed on `(product_id, product_type, financial_account_type)` and
**the accounting rule is NOT in the key**, so both loan enums share one integer space. A
porter who keeps a single flat code→name table — the obvious thing to write, because the two
enums agree on nineteen of the codes they share — **resolves the RIGHT ACCOUNT every time and
names the WRONG SLOT** wherever they disagree. `CashAccountsForLoan` has no 7, 8 or 9 at all
[VERIFIED: `AccountingConstants.java:79-89` and `:95-122` at the pinned sha; ported at
`nexus/internal/apps/ledger/slots.go`].

### THE KILL, MEASURED [`out/T391-11-wrongimpl-matrix.txt`]

```
ARM 1  -ledger-impl ledger-wrong-slot-family-blind, FULL committed corpus
       ledger parity PASS 7 FAIL 3 · inadmissible 0 · harness errors 0 · exit 1
       LDG-ACC-01/02/03 FAIL. ALL SEVEN pre-T391 parity vectors PASS.
       All six refusal vectors and the divergence vector PASS.

       legs[0].slot_name: want "INTEREST_RECEIVABLE",  got "CashAccountsForLoan(7)"
       legs[3].slot_name: want "FEES_RECEIVABLE",      got "CashAccountsForLoan(8)"
       legs[5].slot_name: want "PENALTIES_RECEIVABLE", got "CashAccountsForLoan(9)"

ARM 3  -ledger-impl ledger-go   ledger parity PASS 10 FAIL 0 · exit 0
```

**NOTHING ELSE DIFFERS.** Every `gl_account_id`, every `gl_account_code`, every `entry_side`
and every one of the 24 money cells is CORRECT under this port. **That is the measurement of
the claim that the SLOT and the ACCOUNT are different things** — a corpus that graded the
account and not the slot would report this port GREEN, which is exactly the report the harness
printed before T242 corrected it.

### THE WITHHELD-CORPUS DIRECTION, TAKEN BEFORE THE VECTORS EXISTED

`out/T391-10-RED-wrongimpl-survives-without-vectors.txt`, committed at `3fa91e44`, one commit
**before** the vectors:

```
--- FAIL: TestEveryWrongImplementationIsKilled
    WRONG IMPLEMENTATION "ledger-wrong-slot-family-blind" SURVIVES THE COMMITTED CORPUS.
```

It cannot be re-taken now without deleting the vectors, and a drive that deletes the evidence
it drives is not a drive.

### THE OTHER TWO KILLS THESE VECTORS ADD, AND ONE THEY DELIBERATELY DO NOT

* `ledger-wrong-truncating` now fails **9** parity vectors, up from 7: it dies on `LDG-ACC-02`
  (margin **−38**) and `LDG-ACC-03` (**−34**) and **does not die on `LDG-ACC-01`**, whose every
  amount is a whole tugrik. That is DEC-2 §5.0.1's point about a whole-tugrik corpus, visible
  inside one shape rather than across two. `LDG-ACC-01`'s `graded_against` **does not claim
  that kill**.
* `ledger-wrong-netting-totals` and `ledger-wrong-code-ignored` now fail all 10.

**ONE DEPARTURE FROM AN EXISTING VECTOR'S LABEL, STATED RATHER THAN LEFT TO TRIP A REVIEWER.**
These vectors declare `ledger-wrong-netting-totals` as a **money** kill with the real margin
(−2770000 / −2389538 / −1605634). `LDG-01` declares the **same implementation** as
`structural, margin 0`. `total_debits_minor` and `total_credits_minor` go through `cmpMoney`,
not `cmpStr`, so a wrong value there **is** a money divergence and it has a margin. LDG-01's
label is the weaker of two descriptions of one behaviour; **nothing about the implementation
differs between the vectors and LDG-01 was not touched.**

---

## 5. `capabilities-ledger.json` — THE ROW THE HARNESS PRINTED EVERY RUN, REWRITTEN

**All four sentences were false and the harness printed them on every run, pass or fail, as
measured fact.**

| the sentence | verdict | measured |
|---|---|---|
| *"the observations do not exist"* | **FALSE** | 36 legs on six accrual transactions |
| *"Product 28 is the only ACCRUAL_PERIODIC product … the ONLY row with that value"* | **FALSE** | 28 **and** 63 |
| *"NOT ONE JOURNAL ENTRY IN THIS TENANT ARRIVED THROUGH A RECEIVABLE SLOT"* | **FALSE** | **EIGHTEEN** did |
| *"An accrual vector needs a NEW accrual product on clean accounts PLUS a job run"* | **FALSE** as a cost estimate | both already exist; and T352 had already shown the job was active all along |

**THE SENTENCE THAT SURVIVED BY BEING NARROWED IS NOW FALSE TOO — DELIBERATELY.** T388
recommended keeping *"NOT ONE ENTRY IN THIS **CORPUS**"*, which was true of the promoted store
on 28 August and which T389 independently confirmed. **T391 promoted three vectors carrying
nine receivable-slot legs, so the corpus sentence is spent.** It is recorded in the row as
superseded rather than deleted, because a reader who meets it in T388's handoff or T389's
review must be able to find what became of it.

**The row is REWRITTEN, not deleted**, and enters the graded domain
(`in_graded_domain: true`). `ledger_rest_posting` now declares `ledger.accrual.entry:
exercised`. The row states what is still **NOT** graded: `ACCRUAL_UPFRONT` (no capture at
`accountingRule = 4`), `ACCRUAL_ACTIVITY_POSTING` and the COB path (jobs 33/34 INACTIVE),
accrual REVERSAL, and the five unposted slots.

### `unposted_slots` MOVED to `ledger.slot.resolution`, which STAYS FALSE

**The renderer prints SLOT lines only for rows marked `in_graded_domain: false`**
(`notgraded.go`, `NotGradedCapabilities()`). Leaving the slots on a now-graded row would have
**silently stopped printing a measurement that has already been wrong once in this file's
history**. They belong on the slot-resolution row on the merits too: an unposted slot is a gap
in slot-resolution coverage.

* **Product 28's three rows are unchanged and re-measured**: slot 7 → gl 18 (0), slot 8 → gl 22
  (0), slot 9 → gl 16 (21 rows on the ACCOUNT, ZERO through product 28).
* **Product 63's five unposted slots are ADDED** — 6 → gl 40, 10 → gl 44, 11 → gl 45, 12 → gl
  46, 13 → gl 47, all reading zero.

Verified in the final bar's printed block: eight `SLOT product …` lines, `gl 16` correctly
annotated *"IS NOT AN UNUSED ACCOUNT: 3 vector(s) in this store carry a leg on it"*, the other
seven correctly annotated *"NO VECTOR IN THIS STORE carries a leg on gl …"*.

**`ledger.slot.resolution` stays `in_graded_domain: false`, and the row now says why**: the
accrual-family resolution IS graded (through `ledger.accrual.entry`), but the **payment-type
precedence chain** is not — product 63 has NO `paymentChannelToFundSourceMappings`,
`feeToIncomeAccountMappings` or `penaltyToIncomeAccountMappings` at all [`GET /loanproducts/63`,
`out/T391-04-product63-mapping-rest.txt`], so STEP 2 of `resolveProductAccount` is never
entered and G-06's contested null-payment-type question is untouched — nor is the CASH family,
the financial-activity STEP 0 branch, or the charge/reason levels. The vectors therefore claim
`ledger.accrual.entry`, scoped to what they exercised, and **not** `ledger.slot.resolution`.

---

## 6. WHAT I DID **NOT** DO, AND WHY

1. **I DID NOT POST THE FIVE REMAINING ACCRUAL SLOTS** (6 `LOSSES_WRITTEN_OFF`, 10
   `TRANSFERS_SUSPENSE`, 11 `OVERPAYMENT`, 12 `INCOME_FROM_RECOVERY`, 13 `GOODWILL_CREDIT`).
   The brief is right that the marginal cost is a transaction rather than a product — product
   63 and gl 40/44/45/46/47 are in place and clean. **I declined anyway, and the reason is not
   cost.** Each is a fresh MOVE OF SHARED ORACLE STATE with its own blast radius, and **T388's
   twenty command-source rows and four transactions are STILL UNATTRIBUTED in
   `PROBES.tsv`** — `oracle-state-baseline.sh` still exits 1, and that obligation is T390's,
   in flight this wave. Adding five more unattributed moves while an attribution obligation is
   open deepens it to buy evidence this task did not need. **Instead they are DECLARED**, so
   the harness prints the gap on every run rather than leaving it in a handoff. A later task
   that wants them has a cheaper starting point than T391 did and an attribution instrument
   that will by then be discharged.
2. **I DID NOT PROMOTE `L31`, `L33` or `L34`.** Three of six is the discriminating set: one
   round amount, two different residues, and both trigger paths. Promoting all six would
   triple the same shape and move the money-cell census by 48 for no new discrimination.
3. **I MADE NO PRECISION CLAIM.** T388 said so and is right. Every amount here is exact at two
   decimals and NOTHING IN THESE CAPTURES DISCRIMINATES `(19, HALF_UP)` — a port at precision
   12 produces the same integers. Said in every vector's own `_note`, not only here.
4. **I DID NOT TOUCH `PROBES.tsv`, `CASUALTIES.md`, `RESUME.md`, `gates.md`, `docs/adr/`, or
   `t363-oracle-baseline/`.** All are other tasks' grants or other tasks' open findings
   (T389's M-1 on ratified DEC-2 is a **gate**, not an edit).
5. **I DID NOT RE-ISSUE A SINGLE POST.** T389's reason, unchanged: re-issuing would move the
   oracle a second time and corrupt the evidence being promoted.
6. **I DID NOT RUN A CASUALTY SWEEP.** T391 moved no oracle state, so it created no casualty.
   The counters that moved between T388 and today were moved by the SCHEDULER, not by me, and
   they are recorded in § 2.1 for whoever owns the sweep next: `acc_gl_journal_entry` 91/95 →
   **109/113**, `m_loan_transaction` 21/31 → **24/34**, `m_portfolio_command_source`
   **unmoved at 379/379**.

---

## 7. THE BAR — FROM A CLEAN TREE, `bash`, PROBE PRESENCE BEFORE VALUE

Run after `git add -A` **and** `git commit`, with `git status --porcelain` **EMPTY**, using
`bash` (never `sh`; `sh` exits 3 by design).

**[VERIFIED] `bash .softhouse/conformance.sh` → EXIT 0.**
**`grep -c 'probe = '` → 1** (P-84: presence tested BEFORE value), reading:

```
conformance: reference oracle (https://localhost:8443/.../actuator/health) probe = up
```

| figure | baseline (`1eacb63e`) | now |
|---|---|---|
| ledger parity | PASS 7 FAIL 0 | **PASS 10 FAIL 0** |
| ledger oracle-refusal | PASS 6 FAIL 0 | PASS 6 FAIL 0 |
| ledger inadmissible | 0 | 0 |
| ledger harness errors | 0 | 0 |
| ledger cells / money | 144 / 39 | **268 / 63** |
| divergence vectors | PASS 1 FAIL 0 (pinned 1) | PASS 1 FAIL 0 (pinned 1) |
| loanschedule parity / cells | PASS 46 FAIL 0 / 7,884 | PASS 46 FAIL 0 / 7,884 |
| dead-path frontier | GREEN, `deadOccurrences 108` | GREEN, `deadOccurrences 108` |
| wrong-implementation census | 14, all killed | **15, all killed** |

```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   exemption census READ: LEDGER declared exemptions   = 0  == pinned 0
conformance:   exemption census READ: LEDGER parity vectors        = 10 == pinned 10
conformance:   exemption census READ: LEDGER oracle-refusal vector = 6  == pinned 6
conformance:   exemption census READ: LEDGER money cells compared  = 63 == pinned 63
conformance:   all 15 wrong ledger implementations DIED through this harness, not by hand.
```

Committed transcript: `.softhouse/capture/t391-accrual-promotion/out/T391-BAR-conformance.txt`
(taken from the clean tree at `6087c67a`). **That transcript is not covered by the run that
produced it** — T388's residual, in the same shape — and is closed by a SECOND run taken from
the clean tree at `52d84a14`, the transcript commit itself, which is the run whose figures are
tabulated above.

### A GUARD FIRED ON THIS TASK AND IT WAS RIGHT

The first bar attempt was **exit 2, a HARD guard, no verdict**:

```
conformance: the wire-float round-trip guard REFUSED:
REFUSED — a file in the derived request-body set is not parseable as JSON.
  .softhouse/capture/t391-accrual-promotion/out/T391-A01-je-L29.req  JSONDecodeError
  ... eight in all
```

The guard's population is *"every `*.json` whose DIRECT parent directory is named `req`, plus
every `*.req` wire-bytes artefact, at any depth under `.softhouse/capture`"*, and a member of
that population **is a request body**. A GET has no body, so `capget.sh` had nothing to pin and
was writing the request LINE AND HEADERS under a name that claims to be a body. `cap11.sh`
does not make that mistake — T388's own GET captures carry `.http`/`.status`/`.json` and no
`.req`. **Fixed at the source, not exempted**: `capget.sh` no longer writes `.req`, the eight
files are deleted, and the vectors cite the `.http` record.

**Note for P-84's benefit: that exit 2 had NO probe line** (`grep -c 'probe = '` = 0), which
is exactly the case P-84 says is a harness/guard failure and not an oracle outage. It was.

---

## 8. EXACTLY WHICH `conformance.sh` SYMBOLS I TOUCHED — FOR SERIAL MERGE

**THREE ASSIGNMENT LINES, ANCHORED BY NAME, NEVER BY LINE NUMBER:**

| symbol | from | to |
|---|---|---|
| `EXEMPTION_PIN_LEDGER_PARITY` | `7` | **`10`** |
| `EXEMPTION_PIN_LEDGER_MONEYCELLS` | `39` | **`63`** |
| `EXEMPTION_PIN_LEDGER_WRONGIMPLS` | `14` | **`15`** |

Applied with `sed -i '' 's/^SYMBOL=old$/SYMBOL=new$/'`, anchored `^…$`. `git diff --stat` on
`conformance.sh` reads **3 insertions, 3 deletions** — nothing else in that file was read,
reflowed, re-sorted or reformatted.

**NOT touched:** `EXEMPTION_PIN_LEDGER_REFUSAL` (stays 6), `EXEMPTION_PIN_LEDGER_DECLARED`
(stays 0), and **every registration-guard region, which T404 holds this wave**.

### THE CONTENTION THE DRIVER MUST SEQUENCE — AND IT IS NOT ONLY `conformance.sh`

**T397 holds `nexus/internal/apps/ledger/conformance/` and I wrote in it.** This was
unavoidable: the brief requires populating the ledger schema's slot fields (`vector.go`) and
registering a wrong implementation alongside the existing `ledger-wrong-*` drives (`impl.go`),
and both live in T397's grant. **Declared here rather than discovered at merge.**

Files I touched under `nexus/internal/apps/ledger/conformance/`:

| file | what I changed |
|---|---|
| `vector.go` | added `RequestLeg.SlotCode`, `ProductMapping`, `Request.ProductMappings`, `ExpectLeg.SlotName`. Purely additive |
| `admit.go` | added two blocks of slot admissibility rules; **modified one existing line** — the leg/chart rule is now `if l.SlotCode == 0 && !chart[l.AccountID]` |
| `grade.go` | added one `cmpStr` for `legs[i].slot_name` in `diffEntry`; extended the `CellFields` probe to carry both leg shapes |
| `impl.go` | `PostedLeg.SlotName`; slot resolution in `GoPoster.PostEntry`; three new helpers; `slotFamilyBlindPoster` and its `RegisterWrong` |
| `notgraded_test.go` | two tests re-pointed from `ledger.accrual.entry` to `ledger.slot.resolution`; assertions unchanged |
| `divergence_test.go` | `ParityPass` 7 → 10 (two sites), `MoneyCells` 39 → 63 |

**T397's declared targets are `verbatimInCapture` (a `bytes.Contains` in `admit.go`) and
`report.go:592`.** I did **not** touch `verbatimInCapture` and did **not** touch `report.go`.
The overlap is therefore `admit.go` at two distant regions of the same file. **Merge T391 and
T397 serially in a scratch worktree, run the bar on the MERGE RESULT, then land.**

### COUNTS THAT MOVED, MOVED IN ONE COMMIT (P-83)

Commit `25a8b7de` carries **all five restatements** together: the three `conformance.sh` pins
above, and the two hard-coded expectations in `divergence_test.go`. The Go-side divergence pin
(`DivergencePinCount`, `grade.go`) did **not** move and is still 1.

---

## 9. FILES

**Promoted** — `.softhouse/vectors/ledger/LDG-ACC-01…03*.json`; rewritten
`.softhouse/vectors/capabilities-ledger.json`.
**Rig** — `.softhouse/capture/t391-accrual-promotion/`, `MANIFEST.sha256` over the whole rig
(scripts included, T114's reason), README with both guard incidents.
**Key artefacts** — `out/T391-S01`/`S03` (the slot decode and the bijection checks),
`out/T391-S02` (the drift measurement), `out/T391-S05` (the job windows),
`out/T391-03-reissue-vs-t388.txt` (byte-identity), `out/T391-10-…` (the RED drive),
`out/T391-11-wrongimpl-matrix.txt` (the kill, both directions),
`out/T391-BAR-conformance.txt`.

## 10. WHAT THE NEXT TASK SHOULD KNOW

1. **`PROBES.tsv` is still undischarged** and now has more to attribute than T388 left:
   `L32`/`L33`/`L34` and journal entries 96–113 have **no command-source row and no
   idempotency key at all**, because a cron job wrote them. An attribution instrument keyed on
   idempotency keys **cannot attribute a scheduled job's output**, and T390 should be told so
   before it tries.
2. **The five unposted accrual slots now print every run.** Closing them is a transaction each,
   and the blast-radius/attribution cost is the real cost.
3. **`ledger.slot.resolution` stays false for a NAMED reason** — the payment-type precedence
   chain. Closing it needs a product with `paymentChannelToFundSourceMappings`, which product
   63 does not have. That is a product-creation task, not a transaction.
4. **`ACCRUAL_UPFRONT` (`accountingRule = 4`) is still refused by `admit.go` on evidential
   grounds** — no capture exists at that rule. It is the cheapest remaining widening of the
   accrual class.
5. **T389's M-1 STANDS UNREPAIRED AND HAS MOVED AGAIN — AND THE NEW MEASUREMENT SAYS SOMETHING
   T389's DID NOT.** `docs/adr/DEC-2-gl-accounting-adapter.md:1061` and `:3004` assert, present
   tense, *"60 of the 60 rows in `acc_gl_journal_entry` carry `last_modified_on_utc >
   created_on_utc`"*, and I-5 uses the **UNIVERSALITY** — the column is dismissed as
   discriminating nothing *because every row carries it*. T389 measured **60 of 91**. T391
   measures, read-only [`out/T391-S06-dec2-i5-pin.txt`]:

   ```
   modified | total          cohort                          modified | total
        91  |   109          id <= 75 (predates T388)              71 |    71
                             id 76-95  (T388)                      20 |    20
                             id 96-113 (the scheduled job)          0 |    18
   ```

   **EIGHTEEN ROWS NOW CARRY `last_modified_on_utc == created_on_utc`.** So the premise is not
   merely stale in its cardinal — **the column now DISCRIMINATES**, exactly as I-5 says it does
   not: it separates rows job 9 `Update Accounting Running Balances` has touched from rows it
   has not. Job 9 ran at `16:01:00.003`, **before** the accruals were written at `.100`, which
   is why they are the untouched cohort and why the next run of job 9 will silently repair the
   universality and hide this. **Measure it before that run if the gate is to be raised on
   evidence.** DEC-2 is RATIFIED: amending it is a `user` gate, not an edit, and T391 did not
   touch `docs/`.
