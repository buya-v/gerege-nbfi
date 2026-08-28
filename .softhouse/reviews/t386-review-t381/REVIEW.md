# T386 — independent review of T381 (`softhouse/T381-t379-conditions` @ `9eedfe4d`)

**VERDICT: APPROVED WITH CONDITIONS.**

Subject: T381's application of T379's R1–R4 to
`.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh`, plus three new
instruments, an audit and two bar transcripts.
Reviewed at `9eedfe4d`; `main` was `094bffca` when I measured (it moved twice under me and I
re-derived rather than carried numbers forward).

Everything below was **driven**. Where I quote a number I ran the thing that produced it, and the
instrument that produced it is committed beside this file. Where a claim of T381's survived, I say
so as plainly as where one did not.

---

## 0. The eight answers, up front

| question | answer |
|---|---|
| **Is there a SEVENTH instance of the discarded-status shape?** | **YES — `F-1`, and it is NEW IN T381's OWN R4 REPAIR, not inherited from `main`.** `err=$(cat "$SWEEP_ERRF")` in `sel()` and its twin in `engine_count()` discard their status; and because the whole `$SWEEP_ERRF` mechanism is unchecked, a `2>` redirect that cannot be opened makes bash return **1** — the one status this file reads as "the engine ran and matched nothing". **Reproduced on the branch AND on the merge result: `SWEEP-RESULT … selectors=16 did_not_run=0 calibration=yes exit=0` with fifteen of sixteen selectors printing `MEASURED ZERO` for searches that never ran.** Five lines close it. |
| **Is `engine_count()` itself clean?** | **YES.** Fourteen adversarial cases — rc 128, rc 2, rc 128-with-plausible-stdout, awk killed, awk non-zero after printing, non-numeric, empty, leading whitespace, negative, scientific notation, SIGPIPE, stderr-on-success — **all guarded, zero defects.** The chokepoint is sound. |
| **Does a healthy sweep still pass?** | **YES**, on the branch (`exit 0, selectors=16, did_not_run=0, calibration=yes`) and again on the merge result. The inverse defect T383 shipped this fire is **not** present. |
| **My three `git grep` measurements** | `-E '\bmain\b'` = **114**, `-E 'bmainb'` = **114**, `-F 'bmainb'` = **114**, and all three outputs are **byte-identical (one sha256)**. |
| **T381 vs T379/T238 on R3** | **T381 is right, and I can make its case harder than it did.** See §4. |
| **Is `T371.md:146` really false?** | **YES**, and it is refuted eight lines further down *its own file*. |
| **Bar on the branch** | `BAR_EXIT=0`, probe line **PRINTED** at `:162` reading `up`, frontier 11/11, dead-path GREEN 109/109, `VERDICT: PASS … 46 parity vectors, 7884 cells`. |
| **Bar on the merge result** | `BAR_EXIT=0`, probe **PRINTED** reading `up`, frontier 11/11, dead-path **GREEN 108/108**. The 109→108 move is **`main`'s, not T381's** — established by running the guard on three trees (§8). |

---

## 0.5 What T381 got right, said before the findings

An adversarial review that only lists defects mis-prices the work. Independently verified:

- **All four of T379's findings are closed in source, and every one is driven RED before GREEN.**
  I re-ran the whole drive suite at `9eedfe4d` and every arm reproduced — including the "thirteen"
  in D-R3a, which the drive derives from a diff of `hits total` rows and the review derived by
  reading the selector list, arriving at the same 13 by two routes (§10).
- **`engine_count()` is genuinely clean** — 14 hostile cases, 0 defects, including three shapes
  T381 never claimed to have guarded (`1e+17`, `-5`, `"   12  "`) and guards anyway because it
  validates the *shape* of the tally, not only its status (§2).
- **It found a sixth instance of the shape inside its own repair, before shipping**, and separated
  it as `D-R5` with a constructed RED specimen rather than describing it.
- **It corrected T379 and T238 on R3 and was right** — and I can now show it was more right than
  it knew (§4).
- **Its own drives refuted its own work four times and it recorded all four**, including the run
  it corrupted by editing the script underneath itself. The provenance holds up under checking
  (§10).
- **Its two Python instruments are count-anchored and refuse rather than proceed** — the R5
  variant builder dies if the block it patches is not found exactly once, which is the correct
  failure direction for a thing that constructs test specimens.
- **Scope is clean.** `git diff --name-only main...HEAD` is nine files: the one instrument in the
  grant, T381's own capture directory, and its handoff. `.softhouse/conformance.sh`,
  `.softhouse/guards/`, `.softhouse/vectors/`, `.softhouse/bin/`, `.softhouse/reviews/` and
  `nexus/` are untouched. No vector captured, promoted, edited or re-graded; no probe fired at the
  reference oracle.

**Merging T381 leaves the tree strictly better than `main`**, which still carries six instances of
the shape in this one file. That is why F-1 below is a condition on the `T399` wiring rather than
a rejection.

---

## 1. F-1 — THE SEVENTH INSTANCE. `$SWEEP_ERRF` IS AN UNCHECKED SINGLE POINT OF FAILURE

**Severity: MAJOR. Condition C-1.**

### The site

*(Line numbers are at `9eedfe4d` and they will move. The sites are `engine_count()`'s and
`sel()`'s `$(cat "$SWEEP_ERRF")`, and the two `2>"$SWEEP_ERRF"` redirects — named, per
`f3bf5563`, because I am about to file `FU-T386-5` against exactly this hazard.)*

R4 moved the engine's stderr out of the hit set and into a scratch file. That was the right
repair. But the scratch file is now load-bearing on **every** search in the file, and nothing
checks it:

```
205:  out=$(git grep "$@" 2>"$SWEEP_ERRF"); rc=$?        # engine_count()
207:  ENGINE_ERR=$(cat "$SWEEP_ERRF")                     # status DISCARDED
369:  all=$(git grep "$@" -- .softhouse 2>"$SWEEP_ERRF"); rc=$?    # sel()
370:  err=$(cat "$SWEEP_ERRF")                            # status DISCARDED
378:  if [ -n "$err" ]; then      # <- the ENTIRE R4 repair hangs off this test
```

