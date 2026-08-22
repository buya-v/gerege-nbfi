# Slice A2 — capture plan, mined from Fineract's own test corpus

> **DEFECTS FOUND BY INDEPENDENT REVIEW — read `DEFECTS-FOUND-BY-REVIEW.md` in this directory before
> citing anything under `out/`.** The corpus is real (24 of 27 recipes re-issue byte-identically), but the
> **10 `attempt1-*` recipes are provably false** and must not be cited as reproducible; `cap.sh`'s
> transport-failure handler **cannot fire**; and `manifest.py verify` does **not** cover this file.

Worker **A2-3**, local fire 2026-08-21. Scope: `glaccount`, `producttoaccountmapping`,
`financialactivityaccount` in `fineract-accounting`, plus
`fineract-provider/.../accounting/productaccountmapping`. Source: pinned checkout
`/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

Fineract's test corpus is a **seam to mine**, not code to port. This document says which
behaviours are worth a vector, which are already decided by the DDL and therefore need
none, and which the corpus does not cover at all — that last group is where a port is most
likely to go silently wrong, and it is where this fire spent its budget.

**Nothing in this file is promoted.** No file was written to `.softhouse/vectors/`.

---

## 1. What the corpus actually covers

### 1.1 `fineract-accounting/src/test` — one file, one test

`fineract-accounting/src/test/java/org/apache/fineract/accounting/glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImplTest.java`

| test | behaviour |
|---|---|
| `testDeleteGLAccountSuccessWithNoDependencies` | Mockito; delete with no children / no journal entries / no product mappings returns `resourceId == id` |

The module has **no** unit test for create, update, or `hierarchy` computation. The single
unit test is the *success* branch only.

### 1.2 Integration tests on the slice

`integration-tests/src/test/java/org/apache/fineract/integrationtests/accounting/GLAccountIntegrationTest.java`

| test | behaviour |
|---|---|
| `createUpdateDeleteGLAccountTest` | POST → GET round trip, then PUT changing description/name/glCode/type/manualEntriesAllowed/usage, then DELETE |
| `testDeleteGLAccountWhileThereAreChildren` | 403 `error.msg.glaccount.glcode.invalid.delete.has.children` |
| `testDeleteGLAccountWhileMappedToProduct` | 403 `error.msg.glaccount.glcode.invalid.delete.product.mapping` |
| `testDeleteGLAccountWhileThereIsJournalEntry` | 403 `error.msg.glaccount.glcode.invalid.delete.transactions.logged` |

`integration-tests/src/test/java/org/apache/fineract/integrationtests/FinancialActivityAccountsTest.java`
— one method, `testFinancialActivityAccounts`, covering create / update / unknown activity id
400 / duplicate activity 403 / activity-to-account-type mismatch 403 / delete then 404.

`integration-tests/src/test/java/org/apache/fineract/integrationtests/LoanProductChargeOffReasonMappingsTest.java`
and `LoanProductTest` nested classes `WriteOffReasonsToExpenseMappings`,
`IncomeCapitalizationTest`, `BuyDownFeeTest` — the newer `financial_account_type` keys and
the **delete-then-recreate** semantics of mapping update.

`fineract-e2e-tests-runner/src/test/resources/features/WorkingCapitalLoanProductAdvancedAccounting.feature`
— 13 scenarios over `paymentChannelToFundSourceMappings`, `feeToIncomeAccountMappings`,
`penaltyToIncomeAccountMappings`, `chargeOffReasonToExpenseAccountMappings`,
`writeOffReasonsToExpenseMappings`, including scenario 11, **duplicate `paymentTypeId`
rejected** — but note §4.1 below: that guard is on the *working-capital* product path, and
the plain loan-product path does **not** have it. Observed, not inferred.

Journal-entry-side consumers (they exercise mapping *resolution*, not mapping CRUD):
`CreateJournalEntriesForChargeOffLoanTest`, `CreateJournalEntriesForTransferLoanTest`,
`AccountingProcessorHelperTest`,
`AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoanTest`,
`fineract-investor/.../AccountingServiceImplTest`.

Useful seeded fixtures worth reusing rather than reinventing:
`fineract-e2e-tests-runner/.../GLGlobalInitializerStep.java` (24 GL accounts with fixed
gl_codes) and `FinancialActivityMappingGlobalInitializerStep.java` (pins
`ASSET_TRANSFER=100`, `LIABILITY_TRANSFER=200`).

---

## 2. Behaviours already forced by the schema — **no vector needed**

Read from the running PostgreSQL 18.3 instance (`\d`), not from the changelog, so this
reflects what is actually deployed. Base DDL:
`fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml`.

| forced by | consequence |
|---|---|
| `acc_gl_account.name NOT NULL`, `gl_code NOT NULL`, `disabled NOT NULL`, `manual_journal_entries_allowed NOT NULL`, `account_usage NOT NULL`, `classification_enum NOT NULL` | absence cannot be represented; a Go port on the same schema gets this free |
| `acc_gl_account_gl_code_key` UNIQUE on `gl_code` | global gl_code uniqueness |
| `fk_acc_0000000001` self-FK `parent_id → acc_gl_account(id)` RESTRICT | a parent cannot be deleted out from under a child |
| `acc_gl_financial_activity_account.financial_activity_type NOT NULL UNIQUE` | at most one GL account per financial activity, globally |
| `FK_office_mapping_acc_gl_account` RESTRICT | a GL account referenced by a financial activity cannot be deleted |
| `acc_product_mapping` FKs `gl_account_id`, `charge_id`, `payment_type`, and the three `m_code_value` FKs, all RESTRICT | referenced rows cannot vanish |
| `acc_gl_journal_entry.amount numeric(19,6)` | **not a float** — observed via `information_schema`, recorded in `out/A2-150-db-final-state.txt` |

A vector asserting any of the above tests PostgreSQL, not the port. Skip them.

**But note the messages are still behaviour.** `out/A2-bad-040-dup-glcode.json` shows the
oracle returning the raw PostgreSQL text — `duplicate key value violates unique constraint
"acc_gl_account_gl_code_key"` — straight through the API. Any port that reproduces the
*constraint* but not the *string* diverges on the wire. That is a contract question for
DEC-n, not something to paper over.

---

## 3. Behaviours NOT forced by the schema — these need vectors

Ranked by how likely a reimplementation is to get them wrong.

| # | behaviour | captured this fire? |
|---|---|---|
| 1 | `hierarchy` string computation — **untested anywhere in the Fineract repo** | **YES** — `out/A2-019-db-glaccount-rows.txt`, §4.2 |
| 2 | Payment-type-specific vs generic fund-source resolution | **YES** — `out/A2-087/088`, §4.3 |
| 3 | Resolution MISS when the key is absent entirely | **YES** — `out/A2-092-chargeoff-loan1-unmapped.json`, §4.4 |
| 4 | Duplicate `(product, product_type, financial_account_type, payment_type)` — the JPA `financial_action` unique constraint is **absent from the DDL** | **YES** — §4.1, and it is worse than expected |
| 5 | The three GL-account delete guards and their **precedence** | **YES** — `out/A2-120..A2-124`, §4.5 |
| 6 | `classification_enum ∈ 1..5`, `account_usage ∈ 1..2` — no check constraints | **YES** — `out/A2-bad-046/047/048` |
| 7 | `financial_activity_type ∈ {100,200,101,102,300,103,201}` and the enumeration **order** in the error message | **YES** — `out/A2-fin-104-unknown-activity.json` |
| 8 | `FinancialActivity → GLAccountType` compatibility | **YES** — `out/A2-fin-103-wrong-account-type.json` |
| 9 | GL-account-type checking on product mapping (which types are accepted per key) | **YES** — `out/A2-prod-063-map-wrong-type.json` |
| 10 | Which mapping parameters are mandatory per accounting rule (CASH vs ACCRUAL_PERIODIC) | **YES** — `out/A2-prod-064`, `out/A2-prod-068` |
| 11 | `usage` / `manualEntriesAllowed` update quirk | **YES** — §4.6 |
| 12 | `gl_code` effective max length 45 (DDL) vs entity's declared 100 | **YES** — `out/A2-bad-051-glcode-too-long.json` |
| 13 | `financial_account_type` value collisions between `CashAccountsForLoan` and `AccrualAccountsForLoan` (7/8/9, 22, 24, 25 mean different things) disambiguated only by the product's accounting rule | **PARTIAL** — both a CASH (product 22/23) and an ACCRUAL (product 28) mapping set are captured in `out/A2-072`; the *collision* keys 22/24/25 are not exercised |
| 14 | Mapping replacement (delete-then-recreate) on product update | **NO** — see §5 |
| 15 | `write_off_reason_id` has **no FK** — referential integrity is app-only | **NO** — see §5 |
| 16 | "must be an Expense GL account" for charge-off / write-off mappings | **NO** — see §5 |

---

## 4. What the oracle actually said

Every claim below cites a file under `out/`. Each file is one HTTP exchange or one SQL
result, recorded verbatim, hashed in `MANIFEST.sha256`.

### 4.1 A duplicate mapping is accepted at create and detonates at resolution

`req/prod-067-duplicate-channel.json` sends **two** `paymentChannelToFundSourceMappings`
entries for the same `paymentTypeId`. The oracle returned **HTTP 200** (`out/A2-prod-067-duplicate-channel.json`),
and `out/A2-150-db-final-state.txt` shows both rows persisted:

```
product_id | product_type | financial_account_type | payment_type | n | gl_account_ids
        27 |            1 |                      1 |            1 | 2 | {16,2}
