# T327 — the ACCEPTING side of the closure boundary and of the business-date guard

**T295 backlog B-1 and B-2, both FIRED, both ACCEPTED, on a THROWAWAY instance that no longer
exists.** The standing reference oracle on `:8443` / tenant `gerege` was **never written to** and
its counters are byte-identical before, during and after (§5).

Everything a promoting task needs is in `throwaway/out/`. **No oracle contact is required to
promote from these bytes.**

---

## 0. The two gaps this closes, in the store's own words

`.softhouse/vectors/capabilities-ledger.json`, row `ledger.refusal.parity`:

> "…only the REFUSAL side of each boundary is pinned. That an entry dated closingDate + 1 day, or
> one dated ON the business date, is ACCEPTED with HTTP 200 is `[UNVERIFIED]` in this store,
> because capturing an acceptance means POSTING A JOURNAL ENTRY THAT CANNOT BE DELETED. Both are
> filed as backlog … (B-1, B-2) and NEITHER WAS FIRED."

**Both are now fired.** A journal entry still cannot be deleted; an **instance** can.

**Why it mattered:** `LDG-REFUSE-04` and `LDG-REFUSE-05` pin only refusals, so **a port that
refuses every dated entry passes both and survives the entire corpus** — the mutant shape T305
killed for opening balances (T296 arm A).

---

## 1. The arms, in the order they were fired

| # | case id | transactionDate | relation | observed |
|---|---|---|---|---|
| 1 | `B2-ACCEPT-01-entry-on-business-date` | `2026-08-28` | **== business date** | **HTTP 200**, 3 legs |
| 2 | `B2-CTRL-02-entry-one-day-after-business-date` | `2026-08-29` | business date **+ 1** | HTTP 403 `error.msg.glJournalEntry.invalid.future.date` |
| 3 | `B1-SETUP-03-create-glclosure` | closingDate `2026-08-26` | precondition | HTTP 200, `resourceId` **1** |
| 4 | `B1-CTRL-04-entry-on-closing-date` | `2026-08-26` | **== closing date** | HTTP 403 `error.msg.glJournalEntry.invalid.accounting.closed` |
| 5 | `B1-CTRL-05-entry-before-closing-date` | `2026-08-25` | closing date **− 1** | HTTP 403 `…accounting.closed`, `args[0].value` = **`2026-08-26`** |
| 6 | `B1-ACCEPT-06-entry-one-day-after-closing-date` | `2026-08-27` | closing date **+ 1**, and ≤ business date | **HTTP 200**, 3 legs |

Every POST carried a **distinct** `Idempotency-Key` (`t327-b2-accept-01`, `t327-b2-ctrl-02`,
`t327-b1-setup-03`, `t327-b1-ctrl-04`, `t327-b1-ctrl-05`, `t327-b1-accept-06`). Arms 1 and 6 send
byte-different bodies, but the distinct keys are what make each transcript line an execution rather
than a possible dedupe replay — T305's reason, kept.

Each arm has `.req`, `.req.sha256`, `.json`, `.json.sha256`, `.status`, `.captured-at-utc` and a
`.http` sidecar carrying the case id, the tenant, the idempotency key, the response status, the
business-date candidate and the **latest closing date read from the target at fire time**.

---

## 2. What each accepting arm proves, and how the controls make it a proof

**B-2 — the future-date comparison is STRICT (`>`), not `>=`.**
`DateUtils.isDateInTheFuture` → `isAfterBusinessDate` → `isAfter(transactionDate,
getBusinessLocalDate())`, and `isAfter(LocalDate,LocalDate)` is `first.isAfter(second)`
[`DateUtils.java:262-263, 258-259, 300-302`] — strict in the source. **Arm 1 is the wire
observation that was missing**: an entry dated exactly ON the business date is **accepted**. Arm 2
bounds it from above. Together they don't just confirm strictness — they **MEASURE the business
date on the wire**: accepted at `2026-08-28` ⇒ businessDate ≥ 2026-08-28; refused at `2026-08-29`
⇒ businessDate < 2026-08-29; therefore **businessDate = 2026-08-28**, which is the derived value
and is now observed rather than derived.

