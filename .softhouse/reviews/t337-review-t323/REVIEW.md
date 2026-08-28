# T337 — independent review of T323 (wiring the unwired guards)

**Subject:** branch `softhouse/T323-wire-unwired-guards`, head **`f2484f67`**.
**Diff under review:** `git diff main...softhouse/T323-wire-unwired-guards` — `.softhouse/conformance.sh`
**+312 / −3** [VERIFIED: `git diff --numstat main...` → `312  3  .softhouse/conformance.sh`], plus
20 evidence/handoff files.

**VERDICT: ACCEPT-WITH-CONDITIONS.**

This modifies the grading instrument, so the bar is higher than usual and the review is written
against the question *"can this produce a confidently wrong PASS?"* — not *"is it nice work."*
The answer to that question is **no**: every defect I found fails **closed** (refuses when it
should not) and none fails open. That is why the verdict is not REJECT. The conditions are about
a HARD guard that a legitimate task will trip, whose remedy is **outside that task's edit grant**.

---

## 0. WHAT I RE-DERIVED RATHER THAN RELAYED

Everything below is my own measurement on my own clone of `f2484f67`. I did not accept a single
transcript from the branch.

### 0.1 All four of T323's refutations of its brief are CORRECT

| claim | brief said | T323 said | **T337 measured** | |
|---|---|---|---|---|
| `conformance.sh` length on `main` | 3,101 | 4,132 | **4,132** | ✅ T323 right |
| `fire-program\|ready-tasks\|reconcile\|in_progress` grep on `main` | ZERO | 25 | **25** | ✅ T323 right |
| wrong ledger implementations dying | 11/11 | 13/13 | **13 of 13** | ✅ T323 right |
| dead-path frontier | 98 or 78 | 109 | **109 == pin 109** | ✅ T323 right |

Method: `git show main:.softhouse/conformance.sh | wc -l` and `| grep -cE …`; the ledger and
frontier figures read out of **my own** green-control bar run (§2), not T323's.

T323 iteration 1 is indeed already merged — `guard_capture_namespace`, `guard_dead_path_frontier`
and `guard_reconciler_ownership` are live on `main`, and the three-dot diff into `run_guards`
adds **exactly one** line, confirming the other three were already registered
[VERIFIED: hunk `@@ -2985,6 +3293,7 @@ run_guards()`, a single `+`].

**Four refuted premises, four correct refutations. The brief was wrong and T323 was right about
all of it.** Disbelieving the brief is standing policy here and it paid again.

### 0.2 THE NEAR-REVERT DID NOT SHIP — verified, and this was the check with the worst failure mode

T323 discloses it nearly shipped a `conformance.sh` reverted by a stray
`git checkout main -- …` that the commit then took from the index, caught and amended. **The
amend landed.** Two independent checks:

1. **`git diff softhouse/T323-wire-unwired-guards...main -- .softhouse/conformance.sh` adds
   ZERO lines.** Main's file is a strict subset of the delivered file — there is no fragment of
   `main` missing from what is being handed over. A partial revert would necessarily show up
   here as additions.
2. **The three deleted lines are all comments**, and they are exactly the rotted cardinals §A
   says were repaired:
   ```
   -#       -> 128 distinct evidence directories EVER created in this repository
   -#       -> 107 of them carry a t<n> id prefix
   -#       -> ids prefixing MORE THAN ONE directory, over the entire history:   exactly ONE
   ```
   **No executable line was removed.** `bash -n` on the delivered file: clean.

Also confirmed: `conformance.sh` did not move on `main` between the merge base `5f23f27e` and
`main` (`git log 5f23f27e..main -- .softhouse/conformance.sh` is empty), so the merge could not
have dropped a gate.

### 0.3 The other self-disclosure is complete, not merely present

T323 reports that a naive id regex of its own reported a spurious extra collision that was its
selector rather than the tree. Reproduced exactly — folding the `a2-<n>` id space with
`^[ta][0-9]+` gives:

```
   7 a2
   2 t256
```

`a2` with **seven** directories, as disclosed. `check-capture-namespace.sh` separates that id
space deliberately and records the four false collisions (a2-29/t29, a2-31/t31, a2-33/t33,
a2-34/t34) that motivated it. **The guard was right and the re-derivation was wrong**, exactly as
T323 says. Honest and complete.

