# PART B — T298 RESUMED AT A NEW COMMIT. EVERYTHING BELOW WAS RE-DERIVED, NOT INHERITED.

Part A (`REVIEW.md`) was produced by an earlier T298 session forked at `main@5964ab5`. That session ended
without the branch being merged. This session rebased the branch onto **`main@39d2156`** (82 commits later,
clean rebase, no conflicts) and **re-ran the load-bearing measurements with its own selectors at its own
commit**, because a figure restated without the commit that produced it is exactly the defect T256 was filed
about. Part A is preserved verbatim; where Part B confirms it, the confirmation is independent, and where
Part B adds or corrects, it says so.

Instruments are committed beside their transcripts and are re-runnable. Each transcript prints its own
`HEAD`.

| # | instrument | transcript |
|---|---|---|
| 1 | `t298b-census.sh` | `evidence/t298b-10-census.txt` |
| 2 | `t298b-wider-live-surface.sh` | `evidence/t298b-20-wider-live-surface.txt` |
| 3 | `t298b-marker-attack-matrix.sh` | `evidence/t298b-30-marker-attack-matrix.txt` |
| 4 | `t298b-worktree-composition-drive.sh` | `evidence/t298b-40-worktree-composition.txt` |
| 5 | `t298b-oracle-facts-diff.sh` | `evidence/t298b-50-oracle-facts.txt` |
| 6 | `bash .softhouse/conformance.sh` | `evidence/t298b-90-bar.txt` |

---

## B1. THE POPULATION — RE-MEASURED WITH MY OWN SELECTOR AND MY OWN BUCKET RULE. ALL FIGURES REPRODUCE.

I did not run T256's census. `t298b-census.sh` is written from scratch: fixed-string `-F -l` listing over
tracked files at a named rev, with the search engine's rc **classified** (`0` matches / `1` MEASURED zero /
`>1` engine error, which aborts and is never reported as an absence), and a bucket rule that is *mine*, not
T256's — LIVE is anything under `.softhouse/bin`, `.softhouse/guards`, `conformance.sh`, `.softhouse/launchd`,
`.claude/`, `nexus/`, or a Makefile; ARCHIVED is anything executable-shaped elsewhere; PROSE is the rest.

| figure at `f02d849` | T256 | Part A | **Part B (mine)** | |
|---|---|---|---|---|
| `/Users/buv/gerege-nbfi/.softhouse/toolchain` | 58 | 58 | **58** | REPRODUCES |
| `/Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh` | 39 | 39 | **39** | REPRODUCES |
| union, deduplicated | 92 | 92 | **92** | REPRODUCES |
| LIVE | 1 | 1 | **1** — `.softhouse/bin/go-env.sh`, nothing else | REPRODUCES |
| ARCHIVED | 60 | 60 | **60** | REPRODUCES |
| PROSE | 31 | 31 | **31** | REPRODUCES |

[VERIFIED: `evidence/t298b-10-census.txt`, run at reviewer `HEAD b9187bb`.]

**T256 pinned its figures to a commit, and its census re-derives rather than echoes.** Checked both: the
handoff states `f02d849` beside every number, and `10-population-census.sh` takes the rev as input and
searches the tree rather than restating a constant. That is exactly what the brief asked me to test, and it
holds.

**P-40** — *"an enumerator must count what it skipped and say so. If it cannot parse a file it must name it,
not drop it."* My extension census of the union at `f02d849` is `2 json / 22 md / 10 py / 51 sh / 7 txt`,
summing to 92 with **no `(no-extension)` bucket at all**. Nothing *could* have been silently dropped, which
is stronger than T256's own hedge that its zero was "a statement about the two extension lists".

### B1a. NEW — the population is still GROWING, and that is the honest test of whether the remedy worked

Nobody had measured this. At my `HEAD` the same two literals match **71 + 47 = 108** tracked files, up 16
from `f02d849`, and the transcript lists every addition. Adjudicated one by one:

- **5** are T256's own artefacts (its census, its drive transcripts, its handoff) — instruments that quote
  the literal *in order to measure it*;
