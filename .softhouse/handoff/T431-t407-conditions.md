# T431 — C-T407-1 and the rest of T407's conditions

**Branch:** `softhouse/T431-t407-conditions`, off `main` at `683c8aff`.
**Subject:** the four conditions T407 attached to its approval of T404.
**Honesty rule:** every material claim below is marked `[VERIFIED: <source>]` or `[UNVERIFIED]`.
Where I could not drive something I say so and say what the bound is on — my search, or the
defect.

---

## HEADLINE

**`C-T407-1` reproduced on today's unmodified `main`, and it is worse than T407 measured.**
T407 found ONE typed witness spelling that reaches the hole. I drove **FOUR**, three of which
the ratified one-token pin closes and **one of which it does not**. The fourth — the C-quoting
route T407 recorded as `FU-T407-1`, *reasoned, not driven* — is driven here, and it defeats
`:(literal)` on its own. This is exactly the failure this program keeps repeating: **a fix that
closes the demonstrated spelling and leaves its neighbour open.** I found it by probing the
neighbourhood at the git level *before* trusting the one-token change, not after.

**`T404`'s branch still may not be cited as closing the registration-forgery class — but after
this branch it may, for the routes named below and no others.** See `## Follow-ups`.

---

## Changes Made

All in `.softhouse/conformance.sh`, inside `guard_guards_dir_registration`, plus a capture
directory. **Nothing touches money, the ledger, a vector, a DEC-n, the frozen adapter contract,
a database driver or a pin.** The diff contains no arithmetic and no floating point.

### 1. `C-T407-1` (MAJOR) — the witness lookup

**I located the line by CONTENT, not by number**, because T404's own `+75` rotted seven
citations in this same file. The search was:

    grep -cF 'git ls-files -s -- "$self_norm" 2>/dev/null' .softhouse/conformance.sh   -> 1

Exactly one occurrence [VERIFIED: run on this tree]. It happened to still be at `:3677` on
`main`, but I did not rely on that.

Three changes at that site:

| # | change | closes |
|---|---|---|
| **a** | `git ls-files -s -- "$self_norm"` → `git ls-files -s -- ":(literal)$self_norm"` | arms `X`, `XT`, `XI` — every spelling whose magic suppresses globbing |
| **b** | new refusal `elif [ -z "$self_stat" ]` — an empty pinned result | arm `XQ0`; the exact sibling of T404's `member_none` |
| **c** | new refusal `elif [ "$self_path" != "$self_norm" ]` — **the lookup must ROUND-TRIP** | arm `XQ`, which **(a) and (b) both miss** |

`self_path` is the path field of the pinned `git ls-files -s` line, taken with parameter
expansion off a `CONF_TAB` constant spelled once beside the existing `CONF_LF` — **no pipeline**,
for the `P-57` reason this function keeps everywhere else.

**Why (c) is needed and why I only found it by driving.** `self_norm` is the *output* of a
pathspec lookup, and `git ls-files` **C-quotes** any path carrying a non-ASCII byte, a
backslash, a double quote, a control character or a newline, printing it **wrapped in literal
double quotes** [VERIFIED: `evidence/20`, `evidence/21` — measured on git 2.50.1, and
`core.quotePath=false` still quotes the backslash and dquote cases]. An attacker who **creates a
tracked file whose literal name IS that C-quoted rendering** makes even the *pinned* lookup
succeed — on the decoy, mode `100644`, decoy blob — while the real witness stays a symlink to
the member, and the closing `grep` reads the decoy too. Round-trip equality is the only test
that catches it, and its only fixed point is the true witness, so it refuses nothing legitimate.

### 2. `C-T407-2` (MODERATE) — seven rotted cardinals deleted, not refreshed

`:4090 :4109 :4140 :4143 :4585 :4610 :4611` in the `P-45`/`P-84` block. **All seven re-measured
on `main` before deletion; all seven land on an unrelated line, and `:4090` lands on a bare
double-quote — mid-string** [VERIFIED: `evidence/30-seven-rotted-cardinals.txt`]. Replaced by
one `grep -n 'run_guards\|probe_oracle\|guard_cost_census'` and the argument by name.

**C-T407-2 asks what a guard would cost. Answered in the block itself:** it would have to grade
each comment-borne `:NNN` against an *expected anchor* — a second register kept in step by hand,
i.e. the same class of artefact that just rotted three times. Cheaper and permanent: have no
numbers to grade.

