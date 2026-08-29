# T483 — INDEPENDENT ADVERSARIAL REVIEW OF T470

Branch `softhouse/T483-review-t470`. Subject: `softhouse/T470-refusal-forecloses`, tip **`28fdfee3`**,
6 commits, 19 files, **+3063 / −6**.

Everything below was read from the branches (`git show <branch>:<path>`, `git diff main...<branch>`)
and re-derived on this reviewer's own runs. Where a claim could not be re-derived, it says so.
Nothing was inherited from `T470` or `T468`.

---

## VERDICT: **APPROVED WITH CONDITIONS**

**Safe to merge: YES.** **P-103 is coherent on the merge result: YES, formally — measured on the
actual merge, not asserted.** One condition is MINOR-with-a-drive, one is MINOR and is a false claim
in `T470`'s own handoff, two are LOW/NIT. None blocks the merge.

| # | Severity | Condition |
|---|----------|-----------|
| **C-T483-1** | **MINOR (driven)** | The repaired refusal still sends a refused worker to `P-103` **by its sentence**; that sentence lands at `patterns.md:3835`, whose closing paragraph **still reads "do not add the row to the pin"**, and the erratum is **131 lines below, unannounced**. Measured, not argued. Four `echo` lines close it; **driven RED/GREEN with both predecessor drives re-run PASS**. Text-only, no behaviour change. |
| **C-T483-2** | **MINOR** | `T470`'s handoff §2a asserts `T458`'s drive *"would not have [passed] under the literal §6 text."* **Measured: it PASSES (exit 0).** `T468`'s patch does not rename `THE FORBIDDEN FOURTH`; only `T470`'s paraphrase of it does. **The decision to amend `T468`'s patch is nevertheless UPHELD on two other grounds I measured** (below). Confined to the handoff — **no shipped byte repeats it** — but `main`'s own commit message `e13e94a5` does. |
| **C-T483-3** | **LOW** | The delivered tip `28fdfee3` was **never graded by `T470`** — its final bar is at `f73e82c0`, and the tip adds **911 lines** on top. The handoff at `:392` calls `f73e82c0` *"the tip"*; it is not. **I graded `28fdfee3` myself: EXIT 0, PASS 46 / 7884.** Risk discharged; the habit is the condition, and this is its **second consecutive** occurrence (`C-T468-3` was the first). |
| **C-T483-4** | **NIT** | `check-dead-path-frontier.sh:244` is **120 characters**, introduced by `fa0337e7`, in a file whose every other line is under 100. Comment only. |

**Endorsed without condition:** all **five** sanctioning sites (site 5 is decisive and is in fact
*stronger* than `T470` states); all **four** foreclosure sites including `conformance.sh:2906`; the
forward erratum's form and its arithmetic; the pre-repair control arm; the three self-caught defects;
`C-T468-2`'s arithmetic and its disposal; the `§2c` re-specification; the immobility of the pin,
`LOCK`, `tasks.json`, `RESUME.md` and `program.json`.

---

## 0 · WHAT I RAN, ON WHOSE TREE

All scratch **outside the repository**, under `/tmp/t483-scratch`. `bash`, never `sh`/`zsh`.

