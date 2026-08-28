# T379 — INDEPENDENT review of T371 (`softhouse/T371-t367-conditions` @ `8441c7e3`)

**VERDICT: APPROVED.** Merge it. Every material claim T371 makes reproduced under my own
instruments, and several reproduced under *stronger* discriminators than T371 used. I found four
residual defects; none of them is a regression, none is reachable through the shipped
configuration in a way the selector layer would not also catch loudly, and three of the four are
inherited from `main`. The one that is new is bounded. **Not merging is the worse outcome**: `main`
today carries the demonstrated fail-open (drive A2 below, exit 0 on a search that never ran) *and*
a live wrong cardinal in `reference-oracle.md`, and this branch closes both.

I considered REJECTED on finding **R2** and rejected that verdict; the reasoning is written out
under *Why not REJECTED* so the driver can overturn it on the record.

Reviewer read the diff with `git diff main...softhouse/T371-t367-conditions` and the upstream
handoff with `git show softhouse/T371-t367-conditions:…/T371.md`. Reviewer's own worktree is at
`f1272ae5` (= `main`), so every "BEFORE" measurement below is a measurement of `main`.

**T379 FIRED NO PROBE.** Every statement I issued against the reference oracle (Fineract) is a
`SELECT`, several of them under `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`. Closing
read matches T371's: `je 71/75`, `cs 359/359`, `closure 0 rows`
[`out/R2-POLICY5.txt` § 12]. No `PROBES.tsv` row is required and none was added. T367's finding —
**a 4xx burns the key** — is why: I re-verified it at the pin before deciding not to probe, not
after.

---

## 1. What I checked, so silence is distinguishable from not looking

| # | Claim under test | Method | Result |
|---|---|---|---|
| F1a | `idempotency_key` is `NOT NULL` | `information_schema.columns`, live | **CONFIRMED** — `NO`, `varchar(50)` |
| F1b | 339 minted UUIDs / 20 name a task | **my own** 3-discriminator classifier | **CONFIRMED, and strengthened** |
| F1c | the two classifiers "agree exactly" | **set** equality, not count equality | **CONFIRMED** — 0 disagreement either way |
| F1d | row 352 is a minted UUID, permanently unattributable | live read of ids 350–359 | **CONFIRMED** |
| F1e | minting path at the pin | read `426a23544` | **CONFIRMED** at `:36` / `:27-29` |
| F2a | BEFORE: malformed and empty selectors are byte-identical at exit 0 | re-ran T371's drive | **REPRODUCED** |
| F2b | AFTER: 0 vs 4, and E/F/G/H | re-ran T371's drive | **REPRODUCED**, all 8 rows |
| F2c | a **third** swallowed status | **my own** drive | **FOUND — three of them.** § 3 |
| F2d | exit contract honoured on every path | code read + drives | **honoured except on the R1 path** |
| F2e | `.softhouse/observations/` removal is right | predicate vs T363's own list; cost measured | **CONFIRMED right, and cheap** |
| F3a | live split is 162 / 197 | **my own** SQL | **CONFIRMED** — 162 (157+5) / 197 (195+2) |
| F3b | the qualitative claim is TRUE | live | **TRUE — 197/359 = 54.9 %** |
| F3c | …and stays true under plausible movement | trend analysis, live | **QUALIFIED. § 4 — margin is 17 rows** |
| F3d | the named SQL produces what the prose says | read + re-ran equivalent | **CONFIRMED** |
| F3e | S12–S16 match the site 3×, S1–S11 0× | re-ran the sweep both ways | **CONFIRMED** — 3 vs 0 |
| F3f | the sweep now "takes minutes" | **measured** | **96 s vs 46 s.** § 5 |
| P5a | `acc_gl_closure_id_seq` = `last_value 1, is_called t`, table 0 rows | live | **CONFIRMED** |
| P5b | 281 base tables vs 2 watched | live | **CONFIRMED** (281 in `public`, 281 in all non-system schemas) |
| P5c | 8 rows `reversed = t`, all below the floor | live | **CONFIRMED** — 8 rows, ids 33…60, floor is 64 |
| P5d | 0 float columns across all 281 | live | **CONFIRMED** |
| 4xx | a 4xx **burns** the key | read `426a23544` | **CONFIRMED, and I strengthened the proof** |
| BAR | first bar RED at frontier 110, kept as evidence | read both committed transcripts | **CONFIRMED** |
| BAR | final bar 46/0/0, exit 0, frontier at pin | read the committed transcript | **CONFIRMED** |
| — | no probe fired by T371 | live max-ids + `PROBES.tsv` diff | **CONFIRMED** |

