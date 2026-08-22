# T185 — independent review of T175 (`softhouse/T175-python-swallow-sites`)

Run `2026-08-21-run2-tierA-gl-accounting-A2`. Reviewer fork point: `1672d85` (`git merge-base HEAD
main` = `1672d857f42c7bfe20beec2c8f07e62484c7b469` = `HEAD`; branch `softhouse/T185-review-t175`).

## VERDICT — **APPROVED**

The question this review exists to answer — *do the de-vacuumed checks NOW FAIL on the inputs they
used to SWALLOW?* — is **YES, proven by construction on 16 input classes that T175 did not sweep**,
with **zero silent acceptances**. Three real findings are registered below as follow-ups; none of
them makes a de-vacuumed check vacuous and none falsifies a committed number.

---

## P-59 — which diff form I used, and why

`git diff main...softhouse/T175-python-swallow-sites` (three dots) returns **0 lines** and reads
clean. It is the trap. `git merge-base --is-ancestor softhouse/T175-python-swallow-sites main`
returns true — T175 is fully merged, so `git merge-base main T175` **is the T175 tip itself**
(`fecea5f`) and the symmetric-difference diff is empty by construction.

**Two forms used, and they agree:**

| form | result |
|---|---|
| `git diff --stat dfa1bfa..fecea5f` (fork point `..` branch tip, two dots) | **19 files, 2,437 insertions, 2,551 diff lines** |
| `git show -m --stat 0c35634` (merge commit, second parent) | same 19 files / 2,437 insertions |

`dfa1bfa` is the dispatch commit named as the fork point in T175's own handoff, and is the parent of
the branch's six commits.

**A structural fact the diffstat states and the review must not miss: the change is `A` on every
line — 2,437 insertions, ZERO deletions, ZERO modifications.** T175 removed no swallow site. It
shipped *successors* alongside the originals and left the originals byte-identical, which is the
correct reading of T114's ruling (do not edit scripts that produced committed evidence), and which I
verified independently: `git status --porcelain` is empty in my tree after running every probe
below, and the committed `t55-analyse.py` sha256 is unchanged.

---

## 1. THE CENTRAL QUESTION — driven RED by me, not by T175 (P-22, P-50)

I did not accept T175's probes as the proof. I re-ran them for reproduction, then wrote my own
adversarial drivers over input classes T175 **explicitly listed as "not swept, and therefore not
claimed"**. Probes and transcripts are committed under `.softhouse/reviews/t185-probe/`.

### 1a. Reproduction leg (T175's own probes, re-run in my worktree)

| probe | exit | result |
|---|---:|---|
| `capture/audit-t44/analysis/T175-red/drive-red.sh` | **0** | 18 `AS PREDICTED`, **0** `NOT AS PREDICTED`; transcript **byte-identical** to the committed `drive-red-output.txt` (`diff` = 0 lines) |
| `capture/leapboundary/analysis/T175-red/drive-red.sh` | **0** | 0 `NOT AS PREDICTED`; transcript differs from the committed one **only in worktree and mktemp path strings** (24 diff lines, all paths); `t55-analyse.py` sha256 identical before and after |

### 1b. `t55-invariants-v2.py` — my own plants, including every shape T175 disclaimed

`.softhouse/reviews/t185-probe/probe-t55-successor.py`. Scratch corpora via `mktemp`; the committed
corpus is copied, never written. The ORIGINAL is exercised by calling its `invariants()` **in
process with `OUT` redirected** — never its `main()`, because `main()` calls `sidecars()` which
**writes `../out/*-exact.json`**, and `t55-analyse.py` has **no output-dir env override** (only
`T55_NEG_PREC` / `T55_NEG_ROUND` / `T55_NEG_DOCTOR`). Running its `main()` would have been a write
to committed evidence.

**P-50 other half first:** clean copy of the committed corpus → successor **exit 0**, and reproduces
T175's published figures exactly: **33 of 33 captures, 1,236 money cells inspected, 212 money deltas
considered, 0 swallowed.**

