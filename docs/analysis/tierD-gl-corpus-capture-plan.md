# Tier D — GL / Journal-Entry Golden-Vector Capture Plan (mined from the Fineract test corpus)

**Task:** T488. **Purpose:** hand the next **oracle-reaching** fire — the local launchd fire on Buyan's Mac,
the only fire that reaches a live Fineract instance + PostgreSQL — an executable capture plan for the
GL/accounting context, so that scarce oracle time is spent *executing* a plan rather than *deciding* one.

**This fire captured nothing and could not have.** It ran in the cloud sandbox. **Probed this session, not
assumed from the fire log:** `/var/run/docker.sock` **absent** (the `docker` CLI is on `PATH` but has no
daemon to talk to); `127.0.0.1:5432` **connection refused**; `127.0.0.1:8443` **connection refused**.
`[VERIFIED: ls /var/run/docker.sock → No such file or directory; bash /dev/tcp probes on both ports →
Connection refused]` Per `.softhouse/reference-oracle.md` § *Reachability by fire*, that makes vector work
impossible here and corpus mining the correct use of the fire.

**Pinned checkout.** `/home/user/fineract` at **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**
`[VERIFIED: git -C /home/user/fineract log -1 --format=%H → 426a23544e8426a38ae43ae404670a0a7e85b9eb;
git status --porcelain → empty]`

**Context.** The GL/accounting bounded context, contract **DEC-2** (`docs/adr/DEC-2-gl-accounting-adapter.md`,
revision 5 per `.softhouse/vectors/PIN-ledger.json`). Vector store: `.softhouse/vectors/ledger/`,
schema `gerege.ledger.vector/v1`.

**Companion documents this one does not duplicate.**
`docs/analysis/tier0-vector-capture-plan.md` is the house style and covers the loan-schedule seam.
`.softhouse/reference-oracle.md` carries the oracle's pin, connection facts, and the **probe policy** that
governs every write proposed below. `docs/adr/DEC-2-gl-accounting-adapter.md` carries the graded predicates
`G-01…G-12` and the invariants `I-1…I-7` that each case below names.

---

## 0. The rule this document is written under

> **A golden vector is only valid when its expected value is observed from the reference oracle.**
> No such observation was available to this fire, so **this document contains no expected values at all.**

**There is no "expected" column anywhere below, and its absence is deliberate.** Fineract's test corpus is
full of assertion literals — `1000.0`, `500.00`, `BigDecimal.TEN`, `originalEntryCount * 2`. Every one of
them is *a number somebody typed into a test file*, not an output the oracle produced under **our** tenant
parameters, **our** currency, **our** rounding mode and **our** `MathContext`. Copying such a literal into a
capture plan as an expected value manufactures a golden vector out of thin air. Three labels, and only three,
appear below:

| Label | Meaning | Trust as a vector value |
|---|---|---|
| `TEST-ASSERTION` | A literal a Fineract **test file** asserts, cited with `FILE:LINE`. It is a fact about that file. | **NONE.** Never promoted, never transcribed into a vector, never used as a target. Its only use is to say *what behaviour the test was aiming at*, which is how the case was found. |
| `SOURCE-DERIVED HYPOTHESIS` | A behaviour read out of Fineract **main** source, cited with `FILE:LINE`. | **NONE as a value.** It predicts a *shape* (how many legs, which flag moves), which the capture then confirms or refutes. A capture that only confirms a hypothesis it was designed around proves less than one that could have refuted it — so each case states what observation would refute it. |
| `TO_BE_CAPTURED` | Not present anywhere. The oracle run must produce it. | No value is stated here. |

**Instruction to the capture fire.** If you find yourself about to write a number into a vector's `expect`
block that you did not read out of a `curl` response body or a `psql` result set **taken in that same run**,
stop. That is the failure mode this whole document is arranged to prevent.

---

## 1. The mining record

### 1.1 Measured size of the corpus mined

```
find . -name '*.java' -path '*src/test*' | wc -l                    →    1254
find . -name '*.java' -path '*src/test*' -print0 | xargs -0 cat | wc -l →  320601
find integration-tests/src/test -name '*.java' | wc -l              →     533
find integration-tests/src/test -name '*.java' | xargs wc -l | tail -1 →  192234
find . -name '*.feature' | wc -l                                    →     158
find . -name '*.feature' -print0 | xargs -0 cat | wc -l             →  200763
```
`[VERIFIED: commands run in /home/user/fineract during this session]`

**CLAUDE.md's "~321k test LOC" figure reconciles exactly: 320,601 lines across 1,254 `src/test` Java files.**

**A second corpus exists that the "~321k test LOC" figure does not cover, and it is larger than the
integration-test corpus for GL purposes:** the Cucumber feature files under
`fineract-e2e-tests-runner/src/test/resources/features/` — 158 files, 200,763 lines, of which **1,427 lines
mention journal entries** across **56 feature files**.
`[VERIFIED: grep -ri "journal" --include=*.feature . | wc -l → 1427; grep -ril "journal\|accounting" --include=*.feature fineract-e2e-tests-runner | wc -l → 56]`
These carry GL expectations as **Gherkin data tables** with `| Type | Account code | Account name | Debit | Credit |`
columns — the most structured statement of Fineract's posting behaviour anywhere in the tree. See §1.4(e).

### 1.2 Where I looked — including the places that were empty

| Location | What I searched for | Result |
|---|---|---|
| `fineract-accounting/src/test` | any test at all | **1 file, 88 LOC** — `GLAccountWritePlatformServiceJpaRepositoryImplTest.java`. The accounting module's 149 main files / 12,752 main LOC have essentially **no unit tests of their own**. |
| `fineract-provider/src/test/.../accounting/**` | journal-entry / GL tests | 5 files: 2 `journalentry/*Test`, 2 `journalentry/service/*Test`, 1 `common/AccountingFinanciaActivityStepDefinitions.java` (40 LOC, 0 `@Test` — Cucumber glue, no expectations) |
| `integration-tests/src/test/.../integrationtests/accounting/` | the dedicated accounting package | **2 files only**: `GLAccountIntegrationTest.java` (132 LOC), `AccountingRuleIntegrationTest.java` (76 LOC) |
| `integration-tests/src/test` — `grep -rl JournalEntryHelper` | every test that reads journal entries back | **30 files, 33,910 LOC** (list in §1.3) |
| `integration-tests` + `fineract-provider/src/test` — `grep -rn glclosures` | a GL-closure integration test | **ZERO HITS.** No test in the tree exercises `POST/GET/DELETE /glclosures`. The closure behaviour this program has captured (`LDG-06`, `LDG-REFUSE-04`, `LDG-REFUSE-06`) has **no counterpart in Fineract's own test corpus** and was found by source reading, not by mining. |
| `integration-tests` — `grep -rn journalentries` | direct `POST /journalentries` from a test | **Exactly one call site**: `JournalEntryHelper.createJournalEntry` (`JournalEntryHelper.java:192-194`), used by **one** test — `GLAccountIntegrationTest.testDeleteGLAccountWhileThereIsJournalEntry` (`:109-125`), and there only to make a delete fail. Every other journal entry in the whole integration corpus is a **side effect of a loan/savings command**. **Fineract's own tests never post a manual journal entry for its own sake, and never reverse one.** |
| `fineract-client/src/main/java/.../models/` | the wire model for a journal entry leg | **DIRECTORY ABSENT** — the client models are generated at build time and are not in the checkout. See §1.4(d) and §8 item 3. |
| `fineract-e2e-tests-runner/src/test/resources/features/` | Gherkin GL tables | 56 of 158 feature files, 1,427 journal lines |

### 1.3 Files opened and read, with a verdict on each

`M` = mined (a case below cites it). `R` = read and rejected, with the reason.

| # | Path (relative to `/home/user/fineract`) | LOC | `@Test` | Verdict |
|---|---|---:|---:|---|
| 1 | `integration-tests/.../integrationtests/JournalEntryReversalOrderingIntegrationTest.java` | 184 | 1 | **M** — §3 group R |
| 2 | `integration-tests/.../integrationtests/accounting/GLAccountIntegrationTest.java` | 132 | 4 | **M** — §3 group A, and the only direct `POST /journalentries` in the corpus |
| 3 | `integration-tests/.../integrationtests/AccountingScenarioIntegrationTest.java` | 1302 | 11 | **M (partial)** — 5 loan tests mined (§3 group S); 5 savings/deposit tests **rejected**, see §1.4(a); 1 share-account test deferred to Tier B |
| 4 | `integration-tests/.../integrationtests/LoanChargesMultipleDebitAccountsTest.java` | 856 | 14 | **M** — §3 group S, charge-specific GL resolution |
| 5 | `integration-tests/.../integrationtests/LoanChargeOffAccountingTest.java` | 1078 | 9 | **M** — §3 group C |
| 6 | `integration-tests/.../common/accounting/JournalEntryHelper.java` | 201 | — | **M** — the read-back shapes, and the tenant defect in §1.4(b) |
| 7 | `fineract-provider/.../accounting/journalentry/CreateJournalEntriesForChargeOffLoanTest.java` | 135 | 3 | **M** — §3 group C, slot routing incl. the fraud branch |
| 8 | `fineract-provider/.../accounting/journalentry/CreateJournalEntriesForTransferLoanTest.java` | 135 | 4 | **M** — §3 group T, transfers-suspense routing + a negative |
| 9 | `fineract-provider/.../journalentry/service/AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoanTest.java` | 790 | 22 | **M (pointer only)** — working-capital-loan is Tier B, but 3 of its 22 tests name behaviours this context needs: `testReversalCreatesInverseEntriesAndMarksOriginalReversed` (`:298`), `testReversalKeepsItsMirrorsLive` (`:779`), `testAdvanceAccountingUsesPaymentChannelFundSource` (`:371`) |
| 10 | `fineract-accounting/.../glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImplTest.java` | 88 | 1 | **M** — §3 group A, the *accepting* side of GL-account delete |
| 11 | `integration-tests/.../integrationtests/accounting/AccountingRuleIntegrationTest.java` | 76 | 1 | **M (weak)** — §3 `TDG-A5`; asserts only `resourceId != null` and `size() > 0`, no money |
| 12 | `integration-tests/.../integrationtests/WorkingCapitalLoanRepaymentAccountingTest.java` | 404 | 6 | **R** — Tier B (working-capital-loan). Names one shape worth re-using later: `testRepaymentWithNoAccountingCreatesNoJournalEntries` (`:306`), an absence probe. |
| 13 | `integration-tests/.../integrationtests/WorkingCapitalLoanChargeOffAccountingTest.java` | 494 | 12 | **R** — Tier B |
| 14 | `fineract-provider/.../journalentry/service/AccountingProcessorHelperTest.java` | 125 | 2 | **R** — both tests are `populateSavingsDtoFromMap` transfer-classification on **savings** (`:75`, `:89`), fully mocked, no money math and no GL account. Savings is out (§1.4(a)). |
| 15 | `fineract-provider/.../accounting/common/AccountingFinanciaActivityStepDefinitions.java` | 40 | 0 | **R** — Cucumber glue only, no expectations |
| 16 | `fineract-e2e-tests-runner/.../features/LoanWriteOff.feature` | — | — | **M (sampled)** — read `:64-82` to establish the Gherkin GL-table shape; see §1.4(e) |
| 17 | `integration-tests/.../integrationtests/{FixedDepositTest,RecurringDepositTest,SavingsAccrual*,SavingsInterestPostingJob*,savings/base/*}` | 7,489 | 97 | **R — LEGAL.** Deposit/savings. §1.4(a). |
| 18 | `integration-tests/.../integrationtests/{ClientLoanIntegrationTest,BaseLoanIntegrationTest,SchedulerJobsTestResults,ClientLoanChargeRefundIntegrationTest,LoanAccount*,LoanChargeSpecificDueDateTest,AccountTransferTest,ShareAccountChargeRoundingTest,investor/*,client/feign/*}` | 18,000+ | — | **NOT OPENED — declared, not silently omitted.** They reference `JournalEntryHelper` but their primary subject is loan lifecycle, transfers, shares or the Feign client. They are a **second-wave** source once groups R/C/T/S are captured. `[UNVERIFIED: their internal assertion style]` |

