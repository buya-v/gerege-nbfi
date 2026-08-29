# T458 — the fixture-literal reflex, recorded as `P-103`, and the refusal made to teach the fix

Branch `softhouse/T458-fixture-literal-pattern`. Local fire `20260829-080002`, iteration 6, wave 1.

---

## 1 · The P-number I took, and why it was free

**`P-103`.**

`patterns.md` is the register `check-pnumber-citations.py` reads, and it recognises a definition
by two regexes only — `DEFN_HEAD` (`^#{2,4} P-n[.—–-] …`) and `DEFN_BOLD` (`^[-*>]?\s*\*\*P-n[.—–-] …`).
I rebuilt the register with **those exact regexes**, not by grepping for the token, because a
grep answers a different question and the file cites far more ids than it defines:

```
defined ids  = 97 distinct, MAX = 102
interior gaps= 14, 63, 64, 65, 99
next free    = 103
```

The checker's own run agrees and is the authority: `register=.softhouse/patterns.md ids=101
gaps=none` before my commit, `ids=102 gaps=none` after it. (`ids` counts what the checker's
`build_register` accepts, which is slightly wider than my two-regex scan; `gaps=none` either side
is the load-bearing figure.)

**I did not reuse an interior gap, and the reason matters.** `P-99` is a **permanently reserved
negative control**, declared in `patterns.md` and depended on by
`.softhouse/capture/t255-dec2-rev8/instruments/15-p5-probe.py`, and `T398` had to patch the
checker's gap scan to stop it going fatal on that reservation the moment any pattern landed above
99. `P-14`, `P-63`, `P-64` and `P-65` are all **defined** (as indented bullets the checker's
register builder accepts and my stricter scan did not) and are cited live elsewhere. So the only
genuinely free cardinal is the one above the maximum.

**Freshness check, and how I recorded it.** A whole-repository search for `P-103` before my
commit returned exactly **one** hit, and it is not a definition:

```
.softhouse/capture/fire-20260829-080002/60-BAR-RED-p102-first-draft-FATAL-undefined-citation.txt:125
  PNUMBER-CITATIONS: FATAL UNDEFINED .softhouse/patterns.md:3799 P-103 -- P-103 is defined in neither register
```

That is the transcript of the driver's own `P-102` first draft being refused for spelling the
then-unclaimed next cardinal in `patterns.md`. Defining `P-103` **retires** that dangling
citation rather than creating one — measured: the checker's `undefined` count went **47 → 45**
across my commit, and `0 fatal` either side.

**And I obeyed the rule that draft broke:** I have not written the next unclaimed cardinal
anywhere. It was checked; it is not spelled. An id is a citation the moment it is typed.

**Collision hazard, declared:** four workers were live in this wave. If a rival `P-103` lands,
renumber mine — the entry says so in its own text.

---

## 2 · The six citations, verified by me, with the row counts I read myself

Nothing below is inherited from the dispatch brief. Every figure was read out of the committed
artefact named beside it, on `main`.

| # | Task | Guard | Measured figures | Read from | Brief? |
|---|------|-------|------------------|-----------|--------|
| 1 | `T440` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2` | `.softhouse/reviews/t440-review-t424/out/T440-BAR-own-RED.txt:191`; narrated at `.softhouse/reviews/t440-review-t424/REVIEW.md` §10a | ✔ reproduces |
| 2 | `T446` | `guard_no_fail_open_instruments` | fail-open frontier **15**, `pinned at 11`, **4** new `TIER2` rows, bar `EXIT 2`, `grep -c 'probe = ' = 0` | `.softhouse/reviews/t446-review-t445/REVIEW.md` §11.1; `.softhouse/reviews/t446-review-t445/evidence/80-my-first-bar-REFUSED-failopen.log:100,122` | ✔ reproduces |
| 3 | `T447` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2` | `.softhouse/reviews/t447-review-t442/REVIEW.md` §11 | ✔ reproduces |
| 4 | `T448` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2`, `grep -c 'probe = ' -> 0` | `.softhouse/reviews/t448-review-t433/out/79-BAR-FIRST-RUN-REFUSED-BY-MY-OWN-INSTRUMENT.txt:193`; `REVIEW.md:531` | ✔ reproduces |
| 5 | `T451` | `guard_dead_path_frontier` | `rows=120 pinned=108 added=12`, **all twelve from `bin/10-fixture.sh`** | `.softhouse/handoff/T451-t449-conditions.md:374-382` | ✔ reproduces |
| 6 | `T452` | `guard_dead_path_frontier` | `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1 removed=0`, bar `EXIT 2`, clean tree (0 dirty) | `.softhouse/handoff/T452-t447-conditions.md:404-410` | ✔ reproduces (see note) |

