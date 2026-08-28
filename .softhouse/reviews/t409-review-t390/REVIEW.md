# T409 — independent review of T390 (`softhouse/T390-baseline-attribution`)

**Reviewer** T409 · **branch** `softhouse/T409-review-t390` · fire 20260828-140005 iter4
**Subject** `softhouse/T390-baseline-attribution`, diff `main...` = 57 files, +10701, head `57a386d7`
**Oracle** REACHABLE the whole review; pinned Fineract `426a23544`; PostgreSQL 18.3, tenant `gerege`
**All observations in this file were taken from the live oracle between 2026-08-28T18:10:36Z and
2026-08-28T18:47:56Z (UTC).** That is 02:10–02:47 on 2026-08-29 in Asia/Ulaanbaatar (+08), i.e.
**about two hours after the 00:01 scheduler sweep this review is about.** The oracle edits itself
nightly; every figure below is re-runnable and none is transcribed from T390.

---

# VERDICT: **APPROVED WITH CONDITIONS**

T390's central claim is **correct and I re-derived all of it independently**: the eighteen legs
`96–113` were written by the Fineract scheduler, by app user 2 `system`, with no
`m_portfolio_command_source` row, and job 11 "Add Accrual Transactions" is the author. "Seven, not
four" is right — I reproduced the pre-append red at **27 starred rows** by running the instrument
against `main`'s registry. The append is **verbatim to the byte**. The `CASUALTIES.md` correction is
**right on all four counts**, including the `guard-throwaway-isolation.sh` generator classification,
which I verified through `run-all.sh:50`. Both drives re-run clean at **6/6** and **5/5** on my
machine, the patch regenerates **byte-identical** and `git apply --check`s clean against the real
tree, and **nothing moved in the oracle**.

The conditions are not about the work T390 did. They are about **one thing it did not look at, one
blast radius it did not drive, and three cardinals/citations that its own committed evidence
refutes.**

The one that matters: **in the same minute, the same scheduler UPDATED 91 pre-existing journal
entries — every ledger row that existed before it ran.** T390 measured the eighteen inserts and
stopped. `last_modified_by` is now **2 `system`** on **all 109** rows of `acc_gl_journal_entry`.
That makes T390's own warning against FU-T390-2 — *"never a rule that waves through user 2"* —
sharper than T390 knew, and it makes exception class **(d)** larger than the header now says.

---

## 0. What I did, so the reader can weigh what follows

| | |
|---|---|
| statements issued | 20 committed `.sql` files, `sql/r1…r20`, each with its own sha256 and transcript under `out/` |
| **every one a SELECT** | no `INSERT`/`UPDATE`/`DELETE`/`POST` was issued by this review, at any point |
| instrument runs | 4: T390's registry (GREEN), `main`'s registry (RED, 27 stars), and two manufactured REDs |
| drives re-run | T390's unit drive (6/6), T390's end-to-end drive (5/5), T390's patch generator (byte-identical) |
| drives I added | `--prove` control/RED pair on the patched harness; `capsql.sh` red/green; an independent two-direction attribution cross-check |
| oracle writes | **zero**, verified by comparing `out/r2` (18:11:50Z) with `out/r18-final-state.txt` (18:45:53Z) |

---

## 1. RE-DERIVING THE SCHEDULER ATTRIBUTION — and what "bracketing" is actually worth

### 1.1 The eighteen legs [`out/r2-je-above-95.txt`, 18:11:50Z]

Eighteen rows, ids **96–113**, three transactions **L32/L33/L34**, six legs each,
`created_by = 2`, `last_modified_by = 2`, `manual_entry = f`, `reversed = f`,
`loan_transaction_id` 32/33/34, currency `MNT`, `entry_date` 2026-05-15 / 06-15 / 07-15.
Write instants span **`16:01:00.100207+00` to `16:01:00.117772+00`** — T390 rounded this to
"`.10`", which is fine but blunts the containment test, so I used the exact endpoints.

`m_appuser` [`out/r9-users.txt`]: `1 mifos`, **`2 system`**, `3 interopUser`. **CONFIRMED.**
T388's own legs carry `created_by = 1` [`out/r15-je-modifications.txt`, the per-minute bucket table:
every bucket before 2026-08-28 16:01 is `created_by 1`; the 16:01 bucket of 18 rows is `created_by 2`].

### 1.2 `m_portfolio_command_source` — CONFIRMED, and one of my own checks was worthless

`count = 379`, `max = 379`, `min = 1` [`out/r8-command-source.txt`]. The tail 351→379 is T352/T359/T388
and stops at `T388-A01-runaccruals`. **There is no row for any of the eighteen legs**, so T391's
observation follows immediately: those legs carry **no idempotency key at all**, and an attribution
instrument keyed on idempotency keys cannot reach them even in principle.

