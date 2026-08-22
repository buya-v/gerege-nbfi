# T243 — three unwired guards, one file, one root cause

**Branch** `softhouse/T243-wire-the-guards` · **head** `6875cd7` (rebased) · earlier sha `f881a0c` is the
same work before the rebase and is **not on any branch now**; quote `6875cd7`.

**What this task did:** wired the six wrong ledger implementations, T238's fail-open linter and a
citation check that could not fail into `.softhouse/conformance.sh`'s **automatic path**, and drove all
three **RED through that path**. Nothing was cut over and nothing here authorises it.

---

## 0. FORK POINT — MEASURED, AND IT FALSIFIES BOTH STATED RULES FOR A THIRD CONSECUTIVE FIRE

`P-71`'s title now says *"a worker's fork point is UNPREDICTABLE: MEASURE IT, NEVER ASSERT IT"*, and the
task asked me to say plainly whether my measurement discriminates. **It does, decisively, and it lands
on a THIRD value neither rule names.**

```
git merge-base HEAD origin/main   (at task start)  693c768d752df7a475938df3e4fa3cd72b138e18
git rev-parse origin/main         (at task start)  693c768d752df7a475938df3e4fa3cd72b138e18
git rev-parse HEAD                (at task start)  693c768d752df7a475938df3e4fa3cd72b138e18
git reflog softhouse/T243-wire-the-guards@{3}      693c768 "branch: Created from origin/main"
```

| candidate | commit | matches my fork point? |
|---|---|---|
| **session-start commit** (the harness `gitStatus` snapshot handed to me) | `477dc2d` | **NO** — 26 commits behind |
| **dispatch commit** (`f13bf4a`, *"wave 2 dispatched (T243, T246)"*) | `f13bf4a` | **NO** — `f13bf4a^` **is** my fork point, so I forked one commit BEFORE dispatch |
| `origin/main` at the moment the worktree was created | `693c768` | **YES**, and the reflog says so in words |

So the scoreboard is now: `T225`'s fire → session-start; `20260822-140002` → dispatch; the
`20260822-060013` fire → session-start; **this fire → NEITHER**. The reflog line
`branch: Created from origin/main` is the only thing that has been true every time, and it is a
measurement, not a rule. **Keep telling workers to measure; stop offering them a candidate.**

**`main` MOVED AGAIN DURING THE TASK**, exactly as `RESUME.md` warns: `693c768` → `8e8d65d`
(DEC-2 rev 6 ratified and landed, G-13 closed, G-14 raised). I rebased onto `8e8d65d`, re-ran the whole
BAR on the rebased tree, and §6 is that run. **The sha I am reporting is the one I rebased ONTO, not
the one I looked at first.**

---

## 1. WHAT WAS WIRED, AND HOW

### 1.1 `gate_wrong_ledger_impls_die` — A2-34's F-7, the FOURTH P-45 instance

**The state I re-derived** (`transcripts/10-wrongimpl-red-drive.txt`, BASELINE stanza):

```
exit=2 for: bash .softhouse/conformance.sh --ledger-impl ledger-wrong-truncating
conformance: unknown option --ledger-impl
occurrences of the string 'go test' in .softhouse/conformance.sh : 4      <- all in COMMENTS
```

`-ledger-impl` is a flag on the **binary**; the script never passed it and never ran `go test`, so
`TestEveryWrongImplementationIsKilled` was equally unreachable from here. **A green harness run executed
none of the six.**

**Where it is now called:** `main_grade`, immediately after `gate_exemption_census`, i.e. *after* the
graded run and *before* the return. Two reasons, and the second is load-bearing:

1. the graded run above it is the gate's **anti-no-op control** — it is the CORRECT implementation
   going green over the same corpus, so "these six always go red" and "everything goes red" are
   distinguished by the verdict the same run is about to return;
2. the probe it measured is the one passed in, so **no arm asserts a reachability this run did not
   observe**.

**What it asserts, and why each part exists:**

