# T364 — INDEPENDENT review of T358 (T337's conditions C-1..C-5 on `guard_guards_dir_registration`)

**Subject:** branch `softhouse/T358-t323-conditions`, head **`aac9e12b`**
[VERIFIED: `git rev-parse softhouse/T358-t323-conditions` → `aac9e12b73000d2737e57cf2950f976867950a24`].
The task text as filed named `34303ea2`; that is a mid-drive head and I did **not** review it.
`aac9e12b` adds the resumed 29-arm drive transcript and the final bar transcript on top of it.

**Diff under review:** `git diff main...softhouse/T358-t323-conditions` — 9 files,
**+3145 / −48** [VERIFIED: `--stat`]. Executable surface is **one file**,
`.softhouse/conformance.sh` (**+336 / −48**), plus **17 added comment-only lines** in
`.softhouse/guards/ledgerguard/main.go`. Everything else is the red drive, its evidence and the
handoff.

---

## VERDICT: **ACCEPT-WITH-CONDITIONS.**

**T358 is a net large improvement and `main` is worse without it.** It closes a live
bar-bricking hazard that I reproduced on `main` myself, it removes a **false cardinal that is
live inside the grading instrument on `main` today**, and every gate it claims is unmoved I
re-measured myself and found unmoved. Nothing in it touches money, the ledger, a vector, a
`DEC-n`, the frozen adapter contract or a `user` gate.

**But I found two fail-OPENs T358 did not, and I DROVE BOTH THROUGH THE WHOLE BAR WITH
CONTROLS — they are proven, not argued.** Both defeat a guarantee the guard PRINTS in its own
output:

* **F-T364-1** — an unwired Go checker named **`main.go`**, in any subdirectory under
  `.softhouse/guards`, is reported **`INVOKED`** and the bar stays **GREEN**. The same file under
  a unique basename is refused. **`main.go` is the most likely filename for the next Go checker
  in a directory whose only Go checker is already called that**, and closing `.go` was C-3's
  whole point.
* **F-T364-2** — the rule *"a file may not vouch for itself"*, which the guard prints in its own
  refusal text, is defeated by a leading **`./`**. One line — `REACHED-BY ./<its own path>` —
  absolves any unwired checker, and the guard then prints `(verified: it names …)`.

Neither can produce a wrong answer about money or about any graded parity quantity — they
produce a wrong PASS about *the guard's own coverage*, which is the same class as the
`F-T337-3` defect T358 was commissioned to repair. That is why this is conditions and not
REJECT, and why the conditions are not optional.

**ONE THING THE DRIVER WILL MISREAD IF I DO NOT SAY IT HERE (§8.2).** T358 does **not** stop an
ordinary `.sh` fixture under `.softhouse/guards` from taking the bar to `exit 2` — **I planted
one on the merge result and it still exits 2.** T358 deliberately *keeps* the depth and instead
gives the tripping task a remedy it can apply **in its own edit grant**. **It converts an
unfixable refusal into a fixable one.** That is the right trade and T358 argues it properly, but
"the hazard is fixed" is not the same sentence as "nobody trips it again".

**ON THE MERGE QUESTION THE DRIVER ASKED — answered in full at §9.** Short form: **yes, merge
it, and merge it before the next task that touches `.softhouse/guards`.** I ran the bar on the
merge result myself — **EXIT 0, every pinned gate holding, `deadOccurrences=109` on a corpus of
1314** — and I ran it again with this review branch merged on top. Both green.

---

## 0. WHAT I RE-DERIVED RATHER THAN RELAYED

Everything numbered below is my own measurement, on my own `--no-hardlinks` clones, on this
host, with the reference oracle (Fineract) reachable. I accepted **no** transcript from the
branch. Where I could not verify something I say so.

### 0.1 EVERY PINNED GATE IN T358's §0 TABLE, RE-MEASURED BY ME

Two full bar runs, `bash .softhouse/conformance.sh` (never `sh`), sequential, never concurrent:
one on a fresh clone at `aac9e12b`, one on a fresh clone of `main`. Transcripts:
`evidence/00-t364-bar-on-t358-head.txt`, `evidence/01-t364-bar-on-main.txt`.

| gate | MAIN (my run) | T358 `aac9e12b` (my run) | T358 claimed | |
|---|---|---|---|---|
| exit | **0** | **0** | 0 / 0 | ✅ |
| probe line PRINTED (presence tested before value — P-84, see NOTE-3) | **1 occurrence**, `probe = up` | **1 occurrence**, `probe = up` | 1, `up` | ✅ |
| parity vectors | **PASS 46 / FAIL 0** | **PASS 46 / FAIL 0** | 46 / 0 | ✅ |
| inadmissible | **0** | **0** | 0 | ✅ |
| cells compared | **7884 graded** | **7884 graded** | 7884 | ✅ |
| LDG-05-openingbalance-accepted-empty-ledger | **PASS, 27 cells (8 money)** | **PASS, 27 cells (8 money)** | PASS 27 (8) | ✅ |
| LEDGER parity vectors | **7 == pinned 7** | **7 == pinned 7** | 7 | ✅ |
| LEDGER oracle-refusal vectors | **6 == pinned 6** | **6 == pinned 6** | 6 | ✅ |
| LEDGER money cells (int64 minor units) | **39 == pinned 39** | **39 == pinned 39** | 39 | ✅ |
| LEDGER declared exemptions | **0 == pinned 0** | **0 == pinned 0** | 0 | ✅ |
| wrong ledger implementations dying | **13 of 13** | **13 of 13** | 13/13 | ✅ |
| dead-path frontier | **deadOccurrences=109 == pin 109** | **deadOccurrences=109 == pin 109** | 109 | ✅ |
| fail-open census frontier | **11 == pinned 11**, all rows by path | **11 == pinned 11**, all rows by path | 11 | ✅ |
| host-state census | **18 == pinned 18**, by path and source line | **18 == pinned 18** | 18 | ✅ |
| P-number citations | VERDICT PASS; **directive MISDIRECTING 2 / UNDEFINED 4** | VERDICT PASS; **directive MISDIRECTING 2 / UNDEFINED 4** | unmoved | ✅ |
| GUARDS-DIR-REGISTRATION | `population=5 invoked=3 declared=2 invoked-by-nothing=0` | `population=6 invoked=3 declared=2 **reached-by=1** invoked-by-nothing=0` | 5 → 6, reached-by=1 | ✅ |

**Every figure T358 pinned re-derives on my own runs. No gate was weakened.** The two
non-pinned counts that legitimately move are the corpora: `1313 → 1303` tracked `.sh/.py`
(my `main` clone carries eight commits' worth of files T358's tree does not) and
`8076 → 7876` tracked paths, and `deadOccurrences` is **109 in both**, which is the point.

**Cost: I do NOT reproduce T358's direction and I am not going to pretend otherwise.**
T358 measured 74.97 s BEFORE and 72.58 s AFTER. I measured **76 s on `main`** and **79 s on
`aac9e12b`**, back to back on a host that was otherwise idle. The two measurements disagree in
*sign* and agree in *magnitude*, which is exactly T358's own stated conclusion — *"inside this
host's own run-to-run noise and NOT claimed as an improvement"*. **T358's honesty about the
noise width is what makes its cost claim survive my run; a claimed 2.4 s improvement would not
have.** [VERIFIED: `evidence/00-t364-bar-on-t358-head.txt`, `evidence/01-t364-bar-on-main.txt`.]

**The guard's OWN cost, re-measured by me.** T358 states a measured **0.23 s** in the
`run_guards` comment (T323 had `<=0.16 s` pre-widening; T337 measured 0.064 s for the operations
as they then stood). I re-executed every command the function runs, in order, on the delivered
tree, ten times: **0.297 s mean per iteration** — **under CPU contention from my own 28-arm
drive**, which T358's figure explicitly was not. Same order of magnitude, slightly above, and
the direction is explained by the contention. **The comment's figure is honest**, and it is the
right order of magnitude for the only decision it informs: a fifth to a third of a second
against a ~76 s bar dominated by `guard_reconciler_ownership` at ~30 s. *(This is a cost
measurement, not a correctness one; it is the one place in this review where I ran the guard's
operations outside the wired route, and nothing below rests on it.)*

### 0.2 THE LIVE HAZARD ON `main` IS REAL — I REPRODUCED T337's F-1 SELECTOR MEASUREMENT

On my clone of `main`, with one ordinary tracked test fixture planted at
`.softhouse/guards/ledgerguard/testdata/setup.sh`:

```
main's pathspec        git ls-files -- '.softhouse/guards/*.sh'      -> 6 members, INCLUDING the fixture
T358's pathspec        git ls-files -- ':(glob)…/**/*.sh' + .py + .go -> 7 members, including main.go
```

