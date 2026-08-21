# A2-2 — independent review of A2-1 (Tier A slice A2 behaviour extraction)

**Verdict: MICRO-FIX.**

| | |
|---|---|
| Reviewer | `A2-2` |
| Branch | `softhouse/A2-2-review-a2-1` |
| Artefact reviewed | `softhouse/A2-1-behaviour` @ `4a654b0` — `docs/analysis/tierA-a2-behaviour.md` (1,115 lines) + `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-1.md` |
| How it was read | `git show softhouse/A2-1-behaviour:<path>` — the branch, never the working tree |
| Oracle | `/Users/buv/fineract` @ `426a23544` (`git log --oneline -1` confirms; `git status --porcelain` empty) |
| Method | Re-derivation from Fineract source. Every citation supporting brief items 1 and 2 was opened. Absence claims were re-run with a positive control. |
| Date | 2026-08-21 |

**One-line summary.** Every money-critical limb A2-1 asserts is TRUE — the resolution order, both
naive-transcription defects, the `ordinal()` absence, the refusal to infer a sign convention, and
the written trial-balance stored balance. I refute one citation PATH, one grep-evidence sentence,
and one framework assertion, and I refute A2-1's *mechanism* for how `closing_balance` gets written
(the headline claim survives and the tension with the non-negotiable gets worse, not better).
Nothing found would put a wrong number or a wrong GL account into slice A1.

---

## 1. Brief item 1 — the mapping RESOLUTION ORDER: **CONFIRMED, every limb**

Re-derived by reading `AccountingProcessorHelper.java` end to end and
`ProductToGLAccountMappingRepository.java` in full. Limb by limb, against A2-1's §4.7 summary:

| # | A2-1's limb | Verdict | My own citation |
|---|---|---|---|
| L1 | Seven `FinancialActivity` ids `{100,101,102,103,200,201,300}` pre-empt everything and resolve tenant-globally on activity type alone, ignoring product and payment type | **TRUE** | `AccountingProcessorHelper.java:1187` → `isOrganizationAccount` at `:1340-1342` = `FinancialActivity.fromInt(id) != null`; values at `AccountingConstants.java:439-445`; lookup `:1188-1190` passes only `accountMappingTypeId` |
| L2 | Otherwise the base row is the *core* `acc_product_mapping` row on `(product_id, product_type, financial_account_type)` with **all six** discriminator columns NULL | **TRUE** | `ProductToGLAccountMappingRepository.java:38-40` — the JPQL names `paymentType`, `charge`, `chargeOffReason`, `writeOffReason`, `capitalizedIncomeClassification`, `buydownFeeClassification`, all `is NULL`. Six, counted. |
| L3 | The base row is overridden by a `payment_type`-matching row **only** when the placeholder is the family's fund-source/reference placeholder, value 1 in all three families | **TRUE** | loan `:1199` (`CashAccountsForLoan.FUND_SOURCE` = 1, `AccountingConstants.java:39`); savings `:1285` (`CashAccountsForSavings.SAVINGS_REFERENCE` = 1, `:269`); shares `:1309` (`CashAccountsForShares.SHARES_REFERENCE` = 1, `:519`) |
| L4 | Charges are a separate entry point with **different precedence per family** | **TRUE** | loan `:1218-1238` (charge row wins for **any** placeholder, gated `chargeId != null` at `:1229`); savings `:1240-1269`; shares `:1322-1338` (charge lookup issued **unconditionally**, no `chargeId != null` guard, `:1331`) |
| L5 | For savings the GL account hung off the `m_charge` row **outranks every mapping** | **TRUE** | `:1255` `chargeRepositoryWrapper.findOneWithNotFoundDetection(chargeId).getAccount()`; `:1256-1258` returns it immediately when non-null. Gated to `id ∈ {4,5}` at `:1253-1254`. Neither `:1218-1238` nor `:1322-1338` consults it. |
| L6 | Charge-off / write-off / the two classification lookups **bypass** the base row and **ignore `financial_account_type`** | **TRUE** | call sites `:194`, `:199`, `:205`, `:207`; queries `ProductToGLAccountMappingRepository.java:76-78`, `:109-111`, `:101-103`, `:105-107`. I read all four JPQL strings: each has exactly three predicates — the code-value id, `productId`, `productType`. `financialAccountType` appears in none. Return type is `ProductToGLAccountMapping`, null on miss, no exception. |
| L7 | On a base-row miss loans raise `ProductToGLAccountMappingNotFoundException`; savings, shares and all three charge paths dereference null | **TRUE** | loan `:1208-1211`; WCL `:1024-1027`. No null check precedes `:1268` (savings charges), `:1237` (loan charges), `:1293` (savings product), `:1317` (shares product), `:1337` (shares charges). |

