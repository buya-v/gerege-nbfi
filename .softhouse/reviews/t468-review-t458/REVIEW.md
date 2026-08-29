# T468 — INDEPENDENT ADVERSARIAL REVIEW OF T458

Branch `softhouse/T468-review-t458`. Subject: `softhouse/T458-fixture-literal-pattern`, tip
`0db7538b`, 4 commits, 17 files, +3112.

Read from the branch, never from a working tree (`git show <branch>:<path>`, `git diff
main...<branch>`). Every figure below was re-derived on this reviewer's own runs. Where a claim
could not be re-derived, it says so.

---

## VERDICT: **APPROVED WITH CONDITIONS**

The work is sound and unusually well instrumented. The two claims the dispatch asked me to break
— **`P-103` is free** and **only two of the six instances are fixture literals** — both **HOLD**,
and the second means **the driver's filed premise was wrong**. Nothing blocks the merge.

| # | Severity | Condition |
|---|----------|-----------|
| C-T468-1 | **MAJOR** | The new refusal text and `P-103` both foreclose "pin the row with its reason", which is a disposition the same refusal message offers four lines above and which `T316`'s own header sanctions. One clause repairs it. Text defect, no behaviour change, does not block the merge. |
| C-T468-2 | **LOW** | The handoff states the `conformance.sh` hunk as **+9 lines** in two places (§3a, §6 table). Measured: **+13** (7 `warn` + 6 comment). The *re-specification* is correct; only the self-reported size is wrong. |
| C-T468-3 | **LOW** | The delivered tip `0db7538b` was never graded by T458 — its final bar is at `963fe613`, and the tip adds 871 + 44 lines on top. **I graded the tip myself: GREEN.** Risk discharged; the habit is the condition. |
| C-T468-4 | **LOW** | `20-drive-wrapper-arm.sh`'s GREEN arm re-reads a *supplied transcript* instead of running a bar, so as shipped that arm grades bytes the author handed it. **I discharged it by re-running the drive with a bar transcript I produced myself** (`out/21`, `out/11`). |
| C-T468-5 | **LOW** | §5's "zero findings of any severity are attributed to `patterns.md` itself" is imprecise: two `report DECLARED-AMBIGUOUS` lines name it (`P-12` at :315 vs :1385, `P-13` at :320 vs :1412). Both pre-existing, both declared, both disclosed by T458's own §7.4. Substance ("nothing new, 0 fatal") is correct. |

**Endorsed without condition:** item 3's "no" (§4 below), the six citations, the pin's immobility,
both drives, and the sentence-anchor choice.

---

## 1 · WHAT I RAN, ON WHOSE TREE

All scratch outside the repository, in `mktemp -d`. `bash`, never `sh`/`zsh`.

| Run | Tree | Probe PRESENCE tested first | Result |
|-----|------|------------------------------|--------|
| Full bar | T458 **tip** `0db7538b` | `grep -c 'probe = '` = **1** | **EXIT 0**, PASS 46 vectors / 7884 cells |
| Full bar | T458 `963fe613` | `grep -c 'probe = '` = **1** | **EXIT 0**, PASS 46 / 7884 |
| `check-pnumber-citations.py` | fork point `3f4e236a` | — | `ids=101 gaps=none undefined=47`, PASS 0 fatal |
| `10-drive-remedy-text.sh` | tip `0db7538b` | probe lines = 1 on both arms | **PASS** |
| `20-drive-wrapper-arm.sh` | tip `0db7538b`, GREEN arm fed **my own** bar | red probe = 0, green probe = 1 | **PASS** |
| Full bar | **my own committed tree** | see §9 | see §9 |

Probe value, read only after its presence: `reference oracle (…/actuator/health) probe = up`.

### The transcript is bound to the tree — measured, not assumed

Hard rule 2 says to grade the bytes, because nothing binds a transcript to the tree it claims to
have graded. So I diffed T458's committed `out/90-FINAL-BAR-963fe613.txt` against my own run of
the bar at `963fe613`:

```
81 differing lines. After removing host-absolute paths, per-run guard timings and the
go-env toolchain-fallback banner (this host has no pinned toolchain), the residue is:

    > BAR EXIT = 0          <- a line I appended myself, not part of the harness output
```

**Every corpus cardinal is identical** — 1686 census corpus, 108 dead occurrences, 70 Go files,
73 vector JSONs, 63 Java files, 574 wire documents, 11 fail-open rows, `ids=102`,
`sites=14056 definition=103 consistent=719 bare=13050 misdirecting=81 undefined=45
negative-control=58`, `PASS 46/7884`. T458's §8 quote is verbatim true of that tree.
[`out/12-T468-diff-committed-transcript-vs-my-rerun.txt`]

---

## 2 · `P-103` — HOLDS. NO COLLISION EXISTS TODAY.

Full working: [`out/30-T468-register-rederivation.txt`]. Summary, with the **member sets and
their tree**, not bare counts:

* I copied the two definition regexes verbatim from `check-pnumber-citations.py:100-101` and ran
  them two ways, because `build_register` at :246 does `s = raw.strip()` and T458's stated regex
  did not.
  * **Strict scan, `main` @ `3f4e236a`:** 97 distinct, MAX = 102, interior gaps =
    **{14, 63, 64, 65, 99}**. **Digit for digit what T458 reported.**
  * **Checker-equivalent scan, T458 @ `0db7538b`:** 102 distinct, MAX = 103, gaps = **{99}**,
    in-file collisions = **{12, 13}**. Matches the bar's `ids=102 gaps=none in-file-collisions=2`.
* **The reason for not reusing an interior gap is correct.** `P-14` (:324), `P-63` (:2043),
  `P-64` (:2044), `P-65` (:2045) are all live definitions written as *indented bullets* — invisible
  to a raw-line scan, accepted by the checker because it strips. `P-99` is the permanent negative
  control at `check-pnumber-citations.py:203-206`, keyed to the `t255-dec2-rev8` P-5 probe
  instrument at :59,73 — I opened that file and both lines are there. **103 was the only free
  cardinal.**
* **Freshness.** At the fork point, a whole-tree search for the token returns **exactly one line**,
  in the fire's own `60-BAR-RED-p102-first-draft-FATAL-undefined-citation.txt`. That one line
  carries **two** `P-103` tokens (`grep -o | wc -l` = 2), which is why the checker retires **two**
  sites.
* **`undefined` 47 → 45 is exact**, re-derived by *running* the checker on both trees, not by
  reading T458's number. `0 fatal` and `VERDICT PASS` either side.

### Collision sweep across the four live siblings — the loud answer the brief asked for

```
softhouse/T462-wallclock-refusal  -> 3f4e236a   NO COMMITS (still at the fork point)
softhouse/T465-lock-frontier      -> 3f4e236a   NO COMMITS
softhouse/T466-skipwt-smudge      -> 3f4e236a   NO COMMITS
softhouse/T467-t464-conditions    -> 3f4e236a   NO COMMITS
searching each branch's patterns.md for the token  ->  rc=1 (no hit) on all four
```

**There is no `P-103` collision.** There is also **no `conformance.sh` contention**: `T466` has
produced no commit at all, so its diff against that file is empty and the "concurrent edit"
hazard the brief flagged does not currently exist.

**This is a snapshot of four shas and of nothing later.** All four workers are still live. The
merge-time obligation T458 states is the right one and I restate it: **re-run
`check-pnumber-citations.py` on the MERGE RESULT, not on either branch.**

---

## 3 · THE SIX CITATIONS AND THE RECLASSIFICATION — HOLD

Full working, instance by instance, with the bytes: [`out/31-T468-six-citations-rederivation.txt`].

**All six reproduce, and not one citation is off by a line.** I opened each cited file at the
cited line:

* `T440` — `T440-BAR-own-RED.txt`: `grep -n` finds `T316-DEADPATH-FRONTIER` at **exactly one**
  line, **191**, reading `REFUSED rows=109 pinned=108 added=1 removed=0`. Cited as :191.