[VERIFIED: my own run, `evidence/02-t364-selector-measurement.txt`.] A git pathspec without
`:(glob)` is fnmatch **without** `FNM_PATHNAME`, so `*` crosses `/`. **T337 was right and the
hazard on `main` is live**, and I drove the whole bar on it — §8.

### 0.2b THE EXCLUSIVE HOLD ON `conformance.sh` HELD — RE-VERIFIED OVER THE WHOLE RANGE

T358 claims *"`main` has advanced by eight commits since my fork point and not one of them
touched this file."* **Both halves check out, and the property has since gotten stronger.**

```
git log --oneline be987aad..44fa1db4 | wc -l          ->  9   (the 9th is the driver's own
                                                              "T358 complete on branch" record,
                                                              so 8 at the moment T358 measured)
git diff --name-only be987aad 44fa1db4 -- .softhouse/conformance.sh .softhouse/guards  ->  EMPTY
git log --oneline be987aad..main       | wc -l        -> 24, then 26 an hour later
git diff --name-only be987aad main     -- .softhouse/conformance.sh .softhouse/guards  ->  EMPTY
```

[VERIFIED: my own runs.] **Over every one of the commits `main` has taken since T358 forked,
neither `conformance.sh` nor anything under `.softhouse/guards` moved.** The exclusive hold held
for the whole task and is still held.

**`main` MOVED TWICE WHILE I WAS REVIEWING** — 24 commits ahead of the fork point when I first
measured, 26 when I wrote the evidence file, tip `5a02ed5c` as I write this. I am not going to
pin that count, because it is a cardinal that rots faster than I can type it, and pinning it
would be the exact defect §0.3 is about. **The load-bearing fact is the one that does not rot:
the `git diff` over those two paths is EMPTY, and that is a property of the range, not of its
length.** It is also precisely why §9 exists.

### 0.3 THE ARITHMETIC I RE-DERIVED A THIRD TIME (F-T358-3)

Method as stated in the instrument: `git log --format= --name-only --diff-filter=A --
.softhouse/capture .softhouse/reviews`, directory keys `(capture|reviews)/<leaf>`, ids folded
case-insensitively off `^t[0-9]+`.

| corpus | directories | id-prefixed | **colliding ids** |
|---|---|---|---|
| **HEAD's ancestry** (my derivation at `aac9e12b`) | **160** | **139** | **2 — t255, t256** |
| **HEAD's ancestry** (the guard's own live readback, my bar run, same tree) | **160** | **139** | **T255 → 2 dirs, T256 → 2 dirs** |
| **full ref space** (`git log --all`, my derivation) | 174 | — | **3 — t255, t256, t286** |

**The historical query and the guard's live `git ls-files` readback agree TO THE ROW on my own
run**, which is the property T358 claimed and which makes the "read the readback, never retype
the number" remedy sound. T358 measured 159 / 138 / **2** at `34303ea2`; I measure 160 / 139 /
**2** at `aac9e12b`. The one-directory difference is the head moving between the two commits,
not a disagreement — **and both give TWO, which is the load-bearing figure.**

**F-T358-3 IS UPHELD, and I want to be precise about why, because it is a finding against my
own predecessor.** The sentence T337 offered to repair reads, on `main` today:

> `# The false-positive count of this predicate, over every evidence directory this program has`
> `# ever created, is ZERO; its true-positive count on the only event in class is ONE.`

T337's repair — *"Say `over HEAD's ancestry` and the sentence is true"* — scopes the **first**
clause correctly. It does nothing about the **second**, `on the only event in class is ONE`,
which had already gone false: `t255-frontier-rot` merged with its `OWNER-IS-T258-NOT-T255.md`,
and the guard has printed **two** collisions ever since. **Applying T337's one-line repair
verbatim would have shipped a sentence still carrying a false cardinal.** T358 is right.

**And this is not academic — the false cardinal is LIVE ON `main` RIGHT NOW.** My bar run on
`main` prints `T255 -> 2 directories` and `T256 -> 2 directories` in the same output as a
comment eleven hundred lines above that says *"exactly ONE"*
[VERIFIED: `evidence/01-t364-bar-on-main.txt`]. T358 deletes the cardinal rather than retyping
it for a third time and points the reader at the live readback. **That is the right answer and
I tested it: the readback exists, prints every run, prints one line per colliding id with its
`OWNER*.md`, and cannot rot because it is measured.** T337's full-ref-space count of **three**
also re-derives exactly (t255, t256, t286).

---

## 1. ATTACK 1 — THE OUT-OF-SCOPE EDIT TO `main.go`. **The driver's grade is right; the driver's REASON is wrong, and I refute it.**

**The facts, all verified by me.**

* T358's grant is `files_hint: [".softhouse/conformance.sh", ".softhouse/capture/t358-t323-conditions/"]`
  [VERIFIED: `.softhouse/tasks.json`, task `T358`]. `.softhouse/guards/ledgerguard/main.go` is
  **outside it**. The edit is out of scope as a matter of fact, not opinion.
* It is **+17 / −0, every line a `//` comment** [VERIFIED: `git diff main...` on that path].
  `gofmt -l` on the delivered file returns nothing; `go build ./...` in the module succeeds;
  `guard_ledger_invariants` and the 13 wrong-implementation mutants are byte-identical in my
  before/after bar runs. **Zero Go behaviour changed.** [VERIFIED: my own runs.]

**THE DRIVER GRADED IT A SCOPE NOTE "because it is one machine-read REACHED-BY row REQUIRED by
T358's own C-2 design". I REFUTE THE WORD *REQUIRED*, on two independent grounds, and I did not
inherit the judgement.**

1. **T358's own arm 23 proves the row is not required for the bar to be green.** Arm
   `T358-23-strip-row-FALLS-BACK-to-INVOKED` strips the row and asserts **exit 0, probe
   PRESENT**, `population=6 invoked=4 declared=2 reached-by=0 invoked-by-nothing=0`. I verified
   the mechanism statically and independently: after the DECLARATION TABLE is cut out of the
   haystack, the basename `main.go` still occurs on **two** non-comment lines of
   `conformance.sh` — `:319` of the comment-stripped text, `local ccsrc="…/ledgerguard/main.go"`,
   and `:332`, a `say` — so the invocation test absolves it regardless
   [VERIFIED: my own `grep -v '^[[:space:]]*#'` haystack, `evidence/03-t364-haystack-occurrences.txt`].
   **A row whose removal changes nothing was not required.**
2. **An in-grant alternative existed and T358 did not take it.** `main.go` could have been
   registered by adding one row to the `DECLARED` table *inside `conformance.sh`* — the file
   T358 holds exclusively and is already rewriting. The table already carries a `SUBJECT` row
   naming that exact path. That route is entirely within the grant.

**SO WHY IS IT STILL A NOTE AND NOT A VIOLATION? Because T358 gives a better reason than the
driver did, and it is internal to the very argument under review.** Registering `main.go`
through the table in `conformance.sh` would have been T358 doing *precisely the thing C-2
argues is the defect* — one task excusing another task's file from inside the serialised file —
in the same diff where it argues that is wrong. And the `REACHED-BY` direction would then have
had **zero live users**: exercised only inside the red drive, never asserted in a graded run,
`reached-by=0` forever. A direction no graded run has ever exercised is the shape P-22 is
about.

**MY GRADE: SCOPE NOTE UPHELD, ON CORRECTED GROUNDS.** It is a good design with a scope note,
not a bad design excusing itself — the discriminator being that the edit is comment-only,
disclosed in §9 of the handoff (under a P-number that does not mean what §9 uses it for — see
NOTE-3), reversible in one `git revert` of one hunk, and
argued rather than assumed. **But the driver must stop repeating the word "required".**
"My design requires me to write outside my grant" is the general form of every scope excuse
this program has ever had to refuse; the specific, checkable justification T358 actually gives
is not that, and the two must not be allowed to blur. **CONDITION C-T364-3 records this.**

---

## 2. ATTACK 2 — THE `REACHED-BY` DIRECTION. **The idea is sound. One of its four verifications is forgeable and I forged it; a second is satisfiable by mention.**

`REACHED-BY` is the load-bearing new idea: it moves the registration row out of the serialised
`conformance.sh` and into the member's own header, so the task that trips the guard can perform
the remedy in its own grant. **The architecture is right.** T337's F-T337-2 is a real gap —
both of T323's printed remedies required editing a file this program serialises to one holder
per batch, which is why T299's guard sat unwired for three fires — and moving the row to the
member is the T299 shape T337 endorsed. The alternatives T358 rejected (make it SOFT; move the
register to a shared `.softhouse` file; drop the depth) are rejected for reasons I checked and
agree with; the shared-registry rejection in particular is correct — it relocates the
serialisation point and grows into a suppression list.