**Nothing failed to reproduce.** Two corrections to the brief's framing, both recorded in the
pattern entry:

* **`T452` was abbreviated, not wrong.** The brief gives `rows=109 pinned=108`; the committed line
  also carries `added=1 removed=0`. Lossy, not false.
* **The brief calls all six "fixture literals". Measured, they are three sub-classes, and only
  two are fixtures.** This is the substantive correction:
  * **cross-branch artefact reference — `T440`, `T447`, `T448` (3 of 6).** The instrument names a
    real file that exists only on the branch under review. On the author's own tree that path is
    **genuinely** dead. The census had **zero false positives** here; it caught a claim that stops
    reproducing the moment the instrument leaves one branch.
  * **fixture literal proper — `T451`, `T452` (2 of 6).** Not a reference to this tree at all:
    `T451`'s synthetic-repo paths (which must *mimic* this program's layout — that is the point of
    its cases K and R2), and `T452`'s run-time relocation destination.
  * **the sibling reflex — `T446` (1 of 6).** Not a dead path: four drives whose failure arms
    printed instead of exiting.

  The **reflex** is one; the **object** is not. That distinction changes what a reader should
  generalise, so it is in the entry.

**The good half, and it is the half worth citing.** All six repaired at the instrument; **not one
grew the pin.** `T440` and `T447` made the path a required argument with no default; `T448` made
it the required parameter `T448_GUARD` with `exit 3` in `prepare()` on non-resolution; `T451`
assembled from `S=".softhouse"` (verified verbatim at `.softhouse/capture/t451-t449-conditions/bin/10-fixture.sh:16`);
`T452` derives its destination at run time and sanity-checks it; `T446` rewrote the four drives to
exit rather than print. `T440` also explicitly **refused** the tempting evasion — *"spell the
literal in pieces so the census would not see it. That is gaming a guard this program has paid
for twice."*

---

## 3 · The refusal now teaches the fix — RED and GREEN, at both sites

### 3a · Where the message actually lives — a correction to the brief's scope line

The brief scopes item 2 to *"the guard's refusal message in `.softhouse/conformance.sh`"*. **The
message the six workers actually read is not in `conformance.sh`.** It is printed by
`.softhouse/guards/check-dead-path-frontier.sh`, in the `added_n > 0` branch — that is the file
that emits `A '+' row is a NEW site: REPAIR it rather than pinning it`. `conformance.sh` carries a
**second**, different refusal, on the wrapper arm headed `THE FRONTIER MOVED IN A WAY NOBODY
RECORDED`, and a reader can stop at that one without ever scrolling up to the guard's transcript.

**Both sites now name the remedy**, because fixing only the one the brief named would have been
the corrections-leak shape this program has recorded repeatedly. Files touched: the guard (the
primary site) and `conformance.sh` (the wrapper arm). The `conformance.sh` change is **9 added
lines inside one existing branch**, no logic touched, no cardinal moved — the smallest edit I
could make there, chosen deliberately because that file is contended. See §6.

### 3b · What the refusal says now

The guard's block, verbatim from the RED transcript
(`.softhouse/capture/t458-fixture-literal-reflex/out/30-RED-planted-literal.txt`):