Two failures, one root:

1. **`cat`'s status is not read.** If the scratch file cannot be read, `err` is empty and
   `[ -n "$err" ]` is false, so the R4 repair silently reverts to the pre-R4 behaviour it exists
   to remove: a warning the engine *did* emit is neither counted nor printed. A read that
   ERRORED is indistinguishable from a read that found nothing — the shape, verbatim.

2. **The redirect's own failure is read as a measured zero.** `2>"$SWEEP_ERRF"` is opened by
   *bash*, before the command runs. If it cannot be opened, **the command never runs and bash
   returns 1** — and `1` is the exact status both `engine_count()` and `sel()` are built to read
   as "the engine ran over the corpus and matched nothing". Measured
   [`out/T386-errf-drive.txt` ARM 1]:

   ```
     parent directory missing   : rc=1  stdout=[]
     scratch file mode 000      : rc=1  stdout=[]
   ```

### What T381 got right, and it is why this is a condition and not a rejection

When the scratch file is unopenable **from the start**, the `-F POSITIVE` calibration arm
demands ≥ 1 hit, gets 0, and the sweep **refuses at exit 3** — `CALIBRATION MISSED`
[`out/T386-errf-drive.txt` ARM 2]. That is P-72 earning its keep: a positive arm catches a whole
class of "the engine never ran" that no status check was looking for. **Credit where it is due —
T381's own front door stops the whole-run case.**

### But the calibration runs ONCE, at the front door, and the shape survives behind it

`out/T386-errf-midrun-drive.txt`. A `git` shim counts `grep` invocations and removes the scratch
directory once the seven calibration searches are past. Nothing else is touched. The **control**
is the identical shim with the removal disabled.

```
CONTROL: SWEEP-RESULT: commit=9eedfe4d selectors=16 did_not_run=0 calibration=yes exit=0
         control: exit=0  MEASURED-ZERO lines=0

RED    : SWEEP-RESULT: commit=9eedfe4d selectors=16 did_not_run=0 calibration=yes exit=0
         red: exit=0  MEASURED-ZERO lines=15  DID-NOT-RUN lines=0

DRIVE-RESULT: control_exit=0 control_mz=0 red_exit=0 red_mz=15 red_dnr=0
*** F-1b REPRODUCED
```

Fifteen selectors printed

```
    MEASURED ZERO -- engine ran over 8291 tracked files in the sweep corpus and matched nothing
    hits total: 0   archived (snapshots, correctly stale): 0   LIVE: 0
```

for searches **that never ran**, while the summary line declared the run clean and admissible.
The fifteen (not sixteen) is derived, not chosen: bash opens S1's redirect *before* the shim
deletes the directory, so S1 alone completes on an already-open descriptor. The count falls out
of the mechanism, which is how I know I drove the mechanism I described.

**This is the worst possible failure for this artefact.** The sweep's entire output is candidate
casualties; sixteen zeros at exit 0 reads as "no casualties", which is the negative-nobody-
measured that the file is *named after*. A reader quoting that transcript would be quoting
nothing.

### Reachability

Not exotic: `ENOSPC` on the temp filesystem, a quota, a tmp reaper during a run that makes
sixteen `git grep` passes over 8 300 files, a container tmpfs going away, `TMPDIR` pointed at a
directory a wrapper cleans. None of these needs a hostile actor; the drive uses a shim only to
make the timing deterministic.

### And it is NOT inherited. It is NEW, in T381's own R4 repair

`main` has no scratch file at all:

```
main:137   all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?      # no mktemp anywhere in the file
```

`$SWEEP_ERRF`, the `mktemp`, the two `2>"$SWEEP_ERRF"` redirects and the two unread `$(cat …)`
arrived **with R4**. So this is not a survival from `main` that T381 failed to sweep up — it is
the seventh instance of the shape, **created by the repair for the fourth finding**, exactly as
the sixth was created by the repair for the third. T381 caught its own sixth by auditing its own
new code; it audited its own new *pipelines* and its own new `2>/dev/null`, and the thing it
added was neither.

That is the pattern worth carrying out of this task, and it is stronger than "the shape recurs":
**this file's defect rate is not a property of `casualty-sweep.sh`, it is a property of the
repairs.** Six of the seven instances were introduced by somebody fixing the previous one. The
next task to touch it should budget for an eighth and audit its own diff for *discarded statuses*,
not for the two syntactic forms the last audit happened to bucket.

### The fix, and why it is small

`cat` fails in exactly the same circumstances the redirect fails — the RED transcript shows
`cat: …/errf: No such file or directory` on every affected selector. **Reading `cat`'s status
closes the whole finding:**

```
  err=$(cat "$SWEEP_ERRF"); cat_rc=$?
  if [ "$cat_rc" -ne 0 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR DID NOT RUN: the engine'"'"'s stderr channel is unreadable, so a\n'
    printf '    *** status of %s cannot be told apart from a search that never started.\n' "$rc"
    return
  fi
```

and the same three lines in `engine_count()` (returning 2). Five lines, two sites, and the
seventh instance is gone.

### Why T381's own audit could not have found it — the generalisable part

`AUDIT.md` promises to classify **"every `2>/dev/null` and every pipeline in the file"**. It
delivers exactly that, and its counts are internally correct (§7). But the defect class is
**every discarded status**, and `err=$(cat …)` is neither a `2>/dev/null` nor a pipeline. It has
no row. Nor do `$(date -u +%s)` ×2 or `$(git rev-parse --short HEAD)` ×2.

> **A taxonomy narrower than the defect class does not find the defect; it certifies the part of
> the file the taxonomy could see.** The one construct that fell outside T381's two buckets is the
> one carrying the seventh instance. That is not bad luck — it is what a bucketed audit does.

---

## 2. `engine_count()` — THE CHOKEPOINT IS CLEAN. FOURTEEN CASES, ZERO DEFECTS