- **6** are this review's own artefacts (Part A's evidence and mine) — same category;
- **5** are later fires' `evidence/*.txt` transcripts (`t284-schema2-callsites`, `T293`) — recordings of
  output, not prescriptions;
- **ZERO are new executable instruments that PASTE the line as an instruction.** `removed since f02d849:` is
  empty; `added` contains exactly one non-review `.sh`, and it is T256's own census.

The number went up and **the defect did not**. That is the strongest available evidence that T256 fixed the
right object — the instruction, not the inventory — and it is a finding *for* T256 that T256 could not have
made itself.

---

## B2. "ZERO LIVE EXECUTABLE HARDCODES" — WIDENED ON BOTH AXES. **IT HOLDS.**

This is the claim that licensed leaving 60 sites alone, so I widened past T256's selector on the surface axis
*and* the pattern axis. **P-70** — *"'Latent', 'not promoted', 'can never resolve', 'no guard exists' — four
ways this program stated a search result as a world fact"* — so every line below says where I looked.

**Surfaces the brief names, each measured present or absent** [VERIFIED: `evidence/t298b-20-wider-live-surface.txt` §A]:

| surface | result |
|---|---|
| `Makefile` / `makefile` / `GNUmakefile` | **ABSENT**, all three spellings tested with `-e` |
| `.github` / `.gitlab-ci.yml` / `Justfile` / `Taskfile.yml` / `package.json` / `.pre-commit-config.yaml` | **ABSENT**, each measured |
| **git hooks** | `core.hooksPath` **unset**; common dir `= /Users/buv/gerege-nbfi/.git`; executable non-`.sample` hooks installed **= 0**. A worktree resolves hooks through the common dir, so this is the count for every worktree too |
| **launchd plist** | 1 file; its `ProgramArguments` is `/bin/zsh -lc <…>/fire-program.sh` and nothing else |

**Pattern axis — things a fixed-string search would miss** [same transcript, §C]:

- **Assembled paths** (`"/Users` + suffix, `/Users/$VAR`, `${USER}/`) across the live set: **MEASURED ZERO**.
- **`GOROOT` / `GOPATH` / `GOCACHE` / `GOMODCACHE` / `GEREGE_TOOLCHAIN` assignments outside `go-env.sh`:
  MEASURED ZERO.** This is the sharpest one — the paste the document forbids in prose does not exist anywhere
  in the live harness, so `go-env.sh` really is the single seam.
- **Here-docs** in the live set: 3, all in `fire-program.sh` / `rehydrate-check.sh`, none toolchain-related.
- **Variable-indirect sourcing:** 4 real sites, every one `. "$env_script"` where `env_script` was built
  `BASH_SOURCE`-relative (`conformance.sh:642`, `check-ledger-invariants.sh:58`,
  `drive-red-ledger-invariants.sh:30`) — the robust form, not a host path.
- **Indirect execution of the 60:** no glob-and-execute, no `find … -exec`, no batch runner. The only
  citations of `capture/` or `reviews/` paths in the live set are two **comments**
  (`conformance.sh:732,1797`). `.claude/skills` cites **zero** of them.

**The only host paths that survive comment-stripping in the live executable set** — and I stripped *trailing*
comments too, which is stricter than T256's full-line strip:

```
.softhouse/bin/build-oracle-image.sh:9   FINERACT_SRC="${FINERACT_SRC:-/Users/buv/fineract}"
.softhouse/bin/fire-program.sh:19        REPO="${GEREGE_NBFI_REPO:-/Users/buv/gerege-nbfi}"
.softhouse/bin/fire-program.sh:20        FINERACT_SRC="${FINERACT_SRC:-/Users/buv/fineract}"
.softhouse/launchd/…plist:14,53,55,59,62,64   (host config, by definition)
```

All three `bin/` sites are `${VAR:-default}` **overridable defaults** and all three are named in T256's §7
skipped table. The plist is the Mac fire's own configuration. **`fire-program.sh` mentions the toolchain,
`go-env.sh`, `GOROOT` and `GEREGE_GO_*` exactly zero times**, so the unattended fire's entry point does not
touch this population at all.