| assertion | why it is not decoration |
|---|---|
| the population is **DISCOVERED** from the binary's own `-list-implementations` | a seventh wrong implementation is executed the day it is registered; a hard-coded list is a list somebody forgets |
| the count is **PINNED at 6**, both directions | a wrong implementation that is *deleted* silently withdraws a kill that vectors still cite; a *seventh* dies like the others, so **only the count can see it** |
| exit must be **1 exactly**, not "non-zero" | `2` is this harness's unusable code — an implementation that made the run refuse for an unrelated reason would satisfy "non-zero" while killing nothing (P-62) |
| the kill must land in the **LEDGER half**: `ledger parity FAIL + ledger oracle-refusal FAIL >= 1` | otherwise a wrong LEDGER implementation could be "killed" by an unrelated loanschedule failure. **The six are NOT alike here** — `ledger-wrong-manual-permission-ignored` passes all four parity vectors and dies on an **oracle-refusal** vector alone, which is exactly why the SUM is asserted and not the parity count |
| the report's `THIS IS A DELIBERATELY WRONG IMPLEMENTATION` banner must be present | it is what proves the flag was honoured rather than ignored — the failure mode that would make every arm pass against the CORRECT implementation |

**Cost:** six extra in-process gradings of the committed store, ~1.3 s each, **no extra contact with the
reference oracle** beyond the probe the run already made. **NOT RUN** in self-test mode (the ledger half
does not run there) and **NOT RUN** when `probe != up` (the run is already refusing; a gate that
manufactured a second verdict out of that would be reading its own refusal as evidence). **Both skips
say so in the output.**

### 1.2 `guard_no_fail_open_instruments` — T238's linter, which would have been the FIFTH P-45

T238 shipped it **unwired**, said so loudly, and handed over the exact call line in its §8:

```
python3 .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py || return 1
```

**THAT LINE, APPLIED LITERALLY, DOES NOT WORK, AND I MEASURED WHY BEFORE CHANGING ANYTHING.** At the
fork point the linter **exits 1 on the tree it shipped into**: nine instruments are on its frontier,
two Tier-1 and seven Tier-2, spread across four other tasks' **frozen evidence** directories. One of
them must never be repaired at all — `evidence/red-drive/sweep-ORIGINAL.sh` is T238's **preserved
specimen of the defect**, pinned by a literal `sha256` that T238's own red drive asserts (P-24).

Two ways out existed and only one is honest:

* **(a)** narrow the linter's scope until it goes green — that is **weakening a gate to make wiring
  easy**, and the task forbids it;
* **(b)** run the linter over the **whole tree on every run** and gate its **FRONTIER for equality**
  against a pin held in `conformance.sh`, by **path**, in both directions.

**(b) is what shipped.** Nothing admissible became inadmissible, nothing inadmissible became
admissible, and a **tenth** instrument — or a swap that keeps the total at nine — refuses. It is the
same idiom as `EXEMPTION_PIN_*` twenty lines above it.

**THE PIN WAS ALREADY EVIDENCE BEFORE IT WAS SWITCHED ON.** T238's committed
`evidence/lint.json` records **three** Tier-2 instruments. There are **seven**. Five arrived with
**T239** in the same fire, after T238's measurement and before this wiring, **and nothing noticed** —
which is precisely the drift this gate exists to stop, observed once already.

**Fail-closed three ways**, because a guard about instruments that emit a negative they did not measure
must not be one:

* the linter's **banner** must appear in the captured output — a failed `cd`, an absent python, a
  deleted linter all yield an empty frontier, and an empty frontier would otherwise read as "no
  fail-open instruments";
* the linter's **corpus line** must report a non-zero tracked-file count (P-35);
* the exit code must be **0 or 1**; `2` is the linter's own corpus refusal and anything else is a crash.

**No pipeline anywhere in it** (P-57): the linter's output goes to a file and every read is a
`sed`/`grep` over that file; the pin and the measurement are each sorted **file-to-file**, never through
a pipe, and compared with `diff -u`.

**Where it is called:** last in `run_guards`' tally, so it refuses **before** the oracle is probed and
before any verdict is computed. Confirmed in the red drive: on the refused run **no verdict line is
printed at all**.

### 1.3 The F-3 decision — see §2, and it is a decision, not a report

---

## 2. F-3 — THE ARGUED DECISION, AND WHY IT IS NOT A RETIREMENT

### 2.1 What I measured, independently of the Go code