Instrument: `instruments/t386-engine-count-drive.sh`; transcript `out/T386-engine-count-drive.txt`.
The function is **extracted from git by name** (never by line number — this program lost a day to
a pin that moved 546 lines, `f3bf5563`) and its sha256 printed, so the drive cannot grade an
edited copy: extract sha `5c63699531ce3875…`, file sha `1fa6acfe6a24588c…`.

| case | hostile engine | returned | verdict |
|---|---|---|---|
| C0 | real git, known-present string | 0, `N=2` | control |
| C1 | real git, sentinel absent (rc 1) | 0, `N=0` | control — a *measured* zero |
| C2 | `git grep` → 128 | **2** | guarded |
| C3 | `git grep` → 2 | **2** | guarded |
| C4 | `git grep` → **stdout `file:7` AND exit 128** | **2** | guarded — status beats plausible output |
| C5 | `awk` killed by SIGTERM | **3** | guarded |
| C6 | `awk` prints `9999` then exits 1 | **3** | guarded |
| C7 | `awk` prints `not-a-number` | **3** | guarded |
| C8 | `awk` prints nothing | **3** | guarded |
| C9 | `awk` prints `"   12  "` | **3** | guarded |
| C10 | `awk` prints `-5` | **3** | guarded |
| C11 | `awk` prints `1e+17` (real awk does this past ~1e16) | **3** | guarded |
| C12 | SIGPIPE — awk closes its input immediately | **3** | guarded |
| C13 | search SUCCEEDS but writes stderr | 0, `N=3` | correct — not a hit |

`DRIVE-RESULT: cases_guarded=14 cases_defective=0`.

C11 is worth naming: real `awk` switches to `%.6g` past about 1e16, and `case "$n" in *[!0-9]*)`
catches it. That is a defect T381 did not claim to have guarded and guarded anyway, by choosing to
validate the *shape* of the tally rather than only its status.

**The three statuses `engine_count()` reads — `git grep`'s, `awk`'s, and the tally's own
numeric shape — are the right three, and they are read in the right order.** Everything in F-1
happens *outside* the function's three checks, in the plumbing the function assumes.

---

## 3. `set -o pipefail` — CONFIRMED PRESENT ON `main`, AND IT HELPED NOTHING

Measured, not read from the handoff [`out/T386-status-census.txt` §1]:

```
  SHIPPED : 118:set -uo pipefail
  MAIN    :  56:set -uo pipefail
```

`main`'s copy of `casualty-sweep.sh` (sha `e9f30047bb0fbd46…`, the same BEFORE hash T379 cites
and T381's drive re-derives) has carried `set -uo pipefail` the whole time, while **six**
instances of the fail-open shape lived in it, including the two calibration arms at `:100` and
`:108` that T367, T379 and T381 successively dug out.

> **Propagating a status that nothing reads is not a guard.** `pipefail` made `git grep`'s 128
> available at the assignment. Nobody read the assignment. A reviewer who greps a file for
> `pipefail`, finds it, and moves on has learned that the status was *available* — which is a
> statement about plumbing, not about the instrument. The presence of the option was being quoted
> as reassurance, and that is worse than its absence would have been, because absence at least
> reads as a finding.

T381 says this in its handoff and its `AUDIT.md` §0. It is the most transferable sentence in the
whole task and I confirm it verbatim.

*One precision correction while I am here.* `AUDIT.md` §1 calls `main:100` and `main:108`
"both fail-open sites". Only `:108` is. `:100` is the **positive** arm: a failed search there
yields `n=0`, and `n < 1` is that arm's *refusal* condition, so its discarded status fails
**closed**. The distinction is not pedantry — it is the identical mechanism that stopped the
whole-run half of my F-1 (§1). Recording `:100` as fail-open loses the one lesson that would have
told T381 where its remaining exposure was. **`FU-T386-1`, MINOR.**

---

## 4. R3 — T381 CORRECTED T379 AND T238, AND IS RIGHT. HERE IS THE HARDER VERSION

### My measurements, on the branch head, whole repository and `-- .softhouse` alike

```
git grep -c -E '\bmain\b'  -- .softhouse  →  114
git grep -c -E 'bmainb'    -- .softhouse  →  114
git grep -c -F 'bmainb'    -- .softhouse  →  114
```

T381 measured 109/109/109 at `93e82869`; I measure 114/114/114 at `9eedfe4d` and **108/108** on
plain `main` at `094bffca`. Three heads, three numbers, one fact — exactly as T381 predicted: the
number counts how many times this program has written the string `bmainb` down, so it grows every
time the finding is recorded. T379's 97/97 is the same fact at a smaller corpus. **No conflict.**

### Two measurements neither T379 nor T381 took, and they settle it

```
sha256 of the -n output of all three forms:  c49a10cc1061a4a2…  (IDENTICAL, 114 lines each)
git grep -c -P '\bmain\b'  -- .softhouse  →  22524     <- PCRE, real word boundaries
git grep -c -E 'ma(in|ni)' -- .softhouse  →  33751     <- ERE alternation, interpreted
git grep -c -F 'ma(in|ni)' -- .softhouse  →      0     <- the same pattern, literally
```

The last pair is the one that matters. **This engine interprets ERE metacharacters perfectly
well.** It is not "literal-minded", it is not "broken", and it is not "fabricating". POSIX ERE
simply has no `\b`; `git grep -E` compiles the escape of an ordinary character down to that
character, and the result matches the literal string `bmainb`, 114 times, in 114 lines that are
**documents about this very hazard** — written by T234, T238, T239, T371, T379, T381 and now me.

### And then the sample line told me something none of us expected

`ARM B` prints four of the 114 matching lines. One of them is
`.softhouse/capture/t234-sweep-instrument-audit/HANDOFF.md:272`, and reading it whole
(`:266–276`) shows **T234 already ran the `-P` control, three hundred tasks ago, and already got
this right**:

```
git grep -E  five-alternative=3   four-alternative=3   \bmain\b contributes= 0
git grep -P  five-alternative=64  four-alternative=3   \bmain\b contributes=61
git grep -E -c 'bmainb'  repo-wide = 0        git grep -E -c '\bmain\b' repo-wide = 0
git grep -P -c '\bmain\b' repo-wide = 17646
```
> "**PARTIALLY VOID: the instrument reported 3 hits where a sound engine reports 64 — a 95.3 %
> recall loss (61/64)**"

Two things follow, and they are the most useful output of this review after F-1.

1. **T234 characterised the hazard correctly — as RECALL LOSS — and proved it with the exact
   `-P` control I re-ran.** The "the engine is FABRICATING a hit" framing entered *later*, in
   T238, and has been copied forward ever since — into `casualty-sweep.sh`'s header, into T379,
   into T381's brief, into mine. **The program degraded a correct account into an incorrect one
   and then spent three tasks re-deriving a weaker version of what it already had.**
2. **T234 measured `git grep -E -c 'bmainb'` repo-wide = 0.** I measure **114**. Re-run today by
   `ARM F`:

```
  git grep -E -c 'bmainb'    repo-wide = 114     (T234 measured 0)
  git grep -E -c '\bmain\b'  repo-wide = 114     (T234 measured 0)
  git grep -P -c '\bmain\b'  repo-wide = 22737   (T234 measured 17646)
```

   The `-E` figure went **0 → 114 purely because the program wrote the finding down**. That is
   the self-referential artefact demonstrated **across time**, not asserted — and it is why the
   "97/97", "109/109", "114/114" identity was never evidence of anything except that the notes
   exist. T381's instinct was right; this is the proof it did not have.

### What survives and what does not

- **The HAZARD survives, entirely.** A `\b` in an `-E` selector silently means literal `b`. A
  selector carrying one returns a number that is not the number it claims. `sel()`'s new refusal
  is the correct remedy and I drove it firing (§6, M3).
- **The EVIDENCE long used for it does not.** "The two forms return byte-identical output,
  therefore the engine fabricates" is a **measurement artefact**: the corpus is matching documents
  about itself, and the identity is the *expected* result of a documented POSIX limitation, not
  the symptom of a broken engine. T238's "FABRICATING a hit … and it was the decoy line" framing
  is a misdiagnosis, and T234's own transcript predates and contradicts it. T381 saw the first
  half of this and said so; the `-F`/`-P` controls and the T234 citation are the proof.

**This program should record that it caught itself measuring its own documents.** The corpus is
now large enough, and self-referential enough, that a selector whose pattern appears in
`.softhouse/` cannot distinguish "the world contains this" from "my own notes contain this".
T381 hit the same wall from the other side in its §5.1(1) and (3), where its first `-E`
calibration arm was satisfied by *its own definition line*. Same artefact, two directions, one
fire.

**`FU-T386-8` (MINOR, doctrine).** The correct account (recall loss, with a `-P` control) exists
at `t234-sweep-instrument-audit/HANDOFF.md:266–276` and was superseded in practice by a weaker
one. Worth a line in `patterns.md`: *when a later task re-frames an earlier measurement, cite the
earlier transcript or re-run it — a re-framing that does not is how a program loses a result it
already paid for.*

### Two consequences T381 did not carry all the way

**FU-T386-2 (MINOR) — the header now contradicts itself.** T381 corrected the framing at `:107–110`
("git compiles the backslash-class down to those literal letters") but left T371's earlier prose
standing:

- `:32–35` still says `git grep -E` "has been measured **FABRICATING** a hit". It was not.
- `:49–50` still says `-E` reads `\b` as a literal `b` "and returns **zero SILENTLY**". On this
  corpus it returns **114 self-referential hits**, not zero — which is *T381's own §5.1(3)
  finding*, written into the handoff and the drive's comments but not back into the header whose
  claim it refutes. The file states both accounts, ten lines apart, and `:49–50` is the stated
  *reason* for the `sel()` refusal.

**FU-T386-3 (MINOR) — `SWEEP OBSERVE` has no non-vacuity guard.** Its discriminator is
`escaped == literal ⇒ hazard LIVE`. Two zeros also agree. Measured:

```
git grep -c -E '\bzzqabsentterm\b'  →  0
git grep -c -E 'bzzqabsenttermb'    →  0
   ⇒ AGREE ⇒ it would print "T238 hazard LIVE" having measured nothing.
```

So the standing observation would keep reporting the hazard live on a corpus that had stopped
containing the term — a P-35 shape in the one arm T381 added specifically to stop asserting this
fact in prose. The cheap fix is the control I used above: compare `-E '\bmain\b'` against
`-P '\bmain\b'`, which **cannot** agree on any corpus containing the word (114 vs 22 524 here),
so the arm can never report from an empty measurement. Not blocking; the arm is explicitly
non-gating and it is still better than the prose it replaced.

---

## 5. THE HEALTHY CONTROL — IT PASSES, ON BOTH TREES

The demand is not negotiable in this fire: `T383` shipped a fail-open fix that refused every
healthy run, and a guard that refuses everything is the same defect wearing the opposite sign.

**Branch (`9eedfe4d`)** — `out/T386-healthy-sweep-control.txt`:

```
SWEEP CALIBRATE+F: PASS -- known positive matched 2 time(s) …
SWEEP CALIBRATE-F: PASS -- known negative matched 0 times, and the search RAN (rc=1)
SWEEP CALIBRATE+E: PASS -- -E interpreted it (2 hit(s)) and -F did not (0). They DISAGREE,
SWEEP CALIBRATE-E: PASS -- known negative matched 0 times under -E, and the search RAN (rc=1)
SWEEP OBSERVE: T238 hazard LIVE -- escaped=114 literal=114 AGREE …
SWEEP-RESULT: commit=9eedfe4d selectors=16 did_not_run=0 calibration=yes exit=0
EXIT=0
```

**Merge result (`67fe18f0`)** — `out/T386-misc-drives.txt`, M3 control:

```
SWEEP-RESULT: commit=67fe18f0 selectors=16 did_not_run=0 calibration=yes exit=0
control exit=0
```

