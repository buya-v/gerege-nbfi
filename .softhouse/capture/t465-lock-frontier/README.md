# T465 — the dead-path frontier and the fire-lock cycle

**Owner: T465.** Filed from `T461`'s independent review of `T453`. Everything here was
re-derived on this tree; nothing was inherited from the review.

## The finding, in one table

The whole bar, driven twice per tree, with the lock in and out of the index. Same instrument,
same fixture, same toolchain; the ONLY difference is whether the fire lock is in `git ls-files`.

| tree | lock HELD | lock RELEASED |
|---|---|---|
| `3f4e236a` (before) | exit 0, probe-lines=1, `VERDICT: PASS`, 46 vectors / 7884 cells | **exit 2, probe-lines=0** |
| `6ca0ea03` (after) | exit 0, probe-lines=1, `VERDICT: PASS`, 46 vectors / 7884 cells | exit 0, probe-lines=1, `VERDICT: PASS` |

`instruments/60-bar-on-a-released-tree.sh`; transcripts in `out/` and `out-before/`.
The CONTROL is the left column and it is checked FIRST — an arm that exits 2 for a missing
toolchain or an unreachable reference oracle looks exactly like the finding, so the instrument
refuses rather than reporting an arm nobody can interpret.

## Why it was repaired at the instruments and not pinned

`instruments/10-lock-arms.sh`, against `3f4e236a`, two calibrations and four arms:

```
CALIB-MINUS                      exit=0  GREEN   rows=108 pinned=108 added=0  removed=0
CALIB-PLUS                       exit=1  REFUSED rows=109 pinned=108 added=1  removed=0
ARM-A-LOCK-HELD                  exit=0  GREEN   rows=108 pinned=108 added=0  removed=0
ARM-B-LOCK-RELEASED              exit=1  REFUSED rows=125 pinned=108 added=17 removed=0
ARM-C-PIN-AT-RELEASED            exit=0  GREEN   rows=125 pinned=125 added=0  removed=0
ARM-C-PIN-AT-RELEASED-LOCK-BACK  exit=1  REFUSED rows=108 pinned=125 added=0  removed=17
```

**ARM C is the one that decides the remedy.** Pinned at 108 the guard refuses after every fire
exit; pinned at 125 it refuses during every fire. **The frontier has no fixed point while any
tracked instrument spells the lock path**, so *pinning is not a remedy that exists here* — the
pin's own anti-amnesty rule (`removed>0` is a refusal) closes that door from the other side.
That is a measurement, not a preference, and it is why the 17 sites were repaired.

Against `6ca0ea03` the same instrument reports `GREEN rows=108` on BOTH arms and
`CALIB-PLUS` still goes red on a planted literal — the guard did not stop seeing, the tree
stopped oscillating.

## The 17 members, with their tree

Frontier rows present at `3f4e236a` **only when the lock is out of the index**
(`out-before/arm-B-added-rows.txt`). 17 rows, 17 distinct files, 43 quoted literals between
them; all 43 are gone at `6ca0ea03`.

```
.softhouse/bin/fire-program.sh                                          | .softhouse/LOCK
.softhouse/bin/ready-tasks.py                                           | .softhouse/LOCK
.softhouse/capture/t279-lock-partition/audit-this-fire.py               | .softhouse/LOCK
.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py           | .softhouse/LOCK.
.softhouse/capture/t325-adopt-attestation/instruments/30-survey-drive.sh| .softhouse/LOCK
.softhouse/capture/t349-pretooluse-eval/probe/replay-real-dispatches.py | .softhouse/LOCK
.softhouse/capture/t349-pretooluse-eval/probe/spawn-gate-candidate.py   | .softhouse/LOCK
.softhouse/capture/t350-reconcile-content/bin/50-drive-reconcile.sh     | .softhouse/LOCK
.softhouse/capture/t353-t342-conditions/bin/lock-host-census.sh         | .softhouse/LOCK
.softhouse/capture/t453-t450-conditions/instruments/drive-arms.sh       | .softhouse/LOCK
.softhouse/hooks/push-before-spawn-audit.py                             | .softhouse/LOCK
.softhouse/reviews/T189-probe/hardening.sh                              | .softhouse/LOCK
.softhouse/reviews/T189-probe/reachability.sh                           | .softhouse/LOCK
.softhouse/reviews/t172-probe/check-lock-exclusion-anchor.sh            | .softhouse/LOCK
.softhouse/reviews/t172-probe/run-move-demo.sh                          | .softhouse/LOCK
.softhouse/reviews/t202-probe/make-mutants-b.py                         | .softhouse/LOCK
.softhouse/reviews/t202-probe/patch.py                                  | .softhouse/LOCK
```