```
conformance: !! 1 NEW dead path reference(s). A '+' row is a NEW site: REPAIR it
conformance: !! rather than pinning it. Either make the path resolve, or -- if the
conformance: !! reference is a deliberate fallback candidate -- make the instrument
conformance: !! REFUSE when no candidate resolves, and record why in the pin.
> .softhouse/capture/t458-red-drive-specimen/planted-dead-literal.sh | .softhouse/capture/t458-no-such-directory/no-such-file.txt
conformance: !! ----------------------------------------------------------------
conformance: !! THE REMEDY, because SIX workers in one fire each rediscovered it:
conformance: !!   T440, T446, T447, T448, T451, T452 -- every one of them repaired
conformance: !!   the INSTRUMENT, and not one of them grew the pin. Do ONE of these
conformance: !!   three, and never a fourth:
conformance: !!   1. ASSEMBLE the path at run time from a variable -- S='.softhouse'
conformance: !!      and build downward. This census reads QUOTED LITERALS ONLY, so
conformance: !!      an assembled path is not a row. That is not evasion: it STATES
conformance: !!      that the path is COMPUTED rather than REFERENCED, which is
conformance: !!      exactly what a fixture or a scratch destination means.
conformance: !!   2. MAKE THE LOCATION A REQUIRED PARAMETER -- no default, and a
conformance: !!      HARD EXIT when it does not resolve. Never a skipped case,
conformance: !!      never a warning, never a pass. This is the arm this guard asks
conformance: !!      for in exchange for not pinning the row.
conformance: !!   3. If the failure arm PRINTS instead of exiting, adopt T238's
conformance: !!      sweeplib shape too, so the instrument cannot print a negative
conformance: !!      it never measured. That is the sibling defect T446 was caught
conformance: !!      by, in the same fire, for the same underlying reason.
conformance: !! THE FORBIDDEN FOURTH: do NOT split or concatenate the literal to
conformance: !! slip past the selector. That leaves the false claim standing and
conformance: !! removes the only instrument that would ever have found it.
conformance: !! FULL RULE, the six measured row counts, and the three sub-classes:
conformance: !! grep patterns.md for this SENTENCE -- the line number moves, and an
conformance: !! id is a cardinal that rots, but the sentence relocates with its text:
conformance: !!   A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE
conformance: !! ----------------------------------------------------------------
```

And the wrapper arm, verbatim from
`.softhouse/capture/t458-fixture-literal-reflex/out/40-RED-wrapper-arm-full-bar.txt:228-241`:

```
conformance: guard_dead_path_frontier: THE FRONTIER MOVED IN A WAY NOBODY RECORDED.
…
> .softhouse/capture/t458-red-drive-specimen/planted-dead-literal.sh | .softhouse/capture/t458-no-such-directory/no-such-file.txt
conformance: THE REMEDY, in one line: build the path from a variable at run time, or
conformance: make the location a REQUIRED PARAMETER whose non-resolution is a HARD
conformance: EXIT. Repair the instrument; do not grow the pin, and do not split the
conformance: literal to hide it. The guard's own transcript above states all three
conformance: steps and the forbidden fourth. Full rule and the six measured row
conformance: counts: grep patterns.md for the SENTENCE (the line number moves) --
conformance:   A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE
```

**The anchor is a SENTENCE, never a P-number.** `P-86`'s rule — *"an ID IS A CARDINAL. Never
restate a pattern id in a second document — make the second site NAME THE RULE, or cite the id AND
its sentence together so a shifted number is self-correcting"* — applies with extra force to a
shell string, which nobody re-checks. A renumbered `P-103` does not break either message.

### 3c · The drives

Two instruments, both committed, both run on my own committed tree.

**`bin/10-drive-remedy-text.sh`** — the guard's own message. Run at `6612d7da`
[`out/10-DRIVE-console.txt`]:

```
-- CALIBRATION: the three strings must be present in the guard's SOURCE
   source hits = 1   for: A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE
   source hits = 1   for: THE REMEDY, because SIX workers in one fire each rediscovered it
   source hits = 1   for: THE FORBIDDEN FOURTH
   CALIBRATED: the drive can see the text it is about to report on.

== GREEN ARM: the committed tree, frontier == pin ==
   exit           = 0
   probe lines    = 1      (PRESENCE read before VALUE)
   probe line     = GREEN rows=108 pinned=108 added=0 removed=0
   anchor hits    = 0      (expected 0 -- calibrated present in source above)
   remedy hits    = 0      (expected 0)

== RED ARM: a scratch clone with ONE planted dead literal ==
   planted file tracked in clone = 1   (must be 1, or the arm measures nothing)
   exit           = 1
   probe lines    = 1      (PRESENCE read before VALUE)
   probe line     = REFUSED rows=109 pinned=108 added=1 removed=0
   anchor hits    = 1      (expected >= 1)
   remedy hits    = 1      (expected >= 1)
   forbidden-4th  = 1      (expected >= 1)
   planted row named in the listing = 1   (expected >= 1)

T458-REMEDY-DRIVE: PASS green=exit0/anchor0 red=exit1/anchor1/remedy1
```

