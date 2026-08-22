# A2-29 — G-12 measurement: is `acc_gl_journal_entry`'s stored running balance a CACHE or a SECOND SOURCE OF TRUTH?

Task `A2-29`, run `2026-08-21-run2-tierA-gl-accounting-A2`, branch `softhouse/A2-29-running-balance`.
Analyst role, gate measurement. **No recommendation was written before the measurement**, per the task.

Pinned reference oracle (Fineract) source, re-confirmed at the start of this task:

```
$ git -C /Users/buv/fineract rev-parse HEAD
426a23544e8426a38ae43ae404670a0a7e85b9eb
```

Live oracle: `https://localhost:8443/fineract-provider`, `{"status":"UP"}`, tenant `gerege`,
PostgreSQL 18.3 at `localhost:5432`, database `fineract_gerege`. Every `[OBSERVED: …]` claim below
names a capture under `.softhouse/capture/tierA-a2/out/`.

**The answer, stated once, up front: it is a SECOND SOURCE OF TRUTH.** It was made to disagree with
the derived sum by **MNT 2,000,000.00** on this oracle, the disagreement survived **four**
organisation-wide recalculations, Fineract flagged the disagreeing rows
`is_running_balance_calculated = true` throughout, and the wrong number was served through
`GET /journalentries/{id}?runningBalance=true` **and** `GET /glaccounts/{id}?fetchRunningBalance=true`.

---

## (a) Every reader in the pinned checkout, cited

Census method: `grep -rn --include='*.java' -E "office_running_balance|organization_running_balance|
is_running_balance_calculated|officeRunningBalance|organizationRunningBalance|runningBalanceComputed|
isRunningBalanceRequired|fetchRunningBalance"` over `/Users/buv/fineract`, restricted to `/src/main/java/`,
plus a separate sweep of `*.sql`/`*.xml`/`*.json`/`*.yml`. 92 main-source hits. Every one is classified below;
nothing is omitted.

### A.1 The two money columns — READERS

| # | Reader | File:line | What it does |
|---|---|---|---|
| R1 | `JournalEntryReadPlatformServiceImpl` | `fineract-provider/.../journalentry/service/JournalEntryReadPlatformServiceImpl.java:105-107` (SELECT), `:179-181` (`rs.getBigDecimal`) | Adds all three columns to the `/journalentries` projection when `runningBalance=true`. **Contract boundary.** |
| R2 | `GLAccountReadPlatformServiceImpl` | `fineract-accounting/.../glaccount/service/GLAccountReadPlatformServiceImpl.java:75` (SELECT), `:104` (`rs.getLong`) | Adds `organization_running_balance` to the `/glaccounts` projection when `fetchRunningBalance=true`. **Contract boundary.** Read as a **`Long`**, not a `BigDecimal`, from a `numeric(19,6)` column. |
| R3 | `JournalEntryRunningBalanceUpdateServiceImpl` (org path, org column) | `fineract-provider/.../journalentry/service/JournalEntryRunningBalanceUpdateServiceImpl.java:110-116` | **The writer reads its own prior output** to seed the next incremental recompute. |
| R4 | same (org path, office column) | same file `:134-141` | Same, for the per-office seed. |
| R5 | same (office-scoped path) | same file `:194-200` | Same, for the office-scoped recompute. |
| R6 | `GeneralLedgerReport Table` report SQL — projection | `fineract-provider/src/main/resources/db/changelog/tenant/parts/0018_pentaho_reports_to_table.xml:153` (PostgreSQL variant; MySQL variants at `:41`, `:249`, and `0042`/`0044_table_report_query_fix.xml:28`) | `j1.office_running_balance as aftertxn` inside the `details` subquery. **Discarded** — the outer `SELECT` never names `aftertxn`. |
| R7 | same report SQL — predicate | same line | `and je.office_running_balance is not null` in the `openingbalance` subquery. **Gates the row set that produces a money cell.** |

### A.2 `is_running_balance_calculated` — READERS

| # | Reader | File:line | What it does |
|---|---|---|---|
| R8 | `JournalEntryReadPlatformServiceImpl` | `:105`, `:181` | Served as `runningBalanceComputed`. **Contract boundary.** |
| R9 | `GLAccountReadPlatformServiceImpl` | `:129` (list form), `:203` (by-id form) | Restricts the join to `is_running_balance_calculated = true`. |
| R10 | `JournalEntryRunningBalanceUpdateServiceImpl` | `:72-73` (org), `:93-94` (office) | `MIN(entry_date) WHERE is_running_balance_calculated = false` — this is what decides how far back a recompute reaches. |

