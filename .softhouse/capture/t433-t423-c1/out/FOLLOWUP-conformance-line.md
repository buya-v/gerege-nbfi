# T433 follow-up — the ONE `conformance.sh` line that finishes ARM F's wiring

**Status: DEFERRED BY SCOPE, NOT FORGOTTEN. This file is the deferral, stated by name.**

## Why it is deferred

T433's assigned paths are `.softhouse/capture/t393-t382-conditions/`,
`.softhouse/reviews/A2-11/` and `.softhouse/capture/t433-t423-c1/`. T433 may **not** edit
`.softhouse/conformance.sh` — **T445 holds it this wave** — nor `.softhouse/bin/ready-tasks.py`
(T350 holds it).

Two things were checked before writing this, so "there was no hook to join" is a statement
about a search and not about the world:

```
grep -n "verify-capture-integrity\|A2-11/run-all\|reviews/A2-11" .softhouse/conformance.sh
    -> 0 hits
grep -n "python3 \.softhouse\|bash \.softhouse\|GUARDS=\|guard_list\|SCRIPTS="  .softhouse/conformance.sh
    -> only comments about how to invoke conformance.sh ITSELF
```

`conformance.sh` (5,500 lines) invokes **no script under `.softhouse/`** today. There was
therefore no existing generic hook for ARM F to join, and inventing one inside a file T433
does not own would be the worse defect.

## What T433 DID wire, so this is a gap and not a hole

ARM F is **inside** the shipped grader — section 8 of
`.softhouse/reviews/A2-11/verify-capture-integrity.py` — so it inherits every executable that
already ran that grader. Established by grep, not asserted:

| invoker | how it runs ARM F |
|---|---|
| `.softhouse/reviews/A2-11/run-all.sh:226` | `sec 10 0 python3 "$DIR/verify-capture-integrity.py"` — **adjudicated section 10**, so a non-zero exit MOVES the section and fails RUN-ALL VERDICT |
| `.softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh:31` | `INT="$A211/verify-capture-integrity.py"` — and its `f1-13b` row now **expects `0 1`**, so removing ARM F makes T393's own drive FAIL |
| `.softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh:100,117,130,145` | four direct `python3 …/verify-capture-integrity.py` red drives |
| `.softhouse/capture/t433-t423-c1/instruments/20-t433-armf-in-situ-drive.sh:34` | T433's own RED/GREEN drive |
| `.softhouse/reviews/t382-review-t374/instruments/30-saturation-audit.sh:56`, `60-defeat-arm-a-baseline.sh:26` | T382's audits |
| `.softhouse/reviews/t423-review-t393/instruments/10,30,50,61-*.sh` | T423's drives |

## THE EXACT LINE TO ADD

In `.softhouse/conformance.sh`, inside `run_guards()` (currently line 4308), beside the other
HARD guards:

```bash
hard 'ARM F: every post-fork captured observation vs the blob at the commit that FIRST ADDED it (C-T423-1)' \
     bash .softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh
```

The callable already exists, is committed, and is driveable in both directions:

- `.softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh`
- exit **0** = ARM F present, wired, graded a non-empty population, no unadjudicated difference
- exit **1** = a wiring assertion failed OR a post-fork observation differs from its birth blob
- exit **2** = REFUSED (could not measure) — never read as a pass
- it reads `T433_ROOT` and hard-codes **no host path** (T256/T298)
- runtime is one invocation of `verify-capture-integrity.py` (~45 s on this machine)

**Exact spelling of `hard` must be confirmed against `run_guards()` by whoever adds the line**
— T433 read `conformance.sh` but did not edit it, and a helper name copied from memory is the
kind of claim this program grades as unverified.

## Cross-check the adder should run

After adding the line, the guard must be seen to FAIL, not only to pass (P-22):

```
# RED: remove ARM F from the grader in a scratch clone, then run the bar's guard
python3 - <<'PY'
import re,sys
p='.softhouse/reviews/A2-11/verify-capture-integrity.py'
s=open(p).read().replace('=== 8. ARM F','=== 8. ARM-F-REMOVED')
open(p,'w').write(s)
PY
bash .softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh   # must exit 1
```
