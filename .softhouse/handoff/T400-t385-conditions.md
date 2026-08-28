# T400 — T385's three conditions on T383

Branch `softhouse/T400-t385-conditions`. Subject: `.softhouse/bin/fire-program.sh` only.
All three conditions are comment-level except **F-T385-2**, which was a MEASURED fail-open in
the reasoning and is now a two-line code change plus the corrected claim.

---

## 0. RE-MEASUREMENT OF EVERY CITED LINE AND CARDINAL

The task's citations are prose from a review (P-86). I re-measured each one against the file
that shipped on `main` (`sha256 5c4f0244…`, 3330 lines) before touching anything.

| cited | claim | MEASURED on `main` | verdict |
|---|---|---|---|
| `:748-749` | "the z06/z07 offsets are named here rather than re-spelled … cannot drift apart" | line 748 begins `# The z06/z07 offsets are named here rather than re-spelled, so the tests below` and 749 ends `# that consume them cannot drift apart.` | **exact** |
| `:883-884` | the offsets are re-spelled inline in the rows | 883 = `_row z06 … $(( _NOW_E + LOCK_RELEASE_SKEW_SECS * 2 + 60 ))`; 884 = `_row z07 … $(( _NOW_E + LOCK_RELEASE_SKEW_SECS / 2 ))` | **exact** |
| `:724` | "the four tests below ARE the four fixture expressions" | line 724 = `# cardinal enters this file and none is restated: the four tests below ARE the four fixture` | **exact** |
| `:756-761` | the code has SIX | six `|| _FIXOK=0` assertions at 756, 757, 758, 759, 760, 761 — no more, no fewer (`grep -n '|| _FIXOK=0'`) | **exact: six** |
| `:753-754` | `_SKEW_FAR` / `_SKEW_NEAR` defined | 753/754 | **exact** |
| F-T385-1 site | the false substring example | the bullet spans **`:1437-1439`**, not 1437-1438 — the `lockselftest| ROWS=…` phrase is on 1438 and the sentence closes on 1439. T385's own table says `1437-1439`; the task prompt's "`:1437-1438`" is one line short | **corrected** |
| capture vs echo | the echo is added after the capture | `_ST_OUT="$(…--self-test-lock-readers 2>&1)"` at **`:1339`**, the `log "lockselftest| $l"` loop at **`:1340`**, the population selector at **`:1459`** | **exact** |
| `_SKEW_FAR`/`_SKEW_NEAR` occurrences | "only in the gate and its message" | 749 (a comment), 753, 754, 759, 760, 761, 763 (the refusal message). **Zero** occurrences in any executable row | **exact** |
| row census | 45 declared | `grep -cE '^[[:space:]]*_(row|arow)[[:space:]]'` = **45** before and **45** after my change (comments start with `#` and cannot join the census) | **unchanged** |

Post-fix line numbers, for whoever cites this next (file now 3392 lines,
`sha256 4e8af76d8736f6efe3c254767fcf38e07c7b8b40a1d6d17fa1e115caa76909b2`):
`:724` the de-cardinalised sentence · `:729` the F-T385-3 note · `:761` the F-T385-2 note ·
`:792-793` `_SKEW_FAR`/`_SKEW_NEAR` · `:795-800` the six assertions · `:926-927` z06/z07 ·
`:1382` the capture · `:1480` the corrected bullet · `:1483` the F-T385-1 note · `:1521` the selector.

---

## 1. F-T385-2 (MODERATE, DRIVEN) — FIXED IN CODE

`:926-927` now read `$(( _NOW_E + _SKEW_FAR ))` and `$(( _NOW_E + _SKEW_NEAR ))`. There is
exactly **one** spelling of each offset, and it is the one the fixture gate asserts on, so the
claim is true **by construction** rather than by promise — P-80's own fix, *"make the second
site READ the first"*. The comment no longer says "cannot drift apart" as an unbacked promise;
it states what was wrong, cites T385's `s01`/`s02`, and states the residual (below).

**Re-drive: `.softhouse/capture/t400-t385-conditions/bin/t400-skew-drift-redrive.zsh`**
GREEN on the shipped bytes — `out/02-skew-drift-redrive.txt`, **`CHECKS=7 WRONG=0 VOID=0`**:

| case | what | result |
|---|---|---|
| `s00` | CONTROL, unmutated | `rc 0`, z06 `ok`, z07 `ok`, **the fire STARTS** |
| `s01s` | STRUCTURAL: `_row z0[67]` lines spelling `LOCK_RELEASE_SKEW_SECS` inline | **0** (on `main`: **2**) |
| `s01v` | T385's exact drift string applied to the z06 line | **NO-OP** — `* 2 + 60` is not in the row any more |
| `s01` | T385's `s01` **verbatim**, driven | the mutant is byte-identical, `rc 0`, no `*** FAIL-OPEN`. The drift is not "caught", it is **unspellable** |
| `s01b` | the same drift on the ONE surviving spelling (`_SKEW_FAR` → `/ 2`) | **`rc 78`**, `CONFIGURATION ERROR`, and **never** "this is the READERS" |
| `s02` | T385's CONTROL verbatim (gate variable → 0) | **`rc 78`**, `past-skew offset=0` — the gate is still live |
| `s03` | STATED RESIDUAL: z06 pointed at the WRONG variable (`_SKEW_NEAR`) | `rc 2`, `z06 *** FAIL-OPEN`, blamed on the readers — see §5 |