**A measurement of mine that proves nothing, kept rather than deleted.** I also asked
`count(*) WHERE made_on_date >= '2026-08-28 16:00:00+00'` and got **0**. That is not evidence:
`made_on_date` is **NULL on every row in the table** (visible as the blank column in the same
transcript). The real measurement is the one above — `max(id) = 379` — and it is the only one I rely on.

### 1.3 Is it job 11? Yes — and it is stronger than "bracketing"

`job_run_history.start_time`/`end_time` are `timestamp WITHOUT time zone`;
`acc_gl_journal_entry.created_on_utc` is `timestamp WITH time zone`. Comparing them invokes an
implicit cast that depends on the session `TimeZone`, so I **wrote the conversion out explicitly**
and printed the setting [`out/r7-tz-and-explicit-containment.txt`]:

```
TimeZone = Etc/UTC
jrh 12721 | job 11 | Add Accrual Transactions
          | start 2026-08-28 16:01:00.049   end 2026-08-28 16:01:00.12
          | first_write .100207   last_write .117772   contains_all = t
```

Then I asked the sharper question T390 did not: **how many job runs OVERLAP that window at all?**
[`out/r5-jrh-bracket.txt`] — **exactly one**, jrh 12721. And a wide window 15:55–16:10 shows the
whole field [`out/r6-jrh-window.txt`]: 37 runs, every other one ending by `.048` or starting at
16:02. So this is not merely "a bracket exists"; **the bracket is unique, and nothing else was
running.**

**What that establishes, stated honestly.** There is no foreign key from `acc_gl_journal_entry` to
`job_run_history`. Attribution here is **circumstantial, not recorded**. What makes it decisive is
the *conjunction* of four independent facts, not the interval alone:

1. unique overlap (above);
2. the job is named "**Add Accrual Transactions**" and the rows are accrual legs on receivable/income
   accounts 41/42/43 against 37/38/39;
3. the loan transactions created are **32/33/34**, continuing T388's 29/30/31 exactly — T388 accrued
   to `tillDate` 15 April 2026, and these are the 15 May / 15 June / 15 July periods;
4. `created_by = 2 system`, which no API probe in this tenant has ever used.

**And here is why the interval on its own is a weaker claim than it sounds — measured, not argued.**
For the *mutation* window in §2 below, **three** job runs overlap and **two** genuinely contain it
[`out/r19-mutation-proof.txt`]. Containment did not resolve there and had to be settled from source.
T390 got a unique bracket for the inserts and generalised from it; the generalisation does not hold.

### 1.4 Independent cross-check of the registry, both directions [`out/INDEPENDENT-crosscheck.txt`]

I did not trust the instrument's own `awk` matcher. Re-derived with my own:

* live `transaction_id`s above the je floor 64: **12**; registry `txn` rows: **12**; set difference
  in **both** directions: **0 / 0**.
* live command keys above the cs floor 352: **27**; registry `cmd` rows: **27**; both differences **0**.
* registry rows with an empty task field: **0**. Duplicate keys: **0**. Rows with fewer than five
  tab-separated fields: **0** [`out/VERIFY-APPEND.txt` §6].

The instrument never asks the second direction — a registry that **over-claims** (names a
transaction that does not exist) is invisible to it. Today the over-claim count is 0, so this is a
latent weakness, not a live defect. Recorded, not filed as a finding.

---

## 2. F-T409-1 (MAJOR) — THE SCHEDULER ALSO **REWROTE 91 ROWS THAT ALREADY EXISTED**, AND NOTHING IN THIS PROGRAM CAN SEE IT

This is the finding T390's brief asked for and T390 did not take.

### The measurement

I swept **every base table**, generated rather than hand-listed, for anything written at or after
the scheduler window [`out/r11-sweep-created.txt`, `out/r12-sweep-created-date.txt`,
`out/r13-sweep-modified.txt`]:

| sweep | population | result |
|---|---|---|
| `created_on_utc >= 2026-08-28 16:00Z` | 69 base tables carrying that column | `acc_gl_journal_entry` **18**, `m_loan_transaction` **3**, all others 0 |
| `created_date >= …` | 33 base tables | **all zero** |
| **`last_modified_on_utc >= …`** | 71 base tables | **`acc_gl_journal_entry` 109**, `m_loan_repayment_schedule` 3, `m_loan_transaction` 3, `m_loan_charge` 2, `m_loan` 1 |

`acc_gl_journal_entry` has **109 rows** (max id 113; four ids were consumed and never persisted). So
**every single row in the ledger table carries a modification timestamp inside that one minute.**

Decisive test, because "modified" could just mean "stamped at insert" [`out/r19-mutation-proof.txt`]:

```
rows created BEFORE 16:00Z and modified at/after it        : 91
rows where last_modified_on_utc > created_on_utc           : 91
oldest such row was created 2026-08-21 06:03:41.494198+00
those 91 mutations ran 16:01:00.033938 .. 16:01:00.039824
last_modified_by on all 91                                 : 2
```