All sixteen selectors ran on both, all four new arms passed, and the LIVE lists are populated.
**The four new refusals do not refuse a healthy fire.**

---

## 6. THE OTHER THREE THINGS I DROVE MYSELF

`instruments/t386-misc-drives.sh`, transcript `out/T386-misc-drives.txt`.

**M1 — is `:127`'s surviving `2>/dev/null` really fail-closed?** T381 asserts it. Drive it: a shim
makes `git rev-parse --show-toplevel` exit 128.

```
  exit=2
    SWEEP ABORT (exit 2): not inside a usable git work tree; there is no corpus to sweep
  >>> CONFIRMED FAIL-CLOSED
```

**T381's classification of `:127` stands, and it is the only executable `2>/dev/null` left in the
file** — I re-derived that from the shipped head, not from the audit
[`out/T386-status-census.txt` §2].

**M2 — the inverse defect in `sel()`'s new check.** `printf '%s' "$a" | grep -q PAT` under
`pipefail`: `grep -q` exits on the **first** match, so `printf` can take `EPIPE`, and `pipefail`
would hand back `printf`'s non-zero — which `esc_rc >= 2` reads as *"the CHECK ITSELF did not
run"*. A guard that misfires on its own success is F-1 wearing the opposite sign. Driven at the
worst case (400 kB argument, match at the front):

```
    match at the FRONT of a 400 kB argument (worst case for EPIPE): rc=0
  >>> no misfire
```

**Not a defect.** Reported because the absence of it is a fact someone will otherwise have to
re-derive.

