# T287 ARM 2 — pre-closure journal entry refusal, RAW OBSERVED FORM

Captured from the live reference oracle (Fineract) on **2026-08-23 UTC**, tenant **`gerege`**,
database **`fineract_gerege`** on PostgreSQL 18.3. Decision and blast-radius measurement: `ARM2-DECISION.md`.

**Outcome: arm 2 was TAKEN, not declined — and the closure was created and then DELETED, so the tenant
carries no surviving closure.** `acc_gl_closure` is back to 0 rows, verified in the database and through
the API.

---

## 1. What was done, in order

| # | step | artefact | result |
|---|---|---|---|
| 1 | snapshot state before | `out/M-08-state-before-closure.txt` | 0 closures, 60 JE rows, 347 command rows |
| 2 | `POST /glclosures` office 1, `2026-01-31` | `out/A2-00-create-closure.*` | **200** `{"officeId":1,"resourceId":1}` |
| 3 | `POST /journalentries` dated `2026-01-31` (ON the closing date) | `out/A2-01-preclosure-on-date.*` | **403 ACCOUNTING_CLOSED** |
| 4 | `POST /journalentries` dated `2026-01-15` (before) | `out/A2-02-preclosure-before.*` | **403 ACCOUNTING_CLOSED** |
| 5 | snapshot state while closure exists | `out/M-09-state-during-closure.txt` | 1 closure, **60 JE rows still** |
| 6 | audit inspection (unplanned, see §4) | `out/M-10`, `out/M-11` | refused commands leave ERROR rows |
| 7 | `DELETE /glclosures/1` | `out/A2-03-delete-closure.*` | **200** `{"officeId":1,"resourceId":1}` |
| 8 | snapshot state after delete | `out/M-12-state-after-delete.txt` | **0 closures**, 60 JE rows |
| 9 | `GET /glclosures` | `out/M-13-glclosures-after-delete.json` | **`[]`** |

---

## 2. The refusal, verbatim

Both probes returned **HTTP 403**, and the two response bodies are **byte-identical**
(`cmp out/A2-01-preclosure-on-date.json out/A2-02-preclosure-before.json` → identical):

```json
{"developerMessage":"Request was understood but caused a domain rule violation.","httpStatusCode":"403","defaultUserMessage":"Errors contain reason for domain rule violation.","userMessageGlobalisationCode":"validation.msg.domain.rule.violation","errors":[{"developerMessage":"Journal entry cannot be made prior to last account closing date for the branch","defaultUserMessage":"Journal entry cannot be made prior to last account closing date for the branch","userMessageGlobalisationCode":"error.msg.glJournalEntry.invalid.accounting.closed","parameterName":"id","args":[{"value":"2026-01-31"},{},{}]}]}
```

### Did the oracle agree with the source?

**Yes, on every field the source determines.** `error.msg.glJournalEntry.invalid.accounting.closed` and
"Journal entry cannot be made prior to last account closing date for the branch" are exactly the strings
`GlJournalEntryInvalidReason.ACCOUNTING_CLOSED.errorCode()` / `.errorMessage()` return. Status 403 matches
`PlatformDomainRuleExceptionMapper`. The `{}`/`parameterName: "id"`/string-`"403"` quirks recorded in arm 1
recur identically here, which raises them from a one-off to a property of this exception family.

### Two findings that only a live capture could produce

**(i) `args[0]` carries the CLOSING DATE, not the submitted transaction date — and this DIFFERS from the
future-date refusal.**

`A2-02` submitted `transactionDate = 2026-01-15` and got back `args[0].value = "2026-01-31"`. That is why
the two bodies are byte-identical despite different requests. It follows the source exactly —
`new JournalEntryInvalidException(ACCOUNTING_CLOSED, latestGLClosure.getClosingDate(), null, null)`
[`:637`] passes the *closure* date, whereas the FUTURE_DATE throw at `:631` passes the *transaction* date.
So **the same `args` slot means different things in the two refusals of the same 15-line method.** A port
that fills `args[0]` with "the offending date" uniformly is wrong for one of the two, and the wire cannot
tell you which without this capture.

**(ii) THE BOUNDARY IS INCLUSIVE AND THE MESSAGE IS MISLEADING.**

`A2-01` submitted an entry dated **exactly on** the closing date `2026-01-31` and was **REFUSED** — even
though the message says the entry "cannot be made **prior to** last account closing date". It was not
prior to; it was on. The code is `!DateUtils.isBefore(closingDate, transactionDate)` [`:636`], which
refuses whenever `transactionDate <= closingDate`.

**A port must copy the CODE, not the prose.** Reimplementing from the English message yields a strict
`<` and an off-by-one-day fail-open on the single highest-risk day — the closing date itself, which is
precisely the day a period-end adjustment would be dated. This is the most useful thing arm 2 produced
and it is a divergence hazard, not a curiosity.

I did **not** predict (ii) before sending — I derived the inclusive boundary from the source while writing
`ARM2-DECISION.md` and designed `A2-01` to test it. The observation confirmed the source reading against
the message. Stated plainly so the reviewer can see which half was prediction and which was evidence.