The guard verifies four things about a `REACHED-BY` witness: it **exists**, is **tracked**, is
**not the member itself**, and **names the member's basename**. I attacked all four.

### F-T364-2 — **MEDIUM-HIGH, FAIL-OPEN.** The no-self-certification rule is defeated by a leading `./`.

The self-reference test is a raw string comparison
[VERIFIED: `.softhouse/conformance.sh:3385`, `elif [ "$self_wit" = "$rel" ]; then`]. Every other
step in the chain **normalises** the path and the comparison does not:

```
git ls-files --error-unmatch -- ./.softhouse/guards/ledgerguard/main.go   -> rc 0, prints .softhouse/guards/ledgerguard/main.go
git ls-files --error-unmatch -- .softhouse/guards/ledgerguard/../ledgerguard/main.go -> rc 0, same
```
[VERIFIED: my own run on the delivered tree, `evidence/04-t364-path-normalisation.txt`.]

So for an unwired member `M`, the single line

```
# GUARDS-DIR-REGISTRATION: REACHED-BY ./<M's own repo-relative path>
```

passes **all four** checks: `-f "$REPO_ROOT/./M"` resolves; `git ls-files --error-unmatch`
accepts it and normalises it; `"./M" != "M"` so the self-certification branch is never taken;
and the witness-names-the-member grep is satisfied **by the row's own text**, since the row
contains `M`'s basename. **One line, in a file the task already owns, absolves any unwired
checker in the canonical guards directory — and the guard then PRINTS
`REACHED-BY M — declared in its own header, reached by ./M (verified: it names M)`.**

This is the exact amnesty the direction was built to prevent, and the guard says so in its own
refusal text: *"A file may not vouch for itself — that is self-certification, which is exactly
the amnesty this direction was built to avoid."* **That sentence is false as implemented.**
T358's arm 20 drives the *exact* self-reference red and it does go red — but a guard that
refuses `M` and accepts `./M` has not closed the class, it has closed one spelling of it.

**Fail direction: fail-OPEN.** It cannot produce a wrong money answer. It produces a wrong PASS
about the guard's own coverage, available to any task, in-grant, in one line.

**Driven, not argued** — arms `F3-selfcert-via-dotslash` and `F4-selfcert-via-dotdot` in
`.softhouse/reviews/t364-review-t358/drive-forge-t364.sh`, against control
`F5-CONTROL-selfcert-exact`. Results at §7.

**REPAIR (this is CONDITION C-T364-1, and I did NOT apply it — `conformance.sh` is not mine).**
Compare the *resolved* path, not the typed one. The guard already runs
`git ls-files --error-unmatch` on the witness; make that call **print** and compare its output
to `$rel`, rather than comparing the raw string. That is the only place in the function where a
path is accepted without normalisation, and git is already doing the normalisation for free.

### F-T364-3 — LOW — the four verifications are all satisfiable by MENTION, not by REACH

`grep -qF -- "$base" "$REPO_ROOT/$self_wit"` matches anywhere in the witness, including a
comment, a string literal or a changelog line, and matches on a **substring** of the basename
(a member named `a.sh` is named by any witness containing `data.sh`). This is the identical
standard the pre-existing `CALLER` direction has always used, so it is **not a regression**,
and T358 states it plainly in the guard's printed output. **Recorded, not charged.** It matters
only in combination with F-T364-1 below.

### What I attacked and could NOT break

* A witness path outside the repository (`../../../etc/passwd`) — `-f` resolves, but
  `git ls-files --error-unmatch` refuses. **Fail-closed.** [VERIFIED.]
* A witness that is a directory — `[ ! -f ]` refuses. **Fail-closed.** [VERIFIED by reading;
  not driven through the bar.]
* A pathspec-magic witness (`:(glob)*`) — `-f` refuses first. **Fail-closed.** [VERIFIED by
  reading; not driven.]
* A malformed row with no witness at all (`REACHED-BY` and nothing after) — the anchored regex
  requires `[[:space:]]+[^[:space:]]+`, so it does not match, `self_row` is empty, and the
  member falls through to the invocation test. It is **silently ignored rather than refused**,
  but the member must then pass INVOKED or go red, so the net direction is **fail-closed**.
  Recorded because the warn branch T358 added for "NO witness path after it" is reachable only
  on the *doubled-marker* shape its arm 26 drives, which is narrower than the branch reads.
* `|| self_row=""` swallowing a genuine grep failure (unreadable member) — same analysis, net
  fail-closed.
* **The `REACHED-BY` / calibration interaction.** `REACHED-BY` `continue`s **before** the
  invocation test, so a tree in which every currently-INVOKED member acquired a `REACHED-BY` row
  would drive `invoked` to 0 and trip T323's `CALIBRATION FAILED` refusal
  [VERIFIED by reading: `conformance.sh:3526`, `if [ "$invoked" -eq 0 ]` → `return 1`]. That is an
  **over**-refusal — fail-closed — and it is the direction this guard is supposed to fail in.
  Recorded because the interaction is new and nobody has driven it; **it is not a defect.**
* **P-57 discipline in the new code.** The `grep -m1` is not in a pipeline, and the table cut is
  `grep -vF` over a **here-string**, which is not a pipeline either. `set -o pipefail` cannot
  invert either of them, and `grep -v` consumes all its input so there is no EPIPE surface.
  **T358's reasoning here is correct and I checked it rather than took it.**

---

## 3. ATTACK 3 — THE `INVOKED` FALLBACK. **T358's choice to pin rather than fix is defensible; its WRITE-UP of the gap is too narrow, and the gap is bigger than the arm it pinned.**

### F-T364-1 — **MEDIUM, FAIL-OPEN, and it is a hole in C-3, the very claim T358 was sent to repair.**

The invocation test is `case "$code" in *"$base"*)` over the comment-stripped harness, where
`base` is the member's **basename** [VERIFIED: `conformance.sh:3421`, `case "$code" in *"$base"*)`; `base` is set at
`:3344`, `base="${rel##*/}"`]. After T358's own DECLARATION-TABLE cut, the literal string `main.go` still occurs on
**two non-comment lines** of `conformance.sh` [VERIFIED, my own haystack:]

```
haystack :319  ( = conformance.sh:1484 )  local ccsrc="$REPO_ROOT/…/ledgerguard/main.go" cc ccsize
haystack :332  ( = conformance.sh:1497 )  say "conformance:   the cannotCatch const in …/main.go, which its"
```

**The line numbers on the left are the COMMENT-STRIPPED haystack's, which is what the guard
actually searches; the ones in brackets are `conformance.sh`'s own.** Neither is a call site. Both belong to a **different** guard that reads that file's *text*.

**T358 records this as a fact about ONE FILE — "`main.go` would read INVOKED off
`conformance.sh:1484`" — and pins it in arm 23. It is not a fact about one file. It is a fact
about the BASENAME, and therefore about every future member that has it.** T358 widened the
population to `.go` *specifically* so that an unwired Go checker cannot land unseen. A Go
command's entry point is conventionally named `main.go`; the only Go checker in this directory
today is named `main.go`; so **`main.go` is the single most likely filename for the next one** —
and any file with that name, in any subdirectory under `.softhouse/guards`, is absolved
automatically, with no declaration, no row, and no diff a reviewer would notice.

**T358's own arm 22 misses it by one identifier.** `T358-22-go-checker-unwired-NESTED` plants
`zz-t358-planted-checker.go` — a deliberately unique basename — and goes red. The arm proves
the population widened. It does **not** prove the class is closed, and the handoff's summary of
it, *"a `.go` checker one directory down can no longer land unseen"*, therefore **overstates
what was driven.** That is the same shape as the sentence T337 charged T323 with, one iteration
later.

**Driven, not argued** — arm `F1-unwired-main.go-ABSOLVED` against control
`F2-CONTROL-unwired-unique.go`. The two arms differ **only** in the planted file's basename.
Results at §7.

**JUDGEMENT ON THE CHOICE T358 MADE.** Declining to tighten `INVOKED` into an execution test was
**correct**, and for the reason T358 gives, which I verified rather than accepted: two of the
three genuinely-invoked members are reached through `bash "$g"` after a `local g=` assignment
[VERIFIED, my own haystack: `check-capture-namespace.sh` at `:680` and
`check-dead-path-frontier.sh` at `:745` are `local g=` assignments; only
`check-ledger-invariants.sh` at `:317` is a real `bash "$…"` call]. An execution test needs
dataflow this harness has no business growing, and both would go red on arrival. **T358's
corrected printed wording is exact to the row and replaces a sentence — `never a mention` —
that was false.** Documenting the gap in the instrument and pinning it in a deliberately-GREEN
arm is the right move for a gap you have decided not to close.

