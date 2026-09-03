# T520 — INDEPENDENT REVIEW OF T508

**Target:** branch `softhouse/T508-journalentry-insert-schema`, commit `1abd3a11`, merge base `10baca08`.
**Reviewer branch:** `softhouse/T520-review-t508`. **Reviewer wrote only this file.**
**Date:** 2026-09-03, fire `20260903-170002`.

**VERDICT: `APPROVED`** — with three MEDIUM follow-ups that are disclosure and program-enforcement
gaps, not defects in the money path, and two LOW corrections.

I did not accept the T508 transcript. I re-derived every number from `information_schema`, reproduced
**all four** red drives against the live reference oracle, re-ran the DB-backed test to PASS, and
independently re-verified every source citation. What I found is below; where I found nothing I say
what I checked, so silence is distinguishable from not looking.

---

## 0. Environment and attribution

Reference oracle (Fineract) — pinned checkout `/Users/buv/fineract @ 426a23544`
`[VERIFIED: git log --oneline -1]`. Live instance: containers `gerege-oracle-app` /
`gerege-oracle-db`, both `Up 2 days (healthy)`, PostgreSQL **18.3**, `5432/tcp -> 0.0.0.0:5432`
`[VERIFIED: docker ps, docker port]`. Database `fineract_default`, tenant `default`,
`Asia/Kolkata`, `c_configuration.rounding-mode = 6` (HALF_EVEN) — i.e. **not** the ratified
`(19, HALF_UP)` / `Asia/Ulaanbaatar` tenant. See §6.

**Scope.** The brief pointed me at `.softhouse/bin/scope-check.sh`; the coordinator then corrected
that pointer mid-review. I never used it — it is **absent from `.softhouse/bin/`** on this worktree
`[VERIFIED: ls .softhouse/bin/]`, which matches the correction. I used the merge-base form
throughout:

```
git diff --name-only 10baca08 1abd3a11
  .softhouse/handoff/T508-journalentry-insert-schema.md
  nexus/internal/apps/ledger/journalentry_postgres.go
  nexus/internal/apps/ledger/journalentry_test.go
```

**Exactly the three permitted files. Scope clean.** `[VERIFIED: measurement]` T508's branch is a
single commit off the merge base, so per-commit and merge-base attribution coincide.

**Bar.** On the T508 tree: `go build ./...` exit 0, `go vet ./...` exit 0, `go test ./...` **all 20
packages `ok`** including `ledger` and both conformance packages `[VERIFIED: measurement]`.

**No float anywhere on this path.** `grep -nE "float32|float64"` over every non-test `.go` file in
`internal/apps/ledger/` returns **nothing**; the only occurrences of the token "float" in the two
edited files are two prose comments asserting its absence `[VERIFIED: measurement]`. Amounts stay
`MinorUnits` integers, are rendered by `FormatDecimal(MNTMinorDigits=2)` to exact decimal text, and
are cast to `numeric` by Postgres. The read leg `MinorUnitsFromDecimalText` is **fail-closed on
sub-minor-unit residue** — a non-zero digit past scale 2 is an error, not a truncation
`[VERIFIED: money.go:167-178]` — so the round-trip the new DB test exercises cannot silently lose
money. (Pre-existing code; checked because the new test now depends on it.)

---

## 1. THE LIVE TEST — RE-RUN, AND DRIVEN RED FOUR WAYS OUT OF FOUR

I extracted the T508 tree to a scratch checkout and ran everything myself against
`fineract_default`.

### 1.1 The test passes against the real schema — reproduced

```
PGHOST=localhost PGPORT=5432 PGUSER=root PGDATABASE=fineract_default \
  go test ./internal/apps/ledger/ -run TestAppendExecutesAgainstTheRealSchema -v -count=1
--- PASS: TestAppendExecutesAgainstTheRealSchema (0.03s)
```
`[VERIFIED: measurement, this fire]`

### 1.2 All FOUR red drives reproduced — the transcript is honest

The brief asked for at least two. I did all four, each by editing the statement in the scratch tree
and re-running against the live schema. **Every error string matches T508's report.**

