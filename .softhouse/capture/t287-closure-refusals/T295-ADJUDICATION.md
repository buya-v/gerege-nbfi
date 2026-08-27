# T295 — the adjudication of all four T287 probes, and what happened to each

Added by **T295**, the promotion task, on branch `softhouse/t295-t287-promotion`.
Co-located with the rig, beside `T289-CORRECTIONS.md`, for the reason T289 gave: the captures are
here, so the verdicts on them are here.

Full reasoning: `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T295.md`.

**Nothing in `out/` was rewritten and NO PROBE WAS FIRED.** Every byte T287 captured is untouched.

---

## 0. What was verified before anything was transcribed

```
$ shasum -a 256 -c MANIFEST.sha256
87 lines in MANIFEST.sha256, 87 OK, 0 not-OK          exit 0

$ sh guard-probe-expiry.sh
business date: 2026-08-23  (DERIVED -- enable-business-date='f', m_business_date rows: 0;
                            today in Asia/Ulaanbaatar)
latest GLClosure at office 1: NONE (acc_gl_closure has no row for office 1)

ok      a1-01-future-far.json             transactionDate 2026-12-31 > business date 2026-08-23
ok      a1-02-future-boundary-plus1.json  transactionDate 2026-08-24 > business date 2026-08-23
NOTE    a2-00-create-closure.json         MUTATION recipe, not a probe
REFUSE  a2-01-preclosure-on-date.json     *** NO GLClosure EXISTS at office 1 ***
REFUSE  a2-02-preclosure-before.json      *** NO GLClosure EXISTS at office 1 ***

REFUSED: at least one probe would WRITE to the reference oracle if fired now.   exit 1
```

The guard is **RED**, as T289 said it is and as the driver independently verified. Both `a2-*`
probes are armed **right now**; `a1-02` arms **tomorrow, 2026-08-24**. This task therefore promoted
**bytes already on disk** and touched the oracle only through `conformance.sh`'s read-only health
probe.

Driver's live census, unchanged by this task: `acc_gl_journal_entry` **60 / maxid 64**,
`acc_gl_closure` **0**, distinct transaction ids **26**.

---

## 1. The verdicts

| capture | verdict | where it went |
|---|---|---|
| `A2-01-preclosure-on-date` | **PROMOTED** | `.softhouse/vectors/ledger/LDG-REFUSE-04-preclosure-entry-on-closing-date.json` |
| `A1-02-future-boundary-plus1` | **PROMOTED** | `.softhouse/vectors/ledger/LDG-REFUSE-05-future-dated-entry-one-day-after-business-date.json` |
| `A2-02-preclosure-before` | **NOT PROMOTABLE** | §3 below — the measurement |
| `A1-01-future-far` | **NOT PROMOTABLE** | §4 below — the measurement |

T289's prescribed strategy was **implemented, not refuted**: `businessDate` and `latestClosingDate`
are lifted out of prose into `request.business_date` and `request.latest_closing_date`
(`nexus/internal/apps/ledger/conformance/vector.go`), with default-deny admissibility rules in
`admit.go` and executable tests in `daterefusals_test.go`.

---

## 2. PROMOTED — and what each promoted vector actually kills

### `LDG-REFUSE-04` — the INCLUSIVE closure boundary

This is the money-path finding of the whole arm, and A2-01 is the **only** capture in the corpus
that can carry it.

```java
// JournalEntryWritePlatformServiceJpaRepositoryImpl.java:634-639, pinned 426a23544
final GLClosure latestGLClosure = this.glClosureRepository.getLatestGLClosureByBranch(command.getOfficeId());
if (latestGLClosure != null) {
    if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)) {
        throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.ACCOUNTING_CLOSED,
                latestGLClosure.getClosingDate(), null, null);
```

`DateUtils.isBefore(first, second)` is `first.isBefore(second)` for two non-null `LocalDate`s
[`DateUtils.java:296-298`], so the negation refuses whenever **`transactionDate <= closingDate`**.
The message the same throw returns is *"Journal entry cannot be made **prior to** last account
closing date for the branch"*.

**The code and the message disagree about exactly one day, and that day is the closing date
itself — the day a period-end adjustment carries.**

A2-01 posted `transactionDate = 2026-01-31` while the closure closed `2026-01-31`. **The two are
equal**, which is the *only* relation that separates the two readings:

| transactionDate vs closingDate | inclusive (`<=`, the code) | exclusive (`<`, the message) |
|---|---|---|
| strictly before | refuse | refuse |
| **equal** | **refuse** | **ACCEPT — fails open** |
| strictly after | accept | accept |

`ledger-wrong-closure-boundary-exclusive` is that strict-`<` port, registered in `impl.go` and
executable via `-ledger-impl`. It agrees with the reference implementation on every entry dated
strictly before the closing date — *every pre-closure request a naive corpus would think to
capture* — and dies on `LDG-REFUSE-04` alone, on all three refusal cells.

Measured on the promoting run: `KILLED ledger-wrong-closure-boundary-exclusive — exit 1, ledger
parity FAIL 0 + oracle-refusal FAIL 1`.

