# T490 — INDEPENDENT adversarial review of T487 (Tier A · A1, journal-entry posting)

| | |
|---|---|
| Reviewer | `T490` |
| Branch | `softhouse/T490-review-t487` |
| Under review | `softhouse/T487-a1-journalentry-behaviour` @ `0b2545c1` — `docs/analysis/tierA-a1-behaviour.md` (1,127 lines), `.softhouse/handoff/T487.md` |
| Oracle | Fineract reference implementation (the *test oracle*; never Oracle Database), `/home/user/fineract` |
| Pin, verified by this reviewer | `git -C /home/user/fineract log -1 --format=%H` → **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**; `git status --porcelain` → empty. Run **before** any line below was read and **before** T487's document was opened. T487 claims the same pin; this reviewer did not take that on trust. |
| Date | 2026-09-02 |
| Running instance | **None.** No Fineract process, no PostgreSQL. Every statement below is a statement about *source text this reviewer opened*, never about observed runtime behaviour. |

## Method, and the order it was done in

The order was mandatory and was followed:

1. **All derivations in §A below were made from Fineract source before T487's document was opened.**
   The scope file list, the file count, every grep, every line number in §A is this reviewer's own.
2. Only then was `docs/analysis/tierA-a1-behaviour.md` read (via `git show` from the branch, never a
   working tree).
3. Findings below compare (1) against (2).

No number in this review is inherited from T487. Where this review **agrees** with T487, the agreement
is stated together with the independent derivation that produced it — agreement derived independently
is evidence; agreement by reading is not.

**"Not found" is a statement about the search.** Every negative claim below names the command and the
file set it rests on.

---

## §A — Independent derivation, made before reading T487

Scope file list built with:

```
find fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry \
     fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry \
     fineract-core/src/main/java/org/apache/fineract/accounting/journalentry \
     -name '*.java' | sort
```