**The hunk is deliberately LINE-COUNT NEUTRAL (25 → 25).** `.softhouse/patterns.md:3426` cites
`conformance.sh:3271` and that citation is **currently correct** [VERIFIED: `sed -n 3271p` on
`main` and on this tree both print the `population is EMPTY` refusal]. `patterns.md` is outside
this task's `files_hint`, so rather than rot a correct citation I could not then repair, I sized
the replacement to preserve it. The four lines I spent doing so are the guard-cost answer above,
not padding.

### 3. `C-T407-3` (MINOR) — `member_multi` qualified

Added to T404's block: on any git honouring `:(literal)` the `member_multi` branch **cannot
fire**; its only driven route is the synthetic `R1` revert; it is kept deliberately as the
fail-closed backstop and **must not be deleted as dead code nor cited as coverage**. One thing
T407 did not say and I add: **`self_multi` on the witness side is genuinely live**, because the
witness spelling is *attacker-typed* rather than emitted by git — arm `XC` drives it on a
conforming git with no revert at all.

### 4. `C-T407-4` (MINOR) — the record corrected

`.softhouse/capture/t431-t407-conditions/CORRECTIONS-to-T404-section-8.md`. I did **not** edit
T404's handoff — a handoff is a record of its own moment. Both claims re-verified against the
committed files, and **T407's own citation was slightly off**: the transcripts are in T404's
capture dir, not T407's review dir.

* §8's opening sentence overstates. `evidence/10-RED-BEFORE-full-drive-unfixed-guard.txt` scores
  `H` and `W` `marker=NO census=NO >>> FAIL` at its **lines 15 and 23** [VERIFIED: T431 read the
  file]. The instrument *did* distinguish them, which is what §8's closing sentence says.
* The second, unnamed corruption is real: `evidence/11-RED-BEFORE-arms-H-W-N.txt` **lines 11 and
  14** carry `line 501: r: command not found` and `line 521: syntax error near unexpected token
  'fi'` [VERIFIED: T431 read the file] — the drive was edited **while `bash` was executing it**.
  A unique work root does not prevent that. **Freeze the drive before running it**, which this
  task did: `/tmp/t431/run.sh` copies the drive out of the repo, `chmod a-w`s it, prints its
  SHA-256 and runs the frozen copy. The RED and GREEN runs report the **same** SHA-256
  `f4f0e5845774fe8864019f878868e5aee995f6b60656974457048f7c2283ba2a`, so both were graded by
  identical bytes [VERIFIED: `evidence/40`, `evidence/50` headers].

---

## RED-BEFORE

**On today's unmodified `main` (`683c8aff`), with the drive detecting the tree's state from its
own blob and unable to be told which tree it is grading.**

First, T407's arms, **lifted and re-run, not re-invented** [VERIFIED:
`evidence/10-RED-BEFORE-drive-summary-on-todays-main.txt`, `evidence/11`…`13`]:

    T407-X-WITNESS-ambiguity-FAILOPEN     exit=0  probe=PRESENT  >>> PASS
        census: population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0 symlink-members=0
    T407-XS-witness-symlink-NO-decoy      exit=2  probe=ABSENT   THAT WITNESS IS A SYMLINK
    T407-XC-witness-PLAIN-spelling        exit=2  probe=ABSENT   MORE THAN ONE TRACKED PATH

and the whole bar for `X` reaching
`VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
compared`, with the guard printing, over a witness that is **a symlink to the member itself**:

    conformance:     REACHED-BY .softhouse/guards/zz-t407x/zz-t407x-member.sh — declared in its own header, reached by
    conformance:                .softhouse/guards/zz-t407x/w?.txt (verified: it names zz-t407x-member.sh)

**It reproduces. C-T407-1 is real on today's tree.**

Then my own arm set, 14 arms [VERIFIED: `evidence/40-RED-BEFORE-all-14-arms-on-main.txt`,
**14 PASS / 0 FAIL**]. **FOUR fail-opens**, each at `exit 0 / probe PRESENT / VERDICT: PASS`
with `population=7 … reached-by=2 … symlink-members=0`:

| arm | typed witness spelling | on `main` |
|---|---|---|
| `X`  | `:(literal)P` | **ACCEPTED — fail-open** |
| `XT` | `:(top,literal)P` | **ACCEPTED — fail-open**, a spelling T407 did not try |
| `XI` | `:(literal,icase)P` | **ACCEPTED — fail-open**, likewise |
| `XQ` | the **C-QUOTED** witness | **ACCEPTED — fail-open**, and `:(literal)` does not close it |

`XQ`'s transcript shows the guard printing a *witness path that is not a path*
[VERIFIED: `evidence/41`, line 161]:

    conformance:     REACHED-BY .softhouse/guards/zz-t431q/zz-t431q-member.sh — declared in its own header, reached by
    conformance:                ".softhouse/guards/zz-t431q/w\303\251.txt" (verified: it names zz-t431q-member.sh)

while the index holds

    100644 …  "\".softhouse/guards/zz-t431q/w\\303\\251.txt\""     the planted decoy
    120000 …  ".softhouse/guards/zz-t431q/w\303\251.txt"           the real witness — a SYMLINK to the member

**Nine controls refuse on the same tree**, each for its own reason, so this is not "magic
characters break the guard": `XS` (no decoy → symlink-witness refusal), `XC` (plain spelling →
multi), `XG` `:(glob)`, `XX` `:!`, `XB` backslash-escaped (all → multi), `XA` `:(attr:zz)` →
untracked, `XQ0` (C-quoted, no decoy) → `DOES NOT NAME`.
**And three healthy controls stay ACCEPTED on the same tree** — `Z`, `Y`, and `XM`, a member
whose **own path carries the magic spelling**, which is correctly *not* refused.

---

## GREEN-AFTER

**On this branch's committed tip, same frozen drive (same SHA-256 as the RED run), the drive
detecting `pin=yes / empty=yes / round-trip=yes` from the blob itself:
`=== T431 DRIVE: 18 PASS / 0 FAIL of 18 ===`** [VERIFIED:
`evidence/50-GREEN-AFTER-all-18-arms-on-this-branch.txt`].

### The four fail-opens, all refused

| arm | on `main` | on this branch | refused by |
|---|---|---|---|
| `X`  `:(literal)P` | exit 0, VERDICT: PASS | **exit 2, probe ABSENT** | `THAT WITNESS IS A SYMLINK` |
| `XT` `:(top,literal)P` | exit 0, VERDICT: PASS | **exit 2, probe ABSENT** | `THAT WITNESS IS A SYMLINK` |
| `XI` `:(literal,icase)P` | exit 0, VERDICT: PASS | **exit 2, probe ABSENT** | `THAT WITNESS IS A SYMLINK` |
| `XQ` C-QUOTED | exit 0, VERDICT: PASS | **exit 2, probe ABSENT** | **`DID NOT ROUND-TRIP`** |

### The clean-tree controls that still pass — this is not a guard that refuses everything

| arm | result |
|---|---|
| `Z` unmutated | **exit 0, probe PRESENT**, `population=6 … reached-by=1 … symlink-members=0` |
| `Y` honest independent tracked witness | **exit 0, probe PRESENT**, ACCEPTED at `reached-by=2` |
| `XM` member whose OWN path carries the magic spelling | **exit 0, probe PRESENT**, ACCEPTED at `reached-by=2` |

`Y` and `XM` are ACCEPTED **under all three of my changes**, so the round-trip test's fixed
point really is the true witness and it refuses nothing legitimate.

### Nine controls that refuse for their own reasons, unchanged across the repair

`XS` symlink-witness · `XC` multi · `XG` multi · `XX` multi · `XA` untracked ·
`XB` multi · `XQ0` empty-result — every one exit 2 / probe ABSENT, on both trees.

### `P-22` — which line does what, stated honestly rather than flatteringly

| revert | arm | result | reading |
|---|---|---|---|
| `RV1` pin only | `X` | **exit 2**, `DID NOT ROUND-TRIP` | **the pin is not the only line holding `X`.** It is still the right primary fix — it makes the lookup *correct*, where round-trip only *detects* incorrectness — but I will not claim independence I did not measure |
| `RVQ` round-trip only | `XQ` | **exit 0, probe PRESENT, VERDICT: PASS** | **THE HOLE REOPENS. Round-trip is INDEPENDENTLY NECESSARY.** This is the arm that proves the ratified one-token pin would not have been enough |
| `RVE` empty-result only | `XQ0` | **exit 2**, `DID NOT ROUND-TRIP` | **the empty-result branch is NOT independently necessary.** It is a better *message*, kept for the reason T404 kept `member_none`. Said plainly so nobody later cites it as coverage |
| `RV3` all three | `X` | **exit 0, probe PRESENT, VERDICT: PASS** | `main`'s behaviour, reproduced from the fixed tree |

