# T497 — applying T491's conditions to the Tier D GL capture plan

Task `T497` (`worker`), cloud fire, context `tierD-test-corpus`.
Branch `softhouse/T497-t491-conditions`, branched from `origin/softhouse/T488-tierD-gl-corpus-capture-plan`
@ `7a74ef5c`. Single file edited in place: **`docs/analysis/tierD-gl-corpus-capture-plan.md`**.

Reviewing input: `softhouse/T491-review-t488` — `.softhouse/reviews/t491-review-t488/REVIEW.md` and
`.softhouse/handoff/T491-review-t488.md`, both read in full. Verdict there:
**ACCEPT WITH CONDITIONS, 4 MAJOR / 9 MINOR, safe to execute unattended once conditions 1–4 are applied.**

**Pin, verified by me this session:** `git -C /home/user/fineract rev-parse HEAD` →
**`426a23544e8426a38ae43ae404670a0a7e85b9eb`**. The checkout was read-only throughout; nothing in it was
modified and no other ref was checked out (other workers read it concurrently).

**I RE-DERIVED EVERY FINDING FROM SOURCE BEFORE WRITING IT IN.** This program has twice had a reviewer's
patch refuted by the worker asked to apply it (T451→T449, T455→T448). Nothing below was applied on T491's
word. Where my re-derivation disagreed with T491, I say so and my citation wins.

**What I could not do.** No Fineract, no PostgreSQL, no Docker daemon in this sandbox. **I executed no
capture, created no vector, promoted nothing, and touched nothing under `nexus/`** (I read
`admit.go` / `oraclederived.go` / `oraclederived_test.go`, and did not edit them). No DEC-n, no capability
file, no `.softhouse/gates.md`, no Go.

---

## Per-finding verdict

| Finding | Verdict | Applied where |
|---|---|---|
| **F-1** MAJOR | **APPLIED — confirmed as an error, and one half of the derived finding REFUTED as T491 said** | §1.2, §1.3 rows 2/17/18 + new rows 19/20, **new §1.4(g)**, new §3 group O, new §4.11a, §7 ranks 2a/11, §9, §11 |
| **F-2** MAJOR | **APPLIED — confirmed in full, including the staleness and the overload mismatch** | §3 group C re-anchoring notice; C1/C2/C3 re-cited to main source; §8 item 11; §9 |
| **F-3** MAJOR | **APPLIED — confirmed; exclusion kept, grounds and finality replaced** | §1.4(a) rewritten; §1.3 row 17 relabelled `R — PRODUCT`; §9 |
| **F-4** MAJOR | **APPLIED — confirmed, and BROADER than T491 cited** | §1.4(b) hazard 2; §8 item 2; §9 |
| **F-5** MINOR | APPLIED — confirmed exactly | §1.1, §1.2, §1.4(e), §8 item 2, §9 |
| **F-6** MINOR | APPLIED — confirmed exactly (6/4/1) | §1.3 row 3, §1.4(a), §9 |
| **F-7** MINOR | APPLIED — search widened, **claim kept** | §1.2, §9 |
| **F-8** MINOR | APPLIED as a refinement | §1.4(b) hazard 1 |
| **F-9** MINOR | APPLIED — §10 aligned to §8 item 7 | §10 |
| **F-10** MINOR | APPLIED | §4.0 item 1 |
| **F-11** MINOR | APPLIED | §4.2, §9 |
| **F-12** MINOR | APPLIED | §4.3, §9 |
| **F-13** MINOR | APPLIED | §4.6, §9 |
| **Driver relay (T495/T490): two rounding sites** | **APPLIED after independent re-derivation** | new §3 group P / `TDG-P1`, new §4.11b, §4.12 item 4a, §4.3, §4.9, §7 rank 1a, §8 item 10, §9 |

**Nothing was refuted outright. Two of T491's own statements were corrected** (below), and the review's
conclusions all survived my re-derivation.

---

## The four MAJORs, as I re-derived them

### F-1 — five manual-JE POST call sites, not one; and the universal claim is refuted

`[VERIFIED by me at the pin: grep -rn 'createJournalEntry\b' --include='*.java' . | grep -v /src/main/;
grep -rn 'createGLJournalEntry' --include='*.java' . | grep -v 'fineract-client/src/main']`