| # | What this reviewer derived | Result | Where |
|---|---|---|---|
| A-1 | Files in the three scope paths | **63** = 39 (`provider`) + 22 (`accounting`) + 2 (`core`) | `find … -name '*.java' \| wc -l` |
| A-2 | `setScale` in the 63 files | **0 occurrences** | grep over the 63-file list |
| A-3 | `.divide(` in the 63 files | **exactly 1** | `…JpaRepositoryImpl.java:981` |
| A-4 | `.round(`, `RoundingMode`, `stripTrailingZeros`, `movePointLeft/Right`, `scaleByPowerOfTen`, `toBigInteger`, `BigDecimal.valueOf`, `Math.round` in the 63 files | **0 each** | grep over the 63-file list |
| A-5 | `MathContext` in the 63 files | 2 — `…JpaRepositoryImpl.java:22` (import), `:964` (`MoneyHelper.getMathContext()`) | ditto |
| A-6 | `.floatValue()` sign tests | **exactly 4** — `AccrualBasedAccountingProcessorForLoan.java:2208`, `:2222`; `CashBasedAccountingProcessorForLoan.java:980`, `:994` | ditto |
| A-7 | **`.doubleValue()` on a money `BigDecimal`** | **1 — `SavingsTransactionDTO.java:51`**, `this.overdraftAmount.doubleValue() > 0` | ditto |
| A-8 | `Double`/`Float`/primitive `double`/`float` declarations | **1** — `JournalEntriesApiResourceSwagger.java:159`, `public Double amount;` | ditto |
| A-9 | `MoneyHelper.PRECISION` | `public static final int PRECISION = 19;` | `MoneyHelper.java:35` |
| A-10 | `getMathContext()` | `mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()))` | `MoneyHelper.java:91-93` |
| A-11 | `getRoundingMode()` throws when uninitialised | `throw new IllegalStateException("Rounding mode is not initialized for tenant: " + tenantId)` | `MoneyHelper.java:74` (signature), `:79` (throw) |
| A-12 | `amount` JPA mapping | `@Column(name = "amount", scale = 6, precision = 19, nullable = false)` | `JournalEntry.java:91-92` |
| A-13 | `amount` Liquibase DDL | `<column name="amount" type="DECIMAL(19, 6)">` + `nullable="false"` | `0001_initial_schema.xml:145-146` |
| A-14 | JPA vs Liquibase on `amount` | **They agree.** `scale=6, precision=19` ≡ `DECIMAL(19,6)` | A-12 / A-13 |
| A-15 | `transactionDate` → column | `@Column(name = "entry_date") private LocalDate transactionDate;` | `JournalEntry.java:85-86` |
| A-16 | A separate physical `transaction_date` column | exists, `date DEFAULT NULL` | `0001_initial_schema.xml:174` |
| A-17 | …and it is indexed | `<createIndex indexName="transaction_date_index" tableName="acc_gl_journal_entry">` | `0001_initial_schema.xml:7164` |
| A-18 | …and remarked abandoned | `setColumnRemarks columnName="transaction_date" remarks="Unfinished. Not maintained."` | `0025_add_audit_entries_to_journal_entry.xml:78-83` |
| A-19 | Σdebits == Σcredits enforcement | `if (creditsSum.compareTo(debitsSum) != 0) throw … DEBIT_CREDIT_SUM_MISMATCH` | `…JpaRepositoryImpl.java:323-324`, in `checkDebitAndCreditAmounts` at `:306` |
| A-20 | Call sites of that method | **three** — `:197`, `:217`, `:651` | grep `checkDebitAndCreditAmounts` in that file |
| A-21 | Balance-ish assertions on the **automatic** path | present, but they compare a **charge total to a transaction total**, not debits to credits | `AccountingProcessorHelper.java:433`, `:441`, `:1117`, `:1149`, `:1450` |
| A-22 | DB constraint tying a transaction's legs | **none found.** Where I looked: the `createTable` block for `acc_gl_journal_entry` in `0001_initial_schema.xml` in full; `grep -rn 'acc_gl_journal_entry' … \| grep -iE 'constraint\|unique\|check'` over `fineract-provider/src/main/resources/db/changelog/`. Only `addForeignKeyConstraint` (`0001:7611`, `:7617`, `:7623`, `:7629`, `:7635`, …). No `addUniqueConstraint`, no check constraint. | as stated |
| A-23 | Raw-SQL `UPDATE acc_gl_journal_entry` | **exactly 2** — `JournalEntryRunningBalanceUpdateServiceImpl.java:163`, `:211`. Repo-wide `grep -rniE 'update +acc_gl_journal_entry' --include='*.java' --include='*.xml' --include='*.sql'` (excluding `old-schema-files/`, `multi-tenant-demo-backups/`) returns the same two and nothing else. | as stated |
| A-24 | Recompute seeds from the **stored** value | `select je.organization_running_balance … where entry_date < ?` / `select je.office_running_balance …` | `…RunningBalanceUpdateServiceImpl.java:109-113`, `:131-138`, `:190-197` |
| A-25 | Recompute reach | `select MIN(je.entry_date) … where je.is_running_balance_calculated=false` | `:71-72` (org), `:92-93` (per office) |
| A-26 | **Seed queries are capped** | `sqlGenerator.limit(10000, 0)` on all three seed queries | `:113`, `:138`, `:197` |
| A-27 | Unseeded account fallback | `BigDecimal runningBalance = BigDecimal.ZERO;` then `if (map.containsKey(...))` | `:221-224` |
| A-28 | Reversal shapes **in the three scope paths** | **five** — see F-3 | `…JpaRepositoryImpl.java:370`, `:409/423-424`, `:440/456-457`, `:602/618-619`; **plus** `AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan.java:364-384` |
| A-29 | Repo-wide `setReversed`/`setReversalJournalEntry` (excl. tests) | 5 sites on `JournalEntry` (the four in `…JpaRepositoryImpl` + `AccrualWithDeferredRevenue…:377`, `:381`, `:382`); the `fineract-working-capital-loan` hits are on `…LoanTransaction`, a different type | `grep -rn 'setReversed\|setReversalJournalEntry' --include='*.java' . \| grep -v '/test/'` |
| A-30 | `CurrencyData(String code)` | sets `this.decimalPlaces = 0` | `CurrencyData.java:49`, `:52` |
| A-31 | `JournalEntryMapper` currency | `default CurrencyData mapCurrency(String c) { return new CurrencyData(c); }` | `JournalEntryMapper.java:104-105` |
| A-32 | Idempotency key is optional | `Optional.ofNullable(wrapper.getIdempotencyKey()).orElseGet(() -> getAttribute().orElseGet(idempotencyKeyGenerator::create))` | `IdempotencyKeyResolver.java:36` |
| A-33 | …and the fallback is a UUID | `return UUID.randomUUID().toString();` | `IdempotencyKeyGenerator.java:28` |

`HALF_UP` = `RoundingMode` ordinal 4 is a JDK fact, not a Fineract one, and was not re-derived from
this checkout. The ratified `(19, HALF_UP)` tenant parameter is **supported** by A-9/A-10/A-11.

---

## Findings

### F-1 — MAJOR — the floating-point inventory is incomplete: there is a **fifth** binary-float money decision, and it is on the posting path

**T487's claim.** §6.3, *"Floating point in the slice — the complete inventory"*:
`grep -rn "double \|float \|Double\|Float"` over the three scope paths *"returns **exactly one line**"*
(`JournalEntriesApiResourceSwagger.java:159`), and then *"**Four** sites convert a `BigDecimal` to a
32-bit binary `float` to decide a sign, on the posting path"* — `:2208`, `:2222`, `:980`, `:994`.
§6.3 is titled "the complete inventory".

**Independent derivation.** The four `floatValue()` sites are real and are exactly where T487 says
(A-6, opened and read). But a fifth binary-float money decision exists in the same three scope paths:

`fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/data/SavingsTransactionDTO.java:50-51`

```java
public boolean isOverdraftTransaction() {
    return this.overdraftAmount != null && this.overdraftAmount.doubleValue() > 0;
}
```

`overdraftAmount` is a `BigDecimal` (`:46`). This is a `BigDecimal` → 64-bit binary `double`
conversion used to make a money decision.