**VERDICT ON THE LOAD-BEARING CLAIM: it holds, over a materially wider surface than T256 searched.** I could
not construct a path — Makefile, hook, plist, here-doc, indirection, skill, wrapper — by which a graded run
reaches one of the 60. Where I looked is the table above. What I did **not** do is prove no human will type
`bash <one of them>` by hand; that is `P-70`, and T256 disclosed it itself.

---

## B3. THE MARKER DRIVE — 9 ATTACKS EXECUTED, NOT REASONED ABOUT. **7 CAUGHT, 2 SATISFIED WHILE WRONG.**

`t298b-marker-attack-matrix.sh` mutates the real document, runs the **real** drive, records the **real**
verdict, restores the file, and verifies the tree is clean before it exits. Every row below is an execution
[VERIFIED: `evidence/t298b-30-marker-attack-matrix.txt`].

| # | mutation | drive result | correct? |
|---|---|---|---|
| A0 | control, document as committed | `rc=0 GREEN` | yes |
| A1 | fenced line -> `. ~/gerege-nbfi/…/go-env.sh` (**tilde** host path — evades both substring checks) | `rc=1 RED`, 11 assertions | yes — **caught, and not by the substring check** |
| A2 | fenced line -> `. "$HOME/gerege-nbfi/…/go-env.sh"` | `rc=1 RED`, 11 assertions | yes — **caught** |
| A3 | markers present, fence present, **body empty** | `rc=2 REFUSING` | yes |
| A4 | **multi-line body inside one fence** (the comment says *"Keep it to one line"*) | `rc=1 RED` — *"the prescription is 2 lines, not 1"* | yes |
| A5 | **host path inside the markers, outside the fence** | **`rc=0 GREEN`** | **NO — SATISFIED WHILE WRONG** |
| A6 | **second host-pinned fenced block elsewhere in the document** | **`rc=0 GREEN`** | **NO — SATISFIED WHILE WRONG** |
| A7 | **both markers deleted**, fenced line left in place | `rc=2 REFUSING` | yes *by the drive* — see B3b |
| A8 | BEGIN marker **renamed by one character** | `rc=2 REFUSING` | yes |
| A9 | portable line that activates fine but appends `2>/dev/null`, **silencing go-env.sh's banner** | `rc=1 RED`, 4 assertions | yes |

**A1, A2 and A9 are new attacks neither T256 nor Part A ran, and the drive survived all three.** A1/A2 matter
because the drive's own textual checks are literal substring tests for `/Users/` and `/home/` — both attacks
evade them — and the drive catches them anyway, at STEP 3, *functionally*: off-host the tilde still expands to
this Mac's home, the real toolchain is found, and the assertion `GEREGE_GO_SOURCE=fallback-path` fails. The
drive is a better instrument than its own textual assertions suggest, and I only know that because I tried to
beat it.

### B3a. The two that go green are one defect, stated exactly

**The guarded object is smaller than the object that causes the defect.** The extractor
(`awk … inblk && fence`) sees **one fenced line between two markers**. What manufactured 60 pastes is **the
document** — a worker reads a section, not an `awk` range. So:

- **A5** — one prose line *inside the marker region*, one line below the comment that promises *"replace it
  with a host-pinned path and the drive goes red off-host … with the offending line quoted back."* GREEN.
- **A6** — a *"Toolchain, quick reference"* block appended anywhere else in the file. GREEN. This is the more
  likely of the two in practice: nobody edits between HTML comment markers by accident, but everybody adds a
  quick-reference section.

Part A found both; Part B **reproduces both at a different commit, on a rebased tree, with a freshly written
harness**. Independent confirmation, not a restatement.

### B3b. A7 is the finding that ties the whole thing together

The brief asks: *the markers deleted entirely — does anything notice?* **The drive notices (`rc=2`). Nothing
else does.** And the drive is invoked by nothing (B4). So the honest answer is **no — in the graded world,
nothing notices.** A7's tick above is a tick for the *instrument*, not for the *program*.