* `T446` — `:100` is `frontier 15, pinned at 11`; `:122` is `EXIT 2 — no verdict is available`;
  the four `+TIER2` rows are :111-114; `grep -c 'probe = '` over that log = **0**.
* `T447` — §11 begins at :444, the figure is at :462-464, inside the cited section.
* `T448` — **exactly one** `T316-DEADPATH-FRONTIER` line, at **193**. `REVIEW.md:531` carries the
  same line and :532 carries `BAR EXIT 2   grep -c 'probe = ' -> 0`.
* `T451` — `rows=120 pinned=108 added=12` at :375, `all 12 from bin/10-fixture.sh` at :376,
  inside the cited 374-382.
* `T452` — at :406-407, inside the cited 404-410, **including the `added=1 removed=0` tail the
  dispatch brief dropped**. T458's "lossy, not false" correction is confirmed.

### The reclassification is RIGHT, and the dispatch brief was WRONG. Stated plainly.

The task as filed said six workers were refused *"for spelling a real `.softhouse/…` path as a
literal in a fixture."* Measured:

* **`T447` proves itself from its own header.** `t447-k8-handoff-site.sh:12` reads
  *"ERRATUM-K8-DECOMPOSITION.md, which exists **ONLY** on `softhouse/T442-t440-conditions`"* and
  :28 *"THE ERRATUM IS NOT ON THIS BRANCH and this drive does not pretend otherwise."* That is a
  cross-branch artefact reference. It is not a fixture.
* **`T448`** names a guard its own review states is *"on `softhouse/T433-t423-c1` and not on
  `main`"*.
* **`T440`**'s `+` row names the `t424` comment-claims drive, on the branch under review.
* **Independent corroboration T458 did not offer:** both of those two target files **are tracked
  on `main` today** (`git ls-files | grep -c` = 1 each at `3f4e236a`) — they were merged
  afterwards. That is exactly what "existed only on the branch under review" predicts, and it
  does not depend on anything T458 wrote.
* **`T446` is a different guard** — `guard_no_fail_open_instruments`, a different pin
  (`FAILOPEN_PIN_FILE_LIST`, 11 rows), a different defect (a printing failure arm).
* **`T451` and `T452` are the only two** in the class the brief described, and I read `T451`'s
  **pre-repair bytes** at `0bf11587` to be sure: its `commit "…/capture/t900-work/out/wip.txt" …`
  calls are paths inside a synthetic repository the script builds after `cd "$FIX"`.

**So the census had zero false positives on those three, and `P-103`'s table is a better
description of the fire than the task that commissioned it.** A worker that corrects its own
brief from the tree, and says so, is doing the thing this program is for.

*One loose edge, not a condition:* `T452` is grouped under "fixture literal proper" but is
strictly a **run-time scratch destination** inside this tree, not a synthetic-repo path. T458's
own prose says as much; only the table's two-word label is loose.

### "Not one of them grew the pin" — re-derived

`grep -c -E` for all six task directories over `guards/dead-path-frontier.pin` = **0 rows**. The
fail-open pin likewise carries **0** `t446-review-t445` rows, having shown 15-vs-11 during T446's
RED. **The good half of T458's finding is true.**

### The five repairs, each opened rather than believed

`T440` `f-t440-1.sh:22-23` `${1:?}`/`${2:?}` with `exit 2`; `T447` required argument, `exit 2` at
:50/:64/:65; `T448` `${T448_GUARD:?}` at :46 with `prepare()` returning 1 into `exit 3` at
:86-88/:106-108/:148-150; `T451` `S=".softhouse"` at `10-fixture.sh:16` — **line exact**; `T452`
`C_REL="$(dirname "$SELF_DIR")/t452-relocated-$$/sweep.sh"` at :147; `T446`'s four drives now exit,
their surviving `|| echo` occurrences being *comments about the removed defect*
(`drive-longs.sh:66,92`).

---

## 4 · ITEM 3's "NO" — **ENDORSED**, and now with a drive behind it

T458 concluded the guard **cannot** separate a fixture literal from a genuine dead path and
**should not try**. The brief asked me to hunt for a discriminator it missed, naming one
candidate: *the value's use as an argument vs. its appearance in a heredoc.*

