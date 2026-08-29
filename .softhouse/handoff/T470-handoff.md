# T470 — THE REFUSAL MUST NOT ARGUE WITH ITSELF

Branch `softhouse/T470-refusal-forecloses`, forked from `cb148f59`. Carries `C-T468-1` (MAJOR) and
`C-T468-2` (LOW) from `T468`'s independent adversarial review of `T458`.

**The dispatch said: RE-DERIVE, do not inherit T468's reading; if T468 is wrong, say so.** I re-derived
it from the shipped bytes. **T468 is right, and it under-counted its own evidence.**

---

## VERDICT: THE FORECLOSURE IS REAL — and there are FIVE sanctioning sites, not the two T468 named

`T468` cited two sites (the guard's header, and the same refusal message four lines above). I found
**three more**, all in `.softhouse/guards/dead-path-frontier.pin` — the file this guard grades
against — and the fifth is decisive in a way the first four are not.

---

## 1 · BOTH DISPOSITIONS, QUOTED FROM THE SHIPPED BYTES, AT THEIR LINE NUMBERS

All quotes are from `cb148f59` (my fork point, = `T458`+`T468` merged, tree as delivered).

### DISPOSITION A — PIN WITH ITS REASON. Offered, sanctioned, exercised.

**A1. `.softhouse/guards/check-dead-path-frontier.sh:55-61`** — the header block `WHAT A ROW DOES
**NOT** MEAN:

```
59 # resolves both exit 2 with the probe line ABSENT. A dead literal is a SMELL that must be
60 # inspected once, by a human, and then either repaired or pinned with its reason. This guard
61 # counts; it does not judge.
```

**A2. `.softhouse/guards/check-dead-path-frontier.sh:218-221`** — the **same refusal message**, inside
the **same `if [ "$added_n" -gt 0 ]` branch** `T458`'s block lives in, unchanged since `T316`. This
matters: the branch fires **only on NEW rows**, so the offer is live for exactly the case `T458`
declared closed.

```
218   echo "conformance: !! $added_n NEW dead path reference(s). A '+' row is a NEW site: REPAIR it"
219   echo "conformance: !! rather than pinning it. Either make the path resolve, or -- if the"
220   echo "conformance: !! reference is a deliberate fallback candidate -- make the instrument"
221   echo "conformance: !! REFUSE when no candidate resolves, and record why in the pin."
```

**A3. `.softhouse/guards/dead-path-frontier.pin:215-216`** (rows), reason at **`:170-171`** — the two
`FU-T299-2` ordered-fallback instruments, **pinned, never repaired**.

**A4. `.softhouse/guards/dead-path-frontier.pin:222-225`** (rows), reason at **`:81-87`** — `T305`'s
four red-drive literals, **dead by design**: *"A red drive plants files that MUST NOT exist in a clean
tree; that is what makes it a red drive."*

**A5. `.softhouse/guards/dead-path-frontier.pin:121-125` — THE DECISIVE ONE.** `T326` took a **NEW**
row (`T306`'s injected acceptance vector), inspected it, and **pinned it**:

```
121 #       * SAME CLASS, byte for byte, as the four T305 rows above. Pinning it is the disposition
122 #         T316's own header prescribes: "a SMELL that must be inspected once, by a human, and
123 #         then either repaired or pinned WITH ITS REASON."
124 #       * REPAIR WAS CONSIDERED AND IS NOT AVAILABLE. "Make the path resolve" means committing
125 #         `ZZZ-T306-INJECTED-preclosure-acceptance.json` into `.softhouse/vectors/ledger/`,
```

**A NEW row. Pinned with its reason. By a later worker. After explicitly considering repair and
rejecting it. In the very file this guard grades against.** That is *precisely* the case `P-103`
declared forbidden. No inference is required.

### DISPOSITION B — the foreclosure. `T458`'s text, and the register entry.

**B1. `check-dead-path-frontier.sh:235-236`:**

```
235   echo "conformance: !!   the INSTRUMENT, and not one of them grew the pin. Do ONE of these"
236   echo "conformance: !!   three, and never a fourth:"
```

The three are all repairs. Pinning is not among them, so "never a fourth" excludes it.

**B2. `check-dead-path-frontier.sh:244-245`:**

```
244   echo "conformance: !!      never a warning, never a pass. This is the arm this guard asks"
245   echo "conformance: !!      for in exchange for not pinning the row."
```

**Measurably wrong**, not merely narrow: `A2` requires the *same* refuse-when-nothing-resolves arm
**for the pin route too**. It is not bought in exchange for anything.

**B3. `.softhouse/patterns.md:3908-3911` — THE PERMANENT REGISTER, and the absolute form:**

```
3908 **AND THE FORBIDDEN FOURTH, stated because it is the one that will occur to the next worker:** do
3909 **not** split, concatenate or otherwise disguise the literal to slip past the selector, and do **not**
3910 add the row to the pin. The pin is a frontier, not an amnesty. Splitting the string leaves the false
3911 claim in place and removes the only instrument that would have found it.
```

The **first** half is right. The **second** half of that conjunction — *"and do not add the row to the
pin"* — is flatly contradicted by `A1`–`A5`. Supporting: `:3895` *"One of these three, never a
fourth"*, and `:3903`'s gloss that remedy 2 is *"what the frontier guard asks for in exchange for the
row."*

**B4. `.softhouse/conformance.sh:2906`** — a **third** site `T468`'s condition did not name, and it is
`T458`'s own added line: *"Repair the instrument; **do not grow the pin**, and do not split the"*.

### WHY THIS IS THE `T358` SPECIES, AND WORSE

`.softhouse/conformance.sh:2887-2889`, in the `removed_n` arm of the very same guard wrapper, already
records the class: *"[T358: this line used to say 'the pin is outside T323's edit grant', which stopped
being true when T326 regenerated the pin — **a false statement inside a refusal message**.]"* Same
species. Worse in one respect, exactly as `T468` said: **it also landed in the register**, which is what
every future worker reads as settled.

**One thing I will not overstate.** The presumption `T458` was defending is *correct and unchanged*: a
`+` row is a NEW site and the answer is normally REPAIR. Six of six workers in fire `20260829-080002`
repaired; none needed the pin. `T458` was not wrong about the remedy — it was wrong to write the
exception out of existence while the same screen, the header and the pin were all still exercising it.

---

## 2 · THE REPAIR — BOTH REFUSAL SITES, AND THE REGISTER FORWARD

### 2a · `.softhouse/guards/check-dead-path-frontier.sh` — the site six workers actually read

| Change | What |
|---|---|
| `:235-236` → 4 lines | the foreclosing clause is gone; the three are framed as *how to repair*, and the reader is told there is **exactly one other sanctioned route, named after them** |
| `:244-245` → 3 lines | remedy 2's arm is now asked for **on EITHER route**, because `A2` requires it for the pin route too |
| new block before `THE FORBIDDEN FOURTH` | `THE ROUTE THAT IS NOT A REPAIR, AND IS STILL SANCTIONED` — the gated pin route, quoting `A2` and the header sentence back, and naming the pin's own exercised rows |
| after `THE FORBIDDEN FOURTH` | *"(It is 'the FOURTH' because it is the fourth idea that occurs to a refused worker, not a fourth entry in a list. **PINNING WITH A REASON IS NOT IT.**)"* |
| header comment block | `T470 -- THE REFUSAL MUST NOT ARGUE WITH ITSELF`, with the five sites and the reasoning |

### I DID NOT APPLY `T468`'s §6 REPAIR AS SPECIFIED — and the reason is a measured hazard, not taste

`T468` specified replacing `"three, and never a fourth:"` with `"...the pin-with-a-reason route named
four lines above. **Never a fifth:**"`. **Two defects in that, both measurable:**

1. **`Never a fifth` de-synchronises the name `THE FORBIDDEN FOURTH`**, which is asserted **verbatim**
   by `T458`'s own drive (`10-drive-remedy-text.sh:60`, `FORBIDDEN="THE FORBIDDEN FOURTH"`), and is
   also spelled in `conformance.sh`'s wrapper and in `P-103`. Renaming it to "fifth" would have broken
   the predecessor's drive assertion; leaving it would have shipped a message that numbers a forbidden
   *fourth* after four permitted ones.
2. **"four lines above" is a positional pointer that is already false in the rendered output** — the
   `sed -n '1,40p' "$ADDED"` row listing prints between them, so on a 12-row refusal the offer is 16
   lines above. `P-86` is the rule: *the line moves, the sentence does not.*

**So I kept `THE FORBIDDEN FOURTH` byte-identical, added the pin route as an UNNUMBERED disposition
rather than "a fourth", and anchored by quoted sentence rather than by distance.** `T458`'s drive is
re-run below and still passes on my bytes — which it would not have under the literal §6 text.

This is the **fourth** time in this program a reviewer-proposed patch has been amended by the worker
asked to apply it. `T468`'s **diagnosis** is fully upheld; only its patch text is amended, and the
amendment is driven.

### 2b · `.softhouse/patterns.md` — a FORWARD correction, no new cardinal

Appended at the foot: `### T470 ERRATUM TO P-103 — corrected FORWARD, never edited in place`, following
the `T334 CITATION ERRATUM` precedent already in the file. It carries the five sanctioning sites as a
table, the corrected rule, and what `THE FORBIDDEN FOURTH` still means.

**`P-103` is NOT edited. Nothing above it is touched.**

**IT CLAIMS NO `P-n`, deliberately.** The `P`-number checker is a HARD guard and a citation to a number
that does not exist is fatal to the bar; four workers are live in this wave; and a correction that needs
its own cardinal is a second thing to keep in sync. Measured on my committed tree:

* the erratum heading matches **neither** `DEFN_HEAD` nor `DEFN_BOLD`, so it adds no register entry;
* **`P-103` is still defined EXACTLY ONCE**, at `:3835` — measured with the HARD guard's own
  `DEFN_HEAD`/`DEFN_BOLD` regexes over `strip()`ed lines, because `build_register:246` strips;
* `ids=102 gaps=none in-file-collisions=2` — **identical to `T458`'s tip**; `misdirecting` **81** and
  `undefined` **45**, also identical, so the erratum introduced **no** new misdirecting citation into
  the fatal DIRECTIVE zone;
* **`P-99` untouched** — still the permanently reserved negative control.

### 2c · `.softhouse/conformance.sh` — ONE hunk, declared, and `T480` is concurrently editing this file

`T458`'s `:2906` carried the same absolute *"do not grow the pin"*. Repairing the guard and the register
while leaving that standing would have moved the self-contradiction rather than closed it, so I fixed it
— **minimally**.

> **EXACT RE-SPECIFICATION, so this can be re-applied or conflict-resolved by hand.** In
> `guard_dead_path_frontier()`, in the `elif ! LC_ALL=C diff "$d/rec" "$d/added"` arm, in the `T458`
> remedy block that begins `warn "conformance: THE REMEDY, in one line:`, replace these **three**
> `warn` lines:
>
> ```
> EXIT. Repair the instrument; do not grow the pin, and do not split the
> literal to hide it. The guard's own transcript above states all three
> steps and the forbidden fourth. Full rule and the six measured row
> ```
>
> with these **four**:
>
> ```
> EXIT. Repair the instrument; grow the pin ONLY for a deliberate ordered-
> fallback candidate, WITH ITS REASON. Never split the literal to hide it.
> The guard's transcript has all three steps, the one sanctioned non-repair
> route and the forbidden fourth. Full rule and the six measured row
> ```
>
> `git diff --numstat` = **`4 3`**, net **+1**. No control flow, no variable, no function, no cardinal,
> no `bad=` assignment, no exit code touched. It is `warn`-text only. **`T480` is concurrently editing
> `.softhouse/conformance.sh`**; if git conflicts here, this block resolves it, and if `T480` lands
> anywhere else in those ~6,300 lines it will not conflict at all.

---

## 3 · THE DRIVES — RED, GREEN, AND A PRE-REPAIR CONTROL

`.softhouse/capture/t470-refusal-forecloses/bin/10-drive-pin-route.sh`. All scratch in
`/tmp/t470-scratch`, **outside the repository**. `bash`, never `sh`/`zsh`. Console at
`out/00-DRIVE-console.txt`; transcripts at `out/10`, `out/20`, `out/30`, `out/40`.

**`T470-PINROUTE-DRIVE: PASS`** at tip `fa0337e7`.

### Why the negatives are falsifiable: a PRE-REPAIR CONTROL ARM

The drive clones the repo **twice** with the **same planted dead literal** — once at `HEAD`, once at
`BASE` (`cb148f59`, pre-repair). Without that arm every "the foreclosure is ABSENT" below would be
unfalsifiable — the `T446` defect `P-103` item 3 exists to prevent.

```
== PRE-REPAIR CONTROL: the BASE guard, same plant ==
   exit           = 1        probe lines = 1     (PRESENCE read before VALUE)
   foreclosure A  = 1        <- "three, and never a fourth"          THE DEFECT, before repair
   foreclosure B  = 1        <- "in exchange for not pinning the row"
   pin-route head = 0        pin-route body = 0                      not written yet
   'record why in the pin' = 1   <- IT WAS ALWAYS THERE. That is the finding, MEASURED.
```

That last line is `T468`'s premise, measured on the pre-repair bytes rather than argued.

### RED — the repaired guard, the same plant

```
== RED ARM ==
   exit = 1   probe lines = 1
   probe line = REFUSED rows=109 pinned=108 added=1 removed=0
   'record why in the pin'        = 2      pin-route head = 1     pin-route body = 1
   header sentence quoted back    = 1      THE FORBIDDEN FOURTH preserved = 1
   foreclosure A                  = 0      foreclosure B  = 0
   planted row named              = 1
```

`rows=109 pinned=108 added=1 removed=0` is **digit for digit the refusal `T440`, `T447`, `T448` and
`T452` each took**.

**What it now prints, verbatim from `out/20-RED-repaired-refusal.txt` — pin-with-reason as a legitimate
route:**

```
conformance: !!   the INSTRUMENT, and not one of them grew the pin. THAT IS WHAT SIX
conformance: !!   WORKERS DID; it is not the only disposition this guard sanctions.
conformance: !!   To REPAIR, do ONE of these three. If you are NOT repairing, there
conformance: !!   is exactly ONE other sanctioned route, and it is named after them:
...
conformance: !!   2. MAKE THE LOCATION A REQUIRED PARAMETER -- no default, and a
conformance: !!      HARD EXIT when it does not resolve. Never a skipped case,
conformance: !!      never a warning, never a pass. This is the arm this guard asks
conformance: !!      for on EITHER route -- whether you repair the row away or pin
conformance: !!      it. The sentence above requires it for the PIN route too.
...
conformance: !! THE ROUTE THAT IS NOT A REPAIR, AND IS STILL SANCTIONED:
conformance: !!   PIN THE ROW WITH ITS REASON. Permitted ONLY where the reference is
conformance: !!   a deliberate ORDERED-FALLBACK candidate, or is dead BY DESIGN, and
conformance: !!   ONLY together with remedy 2's arm: the instrument must REFUSE when
conformance: !!   NO candidate resolves. THIS REFUSAL ALREADY OFFERED IT ABOVE --
conformance: !!   'record why in the pin'. This guard's own header SANCTIONS it: grep
conformance: !!   this file for WHAT A ROW DOES **NOT** MEAN -- 'a dead literal is a
conformance: !!   SMELL that must be inspected once, by a human, and then either
conformance: !!   repaired or pinned with its reason. This guard counts; it does not
conformance: !!   judge.' And THE PIN ITSELF TAKES THAT ROUTE, repeatedly -- open it
conformance: !!   and read the reasons: the two FU-T299-2 ordered-fallback rows; the
conformance: !!   four T305 red-drive rows that MUST NOT exist in a clean tree; and
conformance: !!   T306's injected-vector row, which T326 ADDED AS A NEW ROW and pinned
conformance: !!   with 'REPAIR WAS CONSIDERED AND IS NOT AVAILABLE ... Pinning it is
conformance: !!   the disposition T316's own header prescribes.'
conformance: !!   It is the EXCEPTION, not the default -- six of six workers in fire
conformance: !!   20260829-080002 repaired, and not one of them needed it.
conformance: !! ----------------------------------------------------------------
conformance: !! THE FORBIDDEN FOURTH: do NOT split or concatenate the literal to
conformance: !! slip past the selector. ...
conformance: !! (It is 'the FOURTH' because it is the fourth idea that occurs to a
conformance: !! refused worker, not a fourth entry in a list. PINNING WITH A REASON
conformance: !! IS NOT IT.)
```

### GREEN — the clean committed tree

```
== GREEN ARM ==   exit = 0   probe lines = 1   probe = GREEN rows=108 pinned=108 added=0 removed=0
   pin-route head = 0    pin-route body = 0    pin OFFER = 0
```

`rows=108 pinned=108` also proves **my own instruments added zero frontier rows**.

### REGISTER arm — and the HARD guard on these bytes

```
'ERRATUM TO' = 1   'corrected FORWARD, never edited in place' = 3 (T334's + mine)
pin route survives in register = 1   THE FORBIDDEN FOURTH preserved = 5
3835: **P-103 — A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE...
P-103 definition lines = 1     <- forward, not in place
checker exit = 0   VERDICT PASS = 1   '0 fatal' = 1
PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=102 gaps=none in-file-collisions=2
```

### REGRESSION — `T458`'s own drive, re-run on my repaired bytes

`out/t458-regression/50-T458-DRIVE-rerun-on-T470-bytes.txt`:

```
CALIBRATION  1 hit each: the anchor, the remedy head, THE FORBIDDEN FOURTH
GREEN  exit 0  probe 1  GREEN rows=108 pinned=108   anchor 0  remedy 0
RED    exit 1  probe 1  REFUSED rows=109 pinned=108 added=1 removed=0
       anchor 1  remedy 1  forbidden-4th 1  planted row named 1
T458-REMEDY-DRIVE: PASS
```

**This is the assertion that would have failed under `T468`'s literal §6 text**, and it is why the name
was preserved.

### THE DRIVE CAUGHT TWO DEFECTS IN MY OWN INSTRUMENT — recorded, not quietly fixed

Commit `9892d942`. Both are the classes this task is about:

1. **`CALIBRATION 2` scanned the whole guard source** for the foreclosing clause and found **1** hit —
   at `:233`, inside **my own `T470` comment quoting the removed clause**. A whole-file scan cannot tell
   an `echo` from a comment *about* an `echo`; this is the same distinction `T468` had to make for
   `T446`'s surviving `|| echo` occurrences. **Scoped to printable (`echo`) lines**, with the
   printable-line count (**85**) asserted non-zero first so the scan cannot go vacuous. The **output**
   assertion in the RED arm is the one that actually binds, and it was always 0.
2. **The `P-103` definition-line check** used a byte-oriented `grep -E` bracket class and reported
   **ZERO** definitions for a `P-103` that is plainly at `:3835` — the separator is an **EM DASH**.
   Replaced with the HARD guard's own `DEFN_HEAD`/`DEFN_BOLD`, verbatim, in `python3`, over `strip()`ed
   lines.

### AND IT CAUGHT A STALE CITATION IN MY OWN REPAIR

Commit `fa0337e7`. My first draft cited `.softhouse/conformance.sh:2694-2698` as a **live** exercise of
the pin route. **It is not live any more**: `T326` folded `T305`'s four rows into the pin
(`:222-225`, reason `:81-87`) and emptied `DEADPATH_T323_RECONCILE_LIST`, which now reads `''`. Shipping
that would have been the `T358` species **again, inside the repair for the `T358` species**. Corrected
to the pin — where the disposition lives now, and where `A5` makes it decisive.

### `P-103` COMPLIANCE OF MY OWN INSTRUMENT — the rule I am repairing

Run with the census's **own** `LITERAL_RE` (`census_dead_paths.py:68`) over
`bin/10-drive-pin-route.sh`: **0 quoted `.softhouse/` literals.** Every path is built from `S=".softhouse"`
(no trailing slash, so not a row). `T470_SRC` / `T470_OUT` / `T470_TMP` / `T470_BASE` are **required
parameters with no defaults**; non-resolution is `exit 2`; `T470_TMP` inside the repo is refused. Every
read is over a **file**, never a pipeline (`P-57`/`P-81`). Every negative is calibrated before it is
printed.

---

## 4 · `C-T468-2` (LOW) — THE SELF-REPORT, CORRECTED

**`T458`'s handoff reports its `.softhouse/conformance.sh` hunk as `+9` lines, twice. It is `+13`.**
Re-derived independently, not read off `T468`:

```
git diff --numstat 3f4e236a 0db7538b -- .softhouse/conformance.sh   ->  13   0
  added lines matching `warn `      ->  7
  added lines matching `^+\s*#`     ->  6                            7 + 6 = 13
```

| Site | States | Correct? |
|---|---|---|
| `.softhouse/handoff/T458-handoff.md:114` | *"The `conformance.sh` change is **9 added** lines…"* | **NO — it is 13** |
| `.softhouse/handoff/T458-handoff.md:348` (table) | *"**+9** lines inside one existing `warn` branch"* | **NO — it is 13** |
| `.softhouse/handoff/T458-handoff.md:362` (§6 re-spec) | *"insert those **seven** `warn` lines"* | **YES — 7 is right** |

**So the specification was never defective; only the two summary figures were.** For completeness the
guard hunk is **`+35`** = 26 `echo` + 9 comment, which `T458` and `T468` both state correctly.

**`T458`'s committed bytes are left as written, on purpose.** A handoff is a *dated record of what its
author measured*; correcting it forward preserves the audit trail that editing it in place would erase,
and it is not in the checker's fatal DIRECTIVE zone. **Declared as OPEN below** so nobody mistakes this
for an oversight.

---

## 5 · THE BAR AT MY BRANCH TIP

**`bash .softhouse/conformance.sh`** (`bash`, never `sh`/`zsh`), run **TWICE** and **both runs recorded,
neither discarded**:

| Run | Tree | `grep -c 'probe = '` | Result |
|---|---|---|---|
| 1 | `382de20d` (before the stale-citation correction) | **1** | **EXIT 0**, PASS 46 / 7884 — `out/90-BAR-at-382de20d.txt` |
| 2 | **`f73e82c0`, the tip, committed and clean** | **1** | **EXIT 0**, PASS 46 / 7884 — `out/99-FINAL-BAR-at-f73e82c0.txt` |

Run 2 is the binding one; run 1 is kept because a run that happened is a measurement, and this program
records rather than discards. The transcript of run 2 was committed **after** it finished, so the tree it
graded was clean — which the bar itself confirms below.

**PROBE LINE PRESENCE TESTED BEFORE ITS VALUE (`P-84`):**

```
grep -c 'probe = '   ->   1          <- PRESENCE first
then, and only then, the value:
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```

The oracle was **UP**. This is not a PASS reported over a down oracle.

```
BAR EXIT = 0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   ... frontier 11, pinned at 11          (fail-open pin, unmoved)
conformance:   ... literal /tmp path: 18, pinned at 18 (host-state pin, unmoved)
PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=102 gaps=none in-file-collisions=2
PNUMBER-CITATIONS: VERDICT PASS -- 0 fatal
conformance:   LOCAL-STATE CENSUS ... uncommitted edits 0, deleted 0.
```

**NO PIN WAS MOVED.** `dead-path-frontier.pin` is **byte-identical** to `cb148f59`; the fail-open pin is
`11 == 11`; the host-state pin is `18 == 18`. **`.softhouse/LOCK` was not read, written or deleted.**
All scratch lived in `/tmp/t470-scratch`.

---

## 6 · WHAT REMAINS **OPEN — DECLARED, NOT ARGUED SHUT**

1. **`T458-handoff.md:114` and `:348` still read `+9`.** I corrected the figure *here*, in §4, and
   deliberately did not edit another worker's committed handoff — but a reader who greps only
   `T458-handoff.md` will still meet the wrong number. Whoever holds that file next may append a
   one-line erratum pointing at this section. **My scope grant did not name it.**
2. **`conformance.sh:2894-2895` still reads *"REPAIR it rather than pinning it"* with no exception
   clause.** That text is **pre-existing** (not `T458`'s) and it mirrors the guard's own `:218-219`
   presumption, which is correct as a presumption — but unlike the guard, the wrapper never carried the
   exception. I did **not** widen my `conformance.sh` hunk to reach it, because `T480` is concurrently
   editing that file and the value did not justify the contention. **It is the same shape, one degree
   milder.**
3. **The exception's gate is prose, not a predicate.** *"deliberate ordered-fallback candidate or dead
   by design"* is a judgement a human makes; nothing in the guard enforces it. A worker who pins a row
   and writes a bad reason is caught by review, not by the bar. I considered proposing a machine-checked
   gate and **reject it**, for the reason `T458` gave and `T468` endorsed with a drive: the guard cannot
   see intent, and a detector that guessed would fail silently. **Declared, not closed.**
4. **`T468`'s §6 open item stands, unchanged by me:** an explicit author *declaration* on the line
   (`# deadpath: fixture`) is not an *inference*, so `T458`'s impossibility argument does not reach it.
   `T468`'s own answer — that it would be a **second amnesty channel** competing with the pin, scattered
   instead of reviewable in one file — is a *policy* argument and a good one. **This erratum makes it
   sharper, not weaker**: the pin is now explicitly the one sanctioned amnesty channel, so a second one
   would now be redundant as well as scattered. Still not a condition.
5. **`P-103`'s cardinal remains claimed against live siblings.** `T458` declared this and `T468` checked
   it at four shas. My erratum claims **no** new cardinal, so it adds nothing to that hazard, but the
   merge-time obligation is unchanged and I restate it: **re-run `check-pnumber-citations.py` on the
   MERGE RESULT, not on either branch.**
6. **I did not reopen "can the guard distinguish a fixture literal from a genuine dead path?"** The
   dispatch forbade it and I agree with the answer. Untouched.

---

## 7 · FILES

**My own diff sizes are DERIVED, not typed** — `git diff --numstat cb148f59 HEAD`, because a
self-reported hunk size is a claim like any other and that is exactly what `C-T468-2` is about:

| File | `+` / `−` | Change |
|---|---|---|
| `.softhouse/guards/check-dead-path-frontier.sh` | **50 / 3** | refusal repaired; `THE FORBIDDEN FOURTH` byte-identical; `T470` header block. `echo`-only in the printed block; no control flow, no variable, no exit code, no cardinal touched |
| `.softhouse/patterns.md` | **92 / 0** | **append only** — `T470 ERRATUM TO P-103`; nothing above it touched; no new `P-n` |
| `.softhouse/conformance.sh` | **4 / 3** | **one** hunk, 4 `warn` lines replacing 3, re-specified verbatim in §2c |
| `.softhouse/capture/t470-refusal-forecloses/bin/10-drive-pin-route.sh` | **354 / 0** | the drive; 0 quoted `.softhouse/` literals |
| `.softhouse/capture/t470-refusal-forecloses/out/` | — | control / RED / GREEN / checker / `T458` regression / bars |
| `.softhouse/handoff/T470-handoff.md` | — | this file |

**Not touched:** `tasks.json`, `RESUME.md`, `program.json`, `LOCK`, any pin, `P-99`, `P-103` itself,
`T458-handoff.md`.
