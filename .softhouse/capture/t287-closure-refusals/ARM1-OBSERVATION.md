# T287 ARM 1 — future-dated journal entry refusal, RAW OBSERVED FORM

Captured from the live reference oracle (Fineract) on **2026-08-23 UTC**, tenant **`gerege`**
(tenant 2, `Asia/Ulaanbaatar`, `HALF_UP`), database **`fineract_gerege`** on PostgreSQL 18.3.

**This is a raw capture directory, not a vector.** Nothing here is contract-shaped, nothing was
promoted into `.softhouse/vectors/ledger/`, and no pin was touched. Promotion is a separate task.

---

## 1. The citation, re-derived BEFORE anything was sent

`capabilities-ledger.json` and the `conformance.sh` reason line both cite
`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:626-640`. Opened in the pinned checkout
`/Users/buv/fineract` at commit `426a23544e8426a38ae43ae404670a0a7e85b9eb` (`git -C /Users/buv/fineract
rev-parse HEAD`, full hash recorded here because the registry abbreviates it).

**The citation is CORRECT and the line numbers are exact.** Lines 626-640 are:

```java
626  private void validateBusinessRulesForJournalEntries(final JournalEntryCommand command) {
627      // check if date of Journal entry is valid
628      final LocalDate transactionDate = command.getTransactionDate();
629      // shouldn't be in the future
630      if (DateUtils.isDateInTheFuture(transactionDate)) {
631          throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.FUTURE_DATE, transactionDate, null, null);
632      }
633      // shouldn't be before an accounting closure
634      final GLClosure latestGLClosure = this.glClosureRepository.getLatestGLClosureByBranch(command.getOfficeId());
635      if (latestGLClosure != null) {
636          if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)) {
637              throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.ACCOUNTING_CLOSED, latestGLClosure.getClosingDate(),
638                      null, null);
639          }
640      }
```

Both refusals the registry claims live in that exact 15-line window. One correction of emphasis: the
registry describes this row as "opening balances and closure". Lines 626-640 contain **no opening-balance
logic at all** — they contain a FUTURE_DATE guard and an ACCOUNTING_CLOSED guard. Whatever "opening
balances" refers to in that registry row, it is not cited by these lines.

### What the source says the refusal will be

Derived from `JournalEntryInvalidException.GlJournalEntryInvalidReason` [VERIFIED:
`fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/exception/JournalEntryInvalidException.java`]:

| | FUTURE_DATE | ACCOUNTING_CLOSED |
|---|---|---|
| `errorCode()` | `error.msg.glJournalEntry.invalid.future.date` | `error.msg.glJournalEntry.invalid.accounting.closed` |
| `errorMessage()` | `The journal entry cannot be made for a future date` | `Journal entry cannot be made prior to last account closing date for the branch` |
| args | `(transactionDate, null, null)` | `(latestGLClosure.getClosingDate(), null, null)` |

HTTP status derived from `PlatformDomainRuleExceptionMapper.toResponse` →
`Response.status(Status.FORBIDDEN)` with `ApiGlobalErrorResponse.domainRuleViolation(...)`, i.e. **403**
[VERIFIED: `fineract-core/src/main/java/org/apache/fineract/infrastructure/core/exceptionmapper/PlatformDomainRuleExceptionMapper.java`].

### What "future" is measured against

`DateUtils.isDateInTheFuture(d)` → `isAfterBusinessDate(d)` → `isAfter(d, getBusinessLocalDate())`
[VERIFIED: `DateUtils.java:262`, `:258-260`, `:238-240`]. It is a **strict** `isAfter`, so the business
date itself is NOT in the future.

`getBusinessLocalDate()` → `ThreadLocalContextUtil.getBusinessDate()`, populated per-request by
`BusinessDateFilter` from `BusinessDateReadPlatformServiceImpl.getBusinessDates()`, which seeds
`BUSINESS_DATE` with `DateUtils.getLocalDateOfTenant()` and **only** overrides it from `m_business_date`
when `configurationDomainService.isBusinessDateEnabled()`.

On this tenant `enable-business-date` is **`f`** and `m_business_date` is **empty** (0 rows)
[out/M-02-ledger-state-fixed.txt §4b, out/M-01-ledger-state.txt §4]. So the effective business date is
**today in `Asia/Ulaanbaatar` (+08)**. `now()` in the database read `2026-08-23 00:09:58+00`
[out/M-02-ledger-state-fixed.txt §4c], which is 08:09 on **2026-08-23** in Ulaanbaatar.

