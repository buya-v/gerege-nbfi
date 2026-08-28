# T388 MOVED THE REFERENCE ORACLE'S STATE — what changed, and what it does not affect

Same discipline as `.softhouse/capture/t352-a2-next-tranche/ORACLE-STATE-MOVED-BY-T352.md`
and `.softhouse/capture/tierA-a2/ORACLE-STATE-MOVED-BY-T276.md`. A journal entry cannot be
deleted, a GL account cannot be un-created and an idempotency key cannot be un-burned, so
every write this task made is permanent.

**This record is a DIFF, not an assertion.** A BEFORE snapshot was taken before anything was
written (`out/T388-B01-before-snapshot.txt`, `out/T388-B03-before-per-account.txt`,
`out/T388-B04-charges.txt`, `out/T388-B05-tenant-clock.txt`) and the AFTER values are
re-derived live in `out/T388-S01-after-snapshot.txt` and `out/T388-A02-accrual-entries-decoded.txt`.
Every number below is one of those two, quoted.

Fire `20260828-140005`, tenant `gerege`, database `fineract_gerege`, PostgreSQL 18.3, oracle
pinned at `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

---

## THE HEADLINE

**T388 took the first accrual observations in this program.** Nine journal entries arrived
through a RECEIVABLE slot — three through `INTEREST_RECEIVABLE` (slot 7), three through
`FEES_RECEIVABLE` (slot 8), three through `PENALTIES_RECEIVABLE` (slot 9). Before this fire
the count was **zero**, and the ledger section of the bar has printed that zero on every run.

**NO GL ACCOUNT THAT ANY PROMOTED VECTOR READS WAS MOVED.** That was the design constraint
and it is verified rather than hoped — see § *The P0 check* below.

---

## 1. What was created, with ids

### Thirteen NEW GL accounts, ids 35–47

Created so that the accrual could be posted **without touching a promoted account**. Every id
is above the pre-fire `max(acc_gl_account.id) = 34`.

| gl id | gl code | name | classification | AccrualAccountsForLoan slot | creation capture |
|---|---|---|---|---|---|
| 35 | `T388-1000` | T388 Accrual Fund Source | ASSET | 1 FUND_SOURCE | `out/T388-G01-gl-fund-source.*` |
| 36 | `T388-1100` | T388 Accrual Loan Portfolio | ASSET | 2 LOAN_PORTFOLIO | `out/T388-G02-gl-loan-portfolio.*` |
| 37 | `T388-4000` | T388 Interest On Loans | INCOME | 3 INTEREST_ON_LOANS | `out/T388-G03-gl-interest-on-loans.*` |
| 38 | `T388-4100` | T388 Income From Fees | INCOME | 4 INCOME_FROM_FEES | `out/T388-G04-gl-income-from-fees.*` |
| 39 | `T388-4200` | T388 Income From Penalties | INCOME | 5 INCOME_FROM_PENALTIES | `out/T388-G05-gl-income-from-penalties.*` |
| 40 | `T388-5000` | T388 Losses Written Off | EXPENSE | 6 LOSSES_WRITTEN_OFF | `out/T388-G06-gl-losses-written-off.*` |
| **41** | `T388-1200` | **T388 Interest Receivable** | ASSET | **7 INTEREST_RECEIVABLE** | `out/T388-G07-gl-interest-receivable.*` |
| **42** | `T388-1300` | **T388 Fees Receivable** | ASSET | **8 FEES_RECEIVABLE** | `out/T388-G08-gl-fees-receivable.*` |
| **43** | `T388-1400` | **T388 Penalties Receivable** | ASSET | **9 PENALTIES_RECEIVABLE** | `out/T388-G09-gl-penalties-receivable.*` |
| 44 | `T388-1500` | T388 Transfers Suspense | ASSET | 10 TRANSFERS_SUSPENSE | `out/T388-G10-gl-transfers-suspense.*` |
| 45 | `T388-2000` | T388 Overpayment Liability | LIABILITY | 11 OVERPAYMENT | `out/T388-G11-gl-overpayment.*` |
| 46 | `T388-4300` | T388 Income From Recovery | INCOME | 12 INCOME_FROM_RECOVERY | `out/T388-G12-gl-income-from-recovery.*` |
| 47 | `T388-5100` | T388 Goodwill Credit | EXPENSE | 13 GOODWILL_CREDIT | `out/T388-G13-gl-goodwill-credit.*` |

`acc_gl_account`: **23 rows / max 34 → 36 rows / max 47.**

### One NEW loan product, id 63

`T388 Accrual Periodic On Clean Accounts` (`T388`), `accounting_type = 3` ACCRUAL_PERIODIC,
currency **MNT** (ISO 4217 numeric 496, minor unit 2), `digitsAfterDecimal 2`,
`inMultiplesOf 0`. Mapped one-to-one onto GL 35–47, so the mapping is a **bijection** and the
slot decode is unambiguous. Thirteen new `acc_product_mapping` rows.

Terms chosen to actually generate interest, a fee and a penalty — an accrual of zero would
prove nothing: principal `1200000` MNT major units, 6 monthly repayments, `24` percent per
annum, declining balance, equal instalments, `interestCalculationPeriodType 1`,
`daysInYearType 360`, `daysInMonthType 30`, `mifos-standard-strategy`, interest recalculation
OFF. Charges `2` (flat fee per instalment, 2500) and `8` (flat PENALTY per instalment, 1200).

**Every numeric literal in the request body is an INTEGER.** The rate is `24`, not `21.6`,
precisely so that no float token appears anywhere in this capture's request bytes — see
`req/P01-accrual-product.json` and the committed wire bytes
`out/T388-P02-create-accrual-product.req`.

`m_product_loan`: **33 rows / max 60 → 34 rows / max 63.**
`acc_product_mapping`: **132 rows / max 156 → 145 rows / max 189.**

### One NEW client, id 3

Three name fields, per CLAUDE.md, mapped onto Fineract's schema — which has only
`firstname` / `middlename` / `lastname` and cannot be changed here, so the mapping is stated
rather than left implicit:

| Mongolian field | value | Fineract column |
|---|---|---|
| **ovog** (clan name) | `Боржигин` | `lastname` |
| **patronymic** | `Батбаярын` | `middlename` |
| **given name** | `Ганболд` | `firstname` |

**Registration number, the match key:** `external_id` = `УБ90051423`. Structurally valid as a
Mongolian national ID: **10 characters, 2 Cyrillic letters + 8 digits** (`УБ` + `90 05 14 23`,
a 1990-05-14 birth, so no `+20` month offset applies — that rule is for births from 2000
onward). **The check digit is unpublished, so this was validated STRUCTURALLY ONLY** and no
claim is made that this number is issued to anybody.

Activated `01 January 2026`, office 1. `m_client`: **2 rows → 3 rows.**

### One NEW loan, id 8

Client 3 on product 63, submitted / approved / disbursed `15 January 2026`, principal
`1200000` MNT, ACTIVE. Loan transaction 28 (disbursement), journal transaction `L28`.

`m_loan`: **7 → 8.** `m_loan_transaction`: **17 rows / max 27 → 21 rows / max 31.**

---

## 2. The accrual run — TRIGGERED MANUALLY, and said so

**`POST /v1/runaccruals` with `{"tillDate":"15 April 2026"}` was fired by hand.** The
scheduled job was not waited for. The trigger request and response are captured at
`out/T388-A01-runaccruals.req` / `.http` / `.json` / `.status` (HTTP 200, body `{}`).

**This is the SAME CODE PATH as scheduled job 16 "Add Periodic Accrual Transactions", and the
difference is one argument.** [VERIFIED at the pinned sha:
`AccrualAccountingApiResource.java:62` → `excuteAccrualAccounting` →
`AccrualAccountingWritePlatformServiceImpl.executeLoansPeriodicAccrual` →
`loanAccrualsProcessingService.addPeriodicAccruals(tillDate)`, where `tillDate` comes from the
request; `AddPeriodicAccrualEntriesTasklet.execute` calls the identical
`loanAccrualsProcessingService.addPeriodicAccruals(...)` with
`DateUtils.getBusinessLocalDate()`.] So the only thing the manual trigger changes is *which
date* is accrued to — it is not a different mechanism, and this capture is not evidence about
the scheduler.

`enable-business-date` is **`f`** on this tenant [`out/T388-B05-tenant-clock.txt`], so the
job's own `tillDate` would have been today's tenant date; `15 April 2026` was chosen instead
so the accrual lands inside the loan's schedule and the observation is about accrual, not
about the clock.

**Three ACCRUAL loan transactions were produced** — 29 (2026-02-15), 30 (2026-03-15),
31 (2026-04-15) — and each wrote a six-leg journal entry. That periods 1–3 accrued and periods
4–6 did not is the `FIND_LOANS_FOR_PERIODIC_ACCRUAL` predicate behaving as written
(`ls.fromDate < :tillDate`; period 4's `fromDate` is `2026-04-15`, which is not `< 2026-04-15`,
and it is not the minimum instalment).

---

## 3. Four transactions, twenty legs — all MNT, all office 1, all non-manual

| txn | legs | what it is | capture |
|---|---|---|---|
| `L28` | 2 | disbursement: gl 36 DEBIT / gl 35 CREDIT `1200000.000000` | `out/T388-P07-loan-disburse.*` |
| **`L29`** | **6** | **first accrual**, entry_date `2026-02-15` | `out/T388-A03-je-readback-L29.json` |
| **`L30`** | **6** | second accrual, entry_date `2026-03-15` | `out/T388-A04-je-readback-L30.json` |
| **`L31`** | **6** | third accrual, entry_date `2026-04-15` | `out/T388-A05-je-readback-L31.json` |

`acc_gl_journal_entry`: **71 rows / max 75 → 91 rows / max 95.**
`distinct transaction_id`: **31 → 35.**

**Double entry holds on every one**, checked in integer minor units in
`out/T388-A02-accrual-entries-decoded.txt` § 4: `L28` 120000000/120000000, `L29`
2770000/2770000, `L30` 2389538/2389538, `L31` 2001467/2001467, difference **0** on all four.

### The nine receivable-slot legs, with the decode

| je id | txn | date | dr/cr | gl | code | amount MNT | slot | slot name |
|---|---|---|---|---|---|---|---|---|
| 78 | L29 | 2026-02-15 | DEBIT | 41 | `T388-1200` | `24000.000000` | 7 | INTEREST_RECEIVABLE |
| 81 | L29 | 2026-02-15 | DEBIT | 42 | `T388-1300` | `2500.000000` | 8 | FEES_RECEIVABLE |
| 83 | L29 | 2026-02-15 | DEBIT | 43 | `T388-1400` | `1200.000000` | 9 | PENALTIES_RECEIVABLE |
| 84 | L30 | 2026-03-15 | DEBIT | 41 | `T388-1200` | `20195.380000` | 7 | INTEREST_RECEIVABLE |
| 87 | L30 | 2026-03-15 | DEBIT | 42 | `T388-1300` | `2500.000000` | 8 | FEES_RECEIVABLE |
| 89 | L30 | 2026-03-15 | DEBIT | 43 | `T388-1400` | `1200.000000` | 9 | PENALTIES_RECEIVABLE |
| 90 | L31 | 2026-04-15 | DEBIT | 41 | `T388-1200` | `16314.670000` | 7 | INTEREST_RECEIVABLE |
| 93 | L31 | 2026-04-15 | DEBIT | 42 | `T388-1300` | `2500.000000` | 8 | FEES_RECEIVABLE |
| 95 | L31 | 2026-04-15 | DEBIT | 43 | `T388-1400` | `1200.000000` | 9 | PENALTIES_RECEIVABLE |

**WHY THIS IS A SLOT CLAIM AND NOT AN ACCOUNT CLAIM.** T242's correction (A2-34 F-4) is about
exactly this confusion: **one GL account backs several slots**, so an entry that *lands on* a
receivable account is not the same as one that *arrived through* a receivable slot — gl 16 is
`PENALTIES_RECEIVABLE` on product 28 *and* `FUND_SOURCE` on five cash products, and all of its
rows arrive through the latter. The decode here is safe for two reasons that are stated rather
than assumed:

1. the entry's `loan_transaction_id` resolves to an `m_loan_transaction` with
   `transaction_type_enum = 10` (ACCRUAL) on a loan whose product has `accounting_type = 3`,
   so the **accrual** enum is the right one to decode against; and
2. product 63's thirteen mappings point at thirteen **distinct** accounts, so
   `acc_product_mapping.gl_account_id → financial_account_type` is a **function**, not a
   relation. That is a property of how T388 built the product, and it is the reason the
   accounts were created clean rather than reused.

Slot codes decode on `AccrualAccountsForLoan`: 7 `INTEREST_RECEIVABLE`, 8 `FEES_RECEIVABLE`,
9 `PENALTIES_RECEIVABLE` [VERIFIED against the ported enum
`nexus/internal/apps/ledger/slots.go` and Fineract `AccountingConstants.java:95-122` at the
pinned sha]. Note the trap that makes the decode worth writing down: under
`CashAccountsForLoan` those same names are codes **25** and **26** and code 7/8/9 do not exist
at all, so a decode that ignored the accounting rule would be wrong in both directions.

---

## 4. THE P0 CHECK — did any promoted GL account move? **NO.**

The forbidden set was **derived, not remembered**, by
`11-derive-forbidden-set.py` (output `out/T388-D01-forbidden-set.txt`), which walks every JSON
key ending in `gl_account_id` at any depth across all 64 files in `.softhouse/vectors/`,
including the store-level `capabilities-ledger.json`, and splits by
`provenance.capture_ref` into standing-oracle and throwaway instances.

**Forbidden set on the standing oracle: `{1, 2, 4, 6, 8, 10, 15, 16, 17, 18, 21, 22}`.**
(`{1, 2, 3, 4}` on the t305/t327 THROWAWAY instances — a different id space, listed separately
and deliberately not merged: LDG-05/06/07 were captured on instances that no longer exist, and
on the standing oracle id 1 is `10000 Assets`, not `T305-1000`.)

Disjointness verdict, `out/T388-D02-disjointness-check.txt`: intersection **EMPTY**, exit 0.
Red-driven in `out/T388-D03-RED-drive-checker.txt` — `--check 16,41` reports intersection
`[16]`, `VERDICT: FAIL`, exit **1**. A checker nobody has watched fail enforces nothing.

Live per-account counts, BEFORE (`out/T388-B03-before-per-account.txt`) against AFTER
(`out/T388-S01-after-snapshot.txt` and `out/T388-A02-accrual-entries-decoded.txt` § 5):

| gl | code | before | after | moved? |
|---|---|---|---|---|
| 1 | 10000 | 3 | 3 | no |
| 2 | 10100 | 3 | 3 | no |
| 4 | 10201 | 12 | 12 | no |
| 6 | 20100 | 1 | 1 | no |
| 8 | 40100 | 2 | 2 | no |
| 10 | 40300 | 1 | 1 | no |
| 15 | 30000 | 0 | 0 | no |
| 16 | 10300 | 21 | 21 | no |
| 17 | 10400 | 5 | 5 | no |
| 18 | 10500 | 0 | 0 | no |
| 21 | 99008 | 13 | 13 | no |
| 22 | 99010 | 0 | 0 | no |

**Twelve of twelve unmoved.** `gl 18 → 0` and `gl 22 → 0` — the pair the
`ledger.accrual.entry` argument rests on — are specifically unchanged.

This is the route T352 named as correct and declined to pay for: a new ACCRUAL_PERIODIC
product on clean accounts, rather than a loan on product 28 whose slot 9 resolves to gl 16.

---

## 5. Attribution — every write names T388

All twenty `m_portfolio_command_source` rows this fire wrote carry a task-naming
`Idempotency-Key` beginning `T388-` [`out/T388-A02-accrual-entries-decoded.txt` § 7, rows
360–379]. None is a minted UUID. That matters because the column is `NOT NULL` and Fineract
mints one when the caller sends no header, so 339 of the 359 pre-existing rows in this tenant
are unattributable forever (T371).

`m_portfolio_command_source`: **359 rows / max 359 → 379 rows / max 379.**
Status split: **181 PROCESSED / 198 ERROR** (was 162 / 197 when T371 measured it; T388 added
19 PROCESSED and 1 ERROR).

**One refusal, recorded as data.** `T388-P04-loan-application` returned HTTP **400**
(`charges[1][amount]` and `charges[2][amount]` mandatory) and wrote command-source row 375
with `status = 5` ERROR. **A 4xx burns the key**: `saveInitial` runs before
`executeCommandInTransaction`, so that key can never be reused. The retry under the new key
`T388-P05-loan-application` succeeded. Both are captured
(`out/T388-P04-loan-application.*`, `out/T388-P05-loan-application.*`).

### THE PROBES.tsv OBLIGATION IS NOT DISCHARGED, AND THAT IS DELIBERATE

`.softhouse/capture/t363-oracle-baseline/PROBES.tsv` requires a task that probes the standing
oracle to append its rows **in the same commit as its handoff**. T388's write grant is exactly
this directory plus its handoff, and that file is outside it (its directory was concurrently
held in this fire). So the rows are staged verbatim, in the file's own tab-separated format,
at **`out/PROBES-APPEND-T388.tsv`**.

**Until they are appended, `bash .softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh`
WILL EXIT 1** and print `L28`/`L29`/`L30`/`L31` and the twenty `T388-*` keys as UNATTRIBUTED.
That is the instrument working as designed — the absence of a record is what goes red — and it
is the **first item** the follow-on task must discharge.

---

## 6. BLAST RADIUS — derived, not remembered

`bash 30-casualty-sweep-t388.sh`, output `out/T388-SW01-casualty-sweep.txt`.

**Where I looked, stated so the negatives mean something.** Population:
`git ls-files .softhouse` = **8,470 tracked files** (git grep sees TRACKED files only, so the
sweep was run AFTER `git add -A`). Engine `git grep` with `-E` or `-F` stated per selector; **no
`\b` anywhere**, because `git grep -E` reads it as a literal `b` on this host and returns zero
silently (T232). Eighteen selectors, S1–S18, each printing total / archived / LIVE, with the
archive predicate printed in the script. `git grep`'s exit status **is read** — a selector that
did not run (rc ≥ 2) prints differently from a measured zero (rc 1) and sets exit 4 (T367 F2,
repaired by T371 and carried over here). Positive and anti-calibration both PASS.
**I did NOT search outside `.softhouse/`**, and the `nexus/` Go tree was checked separately:
it opens no database and reads no vector account ids at build time.

### A. EXECUTABLE casualties — a program changes behaviour

| site | pin | before T388 | now | does it fail? |
|---|---|---|---|---|
| `capture/t327-closure-accepting-side/throwaway/capture.sh:82` | `m_loan` by string equality against `STANDING-baseline.txt` (`m_loan = 7`) | 7 | **8** | **YES — refuses, when invoked standalone.** NEW casualty. |
| `capture/t327-closure-accepting-side/throwaway/down.sh:54` | same | 7 | **8** | **YES — sets `rc=1`, standalone.** NEW casualty. |
| `…/t327/capture.sh:82`, `…/t327/down.sh:54` | `acc_gl_journal_entry 60/64`, `distinct_transaction_id 26`, `m_portfolio_command_source 352/352` | already broken by T352/T359 | `91/95`, `35`, `379/379` | already failing; T388 moves them further |
| `capture/t305-…/throwaway/capture.sh:77`, `capture2.sh:59`, `down.sh:52` | the same three counters (**t305 does NOT pin `m_loan` — verified by reading all three scripts**) | already broken | as above | already failing; T388 moves them further |

**`m_loan = 7 → 8` IS THE FINDING T363 COULD NOT HAVE HAD.** `CASUALTIES.md:40` records
`m_loan 7` and `m_office 1` as **unmoved**; that sentence is now half false. `m_office` is
still 1.

**The `run-all.sh` caveat still applies and still matters** (T363's correction to T359): step 0
of both `run-all.sh` scripts does `rm -rf "$OUT"` and **regenerates** `STANDING-baseline.txt`
from the live oracle before `capture.sh` or `down.sh` reads it, so **through the supported
entry point both rigs are UNAFFECTED**. They refuse only when `bash capture.sh` is typed by
hand against the committed file. T363's recommended repair — refuse a baseline that does not
belong to the current run, rather than one whose numbers moved — remains unapplied and remains
the right fix. **NOT APPLIED HERE:** `t305/` and `t327/` are outside this task's write grant.

### B. DOCTRINE read as current, and now WRONG

| site | claim | status after T388 |
|---|---|---|
| `.softhouse/vectors/capabilities-ledger.json:52` | *"Product 28 is the only ACCRUAL_PERIODIC product (…and it is the ONLY row with that value)"* | **FALSE.** Live: products **28 and 63**. |
| `.softhouse/vectors/capabilities-ledger.json:52` | *"NOT ONE JOURNAL ENTRY IN THIS TENANT ARRIVED THROUGH A RECEIVABLE SLOT"* | **FALSE.** Live: **9**. |
| `.softhouse/vectors/capabilities-ledger.json:52` | *"The single missing ingredient is A LOAN: product 28 has zero"* | **still true of product 28**, and now beside the point — product 63 has loan 8. |
| `.softhouse/vectors/capabilities-ledger.json:22` | *"ACCRUAL is entirely absent — no accrual product has a loan and no accrual or COB job has run"* | **first clause FALSE** (product 63 has loan 8). The clause *"NOT ONE ENTRY IN THIS **CORPUS** ARRIVED THROUGH A RECEIVABLE SLOT"* is **still TRUE** — the *corpus* is the promoted vector store and T388 promoted nothing. That distinction is the whole difference between this row and the one above it, and it must not be flattened when the row is rewritten. |
| `.softhouse/vectors/capabilities-ledger.json:52` | *"no accrual or COB job has ever run"* | was already corrected by T352 in the same field; unchanged by T388. |
| `.softhouse/capture/t363-oracle-baseline/CASUALTIES.md:40,44` | *"`acc_gl_closure 0/null`, `m_loan 7`, `m_office 1` are unmoved"* | **`m_loan` now FALSE.** The other two hold. |
| `.softhouse/gates.md:4519-4520` | *"two throwaway rigs pin `60/64` and `26` … and now fail closed against a live `71/75` and `31`"* | **the live pair is now `91/95` and `35`**, and a third pin (`m_loan`) has joined them. Correct as history, stale as a statement about today. |
| `.softhouse/capture/t371-t367-conditions/README.md:15-16` | `je 71/75  cs 359/359` | correct as the transcript of T371's run; stale as a statement about now. |
| `.softhouse/reference-oracle.md:912-913` | `m_portfolio_command_source 347→351`, `acc_gl_journal_entry 60/64 … never moved` | already superseded by T363's markers; T388 moves the same counters further. |

**THREE OF THESE ARE PRINTED BY THE HARNESS ON EVERY CONFORMANCE RUN**, pass or fail, as
measured fact — the `ledger.accrual.entry` and `accounting.path.loan.repayment` evidence
strings. That is what makes them worse than a stale comment.

**NONE OF THEM IS REPAIRED BY T388, AND THAT IS A GRANT BOUNDARY.** `.softhouse/vectors/` is
held by a concurrent worker (T360) and `t363-oracle-baseline/instruments/` by T381. Every one
is handed to the promotion task as required work, listed in the handoff.

### C. Checked and NOT affected — verified rather than assumed

- **No promoted vector reads any of `L28`, `L29`, `L30`, `L31`.** Every ledger vector selects
  legs by an explicit `transaction_id`; none names any of the four
  [`out/T388-D01-forbidden-set.txt` enumerates all 64 vectors].
- **No promoted vector grades an account BALANCE.** LDG-01's `_note` says so outright and gate
  G-12 is open on the running-balance columns, so the vector schema has no field that could
  move when an account gains rows.
- **The harness reads no database.** `conformance.sh` reaches the oracle at exactly one place,
  an HTTP health probe; `notgraded.go`'s account-activity measurement is built from
  `legsByAccount` over the **loaded vectors**, not from SQL
  [`nexus/internal/apps/ledger/conformance/notgraded.go:222-233`]. So no printed *count* can
  move because a row was added; only the hand-written *prose* in § B can.
- **`inadmissible_product_ids: [22, 23, 24, 27, 28]`** in `PIN-ledger.json` is untouched.
  Product 63 is new and is not on that list; nothing was promoted, so nothing was admitted.
- **No existing product was retyped and no existing GL account was edited** — the A2-26 hazard
  (GL account 2 flipped ASSET → INCOME underneath five live mappings). Every write here is an
  INSERT.
- **`acc_gl_closure` remains `0 rows / max null`** and `m_office` remains 1.
- **Currency:** the ledger still carries exactly `MNT` (89) and `USD` (2); every one of T388's
  twenty legs is MNT. T352's USD row is still the only non-MNT pair.
- **No deposit or savings behaviour was touched.** The tenant is an NBFI (ББСБ) and accepting
  deposits is prohibited (Law on Non-Banking Financial Activities Art. 12.1.3 / 12.1.4). This
  task created a LOAN product and a LOAN. No savings account, no deposit endpoint, and no
  string produced here describes anything as insured, protected or guaranteed.

---

## 7. Re-derivation

Every probe is re-runnable from this directory, but **the ids will differ** — the oracle
assigns them — so a re-run is a claim about the LEGS and the SLOTS, never about an id. And the
`T388-*` idempotency keys are **burned**: re-running `20-create-glaccounts.sh` against this
tenant will not re-create anything, it will hit
`exceptionWhenTheRequestAlreadyProcessed`. To re-derive from scratch, use fresh keys on a
throwaway instance.

```
python3 10-mkreq-glaccounts.py                       # the thirteen GL bodies
python3 11-derive-forbidden-set.py --check 35,...,47 # the forbidden set + disjointness
bash    20-create-glaccounts.sh                      # thirteen POST /glaccounts
bash    cap11.sh <NAME> POST /loanproducts req/P01-accrual-product.json <KEY>
bash    cap11.sh <NAME> POST /clients      req/C01-client.json          <KEY>
bash    cap11.sh <NAME> POST /loans        req/L02-…                    <KEY>
bash    cap11.sh <NAME> POST '/loans/8?command=approve'  req/L03-approve.json  <KEY>
bash    cap11.sh <NAME> POST '/loans/8?command=disburse' req/L04-disburse.json <KEY>
bash    cap11.sh <NAME> POST /runaccruals   req/A01-runaccruals-till-15-april-2026.json <KEY>
bash    capsql.sh <NAME> sql/q6-t388-accrual-entries.sql
bash    30-casualty-sweep-t388.sh                    # run AFTER git add -A
```