**Main-source files read (not tests), because the recipes depend on them:**

| Path | Lines read | What it settled |
|---|---|---|
| `fineract-provider/.../accounting/journalentry/api/JournalEntriesApiResource.java` | `:75`, `:112`, `:170-177`, `:192-220`, `:222-240`, `:247`, `:263`, `:282-298` | The complete POST surface: 4 commands, listed in §1.4(c) |
| `fineract-provider/.../accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java` | `:343-356`, `:358-378`, `:380-428`, `:432-461`, `:525-530` | The reversal write path — §1.4(f), the whole of group R |
| `fineract-accounting/.../accounting/journalentry/domain/JournalEntryRepository.java` | `:28-35` | `findUnReversedManualJournalEntriesByTransactionId` filters `reversed=false and manualEntry=true` |
| `fineract-accounting/.../accounting/journalentry/command/JournalEntryCommand.java` | `:37-57` | The request shape: `BigDecimal amount`, `SingleDebitOrCreditEntryCommand[] credits/debits`, one scalar `currencyCode` |
| `fineract-accounting/.../accounting/journalentry/data/JournalEntryData.java` | `:50`, `:73-77` | Server-side response money is `BigDecimal`; the two running-balance columns and `runningBalanceComputed` live here |
| `fineract-provider/.../loanaccount/api/LoanTransactionsApiResource.java` | `:94` | `CHARGE_OFF_COMMAND_VALUE = "charge-off"` |

### 1.4 The structural findings that shape every recipe below

**(a) The savings/deposit half of the accounting test corpus is unusable to us, and the reason is LEGAL, not
technical.** `AccountingScenarioIntegrationTest` alone spends 5 of its 11 tests on savings, fixed-deposit and
recurring-deposit accounting flows (`:284`, `:377`, `:475`, `:548`, plus `:1238` on shares). CLAUDE.md's
tenant ratification is **NBFI (ББСБ)**, for which accepting deposits is prohibited — Law on Non-Banking
Financial Activities **Art. 12.1.3 / 12.1.4**. `.softhouse/reference-oracle.md` § *POLICY* item 2 states the
operational consequence in one line: **"No deposit or savings behaviour"** against this tenant. Porting that
code is in scope; **capturing its behaviour by exercising it on a live instance is not**, and no case below
does. This removes roughly a third of the mined surface, and it removes it on grounds no later agent may
re-litigate.

**(b) Every read-back URL in Fineract's own test helper hard-codes `tenantIdentifier=default`.**
`JournalEntryHelper.java:140`, `:163` and `:185` each append `"&tenantIdentifier=default"`. Per
`.softhouse/reference-oracle.md` § *Connection facts*, tenant `default` on our instance is `Asia/Kolkata`
(+05:30, **not** a permitted zone), runs `HALF_EVEN`, and its database `fineract_default` holds **0 GL
accounts and 0 journal entries**. **A recipe copied verbatim out of these tests would read the wrong tenant
and find nothing, and nothing downstream would say so.** Every recipe below sends
`Fineract-Platform-TenantId` explicitly and states the tenant in its attestation; none uses a query parameter
copied from a Fineract test.

**(c) The POST surface of `/journalentries` is exactly four commands, and this program has captured two.**
`[VERIFIED: JournalEntriesApiResource.java:203-220 and :231-240]`

| Command | Endpoint | Covered by an existing `ledger` vector? |
|---|---|---|
| *(no `command` param)* — create a manual entry | `POST /journalentries` | **YES** — `LDG-01`, `LDG-04`, `LDG-DIV-01`, `LDG-REFUSE-01/02` |
| `defineOpeningBalance` | `POST /journalentries?command=defineOpeningBalance` | **YES** — `LDG-05`, `LDG-REFUSE-03` |
| `updateRunningBalance` | `POST /journalentries?command=updateRunningBalance` | **NO** — and §3 group B explains why it stays uncaptured |
| `reverse` | `POST /journalentries/{transactionId}?command=reverse` | **NO** — the largest gap. Group R. |

**(d) The generated client turns journal-entry amounts into a floating-point accessor, and the test corpus
propagates it.** `LoanChargesMultipleDebitAccountsTest` computes its own debit/credit totals as
`BigDecimal.valueOf(entry.getAmount())` at `:66`, `:69`, `:132`, `:186`, `:299`, `:312`, `:352`, `:363`,
`:521`, `:572`, `:590`, `:633`, `:666`, `:742`, `:811`, `:838` — sixteen sites.
`BigDecimal.valueOf(double)` is the double overload; `getAmount()` therefore hands back a floating value on
the client side even though `JournalEntryData.java:50` is a `BigDecimal` on the server. **Consequence for
every recipe below: capture through `curl`, recording the RAW RESPONSE BYTES, never through the generated
Fineract client and never through a JSON parser that widens to `float`.** This is the discipline
`LDG-01`'s own `_note` already records ("Response legs read from the RAW BYTES") and the reason `cap8.sh`
exists. `[UNVERIFIED: the exact declared Java type of the generated accessor — the generated model directory
is absent from the checkout, see §8 item 3. What is verified is the call shape at the sixteen sites above.]`

**(e) The Gherkin GL tables are the densest expectation source in the tree, and they are the *worst* thing to
copy.** A representative block, `fineract-e2e-tests-runner/src/test/resources/features/LoanWriteOff.feature:78-82`:

```gherkin
Then Loan Transactions tab has a "DISBURSEMENT" transaction with date "01 January 2023" which has the following Journal entries:
  | Type      | Account code | Account name              | Debit  | Credit |
  | ASSET     | 112601       | Loans Receivable          | 1000.0 |        |
  | LIABILITY | 145023       | Suspense/Clearing account |        | 1000.0 |
```

It is tabular, it names the classification, the GL code and the side — exactly the fields
`gerege.ledger.vector/v1` wants. **And `1000.0` is a `TEST-ASSERTION`, in EUR** (the scenario disburses
`"1000" EUR` at `:71`), on a stock demo chart of accounts, at whatever `MathContext` that harness runs under.
It is not an MNT amount, not our tenant's GL ids, and not observed. The right use of these 1,427 lines is as
a **case-discovery index** — they enumerate which transaction types produce which slot pairs — and the wrong
use is as a value source. §3 uses them the first way. Systematically indexing all 56 files is a follow-up
task, not this one (§8 item 5).

**(f) The reversal write path, read from source — this is what group R is designed to confirm or refute.**
`SOURCE-DERIVED HYPOTHESIS`, from `JournalEntryWritePlatformServiceJpaRepositoryImpl.java`:

1. `revertJournalEntry(JsonCommand)` at `:343` loads `findUnReversedManualJournalEntriesByTransactionId` (`:345-346`),
   whose JPQL is `... where transactionId = :transactionId and reversed = false and manualEntry = true`
   `[VERIFIED: JournalEntryRepository.java:30]`.
2. If that list has `size() <= 1` it throws `JournalEntriesNotFoundException` (`:349-351`). So **a second
   reversal of the same transaction, and a reversal of any non-manual (accounting-path) transaction, both
   take the not-found branch.**
3. The reversal legs are written under a **NEWLY MINTED transaction id** — `generateTransactionId(officeId)`
   at `:382` — and that id, not the original, is what the response carries (`:352-355`).
4. Each reversal leg copies the original's office, payment detail, GL account, currency, amount and
   **transaction date**, flipping only the side: an original `DEBIT` produces a `CREDIT` (`:409-413`), else a
   `DEBIT` (`:415-419`). `manualEntry` is forced `true` on the reversal legs (`:383`).
5. The original row is then mutated: `setReversed(true)` (`:423`) and `setReversalJournalEntry(...)` (`:424`).
6. A branch closure blocks the reversal too, on the original's transaction date, with the same
   `!isBefore(closingDate, transactionDate)` inclusive test (`:391-399`).

**What this hypothesis is FOR.** DEC-2 §4.4 `I-5` says *"a correction adds a leg pair; it never mutates
one"*, and `capabilities-ledger.json` records that the existing corpus cannot separate *"flags and adds"*
from *"flags and rewrites"* because it holds only a post-reversal snapshot. Steps 4-5 predict **flags and
adds**. `TDG-R1` is built to be able to **refute** that: it records every column of every original leg
*before* and *after*, so a rewrite of `amount`, `gl_account_id`, `entry_type`, `entry_date` or
`currency_code` on an existing row would show up as a diff. If the before/after diff is confined to
`reversed` and `reversal_id`, the hypothesis survives on evidence rather than on reading.

---

## 2. What the ledger corpus already has, and the six gaps this plan aims at

`.softhouse/vectors/capabilities-ledger.json` (`dec2_revision: 5`) is the authority on what a ledger vector
may claim. It lists 14 capabilities; **8 are in the graded domain and 6 are not.** The six that are not are
the target set of this plan, and the mined test corpus maps onto them almost exactly.

| Capability | `in_graded_domain` | Why not (quoted in substance from `capabilities-ledger.json`) | Cases below |
|---|---|---|---|
| `ledger.reversal.entry` | **false** | A reversal exists in the corpus (A2-348/A2-349) but only as a **snapshot**; the other half of `I-5` — *adds vs mutates* — "needs the WRITE path, not a snapshot" | **R1–R5** |
| `ledger.charge.off` | **false** | "UNMAPPED ON BOTH ADMISSIBLE PRODUCTS… unreachable without a NEW product" | **C1–C4** |
| `ledger.transfers.suspense` | **false** | gl 17 has rows only as a **manual** target; "NO accounting-path entry at all" | **T1–T4** |
| `ledger.slot.resolution` | **false** | Partially graded on the accrual family for product 63; still ungraded: the **payment-type precedence chain**, the **cash family** ("no cash-based accounting-path vector exists"), the financial-activity branch, charge/reason precedence | **S1–S6** |
| `ledger.multi.currency.entry` | **false** | **Structurally impossible at this seam** — a leg has no currency field; `currencyCode` is one scalar on the enclosing command `[VERIFIED by T352: SingleDebitOrCreditEntryCommand.java:33-35, JournalEntryCommand.java:40]` | **X1–X2, re-scoped** — see §3 group X |
| `ledger.running.balance` | **false** | "PERMANENTLY REFUSED WHILE GATE **G-12** IS OPEN"; the vector schema has **no field** for either balance column; `/glaccounts?fetchRunningBalance=true` is **HTTP 500 on PostgreSQL** | **B1 — DE-SCOPED**, §3 group B |

