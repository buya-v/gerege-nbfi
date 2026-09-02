# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `cloud-20260902-2000` — CLOUD CATCH-UP. THREE ANALYSTS IN FLIGHT. ORACLE UNREACHABLE BY DESIGN.

> **READ THIS FIRST — THE LOCAL PIPELINE HAS BEEN DEAD SINCE 2026-08-29 AND NOBODY NOTICED FOR FOUR DAYS.**
>
> Measured on `origin/main`, not inferred — and measured **after `git fetch --unshallow`**, because the
> clone this sandbox starts from is **shallow** (60 commits, back only to 2026-08-29 21:51) and the first
> version of this table was truncated at the graft, reporting 14 real commits for 2026-08-29 where the
> full history says **505**:
>
> | Day | commits | lock/reconcile/release no-ops | real work |
> |---|---|---|---|
> | 2026-08-25 | 3 | 3 | **0** |
> | 2026-08-26 | 18 | 18 | **0** |
> | 2026-08-27 | 104 | 16 | 88 |
> | 2026-08-28 | 566 | 7 | 559 |
> | 2026-08-29 | 513 | 8 | 505 |
> | 2026-08-30 | 18 | 18 | **0** |
> | 2026-08-31 | 18 | 18 | **0** |
> | 2026-09-01 | 2 | 2 | **0** |
>
> Eighteen consecutive local launchd fires (six a day: 08/11/14/17/20/23) took the lock, ran the wrapper
> reconcile and released, in about 90 seconds each, and **advanced nothing**.
>
> **AND IT HAS HAPPENED BEFORE.** 2026-08-25 and 2026-08-26 are the same shape — 21 fires, 0 real
> commits — and the program recovered on 08-27 without anything being recorded about why it stopped or
> why it restarted. So this is a **recurring** failure of the scheduler, not a one-off, and the fact that
> a four-day and a two-day outage both passed unremarked is the strongest possible evidence for the point
> in the incident record: **the wrapper detects a zero-turn fire and nothing escalates one.** The wrapper classified the
> last one itself: *"**THE DRIVER PRODUCED 0 MODEL TURNS** and no quota rejection was recorded — cause
> UNKNOWN"*, rc=`1`, fire `20260901-080005`.
>
> **It is not the quota.** `classify_driver_turns()` (`.softhouse/bin/fire-program.sh:2442`) emits a
> *different, named* line when a rate limit rejected the fire, and that line was not the one written.
> Zero assistant events with no rejection recorded is the `claude` CLI failing to produce a turn at all —
> an expired credential on the Mac mini is the first thing to check, not the driver's logic.
>
> **The 09-01 08:00 fire also died before releasing `.softhouse/LOCK`**, which is why this cloud fire found
> a 36.5-hour-old lock and took it over under STEP 0 **arm 3** (the 24 h CEILING); arm 5 agreed
> independently, since the tip was equally old. Arm 2 was deliberately not used — the lock names a pid on
> another host and this driver never judges a pid it cannot see.
>
> **What Buyan must do on `Buyanmunkhs-Mac-mini`** (no agent can do it — the box is not reachable from the
> cloud sandbox): read `/Users/buv/Library/Logs/gerege-nbfi/fire-20260901-080005.jsonl`, then run
> `claude -p "ok"` by hand and read the actual error. Until that box produces model turns again, **the
> oracle-reaching half of this program is stopped**, and only the oracle-free half (this fire's kind of
> work) can advance.

## Oracle state — MEASURED THIS FIRE, NOT ASSUMED

`bash .softhouse/conformance.sh` on `0e1701c5`: **EXIT 2**, probe line **PRESENT** at output line 270 and
reading **`down`** (`https://localhost:8443/fineract-provider/actuator/health`). All three of the outage
conditions in `/softhouse-program` STEP 4 hold, so this is a genuine oracle outage and **not** the
exit-2-with-a-dead-guard case: the run reached the probe, which sits *after* `run_guards`, so no HARD guard
failed silently. There is no Docker daemon and no PostgreSQL in this sandbox; `pg_isready` gets no response.