**What is NOT right is stopping the description at the one instance.** A registration guard
whose invocation test is satisfied by an unrelated mention is weaker than it reads — the task
brief's words — and T358 says so about `main.go` while its own C-3 summary says the opposite
about `.go` generally. **CONDITION C-T364-2.**

---

## 4. ATTACK 4 — F-T358-3 ADJUDICATED. **T358 is right, its remedy is the right one, and I re-derived the corpus a third time.** See §0.3.

The one thing I add: **deleting the cardinal rather than retyping it is testable, and I tested
it.** The remedy is only sound if the live readback the comment redirects to actually prints,
every run, without being asked. It does: my bar runs on **both** trees print `corpus <N>
tracked paths -> <D> evidence directories`, `<P> carry a t<n> id prefix`, and one `T<n> -> 2
directories` line per colliding id with the `OWNER*.md` that claims it and the `UNCLAIMED`
sibling. That is a measured source of truth with an owner, and a retyped copy is not.
**Deleting the cardinal is the right answer.**

T358 also repairs two further false sentences inside the instrument in the same pass, and both
repairs check out:

* `guard_dead_path_frontier`'s `removed=` refusal said *"the pin is outside T323's edit grant"* —
  false since T326 regenerated the pin. **A false statement inside a refusal message is the
  worst place for one**, because it is read by somebody who is already blocked. Replaced with a
  true one; `bad=1` still set, refusal path intact [VERIFIED: the removal enumeration, §5].
* `guard_capture_namespace`'s residual-risk note rested on *"reviews are overwhelmingly FLAT .md
  files"*. Review **directories** now exist — `t337-review-t323` is one, and
  **`t364-review-t358`, this one, is another** — so the premise is weakening and the note now
  says so. Correct, and I have just made it more so.

---

## 5. ATTACK 5 — F-T358-2, THE GUARD THAT SPUN THE BAR. **Reproduced independently. The response is adequate for the bug and INADEQUATE for the finding — FU-T358-1 needs to be a real task.**

**I reproduced the pathology myself, off the bar, with no oracle involved**
[`evidence/05-t364-quadratic-reproduction.txt`]:

```
haystack: .softhouse/conformance.sh = 310,358 bytes; comment-stripped = 94,346 bytes
DELIVERED IDIOM   grep -vF over a here-string, 2 rows:  0.1447 s   (94,164 bytes out)
REJECTED IDIOM    code="${code//"$row"/}",     2 rows:  STILL RUNNING AFTER 40 s — KILLED
```

**F-T358-2 IS REAL.** Bash pattern substitution over a ~94 KB string does not complete in 40
seconds on two rows; the delivered `grep -vF` here-string form does the identical job in 145
milliseconds. The fix is correct, and the P-57 property it was chosen to preserve is genuinely
preserved — a here-string is not a pipeline.

I also verified the cut is **exact**: it removes lines 953 and 954 of the comment-stripped
haystack and nothing else — the `DECLARED="…` assignment and its continuation — 2 lines,
182 bytes [VERIFIED: my own diff of the cut, `evidence/03-t364-haystack-occurrences.txt`].
The vacuity check (`[ -z "$code" ]` → `return 1`) is present and is the right shape.

**THE FINDING, AS OPPOSED TO THE BUG, IS NOT ADEQUATELY ANSWERED, AND I THINK T358 KNOWS IT.**
T358's own three-point analysis is correct and I confirmed each point: `bash -n` is clean on a
quadratic substitution (I ran it); the standalone route is clean because the pathology is a
function of a haystack only the real `conformance.sh` supplies; and **nothing in the bar
measures the bar**. `run_guards` carries a hand-written cost comment per guard — I read them:
`0.23 s`, `0.4 s`, `1.3 s`, `30.3 s` — and **not one of them is checked by anything**. T358
changed `<=0.16 s` to `0.23 s` in that comment, which makes the comment true today and leaves
it exactly as unenforceable as it was.

A guard whose comment says 0.23 s and whose real cost is unbounded is caught by a human
noticing a run that should have taken 75 seconds and has not returned in ten minutes. That is
not an instrument. **And the consequence is the same failure T337's C-2 is about, one level
down: a grading instrument nobody will wait for gets bypassed, which is indistinguishable from
switching it off.**

**MY JUDGEMENT: T358's response is adequate for the defect and NOT adequate for the class, and
naming `FU-T358-1` without raising it leaves the class open.** T358 was right not to build a
timing gate inside a task it did not hold the design argument for — a wall-clock ceiling that
fires on a loaded host is a flaky bar, which is its own way of getting the bar bypassed, and
T358 says so. **But "named rather than left implied" is not the same as "raised".**
**CONDITION C-T364-4: FU-T358-1 becomes a filed task, with the flakiness argument as its first
design constraint.** A per-guard elapsed-time *record* that is printed and censused — the shape
this program already uses for every other frontier, pinned by path and not by threshold — would
have caught this in 75 seconds and does not fire on a loaded host.

---

## 6. ATTACK 6 — COMPOSITION. **Verified: the T358 drive RUNS T323's drive, and a MISSING T323 drive is a hard failure.**

Read out of the delivered script, `.softhouse/capture/t358-t323-conditions/drive-red-t358.sh:287-300`:

```bash
T323_DRIVE="$SCRATCH/.softhouse/capture/t323-wire-the-unwired-guards/drive-red-t323.sh"
if [ -f "$T323_DRIVE" ]; then
  if bash "$T323_DRIVE" "$SCRATCH"; then  … PASSES=$((PASSES+1))
  else                                      … FAILS=$((FAILS+1)); fi
else
  echo ">>> ARM SET 1: T323's drive is MISSING. That is a REFUSAL, not a skip …"
  FAILS=$((FAILS+1))
fi
```

