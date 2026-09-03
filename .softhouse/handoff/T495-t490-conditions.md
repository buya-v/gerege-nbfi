# T495 — handoff

| | |
|---|---|
| Task | Apply `T490`'s review conditions to `docs/analysis/tierA-a1-behaviour.md` (`T487`, Tier A · slice A1) |
| Branch | `softhouse/T495-t490-conditions`, branched from `origin/softhouse/T487-a1-journalentry-behaviour` @ `0b2545c1` |
| Output | `docs/analysis/tierA-a1-behaviour.md`, edited **in place**; this handoff |
| Fineract pin | `426a23544e8426a38ae43ae404670a0a7e85b9eb` — **verified by this worker** with `git -C /home/user/fineract log -1 --format=%H` **before any line below was read**; `git status --porcelain` empty at start and at finish. Read-only; no checkout changed. |
| Running instance | **None.** No Fineract, no PostgreSQL. Every claim below is about source text opened at the pin. |

## Method — this worker re-derived before applying

The task brief was explicit that this program has twice had a reviewer's patch refuted by the worker
asked to apply it. So: **every one of `T490`'s nine findings was re-derived from the pinned source
before it was written into the document**, and the derivations are this worker's own, not `T490`'s.
Two of `T490`'s statements did not survive that check and are recorded as refutations below (one
sub-claim, one count). Neither changes a finding's direction; both are recorded in the document
because the rule that a citation must say what it is cited for applies to reviewers too.

Nothing outside the target document and this handoff was touched. **No gate file, no DEC, no frozen
contract, no vector, no Go, nothing under `nexus/`.**

## Per-finding disposition