```

Disbursing on that product then fails **permanently** (`out/A2-086-disburse-loan3-dupchannel.json`):

```
HTTP 403  error.msg.data.integrity.issue
"More than one result was returned from Query.getSingleResult()"
```

The `@UniqueConstraint(name = "financial_action")` on `ProductToGLAccountMapping` exists only
as a JPA annotation; `grep financial_action` over the changelogs returns zero hits, and `\d
acc_product_mapping` confirms no unique constraint is deployed. So the oracle will
cheerfully create a product that can never disburse. **This is a bug worth carrying
forward deliberately, not reproducing by accident** — a port decision, and one the frozen
contract should speak to.

### 4.2 The `hierarchy` string omits the root's own id

Not exposed by the REST API at all — `/glaccounts/{id}` returns `nameDecorated`, never
`hierarchy`. Only the DB shows it (`out/A2-019-db-glaccount-rows.txt`):

| id | parent_id | hierarchy | nameDecorated |
|---|---|---|---|
| 1 | *(none)* | `.` | `Assets` |
| 2 | 1 | `.2.` | `....Fund Source` |
| 3 | 1 | `.3.` | — |
| 4 | 3 | `.3.4.` | `........Loan Portfolio` |
| 21 | 1 | `.21.` | — |

A child of the root gets `.2.`, **not** `.1.2.`. The hierarchy is therefore *not* a full
path to the root — the top-level ancestor's id is absent, because the root's own hierarchy
is the bare `.` and children append `own_id + "."` to the parent's string. `nameDecorated`
prefixes 4 dots per level of depth: 0 at the root, 4 at depth 2, 8 at depth 3.

Fineract has **no test anywhere** for this. It is the single highest-value thing this fire
captured, because a port would naturally write `.1.2.` and nothing in the corpus would
catch it.

### 4.3 Resolution: the payment-type-specific row wins; absence falls back to generic

Product 22 carries both a generic `FUND_SOURCE` row (`payment_type` NULL → GL 2) and an
override (`payment_type` 1 → GL 16). Two disbursements of the same amount:

| capture | paymentTypeId | credited |
|---|---|---|
| `out/A2-087-journalentries-loan1.json` | 1 (override exists) | **GL 16** `10300` Fund Source Alternate |
| `out/A2-088-journalentries-loan2.json` | 2 (no override) | **GL 2** `10100` Fund Source |

Both debit GL 4 `10201` Loan Portfolio. Amount `1200000.000000` in both, MNT.

### 4.4 Resolution MISS — key absent entirely

Charging off loan 1, whose product 22 has no `CHARGE_OFF_EXPENSE` (=16) row at all
(`out/A2-092-chargeoff-loan1-unmapped.json`):

```
HTTP 404  error.msg.productToAccountMapping.not.found
"Mapping for product of type LOAN with Id 22 does not exist for an account of type CHARGE OFF EXPENSE"
args: ["LOAN", 22, "CHARGE OFF EXPENSE"]
```

Note the account-type name is rendered **space-separated uppercase** — the enum constant
with `_` replaced by a space. A port must reproduce that rendering, not the constant name.

### 4.5 Delete-guard precedence, and a guard that does not exist

| capture | target | fires |
|---|---|---|
| `out/A2-120-delete-has-children.json` | GL 3, child only | `error.msg.glaccount.glcode.invalid.delete.has.children` |
| `out/A2-121-delete-product-mapped.json` | GL 13, mapping only | `error.msg.glaccount.glcode.invalid.delete.product.mapping` |
| `out/A2-122-delete-three-guards.json` | GL 2 — mapped **and** has journal entries **and** is a financial-activity target | `…delete.transactions.logged` — **the transactions guard wins** |
| `out/A2-123-delete-finactivity-mapped.json` | GL 6 — mapped **and** financial-activity target | `…delete.product.mapping` |
| `out/A2-124-delete-clean-success.json` | GL 21 — financial-activity target **only** | **no application guard at all**; falls through to the raw PostgreSQL FK: `violates RESTRICT setting of foreign key constraint "FK_office_mapping_acc_gl_account"` |
| `out/A2-134-delete-clean-success.json` | GL 23, genuinely clean | **HTTP 200** `{"resourceId":23}`; subsequent GET → 404 |

A2-124 is the finding: Fineract has three application-level delete guards (children,
product mapping, journal entries) and **none for financial-activity references**. That case
escapes to the database and leaks the constraint name to the caller.

### 4.6 `usage` and `manualEntriesAllowed` are updatable but do not count as parameters

| capture | body | result |
|---|---|---|
| `out/A2-141-update-usage-only.json` | `{"usage":2}` | **400** "No parameters passed for update." |
| `out/A2-142-update-manual-only.json` | `{"manualEntriesAllowed":false}` | **400** same |
| `out/A2-131-update-usage-with-name.json` | `{"name":…, "usage":2}` | **200**, `changes` includes `usage: 2` |
| `out/A2-132-update-manual-with-name.json` | `{"name":…, "manualEntriesAllowed":false}` | **200**, `changes` includes `manualEntriesAllowed: false` |

A2-141/142 were run against a **fresh account with no children, no mapping and no journal
entries** precisely to rule out the alternative explanation that the target was special —
see the hypothesis note in `mkreq6.py`. Mechanism, confirmed at source
(`fineract-core/.../glaccount/command/GLAccountCommand.java`):

```java
baseDataValidator.reset().anyOfNotNull(this.name, this.glCode, this.parentId,
                                       this.type, this.description, this.disabled);