### A.3 WRITERS, for completeness

| Writer | File:line | What it writes |
|---|---|---|
| Org-scoped recompute | `JournalEntryRunningBalanceUpdateServiceImpl.java:163-164,177-181` | `UPDATE … SET is_running_balance_calculated=TRUE, organization_running_balance=?, office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?` |
| **Office-scoped recompute** | same file `:211-217` | `UPDATE … SET office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?` — **does NOT set the flag and does NOT touch the organisation column.** This asymmetry is measured in §C.4. |
| `SavingsSchedularInterestPoster` | `fineract-savings/.../service/SavingsSchedularInterestPoster.java:164-170`, params at `:150` | Raw-JDBC `INSERT` that hard-codes `false, BigDecimal.ZERO, BigDecimal.ZERO`. A writer only; never reads. |
| The DDL default | `0001_initial_schema.xml:163-171` | `is_running_balance_calculated boolean NOT NULL DEFAULT false`, both balances `DECIMAL(19,6) NOT NULL DEFAULT 0.000000`. Re-read live: `information_schema` confirms `is_nullable = NO`, `column_default = 0`, `numeric_precision 19 / scale 6` [OBSERVED: `A2-473-db-report-predicate.txt` Q6.0]. |

### A.4 The finding that shapes every option — the columns are NOT on the JPA entity

`fineract-accounting/.../journalentry/domain/JournalEntry.java` maps `@Table(name = "acc_gl_journal_entry")`
and declares `@Column` for exactly: `currency_code, transaction_id, loan_transaction_id,
savings_transaction_id, client_transaction_id, share_transaction_id, reversed, manual_entry, entry_date,
type_enum, amount, description, entity_type_enum, entity_id, ref_num, submitted_on_date`.
**Neither running-balance column, nor the flag, appears.** [VERIFIED: `JournalEntry.java:40-41` and its
`@Column` list.] The MapStruct mappers agree explicitly:
`JournalEntryMapper.java:64-66` and `GlAccountMapper.java:54` carry `@Mapping(target = "…RunningBalance",
ignore = true)`.

So on the ORM path — which is how every ordinary journal entry is posted — these columns are **written by
the database default and by nothing else** until a recompute runs. The domain model does not know they
exist.

### A.5 So: written and never read, or depended upon?

**Depended upon, on three distinct surfaces.** They are read by (i) two REST endpoints, (ii) one installed
report's WHERE clause, and (iii) — the one that decides the gate — **their own writer**, which primes each
incremental recompute from the previously stored value rather than re-deriving from the ledger. A column a
system re-reads to compute its own next value is not a projection of the ledger; it is state.

---

## (b) Contract-boundary exposure, OBSERVED

`A2-26` found the columns in a `psql` dump. That is not the boundary. These are the live oracle's own bytes.

### B.1 `/journalentries` — the fields are OPT-IN and ABSENT by default

Without the parameter [OBSERVED: `A2-406-entry14-no-param.json`], `GET /journalentries/14` returns no
`officeRunningBalance`, no `organizationRunningBalance`, no `runningBalanceComputed`.

With it [OBSERVED: `A2-404-entry14-runningbalance.json`], `GET /journalentries/14?runningBalance=true`
returns all three. The list form behaves the same [OBSERVED: `A2-401-…`, `A2-402-…`].

So a vector that never sets `runningBalance=true` cannot expose the column, and no
`/journalentries` cell in the current corpus does.

### B.2 `/glaccounts/{id}?fetchRunningBalance=true` — exposed, and TRUNCATED TO AN INTEGER

[OBSERVED: `A2-409-glaccount4-fetchrunningbal.json`]

```
{"id":4,…,"organizationRunningBalance":4600000}
```

The stored column is `numeric(19,6)`; the served value is a bare integer with no fractional part, because
`GLAccountReadPlatformServiceImpl.java:104` reads it with `rs.getLong(...)`. `GLAccountsApiResourceSwagger.java:74`
declares the field `Long`, and `LoanProductsApiResourceSwagger.java:1002,1025,1060,1095` declares the same
field `Integer` in its nested GL-account shapes — so the documented boundary type disagrees with itself and
with the column. A balance with a non-zero minor-unit part cannot survive this endpoint.

### B.3 `/glaccounts?fetchRunningBalance=true` — **HTTP 500 on PostgreSQL**

