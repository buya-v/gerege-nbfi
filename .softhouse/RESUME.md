# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260829-080002` **ITERATION 5, WAVE 2** — FIVE WORKERS DISPATCHED
Written and pushed BEFORE the first `git worktree add` of this wave.

Oracle **REACHABLE** throughout (one transient container restart, observed by `T446`, recovered).
PostgreSQL `localhost:5432`, pinned Fineract `/Users/buv/fineract @ 426a23544`.

## BAR ON `main` — GREEN AND **ATTESTED**, not merely asserted

Every one of wave 1's five merges was graded **on the merge result, in a scratch worktree outside the
repo, before `main` was touched**, then attested BY TREE SHA and pushed only after the pushed tree was
confirmed to BE the graded tree. Latest: `EXIT 0`, probe PRESENT ×1 `up`, `PASS — 46 vectors / 7884
cells`, frontier `11 == 11`, `deadOccurrences 108`.

## WAVE 1 — FIVE REVIEWED PAIRS, ALL MERGED

| Pair | Verdict | Conditions |
|---|---|---|
| `T350`+`T449` | APPROVED WITH CONDITIONS, 2 MAJOR | `T451` |
| `T442`+`T447` | APPROVED WITH CONDITIONS, 3 MAJOR | `T452` |
| `T412`+`T450` | APPROVED WITH CONDITIONS, 2 MAJOR | `T453` |
| `T445`+`T446` | APPROVED WITH CONDITIONS, 2 MAJOR | `T454` |
| `T433`+`T448` | APPROVED WITH CONDITIONS, 1 MAJOR | `T455` |

## ⚠ THE FOUR THINGS THE NEXT FIRE MOST NEEDS TO KNOW

**1. THE DRIVER PUSH GATE IS LIVE AND IT REFUSED THE DRIVER.** At the `T350`+`T449` merge the driver had
graded the merge result AND verified tree identity by hand — and was still refused, because a transcript
is bytes and nothing binds it to the tree it claims to have graded. The remedy is `bar-attest.sh`, which
checks the tree out ITSELF. **`bypass.log` still does not exist. Never bypass; attest.**

**2. `T453` IS MONEY-ADJACENT AND THE HOLE IS OPEN RIGHT NOW.** The gate's cheap path can print PASS over
`guard_no_float_in_capture_requests`. And **nothing installs the gate** — `.git/hooks` is untracked, so
the cloud fire and any CI runner are silently ungated.

**3. SIX LINKS, SIX REACHED "UNREACHABLE" CLAIMS.** T404→T407→T431→T444→T445→T446. Every author who wrote
"unreachable by construction" or "provably cannot win" was reached by the next reader. The newest:
**`U+017F` folds onto ASCII `s` on APFS and sorts AFTER it**, so `conformance.ſh` wins the checkout and
**the harness that RUNS is forged while the committed blob stays honest**. Generalised form, now the
subject of `T454`: *the text that executes is not necessarily the text that is committed.*

**4. THREE REVIEWERS REDDENED THE BAR WITH THEIR OWN INSTRUMENTS** (`T447`, `T446`, `T448`) — and **all
three repaired rather than pinned**, and recorded the failure. `T446`'s merge went `EXIT 2` with **no
probe line at all**, which is NOT an oracle outage. **Run the bar on your own drives before committing.**

## IN FLIGHT — WAVE 2, FIVE WORKERS (all `opus`, worktree-isolated, file sets disjoint)

| Task | Branch | What it is |
|---|---|---|
| `T453` | `softhouse/T453-gate-state-set` | **MAJOR, money-adjacent, live.** The STATE set admits A/M changes that redden three HARD guards; nothing installs the gate. |
| `T454` | `softhouse/T454-longs-route` | **MAJOR.** The `U+017F` sixth route + the watch that pins READS not USES. **Sole `conformance.sh` writer.** |
| `T451` | `softhouse/T451-t449-conditions` | **2 MAJOR.** The `stillborn` arm never consults the ref store; the ref side argues generosity then applies the strict anchor. **Sole `ready-tasks.py` writer.** |
| `T452` | `softhouse/T452-t447-conditions` | **3 MAJOR.** A fourth fail-open candidate; a correct reviewer finding overturned on a search artefact; a census that is a member of the class it censuses. |
| `T455` | `softhouse/T455-t448-conditions` | **1 MAJOR.** `(iv-a)` is closable and the grader already states the rule nine lines above. |

**Disjointness checked before dispatch:** exactly one writer for `conformance.sh` (`T454`) and one for
`ready-tasks.py` (`T451`); the rest write only their own capture/review directories.

## QUEUE AFTER THAT
`T403` (the reconciler's other half) → `T443` + `T441` (both want `conformance.sh`) → `T419` → `T437` →
`T434`/`T435`/`T436` → `T399`, `T425`, `T394`, `T395`.

## OPEN GATES — none blocks anything, no CONTRACT gate open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`, `G-22`.

## NEEDS A HUMAN EVENTUALLY (not a gate, but no agent should guess)
`T286` is **partially landed**: 27 files on `main`, branch 2 commits ahead, **not** an ancestor. Found by
`T350`, confirmed by `T449`. It printed nothing before this iteration.

## Pause reason
None — pre-dispatch record for wave 2. If you are reading this because the fire died, the five tasks
above were **live and are now dead**. Check each branch (`git rev-list --count main..<branch>`) and mark
each `needs_retry` with what it actually carried. **A branch that exists is not evidence of work, and a
branch that is GONE is not evidence of no work** — both directions were observed live this fire.
