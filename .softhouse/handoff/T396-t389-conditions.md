# T396 — T389's citation conditions on T388, discharged

**Branch:** `softhouse/T396-t389-conditions`.
**Grant written:** `.softhouse/capture/t388-accrual-capture/` (corrections in place) and
`.softhouse/capture/t396-t389-conditions/` (the port-traps write-up), plus this handoff.
**Nothing else was touched.** `.softhouse/vectors/`, `capabilities-ledger.json` (held by T391) and
`.softhouse/conformance.sh` (held by T404) were **not modified** — see §5.
**Pinned source for every citation:** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(`git rev-parse` run in that checkout). **Every line number below was opened and read by T396 at
that sha.** None was inherited from T389's prose or T388's — that inheritance is the defect class
this task exists to repair (P-86).

## What was NOT in question, and is unchanged

The load-bearing claim holds and I re-derived it rather than accepting it:
`/runaccruals` and job 16 converge on the **single overload**
`LoanAccrualsProcessingServiceImpl.addPeriodicAccruals(LocalDate):120-140`, whose own Javadoc at
`:120-122` names both callers — *"method adds accrual for batch job \"Add Periodic Accrual
Transactions\" and add accruals api for Loan"*. `git grep` over the pinned checkout finds exactly
**two** non-test callers of the one-argument method (`AccrualAccountingWritePlatformServiceImpl.java:49`,
`AddPeriodicAccrualEntriesTasklet.java:50`); the third accrual entry point,
`AddPeriodicAccrualEntriesBusinessStep.java:41`, calls the **two-argument** per-loan overload at
`:145-153`, so it is not a counter-example. Job 16 is seeded in source at
`0002_initial_data.xml:821-839`. **T388's observations are genuine periodic accruals.** No
conclusion of T388's was rewritten.

---

## 1. m-1 — the first hop of the `/runaccruals` citation

| | |
|---|---|
| **Was** | `` `AccrualAccountingApiResource.java:62` → `excuteAccrualAccounting` → `AccrualAccountingWritePlatformServiceImpl.executeLoansPeriodicAccrual` → `addPeriodicAccruals(tillDate)` `` |
| **Wrong because** | `:62-63` **builds** the `CommandWrapper`; it dispatches nothing. The chain also silently skipped the entire command bus. |
| **Now says** | `:62-63` builds (`new CommandWrapperBuilder().excuteAccrualAccounting()`, which sets `actionName = EXECUTE`, `entityName = PERIODICACCRUALACCOUNTING`, `href = /accrualaccounting`); **`:64` dispatches** via `commandsSourceWritePlatformService.logCommandSource(commandRequest)`, and the full bus chain is written out. |

**Verified citations (all re-read by T396):**

| symbol | file:line |
|---|---|
| `AccrualAccountingApiResource.executePeriodicAccrualAccounting` | `fineract-accounting/.../accrual/api/AccrualAccountingApiResource.java:61-65`; **build `:62-63`**, **dispatch `:64`** |
| `CommandWrapperBuilder.excuteAccrualAccounting` | `fineract-core/.../commands/service/CommandWrapperBuilder.java:1769-1775` |
| `PortfolioCommandSourceWritePlatformServiceImpl.logCommandSource` | `fineract-core/.../commands/service/PortfolioCommandSourceWritePlatformServiceImpl.java:56-82` (hand-off at `:81`) |
| `SynchronousCommandProcessingService.executeCommand` / `executeCommandAttempt` / `executeCommandInTransaction` | `fineract-core/.../commands/service/SynchronousCommandProcessingService.java:105-109` / `:111-152` / `:154-196` (handler call at `:159`) |
| `CommandSourceService.processCommandAndSaveResult` | `fineract-core/.../commands/service/CommandSourceService.java:116-124` (`handler.processCommand` at `:120`) |
| `ExecutePeriodicAccrualCommandHandler.processCommand` | `fineract-accounting/.../accrual/handler/ExecutePeriodicAccrualCommandHandler.java:37-41`; `@CommandType(entity = "PERIODICACCRUALACCOUNTING", action = "EXECUTE")` at `:31` |
| `AccrualAccountingWritePlatformServiceImpl.executeLoansPeriodicAccrual` | `fineract-provider/.../accounting/accrual/service/AccrualAccountingWritePlatformServiceImpl.java:44-59`; validator `:46`, `tillDate` `:47`, call `:49` |
| job 16 seed | `fineract-provider/src/main/resources/db/changelog/tenant/parts/0002_initial_data.xml:821-839` — `id` `:822`, name `:823`, cron `0 2 0 1/1 * ? *` `:825` |
| `JobName.ADD_PERIODIC_ACCRUAL_ENTRIES("Add Periodic Accrual Transactions")` | `fineract-core/.../infrastructure/jobs/service/JobName.java:36` |
| `AddPeriodicAccrualEntriesConfig` | `fineract-loan/.../jobs/addperiodicaccrualentries/AddPeriodicAccrualEntriesConfig.java:42-57` |
| `AddPeriodicAccrualEntriesTasklet.execute` | `fineract-loan/.../jobs/addperiodicaccrualentries/AddPeriodicAccrualEntriesTasklet.java:39-47` (`:42`), private hop `:49-51` |