**RED control, the same driver on pre-fix `main` — `out/03-skew-drift-RED-on-main.txt`,
`CHECKS=7 WRONG=4 VOID=1`.** `s01s` reports **2 inline spellings**, `s01v` reports **STILL
driftable**, and `s01` reproduces T385's finding independently: `z06 *** FAIL-OPEN
want=HELD got=FREE-released` followed by *"The thresholds validated at startup, so this is the
READERS."* at `rc 2`. Same driver, opposite verdict on the two files — that difference is the
evidence, not my assertion.

One defect in my own driver, caught by its first run and recorded because it is the P-22 shape:
`s01`'s forbidden pattern was the bare token `FAIL-OPEN`, which the self-test's **group headers**
narrate on every healthy run (`"Anything else = FAIL-OPEN (P-85 safety)"`), so the control could
never pass. It is now `\*\*\* FAIL-OPEN`, the row MARK. Noted inline in the driver.

---

## 2. F-T385-1 (MINOR) — FALSE EXAMPLE REPLACED, ANCHORING UNTOUCHED

The selector at `:1521` is **byte-identical** to what shipped. Only the rationale changed.

Re-measured on **my own file** — `bin/t400-substring-and-healthy.zsh`,
`out/01-substring-and-healthy.txt`:

```
A.  self-test rc 0;  lines of $_ST_OUT matching UNANCHORED /ROWS=/   : 1
    the shipped ANCHORED selector                                    : 1
    /lockselftest\| ROWS=/                                           : 0
    the single unanchored match, verbatim: ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0
