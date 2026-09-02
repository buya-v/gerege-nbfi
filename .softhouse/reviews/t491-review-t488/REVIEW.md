# T491 — INDEPENDENT adversarial review of T488

**Reviewing:** `softhouse/T488-tierD-gl-corpus-capture-plan` @ `7a74ef5c7f5bb6b23a43b5f2eef7a3abfab79fd4`
— `docs/analysis/tierD-gl-corpus-capture-plan.md` (856 lines) and `.softhouse/handoff/T488.md`.

**Method, and the order it was done in.** Every measurement, source reading and admissibility check in §A
below was derived **before** either T488 artefact was opened. T488's conclusions were read only afterwards
and compared. **No number in this review is inherited from T488.**

**Fineract pin, verified by me this session:**
`git -C /home/user/fineract rev-parse HEAD` → **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**;
`git -C /home/user/fineract status --porcelain` → **empty**. The checkout was read-only throughout and
nothing in it was modified.

**What I could not do.** There is **no running Fineract and no PostgreSQL in this sandbox**. I executed no
capture, ran no SQL and issued no HTTP request. Every statement below about runtime behaviour is a statement
about **code I read**, and is marked as such.

---

## A. My independent derivation, before reading T488

Re-derived in `/home/user/fineract` at the pin. Commands are stated so the search, not just the result, is
reviewable.

| Measurement | My value | Command |
|---|---|---|
| `src/test` Java files / LOC | **1,254 files / 320,601 LOC** | `find . -name '*.java' \| grep '/src/test/'`, summed across **all** `xargs wc -l` batches |
| `src/main` Java files / LOC | **5,331 files / 544,996 LOC** | same, `/src/main/` |
| `*.feature` files / LOC | **158 / 200,763** | `find . -name '*.feature'` |
| `.feature` lines matching `journal` (ci) | **1,427 lines** across **48 files** | `grep -ri "journal" --include=*.feature .` |
| `.feature` files matching `journal\|accounting` (ci) | **56 files** | `grep -ril "journal\|accounting" --include=*.feature fineract-e2e-tests-runner` |
| `integration-tests/src/test` files / LOC | **533 / 192,234** | `find integration-tests/src/test -name '*.java'` |
| files using `JournalEntryHelper` / LOC | **30 / 33,910** | `grep -rl JournalEntryHelper integration-tests/src/test` |
| `fineract-accounting/src/test` | **1 file / 88 LOC** | `find fineract-accounting/src/test -name '*.java'` |
| savings/deposit tests carrying `JournalEntry` | **7 files / 7,755 LOC / 98 `@Test`** | filename match `saving\|deposit\|recurring` ∩ `grep -l JournalEntry` |
| `BigDecimal.valueOf(entry.getAmount())` in `LoanChargesMultipleDebitAccountsTest` | **16** at `66,69,132,186,299,312,352,363,521,572,590,633,666,742,811,838` | `grep -c` |
| ledger capabilities / not in graded domain | **14 / 6** | parsed `.softhouse/vectors/capabilities-ledger.json` |
| committed ledger vectors | **17**, `dec2_revision: 5` | `ls .softhouse/vectors/ledger/`; `PIN-ledger.json` |

**Direct manual-journal-entry POST call sites in the test corpus** (mine, whole tree):

- `integration-tests/.../accounting/GLAccountIntegrationTest.java:115`
- `integration-tests/.../investor/externalassetowner/InitiateExternalAssetOwnerTransferTest.java:1315` (a
  refusal arm, inside `assertThrows`)
- `integration-tests/.../investor/externalassetowner/InitiateExternalAssetOwnerTransferTest.java:1349`
- `fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:384` and `:397`

**Journal-entry reversal in the test corpus:** searched the whole tree for `reverseJournalEntry`,
`command=reverse` and `"reverse"` outside `/src/main/`. Only hit is
`SavingsAccountHelper.java:93` (`REVERSE_TRASACTION_COMMAND`, a savings-transaction command, not a journal
entry). **No test invokes `POST /journalentries/{txn}?command=reverse`.** The "reversed … Journal entries"
Gherkin steps are loan-transaction reversals.

**`glclosures`:** `grep -ril glclosure` over the **whole tree, all extensions**. The path string
`glclosures` appears only in `GLClosuresApiResource.java:58,88,103,106`, `CommandWrapperBuilder.java:1749,
1757,1765` and `apiLive.htm`. **No test file anywhere references the `/glclosures` path.** Three test files
reference the `GLClosure` **domain class** as a Mockito mock
(`CreateJournalEntriesForChargeOffLoanTest.java:31,65`, `CreateJournalEntriesForTransferLoanTest.java:33,72`,
`AccountingProcessorHelperTest.java:32,59`).

**Deleted markers.** `acc_gl_closure` **has** `is_deleted` (`GLClosure.java:50-51`; liquibase
`0001_initial_schema.xml` createTable at `:78`). `acc_gl_account` **has none** — its createTable spans
`0001_initial_schema.xml:49-75` with columns `id, name, parent_id, hierarchy, gl_code, disabled,
manual_journal_entries_allowed, account_usage, classification_enum, tag_id, description`, and
`GLAccount.java:43-84` (in **`fineract-core`**, not `fineract-accounting`) declares `disabled` and no deleted
field. `GLAccountWritePlatformServiceJpaRepositoryImpl.java:191,212` performs
`this.glAccountRepository.delete(glAccount)` — a hard delete at the JPA call site.

**Capture instruments.** `cap8.sh:82-86` issues `curl … -H "$A" -H "$T" -H "$CT"` and **no
`Idempotency-Key`**. `cap11.sh:53` — `[ -n "$KEY" ] || { echo "REFUSING: … exists to send an
Idempotency-Key and none was given …"; exit 2; }` — and `:79,82` send `-H "Idempotency-Key: $KEY"`. The two
copies (`t352-a2-next-tranche/`, `t388-accrual-capture/`) are byte-identical.