**I tested that candidate against the actual specimen and it does not discriminate.** T451's
pre-repair fixture literals at `0bf11587` are **arguments to a locally-defined `commit` function** —
`commit "<a synthetic-repo path>" "real analysis" "RESCUED: WIP from a worker …"`. Not a heredoc.
Argument position — **the same syntactic position a genuine reference occupies** (`[ -f "$p" ]`,
`grep … "$p"`). The candidate discriminator is refuted on the only two members of the class that
exist.

The one cue that *is* present is a **flow** property: line 14 does `cd "$FIX"`, so everything after
it is relative to a scratch root. A line-oriented regex census over `git ls-files` cannot see that,
and `FIX` is `${1:-/tmp/t451/fixture}` — a caller can point it anywhere, including inside the repo.
A `cd`-based heuristic would therefore excuse an entire instrument on a guess, and **its false
negatives would be silent**, which is the failure this guard exists to prevent. I checked the
selector itself (`census_dead_paths.py:68-73`): it already excludes placeholders (`$VAR`, `%s`,
`{…}`), globs, ellipses and whitespace-bearing prose. There is nothing left to tighten that is not
a guess.

**Endorsed. The inability is the fail-closed direction working.** T454 was praised for the same
habit and this is the same shape, argued rather than asserted.

**One thing I leave open rather than argue shut.** T458's argument establishes that no *inference*
over the text can recover the author's intent. It does not address the one option that is **not**
an inference: an explicit author **declaration** on the line (`# deadpath: fixture`). T458 names
that in "what I did NOT build" but never argues against it. My own view — offered, not imposed —
is that it should still not be built, for a *different* reason than the one given: it would be a
**second amnesty channel** competing with the pin, scattered across the tree instead of reviewable
in one file, and this program already chose the pin. That is a policy argument, not an
impossibility argument, and the entry currently presents only the latter. Not a condition.

---

## 5 · THE DRIVES — I RAN BOTH. BOTH REPRODUCE.

**`10-drive-remedy-text.sh`, on T458's tip** [`out/20`, `out/22`]:

```
CALIBRATION  source hits = 1 for each of the three strings   -> the drive can see what it grades
GREEN  exit 0   probe lines 1   probe = GREEN rows=108 pinned=108 added=0 removed=0
       anchor hits 0    remedy hits 0
RED    planted file tracked in clone = 1
       exit 1   probe lines 1   probe = REFUSED rows=109 pinned=108 added=1 removed=0
       anchor 1  remedy 1  forbidden-4th 1  planted row named 1
T458-REMEDY-DRIVE: PASS
```

The RED probe line is `rows=109 pinned=108 added=1 removed=0` — **digit for digit the refusal
`T440`, `T447`, `T448` and `T452` each took.** The drive reproduces their transcript, not merely
their class. That claim of T458's is true and I saw it print.

**`20-drive-wrapper-arm.sh`, on T458's tip, GREEN arm fed a bar transcript *I* produced**
[`out/21`, `out/23`]:

```
RED    bar exit 2   'probe = ' lines 0   arm head 1  remedy 1  anchor 2
GREEN  'probe = ' lines 1   frontier GREEN 1   arm head 0  remedy 0  anchor 0
T458-WRAPPER-DRIVE: PASS
```

### Did the GREEN control have the opportunity to fail?

This program has repeatedly recorded a GREEN that could not have gone RED. Here it could:

1. **Calibration proves the text exists in the source being graded** — 1 hit each for the anchor,
   the remedy head and `THE FORBIDDEN FOURTH` in the guard, and for the wrapper line, the anchor
   and the arm head in `conformance.sh`. So "0 hits in the green output" is a *conditional* result,
   not a trivially-true one.
2. **The RED arm runs the same bytes and prints them.** Same guard file, same harness, one planted
   row of difference.
3. **The green arm asserts `frontier GREEN >= 1`** — it proves the arm reached the point where it
   could have fired.
4. And on my own independent full bar at the tip I measured directly: arm head **0**, wrapper
   remedy **0**, anchor **0**, guard remedy head **0**, `dead-path frontier: GREEN` **1**.