```

`usage`, `manualEntriesAllowed` and `tagId` are **omitted from that list** while still being
applied by the update. So the "is anything present?" check and the "what gets applied?" set
are different sets. A port that uses one set for both will diverge in both directions.

### 4.7 Guards the oracle does **not** have (each an accepted request)

| capture | what was accepted |
|---|---|
| `out/A2-bad-050-type-mismatch-parent.json` | a **LIABILITY** DETAIL account created under an **ASSET** HEADER parent — parent/child type consistency is not enforced |
| `out/A2-bad-053-unknown-param.json` | an unrecognised JSON parameter silently ignored, HTTP 200 |
| `out/A2-prod-062-map-header-account.json` | a **HEADER** account mapped as `loanPortfolioAccountId` |
| `out/A2-091c-journalentries-loan4.json` | a system journal entry **posted to that HEADER account** (GL 1, `account_usage=2`) — no refusal |
| `out/A2-fin-106-header-account.json` | a HEADER account (GL 15) accepted as a financial-activity target |
| `out/A2-111-update-retype-mapped.json` | GL 2 retyped **ASSET → INCOME** while mapped to four products, carrying journal entries posted as ASSET, and being the `ASSET_TRANSFER` target |

A2-111 is the sharpest of these. `out/A2-150-db-final-state.txt` shows the end state:
`financial_activity_type 100` (ASSET_TRANSFER, which `A2-fin-103` proved *requires* an ASSET
account) now points at GL 2 with `classification_enum = 4` (INCOME). The type rule is
checked **only when the mapping is created** and never re-checked when the account is
retyped. The oracle will hold an inconsistent state it would refuse to let you create.

### 4.8 Refusals catalogued on GL-account create

`out/A2-bad-04*.json`, `out/A2-bad-05*.json` — 16 probes. Highlights beyond those above:

- `A2-bad-045-no-usage` — omitting `usage` is **not** caught by the validator; it reaches
  PostgreSQL and returns **403** with `null value in column "account_usage" … violates
  not-null constraint`, leaking the failing row. The DDL default of `2` does not apply
  because the entity writes an explicit NULL. Contrast `A2-bad-044-no-type`, a clean 400.
- `A2-bad-046/047` — `type` outside 1..5 → `must be between 1 and 5`.
- `A2-bad-048` — `usage` outside 1..2 → `must be between 1 and 2`.
- `A2-014-create-grandchild-asset-detail` — a **DETAIL account cannot be a parent**: 403
  `error.msg.glaccount.parent.invalid`, "The account with id 2 is a 'Detail' account and
  cannot be used as a parent". This is a pre-persist domain check and, unlike the
  constraint violations, does **not** burn an identity value.

### 4.9 `financialactivityaccounts`

`out/A2-fin-10*.json`. The enumeration in the error message for an unknown activity is
returned in **declaration order, not sorted**:

```
The parameter `financialActivityId` must be one of [ 100, 200, 101, 102, 300, 103, 201 ] .
```

That ordering is now pinned by observation. A port that sorts the list diverges on the wire.

---

## 5. Planned but NOT captured, and why

Recorded so the next worker does not assume these were covered.

| item | why not |
|---|---|
| Mapping replacement (delete-then-recreate) on product **update** | `req/upd-070-repoint-fundsource.json` and `req/upd-071-add-channel.json` were written but not sent. Budget went to the resolution and delete-guard captures, which no other fire can take. Cheap next fire: `PUT /loanproducts/23` and re-run `sql/q2-product-mapping-rows.sql`. |
| `feeToIncomeAccountMappings` / `penaltyToIncomeAccountMappings` (charge-specific resolution) | needs an `m_charge` fixture; none exists on `gerege`. This is the **third** resolution dimension (`charge_id`) and it is untested here — the payment-type dimension is captured, the charge dimension is not. |
| `chargeOffReasonToExpenseAccountMappings`, `writeOffReasonsToExpenseMappings` | need `m_code_value` code values seeded first. |
| "must be an Expense GL account" for charge-off / write-off | blocked on the same fixture. |
| `write_off_reason_id` having no FK | needs the write-off-reason fixture to probe a dangling id. |
| `financial_account_type` collision keys 22 / 24 / 25 between cash and accrual | needs capitalized-income / buy-down product config; a distinct and larger probe. |
| Savings and shares mapping keys (`CashAccountsForSavings`, `CashAccountsForShares`) | **out of slice** (A2 is loans) and savings is behind the deposit-activation gate for an NBFI deployment. Porting is in scope; exercising a deposit endpoint on a live instance is not something this task was asked to do. |

---

## 6. Reproducing this corpus

Preconditions are **not optional** — the Path B gate must exit 0 first:

```sh
cd .softhouse/capture/pathb
CANARY_REQ=t22-audit/req/calc-pmode2-gerege.json sh t36/preconditions.sh gerege || exit 1
```

It passed all 23 assertions this fire, including `MoneyHelper.PRECISION = 19`,
`rounding-mode = 4 (HALF_UP)`, `timezone_id = Asia/Ulaanbaatar`, the behavioural HALF_UP
canary (period-1 interest `20925.05`), `org.postgresql.Driver` and
`jdbc:postgresql://db:5432/fineract_tenants`.

