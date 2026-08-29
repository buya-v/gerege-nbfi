# T466 — T459's two MAJORs on T454. Re-derived, driven, closed where closable, declared open where not.

Branch `softhouse/T466-skipwt-smudge`. Scope held: `.softhouse/conformance.sh` and
`.softhouse/capture/t466-t459-conditions/`. `tasks.json`, `LOCK`, `RESUME.md`, `program.json`,
`patterns.md` and the `.pin` files were **not** touched — see "the pins I nearly rotted" below,
which is the one place that nearly went wrong.

Every number here was measured by an instrument in `.softhouse/capture/t466-t459-conditions/instruments/`
and its transcript is in `../evidence/`. Nothing is inherited from T454 or T459; where I agree
with T459 I say so, and where I do not I say that too.

---

## 1. WHAT I MEASURED

### 1a. The fold census — `instruments/fold-census.py`, `evidence/01-fold-census.txt`

T454's `fold_candidates()` kept a candidate only `if len(f) == 1`, which excludes every
multi-character fold **by construction**. I wrote my own probe that keeps multi-character images,
and it measures three things per candidate rather than assuming any of them: the fold (python
`lower`/`casefold`/NFKD), the **byte order** (git orders index entries by `memcmp`, so the winner
of a checkout collision is the entry that sorts LAST), and the **collision itself**, by writing
both spellings into one fresh directory on this volume and reading back which survived. It
calibrates on U+017F and runs a negative control (`aardvark.sh` vs `zebra.sh`) before reporting
any number.

**The set — quoted as a set, not as a cardinal:**

| codepoint | name | ASCII image | live tracked targets |
|---|---|---|---|
| U+017F | LATIN SMALL LETTER LONG S | `s` | 10345 |
| U+037E | GREEK QUESTION MARK | `;` | **0** |
| U+1FEF | GREEK VARIA | `` ` `` | **0** |
| U+212A | KELVIN SIGN | `k` | 812 |
| U+00DF | LATIN SMALL LETTER SHARP S | `ss` | 837 |
| U+1E9E | LATIN CAPITAL LETTER SHARP S | `ss` | 837 |
| U+FB00 | LATIN SMALL LIGATURE FF | `ff` | 720 |
| U+FB01 | LATIN SMALL LIGATURE FI | `fi` | 666 |
| U+FB02 | LATIN SMALL LIGATURE FL | `fl` | 174 |
| U+FB03 | LATIN SMALL LIGATURE FFI | `ffi` | 23 |
| U+FB04 | LATIN SMALL LIGATURE FFL | `ffl` | 4 |
| U+FB05 | LATIN SMALL LIGATURE LONG S T | `st` | 2889 |
| U+FB06 | LATIN SMALL LIGATURE ST | `st` | 2889 |

Thirteen members, of which nine have a multi-character image and eleven have at least one live
tracked target. **T459's correction reproduces exactly, member for member.** T454's four are the
four single-character rows and are a strict subset — its selector was not wrong about what it
measured, it measured the wrong population.

**U+FB01 has the live target T459 named, and I confirmed it: `.softhouse/bin/fire-program.sh`
carries `fi`, and that file is a DECLARED WITNESS in this harness's own DECLARATION TABLE** — the
thing `guard_guards_dir_registration` trusts when it absolves `repo-state-attest.sh`.

Two members — `;` and `` ` `` — have **no tracked target today**. I report that separately rather
than folding it into the headline, because "no path spells it in this repository this week" is a
fact about our file names, not a closed route.

My candidate generation before the filesystem probe was 1401 (1091 single-image, 310 multi),
where T459 got 1380/1090 and T454 got 1075. Three probes, three generation counts, **one
confirmed set** — which is the argument for filtering on the filesystem rather than on the table.

### 1b. The read census — `instruments/read-census.py`, `evidence/02-read-census.txt`

The shipped sentence said "27 executable sites in this file that touch this host's filesystem at
a `$REPO_ROOT` path, and 26 of them … foldable". T459 measured 67. **I could not reproduce 27
under any selector**, and rather than publish a fourth bare number I published the selector with
each one, since selector drift is exactly why three authors got three answers:

| selector | sites | foldable |
|---|---|---|
| S0 the root variable is the operand of something that opens / enters / searches a path | **35** | 28 |
| S1 the root variable appears on a non-comment line at all | **69** | 59 |
| S2 S1 + any non-comment line spelling a path anchored at `.softhouse/` | **114** | 104 |
| S3 S2 + any non-comment line using a local assigned from the root variable (36 such locals) | **309** | 277 |

The narrowest honest reading is already larger than 27; the widest is an order of magnitude
larger. **T459's finding is confirmed: T454's direction is right and its figure is understated.**
The harness comment now carries this table and its selectors instead of the single number.

### 1c. The citation sweep — `instruments/citation-sweep.py`, `evidence/03-citation-sweep.txt`

1799 inbound `conformance.sh:NNNN` citations across 10,353 tracked files. See §4.

---

## 2. WHAT I DROVE — RED FIRST, ON THE UNMODIFIED TIP

Instruments: `instruments/drive.sh` (shared) and `instruments/arms.sh` (the arms). All scratch is
a clone under `/tmp/t466-work`, **outside the repository**, and the instrument refuses to run if
`$T466_WORK` is inside `$SRCREPO`. Every path the instruments plant is assembled from fragments at
run time; none is spelled as a literal. The probe line's **presence** is counted before its value
is read, and an empty bar log is an instrument failure (exit 3), never "the bar refused".

The fixture in every forgery arm is the same and it is what makes the arms mean anything: an
unregistered checker is **committed** into the guards directory, so the honest harness must refuse
it; the forged harness text adds a third DECLARATION TABLE row absolving it.

### Controls, base = tip before my change (`evidence/10-RED-tip-controls.txt`)

| arm | EXIT | probe count | probe | VERDICT | registration census |
|---|---|---|---|---|---|
| CTL — clean clone | 0 | 1 | up | PASS 46 / 7884 | `invoked-by-nothing=0` |
| CTLUNREG — checker committed, honest harness | **2** | **0** | — | none | `invoked-by-nothing=1` |

### RED — the three routes, all on the tip **before** my change

`evidence/11-RED-tip-SKIPWT-ASSUME.txt`, `evidence/12-RED-tip-SMUDGE.txt`,
`evidence/13-RED-tip-SMUDGE-weak-and-LONGNOP.txt`.

| arm | EXIT | probe | VERDICT | `status --porcelain` | `ls-files -v` not H | committed id | `hash-object` | `--no-filters` |
|---|---|---|---|---|---|---|---|---|
| SKIPWT | **0** | 1 up | PASS 46/7884, declared=3 | **EMPTY** | `S .softhouse/conformance.sh` | `7c543532…` | `e9f134f0…` | `e9f134f0…` |
| ASSUME | **0** | 1 up | PASS 46/7884, declared=3 | **EMPTY** | `h .softhouse/conformance.sh` | `7c543532…` | `e9f134f0…` | `e9f134f0…` |
| SMUDGE | **0** | 1 up | PASS 46/7884, declared=3 | **EMPTY** | (none) | `7c543532…` | **`7c543532…`** | `e9f134f0…` |
| LONGNOP | **0** | 1 up | PASS 46/7884, declared=3 | ` M` | (none) | `7c543532…` | `fafff8ff…` | `fafff8ff…` |

- **SKIPWT / ASSUME.** The guard printed
  `this harness .softhouse/conformance.sh: committed 7c543532… / on disk e9f134f0…` — two visibly
  different numbers — one line above `uncommitted edits 0`, and exited 0. Both ids were already in
  hand. They were never compared. T459's C-T459-1 reproduces exactly.
- **SMUDGE.** My **first** construction copied the forged bytes in by hand and left ` M` in
  `git status --porcelain`, so the out-of-band step could still see it. That is recorded in
  `evidence/13-…` as the weaker form, because it is a real difference from T459's claim and I did
  not want to quietly drop it. The **stronger** construction — both filter halves configured, the
  file materialised by `git checkout --` so git's stat cache matches — reproduces T459 exactly:
  porcelain EMPTY, `diff-index` empty, no index bit, and `git hash-object` returning the **honest**
  committed id over forged bytes. The guard's flagship "recompute this yourself" affordance
  **corroborated the forgery**. `git hash-object --no-filters` returned the forged id all along.