---

## 1. FINDINGS

### F-T337-1 — MEDIUM-HIGH — `guard_guards_dir_registration`'s selector matches at ARBITRARY DEPTH, and an ordinary Go test fixture turns the whole bar red

**This is the finding the verdict's conditions hang on, and it is proven through the route, not argued.**

The population is built by
```
pop="$( cd "$REPO_ROOT" && git ls-files -- "$gdrel/"'*.sh' )"     # conformance.sh:3090
```
A git pathspec without `:(glob)` magic uses fnmatch **without** `FNM_PATHNAME`, so `*` **matches
`/`**. The selector is therefore not "the `.sh` files in `.softhouse/guards`" — it is "every
tracked `.sh` at any depth beneath it".

`.softhouse/guards/` contains a **Go module**: `ledgerguard/go.mod`, `ledgerguard/main.go`. Any
task working on `ledgerguard` that adds a shell helper — a fixture generator, a build script,
`testdata/setup.sh` — puts a file into this guard's population that is not a checker and never
will be.

**DRIVEN, not asserted.** I planted `.softhouse/guards/ledgerguard/testdata/setup.sh` containing
one line, `#!/bin/sh`, and ran **the whole bar**:

```
conformance: guard_guards_dir_registration: .softhouse/guards/ledgerguard/testdata/setup.sh IS INVOKED BY NOTHING.
conformance:   GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 invoked-by-nothing=1
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
EXIT=2
```
probe line count in that transcript: **0 — ABSENT**.
[Transcript: `evidence/10-FP-nested-helper-sh-turns-bar-red.txt`.]

**FAIL DIRECTION: fail-CLOSED.** It refuses; it cannot manufacture a PASS. That is the safe
direction and it is why this is a condition rather than a rejection.

**WHAT A LEGITIMATE TASK HAS TO DO TO TRIP IT:** add one tracked `*.sh` anywhere under
`.softhouse/guards/`, including inside the Go module that already lives there. That is not an
exotic input; `.softhouse/guards/ledgerguard/` is the home of the money guard this program cares
most about, and shell fixtures around Go tests are ordinary.

**Why the selector line does not save it.** The guard prints
`(selector: git ls-files over the '*.sh' members of .softhouse/guards, from $REPO_ROOT; …)`.
A reader takes "the members of that directory" to mean its own level. The printed selector
**misdescribes the search it actually ran** — P-70, *"'Latent', 'not promoted', 'can never
resolve', 'no guard exists' — four ways this program stated a search result as a world fact, in
one fire"* [VERIFIED: `.softhouse/patterns.md:2017` defines P-70 as *four ways a search result
was stated as a world fact*]. A count is a statement about the search, and this one states the
wrong search.

### F-T337-2 — MEDIUM — the remedy for F-T337-1 is OUTSIDE the tripping task's edit grant, and that is what makes HARD expensive here

The guard prints exactly two remedies:

> THE FIX is to call it from `run_guards`, or — if something else already runs it — to add its
> row to the DECLARATION TABLE in this function, naming the witness that runs it.

**Both require editing `.softhouse/conformance.sh`**, and this program *serialises* that file.
The evidence is inside the diff under review: `check-capture-namespace.sh`'s own header says

> THIS GUARD IS NOT WIRED INTO `.softhouse/conformance.sh`. That file is outside T299's grant …
> **and wiring it would be the scope violation this program treats as a rejection.**

T299 could not wire its own guard for exactly this reason, which is the entire premise of T323.
So a future task that trips F-T337-1 is in T299's position: it has caused a HARD refusal of every
graded run and **may not lawfully fix it**. It must wait for a fire that grants it
`conformance.sh`.

**Contrast with T299, whose HARD I endorse (F-T337-5).** T299's remedy is adding an `OWNER*.md`
*inside the tripping task's own directory* — in-grant, one file, same diff. T323's argument for
HARD — *"a guard whose remedy is 'say the thing the rule is asking for' is not a blocker, it is
the rule"* — is sound **for T299** and **does not transfer** to its own new guard, because there
the remedy is not in the tripper's hands. T323 makes the argument once and applies it to both.
**That is the gap in the HARD argument, and grading the argument was an explicit instruction.**