[OBSERVED: `A2-408-glaccounts-fetchrunningbal.json`, `A2-455-glaccounts-list-fetchrunningbal.json`, both status `500`]

```
{"timestamp":"2026-08-22T02:41:44.813Z","status":500,"error":"Internal Server Error","path":"/fineract-provider/api/v1/glaccounts"}
```

Root cause, from the oracle's own log:

```
org.postgresql.util.PSQLException: ERROR: syntax error at or near "desc"
  … group by account_id desc, id) t3 … group by t2.account_id desc) t1)
```

`GLAccountReadPlatformServiceImpl.java:127-131` builds `group by account_id desc` — valid MySQL, **not
valid PostgreSQL**. The list form of this reader has never worked on the only database this program
permits. Recorded because it changes what "adopt Fineract's schema" costs: this reader cannot be a parity
target at all.

### B.4 The report surface

`GeneralLedgerReport Table` is installed and live on this oracle (`stretchy_report` id **194**,
`use_report = t`) [OBSERVED: `A2-470-db-report-194-sql.txt`].

Running it [OBSERVED: `A2-471-report-generalledger.json`, `A2-472-report-generalledger-later-start.json`]:

- Output columns are `entry_date, debit_amount, credit_amount, description, openingbalance, transtype,
  cumulative_sum`. **`aftertxn` is not among them** — R6's projection of the stored column really is
  discarded, confirmed by observation and not by reading the SQL.
- `cumulative_sum` and `openingbalance` are both computed by `SUM(…)` over `je.amount` in the query
  itself. The report **derives**.
- `A2-472` (start date `2026-05-01`) serves `openingbalance = 5489549.42`. Re-derived independently in
  integer minor units straight from the ledger: **548 954 942 minor units over 11 rows**
  [OBSERVED: `A2-473-db-report-predicate.txt` Q6.2]. Exact match.
- R7's predicate `office_running_balance is not null` **admits 60 rows and excludes 0**
  [OBSERVED: same file, Q6.1], because the column is `NOT NULL`. It is a no-op *on this schema*.

### B.5 Summary of (b)

The columns reach **three** boundary surfaces: `/journalentries?runningBalance=true` (all three fields,
opt-in), `/glaccounts/{id}?fetchRunningBalance=true` (organisation column only, integer-truncated), and the
GL report's row-set predicate. They are **not** purely internal. But every one of the three is opt-in,
degraded, or inert:

| Surface | Exposure | State on the permitted stack |
|---|---|---|
| `/journalentries?runningBalance=true` | full, `BigDecimal` | works; **absent unless asked for** |
| `/glaccounts/{id}?fetchRunningBalance=true` | organisation column | works, but **truncated to an integer** |
| `/glaccounts?fetchRunningBalance=true` | organisation column | **HTTP 500 — broken on PostgreSQL** |
| `GeneralLedgerReport Table` | predicate only | **admits every row**; supplies no cell |

---

## (c) Cache or second source of truth — what I tried and what happened

A stored balance that always equals the derived sum is a **cache**. One that can drift is a **second
source of truth**. Everything below re-derives the balance **from scratch** — no seed from any stored
value — reproducing `calculateRunningBalance`'s own sign rule
[VERIFIED: `JournalEntryRunningBalanceUpdateServiceImpl.java:220-250`] in the writer's own order
`ORDER BY entry_date, id` [VERIFIED: same file `:258,265`], entirely in **integer minor units**
(`(amount*100)::numeric(19,0)`), with no floating point anywhere.
Query: `.softhouse/capture/tierA-a2/sql/q5-a2-29-running-balance-drift.sql`.

### C.1 Drift was ALREADY PRESENT before I touched anything — back-dated entries

[OBSERVED: `A2-410-db-running-balance-drift.txt`, taken before any mutation]

| `is_running_balance_calculated` | rows | org agrees | **org DISAGREES** | max abs delta (minor) |
|---|---|---|---|---|
| `false` | 34 | 2 | 32 | 720 000 000 |
| **`true`** | 20 | 14 | **6** | **120 000 000** |

The 34 `false` rows store `0.000000`; that is unstarted work, not drift, and the flag says so.
**The six `true` rows are the finding.** Fineract declares them computed and they are wrong by up to
**MNT 1,200,000.00**.

