# t367-review-t363 — the independent review of T363, and the evidence behind it

**Verdict: MICRO-FIX.** Read `REVIEW.md`. The handoff is
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T367.md`.

**T367 FIRED NO PROBE.** Every statement issued against the reference oracle is a `SELECT`. Opening and
closing readings are identical (`acc_gl_journal_entry` 71/75, `m_portfolio_command_source` 359/359),
so **no `PROBES.tsv` row is required for this review and none should be added.**

## Re-run everything

```bash
bash .softhouse/reviews/t367-review-t363/drive.sh                    # 12 red/green drives of T363's instrument
bash .softhouse/reviews/t367-review-t363/drive-t305-t327-pins.sh     # is the third pin real, and would it refuse?
bash .softhouse/reviews/t367-review-t363/drive-sweep-failopen.sh     # the fail-open in casualty-sweep.sh, driven
bash .softhouse/reviews/t367-review-t363/drive-independent-sweep.sh  # selectors T363's sweep does not carry
for f in .softhouse/reviews/t367-review-t363/sql/*.sql; do
  docker exec -i fineract-db-1 psql -U root -d fineract_gerege < "$f"   # every one read-only
done
```

`drive.sh` extracts the artefact under test **from `softhouse/T363-oracle-baseline`** on every run
rather than from disk, so this review cannot silently grade a since-edited copy, and T363's files are
not duplicated into this commit.

## Files

| path | what |
|---|---|
| `REVIEW.md` | the review. Findings F1–F7, the three MICRO-FIX edits, and what was checked and found clean |
| `drive.sh` | 12 drives: GREEN + RED-1/1b/2/2b/4/5/6 + the interpreter guard on `sh`/`dash`/`zsh`/`ksh` |
| `drive-t305-t327-pins.sh` | re-implements the rigs' F5 comparison read-only, without bringing a throwaway up |
| `drive-sweep-failopen.sh` | drives the discarded `git grep` exit status: rc 128 vs 1 vs 0, all printed as "0 hits" |
| `drive-independent-sweep.sh` | 11 selectors T363's sweep lacks; X11 is malformed on purpose and must REFUSE |
| `sql/r1-counts.sql` | the counts, the floor, the float census, the engine |
| `sql/r2-movement.sql` | movement above the floor, per-account legs, currencies at floor vs live |
| `sql/r3-status-split.sql` | the PROCESSED/ERROR split, and whether `idempotency_key` is nullable |
| `sql/r4-key-shape.sql` | does the key NAME a task, or is it merely PRESENT? |
| `sql/r5-defeat.sql` | sequences, table count, `reversed`, the whole-schema float census |
| `out/` | every transcript, including the conformance run |

Everything under `sql/` is `SELECT`-only, by inspection and by intent. Nothing here writes to the
oracle.