---

## 2. F1 — I built my own classifier, and it says T371 is right, by a stronger argument

T371's classifier is an 8-4-4-4-12 hex regex. That is the obvious discriminator and it is easy to
get subtly wrong, so I did not reuse it. Mine
[`sql/r1-classifier.sql`, output `out/R1-CLASSIFIER.txt`] runs three:

- **(A) character-set + length** — canonical 36 chars, `[0-9a-f-]` only, hyphens at 9/14/19/24.
- **(B) strict RFC-4122 version 4** — `…-4xxx-[89ab]xxx-…`. `UUID.randomUUID()` *always* sets the
  version nibble to `4` and the variant nibble into `[89ab]`. **A key that is UUID-shaped but not
  v4 was not minted by `IdempotencyKeyGenerator.create()` — it was supplied by a caller.** That
  distinction is invisible to T371's regex, and if even one row had failed it, "339 minted UUIDs"
  would have been the wrong conclusion from the right count.
- **(C) semantic, and deliberately vocabulary-free** — does the key contain a letter outside the
  hex alphabet followed by two more letters, i.e. a human-authored word? No list of task names
  appears anywhere in the predicate.

Measured live:

```
total 359   nulls 0   blanks 0   distinct 359   min_id 1   max_id 359
shapeA_uuidish  339      shapeB_v4  339      notA  20      notB  20
uppercase-hex UUIDs: 0      A-positive-but-not-v4: 0 rows
```

**All 339 are strict lowercase v4.** So T371's inference — these are server-minted, not
caller-supplied — survives a discriminator it did not run, and I regard F1's central claim as
established rather than merely restated. [VERIFIED: T379, live `fineract_gerege`, `out/R1-CLASSIFIER.txt` §§ 1, 3, 4]

**The boundary of "names a task", stated explicitly, because the brief required it.** My
classifier C is *weaker* than T371's and I report the disagreement rather than hiding it:
C finds **17**, not 20. The three it misses are `a2-29-je-1-0001`, `a2-29-je-2-0001`,
`a2-29-je-2-0002` — every letter in them (`a`, `e`, `b`... ) is a hex character except `j`, and
`j` is not followed by two more letters. **`in_C_only = 0`**: no UUID-shaped key contains a
human word, so the 339 is not contaminated in the other direction. Reading the 20 rows by eye,
all 20 name a task. So the boundary I would state is: *a key names a task iff a human chose the
string*, and on this corpus that is decidable by inspection of 20 rows and by nothing shorter.

**On T371's "two independent classifiers, same answer" — I verified something T371 did not
publish, and it holds.** T371 reported two *counts* that were both 20. Two counts agreeing at 20
is compatible with two *different* sets of 20. I ran the set comparison:

```
token_but_uuid_shaped 0     notuuid_but_no_token 0     agree 20
```
[`out/R2-POLICY5.txt` § 11]. The sets are identical. The claim is true at the level it needed to be
true and was only evidenced at a weaker level.

**One honest caveat on the word "independent."** T371's second classifier is
`(t\d{2,3}|a2-\d+|arm\d+)` — that vocabulary is *this tenant's* task-name vocabulary, so the
regex was necessarily written after looking at the data it grades. It is independent in
*criterion* (semantic vs shape), not in *derivation*. The real evidence for "20" is the listed
20 rows, which T371 did publish. Not a defect; a calibration of how much the agreement is worth.

**Row 352 [FU-T367-4] — CONFIRMED.** `138af578-bd93-4ae5-b8a5-16b6213d0f43`, `status = 5`, strict
v4. Minted, names nothing, permanently unattributable. Rows 353–359 are the seven task-named
keys above the floor, exactly as T371 lists them, and 13 more sit at ids 281–307. Both counts
land exactly. [VERIFIED: `out/R1-CLASSIFIER.txt` §§ 5, 6]

**The minting path at the pin — CONFIRMED, and T371's line cite is right.**
`IdempotencyKeyResolver.java:36` is
`Optional.ofNullable(wrapper.getIdempotencyKey()).orElseGet(() -> getAttribute().orElseGet(idempotencyKeyGenerator::create))`
and `IdempotencyKeyGenerator.create()` at `:27-29` is `return UUID.randomUUID().toString();`
[VERIFIED: T379, `/Users/buv/fineract` @ `426a23544`]. That is what makes the v4 result above
*predicted* rather than coincidental.

