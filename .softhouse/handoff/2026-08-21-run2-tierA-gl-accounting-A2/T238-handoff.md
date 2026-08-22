# T238 — the dead-`cd` FAIL-OPEN class: characterised, made fail-CLOSED, driven RED

**Branch:** `softhouse/T238-failopen-dead-cd`
**Task:** T238 — "a re-run of A2-33's sweep prints 34/34 `(no hits)` and exits 0, which reads exactly like corroboration"

---

## 0. THE THING TO READ FIRST — WHAT THIS TASK DID *NOT* DO

**`DEC-2` revision 5 is RATIFIED and is NOT re-opened. `G-11`'s ratification is NOT undermined.
`docs/adr/` was READ ONLY and never written.** Amending a ratified DEC-n is a `user` gate and
nothing here approaches one.

`A2-33`'s sweep **ran, and it found things.** Its committed transcript
`sweep-output-live-population.txt` carries **34 patterns, ZERO `(no hits)`, 6334 hit lines**. That
transcript, and every other committed artefact in `.softhouse/reviews/a2-33-dec2-rev5/`, is
**byte-identical to what A2-33 committed**. The only file I changed there is the *instrument*,
`sweep.sh`, and the change is **labelled** in a new `CORRECTION.md` per **T114/T176**, which records
the original bytes' sha256 and the exact behavioural diff.

**The defect was REPRODUCIBILITY, not the result.** A sweep that fails OPEN on re-run is worse
than one that cannot run at all, because its silence corroborates whatever the reader already
believed.

---

## 1. FORK POINT — MEASURED, NOT ASSERTED (P-71, falsified twice in this program)

```
git merge-base HEAD origin/main   477dc2da0f9edf3922e7d29e689bc6473289befc
git rev-parse origin/main         477dc2da0f9edf3922e7d29e689bc6473289befc
git rev-parse HEAD (at fork)      477dc2da0f9edf3922e7d29e689bc6473289befc
```

All three identical. `git rebase origin/main` reported *"up to date"*; **no rebase was needed and
none was performed.** This run therefore **does not discriminate** between the session-start rule
and the dispatch rule — the two coincided. I report it as a **non-observation**, not as support for
either rule. The standing duty (measure, never assert) is unaffected.

**Vector store digest — UNCHANGED BY ME.** `git rev-parse HEAD:.softhouse/vectors` =
`8968c559fa613e8642ab030bd0a029c17d147054`, identical at my fork point and at my tip. I touched
nothing under `.softhouse/vectors/`, `nexus/`, `docs/adr/`, `.softhouse/conformance.sh` or
`.softhouse/gates.md`.

---

## 2. THE POPULATION — HOW I ENUMERATED IT, AND BOTH TERMS (P-67)

Instrument: `.softhouse/capture/t238-failopen/instruments/10-failopen-census.py`, over
`git ls-files`, this task's own directory excluded. Transcript: `transcripts/10-failopen-census.txt`.

```
tracked files in repository ................. 5022
tracked .sh + .py (my dir excluded) .........  846      (368 .sh + 478 .py)
of those, containing >= 1 SEARCH call .......  298      <-- the instrument population
carrying >= 1 fail-open mechanism ...........  262
THE LETHAL INTERSECTION (dead path AND a failure arm that PRINTS)  38
```

**`PR-1` FALSIFIED, and loudly.** I pre-registered (commit `000e16d`, before counting) that the
`.sh`+`.py` population was **100–250**. It is **846** — out by a factor of 3.4. Recorded because a
prediction that only ever confirms is not a prediction.

**My population is not T234's, and the difference is predicate width, not a T234 error.** T234
counted *sweep instruments* (94: 60 script, 34 prose-only) using a name/closure-claim predicate;
I counted *search instruments* (298) using "contains a search call". T234's dead-path detector was
**one regex over the literal string `/Users/buv/gerege-nbfi/.claude/worktrees/`**, which finds one
mechanism. Mine finds eight.

### The eight mechanisms, each measured