---

## 2. What was sent

Two probes, both against office 1 (Head Office — the only office on this tenant), both otherwise
well-formed and balanced so that **the transaction date is the only defect**. `officeId` is resolved
before `validateBusinessRulesForJournalEntries` runs [`:150-156`], so the office must be real; the GL
accounts are only resolved *after* the date guard, but valid ones were used anyway so the refusal
isolates exactly one variable.

GL accounts used: debit **4** (`10201` Loan Portfolio), credit **2** (`10100` Fund Source). Both are
`manual_journal_entries_allowed = t`, `disabled = f`, `account_usage = 1` (detail).

| probe | transactionDate | why this date |
|---|---|---|
| `A1-01-future-far` | `2026-12-31` | unambiguously future, immune to any timezone drift during capture |
| `A1-02-future-boundary-plus1` | `2026-08-24` | **business date + 1 day — the minimal future date.** Pins the boundary from the refusing side |

**The boundary is deliberately probed only from the refusing side.** The accepting side (an entry dated
`2026-08-23` or earlier) would be *accepted*, and accepting means writing a journal entry into the
reference oracle. Arm 1's whole value is that it has zero side effects, so that probe was not taken. The
consequence is stated plainly in §5.

### Money

Every amount on the wire is the integer token `1000000` — no decimal point, no exponent, byte-preserved
under a binary-double round trip. Fineract's `amount` field is a `BigDecimal` in **major** units, so
`1000000` denotes MNT 1,000,000.00 = **100000000 minor units** (MNT, ISO 4217 numeric 496, minor unit 2;
`m_organisation_currency` confirms `decimal_places = 2` for MNT [out/M-02-ledger-state-fixed.txt §5]).
The major/minor mapping is recorded here explicitly rather than left implicit, because the wire token and
the minor-unit value are different numbers and a promotion task must not conflate them.

---

## 3. What the oracle actually returned

**Both probes: HTTP 403.** Bodies verbatim (`out/A1-01-future-far.json`, `out/A1-02-future-boundary-plus1.json`):

```json
{"developerMessage":"Request was understood but caused a domain rule violation.","httpStatusCode":"403","defaultUserMessage":"Errors contain reason for domain rule violation.","userMessageGlobalisationCode":"validation.msg.domain.rule.violation","errors":[{"developerMessage":"The journal entry cannot be made for a future date","defaultUserMessage":"The journal entry cannot be made for a future date","userMessageGlobalisationCode":"error.msg.glJournalEntry.invalid.future.date","parameterName":"id","args":[{"value":"2026-12-31"},{},{}]}]}
```

The two bodies are byte-identical except for `args[0].value`, which echoes the submitted
`transactionDate` (`2026-12-31` / `2026-08-24`).

### Did the oracle agree with the source?

**Yes on everything the source determines, and it also told us three things the source reading did not
predict.** Recording both halves, because a prediction that was merely *close* is not a prediction that
was right.

| | predicted from source | observed | verdict |
|---|---|---|---|
| HTTP status | 403 | 403 | agrees |
| envelope `userMessageGlobalisationCode` | `validation.msg.domain.rule.violation` (from `ApiGlobalErrorResponse.domainRuleViolation`) | same | agrees |
| `errors[0].userMessageGlobalisationCode` | `error.msg.glJournalEntry.invalid.future.date` | same | agrees |
| `errors[0].developerMessage` / `defaultUserMessage` | `The journal entry cannot be made for a future date` | same, in **both** fields | agrees |
| args | `(transactionDate, null, null)` | `[{"value":"2026-12-31"},{},{}]` | **NOT predicted exactly** |
| `errors[0].parameterName` | not predicted at all | `"id"` | **NOT predicted** |
| envelope `httpStatusCode` | not predicted | `"403"` — a **string**, not a number | **NOT predicted** |

Three corrections to my own reading, stated as corrections rather than quietly folded in:

1. **The two null args are serialized as empty JSON objects `{}`, not as `null` and not omitted.** The
   `args` array always has arity 3 for this exception. A port that emits `[{"value":"2026-12-31"}]`, or
   `[{"value":"..."},null,null]`, diverges on the wire even though the Java constructor arguments match.