Two further limbs of A2-1's §4.2 table checked and true: the working-capital path has **no** STEP 0
(`:1010-1029` — no `isOrganizationAccount` call) and additionally requires `paymentTypeId != null`
(`:1015`), which the loan path does not.

**Cross-check.** A2-3's live capture on the same commit records *"Resolution order observed, not
inferred: the payment-type-specific row wins; absence falls back to the generic payment_type NULL
row"* and *"Resolution MISS renders the enum space-separated: `CHARGE OFF EXPENSE`"* — the second
independently corroborates L7's loan branch reaching `…fromInt(id).toString()` at `:1210`, since
`toString()` on these enums is `name().replace("_", " ")` (`AccountingConstants.java:70-73`).

---

## 2. Brief item 2 — the two naive-transcription money defects: **BOTH CONFIRMED**

### 2a. `PortfolioProductType.fromInt` permutes 3/4/5 — **CONFIRMED**

I read the whole file, not the cited spans.
`fineract-core/src/main/java/org/apache/fineract/portfolio/PortfolioProductType.java`:

- `:26-31` — `LOAN(1)`, `SAVING(2)`, `CLIENT(**5**)`, `PROVISIONING(**3**)`, `SHARES(**4**)`, `WORKING_CAPITAL_LOAN(6)`.
- `:51-59` — `case 3 -> CLIENT; case 4 -> PROVISIONING; case 5 -> SHARES;`

So `fromInt(v)` is `values()[v-1]` — declaration order, i.e. `ordinal()+1` — not the value map.
Composing the two, my own table, derived before reading A2-1's:

| stored `product_type` | which constant wrote it (`getValue()`) | `fromInt` returns | that constant's `getValue()` |
|---|---|---|---|
| 3 | `PROVISIONING` | `CLIENT` | 5 |
| 4 | `SHARES` | `PROVISIONING` | 3 |
| 5 | `CLIENT` | `SHARES` | 4 |

Identical to A2-1's. `1, 2, 6` are fixed points. A2-1's porting instruction (encode `getValue()` and
write its true inverse; do not transcribe `fromInt`) is correct and is the right instruction.

Callers, my own grep (`grep -rn --include='*.java' "PortfolioProductType\.fromInt" /Users/buv/fineract`,
`/build/` excluded): exactly two outside the declaration —
`fineract-core/.../accounting/common/AccountingEnumerations.java:84` and
`fineract-accounting/.../journalentry/JournalEntryMapper.java:79`. Matches A2-1. Blast radius
correctly left `[UNVERIFIED]` (§11 item 10).

### 2b. `CashAccountsForLoan` vs `AccrualAccountsForLoan` collide at 22, 24, 25 — **CONFIRMED**

`AccountingConstants.java` read directly, `:37-62` and `:95-122`:

| value | `CashAccountsForLoan` | `AccrualAccountsForLoan` |
|---|---|---|
| 7 / 8 / 9 | *absent* | `INTEREST_RECEIVABLE` / `FEES_RECEIVABLE` / `PENALTIES_RECEIVABLE` |
| **22** | `CLASSIFICATION_INCOME` (`:57`) | `INCOME_FROM_CAPITALIZATION` (`:118`) |
| **24** | `INCOME_FROM_DISCOUNT_FEE` (`:59`) | `BUY_DOWN_EXPENSE` (`:120`) |
| **25** | `FEES_RECEIVABLE` (`:60`) | `INCOME_FROM_BUY_DOWN` (`:121`) |
| **26** | `PENALTIES_RECEIVABLE` (`:61`) | *absent* (accrual ends at 25, `:121-122`) |