**VERDICT: UNUSABLE (exit 2) — THIS IS NOT A PASS**, and nothing this fire does may be graded by the bar.
Consequence, and it is the reason none of the 53 READY tasks was dispatched: **every one of them is an
instrument/harness `code` task whose merge would have to be graded on the merge result, and no trustworthy
verdict is available on this host.** Grading them here would be exactly the "lower the bar to keep the loop
moving" that the driver may never do.

## WAVE 1 — DISPATCHED, LIVE (all three ORACLE-FREE by construction)

| Task | Branch | Subject |
|---|---|---|
| `T487` | `softhouse/T487-a1-journalentry-behaviour` | Slice **A1** behaviour extraction — journal-entry posting, the double-entry engine (63 files, 11,374 LOC at the pin) |
| `T488` | `softhouse/T488-tierD-gl-corpus-capture-plan` | Tier D — mine the GL/journal-entry test corpus into a **capture plan** the next oracle-reaching fire executes |
| `T489` | `softhouse/T489-tierC-platform-gap-audit` | Tier C — map the platform surface onto what Nexus already provides; classify gaps only |

Wave 2 is the paired INDEPENDENT reviewers `T490`/`T491`/`T492`, one per landed branch, filed in the SAME
commit as this dispatch and dispatched only after wave 1 lands.

**IF YOU ARE READING THIS AND THE FIRE IS NOT RUNNING, THE WORKERS WERE KILLED.** Each was dispatched to an
isolated worktree on the branch named above. Check `git log --oneline main..<branch>` for each; a branch
with no commit means that worker died before committing and its task must be set `needs_retry`, never left
`in_progress`.

## WHY THIS WORK, AND NOT THE 53 READY TASKS — G-20 IS NOW THE PROGRAM'S BIGGEST PROBLEM

G-20 was raised on 2026-08-28 on the effort ratio. This fire re-measured it with the gate's own git
instrument and **amended G-20 in `gates.md`**: over the 7 days to 2026-09-02, `.softhouse/capture/` took
**44.2 %** of 1,227 commits (34.5 % when the gate was raised) and `.softhouse/reviews/` **22.9 %** (16.8 %),
while `nexus/` — which still includes the grading harness, so it is an *upper* bound on porting — sat flat
at **2.7 %** and the vector store at **1.1 %**. The ratio did not hold; it got worse.

> **A claim this driver withdrew before relying on it.** It first measured the READY queue by `files_hint`
> (46 of 53 declaring only `.softhouse/`; the 5 touching `nexus/` all pointing at a `…/conformance/`
> directory) and was about to write *"not one READY task ports a Fineract behaviour."* **G-20 already
> warns, in its own text, that `files_hint` undercounts and that exactly that sentence is FALSE and must
> not be quoted.** Reading the gate before citing it is what caught this. The git measurement above
> replaces it.

Slice **A1 is the money core of Tier A** (the double-entry engine) and it has no behaviour document at all,
while A2's has been written for eleven days (`docs/analysis/tierA-a2-behaviour.md`, 1,151 lines). Writing
A1's costs no oracle, blocks on nothing, and is the input both the capture plan and the eventual Go port
consume. That is the highest-value oracle-free work available, and it is what this fire spent itself on.

Slice **A1 is the money core of Tier A** (the double-entry engine) and it has no behaviour document at all,
while A2's has been written for eleven days (`docs/analysis/tierA-a2-behaviour.md`, 1,151 lines). Writing
A1's costs no oracle, blocks on nothing, and is the input both the capture plan and the eventual Go port
consume. That is the highest-value oracle-free work available, and it is what this fire spent itself on.

## OPEN GATES — none blocks anything, no CONTRACT gate open
`G-2`, `G-3`, `G-4`, `G-5`, `G-6`, `G-8`, `G-9`, `G-10`, `G-11`, `G-12`, `G-13`, `G-19`, `G-20`, `G-21`, `G-22`.
`ready-tasks.py` inspected every id in `program.json.gates_pending` and reports **0 open CONTRACT gates**.

**For Buyan, and it is not a gate — it is an outage:** the local fire has produced no model turns for four
days. Everything above about G-20 is real, but it is second to this: with the Mac mini down, no vector can
be captured and no conformance verdict can be reached at all.

## Pause reason
Not paused — wave 1 in flight at dispatch time.
