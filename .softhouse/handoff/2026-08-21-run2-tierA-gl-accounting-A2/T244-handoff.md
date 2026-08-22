# T244 — DEC-2 revision 6 PREPARED, NOT LANDED. Gate G-13 block ready for the driver to place.

**Branch:** `softhouse/T244-dec2-rev6-prepared`
**Task:** prepare a DEC-2 revision 6 correcting §4.4's stale evidential reason for `I-5`; raise the gate;
**do not amend the ratified ADR.**
**`docs/adr/` was not touched. `.softhouse/gates.md` was not touched. `.softhouse/vectors/` was not
touched. `nexus/` was not touched.** All four verified as `0 file(s)` in the BAR below.

**A DRIVER CORRECTION ARRIVED MID-TASK** (ugrep not installed; the "five engines" claim dead;
`git grep -E` can FABRICATE; `git grep -P` is sound). **It is addressed in §4.0** — re-derived on my
own fixture, confirmed on every point, refined in two, and the sweep re-verified under sound engines.
**The finding survives it unchanged.**

**THE FOUR THINGS TO READ IF YOU READ NOTHING ELSE:**
1. The §4.4 sentence is **still present and still false**; **8** reversed originals **+ 8** reversing
   legs = **16 rows** re-derived on the live oracle (§1).
2. **A SECOND SITE the task did not name** — §9 item 13, lines 2568-2569 — restates it **in different
   words**. Fixing only line 823 would leave it standing (§1, §2 Hunk B).
3. **DEC-2 still calls itself an unratified draft** although G-11 ratified it (§2 Hunk C).
4. **Do NOT bump `PIN-ledger.json`** when revision 6 lands (§2).

---

## 0. FORK POINT — MEASURED, NOT ASSERTED (P-71, twice falsified), AND `main` MOVED UNDER ME

**At setup**, immediately after `git fetch origin && git rebase origin/main`:

```
git merge-base HEAD origin/main   477dc2da0f9edf3922e7d29e689bc6473289befc
git rev-parse origin/main         477dc2da0f9edf3922e7d29e689bc6473289befc
git rev-parse HEAD                477dc2da0f9edf3922e7d29e689bc6473289befc
```

The rebase reported *"up to date"*. My fork point is **`477dc2d`**, which at that moment **equalled
`origin/main`** and equalled the commit the driver says it ran its baseline bar at.

**THEN `origin/main` MOVED WHILE I WAS WORKING.** At 09:31:44Z the BAR re-measured it:

```
origin/main   8275f8b4ca49ea62b46c4d3d34e98b145f817414     <-- MOVED
merge-base    477dc2da0f9edf3922e7d29e689bc6473289befc     <-- unchanged, still my fork point
```

Five commits landed after my fork:

```
8275f8b DRIVER CATCH: two PENDING task BARs pinned a DEAD vector-store digest — corrected before dispatch
2b8551b patterns: fill the P-73 HOLE, and retitle P-71 whose heading still asserted a dead rule
358c3b9 driver: the oracle PIN FILE did not name the database every ledger vector came from
c0be92b tasks.json: restore 1-space indent (the previous commit reformatted the whole file)
a1b531a wave 1 dispatched (T242, T244, T238, T239) — driver bar green at 477dc2d
```

This is **RESUME's standing instruction confirmed again**: *"`main` is NOT quiescent during a wave."*
`T228` watched it move mid-task; so did I. **Report the sha you MERGED, not the one you LOOKED AT** —
everything below is stamped at **`477dc2d`**, and the driver must re-verify at whatever `main` is when
this merges.

**I checked whether `8275f8b` invalidated my own BAR, because it is precisely about stale BAR pins.**
It does not: it corrects **`T226` and `T235`**, not `T244`. And the digest my brief pinned is still live —

```
vectors digest at my fork 477dc2d  : 8968c559fa613e8642ab030bd0a029c17d147054
vectors digest at new origin/main  : 8968c559fa613e8642ab030bd0a029c17d147054   (UNCHANGED)
```

---

## 1. THE RE-DERIVATION — I DID NOT TRANSCRIBE `A2-34`'s 8 (P-69)

**Instrument:** `.softhouse/capture/t244-dec2-rev6/rederive-reversals.sh` (+ `-part2.sh`).
**Transcripts:** `rederive-reversals.txt`, `rederive-reversals-part2.txt`.
**Stamp:** repo `477dc2da0f9edf3922e7d29e689bc6473289befc`, branch `softhouse/T244-dec2-rev6-prepared`,
measured **2026-08-22T09:22:33Z / 09:23:01Z UTC**, Fineract pin
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, oracle probe `{"status":"UP",...}`,
PostgreSQL `fineract_gerege` via `docker exec fineract-db-1`.

The instrument **resolves and prints the tree it ran in and refuses if `DEC-2` is not under it** —
deliberately, against the fail-OPEN dead-`cd` class.

### The queries and the counts

| # | SQL | Result |
|---|---|---|
| Q1 | `select count(*) from acc_gl_journal_entry` | **60** |
| Q2 | `... where reversed = true` | **8** |
| Q3 | `... where reversal_id is not null` | **8** |
| Q4 | `... where reversed = true or reversal_id is not null` | **8** |
| Q6 | `count(distinct transaction_id)` over Q4's rows | **3** |
| Q9 | `... where id in (select reversal_id ...)` — the REVERSING legs | **8** |
| Q11 | Q4 ∪ Q9 — total reversal-related population | **16** |
| Q8 | **calibration**: `where reversed = true and reversed = false` | **0** |

**`A2-34`'s 8 REPRODUCES EXACTLY, and Q4 refines what it counts.** Q4 = 8, not 16, which proves
`reversed` and `reversal_id` sit on **the same rows** — the 8 are the reversed **originals**. The
**reversing legs are 8 FURTHER rows** (Q9), so the reversal evidence on the oracle is **16 rows over 6
transaction ids in 3 reversal pairs**, not 8. `A2-34`'s arrow notation says the same thing; the bare
number "8 reversal rows" undercounts it, and I am reporting the refinement rather than inheriting the
headline.

```
original 33/34/35 (a28f54bfdaf3) reversed=t -> 38/39/40 (a28f54c1db73)
original 45/46/47 (a28f573f34c7) reversed=t -> 50/51/52 (a28f57412abb)
original 59/60    (a28f605fcdeb) reversed=t -> 63/64    (a28f614e0263)
```

**Q12 — every reversing leg carries an EQUAL `amount` and a FLIPPED `type_enum`, 8 of 8.** That is
I-5's ADDS-A-PAIR half, demonstrated on the live oracle.

**Q7 — the reversal-participating transactions balance in minor units:**
`a28f54bfdaf3` 12500055 = 12500055 (3 legs) · `a28f573f34c7` 12500062 = 12500062 (3 legs) ·
`a28f605fcdeb` 100000000 = 100000000 (2 legs).