Ninety-one rows written between 21 and 28 August — **T352's probes, T359's probes, T388's twenty
legs, all of them** — were **UPDATEd** by user 2 at 00:01 Asia/Ulaanbaatar.

### Which job, and by what evidence

**Interval containment does not resolve this one.** Three runs overlap `[.033938, .039824]` and two
contain it: job 30 *Update Trial Balance Details* (which **failed**, `ClassCastException`), job 9
*Update Accounting Running Balances*, job 17 *Recalculate Interest For Loans*.

It is **job 9**, settled from the pinned source rather than from the clock:

> `JournalEntryRunningBalanceUpdateServiceImpl.java` @ `426a23544`
> `:72-76` — `entityDate = MIN(entry_date) WHERE is_running_balance_calculated = false`, then
> `:157` — select **`where je.entry_date >= ?`** (`organizationRunningBalanceSchema`, `:261-266`), then
> `:163-164` — **`UPDATE acc_gl_journal_entry SET is_running_balance_calculated=?, organization_running_balance=?, office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`**

issued through `jdbcTemplate` — **direct SQL, no JPA, no command bus**. The post-state agrees:
91 rows now `is_running_balance_calculated = t` with both running-balance columns populated, and the
18 rows job 11 created afterwards are still `f` [`out/r15-je-modifications.txt`].

### Why this matters more than a curiosity

1. **Exception class (d) as written is too small.** The instrument's header says the scheduler
   *"writes journal entries with no command-source row"*. It also **mutates** them. Class (d) and
   class (c) (*update below the floor*) **intersect**, and T371 recorded (c) as a theoretical gap
   evidenced by 8 old `reversed = t` rows. It is not theoretical. It ran last night, on the watched
   table, on 91 rows, and both floors moved by **zero**.
2. **The census cannot rise on this axis at all.** A `max(id)` floor detects appends. There is no
   arrangement of `PROBES.tsv` under which the instrument goes red because 91 rows were rewritten.
   It printed `ALL MOVEMENT ATTRIBUTED (exit 0)` this morning with every row in the table freshly
   rewritten by a job nobody registered.
3. **T390's bounding argument covers only half the risk.** *"Nothing is left to accrue, so tomorrow's
   00:01 run adds nothing"* is true for **inserts** on loan 8. It says nothing about job 9, which
   restarts from `MIN(entry_date)` of any uncalculated row.

### A falsifiable prediction, registered now [`out/r17-next-run-prediction.txt`]

`MIN(entry_date) WHERE is_running_balance_calculated = false` = **2026-05-15**, and
`count(*) WHERE entry_date >= 2026-05-15` = **55**. Therefore:

> **At 2026-08-29 16:01:00 UTC (00:01 on 2026-08-30 Asia/Ulaanbaatar), job 9 will UPDATE 55 rows of
> `acc_gl_journal_entry`, and `oracle-state-baseline.sh` will still exit 0.**

Re-run `sql/r19` and `sql/r17` after that to confirm or refute. If `last_modified_on_utc` on those
55 rows advances to 2026-08-29 16:01 while the instrument stays green, this finding is established
end to end.

### A second consequence for **vector capture**, which is what this program is for

`office_running_balance` and `organization_running_balance` are **derived balances written into the
ledger table**, and they change overnight without any transaction. Any golden vector or parity cell
captured from `acc_gl_journal_entry` that includes those columns — or `is_running_balance_calculated`,
or `last_modified_by`, or `last_modified_on_utc` — is **not reproducible across a midnight boundary**.
No current vector does; recorded so the next capture task does not discover it the hard way.

**Drive:** `bash .softhouse/reviews/t409-review-t390/capsql.sh r19-mutation-proof` and
`… r13-sweep-modified`; both re-derive from live and neither writes.

---

## 3. F-T409-2 (MAJOR, DRIVEN) — with the wiring applied, an ATTRIBUTION failure is reported by `--prove` as a **REPO-ROOT DIVERGENCE** failure

T390 drove the patch at two levels: the guard function, and `--self-test` end to end. It did not
drive **`--prove`**, and `--prove` is where the wiring misattributes.

`--prove` does not call `run_guards` [`conformance.sh:5278`, `prove` is dispatched directly]. But
`do_prove21` shells out **twice** to `bash conformance.sh --self-test` [`:5166`, `:5175`], and each of
those *does* run `run_guards`. After the patch, each therefore contacts the oracle's database.

I built the patched harness in a **scratch tree only** (`/tmp/t409/t390tree`; the repo's
`.softhouse/conformance.sh` was never touched — sha256 `e8621e6f…` before and after) and drove both
polarities:

| arm | registry | result | transcript |
|---|---|---|---|
| **GREEN control** | the real one | **`PROOFS: 23 passed, 0 failed`, exit 0** | `out/DRIVE-PROVE-GREEN-control.txt` |
| **RED** | a COPY with `txn L32` removed | **`PROOFS: 22 passed, 1 failed`, exit 1** | `out/DRIVE-PROVE-RED-stale-registry.txt` |
| RED, repeated | same | identical | `out/DRIVE-PROVE-RED-stale-registry-2.txt` |

And this is the line a reader gets:

```
PROOF FAIL T201/T199-D1: the repo-root divergence refusal is not as claimed:
  [GREEN(e2e): exit 2 over its OWN root — the guard now refuses everything.]
  [GREEN(e2e): the run did not complete, so the guard cannot be shown to be pass-through.]
```

**`grep -c 'UNATTRIBUTED'` over the whole `--prove` transcript = 0.** The nested run's output is
captured into a shell variable and never printed, so the cause is *invisible*. A worker reading this
concludes that `guard_graded_root_is_this_tree` has become an unconditional refusal. It has not.
Somebody wrote to the shared oracle.

This is exactly the misattribution class **F-T380-2** exists to close, arriving through a new door.

**A remedy exists and I drove it, with the flakiness I hit recorded rather than hidden.** Forcing the
exit-2 carve-out in the nested runs (`ORACLE_BASELINE_DB_CONTAINER` naming no container) restored
**23/23** [`out/DRIVE-PROVE-REMEDY-skip-2.txt`]. My **first** attempt at that same arm produced
`PROOFS: 22 passed, 1 failed` with a different sub-reason and a
`conformance.sh: line 5279: printf: write error: Broken pipe`
[`out/DRIVE-PROVE-REMEDY-skip.txt`] — see F-T409-6. I am **not** claiming the remedy is proven; I am
claiming the defect is, and that a remedy of this shape passed once and needs T399 to drive it
properly.

---

## 4. "SEVEN, NOT FOUR" — CONFIRMED, and the census **can** rise

**Reproduced, not accepted.** I ran the instrument as it stands on `main` — `main`'s registry and
`main`'s instrument, both extracted from the branch, run against the live oracle
[`out/RERUN-instrument-MAIN-registry.txt`]:

```
27 starred rows:  L28 L29 L30 L31 L32 L33 L34   (7 txn)
                  360…379                        (20 cmd)
VERDICT: UNATTRIBUTED MOVEMENT (exit 1).
```

Exactly T390's `RED-baseline-before-append.txt`. **Seven, not four, is right.**

**And it exits 0 with T390's registry** [`out/RERUN-instrument-green.txt`, 18:15:58Z] — `109/113`,
38 distinct transactions, `379/379`, `m_loan 8`, gl 18 and gl 22 both **UNMOVED**.

**A census that cannot rise is a census nobody should read**, so I made it rise, twice, from
**copies** of the registry:

| drive | mutation | result |
|---|---|---|
| `out/RERUN-instrument-RED-txn.txt` | deleted line 195, the `txn L32` row | **exit 1**, stars `L32 legs=6 ids 96-101` |
| `out/RERUN-instrument-RED-cmd.txt` | deleted the `cmd T388-P07-loan-disburse` row | **exit 1**, stars `378 … DISBURSE/LOAN` |

Both arms of the instrument discriminate. Together with §1.4's two-direction cross-check, the
population **is** genuinely fully attributed on the two axes it watches — **and §2 is the axis it
does not watch.**

---

## 5. THE APPEND — verbatim, byte-for-byte [`out/VERIFY-APPEND.txt`, `verify-append.py`]

I checked bytes, not lines:

| check | result |
|---|---|
| in-tree `PROBES-APPEND-T388.tsv` sha256 | `89b9ded0d45805562a318e437c4cfe336ace1778e4e7c612041e3402436520d8` — **exactly T390's claimed digest** |
| same path at the claimed tip `977e37af` | **identical bytes**, 5211 both |
| `main`'s `PROBES.tsv` is a byte **PREFIX** of T390's | **YES** — nothing above the append was retyped, reflowed or re-indented |
| T388's 5211 bytes occur **contiguously** in the appended tail | **YES, at offset 1** — the one preceding byte is a single `\n` separator |
| bytes after the verbatim block | 4812, T390's own scheduler block, carrying exactly **3** registry rows (`txn L32/L33/L34`) |
| every `txn`/`cmd` row in the final file has ≥ 5 tab-separated fields | **0 malformed**, **0** space-for-tab |

And the three generated rows agree with the database, field by field: entry dates 05-15 / 06-15 /
07-15, loan transactions 32/33/34, and the amounts `12356.34` / `8318.85` / `4200.61` interest with
`2500.00` fee and `1200.00` penalty each, matching `out/r2-je-above-95.txt` exactly.

**Nothing was retyped. CONFIRMED.**

---

## 6. `CASUALTIES.md` — the correction is right on every count I could test

