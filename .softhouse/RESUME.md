# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-080001`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **ELEVEN DISPATCHED, ELEVEN COMPLETED, ELEVEN MERGED, ZERO LIVE AT EXIT.** No isolation violation;
  every branch's scope checked by the driver on the **three-dot** diff before merge.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only, **asserted not assumed** —
  see the fire-log row in `.softhouse/reference-oracle.md`.

**Driver-verified on merged `main` at exit** (re-run by the driver, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells compared
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
--prove              23 passed, 0 failed
ledger-invariants    exit 0   (NEW THIS FIRE — see below)
go build 0 · go vet 0 · go test ok (ledger, loanschedule, conformance)
gofmt -l             exactly contract.go   (expected, G-3)
contract.go          0db73d4a…e37f139  == PIN
vector store         ce821c638724237652b6b29627148d34b72fab3b  (git tree hash), 50 files
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire, all eleven**: `T201`, `A2-19`, `T203`, `T181`, `T185`, `A2-18`, `T202` (batch 1);
`T204`, `A2-20`, `T208`, `T206`, `T205` (batch 2).

---

# HEADLINE 1: the number this whole program quotes was inflatable by a file copy

`A2-19` measured it. **The driver reproduced it independently, with its own probe vector, before writing
the repair task.** Copy any loanschedule parity vector into `.softhouse/vectors/ledger/`, change **only**
`case_id` and `context`:

```
DRIVER-F1-PROBE   parity   path_a_e...   PASS   47 cells
VERDICT: PASS (exit 0) — 44 parity vectors match the pinned reference oracle, 5711 cells compared.
```

A2-19's figures and the driver's agree exactly: **44 / 5711**. Cause: `context` was constrained only to be
non-empty and to equal its own directory name (`admit.go:115`, `:119-120`). **No allowlist existed.** Worse
than inflation — the fake sat in `ledger/` while grading a *loanschedule* schedule, so it read as **GL
coverage that does not exist**.

`A2-20` closed it, and **found a second live form neither A2-19 nor the driver had probed**: the
**contract-refusal** shape (4→5, 5664→5665). Both now `INADMISSIBLE`, exit 2, driver-verified, and the
refusal message names the 44/5711 history so the next reader learns why the rule exists.

**Residual, measured and deliberately not fixed** → `A2-23`: an **empty** unknown-context directory is
still silently ignored. A2-20's argument is sound — a directory with no vector makes no claim — but it is a
store-*shape* question, and it belongs in `StoreFileCensus`, not `Admit`.

## HEADLINE 2: I-3 and I-4 went from ZERO enforcement to harness-enforced

This morning `run_guards` invoked **five** guards, all about float, `gofmt` and exception scope, and
**nothing anywhere looked for a balance write path or an `UPDATE`/`DELETE` against the journal** — while
*"balances are derived, never written"* and *"the ledger is append-only"* are first-tier `CLAUDE.md`
non-negotiables.

`A2-18` built the guard (AST, not regex — a regex fires inside the guard's own doc comment) and
**deliberately did not wire it in**, stating against itself that its byte-identical transcript was *"the
proof that I-3/I-4 remain ungraded at grade time."* `T208` wired it. `run_guards` now invokes **six**.

**Driver-verified independently:** a planted `UPDATE acc_gl_journal_entry` in a throwaway worktree turns
**the harness** red — exit 2, `[I4-DML]` naming file and column, and **zero probe lines printed**. That
last part is load-bearing: this is the **sixth pre-probe exit-2 path**, so a balance write cannot be parked
as an oracle outage.

**Do not overstate it.** I-3/I-4 are now **checked in source**. That is not **graded against the oracle**.
There is still no `ledger` vector and no schema to express one in.

## HEADLINE 3: the vector-store exposure was three times the brief's estimate

| | brief said | truth |
|---|---|---|
| truncating rewriters | 4 | **7** (T203 found 6, T206 found the 7th) |
| live parity vectors at risk | 13 | **26**, including `P-00`, the corpus baseline |

`T206` also found the 7th's live target **had been hand-edited since promotion**, so a re-run would
silently **regress content**, not merely truncate. `T205` narrowed the root cause — not "runtime constants
don't resolve" as T203 stated, but **`partial` not chaining** *and* **`setdefault` blocking the upgrade**.

All seven refuse, **create-only** — driver-verified: no token, flag or environment variable can authorise
overwriting an existing vector.

---

## THE NEXT FIRE STARTS HERE

1. **`A2-21` — DEC-2 revision 3.** Retract the three false *"no `ledger` vector CAN exist"* assertions
   (banner fact 2, §8.1 fact 2, A2-17's §4.10 text); §5.1's own heading has the true, weaker claim —
   not **expressible**. Give §5.2 a spec that is more than non-regression (today it is satisfiable by an
   extension that does nothing). Apply A2-19's split ruling: **P-6 before P-1…P-5; P-7 NOT** — P-7's
   premise is contradicted by §1.1. Fix §2.2's "three columns" (it is two).
2. **`A2-22`** — `CounterfactualCoverage` counts kills from **REFUSED** vectors. Establish the live blast
   radius first (baseline shows `refused 0`, so likely nil today) and **say it**, then fix.
3. **`T209`** — the ledger guard's `CANNOT-CATCH` block **reaches no green run**; its own head filters it
   out while its PASS text tells you to read it. Fix at source, not by growing T208's condensation.
4. **`T210`** — T172's anchor regression is **frozen**: it replays bytes T190 deleted, so it can no longer
   notice a live regression. **`T211`** — SIGTERM cannot promptly stop a fire (zsh defers the trap behind
   the hours-long `claude` child), so **the SIGKILL strand is the normal outcome, not the exotic one**.
5. Then `T193`, `T192`, `T212`, `A2-23`, `T207`, `T145`, `T160`, `T164`, `T174`, `T176`, `T180`, `T195`,
   `T162`, `T168`.

**20 tasks READY. 1 blocked (`T116`, on `T114` — which has NO ENTRY in `tasks.json` and can never resolve;
re-scope or re-point it).**

**`A2-15` is NOT ready and the driver re-pointed its dependency this fire** — it computed as READY off the
done `A2-16`, but A2-16 produced **DEC-2 rev 2, which A2-19 rejected**. It now depends on `A2-21`. Of
DEC-2 §5.3's eight preconditions **only P-8 exists**; there is still no ledger schema, no refusal
expectation shape, no comparator.

---

## Corrections made against the DRIVER this fire — read before trusting its numbers

1. **P-61 — the driver circulated a broken digest.** It put the vector-store digest `5d03795b…` in five
   briefs with the recipe in only one. `T185` and `A2-18` both reported it unreproducible; the driver had
   reproduced it three times and could have dismissed them. **They were right.** The recipe hashes
   `shasum`'s *output lines*, which contain the **file paths**, so the same 50 byte-identical files give
   `5d03795b…` from a relative `find` and `ec72cc0b…` from an absolute one. Every worker ran at a different
   path. **Both had already reported the correct canonical answer — the git tree hash `ce821c63…` — inside
   the report telling the driver its number was broken.** In force: `git rev-parse HEAD:.softhouse/vectors`.
2. **P-62 — the driver's first verification of A2-20 was a NULL CONTROL.** A prior command left the shell
   in `nexus/`, the store copy silently failed, and the run graded **zero vectors** and exited 2 — which is
   exactly what a correct refusal looks like. Caught only by reading the counts, not the exit code.

## Corrections made against already-merged work

- **`T181` on `T178`:** the published split **21/4 is wrong**; truth **20 / 7 / 2 of 25**. The **total was
  always right, so no file went unhardened** — a *reporting* defect. `T204` corrected it by annotation;
  the driver corrected the two carriers in its own files (`tasks.json`, `program.json`).
- **`T208` on `A2-18`:** `CANNOT-CATCH` never reached a green run — and did not standalone either, so
  wiring dropped nothing; the head already did.
- **`T205` on `T203`:** the stated mechanism was true but incomplete.
- **`T185` on `T145`'s premise:** T134's *"74 of 240"* denominator **no longer exists**. Truth on `main`:
  **389 `.py` files, 323 call sites, 211 lacking `parse_float`, in 114 files. T145 starts from 211/114.**

## STANDING INSTRUCTIONS

- **The canonical vector-store digest is `git rev-parse HEAD:.softhouse/vectors` (P-61).** Never
  `find | shasum | shasum` — a tree hash carries no cwd. Publish any digest **with its recipe** (P-38).
- **Verify a refusal by what it SAYS and what population SURVIVES, never by exit code (P-62)** — an empty
  input refuses with the same code. `exit 2` is deliberately overloaded: unusable corpus, failed hard
  guard, unreachable oracle, wrong repo root, and **now an I-3/I-4 violation**.
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The shell's working directory persists between tool calls.** It has now bitten this program twice.
- **A post-merge reviewer sees an EMPTY three-dot diff (P-59)** — assert non-empty first, then use
  `git show -m <merge>` or the merge-base form. It fired on **three** reviewers this fire; all three
  handled it.
- **Count the PROGRAMS before the votes (P-58).** `grep` here is a shell function re-execing as **ugrep
  with `-I`**; `/usr/bin/grep` is BSD 2.6.0-FreeBSD. `-a` and `LC_ALL=C` are load-bearing against
  *different* programs.
- **Never execute a promote or rewriter script from the repo root** — and a `/tmp` copy **cannot run**,
  because they derive `ROOT` from `__file__`. A naive scratch test is a **null control** (P-36).
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root. Invoke the harness
  with **`bash`**, never `sh` (exit 3 = wrong-interpreter refusal). **Never `gofmt -w` `contract.go`** (G-3).
- **Do not modify `.softhouse/bin/fire-program.sh` while a fire runs.** Merging is safe: git **renames**
  (driver-verified, inode `7913849` → `8134531`), which T200 measured as not hijacking a running zsh script.

## What is NOT true, and must not be inferred from the green bar

**Nothing grades the ledger's money.** The 43 passing vectors are `loanschedule`'s; **zero** touch a GL
account, a mapping, a financial activity or a journal entry. I-3/I-4 are now **checked in source** — that
is not **graded against the oracle**. `G-4`, `G-5`, `G-8`, `G-10` remain OPEN, and **`G-11` is new: DEC-2
rev 2 is REJECTED and must not be ratified.** G-11 is *not* a `user` gate — ratification is agent-decidable
— but the clean-review condition is unmet, so no fire may ratify on that clause alone. **Nothing was cut
over, and nothing here authorises it.** The gate register at the top of `gates.md` is authoritative.