**And the run landed on an hour where that separates the tenant zone from UTC.** The host clock
read `2026-08-27T17:33Z`; `2026-08-28` was the date only in `Asia/Ulaanbaatar` (+08). An instance
or a port reading the business date in UTC would have **refused** arm 1. It accepted.

**B-1 — the closure boundary ACCEPTS at `closingDate + 1`.**
Arm 4 is the calibration (P-72 — *"a sweep is an INSTRUMENT; calibrate it on a known positive
before you report its negatives"*): it proves the closure created in arm 3 is **live** and the
boundary **inclusive** on the same instance, minutes before arm 6. Without it, arm 6's 200 would be
consistent with "the closure never took effect". With it, the only difference between the refusal
and the acceptance is **one day**.

**Which rule answered — see §3.**

---

## 3. Which rule answered, and how it was proved

`validateBusinessRulesForJournalEntries` runs `:630` FUTURE_DATE **before** `:636`
ACCOUNTING_CLOSED [`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:626-640`]. So a badly
chosen date measures the wrong rule. Three separate proofs, all from the captured bytes:

1. **The globalisation code names the rule.** Arm 2 returned
   `error.msg.glJournalEntry.invalid.future.date`; arms 4 and 5 returned
   `error.msg.glJournalEntry.invalid.accounting.closed`. Different rules, different codes, no
   inference needed.
2. **Arm 6's date is inside both rules' accepting region, by construction.** `2026-08-27` is
   `> 2026-08-26` (the closing date) **and** `≤ 2026-08-28` (the business date). `:630` cannot fire
   on it — arm 1 accepted a *later* date, `2026-08-28`. So the acceptance is the closure rule
   falling through, not the future-date rule being dodged.
3. **The closure was live at arm 6's fire time, read from the target and recorded in the sidecar.**
   `B1-ACCEPT-06-…​.http` carries `latest-closing-date-at-fire-time: 2026-08-26`.

**Arm 5 is free evidence for T295's backlog B-3.** It was dated `2026-08-25` and the oracle echoed
`args[0].value = "2026-08-26"` — the **closing** date, not the submitted one, because `:637`
constructs the exception with `latestGLClosure.getClosingDate()` while `:631` constructs FUTURE_DATE
with `transactionDate` (arm 2 echoed its own `2026-08-29`). T287's A2-02 showed this on the standing
oracle; **this is the same asymmetry, re-observed on a fresh instance, and arm 2 and arm 5 in the
same run are the contrast.**

---

## 4. The accepted entries, read back

Both accepts produced **exactly three legs** — the request's own legs, **no contra expansion**
(that is `defineOpeningBalance`-only, `:791/:796`; this is the plain create path, `:146`).
`type_enum` 1 = CREDIT, 2 = DEBIT [`JournalEntryType.java:23-24`].

`B1-ACCEPT-06`, transaction `a29aac77c01b`, `entry_date 2026-08-27`:

| id | account_id | gl_code | classification_enum | side | stored amount | minor units |
|---|---|---|---|---|---|---|
| 4 | 1 | `T327-1000` (T327 Cash On Hand) | 1 ASSET | DEBIT | `250000.250000` | 25000025 |
| 5 | 2 | `T327-1100` (T327 Loans Receivable) | 1 ASSET | DEBIT | `100000.370000` | 10000037 |
| 6 | 3 | `T327-2000` (T327 Borrowings) | 2 LIABILITY | CREDIT | `350000.620000` | 35000062 |

`B2-ACCEPT-01`, transaction `a29aac720487`, `entry_date 2026-08-28`: the same three accounts, the
same three amounts, ids 1–3.

**Leg count 3. Debit total 35000062 minor units, credit total 35000062, per transaction. Whole
ledger 70000124 / 70000124.** Recomputed as integers from the committed bytes by
`throwaway/invariant-minor-units.py` → `out/FINAL-invariant-minor-units.txt`.

**THE WIRE SCALE, observed on both seams:**

- **REST** (`GET /journalentries?transactionId=…`) returns `"amount": 250000.25` — a JSON **number
  at scale 2**.
- **Database** (`acc_gl_journal_entry.amount::text`) stores `250000.250000` — **scale 6**, the same
  scale T305 recorded.
- **No amount anywhere in this capture carries a non-zero digit beyond two decimals.** The residue
  rule reported `residue beyond 2 digits found: NONE`, and that NONE is a **measurement**, not a
  default: `red-drive-residue-rule.py` drives the same rule red on `250000.250001`, `0.005`,
  `1.239` and `100.00000001` (P-72 / P-22), output in `out/RESIDUE-RULE-red-drive.txt`.

**No float is constructed from a money value anywhere in this rig.** The conversion is string
surgery plus integer arithmetic; the decimal characters above are the oracle's own, transcribed.

---

## 5. The standing reference oracle did not move

Read **before** the rig started, **before** each accepting POST, **after** each accepting POST, and
**after teardown** — all identical:

```
acc_gl_journal_entry        = 60/64
acc_gl_closure              = 0/null
distinct_transaction_id     = 26
m_portfolio_command_source  = 352/352
m_loan                      = 7
m_office                    = 1
acc_gl_account              = 23   (recorded separately, out/T327-STANDING-COUNTERS-BEFORE/AFTER)
```

**None of T287's four probes was fired.** `.softhouse/capture/t287-closure-refusals/req/` was read
and never POSTed from; every request body here is a new file under `throwaway/req/`.

---

## 6. The trap T295 recorded, and what was actually observed

T295: *"the next closure gets `id = 2`, not 1, because T287's create/delete left `is_called = t` on
the sequence."* That is a fact about the **standing** oracle. On this fresh instance:

```
before: last_value=1 is_called=false
create: HTTP 200 {"officeId":1,"resourceId":1}
after:  acc_gl_closure -> 1 | 1 | 2026-08-26 ;  last_value=1 is_called=true
```

**The observed id is 1.** Recorded because the brief asked which of the two predictions held:
neither was assumed — the id was read from the response, from `acc_gl_closure`, and from
`GET /glclosures`.

---

## 7. Reproducing it

`bash throwaway/run-all.sh` — guard, up, wait, setup, capture, teardown, manifest. It refuses to
overwrite a non-empty `out/` (an accepting capture's bytes are irreplaceable) unless
`T327_FORCE_OVERWRITE=1`.

What it **cannot** reproduce byte-for-byte: the transaction ids (oracle-generated), the timestamps,
and **the dates** — they are computed relative to the business date, i.e. relative to the day it
runs. That is deliberate: the vector these bytes should feed asserts a **relation** between
transaction date, closing date and business date (T289's date strategy (c)), which no calendar can
falsify.

`throwaway/MANIFEST.sha256` covers every **oracle byte** — everything under `throwaway/req/` and
`throwaway/out/`, 99 entries; `shasum -a 256 -c MANIFEST.sha256` verifies (exit 0).

The capture-directory-level `out/` is **supporting evidence about the rig, not oracle output**, and is
deliberately outside that manifest:

| file | what it is |
|---|---|
| `out/T327-STANDING-COUNTERS-BEFORE.txt` / `-AFTER.txt` | the standing oracle's seven counters, read directly, before and after; `diff` is empty |
| `out/T327-RIG-PROVENANCE-rename-proof.txt` | seds each inherited rig file **back** to `t305` and `cmp`s it against T305's committed original, so "this is T305's rig renamed" is a **measurement**. It also **refutes** an overstatement in an earlier draft of `docker-compose.t327.yml`'s own header — see §8 of the handoff. |

---

## 8. Scope — what this capture is NOT

**No vector was promoted, `conformance.sh` was not edited, `admit.go` was not edited and
`capabilities-ledger.json` was not edited.** T326 owns `conformance.sh` and T306 owns `admit.go` in
this same batch, and T306 is re-deciding the capability gate a promotion would have to pass.
Promotion is a separate follow-up **so these oracle bytes are banked regardless of how that
argument lands**.