A consequence for whoever wires it: the drive distinguishes `rc=1` (an assertion failed) from `rc=2`
(*"REFUSING: the document no longer prescribes anything runnable"*). **Both must be HARD failures.** A wiring
that treats `rc=2` as "skip, could not run" reintroduces the exact fail-open shape that made `conformance.sh`
refuse T256's own census.

---

## B4. **SHOULD A GRADED PATH CALL IT? YES. AND NO OTHER GUARD WOULD CATCH THIS — I MEASURED.**

**P-45** — *"A test-only guard is not a guard. … Rule: when hardening a check, verify the path that actually
executes in CI/conformance calls it, not merely that a test does."*

Part A established that nothing calls the drive. I went one step further and asked whether some *other* graded
guard would incidentally catch a re-introduced host path.

- `run_guards()` invokes exactly **8** guards [VERIFIED: `.softhouse/conformance.sh:2011-2018`].
- The only one in the neighbourhood, `guard_no_host_state_in_lint_corpus`, pins assignments **whose value
  starts `/tmp`, `/private/tmp` or `/var/tmp`** — its regex is
  `^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=["']?/(tmp|private/tmp|var/tmp)/`
  [VERIFIED: `conformance.sh:1863`]. **It says nothing about `/Users/`.**
- Search of the whole of `conformance.sh` for `/Users`, `host path`, `HOST_PATH`, `home directory` outside
  comments: **MEASURED ZERO** [VERIFIED, run this session].
- **Live proof, unintended and therefore worth more than the search:** the bar I ran in B6 passed **exit 0
  with `t298b-census.sh` staged in the tree — a brand-new tracked `.sh` file containing the literal
  `/Users/buv/gerege-nbfi/.softhouse/toolchain`.** The fail-open frontier stayed 11 == pinned 11. **A new
  host-path paste entered the repo and the graded bar did not blink.** That is the enforcement gap
  demonstrated rather than argued.

**Where to wire it — exactly.** `.softhouse/conformance.sh`, `run_guards()`, **immediately after line 2018**
(`guard_no_host_state_in_lint_corpus  || failed=1`), as a ninth `|| failed=1` row, so its failure joins the
tally that already prints *"a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass."*

**What to call there — and it is NOT the whole drive.** The drive initialises a scratch checkout and compiles
the module twice; that belongs in a portability task, not in every graded run. Wire the **text half**, which
costs milliseconds and closes A5, A6, A7 and A8 at once:

1. extract the BEGIN…END region of `.softhouse/reference-oracle.md`; **refuse if the markers are absent,
   duplicated, or out of order** — that is A7/A8;
2. assert exactly **one** fenced line in the region — A3/A4;
3. assert **no line anywhere in the region** matches `/Users/|/home/[a-z]|\$HOME|~/` — A5, and it also catches
   A1/A2 textually instead of relying on an off-host functional arm;
4. assert the region is the **only** place in the document prescribing `. …go-env.sh` — A6.

Steps 1-4 need no toolchain, no network, no scratch checkout and no oracle, so they cannot make the bar
flaky. The off-host drive stays a hand-run instrument, which is the right home for something that compiles a
module twice.

---

## B5. THE WORKTREE COMPOSITION — DRIVEN IN THE FIXTURE. **21 ASSERTIONS, 0 FAILURES.**

The brief is right that I am the test fixture, and this is the one part of T256's claim that cannot be tested
from the main checkout. `t298b-worktree-composition-drive.sh` **aborts (`exit 9`) if it finds itself in a
non-linked checkout**, so it cannot pass vacuously [VERIFIED: `evidence/t298b-40-worktree-composition.txt`].

The two queries genuinely disagree here, which is the whole point:

```
rev-parse --show-toplevel  = /Users/buv/gerege-nbfi/.claude/worktrees/agent-a55bfc2e4dfb7aa31
rev-parse --git-common-dir = /Users/buv/gerege-nbfi/.git      -> main checkout /Users/buv/gerege-nbfi
```