**Two of the six cannot be closed by any capture campaign, and saying so is part of the plan.**
`ledger.multi.currency.entry` names a shape the seam cannot produce; `ledger.running.balance` is blocked by
an open gate and by a schema with nowhere to put the value. Proposing captures for them would burn oracle
time on vectors that `admit.go` would refuse on arrival. §3 groups X and B replace them with the questions
that *are* answerable, and rank them accordingly.

---

## 3. Case inventory

Ids are `TDG-<group><n>` (Tier D, GL). Every case states: the behaviour, the mined origin, the DEC-2
predicate or invariant it feeds, and **why it is worth an oracle round-trip**. Recipes are §4.

**Legend for `Rig`:** `THROWAWAY` = a disposable instance per §4.1 (accepted writes that cannot be
un-accepted belong there — reference-oracle POLICY item 1.3). `STANDING` = the shared `gerege` instance on
`:8443`, permitted only when the question is about *that tenant's accumulated state*. `READ-ONLY` = no write
at all.

### Group R — reversal (`ledger.reversal.entry`, invariant `I-5`)

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-R1** | Reverse a 3-leg **manual** MNT entry. Does the oracle **append** mirrored legs under a new transaction id and only flag the originals, or does it **rewrite** them? Every column of every original leg recorded before and after. | `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:380-428` (source); the shape `A2-348`/`A2-349` took a snapshot of | `I-5`, `ledger.reversal.entry` | THROWAWAY |
| **TDG-R2** | Reverse the **same** transaction a second time. Source predicts the `size() <= 1` branch → `JournalEntriesNotFoundException`. Refusal code + message + HTTP status recorded. | `:349-351` + `JournalEntryRepository.java:30` (`reversed=false`) | `ledger.refusal.parity`, DEC-2 §4.9 | THROWAWAY |
| **TDG-R3** | Reverse an **accounting-path** (non-manual) transaction — e.g. a loan disbursement's `L<n>` — through `POST /journalentries/{txn}?command=reverse`. Source predicts the same not-found branch, because the query filters `manualEntry = true`. **This is a different refusal from R2 with the same predicted message**, and a port that implements only one of the two conditions passes on one and fails on the other. | `JournalEntryRepository.java:30`; contrasted with `JournalEntryReversalOrderingIntegrationTest.java:96` which reverses through the **loan** endpoint instead | `ledger.refusal.parity` | THROWAWAY |
| **TDG-R4** | Reverse a **loan repayment** through the loan endpoint (`reverseLoanTransaction`), then re-read journal entries **by the original `L<n>` transaction id**. The Fineract test asserts the entry count **doubles** under the *same* transaction id — structurally different from R1, where the reversal legs land under a *new* id. Record leg count, ids, sides, amounts, `reversed` flags and the ordering the response comes back in. | `JournalEntryReversalOrderingIntegrationTest.java:69,84,90,96,102`; `TEST-ASSERTION` at `:106` is `originalEntryCount * 2` | `I-5`, `I-1`, `ledger.accounting.path.loan.repayment` | THROWAWAY |
| **TDG-R5** | Reversal **under a closure**: post a manual entry, create a `GLClosure` on or after its transaction date, then attempt the reversal. Source predicts `ACCOUNTING_CLOSED` on the *original's* date with the **inclusive** boundary. | `:391-399`; the inclusive boundary is already an observed fact of this program (`LDG-REFUSE-04`) but has **never been observed on the reversal path** | `ledger.refusal.parity`, `ledger.opening.balance.and.closure` | THROWAWAY **only** — a closure consumes `acc_gl_closure_id_seq` irreversibly on the standing tenant (reference-oracle § *ORACLE STATE MOVED BY T287*) |

**Why group R is worth the round-trip.** "Corrections are reversing entries" is one of CLAUDE.md's
non-negotiables and `I-5` is one of DEC-2's five obliged invariants. Today it is graded by **nothing**.
R1 is the single capture that can move it, and R2/R3/R5 are three refusals on a surface where DEC-2 §4.9's
taxonomy currently has no observed reversal refusal at all.

### Group C — charge-off (`ledger.charge.off`)

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-C1** | `POST /loans/{id}/transactions?command=charge-off` on a loan whose product **maps `chargeOffExpenseAccountId`**. Record every leg. Source-level routing under test: credit `LOAN_PORTFOLIO`, debit the charge-off expense slot. | `CreateJournalEntriesForChargeOffLoanTest.java:80,99-107`; `LoanChargeOffAccountingTest.java:109` (periodic accrual), `:637` (cash) | `ledger.charge.off`, `ledger.slot.resolution`, `G-11` | THROWAWAY |
| **TDG-C2** | The same, on a loan **marked as fraud**. The mock test pins that the routing switches to `CHARGE_OFF_FRAUD_EXPENSE`. A port that ignores the fraud flag posts to the same account and is otherwise byte-identical — so this pair is a **discriminating** pair, not two similar captures. | `CreateJournalEntriesForChargeOffLoanTest.java:111,129-135`; `LoanChargeOffAccountingTest.java:265` | `ledger.charge.off` | THROWAWAY |
| **TDG-C3** | Charge-off **with a reason code value mapped** (`getChargeOffMappingByCodeValue`). The mock test shows the reason mapping is consulted *first* and, when present, the fraud/expense product slots are not reached. Precedence, not a value. | `CreateJournalEntriesForChargeOffLoanTest.java:89,101` vs `:114,142` (the `null` arms) | `ledger.slot.resolution` (charge/reason precedence level) | THROWAWAY |
| **TDG-C4** | A **repayment after charge-off**: does income get recognised, and do recovery slots appear? The Fineract test is named `noIncomeRecognitionAfterChargeOff`. | `LoanChargeOffAccountingTest.java:722`; `:498` / `:637` for the goodwill-credit and cash-basis arms | `ledger.charge.off`, `I-1` | THROWAWAY |

**Why.** `capabilities-ledger.json` says charge-off is "UNMAPPED ON BOTH ADMISSIBLE PRODUCTS … unreachable
without a NEW product" — i.e. the blocker is a **product-configuration** one, which a throwaway instance
removes entirely and the standing tenant cannot (creating a product on `gerege` is a permanent append, and
retyping one is explicitly forbidden by the POLICY).

### Group T — transfers suspense (`ledger.transfers.suspense`)

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-T1** | **Initiate** a client transfer holding an active loan. Predicted routing: debit `TRANSFERS_SUSPENSE`, credit `LOAN_PORTFOLIO`, **at the transaction office, not the loan office** (the mock passes office 2 while the loan sits on office 1). | `CreateJournalEntriesForTransferLoanTest.java:77,83-85`; offices at `:53-54` | `ledger.transfers.suspense`, `G-11` | THROWAWAY (needs a **second office**) |
| **TDG-T2** | **Approve** the transfer. Predicted routing is the **mirror** of T1. | `:89,95-97` | same | THROWAWAY |
| **TDG-T3** | **Withdraw** the transfer. The mock asserts withdrawal routes **the same way as approval**, not the same way as initiation — a genuinely counter-intuitive pairing and therefore a good discriminator. | `:101,107-109` | same | THROWAWAY |
| **TDG-T4** | A transfer whose **principal amount is null** → **no journal entries at all**. An **absence** observation, which reference-oracle POLICY item 1.2 prefers over a difference probe. | `:113,119-120` (`verify(helper, never())...`); the same shape as `WorkingCapitalLoanRepaymentAccountingTest.java:306` | `ledger.transfers.suspense` | THROWAWAY |

**Why a throwaway is mandatory here.** T1–T3 need **two offices**. On the standing tenant `m_office` has
exactly one row, and `.softhouse/reference-oracle.md` records that `OfficesApiResource` exposes **no
`@DELETE`** — creating an office there trades a reversible mutation for an irreversible one.

**A note that keeps this group inside the NBFI ruling.** These are **client/loan transfers between offices**,
routed through `AccrualBasedAccountingProcessorForLoan`. They are not savings account transfers and no
deposit account is involved. `AccountTransferTest.java` (savings-to-savings) is **not** mined and must not be.