**Note T389 made and I confirm:** the command-bus hop T388 omitted is exactly what produced
command-source row **379** and its `Idempotency-Key`, which T388 relies on elsewhere in the same
document.

**Correction to T389's own citation, found while verifying:** T389 wrote the job seed as
`0002_initial_data.xml:821-838`. The `</insert>` is at **`:839`**. Trivial, recorded so the next
reader does not inherit it.

---

## 2. m-2 — "the ONLY difference is where `tillDate` comes from"

| | |
|---|---|
| **Was** | *"the only thing the manual trigger changes is which date is accrued to"* |
| **Wrong because** | Read as a statement about the pipeline it is false — and it errs **in T388's own favour**, understating the difference between the paths rather than overstating the result. |
| **Now says** | Inside `addPeriodicAccruals` the paths are identical; **before** it they are not. Five extras sit on the API side only; the tasklet calls the service directly with no bus (`AddPeriodicAccrualEntriesTasklet.java:39-51`). Each is given a verdict on whether it can change what gets accrued. |

### The five differences, each with a verdict

| # | difference | verified citation | **changes what gets accrued?** |
|---|---|---|---|
| **1** | **Permission check `EXECUTE_PERIODICACCRUALACCOUNTING`** | `PortfolioCommandSourceWritePlatformServiceImpl.java:70` — `authenticatedUser(wrapper).validateHasPermissionTo(wrapper.getTaskPermissionName())`. Permission string is `actionName + "_" + entityName` (`CommandWrapper.java:103`; accessor `taskPermissionName():314`), halves set at `CommandWrapperBuilder.java:1770-1771` | **NO.** Binary gate on the whole call — throw, or an identical run. It can never accrue a *different* set. |
| **2** | **Idempotency-key resolution + replay guard** | `SynchronousCommandProcessingService.java:131` → `IdempotencyKeyResolver.resolve:35-37` (request key → request attribute → minted UUID); guard `SynchronousCommandProcessingService.exceptionWhenTheRequestAlreadyProcessed:241-262`, invoked at `:133`, throwing on `UNDER_PROCESSING` / `PROCESSED` / `ERROR` | **NO — but it decides whether it runs at all.** Same gate shape as (1). It is what makes a *repeat* `POST /runaccruals` a refusal rather than a second accrual — behaviour the Go port owes — but it never alters the installment set of a run that proceeds. |
| **3** | **A persisted `m_portfolio_command_source` row**, result written back | `SynchronousCommandProcessingService.java:136-143`, `saveInitial` at `:140`; result update `CommandSourceService.processCommandAndSaveResult:122-123` | **NO.** Audit write, outside the accrual arithmetic. It is why row **379** (`EXECUTE / PERIODICACCRUALACCOUNTING`) exists with an `Idempotency-Key`; the job path writes no such row. |
| **4** | **Maker-checker gate** | `CommandSourceService.validateMakerChecker:126-143`, called at `:121`; test `isMakerCheckerEnabledForTask(permission)` at `:129-130`; `markAsAwaitingApproval` + `RollbackTransactionNotApprovedException` at `:139-140` | **YES, IN ONE DIRECTION — it can make the accrual not happen.** It runs **after** `handler.processCommand` (`:120`) has computed and written the accrual, then rolls the transaction back. On a maker-checker-enabled tenant the API path computes exactly what the job would and persists **nothing**. It cannot make it accrue something *different*. Inert on this tenant by seed default. |
| **5** | **`tillDate` validator (`tillDate <= businessDate`) + unsupported-parameter rejection** | `AccrualAccountingWritePlatformServiceImpl.java:46` → `AccrualAccountingDataValidator.validateLoanPeriodicAccrualData:54-71`; date test `validateDateBefore(DateUtils.getBusinessLocalDate())` at `:67-68`; semantics `DataValidatorBuilder.validateDateBefore:1036-1043` — errors only when `isBefore(businessDate, tillDate)`, so **equality passes** | **NO, AND IT CANNOT.** It only restricts the *domain* of `tillDate` to `<= businessDate`. Because equality passes, the API can reproduce the job's exact input — there is no `tillDate` the job can use that the API cannot. This is the one difference that could in principle have made the paths inequivalent, and it does not. |

