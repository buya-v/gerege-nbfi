# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-080001` round 2, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **TEN DISPATCHED, TEN COMPLETED, TEN MERGED, ZERO LIVE AT EXIT.** No isolation violation; every branch
  scope-checked by the driver on the **three-dot** diff before merge.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells compared
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
         kills named 103 money, 7 structural
--prove              23 passed, 0 failed
ledger-invariants    exit 0
go build 0 · go vet 0 · go test -count=1 ok (ledger, loanschedule, conformance)
gofmt -l             exactly contract.go   (expected, G-3)
t36/attest.py        567e4cf0…             UNCHANGED — T180's whole deliverable
vector store         ce821c638724237652b6b29627148d34b72fab3b   UNCHANGED
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire, all ten**: `T210`, `T176`, `T209` (wave 1a); `A2-21`, `A2-22`, `T212`, `T168`, `T162`,
`T211`, `T180`.

---

# HEADLINE 1: two claims this program has been repeating are now corrected

**(a) `run_guards` invokes SEVEN guards, not six.** `RESUME.md`, the previous fire's headline **and the
driver's own T209 brief** all said six. That count took only the `|| failed=1` arm and silently dropped
`guard_graded_root_is_this_tree`, a **HARD** guard with an early-exit shape. Caught by **A2-21**.

**(b) "I-3 and I-4 went from ZERO enforcement to HARNESS-ENFORCED" is an OVERSTATEMENT.** Driver-verified
from the guard's **own green-run output**: three of its four detection classes inspect an **empty
population** —

```
NIL-COVERAGE — the SQL surface inspected 3955 string literals and found ZERO SQL DML statements of any
kind under …/nexus. … the I-4 SQL classes (I4-DML, I3-SQL-BALANCE) are proven by this program's
--selftest and NOT by this tree.
NIL-COVERAGE — zero mutating driver calls … class OPAQUE-SQL inspected an empty population. The Go
module declares no database driver at all.
```

So enforcement is **live for the balance-identifier class** and **LATENT for SQL**. The guard says this
itself — which is exactly why **T209**'s work to make `CANNOT-CATCH` reach a green run mattered. The two
findings are the same story from opposite ends.

## HEADLINE 2: a fire can now be stopped

`T211` made SIGTERM work. The driver **re-ran its probe on all three arms** rather than accepting its matrix:

| arm | result |
|---|---|
| pre-fix, SIGTERM | trap **never ran**, 45.002 s to harness SIGKILL, LOCK **STRANDED**, child **ORPHANED** under pid 1 |
| post-fix, SIGTERM | handler entered, driver tree of **6** stopped, no survivors, lock released, `rc=143` |
| happy path, rc 0 **and** 7 | `driver exited rc=N` → `run_driver RETURNED rc=N` → `BODY COMPLETED NORMALLY` → lock released |

It refuted its own brief three ways: **`wait` alone is insufficient** (a handler that RETURNS restarts the
wait, hanging 20 s); **background+wait+exit still ORPHANS the child**, trading a stranded LOCK for an
*unlocked* `claude` still writing to the repo — strictly worse, hence `stop_driver()`; and
**`${pipestatus[1]}` dies** because `$pipestatus` holds one element after `wait`.

**Takes effect NEXT fire** — the merge renames the inode; pid 65843 ran the old bytes to the end.

## HEADLINE 3: "zero stranded" answered a narrower question than it was reported as answering

The previous sweep asked `git status --porcelain` — **uncommitted** work. Re-confirmed: **0 dirty** across
93 worktrees. The other half — **committed to a branch and never merged** — is **79 file-paths on 23
branches**, concentrated in four. `T108`, `T109`, `T131`, `T22` are all recorded **`done`**, and
`.softhouse/reviews/T131-review-of-T108.md` is **on `main` citing four paths that are not**. → **T214**.

---

## THE NEXT FIRE STARTS HERE

**16 tasks READY. 1 blocked (`T116`, on `T114` — which has NO ENTRY in `tasks.json` and can never resolve;
re-scope or re-point it, it has been carried unresolved for several fires).**

1. **`A2-15` — now unblocked**, because `A2-21` delivered DEC-2 rev 3. Promote the A2 raw captures into
   parity vectors. **This is the only READY task that would add a vector**, and no vector has been added for
   two fires. Read §5.2 first: A2-21 added a **positive control** and a **required RED demonstration**
   precisely so A2-15 cannot pass vacuously.
2. **`T214`** — the 79 unmerged evidence paths. Prefer `git checkout <branch> -- <paths>` over merging
   ancient branches. Do **not** delete any `softhouse/*` branch; they are currently the only copy.
3. **`A2-24`** — adjudicate A2-22's self-flagged narrowing of `CorroborationsClaimed` (no independent
   finding behind it; indistinguishable on today's store; two-line revert).
4. **`T215`** — the probe covers one of **two** LOCK-exclusion sites; the sites moved to `:496`/`:517` after
   T211's rewrite. **`T217`** — T211's own two follow-ups.
5. Then `T193`, `T192`, `T195`, `T160`, `T207`, `T145`, `T164`, `T174`, `A2-23`, `T213`, `T216`.

