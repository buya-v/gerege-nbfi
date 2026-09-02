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
mention journal entries** across **48 feature files**. A **separate, wider** search — `journal` *or*
`accounting`, over the narrower `fineract-e2e-tests-runner` root — matches **56 files**. The two are
different searches and the earlier draft of this line reported the 1,427 lines as living in the 56 files.
**[CORRECTED BY T497 on T491 finding F-5; re-run at the pin this session.]**
`[VERIFIED: grep -ri "journal" --include=*.feature . | wc -l → 1427;
grep -ril "journal" --include=*.feature . | wc -l → 48;
grep -ril "journal\|accounting" --include=*.feature fineract-e2e-tests-runner | wc -l → 56]`
These carry GL expectations as **Gherkin data tables** with `| Type | Account code | Account name | Debit | Credit |`
columns — the most structured statement of Fineract's posting behaviour anywhere in the tree. See §1.4(e).

### 1.2 Where I looked — including the places that were empty

| Location | What I searched for | Result |
|---|---|---|
| `fineract-accounting/src/test` | any test at all | **1 file, 88 LOC** — `GLAccountWritePlatformServiceJpaRepositoryImplTest.java`. The accounting module's 149 main files / 12,752 main LOC have essentially **no unit tests of their own**. |
| `fineract-provider/src/test/.../accounting/**` | journal-entry / GL tests | 5 files: 2 `journalentry/*Test`, 2 `journalentry/service/*Test`, 1 `common/AccountingFinanciaActivityStepDefinitions.java` (40 LOC, 0 `@Test` — Cucumber glue, no expectations) |
| `integration-tests/src/test/.../integrationtests/accounting/` | the dedicated accounting package | **2 files only**: `GLAccountIntegrationTest.java` (132 LOC), `AccountingRuleIntegrationTest.java` (76 LOC) |
| `integration-tests/src/test` — `grep -rl JournalEntryHelper` | every test that reads journal entries back | **30 files, 33,910 LOC** (list in §1.3) |
| **whole tree, all extensions** — `grep -ril glclosure .` | a GL-closure integration test | **The `/glclosures` PATH STRING appears in main source and documentation only** — `fineract-accounting/.../closure/api/GLClosuresApiResource.java:58,88,103,106`; `fineract-core/.../commands/service/CommandWrapperBuilder.java:1749,1757,1765`; `fineract-provider/src/main/resources/static/legacy-docs/apiLive.htm`. **No test file anywhere in the tree references it.** The `GLClosure` **domain class** does appear in three test files, as a Mockito mock (`CreateJournalEntriesForChargeOffLoanTest.java:31,65`, `CreateJournalEntriesForTransferLoanTest.java:33,72`, `AccountingProcessorHelperTest.java:32,59`) — so "zero hits" is a statement about the path string, not about the subject. The closure behaviour this program has captured (`LDG-06`, `LDG-REFUSE-04`, `LDG-REFUSE-06`) still has **no counterpart in Fineract's own test corpus**. **[SEARCH WIDENED BY T497 on T491 finding F-7 — the earlier citation covered two directories and one extension, which could not have found a `.feature` or `.htm` hit. The conclusion survives the wider search; the claim is kept, the search is corrected.]** |
| **whole tree** — `grep -rn 'createJournalEntry\b' \| grep -v /src/main/` and `grep -rn createGLJournalEntry` | direct manual-JE `POST /journalentries` from a test | **FIVE call sites, not one. [CORRECTED BY T497 on T491 finding F-1 — see §1.4(g).]** `GLAccountIntegrationTest.java:115`; `InitiateExternalAssetOwnerTransferTest.java:1315` and `:1349`; `JournalEntriesStepDef.java:384` and `:397`. The earlier `grep -rn journalentries integration-tests/src/test` was **structurally blind** to four of them: a caller of `JournalEntryHelper.createJournalEntry` goes through the generated client method `createGLJournalEntry` and contains neither the string `journalentries` nor any `/journalentries` path. `[VERIFIED: I re-ran the T488 grep at the pin — its only hits are the three hand-built URLs in `JournalEntryHelper.java:139,163,185` plus two `createjournalentries` provisioning-flag hits, and it surfaces none of the POST sites.]` |
| `fineract-client/src/main/java/.../models/` | the wire model for a journal entry leg | **DIRECTORY ABSENT** — the client models are generated at build time and are not in the checkout. See §1.4(d) and §8 item 3. |
| `fineract-e2e-tests-runner/src/test/resources/features/` | Gherkin GL tables | **48** of 158 feature files carry the 1,427 journal lines; a wider `journal\|accounting` search over this root matches 56. **[CORRECTED BY T497, F-5 — §1.1.]** |

### 1.3 Files opened and read, with a verdict on each

`M` = mined (a case below cites it). `R` = read and rejected, with the reason.

| # | Path (relative to `/home/user/fineract`) | LOC | `@Test` | Verdict |
|---|---|---:|---:|---|
| 1 | `integration-tests/.../integrationtests/JournalEntryReversalOrderingIntegrationTest.java` | 184 | 1 | **M** — §3 group R |
| 2 | `integration-tests/.../integrationtests/accounting/GLAccountIntegrationTest.java` | 132 | 4 | **M** — §3 group A; the only direct `POST /journalentries` **in the dedicated accounting package** (there are four more elsewhere — §1.4(g)) |
| 3 | `integration-tests/.../integrationtests/AccountingScenarioIntegrationTest.java` | 1302 | 11 | **M (partial)** — **6 loan** tests mined (§3 group S) at `:150, :689, :813, :890, :984, :1114`; **4 savings/deposit** tests deprioritised at `:284, :377, :475, :548`, see §1.4(a); **1 share-account** test at `:1238` deferred to Tier B. **[CORRECTED BY T497 on T491 finding F-6: the split is 6/4/1, not 5/5/1 — the earlier text counted the shares test inside the deposit figure. VERIFIED: all eleven `public void` @Test methods enumerated at the pin this session.]** |
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
| 17 | `integration-tests/.../integrationtests/{FixedDepositTest,RecurringDepositTest,SavingsAccrual*,SavingsInterestPostingJob*,savings/base/*}` | 7,489 | 97 | **R — PRODUCT (deprioritised for this plan).** Deposit/savings. §1.4(a). **[RE-LABELLED BY T497 on T491 finding F-3 — it was `R — LEGAL`. The exclusion stands; the grounds are scope and priority, not statute.]** |
| 18 | `integration-tests/.../integrationtests/{ClientLoanIntegrationTest,BaseLoanIntegrationTest,SchedulerJobsTestResults,ClientLoanChargeRefundIntegrationTest,LoanAccount*,LoanChargeSpecificDueDateTest,AccountTransferTest,ShareAccountChargeRoundingTest,client/feign/*}` | 18,000+ | — | **NOT OPENED — declared, not silently omitted.** They reference `JournalEntryHelper` but their primary subject is loan lifecycle, transfers, shares or the Feign client. They are a **second-wave** source once groups R/C/T/S are captured. `[UNVERIFIED: their internal assertion style]` **`investor/*` was in this row in the earlier draft and has been REMOVED from it — see rows 19-20. A universal claim about the corpus was made over this unread set, which is exactly how §1.4(g) happened; treat this row as a boundary on what may be asserted, not merely on what was read.** |
| 19 | `integration-tests/.../integrationtests/investor/externalassetowner/InitiateExternalAssetOwnerTransferTest.java` | 1,735 | 17 | **M — OPENED BY T497 on T491 finding F-1.** Read `:1307-1367` (`addManualJournalEntriesWithAssetExternalization`). Two direct manual-JE POSTs: `:1315` (a refusal arm inside `Assertions.assertThrows(CallFailedRuntimeException.class, …)`, asserting the message contains `"External asset owner with external id:"`) and `:1349` (a manual JE posted **for its own sake**, read back by transaction id at `:1358-1359` and asserted on at `:1361-1365`). Source of §3 group O. |
| 20 | `fineract-e2e-tests-core/.../test/stepdef/common/JournalEntriesStepDef.java` | 487 | 0 | **M (hazard + call sites) — OPENED BY T497.** Two further manual-JE POST helpers at `:384` and `:397`, driven by Gherkin steps at `:403`, `:412`, `:419`. **Also the source of the `runningBalance=true` copy hazard — §1.4(b) bullet 3.** |

**Main-source files read (not tests), because the recipes depend on them:**

| Path | Lines read | What it settled |
|---|---|---|
| `fineract-provider/.../accounting/journalentry/api/JournalEntriesApiResource.java` | `:75`, `:112`, `:170-177`, `:192-220`, `:222-240`, `:247`, `:263`, `:282-298` | The complete POST surface: 4 commands, listed in §1.4(c) |
| `fineract-provider/.../accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java` | `:343-356`, `:358-378`, `:380-428`, `:432-461`, `:525-530` | The reversal write path — §1.4(f), the whole of group R |
| `fineract-accounting/.../accounting/journalentry/domain/JournalEntryRepository.java` | `:28-35` | `findUnReversedManualJournalEntriesByTransactionId` filters `reversed=false and manualEntry=true` |
| `fineract-accounting/.../accounting/journalentry/command/JournalEntryCommand.java` | `:37-57`, `:79` | The request shape: `BigDecimal amount` (`:45`), `SingleDebitOrCreditEntryCommand[] credits/debits` (`:53-54`), one scalar `currencyCode` (`:40`) — **and `externalAssetOwner` at `:57`, validated at `:79`, which §1.4(g) shows this program has never captured** |
| `fineract-accounting/.../accounting/journalentry/data/JournalEntryData.java` | `:50`, `:73-77` | Server-side response money is `BigDecimal`; the two running-balance columns and `runningBalanceComputed` live here |
| `fineract-provider/.../loanaccount/api/LoanTransactionsApiResource.java` | `:94` | `CHARGE_OFF_COMMAND_VALUE = "charge-off"` |