| | mechanism | instruments |
|---|---|---|
| M1 | dead absolute path (assigned or `cd`-ed into) | **69** |
| M2 | failure arm that **prints a reassurance** (`\|\| echo`, `\|\| true`) | 95 |
| M3 | glob that currently expands to nothing | 150 |
| M4 | `for x in $(...)` over an empty producer | 4 |
| M5 | search in a pipeline with no `set -o pipefail` | 171 |
| M6 | calls an engine that is not there (`ugrep` / `rg` / `grep -P`) | 16 |
| M7 | `.sh` with no `set -e` | 167 |
| M8 | **assert-without-measuring** — `cd <dead> && <search>` then an *unconditional* claim | **1** |

**`PR-4` CONFIRMED AND EXCEEDED.** I predicted ≥1 fail-open mechanism that is not a dead path;
there are **four** (M3, M4, M5, M6), each demonstrated in a scratch corpus in
`transcripts/30-pr4-nondead-mechanisms.txt`. All four emit an identical `(no hits)` **at exit 0**
over a corpus that **contains the string**. The class is not the dead `cd`; the dead `cd` is one
entry point to it.

**Honest caveat on the 69/38 figures:** they include container paths (`/work`) from Docker-based
capture rigs, which are legitimately absent on the host. Those are *unreproducible-on-this-host*,
not *defective*. The lethal-38 is an upper bound; the six instruments in §3 are measured
individually.

---

## 3. WHICH INSTRUMENTS FAIL OPEN — MEASURED BY EXECUTION, NOT BY READING

T234 named six dead-`cd` instruments and **tested three**. I ran all six verbatim from the repo
root, exactly as a later auditor would. Transcript: `transcripts/20-run-the-class.txt`;
per-instrument logs in `evidence/class-runs/`.

| instrument | exit | verdict |
|---|---|---|
| `a2-31-dec2-rev4/probe-sweep.sh` | **1** | FAIL-CLOSED (`cd … \|\| exit 1`) |
| `A2-32-evidence/sweep.sh` | **9** | FAIL-CLOSED (`cd … \|\| exit 9`) |
| `a2-33-dec2-rev5/sweep.sh` | **0**, 34 × `(no hits)`, 0 hit lines | **FAIL-OPEN / OPEN-SILENT** |
| `A2-11/enumerate-corpus.py` | **1**, traceback | FAIL-CLOSED (`subprocess … check=True`) |
| `T184-evidence/t184-census.sh` | **0** | **FAIL-OPEN / OPEN-WRONG-CORPUS** |
| `T184-evidence/t184-sweep.sh` | **0** | **FAIL-OPEN / OPEN-WRONG-CORPUS** |

`PR-2`, `PR-3`, `PR-5` all confirmed. (`PR-2` predicted A2-11 would fail closed via `os.chdir`
raising; it fails closed via `check=True` instead — right verdict, wrong mechanism, stated.)

### 3.1 The two T234 left untested fail open in a WORSE shape than A2-33's

A2-33 prints `(no hits)` 34 times. A careful reader may notice. **`t184-census.sh` prints a full,
plausible, confidently-formatted census over the WRONG TREE**, because its `cd` is bare — no `||`,
no `set -e` — so the script simply carries on in whatever directory it was invoked from.

Its committed transcript (`RED-GREEN-T184-review-of-T173.txt:307-318`) against my re-run today:

| | T184 committed | re-run at `000e16d` |
|---|---|---|
| `req` directories | 10 | 10 |
| `.json` bodies | **320** | **348** |
| `.req` files | **0** | **35** |
| `.java` files | **57** | **63** |
| directories | **20** | **24** |

**Four of five numbers changed and the instrument announced nothing.** The only evidence of failure
is a single stderr line at the very top — which any redirect discards, and which T234's own
re-runner discards (`> /tmp/… 2>&1` then `head -6`).

The irony is load-bearing: **T184 is the task that wrote *"A guard that inspects nothing passes
everything. This is an ERROR, not a pass (P-35)"*** — and its own census instrument does exactly
that.

### 3.2 A seventh instrument: T234's own re-runner has T234's own defect

