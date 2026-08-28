# t371-t367-conditions — repairing T367's three conditions on T363

T363 and T367 are both merged to `main`. T367 returned **MICRO-FIX**; the driver adjudicated that verdict
**down** — the pipeline defines MICRO-FIX as at most ten lines, mechanical, **never a number**, and F3 is
a number, live and wrong on `main` — and filed T371 instead. T371 agrees with the adjudication; see
`## Money-math notes` in the handoff for why.

## T371 FIRED NO PROBE

Every statement T371 issued against the reference oracle (Fineract) is a `SELECT`.
`instruments/run-reads.sh` opens with a read of the append-only max ids and **closes with the same read**,
and the two are identical — so this is checkable from the transcripts rather than taken on T371's word:

```
out/Q1-OPENING.txt   je 71/75   cs 359/359   closure 0/null
out/Q5-CLOSING.txt   je 71/75   cs 359/359   closure 0/null
```

**`PROBES.tsv` needs no row for T371, and none was added to the probe section.** (T371 *did* add a comment
block to that file's header — three standing facts, not an attribution row.)

This matters more than it used to. **T367 established that a 4xx BURNS the idempotency key**, because
`saveInitial` runs before handler dispatch. So a *refusal* probe against the standing oracle is as
irreversible as an accepted one, and there is no such thing as a safe write to this tenant.

## What is in here

| path | what |
|---|---|
| `sql/q1-opening-read.sql` | the opening/closing max-id read. Attests T371 moved nothing |
| `sql/q2-status-split.sql` | **F3** — the `PROCESSED` / `ERROR` split, whole-table and at-or-below-floor |
| `sql/q3-key-naming.sql` | **F1** — is `idempotency_key` `NOT NULL`, and does a key NAME a task? Two independent classifiers |
| `sql/q4-instrument-blindspots.sql` | the three evasions T367 found: consumed sequence, 281 tables, `reversed` below the floor |
| `instruments/run-reads.sh` | runs all four, read-only, and diffs opening against closing |
| `instruments/drive-sweep-failclosed.sh` | **F2** — the red drive, both directions, extracting the instrument from git on every run (P-22) |
| `out/DRIVE-SWEEP-FAILCLOSED.txt` | that drive's transcript |
| `out/CASUALTY-SWEEP-T371.txt` | the repaired sweep, run post-repair. T363's pre-repair transcript is left where it is |
| `out/BAR-conformance-t371.txt` | `bash .softhouse/conformance.sh` after these changes |

## The three numbers, re-derived rather than inherited

T371 re-derived every figure it quotes against the live PostgreSQL. It did **not** take T367's word for
any of them, and it used a second, independent classifier where one existed.

**F3 — the status split.** `reference-oracle.md:930` said, in the **present tense**, `156 PROCESSED /
194 ERROR`. Live:

```
status 1 PROCESSED   162      (157 at or below the floor,  5 above)
status 5 ERROR       197      (195 at or below the floor,  2 above)
                     359
```

The repair **does not substitute `162 / 197`.** That pair is wrong by the next probe, and this file has
now gone stale on a hand-typed cardinal four times. The cardinal is deleted, the qualitative claim
(*refusals are the majority of this tenant's command history*) is kept because it is robust, and the
derivation is named.

**F1 — attribution.** `idempotency_key` is `NOT NULL`, so "all 359 rows carry one" is the schema
restated and is evidence of nothing. Fineract mints a UUID when the caller sends no header. Two
classifiers, agreeing exactly:

```
total 359   null 0   blank 0   distinct 359
uuid-shaped (8-4-4-4-12 hex)      339
NOT uuid-shaped                    20      <- of which 7 are above the floor
carries a task token (t\d\d, a2-N) 20      <- independent classifier, same answer
```

The 20 are listed by id in `out/Q3-KEY-NAMING.txt`: thirteen `a2-26`/`a2-29` rows in the 281–307 range,
and the seven T352/T359 rows above the floor. **Row 352 carries a minted UUID and is therefore
permanently unattributable** — which closes FU-T367-4's question: nobody will ever identify it.

**The instrument's bound.** All three of T367's evasions re-derived live:

```
acc_gl_closure_id_seq   last_value 1, is_called t   while acc_gl_closure reads 0 rows / max id null
base tables in tenant   281                          (the instrument attributes on 2)
acc_gl_journal_entry rows with reversed = t   8      (all at or below id 64; the column is never read)
float columns, WHOLE schema                   0      (the check currently looks at 2 tables)
```

## What T371 did NOT touch, and why

- **`t305` / `t327`.** T367 **upheld** T363's refusal as correct scope discipline, and added **F5**:
  `t305/run-all.sh:29`'s `rm -rf "$OUT"` is **unconditional** and destroys 66 committed files, including
  the LDG-05 admissibility evidence T363 rightly refused to delete by hand. Still outside the write
  grant; carried as follow-ups, not repaired here.
- **`.softhouse/conformance.sh`** (T375 holds it) and **`.softhouse/bin/fire-program.sh`** (T377).
- **T363's and T287's dated transcripts.** `t363-oracle-baseline/out/CASUALTY-SWEEP.txt` and
  `t287-closure-refusals/ARM2-OBSERVATION.md:136` keep their original figures. A witness is not edited to
  agree with today (T248 / T258 / T340).
- **`.softhouse/handoff/…/T363.md:30`**, which carries the F1 sentence in its strongest form. It is
  outside the write grant *and* it is an archived dated record; see the handoff's `## Blockers`.