| Finding | Severity | Disposition | Evidence this worker opened |
|---|---|---|---|
| **F-1** — fifth binary-float money site | MAJOR | **APPLIED** | `SavingsTransactionDTO.java:46` (`private final BigDecimal overdraftAmount`), `:50-51` (`return this.overdraftAmount != null && this.overdraftAmount.doubleValue() > 0;`). Eight call sites confirmed by `grep -rn 'isOverdraftTransaction' --include='*.java' . \| grep -v /test/ \| grep -v /build/`: `AccrualBasedAccountingProcessorForSavings.java:60`, `:87`, `:155`, `:212`; `CashBasedAccountingProcessorForSavings.java:59`, `:83`, `:149`, `:184`. Each is `…getTransactionType().isWithdrawal() && …isOverdraftTransaction()` or a sibling — i.e. a **routing** condition, confirming `T490`'s point that this is worse than the four sign tests. §6.3 rewritten around a structural sweep; §10 D-2 extended. |
| **F-2** — the "exactly ONE rounding site" headline | MAJOR | **APPLIED** | `MoneyHelper.java:35` (`PRECISION = 19`), `:91-93` (`new MathContext(PRECISION, getRoundingMode())`); `JournalEntry.java:91` (`@Column(name = "amount", scale = 6, precision = 19, nullable = false)`), `:125` (`this.amount = amount;` — no coercion, inside the `:113-137` constructor); `0001_initial_schema.xml:145` (`<column name="amount" type="DECIMAL(19, 6)">`). JPA and Liquibase agree. `…JpaRepositoryImpl.java:964`, `:981` re-read: `proRatedTax` flows into `ChargeTaxDetailDTO` at `:982`. Headline retracted in place; §6.2 now names **R-1** (Java, 19 sig-digits) and **R-2** (the INSERT, 6 decimal places) and states the stored value is the parity target. §2.3 and §6.2 now agree instead of contradicting. |
| **F-3** — five reversal shapes, not four | MAJOR | **APPLIED** | `AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan.java:364-385` read in full, plus `:51`, `:265-294`, `:349-362`. `:377` `reversalEntry.setReversed(true)` **before** `:379` persists it; `:381-383` flag and persist the original. Entry points `:273` (`supersede=true`, restate) and `:351` (`false`, undo). `createMirrorEntry` `:287-294`. New §5.5; old §5.5 renumbered §5.6 with a sixth column *"Flags the MIRROR too?"*; §10 D-4 → "four of five". |
| **F-4** — E-4's citation | MAJOR | **APPLIED** | `JournalEntryCommand.java:95-127` read in full. `:108` blank; `:109-112` the generic `if (!dataValidationErrors.isEmpty()) throw new PlatformApiDataValidationException(…)`. Per-leg check is `validateSingleDebitOrCredit` `:120-126`, the amount rule at `:124-125` (`notNull().zeroOrPositiveAmount()`). E-4's site corrected; a note under §4.1 records what the old citation actually pointed at. |
| **F-5** — `:105` → `:107` | MINOR | **APPLIED** | Same read. `:105` is `}` closing the inner `for` at `:101-104`. `:107` is `baseDataValidator.reset().parameter("amount").value(this.amount).ignoreIfNull().zeroOrPositiveAmount();`. `T490`'s note that `.ignoreIfNull()` matters is right and is now in the document — the top-level `amount` is optional as well as unused. |
| **F-6** — "six lines" → seven | MINOR | **APPLIED** | Ran T487's pattern verbatim over the three scope paths: 7 lines (`…JpaRepositoryImpl.java:22`, `:964`, `:981`; `AccrualBased…:2208`, `:2222`; `CashBased…:980`, `:994`). Table content unchanged and correct. |
| **F-7** — 10,000-row seed cap (G-12 evidence) | MINOR | **APPLIED** | `JournalEntryRunningBalanceUpdateServiceImpl.java:113`, `:138`, `:197` all end `+ sqlGenerator.limit(10000, 0)`; `:220-224` `BigDecimal runningBalance = BigDecimal.ZERO; if (runningBalanceMap.containsKey(…))`. Added as a **fourth** drift mechanism in §2.5, folded into the G-12 evidence paragraph, added to §10 D-7 and as capture-plan probe 9. **Tagged `[UNVERIFIED]`** for whether any tenant crosses it — a deployment fact. |
| **F-8** — three settleable `[UNVERIFIED]`s | MINOR | **APPLIED, with one sub-claim REFUTED** | Items 12 and 8 settled as `T490` said, re-derived. **Item 5: conclusion confirmed, `T490`'s stated evidence refuted** — see below. Item 2 additionally *sharpened* (round vs truncate vs error), which `T490` itself flagged as the thing the vectors depend on. |
| **F-9** — E-2's "once" | MINOR | **APPLIED** | `grep -n 'checkDebitAndCreditAmounts\|validateBusinessRulesForJournalEntries'` over `…JpaRepositoryImpl.java`: method at `:306`, called `:197`, `:217`, `:651`; `validateBusinessRulesForJournalEntries` at `:626`, called `:157` and `:724`. `:714-730` read — `:724` is inside `defineOpeningBalance`, i.e. **Path C**. E-2 restated as "one method, three call sites, Path A **and** Path C". |
| **Carry** — F-7 evidence for gate G-12 | — | **CARRIED** into §2.5's G-12 paragraph and §10 D-7. **`.softhouse/gates.md` NOT edited** — see "For the driver" below. |
| **Carry** — "exactly two `UPDATE`s" qualification | — | **CARRIED** as C-10 | `AccountingProcessorHelper.java:1414-1416` — `persistJournalEntry` is `glJournalEntryRepository.saveAndFlush(journalEntry)`. Recorded as a block quote in §2.5, echoed in §4.3 and in the G-22 paragraph. Explicitly **not** an amendment to G-22 or DEC-2. |

## Is there a SIXTH binary-float money site? **No.**

This is the question the brief asked to be answered by escaping `T487`'s vocabulary, and the answer
is negative **on a search whose bounds are stated in the document (§6.3) and here**.

**Where this worker looked.** A *structural* sweep — not a word list — over **all 63 files** of the
three scope paths (file list rebuilt with `find` at the pin; 39 + 22 + 2, independently confirming
`T487`'s and `T490`'s count):

1. every `BigDecimal` narrowing/stringifying method: `doubleValue`, `floatValue`, `intValue`,
   `longValue`, `shortValue`, `byteValue`, `intValueExact`, `longValueExact`, `toBigInteger`,
   `toBigIntegerExact`, `toPlainString`;
2. every scaling/rounding method: `setScale`, `.round(`, `.divide(`, `MathContext`, `RoundingMode`,
   `stripTrailingZeros`, `movePointLeft/Right`, `scaleByPowerOfTen`, `.ulp(`, `.precision()`,
   `.scale()`;
3. word-bounded `\b(double|float|Double|Float)\b`, plus `new BigDecimal(`, `BigDecimal.valueOf`,
   `\bMath\.`, `.compareTo(`, `.equals(`.