`.softhouse/capture/t234-sweep-instrument-audit/instruments/20-rerun-dec2-sweeps.sh:6` hard-codes
`R=/Users/…/agent-a71e695cfa5bea70b` — **T234's own worktree**, now deleted. Re-run today it exits
**0**, reporting `exit=127 output lines=1` for all three sweeps and an empty `patterns declared :`.
**The instrument built to detect the fail-open class is in the fail-open class.** This is the
strongest single argument in the task for a structural remedy over a disciplinary one.

### 3.3 An eighth, found by T239, that MY FIRST CENSUS MISSED — reported against myself

The driver relayed T239's independent find: **`.softhouse/reviews/T138-evidence/r11-hygiene.sh:77`**

```bash
cd /tmp/T138-merge 2>/dev/null && \
  git grep -n -a -E '17 capture scripts|…' -- . | sed 's/^/   /'
echo "   (searched the MERGED tree)"
```

`/tmp/T138-merge` does not exist. `2>/dev/null` **hides the only evidence**, the `&&`
short-circuits so the search **never runs**, and the next line prints **`(searched the MERGED
tree)`** — a *positive assertion that a search happened* — then exits 0.

**My first census did not catch it**, because my dead-path regex matched only
`/Users|/home|/opt|/var` and this path is under `/tmp`. That is a recall gap in a recall
instrument — **the P-72 lesson turned back on me: I stated a scope and did not test whether the
scope was real.** I widened M1 to any `cd`-ed absolute path and added **M8** for this shape, which
is *not* the `|| echo` shape and which no earlier mechanism in my census would have caught. After
widening, my census finds it, and **M8 has exactly one instrument in the whole repository**.

`r11-hygiene.sh` is **outside my write scope** — it is frozen T138 review evidence (T114/T176) and
belongs to T239's finding. **Left as backlog, not diffed.** See §8.

---

## 4. THE FAIL-CLOSED MECHANISM, AND THE ARGUMENT FOR IT

### 4.1 The invariant

> **AN INSTRUMENT MUST NOT BE ABLE TO EMIT A NEGATIVE IT DID NOT MEASURE.**
> Equivalently: *"zero hits"*, *"zero corpus"* and *"no working engine"* are three different facts
> and must have three different exit codes. Every fail-open instrument collapses all three onto
> *"print a reassurance, exit 0"*.

### 4.2 Why discipline cannot be the remedy — the argument, not an assertion

**A2-33 is the best-calibrated sweep in this chain.** It published two-engine recall transcripts
with `MISSES=0`, named its engine and flags per P-53, and audited every one of its 34 patterns for
`\b \d \s \w` before P-72 was a week old. **On every axis T234 was dispatched to test, A2-33
passes** — I re-verified the pattern-audit claim myself and it is **true, 0 of 34** (§6).

And it still shipped a fail-open, because **the defect was not in the regex layer at all**. It was
one unguarded `cd` in a subshell whose non-zero exit was caught by a `||` arm that printed
reassurance.

**So "ask the next author to be more careful" was already tried, on the most careful author in the
chain, and it failed.** That rules out discipline. It also rules out a **library on its own**: a
library is adoptable, and anything adoptable is omittable by exactly the person who did not think
they needed it. A2-33 would have had to *remember* to use it.

### 4.3 So the mechanism is a LINTER FIRST, a LIBRARY SECOND

| | what it is | who has to remember |
|---|---|---|
| **the enforcer** | `instruments/50-failopen-lint.py` — grades every tracked `.sh`/`.py` | **nobody** |
| **the library** | `instruments/sweeplib.sh` — sourceable fail-closed preamble | the author |

A linter is different **in kind**. It does not ask the author to remember anything; it runs over
the tree afterwards and refuses instruments that can emit a negative they did not measure. The
author's carefulness stops being load-bearing. **The library is what the linter tells you to adopt;
it is not the fix.**

The linter grades in three tiers **derived from my measurements, not from taste** — because
`a2-31`'s measured behaviour proves a dead path alone is *not* fail-open:

* **Tier 1 — FAIL-OPEN, LIVE**: dead path **and** a printing failure arm. (`a2-33` before repair,
  `A2-32-evidence/sweep.sh`.)
* **Tier 2 — FAIL-OPEN-CAPABLE**: printing arm only; corpus reachable today, one deleted directory
  from Tier 1.
