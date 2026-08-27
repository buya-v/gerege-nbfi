# T298 — INDEPENDENT review of T256 (toolchain population / the self-locating activation line)

Reviewer branch: `softhouse/T298-review-t256`. Fork point: `main` @ `5964ab5`.
Upstream read **from the branch**, not from disk: `git show e6fca83:.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T256.md`.
T256 was already merged as `d97fae3`; the diff under review is `git diff 47b9b5c...e6fca83`.

**VERDICT: SPLIT.**

- **APPROVED** — the population re-derivation, the census instrument, the decision *not* to rewrite the 60
  archived instruments, the two `reference-oracle.md` edits' direction, and the drive as an instrument.
  Everything T256 asserted that I could re-derive, re-derived. Nothing was inflated.
- **NOT APPROVED as a fix — the remedy does not enforce what it claims** (F-3, F-4). The marker convention
  is (a) invoked by no graded path and (b) satisfiable while false. Both are **constructed and executed**
  below, with transcripts. Neither is a merge-blocker now (T256 is already on `main` and is *evidence*, not
  money code), so both are routed as follow-ups rather than a revert. F-3 is a limitation **T256 declared
  itself**, which is why this is a finding against the fix's reach and not against T256's honesty.
- **MICRO-FIX identified but NOT applied** (F-6): the fix site is `.softhouse/reference-oracle.md`, which is
  outside this review's `files_hint`. Exact text given below.

---

## THE BAR, re-run by the reviewer

`bash .softhouse/conformance.sh` (bash, never sh; tree staged first — ledgerguard reads via `git ls-files`).
**P-84** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE … four exit-2
paths precede the probe, and a failed HARD guard is one of them."* Read in that order:

| | reviewer's run |
|---|---|
| probe line **PRESENCE** (read first) | **present, 1 occurrence** |
| probe line value | `probe = up` |
| exit | **0** |
| verdict | `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` |

Reproduces the stated fork-point bar exactly. Transcript: `evidence/90-bar-baseline.txt`.

---

## SCOPE AND NON-NEGOTIABLES — what I checked, so silence is distinguishable from not looking

`git diff 47b9b5c...e6fca83 --name-only` → **8 files**: 2 instruments + 3 evidence transcripts under
`.softhouse/capture/t256-toolchain-population/`, `handoff/…/T256.md`, and `.softhouse/reference-oracle.md`
(57 lines, exactly 2 hunks). [VERIFIED: `git diff 47b9b5c...e6fca83 --stat`]

- **No `nexus/`, no `.go`, no `DEC-n`, no frozen adapter contract, no `tasks.json`.** [VERIFIED: name-only
  filter over `dec-|contract|nexus/|\.go$|tasks.json` returns empty]
- **`conformance.sh`, `admit.go`, `bin/fire-program.sh` untouched** by T256 and by me. [VERIFIED: same filter]
- **Money non-negotiables: not engaged and not violated.** Grep of the entire diff for
  `ojdbc|oracle\.jdbc|1521|mysql|mariadb|float64|float32|BigDecimal|Stripe|Plaid|first_name|last_name|insured|guaranteed`
  returns **one** hit, and it is *pre-existing context* on the `docker compose` line whose own comment
  **forbids** mysql/mariadb. No money path, no ledger code, no `Idempotency-Key` surface is touched.
- **Reference-oracle (Fineract) connection facts intact** — tenant `gerege`, `fineract_gerege`, PostgreSQL,
  `docker-compose-postgresql.yml`, pin `426a23544` all outside both hunks. [VERIFIED: the diff has exactly
  two hunks, at `:150` and `:610-655`]
- **Terminology trap clean.** T256 uses "oracle" only in the Fineract test-oracle sense and says so
  explicitly. **Oracle Database is prohibited and is nowhere in the diff.**

---

## 1. I RE-DERIVED THE POPULATION. IT REPRODUCES — ALL FIVE FIGURES.