### `LDG-REFUSE-05` — the future-date guard reads the BUSINESS DATE

`:629 DateUtils.isDateInTheFuture(transactionDate)` → `isAfterBusinessDate` →
`isAfter(transactionDate, getBusinessLocalDate())` [`DateUtils.java:258-264`]. The business date is
**tenant ambient state**: it appears nowhere in the request body and nowhere in the endpoint's
documentation, so a port can be complete against the API and still have this rule missing.

`ledger-wrong-future-date-ignored` is that port. `KILLED — exit 1, ledger parity FAIL 0 +
oracle-refusal FAIL 1`.

**What `LDG-REFUSE-05` pins and does NOT pin.** It pins that `businessDate + 1` is refused, killing
any port whose future tolerance is a day or more. It does **not** pin that the comparison is
*strict* — a port using `>=` also refuses this request and survives. See backlog **B-2**.

---

## 3. NOT PROMOTABLE — `A2-02-preclosure-before`, and the measurement that settles it

### The measurement

```
$ cmp out/A2-01-preclosure-on-date.json out/A2-02-preclosure-before.json
(no output — the files are identical)

$ shasum -a 256 out/A2-01-preclosure-on-date.json out/A2-02-preclosure-before.json
c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2  A2-01-preclosure-on-date.json
c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2  A2-02-preclosure-before.json
```

**The two captured response bodies are BYTE-IDENTICAL**, despite different requests
(`transactionDate` `2026-01-31` vs `2026-01-15`).

### What follows, and it is two separate things

**(a) A2-02 cannot diverge on any graded cell that A2-01 does not already cover.** The `Refusal`
shape has exactly three cells — `http_status`, `code`, `message` — and A2-02's bytes carry the same
values in all three. A vector promoted from A2-02 would be a second file that no implementation in
this harness could fail independently: it would raise the corpus count by one and the kill count by
zero. That is corpus inflation, and this store's own census exists to catch it.

**Which boundary each one pins, since the brief asked it directly:** A2-01 is **ON** the closing
date and pins the boundary as **INCLUSIVE**. A2-02 is **BEFORE** it (`2026-01-15 < 2026-01-31`) and
is refused under *both* the inclusive and the exclusive reading, so it pins **nothing about the
boundary at all**. The captured pair *can* distinguish inclusive from exclusive — and the member
that does the distinguishing is **A2-01**, which is promoted.

**(b) The byte-identity is itself a finding, and it is the reason A2-02 was captured.** A2-02's
`errors[0].args[0].value` is **`"2026-01-31"`** — the **closing** date — while its own
`transactionDate` was `2026-01-15`. So the `ACCOUNTING_CLOSED` refusal echoes
`latestGLClosure.getClosingDate()`, not the submitted date. Source agrees exactly: `:637` constructs
the exception with `latestGLClosure.getClosingDate()`, whereas `:631` constructs `FUTURE_DATE` with
`transactionDate`. **The same field means different things in the two refusals.** T287 recorded this
in its handoff §1 item 4; T295 re-measured it, and the byte-identity above is the direct proof —
two different requests, one identical response, which can only happen if the response does not
mention the request's date.

**A2-01 cannot show this**, because on A2-01 the two dates coincide. A2-02 is the *only* capture
that separates them.

### Why that finding did not make A2-02 promotable anyway

`errors[0].args` is **not a graded cell**. Adding a fourth cell to `Refusal` is a cross-cutting
schema change that would force a re-adjudication of `LDG-REFUSE-03`, which **deliberately declined**
to grade its own `args` (a 26-member, tenant-state-dependent transaction-id list that would go red
on any unrelated posting to this tenant). T295 did not make that change unilaterally on an adjacent
landed task's reasoning. It is filed as **B-3**.

**The finding is not lost in the meantime:** it is written into `LDG-REFUSE-04`'s and
`LDG-REFUSE-05`'s `_note` as an explicit NOT-GRADED item naming the asymmetry, into the source
comments at the two port steps, and here.

---

## 4. NOT PROMOTABLE — `A1-01-future-far`, and the measurement

### The measurement

```
$ shasum -a 256 out/A1-01-future-far.json out/A1-02-future-boundary-plus1.json
79846c37e18dc392836d0bbd7324abed5c262a9220b4216835745087581c0bf0  A1-01-future-far.json
dacfce8688080d3e4796de4286278e3ed779095cf90f0ec666d701d43a8618f7  A1-02-future-boundary-plus1.json
```

The bodies differ — but the diff is **entirely inside `errors[0].args[0].value`**
(`"2026-12-31"` vs `"2026-08-24"`, each echoing its own `transactionDate`, per `:631`). All three
**graded** cells are identical:

| cell | A1-01 | A1-02 |
|---|---|---|
| `refusal.http_status` | 403 | 403 |
| `refusal.code` | `error.msg.glJournalEntry.invalid.future.date` | *same* |
| `refusal.message` | `The journal entry cannot be made for a future date` | *same* |

### What follows

