# T452 — T447's conditions on T442, worked

**Branch** `softhouse/T452-t447-conditions` · **host** macOS 25.5.0 arm64, `bash 3.2.57(1)`,
`git 2.50.1 (Apple Git-155)`, `/usr/bin/grep` BSD, `python3`. All scratch under `$TMPDIR`,
**outside the repository**; every drive refuses if its scratch resolves inside the repo.

**Nothing here is inherited.** T447's numbers were re-derived, and three of them came out
differently on my tree — each difference is stated with the instrument that produced it. Two
findings are new and belong to neither T442 nor T447.

**Counts in this file carry the tree they were taken on**, because the thing being counted is a
census that is a member of the class it censuses. That is `F-T447-3`, and it applies to this
handoff too.

---

## Headline

| | |
|---|---|
| `a2-33-dec2-rev5/sweep.sh:61` — is it a real fail-open? | **YES**, narrowly: on the **corpus-reach** limb. Driven both ways. **Repaired.** |
| **T452's own fail-OPEN count** | **2** (T442 published 0; T447 left it "not established") |
| new class member found by T452 and by nobody before | `capture/t388-accrual-capture/30-casualty-sweep-t388.sh:83` — **SELF-ONLY, enforced, strictly vacuous** |
| K8 partition, re-derived twice by two independent routes | **`13 + 10 + 6 = 29`** |
| K8 wrong-decomposition sites | **two**, as T440 said. Site 2 (the handoff) **repaired**; site 1 (`AUDIT-CLASS.md`) out of grant, paste-ready |
| bar on the committed tree | see §9 |

---

## 1 · `F-T447-1` (MAJOR) — SETTLED. It is a real fail-open, on one limb, and it is repaired

**Instrument** `capture/t452-t447-conditions/instruments/t452-a2-33-failopen-drive.sh`
**Transcript** `capture/t452-t447-conditions/out/T452-A2-33-FAILOPEN.txt`

### The row

`.softhouse/reviews/a2-33-dec2-rev5/sweep.sh` — a **P-72 positive calibration**, pattern held in
`$CAL_RE`, **enforced at `exit 92`**, corpus `-- .softhouse/reviews/a2-33-dec2-rev5`, i.e. **the
searcher's own task directory**, while the sweep it certifies reads `-- .`, the whole tree.

### Driven BOTH ways, because that is what the condition asked for

| arm | what it does | result |
|---|---|---|
| **B — FOR** | a scratch git repo containing **nothing but this script**, as shipped | **exit 0**, `SWEEP CORPUS: 1`, `SWEEP CALIBRATE+: PASS`, 34 patterns reported, `SWEEP-RESULT … calibration=PASS` |
| **C — AGAINST** | the same script with its task directory renamed | **exit 92** — the guard is *not* unfireable |
| **D — the repair** | the repaired script on **arm B's own specimen** | **exit 94 CORPUS REACH FAILED**, while the *old* limb still passes on it |
| **E** | the repaired script on the real tree | **exit 0**, all three limbs PASS, 34 patterns |
| **F** | the 34 patterns before vs after | **byte-identical** |
| **G** | same specimen builder, both scripts | exits differ (0 vs 94) — the builder is not the cause |
| **H** | anti-evasion, see below | the repaired row is **still visible** to the classifier |

### The adjudication, stated precisely

The calibration's own abort text claims to cover *"the engine, the pattern language or the
corpus"*. Two of those three it genuinely establishes: a small corpus is enough to show
`git grep -i -E` runs and — with the anti-calibration beside it — does not fabricate. **The third
it does not.** Arm B is the proof: the corpus can be degraded to a single file, *the searcher
itself*, and the calibration certifies 34 negatives over it and exits 0. That is the same
reader-facing outcome as the deleted-worktree defect the whole T238 repair block was written to
remove, now with a PASS stamped on it.

Arm C matters too and is why the verdict is *narrow*: the guard fires on a real property — the
reachability of 17 files. It was simply never a guard on the reachability of the ~9.7k the sweep
reads. **So: a real fail-open, on the corpus-reach limb only.**

**T447's hypothesis, and mine.** T447 first thought the row was *strictly vacuous* and its own
drive falsified that (ten siblings carry the token). I reproduce that: with the row's own flags,
11 files match, 10 of them not the searcher. Where I go further is that **family-only here is
true BY CONSTRUCTION** — the pathspec confines the result set, so no corpus can make it
otherwise. That is stronger than "family-only on today's tree", and it is what makes the row
un-rescuable without a second limb.