Full working: `evidence/10-population-rederivation.txt`. **Where I looked:** `git grep -F -l -- <literal>`
over tracked files at rev `f02d849` (T256's stated starting commit — the rev it pinned its figures to), two
fixed-string literals, no regex.

| figure | T256 | reviewer | |
|---|---|---|---|
| `…/.softhouse/toolchain` | 58 files | **58** | REPRODUCES |
| `…/.softhouse/bin/go-env.sh` | 39 files | **39** | REPRODUCES |
| union, deduplicated | 92 | **92** | REPRODUCES |
| LIVE bucket | 1 | **1** | REPRODUCES |
| ARCHIVED bucket | 60 | **60** | REPRODUCES |
| PROSE bucket | 31 | **31** (22 `.md` + 7 `.txt` + 2 `.json`) | REPRODUCES |
| SKIPPED | 0 | **0** | REPRODUCES **and is stronger than T256 claimed** |

On the last row T256 hedged — *"that is a statement about the two extension lists, not about the world."*
I checked the world: the union contains **zero extensionless files**, so nothing *could* have been dropped.
**P-40** — *"an enumerator must count what it skipped and say so. If it cannot parse a file it must name it,
not drop it."* T256 complied and then under-claimed its own compliance.

**"30" and "40" do not reproduce under any selector I tried**, and T256's trace of "30" is right: it is
`RUNNABLE: 30` from `.softhouse/capture/t253-portability/evidence/60-hardcoded-toolchain-census.txt`, the
**first literal only**. The brief was wrong; T256 was right to say so.

I additionally hand-checked the two population members that a driver *reads*, because a data file can
manufacture pastes exactly as an instruction can:
- `.softhouse/tasks.json:2230` — 1 hit, inside a **defect description** (`"D2 — .softhouse/bin/go-env.sh:12
  hardcodes GEREGE_TOOLCHAIN=…"`). An observation. Classification correct.
- `.softhouse/reference-oracle.md` at `HEAD` — `:618` (GOROOT row, relabelled *"an observation of one host,
  not a value to paste"*) and `:639` (quoting the removed line as history). Both observations. Correct.

---

## 2. "ZERO LIVE EXECUTABLE HARDCODES" — attacked BY CONSTRUCTION. **IT HOLDS.**

Full working: `evidence/20-live-execution-by-construction.txt`; instrument
`instruments-xref-live-surfaces.sh`. This is the claim the whole declination rests on, so I went looking
for a path by which one of the 60 executes.

1. **Glob-and-execute arm?** `for … in <capture|reviews|handoff>*`, `find … -name`, `xargs bash`, `bash $f`
   over `conformance.sh`, `bin/*.sh`, `guards/*.sh` → **zero matches.** No batch runner exists.
2. **Direct invocation from `bin/`, `guards/`, `launchd/`?** One match, and it is a comment
   (`fire-program.sh:107`).
3. **The one archived file the graded bar DOES execute** —
   `capture/t238-failopen/instruments/50-failopen-lint.py`, run at `conformance.sh:1565` — carries
   **neither literal** (`grep -c -F` → **0**) and is **not** one of the 92. The sharpest available
   counterexample fails.
4. **A wider citation surface than T256 searched.** T256 searched four directories. I added the surfaces an
   *agent* reads and obeys: `tasks.json`, `.softhouse/state`, **`.claude/` including `.claude/skills/`**,
   `docs/`, `CLAUDE.md` (`.github` and `Makefile` measured absent with `-e`). All 60 basenames, all
   surfaces. **7 of 60 are cited; zero are executed** — every citation is a `conformance.sh` comment, a
   data-pin row, or `tasks.json` prose. **`.claude/skills/**` contains zero references to any of the 60**:
   there is no documented manual invocation and no skill that would cause one to run.
   Restricted to T256's own four-directory selector the count is **exactly 3** — T256's figure REPRODUCES.

**I could not construct any path — wrapper, env var, CI arm, skill instruction, documented manual
invocation — by which one of the 60 executes.** The declination stands. The one residue is the one T256
already stated: no search proves that no human will ever type `bash <one of the 60>` by hand (**P-70**,
*"not found is a statement about the search, never about the world"*). That is correctly disclosed, not a
defect.

**And T256's second, independent reason is verifiable, not rhetorical:** 2 of the 60
(`reviews/T155-probe/prove-ix-sweep-and-help.sh`, `reviews/t246-dec2-rev6/drive-pin-red.sh`) are graded
**INPUT** to a live guard **by path and by exact assignment line**
[VERIFIED: `conformance.sh:1849-1850,1853`, `HOSTSTATE_PIN_TEMP_ASSIGN_LIST`]. Doing the literal thing the
brief's headline asked for really would have reddened the bar with nothing wrong.

---

## 3. F-4 — **BLOCKING FINDING: THE MARKER DRIVE CAN BE SATISFIED WITHOUT BEING TRUE. I BUILT THE TREE.**

Severity: **MAJOR.** The brief's core question, answered in the affirmative, by construction and execution.

**Reproduction (run, transcript committed as `evidence/40-marker-drive-GREEN-while-doc-prescribes-host-path.txt`):**

Insert **one prose line between the markers, outside the fence**, in `.softhouse/reference-oracle.md`:

```
On the local fire, run: `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`
```

Then `bash .softhouse/capture/t256-toolchain-population/instruments/30-portability-red-drive.sh`:

```
asserts: 26   failures: 0   skipped-without-a-failure: 0
DRIVE: GREEN
DRIVE_EXIT=0
```

The document now reads, **inside its own marker block, one line below the comment that says *"replace it
with a host-pinned path and the drive goes red off-host, in a transcript, with the offending line quoted
back"***:

```
```bash
. "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh"
```

On the local fire, run: `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`
<!-- T256-ACTIVATION-LINE:END -->
```

**Mechanism.** The extractor is
`awk '/BEGIN/{inblk=1;next} /END/{inblk=0} inblk&&/^```/{fence=!fence;next} inblk&&fence{print}'`.
It sees **only fenced content** between the markers. It does not police the marker region, and it does not
police the document. A reader reads the region; the drive reads one line of it.

**Variant M5, same green, more likely in practice:** append a *second* ```` ```bash ```` activation block
carrying a host path **anywhere else in the document**. `DRIVE: GREEN`. Full extractor attack matrix in
`evidence/43-marker-extractor-attacks.txt` (M0–M5).

**Why this matters here specifically.** T256's own thesis is that *the instruction manufactures the
population* — 60 pastes came from one sentence. The unit that manufactures pastes is **the document**, or at
minimum **the marker region a reader reads**. The drive grades **one fenced line**. The guarded object is
smaller than the object that causes the defect.

**Fail-closed cases that DO work, so this is a gap and not a rout:** deleting both markers → extraction
empty → drive exits **2** with a REFUSING banner. A second fenced block *inside* the markers → 2 lines →
red. Deleting only the END marker → runaway extraction, 9 lines → red. All correct.

**Shape of a real fix** (in `.softhouse/capture/t256-toolchain-population/`, not applied by this review —
it is a behaviour change, not a mechanical micro-fix): assert on the **whole marker region**, not the
fenced line — refuse if any line between BEGIN and END matches `/Users/|/home/` — and add a document-wide
arm asserting that the marker block is the **only** `. …go-env.sh` prescription in the file.

---

## 4. F-3 — **THE DRIVE IS INVOKED BY NOTHING. THE GRADED BAR IS BYTE-IDENTICAL WITH THE HOST PATH BACK IN.**

Severity: **MAJOR.** This is the decisive form of the vacuity question, and T256 **declared it itself**
(section 9: *"the marker-block convention is enforced by my drive, which is not yet called from
`conformance.sh`"*). I verified it rather than taking it on trust, and then measured the consequence.

**Reproduction:**
1. `sed` the fenced line back to the pre-T256 `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`.
2. `git add -A` ; `bash .softhouse/conformance.sh`.
3. **`CONFORMANCE_EXIT=0`. Probe line present, 1 occurrence, `= up`.
   `VERDICT: PASS (exit 0) — 46 parity vectors …, 7884 cells compared.`**
4. **`diff` against the baseline transcript: EMPTY. Byte-identical.**

Transcript: `evidence/42-graded-bar-GREEN-with-host-path-reintroduced.txt`. Tree reverted; `git status`
clean.

**P-45** — *"A test-only guard is not a guard … Rule: when hardening a check, verify the path that actually
executes in CI/conformance calls it, not merely that a test does."* Cross-checked against the earlier
finding: `grep -rn '30-portability-red-drive\|10-population-census'` across `.softhouse/` excluding T256's
own directory returns **zero** — no `conformance.sh` call, no `guards/`, no `launchd/`, no skill, no
`tasks.json`. The remedy's enforcement reach today is **zero executed sites**.

**Stated plainly, as the brief demands:** T256's remedy *is* a sentence a future worker must remember to
obey, plus an instrument nobody is obliged to run. **A real guard would have been one line in
`conformance.sh`'s verdict block invoking the drive** — which is exactly what T256 proposed and correctly
could not do, because `conformance.sh` was partitioned to other tasks this fire. The gap is real; the
reason for it is legitimate; it is now someone's task, and until it is done the convention enforces nothing.

---

## 5. F-5 — the drive DOES discriminate on the fenced line, and **T256 never drove that arm**. I did.

Severity: **INFORMATIONAL — a claim promoted from asserted to verified.**

T256's headline is *"put a host path back between those markers and the drive goes red."* Its **two vacuity
arms do not test that**: `--vacuity` and `--vacuity-absent` both install the pre-T253b hardcoded **body of
`go-env.sh`** into the scratch checkout [VERIFIED: `30-portability-red-drive.sh:132-158`, `HARD_PREFIX` /
`OLDBODY` heredoc]. Neither mutates the marker content. So the load-bearing claim about the marker
convention was **not itself driven** by its author.

I drove it. Fenced line reverted to `/Users/buv/…`, drive re-run:

```
extracted: [. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh]
ASSERT FAIL : the prescribed line names a host home directory: …
… 12 assertion(s) failed
DRIVE: RED       DRIVE_EXIT=1
```

Transcript: `evidence/41-marker-drive-RED-when-the-fenced-line-is-mutated.txt`. **Claim VERIFIED — by the
reviewer.** The drive is a good instrument. F-3 and F-4 are about what it is pointed at and who runs it.

---

## 6. F-6 — **MICRO-FIX: the self-locating line mislocates from inside a different git repo, and the document itself puts the reader there.**

Severity: **MODERATE.** Not applied — `.softhouse/reference-oracle.md` is outside this review's `files_hint`.

`reference-oracle.md:148` (unchanged by T256, inside a ```` ```bash ```` block):

```bash
cd /Users/buv/fineract
```

`reference-oracle.md:157` (**introduced by T256**), nine lines later:

```bash
"$(git rev-parse --show-toplevel)/.softhouse/bin/build-oracle-image.sh"
```

- `git -C /Users/buv/fineract rev-parse --show-toplevel` → **`/Users/buv/fineract`** [VERIFIED, run]
- `/Users/buv/fineract/.softhouse` → **does not exist** [VERIFIED, `ls`]

So a reader following the document top-to-bottom **on the very host it was written on** gets a path that
does not exist — where the absolute path T256 replaced would have worked. Same property for the activation
line. Reproduction matrix in `evidence/30-selflocating-line-attacks.txt`:

| scenario | `--show-toplevel` says | result |
|---|---|---|
| inside the repo (the case T256 drove) | the worktree | `rc=0`, `GEREGE_GO_SOURCE=pinned` |
| **cwd `/Users/buv/fineract` — the cwd the doc sets at `:148`** | **`/Users/buv/fineract`** | **`rc=1`, sources a path that isn't there, `GEREGE_GO_SOURCE` UNSET** |
| cwd `/tmp`, no checkout | `fatal: not a git repository` | `rc=1`, sources `/.softhouse/bin/go-env.sh`, UNSET |

**The overclaim to fix.** `reference-oracle.md:649` says the replacement *"answers correctly from **any
working directory**"*. It does not. It answers correctly from any working directory **inside this
repository**. In a document whose entire thesis is that a loose instruction manufactures sixty defects, an
overclaimed instruction is the wrong kind of sentence. Mechanical, ≤10 lines:

> `git rev-parse --show-toplevel` answers correctly from any working directory **inside this repository**,
> in the main checkout and in every isolated worker worktree, on any host. **It does not defend you against
> being in a *different* checkout** — run it from `/Users/buv/fineract` and it locates *that* repo. Outside
> any checkout it resolves to nothing and the `.` fails loudly.

**Not verified** — `safe.directory` / dubious-ownership (container running as another user) and a bare or
submodule checkout. I did not have a way to construct those here and I am not going to supply a plausible
result for them. All three failure modes I *could* construct converge on "source a nonexistent file", so I
expect but have not shown that those do too.

---

## 7. F-7 — the mislocation leaves a **fourth** `GEREGE_GO_SOURCE` state that no consumer models. **Route to T267.**

Severity: **MINOR now, MAJOR the moment T267 lands.**

`go-env.sh` defines exactly three states: `pinned` / `fallback-path` / `absent` [VERIFIED:
`go-env.sh:140,163,174`]. Every one of them implies *go-env.sh ran*, and each carries its stderr
announcement. A **mislocated activation line produces a fourth state — `GEREGE_GO_SOURCE` UNSET** — in
which none of that machinery ran at all: no banner, no "paths searched", no "THIS IS NOT THE PINNED
TOOLCHAIN". Measured `rc=1`, `GOROOT` UNSET, and **the calling shell continues** (`.` on a missing file does
not abort a shell without `set -e`).