**The RED figure is `rows=109 pinned=108 added=1 removed=0` — digit for digit the refusal `T440`,
`T447`, `T448` and `T452` each took.** The drive reproduces their transcript, not merely their
class.

**`bin/20-drive-wrapper-arm.sh`** — the harness wrapper's arm, which only fires inside a full bar.
Run at `b4ffcf7c` [`out/35-WRAPPER-DRIVE-console.txt`]:

```
== RED ARM: full bar in a scratch clone with ONE planted dead literal ==
   planted file tracked in clone = 1
   bar exit          = 2     (2 expected: a failed HARD guard, NOT an oracle outage)
   'probe = ' lines  = 0     (0 expected -- read the ABSENCE, not a value)
   wrapper arm head  = 1     (expected >= 1)
   wrapper remedy    = 1     (expected >= 1)
   pattern anchor    = 2     (expected >= 2: guard message AND wrapper arm)

== GREEN ARM: the same harness, frontier == pin ==
   'probe = ' lines  = 1     (PRESENCE read before VALUE)
   frontier GREEN    = 1     (expected >= 1 -- proves the arm HAD the chance to fire)
   wrapper arm head  = 0     (expected 0)
   wrapper remedy    = 0     (expected 0)
   pattern anchor    = 0     (expected 0)

T458-WRAPPER-DRIVE: PASS red=exit2/arm1/remedy1/anchor2 green=arm0/remedy0/anchor0
```

The RED full bar went **`EXIT 2` with the oracle probe line printed ZERO times** — the exact shape
five of the six workers saw, and the shape `P-84` says to read as the guard working.

**Both drives obey `P-103` themselves**, which is not decoration — the author of a rule about
fixture literals is the last person permitted to spell one:

* no repo-relative path is spelled as a quoted literal anywhere in either script; the directory
  name lives in `S=".softhouse"` and the planted specimen's dead literal is *assembled* by
  `printf '…="%s/capture/…"' "$S"` **inside the throwaway clone**, so neither instrument carries a
  row of its own;
* `T458_SRC`, `T458_OUT`, `T458_TMP` and `T458_GREEN_BAR` are `${VAR:?…}` required parameters with
  no defaults, and non-resolution is `exit 2` — never a skip;
* `T458_TMP` is rejected if it is inside the repository;
* every negative is **calibrated first**: before either drive reports "the remedy text did not
  print", it proves the text is present in the source it is grading, and before the red arm reports
  a refusal it proves the planted file is actually tracked (`planted file tracked in clone = 1`).
  Without those, both negatives would be unfalsifiable.

Independently confirmed by the two guards that grade this class: the fail-open linter reports
**`11 instrument(s)` — frontier 11, pinned at 11, zero `t458` rows**; the dead-path census reports
`deadOccurrences=108`, unchanged.

---

## 4 · Item 3 — can the guard distinguish a fixture literal from a genuine dead path?

**No. It cannot, it never will, and it should not try. The pattern entry is the whole remedy.**

The two are **textually identical**. `T451`'s fixture string and a real broken reference are the
same bytes, in the same syntactic position, in the same kind of tracked file. The difference is
entirely in **what the surrounding program does with the value at run time** — whether it is
resolved against this tree or written into a synthetic one — and a string-literal census, by
construction, does not execute anything and cannot see that.