| Run | Tree | Probe PRESENCE tested first | Result |
|-----|------|------------------------------|--------|
| Full bar | **`T470`'s tip `28fdfee3`** (scratch worktree outside the repo) | `grep -c 'probe = '` = **1** | **EXIT 0**, PASS 46 / 7884 |
| Full bar | **my own committed tree** | see §7 | see §7 |
| `10-drive-t468-literal.sh` (mine, 3 arms) | tip + a tree carrying `T468`'s §6 patch **verbatim** + a rename control | probe lines 1/1/0 | **PASS** |
| `20-drive-erratum-pointer.sh` (mine, 3 arms) | tip, tip+proposal, both predecessors' drives | 1 on every measuring arm | **PASS** |
| `10-drive-pin-route.sh` (`T470`'s own) | tip, re-run by me end to end | 1 on every arm | **PASS**, digit for digit |
| `10-drive-remedy-text.sh` (`T458`'s own) | tip; and `T468`'s literal patch; and a rename control | 1 / 1 / **0** | **PASS / PASS / exit 2** |
| Test-merge + `check-pnumber-citations.py` | `main` @ `55af2cc7` **+ `T470`** | — | clean merge, **VERDICT PASS — 0 fatal** |
| Test-merge | `main` + `T470` + **`T480`** | — | **clean, no conflict** |

**Oracle probe, presence read before value:** `grep -c 'probe = '` → **1**, then
`reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`.
Independently: `docker ps` shows `fineract-fineract-1 Up 2 hours (healthy)` and the health endpoint
returns `{"status":"UP",…}`. **This is not a PASS reported over a down oracle.**

### The transcript is bound to the tree — measured

`T470`'s committed `out/99-FINAL-BAR-at-f73e82c0.txt` against my own bar at `28fdfee3`:

```
IDENTICAL: T316-DEADPATH-CENSUS: corpus=1755 deadFiles=75 deadOccurrences=108
           resolving=1577 indeterminate=126 prose=427
IDENTICAL: PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=102 gaps=none
           in-file-collisions=2 cross-register-collisions=[1, 2, 3, 4, 5, 6]
IDENTICAL: VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells compared.
IDENTICAL: frontier 11, pinned at 11;  dead-path frontier: GREEN, list empty
DIFFERS  : sites=14377 (T470) vs 14381 (mine)  definition=103 in BOTH,
           misdirecting=81 and undefined=45 in BOTH
```

The 4-site delta is exactly `P-80` — `T470`'s own 898-line bar transcript entered the citation corpus
when it was committed as `28fdfee3`. It is **why** `C-T483-3` exists and it is also its own discharge:
every cardinal that matters is unchanged, and I graded the tip myself.
[`out/40-BAR-cardinal-comparison.txt`]

---

## 1 · CLAIM 1 — **FIVE SANCTIONING SITES. HOLDS. SITE 5 HOLDS, AND IS STRONGER THAN `T470` SAYS.**

Every site opened at its cited line on `cb148f59` (`T470`'s fork point, = `T458`+`T468` as delivered),
not read out of either handoff.

| Site | Cited | Opened | Verdict |
|---|---|---|---|
| 1 | `check-dead-path-frontier.sh:59-61` | `"…either repaired or pinned with its reason. This guard counts; it does not judge."` at exactly `:59-61` | **HOLDS, verbatim** |
| 2 | `check-dead-path-frontier.sh:218-221` | `"…and record why in the pin."` at `:221`, and `if [ "$added_n" -gt 0 ]; then` opens at **`:217`** | **HOLDS** — it is inside the NEW-row branch, one line in |
| 3 | pin `:215-216`, reason `:170-171` | the two `FU-T299-2` rows are the pin's lines 215 and 216; the reason is the `A ROW IS NOT AN ACCUSATION` block | **HOLDS** |
| 4 | pin `:222-225`, reason `:81-87` | `T305`'s four `red-drive-conformance-guard.sh` rows; `"A red drive plants files that MUST NOT exist in a clean tree"` at `:86-87` | **HOLDS** |
| 5 | pin `:121-125` | see below | **HOLDS — and `T470` under-states it** |

**SITE 5 IS DECISIVE AND `T470` QUOTED ONLY HALF OF ITS FORCE.** `T470` says `T326` took a NEW row and
pinned it. The pin says more than that, at `:106-111`:

```
106 # +1  `.softhouse/reviews/T306/probe/inject-acceptance.py |
107 #      .softhouse/vectors/ledger/ZZZ-T306-INJECTED-preclosure-acceptance.json`
108 #     ARRIVED ON `main` WHILE T326 WAS RUNNING, in T306's merge, and THE GUARD CAUGHT IT ON THE
109 #     FIRST BAR AFTER THE MERGE -- `REFUSED rows=107 pinned=106 added=1 removed=0`. That is the
110 #     wired guard doing the job it was wired for, on a site nobody had told it about. It was
111 #     INSPECTED ONCE, BY A HUMAN-EQUIVALENT READ OF THE SOURCE, before being pinned:
```

then, at `:121-125`, verbatim as `T470` quotes it:

```
121 #       * SAME CLASS, byte for byte, as the four T305 rows above. Pinning it is the disposition
122 #         T316's own header prescribes: "a SMELL that must be inspected once, by a human, and
123 #         then either repaired or pinned WITH ITS REASON."
124 #       * REPAIR WAS CONSIDERED AND IS NOT AVAILABLE. "Make the path resolve" means committing
125 #         `ZZZ-T306-INJECTED-preclosure-acceptance.json` into `.softhouse/vectors/ledger/`,
```

and the row is live in the pin's row list at **`:272`**.

So this is not merely "a new row was pinned". **`T326` took the `added_n > 0` refusal — the identical
refusal, `added=1` — considered repair, rejected it in writing, and pinned.** `P-103` as `T458` wrote
it forbids exactly that. **The MAJOR does not collapse; it is over-determined.**

**FORECLOSURE SIDE — all four sites confirmed, including the third `T468` missed:**

* `check-dead-path-frontier.sh:235-236` — `"…Do ONE of these"` / `"three, and never a fourth:"`. **HOLDS.**
* `check-dead-path-frontier.sh:244-245` — `"…This is the arm this guard asks"` / `"for in exchange for not pinning the row."` **HOLDS, and `T470`'s "measurably wrong" is right**: site 2 requires the refuse-when-nothing-resolves arm *for the pin route*, so it is not bought in exchange for anything.
* `patterns.md:3908-3911` — `"…and do **not** / add the row to the pin."` **HOLDS**, and `:3895` and `:3903` carry the same shape.
* `conformance.sh:2906` — `"EXIT. Repair the instrument; do not grow the pin, and do not split the"`. **HOLDS.** I checked `T468`'s specified repair: it names `guards/check-dead-path-frontier.sh` and `patterns.md` **only**, so `T470` is right that this site is outside `T468`'s condition.

**One supporting observation neither predecessor made.** The sentence `P-103` leans on —
*"The pin is a frontier, not an amnesty"* — is the pin's **own** header sentence, at
`dead-path-frontier.pin:175`, sitting nine lines below `:166-173`, the block that *grants* the
`FU-T299-2` pins. The sentence has never meant "never pin"; it means "never pin without a reason."
`P-103` read it as the stronger thing.

---

## 2 · CLAIM 2 — **WHO WAS RIGHT ABOUT `T468`'s §6 PATCH: BOTH, PARTLY. ADJUDICATED BY MEASUREMENT.**

`.softhouse/reviews/t483-review-t470/bin/10-drive-t468-literal.sh`. Three arms, all outside the repo.
**`T483-T468LITERAL-DRIVE: PASS armA=0 armB=0 armC=2 T470-GROUND1=REFUTED POSITIONAL=FALSE-at-7`**
[`out/00-DRIVE-console.txt`]

```
ARM A -- T470's TIP, T458's own drive re-run on T470's bytes
   guard SOURCE 'THE FORBIDDEN FOURTH'  = 1   'Never a fifth:' = 0
   T458 drive exit = 0    probe lines = 1
   probe line = PASS green=exit0/anchor0 red=exit1/anchor1/remedy1

ARM B -- BASE + T468's §6 patch AS LITERALLY WRITTEN
   guard SOURCE 'THE FORBIDDEN FOURTH'  = 1   'Never a fifth:' = 1
   T458 drive exit = 0    probe lines = 1
   probe line = PASS green=exit0/anchor0 red=exit1/anchor1/remedy1

ARM C -- CONTROL: the same patch PLUS renaming THE FORBIDDEN FOURTH -> FIFTH
   guard SOURCE 'THE FORBIDDEN FOURTH'  = 0
   T458 drive exit = 2    probe lines = 0        <- its CALIBRATION refuses
```

### `T470`'s GROUND 1 IS **REFUTED**, and the control proves the refutation is a measurement

`T458`'s drive holds `FORBIDDEN="THE FORBIDDEN FOURTH"` at `10-drive-remedy-text.sh:60` and asserts it
in CALIBRATION (`:78-84`, `die2` on absence) and in the RED arm (`:164`, `:173`). **`T468`'s patch
replaces one `echo` line — `three, and never a fourth:` — and does not touch the separate `echo` line
that spells `THE FORBIDDEN FOURTH:`.** So the string survives and the drive passes. Arm C builds
`T470`'s stated hazard for real: rename the string and `T458`'s drive exits **2**. The drive **is**
sensitive; arm B's PASS is therefore a measurement and not a blindness. **`T470`'s sentence
*"which it would not have under the literal §6 text"* is false about the bytes.**

### `T470`'s DECISION TO AMEND THE PATCH IS NEVERTHELESS **UPHELD**, on two grounds I measured

1. **`"four lines above"` is false in rendered output.** Measured on arm B's own RED transcript, which
   is the rendered refusal: `record why in the pin` at line **10**, `Never a fifth:` at line **17** —
   **7 lines**, not four, on a **one-row** refusal. The `sed -n '1,40p' "$ADDED"` listing prints
   between them, so the distance **grows with the row count** (18 on a twelve-row refusal). `P-86` is
   exactly this rule. **HOLDS.**
2. **`T468`'s patch is incomplete by `T468`'s own diagnosis.** Arm B's rendered refusal still carries
   `"for in exchange for not pinning the row."` — foreclosure **B2**, which `T468` itself named in
   `C-T468-1`. Its specified repair does not reach it. `T470`'s does.

And the coherence objection is visible in arm B's own output: line 17 says **`Never a fifth:`**, line
31 says **`THE FORBIDDEN FOURTH:`**. That is a refusal that numbers a forbidden *fourth* after four
permitted dispositions — the self-contradiction this whole task exists to remove, re-introduced by the
patch meant to remove it.

### DISPOSAL

**This is the fourth reviewer-proposed patch amended by its assigned worker, and the amendment is
correct — but the ledger entry must be written accurately.** `T468`'s *diagnosis* is upheld in full and
`T470` says so. `T468`'s *patch text* is refuted on grounds 1 and 2 above. `T470`'s **stated ground 1
is itself false**, and it is the ground the driver copied into `main`'s commit message
`e13e94a5` — *"T468's literal patch REFUTED **and shown to break T458's own drive**"*. The second half
of that is wrong. **`C-T483-2`**: correct it forward. **No shipped byte carries the false claim** — I
grepped `patterns.md`, `check-dead-path-frontier.sh`, `conformance.sh` and `10-drive-pin-route.sh` for
it and found nothing; the register's erratum says only that *renaming* would have broken the assertion,
**which is true and which arm C proves**.

---

## 3 · CLAIM 3 — **THE FORWARD ERRATUM. FORMALLY COHERENT. SUBSTANTIVELY, TWO READINGS ARE LIVE.**

### Re-derived with the HARD guard's own predicate, on my own runs

Regexes copied verbatim from `check-pnumber-citations.py:100-101`, applied over `strip()`ed lines
because `build_register:246` does `s = raw.strip()`:

| Tree | defn sites | distinct ids | max | gaps | in-file collisions | **`P-103` definitions** | `P-99` |
|---|---|---|---|---|---|---|---|
| `cb148f59` (BASE) | 104 | 102 | 103 | `{99}` | `{12:2, 13:2}` | **1, at `:3835`** | absent |
| **`28fdfee3` (tip)** | **104** | **102** | **103** | **`{99}`** | **`{12:2, 13:2}`** | **1, at `:3835`** | **absent** |
| **`main`@`55af2cc7` + `T470` (the MERGE RESULT)** | **104** | **102** | **103** | **`{99}`** | **`{12:2, 13:2}`** | **1, at `:3835`** | **absent** |

**The erratum adds ZERO definition sites.** Its heading is
`### \`T470\` ERRATUM TO \`P-103\` — corrected FORWARD, never edited in place`, which matches neither
`DEFN_HEAD` (needs `P-n` immediately after the hashes) nor `DEFN_BOLD`. **It claims no cardinal, and
`P-103` is defined exactly once.** `misdirecting=81` and `undefined=45` are **identical** on the tip
and on the merge result — the erratum introduced no new misdirecting citation into the fatal DIRECTIVE
zone. `P-99` is untouched.

### I did not leave the merge check to the driver — I ran it

`main` has already moved to **`55af2cc7`** (it carries `T474`). The merge of
`softhouse/T470-refusal-forecloses` into it is **clean, zero conflicts**, and on the merge result:

```
PNUMBER-CITATIONS: register=.softhouse/patterns.md ids=102 gaps=none in-file-collisions=2
PNUMBER-CITATIONS: sites=14387 definition=103 consistent=725 bare=13369
                   misdirecting=81 undefined=45 negative-control=64
PNUMBER-CITATIONS: VERDICT PASS -- 0 fatal
CHECKER EXIT = 0
```
[`out/20-MERGE-RESULT-pnumber.txt`]

**`T470`'s asking for a merge-result re-check was right, and it is now discharged rather than
outstanding.** It remains a standing obligation only for whatever lands *after* this.

Also measured, because `T470` declared it as a hazard: **`main` + `T470` + `T480` merges cleanly too**
(`T480` rewrites 300/111 lines of the same `conformance.sh`), and on the result
`grow the pin ONLY for a deliberate ordered-` = **1** while `do not grow the pin` = **0**. The
concurrency the §2c re-specification was written for **does not materialise**.
[`out/21-MERGE-with-T480.txt`]

### THE SUBSTANCE — and this is `C-T483-1`

**Does a forward erratum actually repair a register entry?** Here: **partly.** Measured, not argued
[`out/30-POINTER-DRIVE-console.txt`]:

```
anchor lands at register line          = 3835
erratum heading at register line       = 3966   (distance 131 lines below)
'add the row to the pin' in the entry  = 1   <- the stale half IS what a reader meets
pointer to the erratum in the entry    = 0   <- and nothing tells them it exists
```

The guard's refusal anchors by sentence — `A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS
TREE` — which is right (`P-86`, `P-96`: *the checkable property is the SENTENCE, never the id*). But
that sentence lands at `:3835`, and the entry there **still ends with `"do not add the row to the
pin"`**. The erratum is 131 lines further down, and the refusal never mentions it: in arm A,
`the word ERRATUM printed at all = 0`.

**`T470` had no better option at `:3835`.** Editing the entry in place is precisely what append-only
forbids, and the `T334 CITATION ERRATUM` at `:3371` is the file's own precedent for exactly this
shape. **This is not charged to `T470` as an error.** Two things reduce it further:

* the stale reading **fails SAFE** — it over-prescribes repair, which is the presumption anyway, and
  never grants amnesty. A worker misled by it does more work, not less rigorous work;
* the refusal **on screen** now teaches the pin route at length, and the refusal is the read that
  reaches a worker at the moment of decision.

**But it was closable in the block `T470` was already writing.** See `C-T483-1` below.

---

## 4 · CLAIM 4 — **THE DRIVE AND ITS CONTROL. RE-RUN END TO END. REPRODUCES DIGIT FOR DIGIT.**

I re-ran `T470`'s `10-drive-pin-route.sh` myself against a fresh clone at `28fdfee3`, `T470_BASE=cb148f59`,
scratch outside the repo. [`out/10-T470-DRIVE-rerun.txt`]

```
PRE-REPAIR CONTROL  exit=1  probe=1   foreclosure A=1  B=1   pin-route head=0 body=0
                    'record why in the pin' = 1        <- T468's premise, MEASURED on BASE bytes
RED                 exit=1  probe=1   REFUSED rows=109 pinned=108 added=1 removed=0
                    offer=2  route head=1  route body=1  header sentence=1
                    THE FORBIDDEN FOURTH=1   foreclosure A=0  B=0   planted row named=1
GREEN               exit=0  probe=1   GREEN rows=108 pinned=108 added=0 removed=0
                    route head=0  route body=0  pin OFFER=0
REGISTER            P-103 definition lines = 1   checker exit 0   VERDICT PASS   0 fatal
T470-PINROUTE-DRIVE: PASS
```

**Is the control a real control or a second GREEN?** A real control. It is a *different tree*
(`cb148f59`) carrying the *same plant*, and it produces a *refusal* (exit 1) in which the two
foreclosing clauses are **present** (1, 1) and the pin-route block is **absent** (0, 0). A second
GREEN could not print `foreclosure A = 1`. And its most useful line is `'record why in the pin' = 1`
on the **pre-repair** bytes: `T468`'s whole premise, established by measurement rather than by reading.

**Did the GREEN genuinely have the opportunity to go RED?** Yes, three ways, all in the same run:
CALIBRATION 1 proves all five strings are **present in the guard's source** (`die2` otherwise); the RED
arm proves they **print** when the frontier moves; and the GREEN arm runs **the same guard binary** on
a tree where the frontier equals the pin. The absence assertions are falsifiable.

**Two additional adversarial checks I made that `T470` did not claim:**

* `CALIBRATION 2` reports `echo-line hits = 0 (whole file 1)` for `three, and never a fourth`. I opened
  the whole-file hit: it is `check-dead-path-frontier.sh:244`, inside `T470`'s own comment block, and
  it is a comment **about** the removed clause. The scoping is correct and the `printable (echo)
  lines = 85` non-vacuity assertion in front of it is the right shape.
* The drive's own required parameters use `${VAR:?…}` messages with **no apostrophes**. That matters on
  this host: `bash 3.2` mis-pairs a lone `'` inside such a word **across lines**, which silently ate an
  assignment in *my* first draft. `T470`'s four messages are clean. (Recorded in my own instrument at
  `10-drive-t468-literal.sh:54-59` rather than quietly fixed.)

---

## 5 · CLAIM 5 — **THREE SELF-CAUGHT DEFECTS. ALL THREE REAL, ALL THREE RECORDED, ALL THREE REPAIRED.**

| # | Commit | Checked | Verdict |
|---|---|---|---|
| 1 | `9892d942` | whole-file scan flagged `T470`'s own comment quoting the removed clause; repaired by scoping to `^[[:space:]]*echo ` lines **with `printable lines = 85` asserted non-zero first** so the scan cannot go vacuous, and the binding assertion is the RED **output**, which was always 0 | **REAL, and the repair is the right one** — a whole-file scan genuinely cannot tell an `echo` from a comment about one |
| 2 | `9892d942` | the `grep -E` bracket class `[.-]` reported **zero** definitions for a `P-103` that is at `:3835`; the separator is an **EM DASH** (`—`, U+2014). Replaced with `DEFN_HEAD`/`DEFN_BOLD` verbatim in `python3` over `strip()`ed lines | **REAL.** I confirmed the em dash and I used the same corrected predicate for §3; it is the checker's own |
| 3 | `fa0337e7` | the first draft cited `conformance.sh:2694-2698` as a **live** exercise of the pin route | **REAL — and the repair is exact.** `:2694-2698` still exists and `"They are pinned here, with the reason"` is verbatim at `:2697`; but `DEADPATH_T323_RECONCILE_LIST=''` at `:2792`, so it is **history, not a live route**. The shipped erratum now cites it **parenthetically with the disclosure** — *"`T326` folded them into the pin and emptied that list, so the pin is now the live site"* — and moves the load onto pin `:121-125` |

**Recording beat hiding, on all three.** Each has its own commit with the defect in the message. Defect
3 is the one that matters: a repair for the `T358` species that shipped a stale citation would have
been the `T358` species inside its own repair, and `T470` caught it before the bar.

---

## 6 · CLAIM 6 — **`C-T468-2` AND WHAT IS OPEN**

### `C-T468-2` — re-derived independently. `T470` is right.

```
git diff --numstat 3f4e236a 0db7538b -- .softhouse/conformance.sh   ->  13   0
  added lines matching  warn      ->  7
  added lines matching  ^\+\s*#   ->  6            7 + 6 = 13
git diff --numstat 3f4e236a 0db7538b -- .../check-dead-path-frontier.sh -> 35 0
```

| Site | Reads | Correct? |
|---|---|---|
| `T458-handoff.md:114` | *"The `conformance.sh` change is **9 added**…"* | **NO — 13** |
| `T458-handoff.md:348` | *"**+9** lines inside one existing `warn` branch"* | **NO — 13** |
| `T458-handoff.md:362` | *"insert those **seven** `warn` lines"* | **YES** |

All three opened at their line numbers and quoted above from the bytes.

**Leaving `T458`'s committed handoff intact is the RIGHT disposal, and I endorse it without
qualification.** A handoff is a dated record of what its author measured. Editing it in place would
erase the audit trail, and this file's own doctrine — append-only, corrected forward, `P-96`, the
`T334` erratum — says so. It is not in the checker's fatal DIRECTIVE zone. **Correctly declared OPEN.**

### `T470`'s six open items — checked, none understated

1. **`T458-handoff.md:114`/`:348` still read `+9`.** True; verified at both lines. Correctly open.
2. **`conformance.sh:2894-2895` still reads *"REPAIR it rather than pinning it"* with no exception.**
   True, verified. It is **pre-existing**, not `T458`'s, and it mirrors the guard's own `:218-219`
   presumption — but unlike the guard, it does not go on to offer the pin. **`T470`'s stated reason for
   not widening the hunk (`T480` concurrently rewriting that file) turns out to have been unnecessary:
   I merged `T470` and `T480` and they do not conflict.** That does not make the restraint wrong —
   it could not have known — and the item is correctly open. **Not upgraded to a condition**, because
   it is one degree milder and the guard's message, which is what a worker reads, is now correct.
3. **The exception's gate is prose, not a predicate.** True, and **the refusal to machine-check it is
   correct.** The gate is *"deliberate ordered-fallback candidate or dead by design"* — an intent, and
   a detector that guessed at intent would fail silently, which is the worse direction. Endorsed.
4. **`T468`'s `# deadpath: fixture` open item.** Untouched and correctly characterised: a declaration is
   not an inference, so `T458`'s impossibility argument does not reach it; `T468`'s policy answer (a
   second, scattered amnesty channel) is a good one; and `T470` is right that the erratum makes it
   *sharper*, since the pin is now explicitly the one sanctioned amnesty channel. Not a condition.
5. **`P-103`'s cardinal on the merge result.** **Discharged by me in §3, on the real merge.**
6. **"Can the guard distinguish a fixture literal from a genuine dead path?" not reopened.** Correct.

### Is the §2c re-specification sufficient? — **YES. Verified byte-exact, both sides.**

I extracted the `warn` texts at `conformance.sh:2904-2911` from BASE and from the tip and compared them
to §2c's two quoted blocks:

```
re-spec BEFORE block matches BASE bytes: True
re-spec AFTER  block matches TIP  bytes: True
```

It names the function (`guard_dead_path_frontier()`), the arm
(`elif ! LC_ALL=C diff "$d/rec" "$d/added"`), the anchor line
(`warn "conformance: THE REMEDY, in one line:`), gives **both** sides verbatim, and states the numstat
(`4 3`). This is strictly better than `T458`'s §3b, which `T468` had to rescue with §6. One residual:
like `T458`'s, it quotes the **rendered** text without the `warn "conformance: ` wrapper, so a
hand-reapplier must carry the wrapper onto the new fourth line. Since the three lines being replaced
are already `warn` lines sitting in view, that is unambiguous. **Sufficient.** And the branch itself
carries the diff, so the re-specification is a belt on top of braces.

---

## 7 · THE BAR — AND WHAT I DID NOT MOVE

**Run 1 — `T470`'s tip `28fdfee3`**, in a scratch worktree at `/tmp/t483-scratch/t470tip`,
**outside the repository**. `bash .softhouse/conformance.sh`.

```
grep -c 'probe = '  ->  1                                   <- PRESENCE, first
then the value: reference oracle (…/actuator/health) probe = up
BAR EXIT = 0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   frontier 11, pinned at 11             (fail-open pin, unmoved)
conformance:   literal /tmp … path to a name: 18, pinned at 18   (host-state pin, unmoved)
PNUMBER-CITATIONS: VERDICT PASS -- 0 fatal
```

### §7b — Run 2, THE BAR ON MY OWN COMMITTED TREE

Run at `7f370430`, the commit carrying this review and both drives, with the tree clean.
`bash .softhouse/conformance.sh`, `bash` and never `sh`/`zsh`. [`out/90-BAR-at-my-tip.txt`]

```
grep -c 'probe = '  ->  1                                   <- PRESENCE, first
then the value: reference oracle (…/actuator/health) probe = up
BAR EXIT = 0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   LOCAL-STATE CENSUS … uncommitted edits 0, deleted 0.
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   … frontier 11, pinned at 11                       (fail-open pin, UNMOVED)
conformance:   literal /tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 18   (UNMOVED)
```

**My two committed drives added ZERO rows to any of the three pins**: the dead-path frontier is
GREEN, the fail-open pin is `11 == 11`, and the host-state pin is `18 == 18`. That is the measured
form of the `P-103` compliance claimed above — the census, not my say-so. **I moved no pin.**

This same transcript is committed one commit after the run, which is the structural fact
`C-T483-3` names; unlike `T470` I state the graded sha (`7f370430`) rather than calling it "the tip".

**Nothing of anyone else's was moved.**
`git diff --stat cb148f59 28fdfee3 -- guards/dead-path-frontier.pin LOCK tasks.json RESUME.md program.json`
is **empty**, and the pin's blob hash is `f1cc2f07…` on **both** shas — byte-identical. I did not read,
write or delete `.softhouse/LOCK`. My own scope is `.softhouse/reviews/t483-review-t470/` only; I
edited **no** file of `T470`'s.

**My own instruments obey `P-103`, which is the rule under review.** Run with the census's own
`LITERAL_RE` (`census_dead_paths.py:68`):

```
10-drive-t468-literal.sh     quoted .softhouse/ literals = 0
20-drive-erratum-pointer.sh  quoted .softhouse/ literals = 0
```

Every path is built from `S=".softhouse"` (no trailing slash, so not a row). `T483_SRC`/`T483_OUT`/
`T483_TMP`/`T483_TIP`/`T483_BASE` are required parameters with **no defaults**; non-resolution is
`exit 2`; a `T483_TMP` inside the repo is refused. Every count is read from a **file**, never a
pipeline (`P-57`/`P-81`). Every negative is calibrated before it is printed (`P-22`), and
`20-drive-erratum-pointer.sh` **`die2`s rather than reporting its own finding** if the stale clause is
not at the landing site.

---

## 8 · THE CONDITIONS

### C-T483-1 (MINOR) — the refusal cites the entry it has just superseded, and does not say so. **DRIVEN.**

**The gap, measured** (§3): a refused worker is sent to `P-103` by sentence, lands at `patterns.md:3835`,
and reads `"do not add the row to the pin"`. The erratum is **131 lines below** and the refusal never
names it (`the word ERRATUM printed at all = 0`).

**The repair — four `echo` lines, in the block `T470` already wrote, immediately after the anchor
line.** Anchored by a grep string, never by a line number (`P-86`):

```
  echo "conformance: !! THAT ENTRY IS CORRECTED FORWARD, and this file is APPEND-ONLY, so"
  echo "conformance: !! its own closing paragraph still reads 'do not add the row to the"
  echo "conformance: !! pin'. That half is SUPERSEDED. Read it together with the erratum at"
  echo "conformance: !! the foot of the same file -- grep it for: ERRATUM TO"
```

**Driven, not advised.** `bin/20-drive-erratum-pointer.sh`,
**`T483-ERRATUM-POINTER-DRIVE: PASS before=ptr0 after=ptr1 t458=0 t470=0 gap=131lines`**:

```
ARM A  BEFORE  exit 1  probe 1   anchor printed 1   pointer 0   ERRATUM 0   FORBIDDEN FOURTH 1
ARM B  AFTER   exit 1  probe 1   anchor printed 1   pointer 1   ERRATUM 1   FORBIDDEN FOURTH 1
               T470's pin-route block still printed = 1
ARM C  REGRESSION on the proposed tree:
       T458's drive  exit 0   PASS green=exit0/anchor0 red=exit1/anchor1/remedy1
       T470's drive  exit 0   PASS control=exit1/fa1/route0 red=exit1/route1/offer2/fa0
                                   green=exit0/route0 register=erratum3/defs1
```

`echo`-only. No control flow, no variable, no exit code, no cardinal, no pin, no register edit,
`THE FORBIDDEN FOURTH` byte-identical. **Both predecessor drives still PASS** — the standard `T470`
itself held `T468`'s patch to. **Does not block the merge**; route it as a follow-up.

### C-T483-2 (MINOR) — a false claim in the handoff, in the task about false claims

See §2. `T470-handoff.md` §2a: *"`T458`'s drive is re-run below and still passes on my bytes — **which
it would not have under the literal §6 text**."* **Measured false** (arm B: exit 0), with a working
control (arm C: exit 2). `main`'s commit message `e13e94a5` repeats it. **The refusal of `T468`'s patch
text stands** on two grounds I measured and confirmed. **Correct forward; do not edit `T470`'s handoff
in place** — the same doctrine `T470` correctly applied to `T458`'s.

### C-T483-3 (LOW) — the delivered tip was never graded by its author

`T470`'s final bar is `out/99-FINAL-BAR-at-f73e82c0.txt`; the delivered tip is `28fdfee3`, which adds
that 898-line transcript plus 13 handoff lines. Handoff `:392` calls `f73e82c0` *"the tip"*; it is not.
**I graded `28fdfee3`: EXIT 0, PASS 46 / 7884, oracle probe present then `up`.** Risk discharged. The
condition is the habit — this is its **second consecutive** occurrence (`C-T468-3`) — and it is
structurally hard to avoid, since committing a bar transcript necessarily creates a commit after the
graded one. **The disposal that works is the one both reviews have used: the reviewer grades the tip.**

### C-T483-4 (NIT) — `check-dead-path-frontier.sh:244` is 120 characters

Introduced by `fa0337e7` in a file otherwise under 100. Comment text only.

---

## 9 · WHAT I COULD NOT RE-DERIVE, AND WHAT I LEAVE OPEN

**Could not re-derive:**

* *"Six of six workers in fire `20260829-080002` repaired; not one grew the pin."* I confirmed the pin
  is **byte-identical** across `cb148f59`→`28fdfee3` and that the frontier is `108 == 108`, which is
  consistent with it, but I did not open `T440`/`T446`/`T447`/`T448`/`T451`/`T452`'s branches. **Taken
  from `T458`/`T468`, not verified by me.**
* *"`rows=109 pinned=108 added=1 removed=0` is digit for digit the refusal `T440`/`T447`/`T448`/`T452`
  each took."* The cardinal recurs in **12** committed capture transcripts, but none of them is a
  `T440`/`T447`/`T448`/`T452` bar. **Not verified; it is rhetorical, not load-bearing.**
* Whether any of the *other* live branches (`T475`, `T482`) conflict with `T470`. I tested `T480`
  because `T470` named it, and `T474` because it is already on `main`. **The rest is the driver's.**

**Left open:**

1. **`C-T483-1`'s four echo lines are specified and driven but NOT applied.** I am a reviewer; I edited
   no file of `T470`'s.
2. **`C-T483-2` and `C-T483-3` need a forward correction**, not an in-place edit, and not by me.
3. **`T470`'s open items 1–4 and 6 remain open**, correctly, and I have not narrowed them.
4. **`conformance.sh:2894-2895`** still carries the exception-free presumption. Deliberately not raised
   to a condition (§6 item 2), and now known to be reachable without a `T480` conflict.
5. **`P-103`'s cardinal on anything that merges AFTER this.** Discharged for `main`@`55af2cc7`+`T470`
   and for `+T480`; the standing obligation survives for later merges.

---

## 10 · THE TWO ANSWERS THE DISPATCH ASKED FOR, PLAINLY

**IS THIS SAFE TO MERGE? — YES.** The bar is EXIT 0 at the delivered tip `28fdfee3` on my own run with
the oracle measurably UP (presence before value). No pin moved, no `LOCK` touched, no forbidden file
touched. The merge into `main`@`55af2cc7` is clean, and so is the merge with `T480`, which is the only
concurrent branch touching the same file. Every change to executable text is `echo`/`warn` text: no
control flow, no exit code, no cardinal. The four conditions are all text, all forward-correctable, and
none of them makes the tree worse than it is today.

**IS `P-103` COHERENT ON THE MERGE RESULT? — FORMALLY YES; SUBSTANTIVELY, WITH ONE RESERVATION.**
Measured on the actual merge: **defined exactly once, at `:3835`**; `ids=102`, `gaps=none`,
`in-file-collisions=2`, `misdirecting=81`, `undefined=45`, `definition=103`, checker **VERDICT PASS —
0 fatal**, exit 0. No new cardinal, `P-99` untouched, no new DIRECTIVE-zone misdirection. The register
is not broken and the HARD guard is not at risk.

The reservation is `C-T483-1`, and it is honest to state it as a reservation rather than a defect:
**two readings of `P-103` are live in the merged file** — the entry at `:3835` and the erratum 131
lines below — and the refusal points at the first without naming the second. Under the append-only
rule `T470` could not have closed that at `:3835`, and the stale reading **fails safe** (it demands
more repair, never less rigour). But it was closable in the refusal, and four `echo` lines close it.
That is the follow-up, not a block.

---

## 11 · FILES

| File | What |
|---|---|
| `.softhouse/reviews/t483-review-t470/REVIEW.md` | this |
| `.../bin/10-drive-t468-literal.sh` | the `CLAIM 2` adjudication: T470's tip / `T468`'s patch verbatim / a rename control. 0 quoted `.softhouse/` literals |
| `.../bin/20-drive-erratum-pointer.sh` | `C-T483-1`, driven BEFORE/AFTER plus both predecessors' drives re-run. 0 quoted `.softhouse/` literals |
| `.../out/00-DRIVE-console.txt` | the adjudication drive's console |
| `.../out/10-T470-DRIVE-rerun.txt` | `T470`'s own drive, re-run by me end to end |
| `.../out/20-MERGE-RESULT-pnumber.txt` | the real merge into `main`, and the checker on the merge result |
| `.../out/21-MERGE-with-T480.txt` | `main` + `T470` + `T480`: clean, and the repaired text survives |
| `.../out/30-POINTER-DRIVE-console.txt` | the `C-T483-1` drive's console, with the 131-line gap measured |
| `.../out/40-BAR-cardinal-comparison.txt` | `T470`'s committed bar transcript vs my own run at the tip |
| `.../out/90-BAR-at-my-tip.txt` | §7b, the bar on my own committed tree |
| `.../out/armA-*`, `armB-*`, `armC-*`, `pointer/` | per-arm transcripts |

**Not touched:** `tasks.json`, `RESUME.md`, `program.json`, `LOCK`, any pin, `patterns.md`,
`conformance.sh`, `guards/`, and every file belonging to `T470`.