The row for `run-ownership-matrix.py` is `.softhouse/LOCK.` — with a full stop — because the
literal is an English sentence (`"…does not TOUCH .softhouse/LOCK."`) that the census's
`.softhouse/`-rooted **trim** turns into a bare path. Worth knowing: the trim can manufacture a
concrete-looking path out of prose, and the PROSE bucket only catches it when the whitespace is
*after* the `.softhouse/`.

## The repair is a change of spelling, and that is MEASURED

`instruments/20-assembly-parity.py` evaluates each repaired file's own declaration chain, in
that file's own interpreter, and compares the value against the literal it replaced:

```
T465-ASSEMBLY-PARITY: files=17 sites=19 baseLiterals=43 headLiterals=0 mismatches=0
```

Its CALIBRATION is enforced: if the BASE commit spells zero literals it aborts at 92, because a
clean HEAD proves nothing against a clean BASE.

**It earned its keep during the repair.** It reported one MISMATCH that was a genuine behaviour
change and not a spelling one: a prose line reworded inside `t202-probe/patch.py` turned out to
sit **inside a `new = '''…'''` patch payload**, i.e. inside the bytes that patch applied to
`fire-program.sh`. Reverted, spliced instead, re-driven clean.

## The re-scoped `t172` anchor probe

`check-lock-exclusion-anchor.sh` bound to the SPELT pathspec, so the repair moved its subject.
It is re-scoped rather than deleted, and the new shape is strictly stronger: the pathspec value
is **reconstructed by evaluating the target's own three declaration lines** and compared once,
which also catches a widening introduced AT THE DECLARATION — where no use site would show it.
A widening at a USE site drops the line out of the census, and the categorical floor
(`>=1 DETECT`, `>=1 STAGE`) is what turns that into a named failure; that floor was decorative
before and is load-bearing now. Driven against the live file: `VERDICT: PASS`, 2 sites,
reconstructed value `:(top,exclude).softhouse/LOCK` — byte-identical to what it replaced.

## The minor conditions

| id | what was done | evidence |
|---|---|---|
| C-T461-2 | `gate=`/`headblob=` got a READER (R3) and a second WRITER (`bar-attest.sh`'s FULL rows). Driven red/green/blank. | `instruments/30-r3-provenance-drive.sh`, `out/R3-RESULTS.txt` |
| C-T461-3 | FU-T453-1's blocker does not reproduce: `dirs=219` materialised vs `dirs=237` caller. | `instruments/40-cheap-tier-blocker.sh`, `../t453-t450-conditions/CORRECTIONS-T465.md` |
| C-T461-4 | raised as **G-23** in `.softhouse/gates.md`, ENGINEERING half split from RESERVED half. | `.softhouse/gates.md` |
| C-T461-5 | 335/400 = 83.8 % shipped vs 336/400 = 84.0 % capture-only — ONE commit. 27+43 = **70** entries. | `instruments/50-coverage-remeasure.py` |
| C-T461-6 | `$FIRE_MKTEMP` restored in the T453 reconcile block. | `.softhouse/bin/fire-program.sh` |
| C-T461-7 | answered by the repair; `seed_full`'s limit written into `drive-arms.sh`. | `out/RESULTS.txt`, `../t453-t450-conditions/CORRECTIONS-T465.md` |

## Running any of it

Every instrument takes its destination as an argument, refuses on an unbuildable fixture with a
9x code that is never an arm verdict, and prints its probe line only when it reached one.

```
bash instruments/10-lock-arms.sh              <rev> <outdir>
python3 instruments/20-assembly-parity.py     <base-rev> [--json OUT]
bash instruments/30-r3-provenance-drive.sh    <outdir>
bash instruments/40-cheap-tier-blocker.sh     <rev> <outdir>
python3 instruments/50-coverage-remeasure.py  [--ref origin/main] [--n 400]
bash instruments/60-bar-on-a-released-tree.sh <rev> <outdir>
```
