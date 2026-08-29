# T438 — INDEPENDENT review of T417 (G-22, the scheduler pin)

**STATUS: IN PROGRESS.** Bars still running. **VERDICT BELOW IS PROVISIONAL.**

Reviewer: T438, fire `20260829-080002`. Branch `softhouse/T438-review-t417`.
Oracle: REACHABLE. PostgreSQL 18.3, container `fineract-db-1`, database `fineract_gerege`.
Pinned Fineract: `git -C /Users/buv/fineract rev-parse HEAD` = `426a23544e8426a38ae43ae404670a0a7e85b9eb`
— verified BEFORE any line number was read out of it.
**Every statement this review issued against the oracle is a SELECT.** All red arms were
manufactured from doctored COPIES of witness files under `/tmp`. Nothing was written to the
shared instance.

## PROVISIONAL VERDICT: APPROVED WITH CONDITIONS

One MAJOR finding (F-T438-1): a re-derived figure that is **wrong**, published as measured,
that contradicts a **correct** predecessor and instructs later readers to distrust the correct
value. Details below. Everything else re-derives clean.

---

## 1. F-T438-1 (MAJOR) — `min_entry_date` — T417 is wrong and T409 was right

T417's handoff (Unverified, line 302) says:

> `min(entry_date) WHERE NOT is_running_balance_calculated` = **2026-01-15** … Note T409 wrote
> the minimum as `2026-05-15`; I read **2026-01-15**. The count is 55 either way, so I did not
> chase the discrepancy — but a later reader should not take `2026-05-15` from T409 without
> re-deriving it.

**Re-derived from the live database, 2026-08-29T00:4xZ:**

```
SELECT min(entry_date), count(*) FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated;
  min_entry_date = 2026-05-15    not_calculated = 18
```
`[VERIFIED: live oracle, fineract_gerege]`

**The correct value is `2026-05-15`. T409 was right; T417 is wrong.**

**Root cause, found in T417's own committed SQL** — `sql/s3-ledger-now.sql`, block `s3c`:

```sql
SELECT min(entry_date) AS min_uncalculated_entry_date,
       count(*) FILTER (WHERE NOT is_running_balance_calculated) AS uncalculated_rows
FROM acc_gl_journal_entry;
```

The `count(*)` carries a `FILTER`. **The `min(entry_date)` does not.** It is the *global*
minimum over all 109 rows, wearing a column alias — `min_uncalculated_entry_date` — that
asserts a predicate the aggregate never applied. `2026-01-15` is indeed the global
`min(entry_date)` (2 rows carry it) `[VERIFIED: entry_date distribution, live]`.

**T417's justification for not chasing it is also false.** "The count is 55 either way" cannot
be true: `count(*) WHERE entry_date >= '2026-01-15'` is **109**, every row in the table. The
55 in T417's own transcript comes from the *second* statement in `s3c`, which uses a correlated
subquery that **does** carry the filter — so T417's 55 was derived from `2026-05-15` while its
prose asserted `2026-01-15`. The two figures it printed side by side are mutually inconsistent
and it reconciled them with a claim that does not hold.

**Fineract source agrees with T409, at the pin**
`JournalEntryRunningBalanceUpdateServiceImpl.java:72-73` `[VERIFIED @ 426a23544]`:
```java
String dateFinder = "select MIN(je.entry_date) as entityDate from acc_gl_journal_entry  je "
        + "where je.is_running_balance_calculated=false ";
```
The restart point job 9 uses **is** the filtered minimum. T417 quotes this line itself, three
paragraphs above the figure that contradicts it.

**Why this is MAJOR and not cosmetic.** The figure is the pre-state of T409's falsifiable
prediction, and T417 filed **FU-T417-2** telling the next reader to re-run `s3c` and compare.
That reader inherits a query whose label lies, a wrong number in prose, and an explicit
instruction to distrust the value that is actually correct. The state has not moved since
either reading (`max(last_modified_on_utc)` is still `2026-08-28 16:01:00.117772+00`, and
`uncalculated_rows` is still 18) — so this is not drift, it is a measurement defect.

**DRIVE:** (a) fix `s3c` to `min(entry_date) FILTER (WHERE NOT is_running_balance_calculated)`;
(b) correct the figure at the site and withdraw the instruction to distrust T409's value;
(c) re-run and confirm 2026-05-15 / 18 / 55.

*(Sections 2-6 and the bar figures follow; review still in progress.)*