**C-T468-4 (LOW).** As shipped, drive 20's green arm reads `T458_GREEN_BAR` — bytes the author
supplies — rather than running a bar. It is a *required* parameter and it is calibrated, so it is
not fail-open; but it is the one place in this delivery where a transcript stands in for a run.
I discharged it by supplying a transcript I made. If the drive is ever re-run, feed it a bar the
runner produced.

### T458's own instruments obey `P-103` — verified with the census's own selector

I ran `LITERAL_RE` from `census_dead_paths.py:68` over both drives:

```
bin/10-drive-remedy-text.sh   ->  0 quoted `.softhouse/` literals
bin/20-drive-wrapper-arm.sh   ->  0 quoted `.softhouse/` literals
```

`S=".softhouse"` has no trailing slash, so it is not a row — correct, and deliberate. Both scripts
use `${T458_SRC:?}` / `${T458_OUT:?}` / `${T458_TMP:?}` with no defaults, reject a `T458_TMP`
inside the repo, and `exit 2` on non-resolution. Both prove the planted file is **tracked** before
reporting a refusal, and both calibrate every negative before printing it. **The author of a rule
about fixture literals did not spell one.**

### The pin did not move — byte-measured

The diff of `guards/dead-path-frontier.pin` between `3f4e236a` and `0db7538b` changes **0 lines**.
The frontier is `108 == 108`; the fail-open frontier is `11 == 11`; neither T458 instrument is on
either.

---

## 6 · DOES THE REFUSAL TEACH THE FIX? — MOSTLY YES. ONE MAJOR.

Read as a worker at 10:44 on a Friday, from `out/22`:

**What works.** Remedy 1 hands over the literal idiom (`S='.softhouse'` and build downward) *and*
explains why it is not evasion. Remedy 2 states the shape and forbids the three wrong arms by name
("never a skipped case, never a warning, never a pass"). Remedy 3 names `T238`'s `sweeplib`, which
is one `git ls-files | grep sweeplib` away (I checked: exactly one hit, under
`capture/t238-failopen/instruments/`). The forbidden fourth pre-empts the evasion `T440` explicitly
refused. **A worker can act on this without further reading.** That was the task's second half and
it is met.

**The sentence anchor instead of a P-number: CORRECT, and I checked it resolves.** `grep -F` for
`A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE` in `patterns.md` returns **2 hits,
the first being the definition line :3835**. A reader lands on the entry. A P-number in a shell
string is a citation nobody re-checks and the checker cannot police, and `P-86` says so; the same
file already records `P-86`'s cousin defect (`conformance.sh:1715` → `:1727`, stale by 12).
Endorsed without qualification.

### C-T468-1 (MAJOR) — the message now forbids something the guard sanctions

The pre-existing four lines of the same refusal, unchanged by T458, read:

```
conformance: !! ... Either make the path resolve, or -- if the
conformance: !! reference is a deliberate fallback candidate -- make the instrument
conformance: !! REFUSE when no candidate resolves, and record why in the pin.
```

Four lines later T458's block says **"Do ONE of these three, and never a fourth"** — and the three
do not include pinning — and remedy 2 says the hard-exit arm is *"what this guard asks for **in
exchange for not pinning the row**."* `P-103` then makes it absolute: *"do **not** … add the row to
the pin."*

That is not what the guard asks. `check-dead-path-frontier.sh:57-63` is explicit:

> "A dead literal is a SMELL that must be inspected once, by a human, and then **either repaired
> or pinned with its reason**. This guard counts; it does not judge."

and it records the sanctioned instance — the `FU-T299-2` ordered-fallback pair
(`guard_rvpa_floor_t290.py`, `red/drive-red-t290.py`), pinned, not repaired. The message fires on
`added_n > 0`, i.e. on exactly the NEW-row case for which its own preceding sentence offers the pin
route. So the refusal now contradicts itself within one screen, and the permanent register carries
the stronger, wrong form.