**Q13 / the UTC follow-up — and this is why I-5 stays ungraded even with the reason corrected.**
All 16 rows have `last_modified_on_utc > created_on_utc`; the legacy `created_date` /
`lastmodified_date` columns are NULL on every one. So the rows **were updated after insert**, and a
snapshot cannot tell *"Fineract flags and adds"* from *"Fineract flags and rewrites"*. `A2-15` said
exactly this in `invariants.go:36-47` and I confirm it by measurement. (The 02:43:48Z touch on all
twelve of the earlier rows looks like the running-balance recompute — **that is G-12's territory, it
is already an open gate, and I did not pursue it.**)

### The captures the ADR says do not exist

| Artefact | Status | Content |
|---|---|---|
| `A2-348-je-reverse.{req,json,status}` | **200** | `{"transactionId":"a28f57412abb"}`; request comment *"A2-26 reversal probe: the ledger is append-only, a correction is a reversing entry"* |
| `A2-349-je-manual-after-reverse.{json,status}` | **200** | read-back of 3 legs of `a28f573f34c7`, each carrying **`"reversed":true`** |
| `A2-460-je-reverse.{req,json,status}` | **200** | `{"transactionId":"a28f614e0263"}` — a **third** reversal, `A2-29`/G-12 probe |

All under `.softhouse/capture/tierA-a2/out/`.

### VERDICT ON THE DEFECT

**The §4.4 sentence is STILL PRESENT and STILL FALSE at `477dc2d`.**
`docs/adr/DEC-2-gl-accounting-adapter.md:823`, sha256 of the file as read
`a032ada185fd0c2653df14e965d6c0fbb47432898f72009f53c737b6eff39826`, verbatim bytes preserved at
`.softhouse/capture/t244-dec2-rev6/line823-verbatim.txt`.

**AND THERE IS A SECOND SITE THE TASK DID NOT NAME.** §9 item 13, **lines 2568-2569**, restates the
same false claim in different words: *"It cannot today: **no reversal appears**, and the committed
journal dump does not project the reversal columns."* A revision 6 that fixed only line 823 would
leave the falsehood standing one section over — **which is the exact defect class that rejected this
document three times** (a correction landing where NAMED and not where RESTATED). Both sites are in
the proposed diff.

---

## 2. PROPOSED DEC-2 REVISION 6 — A DIFF, **NOT APPLIED**

**Not applied to `docs/adr/`. This is the deliverable, not a landed change.**

### What changes, and what deliberately does not

**CHANGES — evidential reason only:**
- the ground on which `I-5`'s column 4 answer rests (the corpus DOES contain reversals);
- the same ground where §9 item 13 restates it.

**DOES NOT CHANGE — and I checked myself for the temptation, per the task's instruction:**
- **the invariant statement** *"A correction adds a leg pair; it never mutates one"* — untouched;
- **column 5, "Graded today?" = NO** — untouched and still correct: the six `LDG-*` files are the whole
  ledger corpus, none is a reversal, and `capabilities-ledger.json` carries
  `ledger.reversal.entry` with **`"in_graded_domain": false`** [VERIFIED by me at `477dc2d`];
- **the refusal code `ErrNoDiscriminatingVector`** — untouched. Only its *stated ground* moves, from
  *"no reversal capture exists"* to *"no reversal capture has been PROMOTED to a vector"*. The adapter
  returns the same thing on the same input;
- **the rule paragraph** *"DEC-2 obliges I-1 through I-5 … and grades none of them today"* — untouched;
- the `A2-150` clause and the `A2-8` clause, both of which are **still true** and are kept (see below).

**I FOUND NO OBLIGATION I WANTED TO CHANGE.** If a later reader concludes I-5's *refusal code* should
change now that captures exist, **that is a different and much larger gate** — it would narrow or
re-shape the graded domain — and it must be raised separately, not folded into a reason-correction.

### Why the kept clauses are kept

I re-verified both rather than deleting them with the false generalisation they were attached to:

- **`A2-150`'s dump projects neither `reversed` nor `reversal_id`** — TRUE. `grep -c` over
  `.softhouse/capture/tierA-a2/out/A2-150-db-final-state.txt` returns **0** for both column names, and
  its journal section is **6 rows, three ordinary pairs** at 1200000.000000 each — the six data rows
  at **lines 65-70** (section 61-72), which is exactly the range DEC-2's own `I-1` row cites.
  The clause is true; the **error was generalising from it to "the corpus"**. A2-150 is a snapshot
  taken when the table held **6** rows; it now holds **60**.
- **`A2-8`'s grading table lists no reversal grading** — carried forward **`[NOT RE-OPENED HERE]`**,
  exactly as revisions 1-5 marked it. **Scope: I did not open A2-8.**

### ⚠ A LANDING HAZARD I MEASURED — **DO NOT BUMP `PIN-ledger.json` WHEN REVISION 6 LANDS**

Every ledger vector declares `"dec2_revision": 5`, and the harness **enforces it**:

```go
// nexus/internal/apps/ledger/conformance/admit.go:49-52
if opts.Pin != nil {
        if v.DEC2Revision != opts.Pin.DEC2Revision {
                add("dec2_revision %d but the store pins %d", v.DEC2Revision, opts.Pin.DEC2Revision)
```

The comparison is **vector against `.softhouse/vectors/PIN-ledger.json`** (`"dec2_revision": 5`) — it
**never reads the ADR file**. So landing revision 6 under `docs/adr/` **breaks nothing by itself**, and
the BAR stays green. **But the obvious "tidy-up" is a trap, and it has two bad forms:**

- **Bump the PIN to 6 and not the vectors** → all six go **INADMISSIBLE**; the ledger section drops to
  **0 parity / 6 inadmissible** and the census pins `0/4/2/21` all fail.
- **Bump the PIN and all six vectors** → the **vector-store digest MOVES**, and every BAR in the
  program pins it (P-61).

**Neither is correct, and the reason is the whole point of this gate: revision 6 changes NO OBLIGATION.**
A vector authored against revision 5 is authored against the same contract revision 6 states. **The pin
should stay at 5**, and whoever lands revision 6 should say so explicitly so a later reader does not
"fix" the mismatch.

### HUNK A — §4.4, the `I-5` row (line 823). **This is the correction proper.**