2. **`parameterName` is the literal string `"id"`**, which is not derivable from the throw site — nothing
   in the throw names a parameter. It comes from the generic `ApiParameterError` construction path.
3. **`httpStatusCode` is a quoted string `"403"`**, while HTTP status itself is of course numeric. Both
   spellings appear in one response.

None of this changes the verdict — the refusal fired for the predicted reason with the predicted code —
but items 1-3 are exactly the kind of detail a refusal vector has to pin, and none of them could have
been written down without sending the request.

---

## 4. A refused write wrote nothing — MEASURED, not asserted

`sql/q3-writecheck.sql` run immediately before and immediately after both probes:

```
 je_rows | je_max_id |  earliest  |   latest
      60 |        64 | 2026-02-01 | 2026-08-01
 closure_rows | closure_max_id
            0 |
 payment_detail_rows | payment_detail_max_id
                   3 |                     4
 je_seq_last_value | is_called
                64 | t
```

`diff out/M-04-writecheck-before-arm1.txt out/M-05-writecheck-after-arm1.txt` → **identical**.

`max(id)` and the sequence `last_value` are checked separately from `count(*)` on purpose: a sequence can
advance without a surviving row, and only `last_value` sees that. It did not advance — **64 before, 64
after**. The date guard runs before `paymentDetailWritePlatformService.createAndPersistPaymentDetail`
[`:150-160`], and `m_payment_detail` is unchanged too, which corroborates the ordering read from source.

So arm 1 is confirmed zero-side-effect **on the ledger**, by measurement on this tenant, not by reasoning
about what a rolled-back transaction ought to do.

### CORRECTION, added after arm 2 measured something arm 1 had not thought to look at

**"A refused write writes nothing" is TRUE OF THE LEDGER AND FALSE OF THE DATABASE.** Arm 2 watched
`m_portfolio_command_source` — which `sql/q3-writecheck.sql` above does **not** — and found that Fineract's
command bus records an audit row for a refused command just as it does for a successful one
[out/M-11-command-audit-status.txt]:

```
 id  | action_name | entity_name  | status | resource_id | office_id
 346 | CREATE      | JOURNALENTRY |      5 |             |
 347 | CREATE      | JOURNALENTRY |      5 |             |
```

Rows **346 and 347 are arm 1's own two refusals** (their `command_as_json` carries `"transactionDate":
"2026-12-31"` and `"2026-08-24"` — see out/M-10-command-audit.txt). `status = 5` is **ERROR**
[VERIFIED: `CommandProcessingResultType.java:31-37` — `0 INVALID, 1 PROCESSED, 2 AWAITING_APPROVAL,
3 REJECTED, 4 UNDER_PROCESSING, 5 ERROR`], `resource_id` is NULL, and each row consumed an id and an
idempotency key.

Nothing above about the ledger changes: `acc_gl_journal_entry` and its sequence are provably untouched.
But the claim is now correctly scoped, and the honest statement of arm 1's footprint is: **two permanent
append-only audit rows, no ledger rows, no sequence movement on the ledger.** I am flagging this rather
than leaving §4's original wording to imply more than it measured — the original write-check simply did
not look at that table.

---

## 5. What arm 1 does NOT establish

- **The accepting side of the boundary is UNOBSERVED.** `2026-08-24` is refused, which proves the
  effective business date is strictly earlier than `2026-08-24`. That the business date is *exactly*
  `2026-08-23`, and that an entry dated `2026-08-23` would be *accepted*, is **derived from source and
  from `now()`, not observed** — observing it would require writing a journal entry into the oracle.
  A promotion task that wants the accept side must budget for that write and say so.
- **`enable-business-date` is `f` here.** Everything above about the business date being "today in the
  tenant timezone" is contingent on that configuration row. If a later fire enables the feature, the
  boundary moves to whatever `m_business_date` says and these captures become clock-relative in a
  different way. The `2026-12-31` probe survives that change; the `2026-08-24` probe does not.
- **`A1-02` is CLOCK-RELATIVE and will stop being a refusal on 2026-08-24.** It is committed as a dated
  observation of the boundary, not as a re-runnable assertion. `A1-01` (`2026-12-31`) re-runs as a
  refusal until 2027. Neither should be promoted into a vector without a date strategy; this is the
  single most important thing for the promotion task to notice.
- **No opening-balance behaviour was captured**, because lines 626-640 do not implement any. See §1.