The drive **extracts the line from the document** and refuses to run if what it extracted is not
byte-identical to the line it tests, so it cannot grade a stale line. Then, from **three** working directories
inside the worktree (repo root, `nexus/`, `.softhouse/guards/`), with `GOROOT` / `GOPATH` / `GOCACHE` /
`GOMODCACHE` / `GEREGE_TOOLCHAIN` / `GEREGE_GO_SOURCE` all **unset** first:

| asserted | result |
|---|---|
| `GEREGE_GO_SOURCE` | `pinned` — 3/3 |
| `GOROOT` | `/Users/buv/gerege-nbfi/.softhouse/toolchain/go` — **the MAIN checkout**, 3/3 |
| `GOMODCACHE` | `/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache` — **the MAIN checkout**, 3/3 |
| `go env GOROOT` / `go env GOMODCACHE` — **the compiler's own answer, not just the variable** | agree, 3/3 |
| does `GOROOT` point inside the worktree? | **no**, 3/3 |
| worktree-local `.softhouse/toolchain{,/go,/gopath,/gocache,/gomodcache}` | **absent, all five**, before and after |
| `find <worktree>/.softhouse -maxdepth 1 -name toolchain` | **0** |
| `go build ./...` from the worktree's `nexus/` | **rc=0**, `go1.26.6 darwin/arm64` |

**Nothing executed was broken; a worktree does NOT get its own empty toolchain dir and does NOT get a second
module cache.** The mechanism, read from source and confirmed by the run: `go-env.sh` anchors on
`BASH_SOURCE[0]`'s directory — not on cwd — then asks git for the **common** dir from there
[VERIFIED: `.softhouse/bin/go-env.sh:92-116`]. The activation line's `--show-toplevel` therefore only selects
*which copy of `go-env.sh` to source*; `go-env.sh` re-derives the shared root itself. **The composition is
correct because the two queries are asked at different levels, not despite it.** Its third fallback candidate
`$_g_anchor/../../toolchain` — the one that *would* give a worktree its own toolchain — is unreachable while
git works, and the `find` count of 0 shows nothing created it anyway.

**Negative control, run in the same fixture:** the pre-T256 hardcoded line still returns `src=pinned` here.
The old defect is invisible on this Mac, exactly as T256 said — reproduced rather than believed.

---

## B6. THE BAR — RE-RUN BY ME, AT MY COMMIT, WITH `bash`. **PASS.**

`bash .softhouse/conformance.sh`, tree staged first, output captured to a file, no pasted verdict accepted.
**P-84** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE … four exit-2
paths precede the probe, and a failed HARD guard is one of them."* Read in that order:

| read order | reviewer's run |
|---|---|
| **1. probe line PRESENCE** | **present — 1 occurrence** |
| 2. its value | `reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up` |
| 3. fail-open frontier | `frontier 11, pinned at 11` -> `frontier == pinned (all 11 rows, by path).` |
| 4. exit | **0** |
| 5. verdict | `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` |

[VERIFIED: `evidence/t298b-90-bar.txt`.] The graded root printed is this worktree, so the harness was reading
the tree it was grading. Reproduces Part A's numbers 82 commits later.

---

## B7. THE ORACLE FACTS — DIFFED AT THE CORRECT RANGE. **NOTHING DAMAGED.**

"The oracle" here is the **Fineract reference implementation** (test-oracle sense). **Oracle Database is
prohibited** and is nowhere in this change.

Range: the merge base of `47b9b5c` and `e6fca83` is **`f02d849`**, and the three-dot diff from there is
T256's own change. Part A used the three-dot form and was right to; **my first pass used two dots and produced
a false report that T256 touched `.softhouse/tasks.json`**. I corrected it inside the transcript rather than
quietly re-running [`evidence/t298b-50-oracle-facts.txt` §7 alarm 3]. **T256 touched exactly 8 files, and
`tasks.json` is not one of them.**