Then, from `.softhouse/capture/tierA-a2/`, **against a `gerege` tenant with zero GL
accounts** (`out/A2-000-glaccounts-preexisting.json` recorded `[]` before anything ran):

```sh
python3 mkreq.py  &&  sh run-020-accounts.sh          # GL accounts, ids 1-18
sh run-040-refusals.sh                                 # 16 create refusals
python3 mkreq2.py && sh run-060-mappings.sh            # products 22-28
python3 mkreq3.py                                      # loans 1-3, disburse, journal entries
python3 mkreq4.py && sh run-100-finactivity.sh         # financial activity accounts
sh run-120-delete-update.sh                            # update + delete guards
python3 mkreq5.py ; python3 mkreq6.py                  # follow-up discriminators
docker exec -i fineract-db-1 psql -U root -d fineract_gerege -f - < sql/q3-final-state.sql
python3 manifest.py verify
```

**The ids are positional, not stable.** They hold only on a tenant whose `acc_gl_account`,
`m_product_loan` and `m_loan` sequences are where they were this fire. Re-running against a
dirtier tenant reproduces the *behaviours* but not the *ids*, and the manifest will
correctly go red. That is the manifest working, not a failure.

`manifest.py verify` is demonstrably failable — `prove-manifest-red.py` mutates, deletes and
adds a file, confirms each is caught, and confirms the tree verifies green again afterwards.
Transcript in the handoff.