| red drive | my measured result |
|---|---|
| (a) restore `createdby_id` / `lastmodifiedby_id` | **FAIL** — `ERROR: column "createdby_id" of relation "acc_gl_journal_entry" does not exist (SQLSTATE 42703)` |
| (b) drop the three added columns | **FAIL** — `ERROR: null value in column "created_on_utc" of relation "acc_gl_journal_entry" violates not-null constraint (SQLSTATE 23502)` |
| (c) `submitted_on_date := entry_date` | **FAIL** — `submitted_on_date = "2026-08-24", want "2026-09-03" (the business date, NOT entry_date)` |
| (d) restore the `created_date` / `lastmodified_date` writes | **FAIL** — `created_date = 2026-09-03 10:59:34.019019 +0000 UTC, …; the oracle leaves both NULL on acc_gl_journal_entry` |
| control (unmodified) | **PASS** |

`[VERIFIED: measurement, four separate runs plus three controls, this fire]`

**This test is real.** It is the first thing in this program that could have caught either defect,
and it does catch both, plus the semantic one.

### 1.3 (a) Is the rollback unconditional? — YES

**Structurally.** `defer func() { _ = tx.Rollback(ctx) }()` is registered on the line after `Begin`
succeeds, before every subsequent `t.Fatalf`/`t.Skipf`/`t.Errorf`. `t.Fatalf` exits via
`runtime.Goexit`, which runs deferred functions; a panic runs them too. The only two exits that
precede the defer are the connect failure and the `Begin` failure, and neither has a transaction to
leak. `defer pool.Close()` is registered **earlier**, so LIFO puts the rollback first — the pool is
still open when the rollback runs. `ctx` is `context.Background()`, never cancelled, so the rollback
cannot fail on a dead context. `[VERIFIED: journalentry_test.go:341-352]`

**Empirically.** Before / after a PASS run of the test against `fineract_default`:

| | rows | `max(id)` | rows with `transaction_id = 'T508-EXEC-PROBE'` |
|---|---|---|---|
| before | 2 | 3 | 0 |
| after | 2 | 3 | **0** |

`[VERIFIED: measurement]` **No row survives.** The claim holds.

### 1.4 (b) Does it FAIL, not SKIP, when the oracle is unreachable? — HALF YES. See F-1.

I probed three postures.

| posture | measured |
|---|---|
| **env set, server unreachable** (`PGPORT=5999`) | **FAIL** — `connect: postgres: ping: … connection refused`, package `FAIL`. **Correct: fail-closed.** |
| **env set, wrong database** (`PGDATABASE=postgres`, no Fineract schema) | **SKIP** — `SKIPPED, NOT PASSED: postgres has no GL account / office / user … (ERROR: relation "acc_gl_account" does not exist)`, package reports **`ok`** |
| **no env at all** (the default, and what CI runs) | **SKIP**, package reports **`ok`** |

`[VERIFIED: measurement, three runs]`

The unreachable case is handled correctly. The other two are the fail-open — see **F-1**, which is
about the fact that *nothing in this repository ever sets the env*.

---

## 2. THE DROPPED `CURRENT_TIMESTAMP` WRITES — CORRECT, AND NOW OVER-DETERMINED

T508 dropped the writes to `created_date` / `lastmodified_date` on evidence that the oracle returns
them NULL. The brief asked me to check whether some *other* Fineract path populates them, which
would make the drop diverge in the opposite direction. **It does not.** Six independent lines, two
of which T508 did not cite:

1. **The live rows.** `acc_gl_journal_entry` ids 2 and 3 (the oracle's own API-written rows) carry
   `created_date | (null)` and `lastmodified_date | (null)`. I re-read them directly; every other
   value in T508's capture table also matches byte for byte, including the `.289487` / `.294834`
   microsecond split. `[VERIFIED: live psql, this fire]`
2. **No triggers — anywhere.** `select count(*) from pg_trigger where not tgisinternal` over the
   whole `fineract_default` database returns **0**. Not "none on this table" — **none in the
   database.** `[VERIFIED: measurement]`
3. **No column default.** `information_schema.columns` shows `created_date` and `lastmodified_date`
   as `timestamp without time zone`, `is_nullable = YES`, `column_default = <none>`.
   `[VERIFIED: measurement]`
4. **The JPA mapping cannot reach them.** `JournalEntry extends AbstractAuditableWithUTCDateTimeCustom`
   `[VERIFIED: JournalEntry.java:40]`, whose four `@Column` names come from `AuditableFieldsConstants`:
   `CREATED_BY_DB_FIELD = "created_by"`, `CREATED_DATE_DB_FIELD = "created_on_utc"`,
   `LAST_MODIFIED_BY_DB_FIELD = "last_modified_by"`, `LAST_MODIFIED_DATE_DB_FIELD =
   "last_modified_on_utc"` `[VERIFIED: AuditableFieldsConstants.java:28-31]`. The legacy names
   `createdby_id` / `created_date` / `lastmodified_date` live on a **different** base class,
   `AbstractAuditableCustom` `[VERIFIED: AbstractAuditableCustom.java:43,46,52]`, which
   `JournalEntry` does not extend. **That is where the T503-era column names came from.**
5. **NEW — the migration says so explicitly.** `0025_add_audit_entries_to_journal_entry.xml`,
   changeset `journal-entry-2`, is a `dropNotNullConstraint` on `created_date` and
   `lastmodified_date`; changeset `journal-entry-3` is
   `renameColumn createdby_id -> created_by` / `lastmodifiedby_id -> last_modified_by`.
   `[VERIFIED: pinned source]` Fineract **deliberately stopped writing this pair and renamed the two
   id columns**; that migration is the direct authority for both halves of T508's fix, and T508 did
   not cite it.
6. **The only other hand-written INSERT to this table** names 27 columns and neither of the pair:
   `SavingsSchedularInterestPoster.batchQueryForJournalEntries()`
   `[VERIFIED: SavingsSchedularInterestPoster.java:164-170]`. A repo-wide grep for
   `INSERT INTO acc_gl_journal_entry` finds no third writer.

**Conclusion: dropping the two writes is correct, and keeping them would have been the defect.**
A `CURRENT_TIMESTAMP` write would have made every Go-written row differ from every oracle-written
row on two columns carrying no information — poisoning a shadow-parity window before one was ever
run. `[VERIFIED]`

But see **F-3**: T508 checked one direction of divergence on this table and missed another.

---

## 3. THE COUNTS — RE-DERIVED INDEPENDENTLY FROM `information_schema`. ALL THREE CORRECT.

Method first, because T513 caught T510 getting exactly this class wrong by reading Liquibase XML
instead of the live schema. **I queried the live schema.** I read the Liquibase file too (§2.5), but
only as corroboration of *intent*, never as the source of a count.

```sql
SELECT count(*) FROM information_schema.columns
WHERE table_schema='public' AND table_name='acc_gl_journal_entry'
  AND is_nullable='NO' AND column_default IS NULL;   -->  13
```

| figure | T508 | **my independent re-derivation** | agree? |
|---|---|---|---|
| NOT NULL, no default, total | 13 | **13** | **yes** |
| of those, omitted by the name-corrected pre-fix statement | 4 | **4** | **yes** |
| of those four, server-supplied | 1 (`id`) | **1** | **yes** |
| columns the statement had to gain | 3 | **3** | **yes** |

The 13, enumerated from my own query: `id`, `account_id`, `office_id`, `currency_code`,
`transaction_id`, `entry_date`, `type_enum`, `amount`, `created_by`, `last_modified_by`,
`created_on_utc`, `last_modified_on_utc`, `submitted_on_date`. **Identical to T508's list.**

The pre-fix, name-corrected statement wrote 9 of those 13, omitting `id`, `created_on_utc`,
`last_modified_on_utc`, `submitted_on_date` — **4**. `id` is `is_identity = YES`,
`identity_generation = BY DEFAULT` `[VERIFIED: measurement]`, so omitting it is correct and 3
remain. **After the fix the statement omits only `id`.**

`[VERIFIED: live information_schema, all 31 columns dumped and hand-checked]`

Two things T508 got right that are easy to get wrong, and one it did not mention:
- `reversed` and `manual_entry` are NOT NULL **with** default `false` — no obligation. Confirmed.
- `office_running_balance` / `organization_running_balance` are NOT NULL with default `0` — the
  defaults are how they stay unwritten under I-3. Confirmed.
- **`is_running_balance_calculated`** is a *third* such column (NOT NULL, default `false`) that
  T508 did not name. It is correctly left unwritten and carries no obligation; noted only for
  completeness of the census. `[VERIFIED: measurement]`

**The METHOD is sound and the numbers are right. No finding.**

---

## 4. `submitted_on_date` = BUSINESS DATE, NOT VALUE DATE — VERIFIED, AND NOT A CAPTURE-DAY ARTEFACT

The brief's worry is the right one: the capture ran on 2026-09-03 with `entry_date` 2026-08-24, so
"submitted ≠ entry" could be an artefact of the day the capture happened to run. It is not. Five
independent lines from the pinned source, one of which T508 did not cite:

1. **The constructor.** `this.submittedOnDate = DateUtils.getBusinessLocalDate();`
   `[VERIFIED: fineract-accounting/.../journalentry/domain/JournalEntry.java:136]` — the exact line
   T508 claims. It is set from the business date, and `entryDate`/`transactionDate` are set from the
   request on the surrounding lines. There is no path by which the request's transaction date
   reaches `submittedOnDate`.
2. **The chain.** `DateUtils.getBusinessLocalDate()` = `ThreadLocalContextUtil.getBusinessDate()`
   `[VERIFIED: DateUtils.java:238-240]`, whose map is built by
   `BusinessDateReadPlatformServiceImpl.getBusinessDates()`
   `[VERIFIED: fineract-core/.../businessdate/service/BusinessDateReadPlatformServiceImpl.java:72-84]`:
   `LocalDate tenantDate = DateUtils.getLocalDateOfTenant(); map.put(BUSINESS_DATE, tenantDate);`
   then overwritten from `m_business_date` **only** `if (configurationDomainService.isBusinessDateEnabled())`.
   **Exactly two branches — and the Go port has exactly those two.**
   (Note the module path: this class lives in **`fineract-core`**, not `fineract-provider` as the
   T508 handoff's shorthand citation implies. Immaterial to the claim.)
3. **The tenant zone, not an offset.** `getLocalDateOfTenant()` = `LocalDate.now(getDateTimeZoneOfTenant())`
   and `getDateTimeZoneOfTenant()` = `ZoneId.of(tenant.getTimezoneId())`
   `[VERIFIED: DateUtils.java:64-72]`. A `ZoneId`, read from tenant state. The Go port's
   `SetTenantLocation(*time.Location)` mirrors this correctly and CLAUDE.md's "never hard-code an
   offset" is honoured.
4. **NEW — the backfill settles the semantics on its own.** Migration `0025`, changeset
   `journal-entry-6`, adds the column as
   `<column name="submitted_on_date" type="DATE" valueComputed="created_date"><constraints nullable="false"/>`
   `[VERIFIED: pinned source]`. Fineract backfilled `submitted_on_date` from **`created_date`** — the
   row-creation timestamp — and **not** from `entry_date`. That is a statement of intent independent
   of any capture, on any day: **`submitted_on_date` is the posting day.** T508 did not cite it; it
   is the strongest single piece of evidence for the claim.
5. **A second writer agrees.** `SavingsSchedularInterestPoster` passes
   `DateUtils.getBusinessLocalDate()` into `submitted_on_date` while `entry_date` gets the
   transaction's own date, in the same INSERT `[VERIFIED: SavingsSchedularInterestPoster.java:150-170]`.

**The semantic claim is VERIFIED and does not need re-capture.** What the Kolkata capture cannot
show is the *zone discrimination* — §6.

Also verified while here: `JournalEntryType` is `CREDIT(1)`, `DEBIT(2)`
`[VERIFIED: JournalEntryType.java:23-24]`, Go is `EntryCredit = 1`, `EntryDebit = 2`
`[VERIFIED: money.go:213-215]`, the live rows carry `type_enum = 2` on the debit leg and `1` on the
credit leg `[VERIFIED: live psql]`, and `FindByTransactionID` has an explicit `ORDER BY id`
`[VERIFIED: journalentry_postgres.go]` so the new test's debit-then-credit assertion is
deterministic rather than accidentally passing.

---

## 5. I-4 DISCIPLINE — HELD. T508 KEPT THE LINE IT SAID IT KEPT.

**In the diff.** A case-insensitive sweep of every added line for
`(update|delete)\s+(from\s+)?acc_gl` returns **nothing**. The only occurrences of the tokens
UPDATE/DELETE/TRUNCATE in added lines are **English prose** — the DEC-2 I-4 doc comment, the
handoff's "I did not delete them, deliberately", and three uses of "TRUNCATES" about microsecond
rendering. **No DML mutation of `acc_gl_journal_entry` in code, test setup, fixtures or teardown.**
`[VERIFIED: measurement]` The statement is still one fixed string literal and still an `INSERT`.

**In the world.** T508 said it deliberately left its two seeded journal rows in place rather than
issue the `DELETE` that I-4 exists to forbid. **It held that line:** ids 2 and 3 with
`transaction_id = a2a82d57b7ab` are still present, still `reversed = f`, unchanged
`[VERIFIED: live psql, this fire]`. That is the correct handling and it cost T508 a clean scratch
tenant to do it.

**The ledger invariants guard.** T508 claims the guard is red at the merge base with identical
findings. **I re-derived this rather than accepting it**, running
`.softhouse/guards/check-ledger-invariants.sh` over scratch checkouts of both trees:

| | merge base `10baca08` | T508 `1abd3a11` |
|---|---|---|
| exit | 1 | 1 |
| findings | **10** | **10** |
| finding lines | — | **`IDENTICAL_FINDINGS` (diff empty)** |
| SQL-shaped literals | 377 | 385 |
| exec-family calls | 21 (18 mutating) | 23 (18 mutating) |

All 10 findings are in `internal/apps/savings/**` (7) and `internal/apps/loanproduct/**` (3) —
**T515/T516 territory, correctly untouched.** `[VERIFIED: measurement]` T508's B-3 is accurate to
the digit, including the census deltas.

And the new INSERT is readable by the guard:
`CENSUS DML-classified literal: internal/apps/ledger/journalentry_postgres.go:263:30 INSERT INTO
acc_gl_journal_entry (…` — **`CENSUS`, not `OPAQUE-SQL`, not a finding**
`[VERIFIED: guard output]`. T503's readability repair survives the schema fix, so the guard can
still certify the statement is an INSERT.

---

## 6. THE CAPTURE CAVEAT — PER-VALUE VERDICT (the brief's item 6)

The instance is **not** at the ratified settings: tenant `default`, `Asia/Kolkata` (+05:30),
`rounding-mode = 6` = HALF_EVEN, no MNT-native tenant. CLAUDE.md ratifies `(19, HALF_UP)`, MNT,
`Asia/Ulaanbaatar` (+08). Judgement on each captured value:

| captured value | rounding-sensitive? | zone-sensitive? | verdict |
|---|---|---|---|
| `created_date` / `lastmodified_date` = **NULL** | no | no | **STANDS.** Over-determined by §2 (0 triggers in the whole DB, no default, JPA maps elsewhere, migration dropped the NOT NULL, no other writer). **No re-capture.** |
| `created_by` / `last_modified_by` = `1` | no | no | **STANDS** — `ADMIN_USER_ID`, tenant-independent. |
| `created_on_utc` == `last_modified_on_utc`, in **UTC** | no | **no** — `getAuditOffsetDateTime()` = `OffsetDateTime.now(ZoneOffset.UTC)` reads no tenant `[VERIFIED: DateUtils.java:110-112]` | **STANDS, at insert only** (see F-3). |
| the µs split `.289487` / `.294834` | no | no | not a value; correctly declared uninformative and compare-by-tolerance. |
| `amount` = `250000.250000` in `numeric(19,6)` | **no** — a *scale* fact from the schema, no arithmetic performed, and `250000.25` is exact at scale 6 with no midpoint | no | **STANDS.** Falls squarely in reference-oracle.md's "exact minor-unit quantities with no midpoint — usable, but label the tenant". T508 labels it. |
| `type_enum` 2 debit / 1 credit | no | no | **STANDS** — shape, corroborated from `JournalEntryType.java:23-24`. |
| `office_running_balance` = `0` | no | no | **STANDS** — schema default. |
| **`submitted_on_date` 2026-09-03 vs `entry_date` 2026-08-24** | no | **PARTLY YES** | **SPLIT — see below.** |

**The split, stated precisely because this is the one that matters.**

- The **qualitative** claim — `submitted_on_date` is the posting/business day and is *not*
  `entry_date` — is **zone-independent** and now verified five ways from the pinned source (§4),
  including a migration backfill from `created_date`. **It does not need re-capture.**
- The **discrimination** — that Fineract derives it from the **tenant's zone** rather than from UTC
  or the JVM zone — is what a capture at 10:39 UTC on a `+05:30` tenant cannot deliver, because at
  that instant Kolkata, Ulaanbaatar and UTC are all 3 September.

**Is T508's `[UNVERIFIED]` sufficient? YES.** It names the gap, names the tenant, names the instant
range that would close it, states that the port's behaviour is pinned by unit test rather than by
capture, does **not** propose `T508-CAP-1` as a parity vector, and writes nothing to
`.softhouse/vectors/` — I confirmed the diff touches no vector file. That is the required handling
under the 2026-09-03 correction, and it is the difference between an honest probe and a trap.

**Exactly ONE value must be re-captured after T521, and this is its specification:**

> **RE-CAPTURE R-1 — `submitted_on_date` zone discrimination.** On a restored `Asia/Ulaanbaatar`
> (+08) tenant, `POST /journalentries` at a wall-clock instant in **16:00–23:59 UTC**, with an
> `entry_date` several days in the past. Assert `submitted_on_date == (UTC date) + 1 day`. That is
> the only window in which the tenant zone and UTC disagree, which is exactly why the existing
> capture is silent. Until R-1 lands, no shadow-parity window may be opened on
> `acc_gl_journal_entry.submitted_on_date`.

Nothing else in `T508-CAP-1` requires re-capture. In particular **no value here is
rounding-sensitive at all** — the capture performs no arithmetic, so HALF_EVEN vs HALF_UP never
arises, and T508 says so.

---

## FINDINGS

### F-1 — MEDIUM — the only test that can catch this defect class is opt-in, and *nothing in the repository ever opts in*

`TestAppendExecutesAgainstTheRealSchema` runs only when `PGDATABASE` **and** `PGUSER` are set.

```
grep -rn "PGDATABASE" --include=*.sh --include=*.yml --include=*.yaml --include=*.md --include=*.json .
  (no matches)
```
`[VERIFIED: measurement]` No CI lane, no guard in `.softhouse/guards/`, no script in
`.softhouse/bin/`, no runbook sets it. So in every automated path this program has, the test
**skips**, and `go test ./internal/apps/ledger/` prints exactly `ok` with no `-v`
`[VERIFIED: measurement]`. This is **P-45**: "a guard that only works when someone remembers to run
it enforces nothing." It is the direct successor to the condition T508 itself diagnosed — a
money-core INSERT with no caller and no executing test — and it re-creates a weaker version of it.

A second, sharper edge: when the env **is** set but the target database lacks the Fineract schema,
the test **skips** rather than fails (`PGDATABASE=postgres` → `SKIPPED, NOT PASSED: … relation
"acc_gl_account" does not exist`, package `ok`) `[VERIFIED: measurement]`. Any future misconfigured
lane — wrong database name, wrong search_path, a Go-module database that has not run the Fineract
migrations — will report green.

**Mitigating, and why this is not a rejection.** (i) When the server is genuinely unreachable with
the env set, the test **FAILS** correctly `[VERIFIED: measurement]` — it is not the classic
quiet-pass. (ii) Both skip messages are unusually good: they begin `SKIPPED, NOT PASSED:` and name
what went unchecked. (iii) T508's file allowlist was three files and forbade touching CI or
`.softhouse/guards/**`, so it **could not** have added the lane.

**What is genuinely T508's omission:** its six-item follow-up list does **not** record this. It
records "wire a caller" (a different gap). The enforcement lane should have been follow-up #7.

**Required follow-up (file as a task):** an enforced lane that sets `PG*` at the reference oracle
and runs `go test ./internal/apps/ledger/ -run TestAppendExecutesAgainstTheRealSchema`, plus a
change of the schema-absent branch from `t.Skipf` to `t.Fatalf` **once** a lane exists to guarantee
the schema is present. Do not make it `Fatalf` before that lane exists — that would only convert a
silent skip into a noisy failure for every developer without a database.

### F-2 — MEDIUM — the rollback restores the rows but **not** the identity sequence, and the handoff claims it "leaves nothing behind"

Measured across one PASS run of the DB-backed test:

| | rows | `max(id)` | `acc_gl_journal_entry_id_seq.last_value` |
|---|---|---|---|
| before | 2 | 3 | **18** |
| after | 2 | 3 | **20** |

`[VERIFIED: measurement]` **+2, one per inserted row, permanent.** `nextval` on an identity column
is non-transactional; `ROLLBACK` does not restore it.

This is precisely the movement class `.softhouse/reference-oracle.md` §5 item 1 documents as
**"permanent, non-restoring movement"** that `oracle-state-baseline.sh` **cannot see**, because the
instrument floors on `max(id)` and never reads a sequence. T508's handoff states:

> "The DB-backed test itself leaves nothing behind: it runs inside a transaction it always rolls back."

That is **materially incomplete**, and it is incomplete about the one irreversible-movement class
the canonical record singles out. It is also self-evidently already true of T508's own work: the
sequence stood at **18** against `max(id) = 3` **before I ran anything**, i.e. roughly 15 prior
consumptions from the four red drives and their controls — undisclosed in B-2, which discloses only
the currencies, the 2 GL accounts and the 2 journal rows.

**Not a rejection:** no money moves, no row is written, I-4 is untouched, and running the test at
all is the right call. **But the disclosure must be corrected**, because the next fire will read
"leaves nothing behind" as a licence to run this test against a tenant whose id sequence someone is
relying on.

**My own contribution to this movement, disclosed under reference-oracle.md §3:** across this review
I ran the DB-backed test once plus four red drives plus three controls. Net effect on
`fineract_default`: `acc_gl_journal_entry_id_seq.last_value` **18 → 31** (13 consumed). **Rows
unchanged at 2, `max(id)` unchanged at 3, zero `T508-EXEC-PROBE` rows, `acc_gl_account` unchanged at
2, `m_portfolio_command_source` unchanged at 29** `[VERIFIED: measurement]`. I issued no API call,
no `UPDATE`, no `DELETE`, and created nothing.

### F-3 — MEDIUM — the shadow-parity guidance guards one direction of divergence on this table and misses another: **the oracle UPDATEs journal-entry rows after insert**

T508 correctly identifies `created_date`/`lastmodified_date` as a divergence risk and correctly
flags `created_on_utc`/`last_modified_on_utc` as compare-by-tolerance. It does not mention that
Fineract itself **mutates** rows in `acc_gl_journal_entry` after they are written:

```java
// JournalEntryRunningBalanceUpdateServiceImpl.java:163-164
"UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?, organization_running_balance=?,"
  + "office_running_balance=?, last_modified_by=?, last_modified_on_utc=?  WHERE  id=?"

// JournalEntryRunningBalanceUpdateServiceImpl.java:211
"UPDATE acc_gl_journal_entry SET office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?"
```
`[VERIFIED: pinned source, /Users/buv/fineract @ 426a23544]`

Two consequences that follow-up #5 does not cover:

1. **`office_running_balance` / `organization_running_balance` / `is_running_balance_calculated`
   will be non-zero on the oracle side** once the running-balance job runs, and **0 / false** on the
   Go side forever, because I-3 forbids this port writing them. That is a divergence of exactly the
   kind T508 was trying to avoid when it dropped the `created_date` writes — same table, opposite
   direction. The Go behaviour is **right**; the comparator guidance is what is missing.
2. **`last_modified_on_utc != created_on_utc` on the oracle side after that job.** T508's claim is
   correctly qualified "on insert" in the code comment, so this is not an error — but a comparator
   built from follow-up #5 as written would assert equality and fail on oracle rows that the job has
   touched.

Related and already on the record: reference-oracle.md §5 item 3 notes 8 rows in this tenant already
carry `reversed = t`, flipped by an `UPDATE` the baseline instrument cannot see. **This table is
mutated by the oracle in at least two ways.** A shadow-parity comparator for
`acc_gl_journal_entry` must treat `office_running_balance`, `organization_running_balance`,
`is_running_balance_calculated`, `reversed`, `last_modified_by` and `last_modified_on_utc` as
oracle-mutable, and must fix a point in the job schedule at which it compares.

**Not a defect in the diff** — nothing here writes those columns. It is a gap in the handoff's
parity guidance, and it belongs in `.softhouse/patterns.md` or the comparator task, not in this
branch.

### F-4 — LOW — a confidently-stated **wrong fact about PostgreSQL** in money-core code

`journalentry_postgres.go`, the `auditUTCLayout` doc comment:

> "Go's `.000000` TRUNCATES rather than rounds, **which is the same direction PostgreSQL's own text
> input takes.**"

repeated in the handoff's Unverified list as "PostgreSQL's own text input also truncates."

**PostgreSQL rounds.** Measured on the oracle instance:

```
select '2026-01-01 00:00:00.9999999+00'::timestamptz;  -->  2026-01-01 00:00:01+00
select '2026-09-03 10:39:49.2894875+00'::timestamptz;  -->  2026-09-03 10:39:49.289488+00
```
`[VERIFIED: live PostgreSQL 18.3, this fire]`

**No behavioural consequence, which is why this is LOW:** the Go path formats to exactly 6
fractional digits *before* the value reaches the server, so Postgres never has anything to round,
and the two audit columns are declared compare-by-tolerance anyway. But it is a wrong fact about the
database stated with confidence in the money core, and it makes the `[UNVERIFIED]` JDBC note read
**backwards**: Java's nanosecond-bearing `OffsetDateTime` will be **rounded up** by the server while
Go truncates, so the two implementations differ by up to 1 µs *in a known direction*, not in an
unknown one. The honesty rule is what this program grades on; the comment should be corrected.

Mechanical comment-only fix, but out of my write allowlist. Recorded here.

### F-5 — LOW — `Append` reads the clock twice, so `submitted_on_date` and `created_on_utc` can come from different instants

`resolveSubmittedOnDate()` calls `r.auditClock()`, then `Append` calls `r.auditClock()` again for
`auditUTC` `[VERIFIED: journalentry_postgres.go]`. With the default `time.Now` these are two
different instants. A call that straddles tenant midnight would stamp `submitted_on_date` from
before it and `created_on_utc` from after it. Harmless in practice (nanoseconds apart, no money
involved, and the oracle's own business date is likewise resolved separately from its audit stamp),
and invisible to the tests because they all pin a fixed clock. The clean shape is to read the
instant once in `Append` and pass it into the resolver. Cosmetic.

---

## WHAT I CHECKED AND FOUND NOTHING

So that silence is distinguishable from not looking:

- **Float in the money path** — none, in either edited file or anywhere in `internal/apps/ledger/`
  non-test sources. Amounts are `MinorUnits` integers throughout.
- **Prohibited database engines** — no `mysql`, `mariadb`, `ojdbc`, `oracle.jdbc`, `1521`, no
  non-`pgx` driver introduced. The module still reaches Postgres only through
  `internal/platform/postgres`.
- **I-4** — no `UPDATE`, `DELETE` or `TRUNCATE` against `acc_gl_journal_entry` in code, test setup,
  fixtures or teardown. Verified by grep over added lines and by reading the test end to end.
- **I-3 / G-12** — no balance column written. `office_running_balance`,
  `organization_running_balance` and `is_running_balance_calculated` are absent from the statement
  and keep their schema defaults.
- **Column/expression arity** — 14 target columns, 14 select expressions, 13 unnest arrays with
  `$12` selected twice. Counted by hand and confirmed by the live INSERT succeeding.
- **`ORDER BY` determinism** — `FindByTransactionID` orders by `id`, so the new test's
  debit-then-credit assertion is not accidental.
- **Read-path money safety** — `MinorUnitsFromDecimalText` refuses sub-minor-unit residue rather
  than truncating, so the `numeric(19,6)` → minor-units leg the new test exercises cannot silently
  lose money.
- **Scope** — exactly the three allowlisted files, verified by merge-base diff.
- **Vector store** — the diff writes nothing under `.softhouse/vectors/`; `T508-CAP-1` is correctly
  confined to the handoff and labelled a schema/shape capture.
- **`buildJournalEntryInsertArgs` fixture guard** — the added assertion does fail if the two
  fixtures stop separating `entry_date` from `submitted_on_date`, which keeps red drive (c)
  detectable. Read and confirmed.
- **The refusal path** — `Append` with neither `SetTenantLocation` nor `SetBusinessDate` returns an
  error before any statement is sent (the test passes a nil `postgres.DB`, so reaching the driver
  would panic — a good structural proof that the refusal is early). `2026-2-3` and `2026-02-30` are
  both refused. Read and confirmed; the "no default" reasoning is sound and every alternative
  default T508 rejects is genuinely wrong.

---

## VERDICT

**`APPROVED`.**

The diff is correct where it counts. Every number T508 reported I re-derived from the live
`information_schema` and got the same answer by the same method T513 required; all four red drives
reproduce with the exact error strings claimed; the rollback is unconditional both structurally and
by measurement; the dropped `CURRENT_TIMESTAMP` writes are right and are now supported by two lines
of evidence T508 did not cite, including the migration that dropped their NOT NULL constraint;
`submitted_on_date` really is the business date and that is not a capture-day artefact; I-4 held in
the diff **and** in the world, at the cost of a dirtied scratch tenant T508 disclosed rather than
cleaned; and the non-representative-tenant caveat is handled the way the 2026-09-03 correction
demands.

**The five findings are all disclosure or program-enforcement gaps, none is a money defect, and none
is a ≤10-line mechanical change** — so neither `MICRO-FIX` nor `REJECTED` fits. F-1, F-2 and F-3
should be filed as follow-up tasks before any shadow-parity window opens on this table; F-4 and F-5
are cheap corrections for whoever next touches the file.

**One thing must not get lost in the approval:** this write path still has **no caller**. T508 says
so plainly under Unverified, and it is the right thing to have said. Making the statement executable
and tested is a large step; it is not the same as the ledger having a working write path.

---
*Reviewed independently by T520. Every claim above is marked `[VERIFIED: …]` against a live
measurement, the pinned Fineract source at `426a23544`, or the branch diff. Nothing was accepted on
the strength of T508's transcript.*