- **LONGNOP.** `evidence/13-…`. One inserted line, `return 0` atop the guard's body, carried in on
  a U+017F checkout collision. EXIT 0, probe 1 `up`, PASS 46/7884, planted checker absolved,
  `timed_guard` wiring and `GUARD_COST_BUDGETS` row **intact**, `16 guards timed`,
  `guard-cost: PASS`, and **zero `HARNESS-TEXT` lines in the entire transcript**. Diff against the
  honest text is **4 lines** (the two-line table edit plus one insertion). **The shipped sentence
  "IT MUST DELETE TWO SEPARATE PLACES, not one" is false.** C-T459-2 reproduces.

---

## 3. WHAT I CHANGED

All of it inside `guard_harness_text_is_committed` and its comment, plus one budget row and one
hand-typed cardinal elsewhere in the same file.

### 3a. `--no-filters` on every `hash-object` in the guard
Both the calibration read and the per-path read in the modified-set loop. Without it, a clean
filter declared in `.git/info/attributes` — per-clone, never committed, in no diff — decides what
the guard reads.

### 3b. The two ids the guard already computed are now COMPARED
If `confblob != confdisk` **and** `git diff-index` did not list this file, that is a refusal by
name, with both ids and the fact that git did not report it. If git did list it, the run says so
and defers to the census. This is the minimal form of the fix T459 asked for, and it is kept as
its own named check even though the recompute below subsumes it, so that a reader sees the
harness's own two ids adjudicated **where they are printed**.

### 3c. THE RECOMPUTE — a second, independent reading of "what differs", and the two are compared
The guard now walks the whole HEAD tree (`git ls-tree -r -z HEAD`), re-hashes every entry from
its bytes on disk with an inline python hasher that is **not** `git hash-object`, and compares
with the committed object id. Then it compares that answer with git's:

- **both say differs** → adjudicated exactly as before (SUBSTITUTED vs EDITED vs DELETED);
- **recompute only** → **SUPPRESSED**, refused, path and both ids named;
- **git only** → PHANTOM (mode change, unrefreshed stat data), counted and printed, **not**
  refused — it is not a text substitution and this guard is about text.