**Six pins re-derived live** with the label loop copied out of `capture.sh:70-75`
[`drive/pins-live.sh`, `out/PINS-LIVE.txt`, 18:20:12Z]:

| label | pinned | live | |
|---|---|---|---|
| `acc_gl_journal_entry` | `60/64` | `109/113` | **MOVED** |
| `acc_gl_closure` | `0/null` | `0/null` | unmoved |
| `distinct_transaction_id` | `26` | `38` | **MOVED** |
| `m_portfolio_command_source` | `352/352` | `379/379` | **MOVED** |
| **`m_loan`** | **`7`** | **`8`** | **MOVED** |
| `m_office` | `1` | `1` | unmoved |
| | | | **MOVED = 4**, unmoved = 2 |

**FOUR of six. `m_loan 7` is the false clause. CONFIRMED**, and identical to T390's reading at
17:08:42Z — nothing moved in the intervening 72 minutes.

Same loop against t305's baseline: **`m_loan` and `m_office` are not pinned there at all** — that
file carries exactly four `gerege …` lines. **T388's claim CONFIRMED; the damage is t327's only.**

**The three sites, classified by reading them:**

| site | what the code actually does | T390's classification |
|---|---|---|
| `capture.sh:74` label → **`:82`** `[ "$now" = "$want" ] \|\| refuse …` | string-equality **PIN**, refuses | correct |
| `down.sh:45` label → **`:51`** `if [ "$now" = "$want" ]; then`, **`:54`** `… rc=1` | string-equality **PIN** | correct, **and the `:54 → :51` correction it was handed is right** |
| `guard-throwaway-isolation.sh:121` | reads, then **`:126`** `[ -n "$v" ] \|\| … exit 2`, **`:127`** `say "   gerege $label = $v"` — **no comparison anywhere** | **NOT a pin — the GENERATOR.** correct |

The generator classification is **load-bearing and I verified its mechanism**, not just its absence
of a comparison: `run-all.sh:50` is
`bash "$DIR/guard-throwaway-isolation.sh" > "$OUT/STANDING-baseline.txt"`. So the baseline **is** this
script's stdout. That is exactly why T390's conclusion holds — through `run-all.sh` both rigs
regenerate first and are unaffected; only a hand-typed `bash capture.sh` now refuses, on four labels
rather than three. **A generator misread as a pin would have produced a "fix" that broke the rig.**

**Leaving the old paragraph standing under a superseding block: I judge this CORRECT.** It is not
politeness, it is the file's own rule applied to itself — `CASUALTIES.md` argues three paragraphs
below that `out/STANDING-baseline.txt` must not be retyped because editing a witness forges it. A
correction that silently rewrote T363's true-when-written paragraph would have been the same act on
the file that forbids it. The superseding block is dated, sourced to a committed statement whose
sha256 I verified (`ff838af4…`, matching `out/q9-t327-six-pins-live.sql.sha256`), and states the
verdict in its first line so no reader can meet the stale paragraph without the correction.

---

## 7. THE WIRING REQUEST — **DRIVEN, not merely proposed** (with §3 attached)

I re-ran everything and **did not apply the patch**. `.softhouse/conformance.sh` is unchanged:
sha256 `e8621e6f27cf5cbb08d8f6005dceb51feee5ec3ffe328b725cea5353b2259e95`, `git status` clean of it
throughout.

| | T390 claimed | I measured |
|---|---|---|
| patch generator, anchors asserted unique | refuses otherwise | **4/4 unique**, `PATCH APPLIES CLEANLY`, 6/6 shape checks [`out/RERUN-MAKE-PATCH.txt`] |
| regenerated patch vs committed patch | — | **byte-identical** |
| `git apply --check` against the **real** tree | clean | **exit 0**, file untouched [`out/PATCH-APPLY-CHECK-real-tree.txt`] |
| **UNIT DRIVE** | 6/6 | **6/6** [`out/RERUN-DRIVE-GUARD.txt`] — GREEN control 0; RED-1 rc 1 naming `L32`; GREEN control-2 0; carve-out rc 0 + `ORACLE_STATE_BASELINE = SKIPPED`; instrument-missing rc 1; exit-7 rc 1 |
| **END-TO-END DRIVE** | 5/5 | **5/5** [`out/RERUN-DRIVE-ENDTOEND.txt`] — GREEN exit 0 with the guard's pass line; RED exit 2 naming `L32`; `grep -c 'probe = '` = **0** |
| `--prove` | *not driven* | **§3: the defect** |