---

## What my own arm misses by one

This is the section this program exists to make people write, so it is long and it is specific.

### Closed, and driven closed

Every route below is refused on this branch **and** was measured on `main` first.

| spelling / construction | on `main` | on this branch | refused by |
|---|---|---|---|
| `:(literal)P` | ACCEPTED | REFUSED | the pin, then the symlink refusal |
| `:(top,literal)P` | ACCEPTED | REFUSED | the pin |
| `:(literal,icase)P` | ACCEPTED | REFUSED | the pin |
| C-QUOTED witness + decoy at the quoted literal name | ACCEPTED | REFUSED | **round-trip** — the pin does **not** |
| C-QUOTED witness, no decoy | refused (`DOES NOT NAME`) | refused (`matched NO INDEX ENTRY`) | empty-result |
| plain `P` + decoy | refused | refused | `self_multi` |
| `:(glob)P`, `:(icase)P`, `:(top)P`, `:/P`, bare `:P` | refused | refused | `self_multi` — **they still glob** |
| `:!P`, `:^P`, `:(exclude)P` | refused | refused | `self_multi` — exclusion-only, matches every *other* path |
| `:(attr:zz)P` | refused | refused | `--error-unmatch` non-zero → untracked refusal |
| backslash-escaped `P` **with the `-f` pacifier planted** | refused | refused | `self_multi` |
| member's own path carries the magic | ACCEPTED (correct) | ACCEPTED (correct) | — T404's member-side pin handles it |

**The 14 spellings in the middle rows were measured, not reasoned** [VERIFIED:
`evidence/20-probe-magic-neighbourhood.txt`, git 2.50.1 (Apple Git-155), `core.ignorecase=true`].

**A correction to T404's stated reasoning, reaching the same conclusion by a different route.**
T404 wrote that a backslash-escaped spelling dies at the `-f` test. **Measured false** once the
attacker plants a real file of that literal name — the same move the magic route uses to defeat
`-f`. The route is still closed, but by the **multi** refusal: git tries **exact literal
equality** (the pacifier) *as well as* wildmatch (the globbed sibling) and returns **two lines**
[VERIFIED: `evidence/21`]. The conclusion stood; the reason did not. That is the T404/T407
inversion in miniature and it is why I stopped trusting stated reasons and drove them.

### What each line actually does — `P-22`, stated honestly rather than flatteringly

Four revert arms on the fixed tree. **Two of the three lines are NOT independently necessary,
and I am not going to dress them up as though they were.**

| revert | arm | result | reading |
|---|---|---|---|
| `RV1` pin only | `X` | REFUSED — by the round-trip test | **the pin is not the only line holding `X`.** It is still the right primary fix: it makes the lookup *correct*, where round-trip merely *detects* incorrectness |
| `RVQ` round-trip only | `XQ` | **HOLE REOPENS** | **round-trip is independently necessary.** Nothing else catches `XQ` |
| `RVE` empty-result only | `XQ0` | REFUSED — by the round-trip test | **the empty-result branch is NOT independently necessary.** It is a better *message*, kept for the reason T404 kept `member_none`. Said plainly so nobody later cites it as coverage |
| `RV3` all three | `X` | **HOLE REOPENS** | this is `main`'s behaviour, reproduced from the fixed tree |

### NOT closed — and these are bounds on the DEFECT where I say so, on MY SEARCH where I say that

1. **A path containing a literal NEWLINE.** `git ls-files` C-quotes it, so it lands in the
   round-trip refusal — **but the member enumeration `while IFS= read -r rel` is a different
   matter and I did not drive it.** T404 said the same about arm `N`. **[UNVERIFIED — a bound on
   my search.]** The spelling is: a tracked file under `.softhouse/guards/` whose name contains
   `0x0A`.
2. **A gitlink / submodule entry ending in `.sh`.** Not driven by any generation, mine included.
   **[UNVERIFIED — bound on my search.]**