**Sixth asymmetry, on the JOB side, recorded because it cuts the other way:** the scheduler sets
`ThreadLocalContextUtil.setActionContext(ActionContext.DEFAULT)` at `JobStarter.java:95`, and
`DateUtils.getBusinessLocalDate:238-240` → `ThreadLocalContextUtil.getBusinessDate:94-97` resolves
via `getActionContext().getBusinessDateType()` — `DEFAULT → BUSINESS_DATE`, `COB → COB_DATE`
(`ActionContext.java:29-30`). The same expression yields a **different date** under a COB action
context, which is the context `AddPeriodicAccrualEntriesBusinessStep.java:41` runs in.

**Net effect on T388's conclusion: none.** *"NOT evidence about the scheduler"* survives, and the
corrected argument supports it more strongly than the original.

---

## 3. m-3 — THE ONE THAT COSTS SOMETHING

| | |
|---|---|
| **Was** | *"That periods 1–3 accrued and periods 4–6 did not is the `FIND_LOANS_FOR_PERIODIC_ACCRUAL` predicate behaving as written (`ls.fromDate < :tillDate`; period 4's `fromDate` is `2026-04-15`, which is not `< 2026-04-15`, and it is not the minimum instalment)."* |
| **Wrong because** | That JPQL is `select l from Loan l … and (exists (select ls.id from LoanRepaymentScheduleInstallment ls where ls.loan.id = l.id …))` — `LoanRepository.LOANS_FOR_ACCRUAL:109-116` + `FIND_LOANS_FOR_PERIODIC_ACCRUAL:117-118`, bound at `findLoansForPeriodicAccrual:261-264`. **It selects LOANS, not PERIODS**, and it is an `EXISTS`: installment 1 (`fromDate 2026-01-15 < 2026-04-15`) alone admits loan 8, and the query renders no verdict on period 4 at all. The reading of the JPQL *text* was correct; using it to explain a per-period outcome was not. |
| **Now says** | The per-period cutoff is `LoanAccrualsProcessingServiceImpl.getInstallmentsToAccrue:466-475`, reached from `calculateAccrualAmounts:447-464` at `:456-457` with `isFinal = false` (set by `addAccruals(loan, tillDate, true, false, true, chargeOnDueDate)` at `:152`), and the comparison is `LoanRepaymentScheduleProcessingWrapper.isBeforePeriod:260-263`. Re-derived on T388's own data: installment 1 kept by the **inclusive** branch, 2 and 3 by the **strict** branch, 4 dropped because `2026-04-15` is not *after* `2026-04-15`. **The observed 1–3 / 4–6 split is exactly right.** |

### THE THREE PORT TRAPS — named, and where a porting task meets them

Full write-up with truth tables, Go consequences and the vectors to add:
**`.softhouse/capture/t396-t389-conditions/PORT-TRAPS-periodic-accrual-period-selection.md`.**