Mechanism, verified in source and matched to the data: `updateRunningBalance()` only recomputes entries
with `entry_date >= MIN(entry_date WHERE is_running_balance_calculated = false)`
[VERIFIED: `:72-79`]. Entry id **25** was inserted after entry id **14** but dated **2026-02-01**, before
id 14's **2026-03-01**. Id 14's stored `5 800 000.00` is exactly the prefix sum over the five account-4
debits that existed when the job last ran; the derived sum is now `7 000 000.00` over six. Nobody edited
anything — a later posting with an earlier date silently invalidated an already-computed row, and the row
kept saying `computed: true`.

This is served at the boundary [OBSERVED: `A2-404-entry14-runningbalance.json`]:

```
"amount":200000.000000,…,"officeRunningBalance":5800000.000000,
"organizationRunningBalance":5800000.000000,"runningBalanceComputed":true
```

### C.2 A full recompute HEALED all of it

[OBSERVED: `A2-420-update-running-balance-org.json` → HTTP 200; `A2-421-db-after-recompute.txt`]

`POST /journalentries?command=updateRunningBalance` with body `{}` — the same
`JournalEntryRunningBalanceUpdateService` the `ACCOUNTING_RUNNING_BALANCE_UPDATE` scheduled job drives
[VERIFIED: `UpdateRunningBalanceCommandHandler.java:38`, `AccountRunningBalanceUpdateTasklet.java:37`].

Result: **54 of 54 rows agree, 0 disagree, both columns, max delta 0.**

**Taken alone this would say "cache, refreshed lazily", and that reading would be wrong.** It only shows
that a recompute reaching back to the earliest stale date re-derives correctly. §C.3 attacks the case where
it does not reach back.

### C.3 The lever that beat the recompute: RETYPE an account after its entries are computed

The sign of every leg is decided by `glAccount.classification_enum` **joined at recompute time**
[VERIFIED: `:225-242`, joins at `:256-257` and `:263-264`], while the recompute never revisits an entry
older than the earliest uncalculated one. Retyping an account changes the sign rule for history the job
will not look at again.

Executed on two GL accounts created for this probe alone — glCode **19929** and **19930**. Nothing already
in the corpus was retyped; gl 2 (the G-10 retype) was not touched; neither probe account is mapped by any
product. Scripts: `run-430-a2-29-drift-probe.sh`, `run-437-a2-29-drift-probe-leg2.sh`.

1. Create 19929 as **ASSET**, 19930 as LIABILITY [OBSERVED: `A2-430-…`, `A2-431-…`, gl ids 33 / 34].
2. Manual JE, `01 July 2026`: **debit 19929 MNT 1,000,000**, credit 19930 the same
   [OBSERVED: `A2-432-je-while-asset.json` → `{"officeId":1,"transactionId":"a28f605fcdeb"}`].
3. Recompute [OBSERVED: `A2-433-recompute-1`].
4. **Retype 19929 ASSET → INCOME**: `PUT /glaccounts/33 {"type": 4}`
   [OBSERVED: `A2-435-retype-asset-to-income.json` → `{"resourceId":33,"changes":{"type":4}}`].
5. Recompute again [OBSERVED: `A2-436-recompute-2`]. **No effect** — nothing was flagged uncalculated, so
   `updateRunningBalance()` found no work.
6. Second manual JE, `01 August 2026`: credit 19929 MNT 500,000
   [OBSERVED: `A2-439-je-after-retype.json`]. Recompute a fourth time
   [OBSERVED: `A2-440-recompute-4`].

Measured [OBSERVED: `A2-441-db-after-retype-and-recompute.txt`], in integer minor units:

| entry | account | class **today** | type | amount | `calc` | **stored org** | **derived org** | **delta** |
|---|---|---|---|---|---|---|---|---|
| 59 | 33 (19929) | 4 INCOME | DEBIT | 1 000 000.00 | `true` | **+100 000 000** | **−100 000 000** | **200 000 000** |
| 60 | 34 (19930) | 2 LIABILITY | CREDIT | 1 000 000.00 | `true` | +100 000 000 | +100 000 000 | 0 |
| 61 | 34 (19930) | 2 LIABILITY | DEBIT | 500 000.00 | `true` | +50 000 000 | +50 000 000 | 0 |
| 62 | 33 (19929) | 4 INCOME | CREDIT | 500 000.00 | `true` | **+150 000 000** | **−50 000 000** | **200 000 000** |

**Entry 62 is the one that settles the gate.** It was posted *after* the retype and computed *fresh* by the
recompute — and it is still wrong by **MNT 2,000,000.00**, because the seed query at `:110-116` primed it
from entry 59's already-stale stored value. The stale number did not merely sit there; it **propagated into
a newly computed row**, which the system then flagged `is_running_balance_calculated = true`.