**M3 — does the refusal actually fire on a real `\b` selector?** A probe selector
`-n -E '\bmain\b'`, inserted by a script that refuses unless the backslash-class survives the
round trip (T381's own `awk -v` lesson, applied to my instrument):

```
  *** SELECTOR REFUSED: its pattern carries a backslash-class, which this engine
  SWEEP-RESULT: commit=67fe18f0 selectors=16 did_not_run=0 calibration=yes exit=3
  >>> CONFIRMED: the refusal fires on a real `\b` selector and the run exits 3.
```

**FU-T386-4 (MINOR, and it is a direct input to `T399`).** Look at that `SWEEP-RESULT` line
again. Seventeen selectors were declared, one was refused, and the summary reads
`selectors=16 did_not_run=0 calibration=yes` — **byte-identical in its three cardinals to a
perfectly clean run.** A refused selector is counted in neither `SWEEP_SELECTORS` nor
`SWEEP_DIDNOTRUN`; the *only* thing that distinguishes the two runs is `exit=3`. See §9.

---

## 7. T381'S OWN COUNTS, RE-DERIVED — AND WHERE THE LINE NUMBERS LAND

`instruments/t386-status-census.sh` / `out/T386-status-census.txt`. I enumerate the sites and
print them; the reader counts from the list rather than from prose.

| T381's claim | my finding |
|---|---|
| `pipefail` present `:118`, and on `main` | **CONFIRMED** (`main:56`). §3. |
| `2>/dev/null` on an executable line: **1** (`:127`), fail-closed | **CONFIRMED**, and driven (§6 M1). |
| Pipelines a fact depends on: **4**, all read | **CONFIRMED** — `:209` awk tally, `:345` esc check, `:392` live, `:393` arch. (Two further status-bearing sites, `:205` and `:369`, are command substitutions rather than pipelines and are also read, so the *total* read is 6.) |
| Pipelines whose status is discarded: **10** | **CONFIRMED as a count of pipelines**, and its list is internally consistent. **But it is not a count of discarded statuses.** At least **six** more exist that the audit has no row for: `:207` and `:370` (`$(cat "$SWEEP_ERRF")` — F-1), `:166` and `:194` (`$(date -u +%s)`), `:409` and `:464` (`$(git rev-parse --short HEAD)`). |
| `FU-T381-1` at `casualty-sweep.sh:348`, bounded by the `:376` corpus assertion | **The residual is real and the bound is real** — `:412` (shipped numbering) refuses at exit 2 if `git ls-files` yields < 1, before any selector runs. **The line numbers are wrong at the shipped head**: see below. |

**FU-T386-5 (MINOR).** `AUDIT.md` honestly labels its line numbers "as at `93e82869`". The file
then grew 36 lines (433 → 469) in two later commits, and **14 of the 16 sites I checked have
moved**; only `:118` and `:127` still land. `:309` is now `:345`, `:348` is now `:384`, `:376` is
now `:412`. That is fine inside a dated audit — but the **handoff** §7 hands the next holder a bare
`casualty-sweep.sh:348` as `FU-T381-1`'s site, and at the shipped head `:348` is a `printf` inside
a refusal message. This fire already ratified the rule (`f3bf5563`, *"MATCH THE WRONG-IMPL PIN BY
NAME, NEVER BY LINE — it moved 546 lines"*). Restate the site by name:
*"the `MEASURED ZERO` denominator, `$(git ls-files .softhouse | grep -c .)`, inside `sel()`"*.

---

## 8. THE BAR — BRANCH AND MERGE RESULT, BOTH FROM CLEAN TREES

Run with **`bash`**, never `sh`. `git status --porcelain` empty in both worktrees before the run;
neither transcript was captured over an untracked file (the failure that reddened `main` for
`T370` and `T361`).

**Branch, `/private/tmp/t386-t381` @ `9eedfe4d`** — `out/T386-BAR-branch-9eedfe4d.txt`:

```
:94   frontier 11, pinned at 11
:99   frontier == pinned (all 11 rows, by path).
:157  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
:158  T316-DEADPATH-CENSUS: corpus=1351 deadFiles=76 deadOccurrences=109 …
:162  reference oracle (https://localhost:8443/…/actuator/health) probe = up
:635  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
:665  BAR_EXIT_BRANCH=0
```

**Read presence before value (P-84, `patterns.md:2813`).** The probe line **is printed** and reads
`up`; exit 0 with the probe present is a real PASS. Every figure T381 reports for its own bar
reproduces exactly.

**Merge result, `/private/tmp/t386-mr` @ `67fe18f0`** (`main` `094bffca` + `softhouse/T381-…`,
merged clean by `ort`, no conflicts) — `out/T386-BAR-mergeresult-67fe18f0.txt`:

```
:94   frontier 11, pinned at 11          :99  frontier == pinned (all 11 rows, by path).
:157  dead-path frontier: GREEN
:158  T316-DEADPATH-CENSUS: corpus=1376 deadFiles=75 deadOccurrences=108 …
:162  probe = up                         :635 VERDICT: PASS (exit 0) — 46 parity vectors
:665  BAR_EXIT_MERGE=0
```

### The dead-path number moved, and I established whose it is by RUNNING (P-83)

The branch says 109 and the merge result says 108. Three runs of
`.softhouse/guards/check-dead-path-frontier.sh`, on three trees, no arithmetic:

| tree | census | frontier |
|---|---|---|
| `main` `094bffca`, alone | `corpus=1373 deadFiles=75 deadOccurrences=108` | `GREEN rows=108 pinned=108 added=0 removed=0` |
| `softhouse/T381-…` `9eedfe4d` | `corpus=1351 deadFiles=76 deadOccurrences=109` | `GREEN rows=109 pinned=109 added=0 removed=0` |
| merge result `67fe18f0` | `corpus=1376 deadFiles=75 deadOccurrences=108` | `GREEN rows=108 pinned=108 added=0 removed=0` |

**The 109 → 108 move is `main`'s** — it arrived with the `T383`+`T385` merge, which also carried
the matching pin. T381 contributes `+3` to the corpus and **`+0` dead paths**; `added=0
removed=0` on the merge result is the check, and it is a measurement, not a subtraction.

---

## 9. THE BACKLOG T381 NAMED — EACH ONE CHECKED

### `FU-T381-2` — is `T371.md:146` false? **YES, and its own file refutes it.**

`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T371.md:146`:

> "No file this task touched is read by `conformance.sh`"

Eight lines later, at `:154`, the same document prints the bar refusing **on the file T371
touched**:

```
T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=109 added=1 removed=0
> .softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh | .softhouse/\n
```

and at `:175` states it in words: *"My `casualty-sweep.sh` change **was** tracked when I ran the
bar, so the guard saw it and refused."*

Confirmed independently, by running rather than by inference:

```
$ python3 .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py \
      .softhouse/capture/t363-oracle-baseline/instruments/
corpus    : 2 tracked .sh/.py; 1 are repo-wide search instruments
TIER 1 … : 0
```

and the bar's own census line from my branch run, `:93–94`:
`CENSUS fail-open instruments — inspected 1351 tracked .sh/.py file(s) under … (git ls-files,
whole repository)`. The linter opens `casualty-sweep.sh`; the dead-path census opens it too, and
T371's own RED is the proof that it does.

**A merged handoff carrying a claim its own next paragraph disproves is worth a finding of its
own. `FU-T386-6`, MINOR** — the intended meaning ("no vector, no graded artefact") is correct and
the repair is one line, in a file outside both T381's grant and mine.

### `FU-T381-3` — real, outside T381's grant (`CASUALTIES.md:97`, `reference-oracle.md:930`). Confirmed as sited; not re-litigated here.

### `FU-T381-4` / `P-45` / `T399` — the sweep still gates nothing. **Is wiring it safe?**

T381 files this against itself and does not claim it closed. Correct, and **not** a reason to
reject. `T399` will act on my answer, so here it is, with the reasoning:

**Not yet. Wire it AFTER C-1, and wire it on the EXIT CODE.**

1. **Wiring it before F-1 is closed would make the bar worse, not better.** Today the sweep
   gates nothing, so a transient `TMPDIR` failure produces a misleading transcript nobody has to
   act on. Wired, that same failure produces **`exit 0` on a sweep that measured nothing** — the
   bar would go green *because* the instrument went blind. A gate that a filesystem hiccup turns
   into a rubber stamp is worse than no gate. Five lines (§1) removes the objection.
2. **Gate on the exit status, not on the `SWEEP-RESULT` cardinals.** This inverts the usual
   advice in this program and §6's M3 is why: a refused selector is counted in neither
   `selectors` nor `did_not_run`, so a run with a refusal can print
   `selectors=16 did_not_run=0 calibration=yes` — identical in all three cardinals to a clean
   run. Only `exit` distinguishes them. If a wiring wants to read cardinals as well (it should),
   it must *also* derive the declared selector count from source
   (`grep -c '^sel "' casualty-sweep.sh`) and require `selectors == declared`.
3. **Gate on admissibility only, never on LIVE hits.** The file says so at `:44–46` and it is
   right: a LIVE hit is a candidate for a human, not a failure. Wiring `SWEEP_RC` is wiring
   "was this sweep interpretable", which is exactly what exit 0/2/3/4 already means.
4. **Budget the runtime.** Sixteen `git grep` passes over 8 291 tracked files is not free, and the
   bar already runs long. Consider `--` scoping or a cached corpus if the bar's wall clock
   matters.

One further caution for `T399`: this instrument's exit code is corpus-dependent by design
(S12–S16 hunt a *shape*), so a hard gate acquires a maintenance burden the moment someone commits
a document containing `\b` inside a quoted selector. Gate it; do not pin its numbers.

---

## 10. T381'S OWN RED DRIVES — RE-RUN, AND THE PROVENANCE CHECKED

### Provenance: does the committed transcript come from the frozen copy?

T381 discloses corrupting one run by editing the script under it (`§5.1`, point 5) and says the
final run came from a frozen copy. That disclosure raises the right question and I checked it two
ways rather than taking the answer:

- The committed transcript's header reads `repo: 3798074d`, three commits before the branch head.
  Its `AFTER sha256: 1fa6acfe6a24588cfdab967caa3a1710695f3ac503ad2e2c061b0429ba88e923` is
  **byte-identical to the `casualty-sweep.sh` that ships at `9eedfe4d`** (I hashed it myself), and
  its `BEFORE sha256: e9f30047bb0fbd46…` is **byte-identical to `main`'s** — the same hash T379
  cites. So the transcript grades exactly the artefact under review, whatever tree it was taken
  in. That is the property `P-22` is for, and the drive's design (extract both versions from git
  on every run) makes it hold *independently* of the frozen-copy question.
- `git log 3798074d..softhouse/T381-t379-conditions -- .../t381-t379-conditions/instruments/`
  is **empty**, and the drive script's sha256 at `3798074d` and at the head are the same
  (`48869e4572c5cfd3…`). **The instrument has not moved since the transcript.**

**Provenance accepted.**

### Re-run: every RED before its GREEN

`out/T386-RERUN-D-RED-DRIVES.txt`, run by me at `9eedfe4d` from the clean worktree
`/private/tmp/t386-t381` (`git status --porcelain` empty). `BEFORE_REF=main`, `AFTER_REF=HEAD`,
both hashes as above.

| drive | RED (BEFORE) — reproduced by me | GREEN (AFTER) — reproduced by me |
|---|---|---|
| **D-R2** | `exit 0` both ways; the `CALIBRATE` lines are byte-identical whether the anti-calibration search **ran** or exited **128** | `exit 3`, `the -F ANTI calibration search DID NOT RUN -- git grep rc=128`, and it prints `fatal: Invalid pathspec magic 'zzbogusmagic'` |
| **D-R1** | `exit 0`; four selectors print `hits total: 74 … LIVE: 0`, and the **archived field is EMPTY** — `grep -c` errored, produced no stdout, and the line printed anyway | `exit 4`, six `SELECTOR HIT, BUT ITS CLASSIFICATION DID NOT RUN`, no LIVE figure printed |
| **D-R3a** | under an `-E`→`-F` shim: `calibration=yes exit=0`, and **13** selector rows report a different `hits total` than the control (`clean=16 shimmed=16 ; rows that CHANGED: 13`); `MEASURED ZERO` lines under the shim: **0** | `exit 3`, `-E CALIBRATION MISSED … NOBODY MEASURED`, **no selector result printed at all** |
| **D-R3b** | `MEASURED ZERO … matched nothing` for `-E 'zz\bprobe'`, counted as a selector: `selectors=17 … exit=0` | `SELECTOR REFUSED: its pattern carries a backslash-class`, `selectors=16 … exit=3` |
| **D-R4** | first selector's `hits total` **74 → 75**: a stderr line counted as a hit and listed LIVE | `hits total` **74 → 74**, warning on its own `ENGINE STDERR on a search that DID complete (rc=0). NOT counted as a hit` line |
| **D-GREEN** | — | `exit 0`, four arms pass, `SWEEP OBSERVE … escaped=114 literal=114`, all sixteen selectors ran |
| **D-R5** | the constructed `if printf \| grep -q …` specimen: the selector goes through, prints `MEASURED ZERO … hits total: 0`, `selectors=17 … exit=0`; the only trace is `grep: invalid character range` ×3 | `SELECTOR REFUSED: the backslash-class CHECK ITSELF did not run (rc=2)`, `selectors=0 … exit=3` |

**And the re-run is byte-comparable to the committed transcript.**
`out/T386-RERUN-vs-COMMITTED-diff.txt`: **27 differing lines out of 193**, and every one of them is
a commit hash, a timestamp, or a corpus cardinal that grew by 2–4 files between `3798074d` and
`9eedfe4d` (`8369→8371` tracked, `8289→8291` under `.softhouse/`, `hits total: 230→234`).
**Every verdict line, every exit code and every `>>> RED/GREEN CONFIRMED` is identical.** A drive
that reproduces to that tolerance a day later, from a different head, on a corpus that moved, is a
drive.

**Every RED reproduced before its GREEN. No arm printed `DID NOT REPRODUCE` or `THE REPAIR IS NOT
PROVEN`.** Two of T381's own claims deserve calling out because I re-derived them independently:

- **"Thirteen is not a number I chose."** Correct. The drive derives 13 from a `diff` of the
  `hits total` rows; T379 derived 13 by reading the selector list; my run reproduces `rows that
  CHANGED: 13`. Two derivations, one number, and neither is typed anywhere.
- **`MEASURED ZERO` lines under the shim: 0.** T381's §5.1(3) — a literal-minded engine on *this*
  corpus returns self-referential hits, not silence — reproduces exactly, and it is the same fact
  as §4's 114.

**`FU-T386-7` (MINOR).** The drive **exits 0 no matter what its arms say.** Every
`>>> … DID NOT REPRODUCE` and `>>> … THE REPAIR IS NOT PROVEN` branch prints and continues, and
the script's last statement is an `echo`. A reader who checks the drive's exit status learns
nothing about the drive — which is `P-45` applied to the very instrument written to enforce
`P-45`. One accumulator and one `exit` closes it.

---

## 11. FINDINGS AND CONDITIONS

**Conditions of approval — `C-1` blocks the `T399` wiring, not the merge.**

| id | sev | finding | condition |
|---|---|---|---|
| **C-1** / **F-1** | **MAJOR** | The seventh instance. `$SWEEP_ERRF` is an unchecked single point of failure: `$(cat …)`'s status is discarded at `:207` and `:370`, and a `2>` redirect that cannot be opened returns **1**, which both `engine_count()` and `sel()` read as a measured zero. Driven: `exit 0`, `did_not_run=0`, fifteen fabricated `MEASURED ZERO` lines. | Read `cat`'s status at both sites and refuse (5 lines, §1). **Must land before `T399` wires the sweep into `conformance.sh`.** May be taken as a follow-up task; it does not block merging T381, which is a strict improvement on `main` either way. |
| `FU-T386-1` | MINOR | `AUDIT.md` §1 calls `main:100` fail-open. It is fail-**closed** by direction, and that same mechanism is what stops half of F-1. | Correct the classification; keep the lesson. |
| `FU-T386-2` | MINOR | The shipped header contradicts itself: `:32–35` "FABRICATING", `:49–50` "returns zero SILENTLY" vs `:107–110`'s correct account and T381's own §5.1(3) (a literal engine returns **self-referential hits**, not zeros). | Bring `:32–35` and `:49–50` into line with `:107–110`. |
| `FU-T386-3` | MINOR | `SWEEP OBSERVE` reports "hazard LIVE" from two agreeing zeros — no non-vacuity guard (P-35 shape). | Discriminate `-E` against `-P` on the same escaped pattern (114 vs 22 524 here); they cannot agree vacuously. |
| `FU-T386-4` | MINOR | A refused selector is counted in neither `SWEEP_SELECTORS` nor `SWEEP_DIDNOTRUN`; `SWEEP-RESULT`'s three cardinals cannot distinguish a refusal from a clean run. Driven. | Count refusals, or `T399` gates on the exit code (§9). |
| `FU-T386-5` | MINOR | Handoff §7 sites `FU-T381-1` at `casualty-sweep.sh:348`; at the shipped head that line is a `printf`. 14 of 16 audited line numbers moved. | Restate the site by name, per `f3bf5563`. |
| `FU-T386-6` | MINOR | `T371.md:146`'s claim is false and is refuted eight lines below it in the same file. T381's `FU-T381-2` is correct. | One line, in another task's merged handoff. |
| `FU-T386-7` | MINOR | `t381-red-drives.sh` **exits 0 regardless of its arms.** Every `DID NOT REPRODUCE` / `THE REPAIR IS NOT PROVEN` branch prints and continues; the script ends on an `echo`, and my re-run's `DRIVE_EXIT=0` is the measurement. A reader who checks the drive's exit status learns nothing — the drive is P-45 on itself. | Accumulate a failure count and exit non-zero. |
| `FU-T386-8` | MINOR, doctrine | `t234-sweep-instrument-audit/HANDOFF.md:266–276` already held the correct account of the `\b` hazard, with the `-P` control, and a later re-framing replaced it with a weaker one that three tasks then re-derived. | A line in `patterns.md`: when re-framing an earlier measurement, cite its transcript or re-run it. |

**What I could NOT test.** I did not reach the reference oracle beyond the bar's own probe; I did
not exercise the sweep on a non-macOS `git`, and `git grep`'s `\b` behaviour is a property of the
platform regex library, so §4's adjudication is a statement about *this host* (git 2.50.1, Apple
Git-155) — which is the only host the program's parity work runs on today, and the sweep prints
`SWEEP OBSERVE` on every run precisely so a different host shows up in the transcript.