**Why it is harmless today:** `grep -rn 'GEREGE_GO_SOURCE'` over `conformance.sh`, `bin/`, `guards/`,
`launchd/` returns hits **only inside `go-env.sh` itself** — **no live consumer reads the variable**
[VERIFIED]. It stops being harmless the moment **T267** puts it on stdout in the verdict block. **T267 must
treat UNSET as a refusal, not as a missing value**, or it will render a blank where the real answer is
"activation never happened."

## 8. F-8 — the document prescribes a **weaker** anchor than every executed site already uses.

Severity: **MINOR / design note.**

All three live consumers of `go-env.sh` anchor **`BASH_SOURCE`-relative**, which is immune to cwd, to being
in another repo, and to not being in a repo at all:

- `conformance.sh:399` — `REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"` → `:639` `. "$REPO_ROOT/.softhouse/bin/go-env.sh"`
- `guards/check-ledger-invariants.sh:42` / `guards/drive-red-ledger-invariants.sh:21` — same shape

[VERIFIED, all three]. So **the prescribed line is followed by nobody in the live harness**, and it is the
*less* robust of the two forms. `git rev-parse` is genuinely necessary only for an **interactive paste**,
where there is no `BASH_SOURCE`. The document does not draw that distinction and should: *"in a script, use
`$(cd "$(dirname "${BASH_SOURCE[0]}")/…" && pwd)`; the line below is for an interactive shell."* For
contrast, T238's `sweeplib.sh` — which T256 cites as convergent evidence, correctly [VERIFIED: `sweeplib.sh:3`] —
uses `git rev-parse` but **fails closed on it** (`sweeplib.sh:48-51`, `_sw_die 90 "no corpus root…"`) and
**prints the root it resolved**, so a mislocation is visible. The activation line does neither.