* **Tier 3 — UNREPRODUCIBLE but FAILS CLOSED**: dead path only. Safe to re-run — it exits non-zero
  — but its conclusion can never be re-checked. (`a2-31-dec2-rev4/probe-sweep.sh`, measured exit 1.)

It also carries an explicit **suppression marker** (`# lint-failopen: ok -- <reason>`), deliberately
verbose so it cannot be used lazily, and **every suppression in force is printed in the report** so
they never go quiet.

**The linter earned its keep on its first run: it flagged a `|| echo 0` swallow inside my own
repair of `sweep.sh`.** I fixed the code rather than weakening the rule.

### 4.4 P-45 — SAID LOUDLY, BECAUSE THIS PROGRAM NOW HAS FOUR INSTANCES

**The linter is NOT wired into `.softhouse/conformance.sh`**, because that file is held by **T243**
and **T226** and is outside T238's write scope. **An unwired guard is exactly the P-45 shape, and
shipping one silently would make a fifth instance.** So it is shipped with a RED drive, a GREEN
drive, this paragraph, and the exact wiring line for whoever holds `conformance.sh` next (§8).
**Nobody may cite it as an enforced control until it is wired.**

---

## 5. DRIVEN RED, THROUGH THE ROUTE THAT RUNS IT (P-22 / P-45)

`transcripts/40-red-drive.txt`, committed. Every failure mode is driven through `bash sweep.sh`,
which is how an auditor invokes it — not by hand.

```
BASELINE  the ORIGINAL, recovered from the LITERAL sha 477dc2da and run verbatim:
          exit=0    "(no hits)" lines=34    hit lines=34    -> NOTHING MEASURED

RED 1  not a git work tree                   exit 90   "(no hits)" lines 0   PASS
RED 2  git repo tracking ZERO files          exit 91   "(no hits)" lines 0   PASS
RED 3  calibration misses the known positive exit 92   "(no hits)" lines 0   PASS
RED 4  single-file mode, target absent       exit 90   "(no hits)" lines 0   PASS

GREEN  the live corpus                       exit 0
       34 patterns · 5000 tracked files · 17354 hit lines
       SWEEP CALIBRATE+: PASS — known positive matched 60 time(s)
       SWEEP CALIBRATE-: PASS — known negative matched 0 times
```

All 34 patterns return a **non-zero** hit count on the live corpus
(`evidence/red-drive/90-green-per-pattern-counts.txt`) — **no pattern in the set is dead.**

**ALL 34 PATTERNS ARE BYTE-IDENTICAL TO THE ORIGINAL.** The `^run ` lines of the original and the
repaired file both sha256 to `6895b1bf930023c1e05a72be564e5aaa7b0f70e9806d88a5e6784e92ec0e3cac`.

**A defect I introduced and am reporting rather than quietly fixing.** The first version of the
red-drive took its baseline from `git show HEAD:…`. Once the repair was committed, `HEAD:` resolved
to the **repaired** file, so the leg labelled *"ORIGINAL"* silently began running the new instrument
against itself. That is **P-24** (a baseline is a literal sha, never a moving ref) — and it is the
same family as the defect this task exists to fix: *an artefact reporting something other than what
its label claims*, appearing inside the instrument built to catch that family. Pinned to `477dc2da`.

The green hit count (17,354) is **not** comparable with A2-33's 6,334: the corpus has grown and now
contains T238's own transcripts, which quote these patterns.

---

## 6. ENGINE, FLAGS AND CALIBRATION FOR EVERY SWEEP (P-33 / P-53 / P-72)

Transcript: `transcripts/00-engines.txt`, corpus `evidence/engine-calibration-corpus.txt`.

### 6.1 A committed script has THREE engines here, not five

I measured this **in the environment a committed script actually runs in**, which is not the
environment of the agent's Bash tool — and that difference is the finding.