`instruments/31-citation-census.py` re-implements T233's three branches from the **prose**, not by
calling `admit.go`'s classifier — a census that called the thing under test would agree with it by
construction, which is the shape this whole task exists to remove. It **calibrates both ways** before
printing anything (known positive must resolve in bytes; a case id that exists nowhere must resolve
`UNRESOLVED`), and aborts `2` if either fails.

```
LDG-01 capture_ref          FILE-NAME-ONLY   sha OK
LDG-01 request_capture_ref  HTTP-SIDECAR     sha OK
LDG-02 capture_ref          FILE-NAME-ONLY   sha OK
LDG-02 request_capture_ref  HTTP-SIDECAR     sha OK
LDG-03 capture_ref          FILE-NAME-ONLY   sha OK
LDG-03 request_capture_ref  HTTP-SIDECAR     sha OK
LDG-04 capture_ref          ARTEFACT-BYTES   sha OK
LDG-04 request_capture_ref  HTTP-SIDECAR     sha OK
LDG-REFUSE-01 / -02 (both fields, all four)  HTTP-SIDECAR  sha OK
---
12 citations over 6 vectors: ARTEFACT-BYTES 1, FILE-NAME-ONLY 3, HTTP-SIDECAR 8
```

**A2-34's finding HOLDS, with one refinement worth having.** A2-34 wrote that the id *"occurs in the
artefact's bytes because it is the artefact's own filename"*. It is the **third** branch (file name),
not the first (bytes): the id is **not in those response bytes at all**. Same conclusion, more precise
mechanism, and the precision matters because the two branches are fixed differently.

### 2.2 The decision

> **Part two is KEPT, not retired. Its weakest branch is classified, counted, printed on every run, and
> PINNED by `(case_id, field)` identity — inflation is INADMISSIBLE, deflation is FATAL.**

### 2.3 The argument, and the evidence for it

**(a) "The sha256 makes part two redundant" is FALSE, and I measured it false rather than asserting it.**
The digest answers *"are these the bytes this vector transcribed?"*. It cannot answer *"is this artefact
the capture case the vector NAMES?"* — because a citation pointing at a **different** artefact and
recording **that** artefact's **correct** digest satisfies the digest check completely. **Only part two
notices.** `RED B` in `transcripts/30-citation-red-drive.txt` is exactly that case, driven through
`bash .softhouse/conformance.sh`: the run refuses with *"occurs neither in the bytes of … does not
answer to the case id it claims"*, and the assertion `has changed since the vector` is proven
**ABSENT**, so the digest check is demonstrably silent while part two does the work. If that arm ever
goes green, this decision is wrong and should be reversed to a retirement — the red drive says so in
its own header.

**(b) But the file-name branch is not a check on the ARTEFACT.** It reads **zero bytes** of it. It asks
whether the `ref` string contains the `capture_case_id` string — **two fields of the same vector,
written by the same author in the same edit** — and in this store every ref is spelled
`<capture dir>/out/<case-id><ext>`, so it **cannot fail** for any citation written the ordinary way.
That is the tautology A2-34 named. Leaving it as an unmarked third alternative lets a name-only
citation arrive silently and be read as though it had resolved against bytes.

**(c) Why not simply refuse all three.** Because that would make **three of the four ledger PARITY
vectors inadmissible** over a gap in the **capture rig**, not a defect in the vectors: the rig writes
the case id into the `.http` sidecar for a **request** and not for a **readback response**. The repair
belongs in the rig at the next capture, and the vector store is not mine to change. Until then the
frontier is **three**, named in source with its reason, and it cannot grow without a source edit a
reviewer reads.

**(d) A limit of my own classification, stated rather than left to be assumed (P-66).** I count
`HTTP-SIDECAR` as stronger than name-only because it reads a **second file the rig wrote**. It is **not
uniformly strong**: on the six `.req` citations the id occurs in the sidecar only inside a
`body-wire-bytes-artefact: <case-id>.req` line — itself a file name, one file over. That is still a
second artefact attesting the link rather than a vector agreeing with itself, which is the line I drew,
but it is weaker than `ARTEFACT-BYTES`, and it is written down in `admit.go` where the next reader
stands rather than only here.

### 2.4 What the harness now prints, every run