### 1.4 The structural findings that shape every recipe below

**(a) The savings/deposit half of the accounting test corpus is out of scope for THIS plan, and the reason is
PRODUCT — a scope and priority call — not LEGAL.**
**[RESTATED BY T497 on T491 finding F-3. The exclusion is UNCHANGED; its grounds and its finality are not.
The earlier draft labelled this LEGAL, cited Art. 12.1.3 / 12.1.4 as the reason, and closed with "on grounds
no later agent may re-litigate". That sentence is STRUCK. It read an ACTIVATION gate as a SCOPE BLOCK, which
CLAUDE.md forbids in terms.]**

`AccountingScenarioIntegrationTest` spends **4** of its 11 tests on savings, fixed-deposit and
recurring-deposit accounting flows (`:284`, `:377`, `:475`, `:548`); `:1238` is a **share-account** test, not
a deposit one, and is deferred to Tier B separately (see §1.3 row 3, corrected).

**What CLAUDE.md actually says, quoted so no later agent has to re-derive it.** § *Blocking questions*:
*"Porting `fineract-savings` / deposit code is in scope; **enabling deposit-taking behavior in any live
environment is not** … **This is a licensing gate on the *activation*, not a scope block on the *port*.**"*
Tier B lists savings/deposits as in scope for porting. Art. 12.1.3 prohibits **the NBFI** from accepting
deposits; reading a reference implementation's arithmetic on a disposable Docker instance is not the NBFI
accepting a deposit, and no article makes it one. **So this exclusion cannot rest on statute, and does not.**

**The two grounds it does rest on, both PRODUCT/ENGINEERING and both reversible by a later driver:**

1. **CLAUDE.md ratifies that an NBFI deployment exposes no deposit endpoint.** A deposit golden vector would
   grade a surface the Go module will never serve on this tenant — effort spent on an unserved seam while
   loan/GL seams are ungraded.
2. **DEC-2's graded domain is loan/GL.** A savings vector claims a capability `capabilities-ledger.json` does
   not carry, and `admit.go` refuses it by default-deny (DEC-2 §4.10). It could not be promoted if captured.

**On `.softhouse/reference-oracle.md` § POLICY item 2.** That section is headed *"POLICY — firing a probe at
the **SHARED** reference oracle"* (`:1115`) and its "No deposit or savings behaviour" bullet is at `:1163`.
Its **neighbouring bullet at `:1160`** — *"Never a product retype, a mapping edit, a GL-account edit, a
closure, or a business-date change"* — is one this plan **correctly** reads as standing-tenant-only, since
`TDG-R5` plans a closure and `TDG-A1`–`A4` plan GL-account deletes, both on a throwaway. Reading one bullet of
that list as universal and its neighbour as standing-only was inconsistent. **The consistent reading: every
bullet in §2 is scoped to the shared `gerege` instance.** No case in this plan touches the standing oracle, so
none of them is engaged.

**Recorded so a later agent is not blocked by this paragraph:** porting `fineract-savings` / deposit code
remains **in Tier B scope** per CLAUDE.md. The activation gate is a `user` gate on switching deposit-taking
**on**; it is not a bar on porting, on reading source, or on capturing behaviour from a disposable instance.
A later fire that judges a deposit capture worth its oracle time may make that call and record it — it needs
no `user` gate to do so, only a reason better than this plan's.

**(b) Fineract's own test corpus carries three copy-from-Fineract hazards. A recipe copied verbatim out of it
is wrong in three separate ways, and only the first was in the earlier draft.**

**Hazard 1 — every hand-built read-back URL hard-codes `tenantIdentifier=default`.**
`JournalEntryHelper.java:140`, `:163` and `:185` each append `"&tenantIdentifier=default"`. Per
`.softhouse/reference-oracle.md` § *Connection facts*, tenant `default` on our instance is `Asia/Kolkata`
(+05:30, **not** a permitted zone), runs `HALF_EVEN`, and its database `fineract_default` holds **0 GL
accounts and 0 journal entries**. **A recipe copied verbatim out of these tests would read the wrong tenant
and find nothing, and nothing downstream would say so.** Every recipe below sends
`Fineract-Platform-TenantId` explicitly and states the tenant in its attestation; none uses a query parameter
copied from a Fineract test.
*Refinement, T497 on T491 finding F-8:* the claim is true of every **hand-built URL**, not of every read-back
**path**. `JournalEntryHelper.java:196-200` (`retrieveJournalEntryByTransactionId`) reads back through the
generated client and builds no URL at all, so it carries no tenant parameter. Immaterial to the recipes,
which send the tenant header explicitly — but the two words are not interchangeable.

**Hazard 2 — the e2e step definitions set `runningBalance=true` on EVERY journal-entry read-back, and the
harness refuses such a capture on arrival. [ADDED BY T497 on T491 finding F-4.]**

```java
// fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:364-367
Map<String, Object> journalQueryParams = new HashMap<>();
journalQueryParams.put("transactionId", transactionId);
journalQueryParams.put("runningBalance", true);
journalEntryDataResponse = journalEntriesApi().retrieveAllJournalEntries(journalQueryParams);
```

**T491 cited `:366`. Re-derived at the pin, the pattern is at FIVE sites in that one file — `:174`, `:224`,
`:299`, `:366`, `:438` — i.e. it is the file's uniform read-back idiom, not one stray line.**
`[VERIFIED: grep -n 'runningBalance' on that file, this session]`

Against this program's admission rules that produces an **INADMISSIBLE** capture, not merely a noisy one:

- `nexus/internal/apps/ledger/conformance/admit.go:141` — `bad = append(bad,
  opts.OracleDerived.CaptureRuleReasons(opts.RepoRoot, v)...)`.
- `nexus/internal/apps/ledger/conformance/oraclederived.go:230-243` and `:803-814`: *"A ledger parity vector
  may not be captured with `runningBalance=true` or `fetchRunningBalance=true` … A vector citing such a body
  is **INADMISSIBLE**."* The scanner keys on the three **camelCase response** field names in
  `.softhouse/vectors/oracle-derived-columns.json` → `capture_rule.forbidden_response_field_names`:
  `organizationRunningBalance`, `officeRunningBalance`, `runningBalanceComputed`.
- Why the field names are a sound proxy for the parameter, from Fineract source rather than from the harness's
  own say-so: `JournalEntryReadPlatformServiceImpl.java:104-108` appends those three columns to the SELECT
  **only** inside `if (associationParametersData.isRunningBalanceRequired())`. They are in the body **iff**
  the parameter was set. `[VERIFIED at the pin this session; independently consistent with T429's measured
  pair.]`

**Consequence: a fire that mines the feature corpus and copies its read-back shape burns oracle time
producing captures the harness rejects on arrival.** §4.3's read-back
(`GET /journalentries?transactionId=<txn>&limit=50`) is already correct and must not acquire the parameter.
Repeated as a standing constraint on the follow-up at §8 item 2.