- **Every fact-bearing line is byte-identical across the change.** 149 lines matched a 22-alternative fact
  pattern (`tenant|fineract_gerege|PostgreSQL|426a23544|Asia/Ulaanbaatar|8443|5432|HALF_UP|…`) in **both**
  revisions, and the diff of that text with line numbers stripped is **empty**.
- Named facts asserted one at a time, `pre` vs `post`: `fineract_gerege` 7/7 · `PostgreSQL` 13/13 ·
  `docker-compose-postgresql.yml` 4/4 · `426a23544` 7/7 · `Asia/Ulaanbaatar` 8/8 · `actuator/health` 5/5 ·
  `8443` 3/3 · `5432` 8/8 · `HALF_UP` 9/9 · `fineract-db-1` 3/3. **No loss anywhere.**
- **The one apparent loss was my selector's fault, and I say so.** `gerege` went 19 -> 18 because the *repo
  directory* is named `gerege-nbfi` and my substring caught host paths. The three removed lines are all host
  paths — the `build-oracle-image.sh` invocation, the `GOROOT` row, the `Activation` row. **Every tenant fact
  row survives identically**, including `| 2 | gerege | Gerege T22 Audit Tenant (Asia/Ulaanbaatar) |
  Asia/Ulaanbaatar | fineract_gerege |` and the section *"The `gerege` tenant is the production-representative
  one"*.
- **`ojdbc` / `oracle.jdbc` / `1521` are present 3 / 2 / 3 times in both revisions and that is NOT a
  violation.** Every occurrence is the prohibited product named inside a **negative assertion about it** —
  `:117` *"`ojdbc` / `oracle.jdbc` entries in `/app/fineract-provider.jar` | **0**"*, `:119` *"Listener on
  port `1521` | none"*, `:981` *"prohibited-engine grep … | **0 hits**"*. A document that proves Oracle
  Database is absent has to be allowed to name it. `docker-compose-mysql` / `docker-compose-mariadb`: **0**.
  Recorded here because a reviewer who prints a scary count and does not adjudicate it is doing the thing
  this program calls a fail-open.
- **The `build-oracle-image.sh` invocation change survives and resolves.** `:153`
  `/Users/buv/gerege-nbfi/…/build-oracle-image.sh` -> `:157` the self-locating form. Resolved from this
  worktree, the target **exists and is executable** (`-rwxr-xr-x`, 3279 bytes). The prose reference at `:130`
  was already repo-relative and is unchanged.
- Part A's **F-6 stands, and I confirm the mechanism**: `:148` still says `cd /Users/buv/fineract`, and from
  there `--show-toplevel` answers `/Users/buv/fineract`, which has no `.softhouse`. The new self-locating
  invocation sits nine lines below a `cd` that breaks it.

---

## B8. PART B'S OWN FINDINGS

| # | severity | finding |
|---|---|---|
| **B-1** | **MAJOR — merges into F-3** | **No graded guard anywhere would catch a re-introduced host path.** `run_guards()` has 8 guards; the closest, `guard_no_host_state_in_lint_corpus`, matches only `/tmp`-rooted assignments. Demonstrated live: my bar passed exit 0 with a **new tracked `.sh` carrying the literal** staged in the tree. |
| **B-2** | MODERATE | **The drive has no worktree arm.** Its STEP 1 runs from `$REPO`, `$REPO/nexus`, `$REPO/.softhouse/guards` only. Every worker in this program runs in a **linked worktree**, where the two git queries disagree — the one condition the composition depends on, and the drive never enters it. I drove it (B5) and it is **correct**, so this is a **coverage** gap, not a live defect. Fix: adopt `t298b-worktree-composition-drive.sh`, or add one `worktree add` arm inside the drive. |
| **B-3** | MINOR / wiring note | The drive's `rc=2` (*REFUSING*, markers gone) and `rc=1` (assertion failed) must **both** be HARD failures when wired. Treating `rc=2` as "skip, could not run" is the fail-open shape `conformance.sh` already refused once — in T256's own census. |
| **B-4** | **positive finding** | The population grew 92 -> 108 and **zero of the 16 additions is a new instruction-shaped paste.** The remedy is working on the object it was aimed at. |