3. **A case-SENSITIVE filesystem.** This host is `core.ignorecase=true` [VERIFIED:
   `evidence/20`, first lines]. I did not obtain a case-sensitive host, so the `:(icase)` family
   is measured on the *wrong* filesystem for the interesting case. **[UNVERIFIED — bound on my
   search, and the same one T407 and T404 both recorded.]** The spelling is: `:(icase)P` where
   `P` differs from a tracked path only in case.
4. **`git` versions other than 2.50.1.** Every pathspec measurement here is one binary on one
   host. `:(literal)` semantics are stable since 1.9, but I did not test a second git.
   **[UNVERIFIED — bound on my search.]**
5. **A tracked file at the repository root literally named `:(literal).softhouse/guards/…/x.sh`
   is NOT in this guard's population at all** — the selector is
   `:(glob).softhouse/guards/**/*.sh` and that path does not start with `.softhouse`
   [VERIFIED by construction of the selector, which I read; **[UNVERIFIED]** as a driven arm].
   It is therefore outside this guard's remit rather than a hole in it, but a *different* guard
   might care and none of them was asked.
6. **`self_wit` is taken from the member's own first matching `REACHED-BY` row via
   `grep -m1`.** A member carrying **two** REACHED-BY rows is graded on the first. Not driven.
   **[UNVERIFIED — bound on my search.]**
7. **Still open from earlier generations and NOT touched here**, restated so silence is not read
   as completion: `FU-T375-5` (the `DECLARED` direction, driven by no arm in any generation);
   `guard_graded_root_is_this_tree`'s short-circuit; and the `member_none` branch, never driven
   by a git that actually lacks `:(literal)`.

---

## Bar figures

`bash .softhouse/conformance.sh` — **`bash`, never `sh`** — on the finished, COMMITTED tree at
`20018d18`, with `git status --porcelain` **EMPTY before AND after the run** [VERIFIED:
`evidence/61-FINAL-BAR-figures-summary.txt`; full transcript
`evidence/60-FINAL-BAR-clean-committed-tree.txt`, 749 lines].

**`P-84` DISCIPLINE — PRESENCE ESTABLISHED BEFORE VALUE.**
`grep -c 'probe = '` = **1**, i.e. the probe line was **PRINTED**; *then* its value was read.

| | this branch | stated baseline for `main` at fire start | moved? |
|---|---|---|---|
| **exit** | **0** | 0 | no |
| **probe** | **PRESENT ×1**, reading `up` | PRESENT ×1 `up` | no |
| **VERDICT** | **PASS — 46 parity vectors, 7884 cells** | 46 / 7884 | no |
| guards-dir census | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | same | no |
| dead-path `deadOccurrences` | **108** | 108 | **no** |
| fail-open frontier | **11 == pinned 11**, by path | 11 == 11 | no |
| host-state census | **18 == pinned 18**, by path and source line | — | — |
| ledger money cells | **63 == pinned 63** | 63 | no |
| ledger parity vectors | **10 == pinned 10** | 10 | no |
| exemption census | GROUNDED **4 == 4**, UNGROUNDED **0 == 0** | — | — |
| `guard_guards_dir_registration` cost | **1 s / ceiling 60 s** | — | — |
| wrong ledger implementations | **15**, pin 15, all 15 died | **16** on today's `main` | **YES — see below** |
| T316 corpus | **1454** | 1453 at my fork point | **YES — see below** |

**THE TWO FIGURES THAT MOVED, AND WHY. NEITHER IS CAUSED BY THIS BRANCH'S CHANGE.**

1. **Wrong ledger implementations 15, not 16.** My branch forked from `main` at **`683c8aff`**,
   and `main` has since advanced to **`e4bde474`**. The *only* `conformance.sh` change on `main`
   in that window is `EXEMPTION_PIN_LEDGER_WRONGIMPLS=15 → 16` [VERIFIED:
   `git diff 683c8aff main -- .softhouse/conformance.sh` is exactly that one line, at `:4548`].
   My tree carries pin 15 and 15 implementations — **internally consistent, and it is the
   baseline of my fork point, not a regression.** On my tree that constant now sits at `:4694`;
   **I never touched it, and T407's instruction to match it BY NAME is respected.**
   **The merge is clean:** that line is ~850 lines below my lowest edit.