**Why MAJOR and not MINOR.** This program has already filed this exact class: the `removed_n` arm
in `conformance.sh` carries `[T358: this line used to say 'the pin is outside T323's edit grant',
which stopped being true when T326 regenerated the pin — **a false statement inside a refusal
message**.]` The defect here is the same species, and it is worse in one respect: it is also in
`patterns.md`, which is where the next six workers will look.

**It does not block the merge.** No behaviour changed; `bad=1` and the exit codes are untouched;
the guard's pre-existing sentence is still printed above the new block. It is a one-clause repair.

**The repair, specified precisely** (for the driver to route as a follow-up — I did not apply it,
per my grant):

* In `guards/check-dead-path-frontier.sh`, change
  `"conformance: !!   three, and never a fourth:"` to
  `"conformance: !!   three -- or, ONLY for a deliberate ordered-fallback candidate,"` +
  `"conformance: !!   the pin-with-a-reason route named four lines above. Never a fifth:"`.
* In `patterns.md`'s `P-103`, replace *"and do **not** add the row to the pin"* with *"and do not
  add the row to the pin **unless the reference is a deliberate ordered-fallback candidate, which
  is the one disposition `T316`'s header sanctions and the refusal's own second sentence offers**"*.
* Acceptance: `10-drive-remedy-text.sh` re-run RED must still print the anchor, the remedy and the
  forbidden fourth; add a fourth assertion that the RED output contains both the string
  `record why in the pin` and the amended clause, so the two can never again drift apart.

I have **not** driven this repair, because applying it is outside my grant and this program has
twice recorded reviewer-proposed patches being refuted by the worker asked to apply them. It is a
condition with a specification, not a change.

---

## 7 · THE DECLARED OVERREACH — JUSTIFIED, AND RE-SPECIFIABLE

**Justified.** The brief located the message in `conformance.sh`; the message six workers actually
read is printed by `guards/check-dead-path-frontier.sh` in the `added_n > 0` branch. I confirmed
this from the RED transcripts themselves: `T440-BAR-own-RED.txt:185-188` and
`79-BAR-FIRST-RUN-…txt:188-190` carry the `A '+' row is a NEW site` text, and those are the guard's
`echo` lines, not the wrapper's `warn` lines. Editing only `conformance.sh` would have left every
one of the six citations' actual reading experience unchanged. **Declaring it rather than quietly
widening the grant is the right disposal.**

**Both hunks are echo-only.** Guard: `+35` = **26 `echo`** + 9 comment, inside the existing
`if [ "$added_n" -gt 0 ]` branch. `conformance.sh`: `+13` = **7 `warn`** + 6 comment, inside the
existing `elif ! diff …` branch, immediately after `LC_ALL=C sed -n '1,40p' "$d/diff" >&2`.
**No control flow, no variable, no function, no cardinal, no `bad=` assignment touched.**

**Is §3b a sufficient re-specification?** §3b alone is *not* — it quotes the wrapper text as it
*renders*, stripped of the `warn "conformance: …"` wrapper. But §6 supplies the missing half: it
names the exact insertion anchor and says "insert those **seven** `warn` lines". §3b + §6 together
**are** sufficient to re-apply by hand. Verified: the seven lines are exactly where §6 says.

**C-T468-2 (LOW).** §3a says "**9** added lines inside one existing branch" and the §6 table says
"**+9** lines inside one existing `warn` branch". Measured: **13**. Seven of them are `warn` lines,
which is the number §6's re-specification uses and which is right — so this is a miscount in the
prose, not a defective specification. Worth correcting because in this program a self-reported
diff size is a claim like any other.

**Overlap with `T466`: none exists.** `softhouse/T466-skipwt-smudge` is at `3f4e236a` with **zero
commits**, so there is nothing to conflict with. Should it later land in
`guard_dead_path_frontier()` between the `elif ! diff` line and `bad=1`, git will conflict and §6
resolves it. Anywhere else in those 6,326 lines, it will not.

---

## 8 · T458's OWN OPEN ITEMS — EACH CHECKED

1. **Cardinal claimed against live siblings.** Checked: no collision, all four siblings empty (§2).
   The stated merge-time obligation (re-run the checker on the merge result) is correct. **Open,
   correctly.**