- `integration-tests/.../accounting/GLAccountIntegrationTest.java:115`
- `integration-tests/.../investor/externalassetowner/InitiateExternalAssetOwnerTransferTest.java:1315`
  (refusal arm, inside `assertThrows`, asserting the message contains `"External asset owner with external id:"`)
- `…/InitiateExternalAssetOwnerTransferTest.java:1349` — in `addManualJournalEntriesWithAssetExternalization`
  (`:1307-1367`), posts a manual JE, reads it back at `:1358-1359`, asserts on the legs at `:1361-1365`
- `fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:384` and `:397`

**I re-ran T488's own grep** (`grep -rn journalentries integration-tests/src/test --include=*.java`): its only
hits are `JournalEntryHelper.java:139,163,185` (hand-built URLs) plus two `createjournalentries` provisioning
flags. **It is structurally blind to the POST sites** — the POST goes through the generated
`createGLJournalEntry`, so a caller contains no such string. The claim was also asserted over `investor/*`,
which §1.3 row 18 itself declared NOT OPENED.

**"…and never reverse one" is CONFIRMED, by my own whole-tree searches, and I did not weaken it.**
`grep -rn reverseJournalEntry --include=*.java . | grep -v /src/main/` → empty;
`grep -rn 'command=reverse'` over `*.java` and `*.feature` outside `/src/main/` → empty;
`grep -rn '"reverse"' --include=*.java . | grep -v /src/main/` → one hit, `SavingsAccountHelper.java:93`
(`REVERSE_TRASACTION_COMMAND`), a savings-transaction command.

**Two cases added: `TDG-O1`** (refusal, unregistered `externalAssetOwner`) **and `TDG-O2`** (accept +
read-back, plus the `m_external_asset_owner_journal_entry_mapping` rows).

**THREE THINGS I FOUND THAT NEITHER T488 NOR T491 RECORDED**, all read at the pin:

1. **`externalAssetOwner` has TWO refusal branches, and the first is a global-configuration gate that fires
   before the owner lookup.** `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:173-176` throws
   `JournalEntryRuntimeException("error.msg.glJournalEntry.asset.externalization.not.enabled", …)` when
   `ASSET_EXTERNALIZATION_OF_NON_ACTIVE_LOANS` is disabled; only then does `:179-180` throw
   `ExternalAssetOwnerNotFoundException` (`fineract-investor/.../ExternalAssetOwnerNotFoundException.java:28`).
   **On a fresh throwaway the config branch is reachable, so O1 records `GET /configurations` first and
   predicts NEITHER branch.**
2. **The owner is a JOIN, not a column.** `:679` → `AccountingServiceImpl.java:123-132` writes
   `m_external_asset_owner_journal_entry_mapping`; the read-back surfaces it as
   `eao.external_id as externalAssetOwner` (`JournalEntryReadPlatformServiceImpl.java:103`). There is **no
   `external_asset_owner` column on `acc_gl_journal_entry`**, so §4.3's field list cannot reach it.
3. **A cost claim in T491's condition 1 is wrong.** T491: *"Both are cheap and ride rank-1's throwaway."*
   True of O1. **False of O2** — `InitiateExternalAssetOwnerTransferTest.java:1324-1347` needs a client, a
   loan product, an application, an approval, a **disbursement** and an **initiated external-asset-owner
   transfer** before the owner exists. O1 is ranked **2a**; O2 is ranked **11**, last, with its Tier B
   crossing stated.

**Also a citation correction to T491:** `externalAssetOwner` is at `JournalEntryCommand.java:57` (validated
at `:79`), not `:38` as the review stated. I opened the file.

### F-2 — TDG-C3's citation contradicts its claim; the claim is true on main source

**Confirmed both halves.** `CreateJournalEntriesForChargeOffLoanTest.java:105-107` verifies
`createDebitJournalEntryForLoan(…, AccrualAccountsForLoan.CHARGE_OFF_EXPENSE.getValue(), …)` **in the
reason-mapped arm** — the very arm cited as not reaching the slot. On main source
(`AccrualBasedAccountingProcessorForLoan.java:909-928`): `mapping != null` at `:914` → credit `LOAN_PORTFOLIO`
(`:915-917`), debit `mapping.getGlAccount()` (`:918`); the `else` at `:919-927` holding
`CHARGE_OFF_FRAUD_EXPENSE` (`:921-923`) and `CHARGE_OFF_EXPENSE` (`:924-926`) is **never entered**.

