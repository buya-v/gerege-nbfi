# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-125942`, 4th of the day, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **TEN DISPATCHED, TEN COMPLETED, TEN MERGED, ZERO LIVE AT EXIT.** No isolation violation; every
  branch's scope checked by the driver before merge.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells compared
         contract-refusal 4 · self-test 1 · inadmissible 0 · harness errors 0
         invariant violations 0
go build 0 · go vet 0 · go test ok (ledger, loanschedule, conformance)
DEC-1 49dc8923… and contract.go 0db73d4a… UNMOVED before, during and after every merge
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire, all ten**: `T189`, `T188`, `T182`, `T186`, `A2-13` (batch 1); `T187`, `T191`,
`T184`, `T183`, `A2-14` (batch 2).

---

# THE HEADLINE: a contested count settled by two BLIND derivations agreeing exactly

Three prior counts of the unguarded-rewriter population disagreed (T178: 25 as 21+4; the driver's
grep: 21+8; T179: 22 as 17+5). The driver dispatched **T187 and T183 in parallel**, each required to
state its own counting rule, each **forbidden to read the other's branch**. They used different
methods — **T187 by EXECUTING all 29 scripts** against scratch copies, **T183 by a whole-repo static
sweep** of 386 Python files / 280 write sites — and reached:

| | files | DEC-1 | contract.go | both |
|---|---|---|---|---|
| **T187** | **25** | **20** | **7** | **2** |
| **T183** | **25** | **20** | **7** | **2** (27 pairs) |

They also independently agreed on *why every prior count differed*: T179's 22 misses **exactly**
`edit18/20/21`, whose write target is a helper **parameter**; T178's 25 total is right and its 21/4
**split** is wrong (assigned by filename, not target — `edit22.py` targets `contract.go`); the
driver's 21/8 was a **mention** count, separated from 20 by one file, `leakgrep.py`, **which performs
no write at all**. Neither adjusted toward the other. **Do not re-litigate this number.**

## THE SECOND HEADLINE: the no-float MONEY guards were failing OPEN

`conformance.sh:546` (float in a vector) and `:607` (float64 in Go) — the guards enforcing the **first
non-negotiable in `CLAUDE.md`** — were `perl … | grep -aEq`. `grep -q` exits 0 **the moment it
matches**, `perl` dies of EPIPE, `pipefail` promotes the pipeline to non-zero, and the enclosing `if`
reads **FALSE on a float it did find**. Plus `:1290`. **All three fixed (T191), 24/24 red-green arms.**

**Latent, not live** — and T191 is explicit that a green run afterwards is not evidence one ever was.
It measured the threshold **per producer/consumer pair** on this host (perl 64,776 B; bash builtin
`printf` 65,549 B), establishing that inheriting T188's single number would have been wrong for both.

## THE THIRD HEADLINE: two REJECTED verdicts, both on already-merged work

- **T183 REJECTED T179.** `--enforce` **exits 0** on a directory holding the three parameter-targeted
  rewriters — each an unguarded truncation of the ratified DEC-1, two also of the frozen
  `contract.go`. And **D-3: it punishes the exact shared-guard idiom T178 adopted and T187 extended
  across 25 files**, because a guard living in an *imported* module scores UNGUARDED. Repair: **T196**
  (T183's +25-line patch is written and tested but **deliberately unapplied** — a fix the reviewer
  merges is a fix nobody reviewed).
- **A2-14 REJECTED DEC-2 rev 1.** **On SHAPE, not on honesty** — every `[VERIFIED]` traced to real
  source at the exact cited line, G-9 applied, **G-10 recorded and left UNDECIDED (no gate crossed)**.
  Repair: **A2-16**. The ADR now carries a **DO-NOT-RATIFY banner**.

**Both rejections are recorded on the rejected task's own `tasks.json` entry.** A merged task marked
`done` that carries a rejected verdict must say so, or the next fire trusts it.

---

## THE NEXT FIRE STARTS HERE

1. **`A2-16` — DEC-2 revision 2.** The blocker is **R-1: no `ledger` vector is expressible against the
   frozen schema.** `Expect.Kind ∈ {schedule, refusal}`; `Expect.Sentinel` must be one of three
   *contract* sentinels, so §4.9's oracle-faithful **404 — this context's commonest graded output —
   has no representation**; `StructuralCellFields()` is a closed set and `admitCounterfactual` rejects
   all six cells §5 proposes. Either extend the schema (**real machinery**, and it must leave DEC-1's
   43 vectors passing) or grade what the schema already expresses. **A2-15 is BLOCKED behind it.**