## 9. F-9 — the extractor `eval`s what it finds, with two greps as the only shape check.

Severity: **MINOR.**

Deleting only the `:END` marker makes extraction run away and collect **9 unrelated lines** of the
document — including Java source fragments — which `eval` then executes before the `ACT_N != 1` assertion
reds the run [VERIFIED: `evidence/43-marker-extractor-attacks.txt` case M2]. It fails **red**, but it fails
red *after* evaluating. A one-line reordering (refuse when `ACT_N != 1` **before** the first `eval`, as the
empty case already does with `exit 2`) closes it. The document is in-repo and trusted, so this is hygiene.

---

## 10. On T299 (not mine to fix — does my review change what should be done?)

**Yes, in one place, and it removes a risk T299's own brief flags.**

T299 item 1 warns: *"A rename must not break any instrument or pin that references the old path BY PATH:
grep for it first, including `HOSTSTATE_PIN_TEMP_ASSIGN_LIST`."* I ran that grep as part of F-2:
`grep -n 't256-verdict-predicate' .softhouse/conformance.sh .softhouse/tasks.json .softhouse/bin/*.sh
.softhouse/guards/*.sh` → hits **only in `tasks.json`** (4 lines: `:2372, :3093, :3515, :3825` `files_hint`
entries plus the T299 description). **`conformance.sh` does not pin it** — neither
`HOSTSTATE_PIN_TEMP_ASSIGN_LIST` nor `FAILOPEN_PIN_FILE_LIST` contains it, and `t256-toolchain-population`
is likewise absent from `conformance.sh`. **The rename is pin-safe**; only `tasks.json` `files_hint` rows
need updating. That is the exact trap T256 identified for the *other* population, so it was right to check —
and it does not bite here.