### Group S — slot resolution (`ledger.slot.resolution`, predicates `G-03`, `G-05`, `G-06`, `G-11`)

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-S4** | **`FUND_SOURCE` resolution with NO payment type.** DEC-2 `G-06` records this as *"genuinely undecided"*: the oracle issues the payment-type finder with a null argument and no null guard (`AccountingProcessorHelper.java:1199-1206`), and DEC-2 §9 item 2 states that **neither reading is settled from the pinned checkout and no capture separates them**. One capture settles a predicate the contract currently refuses on. | DEC-2 §4.2 `G-06` + §9 item 2; the behaviour is exercised implicitly by every disbursement in `AccountingScenarioIntegrationTest` | `G-06`, `ledger.slot.resolution` | THROWAWAY |
| **TDG-S1** | **The CASH family end to end.** `capabilities-ledger.json`: *"no cash-based accounting-path vector exists"*, and `G-05` is the predicate that selects the family. Disburse + repay on a cash-based product; record every leg with its slot code and decoded slot name. | `AccountingScenarioIntegrationTest.java:1114`, product built at `:1224-1231` (`withAccountingRuleAsCashBased`) | `G-05`, `ledger.slot.resolution` | THROWAWAY |
| **TDG-S1b** | The **absence** half of S1: a **waive-interest** on a cash-based loan produces **no journal entries**. The Fineract test's own comment says *"waive of fees and interest are not considered in cash based accounting"* and it asserts the absence directly. Cheap, absence-shaped, and it discriminates a port that posts on every transaction type. | `AccountingScenarioIntegrationTest.java:1187-1191` (`ensureNoAccountingTransactionsWithTransactionId`) | `ledger.slot.resolution` | THROWAWAY (same instance as S1) |
| **TDG-S2** | **`ACCRUAL_UPFRONT`.** DEC-2 `G-03` refuses it **for one reason only: it is UNCAPTURED** (revision 2's own words). The whole term interest is accrued at **disbursement** rather than periodically — a different leg set on the same event as S1. | `AccountingScenarioIntegrationTest.java:150`, entries at `:185-193` | `G-03`, `ledger.slot.resolution` | THROWAWAY |
| **TDG-S3** | **Payment-channel → fund-source precedence** (STEP 2 of `resolveProductAccount`). `capabilities-ledger.json` records that product 63 has **no** `paymentChannelToFundSourceMappings` at all, so this step "is never entered". Configure two payment types mapped to two different fund-source accounts and repay once through each. | `AccrualWithDeferredRevenue…Test.java:371` (`testAdvanceAccountingUsesPaymentChannelFundSource`) names the behaviour; `LoanChargesMultipleDebitAccountsTest.java:598` (`testAdvancedAccountingRulesOverrideForChargeSpecificGLAccounts`) is its charge-side sibling | `G-06`, `ledger.slot.resolution` | THROWAWAY |
| **TDG-S5** | **Charge-specific GL accounts, and aggregation by GL account.** Two charges mapped to *different* income accounts vs two mapped to the *same* one: does the oracle emit two legs or aggregate into one? The leg **count** is the observation, and it is the thing a naive port gets wrong. | `LoanChargesMultipleDebitAccountsTest.java:87` (`testMultipleChargesCreateChargeSpecificJournalEntries`), `:153` (`testChargeAggregationByGLAccount`), `:322` (`testProportionalDistributionLogic`) | `ledger.slot.resolution`, `I-1` | THROWAWAY |
| **TDG-S6** | **A charge with no GL account mapping**, and **a zero-amount charge**. Two refusal/absence arms named directly by the Fineract test method names. | `LoanChargesMultipleDebitAccountsTest.java:410` (`testMissingGLAccountMappingHandling`), `:447` (`testZeroAmountChargeHandling`), `:372` (`testAccountingImbalanceErrorHandling`) | `ledger.refusal.parity` | THROWAWAY |

**Ranking inside group S is deliberate and S4 is first.** S4 is the only case in this entire document that
closes a predicate DEC-2 explicitly records as **undecidable from the pinned source**. Everything else in
group S closes a coverage gap; S4 closes an *epistemic* one.

### Group A — GL-account admin, the refusal quartet (`ledger.refusal.parity`)

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-A1** | `DELETE /glaccounts/{id}` on a **parent with children** → refused. `TEST-ASSERTION`: the test asserts HTTP **403** and message containing `error.msg.glaccount.glcode.invalid.delete.has.children`. | `GLAccountIntegrationTest.java:72,82-85` | `ledger.refusal.parity` | THROWAWAY |
| **TDG-A2** | Delete an account **mapped to a product** → refused. `TEST-ASSERTION`: **403**, `error.msg.glaccount.glcode.invalid.delete.product.mapping`. | `:91,102-105` | same | THROWAWAY |
| **TDG-A3** | Delete an account **with journal entries logged** → refused. `TEST-ASSERTION`: **403**, `error.msg.glaccount.glcode.invalid.delete.transactions.logged`. | `:109,120-123` | same | THROWAWAY |
| **TDG-A4** | Delete a **clean** account → accepted. The accepting arm; without it A1–A3 could all be satisfied by an implementation that refuses every delete. | `GLAccountWritePlatformServiceJpaRepositoryImplTest.java:74-88`; `GLAccountIntegrationTest.java:47,68,86-87` | `ledger.refusal.parity` | THROWAWAY |
| **TDG-A5** | `POST /accountingrules` and read back. Weak: the Fineract test asserts only `resourceId != null` and `size() > 0`, no money and no posting. Captured only because it is a distinct DEC-2 seam surface and costs two requests. | `AccountingRuleIntegrationTest.java:60-75` | `ledger.journal.entry.readback` | THROWAWAY, last |

**Why these are cheap.** A1–A4 need **no loan, no product lifecycle and no money movement** — four GL
accounts, one parent/child link, one product mapping, one journal entry. They are the highest
refusals-per-minute in the plan, and DEC-2 §4.9's refusal taxonomy is the part of the contract with the
thinnest observational backing.

### Group X — currency, re-scoped because the named capability is unreachable

**`ledger.multi.currency.entry` cannot be closed at this seam and no case below pretends otherwise.**
`SingleDebitOrCreditEntryCommand` carries exactly `glAccountId`, `amount`, `comments`; `currencyCode` is a
single scalar on `JournalEntryCommand` (`:40`). An entry whose legs differ in currency **is not expressible**.
`[VERIFIED by T352 and recorded in capabilities-ledger.json; independently consistent with
JournalEntryCommand.java:37-57 read this session]`

What *is* answerable, and is the question that actually matters for a Go port:

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-X1** | **A currency whose minor-unit digit count is not 2.** `G-08` defines the residue rule *at* `MinorUnitDigits`; every observation this program holds is at MNT's 2. Enable a 0-decimal currency (e.g. JPY/KRW) and a 3-decimal one (e.g. KWD/BHD) on the throwaway tenant, post one balanced 2-leg entry in each, and record what the wire text and the stored column do. A port that hard-codes 2 is byte-identical to a correct one on every capture taken to date; this is the capture that separates them. | Not from a test — from `G-08` and `LDG-DIV-01`'s own scope note. `GLAccountIntegrationTest.java:115-118` posts in **USD**, which is also 2dp and therefore does not discriminate. | `G-07`, `G-08` | THROWAWAY |
| **TDG-X2** | **Sub-minor-unit residue at the production `MathContext`.** T352 observed the oracle accept, persist and serve back a 3-decimal MNT amount. **That observation is only as good as the tenant parameters it was taken under**, and CLAUDE.md requires the parity corpus re-captured at `(19, HALF_UP)` from a fresh calibration. Re-take it under an attested `(19, HALF_UP)` tenant, and additionally record whether the oracle's **own arithmetic** ever *generates* a residue (T352 supplied the third decimal; it was not computed). | `capabilities-ledger.json` § `ledger.money.minor.unit.conversion` (T352's correction) | `G-08`, `ledger.money.minor.unit.conversion` | THROWAWAY |

**Whether to widen `G-07` beyond MNT is a DEC-2 amendment, not a capture decision.** `capabilities-ledger.json`
raises it as `FU-T352-2`. X1 produces the evidence; it does not settle the gate.

### Group B — running balance: DE-SCOPED, with the reasons

| id | Status |
|---|---|
| **TDG-B1** | **DO NOT CAPTURE AS A PARITY VECTOR.** Three independent blockers, any one of which is sufficient: (i) gate **G-12** is open and `capabilities-ledger.json` marks the capability *"PERMANENTLY REFUSED WHILE G-12 IS OPEN"*; (ii) **the `gerege.ledger.vector/v1` schema has no field for either balance column**, so an admissible vector could not express the value even if it were observed; (iii) `/glaccounts?fetchRunningBalance=true` returns **HTTP 500 on PostgreSQL** because `GLAccountReadPlatformServiceImpl.java:127-131` emits MySQL-only `group by … desc` — that reader has never worked on the only database this program permits. Beyond all three, CLAUDE.md's own non-negotiable is that **balances are derived, never written**, and A2-29 already measured the stored balance behaving as a **second source of truth**. |

If a later fire wants `command=updateRunningBalance` characterised at all, it is a **discrimination probe on a
throwaway**, documented as such, ranked below every case above, and it produces **no vector**.

---

## 4. The executable capture recipes

### 4.0 TDG-00 — ATTESTATION. Nothing below is admissible until this passes.

**No vectors are produced by this step and it is not optional.** CLAUDE.md is explicit that captures taken at
precision 12 or 8 are *discrimination probes, not parity vectors*, and that the parity corpus must be
re-captured at `(19, HALF_UP)` **starting with a new C-00 calibration**. A GL capture inherits exactly the
same obligation.

Record, into `out/TDG-00-*` in the capture directory, each as its own artefact:

| # | What to assert | How | Fail-closed on |
|---|---|---|---|
| 1 | Fineract commit of the running image's source | `git -C <checkout> log -1 --format=%H` | ≠ `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
| 2 | Working tree clean | `git -C <checkout> status --porcelain` | non-empty |
| 3 | Health | `GET /actuator/health` → `{"status":"UP",…}` | anything else; **an unreachable oracle is exit 2, never a PASS** |
| 4 | **Engine** | `docker exec <db> psql -U root -c 'select version()'` → **PostgreSQL 18.3** | any MySQL / MariaDB / Oracle Database string |
| 5 | **Driver, from the running container's env, not from a config file** | `FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME` = `org.postgresql.Driver`; `FINERACT_HIKARI_JDBC_URL` starts `jdbc:postgresql://` | anything else |
| 6 | **Prohibited-engine sweep** | no `*ojdbc*` / `*mysql*jar` / `*mariadb*jar` inside the app container; no host listener on `:1521`, `:3306`, `:33060` | any hit |
| 7 | **Tenant identity** — id, identifier, name, **timezone**, database | `select id, identifier, name, timezone_id from tenants` in `fineract_tenants` | timezone ∉ {`Asia/Ulaanbaatar`, `Asia/Hovd`}; identifier not the one the capture declares |
| 8 | **Rounding mode ordinal** | the tenant's stored `RoundingMode` ordinal | ≠ **4** (`HALF_UP`) |
| 9 | **Precision** | `MoneyHelper.PRECISION` is a compile-time **19** `[VERIFIED in CLAUDE.md against fineract-core/.../MoneyHelper.java:35,91-93]`; assert the running build carries it | ≠ 19 |
| 10 | **Currency** | `select code, decimal_places, name from m_currency where code='MNT'` → decimal_places **2** | ≠ 2 |
| 11 | **Business date** | `GET /businessdates` | unrecorded — several cases below are date-relative and are uninterpretable without it |
| 12 | Image digest | `docker inspect --format '{{.Image}}'` on the app container | unrecorded |

**Every capture artefact produced afterwards carries an attestation sidecar naming: path (`ledger_rest_posting`
/ `ledger_rest_admin` / `ledger_db_readback`), instance (`THROWAWAY:<id>` or `STANDING:gerege`), tenant
identifier, timezone, rounding ordinal, precision, currency, image digest, commit, business date.**
`.softhouse/vectors/PIN-ledger.json` has no tenant field today, which is exactly why the sidecar must.

### 4.1 The throwaway rig — build it once, reuse it for every case in groups R, C, T, S, A, X

**A complete, working template already exists in this repository. Copy it; do not invent a second one.**

```
.softhouse/capture/t327-closure-accepting-side/throwaway/
  docker-compose.t327.yml   env.sh   setup.sh   capture.sh   down.sh
  guard-throwaway-isolation.sh   manifest.sh   run-all.sh
```

Copy to `.softhouse/capture/t488-gl/throwaway/` and change **only** the identifiers:

| Field | t327 value | Use for T488 |
|---|---|---|
| tenant identifier | `t327` | **`t488`** — the identifier IS the disclosure; a throwaway capture must never be mistakable for a `gerege` one |
| database | `fineract_t327` | `fineract_t488` |
| containers | `t327-oracle-db` / `t327-oracle-app` | `t488-oracle-db` / `t488-oracle-app` |
| published port | `8444:8443` | **`8444:8443`** — the house convention; t305 and t327 both used it because **only one throwaway runs at a time**. `down.sh -v` the previous one first. |
| `FINERACT_DEFAULT_TENANTDB_TIMEZONE` | `Asia/Ulaanbaatar` | **unchanged** |
| `FINERACT_CONFIG_ROUNDING_MODE` | `"4"` | **unchanged** — this **seeds** the tenant at `HALF_UP` rather than patching it afterwards |

Non-negotiable properties of that template, kept: **no published database port** (the standing db owns 5432);
**no named volume**, so `down.sh -v` destroys it; log volume points at `/tmp`, never into the pinned checkout;
`guard-throwaway-isolation.sh` runs first and **refuses** unless the rig provably cannot touch the standing
stack, and re-checks the standing baseline afterwards.
`[VERIFIED: docker-compose.t327.yml, env.sh, run-all.sh read this session]`

**The compose file is brought up with the `postgresql` profile lineage only.** It is self-contained and does
not `extends:` the pinned checkout's compose; under no circumstances is `docker-compose-mysql*.yml` or
`docker-compose-mariadb*.yml` used, here or anywhere in this program.

### 4.2 The capture instruments — use the existing ones

| Instrument | Path | Use for |
|---|---|---|
| **`cap11.sh`** | `.softhouse/capture/t352-a2-next-tranche/cap11.sh` | **Every HTTP request.** It takes `NAME METHOD PATH BODYFILE IDEMPOTENCY_KEY` and **refuses if the key is absent**. It sends `--data-binary` (so curl does not strip newlines), commits `out/NAME.req` + `.req.sha256` as the exact wire bytes, writes nothing under `out/` until the exchange completed, and records a non-2xx **as data, not as an error**. |
| **`capsql.sh`** | `.softhouse/capture/t352-a2-next-tranche/capsql.sh` | **Every database read-back.** Commits `out/NAME.sql` — the *executed* bytes, not a pointer to a file a later step may rewrite. |
| ~~`cap8.sh`~~ | `.softhouse/capture/tierA-a2/cap8.sh` | **DO NOT USE for a POST.** It sends **no `Idempotency-Key`**, so Fineract mints a random UUID (`IdempotencyKeyResolver.java:36`, `IdempotencyKeyGenerator.java:25-29`) and the write becomes **unattributable forever**. It remains correct for `GET`. |

**`Idempotency-Key` is mandatory on every money-movement POST** (CLAUDE.md) and it is simultaneously the
**only** attribution link between a command row and the task that fired it (reference-oracle POLICY item 2).
Key naming convention for this plan: **`T488-<CASE>-<ARM>`**, e.g. `T488-R1-post-3leg`, `T488-R1-reverse`,
`T488-R2-reverse-again`. One distinct key per request. A reused key proves nothing about idempotency and a
minted UUID names nothing.

`Idempotency-Key` is the pinned oracle's configured header name
`[VERIFIED via T352's cap11.sh header comment: fineract-provider/src/main/resources/application.properties:179,857
→ fineract.idempotency-key-header-name=${FINERACT_IDEMPOTENCY_KEY_HEADER_NAME:Idempotency-Key}, read at
IdempotencyStoreFilter.java:72]`.

### 4.3 What every recipe records — the common field list

This list applies to **every** case; the per-case sections state only what they add.

**From the HTTP exchange (`cap11.sh` writes all of these):** the wire request bytes + sha256; the raw
response bytes; the HTTP status; the `Idempotency-Key` sent; the UTC timestamp; the method and path.

**From the response body of a posting call:** `officeId`, `resourceId`, `transactionId`, and the complete
`changes` block if present — **verbatim, unparsed**.

**From the read-back (`GET /journalentries?transactionId=<txn>&limit=50`), per leg:** `id`, `glAccountId`,
`glAccountCode`, `glAccountName`, `glAccountType`, `entryType.value`, **`amount` as the RAW WIRE TEXT**,
`transactionDate`, `entryDate`, `createdDate`, `manualEntry`, `reversed`, `currency.code`,
`currency.decimalPlaces`, `officeId`, `entityType`, `entityId`, `transactionDetails`.

> **`glAccountType` is EXCLUDED from every leg of `LDG-01`** and the exclusion is recorded in that vector's
> own `_note`. Capture the field, but do not assume it is gradeable — re-read that note before promoting.

**From PostgreSQL (`capsql.sh`), for the same legs, `acc_gl_journal_entry`:** `id`, `account_id`,
`office_id`, `transaction_id`, `type_enum`, **`amount` and `scale(amount)`**, `currency_code`, `entry_date`,
`transaction_date`, `manual_entry`, `reversed`, `reversal_id`, `is_running_balance_calculated`,
`office_running_balance`, `organization_running_balance`, `created_on_utc`.
The two running-balance columns are recorded **as evidence about the oracle's storage**, and are **never**
promoted into a vector — group B, and the schema has no field for them.

**Money discipline, applying to all of the above.** Record `amount` as the **exact wire characters**
(the oracle emits scale 6, e.g. `100000.250000`). Convert to `int64` minor units by **exact integer/string
arithmetic**, refusing any non-zero digit beyond the currency's minor-unit count rather than truncating or
rounding it. **A recipe that parses a money value into a float, or that lets a JSON library widen it, is a
defect in the recipe** — `python3 -c "json.load(f)"` must be called with `parse_float=decimal.Decimal`, the
form `.softhouse/capture/tierA-a2/run-330-*.sh` already uses.

### 4.4 TDG-R1 — the reversal write path (the plan's flagship capture)

**Preconditions.** Throwaway `t488`, TDG-00 passed. MNT enabled, `decimal_places = 2`. **Three DETAIL GL
accounts that permit manual entries**, created fresh in this run and recorded by id and `glCode` (do not
reuse ids from any prior capture directory — `.softhouse/capture/` ids belong to instances that no longer
exist). No closure on the office. Business date recorded.

**Arms, in order. Each is one `cap11.sh` invocation.**

| Arm | Request | Idempotency-Key | Purpose |
|---|---|---|---|
| `R1-a` | `GET /glaccounts/{id}` ×3 | — | The accounts as the oracle describes them **before** anything is posted: `usage`, `manualEntriesAllowed`, `disabled`, `type` |
| `R1-b` | **SQL** — full `acc_gl_journal_entry` row set for the office, before | — | The floor. Without it "these rows are new" is an assumption |
| `R1-c` | `POST /journalentries` — a **3-leg balanced MNT** entry with **non-round minor units on every leg** (two debits + one credit, or the reverse; the split must not be reconstructible by halving) | `T488-R1-post-3leg` | The subject |
| `R1-d` | `GET /journalentries?transactionId=<txn>&limit=50` | — | **The before-state of the originals, at the contract boundary** |
| `R1-e` | **SQL** — the same rows, every column in §4.3 | — | **The before-state of the originals, in the database.** R1 lives or dies on this artefact |
| `R1-f` | `POST /journalentries/{txn}?command=reverse` with body `{"comments":"T488-R1"}` | `T488-R1-reverse` | The act |
| `R1-g` | `GET /journalentries?transactionId=<txn>&limit=50` | — | The originals, after |
| `R1-h` | `GET /journalentries?transactionId=<reversalTxn>&limit=50`, where `<reversalTxn>` is **read out of R1-f's response body**, not guessed | — | The reversal legs |
| `R1-i` | **SQL** — every `acc_gl_journal_entry` row for the office, after | — | The after-state, and the proof that the only new rows are the reversal legs |

**The observation R1 exists to make** is the **column-by-column diff of R1-e against R1-i, restricted to the
original three legs**. Record that diff as its own committed artefact.

- If the diff is confined to `reversed` (f→t) and `reversal_id` (null→id), **`I-5`'s "adds, never mutates"
  survives on evidence** and a reversal vector becomes expressible.
- If **`amount`, `account_id`, `type_enum`, `entry_date`, `transaction_date` or `currency_code` moves on any
  original row**, the source-derived hypothesis in §1.4(f) is **refuted**, and that is a far more important
  finding than a vector. Record it as a finding and do not promote anything.

**Also record, because the source predicts them and a port could get any of them wrong:** whether
`<reversalTxn>` differs from `<txn>` (source says yes, `:382`); whether each reversal leg carries the
**original's transaction date** rather than today's (source says original, `:411`/`:417`); whether the
reversal legs are `manual_entry = true` (source says forced true, `:383`); and the **default comment text**
when `comments` is blank versus supplied (`:385`, `:405-406`) — the default string is built from the original
entry's id, so it is *derived from data* and a port must build it the same way.

**Refutation condition for the whole case:** if `POST …?command=reverse` returns a non-2xx on a freshly
posted, unreversed, manual, 3-leg entry, every prediction in §1.4(f) is void and R2–R5 must be re-planned
before being run.

### 4.5 TDG-R2, TDG-R3, TDG-R5 — the three reversal refusals

All three run on the **same throwaway instance immediately after R1**, which is why they are cheap.

| Case | Request | Key | Record |
|---|---|---|---|
| **R2** | `POST /journalentries/{txn}?command=reverse` — **the same `<txn>` R1 already reversed** | `T488-R2-reverse-again` | HTTP status; the **complete** error body verbatim; `developerMessage`, `userMessageGlobalisationCode`, `defaultUserMessage`, the whole `errors[]` array. Then **SQL**: assert `acc_gl_journal_entry` gained **no** rows, and assert `m_portfolio_command_source` **did** gain one at `status = 5` |
| **R3** | Post a loan disbursement or repayment on an accounting-enabled product to get an `L<n>` transaction; then `POST /journalentries/L<n>?command=reverse` | `T488-R3-reverse-nonmanual` | The same field list. **Then compare R2's and R3's error bodies byte for byte** and record whether they are identical. Source predicts both take the `size() <= 1` branch (`:349-351`) for *different* reasons — `reversed = true` vs `manualEntry = false`. If the two messages are identical, a port that implements only one condition is **invisible to a message-only comparison**, and the vector must therefore grade the database side-effect too |
| **R5** | Post a fresh manual entry dated `D`; `POST /glclosures` for office 1 with closing date `D`; then attempt the reversal | `T488-R5-post`, `T488-R5-closure`, `T488-R5-reverse-closed` | The refusal body; **whether the message echoes the closing date**; and whether the boundary is **inclusive** on the *reversal* path as it is on the posting path. Then **SQL**: `acc_gl_journal_entry` unchanged, `acc_gl_closure_id_seq` consumed |

**R5 must never run on the standing oracle.** A closure changes how *existing* rows render across ~14
automatic accounting sites and its sequence does not restore — reference-oracle § *ORACLE STATE MOVED BY
T287* and POLICY item 2 (*"Never a … closure"*).

### 4.6 TDG-R4 — loan-transaction reversal (the same-transaction-id shape)