**It is on the posting path**, at eight call sites, all in the savings journal-entry processors —
`grep -rn 'isOverdraftTransaction' --include='*.java' . | grep -v '/test/'`:

- `AccrualBasedAccountingProcessorForSavings.java:60`, `:87`, `:155`, `:212`
- `CashBasedAccountingProcessorForSavings.java:59`, `:83`, `:149`, `:184`

Both files are inside the three scope paths.

**Why this is worse than the four T487 did find, not merely one more.** The four `floatValue()` sites
choose whether to take an absolute value; the value that flows onward is a `BigDecimal` and the
`multiply(new BigDecimal(-1))` is exact, as T487 correctly says. `isOverdraftTransaction()` instead
**selects which GL accounts the posting hits** — it is the branch condition on
`… .isWithdrawal() && savingsTransactionDTO.isOverdraftTransaction()` and its three siblings. A
wrong answer does not change a sign; it routes the money to a different account pair.

**Why T487's method missed it, precisely.** Neither of T487's two sweeps can see this line:

- the §6.3 type grep `"double \|float \|Double\|Float"` — `doubleValue()` has no space after
  `double` and no capital `D`;
- the §6.2 sweep `"setScale\|\.divide(\|\.multiply(\|MathContext\|RoundingMode"` — the line contains
  none of those. (The four `floatValue()` sites were caught by that sweep only incidentally, because
  they happen to contain `.multiply(`.)

This is the vocabulary-grep failure mode in its pure form. A structural sweep — every `BigDecimal`
method that can scale, round, truncate or narrow — finds it in one pass.

**What should change.** §6.3 must add `SavingsTransactionDTO.java:51` and stop saying "complete
inventory" on the strength of a word-list grep. §10 D-2 ("the Go equivalent is a sign test on an
`int64`") must be extended to cover it, and the port note must say that this one is a **routing**
decision. Under the deposit-taking activation gate the savings processors ship disabled for an NBFI
deployment, which lowers the operational urgency but not the correctness of the document.

---

### F-2 — MAJOR — the nominated headline claim, "exactly ONE rounding site on the entire posting path", is false as stated, and T487's own §2.3 says why

**T487's claim.** §6.2, bolded, and nominated by T487 itself as its single most consequential and
most falsifiable claim: *"**There is exactly ONE rounding site on the whole posting path**, and it is
`:981`"*.

**Independent derivation, and what it confirms.** Inside the three scope paths T487 is right about
the Java: `setScale` = 0 occurrences (A-2), `.divide(` = exactly 1 at `…JpaRepositoryImpl.java:981`
(A-3), `.round(`/`RoundingMode`/`Math.round`/`BigDecimal.valueOf`/`movePoint*`/`stripTrailingZeros`
= 0 each (A-4). I opened `:981` and `:964`:

```java
final MathContext mc = MoneyHelper.getMathContext();                                    // :964
final BigDecimal proRatedTax = taxDetail.getAmount().multiply(paidAmount, mc).divide(chargeAmount, mc);  // :981
```

**Where the claim breaks.** `MoneyHelper.getMathContext()` is `MathContext(19, HALF_UP)` — **19
significant digits**, not 6 decimal places (A-9, A-10). The column that receives the result is
`numeric(19,6)` — **6 decimal places** — in both the JPA mapping and the Liquibase DDL, which agree
(A-12, A-13, A-14). `JournalEntry.createNew` assigns `this.amount = amount` with no coercion
(`JournalEntry.java:125`, opened). So a pro-rated tax of, e.g., `1 × 1 ÷ 3` is carried as
`0.3333333333333333333` (19 digits) and **the INSERT is what reduces it to six**. That is a second
rounding site, it is on the posting path, and it is the one that fixes the value parity is graded on.

**T487 already contains the material that refutes its own headline.** §2.3: *"the scale actually
stored is whatever the database does … PostgreSQL rounds to the declared scale on insert"*, and
§6.2's own closing paragraph: *"a division at precision 19 can produce far more than two decimals,
and `numeric(19,6)` will keep six of them."* So this is not missing research — it is a document that
states the second rounding site in two places and then asserts in bold that there is only one. The
§6.2 heading is scoped *"inside the three scope paths"*, but the bolded sentence says *"on the whole
posting path"*, which is broader and includes the INSERT.

**Severity.** MAJOR, because this is the sentence T487 nominated, because it is a money claim, and
because a porter reading §6.2 alone would conclude that reproducing `:981` at `(19, HALF_UP)` is
sufficient for parity. It is not: the port must also reproduce the reduction to 6 decimal places at
persist time.

**What should change.** Restate as: *"exactly one rounding site in Java inside the three scope paths
(`:981`); a second, in the database, at every INSERT of a value with scale > 6."* Then say plainly
that the **stored** value — the parity target — is the `numeric(19,6)` one, and that a Go port in
integer minor units must decide explicitly where both reductions happen. The `[UNVERIFIED]` tag on
the PostgreSQL rounding semantics is correct and should stay: no database was available here either.