```diff
--- a/docs/adr/DEC-2-gl-accounting-adapter.md
+++ b/docs/adr/DEC-2-gl-accounting-adapter.md
@@ -823 +823 @@
-| **I-5** | Corrections are reversing entries | A correction adds a leg pair; it never mutates one | **UNGRADED TODAY.** The A2 corpus contains no reversal: `A2-150`'s journal dump does not project `reversed` or `reversal_id` and its six rows are three ordinary pairs [VERIFIED by this task]; A2-8's grading table lists no reversal grading [VERIFIED BY A2-8, NOT RE-OPENED HERE]. Refused with `ErrNoDiscriminatingVector`; retired by one capture. §9 item 13. | **NO.** Nothing to grade, and nothing to grade it with. |
+| **I-5** | Corrections are reversing entries | A correction adds a leg pair; it never mutates one | **PARTLY — AND REVISION 6 CORRECTS THE REASON REVISIONS 1-5 GAVE, WHICH WAS FALSE WHEN REVISION 5 WAS RATIFIED.** Revisions 1-5 said *"The A2 corpus contains no reversal"*. **It does.** `A2-348` reversed transaction `a28f573f34c7` (HTTP 200) and `A2-349` read its three legs back carrying **`"reversed": true`**; `A2-460` reversed a third [VERIFIED by `T244` from the committed captures under `.softhouse/capture/tierA-a2/out/`]. **RE-DERIVED by `T244` against the LIVE oracle at commit `477dc2d`, 2026-08-22T09:22Z, Fineract pin `426a23544`: 8 rows carry `reversed = true`; the 8 reversing legs they point at are 8 FURTHER rows; 16 rows in 3 reversal pairs over 6 transaction ids; each reversing leg carries an EQUAL `amount` and a FLIPPED `type_enum`, 8 of 8** [`.softhouse/capture/t244-dec2-rev6/`]. **The `A2-150` clause remains TRUE and is kept:** that dump projects neither `reversed` nor `reversal_id`, and its six rows are three ordinary pairs [RE-VERIFIED by `T244`] — it is a snapshot taken when the table held **6** rows and it now holds **60**, and the error was **generalising from one stale dump to the corpus**. A2-8's grading table still lists no reversal grading [VERIFIED BY A2-8, NOT RE-OPENED HERE]. **So the ADDS-A-PAIR half of this invariant is now separable from captured bytes; the NEVER-MUTATES half is not** — all 16 rows show `last_modified_on_utc > created_on_utc`, so telling *"flags and adds"* from *"flags and rewrites"* needs the WRITE path, which no snapshot observes [MEASURED by `T244`; stated first by `A2-15` in `invariants.go:36-47`]. Still refused with `ErrNoDiscriminatingVector` — **on the corrected ground that no reversal capture has been PROMOTED to a vector, not that none exists.** §9 item 13. | **NO.** Unchanged. No `ledger` vector grades a reversal: the six `LDG-*` files are the whole ledger corpus and none is one, and `capabilities-ledger.json` carries `ledger.reversal.entry` with `in_graded_domain: false` [VERIFIED by `T244` at `477dc2d`]. |
```

### HUNK B — §9 item 13 (lines 2568-2569). **The RESTATEMENT. Do not land Hunk A without this.**

```diff
--- a/docs/adr/DEC-2-gl-accounting-adapter.md
+++ b/docs/adr/DEC-2-gl-accounting-adapter.md
@@ -2568,2 +2568,9 @@
-13. **Whether the A2 corpus can grade a reversal.** It cannot today: no reversal appears, and the
-    committed journal dump does not project the reversal columns. §4.4 I-5.
+13. **Whether the A2 corpus can grade a reversal.** **REASON CORRECTED IN REVISION 6 — the answer is
+    still "not today", but the ground revisions 1-5 gave for it was FALSE.** They said *"no reversal
+    appears"*. Several do: `A2-348` and `A2-460` each POSTED one and `A2-349` READ ONE BACK carrying
+    `reversed = true`; `T244` re-derived **8 reversed originals
+    + 8 reversing legs = 16 rows in 3 pairs** against the live oracle at `477dc2d`. The
+    *"committed journal dump"* clause is true of **`A2-150` and only of it** — a snapshot taken when
+    the table held 6 rows, which now holds 60. **What actually blocks grading is (a) no reversal
+    capture has been PROMOTED to a vector, and (b) a snapshot cannot separate *"flags and adds"* from
+    *"flags and rewrites"*, so I-5's NEVER-MUTATES half needs the write path.** §4.4 I-5.
```

### HUNK C — the status header (lines 78-85). **MECHANICAL, AND IT EXPOSES A PRE-EXISTING DEFECT I DID NOT CAUSE.**

A document cannot be *revision 6* while its header says *revision 5*, so **any** rev-6 landing must
touch this block. But reading it turned up something the driver should see on its own account:

> **`DEC-2` LINE 78-85 STILL DESCRIBES ITSELF AS AN UNRATIFIED DRAFT.** It reads
> *"**Status: DRAFT (revision 5)** … **NOT RATIFIED** … Gate **G-11 remains OPEN — NOT RATIFIABLE**
> in `.softhouse/gates.md` and `.softhouse/program.json`"*.
> **G-11 is CLOSED — RATIFIED.** The gate register says so and `program.json` says
> `"state": "CLOSED - RATIFIED (driver, local fire 20260822-140002)"`.
> The last commit to touch the file is `cab9e82` (`A2-32`, revision 5) — **the ratification never
> re-stamped the document.** So the ADR contradicts the authoritative register, and a reader of
> **DEC-2 alone** would conclude it is a draft that may be edited freely — **which is exactly the
> belief this gate exists to prevent.**

I am **not** proposing wording for Hunk C, because the status block is the driver's to write and
because correcting the ratification state is a **different** matter from correcting §4.4's evidential
reason. **The minimal, in-scope correction is HUNK A + HUNK B.** The driver should decide whether to
(a) fold the status re-stamp into rev 6, or (b) re-stamp it separately. **Either way it should not be
left as it is.**

---

## 3. THE GATE BLOCK — READY FOR THE DRIVER TO PLACE. **I DID NOT EDIT `gates.md`.**

### Gate-id verification — what I actually found, as instructed

I checked the **GATE REGISTER table at the top of `.softhouse/gates.md`** (the file's own prose says
that table is authoritative when it disagrees with a heading):

- Ids present in the register: **G-1 … G-6, G-8 … G-12**. **G-7 is recorded as NEVER ALLOCATED**
  ("the id was skipped; nothing is missing, do not go looking for it").
- **Highest allocated id in the register is G-12.**
- **`G-13` appears NOWHERE in `.softhouse/gates.md`.** This is a NEGATIVE, so — after §4.0's engine
  findings — I re-took it on **two sound engines with a positive control in the same file**:

  ```
  /usr/bin/grep -c 'G-13' .softhouse/gates.md   -> 0
  git grep -c -P 'G-13' -- .softhouse/gates.md  -> (no match)
  /usr/bin/grep -c 'G-12' .softhouse/gates.md   -> 7      <-- positive control: the instrument
                                                              demonstrably reads this file
  ```

**So G-13 is the correct next id — CONFIRMED, on sound engines, with the negative calibrated.**