A2-1's D-2 conclusion holds: a stored `(product_type=1, financial_account_type=24)` row is not
decidable without the product's accounting rule, and a Go schema modelling
`financial_account_type` as one flat enum is wrong. Its vector recommendation (cash **and** accrual
loan product at 22, 24, 25) is the right discriminating set; I would add **26**, because that is the
value at which `AccrualAccountsForLoan.fromInt` returns null and `:1210` NPEs.

Savings enums re-read: `CashAccountsForSavings` `:269-278` and `AccrualAccountsForSavings` `:313-326`
— the accrual set is a strict superset (adds 15–18), **no collision**, as A2-1 says.
`CashAccountsForShares` `:519-522` as stated.

---

## 3. Brief item 3 — the ABSENCE claim on `ordinal()`: **CONFIRMED, and strengthened**

A2-1 §3.1: *"No `ordinal()` call exists anywhere in the four scope paths or in
`AccountingConstants.java`."*

I did not reuse A2-1's search. Mine, with the positive control run **first**:

```
# POSITIVE CONTROL — prove the query can find something
grep -rn --include='*.java' "ordinal" /Users/buv/fineract --exclude-dir=build | wc -l
→ 32     (e.g. JdbcJavaType.java:167, JavaType.java:108/318/321, AllocationType.java:39)

# TARGET — the four scope paths + AccountingConstants.java
grep -rn --include='*.java' "ordinal" <4 scope paths> AccountingConstants.java
→ (no output), exit 1
```

Note the pattern is the bare substring `ordinal`, **not** `\bordinal()\b` — deliberately, because
P-12 (`patterns.md`) records that this program already reported a false zero from an unsupported
word-boundary. A substring search cannot fail that way, and the control proves it discriminates.
Claim stands.

**I then closed a loophole A2-1 did not consider.** A grep for `ordinal` cannot see JPA
ordinal persistence: `@Enumerated` with no argument defaults to `EnumType.ORDINAL`, which persists
`ordinal()` without the token ever appearing. So:

```
grep -rn --include='*.java' "Enumerated" <4 scope paths> fineract-core/.../glaccount/
→ (no output), exit 1
# control: 35 files elsewhere in the checkout contain "Enumerated"
```

Zero. Every enum in scope is persisted as a plain `Integer`/`int` column written from `getValue()`
at the call site (`GLAccount.java:73-77`, `ProductToGLAccountMapping.java:61-65`). The absence claim
is true on a stronger reading than A2-1 tested it on. **This is a strengthening, not a defect** — but
the port must keep it: a Go `iota` on a struct field is the same trap wearing Go's clothes.

---

## 4. Brief item 4 — the sign convention: **A2-1's refusal is CORRECT**

Verified, in three directions:

1. **No table in scope carries a sign.** I read the DDL for all three tables:
   `acc_gl_account` (`0001_initial_schema.xml:49-75`) — 11 columns, none a sign or normal-balance
   flag; `acc_product_mapping` (`:179-187` plus the four later changelogs) — none;
   `acc_gl_financial_activity_account` (`:99-109`) — three columns, none.
2. **Nothing derives a normal balance from `GLAccountType`.** I read
   `fineract-core/.../GLAccountType.java` in full (`:23-115`). It carries `value` and an i18n `code`
   and nothing else; the only derived data are `getMinValue()`/`getMaxValue()` (`:47-64`, → 1 and 5)
   and `fromInt` (`:88-107`). There is no `isDebitNormal`, no sign, no polarity.
3. **The one sign the slice consumes is defined outside it** — `JournalEntryRepository.java:52-66`
   (`SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END)`) with
   `JournalEntryType` `CREDIT(1)`, `DEBIT(2)`. Both re-read; A2-1's transcription of the JPQL is
   character-accurate and its instruction that A1 re-derive from those files rather than from the
   document is the right instruction.