| engine | available to `bash script.sh`? | `\b` |
|---|---|---|
| `/usr/bin/grep -E` (BSD 2.6.0-FreeBSD) | yes | honours it |
| `git grep -E` (git 2.50.1) | yes | **literal `b`** |
| `git grep -P` (PCRE2) | yes | honours it |
| `perl` 5.034001 | yes | honours it |
| `/usr/bin/grep -P` | **no** — `invalid option`, exit 2, silent | — |
| `ugrep` | **ABSENT** — not on `$PATH`, not in `/opt/homebrew`, not in `/usr/local` | — |
| `rg` 14.1.1 | **NO** — see below | honours it |

**This corroborates the driver's mid-flight correction independently, and refines it.** `rg` is
*not* a system binary here: it resolves to a **shell function installed by a Claude Code shell
snapshot** that re-execs the `claude` binary with `ARGV0=rg`. Measured:

```
plain bash -c : rg NOT FOUND
plain bash -c : rg --version exit=127
```

So `rg` is sound **for an agent typing into the Bash tool** and **unavailable to a committed
script**. A committed `.sh` that calls `rg` under a `||` arm is a fail-OPEN by M6.

**The filing dimension, since the task asked me to name it.** This is **not new knowledge**:
`T108` established it, `t91/prove-guards.sh:170-183` documents it correctly in an `else` branch,
and T234's `11-census.py:21` states *"ugrep is NOT exported into scripts"*. What is wrong is the
**standing instruction in `RESUME.md`**, which says *"FIVE engines … ripgrep 14.1.1 is present"*
and **drops the qualifier**. Three artefacts record the fact; the summary that everyone reads
does not. **A filing failure, not a knowledge gap** — the same shape T232 hit with P-53.

### 6.2 `git grep -E` does not merely LOSE hits — it FABRICATES them

The driver's correction, reproduced independently on my own committed corpus:

```
git grep -nE  \bmain\b   -> …corpus.txt:2:the bmainb literal is a decoy…
git grep -nE  bmainb     -> …corpus.txt:2:the bmainb literal is a decoy…
git grep -nP  \bmain\b   -> …corpus.txt:1:the main branch was measured
/usr/bin/grep -nE \bmain\b -> 1:the main branch was measured
```

The ERE and the literal `bmainb` return **byte-identical output**, and it is the **decoy** line, not
the true one. **P-53 and P-12 record this as recall loss only. It is worse: `git grep -E` can
return a hit that is not there.**

The consequence is sharp and I have built it into both the library and the repaired instrument:
**"I got hits, so my rig works" is NOT a valid calibration** — a positive-only calibration passes
happily on a fabricating engine. So `sweeplib.sh` and `sweep.sh` now require **both**
`sweep_calibrate` (a known positive must be found) **and** `sweep_anticalibrate` (a known negative
must return zero), and `sweep_run` refuses to run until both have passed. The anti-calibration token
is **assembled at run time** so its literal never appears in the file — a known-negative written out
verbatim would match its own source and abort every run.

### 6.3 The T224 exoneration is now UNVERIFIED, and I have not restated it

`RESUME.md` exonerates T224's sweep with *"it ran under ugrep where `\b` works"*. **ugrep is not on
this machine.** That exoneration is therefore **unverified**, exactly as T239 flagged. I treat
T224's *"two mechanisms, one zero"* as **one measured mechanism** (right-anchoring an inflected
stem) **plus one unverified claim about the engine**, and I have not restated it as settled
anywhere in this handoff or in any artefact I committed.

### 6.4 The multi-line axis — run, and it comes back NEGATIVE

Every sweep in this program has been line-oriented. Mine was not:
`instruments/60-multiline-sweep.py`, **python3 `re`, `DOTALL|IGNORECASE`, whole-file**, over 1262
tracked `.sh`/`.py`/`.md`.

Its calibration is **discriminating by construction**: it requires the known positive (split across
a newline) to be **found multi-line** *and* to be **MISSED by the line-oriented control**. If the
control also matched, the calibration would prove nothing and the script aborts 92.

```
CALIBRATION : PASS — split known positive found multi-line; line-oriented control finds it: False
MULTILINE-RESULT: corpus=1262 patterns=5 multiline_only_matches=1 calibration=PASS
```

