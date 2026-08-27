# T287 ARM 2 — blast-radius measurement and the decision

**Written BEFORE anything was created.** The task required measure → decide → (only if safe) create,
in that order, and this file is the record of steps (a) and (b). What actually happened afterwards is in
`ARM2-OBSERVATION.md`; if the two disagree, this file is the prediction and that one is the evidence.

---

## (a) THE MEASUREMENT — pasted rows, not recollection

All from `out/M-01-ledger-state.txt`, `out/M-02-ledger-state-fixed.txt`, `out/M-08-state-before-closure.txt`.
Tenant `gerege`, database `fineract_gerege`, PostgreSQL 18.3.

### Offices — there is exactly ONE

```
 id |    name     | hierarchy | parent_id | opening_date
----+-------------+-----------+-----------+--------------
  1 | Head Office | .         |           | 2009-01-01
(1 row)
```

### `acc_gl_closure` — EMPTY, as `capabilities-ledger.json` claims

```
 id | office_id | closing_date | is_deleted | created_date | comments
----+-----------+--------------+------------+--------------+----------
(0 rows)

 closure_rows
            0
```

The registry's claim "NO GLClosure EXIST IN THIS TENANT" is **CONFIRMED against the live database.**

### Journal entries per office, and every distinct date

```
 office_id | office_name | entries | earliest_entry_date | latest_entry_date | manual_entries
-----------+-------------+---------+---------------------+-------------------+----------------
         1 | Head Office |      60 | 2026-02-01          | 2026-08-01        |             26

 entry_date | entries | manual
------------+---------+--------
 2026-02-01 |      16 |      0
 2026-03-01 |       8 |      0
 2026-04-01 |       4 |      0
 2026-05-01 |       6 |      0
 2026-06-01 |      16 |     16
 2026-06-02 |       4 |      4
 2026-07-01 |       4 |      4
 2026-08-01 |       2 |      2
(8 rows)
```

**Earliest `entry_date` = `2026-02-01`. Latest = `2026-08-01`.** All 60 on office 1.

### Tenant business date

`2026-08-23`. `enable-business-date` is `f` and `m_business_date` is empty, so the effective business date
is today in `Asia/Ulaanbaatar` (+08); `now()` in the database read `2026-08-23 00:09:58+00` = 08:09 on
2026-08-23 in Ulaanbaatar. Empirically bounded from above by arm 1: `2026-08-24` was refused as future,
so the business date is strictly earlier than `2026-08-24`.

### Loans and loan products

7 loans, **all office 1**, all `submittedon_date` = `disbursedon_date` = `2026-02-01`. Loan products 1-21
are `accounting_type = 1` (NONE) and post no journal entries at all; products 22+ are CASH (2) / ACCRUAL
(3) and do post.

### Pre-mutation counters

```
 office_rows 1 | office_max_id 1
 je_rows 60    | je_max_id 64        | earliest 2026-02-01 | latest 2026-08-01
 closure_rows 0| closure_max_id NULL
 closure_seq_last_value 1  | is_called f     <- sequence never used
 je_seq_last_value 64      | is_called t
 command_source_rows 347   | command_source_max_id 347
 loan_rows 7
```

---

## The blast radius is WIDER than manual journal entries — and it is per-office with no hierarchy walk

Two source facts that decide this arm, both re-derived at pinned commit `426a23544`:

1. **The closure lookup is `WHERE closure.office.id = :officeId`, with no parent/hierarchy walk**
   [VERIFIED: `GLClosureRepository.getLatestGLClosureByBranch`, the whole JPQL is a single `@Query` on
   that file]. So a closure is scoped to exactly one office. On a tenant with one office that scoping
   buys nothing — office 1 *is* the tenant.

2. **A closure does not only refuse MANUAL entries.** `AccountingProcessorHelper.checkForBranchClosures`
   contains the identical `!DateUtils.isBefore(closingDate, transactionDate)` test and is called from
   every automatic accounting path: `CashBasedAccountingProcessorForLoan:67`,
   `AccrualBasedAccountingProcessorForLoan:65`, `CashBasedAccountingProcessorForSavings:57`,
   `AccrualBasedAccountingProcessorForSavings:58`, `CashBasedAccountingProcessorForShares:54`,
   `CashBasedAccountingProcessorForClientTransactions:41`, the working-capital processor (4 sites), and
   `JournalEntryWritePlatformServiceJpaRepositoryImpl:362`. Reversal has its own copy at `:392`.
   So a closure at date D on office 1 would also refuse **a back-dated loan disbursement or repayment on
   any accounting-enabled product**, not merely a manual journal entry. That is the real blast radius and
   it is bigger than the registry row implies.

**The refusal boundary is INCLUSIVE.** `!isBefore(closingDate, transactionDate)` refuses whenever
`transactionDate <= closingDate`, so an entry dated **on** the closing date is refused too — even though
the message says "prior to". Any date arithmetic below uses the inclusive boundary.

---

## The task's premise is WRONG on one point, and this is the load-bearing finding

The brief says creating a closure is a *"tenant-wide, hard-to-reverse mutation"* and that after a closure
at D, entries at or before D are **"refused forever"**. Measured against source, **that is not true on
this codebase**:

- **`deleteGLClosure` is a HARD DELETE.** `this.glClosureRepository.delete(glClosure)`
  [VERIFIED: `GLClosureWritePlatformServiceJpaRepositoryImpl.java:135`]. The `GLClosure` entity carries an
  `is_deleted` column but has **no `@SQLDelete` annotation** [VERIFIED: `GLClosure.java:39-62` — `@Entity`,
  `@Table`, no `@SQLDelete`], so the row is genuinely removed, not soft-flagged. The `deleted` field is
  vestigial.
- **The delete is reachable from the public API**: `@DELETE @Path("{glClosureId}")` on
  `@Path("/v1/glclosures")` [VERIFIED: `GLClosuresApiResource.java:58,151-157`].
- **It is permitted for the closure I would create.** `deleteGLClosure` throws
  `GLClosureInvalidDeleteException` only if a *later* closure exists on that branch
  [`:129-134`]. With `acc_gl_closure` empty, the closure I create is the only one and therefore the
  latest, so the delete is allowed.

I flag this rather than quietly relying on it, because the brief instructed me to weigh irreversibility
and the irreversibility is **contingent on a fact the brief got wrong**. If a reviewer disagrees with my
reading of `delete()`, the whole justification below weakens and arm 2 should be re-judged.

## "Use a dedicated office instead" is the WORSE option here, not the safer one

The brief offers a dedicated office as the safe route. On this tenant it is not:

- Only one office exists, so a dedicated office would have to be **created**.
- **Fineract offices cannot be deleted** — `OfficesApiResource` exposes GET/POST/PUT and **no `@DELETE`**,
  and `m_office` is referenced by FK from clients, loans, journal entries and more. Creating an office is
  a *permanent, irreversible* tenant mutation.
- So the "safe" route costs a permanent new row in `m_office` in order to avoid a **deletable** row in
  `acc_gl_closure`. That trades a reversible mutation for an irreversible one. It also changes the
  office population that every future office-hierarchy capture would observe.

**Cost of the dedicated-office route, stated as the brief asked:** one permanent `m_office` row
(id 2), permanently altering `GET /offices` output and the office count that any future hierarchy capture
sees, plus its own command-source audit row — and it still would not be deletable afterwards. Rejected.

---

## (b) THE DECISION — SAFE, PROCEED, with the closure deleted immediately after capture

**Office: 1 (Head Office). Closing date: `2026-01-31`. To be DELETED as soon as the refusals are captured.**

Justification, each point tied to a measured row:

1. **`2026-01-31` is strictly before the earliest existing journal entry (`2026-02-01`).** With the
   inclusive boundary, the closure forbids `transactionDate <= 2026-01-31`. Not one of the 60 existing
   entries, and not one of the 7 loans (all dated `2026-02-01`), falls in that range. So **even if the
   delete failed and the closure were left in place permanently, it would poison nothing that currently
   exists.** That is the property I optimised for: the plan must be safe *without* relying on the delete
   working.
2. **It cannot poison the pending A2 captures.** `tierA-a2/CAPTURE-PLAN.md` §5 lists what is still
   intended: mapping replacement on product update (`PUT /loanproducts/23`), charge-dimension mappings,
   charge-off/write-off reason mappings, `financial_account_type` collision keys, and savings/shares
   mapping keys. **None of these posts a journal entry**, and none is date-sensitive. The one item that
   would touch the ledger — savings — is behind the deposit-activation `user` gate and is explicitly
   out of slice.
3. **The date is in the past, so the create itself will not be refused.** `createGLClosure` rejects a
   future closing date [`:69-72`]; `2026-01-31` is well before the business date `2026-08-23`.
4. **No other fire is competing for the oracle.** The two contended tasks this fire are T273
   (`conformance.sh`, `capture/t273-residue/`) and T285 (a review of T273 under `reviews/t285-review-t273/`).
   Neither takes oracle captures. T275 is already merged. So the create→capture→delete window does not
   race another worker's ledger write.
5. **The window is seconds and the refusals write nothing**, so the ledger itself is untouched throughout.

### What will NOT be restored by the delete — the permanent residue, declared in advance

Honesty about this is the point of the T276 lesson (`ORACLE-STATE-MOVED-BY-T276.md`): identity does not
restore. Predicted permanent residue:

- **`acc_gl_closure_id_seq` advances from `last_value 1, is_called f` to `is_called t`.** The next closure
  any fire creates will get id 2, not id 1. Permanent and unrewindable.
- **`m_portfolio_command_source` gains audit rows** for the CREATE and the DELETE commands (currently 347
  rows, max id 347). Append-only audit; not undone by deleting the closure.

Neither is a ledger mutation and neither changes any money cell. Both are recorded in
`.softhouse/reference-oracle.md` regardless of outcome, because a mutation the next fire cannot see is a
trap — and that applies to residue just as much as to a surviving row.

### What will be captured while the closure exists

Refusing side only, so nothing is ever written to the ledger:

| probe | transactionDate | what it pins |
|---|---|---|
| `A2-01-preclosure-on-date` | `2026-01-31` | **the inclusive boundary** — entry ON the closing date. The message says "prior to"; the code refuses on-the-date too. If this is refused, the message is misleading and a port must copy the CODE, not the prose |
| `A2-02-preclosure-before` | `2026-01-15` | the plain before-closure case |

The accepting side (`2026-02-01`, closing date + 1) is **deliberately not probed**: it would be accepted,
and accepted means writing a journal entry into the reference oracle.

### The abort condition

If the CREATE returns anything other than a success carrying a closure id, **no refusal probe is sent and
nothing further is attempted** — a closure whose id I do not know is a closure I cannot delete.