**Preconditions.** Throwaway; a client; a loan product with **periodic-accrual** accounting mapping four
accounts (asset, income, expense, overpayment) — the shape
`JournalEntryReversalOrderingIntegrationTest.java:171` builds with `withAccountingRulePeriodicAccrual`; an
approved and disbursed loan; **MNT amounts of our choosing, not the test's** (the test's `10000` / `1000.0f`
are `TEST-ASSERTION`s in the demo currency and carry no authority here — and `1000.0f` is a **float**, which
is exactly what our recipes may not produce).

**Arms.** ① disburse → ② `GET /journalentries?transactionId=L<disbursementTxn>` → ③ repay → ④ `GET
…?transactionId=L<repaymentTxn>` (**this is the before-state; record the leg count**) → ⑤ SQL snapshot →
⑥ reverse the repayment through the **loan** endpoint → ⑦ `GET …?transactionId=L<repaymentTxn>` again →
⑧ SQL snapshot.

**Record additionally:** the leg count before and after under the **same** transaction id; the **order** the
legs come back in (the Fineract test's whole subject is ordering by transaction date, then created date, then
id **descending** — `:113-155`); and each original leg's `reversed` flag.

**State the contrast explicitly in the capture notes**, because it is the finding: R1's reversal legs land
under a **new** transaction id, R4's land under the **same** one. A port that implements one rule for both
paths is wrong on one of them, and only running both cases can see it.

### 4.7 TDG-C1…C4 — charge-off

**Preconditions (one product build serves all four).** Throwaway; a loan product with `accountingRule` set,
mapping the full slot set **including `chargeOffExpenseAccountId` and `chargeOffFraudExpenseAccountId`** —
these are the mappings `capabilities-ledger.json` records as absent on both admissible standing products, and
their absence is the sole blocker. Build the product **twice**, once cash-based and once periodic-accrual, so
`G-05`'s family selection is observed on the same event.

Record the product's **complete `acc_product_mapping` row set** via `capsql.sh` before any posting: the
`(product_id, financial_account_type, gl_account_id, payment_type, charge_id)` tuples. **This is the input to
slot resolution and no capture of a resolved leg is interpretable without it.**

| Case | Act | Key | Additional records |
|---|---|---|---|
| **C1** | `POST /loans/{id}/transactions?command=charge-off` | `T488-C1-chargeoff` | Every leg with the **slot code** it resolved to and the decoded slot name in the family the product declares |
| **C2** | Mark the loan as fraud, then charge off | `T488-C2-chargeoff-fraud` | Same. **Then diff C1's and C2's leg sets — the diff IS the observation.** `SOURCE-DERIVED HYPOTHESIS`, from the mock at `CreateJournalEntriesForChargeOffLoanTest.java:129-135`: the diff is confined to one account id. **If the leg count or any amount also moves, the hypothesis is refuted and that is the finding.** No account id and no amount is stated here |
| **C3** | Configure a charge-off **reason** code value with its own GL mapping; charge off citing that reason | `T488-C3-chargeoff-reason` | Whether the reason mapping **pre-empts** both the product expense slot and the fraud slot |
| **C4** | Repay after charge-off | `T488-C4-repay-after-chargeoff` | Every leg; specifically whether any **income** slot is credited (the Fineract test at `LoanChargeOffAccountingTest.java:722` is named `noIncomeRecognitionAfterChargeOff`), and whether recovery slots appear |

**If `command=charge-off` returns 404 or a mapping error, that is the capture** — record it and stop. It
reproduces the standing tenant's known behaviour on an unmapped product and tells the next fire the product
build is what needs fixing, not the recipe.

### 4.8 TDG-T1…T4 — transfers suspense

**Preconditions.** Throwaway with **two offices** — head office and one child, created in this run and
recorded by id. A client at office 1 with an **active, disbursed loan** on a product mapping
`TRANSFERS_SUSPENSE`. Record the product's `acc_product_mapping` rows as in §4.7.

| Case | Act | Key |
|---|---|---|
| **T1** | Propose the client transfer to office 2 | `T488-T1-propose` |
| **T2** | Accept it | `T488-T2-accept` |
| **T3** | On a **second** client + loan, propose then **withdraw** | `T488-T3-propose`, `T488-T3-withdraw` |
| **T4** | Propose a transfer for a client whose loan has **no principal outstanding** (fully repaid) | `T488-T4-propose-nil-principal` |

**Record for T1–T3:** every leg, and specifically **which office id each leg carries**. The mock test drives
the transaction office (2) while the loan sits on office 1 (`CreateJournalEntriesForTransferLoanTest.java:53-54,
:70`), and office attribution is the thing a port most plausibly gets wrong. **Then diff T1's leg set against
T2's and T3's**: source-derived hypothesis says T2 and T3 route **identically** and T1 is their mirror.

**Record for T4 as an ABSENCE:** `GET /journalentries?transactionId=…` returning an empty `pageItems`, **plus**
a SQL count showing `acc_gl_journal_entry` did not grow, **plus** an `m_portfolio_command_source` row proving
the command was actually processed. An absence probe with no proof the command ran is indistinguishable from
a probe that never fired — this is the trap `.softhouse/patterns.md` calls the vacuous pass.

### 4.9 TDG-S1…S6 — slot resolution

**S4 first.** Build a product whose `FUND_SOURCE` mapping exists at the **core** level and which has **no**
`paymentChannelToFundSourceMappings` at all. Disburse **without** a `paymentTypeId` in the request body. Then
disburse a second loan on the same product **with** a `paymentTypeId` that has no channel mapping. Record
which GL account each disbursement's fund-source leg resolved to, **and** — via `capsql.sh` — the
`acc_product_mapping` rows with their `payment_type` column (null vs set). The two arms together separate
DEC-2 §9 item 2's two readings: *null bound renders as `IS NULL` and matches the core row* versus *matches
nothing*. Keys: `T488-S4-disburse-nopaymenttype`, `T488-S4-disburse-withpaymenttype`.

**S1 / S1b / S2.** One product per accounting rule — `CASH_BASED`, then `ACCRUAL_UPFRONT`. For each: record
`acc_product_mapping`, then disburse, then repay, capturing every leg with its resolved account and slot
code. **S1b** additionally issues a **waive-interest** on the cash-based loan and records the **absence** of
journal entries for that transaction id, with the same three-part absence proof as T4.
Keys: `T488-S1-cash-disburse`, `T488-S1-cash-repay`, `T488-S1b-waive`, `T488-S2-upfront-disburse`,
`T488-S2-upfront-repay`.

**S3.** Two payment types, mapped to two **different** fund-source GL accounts. Repay once through each.
The observation is that the **same product and the same amount** produce **different** fund-source accounts —
which is the only shape that proves the channel level of the precedence chain is entered at all.
Keys: `T488-S3-repay-channel1`, `T488-S3-repay-channel2`.

**S5.** Four arms on one loan: (i) two charges → two *different* income accounts; (ii) two charges → the
*same* income account. **The observation is the leg COUNT and the per-leg amounts**, not just the accounts:
aggregation collapses (ii) into one leg while (i) stays two. Also record the total-debits vs total-credits
sum in `int64` minor units — invariant `I-1`, computed by the harness, never by a float reduction of the kind
at `LoanChargesMultipleDebitAccountsTest.java:66`.
Keys: `T488-S5-charges-distinct`, `T488-S5-charges-same-account`.

**S6.** Three refusal/absence arms: a charge with **no** GL mapping; a **zero-amount** charge; and a
deliberately **unbalanced** posting. Record the complete error body for each, and for the zero-amount arm
record whether a zero-value leg is **emitted** or **omitted** — a port that emits a `0` leg where the oracle
omits it fails `I-1` in neither direction but differs on leg count, which the vector grades.
Keys: `T488-S6-charge-nomapping`, `T488-S6-charge-zero`, `T488-S6-unbalanced`.

### 4.10 TDG-A1…A5 — the GL-account refusal quartet

Cheapest block in the plan; no loan, no lifecycle, no money movement. All on the throwaway.

| Arm | Setup | Act | Key |
|---|---|---|---|
| **A1** | Create parent (usage `HEADER`) + child (usage `DETAIL`) | `DELETE /glaccounts/{parent}` | `T488-A1-delete-parent` |
| **A2** | Create an account; map it into a loan product | `DELETE /glaccounts/{id}` | `T488-A2-delete-mapped` |
| **A3** | Create two accounts; post one balanced manual entry between them | `DELETE /glaccounts/{id}` | `T488-A3-delete-with-entries` |
| **A4** | Create an account and touch nothing else | `DELETE /glaccounts/{id}` | `T488-A4-delete-clean` |
| **A5** | Create an income and an expense account | `POST /accountingrules`, then `GET /accountingrules` | `T488-A5-create-rule` |

**Record for A1–A3:** HTTP status and the **complete** error body — `developerMessage`,
`userMessageGlobalisationCode`, `defaultUserMessage`, every element of `errors[]`, `parameterName`. The
Fineract tests assert only HTTP 403 and a **substring** of the message (`GLAccountIntegrationTest.java:84-85`,
`:104-105`, `:122-123`); a parity vector needs the whole body, because DEC-2 §4.9's taxonomy distinguishes
refusal *classes* and a substring cannot.

**Record for A4:** the accepting response, **and** a SQL assertion on `acc_gl_account` that the row is
**gone**, not flagged. §8 item 4 establishes from the schema and the entity that this table has **no deleted
marker column at all**, which makes "hard delete" a `SOURCE-DERIVED HYPOTHESIS` rather than a certainty about
runtime — **measure it**. `select count(*) from acc_gl_account where id = <id>` before and after.

**A1–A4 are a set and must be promoted or refused as a set.** Three refusals without A4's acceptance would be
satisfied by an implementation that refuses every delete.

### 4.11 TDG-X1, TDG-X2 — currency and residue

**X1.** On the throwaway, enable one **0-decimal** currency and one **3-decimal** currency alongside MNT via
`PUT /currencies` `[VERIFIED: CurrenciesApiResource.java:40 @Path("/v1/currencies"), :63 @PUT]`. Record `select code, decimal_places from m_currency` for all three. Then post one balanced
2-leg entry in each of the three currencies with an amount that has **non-zero digits at and beyond** the
currency's minor-unit position. Record: HTTP status; the **raw wire text** of each leg's amount on read-back;
`scale(amount)` and the stored value from PostgreSQL; and the `currency.decimalPlaces` the response declares.
Keys: `T488-X1-post-0dp`, `T488-X1-post-2dp-mnt`, `T488-X1-post-3dp`.

**The question X1 answers:** does the oracle's acceptance, storage and read-back of a money amount follow the
**currency's** declared minor unit, or is it uniform across currencies? `G-08` is written at
`MinorUnitDigits`; nothing in the corpus has ever varied it. `[UNVERIFIED: whether Fineract's currency
configuration on a fresh tenant offers a 0- or 3-decimal currency at all — §8 item 6. If it does not, X1
degrades to a finding and produces no vector.]`