**Confirmed independently from Part A** (re-derived at a different commit with different instruments, not
copied): the population figures; the "zero live executable hardcodes" declination; F-4's two
satisfied-while-wrong cases (my A5, A6); F-3's "invoked by nothing"; the oracle facts intact.

**Corrected in Part A: nothing.** Part A's three-dot range was right and my two-dot first pass was wrong; the
error recorded above is mine, not Part A's.

---

# FINAL VERDICT (Parts A + B) — **SPLIT**

**APPROVED — the analysis, the declination, and the direction of both document edits.**
Every figure T256 published re-derives at its stated commit under a selector I wrote myself. The decision to
leave the 60 archived instruments byte-identical is **correct, and now supported by a wider search than either
T256 or Part A ran** — no Makefile, no CI, no installed git hook, no plist arm, no here-doc, no indirection,
no skill reaches one. T256's second, independent reason is real and checkable:
`HOSTSTATE_PIN_TEMP_ASSIGN_LIST` pins archived instruments by path **and by exact source line**, so the
literal fix the brief's headline asked for would have reddened someone else's bar. Nothing was inflated,
nothing was asserted that I could not re-derive, and the one number T256 could not reproduce it traced to its
true origin instead of quietly restating it. **No oracle fact was damaged; no money path, ledger, vector,
contract or `DEC-n` is touched; the bar is green at my own commit.**

**NOT APPROVED AS A FIX — the remedy does not yet enforce what its own comment promises.** Two independent
reasons, both executed, both now reproduced at two different commits by two different harnesses:

1. **F-3 / B-1 — it is graded by nothing, and nothing else would catch the regression.** The marker block says
   *"THIS BLOCK IS EXECUTED, NOT JUST READ"*, and today it is only read. `run_guards()`'s 8 guards contain no
   host-path check at all; I proved it by landing a new tracked file carrying the literal and watching the bar
   pass exit 0. **P-45**: *"a test-only guard is not a guard … verify the path that actually executes calls
   it."* Until line 2018 gains a ninth row, this convention enforces nothing.
2. **F-4 / A5+A6 — it can be satisfied while being wrong.** The drive grades one fenced line; the thing that
   manufactures pastes is the document. A host path one line below the promise, or a second quick-reference
   block anywhere else in the file, both go **GREEN**.

**Disposition: neither blocks the merge, and T256 should not be reverted.** T256 is already on `main`; it is
evidence and documentation, not money code; it made the situation strictly better; and F-3 is a limitation
**T256 declared in its own §9** and could not fix, because `conformance.sh` was partitioned to other tasks
that fire. Route both as follow-up tasks — B4 gives the exact file, the exact line, and the four assertions.

**MICRO-FIX (<=10 lines, mechanical) — identified, NOT applied**, because `.softhouse/reference-oracle.md` is
outside this review's permitted edit set: Part A's F-6 wording at `:649` (*"any working directory"* ->
*"any working directory **inside this repository**"*), which the `cd /Users/buv/fineract` at `:148` makes
concretely wrong nine lines earlier.

**Follow-up register** — Part A's F-3, F-4, F-6, F-7, F-8, F-9 all stand, with these amendments:

| # | severity | change from Part A |
|---|---|---|
| F-3 | MAJOR | **strengthened by B-1**; now has an exact wiring site (`conformance.sh:2018`) and a four-assertion, toolchain-free specification of what to call there |
| F-4 | MAJOR | **reproduced independently** at a second commit (A5, A6) |
| B-2 | MODERATE | **new** — the drive never enters a linked worktree; my drive is committed and adoptable as that arm |
| B-3 | MINOR | **new** — `rc=2` must map to a HARD failure when wired |
| F-6 / F-7 / F-8 / F-9 | as filed | unchanged; I re-confirmed F-6's mechanism and F-8's three `BASH_SOURCE`-relative live consumers |