**The staleness, re-derived:** `git log -1 --date=short` → mock **2026-04-17** (`d01fedfd`),
`AccrualBasedAccountingProcessorForLoan.java` **2026-07-20** (`99930230`, "FINERACT-2455: Rework transaction
reprocessing"). **Overloads confirmed by opening `AccountingProcessorHelper.java`:** `:749` is the **9-arg**
(`…, int accountMappingTypeId, loanProductId, paymentTypeId, loanId, …`) the mock verifies; `:756` is the
**7-arg** (`…, loanId, transactionId, transactionDate, amount, GLAccount account`) the charge-off path calls
at `AccrualBasedAccountingProcessorForLoan.java:949` (credits) and `:957` (debits).

**Correction to T491's line numbers:** the credit emit is at `:949`, not `:953`. **Tagged `[UNVERIFIED]` in
the plan (§8 item 11):** whether the mock therefore *fails* at this pin — that is a build question, no Gradle
was run, and `/home/user/fineract` is read-only and shared.

### F-3 — an activation gate read as a scope block

CLAUDE.md § *Blocking questions*: *"Porting `fineract-savings` / deposit code is in scope; enabling
deposit-taking behavior in any live environment is not … **This is a licensing gate on the activation, not a
scope block on the port.**"* Confirmed. `.softhouse/reference-oracle.md:1115` heads that section
*"POLICY — firing a probe at the **SHARED** reference oracle"*; the deposit bullet is `:1163`; its neighbour
at `:1160` (*"Never a … closure … GL-account edit"*) is one **this same plan** treats as standing-only,
since `TDG-R5` and `TDG-A1`–`A4` do both on a throwaway. Reading one bullet universally and its neighbour
narrowly was inconsistent.

**Applied:** exclusion **kept**; `R — LEGAL` → `R — PRODUCT (deprioritised)`; *"on grounds no later agent may
re-litigate"* **struck**; two PRODUCT/ENGINEERING grounds stated (no deposit endpoint on an NBFI deployment;
DEC-2's graded domain is loan/GL and `admit.go` default-denies); and one paragraph recording that porting
deposit code **remains in Tier B scope**.

### F-4 — the `runningBalance=true` copy hazard, broader than cited

T491 cited `JournalEntriesStepDef.java:366`. **Re-derived, the pattern is at FIVE sites in that one file —
`:174`, `:224`, `:299`, `:366`, `:438`** — i.e. it is the file's uniform read-back idiom.
`[VERIFIED: grep -n runningBalance on that file]`

Admissibility chain re-read: `nexus/internal/apps/ledger/conformance/admit.go:141` calls
`opts.OracleDerived.CaptureRuleReasons(...)`; `oraclederived.go:230-243` and `:803-814` state the rule and
call such a vector **INADMISSIBLE**; `.softhouse/vectors/oracle-derived-columns.json` →
`capture_rule.forbidden_response_field_names` = `organizationRunningBalance, officeRunningBalance,
runningBalanceComputed`.

**I grounded the harness's "iff" claim in Fineract source rather than in the harness's own assertion:**
`JournalEntryReadPlatformServiceImpl.java:104-108` appends exactly those three columns to the SELECT **only**
inside `if (associationParametersData.isRunningBalanceRequired())`.

**A third hazard I added, honestly bounded:** `JournalEntryHelper.java:196-200` passes nineteen positional
arguments with a bare trailing `true`. On the **server-side** signature (`JournalEntriesApiResource.java:112-131`)
slot nineteen is `transactionDetails`, not `runningBalance` — so that call is *not* hazard 2 —
but `[UNVERIFIED]` whether the **generated client's** order matches, since its models are absent from the
checkout. The recipe consequence is unconditional either way: named query parameters over `curl`, never
positional args through a generated client.

**Also named the fourth, strongest running-balance blocker** T491 said went unnamed: `admit.go:141`'s
`CaptureRuleReasons` refuses the vector on its **cited capture bytes**, whichever reader produced them —
which is why group B now lists **four** blockers, and why blocker (iii) is now scoped to `/glaccounts`
(module path corrected to `fineract-accounting/…`) and tagged `[UNVERIFIED: runtime]` for its HTTP status.
T429 captured `GET /journalentries/78?runningBalance=true` live on 2026-08-29
(`nexus/.../oraclederived_test.go:19-30`), so the `/journalentries` reader demonstrably works on PostgreSQL.

---

## The driver's relay — T495/T490's two rounding sites

Re-derived before accepting. **All eight lines opened at the pin:**
`MoneyHelper.java:35` (`PRECISION = 19`), `:91-93` (`new MathContext(PRECISION, getRoundingMode())`);
`JournalEntry.java:90` (`@Column(name="amount", scale = 6, precision = 19, nullable = false)`), `:91` (the
`BigDecimal amount` field), `:125` (`this.amount = amount;` — **no coercion**);
`0001_initial_schema.xml:145` (`<column name="amount" type="DECIMAL(19, 6)">`);
and the producer `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:964`
(`final MathContext mc = MoneyHelper.getMathContext();`) and `:981`
(`taxDetail.getAmount().multiply(paidAmount, mc).divide(chargeAmount, mc)`).

**Note on T495's citation:** the annotation is at `:90` and the field it annotates at `:91`; T495 cited `:91`
for both. Immaterial, recorded for accuracy.

**Agreed and applied.** R-2 — the INSERT into `numeric(19,6)` — is a rounding site nothing in this program
has characterised, it cannot be characterised from source, and a `divide` at `(19, HALF_UP)` can exceed six
decimals. Added **`TDG-P1`** (§3 group P, §4.11b), ranked **1a** — four SQL statements on rank 1's instance —
and a **promotion gate at §4.12 item 4a**: no vector graded on an oracle-computed amount may be promoted
while `TDG-P1` is unanswered. Noted at §4.9 (S5/S6) and §4.3 (`scale(amount)` is where R-2 becomes visible).
**`TDG-P1` names no outcome — not round, not truncate, not error, and no rounding mode.**

---

## Case count

**Before:** 29 ids — 27 capture cases + `TDG-00` + the de-scoped `TDG-B1`.
**After: 32 ids — 30 capture cases + `TDG-00` + `TDG-B1`.** Added: `TDG-O1`, `TDG-O2`, `TDG-P1`.
No case was removed and no case's *observation* was changed; group C's rationale was re-anchored and group B
gained a fourth blocker.

---

## The property that had to survive, re-checked after the edit

**No row of this plan states a value that was not observed from a running oracle, and no oracle was reachable
to T488, to T491 or to T497.**

- There is still **no `expect` column** and nothing in an expectation position. I swept the document for
  `expect` / `expected value` / `expects` after editing; the only hits are §0's rule, §8 item 7 and §10's
  corrected wording — all of them statements *that no expected value appears*.
- **The three cases I added state inputs, preconditions, the call to issue and the fields to record, and no
  expected amount, status, message or behaviour.** `TDG-O1` names two source branches and declines to say
  which fires. `TDG-O2` names fields, not values. `TDG-P1` is a probe and names no outcome.
- The only new *numbers* I introduced are `FILE:LINE` citations, LOC / `@Test` counts for §1.3 rows 19-20,
  two commit dates, and `TDG-P1`'s **input** digit counts (7, 12, 19) — values the capture **sends**,
  recorded as sent, per §6 item 6.
- Every `FILE:LINE` I wrote is a line I opened at the pin. Where I could not establish something I wrote
  `[UNVERIFIED]` with a reason: the mock's pass/fail state (§8 item 11), the generated client's parameter
  order (§1.4(b) hazard 3), the `/glaccounts` HTTP status (§3 group B), image provenance (§4.0 item 1), and
  PostgreSQL's `numeric(19,6)` behaviour (§8 item 10).
- Every empty search I restated says **what was searched and over what** — the `glclosures` search was
  **widened, not dropped**, and §1.4(g) records why the original manual-JE search could not have found what
  it claimed to have excluded.

**Document changes are additive and traceable:** a new §11 corrections register lists every revised claim,
its verdict on re-derivation, where it was applied, and whether it changes what gets captured (for eleven of
the thirteen findings: it does not).