> **A2-5 correction to the paragraph above (21 Aug 2026).** That claim was true of the hash
> *comparison* and overstated as a claim about the *manifest*. The A2-4 review (D-3) showed
> `verify` then passed vacuously on empty input, did not recurse into `out/<subdir>/`, and
> covered neither this document nor the rig nor itself — the reviewer appended a false money
> claim to this very file and `verify` stayed green. All three are now closed and each was
> driven RED against the real pre-fix bytes: see `prove-manifest-blind-red.py` /
> `RED-GREEN-D3-manifest-blindness.txt`, and `prove-cap-transport-red.py` /
> `RED-GREEN-D2-cap-transport.txt` for `cap.sh`'s unreachable transport-failure handler (D-2).
> **Read `DEFECTS-FOUND-BY-REVIEW.md` before citing anything in this plan or under `out/`** —
> in particular the 30 `attempt1-*` files listed in `FLAGGED-NOT-REPRODUCIBLE.txt`, which are
> real oracle bytes with false recipes and are not citable. No captured byte under `out/`,
> `req/` or `sql/` was altered by A2-5; its 406 manifest lines are unchanged.

---

## 7. T275 addendum — §5 worked down, and §5's own framing corrected

Worker **T275**, local fire `20260822-060013b`, branch `softhouse/t275-a2-gap-capture`. Path B gate
`t36/preconditions.sh gerege` exit **0**, all 23 assertions, quoted in the handoff. Same pinned
oracle (`426a23544e…`), same tenant `gerege`, same `MathContext(19, HALF_UP)`, PostgreSQL 18.3.