B.  the same run's LOG: 'lockselftest| ROWS=' lines                  : 1   (downstream)
C.  the NAIVE unanchored wrapper (grep 'ROWS=') on healthy input     : rc 0, "tally VERIFIED"
```

So T383's stated reason is false twice over: the prefixed echo is added at `:1383` (was `:1340`),
**after** the capture at `:1382`, so it cannot join the population whether the selector is
anchored or not; and the "naive `grep -c ROWS=` fix" T383 says *"would have refused every healthy
fire"* **starts** it. T385's measurement reproduces exactly on my bytes.

**The anchoring stays, and the new text justifies it without that example**: it is a property
("only a whole line that is nothing but a summary is a summary"), it is what makes m06a/m06b,
m08, m09a/m09b land absent-rather-than-accepted, and it is the standing defence against a future
narration line **emitted by the self-test itself** carrying the token — of which there are
currently none, and that is a measurement (1 unanchored match, and it is the summary), not an
assumption. The example is now *self-test narration*, which is the thing case `m10`/`d12`
actually exercises.

---

## 3. F-T385-3 (MINOR, P-80) — THE CARDINAL IS REMOVED, NOT UPDATED

`:724` said "the **four** tests below ARE the **four** fixture expressions" over **six**
assertions: bullets 1–3 mapped to `:756-758`, the fourth bullet silently covered **two** of them
(`:759` non-wrap and `:760` representable), and **`:761` — z07's own assertion — had no bullet at
all**. Writing "six" would re-arm the same rot, so the count is
**not restated at all**: the sentence now says the tests ARE the fixture expressions, one per
property, each carrying its row id in its own trailing comment. The bullet list is expanded to
six, one per assertion, in the code's own order. Adding an assertion now needs no edit to a
cardinal anywhere.

---

## 4. THE THREE REQUIRED CONTROLS — ALL ON THE FINAL BYTES

Every drive below was re-run **after** the last comment edit, against
`sha256 4e8af76d8736f6efe3c254767fcf38e07c7b8b40a1d6d17fa1e115caa76909b2`, which is exactly the
file on this branch.

1. **192-state wrapper-vs-skill** — `.softhouse/capture/t279-lock-partition/drive-wrapper-vs-skill.zsh`,
   `out/05-192-state.txt`: `expected verdicts generated: 192`, `states driven: 192`,
   **`disagreements … 0`**, `RESULT: PASS`. I changed no lock arm, in either document.
2. **T385's 20-case driver** — `.softhouse/reviews/t385-review-t383/bin/t385-multiplicity-drive.zsh`
   run unmodified against my file, `out/04-t385-20case-redrive.txt`: **`CHECKS=20 WRONG=0 VOID=0`,
   `RESULT: PASS`**, all 20 rows `ok` (d00–d12, n01–n07).
3. **HEALTHY FIRE STARTS** — `out/01-substring-and-healthy.txt` §D and `out/02…` `s00`:
   the unmutated wrapper at `--probe` exits **rc 0** with
   `lockselftest: tally VERIFIED … 45 executed + 0 skipped = 45 declared … FAIL_OPEN=0
   FAIL_SHUT=0, rc=0` and `probe only — exiting…`. A control that refuses everything is the same
   defect as one that cannot fail; this one still starts.

---

## 5. STATED RESIDUAL (`s03`) — WHAT THIS FIX DOES **NOT** CLOSE

Deriving both offsets from one place makes it impossible for the gate and the row to hold
**different values**. It does **not** stop a row naming the **wrong fixture**: driven as `s03`,
z06 reading `_SKEW_NEAR` lands `*** FAIL-OPEN` and the wiring says *"this is the READERS"*.
C and G have carried the identical residual since T361 (`_OLD` vs `_NEAR` are equally
swappable), so this is a pre-existing property of the whole fixture design, not something T400
introduced or T385 asked for. It is written into the source comment so the file does not
overclaim, and it is driven so the claim is not prose. Closing it would need a per-row assertion
of the *sign* of each fixture's offset relative to its bound; that is a bigger change than
either of T385's conditions and I did not take it.

Also still open, and explicitly **not mine**: **F-T385-4** — the fail-open / dead-path census
tracks `.sh`/`.py`, so tracked `.zsh` files are invisible to it. Re-measured on this branch:
**123 tracked `.zsh`, 111 of them under `.softhouse/capture/` or `.softhouse/reviews/`**
(T385 measured 110/98; the corpus has grown since, my two drivers included). T385 filed it as
needing its own grant.

---

## 6. WRITER SAFETY (P-97) — I NEVER WROTE THROUGH THE ORIGINAL INODE

A fire is live: this worker's own environment carried `FIRE_SNAPSHOT_OF`,
`FIRE_SCRIPT_DIR` and `FIRE_REPO_SCRIPT` pointing at `/Users/buv/gerege-nbfi/.softhouse/bin/`.
Every probe `unset`s all four (including `FIRE_NO_SNAPSHOT`, which does **not** override the
first: the snapshot branch is `if [[ -z "${FIRE_SNAPSHOT_OF:-}" && "${FIRE_NO_SNAPSHOT:-0}" != "1" ]]`
— **`main:999`**, re-measured, now `:1042` on this branch — so a set `FIRE_SNAPSHOT_OF` skips it
whatever `FIRE_NO_SNAPSHOT` says) before running anything.

* The live wrapper `/Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh`: inode **19079181**,
  mtime **Aug 28 21:10**, `sha256 5c4f0244…` — measured at the start of this task and again at
  the end, **identical on all three**. I never opened it for writing, never `cp`'d over it, and
  never named it as a probe subject.
* My edits went to the worktree copy through the harness `Edit`/`Write` tools, which rename:
  the worktree file's inode moved **20043226 → 20271826** across the edits, which is the
  isolated signature P-97 measured.
* Every drive ran against `/tmp/t400/fixed.sh` (a copy) or a mutant under `/tmp/t400/`, with
  `GEREGE_NBFI_REPO=/tmp/t400/subject` (a throwaway git repo I created) and `LOG_DIR` under
  `/tmp`. `--probe` exits before the lock is read and before anything is dispatched. The only
  wrapper modes used were `--probe`, `--self-test-lock-readers`, `--lock-decide` (via the
  192-state driver) and `zsh -n`. No lock was taken; nothing was dispatched.
* The change lands through **git**, on a branch — all eight measured git write paths rename.

---

## 7. THE BAR

Run from a clean tree after `git add -A` and commit, with `bash` (never `sh`):
`bash .softhouse/conformance.sh` → **exit 0**, archived at `out/06-bar-on-branch.log`.

```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
frontier 11, pinned at 11 — frontier == pinned (all 11 rows, by path)
dead-path frontier: GREEN, and the T323 reconciliation list is empty
T316-DEADPATH-CENSUS: corpus=1395 deadFiles=75 deadOccurrences=108 …
CENSUS wrong ledger implementations — discovered 14 … pinned at 14; all 14 DIED through this harness
exemption census READ: 4 == pinned 4 (GROUNDED 4, UNDETERMINED 0, UNGROUNDED 0)
```

P-84 presence-before-value: `grep -c 'probe = '` over the bar log = **1** (line 192,
`reference oracle (https://localhost:8443/…/health) probe = up`). Every baseline matches the
task's: 46 parity / 7884 cells, frontier GREEN at `deadOccurrences 108`, wrong-impl pin **14**.

No floating point, no money code, no database driver was touched — this task is entirely inside
the fire wrapper's lock self-test and its wiring.

## Commits (incremental, nothing held uncommitted)

1. `bfae9781` — the three fixes in `fire-program.sh`
2. `7b7a0992` — the skew-drift re-drive, GREEN on the fix + RED on pre-fix `main`
3. `372971cc` — all four drives re-run on the final bytes
4. this handoff