**`PR-7` is confirmed on its letter and falsified in substance.** The single multi-line-only match
(`T138-evidence/r4-guards-red.sh:13`) is a **false positive** — an ordinary
`[ -d x ] && echo A || echo B` if-then-else, not a swallowed corpus failure. **Honest verdict: zero
real fail-open instruments hide across a newline in the `.sh`/`.py` corpus.** That negative is
credible *only* because the calibration proved the instrument could see a split positive and that
the line-oriented control could not.

---

## 7. T234's L-1b IS CLOSED — AND ITS CHARACTERISATION IS FALSIFIED

T234 recorded, `[UNVERIFIED]`, that A2-33's two calibration transcripts show *"81 unique rev-4 lines
under `git grep` vs 86 under ugrep — **a measured 5-line engine divergence**"*.

**It is not an engine divergence.** rev 4 is recoverable — A2-28 wrote it at `1b6b3cf`, A2-32
replaced it at `cab9e82` — so the exact corpus is available (2842 lines,
`sha256 ce734f9c89e54be5fa3b07d8ddb833df8eaa5f17f8e24ce0ff00564ecf821a92`). Replaying all 34
patterns against that blob (`transcripts/70-…`, `transcripts/71-…`):

| engine | `-i` (as A2-33 declared) | case-sensitive |
|---|---|---|
| `git grep -n -I -i -E` | **86** | 64 |
| `git grep -n -I -i -P` | **86** | 64 |
| `/usr/bin/grep -n -i -E` | **86** | 64 |
| `perl` PCRE `//i` | **86** | 64 |

**All four engines agree exactly.** **86 is the correct count** — and it is the number A2-33's
**ugrep** leg reported. The number that reproduces under **no** engine is **81**, the `git grep`
leg. So the 81 was measured over a **different corpus**, almost certainly the ADR as it sat in
A2-33's own worktree rather than the committed rev-4 blob.

**This STRENGTHENS A2-33 rather than weakening it:** `MISSES=0` held on both legs and its ugrep
number is the right one.

**Also excluded by measurement, because it was the obvious candidate:** A2-33's own audit claim,
*"no `\b`, `\d`, `\s` or `\w` in ANY pattern above"*, is **TRUE — 0 of 34**. The escape defect
cannot explain the difference.

**Scope of this finding (P-66/P-70).** I could not run ugrep — it is absent from this machine. I
have **corroborated** that 86 is right under four engines; I have **not verified** the ugrep binary.
Separately: the ugrep transcript declares **no engine version, no flags and no command**, and
**no committed script computes either number** — which is P-72 corollary 2 exactly, *a sweep whose
commands were not committed cannot be audited, only believed.*

---

## 8. WHAT IS LEFT UNDONE — BACKLOG, WITH SCOPE (never a diff)

1. **WIRE THE LINTER.** `50-failopen-lint.py` is **unwired** (§4.4). For whoever holds
   `conformance.sh` next (**T243 / T226**), the exact call:
   `python3 .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py || return 1`
   inside `run_guards`. **Until then it enforces nothing.**
2. **`r11-hygiene.sh:77`** — the M8 site (§3.3). T239's finding, frozen T138 evidence, outside my
   write scope. Needs a labelled correction of its own.
3. **`t184-census.sh` / `t184-sweep.sh`** — measured FAIL-OPEN / OPEN-WRONG-CORPUS (§3.1), and the
   worse shape. Frozen T184 review evidence (T114/T176); **not diffed by me.** Their numbers have
   drifted 320→348, 57→63, 20→24, 0→35.
4. **`20-rerun-dec2-sweeps.sh`** — T234's own re-runner, fail-open (§3.2). Inside T234's capture
   directory, not mine.
5. **`A2-32-evidence/sweep.sh`** — Tier 1 in the lint (dead path **and** `|| echo "(no hits)"`), but
   it exits **9** before reaching the arm, so it is fail-CLOSED *today*. It is one edit away from
   Tier 1 and I did not touch it.
6. **`RESUME.md`'s five-engines line** needs the qualifier *"three to a committed script"* (§6.1).
   Driver's file, not mine.
7. **The 262-instrument advisory tail** (M3/M5/M7) is a real backlog with a stated denominator, not
   a to-do list: most are capture plumbing where a swallowed failure is harmless. **I did not
   triage them individually** and I am not claiming they are clean.