---

### F-3 — MAJOR — there are **five** reversal shapes in the slice, not four, and the fifth is the one that most directly contradicts append-only

**T487's claim.** §5: *"There are **four** reversal shapes in this slice and they are not consistent
with each other"*, tabulated in §5.5 as shapes 1–4.

**Independent derivation.** `grep -rn 'setReversed\|setReversalJournalEntry' --include='*.java' . |
grep -v '/test/'` (A-29) returns, on the `JournalEntry` type, T487's four sites **plus** a fifth in a
file that is inside the three scope paths:

`fineract-provider/…/journalentry/service/AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan.java:364-384`

```java
private void reverseExistingEntries(final WorkingCapitalLoan loan, final WorkingCapitalLoanTransaction txn,
        final boolean supersede) {
    …
    for (final JournalEntry journalEntry : existingEntries) {
        final JournalEntry reversalEntry = createMirrorEntry(journalEntry, transactionId, transactionDate);
        if (supersede) {
            reversalEntry.setReversed(true);                    // :377
        }
        helper.persistJournalEntry(reversalEntry);              // :378
        journalEntry.setReversed(true);                         // :381
        journalEntry.setReversalJournalEntry(reversalEntry);    // :382
        helper.persistJournalEntry(journalEntry);               // :383
    }
}
```

Called at `:273` with `supersede = true` (restatement) and at `:351` with `false`
(`postReversalJournalEntries`, the undo). `createMirrorEntry` is at `:287-294`: same
`transactionId` as the original (`:369`), `manualEntry = Boolean.FALSE` (`:290`), date =
`txn.getReversedOnDate()` or `DateUtils.getBusinessLocalDate()` (`:366`), `entityType`/`entityId`
preserved (`:291`), description copied from the original (`:291`).

**Why this is a distinct shape and not a variant of shape 3.** It is the **only** site anywhere in
the slice that writes `reversed = true` onto a **newly created** row before persisting it — a row
that is born already flagged. Every other shape flags only pre-existing rows. For a ledger the
program requires to be append-only, "a row created in the reversed state" is a materially different
behaviour from "a row later flagged", and a port that models reversal as *append a mirror, flag the
original* cannot express it at all.

**A second reason it is worth calling out.** Its own javadoc at `:354-355` says the method keeps
*"the ledger append-only (nothing is deleted)"* — while `:381-382` mutate the original. That is the
clearest in-source example of the gap between Fineract's use of "append-only" and `CLAUDE.md`'s, and
a behaviour-extraction document is exactly where it belongs.

**T487 read this file.** It appears in §3.2's processor list (*"AccrualWithDeferredRevenueAmortization…ForWorkingCapitalLoan.java (529)"*)
and in the §1.1 file count. The reversal path inside it was not reached.

**What should change.** §5 becomes five shapes; §5.5's table gains a row with a sixth column,
*"flags the mirror too?"*, which is `yes (when superseding)` for shape 5 and `no` for all others.
§10 D-4 must say a uniform Go reversal diverges from **four** of five, not three of four.

---

### F-4 — MAJOR — E-4's citation does not support its claim

**T487's claim.** §4.1, row E-4: *"Each leg's amount is non-negative | **Yes**, but only
`zeroOrPositiveAmount` | `JournalEntryCommand.java:108-111`"*.

**Independent derivation.** I opened `JournalEntryCommand.java:99-135`. Lines `108-111` are:

```java
        if (!dataValidationErrors.isEmpty()) {
            throw new PlatformApiDataValidationException("validation.msg.validation.errors.exist", "Validation errors exist.",
                    dataValidationErrors);
        }
```

— the generic error-collection throw. It contains no amount validation of any kind.

The **per-leg** non-negativity check is in `validateSingleDebitOrCredit`, `:120-126`:

```java
baseDataValidator.reset().parameter(paramSuffix + "[" + arrayPos + "].amount").value(credit.getAmount()).notNull()
        .zeroOrPositiveAmount();                                                        // :124-125
```

The nearest `zeroOrPositiveAmount` to the cited range is `:107`, and that one validates the
**top-level** `amount` — the parameter T487 itself establishes in §3.1 is *"accepted, validated, and
never used"*. So the cited lines point at neither the per-leg check nor a check that has any effect.

**The conclusion is right; only the pointer is wrong.** Per-leg amounts are validated `notNull()` and
`zeroOrPositiveAmount()`, so zero is permitted and negative is refused — exactly what E-4 says.
Graded MAJOR under this program's rule that a citation which does not say what it is cited for is a
MAJOR, because §4.1 is the table a porter transcribes and its authority is entirely its citations.

**What should change.** E-4's site becomes `JournalEntryCommand.java:120-126` (specifically
`:124-125`).

---

### F-5 — MINOR — §3.1 mis-cites the top-level amount validator by two lines

**T487's claim.** §3.1: *"validated `zeroOrPositiveAmount` (`JournalEntryCommand.java:105`)"*.