**A drive of mine failed first, and the failure is instructive** [`out/RERUN-DRIVE-ENDTOEND-FIRST-ATTEMPT.txt`,
`out/RERUN-E2E-GREEN-FIRST-ATTEMPT.txt`]. My first end-to-end attempt had a **passing RED arm and a
failing GREEN control** — exit 2, but from `guard_dead_path_frontier REFUSED (rc=2) … unreadable
corpus member .softhouse/reviews/t409-review-t390/capsql.sh`, because I had deleted my own review
directory from the scratch root while `git ls-files` still listed it. That is **the same class T390
declared as its own first failure**, reached by a different route, and it is independent
corroboration that a green control failing for an unrelated reason must be **repaired**, never
deleted. I restored the directory and re-ran: 5/5.

**On the sequencing condition T390 states, which I now think is stronger than it wrote it.** The
guard reads `$REPO_ROOT/.softhouse/capture/t363-oracle-baseline/PROBES.tsv`, so **every worktree
reads its own copy**. Any worktree branched before this commit has a registry that does not explain
L28–L34, and after wiring **their bar becomes a hard exit 2** — with the natural repair (append the
rows) unavailable to them if `PROBES.tsv` is held by another task. T390 calls this a scheduling
condition; I agree it is not a reason to decline, and it must be a **hard gate on landing**.

---

## 8. P-84 IN THE RED ARM — the guard is genuinely HARD, and it cannot be read as an outage

Read from the patch itself [`out/conformance-T390-wiring.patch`, hunk H3]:

```
timed_guard guard_oracle_state_attributed       || failed=1   # T390, instrument by T363
```

placed last in `run_guards`, before `guard_cost_census`; `failed != 0` then prints
*"a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass."* **Hard, confirmed by
reading the wiring and by the re-run transcript, which prints that exact line.**

`run_guards` is upstream of the oracle probe, so the refusal carries **no `probe = ` line at all** —
`grep -c` = **0** in my re-run. That is P-84 exactly: *read the absence, not the value*.

**Can it be mistaken for an oracle outage? No, on three independent grounds:**

1. an unreachable database takes the **carve-out** — instrument exit 2 → guard returns **0** with
   `ORACLE_STATE_BASELINE = SKIPPED`; the bar continues. So a real outage does not produce this
   signature at all. Driven in the unit drive's carve-out arm.
2. a genuine oracle outage on the *probe* path prints `probe = down`; this prints **nothing**, and the
   driver's own rule is *park on `exit 2` **AND** `probe != up`* [`conformance.sh:5275`]. Absence is
   not `down`.
3. the refusal names its condition in words: `UNATTRIBUTED MOVEMENT IN THE SHARED REFERENCE ORACLE`,
   followed by the starred row.

**The one caveat, and it is §3.** All three of those hold for the **bar**. Under **`--prove`** the
refusal is swallowed and re-labelled as a repo-root divergence failure. So P-84 holds where T390
tested it and fails to hold one entry point over.

---

## 9. NOTHING WAS WRITTEN TO THE ORACLE — confirmed for T390 and for me

**T390:** `git grep` over its `sql/`, `capsql.sh` and `mk-probes-append-t390.sh` for
`INSERT|UPDATE|DELETE|CREATE TABLE|-X POST|-X PUT|-X DELETE|--data` returns **one hit, and it is the
word "update" inside a comment** describing exception class (c). Every one of its ten statements is a
`SELECT`. Its red was manufactured by `grep -v` on a **copy** of the registry — I re-ran that exact
mechanism and it does not touch the database.

**Me:** all twenty of my statements are `SELECT`s; my two reds are `awk`/`grep` on copies in `/tmp`.

**The measurement** [`out/r18-final-state.txt`, 18:45:53Z — compare `out/r2` at 18:11:50Z and
`out/r8` at 18:12:50Z]:

```
acc_gl_journal_entry rows/maxid          109/113      (unchanged)
distinct transaction_id                  38           (unchanged)
acc_gl_closure rows/maxid                0/null       (unchanged)
m_portfolio_command_source rows/maxid    379/379      (unchanged)
m_loan / m_office                        8 / 1        (unchanged)
acc_gl_account rows/maxid                36/47        (unchanged)
THE PROMOTED PAIR  gl 18 legs            0
THE PROMOTED PAIR  gl 22 legs            0
max created_on_utc                       2026-08-28 16:01:00.117772+00
max last_modified_on_utc                 2026-08-28 16:01:00.117772+00
```

**No promoted account moved** — gl 18 and gl 22 are still at **zero legs**, which is the fact
`capabilities-ledger.json`'s `ledger.accrual.entry` argument rests on. The ledger's most recent write
of any kind is still the scheduler's, 2h45m before I finished. `job_run_history` grew 12721 → 12926
during the review, which is the per-minute jobs turning over and wrote nothing to the ledger.

---

## 10. T390's THREE DECLARED FAILURES — two repairs sound, one citation false