Plus the five out-of-scope files this document cites as posting-path dependencies —
`MoneyHelper.java`, `CurrencyData.java`, `MathUtil.java`,
`AbstractAuditableWithUTCDateTimeCustom.java`, `closure/domain/GLClosure.java`. **Zero float hits in
all five.**

**What it returned and why each non-hit was excluded** (all in §6.3):

- `intValue()` — six hits, all `Long`/`Integer` ids or type codes. The nearest to a money context is
  `AccrualBasedAccountingProcessorForLoan.java:1850`, `debitEntry.getKey().intValue()` over a
  `Map.Entry<Integer, BigDecimal>` — the **key**, an accounting-type code; the money is
  `debitEntry.getValue()`, passed on as a `BigDecimal`. Opened `:1838-1856` to confirm.
- `new BigDecimal(...)` — **16** hits, every one `new BigDecimal(int)` (`0` accumulators and `-1`
  sign flips), which is exact. **`new BigDecimal(double)` — the classic float-contamination bug —
  appears nowhere in the scope paths.**
- `BigDecimal.valueOf` — zero. `Math.` — zero.
- `compareTo` — every occurrence is `BigDecimal` vs `BigDecimal.ZERO` or vs another `BigDecimal`.
- `.equals(` — no `BigDecimal.equals` anywhere in the 63 files. The one that looks closest,
  `…JpaRepositoryImpl.java:1044` `this.currency.equals(copy.currency)`, is `String` equality —
  `OfficeCurrencyKey` declares `final String currency` at `:1032` (opened `:1028-1050`).

**What the search does NOT cover, stated so no one is misled:** the portfolio-side producers that
populate `SavingsTransactionDTO` and `ChargePaymentDTO`. Those live in Tier B contexts outside the
one-context scope guard and were deliberately not entered. A float introduced there would be
invisible to this sweep, and the document carries that as an explicit `[UNVERIFIED]`.

**A worthwhile secondary finding.** In the *same* savings files, three lines from the
`isOverdraftTransaction()` call sites, the code makes the same kind of decision **exactly**:
`amount.subtract(overdraftAmount).compareTo(BigDecimal.ZERO) > 0` at
`AccrualBasedAccountingProcessorForSavings.java:61`, `:88`, `:156`, `:213` and
`CashBasedAccountingProcessorForSavings.java:60`, `:84`, `:150`, `:185`. So `:51`'s
`doubleValue()` is an outlier inside its own call sites, not a house style — which is the strongest
available argument that the port must not carry it forward. This is in §6.3.

## Refutations — what did NOT survive re-derivation

Both are against `T490`, both are recorded in the document, and **neither reverses a finding**.

1. **`T490` F-8, item 5 — its stated evidence does not return what it says.** The review settles
   *"whether anything still writes `created_date`/`lastmodified_date`"* by asserting that
   `grep -rn '"created_date"\|lastmodified_date' --include='*.java' .` (excl. `/build/`, tests)
   *"returns hits only on other tables — `fineract-savings` … and `fineract-rates`"*, listing five
   hits. **Run at the pin it returns roughly forty-five hits across at least ten modules**,
   including **`fineract-core`'s `AbstractAuditableCustom.java:46` and `:52`** — a
   `@MappedSuperclass` that maps exactly those two column names. A reader auditing `T490`'s evidence
   would find a core audit superclass mapping `created_date` and could reasonably conclude the item
   was *not* settled.

   **The conclusion is nonetheless correct**, by a stronger and positive route this worker
   established instead: `JournalEntry.java:41` declares
   `public class JournalEntry extends AbstractAuditableWithUTCDateTimeCustom<Long>` — a
   **different** superclass — whose four audit columns are the constants at
   `AbstractAuditableWithUTCDateTimeCustom.java:55`, `:59`, `:63`, `:67`, resolving to
   `created_by` / `created_on_utc` / `last_modified_by` / `last_modified_on_utc`
   (`AuditableFieldsConstants.java:28-31`). `JournalEntry` declares no `created_date` or
   `lastmodified_date` field of its own. Item 5 is settled on that basis, and the refutation is
   recorded inline in §11 item 5.