2. **The remedy is on only one of four wrapper arms.** **True, and correctly chosen.** I read
   `guard_dead_path_frontier()` at `conformance.sh:2871-2898`: arm 1 is unreadable cardinals, arm 2
   is a truncated listing — both *instrument failures*, not this class; arm 3 is `removed_n != 0`,
   which is a frontier *shrink* and a different remedy; arm 4 is `THE FRONTIER MOVED IN A WAY
   NOBODY RECORDED`, the one a new `+` row trips. My own RED full-bar drive fired arm 4 and no
   other. The primary site — the guard's own message on `added_n > 0` — reaches every new-row case
   regardless of which wrapper arm follows. **Correctly scoped.**
3. **Nothing catches the reflex earlier than the bar.** **True for the growth direction, which is
   this class.** I checked the two candidates: `hooks/cheap-subset.sh` runs **only**
   `guard_pnumber_citations` and says so in its own header ("what it therefore does not cover …
   the other fourteen guards"); `hooks/added-path-hazard.py` (T453) asks only the *shrink* question
   — "is any added path capable of making a PINNED DEAD LITERAL resolve?" — and reads nothing about
   the added file's content. Neither would have caught any of the six. T458 does not cite either
   hook, so its open item understates its own homework, but the conclusion is right.
4. **`patterns.md` still carries `P-12`/`P-13` in-file collisions and dangling `131`, `261`.**
   Re-derived independently: collisions `{12, 13}` from my checker-equivalent scan;
   `declared-dangling ids = [131, 261]` from the bar. Report-only, unchanged by T458. **Accurate.**

**C-T468-3 (LOW), which T458 half-declared.** Its §8 honestly notes the transcript is committed one
commit after the tree it grades. The sharper form is that **`0db7538b`, the tree that will actually
merge, was never graded by T458** — it adds 871 transcript lines and 44 handoff lines on top of
`963fe613`, and a committed transcript is itself census corpus-adjacent. **I graded it: EXIT 0,
probe present ×1, `PASS 46/7884`, `deadOccurrences=108`, fail-open `11 == 11`, `ids=102 gaps=none`,
`undefined=45`.** The tip is clean. The condition is the habit, not the outcome: grade the tree you
deliver.

---

## 9 · MY OWN BAR, ON MY OWN COMMITTED TREE

Run with `bash`, never `sh`/`zsh`. Probe-line **PRESENCE** tested before its value was read,
because absence is a failed HARD guard and is not `down`. Tree measured clean before the run.

Figures are recorded in `out/40-T468-BAR-own-tree.txt`, taken at the sha named in that file's
header. Summary: **EXIT 0**, `grep -c 'probe = '` = **1**, `probe = up`,
**`VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
compared`**, `T316-DEADPATH-CENSUS: … deadOccurrences=108` (**pin not moved**), fail-open frontier
`11 == 11`, `PNUMBER-CITATIONS: … ids=102 gaps=none … VERDICT PASS -- 0 fatal`.

This review adds only prose and transcripts under its own directory — no `.sh`, no `.py`, so it
adds nothing to the dead-path census corpus and cannot spell the literal `P-103` forbids.

---

## 10 · WHAT I COULD NOT RE-DERIVE

Stated rather than glossed:

* **I cannot bind T458's earlier transcripts (`out/10`, `out/35`, `out/50`) to the shas they name**
  (`6612d7da`, `b4ffcf7c`) the way I bound `out/90` to `963fe613`. I re-ran both drives at the tip
  instead, which is the stronger check for the delivered artefact but does not retrospectively
  authenticate those three files. They are consistent with everything I did measure.
* **I did not test the refusal on a real worker.** "Does the text teach the fix" is judged by
  reading it, which is a judgement and not a measurement. I have said which parts are concrete and
  which are a pointer.
* **The collision sweep is a snapshot** of four shas. Four workers are live; a `P-103` could still
  land after this review. The merge must re-check.
* **I did not evaluate whether an author-declaration mechanism should exist** (§4). I offered a
  view and left it open.
