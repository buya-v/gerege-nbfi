# F-2026-09-12 — the STANDING reference oracle (Fineract) writes to itself every night

**Found by:** the driver, reviewing OH-TIERD14-CL: the rig's `throwaway/out/STANDING-baseline.txt` opened at
`gerege-oracle-db acc_gl_journal_entry = 154/184`, `distinct_transaction_id = 57`, where every earlier Tier D
capture that day opened and closed at `150/180` and `55`.

## What wrote the four rows (read-only SQL on gerege-oracle-db, tenant gerege)
`acc_gl_journal_entry` ids 181-184: transactions `L74` (loan 12) and `L75` (loan 10), `m_loan_transaction`
type 10 (ACCRUAL), 11.55 each, entry date 2026-09-03 (the tenant's business date), `created_on_utc`
2026-09-11 16:02:00 = **00:02 Asia/Ulaanbaatar on 2026-09-12**, `created_by` 2 = user **`system`**. The tenant's
scheduler has `Add Periodic Accrual Transactions` active with cron `0 2 0 1/1 * ? *` — 00:02 daily — plus other
daily mutating jobs (Add Accrual Transactions, Apply penalty to overdue loans, Loan Delinquency Classification,
Recalculate Interest For Loans, Generate Loan Loss Provisioning, Post Interest For Savings, ...).

**Not a write by any run of ours**: no run touches the standing oracle's API or SQL for writing; the Tier D rig
compares each run's teardown to that run's own opening baseline (12/12 ok on every capture), which is the right
design precisely because the standing oracle moves on its own.

## Consequences
* A read of the standing oracle is a read AS OF A DATE. Any vector captured from tenant `gerege` must keep citing its
  capture timestamp (they do: capture_ref + sha256 of a dated body); re-reading the same endpoint later may differ.
* An isolation check that compared a run's teardown to an OLDER run's baseline would report a false write. Keep the
  per-run baseline; never reuse a committed baseline across runs.
* Disabling the jobs would itself be a write to the standing oracle's configuration — not done. If a frozen standing
  oracle is ever wanted, that is Buyan's call.