**But here is the discrepancy, and it is a real one:** **`G-13` ALREADY EXISTS in
`.softhouse/program.json`** (`gates_pending` = `[G-2, G-3, G-4, G-5, G-6, G-8, G-9, G-10, G-11, G-12,
G-13]`, entry at line 728), raised by local fire `20260822-060013`; `RESUME.md:189` and
`DRIVER.STATE.json` both already assert **"G-13 is RAISED"**. **`gates.md` has never been told.**
The gate register calls itself *"rebuilt from `.softhouse/program.json.gates_pending` at every fire
that touches a gate"* — that rebuild has not happened for G-13. The two records disagree today, and
placing the block below (plus a register row) is what reconciles them. The `program.json` entry's
content and my independently drafted block agree on substance.

### THE BLOCK

```markdown
## G-13 — DEC-2 §4.4's EVIDENTIAL REASON for leaving `I-5` ungraded is FALSE (revision 6 PREPARED by `T244`, NOT LANDED)

- **id**: G-13 · **class**: CONTRACT · **state**: **OPEN — RAISED, revision 6 drafted and awaiting independent review**
- **context**: `tierA-gl-accounting` / slice `tierA-gl-accounting-A2`
- **raised**: local fire `20260822-060013`; revision 6 prepared by `T244`, local fire of 2026-08-22
- **found_by**: `A2-15` (finding 4), confirmed by `A2-34`. **BOTH CORRECTLY DECLINED TO AMEND THE ADR**, and both should be credited with that restraint — `A2-15` recorded the corrected reason in CODE (`invariants.go`, `capabilities-ledger.json`) and left the ratified document alone.
- **blocks**: **NOTHING.** No task is parked on this. The program continues past it.

### Classification — BOTH halves must be said

- **ENGINEERING in substance.** Source and the live oracle settle it completely; no judgement is left over, no preference is involved, and nothing here is a PRODUCT or LEGAL question.
- **PROCEDURALLY GATED because the artefact is RATIFIED.** CLAUDE.md lists *"Any change to a ratified DEC-n or the frozen adapter contract"* under **Blocking questions — `user` decision gates**, routed `executor: "user"`; and the later amendment that made DEC-n *ratification* agent-decidable states explicitly that **"a ratified DEC-n still cannot be amended by an agent without raising a gate."** **DEC-2 revision 5 is RATIFIED (G-11, local fire `20260822-140002`).**
- **The driver OVERRULED `A2-34`'s recommendation** to handle this "through the normal ADR route, not a gate", on the rule as written. Recorded here so the overruling is visible and reversible. The value of "ratified" is that it does not move quietly; the first amendment waved through as too-small-to-gate sets the precedent for the next.

### What was PROVEN

- `docs/adr/DEC-2-gl-accounting-adapter.md:823` says `I-5` is ungraded because **"The A2 corpus contains no reversal"**. **FALSE.**
- **Captures:** `A2-348` (reverse, HTTP 200), `A2-349` (read-back, three legs each `"reversed":true`), `A2-460` (a third reversal) — all under `.softhouse/capture/tierA-a2/out/`.
- **LIVE ORACLE, re-derived by `T244` at commit `477dc2d`, 2026-08-22T09:22Z, Fineract pin `426a23544`, PostgreSQL `fineract_gerege`:** **8** rows `reversed = true`; **8** further reversing legs; **16** rows total in **3** pairs over **6** transaction ids; equal `amount` and flipped `type_enum` on **8 of 8** pairs. Instrument and transcripts: `.softhouse/capture/t244-dec2-rev6/`.
- **A SECOND SITE, not named in the task:** **§9 item 13, lines 2568-2569**, restates the same falsehood. A fix to line 823 alone would leave it standing — the defect class that rejected this document three times.
- **What is NOT wrong:** nothing DEC-2 **obliges** changes. The invariant statement, column 5 (`Graded today? NO`), the `ErrNoDiscriminatingVector` refusal, and the rule paragraph are all still correct. Only the **stated ground** is wrong.

### What is being ASKED

Permission to land **DEC-2 revision 6**, changing the **evidential reason only**, at the **two** sites above. The full diff is in `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T244-handoff.md` §2 and is **not applied**.

### What UNBLOCKS it

1. An **independent review** of revision 6 — the same bar revision 5 met (`A2-33` reviewed `A2-32`), re-deriving the count against the live oracle rather than inheriting it.
2. Then **the driver ratifies**, `chosen_by: agent`, exactly as it ratified revision 5 under CLAUDE.md § Answering gates. **Buyan may reverse it.**

### ⚠ WHOEVER LANDS IT: **DO NOT BUMP `.softhouse/vectors/PIN-ledger.json`**

`admit.go:49-52` marks a ledger vector INADMISSIBLE when its `dec2_revision` differs from the store pin, and all six `LDG-*` vectors and `PIN-ledger.json` currently say **5**. The check compares vector-to-pin and **never reads the ADR**, so revision 6 landing under `docs/adr/` keeps the bar green on its own. Bumping the pin to 6 without the vectors makes all six INADMISSIBLE (ledger census `0/4/2/21` fails); bumping both **moves the vector-store digest** that every BAR pins under P-61. **Revision 6 changes no obligation, so the pin correctly stays at 5** — stated here so a later reader does not "tidy" the mismatch. [MEASURED by `T244` at `477dc2d`.]

### Driver recommendation

**Ratify revision 6 once independently reviewed.** This is the narrowest possible amendment — a false statement of evidence replaced by a measured one, with every obligation untouched — and leaving a known-false sentence inside a ratified contract is worse than amending it through the gate the rules require.

### Also noticed while preparing this, and NOT part of the amendment asked for

**DEC-2's own status header (lines 78-85) still reads "DRAFT (revision 5) … NOT RATIFIED … G-11 remains OPEN — NOT RATIFIABLE".** G-11 is **CLOSED — RATIFIED**; the ratification never re-stamped the document (last touch is `cab9e82`, `A2-32`, revision 5). The ADR therefore contradicts this register, and a reader of DEC-2 alone would believe it is an editable draft. **Driver's call whether to fold the re-stamp into revision 6 or handle it separately — but it should not be left standing.**
```

---

## 4. THE SWEEP — P-26, THE CONCEPT NOT THE SENTENCE

### 4.0 DRIVER CORRECTION, RECEIVED MID-TASK — RE-DERIVED, CONFIRMED, AND REFINED IN TWO PLACES

The driver corrected my briefing mid-flight: **ugrep is not installed**, the "five engines" claim from
`RESUME.md` is wrong, **`git grep -E` can FABRICATE a hit** and not merely lose one, and
**`git grep -P` is sound and available**. It instructed me to re-run under a sound engine and say which.

**I re-derived the whole table myself on my own fixture rather than transcribing it**
(`engine-table.sh` / `engine-table.txt`, fixture `engine-fixture.txt` = `x main y` / `bmainb` /
`HEAD`, searched for `\bmain\b`; true positive is line 1 only, fabrication is line 2):