A2-1 was right to refuse, and right to say so plainly rather than infer. See **F-2** below for a
defect in the *evidence* it offered for this conclusion — the conclusion survives it.

---

## 5. Brief item 5 — `TrialBalance.closing_balance`: **claim CONFIRMED, mechanism REFUTED**

### The claim is true

`m_trial_balance.closing_balance` is a written, stored balance column.

- Entity: `TrialBalance.java:58-59` — `@Column(name="closing_balance", nullable=false) BigDecimal closingBalance`, **no `precision`/`scale`**.
- DDL: `0001_initial_schema.xml:4676-4678` — `DECIMAL(19, 6)`, `nullable="false"`.
- Written at `UpdateTrialBalanceDetailsTasklet.java:81` and `:126`; never derived at read time.

**The tension, stated precisely.** CLAUDE.md's non-negotiable is *"The ledger is double-entry and
append-only. Balances are derived, never written."* `m_trial_balance` is **not the ledger** — the
ledger is `acc_gl_journal_entry`, which A1 owns, and that table is append-only. `m_trial_balance` is
a batch-populated reporting table. So this is not a violation *in Fineract*; it becomes one the
moment a Go port carries the table across as a balance store, because the guard that grades our
diffs greps for writes to balance columns and cannot tell a reporting cache from a ledger balance.
A2-1's D-9 ("do not port as a balance store — derive it, or drop the table") is the correct call and
I endorse it unchanged. **A3 may port `m_trial_balance` only as a derived/materialised view whose
refresh is a pure function of `acc_gl_journal_entry`, and must not accept a write path to
`closing_balance` from application code.**

Second, independent tension: `DECIMAL(19,6)` against MNT minor unit 2 means the column can hold
sub-minor-unit residue. A2-1 flags this (§8 fact 1, B-4) and correctly says the truncation rule is
specified nowhere in the slice. Agreed — that is a program-level decision, not A3's to invent.

### The mechanism A2-1 describes is wrong — **F-1**, the most substantive finding in this review

A2-1 §7 and §8 present the persisted value as the output of a running accumulation:

> `UpdateTrialBalanceDetailsTasklet.java:119-127` then accumulates `closingBalance += amount` over
> rows ordered by `created_date, entry_date`

and §8: *"computed by a batch job and `UPDATE`d in place."* Re-deriving the tasklet end to end
(`:49-128`), that is not what produces the stored value:

1. **The insert path already fills the column.** `insertTrialBalanceForDate` (`:71-89`) maps the
   JPQL projection: `tb.setAmount((BigDecimal) row[2])` at `:78` — `row[2]` is the **signed**
   movement — and `tb.setClosingBalance((BigDecimal) row[5])` at `:81`, where `row[5]` is
   `SUM(je.amount)` (`JournalEntryRepository.java:61`), the **unsigned** total. Every row this code
   writes therefore has a non-null `closing_balance` that is a *sum of absolute journal amounts*,
   not a closing balance in any accounting sense.
2. **The accumulation branch selects rows that cannot exist.** `updateClosingBalances` (`:91-97`)
   drives off `findDistinctOfficeIdsWithNullClosingBalance` (`TrialBalanceRepository.java:47-52`,
   `WHERE tb.closingBalance IS NULL`), and the row fetch is
   `findNewByOfficeAndAccount` (`:31-32`, native, `... and closing_balance is null order by
   created_date, entry_date`). But the column is `NOT NULL` in the DDL (`:4676-4678`) **and**
   `nullable=false` on the entity (`TrialBalance.java:58`), and the only insert path always
   populates it. On this revision's own code, `:99-128` is unreachable.
3. **The one constructor that would produce a NULL row is dead.**
   `TrialBalance.getInstance(...)` (`:61-65`) sets office, account, amount, entryDate,
   transactionDate — and never `closingBalance`. My grep for `TrialBalance.getInstance` across the
   checkout (`--exclude-dir=build`) returns **only the declaration**. Zero callers.