Any detector would therefore be a **guess over surrounding text**: a filename that looks
fixture-ish, a nearby `mktemp`, a `t9xx` task id, a variable assignment three lines up. And the
failure mode of a guess here is the bad one: **a false negative is silent**, and a silently
excused dead reference is exactly what this guard exists to prevent. A guard that cannot fire is
worse than no guard, because it is believed. Measured evidence that the guessing would not even
be well-motivated: **in five of the six instances the census was not producing a false positive at
all** — three were genuinely dead cross-branch references, and `T446` was a different guard
entirely. Only two of six were fixtures. A detector built to suppress "fixtures" would have been
built for a third of the population and would have suppressed real findings in the rest.

**So the inability is the fail-closed direction working, not a gap.** The remedy is to make the
distinction visible **in the text**, which is what all three repairs do: assembling from a
variable, or taking a required parameter, does not *hide* the fixture from the census — it
*states* that the path is computed rather than referenced. The author encodes the intent because
only the author has it. That is why the fix is a pattern plus a better refusal, and not a
detector.

**What I did NOT build, stated so nobody credits it:** no fixture-literal classifier, no
allow-list, no suppression comment, no new census bucket. The census's selector, its four buckets
and the pin are byte-identical to what they were.

---

## 5 · The bar, on my own committed tree

Run with `bash`, never `sh`/`zsh`. Scratch in `/tmp`, outside the repository. **Probe-line
PRESENCE tested before its value was read**, because absence is a failed HARD guard and is not
`down`.

Taken at `b4ffcf7c` (full transcript committed at
`.softhouse/capture/t458-fixture-literal-reflex/out/50-GREEN-full-bar-b4ffcf7c.txt`, 871 lines):

```
$ grep -c 'probe = ' barA.txt
1                                            <- PRESENCE FIRST. 0 would be a harness failure, not `down`.

$ grep 'probe = ' barA.txt
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   T316-DEADPATH-CENSUS: corpus=1686 deadFiles=75 deadOccurrences=108 resolving=1594 indeterminate=126 prose=428
conformance:   P-number citations: VERDICT PASS (evidence-zone drift is REPORTED, never …)
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

BAR EXIT = 0
```

**`guard_pnumber_citations` — the hard guard that reads `patterns.md` — passed with my `P-103`
entry in place**, which is the one that could have reddened `main`:

```
PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=102 gaps=none in-file-collisions=2 …
PNUMBER-CITATIONS: sites=14019 definition=103 consistent=719 bare=13014 misdirecting=81 undefined=45 …
PNUMBER-CITATIONS: VERDICT PASS -- 0 fatal; 126 report-only findings in committed evidence
```

Before my commit it read `ids=101 … undefined=47`; **zero findings of any severity are attributed
to `patterns.md` itself** either side, and the two retired `undefined` sites are the dangling
`P-103` citations in the fire's own RED transcript.

**THE DEAD-PATH PIN IS NOT MOVED.** `git diff` against the fork point touches
`.softhouse/guards/dead-path-frontier.pin` on zero lines, and the frontier is measured at
`108 == 108`.

A second, final bar was run after this handoff was written; see §7.

---

## 6 · Scope, and one declared overreach

Files changed on this branch:

| File | Change | In the brief's scope line? |
|------|--------|---------------------------|
| `.softhouse/patterns.md` | `+P-103` (append only; nothing above it edited) | yes |
| `.softhouse/capture/t458-fixture-literal-reflex/` | new: 2 drives, 7 transcripts | yes |
| `.softhouse/conformance.sh` | +9 lines inside one existing `warn` branch | yes (item 2) |
| `.softhouse/guards/check-dead-path-frontier.sh` | +26 `echo` lines + a comment block inside the existing `added_n > 0` branch | **no — declared** |

**The declared one.** The brief located the refusal message in `conformance.sh`; it is in the
guard. Editing only `conformance.sh` would have left the message six workers actually read
unchanged, which defeats item 2 entirely. I edited both and am flagging it rather than quietly
widening my grant. If a reviewer holds that the guard file was out of grant, the guard hunk is a
self-contained block of `echo` lines inside one `if` and reverts cleanly on its own; the
`conformance.sh` hunk stands independently.