```
    ledger citations        12 PART-TWO resolutions over the loaded corpus: 1 ARTEFACT-BYTES,
                            8 HTTP-SIDECAR, 3 FILE-NAME-ONLY (pinned 3), 0 UNRESOLVED.
                            FILE-NAME-ONLY reads NO byte of the artefact: it checks that the ref
                            this vector wrote contains the case id this vector wrote. It is not
                            evidence about the artefact, it is pinned by (case_id, field) in
                            ledger/conformance/admit.go, and a fourth is INADMISSIBLE.
                            FILE-NAME-ONLY: LDG-01-… provenance.capture_ref -> …/A2-347-je-manual-readback.json
                            FILE-NAME-ONLY: LDG-02-… provenance.capture_ref -> …/A2-338-je-after-repayment-coverage.json
                            FILE-NAME-ONLY: LDG-03-… provenance.capture_ref -> …/A2-383-je-after-overpay.json
```

**Deliberately NOT a tenth census pin in `conformance.sh`.** The equality is gated **inside the ledger
package**, by identity, in both directions, so the nine existing census pins are untouched and still
read `4/4/4/0/0` and `0/4/2/21`.

---

## 3. DRIVEN RED THROUGH THE WIRED ROUTE (P-22 / P-45)

Every arm below is `bash .softhouse/conformance.sh` — the route that runs it — never the binary and
never `go test`. Transcripts committed under `.softhouse/capture/t243-wiring/transcripts/`.

### 3.1 `10-wrongimpl-red-drive.txt` — **26 passed, 0 failed**

| arm | perturbation | result |
|---|---|---|
| CONTROL 0 | none | exit 0, all six `KILLED`, `SURVIVED` **absent** |
| **RED 1** | `truncatingPoster` made to return the CORRECT port's answer. Registration, name, declared defect and every vector untouched — **the only thing that changed is whether the corpus can still tell it apart** | `SURVIVED ledger-wrong-truncating`, `A DELIBERATELY WRONG LEDGER IMPLEMENTATION SURVIVED THE CORPUS.`, **exit 2** |
| **RED 2** | a **seventh** registration, which dies like the other six, so every per-implementation arm stays green | `WRONG-IMPLEMENTATION POPULATION 7, PINNED 6.`, **exit 2** — only the count could see it |
| **RED 3** | one registration **withdrawn** | **exit 2**, and it is caught **upstream** by `admit.go`'s *"names implementation … which is NOT REGISTERED"* refusal rather than by my pin. Recorded rather than assumed |
| GREEN | restored | exit 0, `all 6 … DIED through this harness, not by hand.` |

### 3.2 `20-failopen-red-drive.txt` — **13 passed, 0 failed**

**The plant is RUN and MEASURED before it is put in front of the harness**, so what the harness refuses
is a demonstrated fail-open and not a lint opinion:

```
  the planted sweep, run on its own: exit=0
  '(no hits)' lines it printed: 2
  hit lines it printed        : 4        <- all four are its own echoed pattern headers
  OK [plant] exit 0 while reaching NO corpus — the fail-OPEN shape, measured, not asserted
```

then, tracked:

```
conformance: THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER (- pinned, + measured):
+TIER1 .softhouse/capture/t243-wiring/evidence/planted-failopen-sweep.sh
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
  OK [RED] no verdict line at all on the refused run
```

and removed → `frontier == pinned (all 9 rows, by path).` · `VERDICT: PASS (exit 0)`.

**The plant is ASSEMBLED, not pasted, and that is not style.** If the two lethal lines appeared
literally in the committed instrument, the linter would classify **the red drive itself** as Tier 1 the
moment it was committed — it does not care that they sit inside a heredoc — the frontier pin would move
because the red drive exists, and the red drive would be measuring itself. The dead path and the `||`
are composed from variables and are literal only in the generated file. Verified: with all four T243
instruments tracked, the frontier is still exactly **9**.

### 3.3 `30-citation-red-drive.txt` — **23 passed, 0 failed**