2. **`T490` A-29 / F-3 — "the four in `…JpaRepositoryImpl`" is three.** Re-running
   `grep -rn 'setReversed\|setReversalJournalEntry' --include='*.java' . | grep -v /test/ | grep -v /build/`,
   the `JournalEntry` flagging sites in that file are **three locations** — `:423-424`, `:456-457`,
   `:618-619` — not four. `:370` (which `T490`'s A-28 uses as a shape anchor) is not a flagging
   site, and its absence independently confirms §5.2's claim that shape 2 flags nothing. With the
   working-capital site that is four locations across five shapes. **F-3's substance — that a fifth
   shape exists, where it is, and why it matters — is correct and is applied in full.** Recorded in
   §5's correction note.

## What this worker did NOT do

- Did not redo `T487`. `T490` was explicit the document should not be redone, and re-derivation
  confirmed its method, its 63-file scope count, its `setScale` = 0 finding, its `:981`-is-the-only-
  `.divide(` finding, and its `transaction_date` trap. Every edit is in place.
- Did not edit `.softhouse/gates.md`, any DEC, the frozen contract, any vector, any Go, or anything
  under `nexus/`.
- Did not run Fineract or PostgreSQL — neither exists in this session, and every runtime-shaped
  claim in the document is worded as a claim about code that was read.

## For the driver — things that belong somewhere this worker may not write

1. **G-12 evidence.** The 10,000-row seed cap (`JournalEntryRunningBalanceUpdateServiceImpl.java:113`,
   `:138`, `:197`) with its silent `BigDecimal.ZERO` fallback (`:221-224`) is a **fourth** drift
   mechanism and, for gate purposes, the strongest of them: it needs no prior corruption, only a
   large enough ledger, and it fails with no exception and no log line. It is in the document at
   §2.5 and §10 D-7. **It should be filed against G-12 in `.softhouse/gates.md`; this worker did not
   edit that file.**
2. **G-22 wording.** If G-22 is ratified into DEC-2 as a normative `§4.4a`, the text should say the
   two raw-SQL `UPDATE`s are the only *raw-SQL* ones — Hibernate issues further `UPDATE`s on the
   reversal paths via `saveAndFlush` (`AccountingProcessorHelper.java:1414-1416`) that no string
   grep can see. Carried in the document as a qualification (§2.5, §4.3); **not** an amendment.
3. **Non-negotiable guard / `.softhouse/patterns.md`.** The float guard should match
   `\.(float|double)Value\s*\(` on money types rather than a `double |float |Double|Float` word
   list. `SavingsTransactionDTO.java:51` is precisely what the word list misses, and it took an
   independent reviewer to find it. Recorded as backlog **B-11** in §12; no guard or config edited.
4. **Capture-plan blocker.** New probe **1a** in §10: *does PostgreSQL round, truncate or error on
   insert into `amount numeric(19,6)`, and under which rule?* It cannot be answered from source, it
   fixes the value every parity comparison on this table is graded against, and **no `:981` vector
   should be graded before it is answered.** `T490` reached the same conclusion independently.
5. **B-12** (new): the oracle's published OpenAPI schema types `amount` as a JSON number
   (`JournalEntriesApiResourceSwagger.java:159`). Unreachable at runtime, but the port's own OpenAPI
   document will diverge from the oracle's at that field, and `CLAUDE.md` forbids float in "any
   monetary … API field". Worth knowing before anyone generates a client from the oracle's schema.

## Document changes, by section

`§0.1` new — a corrections register (C-1 … C-10) naming every changed claim and its evidence, so the
document does not quietly change its mind · `§2.3` INSERT named as the second reduction, and the
`[UNVERIFIED]` sharpened to round/truncate/error · `§2.5` seed cap as a fourth drift mechanism, the
raw-SQL qualification, G-12 and G-22 paragraphs updated · `§3.1` `:105` → `:107` with
`.ignoreIfNull()` · `§4.1` E-2 and E-4 corrected, with a note on what the old E-4 citation pointed at
· `§4.3` `saveAndFlush` note, and Fineract's own narrower definition of "append-only" quoted from
`…ForWorkingCapitalLoan.java:354-356` · `§5` four → five with the re-derivation · `§5.5` new (shape
5) · `§5.6` the table, with a new column · `§6.2` headline retracted and restated as R-1/R-2; line
count fixed · `§6.3` rebuilt on a structural sweep; fifth site added; the sixth-site search and its
boundary stated · `§10` D-1, D-2, D-4, D-7 and capture-plan items 1a, 8, 9 · `§11` items 5, 8, 12
settled, item 2 sharpened, intro updated · `§12` B-11, B-12 · `§13` every newly opened file and line
range added.