**Nothing here is promoted.** No file was written to `.softhouse/vectors/` and `.softhouse/conformance.sh`
was not touched. New captures are the `A2-5xx` series; new recipes are `run-500`, `run-514`, `run-520`,
`run-540`, `mkreq-t275.py`, `capsql.sh`, `sql/q8-*`, `sql/q9-*`, `t275-mapping-diff.py`,
`prove-t275-reissue.py`.

### 7.1 §5 row 1 — CAPTURED, and the row's own title is REFUTED

`req/upd-070-repoint-fundsource.json` and `req/upd-071-add-channel.json` were sent, unmodified, for
the first time. §5 called the behaviour **"delete-then-recreate"**. On every path this fire could
reach, **it is not**. `sql/q2-product-mapping-rows.sql` could not have seen this: it does not select
`m.id`, and "updated in place" and "deleted and reinserted" are identical in its projection.
`sql/q8-t275-mapping-ids.sql` selects the primary key first, and `max(id)` over the whole table as an
independent witness — a recreate consumes identity values even when the row count does not move.

| capture | request | mapping-row identity observed |
|---|---|---|
| `A2-500` | *(pre-state)* | product 23 = ids **12–21**; generic `FUND_SOURCE` = id **12** → GL 2; no channel row; table `max(id)` **94** |
| `A2-502/503` | `PUT {fundSourceAccountId:16}` | **id 12 SURVIVES**, `gl_account_id` 2→16, `max(id)` still **94** — **UPDATE IN PLACE** |
| `A2-505/506` | `PUT paymentChannel[pt2→16]` | new row **95** appended; ids 12–21 untouched |
| `A2-508/509` | `PUT {description}` — no accounting parameter at all | **11 ids in, 11 ids out, zero churn** |
| `A2-510/511` | `PUT paymentChannel[]` (empty array) | row **95 DELETED**, nothing recreated, `max(id)` back to **94** |
| `A2-514/515` | re-add the channel | new row **96** (id 95 is **not** reused) |
| `A2-516/517` | **byte-identical body re-sent** | **zero churn** — id 96 survives, `max(id)` still 96 |
| `A2-518/519` | `PUT paymentChannel[pt2→**17**]` — same key, new account | **id 96 SURVIVES**, `gl_account_id` 16→17 |