and the script's last line is `[ "$FAILS" -eq 0 ]`, so any of the three branches other than
"present and passed" makes the drive exit non-zero. **A missing T323 drive is a refusal, not a
silent skip** [VERIFIED by reading and by the drive I ran myself, which entered the `-f` branch
and ran all fifteen of T323's arms]. That is the difference between reuse and a hole, and T358
built it the right way round: T323's drive stays authoritative for its own arms and cannot rot
against a copy.

The `arm()` harness is not rigged. Each arm asserts **exit code AND probe presence AND a narrow
refusal marker**, all three, and the markers are refusal sentences rather than permissive
patterns. **Presence-before-value is honoured structurally** — the probe line's *presence* is
established by `grep -q 'reference oracle (.*) probe = '` before any value is read. That rule is
**P-84**, not P-83; T358's drive cites P-83 for it, and so does my own brief. See NOTE-3. The green control comes
first (P-50) and asserts the widened census line **verbatim**, so a selector that silently
stopped matching fails there.

### THE MUTATIONS ARE NOT RIGGED — I READ ALL THIRTEEN BEFORE RUNNING THEM

Looking specifically for an arm that passes for the wrong reason. I did not find one, and three
things are better than they had to be:

* **Four mutations assert their own PRECONDITION** before the bar is run — arms 17, 23, 24 and
  25 [VERIFIED: `grep -cE '^\s*(!|\[ ! )'` over the drive → **4**], and the
  `main_names_fixture` helper carries the positive form (`grep -qF -- "$FIXTURE_LEAF"
  "$MAIN_ABS" || return 1`) —
  e.g. arm 17 ends `! grep -qF -- "$FIXTURE_LEAF" "$MAIN_ABS" || return 1`, i.e. *"fail this arm
  if main.go DOES already name the fixture"*, so "the witness does not name the member" is
  established rather than assumed; arm 23 asserts the row is actually gone; arm 25 asserts the
  pin is actually zero-length. A mutation that failed to apply reports `MUTATION FAILED TO
  APPLY` and counts as a FAIL, never as a pass.
* **Arm 24 discloses its own confound.** Renaming `main.go` inside `check-ledger-invariants.sh`
  also breaks `guard_ledger_invariants`, which refuses earlier in `run_guards`. The arm says so
  in its own comment and narrows its marker to *the registration guard's* sentence, so it still
  proves what it claims. That is the honest way to ship an arm with a confound.
* **The directive string is spelled ONCE** (`MARKER_WORD="GUARDS-DIR-REGISTRATION:"`) and
  assembled by a `directive()` helper, never retyped in an arm — so no arm can pass because it
  and the guard happen to agree on a typo.

### One cardinal that does NOT re-derive — NOTE, not a charge

**T358 claims "29 arms / 29 PASS". The distinct-arm count is 28.** Arm set 1 contributes T323's
**15** arms; arm set 2 contributes **13**; 15 + 13 = **28**. The script's own `PASSES` counter
increments once more for the *aggregate* arm-set-1 result — its summary line says so in as many
words, `"14 passed, 0 failed. (arm set 1 counts as one.)"` — and 15 + 14 = 29 double-counts the
aggregate. [VERIFIED: the committed transcript
T358's own `capture/t358-t323-conditions/evidence/20-red-drive-DELIVERED-TREE-29-arms.txt`
prints `T323 RED DRIVE: 15 passed` and
`T358 RED DRIVE: 14 passed`, and my own regeneration prints the same.] Nothing is missing and
nothing is unproven; the *label* is one too many. I record it only because this is a review of a
task whose central finding is a cardinal that rotted three times, and the same discipline has
to apply to its own.

---

## 7. THE ARMS I REGENERATED MYSELF (P-22)

*"A guard, a canary, or a control that cannot fire is worse than none, because it is believed."*
I accepted no transcript. Fresh `git clone --no-hardlinks` of `aac9e12b`, every arm through
**the whole bar** via `bash .softhouse/conformance.sh`, never a guard standalone.

### 7.1 T358's OWN DRIVE, REGENERATED IN FULL — **28 arms, 28 PASS, 0 FAIL, `DRIVE RC=0`**

`bash .softhouse/capture/t358-t323-conditions/drive-red-t358.sh <scratch>` against a fresh
`git clone --no-hardlinks` of `aac9e12b`. **I ran the drive T358 committed, unmodified.**
Full transcript: `evidence/10-t364-t358-drive-REGENERATED.txt`.

* **ARM SET 1 — T323's fifteen arms, run unmodified against T358's `conformance.sh`: 15 PASS,
  0 FAIL.** `>>> ARM SET 1: T323 DRIVE PASSED in full.` **Nothing T323 pinned moved because T358
  widened a population**, and that set contains both of T323's *green* arms
  (`00-GREEN-CONTROL`, `T299-02-same-collision-DOCUMENTED`), so a bar that had started refusing
  everything would have failed the set rather than passed it.
* **ARM SET 2 — T358's own thirteen arms: 13 PASS, 0 FAIL.** Every red arm: `exit=2` **AND**
  `probe=ABSENT` **AND** its narrow refusal marker. Every green arm: `exit=0` **AND**
  `probe=PRESENT` **AND** `VERDICT: PASS`.

**P-84 held behaviourally on all 26 red arms** — not one printed a probe line — which is the
empirical half of the structural proof at §10.

**The load-bearing arm, read out of MY OWN transcript.** `T358-16-nested-fixture-DECLARED-in-grant`:

```
T358-16-nested-fixture-DECLARED-in-grant   exit=0 (want 0)  probe=PRESENT (want PRESENT)  marker=YES  >>> PASS

conformance:     REACHED-BY .softhouse/guards/ledgerguard/main.go — declared in its own header, reached by
conformance:     REACHED-BY .softhouse/guards/ledgerguard/testdata/setup.sh — declared in its own header, reached by
conformance:   GUARDS-DIR-REGISTRATION: population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

**That is C-2's whole claim, proven through the wired route by me: the same tree that refuses at
arm 15 goes green at arm 16 on TWO LINES, both inside the `ledgerguard` module — one
`REACHED-BY` row in the fixture's own header, one line in `main.go` naming the fixture.
Neither touches `.softhouse/conformance.sh`. The tripping task can perform the remedy inside its
own edit grant.** T337's F-T337-2 is answered.

### 7.2 MY OWN FORGE DRIVE — **6 arms, 6 matched my prediction, and THREE OF THOSE PREDICTIONS WERE FAIL-OPENS**

`.softhouse/reviews/t364-review-t358/drive-forge-t364.sh`, same discipline: whole bar every arm,
exit **and** probe presence **and** marker, green control first. The committed script is
**byte-identical** to the one I ran (`cmp`). Transcript: `evidence/11-t364-forge-drive.txt`.

**READ THE `want` COLUMN. F1, F3 and F4 ASSERT `exit 0` BECAUSE I PREDICTED A FAIL-OPEN. A PASS
ON THOSE THREE IS A DEFECT FOUND, NOT A GUARD WORKING.**

| arm | exit | probe | census line | what it establishes |
|---|---|---|---|---|
| `F0-GREEN-CONTROL` | **0** | PRESENT | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0` | the control; the bar is not refusing everything |
| **`F1-unwired-main.go-ABSOLVED`** | **0** | PRESENT | `population=7 **invoked=4** … invoked-by-nothing=0` | **F-T364-1 PROVEN.** A genuinely unwired Go checker at `.softhouse/guards/zz-t364-checker/main.go` is reported **`INVOKED`** and the bar stays **GREEN** |
| `F2-CONTROL-unwired-unique.go` | **2** | ABSENT | `population=7 … **invoked-by-nothing=1**` | the SAME file under a unique basename is refused. **The basename is the whole difference** |
| **`F3-selfcert-via-dotslash`** | **0** | PRESENT | `population=7 … **reached-by=2** … invoked-by-nothing=0` | **F-T364-2 PROVEN.** One line, `REACHED-BY ./<its own path>`, and the guard prints `REACHED-BY … zz-t364-selfcert.sh — declared in its own header, reached by` — **a file vouching for itself** |
| **`F4-selfcert-via-dotdot`** | **0** | PRESENT | `population=7 … **reached-by=2**` | the same, via `…/ledgerguard/../<its own leaf>`. Two spellings, both accepted |
| `F5-CONTROL-selfcert-exact` | **2** | ABSENT | `declares REACHED-BY ITSELF` | T358's arm 20 fires correctly on the *exact* spelling. **So the check works and my two spellings walk around it** |

`T364 FORGE DRIVE: 6 arms matched their prediction, 0 did not.`

**Both findings are controlled, not merely observed.** F1 vs F2 differ in exactly one identifier
— the planted file's basename — and F3/F4 vs F5 differ in exactly one prefix on the witness
path. **Nothing else in the tree changed between an arm and its control.**

**One prediction I made and had to abandon, recorded because a review should say when it was
wrong.** I expected `F4` to be confounded by `guard_dead_path_frontier` — the row's literal
`…/ledgerguard/../zz-t364-selfcert2.sh` is not a path `git ls-files` lists, so I thought the
census would score it a dead path and refuse for the wrong reason. **It did not**
(`deadOccurrences` did not move in that arm), so F4's `exit 0` really is the registration guard
accepting the row. The confound would have made the arm useless; it did not materialise.

---

## 8. THE HAZARD AND THE REMEDY, DRIVEN END TO END

**Three bar runs, all mine, all `bash`, all through the whole harness.**

### 8.1 THE HAZARD ON `main` IS REAL — one ordinary tracked fixture bricks every graded run

Clone of `main`, one tracked file planted at `.softhouse/guards/ledgerguard/testdata/setup.sh`
containing `#!/bin/sh` and an `echo`:

```
conformance: guard_guards_dir_registration: .softhouse/guards/ledgerguard/testdata/setup.sh IS INVOKED BY NOTHING.
conformance:   GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 invoked-by-nothing=1
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
EXIT=2       probe line count: 0 — ABSENT
```
[VERIFIED: `evidence/14-t364-hazard-on-main-DRIVEN.txt`.] **T337's F-T337-1 and the driver's
premise are both correct.** `.softhouse/guards/ledgerguard/` is the home of the money guard this
program cares most about, and a shell fixture beside a Go test is not an exotic input.
**Fail-CLOSED — it cannot manufacture a PASS — which is the only reason leaving it on `main` was
survivable.**

### 8.2 **WHAT T358 DOES AND DOES NOT DO ABOUT IT — THE DRIVER MUST NOT MISREAD THIS**

I planted the **identical** fixture on the **merge result** (`main` + T358):

```
conformance: guard_guards_dir_registration: .softhouse/guards/ledgerguard/testdata/setup.sh IS INVOKED BY NOTHING.
conformance:     GUARDS-DIR-REGISTRATION: REACHED-BY <witness path, repo-relative>
conformance:   GUARDS-DIR-REGISTRATION: population=7 invoked=3 declared=2 reached-by=1 invoked-by-nothing=1
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
EXIT=2       probe line count: 0 — ABSENT
```
[VERIFIED: `evidence/15-t364-hazard-on-merge-result.txt`.]

# **STILL EXIT 2. T358 DOES NOT STOP THE FIXTURE TRIPPING THE GUARD, AND IT NEVER CLAIMED TO.**

The task brief says the hazard *"will brick a graded run"* and that T358 *"has already fixed it
on its branch"*. **Both halves are true, but not in the way a fast reader will take them.** T358
**deliberately keeps the depth** — narrowing the pathspec to one directory level would buy the
fix by no longer looking, trading T337's F-1 for a larger F-3, and T358 argues that at length
and declines T337's one-token patch on exactly that ground. **What T358 removes is not the
refusal. It is the DEAD END.**

* On `main`, the tripping task reads a refusal whose only two remedies are edits to
  `.softhouse/conformance.sh`, a file this program serialises to one holder per batch. **It must
  wait for a fire that grants it that file.** That is the bricking.
* On the merge result, the same refusal now prints, first, **a remedy the task can perform in its
  own grant** — one `REACHED-BY` line in the new file's own header — and my arm 16 regeneration
  (§7.1) proves that remedy takes the whole bar back to `exit 0` with the probe present.

**So the correct statement for the driver's records is: T358 converts an unfixable refusal into a
fixable one.** A task that adds a shell fixture under `.softhouse/guards` will still see
`EXIT 2` on its first run, and must still add one line — it just no longer needs somebody else's
edit grant to do it. **Merging T358 does not mean nobody trips this guard again.**

---

## 9. **THE MERGE QUESTION, ANSWERED PLAINLY — the driver will act on this**

### 9.1 IS `softhouse/T358-t323-conditions` SAFE TO MERGE INTO CURRENT `main`?

# **YES. MERGE IT, AND MERGE IT BEFORE THE NEXT TASK THAT TOUCHES `.softhouse/guards`.**

Four things, each measured:

1. **The exclusive hold held, over the whole range, not just the eight commits T358 saw.**
   `git diff --name-only be987aad main -- .softhouse/conformance.sh .softhouse/guards` is
   **EMPTY** across every commit `main` has taken since T358 forked (§0.2b). Neither file
   T358 edits has moved on `main`. A merge cannot silently drop a gate here, because there is
   nothing on `main`'s side of those two paths to drop.
2. **The merge is clean.** I test-merged `aac9e12b` into a scratch clone of `main` at
   **`635c6f60`** and got **9 files, +3145 / −48, no conflict, rc 0**
   [VERIFIED: `evidence/12-t364-merge-test.txt`]. `main` has advanced past that commit while I
   worked; since none of the advance touches either path T358 edits, the merge cannot acquire a
   conflict there — but **the driver merges against whatever `main` is then, and §9.2 is what
   settles it**, not this test.
3. **The merge result passes the bar — I ran it, I did not compute it.** Numbers in §9.2.
4. **`main`'s status quo is strictly worse than the merged result.** `main` today (a) refuses
   every graded run for any task that adds an ordinary `.sh` under `.softhouse/guards` — driven,
   §8 — and (b) carries a **false cardinal inside the grading instrument**, *"exactly ONE
   colliding id"*, contradicted by the guard's own readback **in the same run** (§0.3). Both are
   removed by the merge.

**The two fail-opens I found (F-T364-1, F-T364-2) do not change that answer, and I want the
reason on the record rather than asserted:**

* **F-T364-1 (`main.go` auto-absolved) is NOT a regression.** On `main` the population is `.sh`
  only, so a Go checker named `main.go` is **not a member at all** — invisible by construction,
  which is T337's F-T337-3 fail-open. After the merge it is a member that is wrongly absolved.
  **Same outcome for that one basename, strictly better for every other `.py` and `.go`
  basename.** The merge improves the class and fails to close one spelling of it.
* **F-T364-2 (`./` self-certification) IS new**, because `REACHED-BY` is new. But what it
  replaces is worse: on `main` an unwired file under `.softhouse/guards` has **no lawful remedy
  at all** — it bricks every graded run and the tripping task may not open the file that would
  fix it. T358 trades that for an in-grant remedy that a *deliberately* self-referential
  one-liner can forge, and the forged row is a `REACHED-BY ./<itself>` line sitting in the diff a
  reviewer reads. **Net improvement, condition filed as C-T364-1.**

### 9.2 WHAT THE DRIVER MUST RE-RUN ON THE MERGE RESULT BEFORE BELIEVING IT

**T358 is right that its own before/after pair does not answer this, and it says so.** Both of
its columns are taken at the fork point `be987aad`; that pair isolates *T358's effect* and says
nothing about *the merge*. **This is P-83 exactly** — *"TWO INDEPENDENT MOVEMENTS OF ONE PINNED
NUMBER RECONCILE BY RUNNING, NEVER BY ARITHMETIC"* [VERIFIED: `.softhouse/patterns.md:2806`] —
and it is the pattern whose ordinal both T358's drive and my own brief spend on something else
(NOTE-3).

**I DID THAT RUN, so the driver does not have to take it on faith.** `bash
.softhouse/conformance.sh` on the merge of `main` + `aac9e12b`:

```
=== MERGE RESULT (main @ 635c6f60  +  aac9e12b) ===
EXIT=0   WALL=75s   probe line: 1 occurrence, PRESENT, reading `up`

conformance:   GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0
conformance:   namespace: PASS -- every task-id prefix shared by two directories carries its OWNER record.
conformance:   T316-DEADPATH-CENSUS: corpus=1314 deadFiles=76 deadOccurrences=109 …
conformance:   … frontier 11, pinned at 11
conformance:   … literal /tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 18
    parity vectors          PASS 46   FAIL 0
    inadmissible            0
    cells compared          7884 graded
    ledger cells compared   142 graded, of which 39 are MONEY cells in int64 minor units
    ledger inadmissible     0
conformance:   exemption census READ: LEDGER parity vectors = 7 == pinned 7
conformance:   exemption census READ: LEDGER money cells compared = 39 == pinned 39
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```
[VERIFIED: `evidence/13-t364-bar-on-merge-result.txt`, complete and unedited.]

**THE MERGE RESULT IS GREEN AND EVERY PINNED GATE HOLDS ON IT.** And note the number that could
only have come from a run: **`corpus=1314`** — `main`'s 1313 plus T358's one new tracked `.sh` —
with **`deadOccurrences=109`, equal to the pin.** Two independent movements of one pinned corpus,
reconciled by running.

**THE NUMBER TO WATCH IS `deadOccurrences`, AND IT IS THE ONE THAT CANNOT BE COMPUTED.** T358
adds one tracked `.sh` to T316's corpus; `main` independently added ten more files to it since
the fork point (my two clones measure the corpus at **1303** and **1313**). Those are two
independent movements of one pinned number. `109 + 0 + 0 = 109` is an *arithmetic* answer and
P-83 says it is not an answer. **The run above is the answer.**

**THE DRIVER'S RE-RUN CHECKLIST ON THE MERGE COMMIT** — every item is a line the bar prints, and
the first three are the ones a merge can move:

1. `T316-DEADPATH-CENSUS: … deadOccurrences=<N>` — must equal the pin. *Two independent
   movements; only a run reconciles them.*
2. `CENSUS fail-open instruments … frontier <N>, pinned at <N>` and
   `CENSUS host state … <N>, pinned at <N>` — same reasoning, same corpus growth.
3. `namespace: PASS` — `t358-t323-conditions` is a new evidence directory and
   `t364-review-t358` is another. **AND NOTE T358's WARNING, WHICH I VERIFIED:** over the full
   ref space there is a **third** colliding id, `t286`, whose second directory lives on an
   unmerged rescued-WIP branch. **Merging that branch turns this bar RED on arrival**, and the
   remedy is one `OWNER*.md` inside a directory that branch already owns. That is a true
   positive, not a false one — but a driver planning merges needs to know it is queued.
4. `GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0`
   — the `reached-by=1` is the new direction's only live user; if it reads `0`, the row on
   `main.go` was lost in the merge.
5. `VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`, `inadmissible 0`, LEDGER
   `7 / 6 / 39 / 0`, `13 of 13` wrong implementations dying, LDG-05 `PASS 27 cells (8 money)`,
   and the probe line **PRESENT** reading `up`.
6. **`bash`, never `sh`.** `sh .softhouse/conformance.sh` still exits **3** on the delivered tree
   [VERIFIED by me], and a `3` is a refusal to run, not a verdict.

**WHAT I DID NOT DO, AND WHAT I THEREFORE CANNOT PROMISE.** I did **not** re-run the 28-arm red
drive against the merge result — only against `aac9e12b`. The arms exercise the guard's refusal
paths, which live entirely in `conformance.sh`, and that file is byte-identical in the two trees
[VERIFIED: the merge changed nothing on `main`'s side of it], so I expect the drive to behave
identically — **but "I expect" is not "I measured", and a driver who wants the drive green on the
merge commit must run it.** It costs about ninety minutes.

---

## 10. THE NON-NEGOTIABLES, AND WHAT SILENCE MEANS

Checked, so that finding nothing is distinguishable from not looking.

* **Money is integer minor units.** **CLEAN.** No monetary code path, struct field, schema
  column, API field or test fixture is touched. The only numbers T358 introduces are counters of
  files (`total`, `invoked`, `decl_ok`, `selfdecl`, `unwired`). I grepped every added line for
  `float`/`double`/`decimal`/`big.Float`/`math.Round`/`/ 100`/`* 100`: **the only hits are inside
  the committed bar TRANSCRIPTS**, where they are the harness's own no-float guard reporting its
  census, and not one is in an added code line [VERIFIED: `git diff main... | grep '^+' | grep -i …`].
  The 39 int64-minor-unit LEDGER money cells, the 46 parity vectors and the 13
  wrong-implementation mutants are identical in my before and after runs.
* **Append-only ledger / derived balances / holds.** **NOT TOUCHED.** No ledger code, no vector,
  no schema.
* **`Idempotency-Key`.** **NOT TOUCHED.** No money-movement path in the diff.
* **Frozen adapter contract.** **INTACT.** No file under the contract, no `DEC-n`, no
  `program.json`, no `patterns.md`, no `gates.md`, no vector is in the diff
  [VERIFIED: `git diff --name-only main... | grep -iE 'dec-|contract|adapter|program.json|patterns.md|gates'` → empty].
* **No ratified DEC-n silently changed.** **CONFIRMED** — none is in the diff at all.
* **PostgreSQL only; Oracle Database prohibited.** No driver, dialect or port is touched. The
  word "oracle" throughout T358 and throughout this review means the **Fineract reference
  implementation**.
* **`user` gates.** None approached: no cutover, no regulatory sign-off, no licence fact, no
  deposit activation, no contract change.
* **Syntax and build.** `bash -n` on the delivered `conformance.sh`: **clean**. `gofmt -l` on the
  delivered `main.go`: **empty**. `go build ./...` in `ledgerguard`: **OK**. `sh .softhouse/conformance.sh`
  still refuses at **exit 3**, as T358 claims. [All VERIFIED by me on the delivered tree.]
* **No refusal path was deleted.** T358's enumeration of **13 non-comment removals** re-derives
  exactly: 48 removed lines, **35 comments, 13 non-comments**, and I read all thirteen — every
  one is a `warn`/`say`/assignment replaced in place. Structurally: `bad=1` sites go **13 → 18**
  (the five new REACHED-BY refusals) and `return 1` sites **59 → 60** (the table-cut vacuity
  check). **No `warn` that could refuse, no `return 1`, no `exit`, no guard registration was
  removed.** [VERIFIED: my own counts on both blobs.] T358 correctly declines to claim T337's
  subset check, which cannot hold for a diff that rewrites 48 lines by design, and substitutes
  an enumeration — the stronger instrument.
* **P-84, re-verified STRUCTURALLY by me on the delivered file, not from transcripts.**
  `run_guards` is defined at `:3554`; `grep -nE '^[[:space:]]*run_guards[[:space:]]*$'` returns
  **exactly one line, `:4032`**, a bare command inside `main_grade` — not a subshell, not a
  command substitution — so an `exit` inside it terminates the shell. `probe_oracle` is invoked
  at exactly one site, `:4057`, and the probe line is printed at exactly one place, `:4058`,
  both strictly downstream. **There is no path on which a HARD guard fails and the probe line is
  printed.** [VERIFIED by me on the delivered blob.]
  **One P-45 citation imprecision:** T358's note says the terminating `exit` is at `:3567`. That
  is the `guard_graded_root_is_this_tree` **short-circuit** exit; the exit a failed
  `guard_guards_dir_registration` actually takes is the **tally** exit at **`:3590`**. Both are
  inside `run_guards`, both are upstream of `:4032`'s return, so **the structural conclusion is
  unaffected** — but a P-45 citation names the line that executes, and this one names its
  neighbour. Mechanical. **NOTE, not a condition.**
* **P-86.** Every P-number T358 cites carries its rule text and the `patterns.md` line resolves:
  P-57 at `:1654`, P-84 at `:2813`, P-45 at `:1503`, P-70 at `:1931`. **All four verified by me
  by reading those lines.**
* **The uncommitted standalone fast-check.** `git ls-files | grep -i fastcheck` returns **only**
  T358's `capture/t358-t323-conditions/evidence/30-standalone-fastcheck-NOT-EVIDENCE.txt` —
  the harness itself is genuinely not
  committed, and its transcript is labelled NOT-EVIDENCE in its own first line. **I traced every
  numbered claim in the handoff to either the whole-bar drive, a committed bar transcript, or a
  measurement I reproduced. Nothing rests on the fast-check.** T358's stated reason for not
  committing it — it hard-codes `/tmp` paths, which is exactly what
  `guard_no_host_state_in_lint_corpus` pins at 18 sites — is correct and self-consistent.
* **Committed evidence is genuine and non-vacuous.** The BEFORE transcript prints
  `population=5 … invoked-by-nothing=0` and `corpus=1302 … deadOccurrences=109`; the AFTER
  prints `population=6 … reached-by=1` and `corpus=1303 … deadOccurrences=109`; both print
  `VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`. They are internally consistent, they
  match the handoff, and they match my own independent runs.

### What I did NOT check — stated, because "not found" is a statement about the search

* I did **not** audit whether T299's, T316's or T319's guards are semantically **correct**. I
  checked only that the wiring reaches them, that they fail closed, and that they cannot print a
  probe line.
* I did **not** run `--prove` or `--self-test`; neither is in this diff and neither goes through
  the graded probe path.
* I did **not** re-open anything T337 settled (T323's four refutations, the near-revert, T304's
  79 %, the hardcoded `--selftest`). I found no reason to disturb any of it, and T358 did not
  disturb it either.
* I drove the witness-is-a-directory and witness-is-pathspec-magic cases by **reading**, not
  through the bar. Both are fail-closed by inspection; neither is asserted as driven.

---

## 10a. THIS REVIEW AGAINST ITS OWN RULES

A reviewer who charges an author with turning the bar red, and then turns the bar red, has not
read his own review. **So I ran it.** `main` + T358 + **this review branch**, merged in a scratch
clone, whole bar:

```
=== main + T358 + T364, EXIT=0, probe line 1 occurrence PRESENT ===
conformance:   T316-DEADPATH-CENSUS: corpus=1315 deadFiles=76 deadOccurrences=109 …   == pin
conformance:   … frontier 11, pinned at 11
conformance:   … literal /tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 18
conformance:   namespace: PASS
conformance:   GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0
    parity vectors          PASS 46   FAIL 0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```
[VERIFIED: `evidence/16-t364-SELFCHECK-main-plus-T358-plus-T364.txt`.]

**AND I RAN IT A SECOND TIME ON MY FINAL COMMIT, AGAINST A NEWER `main`** (`main` moved from
`635c6f60` to `f8ef2cd6` while I wrote this, and its corpus grew from 1314 to 1340):

```
=== main @ f8ef2cd6 + T358 + T364 FINAL, EXIT=0, probe line 1 occurrence PRESENT ===
conformance:   T316-DEADPATH-CENSUS: corpus=1340 deadFiles=76 deadOccurrences=109 …   == pin
conformance:   … frontier 11, pinned at 11 ; … /tmp path to a name: 18, pinned at 18
conformance:   namespace: PASS
conformance:   GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0
    parity vectors          PASS 46   FAIL 0        inadmissible  0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```
[VERIFIED: `evidence/17-t364-SELFCHECK-FINAL-newer-main.txt`.]

**THAT IS THE STRONGER RESULT AND THE DRIVER SHOULD USE IT: T358 merges green against TWO
DIFFERENT `main` TIPS, 26 commits apart in corpus terms (1314 → 1340), with
`deadOccurrences=109` on both.** It still is not a substitute for the driver's own run on the
actual merge commit — `main` will have moved again — but it is two independent confirmations
rather than one, and it is the direct empirical answer to P-83's question.

**`corpus` 1314 → 1315** — my `drive-forge-t364.sh` is a tracked `.sh` and joins T316's corpus
like anybody else's — **and `deadOccurrences` stays 109, the frontier stays 11, and the
host-state census stays 18.** Two hazards I had to design around and both are measured clean:

* **Host state.** My first draft assigned a literal `/tmp` transcript path to a variable, which is
  exactly what `guard_no_host_state_in_lint_corpus` pins at 18 sites. I caught it before running
  and rewrote it to `mktemp` with the transcript directory as an argument — the same shape T358's
  own drive uses, and the same reason T358 left its fast-check uncommitted.
* **Dead paths.** My first draft wrote the phrase `.softhouse/-ROOTED` unquoted in a comment,
  which is a `.softhouse/`-rooted literal that resolves to nothing and would have put a row on
  T316's frontier. Quoted.

Neither would have been caught by `bash -n`, and neither is visible until the file is **tracked
and the whole bar is run** — which is F-T358-2's lesson, arriving one review later.

**Namespace (T299):** `T364` prefixes exactly one directory, `.softhouse/reviews/t364-review-t358`.
No collision, no `OWNER*.md` needed, guard PASS on the merged tree.

**Money:** this review adds one `.md`, one `.sh` that plants shell and Go stubs in a scratch
clone, and thirteen `.txt` transcripts. **No monetary code path, schema, fixture or vector is
touched by anything I wrote.**

---

## 10b. NOTES — small, true, and none of them a blocker

Recorded because this is a review of a task whose central finding is a cardinal that rotted
three times, and the same discipline has to apply to its own work and to mine.

**NOTE-1 — the arm count is 28, not 29.** T358 claims "29 arms / 29 PASS". Arm set 1 contributes
T323's **15**; arm set 2 contributes **13**; that is **28** distinct arms. The drive's own
`PASSES` counter increments once more for the *aggregate* arm-set-1 result and says so —
`"14 passed, 0 failed. (arm set 1 counts as one.)"` — and 15 + 14 double-counts it.
[VERIFIED: the committed transcript and my own regeneration both print `15 passed` and
`14 passed`.] **Nothing is missing and nothing is unproven; the label is one too many.**

**NOTE-2 — one P-45 citation names the neighbouring line.** T358's P-84 block says the
terminating `exit` is at `conformance.sh:3567`. That is `guard_graded_root_is_this_tree`'s
**short-circuit** exit. The exit a failed `guard_guards_dir_registration` actually takes is the
**tally** exit at **`:3590`** [VERIFIED: my own `awk` over `run_guards`, which finds
`exit "$EXIT_UNUSABLE"` at exactly `:3567` and `:3590`]. Both are inside `run_guards`, both are
upstream, so **the structural conclusion is untouched** — but P-45 cites the line that executes,
and this one cites its neighbour. Mechanical.

**NOTE-3 — TWO P-NUMBERS ARE CITED FOR RULES THEY DO NOT NAME, AND ONE OF THEM IS IN MY OWN
BRIEF.** This is P-86's subject — *"THE PATTERN IDS THEMSELVES ROTTED, IN THE FILE THAT NAMES THE
ROT"* [VERIFIED: `.softhouse/patterns.md:2854`] — recurring.

* **P-83 is cited for "test the probe line's PRESENCE before its value".** It does not say that.
  `P-83` is *"TWO INDEPENDENT MOVEMENTS OF ONE PINNED NUMBER RECONCILE BY RUNNING, NEVER BY
  ARITHMETIC"* [VERIFIED: `.softhouse/patterns.md:2806`]. The presence-before-value rule is
  **P-84** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE
  VALUE."* [VERIFIED: `patterns.md:2813`]. **T358's drive script cites P-83 for it in a tracked
  instrument, and so does the T364 task brief I was given.** I corrected it in my own drive
  rather than propagating it.
  **And the irony is load-bearing: P-83 is exactly the right pattern for the question the driver
  actually asked me** — main moved, T358 moved, and the merged pin is established **by running
  the bar on the merge result, never by arithmetic**. That is §9, and it is why §9 exists.
* **P-80 is used as "this deliverable against its own rules"** in T358's handoff §9. `P-80` is
  *"A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED. The count is the same defect as the
  line number."* [VERIFIED: `patterns.md:2775`; there is no second register — the only other
  occurrences at `:40`, `:45`, `:2855`, `:2862`, `:2874`, `:3176` and `:3202` all restate that
  same meaning]. T358 *applies* P-80 correctly and at length in its §5 — deleting a thrice-rotted
  cardinal rather than retyping it is P-80's own prescribed fix — and then attaches the ordinal
  to a different idea in §9.

**MEASURED CONSEQUENCE: NONE, AND I CHECKED RATHER THAN ASSUMED.** `guard_pnumber_citations`'
fatal tier is the **DIRECTIVE zone alone** [VERIFIED: `conformance.sh:1771`], and the directive
zone reads **MISDIRECTING 2 / UNDEFINED 4, VERDICT PASS** identically on `main` and on
`aac9e12b` in my own two runs. **No gate moved.** This is documentation drift in the evidence
zone, which that guard reports and never grades — recorded so the next author does not inherit
the gloss, not charged as a defect.

---

## 11. CONDITIONS

Numbered so the next task can answer them one by one. **None is a blocker on the merge** — see
§9 — and every one of them is smaller than the hazard the merge removes.

* **C-T364-1 (from F-T364-2, MEDIUM-HIGH, fail-open) — CLOSE THE `./` SELF-CERTIFICATION
  BYPASS.** Compare the **resolved** witness path against `$rel`, not the typed string. The
  guard already invokes `git ls-files --error-unmatch` on the witness; capture its output — git
  normalises `./p` and `a/../p` to `p` for free — and compare that. Until this lands, the
  guard's own printed sentence *"A file may not vouch for itself"* is false, and one in-grant
  line absolves any unwired checker in the guards directory. Add a red arm for **each** spelling
  (`./M`, `a/../M`) beside T358's arm 20; the existing arm 20 must stay.
* **C-T364-2 (from F-T364-1, MEDIUM, fail-open) — the `.go` class is NOT closed for the
  basename `main.go`, and the instrument must say so.** Either (a) tighten the invocation test so
  a basename that occurs only inside a *string literal being read as data* does not absolve —
  which is a real design argument and may be refused — or (b) at minimum, correct the printed
  selector and the C-3 claim to say what is actually true: *the class closed is tracked
  `.sh`/`.py`/`.go` sources under this directory **whose basename does not already occur on a
  non-comment line of this harness** — and `main.go` is such a basename today*. Add the arm
  T358's arm 22 misses: an unwired Go checker **named `main.go`** in a new subdirectory.
  **Do not let (b) ship alone without the arm** — an overstated guard is how the next author gets
  hurt, which is T337's own F-T337-3 argument, and this is its second iteration.
* **C-T364-3 (process, from §1) — STOP CALLING THE `main.go` EDIT "REQUIRED".** It is a
  deliberate, comment-only, non-load-bearing scope excursion with a good architectural argument
  and a disclosed scope note, and T358's own arm 23 proves the tree is green without it. Record
  it that way in `tasks.json` and in the merge commit. The word "required" generalises into the
  excuse this program exists to refuse, and T358 itself never used it.
* **C-T364-4 (from F-T358-2, §5) — RAISE `FU-T358-1` AS A FILED TASK.** Nothing in the bar
  asserts or records a wall-clock cost, per guard or in total, and four hand-written cost
  comments in `run_guards` are checked by nothing. A guard spun the whole bar for 9m43s and the
  only detector was a human noticing. The flakiness objection T358 raises is correct and belongs
  in the task as its first design constraint — prefer a printed-and-censused per-guard elapsed
  **record**, pinned the way every other frontier in this harness is pinned, over a threshold
  that fires on a loaded host.

---

## 12. WHAT T358 GOT RIGHT, SAID EXPLICITLY

Because a review that lists only defects misrepresents the work.

* It **disbelieved its own brief twice** and both refutations survive my re-derivation: T337's
  C-4 repair really would have shipped a false cardinal (§0.3), and the depth really should be
  kept rather than narrowed away (§2).
* It refused T337's one-token `:(glob)` patch **as the whole answer**, which is what T337 itself
  said to do, and paid for the retained coverage with an in-grant remedy rather than a smaller
  search. That is the right trade and it is argued, not asserted.
* It found and closed a fail-open **nobody asked it to look for** — F-T358-1, the DECLARATION
  TABLE vouching for a member it does not declare — which went live the moment the population
  widened to Go. I verified the cut is exact.
* It caught its own 9m43s pathology **through the wired route**, wrote it up as a finding about
  the instrument rather than a bug it fixed, and recorded the episode beside the code that
  caused it.
* It built the five arms (17-20, 26) that keep `REACHED-BY` from being a self-certification hole
  **before** anyone asked, correctly reasoning that the direction is otherwise an assertion the
  guard repeats back. That the class is one spelling short (F-T364-2) does not diminish that the
  arms exist and fire.
* Its evidence is honest in the two places it would have been easiest not to be: the standalone
  fast-check is labelled NOT-EVIDENCE and left uncommitted, and the cost delta is declared as
  noise rather than claimed as an improvement — **which is why my own contradictory cost
  measurement does not damage it.**