---

## B. The value sweep — the question this review exists to answer first

**I swept every one of the 29 ids (27 capture cases + `TDG-00` + the de-scoped `TDG-B1`), plus §1.4, §4.0–4.12,
§5, §6, §7, §8, §9 and §10 — the whole 856-line document.**

**No row states a value in an expectation position. There is no `expect` column, and I could not construct a
reading in which any number in the document functions as a golden-vector target.**

Every value that appears in the document falls into one of four classes, and I checked each occurrence:

1. **`TEST-ASSERTION` literals**, each carried with `FILE:LINE` and phrased as *"the test asserts X"*. The
   set is: HTTP `403` and the three `error.msg.glaccount.glcode.invalid.delete.*` strings (TDG-A1/A2/A3);
   `originalEntryCount * 2` (TDG-R4); `1000.0` / `"1000" EUR` in the quoted Gherkin block; `10000.0f`,
   `1000.0f`, `Float[] REPAYMENT_AMOUNT`, `BigDecimal.valueOf(entry.getAmount())`. **I verified every one of
   these against the cited file and every one is genuinely what that file says** (see §D). Each is
   accompanied by an instruction not to use it: §0's table gives `TEST-ASSERTION` the trust value
   "**NONE**"; §1.4(e) calls the Gherkin tables "the **worst** thing to copy"; §4.6 says the test's numbers
   "carry no authority here"; §6 item 6 says "Not one of them appears as a value anywhere in this plan".
2. **Ratified tenant parameters** from `CLAUDE.md` — `(19, HALF_UP)`, ordinal `4`, MNT / 496 / minor unit 2,
   `Asia/Ulaanbaatar`, PostgreSQL. These are project facts, not oracle observations, and §5 attributes each
   to `CLAUDE.md`.
3. **One format illustration** — `100000.250000` in §4.3 and §6 item 1, prefixed "e.g.", demonstrating the
   oracle's scale-6 wire text. This is the closest thing in the document to a stray number. It is *not* a
   target for any case, and it is in fact a leg amount already recorded as **observed** in
   `capabilities-ledger.json` § `ledger.money.minor.unit.conversion`.
4. **The pinned commit sha**, which I verified myself.

**`SOURCE-DERIVED HYPOTHESIS` rows — the ones the brief asked me to look at hardest.** I read every one.
None names a money value. Each names a *shape* (which slot, how many legs, which flag moves, which branch),
and each states a refutation condition. The two that come closest to naming something specific are §1.4(f)
step 3 ("a newly minted transaction id") and TDG-C2 ("the diff is confined to one account id") — both are
structural predictions, and TDG-C2 explicitly adds "**No account id and no amount is stated here**".

**One wording over-reach, not a synthesised value (recorded below as F-9).** §10 and the handoff both say
"no expected status code … anywhere in this document". `403` *does* appear, three times, correctly labelled
as a Fineract test's assertion. The accurate sentence is "no value appears in an expectation position; test
literals appear labelled and attributed." A capture operator skimming TDG-A1 could plausibly record `403`
as the target rather than capturing whatever the oracle returns.

---

## C. Findings

### F-1 — **MAJOR** — "exactly one `POST /journalentries` call site" is wrong, and the shape-changing finding built on it is refuted

**T488's claim.** §1.2, §1.4 finding 1, §9 and the handoff §2: *"`grep -rn journalentries` over the whole
integration corpus finds exactly **one** direct `POST /journalentries` call site, used by **one** test, and
only to make a `DELETE` fail … **Fineract's own tests never post a manual journal entry for its own sake,
and never reverse one.**"* Cited: `JournalEntryHelper.java:192-194`; "sole caller
`GLAccountIntegrationTest.java:115-118`".

**My derivation.** The cited search cannot find what it claims to have excluded. `JournalEntryHelper`'s POST
goes through the generated client method `createGLJournalEntry`; a caller of
`JournalEntryHelper.createJournalEntry` contains **neither** the string `journalentries` **nor** any
`/journalentries` path, so `grep -rn "journalentries"` is structurally blind to the call sites the claim is
about. Searching for the caller instead:

```
grep -rn 'createJournalEntry\b'  --include='*.java' . | grep -v '/src/main/'
grep -rn 'createGLJournalEntry'  --include='*.java' . | grep -v 'fineract-client/src/main'
```

- `integration-tests/.../accounting/GLAccountIntegrationTest.java:115` — the one T488 found, correctly
  characterised (setup for a `DELETE` refusal).
- `integration-tests/.../investor/externalassetowner/InitiateExternalAssetOwnerTransferTest.java:1315`
  — inside `Assertions.assertThrows(CallFailedRuntimeException.class, …)`, posting a manual entry with an
  unregistered `externalAssetOwner`, asserting the message contains `"External asset owner with external
  id:"`. **This is a manual-journal-entry refusal arm** — precisely the surface TDG-A1–A3 and DEC-2 §4.9's
  refusal taxonomy are short of.
- `integration-tests/.../InitiateExternalAssetOwnerTransferTest.java:1349` — inside a test **named**
  `addManualJournalEntriesWithAssetExternalization` (`:1306-1370`). It posts a manual journal entry, reads
  it back by transaction id via `JournalEntryHelper.retrieveJournalEntryByTransactionId` (`:1358-1359`) and
  asserts on the returned legs (`:1361-1367`: two page items, `externalAssetOwner` on both). **This is
  posting a manual journal entry for its own sake, and asserting on the result.**
- `fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:378-401` — two further POST
  helpers, `addManualJournalEntryWithoutExternalAssetOwner` and `addManualJournalEntryWithExternalAssetOwner`,
  driven by Gherkin steps such as `:403` *"Admin creates manual Journal entry with {string} amount and
  {string} date and unique External Asset Owner"*.