| engine | my measured result | verdict |
|---|---|---|
| `git grep -E` | matched **line 2 `bmainb`** only | **BROKEN BOTH WAYS — CONFIRMED** |
| `git grep -P` | line 1 | **SOUND, and present — CONFIRMED** |
| `git grep` (basic) | line 1 | sound |
| `/usr/bin/grep -E` (BSD) | line 1 | sound |
| `/usr/bin/grep` (basic) | line 1 | sound |
| `/usr/bin/grep -P` | `invalid option -- P`, **exit 2** | absent — confirmed |
| `python3 re` | line 1 | sound |
| `ugrep` / `ug` | `command -v` → nothing, across all **13** PATH entries | **NOT INSTALLED — CONFIRMED** |

**The driver is right on every point, and point 1 is the important one:** a fabricating engine cannot
be caught by a known positive, so I added a **known-NEGATIVE calibration**, which I had not had.

**REFINEMENT 1 — `git grep -E` fails in BOTH directions, and I caught the other one.** On the driver's
fixture it **fabricated** (`bmainb`). On the *real tree* it does the opposite:
`git grep -E '\brevers\b'` returns **0 hit lines**, where `git grep -P` returns **523** and BSD grep
returns **538**. **So the same unsound engine silently fabricates on one pattern and silently returns
zero on another.** Both failure modes are now measured, in one program, on one machine.

**REFINEMENT 2 — "`rg` is present" is TRUE INTERACTIVELY AND FALSE IN EVERY SCRIPT, and this is not a
quibble: it destroyed my first sweep.** The driver measured `rg` from a prompt and saw it work. Inside
`bash script.sh`, my `engine-table.sh` measured:

```
rg     command -v -> (nothing)
ugrep  command -v -> (nothing)
grep   command -v -> /usr/bin/grep
type -a rg    : type: rg: not found
type -a ugrep : type: ugrep: not found
```

`rg` is a **shell function** in the Claude Code snapshot, not a binary; shell functions are not
exported to child processes. **My first sweep script called `rg`, got `command not found` on every
pattern, and was saved only by a fail-closed calibration (exit 8).** Without it, it would have printed
`(no hits)` for everything and exited 0.

**RECONCILING "ugrep is not installed" WITH WHAT I SAW.** Both are true and they are about different
things. There is **no ugrep binary on PATH** — the driver is right, and I confirm it. But the snapshot
also shims **bare `grep`** to a **bundled ugrep inside the `claude` executable**
(`ARGV0=ugrep "$_cc_bin" -G --ignore-files --hidden -I …`), so **`grep` typed at a prompt is ugrep,
while `grep` in a script is `/usr/bin/grep`.** I observed a live `ugrep` process doing it. The
consequence is what matters: **`-G` means BRE, and `--ignore-files -I` silently narrows the searched
population** — so an interactively-obtained negative is a claim about the un-ignored, non-binary
subset and never says so. **The "five engines" claim is dead; I do not repeat it.**

### 4.0.1 WAS MY OWN SWEEP AFFECTED? — MEASURED, NOT ASSERTED

**My primary engine was `/usr/bin/grep -E` (BSD), which the driver's table and mine both mark SOUND;
the multi-line engine was `python3 re`, also sound.** `git grep -E` appeared **only** as a
cross-check (the calibration count `C2 = 8`, and PASS 3).

**The fabrication/recall defect triggers on backslash classes, and my PASS-1 patterns contain NONE.**
`engine-table.sh` PART 4 lists all twelve verbatim — `corpus contains no revers`, `no revers`,
`revers.{0,40}(absent|missing|…)`, `ErrNoDiscriminatingVector`, and so on. **Zero `\b`, `\d`, `\s`,
`\w`.** So the mechanism could not fire on them.

**I re-ran the load-bearing patterns under `git grep -P` and BSD grep anyway**
(`sweep-reverify-sound-engines.sh` / `.txt`), because "my patterns are immune" is an argument and the
driver asked for a measurement:

```
KNOWN POSITIVE 'corpus contains no reversal'   git grep -P 12 files   BSD grep -E 14 files
KNOWN NEGATIVE (token built at runtime)        git grep -P  0 hits    BSD grep -E  1 hit
FABRICATION PROBE \brevers\b                   git grep -P 523 lines  BSD grep -E 538 lines
                                               git grep -E   0 lines  <-- the unsound engine
```

**HEAD-TO-HEAD ON THE COMBINED LOAD-BEARING PATTERN** `contains no revers|no reversal appears`:

```
git grep -P    : 22 hit line(s)
BSD grep -E    : 22 hit line(s)      <-- EXACT AGREEMENT
```

Same count, same 14 files — `DEC-2` (both sites), `invariants.go`, `capabilities-ledger.json`,
`A2-13.md`, `A2-15-handoff.md`, `RESUME.md`, `program.json`, `tasks.json`, `bar-and-oracle.sh`, and
this task's own artefacts.

**The two sound engines agree on substance; every difference elsewhere is SCOPE, not soundness** —
`git grep` reads **tracked** files, BSD grep reads the **disk** including untracked output. That also explains the
one "failed" negative control: the runtime-built token got echoed into the transcript **on disk**, so
BSD grep found it there and `git grep -P` (tracked-only) did not. **Self-reference again, reported
rather than smoothed.**

**RESULT UNCHANGED UNDER SOUND ENGINES.** `no reversal appears` → **`DEC-2:2568` and nothing else
live**. `retired by one capture` → **`DEC-2:823` and `A2-13.md:193` and nothing else**.
`corpus contains no revers` → the same classified set as §RESULTS below. **The two-live-sites finding
survives the correction.**

### 4.1 THE INSTRUMENT FAILED FIRST, AND THAT IS THE HEADLINE

**`rg` IS NOT A BINARY ON THIS MACHINE.** My first sweep script called `rg`, and the fail-closed
calibration **aborted it at exit 8** with `rg: command not found` — after `rg --version` had happily
printed `ripgrep 14.1.1` in my interactive shell moments earlier.

```
type rg
rg is a shell function from /Users/buv/.claude/shell-snapshots/snapshot-zsh-1787390255449-wx206k.sh

ls /opt/homebrew/bin/rg /usr/local/bin/rg /usr/bin/rg
ls: /opt/homebrew/bin/rg: No such file or directory
ls: /usr/bin/rg: No such file or directory
ls: /usr/local/bin/rg: No such file or directory
```

The snapshot defines it **only because ripgrep is absent** — the guard is literally
`# Check for rg availability` / `if ! (unalias rg 2>/dev/null; command -v rg) …`, and the function
re-execs the `claude` binary with `ARGV0=rg`.

**Why this matters to the program, not just to me.** A sweep **script** that calls `rg` gets
`command not found` on every invocation and, unless it fails closed, prints **`(no hits)` for every
pattern and exits 0**. That is **the fail-OPEN class arriving through a mechanism this program has not
catalogued** — RESUME HEADLINE 5 records the dead-`cd` form; this is a different one with an identical
signature. **And `RESUME.md`'s engine catalogue is wrong in a load-bearing way:** *"ripgrep 14.1.1 is
present"* (`T228`) is true **interactively** and **false for every script**. For scripts there are
**two** general engines here, not five.

