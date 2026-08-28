# T367 — independent review of T363 (`softhouse/T363-oracle-baseline` @ `8313ab6d`)

**VERDICT: MICRO-FIX.** Three bounded edits, none of them a number, listed in § 9. The load-bearing
design claim survives attack, every money figure re-derives exactly, the fail direction is real and I
regenerated it, and the bar is intact. What does not survive intact is one sentence of the central
guarantee (F1), one fail-open in a shipped `.sh` instrument (F2), and one stale live cardinal left in
the doctrine file this task exists to repair (F3).

Reviewer fired **NO PROBE**. Every statement T367 issued against the oracle is a `SELECT`, and the
review's own closing reading matches its opening: `acc_gl_journal_entry` **71 rows / max id 75**,
`m_portfolio_command_source` **359 rows / max id 359**, `acc_gl_closure` **0 / null**
[`out/DRIVE-GREEN.txt`, `out/r1-counts.sql` output]. **`PROBES.tsv` needs no row for T367.**

---

## 1. What I attacked, and what the attack found

| # | claim under attack | result |
|---|---|---|
| 1 | attribution is **TOTAL** — 359 rows all carry an `Idempotency-Key` | **half true.** Presence is total and is a *schema tautology*; NAMING is not — 339/359 keys are server UUIDs. **F1** |
| 2 | a missing record makes the next run exit 1 (the P-45 argument) | **TRUE, regenerated.** RED-4 reproduced byte-for-byte in shape, plus 4 new red drives I invented |
| 3 | the interpreter guard now refuses `sh` | **TRUE, driven on four shells** — `sh`, `dash`, `zsh`, `ksh`, all exit 3 |
| 4 | the `t305`/`t327` blast radius is **three** pins, not two | **TRUE, driven.** Three of four pinned counters would refuse, in **both** rigs |
| 5 | T359's two HTTP 400s wrote permanent rows | **TRUE.** rows 357/358, `status = 5` |
| 6 | T352's one declared casualty is not a casualty | **TRUE in all three particulars**, re-derived a third time |
| 7 | `run-all.sh` step 0 deletes and regenerates the baseline | **TRUE for t305. OVERSTATED for t327.** **F4** — and t305 is worse than T363 realised: **F5** |
| 8 | the superseding markers supersede rather than restate | **TRUE** — no historical figure was retyped |
| 9 | T363 fired no probe | **TRUE** — opening == closing == my independent reading |
| 10 | the misrouted T365 message was not acted on | **TRUE** — nothing in the diff reflects a different task's subject |
| 11 | the bar is not weakened | **TRUE** — `conformance.sh` exit 0, 46/0, inadmissible 0 |
| — | *(my own selectors, not T363's)* | **one missed live casualty** in the file T363 edited: **F3** |
| — | *(can a probe leave no trace the instrument reads?)* | **yes, three ways.** **F6/F7** |

---

## 2. The load-bearing design claim — RE-DERIVED

### 2.1 The count and the totality

Re-derived by me against the live PostgreSQL, not read from T363 [`sql/r1-counts.sql`,
`sql/r3-status-split.sql`, `sql/r4-key-shape.sql`; outputs in `out/`]:

```
cs_total_rows      359       je_rows          71      ledger_float_cols  0
cs_max_id          359       je_max_id        75      engine  PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1)
cs_null_idem         0       je_rows_gt_64    11
cs_blank_idem        0       je_distinct_txn  31
cs_distinct_idem   359       je_currencies    MNT,USD
cs_gaps_in_id        0       closure_rows      0
```

**359 rows, 0 NULL, 0 blank, 359 distinct.** T363's cardinal is exact and its totality claim about
*presence* is TRUE [VERIFIED: live, T367].

### 2.2 …and why that is not the evidence T363 thinks it is — **F1 (MAJOR, argument)**

```
column_name       | is_nullable | data_type
idempotency_key   | NO          | character varying
```

**`m_portfolio_command_source.idempotency_key` is `NOT NULL`** [VERIFIED: live,
`information_schema.columns`]. So *"all 359 rows carry one"* is not a measurement that could have come
out differently — it is the schema restated. It is evidence of nothing.

The property the instrument actually needs is that the key **names a task**, and that is **not** total:

```
looks_like_uuid  339     not_uuid  20     total 359
uuid-shaped, id <= 352   339
uuid-shaped, id >  352     0
```

**339 of 359 keys are server-generated UUIDs that name nothing** — e.g. row 349
`2658190f-7139-456b-9828-23501f0513c3`. Fineract mints them itself when the caller sends no header:
`IdempotencyKeyResolver.resolve` → `…orElseGet(idempotencyKeyGenerator::create)`, and
`IdempotencyKeyGenerator.create()` is `return UUID.randomUUID().toString()`
[VERIFIED: `fineract-core/…/commands/service/IdempotencyKeyResolver.java:36`,
`IdempotencyKeyGenerator.java:25-29`, pinned commit `426a23544`]. Exactly **20** rows carry a
task-naming key, and **7** of those are above the floor.

So T363's handoff sentence — *"Every command names its task — including every refusal"* — is **false
by 339 rows**. `README.md` carries the saving conditional (*"…if the task named itself in the key"*)
and is right; the handoff and `reference-oracle.md`'s POLICY §2 drop it and are wrong.

**Does this break the instrument? No.** A UUID key does not match `PROBES.tsv`, so an unrecorded probe
is starred UNATTRIBUTED and the run exits 1 — fail-closed. The defect is in the *argument*, and the
argument is load-bearing precisely because a future reader will trust it. It is also a live hazard
T363 half-names elsewhere: a prober who forgets the header still gets a row, still goes red, and is
then **unidentifiable forever** — which is the exact predicament of row 352 that T363 declines to
explain.

---

## 3. The fail direction — REGENERATED, then attacked

`bash drive.sh` extracts the instrument **from the branch** (never from disk) and drives it. Twelve
drives, all as expected [`out/DRIVE-SUMMARY.txt`]:

| drive | mine? | expected | got |
|---|---|---|---|
| `DRIVE-GREEN` | — | 0 | **0** |
| `DRIVE-RED4` — T359's rows removed | regenerated | 1 | **1**, names `a29bd5eaeb1b` and rows 357–359 **only** |
| `DRIVE-RED1` — every attribution row removed | regenerated | 1 | **1** |
| `DRIVE-RED1b` — only the `txn` rows removed | **new** | 1 | **1** |
| `DRIVE-RED2` — container absent | regenerated | 2 | **2** |
| `DRIVE-RED2b` — container up, **database name wrong** | **new** | 2 | **2** |
| `DRIVE-RED5` — registry file missing | **new** | 1 | **1** (refuses; does not treat absence as "nothing to attribute") |
| `DRIVE-RED6` — registry present, floor line deleted | **new** | 1 | **1** |
| `DRIVE-INTERP-{sh,dash,zsh,ksh}` | **new (T363 drove `sh` only)** | 3 | **3** ×4 |

RED-4 is the whole P-45 argument and it holds: remove one task's rows and the next run goes red naming
that task's transactions. **A missing record is what fails.**

The macOS fact behind the exit-3 fix reproduces on this host:
`sh -c 'shopt -qo posix; echo rc=$?; echo $BASH_VERSION'` → `rc=0`, `3.2.57(1)-release`; under `bash` →
`rc=1`. The committed `RED-3-wrong-interpreter.txt` shows the first version running to completion under
`sh` — the defect was real, and the shipped guard closes it on every shell this host has.

### Can a probe be fired that leaves no trace the instrument reads? — **YES, three ways**

**F6 (MINOR).** *A consumed sequence is invisible.* The floor is `max(id)`; the instrument never reads
a sequence. Live: `acc_gl_closure_id_seq` is `last_value 1, is_called t` while `acc_gl_closure` reads
`0 rows / max id null` [VERIFIED: live]. The instrument prints that as pristine — yet
`reference-oracle.md` itself records that consumed sequence as **permanent, non-restoring** movement
and warns the next closure will be id 2. **The one class of irreversible movement the canonical file
already documents is the class the new instrument cannot see.** (It is caught *indirectly*: a closure
create or delete lands a command-source row above the floor — row 351 is exactly such a row.)

**F7 (MINOR).** *Coverage rests on an unstated argument.* The instrument attributes on **2** tables;
the tenant has **281** base tables. Its real coverage claim is *"every API-driven write lands an
`m_portfolio_command_source` row above the floor, so the command floor catches a write to any of the
other 279."* That claim is correct as far as I checked and is **nowhere written down**. Its exception
class is: a write made by **direct SQL**, an **`UPDATE` of a row below the floor** (e.g. flipping
`reversed` — 8 rows already carry `reversed = t` and the instrument never reads that column), and a
**rolled-back transaction**. DDL is covered only by the float check, and that check is free to widen:
there are **0** float columns across the whole 281-table tenant, not just the two ledger tables
[VERIFIED: live].

---

## 4. The three new findings — ADJUDICATED

### 4.1 The third pin exists AND fails — **T363 IS RIGHT**

[`drive-t305-t327-pins.sh`, output `out/DRIVE-T305-T327-PINS.txt`.] I re-implemented the rigs' F5
comparison read-only rather than running `capture.sh` (which would bring a throwaway up and fire
writes at it):

```
t305  baseline taken 2026-08-27T15:38:48Z        t327  baseline taken 2026-08-27T17:31:27Z
 ***  acc_gl_journal_entry        60/64  -> 71/75   WOULD REFUSE       (same)
 ok   acc_gl_closure              0/null -> 0/null                     (same)
 ***  distinct_transaction_id     26     -> 31      WOULD REFUSE       (same)
 ***  m_portfolio_command_source  352/352-> 359/359 WOULD REFUSE       (same)
```

**Three of four pinned counters are stale, in both rigs**, and the third — `m_portfolio_command_source`
— is named by neither T352 nor T359. T363's "three pins, not two" is **VERIFIED and driven**.

### 4.2 "A refused write writes nothing" — **exactly right, not a rationalisation**

Rows 357 and 358 persist at `status = 5`, `action_name = CREATE`, `entity_name = JOURNALENTRY`
[VERIFIED: live]. `5 = ERROR` in `CommandProcessingResultType` at `426a23544`. The distinction is not
rhetorical, it is architectural: `SynchronousCommandProcessingService.executeCommandAttempt` writes the
command source **before** dispatching the handler (`commandSourceService.saveInitial`, then
`executeCommandInTransaction`) [VERIFIED: `SynchronousCommandProcessingService.java:110-150`]. The row
is committed by construction, independent of whether the business transaction commits. So the ledger
and the audit table have **different transactional fates by design**.

**What it means for any future task that treats a 4xx as a no-op:** a 4xx is a no-op *for the ledger
only*. It permanently consumes a command id **and burns the idempotency key** — Fineract's own
`exceptionWhenTheRequestAlreadyProcessed` refuses a retry that reuses a key whose command reached a
terminal state. A refusal probe against the standing oracle is therefore **as irreversible as an
accepted one** for key-reuse purposes, and must be registered in `PROBES.tsv` exactly like a write.
T363 already encodes this (`cmd` rows for `T359-P01/P02`); the reasoning behind it is sound and should
not be softened.

### 4.3 T352's declared casualty — **T363 IS RIGHT, all three particulars, re-derived a third time**

1. `.softhouse/capture/t352-a2-next-tranche/sql/` holds exactly **two** files,
   `q1-t352-residue-rows.sql` and `q2-t352-accrual-reachability.sql`. The cited path does not resolve
   from T352's own directory; the file lives at `.softhouse/capture/tierA-a2/sql/`.
2. It is **A2-26's** query. A2-15's is `q7-a2-15-ledger-state-json.sql`, same directory.
3. **Neither asserts.** `q4:23` projects `j.currency_code` as one of twenty columns; its only
   per-transaction check `GROUP BY j.transaction_id` with no currency predicate. `q7:74-75` emits
   `distinct_currency_codes` as a `json_agg` **projection**. No `WHERE`, no filter, no aggregate
   assertion over currency in either file [VERIFIED: read in full, T367].

**Stated plainly, as asked: T352's blast-radius record was wrong in both directions at once.** It
declared one casualty that is not one, and missed the third standing pin its own probes invalidated.
The instructive part is T363's: the two SQL files **derive**, so they did not rot. What rotted is what
was typed into prose. That is the argument for the instrument, and it is a good one.

*(Unrelated latent issue, recorded because I read the file: `q4:33-36` derives minor units as
`amount * 100`, hard-coded to minor unit 2. It survives the USD row only because USD is also minor
unit 2. Not a casualty of this movement; outside T363's grant and mine.)*

---

## 5. The refusal to repair `t305`/`t327` — **CORRECT SCOPE REFUSAL, not an evasion**

The `run-all.sh` step-0 claim is the load-bearing one and I re-derived it line by line.

**For t305 the claim is fully VERIFIED and understated:**

```
run-all.sh:29   rm -rf "$OUT" "$DIR/req"                     <- UNCONDITIONAL
run-all.sh:33   bash guard-throwaway-isolation.sh > "$OUT/STANDING-baseline.txt"
run-all.sh:53   bash "$DIR/capture.sh"
```

**F5 (MAJOR, new — T363's own argument implies it and did not name it).** t305's `out/` holds **66
committed files**. The `rm -rf` at `:29` is unconditional, so **`bash run-all.sh` on t305 destroys the
LDG-05 admissibility evidence** — the very evidence T363 refuses to delete by hand, deleted by the
rig's own documented entry point, on any invocation. t327 guards against exactly this and t305 does
not. This belongs in FU-T363-2 and it *strengthens* the refusal.

**F4 (MINOR-MAJOR, citation overstated).** T363 writes *"step 0 of **both** `run-all.sh` scripts does
`rm -rf "$OUT"` and then regenerates"* and cites `t327:45,50 then :70`. The line numbers are accurate;
the prose is not. t327's `rm` at `:45` sits inside a branch that first **REFUSES**:

```
run-all.sh:38   if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT" …)" ]; then
run-all.sh:39     if [ "${T327_FORCE_OVERWRITE:-0}" != "1" ]; then
run-all.sh:40-43   echo "REFUSE: $OUT is not empty…" ; exit 1
run-all.sh:45     rm -rf "$OUT"
```

t327's `out/` carries **89 committed files**, so an unforced `bash run-all.sh` on t327 **exits 1 at
step 0 and never reaches `capture.sh`**. The generalisation runs in the direction that favours the
argument, which is the direction to be careful about.

**Does F4 overturn the refusal? No.** Every one of T363's four reasons stands on its own:

- *Delete* — rejected correctly; the recipe **is** the admissibility argument for a capture taken on a
  destroyed instance (`t305/throwaway/run-all.sh:6-12`).
- *Retype the cardinals* — rejected correctly. `STANDING-baseline.txt` is a **capture output** stamped
  `2026-08-27T15:38:48Z`, produced by `guard-throwaway-isolation.sh`. Retyping it makes the file
  disagree with the run that produced it. That is a forged witness and it rots on the next probe.
- *Convert the pin to a query* — rejected correctly; `$now` is already a live `SELECT`
  (`capture.sh:73`). The wanted invariant is a **delta across my own run**, not equality with a file of
  unknown age.
- *Fix the AGE (`-nt` against a run mark)* — the right shape: fail-closed, types no cardinal, never
  rots, turns a silent wrong answer into a named refusal.

And the write grant genuinely excludes those paths. **This is a scope refusal, correctly argued and
correctly escalated as FU-T363-2.** The `[UNVERIFIED]` on `-nt` sub-second resolution is honest.

*(FU-T363-2's "5 sites" is right: `STANDING-baseline.txt` appears in 7 files, but 2 of those are the
`run-all.sh` **producers**; the 5 consumers are t305 `capture.sh`/`capture2.sh`/`down.sh` and t327
`capture.sh`/`down.sh`. Checked, no defect.)*

---

## 6. The instruments themselves

### 6.1 `oracle-state-baseline.sh` — sound, and fail-closed everywhere I pushed

- Interpreter guard refuses `sh`, `dash`, `zsh`, `ksh` (§3). The ordering rationale is correct: the
  non-bash test runs first because `shopt` is not a builtin in dash.
- `q()` folds stderr into stdout, and **that is fail-closed here**, which I checked rather than
  assumed: a mid-run psql failure makes `je_rows`/`cs_rows` non-empty garbage that matches no registry
  row → starred UNATTRIBUTED → exit 1; and `FLOATCOLS` non-`"0"` → exit 1. Driven as `DRIVE-RED2b`.
- A non-numeric or absent floor **refuses** (`DRIVE-RED6`); an absent registry **refuses**
  (`DRIVE-RED5`). Neither is read as "nothing to attribute".
- No unset variable is read as a pass; `set -uo pipefail` is set and `rc` is accumulated explicitly
  rather than inherited from a pipeline.
- `gl 18` / `gl 22` really are derived by an explicit per-account subquery returning `0`, not by a
  `GROUP BY` that would omit the row. I re-ran that query standalone: both `0` at floor and `0` live.

### 6.2 `casualty-sweep.sh` — **F2 (MAJOR): a negative it never measured**

```sh
all=$(git grep "$@" -- .softhouse/ 2>/dev/null)      # casualty-sweep.sh:39
```

Stderr is discarded and the **exit status is never read**. Driven [`drive-sweep-failopen.sh`,
`out/DRIVE-SWEEP-FAILOPEN.txt`]:

```
B) valid selector, genuinely no hits    total=0  archived=0  LIVE=0
C) MALFORMED selector, never ran        total=0  archived=0  LIVE=0     <-- identical
D) git grep rc  MALFORMED = 128    EMPTY-RESULT = 1    HITTING = 0
E) 'git grep' occurrences in the shipped sweep: 4;  exit statuses inspected: 0
```

The information needed to tell "searched and found nothing" from "never searched" **exists** and the
script throws it away — in the instrument whose own header cites T232 (`git grep -E` silently reading
`\b` as a literal `b`) as the reason it exists, and whose stated thesis is *"not found is a statement
about the SEARCH, never about the world"*. This is the repo's recurring fail-open shape reappearing
inside the artefact written to prevent it.

`casualty-sweep.sh` **gates nothing** — no caller reads its exit status — so this is not a bar defect.
It is a defect in the evidence the casualty list rests on. Fix in § 9.

*(Secondary, no action asked: the `ARCHIVE` predicate classes `.softhouse/observations/` as archived,
yet T363's own casualty list correctly names
`observations/20260827-chain2-standing-oracle-baseline.md:21-26` as a real casualty. So the script's
LIVE list is narrower than the finding it supports — the list was not derived from the script alone.)*

---

## 7. The superseding markers, and the one they missed

**They supersede; they do not restate.** Both markers were verified against `main`'s copy of the file:
the `60/64`, `351 → 352` and `26` figures at the old `:906-909` and `:999-1005` are **byte-identical**
before and after — no historical figure was retyped anywhere in the diff. That is T248/T258/T340
applied correctly.

Two notes:

- The handoff cites markers at `:907` / `:917` / `:1001`. Only **two** markers exist. `:907` and
  `:1001` are table rows covered by their section markers. **`:917` is prose, not a table**, and the
  marker's own wording (*"the next two tables"*) does not reach it. Since `:917` **restates** a
  historical fire's figure, the rule says leave it — so the **artefact is right and the handoff's
  enumeration is loose**. No fix needed to the file.
- **F3 (MAJOR, missed casualty) — and it is in the very section T363 cites.**

### F3 — `reference-oracle.md:924` (`:930` on the branch)

```
Across the whole `gerege` audit table the split is **156 PROCESSED / 194 ERROR**, so refusals
are the majority of this tenant's command history
```

Live, re-derived [`sql/r3-status-split.sql`]:

```
status 1  PROCESSED  162          (at or below the floor: 157)
status 5  ERROR      197          (at or below the floor: 195)
total                359
```

This is **present tense** (*"the split **is**"*), it is a **live doctrine** claim about the *whole*
table, it is **NAMED** and not restated — `grep` finds it exactly once in the repository — and it sits
**three lines above** the sentence T363 quotes for correction #2 (*"a fact `reference-oracle.md`
already recorded under T287 and that was forgotten one section later"*). It is uncorrected, unmarked,
and outside the marker's stated scope, which covers a different `###` subsection.

**No selector in `casualty-sweep.sh` matches it** — `grep -c '156 PROCESSED'` over the committed
`out/CASUALTY-SWEEP.txt` returns **0**. My own selector `X1` found it on the first pass
[`drive-independent-sweep.sh`, `out/DRIVE-INDEPENDENT-SWEEP.txt`]. T363's honest
`[UNVERIFIED] that the 11 selectors are exhaustive` was the right thing to write, and it bit.

*(My sweep carries the fix F2 asks for: selector `X11` is deliberately malformed and reports
`*** SELECTOR DID NOT RUN (git grep rc=128). This is NOT "zero hits."`)*

---

## 8. The things I checked that were clean — so silence is distinguishable from not looking

- **Money math, all five accounts, re-derived independently** [`sql/r2-movement.sql`]:
  `gl 16: 16→21`, `gl 17: 4→5`, `gl 18: 0→0`, `gl 21: **8**→13`, `gl 22: 0→0`. **T352's `7 → 12` was
  wrong and T363's `8 → 12 → 13` is right.** Currencies excluding the five registered transactions:
  **`MNT` only**; live: `MNT,USD`. So `a29bcb5d6fcf` really is the first non-MNT entry in this tenant.
- **The floor.** Row 64 is `a28f614e0263`, `2026-08-22`; rows 65–75 are the eleven probe legs, dated
  `2026-08-28`. Nothing else sits above the floor. `acc_gl_journal_entry` has 4 id gaps (5, 8, 13, 22)
  — **all below the floor**, none above; they do not touch any claim made here.
- **Scope.** 15 files, all inside `.softhouse/capture/t363-oracle-baseline/` + `reference-oracle.md` +
  its own handoff. No vector, no `conformance.sh`, no guard, no Go file, no contract file.
- **Non-negotiables over added lines.** `float` / `double` / `real` / `money` hits are the instrument's
  own **detector** and captured transcript text; **0** prohibited-engine tokens (`ojdbc`,
  `oracle.jdbc`, `1521`, MySQL, MariaDB); no `first_name`/`last_name`; no insured/guaranteed language;
  no monetary value in any float form anywhere in the diff.
- **The misroute.** `grep -inE 'fire-program|t365|T361'` over the whole three-dot diff returns exactly
  two hits: an incidental `git grep` line **inside the captured `CASUALTY-SWEEP.txt` transcript**, and
  T363's own disclosure of the misroute in its handoff. `.softhouse/bin/fire-program.sh` and
  `.softhouse/capture/t365-t361-conditions/` do **not** appear in the changed-file list. **Nothing in
  T363's output reflects a different task's subject** [VERIFIED from the diff, not from its word].
- **The bar, re-run by me** [`out/BAR-conformance-t367.txt`]: **exit 0**; probe line **presence tested
  before value** (`grep -c 'oracle probe'` → **1**, then `163: oracle probe UP`); **46 parity PASS / 0
  FAIL**, 7,884 cells; contract-refusal 4/0; self-test 1/0; **ledger parity 7/0**; ledger
  oracle-refusal 6/0; **ledger inadmissible 0**; **inadmissible 0**; **13** wrong ledger
  implementations KILLED. Invoked with `bash`, never `sh`.
  I additionally verified this run *is* a valid check on T363: `conformance.sh` names
  `reference-oracle.md` only in three **comments** and reaches the oracle at exactly one place —
  `grep -nE 'psql|docker exec|fineract-db-1|5432|localhost:8443' .softhouse/conformance.sh` returns the
  **health URL line and nothing else**. T363 changed no file `conformance.sh` reads.
- **The stale vector-store cardinals T363 names are real and are reprinted by the harness.**
  `capabilities-ledger.json` carries the token `SIXTEEN` **3** times (*"gl 16 carries SIXTEEN"*,
  *"gl 16 -> SIXTEEN"*, and T352's own restatement of it) and says *"the live count is now TWENTY,
  gl 17 is FIVE and gl 21 is TWELVE"* — live **21 / 5 / 13**, so TWENTY and TWELVE are wrong and FIVE
  happens to be right. My own conformance transcript carries `SIXTEEN` **2** times: the harness
  restates the stale figure with the authority of a run. FU-T363-3 is correctly raised and its
  instruction — *"the right fix is not a fourth retype"* — is the right instruction.
- **`FIRED NO PROBE`, both tasks.** T363's first observation (`RED-3`, 08:57:22Z) reads 71/75 and
  359/359; its closing green run (09:06:10Z) reads the same; my run (09:25:10Z) reads the same. Neither
  task moved the oracle.

---

## 9. MICRO-FIX — the three edits, none of them a number

Each is inside T363's existing write grant.

1. **`instruments/casualty-sweep.sh:39` — read the exit status (F2).** ~4 lines, mechanical:
   ```sh
   all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?
   if [ "$rc" -ge 2 ]; then
     printf '    *** SELECTOR DID NOT RUN (git grep rc=%s) -- this is NOT "zero hits"\n%s\n' "$rc" "$all"
     return
   fi
   ```
   Red-drivable in one line, already shipped as `drive-sweep-failopen.sh` § C/D, and demonstrated
   working in `drive-independent-sweep.sh` § X11. If the driver judges a control-flow change to need
   its own red drive in a follow-up, that is reasonable — `casualty-sweep.sh` gates nothing, so it
   need not block the merge.

2. **Restore the conditional on the totality claim (F1)** — in `T363.md`, and in
   `reference-oracle.md` POLICY §2 where it says *"every row in the table has one"*. Wording only, no
   number: the **presence** of a key is guaranteed by a `NOT NULL` column and proves nothing;
   **attribution** comes from the naming convention this policy mandates, which today holds for 20 of
   359 rows and for all 7 above the floor. `README.md`'s existing phrasing (*"…if the task named itself
   in the key"*) is the correct model. Delete the sentence *"Every command names its task — including
   every refusal."*

3. **Put a superseding marker over `reference-oracle.md:924` (F3)** — marker only, in the shape T363
   already established, pointing at the instrument. **Do not retype `156 / 194`.**

## 10. Follow-ups for the driver (not merge blockers)

- **FU-T367-1 (MAJOR).** t305's `run-all.sh:29` unconditionally `rm -rf`s **66 committed capture
  files**. Fold into FU-T363-2 and give t305 the non-empty refusal t327 already has. (**F5**)
- **FU-T367-2 (MINOR).** Add the `acc_gl_closure_id_seq` / `acc_gl_journal_entry_id_seq` **sequence**
  `last_value, is_called` to the instrument's derived output, and say in `PROBES.tsv` that a floor on
  `max(id)` does not see a consumed sequence. (**F6**)
- **FU-T367-3 (MINOR).** Write the coverage argument down in `oracle-state-baseline.sh` — two watched
  tables cover 281 because every API-driven write lands a command-source row — together with its three
  exceptions (direct SQL, `UPDATE` below the floor, rolled-back transaction). Widen the float check
  from the two ledger tables to the schema; it is currently **0** across all 281. (**F7**)
- **FU-T367-4 (MINOR).** T363's `[UNVERIFIED]` on row 352 stands. It carries a UUID key, so it is
  **permanently unattributable** — worth one line in `PROBES.tsv` saying so, rather than leaving a
  reader to rediscover it.
- I endorse **FU-T363-1** (wire the instrument, reported and non-gating) and **FU-T363-3** (derive the
  `capabilities-ledger.json` counts, do not retype them a fourth time) as written.

## 11. Recorded because this review is also evidence

- **T367 fired NO PROBE.** Every statement was a `SELECT`; opening and closing max ids identical
  (§ head). **No `PROBES.tsv` row is required for this review**, and none should be added.
- Nothing in this review was accepted from a transcript. Every number above was re-derived by T367
  against the live PostgreSQL, and every red drive was regenerated from the branch (P-22).
- `drive.sh` extracts the artefact under test **from the branch** on each run, so this review cannot
  silently grade a since-edited copy, and T363's files are not duplicated into this commit.
- **What I did NOT check:** the pinned Fineract image digest; the tenant rounding mode; whether any
  promoted vector's *cells* changed (I ran the harness, which is the evidence, and did not separately
  diff the vector store); anything outside `.softhouse/` except the pinned Fineract sources cited by
  path; the `nexus/` Go tree. A selector not in `drive-independent-sweep.sh` was not searched, and that
  script is the record of that.