**(1) The symlink scratch roots. SOUND, and independently corroborated.** Directory walkers do not
descend symlinks, so `ledgerguard` and `guard_no_float_in_vectors` censused **zero** files and the
green control failed for a reason unrelated to the patch. Repairing the control instead of deleting
it is the right half of that choice, and the fix (materialise everything, symlink only `.git`) removes
the whole class rather than the two instances. **I hit the same class myself** (§7) from a different
cause and reached the same conclusion. The incidental observation — that both of those censuses are
**fail-closed on an empty population** — is real and visible in the transcripts.

**(2) The dead-path frontier, 108 → 109. SOUND, and the fourth attempt is the valuable one.** T390's
own drive caught a movement T390 caused; it repaired **at the site** rather than widening the pin,
which is what `guard_dead_path_frontier`'s own printed rule demands; and the third repair went red
**identically** because it *quoted the offending token in the comment explaining the fix*. That is a
true and non-obvious property of the census — its corpus is
`git ls-files '.softhouse/*.py' '.softhouse/*.sh'` and its selector matches any quoted string
containing a `.softhouse/` path, **so prose in a tracked script is code as far as the census is
concerned**, and the ellipsis `…` is the sanctioned escape [`census_dead_paths.py:11,29,76`]. T390's
`BAR-2` reads `deadOccurrences=108`, back at pin, and my own bar (§12) reads 108 as well.

**(3) `capsql.sh` and `ON_ERROR_STOP=1`. THE FIX IS REAL. THE CITATION IS FALSE.** → **F-T409-4**.

---

## 11. FU-T390-2 — the warning is RIGHT, WELL-PLACED, and **UNENFORCED**; and my §2 evidence makes it urgent

T390's sketched fix is *"verify `created_by` **and** a bracketing `job_run_history` row"*, with the
standing warning *"never a rule that waves through user 2"*. I judge the **warning correct and the
protection inadequate**, on three measured grounds:

1. **`last_modified_by = 2` is now true of every row in the ledger table** [`out/INDEPENDENT-crosscheck.txt`
   §F: `distinct last_modified_by over the whole ledger table: 2`]. A rule keyed on user 2 would not
   wave through *future* scheduler writes — it would wave through **the entire existing table,
   retroactively, including every probe T352, T359 and T388 ever fired.** T390 wrote the warning
   against a hypothetical; the hypothetical is already the present state.
2. **The bracketing condition does not identify a job.** For the mutation window, three runs overlap
   and two contain (§2). A rule of the form *"user 2 AND some bracketing `job_run_history` row"* can
   at best conclude *"a scheduler did it"* — but T390's own registry format requires naming the job
   and its `job_run_history` id, and that is a stricter thing than the rule can supply.
3. **`job_run_history` is not independent evidence.** It is written by the same process, in the same
   transaction-less way, with no link to the rows. It corroborates; it does not authenticate.

**Condition C3 below states what T417 must do instead.** The warning itself lives in three places
(handoff §5, the instrument header, the `PROBES.tsv` block) and that is good practice — but all three
are **prose**. Nothing fails if T417 ignores them. That is P-45 in miniature, and the remedy is a
**red drive**, not a fourth paragraph.

---

## 12. FINDINGS

| id | severity | one line | drive |
|---|---|---|---|
| **F-T409-1** | **MAJOR** | The same 00:01 sweep **UPDATEd 91 pre-existing ledger rows** (job 9, direct SQL). Class (d) also mutates; class (c) is live, not theoretical; the instrument cannot rise on this axis. | `capsql.sh r19-mutation-proof`, `r13`, `r17`; source `JournalEntryRunningBalanceUpdateServiceImpl.java:72-76,157,163-164,261-266` |
| **F-T409-2** | **MAJOR** | With the wiring applied, an attribution failure surfaces through `--prove` as **`PROOF FAIL T201/T199-D1`** with **zero** mention of attribution — the wrong guard named. | control 23/23 vs RED 22/1, `out/DRIVE-PROVE-*.txt` |
| **F-T409-3** | **MODERATE** | *"Nineteen jobs read `is_active = t`"* — written into the **committed instrument header** and into FU-T390-4 — is wrong. It is **31 of 41**, and 31 distinct jobs ran in the last 24h. T390's **own** `q3-jobs.txt` lists all 41 rows. The blind spot is 63% larger than stated. | `capsql.sh r20-jobs` |
| **F-T409-4** | **MINOR** | *"the fix is visible in q7's `rc=3`"* is false: **every** committed transcript in that directory ends `-- psql rc=0`, q7 included, and the failing first run of q1 was not kept. The fix itself is real — I drove it. | `drive/capsql-on-error-stop.sh` → RED `rc=3`, GREEN `rc=0` |
| **F-T409-5** | **MINOR** | In the `CASUALTIES.md` block whose stated purpose is correcting two citations, the third citation is off by one: the fail-closed-on-empty is `guard-throwaway-isolation.sh:126`; `:127` is the print. | `grep -n` on the file |
| **F-T409-6** | **OBSERVATION** | One `--prove` run on the patched harness produced `line 5279: printf: write error: Broken pipe` and a spurious `PROOF FAIL`; an identical repeat passed 23/23. **Not diagnosed and not attributed to the patch.** Recorded so it is not discovered twice. | `out/DRIVE-PROVE-REMEDY-skip.txt` vs `-2.txt` |