**Why it matters, and why it is an obligation and not a rejection.** It does not change D-9's
recommendation and it puts no number into A1 — A1 owns `acc_gl_journal_entry`, not
`m_trial_balance`. But the brief routes item 5 to A3 with *"this shapes what slice A3 may port,"*
and an A3 porter reading §7 would implement a running-balance accumulator and reproduce a *different*
column than Fineract stores. It also makes the tension with the non-negotiable **worse**, not
better: the persisted `closing_balance` is an unsigned sum wearing a balance's name, so porting it
as-is would be both a written balance *and* a wrong one.

**And it is a missing `[UNVERIFIED]`.** A2-1's §11 is careful about reachability elsewhere — item 5
(the `fromInt(...).toString()` NPEs) and item 11 (the `account_usage = 2` default) are both listed
precisely because "the code says X but is X reached?" was unresolved. The identical question about
`:99-128` was not asked. Under the honesty rule this is a claim carrying more confidence than its
evidence supports.

---

## 6. Findings

Severity per the brief and P-5 (`.softhouse/gates-proposed-answers.md`, Buyan, 21 Aug 2026): REJECT
is reserved for a wrong number / wrong GL account into A1, or a citation that does not support its
claim; a prose finding no vector would catch is an **obligation** and the stream proceeds.
(Not `patterns.md`'s P-5, which is the worktree-cutting rule — citation-hazard table,
`patterns.md:3-20`.)

### F-1 — `m_trial_balance.closing_balance` mechanism (§7, §8, D-9) — **OBLIGATION**

Detailed in §5 above. Required correction, in §7 and §8 both (Run-1 lesson: *corrections leak; grep
the whole document for restatements*):

- state that `closing_balance` is written **at insert** from `SUM(je.amount)` — the **unsigned**
  total, `JournalEntryRepository.java:61` → `Tasklet:81` — while `amount` gets the **signed**
  movement from `row[2]` → `:78`;
- mark the accumulation at `:119-127` as **`[UNVERIFIED: reachable]`**, with the reason: it is gated
  on `closing_balance IS NULL` (`TrialBalanceRepository.java:31`, `:47-52`) against a `NOT NULL`
  column (`0001_initial_schema.xml:4676-4678`, `TrialBalance.java:58`), and the only constructor
  that omits `closingBalance` (`TrialBalance.java:61-65`) has zero callers;
- add it to the §11 list.

### F-2 — the sign-convention grep evidence is not what the grep returns (§7) — **OBLIGATION**

A2-1 writes: *"Grep of the scope paths for `debit`/`credit` finds hits only in the trial-balance job
described below and in Swagger example strings."*

Re-run, case-insensitive, over the four scope paths: **zero** hits in the entire `glaccount` path —
including `jobs/updatetrialbalancedetails/UpdateTrialBalanceDetailsTasklet.java` (0) and
`api/GLAccountsApiResourceSwagger.java` (0). The only hits in the other three paths are the
identifier `GOODWILL_CREDIT` and its API param strings — a placeholder name, not a sign.

The most likely cause is that the grep actually swept a wider path (the `accounting/journalentry`
package, where debit/credit and Swagger examples are plentiful) and the result was reported as
scoped. **The conclusion survives a fortiori** — the true evidence is *stronger* than the sentence
claims — but the sentence describes a search that does not return what it says. Replace it with:
"zero case-insensitive hits for `debit`/`credit` in the four scope paths other than the
`GOODWILL_CREDIT` placeholder identifier."

### F-3 — `findBy…PaymentTypeId(…, null)` "simply matches nothing" is unsupported (§4.2) — **OBLIGATION**

A2-1's §4.2 table, loan row: *"**no null-check on `paymentTypeId`**"* — true, verified at `:1199`.
But the parenthetical that follows — *"`findBy…PaymentTypeId(…, null)` is issued with a null
argument and simply matches nothing"* — is a claim about **Spring Data JPA derived-query
semantics**, carries no citation, carries no `[UNVERIFIED]`, and is not in the §11 list.