So: **five** direct manual-JE POST sites in the test corpus, **three** inside `integration-tests` alone, and
the universal claim is false. T488's §1.3 row 18 honestly declares the `investor/*` suite **NOT OPENED** —
which makes this a universal claim asserted over files the same document says it did not read.

The "never reverse one" half is **CONFIRMED** (my whole-tree search for `reverseJournalEntry` /
`command=reverse` outside `/src/main/` returns nothing relevant).

**What should change.** (i) Restate the claim as *"one direct manual-JE POST in the dedicated accounting
package; three in `integration-tests` overall; two more in the e2e step definitions."* (ii) Add two cases —
a manual JE with an **invalid** `externalAssetOwner` (a refusal arm for group A, mined from `:1315`) and a
manual JE **with** a valid one, checking that `externalAssetOwner` survives to the read-back legs (mined
from `:1349`). Both are cheap and ride rank-1's throwaway. (iii) The `externalAssetOwner` field is on
`JournalEntryCommand.java:38` and is otherwise uncaptured by this program; a Go port that drops it is
byte-identical to a correct one on every capture taken to date.

---

### F-2 — **MAJOR** — TDG-C3's cited lines do not support the claim they are cited for

**T488's claim.** §3 group C, TDG-C3: *"The mock test shows the reason mapping is consulted **first** and,
when present, the fraud/expense product slots are **not reached**."* Cited:
`CreateJournalEntriesForChargeOffLoanTest.java:89,101` vs `:114,142` (the `null` arms).

**My derivation.** The cited lines resolve, and they support the *first* half only:

- `:89` stubs `getChargeOffMappingByCodeValue(…)` to return a non-null `ProductToGLAccountMapping`; `:101`
  verifies it was called once. **Consulted — supported.**
- `:114` and `:142` stub it to `null` in the fraud and no-fraud arms. **Supported.**

The second half is **contradicted by the very test cited**. In the reason-mapped arm
(`shouldCreateJournalEntriesForChargeOff`, `:80-108`), `:105-107` verifies
`createDebitJournalEntryForLoan(…, AccrualAccountsForLoan.CHARGE_OFF_EXPENSE.getValue(), …)` — the product
expense slot **is** named in the assertion. Read only the cited lines and you get the opposite of the claim.

**The claim is nonetheless TRUE — but on evidence T488 does not cite.** From main source,
`AccrualBasedAccountingProcessorForLoan.java:909-928`:

```
909  ProductToGLAccountMapping mapping = chargeOffReasonCodeValue != null
910          ? helper.getChargeOffMappingByCodeValue(loanProductId, PortfolioProductType.LOAN, chargeOffReasonCodeValue)
911          : null;
913  if (MathUtil.isGreaterThanZero(principalAmount)) {
914      if (mapping != null) {
915-918      … addToCredit(LOAN_PORTFOLIO account); addToDebit(mapping.getGlAccount(), principalAmount);
919      } else {
921-926      … CHARGE_OFF_FRAUD_EXPENSE if isMarkedFraud, else CHARGE_OFF_EXPENSE
```

When the reason mapping resolves, the debit goes to `mapping.getGlAccount()` and **neither** slot enum is
reached. Precedence confirmed, from main source.

**A second, more consequential problem this exposes.** The charge-off path calls the **7-argument**
`createDebitJournalEntryForLoan(office, currencyCode, loanId, transactionId, transactionDate, amount,
glAccount)` (`AccountingProcessorHelper.java:756`, called at
`AccrualBasedAccountingProcessorForLoan.java:957`). The mock test verifies the **9-argument** overload
(`AccountingProcessorHelper.java:749`) at `:105-107`. `git log -1` puts the mock test at **17 Apr 2026** and
`AccrualBasedAccountingProcessorForLoan.java` at **20 Jul 2026** — the test predates a rework of the code it
tests. **Group C's hypotheses are anchored to a mock corpus that may no longer describe the live path.**

**What should change.** Re-cite TDG-C3 to `AccrualBasedAccountingProcessorForLoan.java:909-928`. Re-anchor
every group-C `SOURCE-DERIVED HYPOTHESIS` to main source and demote
`CreateJournalEntriesForChargeOffLoanTest` to case-discovery only, with the staleness noted. The **recipe**
in §4.7 is unaffected — it asks the right question ("whether the reason mapping pre-empts …") and states no
value — so this changes the rationale, not what gets captured.

---

### F-3 — **MAJOR** — the savings/deposit rejection reads an activation gate as a scope block, and applies a standing-oracle policy to a throwaway

**T488's claim.** §1.4(a) and handoff §2 finding 3: *"The savings/deposit half of the accounting test corpus
is unusable to us, and the reason is **LEGAL**, not technical … Law on Non-Banking Financial Activities Art.
12.1.3 / 12.1.4 … `.softhouse/reference-oracle.md` § POLICY item 2 … ~7,500 LOC / 97 tests … it removes them
**on grounds no later agent may re-litigate**."*

**My derivation of the facts.** The measurement reproduces: 7 files carrying `JournalEntry` whose names match
`saving|deposit|recurring`, **7,755 LOC**, **98 `@Test`** (T488: 7,489 / 97 — within one; the difference is a
filter boundary and is immaterial). The POLICY line exists —
`.softhouse/reference-oracle.md:1163`: *"**No deposit or savings behaviour.** The tenant is an NBFI (ББСБ) —
Law on Non-Banking Financial Activities Art. 12.1.3 / 12.1.4."*

**My derivation of the reasoning — and this is where it fails.**

1. **The label is wrong.** `CLAUDE.md` § *Blocking questions* is explicit: *"Porting `fineract-savings` /
   deposit code is in scope; **enabling deposit-taking behavior in any live environment is not** … **This is
   a licensing gate on the ACTIVATION, not a scope block on the PORT.**"* Art. 12.1.3 prohibits **the NBFI**
   from accepting deposits. Reading a reference implementation's arithmetic on a disposable Docker instance
   is not the NBFI accepting a deposit, and no article makes it one. This is not a **LEGAL** item under
   `CLAUDE.md` § *Answering gates*.