**Independent derivation.** `:105` is `}` (closing an inner `for`). The `zeroOrPositiveAmount` call on
the top-level `amount` is at `:107`:
`baseDataValidator.reset().parameter("amount").value(this.amount).ignoreIfNull().zeroOrPositiveAmount();`

**What should change.** `:105` → `:107`. Worth noting the citation also omits `.ignoreIfNull()`, which
matters: the top-level `amount` is optional as well as unused.

---

### F-6 — MINOR — §6.2 says its own grep returns six lines; it returns seven

**T487's claim.** §6.2: *"The sweep: `grep -rn "setScale\|\.divide(\|\.multiply(\|MathContext\|RoundingMode" --include='*.java'`
over the three scope paths. **Complete output, six lines, all of them:**"*, followed by a five-row table.

**Independent derivation.** I ran that exact pattern over the three scope paths. It returns **7
lines** (`… | wc -l` → 7): `:22`, `:964`, `:981`, `AccrualBased…:2208`, `:2222`, `CashBased…:980`,
`:994`. The five-row table is right — it collapses the two `floatValue` pairs into one row each — but
the line count is stated wrong.

**Why it is worth a finding at all.** §6.2's entire evidentiary weight is *"this grep's output is
complete, and here it is"*. A stated count that does not match the stated command undermines the one
thing that section is asking the reader to accept without re-running it. (I re-ran it; the table's
**content** is correct and complete for that pattern. Its incompleteness as a *rounding* sweep is F-1
and F-2, which are different problems.)

**What should change.** "six lines" → "seven lines", or drop the count and keep the table.

---

### F-7 — MINOR — §2.5's G-12 mechanism omits the 10,000-row seed cap, which is a stronger drift mechanism than the three it lists

**T487's claim.** §2.5 identifies three properties that let a stored running balance drift and stay
drifted: the seed from the stored value (`:110-116`, `:134-141`), the reach limit
(`:72-73`, `:93-94`), and the recompute-time classification join (`:225-242`). I confirmed all three
independently (A-24, A-25, and `:225-242` read).

**Independent derivation of a fourth.** All three seed queries are capped:

```
:113   + "group by je.id order by je.entry_date DESC " + sqlGenerator.limit(10000, 0);
:138   + "group by je.id order by je.entry_date DESC " + sqlGenerator.limit(10000, 0);
:197   + "group by je.id order by je.entry_date DESC " + sqlGenerator.limit(10000, 0);
```

and an account absent from the seed map does not fail — it silently starts from zero
(`:221-224`, opened):

```java
BigDecimal runningBalance = BigDecimal.ZERO;
if (runningBalanceMap.containsKey(entry.getGlAccountId())) {
    runningBalance = runningBalanceMap.get(entry.getGlAccountId());
}
```

So once a tenant's chart of accounts × distinct `entry_date` combinations before `entityDate`
exceeds 10,000 rows, some accounts are re-seeded from **zero** rather than from their prior balance,
and the recompute writes that as the running balance. This is a size-dependent correctness cliff with
no error and no log line, and it strengthens rather than contradicts T487's and `A2-29`'s conclusion
that the stored value is a second source of truth.

`[UNVERIFIED: no database was available; whether any real tenant crosses 10,000 seed rows is a
deployment fact, not a source fact. The cap and the zero fallback are source facts, read at the lines
above.]`

**What should change.** Add the cap as a fourth mechanism in §2.5, and add it to whatever evidence
G-12 carries. A Go port that derives balances (as `CLAUDE.md` requires) does not inherit this bug —
which is itself an argument for the derived-balances non-negotiable, and worth saying in §10.

---

### F-8 — MINOR — three of the thirteen `[UNVERIFIED]` items are settleable from source; settled here

T487's §11 is, on the whole, honest and well-drawn — items 1, 2, 3, 4, 6, 7, 11 and 13 are correctly
tagged, and item 7's distinction (*"nothing would catch it" is not "it happens"*) is exactly right.
Three are over-strong:

| §11 item | T487 | Settled here, from source |
|---|---|---|
| **12** — *"Whether `JournalEntriesApiResourceSwagger.java:159`'s `Double amount` reaches any runtime path. It was read, not traced."* | untraced | **Settled: it does not.** `grep -rn 'JournalEntriesApiResourceSwagger' --include='*.java' .` (excl. `/build/`) returns the declaration (`:31`, a package-private `final class` with a private constructor at `:33`) and five references, **all** inside `@Schema(implementation = …)` / `@RequestBody` annotations in `JournalEntriesApiResource.java` (`:111`, `:175`, `:202`, `:229`, `:230`). It is never instantiated, never deserialized into, never returned. The `Double` is OpenAPI metadata. It is still worth recording that the **published contract** therefore types `amount` as a JSON number — a `CLAUDE.md` "no float in any monetary API field" concern at the documentation surface, if not at runtime. |
| **8** — *"Whether `?runningBalance=true` … is reachable on PostgreSQL. Did not re-read the `/journalentries` SQL for the same defect."* | untraced | **Settled: the defect is absent.** `grep -niE 'group by.*desc\|order by.*group'` over `JournalEntryReadPlatformServiceImpl.java` returns nothing. The MySQL-only `group by … desc` that `A2-29` found in the `/glaccounts` variant does not appear in this file. (Whether the endpoint *executes* is still unverifiable — no instance — but the specific defect named is not there.) |
| **5** — *"Whether anything still writes `created_date` / `lastmodified_date`. The whole checkout was **not** swept."* | unswept | **Swept here.** `grep -rn '"created_date"\|lastmodified_date' --include='*.java' .` (excl. `/build/`, tests) returns hits only on **other** tables — `fineract-savings` (`SavingsOfficerAssignmentHistory.java:55`, `:59`; `DepositAccountOnHoldTransaction.java:59`; `SavingsAccountTransaction.java:112`) and `fineract-rates` (`FloatingRatesReadPlatformServiceImpl.java:105`). Nothing maps or writes `acc_gl_journal_entry.created_date` / `.lastmodified_date`; `JournalEntry.java` declares no such field. |