**X2.** Post an MNT entry whose legs carry a **non-zero third decimal**, under the attested `(19, HALF_UP)`
tenant from TDG-00. Record the wire text, the stored `scale(amount)`, and the read-back. Then, separately,
drive an **oracle-computed** amount that could produce a residue — an interest accrual on a principal and rate
chosen so the exact quotient does not terminate at 2 decimals — and record whether the oracle's **own
arithmetic** ever emits a third non-zero decimal. Keys: `T488-X2-supplied-residue`, `T488-X2-computed-residue`.

**The distinction X2 preserves** is the one `capabilities-ledger.json` insists on: T352 **supplied** the third
decimal, it was not **computed**, and those are different facts about the oracle.

### 4.12 Promotion — what happens to these captures afterwards

**Nothing in this plan promotes anything.** A capture becomes a vector only by a separate, reviewed step that:

1. writes a `gerege.ledger.vector/v1` file citing `provenance.capture_ref` **and `capture_sha256`** of the
   raw artefact (the shape every existing `LDG-*` file uses);
2. stamps `dec2_revision` against `.softhouse/vectors/PIN-ledger.json`, **not** `dec1_revision`;
3. claims **only** capabilities that `capabilities-ledger.json` marks `in_graded_domain: true` — and for
   groups R, C, T, S, X that means the capability row must be **amended first**, with its evidence rewritten
   to say what the new capture actually exercised. **Amending that file is the gating step, not writing the
   vector**, and an absent or `false` row **refuses** (default-deny, DEC-2 §4.10);
4. registers at least one `graded_against` wrong implementation that the vector **kills** — a vector no
   registered wrong implementation fails is a vacuous pass;
5. adds the `txn` and `cmd` attribution lines to `.softhouse/capture/t363-oracle-baseline/PROBES.tsv`
   **if and only if** any arm touched the standing oracle. **No case in this plan does.** If a future fire
   moves one to STANDING, that obligation attaches immediately and `oracle-state-baseline.sh` exits 1 without it.

---

## 5. Tenant parameters, pinned — every capture in this document runs under exactly these

| Parameter | Value | Authority |
|---|---|---|
| `MathContext` | **`(19, HALF_UP)`** | CLAUDE.md § *Ratified tenant parameters*. **This is the production setting and the only one at which a parity vector may be taken.** |
| Precision | **19**, compile-time constant, **not tenant-configurable** | `MoneyHelper.PRECISION = 19`; `getMathContext()` = `new MathContext(19, tenantRoundingMode)` `[VERIFIED in CLAUDE.md against fineract-core/.../MoneyHelper.java:35,91-93]` |
| Rounding mode | **`HALF_UP`**, stored ordinal **4** | CLAUDE.md; seeded on the throwaway by `FINERACT_CONFIG_ROUNDING_MODE: "4"`, **not** patched after tenant creation |
| Currency | **MNT**, ISO 4217 numeric **496**, minor unit **2** | CLAUDE.md; `m_currency` seeds MNT at `decimal_places = 2` `[VERIFIED in .softhouse/reference-oracle.md § Findings 2]` |
| Timezone | **`Asia/Ulaanbaatar`** (+08, no DST), zone **named**, offset **never hard-coded** | CLAUDE.md; `FINERACT_DEFAULT_TENANTDB_TIMEZONE` on the throwaway |
| Tenant identifier | **`t488`** on the throwaway. **Never `default`** | reference-oracle § *Connection facts*: `default` is `Asia/Kolkata` +05:30 with `HALF_EVEN` and an empty ledger, and exists in this program **only** as a negative control |
| Database | **PostgreSQL 18.3** | CLAUDE.md non-negotiable. MySQL/MariaDB/Oracle Database are prohibited; the `postgresql` compose lineage only |
| Fineract commit | **`426a23544e8426a38ae43ae404670a0a7e85b9eb`** | this document's pin, asserted by TDG-00 |

**Captures at any other precision are NOT reusable and this plan claims none.** CLAUDE.md is explicit that
`C-00`, `D-01`, `D-02`, `D-03`, `D-04`, `D-01-p8` and `D-01-mnt` — taken at precision 12 or 8 — are
**discrimination probes, not parity vectors**. **A GL capture inherits the same rule, and there is a live
instance of it:** T352's residue observation is real, and `TDG-X2` **re-takes it** under an attested tenant
rather than assuming the earlier one was production-representative. Where a case below would merely re-observe
something the corpus already holds, it is either re-scoped to a new question or dropped.

---

## 6. Money representation

**Money is integer minor units. No floating-point in any monetary code path, struct field, schema column,
API field, or test fixture — including intermediate calculation** (CLAUDE.md). Applied to capture:

1. **On the wire the oracle emits scale 6** — e.g. `100000.250000` for MNT 100,000.25. Record those
   characters verbatim. Do not normalise, do not strip trailing zeros, do not re-serialise.
2. **Convert to `int64` minor units by exact integer/string arithmetic**: split on `.`, right-pad or verify
   the fractional part, refuse a non-zero digit beyond `decimalPlaces`. Never `float(x) * 100`.