---

## 3. F2 — the repair works. I found three residual swallowed statuses, one of them new

### 3.1 The repair, reproduced independently

I re-ran T371's drive from my own worktree
[`out/R3-DRIVE-REPRODUCED.txt`, instrument extracted from git on every run, both sha256s printed,
`AFTER e9f30047…`]. **All eight rows reproduce exactly**, including the byte-identical BEFORE pair
that is the defect:

```
A1 before EMPTY      exit 0     hits total: 0   archived: 0   LIVE: 0
A2 before MALFORMED  exit 0     hits total: 0   archived: 0   LIVE: 0    <- IDENTICAL. F2.
C  after  EMPTY      exit 0     MEASURED ZERO -- engine ran over 8224 tracked files
B  after  MALFORMED  exit 4     SELECTOR DID NOT RUN (git grep rc=128)
E  calibration+ red  exit 3     F  anti-calibration exit 3     G  no corpus exit 2
H  green             exit 0     selectors=16 did_not_run=0
```

The engine arm independently agrees: `git grep` empty-result **1**, malformed **128**, hitting
**0**; `main` reads **0** of 4 `git grep` statuses, the branch reads **1**. The repair is real.

### 3.2 R1 — the ARCHIVE-predicate greps still discard their status *(inherited from `main`)*

`sel()` reads `git grep`'s status, then hands the hits to two greps whose status it does **not**
read:

```
live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE")
arch=$(printf '%s' "$all" | grep -c -E "$ARCHIVE")
```

I drove it [`instruments/t379-third-status-drive.sh` → `out/R4-THIRD-STATUS-DRIVE.txt` § X], breaking
**only** `$ARCHIVE` and leaving the shipped instrument otherwise intact:

```
X1 valid predicate     hits total: 2   archived: 1   LIVE: 1        exit 0
X2 malformed predicate hits total: 2   archived:     LIVE: 0        exit 0   <- R1
```

A selector that **hit** is reported as `LIVE: 0` at exit 0, with `did_not_run=0`. That is F2's
exact shape — a negative the instrument never measured — moved one step downstream of where T371
repaired it, and the exit contract's promise for `0` ("every selector RAN. Hits or measured
zeros; both are MEASUREMENTS") is not honoured on that path.

**Why this is a follow-up and not a blocker.** It is pre-existing on `main`, it is unreachable
unless someone edits `$ARCHIVE` into an invalid ERE — and the blank in the `archived:` field is a
visible tell. But `$ARCHIVE` is *exactly* the line T371 just edited, so this is live territory,
not dormant code.

### 3.3 R2 — the anti-calibration passes on a search that never ran *(NEW, in T371's own code)*

This is the one I would most like fixed, because it is the same defect **inside the guard written
to repair that defect**:

```
n=$(git grep -c -F "$CALIB_NEG_STR" -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
if [ "${n:-0}" -gt 0 ]; then  … exit 3 ; fi
```

`2>/dev/null` discards the engine's complaint and the pipe into `awk` discards its status, so a
`git grep` that **errors** yields `n=0`, which is indistinguishable from "the sentinel is
correctly absent." Driven, changing nothing but making that one search fail
[patched pathspec, raw `git grep` rc **128**]:

```
SWEEP CALIBRATE+: PASS -- known positive matched 1 time(s) in …/instruments/
SWEEP CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus
SWEEP-RESULT: … calibration=yes exit=0
```