**`G-11` remains OPEN and NOT RATIFIABLE.** A2-21 delivered rev 3 and **correctly did not ratify it** — it
is not authorised to. Ratification needs a further **independent** review passing clean.

---

## Corrections made against the DRIVER this fire — read before trusting its numbers

**P-63 — the driver validates against TEXT instead of against the LIVE PROGRAM. Four times in one fire.**

1. A branch sweep that inspected **one file per branch** and reported it as the whole diff (20 files on
   `T38-dec1-v7-pass2` alone). Caught by hand-checking a single branch. P-35 inside the check written to
   find P-35.
2. **"six guards"** pasted into the T209 brief from an old description. Corrected by A2-21.
3. **"SCRATCH 337→337, 7 chain moves"** demanded of T212; truth at `cc33f7f` is **357→357 and 9**. T212
   reported the discrepancy instead of tuning to hit the driver's number.
4. A one-line regex that matched **line 172 of `fire-program.sh` — a COMMENT QUOTING T202's DELETED CODE** —
   from which the driver briefly concluded T168 was wrong about SIGQUIT coverage. **T168 was right**;
   `:202-206` set INT/TERM/HUP/QUIT on separate lines.

**P-64 — an INCONCLUSIVE run is indistinguishable from a RED one, and the default reading is wrong.** The
driver's first happy-path check of T211 reported `LOCK PRESENT-STRANDED / DRIVER CHILD ORPHANED` and read
exactly like a regression. It was **misconfigured** — `T211_FAKE_RC` unset, so the fake child slept its full
300 s past the probe's 40 s ceiling and the arm never reached completion. **Before calling an arm red, prove
the arm RAN.**

**Also**: the driver removed `/private/tmp/t-merge` (detached, 5 commits ahead) **before** checking what was
on it, then checked. No deliverable lost — all scratch test-merges from the P-24 rig, surviving as dangling
objects. The check belonged first.

## Corrections made against already-merged work

- **T180 → T161**: T161's own prover asserted `attester == PRE-FIX` on the SIGKILL/POST-FIX row and **would
  have failed on the fixed script for the right reason**. Corrected rather than left to rot.
- **T168 → itself**: found the SIGQUIT omission a **second time**, in `restore_store()`'s re-entrancy guard.
- **T176 → T169's framing**: chose "fix the generator" with a reason the brief did not supply —
  `StackOverflowError` is an `Error`, not a `RuntimeException`, so the original handler **could never have
  caught** the failure mode T159 exists to probe.

## STANDING INSTRUCTIONS

- **Re-derive every figure from the live artefact at the moment of dispatch (P-63).** A number in
  `tasks.json` is evidence of when it was true, not that it is true. Three of this fire's driver defects
  were stale or mis-scoped figures.
- **Before calling an arm RED, prove the arm RAN (P-64).** Check the probe's preconditions and ceilings
  first; a run that measured nothing looks exactly like a failure.
- **A regression probe must bind by CONTENT, not line number** — proven inside this fire. T211 moved
  `run_driver` 237–291 → 356–474 and T210's probe, merged hours earlier, **still passed**.
- The canonical vector-store digest is `git rev-parse HEAD:.softhouse/vectors` (**P-61**). Never
  `find | shasum | shasum`. Publish any digest **with its recipe** (P-38).
- **Verify a refusal by what it SAYS and what population SURVIVES, never by exit code (P-62)** —
  `exit 2` is overloaded across unusable corpus, failed hard guard, unreachable oracle, wrong repo root,
  and an I-3/I-4 violation.
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The shell's working directory persists between tool calls.** It has now bitten this program three times.
- **Count the PROGRAMS before the votes (P-58).** `grep` here is a shell function re-execing as **ugrep with
  `-I`**; `/usr/bin/grep` is BSD 2.6.0-FreeBSD. **And make any census distinguish live code from
  commentary** — the driver's regex matched a comment quoting deleted code this fire.
- **Never execute a promote or rewriter script from the repo root**, and a `/tmp` copy **cannot run** — they
  derive `ROOT` from `__file__`, so a naive scratch test is a **null control** (P-36). Use a **sibling file
  in the same directory** (T161's shape, adopted by T180).
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root. Invoke the harness
  with **`bash`**, never `sh` (exit 3 = wrong-interpreter refusal). **Never `gofmt -w` `contract.go`** (G-3).
- **Do not modify `.softhouse/bin/fire-program.sh` while a fire runs.** Merging is safe: git **renames**.

## What is NOT true, and must not be inferred from the green bar

**Nothing grades the ledger's money.** The 43 passing vectors are `loanschedule`'s; **zero** touch a GL
account, a mapping, a financial activity or a journal entry. **I-3/I-4 are checked in source for the
balance-identifier class only — three of the guard's four detection classes inspect an EMPTY population,
and the SQL classes are proven by `--selftest`, not by this tree.** `G-4`, `G-5`, `G-8`, `G-10` remain OPEN,
and **`G-11` is OPEN and NOT RATIFIABLE**. **No vector was added this fire, and none has been added for two
fires** — `A2-15` is the task that changes that. **Nothing was cut over, and nothing here authorises it.**
The gate register at the top of `gates.md` is authoritative.