3. **The store's `expect.*_minor` fields are decimal strings of `int64` values** — `"10000025"`, not
   `100000.25` and not `1.0000025e7` (see `LDG-01`'s `expect.legs[].amount_minor`).
4. **Every parse in a capture script uses `parse_float=decimal.Decimal`.** The corpus already carries a
   guard for this and a `PARSE-FLOAT-EXEMPT.txt` list; a new script that omits it will be caught, and should
   not need to be.
5. **Display is 0 decimals with a postfix symbol (`1,250,000₮`); storage is 2 (ISO).** No capture artefact
   contains a display-formatted amount.
6. **Fineract's own test corpus violates this and must not be copied.** `AccountingScenarioIntegrationTest`
   holds its principal as `Float LP_PRINCIPAL = 10000.0f` (`:97`) and its repayments as
   `Float[] REPAYMENT_AMOUNT` (`:119`); `JournalEntryReversalOrderingIntegrationTest` repays `1000.0f`
   (`:84`); `LoanChargesMultipleDebitAccountsTest` reduces journal-entry amounts through
   `BigDecimal.valueOf(entry.getAmount())` at sixteen sites (§1.4(d)). **These are `TEST-ASSERTION`s in a
   foreign harness. Not one of them appears as a value anywhere in this plan, and the amounts each recipe
   posts are chosen by the capture fire in MNT minor units, deliberately non-round, and recorded as sent.**

---

## 7. Ordering and cost — what to do with one short window

**Assumption stated so it can be corrected:** the Mac has been down for four days, so the first
oracle-reaching fire is time-boxed and may be interrupted. This ranking assumes **oracle time is the scarce
resource** and that a **partial** result on a high-value case beats a complete result on a low-value one.

**The cost model.** The dominant fixed cost is **throwaway bring-up** — `docker compose up` + health wait +
tenant seed + GL-account/product setup. Every case in groups R, C, T, S, A, X runs on a throwaway, so
**batching by rig, not by group, is what actually saves time**. The variable cost is roughly linear in HTTP
exchanges plus one SQL snapshot per state transition.

| Rank | Block | Cases | Why here | Rig cost |
|---:|---|---|---|---|
| **0** | **Attestation** | TDG-00 | **Mandatory, not optional.** Nothing captured before it is admissible, and CLAUDE.md requires a fresh calibration at `(19, HALF_UP)` before any parity capture. | on whichever instance is used |
| **1** | **Reversal** | R1, R2, R3 | Closes the half of `I-5` that a snapshot cannot reach, on a surface where **`command=reverse` has never been captured by this program**. R1 is the only capture in the plan that can **refute** a source-derived hypothesis about a project non-negotiable. R2/R3 ride the same instance for ~4 extra requests. | 1 throwaway |
| **2** | **GL-account refusals** | A1, A2, A3, A4 | **Highest refusals-per-minute in the plan** — no loan, no product lifecycle, no money movement. DEC-2 §4.9's taxonomy is the thinnest-evidenced part of the contract. Runs on **the same instance as rank 1**, so its marginal rig cost is zero. | shared with rank 1 |
| **3** | **`G-06` null payment type** | S4 | The only case that closes a predicate DEC-2 records as **undecidable from the pinned source** (§9 item 2). Needs a product build, so it cannot ride rank 1's instance for free — but it is two disbursements once built. | product build |
| **4** | **Cash family + its absence** | S1, S1b, S2 | `capabilities-ledger.json`: *"no cash-based accounting-path vector exists"*, and `G-03` refuses `ACCRUAL_UPFRONT` **solely because it is uncaptured**. Two product builds, then two lifecycles each. | 2 product builds |
| **5** | **Charge-off** | C1, C2, C3, C4 | Closes `ledger.charge.off` outright, and the blocker is **product configuration**, which the throwaway removes. C1/C2 as a **pair** is the discriminating observation. | 2 product builds |
| **6** | **Reversal under closure** | R5 | Completes group R. Ranked below rank 5 only because a closure needs its own clean instance (it changes how existing rows render). | 1 throwaway |
| **7** | **Transfers suspense** | T1, T2, T3, T4 | Closes `ledger.transfers.suspense`. Ranked here because it is the **most expensive setup** in the plan: two offices, two clients, two loans. | 1 throwaway + 2 offices |
| **8** | **Charge-specific slots** | S3, S5, S6 | Valuable but the deepest setup — payment types, channel mappings, charge-level GL mappings. | shared with rank 5 |
| **9** | **Currency** | X1, X2 | X1 is high-value **if** non-2dp currencies are configurable (§8 item 6); it is ranked here because that precondition is unverified and a failed precondition wastes a window. X2 re-takes an existing observation under attested parameters. | shared with rank 1 |
| **10** | **Accounting rules** | A5 | Two requests, almost no discriminating power. | shared |
| **—** | **Running balance** | B1 | **DE-SCOPED.** Three independent blockers (§3 group B). Do not spend oracle time here. | — |

**If the window closes mid-block:** commit the raw artefacts you have with the TDG-00 attestation sidecar and
an explicit incompleteness note. **A half-finished capture is evidence; a completed capture with a guessed
value is a forgery.** In particular, if R1's arms `a`–`e` completed and `f` did not, **that is still a
valuable commit** — the before-state is the artefact R1 uniquely needs, and it cannot be reconstructed later
on a destroyed instance.

**Do not batch two cases into one `Idempotency-Key` to save a request.** The key is the attribution record.

---

## 8. What I could not determine

| # | Item | Why, and what would settle it |
|---|---|---|
| 1 | `[UNVERIFIED]` **The internal assertion style of the ~18,000 LOC of `JournalEntryHelper`-using tests I did not open** (§1.3 row 18: `ClientLoanIntegrationTest` 8,354 LOC, `BaseLoanIntegrationTest` 1,944, `SchedulerJobsTestResults` 1,509, the Feign suite, the investor suite, `AccountTransferTest`). They are declared, not silently omitted. Opening them is a second-wave mining task. |
| 2 | `[UNVERIFIED]` **Whether the 1,427 Gherkin journal-entry lines contain transaction types the Java corpus does not.** I read one representative block (`LoanWriteOff.feature:78-82`) to establish the table shape. A systematic index of all 56 files would likely surface slot pairs no case above covers — §3 groups S and C would grow. It is a mechanical, oracle-free task and is the highest-value follow-up to this document. |
| 3 | `[UNVERIFIED]` **The declared Java type of the generated client's journal-entry `getAmount()`.** `fineract-client/src/main/java/.../models/` does not exist in the checkout — the models are generated at build time. What **is** verified is that sixteen call sites in `LoanChargesMultipleDebitAccountsTest` wrap it in `BigDecimal.valueOf(...)`, and that the server-side `JournalEntryData.amount` is a `BigDecimal` (`:50`). Settled by running `./gradlew :fineract-client:build` and reading the generated model. **A JDK IS present in this sandbox** — `openjdk 21.0.10`, and `/home/user/fineract/gradlew` exists `[VERIFIED: java -version; ls gradlew]` — so the obstacle is not tooling but scope and cost: a full Gradle dependency resolution against Maven Central through the agent proxy is not what this task was dispatched to do, and **`/home/user/fineract` is read-only for workers** and shared with concurrent readers, so a build there is not permissible. **The recipes do not depend on the answer**, because they read raw bytes regardless. |
| 4 | **CLOSED, not unverified — and the earlier draft of this row was WRONG, so it is corrected here rather than deleted.** It asserted *"`GLAccount` has an `is_deleted` column"*, inferred from the `GLClosure` note in `.softhouse/reference-oracle.md` and never checked. **Measured:** `acc_gl_account` is created once, at `fineract-provider/.../db/changelog/tenant/parts/0001_initial_schema.xml:49-75`, with columns `id, name, parent_id, hierarchy, gl_code, disabled, manual_journal_entries_allowed, account_usage, classification_enum, tag_id, description` — **no deleted marker** — and the entire changelog tree references `tableName="acc_gl_account"` on exactly **three** lines, all in that one file (the createTable plus two `createIndex`), so **no later part ever adds one**. `GLAccount.java` (`fineract-core/.../glaccount/domain/GLAccount.java:48`) declares `disabled` (`:67-68`) and carries **no `@SQLDelete` and no deleted field** `[VERIFIED: grep for "deleted\|@SQL" over that file → no output]`. **SOURCE-DERIVED HYPOTHESIS: GL-account delete is a HARD delete, like the closure delete.** The mock test only proves `repository.delete(glAccount)` is *called* (`GLAccountWritePlatformServiceJpaRepositoryImplTest.java:88`), which does not by itself distinguish the two. **TDG-A4's SQL arm confirms or refutes it.** |
| 5 | `[UNVERIFIED]` **Whether the standing `gerege` tenant's existing products can serve any case in this plan.** `capabilities-ledger.json` says charge-off is unmapped on both admissible products and that product 63 has no channel/fee/penalty mappings; I did not query the live tenant because it is unreachable from here. **This does not change the plan** — every case is routed to a throwaway anyway, which is where the probe policy wants accepted writes. |
| 6 | `[UNVERIFIED]` **Whether a 0-decimal or 3-decimal currency is enable-able on a fresh Fineract tenant.** `m_currency` is seeded from a Liquibase changelog I did not open. This is `TDG-X1`'s precondition; if it fails, X1 produces a finding and no vector, which is why X1 is ranked 9 and not higher. |
| 7 | `[UNVERIFIED]` **The exact HTTP status and error body of every predicted refusal.** R2, R3, R5, S6, A1–A3 all state a *predicted branch* from source. **No status code and no message string is asserted anywhere in this document as an expected value** — the Fineract tests' `403` and their message substrings are labelled `TEST-ASSERTION` and are cited as facts about those files. Settled only by running the recipes. |
| 8 | `[UNVERIFIED]` **How long the throwaway bring-up actually takes on the current host**, and therefore whether ranks 1–3 fit in one window. `t327`'s `run-all.sh` waits on a health check with 60 retries. The ranking in §7 is by **value per rig**, which is robust to the answer. |
| 9 | `[UNVERIFIED]` **Whether the recurring `Exited (143)` / SIGTERM incidents** recorded in `.softhouse/reference-oracle.md` for local fire `20260829-080002` affect a throwaway instance as well as the standing one. Root cause is unknown and is a host-level question. If a throwaway dies mid-capture, that is an **outage, never a corpus fault** — re-run; do not report the partial as a result. |

**Explicitly NOT unverified, and stated so no reviewer has to re-check it:** the pinned commit (§0), the four
POST commands on `/journalentries` (§1.4(c)), the reversal repository predicate `reversed=false and
manualEntry=true` (`JournalEntryRepository.java:30`), the reversal write path's six steps (§1.4(f)), the
`tenantIdentifier=default` defect in Fineract's own helper (§1.4(b)), the six ungraded ledger capabilities
(§2), and every `FILE:LINE` in §1.3 — each was opened and read in this session.

---

## 9. Evidence ledger

| Claim | Evidence |
|---|---|
| Pinned commit | `git -C /home/user/fineract log -1 --format=%H` → `426a23544e8426a38ae43ae404670a0a7e85b9eb`; `git status --porcelain` → empty |
| 320,601 test LOC / 1,254 files | `find . -name '*.java' -path '*src/test*' -print0 \| xargs -0 cat \| wc -l`; `… \| wc -l` |
| 200,763 feature LOC / 158 files | `find . -name '*.feature' -print0 \| xargs -0 cat \| wc -l`; `… \| wc -l` |
| 1,427 journal lines in features, 56 files | `grep -ri "journal" --include=*.feature . \| wc -l`; `grep -ril "journal\|accounting" --include=*.feature fineract-e2e-tests-runner \| wc -l` |
| 30 integration tests use `JournalEntryHelper`, 33,910 LOC | `grep -rl "JournalEntryHelper" integration-tests/src/test --include=*.java`; `… \| xargs wc -l \| tail -1` |
| `fineract-accounting/src/test` holds exactly one file | `find fineract-accounting/src/test -type f` |
| No `glclosures` test anywhere | `grep -rn "glclosures" --include=*.java integration-tests fineract-provider/src/test` → no output |
| One direct `POST /journalentries` call site in the whole integration corpus | `grep -rn "journalentries" integration-tests/src/test --include=*.java`; `JournalEntryHelper.java:192-194`; sole caller `GLAccountIntegrationTest.java:115-118` |
| Four POST commands on `/journalentries` | `JournalEntriesApiResource.java:203-220`, `:231-240` |
| Reversal loads only unreversed **manual** legs | `JournalEntryRepository.java:30-31` |
| Reversal mints a new transaction id; mirrors sides; flags the originals | `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:382`, `:409-419`, `:423-424` |
| Reversal is blocked by a closure on the original's date, inclusively | `:391-399` |
| `size() <= 1` → `JournalEntriesNotFoundException` | `:349-351` |
| Request money is `BigDecimal`; one `currencyCode` scalar; leg array typed `SingleDebitOrCreditEntryCommand[]` | `JournalEntryCommand.java:39-57` |
| Response money is `BigDecimal`; running balances + `runningBalanceComputed` live on the same DTO | `JournalEntryData.java:50`, `:73-77` |
| `charge-off` command constant | `LoanTransactionsApiResource.java:94` |
| Fineract's read-back helper hard-codes `tenantIdentifier=default` | `JournalEntryHelper.java:140`, `:163`, `:185` |
| Sixteen float-widening sites in the charge test | `LoanChargesMultipleDebitAccountsTest.java:66,69,132,186,299,312,352,363,521,572,590,633,666,742,811,838` |
| Six ungraded ledger capabilities | `.softhouse/vectors/capabilities-ledger.json`, `in_graded_domain` per row |
| 17 existing ledger vectors, none of them a reversal or a running balance | `ls .softhouse/vectors/ledger/` |
| `acc_gl_account` has no deleted-marker column, and never gains one | `fineract-provider/.../db/changelog/tenant/parts/0001_initial_schema.xml:49-75`; `grep -rn 'tableName="acc_gl_account"'` over the whole changelog tree → **3 lines, all in that file** |
| `GLAccount` carries no `@SQLDelete` and no deleted field | `fineract-core/.../glaccount/domain/GLAccount.java:48,67-68`; grep for `deleted\|@SQL` → no output |
| `fetchRunningBalance` emits MySQL-only `group by … desc` | `GLAccountReadPlatformServiceImpl.java:127-131` — re-read this session, independently of `capabilities-ledger.json`: `group by account_id desc, id` and `group by t2.account_id desc` |
| `PUT /currencies` is the enable surface TDG-X1 needs | `fineract-core/.../organisation/monetary/api/CurrenciesApiResource.java:40` (`@Path("/v1/currencies")`), `:49` (`@GET`), `:63` (`@PUT`) |
| This fire could not reach an oracle | `ls /var/run/docker.sock` → absent; `/dev/tcp/127.0.0.1/5432` and `/dev/tcp/127.0.0.1/8443` → Connection refused |
| The throwaway rig template and its guarantees | `.softhouse/capture/t327-closure-accepting-side/throwaway/{docker-compose.t327.yml,env.sh,run-all.sh}` |
| `cap11.sh` refuses a missing `Idempotency-Key`; `cap8.sh` sends none | `.softhouse/capture/t352-a2-next-tranche/cap11.sh:35,53`; `.softhouse/capture/tierA-a2/cap8.sh:82-85` |
| The standing oracle's probe policy, and that a refused write still burns a command id and a key | `.softhouse/reference-oracle.md` § *POLICY*, § *ORACLE STATE MOVED BY T287* |

---

## 10. The reviewer's first question, answered here

> **Does any row of this plan state a value that was not observed?**

**No.** There is no `expect` column, no expected status code, no expected amount and no expected message
string anywhere in this document. Where a Fineract test asserts a literal, it is labelled `TEST-ASSERTION`,
attributed to `FILE:LINE`, and described as *"the test asserts X"* — a fact about that file, never a target
for the oracle. Where Fineract main source predicts a behaviour, it is labelled
`SOURCE-DERIVED HYPOTHESIS`, cited, and each case states **what observation would refute it**. Everything
else is `TO_BE_CAPTURED` and states no value.

**No oracle was reachable from this fire, and that was probed rather than assumed** — `/var/run/docker.sock`
absent, `127.0.0.1:5432` refused, `127.0.0.1:8443` refused — so no value in this document *could* have been
observed, and none is claimed to have been.

**One further disclosure, because a document that hunts for unverified claims should report its own.** The
first draft of §8 item 4 asserted that `GLAccount` carries an `is_deleted` column. It does not. The claim was
inferred from a neighbouring fact about `GLClosure` and was never checked; it was caught by a pre-commit
sweep of this document's own citations, measured against the schema and the entity, and **corrected in place
with the error named** rather than quietly deleted. No other claim in this document was found to be
unsupported by that sweep.
