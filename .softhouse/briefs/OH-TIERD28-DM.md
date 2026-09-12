# OH-TIERD28-DM — Tier D: replay LoanRepayment-Part3.feature in MNT, then READ EVERY LOAN'S JOURNAL ENTRIES. CAPTURE ONLY.

Worktree: `/Users/buv/oh-gerege-tierd28` (branch `feat/OHTIERD28DM`)
Work ONLY in that directory (plus the disposable copy `/Users/buv/fineract-tierd`). The driver pushes; never exercise
the push gate. Commit after each step, and tear down even if a step fails.

## Why (read this, then do not search)
The REFUND transaction on an ACTIVE loan (`createJournalEntriesForRefundForActiveLoan`) has been observed ONCE
(loan-p3-mnt loan 19 L71). `LoanRepayment-Part3.feature` (50 scenarios; 26 "REFUND" transaction lines; 4 charge-off lines;
no USD product) should add more, with other portions and on other products.
Repeat the sweep step (OH-TIERD12-CE): after the replay, BEFORE teardown, read every loan's journal entries from the
throwaway.

**Git in this shared repository:** run every `git commit` as `git commit -F <file> </dev/null` with the message file
INSIDE the worktree (delete it after); a commit that inherits stdin can hang. Do NOT create or edit `AGENTS.md` or any
file outside your capture directory (OH-TIERD24-DE added a root AGENTS.md; the driver reverted it).

**Charged-off classification — use exactly this rule:** a leg's transaction is on a charged-off loan only if the
loan's LATEST read-back (highest index) has `chargedOff` true and lists a chargeOff transaction with an EARLIER transaction
DATE than the leg's transaction, or the SAME date and a LOWER id. Order by DATE, not by id: a backdated repayment has a
higher id but posts as not charged off (OH-TIERD26-DJ, chargeoff-p2-mnt/DRIVER-NOTE.md). Undone charge-offs vanish from
the latest read-back (OH-TIERD23-DC).

## Copy, do not re-derive
`.softhouse/capture/tierd-feasibility/merchant-refund-mnt/`: its run script, `sweep-journalentries.py` (change FEATURE, LOG, the
container name), `organize.py`, `build-results.py`, `extract-journalentries.py`, `extract-product-mappings.py`, and
its OWNER.md shape. Rig: `.softhouse/capture/tierd-feasibility/throwaway/` (`preflight.sh`, `down.sh`, `env.sh`).

## Steps — commit after each (`git commit -F <file>`; never TASK.md, never `stage/`)
1. `preflight.sh`, bring up the throwaway, replay **`LoanRepayment-Part3.feature`** (50 scenarios) with the Feign capture on.
   Record PASSED/FAILED per scenario (a failure is recorded, not diagnosed). Commit the result table.
2. Extract with `bin/extract.py` + the copied `organize.py` into `.softhouse/capture/tierd-feasibility/repayment-p3-mnt/`
   (PASSED loans only under `loans/`, sha256 manifests). Commit.
3. **THE NEW STEP — while the throwaway is still UP:** for every loan id the replay created, read
   `GET https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1` with
   `curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd'` — **port 8444, tenant `tierd`, the
   THROWAWAY. Never 8443, never tenant `gerege` or `default`.** Save each body verbatim as
   `journalentries-sweep/loan-<id>.json`, plus a manifest with sha256 and the exact URL. A GET only; no write. Commit.
4. `product-mappings/` with the copied extractor for every product the loans use. Commit.
5. `down.sh` → `teardown-isolation.txt` (12/12 must equal the baseline). Commit.
6. The type join: every sweep leg → its transaction TYPE through the loan read-backs, and for each leg whether the
   loan was CHARGED OFF at that transaction (a non-reversed chargeOff with a LOWER transaction id; use each loan's LATEST
   read-back). OWNER.md: type × charged-off → legs → loans; for `refund` (REFUND_FOR_ACTIVE_LOAN; name the exact type code you see),
   `repayment`, `merchantIssuedRefund`, `payoutRefund`, `creditBalanceRefund` and `interestRefund`, with each refund's portions list the DISTINCT leg shapes (account ids + sides) with one example each (loan,
   tx id, portions, paymentType id) and the count of transactions per shape. A type with no legs is a finding — say so.
   State each loan's currency. Commit.

## THE LESSON FROM THE LAST CAPTURE — read it
OH-TIERD16-CO wedged at the product-mapping step on `grep … "$FEIGN"` written BEFORE `FEIGN=` was assigned: grep read
stdin and never returned. Assign every variable before you use it, and never pipe or grep a file whose path is unset.

## Run every command in the FOREGROUND with a bound
Two earlier capture runs wedged: one waited on a background job (`jobs`), one on a command that never returned.
**Never `&`, never `jobs`, never `wait`, never `sleep` > 60.** Give every long command a bound (`--max-time` for curl;
for Gradle, the copied run script). If a command does not return, note it in OWNER.md and move to the next step.

## Non-negotiables
Standing tenants `gerege` and `default` untouched — proven by the rig. Never write into `/Users/buv/fineract`. Tear
down every `tierd-*` container. Money in integer minor units in anything you write. **Do not touch `nexus/`,
`.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, `.softhouse/maps/`.** PostgreSQL only;
**Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. ~400 iterations; commit the result table by iteration 120.
