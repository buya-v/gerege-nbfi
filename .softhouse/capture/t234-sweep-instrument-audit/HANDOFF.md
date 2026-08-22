# T234 — audit of every committed sweep instrument under `.softhouse/`

**Branch:** `softhouse/T234-sweep-instrument-audit`. **Role:** analyst / auditor.
**Date:** 22 August 2026. **Depends on:** `T232`.

**Fork point — CORRECTION TO THE BRIEF, AND A THIRD DATA POINT FOR P-71.** The brief named
`8611e754` as the fork point, "`git rev-parse HEAD` at the moment of dispatch, verified by the
driver". Measured in this worktree:

```
git rev-parse HEAD          = 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3
git merge-base HEAD main    = 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3
```

`2d41838` is **two commits behind** the stated `8611e754` — `git log 2d41838..main` shows
`8611e75` ("register A2-34…") and `f84d0f5` ("wave 1 dispatched: A2-15, T234, T219, T216 —
fork point 8611e754") sitting between them. And `2d41838` is **exactly the commit this session's
opening `gitStatus` reported as `main`'s tip.**

So for T234 the worktree forked from **the session-start commit**, which is P-71 **as originally
written** — the rule the brief told me had been "falsified last fire", and which the driver has since
replaced twice (`251be22`: *"P-71 SECOND CORRECTION — both fork-point rules now falsified"*).

**Neither rule is right, because the question is malformed.** "Session-start" and "dispatch commit"
coincide whenever the driver commits nothing between the two, and diverge whenever it does — which is
exactly what happened here: the driver registered A2-34 and the wave *after* the session snapshot but
*before* dispatch. The only sound instruction is the one every worker can execute unaided:
**`git merge-base HEAD main`, measured in your own worktree, and stated in the handoff.** A driver
should stop asserting the fork point in the brief at all; it has now been wrong three fires running,
in three different directions.

Everything below is measured at `2d41838` unless a rev is stated.

**Vector store in my tree:** `git rev-parse HEAD:.softhouse/vectors` =
`73c3ea7b43dd75f04884072719a87fc8e1d255c1` — **UNCHANGED**, as required. I authored nothing under
`.softhouse/vectors/`.

**Everything in this document is measured on macOS 25.5.0 / arm64, Apple Git 2.50.1 (Apple Git-155),
BSD grep 2.6.0-FreeBSD, ugrep 7.5.0, python3 3.9.6. `[UNVERIFIED]` off this machine** — the engine
readings below are *the whole subject*, and they are properties of these binaries.

---

## 0. Headline

Three things, in descending order of how much they should change what the driver does next.

1. **The program already knew.** `P-53` in `.softhouse/patterns.md:959-985` says, verbatim, *"`\b` is
   not a word boundary in POSIX ERE"* and *"a count produced by a regex sweep is only quotable
   together with the engine that produced it… 'The sweep found N' is not a measurement; 'Python `re`
   found N' is."* `P-12` at `.softhouse/patterns.md:1305-1309` records a **second**, independent
   measurement of the identical defect: *"the first grep was WRONG: `git grep -E '\bP-5\b' <commit>`
   returned **0 hits** on a file that provably contains the string."* T232 re-discovered, at real
   cost, a pattern that has been in force and correct for two runs. The defect is not that the
   knowledge was missing; it is that **it was filed under a pattern about ID collisions and a pattern
   about guard classifiers, where nobody writing a sweep would look.**

2. **The escape defect is real but SMALLER than the brief assumes — and a different, TOTAL failure is
   sitting on the instrument behind DEC-2's ratification.** Of 4,508 search invocations under
   `.softhouse/`, **10** carry an engine-dependent escape under an engine that voids it, and **8 of
   those 10 are the write-ups documenting the defect itself.** Only **one live instrument** actually
   loses recall to it (`r11-hygiene.sh`, 61 of 64 hit lines — §4). Meanwhile **A2-33's `sweep.sh`, the
   sweep behind the rev-5 review that RATIFIED DEC-2, prints `(no hits)` for all 34 of its patterns
   and exits 0 without searching a single byte** (§3.2). That is the same invisible-failure class, but
   total rather than partial, and it is on the more load-bearing artefact. **And A2-33 is the
   best-calibrated sweep in the entire chain** — it committed two-engine recall transcripts with
   `MISSES=0` and explicitly audited its own patterns for `\b\d\s\w` (§3.2.1). The failure is one
   unguarded `cd`, not a lapse of care, so **the remedy is a sweep harness, not another pattern
   telling reviewers to be careful.**

3. **A multi-line matcher has now been run against this repo — the first time (closes `FU-T227-2`).**
   **743** matches of the retracted-claim concept **span a newline** and were therefore outside every
   sweep this program has ever run. **64** of them are in live artefacts. I opened all 64. **None is a
   new live restatement of the retracted claim** — every one is a labelled retraction, a correctly
   attributed quotation, or an unrelated use of the same English (§6). That is a *calibrated* negative,
   which is what T224's was not.

---

## 1. The engine matrix — four engines, four answers, measured

`instruments/00-engine-baseline.sh`, `01-escape-matrix.sh`, `02-escape-matrix-fix.sh`;
transcripts `00`, `01`, `02`.

**T232 said three engines. There are four, and the fourth is the one that matters most for scripts.**

| escape | `git grep -E` | `git grep -P` | `/usr/bin/grep -E` (BSD 2.6.0) | ugrep 7.5.0 `-E` | python3 `re` |
|---|---|---|---|---|---|
| `\b` | **literal `b`** | word boundary | **word boundary** | **word boundary** | word boundary |
| `\d` | **literal `d`** | digit class | **digit class** | *[UNVERIFIED]* | digit class |
| `\s` | **literal `s`** | whitespace | **whitespace** | *[UNVERIFIED]* | whitespace |
| `\w` | **literal `w`** | word char | **word char** | *[UNVERIFIED]* | word char |

Evidence, self-calibrating (a positive and a negative control in one pair), repo-wide at `2d41838`:

```
git grep -E '\balance column'    lines=218  files=101   ==  unanchored 218/101  -> \b read as literal b
git grep -E '\bbalance column'   lines=0    files=0                             -> searched "bbalance column"
git grep -P '\balance column'    lines=0    files=0                             -> real boundary
git grep -P '\bbalance column'   lines=218  files=101                           -> real boundary
git grep -E 'a\db' 341   /  -P 2571        git grep -E 'a\sb' 0 / -P 1585      git grep -E 'a\wb' 0 / -P 51675
```

**Two corrections to T232, both material:**

- **`/usr/bin/grep -E` — BSD grep — HONOURS all four escapes.** T232 recorded that `grep` on `PATH`
  is ugrep. That is true *in the agent's interactive shell*, where the Claude Code harness installs a
  shell **function** wrapping ugrep. It is **false inside a script**: `BASH_FUNC_grep` is not
  exported, so a `#!/usr/bin/env bash` sweep gets `/usr/bin/grep`, BSD grep 2.6.0-FreeBSD
  [VERIFIED: transcript `00`, `declare -F grep` → "NOT a function in this script env"; `env -i
  /bin/bash -c 'command -v grep'` → `/usr/bin/grep`]. **Every committed `.sh` sweep in this repo that
  writes `grep -E '\b…'` is therefore SOUND, not void.** That is most of them, and treating them as
  void would be a false alarm at scale.
- **`grep -P` DOES NOT EXIST here.** BSD grep rejects `-P` with `exit 2` and a usage message on
  stderr. A caller redirecting stderr and not checking `$?` gets **empty output and no warning** —
  indistinguishable from "no matches". This is a *fifth* silent-zero mechanism, and it is not in P-53,
  P-12 or P-72.

**T232's `= 14` does not reproduce and I could not reconcile it.** `git grep -E 'balance column'` at
`90c21d6` measures **81 files / 162 hit lines**; at `2d41838`, **101 / 218**; scoped to `.softhouse`,
**97 / 213**. None is 14. `git grep -c` emits one `path:count` line per file, so a bare `-c` read as a
single number is neither files nor lines; I suspect that, but **I did not reproduce 14 under any scope
I tried and I am not asserting the cause.** The *shape* of T232's finding is confirmed by my own
independent measurement above; only its scalar is unreconciled. **`[UNVERIFIED]` — flagged for the
driver, not resolved.**

---

## 2. Census — how I enumerated, and what the numbers are

Two independent programs (P-58), named, reconciled. `instruments/11-census.py` (broad) and
`12-sweep-census.py` (focused). Corpus: **4,800** git-tracked files under `.softhouse/` at `2d41838`,
this audit directory excluded.

- **PROGRAM A — invocation-site.** `git grep -l` pre-filters to files containing a search-engine token;
  those are parsed line by line and the engine is derived **from the invocation's own flags**, never
  from the author's prose. → **649** candidate files, **4,508** invocation sites.
- **PROGRAM B — self-declaration.** Files that name themselves a sweep/census/scan/enumeration, or
  whose text asserts a closed population. → **151** files. A-only 566, B-only 68, both 83.

Broad engine distribution over all 4,508 sites:

| engine | sites |
|---|---|
| BSD grep BRE (script) / ugrep BRE (interactive) | 3081 |
| ugrep, explicit | 592 |
| BSD grep `-E` / ugrep `-E` | 513 |
| python `re` | 166 |
| `git grep` BRE (default) | 75 |
| **`git grep -E`** | **59** |
| `git grep -P` | 21 |
| `grep -P` → nonexistent option | 1 |

**166** sites carry an engine-dependent escape. **Of those, 10 sit under `git grep -E`/BRE and are
therefore VOID; the rest are under engines that honour the escape.**

Applying the focused sweep predicate (stated in `12-sweep-census.py`'s docstring so what it excludes
is visible) gives the audited population: **94 artefacts — 60 script instruments, 34 prose-only
records.**

---

## 3. Verdicts — the named suspects

Re-run verbatim, unmodified, today: `instruments/20-rerun-dec2-sweeps.sh`, transcript `20`.

| instrument | engine actually invoked | escapes | verdict | what it CLAIMED to close |
|---|---|---|---|---|
| `.softhouse/reviews/a2-31-dec2-rev4/probe-sweep.sh` | `git grep -i -E` ×1, `git grep` BRE ×2, BSD `grep -v` ×2 | **none** | **SOUND on escapes; UNREPRODUCIBLE** | DEC-2 rev 4: every claim rev 4 says it retracted, repo-wide, classes R1–R6 |
| `.softhouse/handoff/…/A2-32-evidence/sweep.sh` | `git grep -n -i -E` | **none** | **SOUND on escapes; UNREPRODUCIBLE** | DEC-2 rev 4/5: **"the population is closed"** — 27 patterns, 2,246 hit lines |
| `.softhouse/reviews/a2-33-dec2-rev5/sweep.sh` | `git grep -n -I -i -E`, BSD `grep -n -i -E` | **none** | **SOUND — calibrated on 2 engines, `MISSES=0` (§3.2.1); UNREPRODUCIBLE AND FAILS OPEN** | DEC-2 rev 5, the **RATIFYING** review: F-1 and F-2 claim classes, 34 patterns |
| `T224`'s nine terms | **none — no script was ever committed** | `\b` ×2 | **UNAUDITABLE** (§5) | *"no fourth or fifth surviving live assertion of the claim exists in this repository"* |
| `T227`'s re-run sweep | `/tmp/t227-sweep.sh` + `/tmp/t227-binary-sweep.sh` — **both gone** | unknown | **UNAUDITABLE** | why T224 missed; 4,813 files; binary sweep 0 hits |

**None of the three DEC-2 sweeps carries an engine-dependent escape.** The `\b` hypothesis in the
brief does **not** void them. What voids them is different and worse.

### 3.1 All three hard-`cd` into worktrees that no longer exist

```
GONE  agent-a3fcb4c7f1ea451ee   (A2-31 probe-sweep.sh, line 15)
GONE  agent-a356a016636abdd7e   (A2-32 sweep.sh,       line 8)
GONE  agent-a5244bad2b6814a39   (A2-33 sweep.sh,       line 14)
```
[VERIFIED: transcript `20`; the 28 live worktrees under `.claude/worktrees/` contain none of them.]

Run today, verbatim:

- **A2-31** → `exit 1`, one line of output. Fails **closed**. Loud, safe.
- **A2-32** → `exit 9`, one line of output. Fails **closed**. Loud, safe.
- **A2-33** → **`exit 0`, 136 lines of output, `(no hits)` printed for 34 of 34 patterns, having
  searched nothing.** Fails **OPEN.**

### 3.2 A2-33 — the one that matters

```bash
run() {
  ...
  ( cd "$WT" && git grep -n -I -i -E "$re" -- . ) || echo "   (no hits)"
}
```
`$WT` is a dead worktree. `cd` fails, `&&` short-circuits, the subshell exits non-zero, and the `||`
arm prints **`(no hits)`**. Every pattern. `set -u` does not catch it; there is no `set -e`, no `cd ||
exit`, no post-condition. The script exits 0.

Measured [transcript `20`]: `patterns declared: 34` / `patterns reporting "(no hits)": 34` /
`actual match lines emitted: 34` — all 34 of those "match lines" being the `(no hits)` string itself.

**Scope this precisely, because the distinction is the whole point.** This does **not** show that
A2-33 got no hits when it ran live in its own worktree; `sweep-output-live-population.txt` is
committed alongside at **6,406 lines**. What it shows is that **the instrument behind DEC-2's
ratification is not re-runnable, and re-running it produces a clean, total, exit-0 false negative** —
so any later auditor who re-runs it to check the ratification is handed "the population is closed"
by a script that never opened a file. That is the exact failure T234 was raised to find, one
mechanism over from the one it was raised to look for.

### 3.2.1 A2-33 IS THE BEST-METHODOLOGY SWEEP IN THE CHAIN, AND IT STILL FAILS OPEN

I expected to find carelessness and found the opposite. A2-33 committed two calibration transcripts
I did not know existed until I opened its evidence directory:

- `sweep-recall-calibration-gitgrep.txt` — states its engine (`git version 2.50.1 (Apple Git-155)`),
  its flags (`git grep -n -I -i -E`), and, **in terms**, *"no `\b`, `\d`, `\s` or `\w` in ANY pattern
  above"*. Recall against **17** ground-truth lines: **`MISSES=0`**.
- `sweep-recall-calibration-ugrep.txt` — the **same patterns re-run on a second engine**, recall
  against the 15 F-2 ground-truth lines: **`MISSES=0`**.

So A2-33 applied P-72 before P-72 was a week old, named its engine per P-53 rule 1, audited its own
patterns for exactly the escapes T234 was dispatched to hunt, and cross-checked two engines. **On
every axis this task was told to test, A2-33 passes.** Its sweep is `SOUND`.

**And it still hands a re-runner a total false negative**, because the failure is not in the regex
layer at all — it is one unguarded `cd` in a subshell whose non-zero exit is caught by a `||` arm that
prints reassurance. **The lesson for the driver is structural, not disciplinary:** no amount of
pattern hygiene fixes this, because pattern hygiene is not where it lives. A sweep instrument needs
its root passed in (`${1:-$(git rev-parse --show-toplevel)}`), a `cd … || exit`, and a
post-condition that refuses to report "no hits" when the corpus size it searched was zero. Asking the
next reviewer to be more careful would not have caught it; asking the *most* careful reviewer in the
chain did not catch it.

**One loose thread in A2-33's own evidence, unreconciled by me:** the two calibration files report
**81** unique rev-4 lines hit under `git grep` and **86** under ugrep — a **5-line engine divergence**
that A2-33 measured, committed, and (in these two files) does not explain. It does not affect the
`MISSES=0` recall result. I did not chase it. **`[UNVERIFIED]` — flagged, not resolved.**

### 3.3 The same shape elsewhere

`12-sweep-census.py` finds **6** sweep instruments with a dead hard-coded worktree path:
`a2-31-dec2-rev4/probe-sweep.sh`, `A2-32-evidence/sweep.sh`, `a2-33-dec2-rev5/sweep.sh`,
`reviews/A2-11/enumerate-corpus.py` (`agent-a3ac3d56d665ff7da`), `reviews/T184-evidence/t184-census.sh`
and `t184-sweep.sh` (both `agent-ae0f13a1bbf7c82f8`). **I checked the fail-open/fail-closed behaviour
of the three DEC-2 ones only; the other three are `[UNVERIFIED]` on that axis** (§8).

---

## 4. The one live instrument that genuinely loses recall to `\b`

`.softhouse/reviews/T138-evidence/r11-hygiene.sh:35` — T138's **P-24 hygiene check**, "every baseline
in T115's scripts must be a LITERAL sha":

```bash
git grep -n -a -E 'merge-base|main:|origin/main|rev-parse main|\bmain\b' "$T115" -- \
  .softhouse/capture/t91/ .../preconditions.sh .../preconditions-COPY.sh
```

The first four alternatives are literal and work. The fifth compiles to the literal string `bmainb`.
Measured over exactly the paths the script passes [`instruments/21-r11-recall-loss.sh`, transcript `21`]:

```
git grep -E  five-alternative=3   four-alternative=3   \bmain\b contributes= 0
git grep -P  five-alternative=64  four-alternative=3   \bmain\b contributes=61
git grep -E -c 'bmainb'  repo-wide = 0        git grep -E -c '\bmain\b' repo-wide = 0
git grep -P -c '\bmain\b' repo-wide = 17646
```

**PARTIALLY VOID: the instrument reported 3 hits where a sound engine reports 64 — a 95.3 % recall
loss (61/64)**, on a guard-hygiene check whose whole purpose is to catch a bare `main` reference.
I report it; I have not touched it — T138's review evidence is frozen (T114/T176), and the correct
disposition is a driver-registered follow-up, not a silent edit by me.

The other nine `git grep -E` + escape sites are: `RESUME.md:86`, `A2-33.md:66`, `T232.md:89/92/184`,
`patterns.md:1307/2100/2103`, `a2-33-dec2-rev5/REVIEW.md:168`. **Eight of the nine are prose
*documenting this very defect*** — `\balance column` quoted as the demonstration. `patterns.md:1307`
is P-12's own record of it. **None is a live instrument.** The escape defect's real live blast radius
in this repository is **one script**.

---

## 5. Prose-only sweeps — unauditable by construction

**34** artefacts record a swept population with no committed instrument behind it. Full list in
`transcripts/12-sweep-census.txt`; the load-bearing ones:

| artefact | closure-claim lines | what is unauditable |
|---|---|---|
| `handoff/…/T224.md` | 5 | the nine terms **and the engine**. No command, no script. |
| `handoff/…/A2-31.md` | 4 | narrative around a script that no longer runs |
| `handoff/…/T227.md` | 3 | `/tmp/t227-sweep.sh`, `/tmp/t227-binary-sweep.sh` — both gone |
| `handoff/…/A2-25.md` | 2 | *"`/usr/bin/grep -nE` over the whole ADR"* — engine named, invocation not |
| `handoff/…/A2-32.md` | 2 | *"I did not open all 2,246 hits individually"* |
| `patterns.md`, `tasks.json`, `program.json`, `RESUME.md` | 5/6/1/1 | driver restatements of the above |

**T227 named its own defect and then reproduced it.** `T227.md:124-127` says *"T224's sweep is not
reproducible. Its handoff records the terms… I could only transcribe them literally."* T227 then wrote
its own sweep **to `/tmp`** and did not commit it. It is now equally unauditable. `A2-25` is the best
of the set: it at least names `/usr/bin/grep -nE`, which under §1's matrix is a **sound** engine.

### 5.1 A CORRECTION to the brief, and to any restatement of T232 that generalises it

The brief states T224's *"stated widest net `\bnot exist\b` compiles under `-E` to a search for
`bnot existb` and matches ZERO files repo-wide."* **That is true of `git grep -E`. T224's own prose
says it did not use `git grep`:**

> *"the grep ran over everything `find .` would reach except `.git`"* [`T224.md:74-76`]

— i.e. a recursive `grep -r` typed into the Bash tool, which resolves to **ugrep 7.5.0**. Measured in
the interactive shell [transcript `31`-adjacent, run inline]:

```
ugrep -E 'balance column'   = 2      ugrep -E '\balance column'  = 0      ugrep -E '\bbalance column' = 1
ugrep -E 'not exist'        = 2      ugrep -E '\bnot exist\b'    = 1   (matched "not exist here", NOT "not existing here")
```

**Under the engine T224 actually implies, `\b` worked.** T224's term failed for the reason **P-72
Mechanism 1** already gives — the trailing `\b` on the inflected stem `exist` excludes `existing` —
**not because of the engine.** The engine defect and the right-anchor defect are two separate
mechanisms that happen to produce the same zero, and T232's measurement establishes the first without
establishing that it is what killed T224. **Both are real; only one killed T224.**
(*Caveat, stated rather than hidden:* T224's exact command was never recorded, so "ugrep" is an
inference from its prose, not an observation. **`[UNVERIFIED]`.**)

---

## 6. The re-run — sound instrument, calibrated, multi-line

`instruments/31-sound-sweep.py`, transcript `31`. **Engine: python3 `re` 3.9.6** (P-53 rule 1: the
count is quotable only with the engine). Chosen for one semantics across `\b\d\s\w`, for multi-line
capability, and because it reads the worktree directly and so is not blind to `.gitignore`d paths the
way the Bash-tool `grep` function is (`.gitignore:2` = `.claude/worktrees/`; the mechanism is already
recorded in `patterns.md:704-709`).

### 6.1 Calibration first (P-72) — and it reproduces T227 independently

| known positive @ `90c21d6` | T224's 9 terms | T234 sound net |
|---|---|---|
| `.softhouse/guards/ledgerguard/main.go:1` — the survivor T224 missed | **0 / 9** | **5 / 6** |
| `.softhouse/conformance.sh:1116` — the site T224 was **handed by line number** | **0 / 9** | **3 / 6** |

**`CALIBRATION VERDICT: PASS.`** T227's and T232's central measurement — zero recall on the positive
already in hand — is now reproduced by a third, independently written instrument. The sound net's
negatives below are therefore meaningful; T224's were not.

### 6.2 Live re-run at `2d41838`

Whole tracked worktree, **4,865** files, 25 skipped (binary or >4 MB). Six concept classes, none
right-anchored on an inflected stem, all gaps crossing newlines:

```
S1-fwd     hits=525 files=155     S4-441      hits= 56 files=17
S2-rev     hits=499 files=151     S5-records  hits= 48 files=14
S3-bare    hits=466 files=199     S6-noguard  hits= 44 files=12
```

### 6.3 Multi-line — the first time (closes `FU-T227-2`)

**743 matches span a newline** across 161 files. **No line-oriented sweep in this chain — T224's,
T227's, T232's, A2-31's, A2-32's, A2-33's — could have found any of them.** Concrete examples of the
retracted claim itself, split across a line break:

```
docs/adr/DEC-2-gl-accounting-adapter.md:124   "No\nguard for either"
.softhouse/handoff/…/A2-28.md:53              "records as not\nexisting"
.softhouse/handoff/…/A2-28.md:410             "records as not\n  existing"
.softhouse/handoff/…/A2-31.md:581             "records as NOT\n  EXISTING"
.softhouse/patterns.md:2089                   "records as not\nexist"
```

**Triage** (`instruments/32-triage-live.py`, transcript `32`): 743 = **64 in live artefacts** +
**679 in frozen evidence**. I opened **all 64**. Live rollup: DEC-2 21, `patterns.md` 17,
`conformance.sh` 7, `ledgerguard/main.go` 5, `gates.md` 4, `tasks.json` 3, `program.json` 1,
`nexus/**` 6.

**Result: NO new live restatement of the retracted claim.** Every one of the 64 is:

- a **labelled retraction or historical explanation** — `DEC-2:124` is inside the paragraph
  *"Why revision 3 was rejected"*, quoting F-1 in the past tense; `ledgerguard/main.go:1-10` is
  T227's `⚠ CORRECTION` block, which says in terms *"That was TRUE THE DAY A2-18 WROTE IT and it is
  FALSE NOW"*; `conformance.sh:1173-1174` is the same, self-correcting in the next clause;
  `gates.md:139` is the driver's record of A2-31's three survivors;
- or **an unrelated use of the same English** — `nexus/internal/apps/ledger/errors.go:141` and
  `resolve.go:86` are GL-account-not-found messages; `gates.md:1871` and `:2939` are about missing
  *capture mechanisms*, not about the guard.

A quotation correctly attributed is not a defect and a frozen transcript is evidence, not a bug
(T114/T176). **The population is, as far as a calibrated multi-line instrument can see, closed — and
this is the first time that sentence has been backed by an instrument whose recall was measured
before the sentence was written.**

---

## 7. Live claims for the driver to register

Reported, not fixed — `gates.md`, `vectors/`, `conformance.sh` and `patterns.md` are held by other
workers this fire.

| # | file:line | instrument that found it | claim |
|---|---|---|---|
| **L-1** | `.softhouse/reviews/a2-33-dec2-rev5/sweep.sh:14` | `20-rerun-dec2-sweeps.sh` | Fails **OPEN**: dead `cd` inside `( … ) \|\| echo "(no hits)"` → exit 0, `(no hits)` × 34, nothing searched. **The instrument behind DEC-2 rev-5 ratification** — and, per §3.2.1, the *best-calibrated* sweep in the chain. The fix is structural (root as `$1`, `cd \|\| exit`, refuse to report a negative over an empty corpus), not disciplinary. |
| **L-1b** | `.softhouse/reviews/a2-33-dec2-rev5/sweep-recall-calibration-{gitgrep,ugrep}.txt` | manual read | A2-33's own transcripts report **81** unique rev-4 lines under `git grep` vs **86** under ugrep. A measured 5-line engine divergence, committed, unexplained in those files. Does not affect its `MISSES=0`. **`[UNVERIFIED]`, not chased.** |
| **L-2** | `.softhouse/reviews/T138-evidence/r11-hygiene.sh:35` | `21-r11-recall-loss.sh` | `\bmain\b` under `git grep -E` → literal `bmainb`. **61 of 64 hit lines lost (95.3 %)** on a P-24 hygiene check. |
| **L-3** | `.softhouse/patterns.md:959-985` (P-53) and `:1305-1309` (P-12) | `11-census.py` + manual read | The `\b`-under-ERE defect was **measured and written down twice before T232**, filed where no sweep author would look. P-72/P-73 should cross-reference P-53; P-53 should gain the `git grep -E` row and the **`grep -P` = nonexistent option** row. |
| **L-4** | `A2-31 probe-sweep.sh:15`, `A2-32 sweep.sh:8`, `A2-33 sweep.sh:14`, `A2-11/enumerate-corpus.py`, `T184-evidence/t184-census.sh`, `t184-sweep.sh` | `12-sweep-census.py` | **6** committed sweep instruments hard-`cd` into deleted worktrees. All are unreproducible; one fails open. A sweep instrument should take its root as `$1` defaulting to `git rev-parse --show-toplevel`, and must `cd … \|\| exit`. |
| **L-5** | `T224.md` (no script), `T227.md` (`/tmp`, gone), + 32 more | `12-sweep-census.py` | **34** prose-only sweep records. A closure claim whose instrument was never committed is uncheckable in principle. |
| **L-6** | brief for T234; any restatement of T232 | §5.1, ugrep measurement | T224's `\bnot exist\b` was **not** killed by the engine — its prose implies ugrep, where `\b` works. It was killed by the right-anchor (P-72 M-1). Correct this before it hardens into program lore. |
| **L-7** | `T232.md:89` | `02-escape-matrix-fix.sh` | T232's `= 14` reproduces at **no** scope I tried (81/162 at `90c21d6`; 101/218 at `2d41838`; 97/213 in `.softhouse`). Shape confirmed independently; **scalar unreconciled, `[UNVERIFIED]`**. |
| **L-8** | T234's dispatch brief; P-71 and both its corrections | `git merge-base` in this worktree | My fork point is `2d41838` = the **session-start** commit, not the briefed dispatch commit `8611e754`. Third fire, third answer. The two rules coincide unless the driver commits between snapshot and dispatch — which it did here (`8611e75`, `f84d0f5`). **Drop the fork-point assertion from dispatch briefs; require each worker to measure and state `git merge-base HEAD main` instead.** |

**No `user` gate is implicated.** Nothing here touches cutover, licensing, regulatory sign-off, or the
frozen contract.

---

## 8. What I skipped, and why (P-40)

Counted, not estimated.

1. **4,342 of 4,508 invocation sites not opened individually.** I opened the **166** carrying an
   engine-dependent escape, and of those the **10** under a voiding engine. The remaining 4,342 carry
   no engine-dependent escape, so the defect under audit cannot apply to them. Their engine
   classification is mechanical (`11-census.py`) and stands unopened.
2. **57 of the 60 script instruments not read line by line.** I read exactly three end to end —
   `a2-31-dec2-rev4/probe-sweep.sh`, `A2-32-evidence/sweep.sh`, `a2-33-dec2-rev5/sweep.sh` — plus
   A2-33's committed evidence directory, and I skimmed `conformance.sh`. The other 57 are covered by
   the census's **mechanical** engine and dead-`cd` analysis only, which is a weaker check than
   reading them. (`r11-hygiene.sh`, §4, is **not** among the 60: it fails the focused sweep predicate
   and was caught by the broad census instead. Two programs, and only one of them found the single
   live escape defect in the repository — which is the argument for P-58 in one line.)
3. **Fail-open/fail-closed behaviour tested for 3 of the 6 dead-`cd` instruments.** `A2-11/enumerate-corpus.py`,
   `t184-census.sh` and `t184-sweep.sh` are `[UNVERIFIED]` on that axis. **If any of the three fails
   open like A2-33, it is a second L-1.** This is the largest single gap I am leaving.
4. **679 of 743 multi-line hits not triaged individually** — all in frozen handoffs, reviews and
   captured transcripts, excluded by the stated live/frozen predicate in `32-triage-live.py`. A hit
   there is evidence, not a defect.
5. **25 files skipped by the sound sweep** (binary or >4 MB). T227 walked 155 binary-ish files with
   `grep -a` and found 0; I did **not** repeat that, and my multi-line net has therefore **never been
   run against binary content**. `[UNVERIFIED]`.
6. **Scope was `.softhouse/`, as briefed.** Sweep instruments under `docs/`, `nexus/` or the repo root
   were not enumerated. The sound sweep's *corpus* was the whole repo; the *instrument census* was not.
7. **ugrep's `\d`/`\s`/`\w` readings are `[UNVERIFIED]`** — ugrep is reachable only through the
   interactive shell function, which a committed script cannot invoke, so I could not put those cells
   in a reproducible transcript. Only its `\b` reading is measured (§5.1), inline.
8. **T232's `= 14` unreconciled** (L-7). I tried repo-wide at two revs and `.softhouse`-scoped; I did
   not exhaustively search for a pathspec that yields 14.
8b. **A2-33's 81-vs-86 engine divergence not chased** (L-1b). Reconciling it means diffing its two
   committed hit sets line by line; I read the two calibration transcripts and stopped there.
9. **I did not re-run A2-32's 27 patterns or A2-31's R1–R6 against a sound instrument.** Both are
   SOUND on escapes and their committed outputs are non-empty; the defect I found in them is
   reproducibility, not recall. My own S1–S6 net (§6) covers the same concept independently and with
   measured calibration, which is the stronger check. **This is a deliberate substitution, not an
   omission — but it is a substitution, and I say so.**

---

## 9. BAR — observed in this worktree, at `2d41838`

`instruments/90-bar.sh` / `91-prove.sh`; transcripts `90-bar.txt`, `91-prove.txt`.

| item | required | observed |
|---|---|---|
| oracle probe line | PRESENT, `up` | **PRESENT**, `reference oracle (https://localhost:8443/…/health) probe = up` (`90-bar.txt:81`) |
| verdict | `PASS` exit 0 | **`VERDICT: PASS (exit 0)`**, `CONFORMANCE_EXIT=0` |
| parity vectors / cells | 46 / 7884 | **46 PASS 0 FAIL / 7884 graded** (93 ungraded) |
| inadmissible | 0 | **0** |
| harness errors | 0 | **0** |
| invariant violations | 0 | **0** |
| exemptions | 4 EXEMPTED, 4 GROUNDED, 0 UNGROUNDED, 0 UNDETERMINED | **4 / 4 / 0 / 0** |
| `--prove` | 23 / 0 | **`PROOFS: 23 passed, 0 failed`**, `PROVE_EXIT=0` |
| `go build` / `go vet` | 0 / 0 | **`BUILD_EXIT=0`, `VET_EXIT=0`** |
| `go test -count=1` | ok | **ok** (ledger, loanschedule, conformance) |
| `gofmt -l` | exactly `contract.go` | **`internal/apps/loanschedule/contract/contract.go`**, that file alone |
| `HEAD:.softhouse/vectors` | `73c3ea7b…` unchanged | **`73c3ea7b43dd75f04884072719a87fc8e1d255c1`** |

---

## 10. Contents

```
instruments/00-engine-baseline.sh     which engine each spelling of "grep" resolves to, script vs interactive
instruments/01-escape-matrix.sh       \b \d \s \w across four engines (the \d row here is BROKEN — see 02)
instruments/02-escape-matrix-fix.sh   repairs 01's \d control; reconciles T232's "= 14" (unreconciled)
instruments/10-census.py              first census attempt — KILLED at >4 min, superseded by 11. Kept: it
                                      is why the corpus is pre-filtered, and a killed instrument is evidence.
instruments/11-census.py              broad two-program census, 4,508 invocation sites
instruments/12-sweep-census.py        focused census under the stated sweep predicate, 94 artefacts
instruments/20-rerun-dec2-sweeps.sh   A2-31 / A2-32 / A2-33 re-run verbatim today
instruments/21-r11-recall-loss.sh     quantifies r11-hygiene.sh's 61/64 loss
instruments/30-sound-sweep.py         first sound-sweep attempt — KILLED (one `git show` per file)
instruments/31-sound-sweep.py         THE SOUND INSTRUMENT: python3 re, calibrated, multi-line
instruments/32-triage-live.py         743 multi-line hits -> 64 live, triaged
instruments/90-bar.sh, 91-prove.sh    BAR
transcripts/                          every run above, verbatim
evidence/census.json, sweep-census.json, sound-sweep-HEAD.json,
         multiline-only-hits.json, multiline-live-hits.json
```

`10-census.py` and `30-sound-sweep.py` are retained deliberately. Both were killed on timeout; both
are named as killed in this document. A deleted failed instrument leaves a handoff that reads as if
the first attempt worked.