2. **T316 corpus 1454.** `683c8aff` carries **1453** tracked `.softhouse/` `.py`/`.sh` files and
   my branch carries **1454** — the difference is **exactly `drive-t431.sh`** [VERIFIED: measured
   both trees with `git ls-tree -r --name-only … | grep -cE '\.(py|sh)$'`]. **`deadOccurrences`
   did NOT move** (108 → 108), because every planted path in the drive is assembled at run time
   from a directory variable plus a leaf, so it contributes **zero** CONCRETE repo-rooted
   literals. **No pin regeneration is required by this branch.** This is the same shape T407
   recorded for its own drive.

**A NOTE ON THE BASE, so nobody reads a stale figure.** My two RED-BEFORE runs were taken
against `main` as it stood at the moment each clone was made — the T407-arm run at
**`ec285e17`** and the 14-arm run at **`e864dd3d`**, both *newer* than my fork point
[VERIFIED: `git log` inside each arm's clone]. That strengthens the finding rather than weakening
it: the defect was live on the newest tree available at run time. **The merger should
re-baseline by RUNNING, not by reading this table.**

---

## Unverified

Marked here so nothing above is read as measured when it was not.

* **The `sh` vs `bash` and toolchain conditions of the arm runs.** Every arm ran under
  `go-env.sh`'s announced **FALLBACK** toolchain (`go1.23.4 darwin/arm64` on `PATH`), because the
  scratch clones in `/tmp` have no `.softhouse/toolchain` [VERIFIED: the banner is in every arm
  transcript]. **RED and GREEN both ran that way**, so the comparison is like-for-like, but no
  arm was graded under the pinned toolchain. **[UNVERIFIED for the pinned toolchain.]**
* **Machine contention.** Up to seven concurrent `conformance.sh` runs from other agents were on
  this host during the GREEN drive [VERIFIED: `ps`]. No guard breached its wall-clock ceiling in
  my final bar (worst: `guard_reconciler_ownership` 33 s / 500 s), but the arm timings are not a
  cost measurement of anything. **[UNVERIFIED as a cost claim.]**
* **A conflicted index (stage 1/2/3 entries for one path)** would make `git ls-files -s` print
  several lines for the *same* path, `self_path` would then carry embedded newlines and the
  round-trip test would REFUSE. **Reasoned from the output format, NOT DRIVEN. [UNVERIFIED.]**
  The bar requires a clean tree anyway.
* **I did not re-verify T404's arm table against `evidence/12` and `evidence/13` myself** — T407
  did, and I record that as T407's measurement, not mine. **[UNVERIFIED by me.]**
* **`git diff main` is not this branch's diff.** `main` moved during the run. This branch's own
  diff is `git diff 683c8aff HEAD`: **16 files, +4057 / −29**, touching only
  `.softhouse/conformance.sh` (+201/−29 of it), my capture directory, and my handoff
  [VERIFIED].

---

## Follow-ups

* **`FU-T431-1` — does `T404` now close the registration-forgery class?** For the witness-side
  routes enumerated in the table above, **yes, on the evidence in this branch**: four fail-opens
  driven RED on `main` and refused after, with three healthy controls still ACCEPTED and a clean
  clean-tree bar. **For the class as a whole, no** — items 1, 2, 3, 4 and 6 of *"NOT closed"*
  are undriven, and every one of them is a bound on my search rather than on the defect.
  **The honest citation is: "T404 + T431 close the pathspec-ambiguity and pathspec-quoting
  routes on the witness side, driven; the newline, gitlink, case-sensitive-host and
  multiple-row routes are unreached, not unreachable."**
* **`FU-T431-2` — `.softhouse/bin/fire-program.sh:1406` cites `.softhouse/conformance.sh:3217-3220`
  for a sentence that is at `:3271`.** Already rotted on `main` before this branch
  [VERIFIED: `sed -n '3217,3220p'` on `main` prints the function header, not the quoted refusal].
  **Not fixed here: `fire-program.sh` is outside this task's `files_hint`** and the scope guard
  is a rejection criterion. Remedy of record: delete the range, cite
  `guard_guards_dir_registration` by name.
* **`FU-T431-3` — a citation guard for `conformance.sh`'s own line numbers.** Argued in-code and
  declined, with the cost stated. Someone may disagree; the argument is written down where the
  numbers used to be.
* **`FU-T431-4` — `patterns.md` has no entry for "freeze the drive before you run it".** The
  corruption is now named in `CORRECTIONS-to-T404-section-8.md` and in this drive's header, but
  `patterns.md` is outside this task's `files_hint` and I did not add a `P-` number. Recording a
  pattern is the pipeline's own step; this is the input to it.