2. **`T194` — P-35 inside the P-35 machinery.** `_run_capture_guard` tests the **presence** of a
   `^CENSUS` line and **never parses its numbers**; a stub printing `0/0/0` and exiting 0 yields
   **exit 0, VERDICT PASS**. Driver-confirmed by reading the function. The comment above the test even
   says *"must be present before its value is read"* — and the value is never read.
3. **`T196`** — apply T183's backstep patch; **adjudicate its 5 repo-wide reclassifications
   individually**, and **re-take the file count against post-T187 `main`** (T183 forked before T187
   merged and said so against itself).
4. **`T190`** — `fire-program.sh`'s one genuinely live fail-open: `DIRTY=$(git status --porcelain | …
   || true)` is **empty when git itself fails** (rc=128 measured) and the guard concludes "clean".
   T189 drove the fix red/green and **did not apply it** — it is this fire's running wrapper.
5. Then **`T192`** (14 fail-closed sites, before the corpus reaches ~135 vectors), **`T193`** (42 of
   43 parity vectors descend from `capture-prod3*` bodies **no guard inspects**), **`T195`**,
   `T165`, `T174`, `T176`, `T180`, `T160`, `T164`, `T162`, `T168`, `T145`, and reviewers `T181`,
   `T185`. `T116` stays parked behind T177's re-scoping.

---

## Four claims the driver made and had overturned — read before trusting this file

1. **"An empty `ledger/` cannot pass silently."** Repeated from A2-13 **as fact in a merge commit**.
   A2-14 disputed it; the driver **measured it** — empty `.softhouse/vectors/ledger/`, harness run
   unfiltered *as `conformance.sh` actually invokes it* — **exit 0, VERDICT PASS**, with "ledger"
   appearing once in the whole output, in the no-float census line. **False.**
2. **The three-dot diff instruction** (P-41) was given to five reviewers whose subjects were **already
   merged**, where it returns **empty** and reads as clean. → **P-59**, caught by T182.
3. **A2-14's worktree forked from a PARENT of the A2-13 merge**, so the document it was sent to review
   **did not exist in its tree** while its brief said "forked from current main". → **P-60**.
4. **P-55's worked example** was refuted by T189: the mechanism was never seekable-vs-pipe in BSD grep.

## STANDING INSTRUCTIONS

- **Count the PROGRAMS before you count the votes (P-58, NEW).** `grep` on this host is a **shell
  function** re-execing as **ugrep with `-I`**; `/usr/bin/grep` is BSD 2.6.0-FreeBSD. The four-way
  dispute was **one program measured twice** against another measured twice. **`-a` and `LC_ALL=C` are
  both load-bearing, against different programs.**
- **A post-merge reviewer sees an EMPTY three-dot diff (P-59, NEW).** Assert the diff is non-empty
  **before** reviewing; if the subject is merged, use `git show -m <merge>` or the merge-base form.
- **A worktree forks when CREATED, not when the prompt is written (P-60, NEW).** Never assert the fork
  point in a brief; tell the worker to establish it and to treat an absent artefact as a **STOP**.
- **Test the merge WHERE IT RUNS, not in a scratch tree (P-56).** It bit **three** workers' own provers
  this fire; each recorded it against itself.
- **Under `pipefail`, never `| grep -q` or `| head` (P-57)** — and **polarity is the diagnosis**:
  fail-open sites hide defects, fail-closed ones only cry wolf.
- **`git diff main...branch` — THREE DOTS while unmerged (P-41), and see P-59 after.**
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root.
- **Invoke the harness with `bash`, never `sh`.** Oracle-down is exit 2 **AND a probe line actually
  PRINTED AND reading `down`** — test **presence** first.
- **Never `gofmt -w` `contract.go`** (G-3). **Ship no guard you have not driven RED (P-22)**; a prover
  must be falsifiable toward the **FIX** too (P-50). **Quote by extraction (P-46).**
- **The shell's working directory persists between tool calls** — the driver ran a merge in the
  Fineract checkout this fire because a prior command had `cd`'d there.

## What is NOT true, and must not be inferred from the green bar

**Nothing grades the ledger's money.** A2-14 established it plainly: no vectors, **no schema to express
one in**, and **no guard for `I-3`/`I-4`** — `run_guards` invokes five guards, all about float, `gofmt`
and exception scope. DEC-2 §8's claim that the guards cover the ledger tree is **true for float** and
**will be misread** as covering the append-only and derived-balance invariants. The 43 passing vectors
are `loanschedule`'s. **`G-4`, `G-5`, `G-8`, `G-10` remain OPEN**; `G-4` and `G-5` are hard `user`
gates (each amends a ratified DEC-n). The gate register at the top of `gates.md` is authoritative.