| plant into `LB-LEAPIN-p7.totalRepaymentExpected` | ORIGINAL | SUCCESSOR |
|---|---|---|
| `"1200000.000"` (parseable 3 dp — T175's control) | I6 **VIOLATED** | exit 1, VIOLATED |
| `"1,200,000.000"` (T175's own plant) | **I6 `ok`** | exit 1, VIOLATED + 3 swallows named |
| **`""` empty string** *(disclaimed by T175)* | **I6 `ok`** | exit 1, VIOLATED + 3 swallows named |
| **`"null"` the string** *(disclaimed)* | **I6 `ok`** | exit 1, VIOLATED + 3 swallows named |
| **`"−1200000.00"` U+2212 minus** *(disclaimed)* | **I6 `ok`** | exit 1, VIOLATED + 3 swallows named |
| **`"1\xa0200\xa0000.000"` NBSP separators** | **I6 `ok`** | exit 1, VIOLATED + 3 swallows named |
| `"１２０００００.０００"` full-width digits | I6 VIOLATED | exit 1, VIOLATED |
| **bare JSON number `1200000.000`** (`cells()` class) | **I6 `ok`** | exit 1, "1 MONEYISH leaf dropped by `cells()` … the denominator shrank invisibly" |
| **JSON `null`** (`cells()` class) | **I6 `ok`** | exit 1, same |
| **nested object** (`cells()` class) | **I6 `ok`** | exit 1, same |
| `"1.200000000E+6"` Decimal-legal exponent 3 dp | I6 VIOLATED | exit 1, VIOLATED |

**11 of 11 caught by the successor. The original silently answered `I6 ok` on 7 of the 11.**
Every one of those 7 is a real breach of the MNT minor-unit rule that the merged instrument
reported as clean.

### 1c. `t44_float_roundtrip_v2.py` — my own inputs

`.softhouse/reviews/t185-probe/probe-t44-successor.sh`.

| input class | successor exit | named? |
|---|---:|---|
| valid JSON, **zero bare float literals** (P-35 empty sample) | **1** | yes |
| **unreadable file** (`chmod 000`) | **1** | yes — `PermissionError` printed with the path |
| **a directory** matching the glob | **1** | yes |
| **UTF-16 / binary** file | **1** | yes — `UnicodeDecodeError` printed with the path |
| a **VALUE-lossy** money literal | **0 — `PASS`** | detector fires and prints, but see F-1 |

Four of five classes fail loud and name the input. The fifth is finding F-1.

### 1d. P-35 / T194 — are the counts read as VALUES, not presence?

**Yes.** T175's `drive-red.sh` extracts numbers and compares them, e.g.

```
check "SUCCESSOR skip count there" "0" \
      "$(sed -n 's/.*files SKIPPED *: *\([0-9]*\).*/\1/p' "$SCRATCH/succ-clean.txt")"
```

It does not test for the presence of a line. A stub printing `0/0/0` cannot pass it: the counts are
cross-checked against an independently computed `census.py --count-unparseable`, and LEG 5 proves
the acknowledgement path is itself falsifiable (`--expect-skips 18` → 0, `--expect-skips 17` → 1).
Zero-inspected is an error in both successors, and I drove that leg myself (1c row 1, and the t55
empty-corpus leg).

### 1e. P-58 / P-33 — tool identity for every claim above

- `grep` at my shell is a **function** (`/Users/buv/.claude/shell-snapshots/snapshot-zsh-…`).
  It is **NOT exported** — `bash -c 'declare -F grep'` reports `NOT-EXPORTED` — so every bare
  `grep` inside `drive-red.sh` invoked as `bash <file>` resolves to **`/usr/bin/grep`, BSD grep
  2.6.0-FreeBSD**. One program, deterministic; the `\|` BRE alternation in its LEG 1 count is BSD
  syntax and behaves. No ugrep is involved in any T175 probe leg.
- Every measurement of my own that greps uses `/usr/bin/grep` explicitly, or `python3` AST.
- `python3` = `/usr/bin/python3`, **3.9.6** (Clang 21.0.0). Locale `LANG=C.UTF-8`,
  `LC_COLLATE=C.UTF-8`; all sorts forced with `LC_ALL=C`.

---

## 2. MY OWN SWEEP (P-37) — and an honest negative

A reviewer's site list is a starting point, never the sweep. I wrote an **independent** AST
classifier (`.softhouse/reviews/t185-probe/t185-independent-sweep.py`) from the definition, without
reading T175's `census.py`, and ran it **at T175's own tip `fecea5f`** for an apples-to-apples
comparison.

| | T175's census | T185's independent sweep |
|---|---:|---:|
| `.py` files walked | 353 | **353** |
| files unreadable / unparseable | 0 / 0 | **0 / 0** |
| `except` handlers seen | 87 | **87** |
| classified SWALLOW | 29 | 37 |

**The denominators reproduce exactly under an independently written instrument.** My 37 is a strict
superset of T175's 29 — `comm -13` is empty, so T175 classified nothing as a swallow that I do not.

**The 8 extra sites are a definitional difference, not 8 missed defects.** I hand-read all eight;
every one assigns a **visible sentinel that is returned or printed downstream**, so nothing is
silent:

| site | handler body | why it is not silent |
|---|---|---|
| `capture/tierA-a2/prove-resolve8-float-red.py:217` | `residue = None` | next statement is `check(…, residue == 0, "residue = %s" % residue)` — **fails closed and prints** |
| `capture/mathcontext/analysis/t46_assert_pathb_slot.py:144` | `mc_index = None` | carried into the record as `"mc_arg_position": mc_index` |
| `capture/pathb/t149/prove-exit-trap.py:174` | `timed_out = True; rc = None` | both returned in the result dict |
| `capture/pathb/t80/prove-f1-recovery.py:235` | `hung = True; rc = None` | both returned |
| `reviews/T158-bash-signal-semantics.py:16` | `rc = "TIMEOUT"` | printed |
| `reviews/T158-drive-t156-refusals.py:88` | `rc = "TIMEOUT"` | returned and printed |
| `reviews/T158-drive-untrapped-signals.py:43,57` | `rc = "TIMEOUT"` | printed |

**Sites T175 missed, by T175's own stated definition: ZERO.** This is an honest negative and it is
the single strongest thing in T175's favour — its census survived re-derivation by a differently
written tool.

**Sites that appeared on `main` AFTER T175's tip (not T175's):** 3, all in
`.softhouse/reviews/t179-guard-classifier/guard_classify.py` at `:201`, `:820`, `:1025` — **T179's
file**, merged later in this fire. Registered for whoever owns T179's output, not chargeable here.

**NET 2 — the class T175 named as its largest blind spot** (a silent narrowing with no `except` at
all). My net flagged **240** candidate `if …: continue` narrowings inside money-ish loops across 389
files. That net is **over-broad** and I do not present the number as a finding — it is an upper
bound, and converting it into a site list needs a targeted read that is a task, not a review leg.
T175 enumerated exactly one instance by hand (`t55-prior-capture-assessment.py:97`) and correctly
said no AST net over `except` can close the class. **I could not close it either.**

---

## 3. FINDINGS

### F-1 — [MEDIUM] `t44_float_roundtrip_v2.py` prints `PASS` and exits 0 on a money literal that IS corrupted by the float round-trip

Demonstrated by construction (`probe-t44-successor.sh`, leg A1). Input
`{"amount": 0.1234567890123456789, "other": 1.5}`:

```
  literals whose float VALUE != the decimal : 1 of 2
  VALUE-lossy examples:
T175 SUCCESSOR: PASS -- 1 of 1 files scanned, 0 skipped, 2 distinct literals inspected.
exit=0
```

The `lossy_value` detector **is not vacuous — it fires**, which is the P-50 half that matters most
and which T175 never demonstrated (its LEG 4 only shows the detector reproducing a **zero**). But
`lossy_value` is never appended to `failures`, so the run is reported **PASS**. The headline claim
built on this instrument is *"0 of 245 change VALUE … so no committed charges number is corrupted"*;
a reader who runs this tool and sees `PASS` will read it as that claim holding.

The original had no PASS/FAIL banner at all, so the misleading verdict surface is **new in the
successor**.

**Why I did not call this a MICRO-FIX**, though it is two lines and is behaviour-preserving on every
committed corpus (all of which measure 0 VALUE-lossy): the file carries an explicit, reasoned design
statement — `# HAZARD CHARACTERISATION ONLY - these floats never touch a verdict.` — and the whole
point of that line is P-25 compliance. Putting `lossy_value` on the verdict path deliberately
contradicts it and puts a float-derived predicate on a verdict. That is a design decision for the
next owner to make consciously, not a mechanical repair for a reviewer to impose. **Registered as a
follow-up with the tension stated, so the decision is made rather than inherited.**

### F-2 — [MEDIUM] T175 ADDED 8 `json.load` call sites with no `parse_float=`, enlarging the exposure T145 owns

Measured with an AST walk over three trees (`.softhouse/reviews/t185-probe/` methodology, `ast`,
python 3.9.6):

| tree | `.py` files | `json.load(s)` call sites | **call sites with NO `parse_float=`** | files with ≥1 such call |
|---|---:|---:|---:|---:|
| `dfa1bfa` (T175 fork point) | 344 | 302 | **193** | 103 |
| `fecea5f` (T175 tip) | 353 | 312 | **201** | 107 |
| `HEAD` / `main` today | 389 | 323 | **211** | 114 |

T175's own new files account for the `193 → 201` move. Of its ten new call sites, **8 lack
`parse_float`**:

```
T175-red/census.py:26, :36
T175-red/field-census.py:50, :70, :77
T175-red/measure-other-sites.py:85, :86
T175-red/plant.py:74
```

Its two **deliverable** call sites are correct — `t44_float_roundtrip_v2.py:111` uses
`parse_float=make_hook(p)` and the hook `return Decimal(s)  # NEVER a float on the recording path`,
and `measure-other-sites.py:42` uses `parse_float=str, parse_int=str`. The author plainly knows the
idiom; it was applied in the deliverables and not in the probe tooling in the same file.

The two that matter are `measure-other-sites.py:85-86`, `A = m.cells(json.load(open(fa)))` — these
sit on the money-delta path that produced T175's committed claim of **12 of 12 pairs / 772 money
deltas / 0 swallowed**.

### F-3 — [LOW-MEDIUM] `measure-other-sites.py` omits the very drop-counter T175 invented for `t55-invariants-v2.py`

`cells()` keeps only `str`/`bool` leaves. Fed by a `json.load` with no `parse_float` (F-2), a bare
JSON money number becomes a binary double and is dropped **before** the delta loop. T175 identified
this narrowing, instrumented it in `t55-invariants-v2.py` as *"MONEYISH leaves dropped by `cells()`
before I6"*, made it a hard failure — and did **not** carry it into the tool that published the 772
figure, which has no drop counter at all.

I measured it (`measure-cells-drop.py`, transcript committed):

```
files inspected                                  : 12
TRUE MONEYISH leaves in the corpus               : 1554
leaves cells() actually hands to the delta loop  : 1554
SILENTLY DROPPED before any delta is computed    : 0
files containing at least one BARE JSON NUMBER   : 0 of 12
```

**The published figure is not understated.** It holds because every money cell in that corpus
happens to be a JSON string — *by luck of the corpus, not by check*. That is verbatim the diagnosis
T175 itself applied to the 18 unscanned `-raw.json` files ("It held by luck, not by test"), now
applying to T175's own tool.

### F-4 — [INFO] the successors are wired to nothing

`t55-invariants-v2.py` and `t44_float_roundtrip_v2.py` are referenced only by their own
`T175-SUPERSEDES.md`, their own red probes and the handoff. No harness, no CI, no `conformance.sh`
entry drives them. Nothing re-runs on a schedule, so the next drift is detected only if a human
remembers. Not chargeable to T175 — `conformance.sh` is held by T201 this fire — but it is the gap
between "a correct instrument exists" and "a correct instrument runs".

### F-5 — [INFO] T175's `SUPERSEDES` markers are documentation, not enforcement

The originals remain executable and importable, with the swallow at `t55-analyse.py:352` intact.
Correct under T114, but the only thing stopping the next author re-running the vacuous instrument is
reading a README. A note, not a defect.

---

## 4. RE-MEASURED NUMBER FOR T145 (the adjacent live exposure)

T134 recorded **74 of 240** `.py` files under `.softhouse/` calling `json.load` with no
`parse_float=`. **That denominator no longer exists** — the tree is now 389 `.py` files.

**Re-measured on `main` at `1672d85`, AST (python 3.9.6), 0 files unparseable, 0 unreadable:**

| measure | today |
|---|---:|
| `.py` files walked under `.softhouse/` | **389** |
| `json.load` / `json.loads` **call sites** | **323** |
| …**call sites with NO `parse_float=`** | **211** |
| files containing ≥1 `json.load` call | **184** |
| **files with ≥1 call lacking `parse_float`** | **114** |

**T145 should start from 211 call sites in 114 files, not 74 files.** Two programs counted (P-33):
`/usr/bin/grep -la 'json\.load'` reports **192** files, AST reports **184**; the 8-file delta is
`json.load` appearing in comments and docstrings, and the AST number is the correct one.

**Did T175 move it?** Yes, upward: `193 → 201` call sites lacking `parse_float` (F-2). The remaining
`201 → 211` came from other branches merged later in this fire.

**T134's worst instance is unrepaired and unchanged.**
`.softhouse/capture/actualactual/analysis/discriminate.py:160` still decides a money claim by binary
float equality —

```
            if [float(g) for g in got] != [float(w) for w in want]:
```

— and still prints `"ALL %d PERIODS REPRODUCED DIGIT FOR DIGIT"`. Its loader at `:28` is
`return json.load(fh)` with no `parse_float`. T175 neither touched nor worsened it.

---

## 5. STANDING-RULE CHECKS

- **Vector store.** 50 `.json` files, matching the stated count. Git tree object for
  `.softhouse/vectors` = `ce821c638724237652b6b29627148d34b72fab3b`; `git diff main -- .softhouse/vectors`
  is empty, and `git diff dfa1bfa..fecea5f -- .softhouse/vectors` is empty — **T175 touched no
  vector**, and neither did I. `git status --porcelain` empty after every probe.
  **I could not reproduce the digest `5d03795b6042…`**: it appears **nowhere in the repo** (`grep -rla`
  across the tree, excluding `.git`, returns no file), so no recipe is recorded, and the two natural
  recipes give `b22ea986…` (sha256 of the sorted per-file hash list) and `f162ba20…` (sha256 of
  sorted concatenated content). The file count matches and git proves byte-identity, so I record the
  digest as **unreproducible-as-stated, not as moved**. Stating the recipe alongside the digest would
  close this.
- **No promote/rewriter script executed.** Every probe ran from `/tmp` scratch copies or wrote only
  into `mktemp -d`.
- `conformance.sh`, `bin/fire-program.sh`, `handoff/*promote-vectors.py`, `.softhouse/vectors/`,
  `nexus/` — **not touched**. No `gofmt`. No Go code involved.
- Harness invoked with `bash`, never `sh`. **Oracle not contacted and not needed** — both originals
  and both successors read only committed bytes; there is no exit-2 / probe-line condition to test
  here, and I assert none.

## 6. WHAT I COULD NOT CLOSE

- **The no-`except` swallow class.** 240 candidate narrowings under an admittedly over-broad net;
  neither T175 nor I converted it to a site list. It remains the largest open blind spot.
- **Whether the 22 sites T175 called "not load-bearing" really are.** T175 hand-read them and built
  no red probe for any; I hand-read the 8 in my superset and spot-checked others, but I did not
  build 22 probes either. Both of us are asserting from a read.
- **The historical question** — whether the swallows dropped anything on the day the committed
  outputs were produced. T175 marked it unrecoverable and I agree: a dropped file leaves no trace.
- **The frozen-digest recipe** (above).
- **Non-Python swallows** (bash `|| true`, `2>/dev/null`, Go `_ =`): out of my time budget and out of
  T175's stated scope; unmeasured, and I claim nothing about them.