Spring Data JPA translates a null argument bound to a derived-query equality into `IS NULL`, not
into `= NULL`. Under that reading the emitted predicate is `payment_type IS NULL` and it matches the
**core row**, not nothing. **I could not settle this from the pinned checkout** — Boot 3.5.15
(`build.gradle:116`), and no `spring-data-jpa` artefact is resolvable locally — so I record my
counter as contested, not as a refutation. Either way the sentence as written is an unsupported
framework assertion, and this repo has been burned by exactly one of those before: A2-1 itself
withdrew the `ddl-auto` sentence for precisely this reason and then left this one standing.

**Money impact: none, on the data the write paths can produce.** I traced every writer of
`acc_product_mapping`: only `savePaymentChannelToFundSourceMapping`
(`ProductToGLAccountMappingHelper.java:599-608`) sets `payment_type`, and it always sets it non-null
(`:601-602` throws if the payment type is absent). Charge rows use `financial_account_type` 4 or 5
(`:629`, `:634`); reason rows use 16 or 6 (`:666`, via `matching(...)` `:642-650`); classification
rows use 22 (`:699`). So for `financial_account_type = 1` there is exactly **one** `payment_type IS
NULL` row — the core row — and both readings resolve to the **same GL account**. That is why this is
an obligation and not a rejection.

It stops being harmless the moment a duplicate exists, which §5.2 proves is physically possible and
A2-3 **observed** live (*"More than one result was returned from Query.getSingleResult()"*). Required:
mark the sentence `[UNVERIFIED]`, add it to §11, and name the vector below.

### F-4 — `JournalEntryType.java` is cited in the wrong Gradle module (§7, §13) — **MICRO-FIX**

A2-1 cites `fineract-accounting/.../journalentry/domain/JournalEntryType.java:23-24` in §7, and in
§13 groups it as `fineract-accounting/.../journalentry/domain/{JournalEntryRepository,JournalEntryType}.java`.

**That path does not exist.** `find /Users/buv/fineract -name 'JournalEntryType.java'` returns exactly
one file: `fineract-core/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntryType.java`.
(`JournalEntryRepository` *is* in `fineract-accounting` — only the second half of the brace expansion
is wrong.) The **content** is correct: `:23` `CREDIT(1, …)`, `:24` `DEBIT(2, …)`, verified.

This is a one-token fix, but it is not cosmetic: §7's instruction to A1 is *"A1 must re-derive it
from `JournalEntry`/`JournalEntryType` directly, not from this document"*, so this is the single
citation A2-1 most expects a downstream worker to follow, and it resolves to nothing. It is also an
instance of A2-1's own headline finding B-1 — *the slice's core types live in `fineract-core`, not
where the directory suggests* — committed inside the document that raises it.

### F-5 — completeness of the `[UNVERIFIED]` list

The brief asks whether the 12-item list is complete, not whether it is long. **It is not complete.**
Three items belong on it and are absent: F-1 (reachability of `Tasklet:119-127`), F-3 (Spring Data
null-parameter semantics), and — lower value — the reachability of the savings charge path's
`chargeRepositoryWrapper.findOneWithNotFoundDetection(chargeId)` at `:1255`, which is called with no
`chargeId != null` guard and will throw on a null charge id, unlike the loan path's `:1229` guard.
A2-1 notes the loan guard's presence but never says what the savings path does when `chargeId` is
null.

The twelve items that *are* listed are all genuine gaps, correctly reasoned, and none of them is a
guess dressed as a gap. The list's quality is high; its coverage is three items short.

---

## 7. Everything else I re-derived and found TRUE

Sampled beyond items 1–5, because a document is graded hardest where it feeds a decision.

- **Scope counts.** 58 files / 6,636 LOC across the four paths — my `find`/`wc` reproduces both exactly.
- **`acc_gl_account` DDL vs JPA.** All eleven rows of A2-1's §2.1 table re-read against
  `GLAccount.java:50-84` and `0001_initial_schema.xml:53-74`. Every cell correct, including the three
  length disagreements (`name` JPA 45 / DDL 200; `gl_code` JPA 100 / DDL 45; `description` 500/500)
  and the `account_usage` `TINYINT` default 2 (`:67-69`).
