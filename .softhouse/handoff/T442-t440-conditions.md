# T442 — T440's six conditions on T424

**Branch** `softhouse/T442-t440-conditions` · **grant** `.softhouse/capture/t424/` (plus this
handoff) · **host** macOS 25.5.0 arm64, `bash 3.2.57(1)`, `git 2.50.1 (Apple Git-155)`,
`/usr/bin/grep` BSD. All scratch under `/tmp` and `$TMPDIR`, never inside the repository.

**Every number below was produced by running something on this host.** Nothing is carried over
from T424's or T440's write-ups without being re-measured, and where a re-measurement contradicts
T440 it says so (that is `F-T442-1`, and it is the most interesting thing in this task).

---

## Disposition, per condition

| # | condition | disposition |
|---|---|---|
| `C-T440-1` | MAJOR — the transcript on `main` records a result the code does not produce | **FIXED and driven RED→GREEN from committed bytes.** Probe assembled at run time; transcript re-captured on a clean detached clone; class swept. |
| `C-T440-2` | MINOR — the K8 decomposition `16+8+6=30` | **RE-MEASURED: `13 + 10 + 6 = 29`.** Confirmed independently of T440's arithmetic, red arm included. Correction **filed, not applied** — the text is in another task's grant. Found a **second** wrong site T440 did not name, and disproved T440's claim that the handoff carries it too. |
| `C-T440-3` | MINOR — `F-T424-N1` is filed nowhere | **FILED, with a re-measurement**, in `capture/t424/FU-T424-N1-FILING.md`. `conformance.sh` **not edited**: `T445` holds it this wave. |
| `C-T440-4` | LOW — the `pipefail` sentence is over-broad | **CLOSED on evidence**, driven against the *shipped block* with only its producer substituted. Narrowed sentence written out; not applied (`casualty-sweep.sh` is not this grant). |
| `C-T440-5` | LOW — exported `T381_DRIVE_INNER` disables the guard | **JUDGED AND CLOSED: it should not be reachable at all.** The patch now makes the marker parent-pid-bound; RED (bypass, exit 0) and GREEN (refused, exit 2) both driven. |
| `C-T440-6` | LOW — `BEFORE_REF=main` "aborts at D-R2 exit 4" | **DOES NOT REPRODUCE HERE — `F-T442-1`.** On the merged tree it aborts **exit 2, "BEFORE and AFTER are the SAME FILE"**, which is what T424 originally wrote. Both accounts are tree-dependent and neither says so. Tree-qualified wording supplied. |

---

## 1 · `C-T440-1` — the repair, and the property that actually failed

**The property that failed was not "the drive passes". It was "the record reproduces from
committed bytes on a clean checkout that is not the author's worktree."** So that is what was
tested, twice.

```
RED    .softhouse/capture/t424/out/T442-C1-RED.txt
       shipped instrument, committed bytes, clean detached clone at b102875c, 0 dirty paths
       -> no match rc=0 ... T424-COMMENT-CLAIMS-RESULT: disagreements=1 ... ACTUAL EXIT=1

GREEN  .softhouse/capture/t424/out/T424-comment-claims.txt   (re-captured, replaces the old one)
       -> T424-COMMENT-CLAIMS-RESULT: disagreements=0 ... ACTUAL EXIT=0

BOTH   .softhouse/capture/t424/out/T442-C1-REPRODUCTION.txt
       instruments/t442-c1-reproduction-drive.sh
       ARM A green from committed bytes; ARM B red with the defect RE-INJECTED AND COMMITTED
       -> T442-C1-REPRODUCTION-RESULT: disagreements=0
```

**The repair.** CLAIM 3's probe is built at run time from the pid, `$RANDOM` and the epoch second,
so no byte sequence equal to it exists in any tracked file at any commit. **It was not respelled
in pieces to slip past `git grep`** — that hides the control from the census instead of repairing
it. Three arms were added and are graded:

* the probe must be absent from the **whole repository**, not merely from `.softhouse`;
* the probe must **not appear in the instrument's own source** — this is the C-T440-1 regression
  check, and it is the arm that fires if anyone hard-codes the token back;
* a literal that *is* in tracked source is searched and **shown to return 0**, so the reader
  watches the inversion happen instead of being told about it.

**ARM B is itself exposed to the bug it tests for, and that is handled.** Had the specimen token
been spelled literally in the reproduction drive, `git grep` would find it whether or not the
injection landed and the red arm would pass vacuously — the fail-open half of this very class. So
the specimen token is assembled at run time too, and the drive **proves** it is absent from the
real repository and present in the specimen clone before drawing any conclusion from ARM B.