### F-T337-3 — MEDIUM — the class is NOT closed; only `.sh` is

The handoff claims the structural win as:

> a **fourth** checker could still land in `.softhouse/guards` and be reached by nothing. **Now
> it cannot.**

It still can. The population is `*.sh` only. `.softhouse/guards/ledgerguard/main.go` is a
**checker living in the canonical guards directory right now** and is outside the population by
construction. A new `.softhouse/guards/check-foo.py` — and this program writes checkers in
Python routinely (`census_dead_paths.py`, `run-ownership-matrix.py`,
`check-pnumber-citations.py`, `10-population-census.py`) — is invisible to this guard.

**Fail direction: fail-OPEN**, and it is the only fail-open in the diff. It does not produce a
wrong PASS about money or about any graded quantity; it produces a **wrong PASS about the
guard's own coverage claim**, which is the claim the handoff leads with. Severity is capped
because the guard's printed selector does say `'*.sh'`; the overstatement is in the prose, not in
the instrument.

### F-T337-4 — LOW-MEDIUM — the invocation test proves the NAME APPEARS, not that it EXECUTES: a P-45 guard with a P-45 hole

`case "$code" in *"$base"*)` (`conformance.sh:3157`) is a substring test over the
comment-stripped file. I measured the three `INVOKED` members' non-comment occurrences:

```
check-capture-namespace.sh    1 occurrence:  local g="$REPO_ROOT/.softhouse/guards/check-capture-namespace.sh"
check-dead-path-frontier.sh   1 occurrence:  local g="$REPO_ROOT/.softhouse/guards/check-dead-path-frontier.sh"
check-ledger-invariants.sh    1 occurrence:  bash "$REPO_ROOT/.softhouse/guards/check-ledger-invariants.sh" || rc=$?
```

**Two of the three are variable ASSIGNMENTS, not calls.** Delete the `bash "$g"` line from
`guard_dead_path_frontier` and leave the `local g=` line, and this guard still reports
`INVOKED`. The tight coupling that saves the tree today is that those two functions would
themselves misbehave — defence in depth, not this guard's doing.

The guard is honest about the mechanism in its printed line (`INVOKED means named on a
NON-COMMENT line of this file`) but then overstates it in the same breath: **`never a mention`**.
A `local g="…"` that nothing executes *is* a mention. P-45 is the rule this guard exists to
serve — *"A test-only guard is not a guard … verify the path that actually executes in
CI/conformance calls it, not merely that a test does"* [VERIFIED: `.softhouse/patterns.md:1503`]
— and the guard verifies naming, not execution. Fail direction: **fail-OPEN**, narrow.

### F-T337-5 — ACCEPT — T299's HARD is the right call, but the population behind "false-positive count is ZERO" was not stated

I re-ran T299's load-bearing measurement rather than believing it, and **the repaired cardinals
reproduce exactly**:

```
151 evidence directories   130 carry a t<n> id prefix   colliding ids: 1  (T256)
```

Iteration 1's `128 / 107` had indeed rotted. Over **`HEAD`'s ancestry** — 151 directories ever
created — exactly one id has ever prefixed two. **T323's conclusion holds.**

**But the count depends on which ref space you search, and T323 does not say.** Over the
repository's full ref space (`git log --all --diff-filter=A`) there are **three**:

| id | directories | |
|---|---|---|
| T256 | `capture/t256-verdict-predicate`, `capture/t256-toolchain-population` | in HEAD, documented |
| **T255** | `capture/t255-dec2-rev8` (in HEAD), **`capture/t255-frontier-rot`** | added by **T258**, on an unmerged branch |
| **T286** | `capture/t286-t268-retry` (in HEAD), **`capture/t286-rvpa-retry`** | on a rescued-WIP branch |

`t255-frontier-rot` was written by **T258** — the identical renumbering shape that motivated the
guard. So the id-reuse event has happened **three times, not once**, and merging either branch
refuses the bar.

