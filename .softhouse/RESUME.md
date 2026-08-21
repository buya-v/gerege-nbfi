# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-054355`, oracle REACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**.
- **Seven workers dispatched, seven completed, ZERO LIVE AT EXIT.** No isolation violation, no scope breach.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

---

# THE HEADLINE: `main` is at 43 parity vectors, and the 43rd arrived WITH its review

T149's vector — the first in the store ever observed through the **running Fineract server**, where all 42
others come from the in-process Path A seam — was held unmerged last fire because the driver had dispatched
it **without a paired reviewer**. **T153 is that review: MICRO-FIX → APPROVED, no defect in any money path.**
The violation is closed, and holding it was right: T153 found two real overclaims.

**Driver re-ran everything on merged `main` after applying the micro-fix — nothing here is on a worker's report:**

```
probe line PRESENT, line 1: conformance: reference oracle (https://localhost:8443/...) probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells graded
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
go1.26.6 (repo-local, `. .softhouse/bin/go-env.sh`): build 0 · vet 0 · test ./... ok
gofmt -l names exactly contract.go — EXPECTED under G-3
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Merged this fire**: `A2-6`, `T149`, `T153`, `A2-5`, `A2-10`, `A2-7`.
**Held unmerged**: `T154` — see below.

## THE NEXT FIRE STARTS HERE

1. **T155 — review T154, then merge it. NEEDS THE ORACLE.** T154 (the consolidated no-float guards) is
   **deliberately unmerged**: it is money-path guard code and its paired reviewer has not run. This is
   exactly the T149 call, and the T149 precedent was **vindicated this fire**. Its branch verified green
   (build/vet/test 0, conformance exit 0, and a post-merge scratch at 43/5664), but a green branch is not a
   review. **Tell T155 that T154 self-corrected three inherited claims and found a P-24 bug in its own rig —
   it should hunt for any hard-coded expectation left in its provers, since main's parity count keeps moving.**
2. **A2-8 — THE A2 CODER. IT IS READY.** Its dependency on A2-7 was removed (the driver's false premise).
   Its brief has been re-derived and amended; read it in full, and read `A2-7.md` and G-10 first.
3. **A2-11** — review of A2-7. It should attack the refutation that overturned the driver, not just the new
   captures: that refutation is now written into `gates.md` and `program.json` **as fact**.
4. **A2-9** after A2-8. **T156** (unguarded `mv` leaves a green `PASS 42`). **T157** (last unhardened grep).
5. Carried money work still open: **T116**, **T117**, **T145** — all collide on `.softhouse/capture/`;
   serialise them.

## G-9 CLOSED — and the driver's own consequence was FALSE

**Decision (stands, `chosen_by: agent`, reversible):** the chart of accounts is **DATA, not code**; launch
with the minimal chart the vectors exercise; an FRC-aligned chart is a separate data-only deliverable
downstream of CUTOVER. Premise re-derived correctly: **0 of 1,918 seed `<insert>` elements** target
`acc_gl_account`; it appears only as `createTable` + two `createIndex`. Fineract ships the table and no rows.

**What was wrong, and it was the driver's:** it claimed the corpus held "four accounts, all ASSET" and
"2 of the 9" mandatory. **False three ways.** `main` already held a **21-row dump across all five
classifications** and **product 22 with all nine slots mapped**. A2-7 refuted it *before acting* and created
zero accounts. Cause: an enumerator with `json.load` inside `except Exception: continue`, swallowing the
psql `.txt` dumps where the state actually lives, reporting the subset as the whole. **Recorded as P-40.**

## What A2-7 established instead — these are design inputs to A2-8

- **Zero `GET /loanproducts/{id}` existed in the entire corpus** (eleven POSTs, no reads). The mapping A2-8
  must port had **never been observed at the contract boundary**. Write and read field names differ for
  **every** slot (`fundSourceAccountId` → `fundSourceAccount`); the read returns `{id, name, glCode}` and
  **no type/usage**; unmapped optional slots are **absent, not null**.
- **Runtime and creation mandatory sets DIFFER — measured.** A product with all nine `notNull()` slots still
  404s on charge-off and goodwill, both `ignoreIfNull()` at creation. **Fineract will create a product that
  cannot complete every posting path.**
- **G-10 (OPEN)**: the oracle holds five mappings whose GL account was retyped ASSET→INCOME underneath them,
  serves them without complaint, and **refuses to re-create them** (403) — and the read-back structurally
  cannot reveal it. Driver recommends **(c)**: take vectors only from products the oracle would still accept.

## Reviewer catches this fire — four for four

- **T153 → T149**: measured the missing control rather than arguing it; both conclusions survived, the
  wording fell. Re-observed the tie live, byte-for-byte identical, with a *cleaner* counterfactual than T149.
- **A2-10 → A2-5**: found a **P-22 regression the fix task itself introduced** (symlinked fabrication
  invisible to `verify`; the pre-fix code caught it). **Third instance** of a P-22 fix opening another.
  Adjudicated A2-5's three deviations by **building the prescribed fix and running it** — all three A2-5's way.
- **A2-7 → the driver**: refuted the central premise and acted on its own measurement.
- Driver applied both micro-fixes and **drove A2-10's fix RED itself** in a sandbox before believing it.

## Driver self-catches (P-20 — the count keeps rising, and that is the system working)

- **A2-5 was dispatched with no paired reviewer** — the same rule-1 violation as T149. Caught mid-flight by
  running the plan gate over the driver's *own* additions (**P-44**). A2-10 then found a real regression.
- **The A2-10 brief's "22-line hunk"** was a `--stat` misreading; 11 identical `|| exit 1` lines.
- **T153's `files_hint` was too narrow** for the task the driver commissioned. Not charged to the worker.
- **The driver re-derived A2-8's own brief before dispatch** (**P-42**) and found a hazard nobody had
  recorded: across `CashAccountsForLoan`/`AccrualAccountsForLoan` the name↔code relation is **not a function
  in either direction** (`FEES_RECEIVABLE` = 25 cash, 8 accrual), so keying on the code cross-maps *and*
  keying on the name cross-maps. Trap 4 deliberately **not** checked and marked unconfirmed.

## STANDING INSTRUCTIONS

- **`git diff main...branch` — THREE DOTS, always (P-41).** `main` moves during a fire and the two-dot form
  renders main's own advances as the branch's deletions. **`/softhouse` SKILL.md STEP 5 says two dots and is
  wrong.**
- **Invoke the harness with `bash`, never `sh`.** Exit 3 is the interpreter guard's **refusal**, not an
  oracle outage. Only exit **2** with a probe line **actually printed** and reading `down` is the oracle-down
  condition — **test for the line's presence first**; a failed HARD guard exits 2 in silence.
- **The Go toolchain is repo-local and NOT on PATH**: `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`.
  A bare `go build` reports "command not found", and `go build ./... | head` will report **`head`'s** exit
  code as if it were the compiler's. Do not read that as a pass.
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **Ship no guard you have not driven RED** (P-22). A2-5 set the shape to copy: provers read the real
  pre-fix bytes from **immutable git blobs** and refuse on sha mismatch, so they cannot drift into testing
  the fixed code. **A test-only guard is not a guard (P-45)** — `conformance.sh` never runs `go test`.
- **An enumerator must count what it skipped and say so (P-40).** `except: continue` over a directory you
  are measuring is the same defect as a guard that cannot fail.
- **Verify post-merge assertions on a scratch merge** (P-24), against the **real pre-fix bytes**.
- **An obligation is not a proof.** Where `obligations.md` says *Ungraded*, nothing catches the thing.

## Open gates — none blocks work today

- **G-4**, **G-5** (OPEN, ENGINEERING) — wording-only amendments to a **ratified** DEC-1; the skill's
  never-cross list names *any change to a ratified DEC-n*. Both corrected readings are already operationally
  in force. **Buyan decides.**
- **G-8** (OPEN) — options (b) and (c) amend the graded domain: hard `user` gates.
- **G-10** (OPEN, ENGINEERING, raised this fire) — driver recommends (c), which is free and reversible.
  (b) narrows the graded domain and is a hard `user` gate.
- **N9 / N10** (OPEN) — only FU-1 (obligation T139) closes them.
- **G-9** — **CLOSED this fire**, decision intact, its false consequence corrected in writing.
- **CUTOVER** — untouched, every context. Needs vectors passing **and** a clean shadow-parity window **and**
  regulatory/parallel-run sign-off. The latter two do not exist.