| arm | what it does | result |
|---|---|---|
| CONTROL 0 | pristine | census line present, `3 FILE-NAME-ONLY (pinned 3)`, exit 0 |
| **RED A** — inflation | repoint `LDG-REFUSE-01`'s `capture_ref` at a readback artefact whose sidecar does **not** carry the id, moving the id and the **correct** sha256 with it | `resolves PART TWO of its citation BY FILE NAME ONLY`, `reads ZERO bytes of the` artefact, **exit 2**; `has changed since the vector` proven **absent** |
| **RED B** — the argument | `LDG-REFUSE-02`'s `capture_ref` → a **different** capture's artefact with **that** artefact's correct sha256 | `occurs neither in the bytes of`, `does not answer to the` case id, **exit 2**; digest check silent |
| **RED C** — deflation | a **fourth** pin row for a citation that resolves `ARTEFACT-BYTES` | `citationNameOnlyPin carries …`, `resolved ARTEFACT-BYTES on this run`, `A pin nothing needs is a sentence nothing checks`, **exit 2** |
| GREEN | restored | exit 0 |

```
  vector digest at start : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
  vector digest at end   : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
  OK [digest] the vector store is byte-identical to where it started
```

Three package tests carry the same three properties so they also fail a `go test` run:
`TestPartTwoOfTheCitationCanFail/{an_unpinned_file_name_only_citation_is_refused,
a_stale_pin_is_reported, a_mis_cited_artefact_with_a_correct_digest_is_caught_only_by_part_two}`.

---

## 4. TWO DEFECTS FOUND IN MY OWN WORK, REPORTED RATHER THAN SMOOTHED

**4.1 `git checkout -- <file>` IS NOT A RESTORE.** My first run of red drive 3 used
`git checkout -- "$V" "$ADMIT"` to revert each perturbation — the idiom A2-34's red drive uses. Because
my change to `admit.go` was **uncommitted at that point**, the first `restore()` silently reverted it to
`HEAD`, and every later arm ran against a tree that **did not compile** and "failed" for a reason that
had nothing to do with what it was testing. Both red drives now restore from a **byte copy taken before
any mutation**, under a `trap` (P-54), and both print a `cmp`/`diff -r` result at the end. **A restore
whose behaviour depends on what has been committed is not a restore**, and it fails in the direction
that destroys work.

**4.2 A POST-REPORT GATE LEAVES A STALE `VERDICT: PASS` LINE IN THE OUTPUT.** My first red-drive
assertion demanded that `VERDICT: PASS (exit 0)` be **absent** from a refused run. It is not absent: it
is the **binary's** verdict over the vector corpus, printed before the shell gate runs. **This is
pre-existing** — `gate_exemption_census` has had exactly this shape since T233 — and I did not weaken
the assertion to accommodate it. Instead the new gate now prints, on every refusal:

```
conformance: THE REPORT ABOVE MAY CARRY THE BINARY'S OWN 'VERDICT: PASS (exit 0)' LINE. IT IS
conformance: WITHDRAWN BY THIS GATE. … The verdict of the RUN is this one, and it is EXIT 2.
```

and the red drive asserts **the retraction**. The same hazard still applies to
`gate_exemption_census`'s refusal path, which I did not touch — see §7.

---

## 5. WHAT I JUDGED UNSAFE TO FORCE, AND WHAT I PROPOSE INSTEAD

The task warned that `conformance.sh` is a `pipefail` script with known early-exiting-consumer hazards
and that **restructuring a pipeline to wire this in is forbidden**. **I restructured nothing.** Both
additions are new functions plus one call each; no existing pipeline, guard, census expression or exit
path was altered. The only edits to existing lines are the two `warn` blocks in §4.2 and the
`guard_ledger_invariants || failed=1` line gaining a sibling.

**One thing I did NOT force, and it is the honest half of §1.2.** T238's literal call line
(`… || return 1`) cannot be used, because it makes the harness permanently red over nine files I may
not edit and one that must never be repaired. **What I propose, and did not do:**

* **P-1.** Repair the **seven Tier-2** instruments (`t234-sweep-instrument-audit` ×2,
  `t239-r11-rerun` ×5) so their `|| echo` arms exit instead of printing, then delete their rows from
  `FAILOPEN_PIN_FILE_LIST` in the same commit. Each lives in another task's capture directory; T238
  named the first two in its §8 and did not diff them either. **Scope: two files under
  `.softhouse/capture/t234-sweep-instrument-audit/instruments/`, five under
  `.softhouse/capture/t239-r11-rerun/instruments/`.**
* **P-2.** `A2-32-evidence/sweep.sh` (Tier 1) is T238's §8 item 5 and is fail-**closed** today because
  it exits 9 before reaching the arm. Repair or annotate; it is one edit from live.
