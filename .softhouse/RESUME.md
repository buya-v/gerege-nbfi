# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, chain iteration 3 — **IN FLIGHT. FIVE LIVE WORKERS.**

**If you are reading this and no driver session is running, five workers were killed mid-flight.**
Mark each `needs_retry` with the WIP evidence from its branch. `in_progress` never means "work is
happening"; it means "a driver said so, once".

### Why this iteration exists
Iteration 2 ended at ~10:35Z on a `five_hour` rate limit (`resetsAt=1787914200`), not on a stop
condition. The wrapper reconciled state at `cefd8f6c`. The limit had reset by the time this iteration
started (11:15Z), the tree was clean, `origin/main` tip was 47 s old, and **zero workers were live**.

### Pre-flight, measured — not assumed
| Check | Result |
|---|---|
| Lock arm taken | own fire (`20260828-140005`), wrapper-held |
| `origin/main` tip age | 0.01 h |
| `git status --porcelain` | empty |
| `bash .softhouse/conformance.sh` on `main` | **EXIT 0**, probe line **PRESENT** at line 162 reading `up` |
| loanschedule | parity **PASS 46 FAIL 0**, contract-refusal 4, inadmissible 0, 7,884 cells |
| ledger | parity **PASS 7 FAIL 0**, oracle-refusal 6, inadmissible 0, 142 cells (39 money) |
| 13 `ledger-wrong-*` drives | all **KILLED** |
| Pre-fire attestation snapshot | `/tmp/attest-before-iter3.json` (7-term, T318 shape) |

Reference oracle **REACHABLE**: `https://localhost:8443/fineract-provider/actuator/health`.
PostgreSQL up on `:5432`. No prohibited-engine port open.

## WAVE 1 — IN FLIGHT. Five workers. Grants are pairwise DISJOINT.

| Task | Branch | Model | Exclusive grant |
|---|---|---|---|
| `T382` review T374 | `softhouse/T382-review-t374` | opus | `.softhouse/reviews/t382-review-t374/` |
| `T375` T364's conditions on T358 | `softhouse/T375-t364-conditions` | opus | **`.softhouse/conformance.sh`**, `.softhouse/capture/t375-t364-conditions/` |
| `T383` F-T380-1 tail -1 fail-open | `softhouse/T383-t380-conditions` | opus | **`.softhouse/bin/fire-program.sh`**, `.softhouse/capture/t383-t380-conditions/` |
| `T381` T379's R2 anti-calibration | `softhouse/T381-t379-conditions` | opus | `.softhouse/capture/t363-oracle-baseline/instruments/`, `.softhouse/capture/t381-t379-conditions/` |
| `T360` divergence vector class | `softhouse/T360-divergence-class` | opus | `.softhouse/vectors/`, `.softhouse/capture/t360-divergence-class/`, `nexus/internal/apps/ledger/conformance/` |

`T375` is a **RESUME of a killed worker**, from its own 8-commit branch head `2422adc9` — not a restart,
and **not** a consumed retry: it was killed by a rate limit, not rejected.

### Plan gate, checked AT dispatch rather than after
Four of the five are `code` tasks, so check 1 needs a paired reviewer for each. **`T384` (reviews
T375), `T385` (T383), `T386` (T381), `T387` (T360) were filed in the SAME commit as the dispatch**,
before any worker spawned. Iteration 2 found three code tasks dispatched with no reviewer at all; this
closes that shape by construction rather than by inspection.

### Deliberately NOT dispatched, with reasons
- **`T372`** (install the PreToolUse push-before-spawn gate) — its own brief forbids dispatch while any
  worker is live, because it installs a `deny` hook on the **Agent** tool. Reserved for a wave with
  **zero** live workers. This is the only mechanism that would give the push-before-spawn obligation any
  mechanical backing; it currently has none (P-45).
- **`T366`** — the previous manifest records it as touching `conformance.sh`, which `T375` holds.
- **`T373`, `T378`** — blocked on `T370`, which is **parked** (rejected by `T376`, and already T351's one
  retry). `T378` is the landing task that unblocks them.

## MERGE HAZARD carried forward from iteration 2 — read before merging anything
`T374` ships the dead-path pin at **108**; `main` is at **109**; `T375` is at **109**.
**Re-run `.softhouse/capture/t326-frontier-host-state/instruments/10-regen-pin.py` ON THE MERGE RESULT.
Never pick a side between two pins** (P-83: two independent movements of one pinned number reconcile by
running, never by arithmetic).

`T360` may move the parity counts. If it does, the summary and **every pinned census that restates them**
move in ONE commit, and the bar is re-run on the merge result.

## UNMERGED AND COMPLETE ON BRANCHES
| Task | Branch | Head | Waiting on |
|---|---|---|---|
| `T374` | `softhouse/T374-t362-conditions` | `f4157d42` | `T382` (dispatched) |
| `T376` | `softhouse/T376-review-t370` | `9255d1af` | nothing — it is a review, verdict **REJECTED** |
| `T370` | `softhouse/T370-t351-retry` | `4925bbef` | **parked**; substance verified good, lands via `T378` |
| `T351` | `softhouse/T351-progress-accounting` | `a0139c5d` | superseded by `T370`/`T378` |
| `T369` | `softhouse/T369-review-t351` | `e10e3f07` | `T373` |

## THE PROGRAM-LEVEL FACT THIS DRIVER IS SURFACING TO BUYAN
`T352` found it and it is still true, measured again this iteration: **the READY queue contains 31 tasks
and not one of them ports Fineract code.** Every one repairs the harness. Program progress stands at
**1 of 17 contexts done, 182 LOC of ~544,000**. The harness work is not waste — the bar has caught a
false PASS in nearly every fire — but a driver that only ever dispatches harness repair will never
finish the migration. Raised as `G-20` in `.softhouse/gates.md`; it blocks nothing and needs no answer
to keep working.

## Open gates
`G-19` (oracle accepts a sub-minor-unit residue the port refuses) — OPEN for Buyan, blocks nothing.
`G-20` (the READY queue has no porting work in it) — OPEN for Buyan, blocks nothing.

## Pause reason
**Not paused.** Five workers dispatched and being awaited by chain iteration 3.