**On contention.** `conformance.sh` was **not** held by another worker at any point I touched it,
and my hunk adds no function, no variable, no cardinal and no control flow — 9 `warn` lines
appended after an existing `sed` inside the existing `elif` branch. Conflict risk against a
concurrent edit elsewhere in that 6,300-line file is minimal, but if a merge does conflict, **the
change is fully specified by §3b above** and can be re-applied by hand: insert those seven `warn`
lines immediately after `LC_ALL=C sed -n '1,40p' "$d/diff" >&2` in `guard_dead_path_frontier()`.

Untouched, as required: `.softhouse/LOCK`, `.softhouse/tasks.json`, `.softhouse/RESUME.md`,
`.softhouse/program.json`, `.softhouse/guards/dead-path-frontier.pin`, the census, the vector
store, every Go path.

---

## 7 · What is still open

1. **The `P-103` cardinal is claimed against three live sibling workers.** If `T462`, `T465`,
   `T466` or `T467` also landed a `P-103`, **renumber mine, not theirs** — the entry says so, and
   the merger should re-run `check-pnumber-citations.py` on the merge result rather than on either
   branch.
2. **The wrapper-arm remedy is not reachable on every refusal path.** `guard_dead_path_frontier()`
   in `conformance.sh` has four `warn` arms; I added the remedy to the one that fires on an
   unrecorded `+` row, which is the one this class trips. The `removed_n != 0` arm and the two
   instrument-failure arms are different defects with different remedies and were deliberately
   left alone.
3. **Nothing here detects the reflex earlier than the bar.** A worker still learns at their first
   committed bar rather than at edit time. A pre-commit hook or a `sweeplib` helper that offers the
   assembled-path idiom would move the lesson earlier; that is a separate task and I did not file
   it, since filing tasks is outside this worker's grant.
4. **`patterns.md` still carries two in-file `P-n` collisions** (`P-12`, `P-13`, each defined
   twice) and two declared-dangling ids (`131`, `261`). Report-only today, and unchanged by me —
   but a register with duplicate definitions is one landing away from the `P-86` shape again.

---

## 8 · Final bar, on the fully committed tree

Re-run after this handoff and the drive transcripts were committed, so that the graded tree and
the delivered tree are the same bytes.

Taken at **`963fe613`**, on a tree measured clean **before** the run (`git status --porcelain`
= **0 paths**). Full transcript committed at
`.softhouse/capture/t458-fixture-literal-reflex/out/90-FINAL-BAR-963fe613.txt`.

```
$ git status --porcelain | grep -ac ''
0                                            <- clean BEFORE the run

$ bash .softhouse/conformance.sh            # bash, never sh/zsh
BAR EXIT = 0

$ grep -c 'probe = ' barFINAL.txt
1                                            <- PRESENCE TESTED FIRST. 0 would be a failed HARD
                                                guard (exit 2 precedes the probe line), never `down`.
$ grep 'probe = ' barFINAL.txt
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```

```
conformance:   frontier == pinned (all 11 rows, by path).                       <- fail-open, unmoved
conformance:   PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=102 gaps=none in-file-collisions=2
conformance:   PNUMBER-CITATIONS: sites=14056 definition=103 consistent=719 bare=13050
                                  misdirecting=81 undefined=45 negative-control=58
conformance:   PNUMBER-CITATIONS: declared-dangling ids = [131, 261]
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   T316-DEADPATH-CENSUS: corpus=1686 deadFiles=75 deadOccurrences=108
                                     resolving=1594 indeterminate=126 prose=428
conformance:   GUARD-COST CENSUS: 16 guards timed, 66s total wall, ceiling breaches 0,
                                  unbudgeted guards 0.
conformance:   all 16 wrong ledger implementations DIED through this harness, not by hand.
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

`ids=102 gaps=none` with `P-103` defined, `definition=103`, **0 fatal** — the hard guard that
reads `patterns.md` is green on my entry. `deadOccurrences=108` and the fail-open frontier
`11 == 11`: **neither pin moved, and neither instrument I shipped is on either frontier.**

**One honest note on ordering.** This transcript is committed *after* the run that produced it,
so the commit carrying it is by construction one commit later than the tree it grades. The graded
sha is stated above and the tree was clean at that sha; every byte of the deliverable — the
pattern entry, both message changes, both drives, all their transcripts, and this handoff — was
present and committed at `963fe613`. The only thing added afterwards is this section and the
transcript file it quotes.