**What should change.** Fold the three answers in and drop the tags. This is a minor finding: an
`[UNVERIFIED]` that a reviewer can settle costs a little of the document's authority, but T487
over-tagging is a far better failure than under-tagging, and the other ten are properly drawn.

---

### F-9 — MINOR — E-2's "once" is loose, and the third call site is not the manual path

**T487's claim.** §4.1 row E-2: *"**Yes**, once, at the boundary | `checkDebitAndCreditAmounts`,
`:306-326`; called from `validateBusinessRulesForJournalEntries:651` and again inside the
accounting-rule branches at `:197` and `:217`"*.

**Independent derivation.** One method (`:306`, body `:308-325`, the comparison at `:323-324`), and
**three** call sites — `:197`, `:217`, `:651` (A-19, A-20). So "once" and the site list disagree
within the same table cell; the site list is correct and complete, and this reviewer found no fourth
call site (`grep -n 'checkDebitAndCreditAmounts'` over that file).

One substantive addition: `:651` sits inside `validateBusinessRulesForJournalEntries`, which is
called from **`:157`** (`createJournalEntry`, Path A) **and `:724`** (the opening-balance path, which
T487 itself calls Path C). So the check covers Path A and Path C, not "the manual path" alone. Both
create legs with `manualEntry = true`, so the sentence is defensible — but a porter reading "manual
path only" may not realise Path C is included.

**What should change.** "once" → "by one method, at three call sites"; and name Path C explicitly.

---

## Claims verified and CONFIRMED by independent derivation

Stated separately because agreement that was derived is evidence, and this is what I actually
achieved on each — **confirmed**, not merely *unable to falsify*:

| T487 claim | My derivation | Verdict |
|---|---|---|
| Pin `426a2354…` | ran `git log -1 --format=%H` myself, before reading the doc; `git status --porcelain` empty | **CONFIRMED** |
| §1.1 — 63 files across three paths (39/22/2) | A-1, my own `find` | **CONFIRMED** |
| §6.2 — `setScale` appears nowhere in the three scope paths | A-2, 0 occurrences | **CONFIRMED** |
| §6.2 — `:981` is the only `.divide(` in the scope paths, at `MoneyHelper.getMathContext()` | A-3, A-5; both lines opened | **CONFIRMED** |
| §6.3 — four `floatValue() < 0` sign tests at `:2208`, `:2222`, `:980`, `:994` | A-6; all four lines opened; and they *are* on the posting path | **CONFIRMED as to those four** — but not as a *complete* inventory (F-1) |
| §6.3 — the `multiply(new BigDecimal(-1))` is exact, so no precision is lost in the amount | `new BigDecimal(int)` is an exact construction; the value flowing on is `BigDecimal` | **CONFIRMED** |
| §6.1 — `PRECISION = 19` at `:35`; `getMathContext()` at `:91-93`; `getRoundingMode()` throws if uninitialised | A-9, A-10, A-11; `:35`, `:91-93`, `:74`/`:79` opened | **CONFIRMED** |
| §2.3 — `BigDecimal` at `DECIMAL(19,6)`, JPA and Liquibase **agree**, and nothing scales to the minor unit before persisting | A-12, A-13, A-14; plus `JournalEntry.java:125` `this.amount = amount` opened | **CONFIRMED** |
| §2.2 — the `transaction_date` trap: `transactionDate` → `entry_date`; separate unmapped indexed `transaction_date` remarked *"Unfinished. Not maintained."* | A-15, A-16, A-17, A-18; all four lines opened | **CONFIRMED** |
| §4.1 E-9 / §2.4 — no DB constraint ties a transaction's legs | A-22, with the search stated | **CONFIRMED**, to the extent a negative can be — the search is stated and bounded |
| §4.1 E-8 / §4.2 — no Σdebits==Σcredits check on the automatic path; balance holds because the balancing leg *is* the running sum | A-21: the automatic-path assertions I found (`AccountingProcessorHelper:433`, `:441`, `:1117`, `:1149`, `:1450`) compare a **charge total to a transaction total**, never debits to credits — which is precisely what T487 says at E-10/E-11 and §4.2 | **CONFIRMED**, and T487 is more careful here than a casual reading of "no check on the automatic path" would suggest |
| §4.3 / §5 — reversal MUTATES the original row | A-28, A-29; `setReversed(true)` + `setReversalJournalEntry(...)` + `persistJournalEntry(journalEntry)` opened at `:423-426`, `:456-459`, `:618-621` | **CONFIRMED** |
| §5.5 — shapes 1–4 differ in txn id / `manualEntry` / date / entity linkage / whether the original is flagged | all four blocks opened (`:359-378`, `:402-427`, `:436-459`, `:596-621`); every cell in T487's table matched what I read | **CONFIRMED** — the four described are described correctly; the count is wrong (F-3) |
| §2.5 / G-22 — exactly two `UPDATE acc_gl_journal_entry`, at `:163` and `:211` | A-23, incl. a repo-wide sweep over `.java`/`.xml`/`.sql` | **CONFIRMED for raw SQL.** See the caveat below — it is not true of the ORM |
| §2.5 / G-12 — the recompute **seeds from the stored value** and its reach is bounded by `MIN(entry_date) WHERE not calculated` | A-24, A-25; `:71-72`, `:92-93`, `:109-113`, `:131-138` opened | **CONFIRMED** |
| §7.3 — `JournalEntryMapper` builds `CurrencyData` with `decimalPlaces = 0` | A-30, A-31; `CurrencyData.java:49`/`:52` and `JournalEntryMapper.java:104-105` opened | **CONFIRMED** — zero minor units for MNT on that read path |
| §4.4 — `Idempotency-Key` is optional in the oracle | A-32, A-33; `IdempotencyKeyResolver.java:36`, `IdempotencyKeyGenerator.java:28`, `application.properties:179` opened | **CONFIRMED**, and T487's conclusion that this is a deliberate divergence (unvectorable) is sound |
| §6.4 — no scale-sensitive `BigDecimal.equals` money comparison in the scope paths | `grep -n '\.equals(' JournalEntry.java` → only `:150`, `:154`, both `Integer.equals` on `type` | **CONFIRMED** for that file, as T487 scoped it |