**Hazard 3 — the integration helper's client read-back passes bare positional booleans.**
`JournalEntryHelper.java:196-200` calls `retrieveAllJournalEntries` with nineteen positional arguments, the
last of which is `true`. On the **server-side** resource signature
(`JournalEntriesApiResource.java:112-131`, read this session) the parameter order ends
`… loanId, savingsId, runningBalance, transactionDetails` — so the nineteenth slot is `transactionDetails`
and that call is **not** hazard 2. `[UNVERIFIED: whether the GENERATED CLIENT's parameter order matches the
resource's — `fineract-client/src/main/java/.../models/` is absent from the checkout (§8 item 3), so the
positional mapping cannot be confirmed at this pin.]` **The recipe consequence is unconditional either way:
send named query parameters over `curl`, never positional arguments through a generated client**, which is
what every recipe below already does.

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
use is as a value source. §3 uses them the first way. Systematically indexing all **48** journal-bearing files is a follow-up
task, not this one (§8 item 2 — the pointer said item 5 in the earlier draft; item 5 is about the standing tenant's products. [T497]).

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

**(g) THE MANUAL-JE CALL SITES — a claim this document got wrong, and the correction.
[ADDED BY T497 on T491 finding F-1.]**

**What the earlier draft said**, in §1.2, in §9 and in the T488 handoff: *"`grep -rn journalentries` over the
whole integration corpus finds exactly **one** direct `POST /journalentries` call site, used by **one** test,
and only to make a `DELETE` fail … **Fineract's own tests never post a manual journal entry for its own sake,
and never reverse one.**"*

**Why it was wrong, and the lesson is the search, not the count.** `JournalEntryHelper`'s POST goes through
the generated client method `createGLJournalEntry` (`JournalEntryHelper.java:192-193`). A **caller** of
`JournalEntryHelper.createJournalEntry` therefore contains neither the string `journalentries` nor any
`/journalentries` path, so `grep -rn "journalentries"` **cannot see the call sites the claim was about**. The
empty-ish result was read as a fact about the world when it was a fact about the search. Worse, the universal
half of the claim was asserted over `investor/*` — a set §1.3 row 18 **itself declared NOT OPENED**.

**Re-derived at the pin this session, whole tree:**

```
grep -rn 'createJournalEntry\b' --include='*.java' . | grep -v '/src/main/'
grep -rn 'createGLJournalEntry' --include='*.java' . | grep -v 'fineract-client/src/main'
```

| `FILE:LINE` | What it is |
|---|---|
| `integration-tests/.../accounting/GLAccountIntegrationTest.java:115` | The one the earlier draft found, and correctly characterised: setup for a `DELETE` refusal. |
| `integration-tests/.../investor/externalassetowner/InitiateExternalAssetOwnerTransferTest.java:1315` | Inside `Assertions.assertThrows(CallFailedRuntimeException.class, …)`: a manual JE with an **unregistered** `externalAssetOwner`. **A manual-journal-entry REFUSAL arm** — the surface `TDG-A1`–`A3` and DEC-2 §4.9's refusal taxonomy are shortest of. |
| `…/InitiateExternalAssetOwnerTransferTest.java:1349` | Inside `addManualJournalEntriesWithAssetExternalization` (`:1307-1367`). Posts a manual JE, reads it back by transaction id (`:1358-1359`), asserts on the returned legs (`:1361-1365`). **This is posting a manual journal entry for its own sake and asserting on the result.** |
| `fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:384` | `addManualJournalEntryWithoutExternalAssetOwner`. |
| `fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:397` | `addManualJournalEntryWithExternalAssetOwner`, driven by Gherkin steps at `:403`, `:412`, `:419`. |

**THE CORRECTED CLAIM.** *One* direct manual-JE POST in the dedicated accounting package; **three** in
`integration-tests` overall; **five** in the test corpus as a whole. **Fineract's tests DO post a manual
journal entry for its own sake — `:1349` — so that half of the earlier finding is REFUTED and is withdrawn.**

**The other half STANDS and is not weakened.** *"…and never reverse one."* I searched the whole tree for
`reverseJournalEntry`, for `command=reverse`, and for the literal `"reverse"` outside `/src/main/`; the only
relevant hit is `SavingsAccountHelper.java:93` (`REVERSE_TRASACTION_COMMAND`), a **savings-transaction**
command, not a journal-entry one. **No test anywhere invokes `POST /journalentries/{txn}?command=reverse`,**
which is why group R remains the plan's flagship: it is a surface Fineract's own corpus never exercises.
`[VERIFIED: searches re-run at the pin this session, independently of T488 and of T491.]`

**What the correction buys, beyond accuracy.** `externalAssetOwner` is a request field on
`JournalEntryCommand.java:57`, validated at `:79`
`[CORRECTION TO T491, which cited :38 — the field is at :57 in this checkout; I opened the file]`, and it is
**uncaptured by this program**. A Go port that silently drops it is byte-identical to a correct one on every
capture taken to date. §3 group **O** adds the two cases.

**And a second finding the mining missed entirely, read out of the write path this session:** the
`externalAssetOwner` field has **two** refusal branches, not one, and the first is a
**global-configuration** gate that fires before any owner lookup —
`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:172-183`:

1. `:173-176` — if global configuration `ASSET_EXTERNALIZATION_OF_NON_ACTIVE_LOANS` is **not enabled**:
   `JournalEntryRuntimeException("error.msg.glJournalEntry.asset.externalization.not.enabled", …)`.
2. `:179-180` — only then, if `externalAssetOwnerRepository.findByExternalId(externalId)` is empty:
   `ExternalAssetOwnerNotFoundException` (`fineract-investor/.../exception/ExternalAssetOwnerNotFoundException.java:28`).

**This matters to the recipe and is why group O records the branch rather than assuming one:** on a fresh
throwaway with that configuration at its default, an `externalAssetOwner` POST may take branch 1 and never
reach branch 2. **Which branch it takes is `TO_BE_CAPTURED` and no prediction of it is stated here.**

**Third: the owner is a JOIN, not a column.** `accountingService.createMappingToOwner(...)`
(`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:679` → `AccountingServiceImpl.java:123-132`) writes a
row into **`m_external_asset_owner_journal_entry_mapping`**, and the read-back surfaces it as
`eao.external_id as externalAssetOwner` (`JournalEntryReadPlatformServiceImpl.java:103`). **There is no
`external_asset_owner` column on `acc_gl_journal_entry`**, so §4.3's SQL field list cannot reach it — group O
reads the mapping table explicitly.

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
| `ledger.running.balance` | **false** | "PERMANENTLY REFUSED WHILE GATE **G-12** IS OPEN"; the vector schema has **no field** for either balance column; the **`/glaccounts`** running-balance reader emits MySQL-only SQL; and — the strongest — `admit.go:141` refuses any vector whose cited capture bytes carry the running-balance field names at all | **B1 — DE-SCOPED**, §3 group B |

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

> **RE-ANCHORING NOTICE — T497, on T491 finding F-2. Read this before trusting any `Mined from` cell below
> that names `CreateJournalEntriesForChargeOffLoanTest`.**
>
> That mock test is **case-discovery material only**. It is not evidence about the live charge-off path, for
> two reasons I verified at the pin this session.
>
> **(i) It is stale relative to the code it mocks.**
> `git log -1 --date=short` gives `CreateJournalEntriesForChargeOffLoanTest.java` → **2026-04-17**
> (`d01fedfd`, "Merge pull request #5349") and
> `AccrualBasedAccountingProcessorForLoan.java` → **2026-07-20** (`99930230`, "FINERACT-2455: Rework
> transaction reprocessing"). **The test predates a rework of the path it tests by three months.**
>
> **(ii) It verifies a helper overload the charge-off path no longer calls.** `AccountingProcessorHelper`
> declares both: the **9-argument** `createDebitJournalEntryForLoan(office, currencyCode, int
> accountMappingTypeId, loanProductId, paymentTypeId, loanId, transactionId, transactionDate, amount)` at
> **`:749`**, and the **7-argument** `createDebitJournalEntryForLoan(office, currencyCode, loanId,
> transactionId, transactionDate, amount, GLAccount account)` at **`:756`**. The mock's
> `verify(…)` at `CreateJournalEntriesForChargeOffLoanTest.java:105-107` targets the **9-arg** overload; the
> charge-off path's actual emit loop calls the **7-arg** one, at
> `AccrualBasedAccountingProcessorForLoan.java:957` (debits) and `:949` (credits).
> `[UNVERIFIED: whether the mock therefore FAILS at this pin — no Gradle build was run and none is
> permissible here (`/home/user/fineract` is read-only and shared). What is verified is the two signatures,
> the call site, and the two dates.]`
>
> **Consequence, applied below:** every group-C `SOURCE-DERIVED HYPOTHESIS` is re-cited to **main source**.
> The mock's line numbers are retained only to say *how the case was found*. **Nothing that gets captured
> changes** — the §4.7 recipe already asks the right question and states no value.

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-C1** | `POST /loans/{id}/transactions?command=charge-off` on a loan whose product **maps `chargeOffExpenseAccountId`** and whose loan carries **no** charge-off reason code and is **not** marked fraud. Record every leg. `SOURCE-DERIVED HYPOTHESIS`, **re-anchored to main source**: `AccrualBasedAccountingProcessorForLoan.java:909-911` computes `mapping` as `null` when `chargeOffReasonCodeValue` is null; `:919-927` then takes the `else` arm and `:925-926` selects `LOAN_PORTFOLIO` / `CHARGE_OFF_EXPENSE`. **Refuted if** the debit resolves anywhere but the product's charge-off-expense slot. | main: `AccrualBasedAccountingProcessorForLoan.java:909-928`. Case discovery only: `CreateJournalEntriesForChargeOffLoanTest.java:80,99-107`; `LoanChargeOffAccountingTest.java:109` (periodic accrual), `:637` (cash) | `ledger.charge.off`, `ledger.slot.resolution`, `G-11` | THROWAWAY |
| **TDG-C2** | The same, on a loan **marked as fraud** and still with no reason code. `SOURCE-DERIVED HYPOTHESIS`, **re-anchored to main source**: `AccrualBasedAccountingProcessorForLoan.java:921-923` — `if (isMarkedFraud)` selects `CHARGE_OFF_FRAUD_EXPENSE` instead of `CHARGE_OFF_EXPENSE`, with the credit slot (`LOAN_PORTFOLIO`) and the amount unchanged. A port that ignores the fraud flag posts to the same account and is otherwise byte-identical — so this pair is a **discriminating** pair, not two similar captures. | main: `:919-927`. Case discovery only: `CreateJournalEntriesForChargeOffLoanTest.java:111,129-135`; `LoanChargeOffAccountingTest.java:265` | `ledger.charge.off` | THROWAWAY |
| **TDG-C3** | Charge-off **with a reason code value mapped**. `SOURCE-DERIVED HYPOTHESIS`, **re-anchored to main source — and the earlier citation is WITHDRAWN**: at `AccrualBasedAccountingProcessorForLoan.java:909-911` the reason mapping is resolved **first**, and at `:914-918`, when it is non-null, the debit goes to `mapping.getGlAccount()` and control **never enters** the `else` at `:919-927` where the two product slot enums live. **So the reason mapping pre-empts both the fraud slot and the expense slot.** Precedence, not a value. **Refuted if** a leg resolves to either product slot while a reason mapping exists. | main: `AccrualBasedAccountingProcessorForLoan.java:909-928`. **The earlier draft cited `CreateJournalEntriesForChargeOffLoanTest.java:89,101` vs `:114,142`; those lines CONTRADICT the claim — `:105-107` names `CHARGE_OFF_EXPENSE` in the very arm cited as not reaching it. See the re-anchoring notice above.** | `ledger.slot.resolution` (charge/reason precedence level) | THROWAWAY |
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

### Group O — `externalAssetOwner` on a manual journal entry (`ledger.refusal.parity`, `ledger.journal.entry.readback`)

**[ADDED BY T497 on T491 condition 1. Mined from the two call sites §1.4(g) recovered.]**

`externalAssetOwner` is a request field on `JournalEntryCommand.java:57` that **no capture in this program has
ever exercised**. A Go port that accepts the field and silently discards it is byte-identical to a correct one
on every vector taken to date. These two cases are the ones that separate them.

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-O1** | `POST /journalentries` — a balanced 2-leg MNT manual entry carrying an `externalAssetOwner` external id that **does not exist**. Record the HTTP status and the **complete** error body verbatim. **Which of the two refusal branches fires is `TO_BE_CAPTURED` and no prediction is stated:** §1.4(g) shows the global-configuration gate at `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:173-176` runs **before** the owner lookup at `:179-180`, so on a fresh throwaway the config branch is reachable. **Also record** `GET /configurations` for `ASSET_EXTERNALIZATION_OF_NON_ACTIVE_LOANS` **before** the POST, so the branch taken is interpretable; and a SQL assertion that `acc_gl_journal_entry` gained **no** rows while `m_portfolio_command_source` gained one. | `InitiateExternalAssetOwnerTransferTest.java:1315` (`TEST-ASSERTION`: that test asserts only that the message *contains* `"External asset owner with external id:"`, which is a substring, and DEC-2 §4.9 needs the whole body); main: `:172-183`, `ExternalAssetOwnerNotFoundException.java:28` | `ledger.refusal.parity`, DEC-2 §4.9 | THROWAWAY, **rides rank 1's instance** |
| **TDG-O2** | `POST /journalentries` — the same entry with a **registered** `externalAssetOwner`, then read back by transaction id. Record, per leg, whether `externalAssetOwner` **survives to the response**; and, from SQL, the rows in **`m_external_asset_owner_journal_entry_mapping`** joining each leg to the owner — §1.4(g) establishes there is **no `external_asset_owner` column** on `acc_gl_journal_entry`, so §4.3's field list cannot reach it. | `InitiateExternalAssetOwnerTransferTest.java:1349`, read back at `:1358-1359`, asserted at `:1361-1365`; main: `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:679` → `AccountingServiceImpl.java:123-132`; `JournalEntryReadPlatformServiceImpl.java:103` | `ledger.journal.entry.readback` | THROWAWAY |

**A cost correction, and I am recording it because T491's condition asserted the opposite.** T491 wrote that
both cases are *"cheap and ride rank-1's throwaway."* **That is true of O1 and NOT of O2.** Reading
`InitiateExternalAssetOwnerTransferTest.java:1307-1367` at the pin: registering an external asset owner
requires a client (`:1324`), a loan product (`:1327-1328`), a loan application (`:1330-1332`), an approval
(`:1337-1339`), a **disbursement** (`:1340-1342`) and an **initiated external-asset-owner transfer**
(`:1343-1347`) before the owner exists to be referenced. **O2 therefore carries a full loan lifecycle plus an
investor-context command**, and is ranked accordingly in §7 — not with O1.

**A scope note, stated rather than assumed.** `externalAssetOwner` resolution lives in `fineract-investor`,
which is **Tier B**. **O1 stays inside this context** — it is a `POST /journalentries` refusal, graded by
DEC-2 §4.9, and it never reaches the investor write path (it is refused before it gets there). **O2 crosses
into Tier B setup** to reach a GL read-back. It is included because the *observation* is a GL one, and it is
ranked last so a fire that judges the crossing not worth it can drop it without losing O1.

### Group P — the persistence rounding site (`G-08`, and a precondition for anything graded on a computed amount)

**[ADDED BY T497 at the driver's relay of T495/T490's finding, re-derived at the pin before being written in.]**

**The posting path has TWO rounding sites, not one.**

- **R-1 — Java arithmetic** at `MathContext(19, HALF_UP)`: **19 SIGNIFICANT DIGITS.**
  `[VERIFIED: fineract-core/.../organisation/monetary/domain/MoneyHelper.java:35 (`PRECISION = 19`) and
  `:91-93` (`new MathContext(PRECISION, getRoundingMode())`), opened this session.]`
- **R-2 — the INSERT itself**, into `numeric(19,6)`: **6 DECIMAL PLACES.**
  `[VERIFIED: fineract-accounting/.../journalentry/domain/JournalEntry.java:90` —
  `@Column(name = "amount", scale = 6, precision = 19, nullable = false)` — and `:91` the `BigDecimal amount`
  field it annotates; `:125` is `this.amount = amount;` with **no coercion, no `setScale`, no rounding** on
  the Java side; `fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml:145`
  declares the column `DECIMAL(19, 6)`. All four opened this session.]`

**R-2 is a rounding site nobody in this program has characterised, and it CANNOT be characterised from
source.** Java hands the driver an unrounded `BigDecimal`; what lands in the column is then decided by
**PostgreSQL**, and *round / truncate / error* are three different answers with three different parity
consequences. There is no database in this sandbox, so it is unanswerable here.

**Why it is not hypothetical.** `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:981` is a live
producer of unbounded-scale values on the posting path:

```java
// :964   final MathContext mc = MoneyHelper.getMathContext();
// :981
final BigDecimal proRatedTax = taxDetail.getAmount().multiply(paidAmount, mc).divide(chargeAmount, mc);
```

`[VERIFIED: both lines opened at the pin this session.]` A `divide` at `(19, HALF_UP)` may yield **up to 19
significant digits** — far more than six decimal places — so for any charge whose tax pro-rate does not
terminate, **the value that reaches the column is not the value Java computed**, and parity is graded against
the column.

| id | Behaviour | Mined from | Feeds | Rig |
|---|---|---|---|---|
| **TDG-P1** | **What does PostgreSQL do on insert into `numeric(19,6)` when handed more than six decimal places, at the ratified tenant setting?** Issue, on the attested `t488` throwaway: `create temporary table t497_p1 (a numeric(19,6));` then, **as separate statements so one failure does not mask the others**, insert a value with 7 decimals, one with 12, one with 19 significant digits, and one that would exceed precision 19 on the left of the point. **Record, per statement: whether it succeeded or raised; the complete `SQLSTATE` and message text if it raised; and, if it succeeded, `select a, scale(a)` as RAW TEXT.** Then repeat the same four values against a real `acc_gl_journal_entry` row via `TDG-R1`'s posting arm, to confirm the temp-table answer is the column's answer. **`TO_BE_CAPTURED` in every cell. NO PREDICTION IS RECORDED HERE — not "it rounds", not "it truncates", not "it errors", and not a rounding mode.** Naming an outcome for a probe whose only purpose is to observe one would be the exact forgery §0 exists to prevent. | main: `MoneyHelper.java:35,:91-93`; `JournalEntry.java:90-91,:125`; `0001_initial_schema.xml:145`; the producing site at `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:964,:981` | `G-08`, `ledger.money.minor.unit.conversion`; **a precondition for `TDG-X2` and for any vector graded on a computed amount** | THROWAWAY, **rides rank 1's instance — it is four SQL statements** |

**THE CONSTRAINT THIS PROBE IMPOSES UNTIL IT IS ANSWERED.** **No vector derived from the `:981` tax pro-rate
site — or from any other site whose value can exceed scale 6 before the INSERT — may be graded while `TDG-P1`
is unanswered.** The value parity is graded against is the value in the column, and until R-2's behaviour is
observed, that value is unknown even when the Java arithmetic is fully understood. This binds §4.9's charge
cases (`TDG-S5`, `TDG-S6`) and §4.12's promotion step; both carry the note.

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
| **TDG-B1** | **DO NOT CAPTURE AS A PARITY VECTOR.** **FOUR** independent blockers, any one of which is sufficient. **[REVISED BY T497 on T491's re-derivation: blocker (iii) was over-broad and under-tagged, and the strongest blocker was missing entirely.]** **(i)** Gate **G-12** is open and `capabilities-ledger.json` marks the capability *"PERMANENTLY REFUSED WHILE G-12 IS OPEN"*; `admit.go:128-149` enforces it. **(ii)** **The `gerege.ledger.vector/v1` schema has no field for either balance column**, so an admissible vector could not express the value even if it were observed. **(iii)** The **`/glaccounts` reader** — `GET /glaccounts?fetchRunningBalance=true` — cannot run on PostgreSQL: `fineract-accounting/.../glaccount/service/GLAccountReadPlatformServiceImpl.java:127-131` emits `group by account_id desc, id` (`:129`) and `group by t2.account_id desc` (`:131`), MySQL-only syntax PostgreSQL rejects. `[UNVERIFIED: the resulting HTTP STATUS. The earlier draft said "HTTP 500" without a tag; that is a RUNTIME claim and no instance was reachable from this fire. What is verified is the SQL, read at the pin. **And it is true of the `/glaccounts` reader only** — the `/journalentries` running-balance reader demonstrably DOES work on PostgreSQL: T429 captured `GET /journalentries/78?runningBalance=true` live on 2026-08-29 (`nexus/.../conformance/oraclederived_test.go:19-30`).]` **(iv) THE STRONGEST, and it applies to the whole capability, not to one reader:** `admit.go:141` → `oraclederived.go:230-243` scans the **cited capture bytes** and refuses a vector carrying `organizationRunningBalance`, `officeRunningBalance` or `runningBalanceComputed`. **A running-balance capture is inadmissible on arrival regardless of which reader produced it.** Beyond all four, CLAUDE.md's own non-negotiable is that **balances are derived, never written**, and A2-29 already measured the stored balance behaving as a **second source of truth**. |

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
| 1 | **Pinned checkout commit** — a fact about the CHECKOUT, not about the running image. **[RELABELLED BY T497 on T491 finding F-10; the earlier wording said "Fineract commit of the running image's source", which a `git log` cannot establish.]** `[UNVERIFIED: that the running image was built from this commit. Item 12 records the image digest but nothing in this plan ties the digest to a commit. If the fire can produce build provenance — a label, a build arg, a `docker inspect` config entry naming the source ref — record it as item 12a and this becomes verified; if it cannot, record the gap rather than the inference.]` | `git -C <checkout> log -1 --format=%H` | ≠ `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
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
| **`cap11.sh`** | `.softhouse/capture/t352-a2-next-tranche/cap11.sh` | **Every HTTP request.** It takes `NAME METHOD PATH BODYFILE IDEMPOTENCY_KEY` and **refuses if the key is absent**. **Cosmetic warning, so a fire does not think it grabbed the wrong file [T497, on T491 finding F-11]: `cap11.sh` self-identifies as `cap10.sh` throughout — its header (`:2`, `:15`, `:31`), its `usage:` string (`:52`), its refusal message (`:53`) and its `mktemp` template (`:66`) all say `cap10.sh`. The file at that path IS the key-refusing instrument; the name in the strings is stale.** `[VERIFIED: grep -n 'cap10' on that file, this session.]` It sends `--data-binary` (so curl does not strip newlines), commits `out/NAME.req` + `.req.sha256` as the exact wire bytes, writes nothing under `out/` until the exchange completed, and records a non-2xx **as data, not as an error**. |
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

> **Why recording those two SQL columns is SAFE, and does not make the artefact inadmissible.
> [ADDED BY T497 on T491 finding F-12 — a careful fire could reasonably fear the opposite and drop the most
> useful SQL columns in the plan.]** The capture scanner keys on the **camelCase RESPONSE field names**
> `organizationRunningBalance`, `officeRunningBalance`, `runningBalanceComputed`
> (`.softhouse/vectors/oracle-derived-columns.json` → `capture_rule.forbidden_response_field_names`, read
> this session), which appear in a `/journalentries` body **iff** `runningBalance=true` was sent
> (`JournalEntryReadPlatformServiceImpl.java:104-108`). A `psql` artefact emitting **snake_case** headers
> — `office_running_balance`, `organization_running_balance`, `is_running_balance_calculated` — matches none
> of those three names and trips nothing. The separate snake_case check in `admit.go:142-149` reads the
> vector's **`_note` text** for the phrase `grades <column>`, and constrains **vector cells**, not artefact
> bytes. **So: record the SQL columns; never send `runningBalance=true` on the HTTP read-back; never write
> "grades office_running_balance" in a `_note`.** All three are separate obligations.

> **The `numeric(19,6)` constraint. [ADDED BY T497 — see §3 group P.]** The `amount` column is
> `DECIMAL(19, 6)` (`0001_initial_schema.xml:145`) and Java applies no coercion before the INSERT
> (`JournalEntry.java:90-91,:125`). **`scale(amount)` in the field list above is therefore not a formality:
> it is the only place the R-2 rounding site becomes visible in an artefact.** Record it on every leg, and
> record the response's raw wire text alongside it, so a divergence between what the oracle computed and what
> the column holds is present in the evidence rather than inferred later.

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

> **The Fineract ordering test is NOT evidence of the rule it documents, and TDG-R4 must not be read as
> confirming it. [ADDED BY T497 on T491 finding F-13 — a strengthening, not a defect.]**
> `JournalEntryReversalOrderingIntegrationTest.verifyJournalEntriesOrdering` (`:113-155`) contains **exactly
> one** assertion, at `:140`, and it is reachable only when the transaction date **and** the created date are
> equal; the other four branches (`:130-131`, `:136-137`, `:142-145`, `:146-149`) are empty comment blocks.
> The rule it *states* in comments at `:124-127` — transaction date ascending, created date ascending, id
> descending — is therefore **documented but almost entirely unexercised by its own test**. TDG-R4 already
> plans to **capture** the ordering rather than trust it, which is the right handling; this note exists so no
> later fire cites that test as the authority for an ordering a vector grades.

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

> **S5 and S6 are ORACLE-COMPUTED amounts and are therefore behind the `TDG-P1` gate.
> [ADDED BY T497 — §3 group P, §4.12 item 4a.]** A charge with tax details reaches the pro-rate at
> `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:981`, a `divide` at `MathContext(19, HALF_UP)`
> whose result can carry far more than the six decimal places the `amount` column holds. **Capture S5 and S6
> freely — the artefacts are evidence either way — but do not promote a vector from them until `TDG-P1` has
> observed what the column does with such a value.** Record `scale(amount)` on every leg, per §4.3.

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

### 4.11a TDG-O1, TDG-O2 — `externalAssetOwner` on a manual journal entry

**[ADDED BY T497 on T491 condition 1.]**

**O1 — the refusal arm. Rides rank 1's instance; two GL accounts and one POST.**
Preconditions: the same three DETAIL accounts `TDG-R1` created, or two of them. **Before the POST**, record
`GET /configurations` (or the `c_configuration` row) for `ASSET_EXTERNALIZATION_OF_NON_ACTIVE_LOANS` — this
is what makes the branch taken interpretable, and it costs one GET.

| Arm | Request | Key | Record |
|---|---|---|---|
| `O1-a` | `GET /configurations` | — | the `ASSET_EXTERNALIZATION_OF_NON_ACTIVE_LOANS` row, enabled or not, verbatim |
| `O1-b` | `POST /journalentries` — balanced 2-leg MNT, `externalAssetOwner` set to a string that exists nowhere | `T488-O1-post-unknown-owner` | HTTP status; the **complete** error body verbatim — `developerMessage`, `userMessageGlobalisationCode`, `defaultUserMessage`, every element of `errors[]`, `parameterName` |
| `O1-c` | **SQL** | — | `acc_gl_journal_entry` gained **no** rows; `m_portfolio_command_source` **did** gain one, and at what `status` |

**Which of the two branches (`:173-176` config, `:179-180` owner-not-found) fired is the observation.** It is
`TO_BE_CAPTURED`; nothing here predicts it. If the config branch fires and the fire has budget, enable the
configuration and **re-run `O1-b` under a second key** (`T488-O1-post-unknown-owner-configon`) so both
refusals are on the record — that is two extra requests and it doubles the refusal yield of the case.

**O2 — the accepting arm. NOT cheap; see the cost correction in §3 group O.** It needs the full setup
`InitiateExternalAssetOwnerTransferTest.java:1324-1347` performs: client → loan product → loan → approve →
disburse → `initiateTransferByLoanId`. **Amounts are ours, in MNT minor units, deliberately non-round —
the test's `1000.0` and `BigDecimal.TEN` are `TEST-ASSERTION`s in USD and carry no authority here.**
Keys: `T488-O2-client`…`T488-O2-transfer` for the setup, `T488-O2-post-with-owner` for the subject.

**Record for O2, additionally to §4.3:** whether each read-back leg carries `externalAssetOwner`; and the
`m_external_asset_owner_journal_entry_mapping` rows for those legs from `capsql.sh`
(`journal_entry_id`, `owner_id`), since the value is a **join**, not a column on `acc_gl_journal_entry`.

### 4.11b TDG-P1 — what PostgreSQL does with more than six decimal places

**[ADDED BY T497 at the driver's relay of T495/T490's two-rounding-sites finding.]**
**Four SQL statements on rank 1's instance. It answers a question that gates a whole class of later vectors.**

Run through `capsql.sh` so the **executed bytes** are committed, each statement as its own artefact so one
failure does not mask the others:

| Arm | Statement | Record |
|---|---|---|
| `P1-a` | `create temporary table t497_p1 (a numeric(19,6));` | that it succeeded |
| `P1-b` | insert a value with **7** decimal places, then `select a, scale(a)` | succeeded or raised; if raised, the **complete** `SQLSTATE` and message; if succeeded, `a` and `scale(a)` as **raw text** |
| `P1-c` | the same with **12** decimal places | same field list |
| `P1-d` | the same with **19 significant digits**, and separately a value exceeding precision 19 to the left of the point | same field list |
| `P1-e` | post the same values as journal-entry legs through `TDG-R1`'s posting arm, then read `amount`, `scale(amount)` from `acc_gl_journal_entry` | whether the real column agrees with the temp table |

**NO OUTCOME IS STATED FOR ANY ARM.** Round, truncate and error are all `TO_BE_CAPTURED`. A probe whose only
purpose is to observe a behaviour must not carry a guess at that behaviour — §0's rule applies to it with
more force than to any other case in this document, not less.

**What P1 settles, and what it does not.** It settles what the **column** does. It does **not** settle
whether Fineract ever hands the column such a value in production — that is what the `:981` producer site and
`TDG-X2`'s computed-residue arm are for. **Both halves are needed before a computed amount can be graded.**

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
4a. **[ADDED BY T497 — the `numeric(19,6)` gate, §3 group P.]** for any vector whose graded amount is
   **computed by the oracle** rather than supplied by the capture — anything downstream of the tax pro-rate
   at `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:981`, and any charge case in §4.9 — **refuses
   unless `TDG-P1` has been answered**. Until R-2's behaviour on insert into `numeric(19,6)` is observed, the
   relationship between the value Java computed and the value the column holds is unknown, and the column is
   what parity grades. A supplied-amount vector (`TDG-R1`, `TDG-A3`, `TDG-O1`) is unaffected;
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
| **1a** | **The `numeric(19,6)` persistence probe** | **P1** | **[ADDED BY T497.]** Four SQL statements, no HTTP, no setup — and it is a **precondition for every vector graded on an oracle-computed amount** (§4.12 item 4a), which is most of groups C, S and X. Ranked immediately after rank 1 because it is the cheapest thing in the plan that unblocks the most, and because R-2 is a rounding site **nothing in this program has characterised**. | shared with rank 1 |
| **2** | **GL-account refusals** | A1, A2, A3, A4 | **Highest refusals-per-minute in the plan** — no loan, no product lifecycle, no money movement. DEC-2 §4.9's taxonomy is the thinnest-evidenced part of the contract. Runs on **the same instance as rank 1**, so its marginal rig cost is zero. | shared with rank 1 |
| **2a** | **Manual-JE `externalAssetOwner` refusal** | **O1** | **[ADDED BY T497 on T491 condition 1.]** One GET, one POST, one SQL check, on rank 1's instance and its accounts. It exercises a request field (`JournalEntryCommand.java:57`) **no capture in this program has ever touched**, and it lands in the same thin refusal taxonomy as rank 2. | shared with rank 1 |
| **3** | **`G-06` null payment type** | S4 | The only case that closes a predicate DEC-2 records as **undecidable from the pinned source** (§9 item 2). Needs a product build, so it cannot ride rank 1's instance for free — but it is two disbursements once built. | product build |
| **4** | **Cash family + its absence** | S1, S1b, S2 | `capabilities-ledger.json`: *"no cash-based accounting-path vector exists"*, and `G-03` refuses `ACCRUAL_UPFRONT` **solely because it is uncaptured**. Two product builds, then two lifecycles each. | 2 product builds |
| **5** | **Charge-off** | C1, C2, C3, C4 | Closes `ledger.charge.off` outright, and the blocker is **product configuration**, which the throwaway removes. C1/C2 as a **pair** is the discriminating observation. | 2 product builds |
| **6** | **Reversal under closure** | R5 | Completes group R. Ranked below rank 5 only because a closure needs its own clean instance (it changes how existing rows render). | 1 throwaway |
| **7** | **Transfers suspense** | T1, T2, T3, T4 | Closes `ledger.transfers.suspense`. Ranked here because it is the **most expensive setup** in the plan: two offices, two clients, two loans. | 1 throwaway + 2 offices |
| **8** | **Charge-specific slots** | S3, S5, S6 | Valuable but the deepest setup — payment types, channel mappings, charge-level GL mappings. | shared with rank 5 |
| **9** | **Currency** | X1, X2 | X1 is high-value **if** non-2dp currencies are configurable (§8 item 6); it is ranked here because that precondition is unverified and a failed precondition wastes a window. X2 re-takes an existing observation under attested parameters. | shared with rank 1 |
| **10** | **Accounting rules** | A5 | Two requests, almost no discriminating power. | shared |
| **11** | **`externalAssetOwner` read-back** | **O2** | **[ADDED BY T497.]** The observation is a GL one — does the owner survive to the read-back legs, and what does the mapping table hold — but reaching it needs a client, a product, a loan, a disbursement and an **investor-context** transfer initiation (`InitiateExternalAssetOwnerTransferTest.java:1324-1347`). **Ranked last deliberately: T491's condition described both O cases as cheap; O2 is not, and a fire that drops it loses nothing that O1 already gives.** | 1 throwaway + full loan lifecycle |
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
| 2 | `[UNVERIFIED]` **Whether the 1,427 Gherkin journal-entry lines contain transaction types the Java corpus does not.** I read one representative block (`LoanWriteOff.feature:78-82`) to establish the table shape. A systematic index of all **48** files (§1.1, corrected) would likely surface slot pairs no case above covers — §3 groups S and C would grow. It is a mechanical, oracle-free task and is the highest-value follow-up to this document. **TWO STANDING CONSTRAINTS ON THAT FOLLOW-UP, so it cannot go wrong the way this document nearly did. [ADDED BY T497 on T491 findings F-1 and F-4.]** ① **Do not copy the corpus's read-back shape.** The e2e step definitions set `runningBalance=true` on **every** journal-entry read-back — `JournalEntriesStepDef.java:174, :224, :299, :366, :438` — and a capture whose cited bytes carry the resulting response fields is **INADMISSIBLE** under `admit.go:141` → `oraclederived.go:230-243`. Mine the corpus for **which transaction types produce which slot pairs**; issue the read-back yourself, per §4.3, without that parameter. ② **Do not make a universal claim from a search over files you did not open.** §1.4(g) is the record of what that costs: a grep that was structurally blind to four of five call sites produced a "Fineract never does X" finding that was false. State what you searched and over what; "not found" is a statement about the search. |
| 3 | `[UNVERIFIED]` **The declared Java type of the generated client's journal-entry `getAmount()`.** `fineract-client/src/main/java/.../models/` does not exist in the checkout — the models are generated at build time. What **is** verified is that sixteen call sites in `LoanChargesMultipleDebitAccountsTest` wrap it in `BigDecimal.valueOf(...)`, and that the server-side `JournalEntryData.amount` is a `BigDecimal` (`:50`). Settled by running `./gradlew :fineract-client:build` and reading the generated model. **A JDK IS present in this sandbox** — `openjdk 21.0.10`, and `/home/user/fineract/gradlew` exists `[VERIFIED: java -version; ls gradlew]` — so the obstacle is not tooling but scope and cost: a full Gradle dependency resolution against Maven Central through the agent proxy is not what this task was dispatched to do, and **`/home/user/fineract` is read-only for workers** and shared with concurrent readers, so a build there is not permissible. **The recipes do not depend on the answer**, because they read raw bytes regardless. |
| 4 | **CLOSED, not unverified — and the earlier draft of this row was WRONG, so it is corrected here rather than deleted.** It asserted *"`GLAccount` has an `is_deleted` column"*, inferred from the `GLClosure` note in `.softhouse/reference-oracle.md` and never checked. **Measured:** `acc_gl_account` is created once, at `fineract-provider/.../db/changelog/tenant/parts/0001_initial_schema.xml:49-75`, with columns `id, name, parent_id, hierarchy, gl_code, disabled, manual_journal_entries_allowed, account_usage, classification_enum, tag_id, description` — **no deleted marker** — and the entire changelog tree references `tableName="acc_gl_account"` on exactly **three** lines, all in that one file (the createTable plus two `createIndex`), so **no later part ever adds one**. `GLAccount.java` (`fineract-core/.../glaccount/domain/GLAccount.java:48`) declares `disabled` (`:67-68`) and carries **no `@SQLDelete` and no deleted field** `[VERIFIED: grep for "deleted\|@SQL" over that file → no output]`. **SOURCE-DERIVED HYPOTHESIS: GL-account delete is a HARD delete, like the closure delete.** The mock test only proves `repository.delete(glAccount)` is *called* (`GLAccountWritePlatformServiceJpaRepositoryImplTest.java:88`), which does not by itself distinguish the two. **TDG-A4's SQL arm confirms or refutes it.** |
| 5 | `[UNVERIFIED]` **Whether the standing `gerege` tenant's existing products can serve any case in this plan.** `capabilities-ledger.json` says charge-off is unmapped on both admissible products and that product 63 has no channel/fee/penalty mappings; I did not query the live tenant because it is unreachable from here. **This does not change the plan** — every case is routed to a throwaway anyway, which is where the probe policy wants accepted writes. |
| 6 | `[UNVERIFIED]` **Whether a 0-decimal or 3-decimal currency is enable-able on a fresh Fineract tenant.** `m_currency` is seeded from a Liquibase changelog I did not open. This is `TDG-X1`'s precondition; if it fails, X1 produces a finding and no vector, which is why X1 is ranked 9 and not higher. |
| 7 | `[UNVERIFIED]` **The exact HTTP status and error body of every predicted refusal.** R2, R3, R5, S6, A1–A3 all state a *predicted branch* from source, and **O1 deliberately does not even do that** — §1.4(g) shows it has **two** reachable branches and the plan names neither as the one that fires. **No status code and no message string is asserted anywhere in this document as an expected value** — the Fineract tests' `403` and their message substrings are labelled `TEST-ASSERTION` and are cited as facts about those files. Settled only by running the recipes. |
| 8 | `[UNVERIFIED]` **How long the throwaway bring-up actually takes on the current host**, and therefore whether ranks 1–3 fit in one window. `t327`'s `run-all.sh` waits on a health check with 60 retries. The ranking in §7 is by **value per rig**, which is robust to the answer. |
| 9 | `[UNVERIFIED]` **Whether the recurring `Exited (143)` / SIGTERM incidents** recorded in `.softhouse/reference-oracle.md` for local fire `20260829-080002` affect a throwaway instance as well as the standing one. Root cause is unknown and is a host-level question. If a throwaway dies mid-capture, that is an **outage, never a corpus fault** — re-run; do not report the partial as a result. |
| 10 | `[UNVERIFIED]` **What PostgreSQL does on insert into `numeric(19,6)` when handed more decimal places than the column holds.** **[ADDED BY T497 — this is `TDG-P1`, §3 group P.]** The Java side is fully verified — `MoneyHelper.java:35,:91-93` computes at 19 **significant digits**, `JournalEntry.java:90-91` declares the column at 6 **decimal places**, `:125` applies no coercion, `0001_initial_schema.xml:145` is `DECIMAL(19, 6)`, and `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:981` is a live producer of unbounded-scale values. **The database's response is the one link in that chain that source cannot supply, and no database was reachable from this fire.** Round, truncate and error are all live possibilities and this document names none of them. Settled by four SQL statements (§4.11b). |
| 11 | `[UNVERIFIED]` **Whether `CreateJournalEntriesForChargeOffLoanTest` still passes at this pin.** §3 group C's re-anchoring notice establishes that its `verify` at `:105-107` targets the 9-arg `AccountingProcessorHelper.java:749` overload while the charge-off path calls the 7-arg `:756` one at `AccrualBasedAccountingProcessorForLoan.java:957`. Whether that makes the test red is a **build** question; no Gradle run was performed and none is permissible here (`/home/user/fineract` is read-only and shared with concurrent readers). **It does not matter to any recipe** — group C is now anchored to main source — and is recorded only so the inference is not mistaken for a measurement. |

**Explicitly NOT unverified, and stated so no reviewer has to re-check it:** the pinned commit (§0), the four
POST commands on `/journalentries` (§1.4(c)), the reversal repository predicate `reversed=false and
manualEntry=true` (`JournalEntryRepository.java:30`), the reversal write path's six steps (§1.4(f)), the
**five** manual-JE POST call sites and the "never reverses one" half of the finding (§1.4(g)), the
`tenantIdentifier=default` defect and the two further copy hazards in Fineract's own corpus (§1.4(b)), the six
ungraded ledger capabilities (§2), and every `FILE:LINE` in §1.3 — each was opened and read, at the pin, in a
session of this program, and every one that T497 touched was re-opened by T497 rather than inherited.

---

## 9. Evidence ledger

| Claim | Evidence |
|---|---|
| Pinned commit | `git -C /home/user/fineract log -1 --format=%H` → `426a23544e8426a38ae43ae404670a0a7e85b9eb`; `git status --porcelain` → empty |
| 320,601 test LOC / 1,254 files | `find . -name '*.java' -path '*src/test*' -print0 \| xargs -0 cat \| wc -l`; `… \| wc -l` |
| 200,763 feature LOC / 158 files | `find . -name '*.feature' -print0 \| xargs -0 cat \| wc -l`; `… \| wc -l` |
| 1,427 journal lines in features, across **48** files; a separate wider search matches 56 files | `grep -ri "journal" --include=*.feature . \| wc -l` → 1427; `grep -ril "journal" --include=*.feature . \| wc -l` → **48**; `grep -ril "journal\|accounting" --include=*.feature fineract-e2e-tests-runner \| wc -l` → 56. **[CORRECTED BY T497, F-5 — all three re-run at the pin.]** |
| 30 integration tests use `JournalEntryHelper`, 33,910 LOC | `grep -rl "JournalEntryHelper" integration-tests/src/test --include=*.java`; `… \| xargs wc -l \| tail -1` |
| `fineract-accounting/src/test` holds exactly one file | `find fineract-accounting/src/test -type f` |
| No test anywhere references the `/glclosures` **path** | **Widened by T497 (F-7) to the whole tree, all extensions:** `grep -ril glclosure .` → the path string occurs only in `fineract-accounting/.../GLClosuresApiResource.java:58,88,103,106`, `fineract-core/.../CommandWrapperBuilder.java:1749,1757,1765` and `fineract-provider/src/main/resources/static/legacy-docs/apiLive.htm`. Three test files reference the `GLClosure` **domain class** as a Mockito mock (`CreateJournalEntriesForChargeOffLoanTest.java:31,65`; `CreateJournalEntriesForTransferLoanTest.java:33,72`; `AccountingProcessorHelperTest.java:32,59`). The earlier citation covered two directories and one extension and could not have found a `.feature` or `.htm` hit; the conclusion survives the wider search. |
| **FIVE** direct manual-JE `POST /journalentries` call sites in the test corpus — **not one** | **[CORRECTED BY T497, F-1 — §1.4(g).]** `grep -rn 'createJournalEntry\b' --include='*.java' . \| grep -v /src/main/` and `grep -rn createGLJournalEntry --include='*.java' . \| grep -v fineract-client/src/main` → `GLAccountIntegrationTest.java:115`; `InitiateExternalAssetOwnerTransferTest.java:1315`, `:1349`; `JournalEntriesStepDef.java:384`, `:397`. The earlier `grep -rn journalentries` is structurally blind to four of them (the POST goes through the generated `createGLJournalEntry`, so a caller contains no such string); I re-ran it and its only hits are `JournalEntryHelper.java:139,163,185` plus two `createjournalentries` provisioning flags. |
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
| The **`/glaccounts`** running-balance reader emits MySQL-only `group by … desc` | `fineract-accounting/.../glaccount/service/GLAccountReadPlatformServiceImpl.java:127-131` — re-read by T497 this session: `group by account_id desc, id` (`:129`) and `group by t2.account_id desc` (`:131`). **The module path is `fineract-accounting`, not `fineract-provider` [T497].** The resulting HTTP status is `[UNVERIFIED: runtime]`. |
| `PUT /currencies` is the enable surface TDG-X1 needs | `fineract-core/.../organisation/monetary/api/CurrenciesApiResource.java:40` (`@Path("/v1/currencies")`), `:49` (`@GET`), `:63` (`@PUT`) |
| This fire could not reach an oracle | `ls /var/run/docker.sock` → absent; `/dev/tcp/127.0.0.1/5432` and `/dev/tcp/127.0.0.1/8443` → Connection refused |
| The throwaway rig template and its guarantees | `.softhouse/capture/t327-closure-accepting-side/throwaway/{docker-compose.t327.yml,env.sh,run-all.sh}` |
| `cap11.sh` refuses a missing `Idempotency-Key`; `cap8.sh` sends none | `.softhouse/capture/t352-a2-next-tranche/cap11.sh:35,53`; `.softhouse/capture/tierA-a2/cap8.sh:82-85` |
| The standing oracle's probe policy, and that a refused write still burns a command id and a key | `.softhouse/reference-oracle.md` § *POLICY*, § *ORACLE STATE MOVED BY T287* |
| That POLICY section is scoped to the **SHARED** oracle, and its deposit bullet sits beside bullets this plan reads as standing-only | `.softhouse/reference-oracle.md:1115` (heading *"POLICY — firing a probe at the **SHARED** reference oracle"*), `:1160` (closures / GL-account edits), `:1163` (deposit or savings behaviour) **[T497, F-3]** |
| `AccountingScenarioIntegrationTest` splits **6 loan / 4 savings-deposit / 1 shares**, not 5/5/1 | 11 `@Test` methods enumerated at the pin: loan `:150, :689, :813, :890, :984, :1114`; savings/deposit `:284, :377, :475, :548`; shares `:1238` **[T497, F-6]** |
| The e2e read-back idiom sets `runningBalance=true`, which the harness refuses | `JournalEntriesStepDef.java:174, :224, :299, :366, :438`; `nexus/.../conformance/admit.go:141`; `nexus/.../conformance/oraclederived.go:230-243, :803-814`; `.softhouse/vectors/oracle-derived-columns.json` → `capture_rule.forbidden_response_field_names` **[T497, F-4]** |
| Those three response fields appear **iff** the parameter was set — from Fineract, not from the harness | `JournalEntryReadPlatformServiceImpl.java:104-108`, the `if (associationParametersData.isRunningBalanceRequired())` block **[T497]** |
| snake_case SQL column headers do not trip the camelCase capture scanner | `capture_rule.forbidden_response_field_names` = `organizationRunningBalance, officeRunningBalance, runningBalanceComputed`; the snake_case check at `admit.go:142-149` reads the vector's `_note`, not artefact bytes **[T497, F-12]** |
| TDG-C3's claim is true on **main** source and NOT supported by the mock lines it was cited to | `AccrualBasedAccountingProcessorForLoan.java:909-928` — `mapping != null` at `:914` debits `mapping.getGlAccount()` at `:918` and never enters the slot-enum `else` at `:919-927`. The mock's `:105-107` names `CHARGE_OFF_EXPENSE` in the very arm cited as not reaching it **[T497, F-2]** |
| The charge-off mock predates the path it mocks, and verifies an overload that path no longer calls | `git log -1 --date=short`: test → **2026-04-17** (`d01fedfd`), `AccrualBasedAccountingProcessorForLoan.java` → **2026-07-20** (`99930230`). `AccountingProcessorHelper.java:749` is the 9-arg overload the mock verifies; `:756` is the 7-arg one called at `AccrualBasedAccountingProcessorForLoan.java:949` (credits) and `:957` (debits) **[T497, F-2]** |
| No test invokes `POST /journalentries/{txn}?command=reverse` | whole-tree searches re-run by T497: `grep -rn reverseJournalEntry --include=*.java . \| grep -v /src/main/` → empty; `grep -rn 'command=reverse'` over `*.java` and `*.feature` outside `/src/main/` → empty; `grep -rn '"reverse"' --include=*.java . \| grep -v /src/main/` → one hit, `SavingsAccountHelper.java:93` (`REVERSE_TRASACTION_COMMAND`), a savings-transaction command. **The "never reverses one" half of §1.4(g) is CONFIRMED, independently.** |
| `externalAssetOwner` is a `JournalEntryCommand` field with **two** refusal branches, and the owner link is a join | `JournalEntryCommand.java:57` (field), `:79` (validation); `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:173-176` (global-configuration gate) and `:179-180` (owner not found); `ExternalAssetOwnerNotFoundException.java:28`; `:679` → `AccountingServiceImpl.java:123-132` writes `m_external_asset_owner_journal_entry_mapping`; `JournalEntryReadPlatformServiceImpl.java:103` reads it back as `eao.external_id` **[T497, F-1 follow-through]** |
| **Two rounding sites on the posting path, not one** | **R-1:** `fineract-core/.../monetary/domain/MoneyHelper.java:35` (`PRECISION = 19`), `:91-93` (`new MathContext(PRECISION, getRoundingMode())`) — 19 **significant digits**. **R-2:** `fineract-accounting/.../journalentry/domain/JournalEntry.java:90` (`@Column(name="amount", scale=6, precision=19)`), `:91` (the `BigDecimal` field), `:125` (`this.amount = amount`, no coercion), `0001_initial_schema.xml:145` (`DECIMAL(19, 6)`) — 6 **decimal places**. Producer of unbounded scale: `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:964` (`mc = MoneyHelper.getMathContext()`), `:981` (`multiply(paidAmount, mc).divide(chargeAmount, mc)`). **All eight lines opened by T497 at the pin. What the database does with such a value is `TDG-P1` and is UNOBSERVED.** |
| The Fineract ordering test asserts on one branch of five | `JournalEntryReversalOrderingIntegrationTest.java:113-155`: sole assertion at `:140`; the four other arms (`:130-131`, `:136-137`, `:142-145`, `:146-149`) are empty comment blocks; the stated rule is a comment at `:124-127` **[T497, F-13]** |
| `cap11.sh` self-identifies as `cap10.sh` | `.softhouse/capture/t352-a2-next-tranche/cap11.sh:2,15,31,52,53,66` **[T497, F-11]** |

---

## 10. The reviewer's first question, answered here

> **Does any row of this plan state a value that was not observed?**

**No. There is no `expect` column and NO VALUE APPEARS IN AN EXPECTATION POSITION.** Test literals appear
**labelled and attributed**, which is a different thing.

**[WORDING CORRECTED BY T497 on T491 finding F-9.** The earlier draft said *"no expected status code … anywhere
in this document"*, which over-reached: HTTP **`403`** *does* appear, three times, in `TDG-A1`–`A3` — correctly
labelled `TEST-ASSERTION`, correctly attributed to `GLAccountIntegrationTest.java:84-85, :104-105, :122-123`,
and correctly described as what that test asserts. §8 item 7 already stated the position accurately: *"No
status code and no message string is asserted anywhere in this document **as an expected value**."* **§10 now
matches §8 item 7. The qualifier is the whole point** — without it, a capture operator skimming `TDG-A1` could
read `403` as the target rather than capturing whatever the oracle returns.**]**

Where a Fineract test asserts a literal, it is labelled `TEST-ASSERTION`,
attributed to `FILE:LINE`, and described as *"the test asserts X"* — **a fact about that file, and the §0
table gives it trust value NONE.** Where Fineract main source predicts a behaviour, it is labelled
`SOURCE-DERIVED HYPOTHESIS`, cited, and each case states **what observation would refute it**. Everything
else is `TO_BE_CAPTURED` and states no value.

**The cases T497 added are held to the same rule and were written under it.** `TDG-O1` names the two refusal
branches from source and **declines to say which one fires**. `TDG-O2` names the fields to record and no value
for any of them. `TDG-P1` — a probe whose entire purpose is to observe one behaviour — **does not name that
behaviour**: not round, not truncate, not error, and no rounding mode. A guess written into a probe would be
worse than a guess written anywhere else in this document, because nothing downstream would ever question it.

**No oracle was reachable from this fire, and that was probed rather than assumed** — `/var/run/docker.sock`
absent, `127.0.0.1:5432` refused, `127.0.0.1:8443` refused — so no value in this document *could* have been
observed, and none is claimed to have been.

**One further disclosure, because a document that hunts for unverified claims should report its own.** The
first draft of §8 item 4 asserted that `GLAccount` carries an `is_deleted` column. It does not. The claim was
inferred from a neighbouring fact about `GLClosure` and was never checked; it was caught by a pre-commit
sweep of this document's own citations, measured against the schema and the entity, and **corrected in place
with the error named** rather than quietly deleted. No other claim in this document was found to be
unsupported by that sweep. **T497 note: that sweep could not have caught §1.4(g), because every citation in
the false claim resolved. The residual risk this document carries is not mis-citation — it is a UNIVERSAL
CLAIM MADE OVER UNREAD FILES, and §1.3 row 18 is the boundary that says which files those are.**

---

## 11. Corrections register — T497, applying T491's review

**This section exists so that a later reader can tell which claims in this document were revised, on whose
evidence, and whether the revision changed what gets captured.** T488 wrote the plan; **T491** reviewed it
independently and returned **ACCEPT WITH CONDITIONS (4 MAJOR, 9 MINOR)**; **T497** applied the conditions.

**T497 re-derived every finding from `/home/user/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`
before writing it in** `[VERIFIED: git rev-parse HEAD → 426a23544e8426a38ae43ae404670a0a7e85b9eb; the
checkout was read-only throughout and nothing in it was modified]`. **No finding was applied on T491's word.**
T497 also reached **no oracle**: no Fineract, no PostgreSQL and no Docker daemon in its sandbox, so it
executed **no capture, created no vector, and promoted nothing.**

| Finding | Verdict on re-derivation | Where applied | Does it change what gets captured? |
|---|---|---|---|
| **F-1** MAJOR — "exactly one POST call site"; "never posts a manual JE for its own sake" | **CONFIRMED as an error, and the shape-changing half REFUTED.** Five sites re-derived; `:1349` posts for its own sake. **The companion "never reverses one" is CONFIRMED by T497's own whole-tree searches and is NOT weakened.** | §1.2, §1.3 rows 2/18/19/20, **new §1.4(g)**, §9 | **Yes — two cases added (group O).** |
| **F-2** MAJOR — TDG-C3 cited to lines that contradict it | **CONFIRMED.** `:105-107` names `CHARGE_OFF_EXPENSE` in the cited arm. Claim **true on main source** (`:909-928`). Mock dated 2026-04-17 vs processor 2026-07-20; mock verifies the 9-arg `AccountingProcessorHelper.java:749`, path calls the 7-arg `:756` at `:949`/`:957`. | §3 group C re-anchoring notice; C1/C2/C3 re-cited; §8 item 11; §9 | **No.** The §4.7 recipe already asked the right question and stated no value. |
| **F-3** MAJOR — activation gate read as a scope block | **CONFIRMED.** CLAUDE.md: *"a licensing gate on the activation, not a scope block on the port."* POLICY heading at `reference-oracle.md:1115` is scoped to the **SHARED** oracle; its `:1160` neighbour is treated as standing-only by this same plan. | §1.4(a) rewritten; §1.3 row 17 relabelled; §9 | **No.** The exclusion stands; only its grounds and finality change. |
| **F-4** MAJOR — unflagged `runningBalance=true` copy hazard | **CONFIRMED, and BROADER than cited.** T491 cited `:366`; T497 re-derived **five** sites in that file (`:174, :224, :299, :366, :438`). Admissibility chain re-read in `nexus/`. | §1.4(b) hazard 2; §8 item 2; §9 | **No new case; it constrains the plan's own top follow-up.** |
| **F-5** MINOR — 1,427 lines across 56 files | **CONFIRMED.** 1,427 lines across **48**; 56 is a different search. | §1.1, §8 item 2, §9 | No. |
| **F-6** MINOR — `AccountingScenario` split | **CONFIRMED.** 6 loan / 4 deposit / 1 shares, all eleven methods enumerated. | §1.3 row 3, §1.4(a), §9 | No. |
| **F-7** MINOR — `glclosures` search under-scoped | **CONFIRMED as under-scoped; the CLAIM HOLDS when widened** to the whole tree, all extensions. **Claim kept, search corrected — not dropped.** | §1.2, §9 | No. |
| **F-8** MINOR — "every read-back URL" vs "path" | **CONFIRMED.** `JournalEntryHelper.java:196-200` builds no URL. | §1.4(b) hazard 1 refinement | No. |
| **F-9** MINOR — §10 over-reaches | **CONFIRMED.** `403` appears, labelled. §8 item 7 was already accurate. | §10 aligned to §8 item 7 | No. |
| **F-10** MINOR — `TDG-00` item 1 mislabelled | **CONFIRMED.** A `git log` is evidence about a checkout. | §4.0 item 1 | No. |
| **F-11** MINOR — `cap11.sh` says `cap10.sh` | **CONFIRMED** at `:2,15,31,52,53,66`. | §4.2, §9 | No. |
| **F-12** MINOR — snake_case SQL columns are safe | **CONFIRMED.** The scanner keys on three **camelCase** response names. | §4.3, §9 | **No — it PREVENTS a fire dropping useful columns out of unfounded caution.** |
| **F-13** MINOR — the ordering test is near-vacuous | **CONFIRMED.** One assertion at `:140`; four empty comment arms. | §4.6, §9 | No. |

**Two things T497 did NOT simply transcribe.**

1. **A cost claim in T491's condition 1 is corrected.** T491 wrote that both `externalAssetOwner` cases are
   *"cheap and ride rank-1's throwaway."* True of **O1**; **false of O2**, which needs a client, product,
   loan, approval, disbursement and an investor-context transfer initiation
   (`InitiateExternalAssetOwnerTransferTest.java:1324-1347`). O1 is ranked **2a**; O2 is ranked **11**.
2. **A citation in T491's review is corrected.** T491 placed `externalAssetOwner` at
   `JournalEntryCommand.java:38`. In this checkout it is the field at **`:57`**, validated at `:79`.

**Three things T497 found that neither T488 nor T491 recorded**, all from source opened this session:
the `externalAssetOwner` **global-configuration** refusal branch that fires *before* the owner lookup
(`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:173-176`); that the owner is a **join**
(`m_external_asset_owner_journal_entry_mapping`), not a column on `acc_gl_journal_entry`; and that the
`runningBalance` response fields are appended to the SELECT **only** inside
`if (associationParametersData.isRunningBalanceRequired())` (`JournalEntryReadPlatformServiceImpl.java:104-108`)
— which grounds the harness's "iff" claim in Fineract source rather than in the harness's own assertion.

**One finding folded in from outside T491's review.** The program driver relayed T495/T490's **two rounding
sites** correction. T497 re-derived all eight cited lines at the pin before accepting it, and added **group P
/ `TDG-P1`** plus the promotion gate at §4.12 item 4a. **It is a probe, and it records what to observe and
nothing about what will be observed.**

**The property that had to survive this edit, re-checked after it.** **No row of this plan states a value that
was not observed from a running oracle, and no oracle was reachable to T488, to T491 or to T497.** There is
still no `expect` column. The cases T497 added state inputs, preconditions, the call to issue and the fields
to record — and no expected amount, status, message or behaviour. The only new *numbers* T497 introduced are
`FILE:LINE` citations, LOC and `@Test` counts for §1.3 rows 19-20, commit dates, and the **input shapes** for
`TDG-P1` (7, 12 and 19 digits) — which are values the capture **sends**, recorded as sent, exactly as §6
item 6 requires of every amount in this plan.