**This does not overturn HARD, and I want to be clear about why.** Those two are **true
positives**: an undocumented collision is exactly what the guard is for, the remedy is one
`OWNER*.md` inside the offending directory, and that is in the tripping task's own grant. **HARD
is correct for T299.** The defect is the *statement*: "the predicate's historical false-positive
count is ZERO" is a claim about a search whose corpus was never named — the same P-70 shape T323
correctly catches itself committing in §A. **Say `over HEAD's ancestry` and the sentence is
true.**

### F-T337-6 — ACCEPT — P-84 holds STRUCTURALLY, and the converse has no path

Verified by reading control flow, not by counting transcripts.

```
main_grade()                                       conformance.sh:3741
  run_guards                                       conformance.sh:3744   ← plain call, NOT a subshell
    guard_guards_dir_registration || failed=1      conformance.sh:3296
    guard_capture_namespace       || failed=1      conformance.sh:3297
    guard_dead_path_frontier      || failed=1      conformance.sh:3298
    guard_reconciler_ownership    || failed=1      conformance.sh:3299
    if [ "$failed" -ne 0 ]; then exit "$EXIT_UNUSABLE"; fi   conformance.sh:3300-3303
  …
  probe="$(probe_oracle)"                          conformance.sh:3769
  say "… reference oracle ($ORACLE_HEALTH_URL) probe = $probe"   conformance.sh:3770
```

Three facts make it structural:
- **`run_guards` is called exactly once** (`grep -n 'run_guards'` → one call site, `:3744`), and
  **not in a subshell or command substitution** — so its `exit` terminates the whole shell rather
  than returning.
- **`probe_oracle` is invoked exactly once**, `:3769`, and the probe line is printed at exactly
  one place, `:3770`, both strictly downstream.
- The only other entry points are `--prove` (no probe line, no `run_guards`, documented at
  `:3814`) and `--self-test` (runs `run_guards`, prints no probe line at all).

**Converse: there is no path on which a HARD guard fails and the probe line is printed.**

One completeness note, because P-84 is a reader's discriminator and readers over-read it: `exit 2
+ probe ABSENT` is **not** uniquely "a guard fired" — a build failure (`:3737`) or a failed
`mktemp` also exits 2 before the probe, distinguished only by the message. P-84's own text —
*"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."*
[VERIFIED: `.softhouse/patterns.md:2813`] — is one-directional, and **T323 states the direction
correctly** ("a failed HARD guard cannot print a probe line"). No finding; recorded so the next
reader does not invert it.

### F-T337-7 — ACCEPT — T316's self-referential refusal survives the wiring, including a shape T323's drive does not cover

T323's arms 06/07 remove the census and the pin. I confirmed those (§2) **and drove a third,
different degradation the drive never exercises**: a pin that is **present but empty** — the
failure mode where a guard is most likely to quietly compute "frontier vs nothing" and report
green.

```
pin size now: 0 bytes
ERROR: an empty pin is a failed READ, never an empty frontier. REFUSING (exit 2).
conformance: guard_dead_path_frontier REFUSED (rc=2): a path this guard DEPENDS ON did not resolve…
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
EXIT=2
```
probe line count: **0 — ABSENT**. [Transcript: `evidence/11-T316-empty-pin-still-refuses.txt`.]

It also holds structurally: **every** dependency failure inside
`check-dead-path-frontier.sh` exits **2** (11 distinct sites: `:102 :118 :124 :129 :145 :153
:158 :175 :187` and the root/reach checks), exit 1 is reserved for a genuine frontier finding,
and the wiring maps `rc >= 2` → `return 1` with an explicit refusal message
(`conformance.sh:2770-2778`). It **cannot** degrade to green for lack of inputs.

### F-T337-8 — ACCEPT — T319's `--selftest` is genuinely hardcoded, with a presence-before-value check

```
/usr/bin/python3 "$rig" --repo "$REPO_ROOT" --tool "$tool" --selftest >"$tf" 2>&1   # conformance.sh:2945
```
Not a variable, not a flag, no conditional. Backed by a **presence** assertion — `grep -q
'^SELFTEST OK:'` at `:2959` — so a zero exit with no attestation is an instrument failure rather
than a pass, and by refusals for a missing rig, missing tool and missing `/usr/bin/python3`. Arm
10 (every cell blind to a re-dispatch) refuses through the wiring (§2). T319's argument that the
flag cannot be optional is correct and was honoured.

### F-T337-9 — ACCEPT — the T304 declination is right, and the 79% re-derives exactly

I re-ran `10-population-census.py` myself on the delivered tree:

```
DESTRUCTIVE-SITE HITS: 6291 across 1036 files
   4971 redirect      609 rm      261 truncate    218 py-rmtree     73 mv
     53 inplace-edit   46 tee      36 git-restore   24 git-clean