### 4.2 WORSE THAN `rg`: **BARE `grep` IS SHIMMED TOO, AND THE SHIM FILTERS THE POPULATION**

Chasing the `rg` failure turned up the general case. **`grep` is also a shell function** in the same
snapshot, and it does **not** run BSD grep:

```
type grep
grep is a shell function from /Users/buv/.claude/shell-snapshots/snapshot-zsh-1787390255449-wx206k.sh

# its body, verbatim:
ARGV0=ugrep "$_cc_bin" -G --ignore-files --hidden -I \
      --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg \
      --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl ${1+"$@"}
```

**`ugrep` is NOT INSTALLED as a PATH binary** — `command -v ugrep` and `command -v ug` both return
nothing across all 13 PATH entries, and there is no binary in `/opt/homebrew/bin` or `/usr/local/bin`.
**The driver's correction is right about that and I confirm it.** What I add is that a **bundled**
ugrep inside the `claude` executable nonetheless *executes* on every interactive `grep`. **These two
statements are about different things and both are true:** there is nothing to install, invoke or cite
as an engine, **and** the thing you actually run when you type `grep` at a prompt is not BSD grep.
**So the catalogue is wrong in both directions: `ripgrep` was recorded PRESENT and is unavailable to
scripts; `ugrep` is correctly recorded absent yet is what bare `grep` dispatches to interactively.**

**Three consequences, and the third is the dangerous one:**

1. **`-G` — basic regular expressions by default.** An ERE written without an explicit `-E` does not
   mean what its author thinks.
2. **`--ignore-files` and `-I` — the shim SILENTLY NARROWS THE POPULATION.** It honours
   `.gitignore`-style ignore files and skips binaries. A negative obtained this way is a statement
   about the *un-ignored, non-binary* subset, **not about the tree** — and it never says so.
3. **THE SAME COMMAND TEXT MEANS DIFFERENT THINGS INTERACTIVELY AND IN A SCRIPT.** Shell functions are
   not exported, so `grep` inside `bash script.sh` is the real `/usr/bin/grep` over the *whole* tree,
   while the identical `grep` typed at the prompt is `ugrep` over a *filtered* tree. **An agent that
   calibrates interactively and then commits the script has calibrated a different instrument from the
   one that ships.**

**I therefore re-ran my own two headline NEGATIVES through the real binary**, because I had originally
taken them through the shim:

```
/usr/bin/grep -c -i 'revers' .softhouse/patterns.md                      -> 4   (identical, all unrelated)
/usr/bin/grep -rn -i -E 'no reversal|contains no revers' docs/           -> exactly DEC-2:823 and DEC-2:2568
```

**Both reproduce exactly.** The negatives in §F stand on the real engine, not on the shim. The sweep
script itself was already immune: it pins `G=/usr/bin/grep` explicitly.

**Blast radius — BOUNDED, and this is the good news.** I checked whether any committed instrument
depends on it:

```
git grep -n -E '(^|[[:space:]}(;&|])rg[[:space:]]+(-|"|'"'"')' -- .      ->  ZERO hits
```

**Scope of that negative:** all **4,982** tracked files (368 `.sh`, 478 `.py`, and every other tracked
file). The only two `git grep -c 'rg '` hits are the substring in *"o**rg** "* and *"calle**rg**"* —
false positives. **No previously committed sweep result in this program is void by this mechanism.**
The exposure is to **ad-hoc in-session sweeps**, which is what mine would have been.

### 4.3 Engines, flags, calibration — as finally run

```
ENGINE 1  BSD grep 2.6.0-FreeBSD      -r -n -i -E     SOUND. This was the PRIMARY engine.
ENGINE 2  git grep (git 2.50.1)       -n -i -E        *** UNSOUND (see 4.0) *** cross-check
                                                      ONLY, and RE-VERIFIED under `git grep -P`,
                                                      which IS sound and which the program's
                                                      lore never recorded.
ENGINE 3  python3 3.9.6 `re`          IGNORECASE|DOTALL   SOUND. <-- the MULTI-LINE pass
NOT USED  rg          -> shell function only, invisible to scripts (above)
NOT USED  grep -P     -> DOES NOT EXIST here; `echo abc | /usr/bin/grep -P 'a.c'` -> exit 2
NOT USED  ugrep       -> NOT on PATH as a binary, but it IS what bare `grep` runs
                         interactively (bundled in the claude executable), with
                         -G --ignore-files -I. Deliberately avoided: engine 1 pins
                         the absolute path /usr/bin/grep so the script and the
                         prompt search the SAME population.
NOT USED  ggrep / pcre2grep           -> ABSENT (`command -v` returns nothing)
NOT USED  `\b` under `git grep -E`    -> reads as a literal 'b'. P-53/P-12 record this as
                                         SILENT ZERO; it is worse. MEASURED BOTH WAYS by me:
                                         it FABRICATED `bmainb` on a fixture, and returned
                                         ZERO for `\brevers\b` on the real tree where sound
                                         engines return 523/538. Recall loss AND false
                                         positives from one engine.
ANCHORING the stem is `revers`, NO RIGHT ANCHOR — T224's zero came from right-anchoring
          an inflected stem, not from the engine. Catches reversal/reversed/reversing/reverse.
```

**SCOPE, stated before any negative (P-66 / P-70):** the whole worktree on disk, **4,990** files,
excluding `.git` only; 411 `.md`, 1,593 `.json`; 4,982 tracked.

**CALIBRATION ON A KNOWN POSITIVE, FAIL-CLOSED — the script aborts at exit 8 if any engine is blind:**

```
engine 1 BSD grep  'corpus contains no reversal' -> hit lines: 15
engine 2 git grep  'corpus contains no reversal' -> hit lines:  8
engine 3 python3   'corpus contains no reversal' -> hit lines: 18
engine 1 unanchored stem 'revers'                -> hit lines: 743
CALIBRATION PASSED on all three engines. Negatives below are MEASUREMENTS.
```

The three counts **differ, legitimately**: engine 2 sees tracked files only; engine 3 counts *matches*
(several per line) and reads untracked files too. I report all three rather than the flattering one.

**NEGATIVE CONTROL, and it did NOT return 0 — reported honestly.** `zzq-t244-nonexistent-token`
returned **2** on both engines, because by then the token existed **in my own script and transcript**.
The instrument found itself. That is not a defect in the sweep but it *is* the reason `mlsweep.py`
separates self-hits from real hits in the multi-line pass, and the reason the classification below
excludes `.softhouse/capture/t244-dec2-rev6/`.

### 4.4 RESULTS — every hit classified

**A. TRUE RESTATEMENTS of the stale reason, in LIVE artefacts — these are the finding**