T299 item 2 (bare `50-failopen-lint.py` dirties a tracked file) is **unchanged** by this review and I agree
with its framing. One reinforcement: `conformance.sh:1560-1565` already diverts the JSON to `mktemp` with
an explicit comment (*"a harness that rewrote a tracked file on every graded run would dirty the tree it is
grading"*), so the **graded** path is safe; only the bare human invocation is not. That is precisely the
P-45 shape T299 names, and making the default safe rather than documenting the variable is the right call.

---

## 11. What I checked and found NOTHING wrong with

So that silence is distinguishable from not looking:

- Every arithmetic and population figure in the T256 handoff that I could re-derive — **all reproduce**.
- Frozen adapter contract: **untouched**; no `DEC-n` changed; no Go, no `nexus/`.
- Scope partition respected: `conformance.sh`, `admit.go`, `fire-program.sh`, `go-env.sh` all untouched by
  T256, exactly as it claimed.
- The three checkable citations T256 offered: `capture/t253-portability/instruments/30-d2-red-drive.sh:34`
  really does preserve the old hardcoded body as `OLD_ENV_BODY` [VERIFIED];
  `reviews/a2-34-review-a2-15/run-bar.sh:11` really does `cd` into worktree `agent-ac008956278f2d6ea`, which
  **does not exist** [VERIFIED, `ls`], so it is already unrunnable; `t238-failopen/instruments/sweeplib.sh:3`
  really does document the same self-locating shape independently [VERIFIED].
- Fail-closed behaviour of the drive on the two mutations that *do* red it: markers deleted → `exit 2`
  REFUSING; two fenced blocks → red. Both correct.
- `load_toolchain` in `conformance.sh:644-648` fails **closed** (`exit 2`, *"the harness is unusable. This is
  NOT a pass"*) when no `go` reaches PATH — the live path is not affected by any of the above.
- Bar re-run twice, unpiped, staged, with `bash`. Both runs exit 0, probe present, 46/7884.
- Tree left clean; `.softhouse/reference-oracle.md` restored to `HEAD` after both mutations.

## 12. What I tried and could NOT show

- I could **not** find a live execution path to any of the 60 archived instruments (attack 2 succeeded for
  T256, not for me).
- I could **not** construct `safe.directory` / dubious-ownership or bare/submodule cases for the
  self-locating line, and I am not supplying a guess for them.
- I did **not** run anything on a non-Darwin host. T256's "not proven" list on that point is accurate and I
  did not narrow it.
- I did **not** re-derive the money math, because **T256 touches no money path** — the diff contains no
  monetary value, no schedule, no ledger, no vector. Verified by the non-negotiable grep in §Scope.

---

## Follow-ups this review raises

| # | severity | what | where |
|---|---|---|---|
| F-3 | MAJOR | wire `30-portability-red-drive.sh` into `conformance.sh`'s graded path, or the convention enforces nothing (P-45) | `conformance.sh` — a partitioned file, so a task of its own |
| F-4 | MAJOR | the drive grades **one fenced line**, not the marker region and not the document; assert on the whole BEGIN…END region and add a document-wide "only one activation prescription" arm | `.softhouse/capture/t256-toolchain-population/instruments/30-portability-red-drive.sh` |
| F-6 | MICRO-FIX | delete the "any working directory" overclaim at `reference-oracle.md:649`; and `:148`'s `cd /Users/buv/fineract` now sits nine lines above a self-locating invocation it breaks | `.softhouse/reference-oracle.md` (outside this review's files_hint) |
| F-7 | route | **T267** must treat `GEREGE_GO_SOURCE` **UNSET** as a refusal, not a missing value | T267 |
| F-8 | MINOR | say in the document that scripts should anchor `BASH_SOURCE`-relative and that the prescribed line is for an interactive shell | `.softhouse/reference-oracle.md` |
| F-9 | MINOR | refuse `ACT_N != 1` **before** the first `eval`, not after | `30-portability-red-drive.sh` |
| — | note | T299's rename is **pin-safe**; only `tasks.json` `files_hint` rows reference `t256-verdict-predicate` | T299 |

---
---

**PART B of this review is in `PART-B.md` beside this file.** It was written by a resumed T298 session at a later commit and RE-DERIVES every load-bearing claim above with its own instruments. Read the FINAL VERDICT at the end of `PART-B.md`; it supersedes the verdict block at the top of this file, which it confirms rather than contradicts.
