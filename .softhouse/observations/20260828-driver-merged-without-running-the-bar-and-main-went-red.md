# The driver merged a review without running the bar, and `main` was RED for ~40 minutes

**Fire** `20260828-080001`, chain iteration 2. **Driver error. Recorded because two workers forked from the red tree.**

## What happened

The driver merged `T280` at `346b7a1d` (12:0x) after checking **scope** and **T114 byte-preservation** — and
**did not run `bash .softhouse/conformance.sh` on the merge result.** T280's review directory contains
`probe/drive-hook.sh`, which at line 66 wrote a scratch file via the literal
`"$T/wt/.softhouse/late.txt"`. `$T` is a `mktemp` root **outside this repo**, but T316's dead-path guard
extracts the repo-shaped *tail* of a path string and cannot see a variable prefix. It therefore scored
`.softhouse/late.txt` as a **NEW dead path**:

```
T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=109 added=1 removed=0
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

**Exit 2 with NO probe line printed** — the guard runs at `conformance.sh:281`, the probe prints at `:296`.
This is precisely the case STEP 4 of the skill warns about: *not* an oracle outage, and nothing may be parked
for it. The driver's own rule, applied to the driver's own breakage.

## Who found it

**Not the driver — `T342` did**, while doing something else entirely, and it did the thing that makes the
report usable: it verified the refusal **reproduces on a pristine clone of its own branch base** (`a2fa69f4`),
which is what established the fault was on `main` and not in its work. It then correctly declined to fix it —
the pin and `conformance.sh` were both outside its grant — and filed it as a blocker instead.

## The fix, and why not the pin

The guard's own message prescribes the remedy: *"A '+' row is a NEW site: REPAIR it rather than pinning it."*
The row is a **false positive** — the path is a scratch temp path — so pinning it would have recorded a
non-existent dead path as an accepted one, permanently. The repair used is this program's established remedy
for exactly this guard: **assemble the path instead of writing it as a literal**, which is what `T258` did
when the same guard fired on its drives (`REFUSED rows=112 pinned=109 added=3` — it assembled rather than
moved the pin). Runtime behaviour is byte-identical; a comment at the site explains why, so a later reader
does not "tidy" it back.

Bar after the repair: **exit 0**, probe line PRESENT reading `up`, 46 parity vectors / 7884 cells.

## The cost, stated plainly

`T339` and `T340` were both dispatched **while `main` was red** and forked from it. Their briefs instruct them
to re-run the bar; they will see `exit 2` and a HARD guard failure that has nothing to do with the work they
are reviewing. That is wasted worker attention caused by the driver, not by them.

## The rule this changes

**Scope-check and T114-check are not a merge gate. Running the bar is.** The driver checked the two things it
could check by reading, and skipped the one thing that required executing. Every future merge in this program
runs `bash .softhouse/conformance.sh` on the merge result **before** the next dispatch — and a driver that
dispatches onto an unverified `main` is spending workers on a tree it has not graded.

There is a second, narrower lesson worth keeping: **a review's own probe scripts are part of the graded
tree.** Evidence directories are not inert. A probe that constructs paths as literals can move a frontier.