A porting task meets them at **three doors**, all now signposted:

1. `.softhouse/capture/t388-accrual-capture/README.md` — a `⚠` section above the fold, before the
   Files table, because the README is what a promotion task opens first.
2. `.softhouse/capture/t388-accrual-capture/ORACLE-STATE-MOVED-BY-T388.md` §2 — the corrected m-3
   paragraph ends in a boxed pointer, so a reader arriving at the observation itself cannot miss it.
3. The traps file lives in this task's own grant directory and states its audience in its first
   section: whoever promotes T388's observations, or ports `LoanAccrualsProcessingService` in
   program context **A2 / GL-accounting**.

**TRAP A — the FIRST installment compares `<=`, every other one `<`.**
`isBeforePeriod:262` is `isFirstPeriod ? isBefore(targetDate, fromDate) : !isAfter(targetDate, fromDate)`;
negated by `getInstallmentsToAccrue:472` that is **`tillDate >= fromDate`** for the first
installment and **`tillDate > fromDate`** for all others. And "first" is not "number 1":
`fetchFirstNormalInstallmentNumber:236-239` returns the first **non-down-payment** installment, so
on a down-payment product the inclusive branch belongs to installment 2. A Go port with one
comparison for all installments diverges on exactly one input class — `tillDate ==
firstNonDownPaymentInstallment.fromDate` — where Fineract accrues installment 1 and the port
accrues nothing, silently, because the loan-level JPQL carries the same special case
(`LoanRepository.java:118`) and still selects the loan. **T388's capture is blind to this**
(`2026-04-15` is strictly after `2026-01-15`, so both branches agree).

**TRAP B — one config row switches the date test OFF, at both levels.**
`getInstallmentsToAccrue:472` reads `(!chargeOnDueDate || (…date test…))`, so when
`chargeOnDueDate` is false the `||` short-circuits and **every** non-down-payment installment not
before the organisation start date is returned, future ones included. `chargeOnDueDate =
isChargeOnDueDate()` (`:1184-1187`) is false exactly when global config `charge-accrual-date` is
`"submitted-date"` (`ACCRUAL_ON_CHARGE_SUBMITTED_ON_DATE` at `:104`). Seed default is `due-date`
and **switchable** (`0107_add_configuration_charges_accrual_date.xml`, `string_value = "due-date"`,
`enabled` true, `is_trap_door` false); code default also `due-date` when blank
(`ConfigurationDomainServiceJpa.getAccrualDateConfigForCharge:519-529`). The **same** flag is
passed as the `:futureCharges` bind at `addPeriodicAccruals:126-127`
(`findLoansForPeriodicAccrual(…, !isChargeOnDueDate())`), and
`FIND_LOANS_FOR_PERIODIC_ACCRUAL:117-118` begins `and (:futureCharges = true or ls.fromDate <
:tillDate or (…))` — so the loan-level cutoff collapses to `true` as well. **One config value
removes both date cutoffs.** A Go port that hard-codes the predicate is wrong for a whole tenant
configuration Fineract ships, and wrong in the under-accruing direction. **T388's capture is blind
to this** (it ran on the seed default).

**TRAP C — `tillDate + 1 day` for interest and selection, unshifted `tillDate` for charges.**
`calculateAccrualAmounts:454-455`:
`interestCalculationTillDate = loan.isProgressiveSchedule() && …isInterestRecognitionOnDisbursementDate() ? tillDate.plusDays(1L) : tillDate`,
and then **two different dates flow from one loop**: the shifted date goes to
`getInstallmentsToAccrue` (`:457`) and `addInterestAccrual` (`:460`); the **unshifted** `tillDate`
goes to `addChargeAccrual` (`:461`, signature `:577-578`). Predicate members:
`Loan.isProgressiveSchedule:1816`, `ILoanConfigurationDetails.isInterestRecognitionOnDisbursementDate:68`
(impl `LoanConfigurationDetails.java:201`), constructor parameter `LoanProduct.java:285`. Two
distinct Go failures from one omission: (i) a **different installment set** at every period
boundary — on such a product T388's own `tillDate = 2026-04-15` would have accrued installment 4
too, so a single-`tillDate` port reproduces this capture and diverges by a whole installment on
that product family; (ii) if the port shifts `tillDate` once at the top and uses it everywhere, it
gets interest right and **charges wrong** — the mirror bug, harder to see because the entry still
balances. **T388's capture is blind to this** (product 63 is not such a product).