**The rule the oracle actually follows is reconcile-by-key.** A generic slot is updated in place. A
list entry whose key is already present is updated in place. A row is deleted only when its key
**leaves** the list. An update carrying no accounting parameter disturbs no mapping at all, so
replacement is scoped to the payload and is not a property of the update command.

A port written to §5's title — rebuild the mapping set on every product save — would churn every
`acc_product_mapping.id` on every save and diverge from the oracle on identity, while looking correct
in any projection that omits the key. That is precisely the divergence this capture exists to prevent.

**One wire-form finding, separate from the identity one.** `A2-516` re-sent a byte-identical body
against state that already satisfied it, and the response still reported the field as changed:

```
{"resourceId":23,"changes":{"locale":"en","paymentChannelToFundSourceMappings":"[{\"paymentTypeId\":2,\"fundSourceAccountId\":16}]"}}
```

So `changes` is **not** a delta for this field — it is an echo of what was submitted, serialised as a
**JSON string, not a JSON array**. A port returning a true delta, or returning an array, diverges on
the wire on the ordinary retry path.

### 7.2 §5 row 2 (charge dimension) — CAPTURED. §5's stated blocker was already false.

§5: *"needs an `m_charge` fixture; none exists on `gerege`."* Measured at this fire and committed as
`out/A2-520-db-fixtures.txt`: **18 active LOAN charges exist**, 16 fee and 2 penalty, seeded by the
T40/T48/T51 Path B fires. No fixture was created by T275. The third resolution dimension is now
exercised: before this fire the corpus had **zero** `acc_product_mapping` rows with `charge_id` set;
it now has seven.

| capture | probe | oracle |
|---|---|---|
| `A2-522/528` | fee charge 1 → GL 11, penalty charge 6 → GL 8, both attached | **200**, product 56, rows **107** (`fat=5, charge=6, gl=8`) and **108** (`fat=4, charge=1, gl=11`) |
| `A2-524` | fee override naming charge 2, **not attached to the product** | **200** — row 119 persisted. **No attachment check.** |
| `A2-525` | penalty override on a **fee** charge, fee override on a **penalty** charge | **200** — rows 130, 131. **`is_penalty` is not checked against the mapping key.** |
| `A2-526` | fee override → GL 13, an **EXPENSE** account | **403** `error.msg.incomeAccountId.invalid.account.type` |
| `A2-527` | **two** fee overrides for the **same** `chargeId`, different accounts | **200** — rows **152** and **153**, both `fat=4, charge=1` |

A charge-scoped row carries the **same** `financial_account_type` as the generic slot it overrides
(`4` = fees, `5` = penalties); only `charge_id` distinguishes them. Resolution therefore has to
discriminate on a nullable column, exactly as the payment-type dimension does.

`A2-527` is the charge-dimension twin of §4.1. The duplicate is accepted and persisted here too, so
the "created happily, detonates at resolution" hazard is **not specific to payment types**. Whether it
detonates identically at resolution is **not captured** — see 7.5.

`A2-526`'s message, verbatim, is a wire-form finding in its own right:

```
Passed in GLAccount incomeAccountId with Id 13maps to the account Losses Written Off of type EXPENSE,
the expected account type was one among [4, 2]
```

Two things a port must not tidy. **`13maps`** — the missing space is in the oracle's own string.
And **`[4, 2]`** — the accepted types for an *income* mapping are INCOME **and LIABILITY**, so this
slot admits a liability account.

**Identity burn.** `A2-526` was refused, and the refusal still consumed `m_product_loan` id **59** and
`acc_product_mapping` ids **132–141** — visible as gaps between products 58 and 60 in
`out/A2-528-db-mapping-after-charge-dimension.txt`. Same class as §4.8's note on `A2-bad-045`.

### 7.3 §5 rows 3–5 (reason mappings) — the fixture-free half CAPTURED

A **dangling** reason id needs no fixture by definition; the fixture is what would make an id
*resolve*. Both sides probed, both with an expense account and with a non-expense one, so the
**order** of the two rules is observed rather than assumed.