**One qualification on "exactly two `UPDATE`s" (§2.5, G-22).** The claim is true and I confirmed it
**about raw SQL**. It is not true about the statements the database actually receives: the reversal
paths mutate managed JPA entities and call `helper.persistJournalEntry(journalEntry)`
(`AccountingProcessorHelper.java:1414`, a `saveAndFlush`), so Hibernate issues further `UPDATE`s
against `acc_gl_journal_entry` that no grep for the literal string can see. T487 does not claim
otherwise — §4.3 explicitly names the two ORM-mutable fields — but G-22's wording, *"the only two
`UPDATE`s against the table"*, invites the reading that a posted row is otherwise never updated, and
it is. Recorded here as a qualification rather than a finding; if G-22 is ratified into DEC-2 as
`§4.4a`, the ORM-issued updates belong in that text. **I have not amended DEC-2 or G-22.**

---

## G-12 / G-22 and DEC-2

I re-derived the mechanism behind both gates from source (A-23 … A-27) **before** reading T487's
§2.5 or `.softhouse/gates.md`. My reading and T487's agree on every point I checked, and I add one
mechanism T487 missed (F-7, the 10,000-row seed cap).

`docs/adr/DEC-2-gl-accounting-adapter.md` §4.4 row `I-3` states that G-12 is open on this exact
invariant and that DEC-2 does not resolve it. **I found no contradiction between T487's document and
any ratified DEC.** I have not amended DEC-2, the frozen adapter contract, or any gate; nothing in
this review takes a position on how G-12 or G-22 should be resolved — both remain `user`/driver
gates.

---

## Citation spot-check

Every line below was opened at the pin with `sed -n 'Np' FILE` and read.

**Sample: 52 discrete `FILE:LINE` citations**, drawn across all thirteen sections and both the Java
and Liquibase sources — `JournalEntry.java` (6), `…JpaRepositoryImpl.java` (14),
`AccountingProcessorHelper.java` (4), `JournalEntryRunningBalanceUpdateServiceImpl.java` (7),
`JournalEntryReadPlatformServiceImpl.java` (2), `JournalEntryRepository.java` (3),
`JournalEntryCommand.java` (2), `JournalEntryInvalidException.java` (4),
`JournalEntryJsonInputParams.java` (1), `JournalEntryMapper.java` (1), `MoneyHelper.java` (4),
`CurrencyData.java` (2), `MathUtil.java` (2), `IdempotencyKeyResolver.java` (1),
`IdempotencyKeyGenerator.java` (1), `JournalEntriesApiResourceSwagger.java` (1),
`application.properties` (1), `0001_initial_schema.xml` (5), `0025_add_audit_entries_to_journal_entry.xml` (2).

**Wrong: 2.** `JournalEntryCommand.java:108-111` (F-4, MAJOR — cited for a per-leg non-negativity
check, contains a generic throw) and `JournalEntryCommand.java:105` (F-5, MINOR — off by two).