```
**4971 / 6291 = 79.02%.** T323's figure, to the row.

The defect is readable straight off the matcher rather than inferred:
```python
('redirect', re.compile(r'(?<![0-9<>&|])>\s*(?!&|\s*>)[A-Za-z0-9_$"\'./{-]'))
```
`-` is **not** in the lookbehind exclusion set, so `->` matches; and a spaced bare `>` matches,
so numeric comparison matches. Both reproduced against real rows, including the money-adjacent
one T323 names:

```
.softhouse/reviews/t47-probe/t47_edit_1.py  277  redirect  "packed(a, b) = k − [a.day > b.day]   # ChronoUnit.MONTHS.between, :1435"
```

That is **loan-schedule month arithmetic** being classified as an evidence-destruction risk.
**The declination is correct**, the brief's "223 legitimate sites" understates by an order of
magnitude, and "fix the lexical matcher in `10-population-census.py` first, as its own task" is
the right output rather than a deferral. [Evidence:
`evidence/20-t304-census-independent-rerun.txt`.]

### F-T337-10 — ACCEPT — the PNUMBER-CITATIONS judgement was right

`misdirecting` 70 → 75, all five in the **evidence** zone. The guard's fatal tier is the
**directive** zone alone, unchanged at MISDIRECTING 2 / UNDEFINED 4, and that design is recorded
in `conformance.sh:1765-1811` with T331's prior adjudication of the identical false-positive
shape (a *correct* `P-66/P-70` citation scoring 8 against a fatal floor of 9). The same block
measures why: with the zone restriction lifted the fatal predicate would be **~76% false
positives** (41 of 9,016 sites fire, only 10 are true drift).

**Leaving the five alone was correct.** Rewording a correct citation to move a heuristic score is
fitting the tree to the guard, and the five arise *because* the documents obey P-86 — *"cite the
rule TEXT beside any P-number"* — and the extractor sweeps the quoted gloss past the citation.

On the brief's sharper question — *is a score that moves on evidence files measuring anything?* —
**the evidence-zone total is not measuring correctness, and the design already says so** ("evidence-zone
drift is REPORTED, never fatal", `:1892`). It is a documentation-drift odometer. That is
legitimate as long as nobody grades on it, and nothing does. **No change required.** Minor
suggestion only: the headline `misdirecting` total would be more useful reported **per zone**,
since the only actionable number is the directive one.

### F-T337-11 — ACCEPT — the cost claim is sound and the method is honest

I measured the guard's constituent operations directly (one `git ls-files`, one comment-strip of
the 4,441-line file, two `grep -qF` on small files), **under CPU contention from my own 15-arm
drive**:

```
0.064 s
```

Consistent with, and comfortably below, T323's stated **0.16 s upper bound** — which T323
correctly flags as an over-statement because it includes a whole `bash` start-up and a `sed`
extraction wrapper.

**The method is the right one.** T323 explicitly **refuses** to attribute the +1.46 s
clone-to-clone delta to the guard, on the grounds that it exceeds the directly measured upper
bound, that two runs of the same clone already differed by 0.09 s, and that the delivered tree
produced the *fastest* of the four runs. That is the honest reading of a noisy measurement, and
it also declares a concurrent-worker CPU contaminant rather than averaging it away. The bar
remains ~70 s dominated by `guard_reconciler_ownership` at ~30 s. **Nobody bypasses this bar
because of T323.**

### F-T337-12 — INFO — a latent portability note, not live on this host

`check-capture-namespace.sh` verifies an OWNER record with `grep -Eqa '\b[Tt][0-9]+\b'`. The
file's own header disclaims P-53's backslash-class trap on the grounds that *"No `git grep -E` is
used anywhere here"* — which is true but narrower than the hazard, since this is plain `grep -E`
with `\b`. **Not live:** this host's `/usr/bin/grep` (BSD grep 2.6.0-FreeBSD) implements `\b` as
a word boundary [VERIFIED: `\bT` does not match `xTx`]. Were it ever read literally, the
documented T256 collision would be classed undocumented and the bar would go **red** — fail-
closed. Recorded, no action.

---

## 2. THE 15-ARM RED DRIVE, REGENERATED BY ME (P-22)

*"A guard, a canary, or a control that cannot fire is worse than none, because it is believed"*
[VERIFIED: `.softhouse/patterns.md:2346`, P-22/P-36]. I did not accept T323's transcripts. I
cloned `f2484f67` fresh (`git clone --no-hardlinks`) and ran all 15 arms myself, every arm
through **the whole bar** via `bash .softhouse/conformance.sh`.

I read the drive harness first, looking for a rigged assertion, and did not find one: each arm
asserts **exit code AND probe presence AND a specific refusal marker**, all three must match, and
the markers are narrow refusal sentences rather than permissive patterns. The green control and
the DOCUMENTED-collision discrimination arm both demand `exit 0` + `probe PRESENT` +
`VERDICT: PASS`, so a bar that refused everything would fail the drive.

**RESULT — see `evidence/30-t337-independent-red-drive.txt`.**

**Pinned gates, read out of MY OWN green-control transcript** (not T323's), all unmoved:

| gate | my measurement |
|---|---|
| exit code / probe | **0**, `probe = up` **PRESENT** |
| parity vectors | **PASS 46 / FAIL 0** |
| inadmissible | **0** |
| cells compared | **7884 graded** |
| LDG-05-openingbalance-accepted-empty-ledger | **PASS**, 27 cells (8 money) |
| LEDGER parity vectors | **7 == pinned 7** |
| LEDGER oracle-refusal | **6 == pinned 6** |
| LEDGER money cells | **39 == pinned 39** |
| wrong ledger implementations dying | **13 of 13** |
| dead-path frontier | **deadOccurrences=109 == pin 109** |
| fail-open census frontier | **11 == pinned 11** |
| P-number citations | **VERDICT PASS — 0 fatal** |
| GUARDS-DIR-REGISTRATION | `population=5 invoked=3 declared=2 invoked-by-nothing=0` |

**NO EXISTING GATE WAS WEAKENED.** Wrong-interpreter refusal also re-verified: `sh
.softhouse/conformance.sh` → **exit 3** with the WRONG INTERPRETER message.

---

## 3. CONDITIONS FOR ACCEPTANCE

These are **follow-up tasks against `conformance.sh`**, not blockers on the merge. The delivered
tree is green, every pinned gate is unmoved, and every defect found fails closed. Holding the
merge would leave `main` with three guards wired and no registration guard, which is strictly
worse.

**C-1 (from F-T337-1, F-T337-2) — fix the depth-crossing selector, and put the remedy in the
tripping task's grant.** Required before another fire adds a shell helper under
`.softhouse/guards/ledgerguard/`.

*Immediate one-token mitigation*, verified by me on the delivered tree:
```diff
-  pop="$( cd "$REPO_ROOT" 2>/dev/null && git ls-files -- "$gdrel/"'*.sh' 2>/dev/null )"
+  # ':(glob)' magic — WITHOUT it a git pathspec '*' matches '/' too, so this swept every
+  # tracked .sh at ANY depth, including fixtures inside the ledgerguard Go module. [T337 F-1]
+  pop="$( cd "$REPO_ROOT" 2>/dev/null && git ls-files -- ":(glob)$gdrel/"'*.sh' 2>/dev/null )"
```
[VERIFIED by me: with a nested `ledgerguard/testdata/setup.sh` planted, the current selector
returns 6 members and the `:(glob)` selector returns the correct 5.]

**This mitigation is not sufficient on its own** and must not be applied as the whole answer: it
buys correctness by *narrowing coverage*, so a genuine unwired checker in a subdirectory now
escapes — trading F-T337-1 for a bigger F-T337-3. The task that takes C-1 should also add a
**third declaration direction whose row lives in the member file rather than in
`conformance.sh`** — the member names its witness in its own header, and the guard verifies the
witness names the member, exactly as the existing CALLER direction does. That keeps
"verified, not believed" while moving the remedy in-grant, which is the actual defect.

**C-2 (from F-T337-3) — state the closed class accurately, or close it.** Either extend the
population beyond `*.sh` (the directory already contains a Go checker), or amend the claim: the
class closed is *tracked shell files*, not *checkers*.

**C-3 (from F-T337-5) — one sentence.** "the predicate's historical false-positive count is
ZERO" should name its corpus: **over `HEAD`'s ancestry**. Two further colliding ids exist on
unmerged branches (T255 via T258, T286), and a reader planning a merge should know that.

**C-4 (from F-T337-4) — one sentence.** The printed selector's `never a mention` overstates a
substring test that two of three current members satisfy via a variable assignment. Either say
"named on a non-comment line" and stop, or test for an executed call.

**C-5 — housekeeping T323 itself filed and I confirm:** FU-T323-5, the stale sentence inside
`guard_dead_path_frontier`'s `removed=` branch still claiming *"the pin is outside T323's edit
grant"* after T326 regenerated it. It is a false statement inside a refusal message, which is the
worst place for one.

---

## 4. WHAT I DID NOT CHECK

Stated because "not found" is a statement about the search.

- **I did not audit whether T299's, T316's or T319's guards are semantically CORRECT** — only
  that their wiring reaches them, fails closed, and cannot print a probe line. T323 disclaims the
  same scope, and the disclaimer is accurate.
- **I did not re-verify the 5 inherited iteration-2 commits line-by-line against their claims.**
  What I did instead is stronger for this purpose: I re-derived the **delivered artefact's**
  behaviour from scratch — the diff, the file contents, the four cardinals, the census, the cost,
  and all 15 arms. A defect in an inherited commit that survives into the delivered tree would
  have to be invisible to all of that.
- **I did not run `--prove`**, the harness's own mutation proofs. It does not go through
  `run_guards` and is outside this diff.
- **I did not examine the T304 `20-resolve-targets.py` / `30-count-tracked-under-target.py`
  stages** — only stage 10, which is where the 79% claim lives.
- **Where I looked for other checker homes:** `git ls-files` under `.softhouse/guards` (8 files,
  5 shell), plus the four named by T333/T303/T311/T257 under `capture/`. I did not sweep the tree
  for every executable that behaves like a checker.

## 5. MONEY

**No monetary code path, schema, fixture or vector is touched by this diff.** The added guard
reads file names and greps substrings; its only numbers are three counters of files. No float
enters any path. The 46 parity vectors, LDG-05, the LEDGER money-cell count (39, int64 minor
units) and the 13 wrong-implementation mutants were all re-measured by me and are byte-identical
to the pinned values. No `user` gate was approached — nothing here touches the adapter contract,
a DEC-n, a cutover, regulatory sign-off, or deposit activation.

## 6. P-80 — THIS REVIEW AGAINST ITS OWN RULES

- **Namespace:** this review adds `.softhouse/reviews/t337-review-t323/`. `T337` prefixes **no
  other** directory in the tree [VERIFIED: `grep -i t337` over the 151-directory population
  returns nothing], so it creates no collision and needs no `OWNER*.md`.
- **Dead-path frontier:** everything added here is `.md` and `.txt`. T316's corpus is tracked
  `*.py` / `*.sh` only, so **no row can reach the frontier** from this deliverable, and
  `deadOccurrences` cannot move.
- **Guards directory:** nothing added under `.softhouse/guards`, so `population` stays 5.
- **P-86:** every P-number above carries its rule TEXT and a `patterns.md` line verified by
  grepping the text, not the ordinal.
- **P-83:** I tested that the probe line was PRINTED before reading its value in every transcript
  I judged, and reported probe presence as a count, not an impression.
- **The bar, run on this review's own committed deliverable** —
  `evidence/40-bar-on-t337-own-deliverable.txt`: **EXIT 0, 72 s**, `probe = up` PRESENT, 46
  parity PASS / 0 FAIL / 0 inadmissible, 7884 cells, LEDGER 7 / 6 / 39 == pinned, **13 of 13**
  wrong implementations dying, `deadOccurrences=109` **unmoved**, fail-open frontier == pinned,
  P-number citations VERDICT PASS. **This review moves nothing.**