---

## 3. The ledger was never touched

`acc_gl_journal_entry` across all three snapshots (before / during / after):

```
 je_rows | je_max_id |  earliest  |   latest
      60 |        64 | 2026-02-01 | 2026-08-01     <- M-08, before closure
      60 |        64 | 2026-02-01 | 2026-08-01     <- M-09, while closure existed
      60 |        64 | 2026-02-01 | 2026-08-01     <- M-12, after delete
```

`je_seq_last_value` is `64 / is_called t` in all three. `m_office` is `1 row / max id 1` in all three.
`m_loan` is 7 rows in all three.

**The closure was removed by a HARD DELETE**, as read from source:

```
 closure_rows | closure_max_id          id | office_id | closing_date | is_deleted | comments
            0 |                        (0 rows)
```

`GET /glclosures` → `[]`. So the removal is real at both the database and application layers, not an
`is_deleted` flag left behind. The prediction in `ARM2-DECISION.md` that `delete()` is a hard delete
(no `@SQLDelete` on `GLClosure`) is **confirmed by observation.**

---

## 4. THE PERMANENT RESIDUE — what the delete did NOT restore

Declared in advance in `ARM2-DECISION.md`, and both predictions were correct. Recording it here and in
`.softhouse/reference-oracle.md` because a mutation the next fire cannot see is a trap, and that applies
to residue as much as to a surviving row (the T276 lesson: *identity is not value, and identity does not
restore*).

| counter | before | after | restored? |
|---|---|---|---|
| `acc_gl_closure` rows | 0 | 0 | **yes** |
| `acc_gl_closure_id_seq` | `last_value 1, is_called f` | `last_value 1, is_called t` | **NO — permanent** |
| `m_portfolio_command_source` | 347 rows / max 347 | 351 rows / max 351 | **NO — permanent, append-only** |
| `acc_gl_journal_entry` | 60 / max 64 / seq 64 | 60 / max 64 / seq 64 | **yes — never moved** |
| `m_office` | 1 / max 1 | 1 / max 1 | **yes — never moved** |

**Consequence for the next fire: the next `GLClosure` created on this tenant will get `id = 2`, not
`id = 1`.** The sequence was never used before this task and is now marked called. Any future capture that
hard-codes closure id 1, or asserts on `resourceId` from a closure create, will be off by one. This is the
same class of drift T276 recorded for `acc_product_mapping`, and it is unrewindable.

### Unplanned finding: a refused command still writes an audit row

`m_portfolio_command_source` moved **+4**, not +2: the closure CREATE, the closure DELETE, **and both
refused journal-entry posts.**

```
 id  | action_name | entity_name  | status | resource_id | office_id
 348 | CREATE      | GLCLOSURE    |      1 |           1 |         1     <- PROCESSED
 349 | CREATE      | JOURNALENTRY |      5 |             |               <- ERROR (refused, 2026-01-31)
 350 | CREATE      | JOURNALENTRY |      5 |             |               <- ERROR (refused, 2026-01-15)
```

`status 5 = ERROR`, `1 = PROCESSED` [VERIFIED: `CommandProcessingResultType.java:31-37`]. Across the whole
table: **156 PROCESSED, 194 ERROR** — refused commands are in fact the *majority* of this tenant's audit
history, which is what a capture corpus built largely out of refusal probes should look like.

This retro-scopes arm 1's "a refused write writes nothing": true of the ledger, false of the database.
`ARM1-OBSERVATION.md` §4 has been corrected accordingly rather than left to imply more than it measured.

---

## 5. What arm 2 does NOT establish

- **The accepting side is UNOBSERVED.** An entry dated `2026-02-01` (closing date + 1) should be accepted,
  and that would demonstrate the boundary is exactly one day wide. It was not probed because accepting
  means writing a journal entry into the oracle. The refusal at `2026-01-31` proves the boundary is
  **inclusive**; it does not prove `2026-02-01` would have passed.
- **Only the MANUAL journal-entry path was exercised.** `ARM2-DECISION.md` shows the identical
  `checkForBranchClosures` test is called from ~14 automatic accounting sites (loan, savings, shares,
  client transactions, working capital, reversal). **None of those was captured.** A back-dated
  disbursement on an accounting-enabled product refusing under a closure is a *predicted* behaviour here,
  not an observed one, and predicting is not observing.
- **The reversal path at `:392` was not exercised**, though it carries its own copy of the same test.
- **Multi-office behaviour is UNTESTABLE on this tenant.** The lookup is per-office with no hierarchy
  walk, so a closure on a branch should not affect a sibling — but `m_office` has exactly one row, so
  that cannot be observed here without creating an office, which is irreversible (no `@DELETE` on
  `OfficesApiResource`).
- **Maker-checker was not in play** (`status` went straight to PROCESSED, never AWAITING_APPROVAL). If a
  later fire enables maker-checker, the closure create returns a different shape.