---

## 11.5 Everything I wrote, and what it does

All inside `.softhouse/reviews/t386-review-t381/`. Nothing else in the repository was touched.

| path | what |
|---|---|
| `REVIEW.md` | this file |
| `instruments/t386-engine-count-drive.sh` | 14 hostile engines against `engine_count()`, extracted from git **by name** and sha-printed (§2) |
| `instruments/t386-errf-drive.sh` | F-1 ARM 1–3: what bash returns on a failed `2>` redirect, and the whole-run case the calibration catches (§1) |
| `instruments/t386-errf-midrun-drive.sh` | **F-1b**, the seventh instance: the scratch directory removed once calibration is past, with the removal-disabled control (§1) |
| `instruments/t386-misc-drives.sh` | M1 `:127` fail-closed, M2 the inverse defect, M3 the `\b` refusal + the healthy control (§6) |
| `instruments/t386-r3-measure.sh` | the R3 adjudication: the three counts, byte-identity, the `-F` and `-P` controls, T234's own figures re-run (§4) |
| `instruments/t386-status-census.sh` | independent re-derivation of T381's site counts, and the AUDIT-vs-shipped line-number check (§7) |
| `instruments/t386-deadpath-attribution.sh` | the dead-path guard on three trees, so 109→108 is attributed by running (§8) |
| `instruments/t386-filter-transcript.sh` | writes a sweep transcript with the quoted hit lines removed **and says so in the file** — committing 235 kB of other files' lines would import their repo-path references into T316's census, which is how T371's own bar went RED |
| `out/T386-engine-count-drive.txt` | `cases_guarded=14 cases_defective=0` |
| `out/T386-errf-drive.txt` | ARM 1 `rc=1`; ARM 2 refuses at exit 3; ARM 3 control exit 0 |
| `out/T386-errf-midrun-drive.txt` | `control_exit=0 control_mz=0 red_exit=0 red_mz=15 red_dnr=0` |
| `out/T386-misc-drives.txt` | M1/M2/M3 and the healthy control at exit 0 |
| `out/T386-r3-measure.txt` | 114/114/114, one sha256, `-P`=22524, `-F 'ma(in\|ni)'`=0, T234's 0→114 |
| `out/T386-status-census.txt` | the site enumeration and the 14-of-16 moved line numbers |
| `out/T386-deadpath-attribution.txt` | 108/108, 109/109, 108/108 on three clean trees |
| `out/T386-healthy-sweep-control.txt` | the healthy sweep, filtered as stated in its own header |
| `out/T386-RERUN-D-RED-DRIVES.txt` | my re-run of T381's own suite, `DRIVE_EXIT=0` (see `FU-T386-7`) |
| `out/T386-RERUN-vs-COMMITTED-diff.txt` | 27 differing lines in 193, all hashes/timestamps/corpus cardinals |
| `out/T386-BAR-branch-9eedfe4d.txt` | the bar on T381's branch — `BAR_EXIT=0`, probe printed `up` |
| `out/T386-BAR-mergeresult-67fe18f0.txt` | the bar on the merge result — `BAR_EXIT=0`, probe printed `up` |
| `out/T386-BAR-t386-branch.txt` | the bar on **this review's own branch**, from a clean tree after `git add -A` and commit |

---

## 12. Non-negotiables

No money path, no vector, no ledger code, no schema, no database, no network beyond the bar's own
health probe. This review captured, promoted, edited and re-graded **zero** vectors. Nothing here
touches deposit-taking, savings wording, name fields, national-ID handling, time zones or payment
rails. PostgreSQL remains the only database named. Everything I wrote is inside
`.softhouse/reviews/t386-review-t381/`.
