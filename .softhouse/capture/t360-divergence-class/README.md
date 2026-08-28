# T360 — evidence for the DIVERGENCE vector class (G-19)

Branch `softhouse/T360-divergence-class`. Fire `20260828-140005`. Pinned reference oracle
`426a23544e8426a38ae43ae404670a0a7e85b9eb` at `/Users/buv/fineract`, live at
`https://localhost:8443/fineract-provider`, probe **UP**. PostgreSQL is the only database in
the path. Nothing here contacted Oracle Database, MySQL or MariaDB, and nothing could:
the only wire call T360 made is the read-only `GET` below.

## THE ORACLE WAS NOT MOVED BY THIS TASK

T360 posted **nothing**. It made exactly one call to the reference oracle, a read-only
`GET /journalentries?transactionId=a29bca0816a7&transactionDetails=true`, and it did so to
re-verify a banked observation rather than to create one. Row counts, GL-account leg counts
and `distinct_transaction_id` are unchanged by T360.

## FILES

| file | what it is | exact conditions |
|---|---|---|
| `out/T360-R01-readback-a29bca0816a7.json` | the live read-only re-read of T352's residue transaction | HTTP 200. **BYTE-IDENTICAL** to the committed capture `.softhouse/capture/t352-a2-next-tranche/out/T352-A09-residue-3dp-readback-cited.json` (`diff` exit 0). This is the `rerun_invariant` of `LDG-DIV-01`, actually re-run. |
| `out/T360-R01-readback-a29bca0816a7.http` / `.status` | response headers and the status code | `200` |
| `out/T360-D01-wrongimpl-DIES.txt` | the KILL drive | branch as committed; `-oracle-probe=up -ledger-impl=ledger-wrong-residue-rounding`, **no context filter**. `VERDICT: FAIL (exit 1)`. `ledger parity PASS 7 FAIL 1`, `divergence vectors PASS 0 FAIL 1`. **The other thirteen ledger vectors all PASS** — the kill comes from `LDG-DIV-01` alone. |
| `out/T360-D02-wrongimpl-SURVIVES-without-the-vector.txt` | the LOAD-BEARING drive | the same branch with **two temporary edits, both reverted before commit**: `LDG-DIV-01` moved out of `.softhouse/vectors/ledger/`, and `divergencePinCount` set to `0` so the run refuses for the vector's absence rather than for the pin. `VERDICT: PASS (exit 0)`, `ledger parity PASS 7 FAIL 0`. **The deliberately wrong implementation SURVIVES the entire corpus when this one vector is withheld.** |
| `CONFORMANCE-SH-PATCH-REQUEST.md` | the `.softhouse/conformance.sh` edit T360 could not make | that file is held by **T375** this fire. Patch 1 is **merge-blocking**: one integer, `EXEMPTION_PIN_LEDGER_WRONGIMPLS` 13 → 14. |
| `out/T360-BAR-as-committed.log` | `bash .softhouse/conformance.sh` on the committed branch | see the exit-code note below |
| `out/T360-BAR-with-patch1.log` | the same bar with patch 1 applied | see below |

## THE TWO BAR RUNS, AND HOW TO READ THEIR EXIT CODES (P-84)

Both were taken from a **clean tree** — `git status --porcelain` empty — **after**
`git add -A` and `git commit`. Both printed the probe line
`conformance: reference oracle (…) probe = up` **before** any exit code was read, so neither
`2` can be an oracle outage: **P-84 is read as "the probe line was PRINTED, and it says `up`"**,
not as "the exit code was 2".

- **`T360-BAR-as-committed.log` — exit 2, probe line PRINTED, reads `up`.** The refusal is
  `WRONG-IMPLEMENTATION POPULATION 14, PINNED 13`. That is
  `.softhouse/conformance.sh`'s own both-directions pin **working**: T360 registered a
  fourteenth deliberately-wrong implementation and may not edit the file that pins the
  population. It is not an oracle outage and it is not a corpus defect.
- **`T360-BAR-with-patch1.log` — exit 0, probe line PRINTED, reads `up`.** Identical tree plus
  the single character of patch 1. This is the state after the driver sequences the patch.

  **HOW THAT RUN WAS TAKEN, stated exactly, because a green transcript from a tree that is not
  the committed tree has to say so.** From the committed tree, `sed -i ''` changed
  `EXEMPTION_PIN_LEDGER_WRONGIMPLS=13` to `=14` — `git diff --stat` read
  `.softhouse/conformance.sh | 2 +-`, one insertion, one deletion, and **nothing else was
  modified** — the bar was run, and `git checkout -- .softhouse/conformance.sh` reverted it.
  `.softhouse/conformance.sh` is byte-identical to `main` on the committed branch:
  `git diff main -- .softhouse/conformance.sh` is empty. The log therefore describes the tree
  the driver will have **after** sequencing patch 1, and describes no other tree.

  Both `exemption census` blocks are identical in the two logs — nine `READ` lines, all
  matching, including `LEDGER parity vectors = 7`, `LEDGER oracle-refusal vector = 6` and
  `LEDGER money cells compared = 39`. The **only** difference between the two runs is the
  wrong-implementation population.

## BASELINES, RE-DERIVED BY RUNNING (P-83) RATHER THAN BY ARITHMETIC

The "before" column of T360's count table is not subtraction. It is read off
`out/T360-D02-…txt`, which is this same code over this same store **with `LDG-DIV-01`
withheld**:

| figure | withheld (before) | committed (after) |
|---|---|---|
| ledger cells compared | 142 graded, 39 MONEY | 144 graded, **39 MONEY** |
| ledger kills named | 10 money, 21 structural | 10 money, 22 structural |
| ledger citations | 26 | 28 |
| ledger parity | PASS 7 FAIL 0 | **PASS 7 FAIL 0** |
| ledger oracle-refusal | PASS 6 FAIL 0 | **PASS 6 FAIL 0** |

## WHAT THE DRIVES PROVE, TOGETHER

D01 and D02 are one measurement in two halves, and neither half is worth anything alone:

- D02 alone would say "this implementation is not caught", which is a statement about the
  implementation.
- D01 alone would say "this implementation is caught", which is satisfied by any vector that
  happens to go red.
- **Together** they say the thing that matters: `ledger-wrong-residue-rounding` is
  **indistinguishable from the correct port on every vector this store had before T360**, and
  `LDG-DIV-01` is the only thing that can see it. That is the T328 shape (a mutant measured
  SURVIVING before the vector that kills it was promoted), and it is the reason the new class
  is not decoration.

`TestTheWrongImplementationIsIndistinguishableOnEveryOtherVector` asserts the same property in
`go test`, so it cannot silently stop being true between fires.