- **Hierarchy.** `GLAccount.java:186-197` — `child.hierarchy = parent.hierarchy + child.id + "."`,
  root `"."`. A2-1's worked example is right, and the counter-intuitive part (own id present, root id
  absent) is stated correctly. **Independently corroborated by A2-3's live capture**: a child of root
  1 stores `.2.`, not `.1.2.` — a second method, a different worker, same answer.
- **Two-flush create** `:96/:98/:100`; **re-parent does not cascade** `:134-138`; the display-only
  consumer `GLAccountReadPlatformServiceImpl.java:49`. All as stated.
- **U3/U4 run before the account is loaded** — `:119-126` precede `:128-129`. Confirmed; a real,
  cheap refusal vector.
- **`validateForAttachedProduct`** `:177-187` — the `count == null || count > 0` quirk is transcribed
  exactly (`:181`).
- **Delete guards** `:192-193`, `:196-198`, `:201-205`, `:207-211` — all four present in the stated
  order.
- **`handleGLAccountDataIntegrityIssues`** substring-matches `acc_gl_code` at `:242`, falls through
  to `:248`. The DDL declares uniqueness inline and **unnamed** (`:58-60`). A2-1's `[UNVERIFIED]` on
  which error code actually fires is correctly placed — this genuinely cannot be settled from source.
- **`financial_action` unique constraint absent from the DDL.** My own grep:
  `grep -rn "financial_action" fineract-provider/src/main/resources/db/` → **0**; positive control
  `acc_product_mapping` over the same tree → **56**, so the search discriminates. Zero hits anywhere
  outside `.java` in the whole checkout. Annotation confirmed at `ProductToGLAccountMapping.java:42-43`.
  A2-3 corroborates at runtime. Three methods, one answer.
- **The write-path table (§5.3).** All seven rows opened: `:599-608` (no type check, `FUND_SOURCE`
  hard-wired to 1 for every family at `:605`), `:614-640` (penalty→INCOME `:627-628`, fee→INCOME|LIABILITY
  `:631-633`, the in-source TODO at `:618-619`), `:652-676` (no type check, silent skip `:663`,
  idempotent `:658-661`), `:678-709` (silent skip `:696`, `financial_account_type` hard-wired to 22
  at `:699` for **both** classification kinds, disambiguated only by which nullable column is set
  `:701-705`), `:757-764`, `:766-772`. Every claim true.
- **`getAccountByIdAndType` validates type only, never usage** — `:727-736`; and `getAccountById`
  `:738-741` validates nothing. So "detail accounts only" is a dropdown convention
  (`GLAccountReadPlatformServiceImpl.java:214-222`, called at
  `AccountingDropdownReadPlatformServiceImpl.java:96,101,110,119,128,137,146` — all seven line numbers
  correct), not a domain rule. Confirmed.
- **Share create writes under the wrong `product_type` (D-8).**
  `ProductToGLAccountMappingWritePlatformServiceImpl.java:386-387` calls the **savings** helper;
  `SavingsProductToGLAccountMappingHelper.java:113` and `:124-125` hard-wire
  `PortfolioProductType.SAVING`. Both citations exact. A2-1 correctly marks it
  `[UNVERIFIED: not observed at runtime]` — the source evidence is strong and the honesty tag is
  still right.
- **Savings `ACCRUAL_UPFRONT` gets no mappings at all** — `:311-349`, the switch handles `NONE`,
  `CASH_BASED`, `ACCRUAL_PERIODIC`, then `default: break` at `:345-346`. True.
- **Financial activity create/update asymmetry.** `FinancialActivityAccountDataValidator.java:62-66`
  lists **seven**; `:89-92` lists **five** — `CASH_AT_MAINVAULT` (101) and `CASH_AT_TELLER` (102) are
  creatable but not settable on update. Both halves read. Clean refusal vector, exactly as claimed.
- **`acc_gl_financial_activity_account` has no office column** — `0001_initial_schema.xml:99-109`,
  three columns; `gl_account_id` `NOT NULL DEFAULT 0` (`:103-105`); `financial_activity_type`
  `NOT NULL UNIQUE` inline and unnamed (`:106-108`). Tenant-global confirmed.