### The repair

A second **enforced** limb (`exit 94`) that calibrates on **the sweep's own corpus**: does the
engine match any non-blank byte in a tracked text file **outside** the searcher's task directory?
No hard-coded foreign path (that is what rotted in 2026-08-22) and no external token — only the
tree the sweep is about to read, minus the family that cannot vouch for it. It fails **closed**.
The trailer now carries `calib_corpus=` and `reach_files=` so a machine consumer sees the gap.
**All 34 patterns are byte-identical**, asserted by arm F.

### Anti-evasion — the repair nearly hid its own row, and that is arm H

Hoisting the hard-coded task directory into `SELF_DIR=` — an ordinary tidy-up — makes the
**pathspec** variable-indirect. T442's census marks any `$`-bearing pathspec as run-time-built and
drops the row, so **the repair would have made the repaired row invisible to the census that
found it**: the same blind spot, one operand to the right. A repair that hides the repaired row
from its own instrument is not a repair. `t452-classify-v2.py` therefore resolves one level of
same-file dataflow in **pathspec** position as well as pattern position, and **arm H asserts the
row is still visible and still flagged family-only**, with a companion arm proving that an empty
selection **refuses** rather than reading clean.

---

## 2 · My own fail-OPEN count: **2** — and the method that produced it

**Instrument** `instruments/t452-classify-v2.py` · **transcript** `out/T452-CLASSIFY-V2.txt`

### The definition, written down before the count

A row is **fail-OPEN** iff **(1)** its search result is *consumed by an enforcement* — an exit, an
abort, a refusal — and not merely printed; **AND (2)** the assertion is **PRESENT-direction**: it
is satisfied when the search *finds* something; **AND (3)** it can be satisfied without the
property it asserts being true, which for a self-matching probe means every matching file is the
searcher (**self-only**) or lies inside the searcher's own task directory (**family-only**).

Direction and enforcement are read mechanically from the eight lines following the search and
reported `PRESENT` / `ABSENT` / `UNDECIDED`. **`UNDECIDED` rows are never counted safe** — they
are printed in full and adjudicated by hand, and the count of them is published.

### What the re-run changed

Three of T442's instrument choices were replaced, each for a reason T447 named:

* **variable-indirect patterns are resolved** one level from a same-file literal, instead of
  being routed to `RUNTIME` and counted safe on syntax alone (`F-T447-1`);
* **the row's own flags are replayed** (`-i/-E/-F/-w/-P`) instead of a blanket `git grep -l -F`
  (`F-T447-5`) — for `a2-33` that is **11** matching files, not the census's **2**, reproduced;
* **post-pipe self-exclusion is detected** on the whole line, not lost to `cut_at_pipe()`
  (`F-T447-4`) — **3 rows in 2 files**, reproduced.