| Site | What it says | Action |
|---|---|---|
| `docs/adr/DEC-2-gl-accounting-adapter.md:823` | *"The A2 corpus contains no reversal"* | **HUNK A** — the NAMED site |
| `docs/adr/DEC-2-gl-accounting-adapter.md:2568-2569` | *"no reversal appears"* | **HUNK B — the RESTATEMENT.** Not named in the task; found by this sweep |

**B. HISTORICAL record, correctly stamped — recommend NOT rewriting**

| Site | What it says |
|---|---|
| `.softhouse/handoff/…/A2-13.md:193` | revision 1's own table: *"**UNGRADED TODAY.** The A2 corpus contains no reversal; `A2-150`'s dump does not even project the reversal columns."* |

`A2-13` is the handoff that **authored revision 1**. It was true-as-believed when written and is a
dated record of what that revision claimed. **Recommend leaving it**, on the driver's own precedent
from `8275f8b`: *"the 22 DONE tasks that also quote `73c3ea7b` … are historical records, correctly
stamped, and were deliberately NOT rewritten."* Rewriting finished handoffs destroys the audit trail
that makes the rejection history legible.

**C. ALREADY CARRY THE CORRECTED REASON — no action, and they are why this was caught**

- `nexus/internal/apps/ledger/conformance/invariants.go:36-47` — `A2-15`'s corrected reason, naming
  A2-348/A2-349 and stating the never-mutates gap. **This is the model: fix it in code, leave the
  ratified ADR alone, flag it.**
- `.softhouse/vectors/capabilities-ledger.json:81-84` — `ledger.reversal.entry`,
  `in_graded_domain: false`, evidence text explicitly *"CORRECTS DEC-2 §4.4's stated reason"*.
- `.softhouse/handoff/…/A2-15-handoff.md:447` · `.softhouse/reviews/a2-34-review-a2-15/REVIEW.md:786-804`.
- `.softhouse/reviews/a2-34-review-a2-15/bar-and-oracle.sh:73` — a **detector** for the stale sentence,
  not a restatement.

**D. DRIVER / TASK records quoting it deliberately — no action**