| capture | probe | oracle |
|---|---|---|
| `A2-540` | `writeOffReasonCodeValueId: 999999`, expense GL 13 | **400** `validation.msg.writeoffreason.invalid` — *"Write-off reason with ID 999999 does not exist"*, `parameterName: writeOffReasonsToExpenseMappings`, `args: []` |
| `A2-541` | same id, **GL 9 (INCOME)** — both rules violated | **400** with **both errors, accumulated**, the **account error first**: `validation.msg.glaccount.not.found` — *"GL Account with ID 9 does not exist or is not an Expense GL account"*, `parameterName: expenseAccountId` — then the reason error |
| `A2-542` | `chargeOffReasonCodeValueId: 999999`, expense GL 13 | **400** `validation.msg.chargeoffreason.invalid` — *"Charge-off reason with ID 999999 does not exist"*, `parameterName: chargeOffReasonToExpenseAccountMappings` |
| `A2-543` | same id, GL 9 | **400**, both errors, same order as `A2-541` |

**Validation is accumulating, not short-circuiting.** A port that returns the first failure returns a
one-element `errors` array where the oracle returns two.

**§3 row 15 is now closed on both halves.** The DDL half:
`acc_product_mapping.charge_off_reason_id`, `.capitalized_income_classification_id` and
`.buydown_fee_classification_id` each carry an FK to `m_code_value`; **`write_off_reason_id` carries
none** [`out/A2-520-db-fixtures.txt`]. The behavioural half: the application check fires first on
**both** sides, so the FK asymmetry never surfaces on this path — and on the write-off side that
application check is the **only** referential integrity there is.

**§3 row 16 is closed.** *"must be an Expense GL account"* is real, and its message **conflates**
absence with wrong type under a single code, `validation.msg.glaccount.not.found`. A port that
distinguishes "no such account" from "wrong type" diverges on the wire even when both refuse.

Zero rows persisted from any group-C probe: `write_off_reason_id` and `charge_off_reason_id` are both
still `NULL` on every row of `acc_product_mapping` [`out/A2-544-db-mapping-after-reason-probes.txt`].

### 7.4 §5 rows STILL EXCLUDED, each with its blocker MEASURED rather than inherited

| §5 row | still blocked on | measured this fire |
|---|---|---|
| charge-off / write-off reason mappings that **RESOLVE** | `m_code_value` seeding | `m_code` **26 `WriteOffReasons`** and **39 `ChargeOffReasons`** exist with **0** values each; 22 code values exist in total, none under either code |
| `financial_account_type` collision keys **22 / 24 / 25** (cash vs accrual) | capitalized-income / buy-down product config, which itself needs `m_code_value` | `m_code` **40 `capitalized_income_transaction_classification`** and **41 `buydown_fee_transaction_classification`** exist with **0** values each; both mapping columns FK `m_code_value`, so the rows are unreachable until they are seeded |
| savings / shares mapping keys | **not a fixture blocker — a policy one** | out of slice (A2 is loans) and deposit-taking activation is prohibited for the ratified NBFI licence (CLAUDE.md). Unchanged by this fire. |

Seeding `m_code_value` is a **write to reference data**, not a capture, and it is the first thing the
next oracle-reaching fire should do if it wants the resolving cases: two `POST /codes/26/codevalues`
and two `POST /codes/39/codevalues` unblock rows 3–5 of §5 completely, and codes 40/41 unblock the
collision keys.

### 7.5 What T275 did NOT establish — read this before citing 7.1 or 7.2

- **Whether a payment-type KEY CHANGE (not a value change) reuses the row.** Every list probe here
  held `paymentTypeId` at 2. A body moving an entry from payment type 2 to payment type 1 was not sent.
- **Multi-entry list reconciliation.** Every list sent carried at most one entry.
- **The ACCRUAL product path.** All group-A and group-B products are `accounting_type` 2 (CASH).
- **Whether the duplicate charge mapping of `A2-527` detonates at resolution** the way the duplicate
  channel of §4.1 did. That needs a loan, a disbursement and a charge to fall due on product 60 —
  a runtime capture, not a configuration one. It is the single highest-value follow-up here.
- **`deleteAll` is in the source and was not observed firing.**
  `ProductToGLAccountMappingHelper.java:417/440` does call `deleteAll` / `delete` on the channel
  collection. This fire observed the *outcome* on four inputs; it did not observe the *mechanism*, and
  nothing above should be read as a claim about which JPA call ran.