**No float is involved in any of the three.** They are calendar-date and configuration traps; the
amounts they move remain integer minor units under the ratified production `MathContext
(19, HALF_UP)`.

---

## 4. What was changed, file by file

| file | change |
|---|---|
| `.softhouse/capture/t388-accrual-capture/ORACLE-STATE-MOVED-BY-T388.md` | §2 rewritten **in place**: a correction banner naming m-1/m-2/m-3 and the sha; the corrected `/runaccruals` chain (m-1); a new subsection *"The same METHOD is not the same PIPELINE"* with the five-row verdict table and the `ActionContext` note (m-2); a new subsection replacing the JPQL attribution with `getInstallmentsToAccrue` + `isBeforePeriod`, re-derived on T388's own dates, ending in the boxed pointer to the traps file (m-3). **T388's observations, amounts, tables and conclusions are untouched.** |
| `.softhouse/capture/t388-accrual-capture/README.md` | `⚠` section added above the fold pointing promotion/porting tasks at the traps file, and stating explicitly that no *observation* changed; T396 note appended to the *"Not that the SCHEDULED JOB was observed"* bullet summarising the five pipeline differences. |
| `.softhouse/capture/t396-t389-conditions/PORT-TRAPS-periodic-accrual-period-selection.md` | **new.** Audience, why it exists, the pinned code quoted with line numbers, the three traps with truth tables and Go consequences, the vectors each one demands, and a *"what a promotion task must not do"* list. |
| `.softhouse/capture/t388-accrual-capture/MANIFEST.sha256` | **regenerated** — see §4a. |
| `.softhouse/capture/t396-t389-conditions/T396-BAR.txt`, `T396-BAR-run2.txt` | the two bar transcripts. |
| `.softhouse/handoff/T396-t389-conditions.md` | this file. |

### 4a. The manifest — a casualty of my own correction, repaired narrowly and declared

`MANIFEST.sha256` pins **all 193** files in T388's capture directory, prose included. Correcting
two prose documents therefore broke it: measured before repair,
`shasum -a 256 -c MANIFEST.sha256` reported **191 OK, 2 FAILED**
(`./ORACLE-STATE-MOVED-BY-T388.md`, `./README.md`).

Repaired by re-running **T388's own generator**, `sh manifest.sh`, unmodified — not by hand-editing
digests. Result: **193 entries, `shasum -c` 193/193 OK, zero FAILED**, and
`git diff --stat .softhouse/capture/t388-accrual-capture/MANIFEST.sha256` is
**`1 file changed, 2 insertions(+), 2 deletions(-)`** — exactly the two prose digests. **All 191
evidence digests — every byte under `out/`, `req/`, `sql/` and every script — are unchanged**, and
the diff proves it rather than asserting it.

Declared loudly, in the corrected file's own banner as well as here, because a regenerated
integrity manifest is the shape of a tampered one. T389's `out/T389-R04-manifest-integrity.txt`
records the pre-correction digests; that transcript is history and is not superseded. **The
alternative — leaving T388's integrity instrument permanently red — was worse.**

## 5. Held paths — not touched

`git diff --name-only main...HEAD` is **7 files**: 3 under
`.softhouse/capture/t388-accrual-capture/` (two prose corrections + the regenerated manifest),
3 under `.softhouse/capture/t396-t389-conditions/` (the traps write-up + two bar transcripts), and
this handoff. **Zero** hits for `.softhouse/vectors/` (T391), `capabilities-ledger.json` (T391) or
`.softhouse/conformance.sh` (T404) —
`git diff --name-only main...HEAD | grep -E 'vectors/|capabilities-ledger|conformance\.sh'`
returns **rc 1, no matches** (the engine ran and matched nothing; not an unrun selector).