2. **The policy is applied outside its own scope.** `.softhouse/reference-oracle.md:1115` heads that section
   *"POLICY — firing a probe at the **SHARED** reference oracle"*. Item 2's neighbouring bullets in the same
   list — *"Never a … closure"*, *"Never a … GL-account edit"* — are ones T488 **correctly** treats as
   standing-tenant-only, since TDG-R5 plans a closure and TDG-A1–A4 plan GL-account deletes, both on the
   throwaway. The plan therefore reads two bullets of one list at two different scopes, and does not say why.
3. **"No later agent may re-litigate" is the harm.** That sentence converts a licensing gate on activation
   into an un-re-openable scope block over ~7,755 LOC of corpus, in direct tension with `CLAUDE.md`'s own
   wording. Tier B explicitly places savings/deposits **in scope for porting**. A later worker citing this
   sentence would block work `CLAUDE.md` mandates.

**Is the outcome nonetheless right? Yes — on different grounds.** No deposit capture belongs in *this* plan,
because (a) `CLAUDE.md` ratifies that an NBFI deployment **exposes no deposit endpoint**, so a deposit golden
vector grades a surface the Go module will never serve, and (b) DEC-2's graded domain is loan/GL — a savings
vector claims a capability `capabilities-ledger.json` does not carry, and `admit.go` refuses by default-deny.
Both are **PRODUCT/ENGINEERING** grounds, decidable by the driver and reversible.

**What should change.** Re-label §1.4(a) **PRODUCT (deprioritised), not LEGAL**; keep the exclusion; state
the two grounds above; **strike "on grounds no later agent may re-litigate"**; and add one sentence recording
that porting deposit code remains in Tier B scope per `CLAUDE.md`.

---

### F-4 — **MAJOR** — the plan misses a copy-from-Fineract hazard exactly parallel to its own §1.4(b), and it sits in the corpus the plan names as its top follow-up

**Context.** §1.4(b) is one of T488's three shape-changing findings, and a good one: Fineract's own read-back
helper hard-codes the wrong tenant, so a recipe copied verbatim reads an empty ledger. **Confirmed** (F-8).
§8 item 2 then names systematically indexing the Gherkin corpus as *"the highest-value follow-up to this
document."*

**The hazard the plan does not warn about.** The e2e corpus's own journal-entry read-back sets the one query
parameter this program's harness refuses outright:

```
fineract-e2e-tests-core/.../stepdef/common/JournalEntriesStepDef.java:364-367
    Map<String, Object> journalQueryParams = new HashMap<>();
    journalQueryParams.put("transactionId", transactionId);
    journalQueryParams.put("runningBalance", true);
    journalEntryDataResponse = journalEntriesApi().retrieveAllJournalEntries(journalQueryParams);
```

Against our admission rules that produces an **inadmissible** capture, not merely a noisy one:

- `nexus/internal/apps/ledger/conformance/admit.go:141` calls
  `opts.OracleDerived.CaptureRuleReasons(opts.RepoRoot, v)`.
- `oraclederived.go:230-243` and `:809-814`: *"A ledger parity vector may not be captured with
  `runningBalance=true` or `fetchRunningBalance=true` … the scanner looks for
  `organizationRunningBalance, officeRunningBalance, runningBalanceComputed` in the cited bytes … A vector
  citing such a body is **INADMISSIBLE**."*
- `.softhouse/vectors/oracle-derived-columns.json` → `capture_rule.forbidden_response_field_names`.

A fire that mines the feature corpus and copies its read-back shape burns oracle time producing captures the
harness rejects on arrival — the exact cost T488 correctly avoids in group B.

**What should change.** Add a third bullet to §1.4(b) — *"and the e2e step definitions set
`runningBalance=true` on every journal-entry read-back (`JournalEntriesStepDef.java:366`), which
`admit.go`/`oraclederived.go` refuse"* — and repeat it in §8 item 2 as a standing constraint on the follow-up.
§4.3's read-back URL (`GET /journalentries?transactionId=<txn>&limit=50`) is already correct and needs no
change.

---

### F-5 — MINOR — "1,427 journal-entry lines across 56 feature files" conflates two different searches

**T488's claim.** §1.1, §8 item 2, §9 and handoff §2. **My derivation:** both cited commands reproduce
**exactly**, and they are not the same search:

```
grep -ri  "journal"             --include=*.feature .                          → 1427   (lines)
grep -ril "journal\|accounting" --include=*.feature fineract-e2e-tests-runner  →   56   (files)
grep -ril "journal"             --include=*.feature .                          →   48   (files)
```

The 1,427 lines live in **48** files, not 56; the 56 counts files mentioning `journal` **or** `accounting`,
over a narrower root. **Credit where due:** T488 cited the literal commands in a `[VERIFIED: …]` bracket,
which is the only reason this was catchable — the failure is in the prose that summarises them, not in the
evidence. **What should change:** state it as *"1,427 journal lines across 48 feature files; 56 files mention
journal or accounting."* Nothing downstream depends on the figure.

### F-6 — MINOR — the `AccountingScenarioIntegrationTest` split is off by one in both places it appears

**T488's claim.** §1.4(a): *"5 of its 11 tests on savings, fixed-deposit and recurring-deposit accounting
flows (`:284`, `:377`, `:475`, `:548`, plus `:1238` on shares)"*; §1.3 row 3: *"5 loan tests mined; 5
savings/deposit tests rejected; 1 share-account test deferred."*