**Byte-reproducibility is deliberately not claimed.** The probe is a nonce, so the transcript
differs every run — which is exactly why no tracked file can contain it. What reproduces is the
verdict, and `t442-c1-reproduction-drive.sh` is the machine check for that.

### The class sweep

Instrument `instruments/t442-selfmatching-probe-census.py`, transcript `out/T442-CLASS-SWEEP.txt`,
adjudication `out/T442-CLASS-SWEEP-ADJUDICATION.md`.

```
T442-CLASS-SWEEP-RESULT: scripts=1704 searches=399 self_only=2 self_only_files=2
                         self_plus_others=33 family_only=3 unparsed=23 runtime=131
                         immunised=0 elsewhere=233
```

**Adjudicated: 4 instruments spell a self-matching probe that changes what their search reports.
All 4 invert. All 4 invert FAIL-CLOSED. 0 invert fail-OPEN.**

1. `capture/t424/…/t424-comment-claims-drive.sh` — **repaired here**.
2. `reviews/t379-review-t371/instruments/t379-anticalibration-drive.sh:49,51` — probe
   `zzq-t379-nothing`, measured **rc=0**, sole matching file is the drive itself. Its legend says
   `1 == a MEASURED zero`; it prints 0.
3. `reviews/t367-review-t363/drive-sweep-failopen.sh:34,44` — arm **B**, captioned *"a selector
   that IS valid and genuinely finds nothing"*, measured **rc=0**, two matching files: the drive
   and its own transcript.
4. `reviews/t245-oracle-pin/measure.sh:131` — `CALIB negative 'zzq_nonexistent'`, a line whose job
   is to print **0**, prints **5**.

None of the three is this task's grant; all three are recorded above and in the adjudication with
their measurements, for filing.