Plus one T447 did not have: **pathspec-position variable resolution** (see §1's arm H).

### The result, tree-qualified

```
T452-CLASSIFY-V2-RESULT: tree=cbc8733c+17_dirty scripts=1791 searches=454 var_resolved=4
  self_only=1 self_plus_others=35 family_only=2 fail_open=1 undecided=1
  runtime_assembled=13 unresolved_var=29 nolit=127 immunised_pathspec=1
  immunised_postpipe=3 elsewhere=263 unparsed=24
```

The tree is on the result line **by construction**, dirty count included, so a count cannot be
copied without it. The figures above were taken *before* the run's own transcripts were staged;
**re-run with them staged, every figure above is identical** — because the two members' A1/
family-only tests are relative to the corpus each row's own assertion searches, which no
publication of ours can enter (§4). That is the drift-stability the member set was introduced for,
demonstrated rather than asserted.

`fail_open=1` **mechanically**, plus **1 `UNDECIDED` that I adjudicated by hand** — the `a2-33`
row, whose direction the eight-line window cannot resolve because both a `-lt 1` and a `-gt 0`
test sit inside it. Reading it: the `-lt 1` branch is the one that `exit 92`s, so it is
PRESENT-direction and enforced; §1 drove it. **Total: 2.**

| # | row | shape | direction | enforced | status |
|---|---|---|---|---|---|
| 1 | `capture/t388-accrual-capture/30-casualty-sweep-t388.sh:83` | **SELF-ONLY** — 1 carrier in a 194-file corpus, and it is the script | PRESENT | `exit 3` | **LIVE, UNOWNED** — filed in §6 |
| 2 | `reviews/a2-33-dec2-rev5/sweep.sh` (was `:61`) | FAMILY-ONLY **by construction** | PRESENT | `exit 92` | **REPAIRED by T452** |

**The residual I read by hand and found clean.** Of the 29 `unresolved_var` rows, **24 are false
positives of the search detector** — `echo`/`printf` lines whose *message text* contains the words
"git grep", which are not searches at all — and **5** are genuine unresolved variables:
`sweep-ORIGINAL.sh:14` (`$re`, the preserved fail-open specimen, already TIER1-pinned),
`drive-sweep-failclosed.sh:94` (`$BAD`, a malformed-pattern control), `a2-33 sweep.sh:172` (`$re`,
the loop parameter of `run()`, which prints and does not assert), `t447-failopen-a2-33.sh:68` (a
`grep -c -F` of a line of source) and `t452-.../evidence/sweep-AS-SHIPPED-19fcde77.sh:106` (my own
content-pinned before-image of the third). **0 additional class members.** This agrees with T447's
hand read of its own 11, and the 24 false positives are a precision limit of the detector that is
worth naming: it counts a *mention* of `git grep` inside a message string as a search.

**A residual I could not close, named rather than buried.** Clause (3) treats a row as safe when
some *other* file carries the probe. If those other files are all *transcripts of the same task*
published in a different directory, the assertion is still effectively self-satisfying and my
instrument will not say so. Detecting that needs a notion of "independent carrier" that I did not
build. **34 `A2` rows are exposed to it.** T442 read all 33 of its own by hand and I did not
repeat that; I re-read only the family-only and self-only rows.

---

## 3 · `F-T447-2` (MAJOR) — T440 was right. Two sites. Site 2 repaired

**Instrument** `instruments/t452-k8-sites-drive.sh` · **transcript** `out/T452-K8-SITES.txt`
(exit 0, `disagreements=0`)

### The partition, re-derived twice by two independent routes

Not taken from T442, not taken from T447.

* **from the subject file** `capture/t363-oracle-baseline/instruments/casualty-sweep.sh`:
  **16** `sel` calls at column 0; **3** of them (`S1`, `S3`, `S7`) carry no `|` in their own ERE
  and so never reach the wide `K8`; **10** `SWEEP_*=$((…))` counter lines over **3** distinct
  counters.
* **from the K8 block of the census transcript** `out/T424-CENSUS-after-with-K8.txt`:
  **29** rows extracted, of which **13** `sel`, **10** counter, **6** residual parent-side.

**`13 + 10 + 6 = 29`**, equal to the census's own printed `== K8 SITES: 29`, and the two routes
agree cell for cell. The published `16 + 8 + 6 = 30` is wrong three ways.

### Two sites, found by searching WORDS as well as digits

T442 concluded "one site" from `git grep 'all sixteen'` over `.softhouse/handoff/`. The second
site spells the same split as **words in running prose**, so that search could never have reached
it. **"Not found" is a statement about the search, never about the world** — the rule T442
invokes correctly two paragraphs earlier in the same document.

**Where I looked:** all **9,999** tracked files under `.softhouse/`, for a cardinal-16 claim
within 80 non-sentence characters of `sel`, **and** a cardinal-8/`×8` claim within 80 characters
of `SWEEP_`, in either order, case-insensitive, digits and words alike. The site predicate is the
**pair within 4 lines** — because "there are sixteen `sel` calls in the file" is TRUE and must not
be flagged; the defect is a 16-cell inside a *partition of 29*.

**Result: 7 files match the shape; 6 are declared quoting files (they reproduce the wrong
cardinals in order to correct or to test them); 1 is a live assertion site** —
`.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md:102,106,107`, which is outside every
grant so far and whose replacement text is paste-ready in the erratum.

**Site 2 — `.softhouse/handoff/T424-t408-conditions.md:233-236` — is REPAIRED.** It now reads
"Thirteen of the sixteen `sel` calls reach the wide list … Ten are `SWEEP_*=$((…))` counter rows
over three distinct counters … Six are parent-side assignments. `13 + 10 + 6 = 29`". It drops out
of the measured site set **by measurement**, not by exclusion. The superseded sentence is **not
re-spelled** in the correction note — re-planting the defect shape in the repaired file is how a
corrected cardinal comes back (`P-80`) — and it is preserved verbatim in `git` history and quoted
in the erratum, which is a declared quoting file.

### The acceptance test now reaches both sites

The erratum's original test mentioned the handoff **zero** times, so applying it as written went
green with the defect on `main`. It is replaced by a **set-equality** assertion against a site
table **parsed out of the erratum**, never typed into the drive. A new site turns it RED; a site
that is repaired **also** turns it RED unless the table loses the row in the same commit — the
same discipline `conformance.sh`'s fail-open frontier pin uses. The quoting list is likewise
declared in the erratum, and **a stale entry that matches no file is a failure**, so the exclusion
list cannot outlive what it excuses. (It caught one during development, twice.)

**Non-vacuity is driven, not asserted (P-22):** R1 requires this detector to fire on a /tmp
specimen carrying the word-spelled defect; R2 requires **T442's own recipe to find nothing on the
same specimen** — the artefact, reproduced; R3 requires the detector **not** to fire on the
corrected text, so it is not a rubber stamp.

---

## 4 · `F-T447-3` (MAJOR) — decided: **PIN, DO NOT EXCLUDE.** With the argument

The condition says: *every published count from a self-referential census must carry the tree it
was taken on, **or** be taken in a way that excludes its own publication. Decide which, and argue
it.*

**Decision: pin — and publish a drift-stable figure alongside. Do not exclude.**

**The argument.** Excluding one's own publication from the corpus is precisely the
`:!`-pathspec self-exclusion that the adjudication itself names as **the wrong repair**: it
repairs the row and opens a hole, because everything else under the excluded path stops being
scanned — including a future instrument published there. Buying stability at the price of a blind
spot, in the *one document whose subject is blind spots*, is the wrong trade.

There is a second reason, and it is the stronger one. **The drift is not an artefact — it is a
true change in the world.** A newly tracked carrier really does change what an ABSENT-assertion
measures; the census was right when it was taken and is right now. What was wrong was quoting the
numbers **bare**. Excluding the publication would make the record *stable* by making it *false*.

**So, applied:**

* the adjudication's headline table, the census's own blind-spots block and the marker file now
  carry `97bad8ed` and state the direction of drift at `c223a16b` (`self_only 2→0`,
  `family_only 3→0`, `scripts 1704→1707`, `searches 399→401`);
* `t452-classify-v2.py` prints its tree **on the RESULT line itself**, including the dirty count,
  so a count cannot be copied without it;
* and it prints a **MEMBER SET** — paths and lines — which is the figure to quote bare, because
  publishing a transcript changes bucket *labels* and never membership.

**One further sharpening, which is a method finding rather than a condition.** The A1/self-only
test should be relative to **the corpus the row's own assertion searches**, not to the whole tree.
Where it is (`a2-33`, `t388`), the finding is drift-stable and no publication of ours can enter it
— demonstrated: my own `t388` drive stays green after its transcript is committed, and asserts
the carriers *outside* that corpus as a **set** (they may only be T452's own record), so a new
carrier anywhere else turns it RED rather than quietly softening the finding. Where it is not
(`t379`, `t367`, `t245`, whose probes search all of `.softhouse/`), the drift is real and
unavoidable — and it is why those three now show **8, 8 and 11** carriers on my tree where T447
measured fewer.

**Demonstrated, not asserted.** Re-running `t452-t388-vacuous-calibration.sh` after its own
transcript was staged: `carriers outside the subject's own calibration corpus` went **0 → 2**,
both of them T452's own record, and the drive stayed **exit 0** because that arm asserts a *set*
and not a cardinal. The finding itself (`carriers = 1`, `self = 1`) did not move. A new carrier
anywhere that is **not** T452's record would turn it RED rather than quietly softening the
finding — which is what "pin, do not exclude" buys.

**Not closed:** `.softhouse/handoff/T442-t440-conditions.md` also quotes the counts bare and is
**outside T452's grant**. Filed in §6.

---

## 5 · The MINOR / LOW conditions

| # | disposition |
|---|---|
| **`F-T447-4`** (MINOR) | **Done.** The `immunised = 0` sentence is narrowed to the `:!`-pathspec mechanism in the adjudication, the three post-pipe rows are recorded by path and line, and `t452-classify-v2.py` counts `immunised_postpipe` as a first-class bucket (**3 rows, 2 files** — reproduced). The pathspec count of 0 is correct and reproduces. T447's positive side note — **0** candidate searchers outside `.softhouse/` repo-wide — is kept. |
| **`F-T447-5`** (MINOR) | **Done.** Added to the census's own printed blind-spots block *and* to the adjudication, with the measured instance (`a2-33`: census **2** files, the row's own command **11** — I reproduce both). `t452-classify-v2.py` replays the row's flags. Two blind spots were added, not one: the second is that the **pathspec** is variable-indirect too. |
| **`F-T447-6`** (LOW) | **Cannot close here — `tasks.json` is outside the grant.** Re-measured on my tree: `T381_DRIVE_INNER` occurs **0** times in the live `t381-red-drives.sh` and **5** times in `FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch`; `FU-T386-7` occurs **once** in `tasks.json`, inside `T424`, which is `merged`. **No open task applies the patch.** Paste-ready entry in §6. |
| **`F-T447-7`** (LOW) | **Done.** Both citations in `t424-comment-claims-drive.sh` (`:30`, `:135`) now read `…-census.py`. `git grep -c 'selfmatching-probe-census.sh' -- .softhouse` no longer returns those two. Both of that file's own drives were re-run after the edit: `t424-comment-claims-drive.sh` → **exit 0, `disagreements=0`**; `t442-c1-reproduction-drive.sh` → **exit 0, `disagreements=0`**. |

---

## 6 · Paste-ready task entries — five owners needed, all outside T452's grant

Every one has been re-measured on my tree at the exact line claimed. Numbers are tree-qualified
because the class drifts (§4).

```jsonc
// --- 1. THE NEW ONE. Found by T452's re-classification; missed by T442 and by T447.
{
  "id": "FU-T452-1",
  "title": "t388 casualty sweep: the P-72 positive calibration is STRICTLY VACUOUS (self-only, enforced)",
  "executor": "agent", "model": "sonnet", "status": "todo",
  "files_hint": [".softhouse/capture/t388-accrual-capture/"],
  "description": "`.softhouse/capture/t388-accrual-capture/30-casualty-sweep-t388.sh:83` is a P-72 POSITIVE calibration, ENFORCED at `exit 3`, whose known-positive `$CALIB_POS_STR` is spelled as a literal in the searcher's own source and whose corpus `$CALIB_POS_PATH` is the searcher's own task directory. MEASURED by T452 (`capture/t452-t447-conditions/instruments/t452-t388-vacuous-calibration.sh`, exit 0): the probe matches 2 times in exactly ONE file of a 194-file corpus, and that file is the script itself; it appears nowhere else in the 10,090-file tree. So the assertion 'the engine can find something here' is satisfied by the searcher's own bytes and would keep passing over an otherwise empty corpus. PRESENT-direction and enforced -- the fail-OPEN half. STRONGER than F-T447-1's a2-33 row, which at least has ten sibling carriers. It was invisible to T442's census because BOTH operands are variable-indirect (`$CALIB_POS_STR`, `$CALIB_POS_PATH`). FIX: adopt the two-limb shape T452 applied to a2-33 -- keep the engine/pattern-language limb, add an enforced CORPUS-REACH limb over the corpus the sweep actually reads, using no hard-coded foreign path. Re-run the drive above; it must stay exit 0 and the new limb must fire on a one-file specimen. Do NOT repair it by moving the probe out of the file: that hides the row from the census, which is the wrong repair (see T452 handoff arm H)."
}

// --- 2. carried forward from T442/T447, re-confirmed by T452 at the exact lines
{
  "id": "FU-T452-2",
  "title": "t379 anti-calibration drive: the printed calibration is wrong (rc=0 under a legend that says 1)",
  "executor": "agent", "model": "sonnet", "status": "todo",
  "files_hint": [".softhouse/reviews/t379-review-t371/"],
  "description": "`.softhouse/reviews/t379-review-t371/instruments/t379-anticalibration-drive.sh:49,51` searches for the literal `zzq-t379-nothing`, which the drive itself spells, so the search finds the searcher. Re-measured by T452: the row's own command returns **rc=0**, and the legend one line below reads `(1 == a MEASURED zero)`. The drive prints 0. ABSENT-direction, so FAIL-CLOSED -- no verdict moves -- but the calibration a reader is asked to trust is wrong. Carriers on T452's tree: **8** files (the drive, T442's transcript and adjudication, T442's handoff, T447's REVIEW and two of its transcripts, tasks.json) -- the count DRIFTS as the class is written about, which is F-T447-3; the drive itself is the stable member. FIX: assemble the probe at run time (`$$`/`$RANDOM`/`date`), the shape already used by t371 and t388, and re-run so the legend and the printed status agree."
}

{
  "id": "FU-T452-3",
  "title": "t367 drive-sweep-failopen: arm B no longer stands on a genuinely empty search",
  "executor": "agent", "model": "sonnet", "status": "todo",
  "files_hint": [".softhouse/reviews/t367-review-t363/"],
  "description": "`.softhouse/reviews/t367-review-t363/drive-sweep-failopen.sh:34,44` uses the literal `zzz-no-such-string-t367` for an arm captioned 'a selector that IS valid and genuinely finds nothing'. It does not find nothing: re-measured by T452, **8** tracked files carry the token today (the drive, its own transcript `out/DRIVE-SWEEP-FAILOPEN.txt`, and six later files that quote the class), up from the 2 T447 measured -- the drift is the class writing about itself. The drive's POINT (arms B and C are indistinguishable because the sweep discards the status) survives; its demonstration does not. ABSENT-direction, FAIL-CLOSED. FIX: run-time-assembled probe, re-capture the transcript, and state in the caption that the arm's emptiness is now enforced by construction rather than by the corpus."
}

{
  "id": "FU-T452-4",
  "title": "t245 measure.sh: the negative calibration prints 11, and it exists at TWO sites",
  "executor": "agent", "model": "sonnet", "status": "todo",
  "files_hint": [".softhouse/reviews/t245-oracle-pin/"],
  "description": "`.softhouse/reviews/t245-oracle-pin/measure.sh:131` is a calibration whose whole job is to print **0** for the known-absent token `zzq_nonexistent`. Re-measured by T452 on my tree it prints **11** (T442 recorded 5, T447 confirmed 5; the growth is the class being written about -- F-T447-3, so quote the tree). A SECOND site that T442 does not mention exists at **`measure.sh:119`**: `len(re.findall(b'zzq_nonexistent', pre))` inside the embedded python block. That one scans a captured buffer rather than the tree, so it is NOT degraded today -- but a filing that names only `:131` under-describes the file, and the buffer could acquire the token the same way. ABSENT-direction, FAIL-CLOSED: nothing aborts, so a reader can take the table below it as calibrated when it is not. FIX: assemble the token at run time at BOTH sites, re-run, and re-capture `measure-output.txt`."
}

// --- 3. F-T447-6: the repaired guard has no owner (P-45)
{
  "id": "FU-T452-5",
  "title": "FU-T386-7's amended red-drive guard has no owner: apply the patch or retire it",
  "executor": "agent", "model": "sonnet", "status": "todo",
  "files_hint": [".softhouse/capture/t381-t379-conditions/", ".softhouse/capture/t424/patches/", ".softhouse/tasks.json"],
  "description": "T442 repaired `FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch` and T447 accepts that disposition -- repairing the patch IS repairing the subject, and closing the surface while nothing runs is when it is cheapest. The residual is OWNERSHIP, not correctness. Re-measured by T452: `T381_DRIVE_INNER` occurs **0** times in the live `.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh` and **5** times in the patch; `FU-T386-7` occurs **once** in `tasks.json`, inside `T424`, which is `merged`. **No open task applies this patch**, so the parent-pid-bound marker never runs. P-45 -- *'A test-only guard is not a guard'*: verify that the path which actually executes in CI/conformance calls the check, not merely that a test does. Here nothing calls it at all. DECIDE AND RECORD: apply the patch to the live drive and re-run `t442-t440-lows-drive.sh` (nineteen arms, must stay exit 0 / disagreements=0, including the healthy control), or formally retire the patch with the reason. Either way the outcome must be a tasks.json entry, because T442 and T452 both lack the grant."
}
```

**Two more residuals that need a grant, not a task id of their own** (fold them into whoever
picks up the K8 and census work):

* `.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md:102,106,107` — the **live** K8 site.
  Paste-ready replacement text is in `capture/t424/ERRATUM-K8-DECOMPOSITION.md`. When it is
  applied, the erratum's `T452-SITE-TABLE` must lose the row **in the same commit** or
  `t452-k8-sites-drive.sh` goes RED, which is the intended behaviour.
* `.softhouse/handoff/T442-t440-conditions.md` — quotes the class-sweep counts **bare**. It needs
  the same `97bad8ed` qualification the adjudication and the marker file now carry.

---

## 7 · What I confirmed of T447's account, and where I differ

| claim | my instrument | result |
|---|---|---|
| K8 = `13 + 10 + 6 = 29` | subject file **and** census transcript, independently | **reproduces**, cell for cell |
| the handoff carries the wrong split at `233,235,236` | site detector over all 9,999 tracked `.softhouse/` files, words and digits | **reproduces** |
| `git grep 'all sixteen'` cannot see it | run on a /tmp specimen carrying the defect | **0 matches — the artefact reproduces** |
| `a2-33` row is family-only and enforced | the row's own flags | **reproduces**, and is family-only *by construction* |
| the census reports 2 files where the row matches 11 | both commands | **reproduces exactly** |
| `immunised_postpipe = 3` in 2 files | whole-line detector | **reproduces** |
| the three unowned members at their exact lines | `git grep` on my tree | **all three confirmed**, plus `t245:119` |
| carrier counts for those three | `git grep -l` | **I differ: 8 / 8 / 11**, where T447 measured fewer — the class drifts as it is written about (F-T447-3), which is why the member set and not the count is the thing to quote |
| `0 fail-OPEN` | the re-classification | **I differ: 2** |
| `family_only` in T442's census | re-run at my tip | **I differ: 0 by T442's instrument, 2 by mine** — the flags and the variable resolution move it |
| `C-T440-1` closed; `F-T442-1` closed | not re-driven — settled by the task brief | left closed. `t442-c1-reproduction-drive.sh` re-run after my citation edit: **exit 0** |

---

## 8 · Scope

Changed paths, all inside the grant:

```
.softhouse/capture/t452-t447-conditions/**            (mine)
.softhouse/capture/t424/ERRATUM-K8-DECOMPOSITION.md
.softhouse/capture/t424/instruments/t424-comment-claims-drive.sh      (F-T447-7)
.softhouse/capture/t424/instruments/t442-selfmatching-probe-census.py (F-T447-5/4/3 blind spots)
.softhouse/capture/t424/out/T442-CLASS-SWEEP-ADJUDICATION.md
.softhouse/capture/t424/out/T424-comment-claims.TRANSCRIPT-IS-NOT-REPRODUCIBLE.md
.softhouse/handoff/T424-t408-conditions.md            (F-T447-2, second site only)
.softhouse/reviews/a2-33-dec2-rev5/sweep.sh           (F-T447-1's site only)
.softhouse/handoff/T452-t447-conditions.md            (this file)
```

`conformance.sh` (T454), `bin/ready-tasks.py` (T451) and `hooks/` (T453) are **untouched**.
No money path, no vector, no schedule figure, no ledger code is in the diff; the whole change is
instruments, transcripts and prose.

---

## 9 · The bar

Run with `bash`, never `sh`/`zsh`; scratch in `/tmp`, **outside the repository**; on the finished
**committed** tree. **Presence of the probe line was tested before its value was read** —
`grep -c 'probe = '` first, because absence is a harness failure and is not `down`.

**The bar refused my first committed attempt, and that is recorded rather than hidden.** Arm C of
the `a2-33` drive spelled its relocated specimen path as a literal —
`.softhouse/reviews/…-dec2-rev5/sweep.sh` under a name that exists nowhere — so
`guard_dead_path_frontier` refused: `T316-DEADPATH-FRONTIER: REFUSED rows=109 pinned=108 added=1
removed=0`, **BAR EXIT=2**, on a clean tree (0 dirty). The guard's own prescription is *"repair it
rather than pinning it"*, so the destination is now **assembled at run time** from the real
directory (`$(dirname "$SELF_DIR")/t452-relocated-$$`) and the arm sanity-checks the derived path
before using it. **The pin is untouched and the frontier is back at 108.** This is the same
repair T447 made to its own hard-coded path, and the same one T440 made before that — the third
time this exact guard has caught this exact reflex, which is worth a `patterns.md` note.

BAR TRANSCRIPT: `capture/t452-t447-conditions/out/T452-BAR.txt`

```
grep -c 'probe = ' -> 1     (PRESENCE tested FIRST; absence would be a harness failure, not `down`)
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
T316-DEADPATH-FRONTIER: rows=108 pinned=108
deadOccurrences 108   frontier 11 == 11
VERDICT: PASS (exit 0)
BAR EXIT=0
```