A1-01's relation is `transactionDate = businessDate + 130 days`; A1-02's is `+ 1 day`. **Under a
monotone date predicate — which the ported comparison is by construction, and which every plausible
port is — refusing `+1` implies refusing `+130`.** A1-02 kills strictly more: it kills any port
whose future-date tolerance is one day or more, which includes every port A1-01 would kill. A1-01
adds no kill and no graded cell.

**The one thing A1-01 would catch that A1-02 does not** is a *non-monotone* predicate — a port
refusing exactly `businessDate + 1` and accepting everything beyond it. That is not a defect shape
any real port has; it is recorded here so the next reader does not have to re-derive that it was
considered. If a reviewer disagrees, promoting A1-01 is a five-minute transcription from bytes that
are on disk and verified, and requires **no** oracle contact.

---

## 5. BACKLOG — the captures that would close the remaining gaps, AND WHY NONE WAS FIRED

Every item below requires the oracle to **ACCEPT** a posting. **A posted journal entry cannot be
deleted** — unlike the `GLClosure` T287 created and removed (`deleteGLClosure` is a hard delete,
`:135`, and `GLClosure` carries no `@SQLDelete`), the only "undo" for a journal entry is posting
more entries. So each of these permanently moves the reference oracle every vector in this program
is graded against, and **T295 fired none of them.** They are written out in full so the decision to
take one is a deliberate, costed decision by a later task with a driver's sign-off, and not a
rediscovery.

### B-1 — the ACCEPTANCE side of the closure boundary

`LDG-REFUSE-04` pins that `transactionDate <= closingDate` is refused. That `closingDate + 1` is
**accepted** is `[UNVERIFIED]` — no capture shows it.

- **Precondition:** a `GLClosure` at office 1 with `closingDate = D`. `acc_gl_closure` is currently
  empty, so one must be created first (`req/a2-00-create-closure.json`) — **and the next closure
  gets `id = 2`, not 1**, because T287's create/delete left `is_called = t` on the sequence.
- **Request:** `POST /journalentries`, tenant `gerege`

  ```json
  { "officeId": 1, "transactionDate": "<D + 1 day>", "dateFormat": "yyyy-MM-dd", "locale": "en",
    "currencyCode": "MNT", "comments": "B-1 closure upper-edge acceptance probe",
    "debits":  [ { "glAccountId": 4, "amount": 1000000 } ],
    "credits": [ { "glAccountId": 2, "amount": 1000000 } ] }
  ```
- **Expected:** HTTP 200 and **a journal entry that exists forever**. `D + 1` must also be `<=` the
  business date or `:629` answers first.
- **COST, STATED PLAINLY:** two permanent `acc_gl_journal_entry` rows, `je_rows` 60 → 62. This is
  the item to weigh hardest: it converts an `[UNVERIFIED]` into a vector at the price of
  contaminating the oracle, and the refusal side — the side that catches a port failing **open** —
  is already pinned without paying it.

### B-2 — the STRICTNESS of the future-date comparison

`LDG-REFUSE-05` pins that `businessDate + 1` is refused. It does not distinguish `>` from `>=`. The
capture that would: an entry dated **ON** the business date, expected HTTP 200.

- **Precondition:** none beyond the tenant's business date being what it is.
- **Request:** as B-1, with `"transactionDate": "<today in Asia/Ulaanbaatar>"` and no closure
  interfering (`acc_gl_closure` empty is sufficient).
- **Expected:** HTTP 200, **two permanent journal entries**.
- **Note:** the source is unambiguous (`isAfter`, strict) and the port implements the strict
  reading, with `TestFutureDateGuardReadsTheBusinessDateAndNoClock` asserting it. What is missing is
  a *wire observation*, not an answer.

### B-3 — grade `errors[0].args`, which would make A2-02 promotable

A fourth `Refusal` cell (or a dedicated, optional-but-admit-enforced arg cell) would let the corpus
grade that `ACCOUNTING_CLOSED` echoes the **closing** date while `FUTURE_DATE` echoes the
**transaction** date. It would then kill a new wrong implementation —
`ledger-wrong-accounting-closed-echoes-transaction-date` — and **A2-02 would become promotable from
bytes already on disk, with NO oracle contact at all.**

**This is the only backlog item here that costs nothing at the oracle**, and it is the one a later
task should take first. The obstacle is not risk, it is scope: it must be reconciled with
`LDG-REFUSE-03`'s deliberate refusal to grade its own 26-member, tenant-state-dependent `args`
list, which is an adjacent landed task's reasoning and not T295's to overturn.

---

## 6. One correction to this rig's own guard, recorded and NOT applied

`guard-probe-expiry.sh` classifies by file name and fails closed, which is right. But its `a2-*`
branch would now also need to know that **two of the four probes are promoted**, so re-firing them
is not merely dangerous but pointless — the bytes are already graded. The guard was **not edited**:
T289 owns it, it is correct as written (it refuses today), and widening its remit inside a
promotion task would be an add/add hazard on a file whose whole value is that it is
conservative. Recorded here instead, which is where the next reader of the rig will meet it.