**Not findings, recorded for the next reader:** the instrument never checks the *over-claim*
direction (a registry naming a transaction that does not exist) — today that count is 0; and 192 of
281 base tables carry **no audit column at all** [`out/r14-unmeasurable-tables.txt`], so for those no
"when was this written" question can be asked by anybody, including me.

---

## 13. CONDITIONS — each drivable

**C1 (on FU-T390-1, for T399) — do not land the wiring without driving `--prove`.**
Re-run `bash .softhouse/conformance.sh --prove` on the patched tree twice: once with the real
registry (must be 23/23) and once with a **copy** of the registry with one `txn` row removed. If the
red arm still reports `T201/T199-D1` without the word `UNATTRIBUTED` anywhere in the transcript, fix
it before landing — either by making `do_prove21`'s nested self-tests take the exit-2 carve-out, or
by having the nested refusal's cause reach the reader. **Drive:** `out/DRIVE-PROVE-GREEN-control.txt`
and `out/DRIVE-PROVE-RED-stale-registry.txt` are the reference transcripts.

**C2 — correct "nineteen".** The instrument's class-(d) header and FU-T390-4 both state a cardinal
that is wrong and that the same task's own transcript refutes. Replace it with a **derived** figure
or delete it — the instrument's own header says *"this instrument TYPES NO COUNT"*, and this is a
typed count in that very header. **Drive:** `capsql.sh r20-jobs` → `41 total / 31 active / 10 inactive`.

**C3 (on FU-T390-2, for T417) — class (d) must say MUTATES, and the derived rule must refuse
mutations.** Widen the header to record that the 00:01 sweep both inserts and **rewrites** ledger
rows below the floor, with job 9's `UPDATE` statement cited from source. Then T417's rule must
(i) **name** the job and its `job_run_history` id, refusing when the bracket is not unique — it is not
unique for mutations, three runs overlap; (ii) never be satisfied by `created_by`/`last_modified_by`
alone, because **every row in the table now carries user 2**; and (iii) ship a **red drive** proving
it refuses a user-2 write with no bracketing run, plus a green control. **Drive:** `capsql.sh r19-mutation-proof`.

**C4 — correct the `q7` / `rc=3` citation** in the handoff's declared-failure list, or point it at a
transcript that actually shows a non-zero rc. `drive/capsql-on-error-stop.sh` produces one.

**C5 — correct `:127` → `:126`** in the `CASUALTIES.md` superseding block.

None of C1–C5 requires re-running a probe against the oracle, and none of them touches
`.softhouse/conformance.sh`, which is held by T404.

---

## 14. BAR

Run from a **CLEAN tree AFTER commit**, with `bash`, never `sh`.
Transcripts: `out/BAR-T409-clean-tree.txt` (tree `6a34876c`) and
`out/BAR-2-T409-final-tree.txt` (the final content head). Figures below are from the first;
`out/BAR-SUMMARY.txt` carries the line references.

**P-84 applied, PRESENCE before value:** `grep -c 'probe = '` = **1**, then the value —
`reference oracle (https://localhost:8443/…/health) probe = up`.

**EXIT 0.** Baseline held, every figure read from the transcript:

* **46** parity vectors PASS / **0** FAIL · **7884** cells compared, 93 ungraded
* contract-refusal 4/0 · divergence vectors 1/0 (pinned 1) · self-test fixture 1/0 (excluded)
* ledger cells compared **144** graded, of which **39** are MONEY cells in **int64 minor units**
* exemption census: **every** figure `== pinned` (ledger parity 7, oracle-refusal 6, money cells 39,
  GROUNDED 4, UNGROUNDED 0)
* **14** wrong ledger implementations discovered, **pinned at 14**, all 14 KILLED through the harness
* dead-path frontier **GREEN**, `deadOccurrences=108` — **back at the pin**. This review added four
  tracked `.sh`/`.py` files to the census corpus (1403 → 1410) and moved the frontier by **zero**.
* repo-state attest frontier 11 == pinned 11; temp-path census 18 == pinned

**`.softhouse/conformance.sh` was never edited** — sha256
`e8621e6f27cf5cbb08d8f6005dceb51feee5ec3ffe328b725cea5353b2259e95` before and after. The wiring
patch was checked with `git apply --check` and applied **only inside a `/tmp` scratch tree**.

**Re-run the bar on the merge result regardless** — a transcript is evidence about the tree it ran
on, not about a merge, and T391 is expected to move ledger pins when it lands. Re-baseline by
RUNNING (P-83), never by arithmetic.