* **P-3.** `sweep-ORIGINAL.sh` (Tier 1) must **stay** on the pin **permanently**. It is a specimen, not
  an instrument. A future task that "cleans up the frontier" must not touch it, and the pin comment in
  `conformance.sh` says so.
* **P-4.** Promote T238's `sweeplib.sh` to `.softhouse/bin/` (T238 §8 item 8) so the linter's advice
  points at a stable path.

**The `.softhouse/vectors/` payloads, `docs/adr/` and `.softhouse/gates.md` were not touched.**
`git diff --stat` against my fork point shows zero files under any of them.

---

## 6. THE BAR — RUN BY ME, ON THE REBASED TREE, PASTED FROM `transcripts/90-bar.txt`

Harness invoked with **`bash`**, never `sh`. **`gofmt -w` was never run on `contract.go`** (G-3).

```
commit         : 6875cd7d949df31d5de371b7b5e1b5ba4d3931f3
fork point     : 8e8d65da2883cb5274aad0f82a220e7061176e59
origin/main    : 8e8d65da2883cb5274aad0f82a220e7061176e59
vector store   : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d      <- UNCHANGED BY ME

conformance.sh exit  : 0
conformance: CENSUS fail-open instruments — inspected 891 tracked .sh/.py file(s)
conformance:   frontier 9, pinned at 9.
conformance:   frontier == pinned (all 9 rows, by path).
conformance: reference oracle (https://localhost:8443/…/health) probe = up     <- PRESENT, and 'up'
    ledger parity           PASS 4    FAIL 0
    ledger oracle-refusal   PASS 2    FAIL 0
    ledger inadmissible     0
    ledger harness errors   0
    ledger cells compared   70 graded, of which 21 are MONEY cells in int64 minor units
    ledger citations        12 PART-TWO resolutions: 1 ARTEFACT-BYTES, 8 HTTP-SIDECAR,
                            3 FILE-NAME-ONLY (pinned 3), 0 UNRESOLVED.
    parity vectors          PASS 46   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    self-test fixtures      PASS 1    FAIL 0
    refused                 0
    inadmissible            0
    harness errors          0
    cells compared          7884 graded, 93 ungraded
    invariant violations    0
    invariant assertions    0 NOT RUN
    invariant assertions    4 EXEMPTED BY A VECTOR
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   exemption census READ: exempted assertions (graded) = 4 == pinned 4
conformance:   exemption census READ: declared exemptions (loaded) = 4 == pinned 4
conformance:   exemption census READ: GROUNDED                     = 4 == pinned 4
conformance:   exemption census READ: UNDETERMINED-ON-THE-RECORD   = 0 == pinned 0
conformance:   exemption census READ: UNGROUNDED                   = 0 == pinned 0
conformance:   exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
conformance:   exemption census READ: LEDGER parity vectors        = 4 == pinned 4
conformance:   exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
conformance:   exemption census READ: LEDGER money cells compared  = 21 == pinned 21
conformance: CENSUS wrong ledger implementations — discovered 6 … pinned at 6.
conformance:   KILLED  ledger-wrong-code-ignored — exit 1, ledger parity FAIL 4 + oracle-refusal FAIL 0
conformance:   KILLED  ledger-wrong-header-refusing — exit 1, ledger parity FAIL 1 + oracle-refusal FAIL 0
conformance:   KILLED  ledger-wrong-manual-permission-ignored — exit 1, ledger parity FAIL 0 + oracle-refusal FAIL 1
conformance:   KILLED  ledger-wrong-netting-totals — exit 1, ledger parity FAIL 4 + oracle-refusal FAIL 0
conformance:   KILLED  ledger-wrong-split-drift — exit 1, ledger parity FAIL 2 + oracle-refusal FAIL 0
conformance:   KILLED  ledger-wrong-truncating — exit 1, ledger parity FAIL 4 + oracle-refusal FAIL 0
conformance:   all 6 wrong ledger implementations DIED through this harness, not by hand.

--prove exit         : 0
PROOFS: 23 passed, 0 failed

go build exit        : 0
go vet exit          : 0
go test exit         : 0
ok  github.com/gerege/nexus/internal/apps/ledger                        0.4s
ok  github.com/gerege/nexus/internal/apps/ledger/conformance            3.5s
ok  github.com/gerege/nexus/internal/apps/loanschedule                  8.0s
ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance     73.7s
gofmt -l             :
    internal/apps/loanschedule/contract/contract.go
```