- **`GLAccountInvalidUsageException` is dead code.** My grep returns exactly two lines, both inside
  its own file (`:26`, `:28`). Control: the same query for `GLAccountInvalidParentException` returns
  cross-file hits in the write service, so it discriminates. And the swapped error codes are real —
  `GLAccountInvalidUsageException.java:29` emits `error.msg.glaccount.classification.invalid`;
  `GLAccountInvalidClassificationException.java:29` emits `error.msg.glaccount.usage.invalid`.
- **`%?%` invalid SQL** at `GLAccountReadPlatformServiceImpl.java:154`; **`rs.wasNull()` mis-ordering**
  at `:98-99`; **direct interpolation** at `:177`, `:185`. All three verbatim as described, all three
  correctly tagged unprobed.

---

## 8. Vectors this review adds

Beyond A2-1's own list, which I endorse:

1. **Null payment type on a FUND_SOURCE resolution** (settles F-3). Loan product with a core
   `FUND_SOURCE` mapping and one payment-channel mapping; disburse with **no** payment type, and
   capture the GL account posted. Then repeat with a deliberately duplicated core row — under
   `IS NULL` semantics the second case must raise the non-unique-result error A2-3 already observed;
   under "matches nothing" it must succeed. That is the discriminator.
2. **`financial_account_type = 26` on a cash loan product with the mapping missing** (settles §11
   item 5, and it is the *error* path, so it is a refusal vector). `AccrualAccountsForLoan.fromInt(26)`
   is null → `:1210` NPEs instead of returning
   `error.msg.productToAccountMapping.not.found`. Mirror case: WCL at 7, 8 or 9 via `:1026`.
3. **Trial-balance job on a tenant with journal entries** (settles F-1). Run
   `UpdateTrialBalanceDetails` and read back `m_trial_balance`: compare the stored `closing_balance`
   against both candidate formulas — per-group `SUM(je.amount)` (unsigned) versus a running
   accumulation of the signed `amount`. One capture separates them. This is the vector A3 needs
   before it decides what to do with the table.

---

## 9. Verdict

**MICRO-FIX.**

The document is strong. Its five highest-value claims — the resolution order, both transcription
defects, the `ordinal()` absence, the sign-convention refusal, and the written trial-balance —
all survive independent re-derivation, and the citation quality is high: of roughly sixty
`FILE:LINE` citations I opened, **one** has a wrong path and **zero** have a wrong line number.
The 58-file / 6,636-LOC count reproduces exactly. It is safe for slice A1 to build the posting
engine's account resolution on §4.

Micro-fix, in one pass, no third draft:

| id | Fix | Where |
|---|---|---|
| **F-4** | `JournalEntryType.java` → `fineract-core/...`, not `fineract-accounting/...` | §7, §13 |
| **F-1** | Correct the `closing_balance` mechanism (written at insert from unsigned `SUM(je.amount)`); mark `:119-127` `[UNVERIFIED: reachable]`; add to §11. **Grep §7, §8 and D-9 for restatements** | §7, §8, §10 D-9, §11 |
| **F-2** | Replace the sign-convention grep sentence with what the grep actually returns | §7 |
| **F-3** | Mark the `findBy…PaymentTypeId(…, null)` parenthetical `[UNVERIFIED]`; add to §11 | §4.2, §11 |
| **F-5** | Add the savings-charge null-`chargeId` reachability gap to §11 | §11 |

No REJECT. Nothing found would put a wrong number or a wrong GL account into slice A1: F-1 concerns
a reporting table A1 does not own, F-2 and F-3 leave their conclusions intact (F-2's a fortiori,
F-3's because only one `payment_type IS NULL` row can exist at `financial_account_type = 1` under
every write path in the tree), and F-4 is a path typo over correct content.

**Absence claims whose search I could not make discriminate: none.** Every absence claim I checked
(`ordinal`, `@Enumerated`, `financial_action`, `GLAccountInvalidUsageException`,
`TrialBalance.getInstance` callers, `PortfolioProductType.fromInt` callers) was run with a positive
control that returned hits, and the target query returned zero.