`.softhouse/tasks.json:2510` (T244's own brief) · `.softhouse/program.json:732` (the G-13 entry) ·
`.softhouse/RESUME.md:189`.

**E. FALSE POSITIVES of the unanchored stem — listed to show the sweep's noise floor**

`T69.md:93,95,223` · `T182.md:50,51,204` · `t234-sweep-instrument-audit/evidence/census.json` ·
`contract.go:2194` — all `slices.Reverse`, "never reversing" about a JVM step, or "never the reverse".

**F. NEGATIVES, with scope stated (P-66 / P-70)**

- **`.softhouse/patterns.md` — NO restatement.** Scope: the whole 2,292-line file, BSD grep `-n -i` on
  the unanchored stem `revers`; **4 hits**, all unrelated (P-5 prose, the append-only non-negotiable,
  "reversed ordering", "reversible with one `rm -rf`").
- **`docs/` outside DEC-2 — NO restatement.** Scope: both ADRs (`DEC-1`, `DEC-2`) and all of `docs/`;
  `grep -rn -i 'no reversal\|contains no revers' docs/` returns **exactly the two DEC-2 lines**.
- **No vector restates it.** Scope: all 61 `.json` under `.softhouse/vectors/`. The only `revers`
  matches are `capabilities-ledger.json` (corrected reason) and `LDG-04`'s note, where "a reversal"
  appears in prose about the oracle having moved — neither is a restatement, and **no vector grades a
  reversal**.

**MULTI-LINE PASS — AND IT REACHED FILES THE LINE-ORIENTED PASS DID NOT.** Run via `mlsweep.py`
(engine 3, `DOTALL`) over all 4,990 files, seven newline-spanning patterns, all seven completed:

```
corpus[\s\S]{0,60}?no[\s\S]{0,30}?revers                                24 hits outside self
contains[\s\S]{0,40}?no[\s\S]{0,40}?revers                              21
\bno\s+revers                                                           42
revers[\s\S]{0,80}?(ungraded|not graded|no vector|nothing to grade|…)     7
(ungraded|not graded|nothing to grade)[\s\S]{0,80}?revers               15
I-5[\s\S]{0,120}?revers                                                 43
revers[\s\S]{0,120}?I-5                                                 14
```

**CORRECTION TO MY OWN EARLIER STATEMENT.** Partway through I wrote that the multi-line pass returned
"the same file set" as the line-oriented one. **That was wrong and I am correcting it rather than
leaving it.** The completed pass reached **~20 files the line-oriented pass never hit** — chiefly
`.softhouse/guards/ledgerguard/main.go`, `.softhouse/state/DRIVER.STATE.json`,
`.softhouse/handoff/…/A2-18.md`, and ~17 committed conformance transcripts — because `I-5` and
`revers` sit on **adjacent lines** there, which no line-oriented pattern can join. **This is exactly
the gap T234 measured (743 newline-spanning matches across 161 files) and it is why the pass was
required.**

**What it did NOT find is a new restatement, and I opened the new files to check rather than
inferring it:**

- **`ledgerguard/main.go:40-43` and `:757-759`** give a **different and still-TRUE** reason:
  *"I-5 … is DELIBERATELY NOT IMPLEMENTED as its own class. 'Mutates a leg instead of adding a
  reversing pair' is only decidable once a leg type and a correction path exist; neither does today."*
  That is a statement about the **Go tree**, not about the corpus. **It is a third, independent and
  sound ground for I-5 being unenforced, and revision 6 does not disturb it.**
- **The conformance transcripts print exactly that same guard text** (`ledger-invariants: 4. I-5 …`),
  so **the harness does not print the stale claim** — worth stating explicitly because `T242` is open
  on the harness printing a false coverage sentence, and **this is not another instance of it.**
- `A2-18.md` is the guard's build handoff carrying the same correct reason;
  `DRIVER.STATE.json` is a driver record already classified under **D**.

---

## 5. THE BAR — RUN BY ME, REAL OUTPUT

Script `.softhouse/capture/t244-dec2-rev6/bar.sh`; full transcript
`.softhouse/capture/t244-dec2-rev6/bar-output.txt`. Run at HEAD `477dc2d` on branch
`softhouse/T244-dec2-rev6-prepared`, 2026-08-22T09:31:44Z. Harness invoked with **`bash`**, never `sh`.

**RUN TWICE.** The transcript quoted below is the first run. After the driver's mid-task correction
and every edit it caused, **I re-ran the whole bar** — transcript
`.softhouse/capture/t244-dec2-rev6/bar-output-final.txt`, at commit `6e22eed`. **Identical and green:**
`probe = up`, `VERDICT: PASS (exit 0)` 46 parity / 7884 cells, **all nine census pins `== pinned`**
(`4/4/4/0/0` and LEDGER `0/4/2/21`), `conformance exit code = 0`, `go build rc=0`, `go vet rc=0`. A
task that changes only prose should not move a number, and it did not.

**This task changes no code and no vectors, so the bar is a NO-REGRESSION check.**

```
### VECTOR STORE DIGEST (P-61) — must be UNCHANGED BY THIS TASK ###
expected (main 477dc2d) : 8968c559fa613e8642ab030bd0a029c17d147054
actual   (this branch)  : 8968c559fa613e8642ab030bd0a029c17d147054     <-- UNCHANGED

### did this task touch anything it must not? ###
docs/adr/            : 0 file(s)  [MUST BE 0]
.softhouse/gates.md  : 0 file(s)  [MUST BE 0]
.softhouse/vectors/  : 0 file(s)  [MUST BE 0]
nexus/               : 0 file(s)  [MUST BE 0]

conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
    oracle probe    UP

VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
         This means "matches the reference oracle on captured vectors, within the graded domain".
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.

conformance:   exemption census READ: exempted assertions (graded) = 4 == pinned 4
conformance:   exemption census READ: declared exemptions (loaded) = 4 == pinned 4
conformance:   exemption census READ: GROUNDED                     = 4 == pinned 4
conformance:   exemption census READ: UNDETERMINED-ON-THE-RECORD   = 0 == pinned 0
conformance:   exemption census READ: UNGROUNDED                   = 0 == pinned 0
conformance:   exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
conformance:   exemption census READ: LEDGER parity vectors        = 4 == pinned 4
conformance:   exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
conformance:   exemption census READ: LEDGER money cells compared  = 21 == pinned 21
conformance exit code = 0

    refused                 0   (no discriminating vector / seam blind — not a pass, not a failure)
    inadmissible            0
    harness errors          0
    invariant violations    0
    invariant assertions    0 NOT RUN (a cell nobody observed; listed above, never inferred)
    ledger inadmissible     0
    ledger harness errors   0

PROOFS: 23 passed, 0 failed
--prove exit code = 0

go build rc=0
go vet   rc=0
ok  github.com/gerege/nexus/internal/apps/ledger              0.842s
ok  github.com/gerege/nexus/internal/apps/ledger/conformance  2.975s
ok  github.com/gerege/nexus/internal/apps/loanschedule        9.484s
ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance  91.562s
go test rc=0

--- gofmt -l . (expect EXACTLY contract.go — never gofmt -w it, G-3)
internal/apps/loanschedule/contract/contract.go
gofmt listed 1 file(s)
```

**Probe line PRESENT and reading `up`** — tested for **presence** first, per the standing rule that
oracle-down is exit 2 **and** a probe line actually printed reading `down`.
**Every item on the bar is met.** `contract.go` was **not** `gofmt -w`'d (G-3).

---

## 6. WHAT I DID NOT DO, WITH SCOPE

- **Did not amend `docs/adr/DEC-2-gl-accounting-adapter.md`.** That was the point of the task.
- **Did not edit `.softhouse/gates.md`.** `T241` also holds that file this program and the driver
  places gate blocks. The block is in §3 above, ready to paste, plus the register row it needs.
- **Did not edit `.softhouse/program.json`.** Its `G-13` entry already exists and agrees with my block;
  reconciling the register is the driver's action.
- **Did not re-open `A2-8`'s grading table.** Carried forward as `[NOT RE-OPENED HERE]`, as revisions
  1-5 marked it.
- **Did not pursue the running-balance UPDATE on all 16 reversal rows.** It is **G-12**'s subject,
  G-12 is open and already measured by `A2-29`, and widening this task into it would be exactly the
  fold-in the brief warned against.
- **Did not propose wording for the status-header re-stamp (Hunk C).** Flagged, not authored.
- **Did not verify the `A2-13.md` restatement against anything but its own text** — it is a historical
  handoff and I am recommending it be left alone.
- **Did not re-run the FULL twelve-pattern PASS-1 battery under `git grep -P`.** I re-ran **four**
  load-bearing patterns (`corpus contains no revers`, `contains no revers`, `no reversal appears`,
  `retired by one capture`) plus the combined pattern and two calibrations. **The other eight were not
  re-run under `-P`, and did not need to be**: the primary engine for all twelve was already
  `/usr/bin/grep -E`, which both the driver's table and mine mark SOUND, and none of the twelve
  contains a backslash class. **Stated as a scope limit rather than left implicit.**
- **Did not run a sweep for OTHER stale evidential reasons in DEC-2 beyond the reversal concept.**
  Scope: my sweep targeted the `revers` concept only. §4.4's other rows carry `[VERIFIED]` stamps that
  a fresh task could re-derive the way `A2-31` and `A2-33` did — **not attempted here.**

## 7. FOLLOW-UPS THIS TASK RAISES

- **FU-T244-0 — `patterns.md` SHOULD RECORD WHAT THE DRIVER AND I BOTH MEASURED THIS FIRE**, because
  P-53/P-12 are now known to be **understated**: `git grep -E` does not merely lose a `\b` hit, it can
  **fabricate** one (`bmainb` matched on a fixture) *and* return **zero** on the real tree
  (`\brevers\b` → 0, versus 523 under `git grep -P` and 538 under BSD grep). **Both polarities, one
  engine.** Two rules follow and neither is in the lore: **calibrate on a known NEGATIVE as well as a
  known positive** — a positive cannot catch a fabricator — and **`git grep -P` is sound and
  available here**, the cheapest sound route inside a git tree, which the lore only ever discussed as
  `/usr/bin/grep -P` (absent, exit 2). **The `RESUME.md` "five engines" claim is dead.**
- **FU-T244-1 — THE ENGINE CATALOGUE IS WRONG IN BOTH DIRECTIONS, AND THE SHIMS FILTER SILENTLY.**
  `RESUME.md`/`T228` record *"ripgrep 14.1.1 is present"* — true
  interactively, **false for every script** (`rg` is a shell function; no binary exists). The driver's
  correction says **`ugrep` is not installed**, which is **right about PATH** and which I confirm
  across all 13 PATH entries — but bare **`grep` still RUNS a bundled `ugrep`** interactively, with **`-G`** (BRE, not ERE)
  and **`--ignore-files -I`**, so it **silently narrows the searched population** and never says so.
  **The same command text therefore searches different populations at the prompt and in a script.**
  Worth a `patterns.md` entry beside the dead-`cd` class, stating the rule that follows from it:
  **pin the absolute engine path in any committed instrument (`/usr/bin/grep`), and calibrate
  fail-closed on a known positive — never trust an engine by name.** The three-engine counts in my own
  calibration (15 / 8 / 18 for one known-present string) show how far apart "the same search" can land.
- **FU-T244-2 — DEC-2's status header contradicts the gate register** (Hunk C above).
- **FU-T244-3 — `gates.md` has never been told about G-13**, though `program.json`, `RESUME.md` and
  `DRIVER.STATE.json` all record it as raised. The register is supposed to be rebuilt from
  `program.json` at every fire that touches a gate.