**Every figure in the driver's stated bar holds.** The nine census pins are the same nine and read the
same values; the two new census lines (`CENSUS fail-open instruments`, `CENSUS wrong ledger
implementations`) are **not** census pins and do not change that count. `--prove` is still **23/0** —
nothing was added to it, deliberately: `--prove` is the harness's proof of its *own* mutation
behaviour, and these three guards are proved by the committed red drives instead.

---

## 7. WHAT REMAINS UNWIRED, AND ITS SCOPE

1. **T226's `v3`** — the THIRD P-45 instance, still wired to nothing. **Not touched by me.** It also
   holds `conformance.sh`; my two additions are self-contained functions plus one call each, so a
   `v3` wiring should merge cleanly. **Scope: `.softhouse/conformance.sh` plus whatever T207 left.**
2. **The seven Tier-2 and one Tier-1 fail-open instruments** (§5 P-1/P-2). Pinned, printed on every
   run, and **not repaired**. The pin is a frontier, not an amnesty.
3. **`gate_exemption_census`'s refusal path** still leaves the binary's stale `VERDICT: PASS` line
   unretracted (§4.2). I added the retraction to my gate only; widening it to the census gate is three
   `warn` lines in a function I had no mandate to edit. **Scope: `.softhouse/conformance.sh`,
   `gate_exemption_census`'s final `if [ "$ok" -ne 1 ]` block.**
4. **The capture-rig gap behind the three FILE-NAME-ONLY citations** (§2.3c). The fix is in the rig:
   write the `capture_case_id` into the `.http` sidecar for **readback responses** as it already does
   for requests. When that lands, the three pin rows must be **deleted** — and the deflation arm will
   demand it. **Scope: `.softhouse/capture/tierA-a2/` rig, plus re-capture.**
5. **`TestEveryWrongImplementationIsKilled`** is still only reachable from `go test`. That is now
   redundant rather than load-bearing — the shell gate runs the same six on every graded run — but the
   test was not removed and should not be: it fails the build, which is a second, earlier route.

## 8. WHAT MUST NOT BE INFERRED FROM ANY OF THIS

A green run still means *"matches the reference oracle on captured vectors, within the graded domain"*.
The ledger is graded on **six captured cases**; accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances, `GLClosure` and slot resolution remain **ungraded**. What changed
today is only that **three checks which could not fail now can**, and that a green harness run now
**executes** the six wrong implementations instead of merely coexisting with them. **Nothing was cut
over and nothing here authorises it.**

## 9. FILES

| file | what changed |
|---|---|
| `.softhouse/conformance.sh` | `+FAILOPEN_PIN_FILE_LIST`, `+guard_no_fail_open_instruments` (called from `run_guards`), `+EXEMPTION_PIN_LEDGER_WRONGIMPLS`, `+gate_wrong_ledger_impls_die` (called from `main_grade`), `+` the verdict-retraction lines |
| `nexus/internal/apps/ledger/conformance/admit.go` | `CitationMode` / `CitationResolution` / `citationMode` / `CitationResolutions` / `citationNameOnlyPin` / `StaleCitationPins`; `citationReasons` now takes the vector's case id and refuses an unpinned name-only resolution |
| `nexus/internal/apps/ledger/conformance/grade.go` | `Summary.Citations` + four counters; the census over loaded vectors; the deflation `Fatal` |
| `nexus/internal/apps/loanschedule/conformance/report.go` | the `ledger citations` block (T242's `report.go` shape read first, not assumed) |
| `nexus/internal/apps/ledger/conformance/conformance_test.go` | `TestPartTwoOfTheCitationCanFail`, three subtests, both directions plus the argument |
| `.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py` | **outside my stated scope, declared not smuggled**: two ADDITIVE, default-preserving changes — a `FAILOPEN_LINT_JSON` override (the harness must not rewrite a tracked file on every graded run) and a machine-readable `FAILOPEN-FRONTIER` line for the gate to read. Every T238 transcript re-runs identically |
| `.softhouse/capture/t243-wiring/` | four instruments, four transcripts, per-arm evidence |