## 6. Conditions NOT discharged by this task

Recorded so the next reader does not mistake silence for completion. T389 raised **six**
conditions; this task was scoped to **condition 2 only** (m-1/m-2/m-3).

- **T389 condition 1 / M-1** — widen the casualty sweep to the whole repo and repair
  `docs/adr/DEC-2-gl-accounting-adapter.md:1061,3004`. **Open.** DEC-2 is ratified, so amending it
  is a `user` gate, not an edit — it must be raised, not applied.
- **T389 condition 3 / m-4, m-5** — the `t327` `run-all.sh` mechanism statement and the stale gl-16
  numbers. **Open**, outside this task's brief.
- **T389 condition 4** — discharge the `PROBES.tsv` obligation from `out/PROBES-APPEND-T388.tsv`.
  **Open**; the target is outside this task's grant.
- **T389 condition 5** — repair `.softhouse/RESUME.md:77`. **Open**; outside grant.
- **T389 condition 6** — preserve *"NOT ONE ENTRY IN THIS CORPUS"* when `capabilities-ledger.json`
  is rewritten. **Not mine**: T391 holds that file this wave. Nothing in T396's diff touches it.
- **T389 t-1, t-2** (the `67`/`68` and `191`/`193` counts). **Open**, trivial, outside brief.

## 7. The bar

Run from a **clean tree** after `git add -A` and commit, with **`bash`**, never `sh`. Probe-line
**presence** tested before its value (P-84): `grep -n 'probe'` first, then the value read from the
matched line — the line is **PRESENT** at `T396-BAR.txt:192` and reads
`reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`.

**Transcripts:** `.softhouse/capture/t396-t389-conditions/T396-BAR.txt` (run 1, on
`1d2670e2`+handoff, exit 0) and `T396-BAR-run2.txt` (run 2, on the fully-committed tree including
run 1's own transcript — the T370/T361 residual, closed positively rather than asserted).

| figure | required baseline | measured, run 1 | measured, run 2 |
|---|---|---|---|
| exit code | 0 | **0** | **0** |
| probe line | PRESENT, then `up` | **PRESENT** (`:192`), `probe = up` | **PRESENT**, `probe = up` |
| loanschedule parity | 46 / 0 | **46 PASS / 0 FAIL** | **46 / 0** |
| cells compared | 7,884 | **7884 graded**, 93 ungraded | **7884** |
| dead-path frontier | GREEN at deadOccurrences 108 | **GREEN**, `deadOccurrences=108` (corpus 1395, deadFiles 75); frontier 11 == pinned 11 | **GREEN**, `108` |
| wrong-impl pin | 14 | **all 14 wrong ledger implementations DIED through this harness** | **14** |
| ledger parity | — | **7 PASS / 0 FAIL** (== pinned 7) | **7 / 0** |
| ledger oracle-refusal | — | **6 PASS / 0 FAIL** (== pinned 6) | **6 / 0** |
| ledger money cells | — | **39** (== pinned 39) | **39** |
| inadmissible / harness errors / invariant violations / NOT RUN | 0 | **0 / 0 / 0 / 0** | **0 / 0 / 0 / 0** |
| VERDICT | PASS | **PASS (exit 0)** | **PASS (exit 0)** |

**One figure differs from T389's transcript, and it is `main`'s doing, not T396's — attributed
rather than waved through.** T389 recorded `ledger cells 142 / 39 money`; this run reads
**`144 graded, of which 39 are MONEY`**. Cause: `main` advanced from T389's `01a7a05a` to
`7400d9f2`, merging T360/T387 —
`git diff --name-only 01a7a05a main -- .softhouse/vectors/ nexus/` returns
`.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json` and six
`nexus/internal/apps/ledger/conformance/*.go` files. **T396's diff is Markdown, two `.txt`
transcripts and one `.sha256` manifest — no vector and no Go file**
(`git diff --name-only main...HEAD`), so it cannot have moved a graded cell. The **money** cell
count is unmoved at 39.

**A third bar run was taken after the manifest repair** (`T396-BAR-run3.txt`), because the repair
landed after run 2 and a transcript must cover the tree it describes.