Account 34, never retyped, agrees on every row. It is the control, and it holds.

Four organisation-wide recomputes ran across this sequence. None healed it.

### C.3.1 The drift was served at the contract boundary, labelled `computed: true`

[OBSERVED: `A2-452-entry62-runningbalance.json`]

```
"glAccountType":{"id":4,"code":"accountType.income","value":"INCOME"},
"entryType":{"id":1,…,"value":"CREDIT"},"amount":500000.000000,
"officeRunningBalance":1500000.000000,"organizationRunningBalance":1500000.000000,
"runningBalanceComputed":true
```

An INCOME account, debited 1,000,000 then credited 500,000, has a derived balance of **−500,000.00**. The
API served **+1,500,000.00** and called it computed.

And on the account surface [OBSERVED: `A2-453-glaccount33-fetchrunningbal.json`]:

```
"type":{"id":4,…,"value":"INCOME"},…,"organizationRunningBalance":1500000
```

The control account is right at the same moment [OBSERVED: `A2-454-glaccount34-fetchrunningbal.json`,
`organizationRunningBalance: 500000`], so this is not a broken endpoint — it is a faithful read of a wrong
stored number.

### C.4 The office-scoped recompute leaves the two columns describing DIFFERENT ledgers

`updateOfficeRunningBalance(officeId)` writes `office_running_balance` only, and sets neither the flag nor
the organisation column [VERIFIED: `:211`], where the organisation-scoped path sets all three
[VERIFIED: `:163-164`].

Executed [OBSERVED: `run-460-a2-29-reversal-and-office-scope.sh`; `A2-460-je-reverse.json` →
`{"transactionId":"a28f614e0263"}`; `A2-461-recompute-office1` with body `{"officeId": 1}`], then measured
before anything else touched it [OBSERVED: `A2-462-db-after-office-scope.txt`]:

| `calc` | rows | org agrees | **org DISAGREES** | office agrees | office disagrees |
|---|---|---|---|---|---|
| `false` | 2 | 2 | 0 | 2 | 0 |
| `true` | 58 | 55 | **3** | **58** | **0** |

Entry 59 at that moment:

```
office_running_balance = −100 000 000   organization_running_balance = +100 000 000
```

**This tenant has exactly one office** (`m_office`: id 1, Head Office, hierarchy `.`
[OBSERVED: `A2-410-…` Q5.4]). With one office the two figures are the same quantity by definition, and the
oracle stored them **MNT 2,000,000.00 apart**. Two stored columns for one ledger fact, updated by two code
paths with different write sets, is a second source of truth by construction — and here it is measured.