**My derivation.** The file has **11** `@Test` methods (T488's count of 11 is right). The split is
**6 loan / 4 savings-deposit / 1 shares**: loan at `:150, :689, :813, :890, :984, :1114`; savings/deposit at
`:284, :377, :475, :548`; shares at `:1238`. Every cited line resolves to the method T488 names. The prose
counts the shares test inside the deposit figure in §1.4(a), and §1.3's 5/5/1 totals 11 by absorbing a loan
test into the deposit column. **What should change:** correct to 6/4/1. Changes nothing that gets captured.

### F-7 — MINOR — the `glclosures` empty search is under-scoped as cited, but the conclusion survives a wider one

**T488's claim.** §1.2: *"**ZERO HITS.** No test in the tree exercises `POST/GET/DELETE /glclosures`"*;
§9 cites `grep -rn "glclosures" --include=*.java integration-tests fineract-provider/src/test → no output`.

**My derivation.** That search covers two directories and one extension. I widened it to the **whole tree,
all extensions**: `grep -ril glclosure .`. The path string `glclosures` appears only in main source
(`GLClosuresApiResource.java:58,88,103,106`; `CommandWrapperBuilder.java:1749,1757,1765`) and `apiLive.htm`.
**The conclusion holds — no test anywhere exercises the `/glclosures` path — and I state it as a claim about
that search.** However, `GLClosure` the *domain class* does appear in three test files as a Mockito mock
(`CreateJournalEntriesForChargeOffLoanTest.java:31,65`; `CreateJournalEntriesForTransferLoanTest.java:33,72`;
`AccountingProcessorHelperTest.java:32,59`), so "zero hits" is true of the string searched, not of the
subject. **What should change:** record the wider search, so the empty result rests on a search that could
have found something. **This is the search the brief flagged as easiest to get wrong; I could not falsify
it, and I widened it enough to say I confirmed it.**

### F-8 — MINOR — "every read-back URL" is true of the hand-built URLs; there is a fourth read path

**T488's claim.** §1.4(b): *"Every read-back URL in `JournalEntryHelper` hard-codes `tenantIdentifier=default`
(`:140`, `:163`, `:185`)."*

**My derivation — CONFIRMED, all three lines opened.** `:139-141`, `:163-164` and `:185-186` each append
`"&tenantIdentifier=default"`. The consequence T488 draws is right and independently corroborated:
`.softhouse/reference-oracle.md:91` (tenant `default` → `Asia/Kolkata`), `:99` and `:168` (`HALF_EVEN`
negative control; `fineract_default` holds **0 GL accounts, 0 journal entries, 0 loans**). The refinement:
`JournalEntryHelper.java:196-200` (`retrieveJournalEntryByTransactionId`) reads back through the generated
client and builds **no** URL, so "every read-back **path**" would be false while "every read-back **URL**" is
true. Immaterial to the recipe, which sends the tenant header explicitly.

### F-9 — MINOR — §10's "no expected status code anywhere" over-reaches its own taxonomy

`403` and three `error.msg.glaccount.glcode.invalid.delete.*` strings appear in TDG-A1/A2/A3, correctly
labelled `TEST-ASSERTION` and correctly attributed — I verified each against
`GLAccountIntegrationTest.java:84-85, :104-105, :122-123`. §8 item 7 states the position accurately
("No status code and no message string is asserted anywhere in this document **as an expected value**").
§10 and the handoff drop the qualifier. **What should change:** align §10 and the handoff to §8 item 7's
wording, so a capture operator cannot read TDG-A1's `403` as a target.

### F-10 — MINOR — TDG-00 item 1 asserts a checkout fact and labels it a running-image fact

*"Fineract commit of the running image's source — `git -C <checkout> log -1 --format=%H`."* A `git log` in a
checkout is evidence about the checkout, not about what a container was built from. Item 12 (image digest)
partly mitigates, but nothing ties the digest to the commit. **What should change:** relabel item 1
"pinned checkout commit", and add an explicit `[UNVERIFIED: the running image is built from this commit]`
unless the fire can produce build provenance.

### F-11 — MINOR — `cap11.sh` self-identifies as `cap10.sh`

Every header line, the `usage:` message (`:52`) and the refusal message (`:53`) in
`.softhouse/capture/t352-a2-next-tranche/cap11.sh` say `cap10.sh`. Harmless, but a fire following §4.2 will
see a usage string naming a different script. Worth one parenthetical in §4.2.

### F-12 — MINOR — the SQL running-balance columns §4.3 records are safe, and the plan should say why

§4.3 instructs recording `office_running_balance`, `organization_running_balance` and
`is_running_balance_calculated` from `capsql.sh` "as evidence … never promoted into a vector". **I verified
this is safe**: the capture scanner keys on the **camelCase response** names
(`organizationRunningBalance, officeRunningBalance, runningBalanceComputed` —
`oracle-derived-columns.json` → `capture_rule.forbidden_response_field_names`), while `forbidden_cells`
constrains **vector cells**, not artefact bytes. A `psql` artefact emitting snake_case headers trips neither.
The plan does not say this, and a careful fire could reasonably fear the opposite and drop the most useful
SQL columns in the plan. **What should change:** one sentence recording the distinction.

### F-13 — MINOR (a strengthening, not a defect) — the Fineract ordering test TDG-R4 mines is near-vacuous

`JournalEntryReversalOrderingIntegrationTest.verifyJournalEntriesOrdering` (`:113-155`) contains exactly one
assertion, at `:140`, reachable only when transaction date **and** created date are equal; the other four
branches (`:130-131`, `:136-137`, `:142-145`, `:146-149`) are empty comment blocks. Its stated rule is
transaction date **ascending**, created date **ascending**, id **descending** (`:124-127`) — which is what
T488's §4.6 says, read correctly. TDG-R4 already plans to **capture** the ordering rather than trust it,
which is the right handling; the plan should simply say that the Fineract test is not evidence of the rule
it documents, so no later fire treats it as one.

---

## D. Item-by-item answers to the brief

### 1. Synthesised values — **swept all 27 cases (29 ids); none found**

See §B. **No row of the plan states a value the worker could not have observed, in any expectation position.**
The `SOURCE-DERIVED HYPOTHESIS` rows — the ones most at risk of hardening into expectations — name shapes
and branches, never amounts, and every one states a refutation condition. This is the strongest part of the
document and the claim in §10 is, on the substance, true.

### 2. The de-scoping decision — **both de-scopes are CORRECT, and better-founded than T488 states**

I counted the `in_graded_domain: false` entries myself: **6 of 14**, namely `ledger.slot.resolution`,
`ledger.transfers.suspense`, `ledger.charge.off`, `ledger.multi.currency.entry`, `ledger.reversal.entry`,
`ledger.running.balance`. T488's set is right.

**`ledger.multi.currency.entry` — genuinely unreachable at this seam. Re-derived from source at the pin, not
inherited.** `SingleDebitOrCreditEntryCommand.java:33-35` declares exactly `glAccountId`, `amount`,
`comments` (plus `parametersPassedInRequest` at `:37`); `JournalEntryCommand.java:40` carries
`currencyCode` as a single scalar on the enclosing command. **An entry whose legs differ in currency is not
expressible at `ledger_rest_posting`.** A second, independent refusal T488 does not cite:
`admit.go:165-172` rejects any vector with `request.currency.code != "MNT"` or
`request.currency.minor_unit_digits != 2` (G-07). So such a vector is refused twice over. **Correctly
dropped.** One precision note: the *database* row carries a per-entry `currency_code`, so the shape is
expressible in the schema even though not at the seam; reaching it would need a non-REST path, which is well
outside this context. T488's re-scope to X1 (non-2dp currencies) / X2 (residue at attested parameters) is a
better use of the slot.

**`ledger.running.balance` — correctly de-scoped, but blocker (iii) is overstated and under-tagged.**
- (i) **G-12 open** — confirmed; `admit.go:128-149` refuses a vector whose `_note` claims to grade either
  column.
- (ii) **No schema field** — confirmed at `admit.go:130-133` ("The schema has no field for them, see
  `PostedEntry`'s doc comment") and `conformance_test.go:240-241`.
- (iii) **"HTTP 500 on PostgreSQL"** — I verified the *source basis*:
  `GLAccountReadPlatformServiceImpl.java:129` and `:131` emit `group by account_id desc, id` and
  `group by t2.account_id desc`, which is MySQL-only syntax that PostgreSQL rejects. **The status code is a
  runtime claim.** T488 carries it by quoting `capabilities-ledger.json` and does not tag it
  `[UNVERIFIED: runtime, no instance reachable]`, though §8 tags nine other things. It is also
  **imprecise as a blocker for the capability**: the *other* running-balance reader,
  `GET /journalentries?runningBalance=true`, demonstrably **does** work on PostgreSQL — it was captured by
  T429 (`oraclederived_test.go:22`; `oraclederived.go:240-243`). So (iii) is true of the `/glaccounts`
  reader, not of the capability.
- **A fourth blocker, stronger than any of the three, that T488 does not name:** `admit.go:141` →
  `CaptureRuleReasons` refuses a vector whose *cited capture bytes* carry the running-balance field names at
  all. The de-scope is right; its best argument is missing.

**Is a third capability unreachable, or is a reachable one planned for wastefully?** No. Working from each
row's own evidence text: `ledger.reversal.entry` needs the **write** path (a before/after DB diff — TDG-R1
does exactly that); `ledger.charge.off` needs a **new product** with the charge-off mappings (a throwaway
supplies one); `ledger.transfers.suspense` needs an **account/client transfer** and a **second office** (ditto);
`ledger.slot.resolution` needs the **cash family** and the **payment-type precedence chain** (ditto). All four
are reachable on a throwaway, and all four are planned. **No capture is wrongly dropped and none is wrongly
planned.** With F-2's caveat that group C's *rationale* needs re-anchoring to main source.

### 3. The mining record and its empty searches — **re-measured; three of four reproduce exactly**

| Claim | T488 | Mine | Verdict |
|---|---|---|---|
| test-Java LOC / files | 320,601 / 1,254 | **320,601 / 1,254** | **AGREE, exact** |
| `.feature` files / LOC | 158 / 200,763 | **158 / 200,763** | **AGREE, exact** |
| journal lines / files in features | 1,427 / **56** | 1,427 / **48** | lines agree exactly; file count conflates two searches → **F-5** |
| zero `glclosures` tests | zero | **zero for the path, whole tree** | **AGREE**, on a wider search than cited → **F-7** |
| one `POST /journalentries` call site | one | **three** in `integration-tests`, five in the corpus | **DISAGREE** → **F-1** |
| `integration-tests` 533 / 192,234 | ✓ | **533 / 192,234** | AGREE, exact |
| 30 files / 33,910 LOC use `JournalEntryHelper` | ✓ | **30 / 33,910** | AGREE, exact |
| `fineract-accounting/src/test` = 1 file / 88 LOC | ✓ | **1 / 88** | AGREE, exact |
| sixteen float-widening sites | 16, listed | **16**, same lines | AGREE, exact |

`CLAUDE.md` reconciliation: `320,601` matches "~321k test LOC". Separately, `.softhouse/program.json` /
`CLAUDE.md` record **5,317** main files; I measure **5,331** (`544,996` LOC, consistent with "~544k"). That
is a program-inventory drift, not a T488 defect, and I flag it only so it is on the record.

### 4. The three shape-changing findings

- **(a) "never post a manual JE for its own sake, and never reverse one."** The first half is **REFUTED** —
  see F-1. The second half is **CONFIRMED** from my own whole-tree search.
- **(b) "every read-back URL hard-codes `tenantIdentifier=default`."** **CONFIRMED** — all three lines
  opened; the tenant-`default` consequence corroborated at `.softhouse/reference-oracle.md:91,99,168`. One
  refinement in F-8. **A stronger sibling hazard in the same corpus is missing** — F-4.
- **(c) ~7,500 LOC / 97 deposit tests rejected on LEGAL grounds.** The **measurement** reproduces
  (7,755 LOC / 98 `@Test` across 7 files). The **consequence** is right but the **grounds are wrong**: this
  is a scope block read into an activation gate, and the "no later agent may re-litigate" clause is the
  harm. **F-3.** Answering the brief's question directly: *has a scope block been read into an activation
  gate?* **Yes** — and it should be re-labelled PRODUCT and the finality clause struck, while keeping the
  exclusion.

### 5. Tenant parameters — **pinned correctly, and the precision trap is avoided**

§5 pins `(19, HALF_UP)` / ordinal 4 / MNT-496-2 / `Asia/Ulaanbaatar` / PostgreSQL / tenant `t488` for
**every** capture, and `TDG-00` fails closed on each (items 4–10). I verified the underlying facts myself:
`MoneyHelper.java:35` (`public static final int PRECISION = 19`) and `:91-93`
(`new MathContext(PRECISION, getRoundingMode())`) — note the real path is
`fineract-core/.../organisation/monetary/**domain**/MoneyHelper.java`. The throwaway template it points at is
real and correctly parameterised: `.softhouse/capture/t327-closure-accepting-side/throwaway/` exists with
`docker-compose.t327.yml:91` `FINERACT_DEFAULT_TENANTDB_TIMEZONE: Asia/Ulaanbaatar`, `:92`
`FINERACT_CONFIG_ROUNDING_MODE: "4"`, `:82` `"8444:8443"`, plus `guard-throwaway-isolation.sh` and `down.sh`.

**Does it treat a non-production-precision capture as reusable? No — and this is the plan's second-best
judgement.** `TDG-X2` **re-takes** T352's sub-minor-unit residue observation rather than citing it, on the
explicit ground that it was not taken under an attested `(19, HALF_UP)` tenant, and adds a genuinely new arm
(whether the oracle's **own arithmetic** ever generates a residue, versus T352 having **supplied** the third
decimal — a distinction `capabilities-ledger.json` itself insists on). That is exactly the discipline
`CLAUDE.md` demands of the `C-00`/`D-*` corpus, applied to a capture nobody had yet applied it to.
`TDG-00`'s attestation sidecar also correctly compensates for `PIN-ledger.json` carrying no tenant field —
I confirmed it does not.

### 6. The instrument correction — **CONFIRMED, both halves, from the scripts**

- `cap8.sh:82-86` — `curl -sk -X "$METHOD" "$B$RPATH" -H "$A" -H "$T" -H "$CT" --data-binary @… ` — **no
  `Idempotency-Key`**. Its `.http` record (`:114-128`) writes no `Idempotency-Key` line either. **Must not be
  used for a POST**, exactly as T488 says. The consequence T488 draws is also verified from Fineract:
  `IdempotencyKeyResolver.java:36` falls back to `idempotencyKeyGenerator::create`, and
  `IdempotencyKeyGenerator.java:27-29` returns `UUID.randomUUID().toString()` — an unattributable write.
- `cap11.sh:53` refuses without a key and `:79,82` send it; `:115` records it. **Correct.** The header name
  is also verified: `application.properties:179` and `:857`
  (`fineract.idempotency-key-header-name=${FINERACT_IDEMPOTENCY_KEY_HEADER_NAME:Idempotency-Key}`), read at
  `IdempotencyStoreFilter.java:72`.
- Cosmetic: F-11.

### 7. The self-caught error — **the correction is RIGHT**, and the follow-through it prompted

**Verified independently.** `acc_gl_account` is created once at
`0001_initial_schema.xml:49-75` (I read line 49 `<createTable tableName="acc_gl_account">` and line 75
`</createTable>`) with eleven columns and **no deleted marker**. `GLAccount.java:43-84` — in **`fineract-core`**
— declares `disabled` (`:67-68`) and no deleted field. By contrast `acc_gl_closure` **does** carry
`is_deleted` (`GLClosure.java:50-51`), which is exactly the neighbouring fact T488 says it wrongly
generalised from. The correction is right, and its downgrade of "hard delete" to a
`SOURCE-DERIVED HYPOTHESIS` that TDG-A4's SQL arm measures is the correct handling — the JPA call site
(`GLAccountWritePlatformServiceJpaRepositoryImpl.java:212`, `glAccountRepository.delete(glAccount)`) shows
intent, not the row's fate.

**Taking the incident as a lead, as instructed.** A citation sweep proves a line **exists**, not that it
**says** what it is cited for — so I checked for **support**.

> **Sample size: 67 claim-level `FILE:LINE` citations opened and read for support** (not resolution), drawn
> from every section that carries citations and covering **every** citation in §1.4(f), §1.4(c), §3 groups
> A/C/T/X, §5, §6 and §9, plus all of §1.4(b), §1.4(d) and §8 item 4.
> **Supported: 66. Not supported: 1 (F-2).**
> **Citation support rate: 66/67 = 98.5%.**

The one failure is TDG-C3's, and its *conclusion* is nonetheless true on main source. Notably, the six
numbered source claims of §1.4(f) — the plan's flagship, and where a wrong line number would be most costly —
are **all six supported**, line by line: `:343`, `:345-346`, `:349-351`, `:352-355`, `:382`, `:383`,
`:385/:405-406`, `:391-399`, `:409-413`, `:415-419`, `:423`, `:424`, plus `JournalEntryRepository.java:30`'s
JPQL quoted verbatim and correctly. So did the four-command POST surface
(`JournalEntriesApiResource.java:203-220`, `:231-240`), the `G-06` null-payment-type finding
(`AccountingProcessorHelper.java:1199-1206` — the `FUND_SOURCE` lookup with no null guard), the sixteen float
sites, and every `error.msg.*` / `403` / method-name citation in groups A, C, T and S.

**The residual risk the incident points at is not mis-citation — it is universal claims made over unread
files.** F-1 is exactly that shape, and it is the same failure as the `is_deleted` inference in a different
costume: a general statement inferred rather than measured. The sweep could not catch it, because every
citation in it resolves.

---

## E. Verdict

# ACCEPT WITH CONDITIONS

The plan is careful, honestly bounded, and does the one thing that mattered most: **it states no expected
value, and I could not construct a reading in which any of its 29 ids hands a capture fire a number nothing
produced.** Its taxonomy (`TEST-ASSERTION` / `SOURCE-DERIVED HYPOTHESIS` / `TO_BE_CAPTURED`), its refutation
conditions, its refusal to reuse T352's non-attested observation, its throwaway routing, and its instrument
correction are all correct and independently verified. Both de-scopes are right. Its self-disclosed error is
real, correctly fixed, and correctly downgraded.

**Findings: 4 MAJOR, 9 MINOR. Citation support rate 66/67 = 98.5% on a 67-citation sample.**

**Conditions (all are edits to the document; none requires an oracle):**

1. **F-1** — correct the "exactly one POST call site" claim and the "never post a manual JE for its own
   sake" finding; add the two `externalAssetOwner` manual-JE cases mined from
   `InitiateExternalAssetOwnerTransferTest.java:1315` and `:1349`.
2. **F-2** — re-cite TDG-C3 to `AccrualBasedAccountingProcessorForLoan.java:909-928`; record that
   `CreateJournalEntriesForChargeOffLoanTest` predates the July 2026 rework of the path it mocks and verifies
   an overload the charge-off path no longer calls; re-anchor group C's hypotheses to main source.
3. **F-3** — re-label the savings/deposit exclusion **PRODUCT**, not LEGAL; keep the exclusion; strike "on
   grounds no later agent may re-litigate"; record that porting deposit code remains in Tier B scope per
   `CLAUDE.md`.
4. **F-4** — add the `runningBalance=true` copy-hazard (`JournalEntriesStepDef.java:366`) to §1.4(b) and to
   §8 item 2, citing `admit.go:141` / `oraclederived.go:230-243`.
5. **F-5, F-6, F-7** — correct the three mining-record numbers/scopes (48 vs 56; 6/4/1; the widened
   `glclosures` search).
6. **F-9** — align §10 and the handoff to §8 item 7's accurate wording, so TDG-A1's `403` cannot be read as
   a target.
7. **F-10, F-12** — relabel `TDG-00` item 1 as a checkout fact with an `[UNVERIFIED]` on image provenance;
   add the one sentence recording that snake_case SQL columns do not trip the camelCase capture scanner.

F-8, F-11 and F-13 are recorded for accuracy and need no action before execution.

## F. Is this plan safe to hand to an oracle-reaching fire to execute unattended?

**Yes — with conditions 1–4 applied first, and they are text edits that need no oracle.**

The reasoning, stated as the risk it is:

- **It cannot forge a vector.** Nothing in it states an expectation; §0's instruction to the capture fire
  ("if you are about to write a number you did not read out of a `curl` response body or a `psql` result set
  taken in that same run, stop") and §7's "a half-finished capture is evidence; a completed capture with a
  guessed value is a forgery" are exactly the right standing orders. `TDG-00` fails closed and treats an
  unreachable oracle as exit 2, never a PASS.
- **It cannot damage the standing oracle.** Every case is routed to a throwaway; `PROBES.tsv` is unchanged;
  the closure (R5) and the GL-account deletes (A1–A4) — the two genuinely irreversible acts — are explicitly
  barred from `gerege`, and §4.12(5) attaches the attribution obligation the moment anything moves to
  STANDING. The rig template it names exists, is isolated by `guard-throwaway-isolation.sh`, and is already
  seeded at `Asia/Ulaanbaatar` / rounding ordinal 4.
- **It cannot produce an unattributable write.** §4.2 routes every POST through `cap11.sh`, which refuses
  without an `Idempotency-Key`, with a one-key-per-request naming convention.
- **Its residual failure modes are omission and mis-rationale, not fabrication.** Without condition 1 the
  fire leaves two cheap, in-scope refusal/read-back cases on the table. Without condition 4 the fire's own
  named follow-up can generate captures `admit.go` refuses on arrival. Without condition 2 group C's
  captures are still *correct* — the recipe asks the right question — but their stated rationale points at a
  stale mock. Without condition 3 a later worker inherits a wrongly-absolute scope block.
- **The ordering is sound for a short window.** Ranks 0–2 (attestation, reversal, GL-account refusals) share
  one throwaway and cover the plan's highest-value case (R1, the only capture that can refute a
  source-derived hypothesis about a `CLAUDE.md` non-negotiable) plus the cheapest block. If the window closes
  after R1 arms `a`–`e`, the instruction to commit the before-state is right: it is the artefact that cannot
  be reconstructed once the instance is destroyed.

**What I achieved, per claim, since being unable to falsify is not confirming.** I **confirmed** by
independent re-derivation: the pin; nine of the ten mining measurements; the reversal write path's six
source claims; the four-command POST surface; the `tenantIdentifier=default` defect; the `acc_gl_account`
no-deleted-marker correction; the multi-currency seam impossibility; the MySQL-only running-balance SQL; both
capture-instrument facts; the tenant-parameter pins; the rig template's existence and parameters. I
**refuted** T488's manual-JE call-site claim and its "never for its own sake" finding, and TDG-C3's citation.
I was **unable to falsify, and did not confirm**: any runtime behaviour whatsoever — no Fineract, no
PostgreSQL, no Docker daemon in this sandbox — which includes the "HTTP 500 on PostgreSQL" status code, the
predicted refusal branches, and throwaway bring-up cost. Those are precisely what the plan exists to have
measured.
