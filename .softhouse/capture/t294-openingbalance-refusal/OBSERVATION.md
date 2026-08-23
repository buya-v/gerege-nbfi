# T294 — the opening-balance refusal, captured

**One POST. HTTP 403. The reference oracle's ledger did not move.**

Rig: `.softhouse/capture/t294-openingbalance-refusal/`. Tenant `gerege` (never `default`),
PostgreSQL `fineract_gerege` in container `fineract-db-1`, REST at `https://localhost:8443`.
Pinned Fineract `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

`env.sh`, `cap.sh`, `capsql.sh` and `manifest.sh` are **copies** of T287's, not sources of
them. That is deliberate and it is T287's own property, kept: a cross-directory `source` is
a dependency a reviewer reading `git show <branch>:<path>` cannot see. Only the header
comments differ; the executable bodies are byte-identical apart from the scratch-directory
prefix.

---

## 1. What was re-derived before anything was sent

Every clause of the driver's safety paragraph was checked against the pinned source **and**
against read-only SQL on the live oracle, in that order, before the POST.

| claim | where it was checked | result |
|---|---|---|
| `defineOpeningBalance` is reached by `POST /journalentries?command=defineOpeningBalance` | `JournalEntriesApiResource.java:211-212` | TRUE |
| it enters `defineOpeningBalance` | `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:703` | TRUE |
| the guard is at `:717` → `:810-816` | same file | TRUE, verbatim |
| the code is `error.msg.journalentry.defining.openingbalance.not.allowed` | `:813` | TRUE |
| the message is "Defining Opening balances not allowed after journal entries posted" | `:814` | TRUE |
| it fires whenever any non-contra journal entry exists | `JournalEntryRepository.java:32-34` JPQL | TRUE |
| financial-activity type 300 is mapped, id 4 → GL 15 | live SQL, `M-01` | TRUE |
| the tenant has journal entries | live SQL, `M-02`: **60 rows, 26 distinct transaction ids** | TRUE |
| **it throws BEFORE any write** | source read of `:703-758` | TRUE — see below |
| it needs no closure, no office, no clock | source read | TRUE — see below |

**"Throws before any write", established by reading the whole method rather than the guard.**
In `defineOpeningBalance` the statements before `:717` are: deserialize (`:705`),
`validateForCreate()` (`:706`), resolve the type-300 mapping (`:708`), null-check the contra
id (`:710-714`). None writes. The **first** write on that path is the reversal loop at
`:726-733` (`revertJournalEntry`), and the persists are at `:742`/`:745` inside
`saveAllDebitOrCreditOpeningBalanceEntries`. Both are **after** `:724`, which is itself
after `:717`.

**"No closure, no office, no clock", from the same read.** The office lookup is `:719-720`,
*after* the guard. The future-date test (`:630`) and the closure test (`:634-640`) are inside
`validateBusinessRulesForJournalEntries`, called at `:724` — also after. So neither the
business date nor `acc_gl_closure` can influence this refusal. That is the whole reason this
capture is cheap where T287's four were not.

**Nothing was found false, so nothing was aborted.** Had any clause failed — especially the
write clause — the instruction was to stop and capture nothing.

---

## 2. Two fences, because P-92

`P-92`, learned from T289's review of T287, in its own words: *"a probe whose safety comes
from an EXTERNAL PRECONDITION rather than from its own content is a loaded weapon, and the
danger is highest immediately after the capture SUCCEEDS — because taking the observation is
often what removes the precondition. A refusal capture must carry a fail-closed fence that
re-checks the precondition at fire time, never a comment asserting the refusal, because the
comment is written when the precondition holds and is not re-read when it stops holding."*

So this rig does **not** rely on the tenant state alone.

- **FENCE 1 — CONTENT.** `req/ob-01-openingbalance-after-posted-entries.json` is **unbalanced
  by exactly one MNT minor unit**: debit GL 4 `250000.25`, credit GL 2 `250000.24`.
  `checkDebitAndCreditAmounts` (`:651`, reached from `:724`) refuses an unbalanced command
  before any write, whatever the tenant state is. This fence is clock-independent,
  state-independent and cannot expire. Contrast T287's four bodies, every one of which was a
  **valid, balanced, postable** entry whose only refusal lived in the oracle.
- **FENCE 2 — STATE.** The refusal actually captured. Re-measured live on every run of
  `guard-precondition.sh`: type 300 must map (else `:708` throws a *different* error), and
  `findNonContraTransactionIds(contraId)` must be non-empty.

`guard-precondition.sh` fails **closed**: an unreachable database, an unparseable body, a
missing file and an unclassifiable result are all exit 1. It was driven through **one green
and three red arms** before the POST, and the three red arms substitute a measured input
rather than mutating the oracle. A substituted input **can never yield exit 0** — the
what-if branch exits 1 by construction, so a debugging affordance cannot manufacture a green.

T287's own fence, `guard-probe-expiry.sh`, was run first and is **RED (exit 1)** today, as
T289 predicted: `a2-01` and `a2-02` would now **post two journal entries each**. **None of
T287's four probes was fired by this task.**

---

## 3. The one POST, and the wire

```
POST /journalentries?command=defineOpeningBalance      -> HTTP 403
out/OB-01-openingbalance-after-posted-entries.status   403
request  556 bytes, sha256 dae579d2e7a34a26980acad2a09779d7aaaea017d2e1519b50e6b5cf7e70aeae
response 822 bytes, sha256 9383ed52390f73c365f51eab450c75122aaed628603d178092444c46a06462b7
captured-at-utc 2026-08-23T02:02:47Z
```

`errors[0]`:

```
userMessageGlobalisationCode  error.msg.journalentry.defining.openingbalance.not.allowed
defaultUserMessage            Defining Opening balances not allowed after journal entries posted
developerMessage              Defining Opening balances not allowed after journal entries posted
parameterName                 id
args                          [{"value": [ ...26 transaction ids... ]}]
```

**THE WIRE MESSAGE AND THE SOURCE STRING AT `:814` AGREE CHARACTER FOR CHARACTER.** There
was no conflict to resolve. Had there been one, the wire would have won and this section
would say so in capitals.

**What the wire adds that the source reading did not predict, and which no vector grades:**

- `args` is **one** element — `{"value": [...]}` — carrying **all 26 non-contra transaction
  ids**, because `transactionIds` is passed as a single vararg `Object` at `:815`. It is
  therefore **tenant-state-dependent**, and a vector grading it would go red on any future
  posting to this tenant. The ids are carried in `LDG-REFUSE-03` as an **input** instead.
- `httpStatusCode` is the **string** `"403"` while the HTTP status is numeric — T289's pin
  item 3, confirmed on a second, unrelated error class.
- `parameterName` is the literal `"id"` — likewise confirmed on a second error class. Neither
  T287's `JournalEntryInvalidException` nor this `GeneralPlatformDomainRuleException` sets it
  meaningfully.

**The oracle answered THIS refusal for a request that also violates the balance rule.** That
is the precedence observation: `:717` beats `:651`, measured rather than read off. It is the
only ordered pair of refusals in the ledger corpus.

---

## 4. The ledger did not move — before and after, committed

`sql/q2-ledger-state.sql`, fired identically either side of the POST.

| | `M-02` BEFORE | `M-03` AFTER |
|---|---|---|
| `acc_gl_journal_entry` count / max id | **60 / 64** | **60 / 64** |
| `acc_gl_closure` count / max id | **0 / (null)** | **0 / (null)** |
| distinct journal-entry transaction ids | **26** | **26** |
| `m_portfolio_command_source` count / max id | 351 / 351 | **352 / 352** |

`M-01` / `M-04` (`sql/q1-refusal-precondition.sql`) are unchanged either side: type 300 → GL
15, `non_contra_transaction_id_count` **26**, `contra_account_entry_count` **0**.

**Sequences (`M-05`), read directly off the relations because `pg_sequences` does not expose
`is_called`:** `acc_gl_journal_entry_id_seq` **64/t**, `acc_gl_closure_id_seq` **1/t** — both
exactly as T289 left them — and only `m_portfolio_command_source_id_seq` moved, 351 → **352**.
**No ledger sequence was touched.**

---

## 5. The residue this probe leaves, characterised and not merely counted

T289's F-T289-3 found T287's disclosure read as *"a counter moved"* when the truth was *"the
oracle's public API now tells this story"*. So this rig looked.

**One row, `m_portfolio_command_source` 352** (`M-05`):

```
352 | DEFINEOPENINGBALANCE | JOURNALENTRY | resource_id NULL | status 5 | office_id NULL | /journalentries/update
```

`status 5` is the refused-command status, the same one T287's rows 346/347/349/350 carry.
`command_as_json` stores **the probe body verbatim, including its `comments` string** — the
same public-prose residue T287 left, and it is disclosed here for the same reason.

**The public audit API serves it** (`M-06`, read-only `GET /v1/audits?entityName=JOURNALENTRY&actionName=DEFINEOPENINGBALANCE`, HTTP 200):

```json
[{"id":352,"actionName":"DEFINEOPENINGBALANCE","entityName":"JOURNALENTRY","maker":"mifos",
  "madeOnDate":1787450567922,"processingResult":"Error","url":"/journalentries/update","ip":""}]
```

**One difference from T287's residue matters and is stated rather than glossed:**
`processingResult` here is **`"Error"`**, not `"Processed"`. T287's two GLCLOSURE rows assert
a **`Processed`** closure with `resourceId 1` that no longer exists; this row asserts a
command that **failed**, which is what actually happened. A future Tier C capture of the
audit/command context will see **both**, and must treat both as *tenant history left by this
program's own probes*, never as parity facts.

**Nothing else moved.** No journal entry, no closure, no sequence but the command one.

---

## 6. Promoted

`.softhouse/vectors/ledger/LDG-REFUSE-03-openingbalance-after-posted-entries.json`, class
`oracle-refusal`, `dec2_revision 5`, capabilities `ledger.refusal.parity` and
`ledger.opening.balance.and.closure`. It kills the registered wrong implementation
`ledger-wrong-openingbalance-posted-entries-ignored` on `refusal.code` and `refusal.message`
— **not** on `refusal.http_status`, because both refusals are 403 and T9-F1b forbids
recording a kill on a cell that does not diverge.

**A raw capture nobody promotes is how the ledger corpus stayed at 6 vectors / 21 money cells
for many fires.** It is now 7 / 21 — the money-cell figure does not move, and that is
correct: a refusal vector asserts no amount.