This makes the closure a property of the **whole tree** rather than of this one path: a bit or a
filter on any tracked file lands the same way. Symlink entries are hashed from their link target
(git's own blob rule for mode 120000) rather than dereferenced; a gitlink or any other mode the
hasher does not implement is an explicit refusal, never a silent skip; a missing file is reported
as MISSING and adjudicated, never treated as a match.

Calibrated before it is believed (P-72): the hasher must reproduce **both** of this file's ids —
committed and on disk — or the guard refuses as an instrument failure. That also refuses a
repository whose object format the hasher does not implement, instead of reporting all 10,347
paths as DIFFERS.

### 3d. THE LOCAL-STATE CENSUS — printed every run, pass or fail
`index entries NOT in state H`, `configured content filters`, `lines in this clone's private
attributes file`. All three are uncommitted and appear in no diff, and all three decide what git
answers, so the transcript now discloses them. **An index entry not in state `H` is itself a
refusal** — `S` or a lowercase letter has no legitimate use in a run whose whole job is comparing
paths. Filters and the attributes file are **printed, not refused**: they have legitimate uses,
they can no longer move a verdict (`--no-filters` plus a recompute that never asks git), and the
refusal for them comes from the **effect**, named at the path where it lands.

### 3e. GUARD_COST_BUDGETS: `guard_harness_text_is_committed` 60 → 300
Not to make a breach go away — it had never breached. The work grew: the guard now reads every
tracked byte. **Measured on this tree: 10,347 HEAD entries, ~252 MB, 4s warm and 21s cold.** The
budget block's own stated rule is `max(60, 10 × the cold measurement)` = 210, rounded up to 300 —
in family with `guard_ledger_invariants` (300) and well under `guard_reconciler_ownership` (500).
Observed on graded runs since: **2–6s**, printed as `COST Ns / ceiling 300s`.

### 3f. The comment, corrected where it was false
- The "MUST DELETE TWO SEPARATE PLACES" sentence is **replaced by what is true**, with LONGNOP's
  measurements and the diff sizes (LONGS 3 · LONGNOP 4 · LONGSTRIP1 4 · LONGSTRIP 5), and the
  standing instruction **stop pricing forgeries in deletions**. The old sentence is quoted in
  place so the correction is legible rather than invisible.
- The fold census is stated as the **member set** above, not as a number.
- The read census is stated as the **four selectors with their counts**, not as `27`.
- SKIPWT and SMUDGE get their own block, with what was measured before the fix and how each is
  closed, and the bound (§5) stated in the same breath.

### 3g. The last hand-typed cardinal (T459's LOW)
`yet three of them are invoked verbatim` is gone from the refusal and from the calibration
paragraph a thousand lines above it. The number a reader wants is `invoked=` on the
GUARDS-DIR-REGISTRATION line, which is derived and printed every run. P-80: "A CORRECTED CARDINAL
ROTS IN EVERY PLACE IT WAS RESTATED."

---

## 4. THE PINS I NEARLY ROTTED — measured, then repaired

My first draft inserted 9 lines **above** the population-empty refusal. The sweep
(`evidence/03-citation-sweep.txt`) caught it: **213** of 1799 inbound citations moved, and two of
them were load-bearing —

- `.softhouse/patterns.md:3271` (the founding instance of its vacuous-pass rule), and
- `.softhouse/bin/fire-program.sh:3217`.

Both are outside my scope, so repairing them at the citing end was not available. I did what T454
records doing: **moved my prose below the pins rather than the pins below my prose.** The
calibration paragraph is now a line-count-neutral rewrite in place, and the P-80 argument lives at
the refusal itself, which is below both pinned lines.

After the repair: **20** moved citations of 1799, and **not one** is a `.pin`, a guard,
`patterns.md`, or `fire-program.sh`. All 20 are prose in review documents, evidence transcripts
and task records — the class this program already treats as line-pinned history.

`tasks.json` carries **3** moved citations after the repair (9 before it), all three pointing at
the same line of a comment I did not touch. **I did not edit `tasks.json`** — it is the driver's
file. Noting it, as instructed. T459 reported 6 for its own diff; a different diff moves a
different set, so the two figures are not comparable and I am not claiming to have reproduced it.

---

## 5. THE HONEST BOUND — preserved, not narrowed

**SKIPWT, ASSUME and SMUDGE all live in LOCAL, UNCOMMITTED STATE. What they forge is a
TRANSCRIPT, never the commit.** An index bit, a git config filter driver and `.git/info/attributes`
are all per-clone; none appears in any diff; a reader who fetches the commit and hashes it
themselves was never fooled by any of them, and is still the only reader who cannot be.

Closing them here makes a fraudulent transcript **cost more**. It does not make a transcript
trustworthy on its own. That is exactly the argument for T460's external verifier, and it is why
the guard now tells a reader to recompute the right-hand id **with `--no-filters`** — the flag is
load-bearing for the verifier too, since SMUDGE defeats the unflagged form.

---

## 6. GREEN — the fix driven on my own committed tip

`evidence/20-…`, `evidence/21-…`, `evidence/22-…`. Committed harness blob `6d4ee305…`.

| arm | EXIT | probe count | probe | VERDICT | what the guard printed |
|---|---|---|---|---|---|
| CTL clean clone | **0** | 1 | up | PASS 46 / 7884 | ids equal, no findings |
| CTLUNREG | **2** | 0 | — | none | registration refusal, unchanged |
| **WDIRTY** honest uncommitted edit | **0** | 1 | up | PASS 46 / 7884 | `HARNESS-TEXT: uncommitted edit — .softhouse/conformance.sh (on disk c6244f73…)` + `edited but not committed — git agrees` |
| **SKIPWT** | **2** | **0** | — | none | all three findings fire (below) |
| **ASSUME** | **2** | **0** | — | none | all three findings fire |
| **SMUDGE** | **2** | **0** | — | none | filter halves named, suppression named, ids compared |
| **LONGNOP** | **0** | 1 | up | PASS 46 / 7884 | **nothing — still open, see §7** |

**SKIPWT / ASSUME, the three independent refusals** (each of which would refuse on its own):

```
conformance: guard_harness_text_is_committed: 1 TRACKED PATH(S) CARRY AN INDEX
             BIT THAT TELLS GIT NOT TO LOOK AT THE WORKING TREE.
conformance:   S .softhouse/conformance.sh          (ASSUME arm: h .softhouse/conformance.sh)
conformance: guard_harness_text_is_committed: THE BYTES ON DISK AT .softhouse/conformance.sh
             ARE NOT THE COMMITTED BYTES, AND GIT DID NOT REPORT IT.
conformance: guard_harness_text_is_committed: THE HARNESS THAT IS RUNNING IS NOT THE
             HARNESS THAT IS COMMITTED, AND GIT DID NOT REPORT IT.
conformance:   .softhouse/conformance.sh committed : 6d4ee3058e24e0e919dd434766f1552623e1575c
conformance:   .softhouse/conformance.sh on disk   : b42ecda2ed3492aaa5eea82bba895ce02dbabd37
conformance:   git diff-index     : did NOT list it
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

**SMUDGE** — the census now names the mechanism and the ids are honest again:

```
conformance:     LOCAL-STATE: content filter configured — filter.t466.clean  /tmp/…/clean.sh
conformance:     LOCAL-STATE: content filter configured — filter.t466.smudge /tmp/…/smudge.sh
conformance: guard_harness_text_is_committed: THE BYTES ON DISK AT .softhouse/conformance.sh
             ARE NOT THE COMMITTED BYTES, AND GIT DID NOT REPORT IT.
committed 6d4ee305… / on disk b42ecda2…      <- the FORGED id, because of --no-filters
git hash-object (no flag) on that same file  == 6d4ee305…, the honest id. The flag is the fix.
```

**WDIRTY is the one that matters as much as the refusals.** T454 established that a bar which
refuses every dirty tree is a bar that gets run with a flag to switch it off. That boundary is
intact: an honest uncommitted edit still reaches EXIT 0 and PASS, and is named, counted and
printed.

---

## 7. WHAT REMAINS OPEN — declared, not argued shut

1. **LONGNOP (and LONGSTRIP, its sibling) — OPEN.** Re-driven on my own fixed tip: EXIT 0, probe
   x1 `up`, PASS 46/7884, planted checker absolved, wiring and budget row intact, zero
   `HARNESS-TEXT` lines. **Nothing I added touches it and nothing inside this file can.** A guard
   that lives in the text under attack cannot survive an attacker who edits that text. The only
   remedy is a verifier outside the file — and it must use `--no-filters`, or SMUDGE defeats it
   too. FU-T454-1 / T460.
2. **The whole class of "the transcript is the artefact".** §5. Everything T466 closed was closed
   *in the transcript*. A reader who does not re-derive from the commit is still trusting a
   worker.
3. **U+FB01 against `.softhouse/bin/fire-program.sh` — OPEN and now demonstrated to have a live
   target.** I did not drive a collision at that path; I proved the fold, the byte order and the
   collision on this volume, and that the file exists and is a DECLARED WITNESS. That file is also
   where T460 proposes to put the external verifier. **Whatever is built there must not be
   forgeable by the route it exists to close.**
4. **U+037E → `;` and U+1FEF → `` ` `` have no tracked target today.** Not closed. The first
   tracked path that spells either character opens them.
5. **PHANTOM is printed, not refused.** A mode-only divergence between HEAD and the working tree
   is counted and named and does not fail the bar. I argued that a metadata change is not a text
   substitution; a reviewer may reasonably want it refused, and the counter is already in the
   transcript if so.
6. **The recompute trusts `python3` and the HEAD tree listing.** It is calibrated against both of
   this file's ids, so a wrong hasher refuses rather than passing — but the guard now has a
   dependency it did not have, and a host without `python3` fails closed rather than degrading.
7. **The index-bit refusal is absolute.** If some future workflow has a legitimate reason to set
   `--skip-worktree`, this guard will refuse it and the argument will have to be had. I chose
   refuse-and-argue over allow-and-hope; that is a decision, not a discovery.
8. **`tasks.json` carries 3 moved citations after my repair.** Out of my scope; noted, not fixed.

---

## 8. RESIDUE — verified, not asserted (`evidence/40-residue-check.txt`)

```
--- 1. INDEX BITS: every tracked entry whose ls-files -v state is not H
    entries not in state H: 0
    [nothing listed above = no bit left set]
--- 2. THIS CLONE'S PRIVATE ATTRIBUTES FILE
    git-dir: /Users/buv/gerege-nbfi/.git/worktrees/agent-abca32bc26a9f29f5
    …/info/attributes DOES NOT EXIST.
--- 3. CONFIGURED CONTENT FILTERS
    [nothing listed above = no filter driver configured]
--- 5. SCRATCH LOCATION   T466_WORK = /tmp/t466-work   outside the repository: confirmed
--- 6. tracked paths matching zz-t466: 0  [0 = none]
```

Every bit and every attributes file I set lived in a throwaway clone under `/tmp/t466-work`. None
was ever set in this repository. The check above is run **against this repository**, not against
the scratch, and is re-runnable from `/tmp/T466-residue.sh`'s recorded contents.

---

## 9. FINAL BAR ON THE COMMITTED TREE

`bash .softhouse/conformance.sh` — `bash`, not `sh`/`zsh`. Driver:
`instruments/finalbar.sh` (derives the repo root from its own location; spells no absolute path).
Summary in `evidence/90-FINAL-BAR.txt`, full 884-line transcript in
`evidence/91-FINAL-BAR-full-transcript.log`. **The probe line's PRESENCE is counted before its
value is read.**

Run on commit `64b730ba`, the commit that carries the change. The commit that adds this section
does **not** touch `.softhouse/conformance.sh`, so the harness text graded below —
blob `d1c45afc1c037135896bd52b4ee90c47c6843f8b` — is byte-identical on the branch tip. Recompute
it yourself with `git rev-parse HEAD:.softhouse/conformance.sh`, and the right-hand id with
`git hash-object --no-filters -- .softhouse/conformance.sh`, **with the flag**.

```
=== 0. THE TREE BEING GRADED ===================================================
HEAD                                  = 64b730bad7d797bf7dde30c05681c88ae6a9e883
git status --porcelain (must be empty):
git rev-parse HEAD:<harness>          = d1c45afc1c037135896bd52b4ee90c47c6843f8b
git hash-object --no-filters <harness>= d1c45afc1c037135896bd52b4ee90c47c6843f8b
git hash-object (no flag)  <harness>  = d1c45afc1c037135896bd52b4ee90c47c6843f8b
ls-files -v, entries NOT in state H   : []

=== 1. THE RUN =================================================================
command: bash .softhouse/conformance.sh   (bash, not sh, not zsh)
EXIT = 0

=== 2. PROBE PRESENCE BEFORE PROBE VALUE =======================================
grep -c 'probe = '  -> 1      <-- PRESENCE, read first
probe value         -> up

=== 3. VERDICT =================================================================
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

=== 4. THIS GUARD'S OWN OUTPUT =================================================
    1:conformance:   LOCAL-STATE CENSUS (uncommitted, in no diff, and it decides what git
    5:conformance:   HARNESS-TEXT CENSUS: HEAD 64b730bad7d797bf7dde30c05681c88ae6a9e883; …
    8:conformance:   RECOMPUTE: 10364 HEAD entries re-hashed from their bytes on disk;
   13:conformance:   this harness .softhouse/conformance.sh: committed d1c45afc… / on disk d1c45afc…
   21:conformance:    SUBSTITUTION and a SUPPRESSION are refused. [T454, T446 MAJOR-1, T466.]

=== 5. GUARD COST ==============================================================
  207:conformance:   GUARD-COST CENSUS: 16 guards timed, 72s total wall,
  210:conformance:     COST 4s / ceiling 300s   guard_harness_text_is_committed
  231:conformance:   guard-cost: PASS — every guard timed, every ceiling row used, none breached.

=== 6. ANY GUARD REFUSAL =======================================================
    [nothing listed above = no guard refused]
```

`16 guards timed` is unchanged — no guard was added or removed, only made to do more work. The
recompute covered **10,364** HEAD entries at a cost of **4 s** against its new **300 s** ceiling.