**The fail-OPEN hunt, and where I looked.** The dangerous direction is a *present*-assertion
satisfied by the searcher's own bytes: it passes vacuously and says nothing about the corpus. I
looked for it three ways — every `A1` row (searcher is the sole carrier, so a present-assertion
there is vacuous by construction); a mechanical **FAMILY-ONLY** flag (every match inside the
searcher's own task directory — the "confirmed by my own artefacts" shape), which produced 3 rows;
and by hand over all 33 `A2` rows. **Zero found.** That is a statement about this search: it saw
only tracked files under `.softhouse/`, only grep-family calls in command position, and its named
blind spots are continuation lines, patterns held in variables assigned from a literal earlier
(131 rows counted safe, some may not be), run-time pathspecs, `find -exec grep`, non-script
searchers, and helper-function searches. 23 lines could not be tokenised and are **listed by name**
in the transcript rather than dropped.

**`immunised = 0`** — nobody dodges the self-match by excluding themselves from their own pathspec.
That is the *wrong* repair (it un-scans everything else under the excluded path) and it is worth
recording that nobody has done it, so the next reviewer can tell that from "nobody looked".

---

## 2 · `C-T440-2` — the K8 decomposition

Drive `instruments/t442-k8-decomposition.sh`, transcript `out/T442-K8-DECOMPOSITION.txt`,
erratum with paste-ready replacement text: `capture/t424/ERRATUM-K8-DECOMPOSITION.md`.

```
GREEN (measured 13/10/6)          T442-K8-DECOMPOSITION-RESULT: disagreements=0, exit 0
RED   (T442_K8_PUBLISHED=1, 16/8/6=30)  disagreements=3, exit 1
      sel rows           expected=16 actual=13   *** DRIVE DISAGREES
      SWEEP counter rows expected=8  actual=10   *** DRIVE DISAGREES
      partition total    expected=30 actual=29   *** DRIVE DISAGREES
```

Confirms T440's 13 / 10 / 6, derived independently from the census transcript by pattern. Two
things T440 did not have:

* **the `16` has an explanation and it is measured** — there really are 16 `sel` calls in
  `casualty-sweep.sh`, but `S1`, `S3`, `S7` use `-F` patterns with no `|`, so 16 − 3 = 13 reach the
  wide K8 list. 16 counted the *file*; 13 is the count *in the census*.
* **the `8` has none, and it is wrong in two places.** Measured: `SWEEP_*=$((…))` lines today =
  **10**; distinct counter variables = **3**; the same lines at `8fa677a6` (last commit before
  T402) = **3**. So 8 is neither end of the history nor the variable count. `AUDIT-CLASS.md:102`
  carries the same `×8` under `K1+K7` and is also wrong.
* **T440's "and the handoff" is not right.** `git grep 'all sixteen'` over `.softhouse/handoff/`
  returns only unrelated T39/T242/T379 matches; `T424-t408-conditions.md` states the total 29
  without decomposing it. **One** site to correct, not two.

Not applied: `AUDIT-CLASS.md` is in `capture/t402-t386-conditions/`, outside this grant.

---

## 3 · `C-T440-3` — `F-T424-N1` filed

`capture/t424/FU-T424-N1-FILING.md`. Re-measured at `97bad8ed`, running the sentence's own recipe:

| recipe as the comment gives it | it says | **today** |
|---|---|---|
| `LC_ALL=C grep -c 'CONFORMANCE_REPO_ROOT' conformance.sh` | 0, exit 1 | **22**, exit 0 |
| same, executable lines only | 0 | **16** |
| `LC_ALL=C grep -c -- '-repo-root' conformance.sh` | 0, exit 1 | **2**, exit 0 |
| same, executable lines only | 0 | **0** |

Cause right, **tense** wrong: the paragraph describes the pre-`T201` hole and `T201`'s repair is
what made it false. The filing carries the defect, the evidence, a past-tense replacement
sentence, and an acceptance test — including the trap that `t424-comment-claims-drive.sh`'s
CLAIM 2 **locates that paragraph by the anchor `each occur ZERO times in it`** and will REFUSE
(exit 2) if the phrase is deleted without updating the anchor in the same commit.

**Contention re-checked, not assumed.** `T431` is `merged`, so it no longer holds the region;
**`T445` is `in_progress` on `softhouse/T445-case-route` with `conformance.sh` in its
`files_hint`** [VERIFIED: `.softhouse/tasks.json`]. So the region is *still* not free, and T424's
original decision not to edit it remains right. **I did not edit `conformance.sh`.**

`FU-T424-*` / `F-T424-*` still appears in `tasks.json` exactly **2** times, both inside T442's own
description, and **0** times in `obligations.md` and `gates.md`. `tasks.json` is outside this
grant, so **the driver still has to paste this into the backlog** — the filing file is written so
that is a paste, not an investigation.

---

## 4 · `C-T440-4/5/6`

Drive `instruments/t442-t440-lows-drive.sh`, transcript `out/T442-T440-LOWS.txt`,
`T442-LOWS-RESULT: disagreements=0`, exit 0.

### `C-T440-4` — closed, sentence narrowed (filed, not applied)

Driven against the **shipped block**, extracted by content from `casualty-sweep.sh` with only its
producer substituted:

```
ARM 1  producer fails 128 AFTER emitting 3 lines -> captured=[3] rc=128
       shipped block exits 2: "the corpus COUNT DID NOT RUN (rc=128)"   <- MISATTRIBUTION
ARM 2  producer fails 128 with NO output         -> captured=[0] rc=1
       shipped block exits 2 on the VALUE test: "tracks ZERO files"     <- correct
ARM 3  the COUNT itself fails (grep rc>=2)       -> captured=[] rc=2    <- what the message is for
```

The sentence is true **only** in the no-output case. Fail-CLOSED, so not a hole — but it is a
message naming the wrong cause one line below a comment that exists to correct a message naming
the wrong cause. The narrowed replacement is printed verbatim in the transcript.

### `C-T440-5` — judged: the marker should not be reachable from the environment at all

**Established by grep first: the amended guard is NOT applied to the live instrument.**
`T381_DRIVE_INNER` occurs **0** times in `capture/t381-t379-conditions/instruments/t381-red-drives.sh`
and **5** times in the patch. It ships as a *proposed* patch, so nothing that runs today is
affected either way — which is precisely when the surface is cheapest to close.

The patch `patches/FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch` now carries the
repair: the outer publishes `T381_DRIVE_INNER="t424-inner:$$"`, and the inner **refuses unless the
marker names its own `$PPID`**. Every other value is exit 2 — fail-CLOSED where the old shape
failed open. Driven, with the guard text taken from the patch's own preamble hunk and the *red*
arm reconstructed by reversing the repair (`instruments/t442-unrepair-guard.py`, which refuses if
the reversal changed nothing):

```
RED   normal invocation, failing arm : exit 1     T381_DRIVE_INNER=1 : exit 0   <- bypassed
GREEN normal invocation, failing arm : exit 1     T381_DRIVE_INNER=1 : exit 2   <- REFUSED
      forged "t424-inner:1"          : exit 2     HEALTHY CONTROL (clean body)  : exit 0
```

The healthy control matters: a guard that refuses everything grades nothing either.

### `C-T440-6` — **`F-T442-1`: the condition does not reproduce, and T424 was right here**

Measured on the tree I have, not taken from either account:

```
blob of casualty-sweep.sh at main : b7893bd0…   at HEAD : b7893bd0…   SAME
BEFORE_REF=main       -> exit 2   "DRIVE ABORT (exit 2): BEFORE and AFTER are the SAME FILE."
                                  never reaches D-R2
BEFORE_REF=964b532e   -> exit 4   "D-R2 patch: expected 1 anti-calibration search line in
                                   BEFORE, found 0"
```

T424 wrote *"refuses (BEFORE and AFTER are the same file)"* — **true on the merged tree**. T440
corrected it to *"aborts at D-R2, exit 4"* — **true on a tree where the two refs carry different
copies of the subject**, which is reproduced here with `BEFORE_REF=964b532e`. Neither sentence is
wrong; **both are tree-dependent and neither says so**, which is the same defect as `F-T424-N1`
(a present-tense measurement carrying its own recipe) and as `C-T440-1` itself. The tree-qualified
replacement wording is in the transcript. The substantive claim — the drive cannot be run to
completion on any available ref, so `FU-T386-7`'s guard has nothing to grade yet — **stands.**

---

## P-45 — what automatic path invokes any of this

**Established by grep, and the answer is: nothing.**
`git grep` for `t424-comment-claims-drive|t442-*|t424-neighbour-census|t424-f2-true-cause|
t424-k8-discrimination|t424-buffered-writer-drive` outside `capture/t424/` and `reviews/t440*`
returns only **prose** references — `AUDIT-CLASS.md`, `T402`/`T424` handoffs, `casualty-sweep.sh`'s
comments, and `tasks.json`. **`conformance.sh` invokes none of them.** These are evidence
instruments, not guards, and they are not claimed to be guards. What *does* reach them
automatically is the bar's own censuses, which walk tracked `.sh`/`.py` under `.softhouse/` and
carry pinned frontier counts — so the five new scripts added here (`t442-c1-reproduction-drive.sh`,
`t442-selfmatching-probe-census.py`, `t442-k8-decomposition.sh`, `t442-t440-lows-drive.sh`,
`t442-unrepair-guard.py`) are inside a corpus the bar measures, and the bar was run to confirm
they move nothing (below). **Wiring any of these into
`conformance.sh` is not possible this wave: `T445` holds that file.**

## The bar

Run with `bash`, never `sh`/`zsh`; scratch in `/tmp`, outside the repository. Twice on committed
trees — `65f384a0` and the finished tree `34e1382e` — with identical results:

```
grep -c 'probe = ' → 1          (PRESENCE tested before the value was read: four exit-2 paths
                                 run before the probe prints, so absence would not have been 'down')
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
all 16 wrong ledger implementations DIED through this harness, not by hand.
BAR EXIT=0
```

No money path, no vector, no schedule figure is touched by this branch; the diff is instruments,
transcripts and prose under `capture/t424/`, plus one patch artefact and this handoff.

## What I could not close

* **`AUDIT-CLASS.md` (C-T440-2) and `casualty-sweep.sh` (C-T440-4) are not corrected**, and
  `conformance.sh` (C-T440-3) is not corrected. All three are outside this grant; `conformance.sh`
  is additionally held by `T445`. Each has a paste-ready replacement text and an acceptance test.
* **`FU-T424-N1` is still not in `tasks.json`.** I cannot put it there; the driver must.
* **The three other members of the class** (`t379`, `t367`, `t245`) are measured and named but not
  repaired — each lives in another task's directory.
* **This file's sibling marker keeps a filename that is now false** —
  `out/T424-comment-claims.TRANSCRIPT-IS-NOT-REPRODUCIBLE.md`. It is banner-corrected inside, and
  kept at that path because `tasks.json` and the driver's merge note both reference it. Renaming
  it is a one-line follow-up for whoever can touch `tasks.json` in the same commit.
* **GNU `tee` remains `[UNVERIFIED]`.** There is no GNU `tee` on this host and I did not claim
  otherwise.
* **The census's 131 "runtime" rows are counted safe on syntax alone.** A pattern held in a
  variable that was assigned from a literal earlier in the same file would land there and would
  still be in the class. Closing that needs dataflow, not a regex; it is the sweep's largest
  residual and it is named in the transcript rather than left implicit.