**It printed `PASS … matched 0 times across the tracked corpus` for a search that ran over
nothing**, then declared the sweep calibrated —  and the control run with the *unmodified*
instrument prints those three lines **byte-identically**, which is precisely the BEFORE/AFTER
indistinguishability that made T367's F2 a rejection
[`instruments/t379-anticalibration-drive.sh` → `out/R7-ANTICALIBRATION-DRIVE.txt`; instrument
extracted from git, sha256 `e9f30047…`, only the anti-calibration's *pathspec* substituted].
The positive arm has the identical construction
but fails *safe* (a never-run positive yields `n=0` → `exit 3`); only the anti-calibration arm is
fail-open.

**Bounded, and that is why it does not block.** In the realistic world where `git grep` is broken
enough to error on `-- .softhouse/`, all sixteen selectors error too, each prints `SELECTOR DID
NOT RUN`, and the run exits **4** — loudly inadmissible. R2 bites only for an engine that errors
on the anti-calibration's invocation and not on the selectors', and both are
`git grep … -- .softhouse/`. Remedy, for the follow-up: capture `rc` for each calibration search
before the pipe and `exit 3` on `rc >= 2`. That is a control-flow change to a guard and by T371's
own (correct) argument it needs its own red drive, which is precisely why it is not a MICRO-FIX.

### 3.4 R3 — the calibration exercises `-F`; thirteen of the sixteen selectors use `-E`

Both calibration searches are `git grep -c -F`. The shipped selectors are **3 `-F` and 13 `-E`**
[`out/R4-THIRD-STATUS-DRIVE.txt` § Y]. The header's stated justification for the anti-calibration
is a `-E` hazard — *"because `git grep -E` on this host has been measured FABRICATING a hit
(T238)"* — and `-F` has no metacharacters to misinterpret, so it cannot reach that hazard.

**T238's finding still reproduces on this host, today, measured by me:**

```
git grep -E '\bmain\b'   hits = 97
git grep -E 'bmainb'     hits = 97      <- identical: -E is reading \b as a literal b
```

So the failure mode is live, not historical, and the calibration cannot see it. If `git grep -E`
mis-parses a selector it returns rc **1**, and the instrument prints `MEASURED ZERO — engine ran
over 8224 tracked files and matched nothing` — **a negative it did not measure**, which is the
invariant this whole repair is named after, unenforced for 13 of 16 selectors.

**Mitigating, and it is why this is not a rejection:** the instrument's header *states* this blind
spot explicitly (*"NO `\b` anywhere, because `git grep -E` reads `\b` as a LITERAL 'b' on this
machine and returns zero SILENTLY"*), and none of S1–S16 uses `\b`. Under `patterns.md:661` that
is the honest kind of tripwire, not the vacuous kind. The remedy is one extra calibration pair
run through `-E`.

### 3.5 R4 — stderr is folded into the hit set on *every* path, including `rc = 0` *(cosmetic)*

`all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?`. The fold is wanted on the `rc >= 2` path, where
T371 correctly prints the engine's complaint. On `rc = 0` it means a warning line is counted by
`grep -c .` as a hit and, unless it happens to match `$ARCHIVE`, listed as LIVE. Direction is
toward false positives, so it is conservative; but `hits total` is not purely a hit count.
Symmetrically, on `rc = 1` the folded stderr is discarded unprinted.

### 3.6 The rest of the exit contract IS honoured

Paths the drives do not exercise, checked by reading: not-a-work-tree → 2; work tree with zero
tracked files under `.softhouse/` → 2 (`P-35`, correctly a denominator error and not a pass);
`sel()` before `calibrate()` → refuses without searching and sets 3 (defensive, unreachable in
shipped order); `SWEEP_RC` is accumulated by assignment and never inherited from a pipeline;
`set -uo pipefail` with no `-e`, so no path exits silently early. `4` wins over a later `0`
because nothing ever resets `SWEEP_RC`. **The one contract violation is R1's path**, where a
mis-classified hit exits `0`.

### 3.7 F2-adjacent — removing `.softhouse/observations/` from ARCHIVE is RIGHT, and cheap

The inconsistency T367 found is real and I reproduced it: `CASUALTIES.md:95` names
`observations/20260827-chain2-standing-oracle-baseline.md:21-26` as a **LIVE** casualty while
`main`'s predicate contained `\.softhouse/observations/`, so the shipped list was not derivable
from the shipped script. Removing it resolves the contradiction **in the widening direction**,
which is the safe one for an instrument that gates nothing.

I checked the cost rather than assuming it. Of **1402** LIVE lines in a full post-repair sweep,
exactly **17** come from `.softhouse/observations/`. Nothing that should be treated as archived is
newly swept: `runs/`, `logs/`, `handoff/`, `reviews/`, `capture/bar-`, `/out/`, `/evidence/`,
`/transcripts/` all remain in the predicate, and observations are standing notes a reader treats
as current — which is exactly T371's stated criterion and it is the right one. **Approved.**

---

## 4. F3 — the departure was right; the qualitative claim is TRUE but thinner than T371 says

**The live figures — my own derivation, not T371's.** [`out/R1-CLASSIFIER.txt` § 7]

```
status 1 PROCESSED  162   (157 at or below the floor,  5 above)
status 5 ERROR      197   (195 at or below the floor,  2 above)
total               359
```

Identical to T371's, to the cell. `sql/q2-status-split.sql` is **correct** — the enum cite is
right (`0 INVALID … 5 ERROR`), it groups whole-table *and* splits on the id-352 floor, and it
produces exactly what the prose derives from. [VERIFIED: T379]

**Was deleting the cardinal right?** Yes, and I would have graded a substituted `162 / 197` down.
The file's own POLICY § 3 says do not add a count to this file, the sentence had gone stale four
times, and the replacement pair is wrong the moment anyone probes. Recording the superseded
sentence in a **past-tense** block over a *sentence* — rather than a superseding marker, which is
right over a *dated table* — is the correct instrument choice and T371 argues it correctly against
T367's MICRO-FIX # 3. I verified the old pair survives on the branch only as a quotation inside
that block (`reference-oracle.md:934`) and that the new pair is typed **nowhere** in
`reference-oracle.md`. Confirmed.

**Is the qualitative claim TRUE?** Yes. 197 of 359 = **54.9 %**. Not vacuous either — it is
falsifiable, which is the property that distinguishes it from "a claim vague enough never to be
wrong."

**Does it stay true under plausible movement? THIS IS WHERE I QUALIFY T371.** The margin over a
bare majority is **17 rows**, and the recent history runs *against* the claim
[`out/R5-TREND.txt`, live]:

```
ids   1– 30 :   0 ERROR /  30 ok            ids 241–270 :  17 / 13
ids  31– 60 :  14 / 16                      ids 271–300 :   4 / 26
ids  61–150 :  49 / 41                      ids 301–330 :   7 / 23
ids 151–240 :  89 /  1   <- the block that carries the claim
                                            ids 331–359 :  17 / 12
```

**In the most recent 89 commands, refusals are a 31 % MINORITY** (28 / 61). The whole-table
majority rests on ids 151–240. At that recent mix it takes roughly **94** further commands to
falsify the sentence; at a PROCESSED-only mix, **35**. This tenant accumulated 359 rows over the
program to date, so neither number is remote.

Two consequences the driver should have in writing:

1. T371 calls this *"the claim that is actually robust."* It is **more** robust than a cardinal —
   a cardinal is wrong after one row, this survives ~35 — but it is not robust, and the handoff's
   framing overstates by omitting the margin.
2. **When it does become false it will become false silently, and S12–S16 cannot help.** Those
   selectors hunt *a digit in doctrine prose*; the repair removed the only digit at this site. The
   selectors would have caught the old sentence — I confirmed `[0-9]+ (PROCESSED|ERROR|…)` matches
   `main`'s line 930 — and they will not catch its successor going stale. That is not an argument
   for putting the cardinal back; it is an argument for the correction block to carry the margin,
   or for the sentence to be made structurally true (*"a large fraction … by construction —
   derive the split"*). **Recommended, not required. Filed as FU-T379-1.**

**S12–S16 coverage — CONFIRMED independently.** Running the repaired sweep in my worktree (whose
`reference-oracle.md` is `main`'s, i.e. still carries the stale sentence):

```
S12/S13 hits on the F3 site:  3      (:929 the enum line, :930 twice)
Same site under S1..S11 only: 0
```
[`out/R3-DRIVE-REPRODUCED.txt` § H]. Exactly T371's claim. One point of precision: one of the
three is the adjacent **enum-definition** line, which is a correct `VERIFIED` citation and not a
casualty — so the *casualty line itself* is matched twice. T371 says "the F3 site", which is fair,
but a reader counting casualties should know.

**A small casualty T371 created while repairing one.** `casualty-sweep.sh:191` — a **live**
instrument, not archive — now carries the comment `# … -- live 162 / 197, T371 re-derived it`.
That is a fresh cardinal about a live table, in the present tense, in a tracked non-archive file:
the exact class F3 is about, one generation on. Its own S12 duly reports it as a **LIVE** hit
[`out/CASUALTY-SWEEP-T371.txt:1103`]. `CASUALTIES.md:97` states the same pair **dated** ("Live at
2026-08-28 was 162 / 197"), which is correct as a witness. The one-word fix is to date the comment
the same way. **FU-T379-2, MINOR.**

---

## 5. Cost — I measured it, and it is acceptable (P-45)

T371 says the sweep "takes minutes" and does not publish a number. I timed it, same corpus, same
host, sequentially:

| | selectors | real | user | CPU |
|---|---|---|---|---|
| `main` | 11 | **46.1 s** | 154 s | ~335 % |
| branch | 16 | **96.4 s** | 323 s | ~335 % |
| S15 alone (raw `git grep`) | — | **22.3 s** | 74 s | — |

So: **2.1× slower, +50 s, 96 s total.** T371's "minutes, not seconds" is a mild overstatement of
its own cost; its "S15 is the slowest, 10–60 s alone" and "~250–300 % CPU" are accurate.

**Judgement: ACCEPTABLE, and P-45 is not triggered.** P-45's failure is a guard nobody runs or one
invoked nowhere. This one gates nothing, is invoked by hand, and is run once by a task that
touches the standing oracle. Ninety-six seconds is not a deterrent at that cadence. **The trade is
also the right one on the merits** — S12–S16 are the selectors that found the casualty eleven
narrow ones missed, and a selector that is fast because it is narrow is the failure this
instrument exists to prevent.

**The real cost is not time, it is triage volume, and T371 does not quantify it.** The full sweep
emits **1402 LIVE lines** (S9 464, S11 465, S14 234 dominate; the new S12–S16 contribute **376**).
T371 declares honestly that it did not triage them and files FU-T371-2 — correct, but a reader
should see the number before deciding how much the sweep's next "LIVE" list is worth. Recorded
here so the follow-up is scoped. **Not a defect.**

---

## 6. Carried-forward facts — all four re-derived at the pin or live

**A 4xx burns the key — CONFIRMED, and I strengthened it beyond T371's citation.**
`SynchronousCommandProcessingService.java` @ `426a23544`: `:133`
`exceptionWhenTheRequestAlreadyProcessed(...)`; `:140` `commandSourceService.saveInitial(...)`;
`:151` `return executeCommandInTransaction(...)`; `:241-260` the switch, with `case ERROR ->` at
`:257-259` throwing `IdempotentCommandProcessFailedException` when `!retry`. All four line cites
are exact. Two things T371 asserted that I verified rather than took:

- `CommandSourceService.saveInitial` at `:66` is **not** `@Transactional` and calls
  `saveAndFlush`; the class comment at `:50-51` is verbatim *"The initial command source is
  persisted separately for idempotency."*
- **The business transaction opens *after* the row is flushed**:
  `CommandSourceService.processCommandAndSaveResult` is the `@Transactional` method (`:116-117`)
  and it is reached only from `executeCommandInTransaction` (`:159`), which `:151` calls. So the
  audit row genuinely survives a rolled-back business transaction, which is the strong form of
  the claim and is what `oracle-state-baseline.sh`'s new header block asserts.
  **[VERIFIED: T379, pinned `426a23544`.]**

  *Wording note, no action needed:* POLICY § 5's fourth case — *"a rolled-back transaction leaves
  nothing to attribute at all"* — sits awkwardly beside that. Read in context it means a rolled-back
  **direct-SQL** transaction (evasion b), not a rolled-back command; the two are consistent but a
  hurried reader could take them as contradicting.

**The three evasions — all CONFIRMED live** [`out/R2-POLICY5.txt`]:

| evasion | T371 | T379 measured |
|---|---|---|
| consumed sequence | `acc_gl_closure_id_seq` `last_value 1, is_called t`; table 0 rows / max id null | **identical** |
| other tables | 281 base tables, 2 watched | **281** in `public`; **281** across all non-system schemas |
| `UPDATE` below the floor | 8 rows `reversed = t`, all ≤ 64 | **8 rows, ids 33…60**; floor is 64 |
| (float check) | 0 float columns across all 281 | **0** (`double precision`/`real`/`money`) |

---

## 7. The bar — verified the way the brief required, including that T371 did it that way

**Both transcripts are committed and show what T371 says they show.**

`out/BAR-RED-deadpath-frontier.txt`, kept as evidence rather than discarded:
```
:157  guard_dead_path_frontier: THE FRONTIER MOVED IN A WAY NOBODY RECORDED.
:163  > .softhouse/capture/…/casualty-sweep.sh | .softhouse/\n
:166  T316-DEADPATH-CENSUS: corpus=1343 deadFiles=77 deadOccurrences=110 …
:176  T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=109 added=1 removed=0
 last  a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

`out/BAR-conformance-t371.txt`:
```
:158  T316-DEADPATH-CENSUS: corpus=1344 deadFiles=76 deadOccurrences=109 …
:171  oracle probe    UP
:613  parity vectors PASS 46  FAIL 0     :614 contract-refusal PASS 4  FAIL 0
:615  self-test PASS 1  FAIL 0           :616 refused 0    :617 inadmissible 0
:435  ledger parity PASS 7  FAIL 0       :436 ledger oracle-refusal PASS 6  FAIL 0
:635  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
:651-663  13 KILLED wrong ledger implementations
```

Corpus **1343 → 1344** and occurrences **110 → 109** confirm the claim that matters most: the new
tracked instrument **is** in the census, and the frontier is back **at its pin (109)**, repaired at
source rather than pinned over. The bar is not weakened — same 46/0, same 0 inadmissible, same 13
kills.

**MICRO-FIX candidate, mechanical, not a number.** The handoff quotes `BAR_EXIT=2` and `BAR_EXIT=0`
inside blocks presented as transcript excerpts; neither string is in either committed transcript —
they are the author's shell wrapper's output. The exit codes themselves are corroborated by the
transcripts' own last lines. Cosmetic.

**One self-contradiction worth correcting on merge.** The handoff states *"No file this task
touched is read by `conformance.sh`."* That is **false**, and the same document proves it false
four paragraphs later: `conformance.sh`'s dead-path census reads tracked `.softhouse/**/*.sh`, it
read `casualty-sweep.sh`, and that is exactly why the first bar went RED. The intended meaning —
*no vector or graded artefact* — is correct. **MICRO-FIX class: ≤ 1 line, mechanical, no number.**

**T371 fired no probe — CONFIRMED from three sides.** Its `PROBES.tsv` diff adds **42 comment
lines and zero data rows** (checked by filtering `^+` for non-`#`). Live max-ids today match its
opening *and* closing reads exactly — `je 71/75`, `cs 359/359`, `closure 0` — and `cs_max` is
still **359**, so nothing has landed above the floor since. `run-reads.sh` issues only `SELECT`s
and self-checks the opening/closing pair.

---

## 8. The declared open blocker — leaving `T363.md:30` was right, for one of the two stated reasons

`.softhouse/handoff/…/T363.md:30` still reads *"Every command names its task — including every
refusal."* It is false — 339 of 359 rows name nothing.

**I agree with the refusal, and I would merge without it fixed.** It is outside the write grant;
T363's own refusal to reach outside its grant was upheld by T367; and both **live** statements of
the claim (`reference-oracle.md` POLICY § 2, `t363-oracle-baseline/README.md`) are repaired, which
is where a reader forms a belief.

**But T371's second reason does not survive scrutiny, and the driver should know.** T371 groups
this with T287's `ARM2-OBSERVATION.md:136` as *"an archived, dated record"* and invokes POLICY § 4.
The two are not the same class:

- T287's `156 PROCESSED / 194 ERROR` **was true when it was written**. It is a *measurement*, and a
  witness is not edited to agree with today. POLICY § 4 applies squarely.
- T363's *"every command names its task"* was **false on the day it was written** — 339 minted
  UUIDs already existed. It is not a dated measurement, it is a dated **inference**, and it was
  wrong. "Do not retype a historical figure" does not extend to "do not mark a false inference."

So the correct instrument is the one T371 filed as **FU-T371-1**: a superseding *annotation*
pointing forward, never a deletion. I endorse granting it, and I endorse the general rule T371
offers as the alternative — *archived handoffs are never corrected, only annotated*. **Not a
blocker for this merge.**

---

## 9. Non-negotiables

No money path is touched. No monetary value, arithmetic, rounding or currency conversion is added
or altered. I re-checked the diff for floats in a monetary sense: the only `float`/`double`/`real`/
`money` tokens are `oracle-state-baseline.sh`'s **detector** for prohibited column types and
`sql/q4`'s query counting them — which returns **0** across all 281 tables, live, as I
independently confirmed. The only arithmetic is `SWEEP_SELECTORS+1` / `SWEEP_DIDNOTRUN+1`, integer
counters over selectors. Ledger append-only, holds, `Idempotency-Key`-on-money-POST, the frozen
adapter contract, three-field names, national-ID, time zones, payment rails: **untouched**.
PostgreSQL only — every query I ran went to `fineract-db-1` (`postgres:18.3`) via `psql`; no
Oracle Database, MySQL or MariaDB driver, dialect or port appears anywhere in the diff or in my
own artefacts.

---

## 10. Verdict, and why not REJECTED

**APPROVED.**

Everything T367 asked for is delivered and every load-bearing number reproduces under independent
instruments — several under stronger ones. The F2 repair is genuine, red-driven eight ways, and I
reproduced all eight rows myself with the instrument extracted from git.

**Why not REJECTED.** The strongest case for rejection is **R2**: a fail-open inside the guard
T371 wrote to close a fail-open, which is the precise ground on which T367→T371 was escalated. I
declined it on three measurements, not on charity:

1. **R2 is caught downstream in every realistic failure mode.** An engine broken enough to error
   on the anti-calibration's `git grep … -- .softhouse/` errors on all sixteen selectors too, each
   printing `SELECTOR DID NOT RUN`, and the run exits **4**. R2 bites only in a state where those
   two identical invocations diverge.
2. **R1 and R3 are inherited from `main`; R4 is cosmetic.** Rejecting this branch keeps `main`'s
   *demonstrated* fail-open (drive A2: exit 0 on a search that never ran, for **every** selector,
   on **every** run) in order to avoid a bounded one. That trade is strictly worse for the program.
3. **R2 and R3 both require a control-flow change to a shipped guard**, which by T371's own
   argument — the argument I agree with, and which the driver already endorsed when it declined
   T367's MICRO-FIX # 1 — needs its own red drive. They therefore cannot ride in on a MICRO-FIX,
   and holding a correct repair hostage to them is not proportionate.

**MICRO-FIX offered but not required on merge** (≤ 1 line each, mechanical, no number):
the handoff's *"No file this task touched is read by `conformance.sh`"* (self-contradicted by its
own red drive), and dating `casualty-sweep.sh:191`'s `live 162 / 197` comment the way
`CASUALTIES.md:97` dates it.

### Follow-ups filed

- **FU-T379-1 (MINOR, F3).** Record the margin beside the qualitative claim, or make it
  structurally true. Measured: 197/359, **17 rows** over a bare majority; the most recent 89
  commands are **31 %** refusals; ~35 PROCESSED-only rows, or ~94 at the recent mix, falsify it —
  **silently**, since S12–S16 need a digit and the repair removed the only one at that site.
- **FU-T379-2 (MINOR, F3).** `casualty-sweep.sh:191` types `live 162 / 197` in a live instrument.
  Date it, as `CASUALTIES.md:97` already does. Its own S12 reports it LIVE.
- **FU-T379-3 (MAJOR, F2/R2).** Capture `rc` for both calibration searches before the pipe into
  `awk` and `exit 3` on `rc >= 2`. Today `2>/dev/null` + pipe make a never-run anti-calibration
  print `PASS … matched 0 times across the tracked corpus`. Needs its own red drive.
- **FU-T379-4 (MAJOR, F2/R3).** Add a `-E` calibration pair. 13 of 16 selectors are `-E`; both
  calibrations are `-F`; the header's own justification is a `-E` hazard, and that hazard still
  reproduces on this host — `git grep -E '\bmain\b'` and `git grep -E 'bmainb'` both return **97**.
- **FU-T379-5 (MINOR, F2/R1).** Read the two `$ARCHIVE` greps' statuses in `sel()`. Driven: a
  malformed predicate turns a real hit into `LIVE: 0` at exit 0.
- **Endorsed as written:** FU-T371-1 (annotate `T363.md:30` — see § 8 for why its second
  justification is weaker than stated), FU-T371-2, FU-T371-3 (**agree — do not widen the sweep
  into the dead-path census's territory; a second frontier that can disagree with the gating one
  is worse than none**), FU-T367-1/1b/2/3, FU-T363-1, FU-T363-3.

---

## Artefacts

| file | what it is |
|---|---|
| `sql/r1-classifier.sql`, `out/R1-CLASSIFIER.txt` | my own 3-discriminator classifier, set-equality, F3 split, robustness margin. Read-only. |
| `sql/r2-policy5.sql`, `out/R2-POLICY5.txt` | POLICY § 5 evasions, T371's classifier re-run for set equality, closing max-ids. Read-only. |
| `out/R3-DRIVE-REPRODUCED.txt` | T371's eight-drive fail-open drive, re-run from my worktree, timed |
| `instruments/t379-third-status-drive.sh`, `out/R4-THIRD-STATUS-DRIVE.txt` | my attack: R1, R3, R4 |
| `out/R5-TREND.txt` | refusal share across the command history, for the F3 robustness judgement |
| `out/R6-COST.txt` | sweep timings, per-selector LIVE volume, the ARCHIVE change's 17-line cost |
| `instruments/t379-anticalibration-drive.sh`, `out/R7-ANTICALIBRATION-DRIVE.txt` | R2 driven: the anti-calibration passing on a search that never ran |

Both of my drive instruments extract the code under test **from git** on every run and print its
sha256 (P-22), so neither can silently grade a since-edited working copy.