8. **`sweeplib.sh` should live in `.softhouse/bin/`**, not in a task capture directory. Promoting it
   is outside my write scope.

---

## 9. THE BAR — RUN BY ME, PASTED VERBATIM

`transcripts/90-bar.txt`. Harness invoked with **`bash`**, never `sh`.

```
=== vector store digest (P-61) — MUST BE UNCHANGED BY T238 ===
  expected at main 477dc2d : 8968c559fa613e8642ab030bd0a029c17d147054
  measured here            : 8968c559fa613e8642ab030bd0a029c17d147054

go build   exit=0
go vet     exit=0
go test    exit=0     (ledger, ledger/conformance, loanschedule, loanschedule/conformance all ok)

gofmt -l   internal/apps/loanschedule/contract/contract.go        <-- exactly one, NEVER gofmt -w (G-3)

PROOFS: 23 passed, 0 failed        (--prove exit=0)

conformance: reference oracle (https://localhost:8443/…/health) probe = up
             ^^ probe line PRESENT, and reading `up` — tested for PRESENCE first

--- SUMMARY ---
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
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.

exemption census READ: exempted assertions (graded) = 4 == pinned 4
exemption census READ: declared exemptions (loaded) = 4 == pinned 4
exemption census READ: GROUNDED                     = 4 == pinned 4
exemption census READ: UNDETERMINED-ON-THE-RECORD   = 0 == pinned 0
exemption census READ: UNGROUNDED                   = 0 == pinned 0
exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
exemption census READ: LEDGER parity vectors        = 4 == pinned 4
exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
exemption census READ: LEDGER money cells compared  = 21 == pinned 21
GRADE exit=0
```

**Every element of the bar is met**, and `loanschedule` 46 parity / 7884 cells is **UNDISTURBED**.

---

## 10. PRE-REGISTERED PREDICTIONS — SCORED

Registered in commit `000e16d`, **before** any instrument was run and before the population was
counted.

| | prediction | outcome |
|---|---|---|
| PR-1 | `.sh`+`.py` population is 100–250 | **FALSIFIED** — 846 |
| PR-2 | `A2-11/enumerate-corpus.py` fails CLOSED | CONFIRMED (via `check=True`, not `os.chdir`) |
| PR-3 | ≥1 of the two `t184` scripts fails OPEN | CONFIRMED — **both**, and in the worse shape |
| PR-4 | ≥1 fail-open mechanism that is not a dead path | CONFIRMED — **four** |
| PR-5 | `a2-31` and `A2-32` fail CLOSED | CONFIRMED (exit 1 / exit 9) |
| PR-6 | L-1b is explainable from committed artefacts | CONFIRMED, and it **falsifies T234's reading** |
| PR-7 | multi-line finds ≥1 extra fail-open instrument | **letter yes, substance NO** — 1 match, a false positive |

Two of seven wrong, one only half-right. Recorded as scored.

---

## 11. FILES

**Modified (2, both inside scope):**
`.softhouse/reviews/a2-33-dec2-rev5/sweep.sh` — fail-closed repair, all 34 patterns byte-identical
`.softhouse/reviews/a2-33-dec2-rev5/CORRECTION.md` — **new**, the labelled correction (T114/T176)

**New, all under `.softhouse/capture/t238-failopen/`:**
`PREDICTIONS.md` · `instruments/{00-engines.sh, 10-failopen-census.py, 20-run-the-class.sh,
30-pr4-nondead-mechanisms.sh, 40-red-drive.sh, 45-trim-green.sh, 50-failopen-lint.py,
60-multiline-sweep.py, 70-l1b-81-vs-86.sh, 71-l1b-gitgrep-leg.sh, 90-bar.sh, sweeplib.sh}` ·
`transcripts/` (10 files) · `evidence/` (census JSON, lint JSON, calibration corpus, 7 class-run
logs, 8 red-drive artefacts)

**Untouched, verified:** `.softhouse/vectors/` (digest identical) · `nexus/` · `docs/adr/` ·
`.softhouse/conformance.sh` · `.softhouse/gates.md` · every committed A2-33 transcript.