Rows 63/64 (the reversal's own entries) additionally show the office column written while
`is_running_balance_calculated` stayed `false` — the flag does not mean "the office column is current".

### C.5 The reversal, on its own, does NOT drift

`POST /journalentries/a28f605fcdeb?command=reverse` [OBSERVED: `A2-460-je-reverse.json`] behaved exactly as
`A2-26` recorded: originals keep their amounts, `reversed` flips, and a new transaction carries the
opposite legs. The recompute sums **all** entries including reversed ones
[VERIFIED: `organizationRunningBalanceSchema()` at `:261-266` has no `reversed` filter], and because the
reversal is itself a pair of real opposite legs the net is right.

After the organisation-scoped recompute [OBSERVED: `A2-463-recompute-org-after-reversal`;
`A2-464-db-after-org-recompute.txt`]: **60 of 60 rows agree, 0 disagree, both columns.**

**This also healed the §C.3 drift** — and *how* it healed matters more than *that* it healed. The reversal
entries were dated `2026-07-01`, on or before entry 59, so `MIN(entry_date WHERE not calculated)` moved
back to `2026-07-01` and the recompute finally revisited the retyped history with a clean (empty) seed.
Boundary confirms [OBSERVED: `A2-480-entry59-after-heal.json` → `−1000000.000000`;
`A2-481-entry62-after-heal.json` → `500000.000000`; `A2-482-glaccount33-after-heal.json` → `500000`].

So the honest statement of the drift's lifetime is: **it survives an unbounded number of recomputes, and is
cleared only if some later posting happens to be back-dated to on-or-before the earliest affected entry.**
In §C.3 the second posting was dated `01 August 2026`, after entry 59, and the drift survived. Nothing in
the system detects it, reports it, or bounds how long it lasts.

### C.6 What I tried and could NOT make drift

Stated as required — a failed attempt to break something is a result, not proof of correctness.

| Attempt | Outcome |
|---|---|
| **Entries across offices** | **NOT TESTED against a multi-office ledger.** The `gerege` tenant has exactly one office. I did not create a second office: it is a structural mutation to a shared oracle other tasks read, and §C.4 already produced an office-vs-organisation disagreement without one. The `office_id`-partitioned cases — an entry moving office, an office hierarchy change, `m_office` re-parenting — are **UNMEASURED**. |
| **Reversal as a drift lever** | Tried, §C.5. **Did not drift.** |
| **The seed query's uncorrelated join** (`:112`, `:137`: `je3` groups by `account_id` but joins on `je.entry_date = je3.date` only, with no `account_id` correlation) | Tried to construct a case. **Could not.** The `ORDER BY je.entry_date DESC` plus first-wins per account appears to re-select each account's own latest row even though the join admits extra candidates. **I could not make this one produce a wrong seed, and I am not claiming it is safe** — only that I did not break it. |
| **The seed query's `LIMIT 10000`** (`:113,138,197`) | **NOT DEMONSTRATED.** With more than 10 000 (account, date) seed rows the seed silently truncates and the missing accounts restart from `BigDecimal.ZERO` (`calculateRunningBalance:221`). A 60-row corpus cannot exercise this. Source-derived hazard, **[UNVERIFIED]**. |
| **Making the report predicate bite** | **IMPOSSIBLE on this oracle.** `office_running_balance` is `NOT NULL`, so no row can be excluded [OBSERVED: `A2-473-…` Q6.0/Q6.1]. The predicate's behaviour against a NULL-tolerant port is **UNVERIFIED** by construction. |
| **`GET /glaccounts?fetchRunningBalance=true`** | Could not measure its drift behaviour at all — it is **HTTP 500** on PostgreSQL (§B.3). |

### C.7 Verdict on (c)

**SECOND SOURCE OF TRUTH.** Not a cache.

A cache can be dropped and rebuilt from the source of truth at any moment and nothing changes. This one
cannot: its own writer reads it back to compute the next value (§A.1 R3–R5), so the stored history is an
*input* to future stored history. Two code paths write overlapping subsets of it (§C.4). Its correctness
depends on a mutable foreign attribute — `acc_gl_account.classification_enum` — that is read at recompute
time and never versioned against the entries it already signed (§C.3). And the one flag that claims to
describe its freshness, `is_running_balance_calculated`, was observed `true` on rows wrong by
**MNT 2,000,000.00** through four recomputes and two REST endpoints.

---

## Artefacts

New captures, `A2-4xx` series (`A2-26` used `A2-300`–`A2-384`; no collision). All under
`.softhouse/capture/tierA-a2/out/`.

| Range | What |
|---|---|
| `A2-401`–`A2-409` | Boundary reads before any mutation, incl. the `500` on the list form |
| `A2-410` | Drift dump, **pre-mutation** — the six `true`-flagged disagreeing rows |
| `A2-420`, `A2-421` | Organisation recompute + post-recompute dump (healed) |
| `A2-430`–`A2-441` | The retype drift probe, incl. `A2-437-…-futuredate` (the `403` refusal, kept) |
| `A2-450`–`A2-455` | The drift, read at the contract boundary |
| `A2-460`–`A2-464` | Reversal + office-scoped recompute + org recompute, with the dump taken between |
| `A2-470`–`A2-473` | The report reader, run live, and the predicate measured |
| `A2-480`–`A2-482` | Boundary re-read after the heal |

Rigs: `run-400`, `run-420`, `run-430`, `run-437`, `run-450`, `run-460`, `run-463`, `run-470`.
SQL: `sql/q5-a2-29-running-balance-drift.sql`, `sql/q6-a2-29-report-predicate.sql` — read-only, integer
minor units throughout. Helpers: `mkje-a2-29.py`, `a2-29-retype-path.py` — neither ever constructs a
`float`; `mkje-a2-29.py` additionally refuses to emit a wire token that a binary-double round trip would
alter, which is T193's own check applied at write time.

**Oracle state changed by this task**, recorded so nobody mistakes it for the state `A2-370` describes:
2 new GL accounts (33 / 19929 now INCOME, 34 / 19930 LIABILITY), 3 manual journal entries, 1 reversal,
1 account retype, 6 running-balance recalculations. Every `is_running_balance_calculated` in the tenant is
now `true` and every stored balance now equals its derived sum.