**Rate: 2 / 52 = 3.8% incorrect; 96.2% of the sampled citations said what they were cited for.**

Both failures are in the same file and neither changes a conclusion. Multi-line range citations
(e.g. `:110-132`) were counted as correct when the cited construct falls inside the range, even where
an individual line within it is blank; I did not count those as failures.

---

## Verdict

**ACCEPT WITH CONDITIONS.**

This is a strong, honest document. Its method is right — it states its greps, it distinguishes source
facts from runtime claims, its `[UNVERIFIED]` register is mostly well-drawn, and it repeatedly
declines to over-claim (§11 item 7 and §4.2's "nothing would catch it" vs "it happens" are model
formulations). Its citation accuracy at 96.2% on a 52-citation sample is high. Nothing in it
contradicts a ratified DEC, and its §2.5 supplies real independent mechanism for G-12/G-22. It should
not be redone.

But three MAJOR money/non-negotiable claims are wrong or incomplete, and two of them are in the
sections a porter will lean on hardest. Conditions for acceptance:

1. **F-1** — add `SavingsTransactionDTO.java:51` (`doubleValue() > 0`) to §6.3; the count of binary-float
   money decisions on the posting path is **five**, not four, and this one routes rather than negates.
   Replace the vocabulary grep with a structural one over `BigDecimal`'s scaling/narrowing methods and
   re-run it before re-asserting "complete inventory". Extend §10 D-2.
2. **F-2** — retract the bolded "exactly ONE rounding site on the whole posting path". Restate as one
   Java site in scope plus the `numeric(19,6)` reduction at INSERT, and name the **stored** value as
   the parity target. §6.2 and §2.3 must stop contradicting each other.
3. **F-3** — §5 and §5.5 become **five** reversal shapes; add
   `AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan.java:364-384`,
   including its `supersede` flag, which is the only site that creates a row already flagged
   `reversed = true`. Correct §10 D-4 to "four of five".
4. **F-4, F-5** — fix the two `JournalEntryCommand.java` citations (`:108-111` → `:120-126`;
   `:105` → `:107`).
5. **F-6, F-7, F-8, F-9** — correct the line count in §6.2; add the 10,000-row seed cap to §2.5 and to
   the G-12 evidence; fold in the three settled `[UNVERIFIED]` answers; tighten E-2's "once".

None of these requires a new run. All are edits to `docs/analysis/tierA-a1-behaviour.md` on T487's
branch, and none of them touches a DEC, the frozen contract, `nexus/`, or a vector.

---

## Claims I could neither confirm nor falsify

Stated separately, because being unable to falsify is not confirming:

1. **That PostgreSQL rounds (rather than truncates or errors) when a `BigDecimal` of scale > 6 is
   inserted into `numeric(19,6)`.** F-2 rests on *some* reduction happening at the column; which
   rounding rule applies is standard `numeric` semantics, not something observable here. **No
   PostgreSQL instance in this session.** The direction of F-2 does not depend on which — any of the
   three makes it a second site — but the parity vectors will depend on it, and it must be measured
   against the live oracle before any `:981` vector is graded.
2. **Whether `MoneyHelper` is initialised to `HALF_UP` (ordinal 4) on the reference instance.** I
   confirmed `PRECISION = 19` is a compile-time constant and that `getRoundingMode()` throws when
   uninitialised. What value `initializeTenantRoundingMode` is actually called with is a deployment
   fact. **No running instance.**
3. **Whether any automatic posting path ever actually emits an unbalanced transaction.** I confirmed
   (A-21, A-22) that nothing in the slice and nothing in the schema would catch one. That is not
   evidence that one occurs. T487 draws the same distinction at §11 item 7 and is right to.
4. **Whether the 10,000-row seed cap (F-7) is ever crossed in practice.** Source fact: the cap and the
   zero fallback. Deployment fact: whether any tenant exceeds it. **No database.**
5. **T487's §3.1 claim that `Long.parseLong(uniqueVal)` in `generateTransactionId` can overflow.** I
   read `:690` and the arithmetic is as described, but I did not sample id ranges and did not execute
   it. T487 tags this `[UNVERIFIED]` and that tag is correct.
6. **Whether the `?runningBalance=true` endpoint executes on PostgreSQL.** I settled that the specific
   MySQL-only `group by … desc` defect is absent from `JournalEntryReadPlatformServiceImpl.java`
   (F-8). Whether the endpoint runs clean is a runtime question and stays open.
7. **T487's §2.1 column-by-column table** was spot-checked, not exhaustively re-derived. The 11 rows I
   opened were all correct; the remaining rows I neither confirmed nor falsified.
8. **Everything `A2-29` measured against a live oracle**, which T487 cites as *A2-29 measured it*. I
   did not re-run it and take no position on it; T487's handling (citing, never re-asserting as its
   own observation) is the correct one.

---

*Reviewer T490. No Go was written, no vector created, no DEC or contract amended, nothing under
`nexus/` touched, and `/home/user/fineract` was read only — `git status --porcelain` was empty at the
start and no checkout was changed.*
