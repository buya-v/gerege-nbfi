# T445 — `softhouse/T445-case-route`

**Subject:** T444's `M-1` (MAJOR, live on `main`) plus `C-1`, `C-2`, `C-3`, `C-4` and the five LOW.
**Grant:** `.softhouse/conformance.sh` (sole writer this wave), `.softhouse/capture/t445-case-route/`,
and this handoff. Nothing else is touched — checkable with `git diff --name-only main...HEAD`.

Honesty rule: every material claim carries `[VERIFIED: <path>]` or is marked `[UNVERIFIED]`.

---

## THE HEADLINE

**M-1 was one instance of a class, and the class had three more live members on `main`.** Every one
of them is the same confusion: **a test that reads the WORKING TREE deciding a question about what
is COMMITTED.** I re-derived M-1 from the source rather than inheriting it, drove it RED with my own
instrument and my own construction, and then asked T444's closing question — *which read looks at
the index, which at the working tree, and what happens when the two disagree?* — of **every
remaining read in `guard_guards_dir_registration`**. Three more fail-opens fell out. Each was driven
through the whole bar at **`EXIT 0` / probe PRESENT / `VERDICT: PASS`** before a character was
changed.

**After this change the guard performs ZERO working-tree reads of any member, witness or declared
witness.** The only file it still reads from this host is `.softhouse/conformance.sh` itself, and
that is correct and argued below.

The full audit — every read, classified, with the divergence mechanisms I could and could not close
— is `.softhouse/capture/t445-case-route/evidence/00-index-vs-worktree-audit.md`.
Condition-by-condition disposition is `evidence/02-condition-by-condition.md`.

---

## WHAT CHANGED IN `conformance.sh`

Entirely inside `guard_guards_dir_registration`, plus one new function beneath it. **No line count
is restated here** — `git diff --stat main...HEAD -- .softhouse/conformance.sh` derives it, and a
count restated beside the thing that derives it is P-80's own defect. No arithmetic, no money, no
float, no ledger, no vector, no DEC-n, no contract, no database driver, no pin change
[VERIFIED: read the whole diff].

1. **The member's own `REACHED-BY` row is read from its TRACKED BLOB** (`git cat-file blob
   "$member_blob"`, already in hand from the pinned lookup that decided the mode) instead of from
   `"$REPO_ROOT/$rel"`. Closes arms `MCASE` and `LEGDIRTY`.
2. **The witness naming test — the test that decides — reads the TRACKED BLOB** (`git cat-file blob
   "$self_blob"`) instead of `"$REPO_ROOT/$self_norm"`. **This is T444's M-1 remedy, and it is
   T375's own argument applied for the first time to the deciding test.** Closes arms `CASE`
   and `WDIRTY`.
3. **The `DECLARED` direction reads the index too**: the witness must be ONE tracked index entry
   with a regular-file mode (`100644` or `100755` — both are live on this tree today), and both the
   `CALLER` and `SUBJECT` token tests read tracked blobs. Replaces `[ ! -f "$REPO_ROOT/$witness" ]`.
   Closes arm `CDIRTY`.
4. **`[ ! -f "$REPO_ROOT/$self_wit" ]` is DELETED** (T444 `LOW-4`). It graded the TYPED spelling on
   this host while everything downstream graded `$self_norm` from the index; it could not fail open,
   but it refused honest work — a committed witness that this checkout does not materialise. Arm
   `WGONE`. The downstream "NOT TRACKED" message, which asserted *"the existence test above
   passed"*, is corrected in the same commit.
5. **A member carrying MORE THAN ONE `REACHED-BY` row is refused** (T444 `LOW-5`), counted from the
   tracked blob. Arm `2ROW`.
6. **`guard_registration_decisive_lines`** — new, called from `guard_guards_dir_registration` on
   every graded run (T444 `C-2`). See below.
7. **The `member_multi` "unreachable-by-construction" sentence is corrected** to what T444 measured
   (T444 `C-1`).
8. **Every `patterns.md:NNNN` line citation in this file is replaced by the rule ID** — seventeen
   occurrences, nine distinct numbers, **three of them already rotted** (T444 `C-3`'s method,
   applied in the direction nobody had swept).

---

## THE INSTRUMENT

`.softhouse/capture/t445-case-route/instruments/drive-t445.sh`, **FROZEN with `chmod a-w` before
every run recorded here**, so an edit could not reach a run in flight.

**TWO frozen states, and which arms ran under which is stated rather than blurred:**

* `sha256 = 9adf98c4900e81fe79023fbf865d1130543a8136a0889685bed408e8276a764c` — every arm in the
  table except `RWB2`.
* `sha256 = dbcae7a049442cdb2710d9dac7187e6293554be04fc86123cf94668610f8a4b4` — `RWB2` only. The
  difference between the two is exactly the addition of `plant_RWB2`, which no other arm calls
  [checkable: `git log -p -- .../drive-t445.sh`]. The committed file is the second.

Two earlier states of the file existed and are named so the record is complete:
`4f1cc183…` (which produced the first `Z`/`CASE`/`MCASE` RED transcripts and the first, invalid
`LEGDIRTY`) and `99e43a60…` (never used for a run — it carried a `local`-expansion bug that aborted
before the first bar). All four are in this branch's history.

It takes its **work root** and its **source repository** as ARGUMENTS and binds no literal
shared-temp path to a name, so it adds no row to `HOSTSTATE_PIN_TEMP_ASSIGN_LIST`. Every planted
repo-rooted path is assembled at run time from `$GDR` plus a leaf, so it plants no dead path in
T316's frontier.

Per arm: clone the tree under test → mutate + commit → **RE-CLONE** (so a case collision
materialises exactly as a fresh checkout would) → apply any working-tree-only mutation **to the tree
that is graded** → run the **whole bar** from a cwd outside the repo → record the exit code, then
the probe **PRESENCE**, then its value (P-84 — an ABSENT probe line is not `down`), then the census
line and the decisive sentences. **The instrument DETECTS which tree it is grading from that tree's
own text and prints it on every arm; the mode is not passable in.**

`RED` = **`eb795f1d`** — this branch before any change to `conformance.sh`; that file is
byte-identical to `main` at `2a1dac46` [VERIFIED: `git diff 2a1dac46 eb795f1d -- .softhouse/conformance.sh`
is empty].
`GREEN` = **`be2ebea5`**, the committed tip (T444 `LOW-3`, adopted as a requirement).

Supporting probe: `instruments/probe-collision-order.sh` → `evidence/01-collision-order-probe.txt`.
**MEASURED, not reasoned: the index entry that sorts LAST wins a checkout collision**, so a target
spelled in all lower case cannot be beaten by any case variant, and one carrying an upper-case
letter loses to its lower-case decoy.

---

## THE ARM TABLE

`RED` = **`eb795f1d`** (this branch before any change; `conformance.sh` byte-identical to `main`).
`GREEN` = **`be2ebea5`**, the committed tip. Every cell is a **whole-bar** run: exit code, then probe
PRESENCE, then value, then the census line.

| arm | what it is | on `eb795f1d` (= `main`) | on this branch | reading |
|---|---|---|---|---|
| `Z` | unmutated control | **0 / PRESENT / `up` / PASS 46-7884** `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | **identical** | a clean tree still passes |
| `LEGA` | an entirely honest, plain-ASCII registration | **0 / PRESENT / PASS / `reached-by=2`** | **0 / PRESENT / PASS / `reached-by=2`** | **honest work is still accepted** |
| **`CASE`** | T444's M-1, re-derived: `W.txt` (100644 decoy) DECLARED, `w.txt` (120000 symlink to the member) wins the checkout | **0 / PRESENT / PASS / `reached-by=2`** — *"(verified: it names zz-t445k-member.sh)"* printed over a symlink to the member | **2 / ABSENT — `DOES NOT NAME … IN ITS COMMITTED BYTES`** | **M-1 CLOSED** |
| **`MCASE`** | **T445's own:** two index entries whose DIRECTORIES differ only in case; the smuggled member's header is read out of the honest one | **0 / PRESENT / PASS / `reached-by=3`** — *"ZZ-T445M/x.sh — declared in its own header"* over a member whose header has no row | **2 / ABSENT — `ZZ-T445M/x.sh IS INVOKED BY NOTHING`, `invoked-by-nothing=1`, and the honest sibling STILL `REACHED-BY` in the same run** | **new route CLOSED, with the discrimination visible in one transcript** |
| **`LEGDIRTY`** | **T445's own:** the registration row exists ONLY in the working tree | **0 / PRESENT / PASS / `reached-by=2`** | **2 / ABSENT — `IS INVOKED BY NOTHING`** | uncommitted host state no longer registers a checker |
| **`WDIRTY`** | **T445's own:** the witness names the member ONLY in the working tree | **0 / PRESENT / PASS / `reached-by=2`** | **2 / ABSENT — `DOES NOT NAME … IN ITS COMMITTED BYTES`** | same, witness side |
| **`CDIRTY`** | **T445's own:** the DECLARED witness stops naming its token in the working tree only | **`guard_guards_dir_registration FAILED` — `is DECLARED as being run by … NO LONGER NAMES`** | **`guards-dir registration: PASS`** | the DECLARED verdict is no longer decided by this host. **Exit is 2 on BOTH trees, identically, from `guard_dead_path_frontier` (`rows=107 pinned=108 removed=1`) — my stub removed a dead-path row. An equal confound in both directions; the measurement is the guard's own sentence, and it flipped.** |
| **`WGONE`** | a committed witness that this checkout does not materialise | **2 / ABSENT — `THAT REACHED-BY WITNESS DOES NOT EXIST`** | **0 / PRESENT / PASS / `reached-by=2`** | **LOW-4: the over-refusal is gone** |
| `GITLW` | the witness is a GITLINK (`160000`); its object is a commit, not a blob | 2 / ABSENT (`DOES NOT EXIST`, via the `-f` test) | **2 / ABSENT (`DOES NOT NAME … IN ITS COMMITTED BYTES`)** | fail-CLOSED both ways; on this branch for the accurate reason |
| **`2ROW`** | a member carrying TWO `REACHED-BY` rows | **0 / PRESENT / PASS / `reached-by=2`** with the second row ungraded | **2 / ABSENT — `carries 2 REACHED-BY DIRECTIVES`** | **LOW-5 closed** |
| **`RVQ`** | the round-trip line DELETED | **0 / PRESENT / `up` / PASS 46-7884** — T444's C-2 finding reproduced independently, `roundtrip=NO` detected from the tree's own text | **2 / ABSENT — `THE DECISIVE LINE IS GONE — the witness lookup must ROUND-TRIP`**, `1 of 7 decisive line(s) absent` | **C-2 closed: the one independently necessary line now has an arm** |
| **`RWB2`** | the witness tracked-blob read REVERTED to a host read | n/a (the line does not exist on `main`) | **2 / ABSENT — `THE DECISIVE LINE IS GONE — the WITNESS naming test reads the TRACKED BLOB`** | the new remedy is itself watched |

**Two arms that did NOT measure what they were built to measure, recorded rather than deleted** —
an arm that refuses for the wrong reason looks exactly like an arm that worked:

* **`RWB`** (superseded by `RWB2`): it DELETED every line carrying the tracked-blob read, but that
  line is the second line of a two-line command substitution, so the mutant died of a **shell syntax
  error** at `line 4276: syntax error near unexpected token 'done'`. Exit 2 with the probe absent —
  a refusal, but not the one asked for. `RWB2` substitutes instead of deleting.
  [`evidence/GREEN-RWB-bar.log`]
* **`LEGDIRTY`, first construction**: the uncommitted edit was applied to the SEED, which `git clone`
  does not carry, so the graded tree never saw it — exit 2 for the honest reason that the committed
  member has no row. The instrument gained a **post-clone** mutation hook and the arm was re-driven.
  [`evidence/RED-LEGDIRTY-figures.txt` is the invalid one; `evidence/RED2-LEGDIRTY-figures.txt` is
  the measurement.]


---

## `guard_registration_decisive_lines` — T444's C-2

**The wiring, established by grep and not asserted** [VERIFIED: `grep -n` on the tip]:

```
main_grade                                        :5203   (graded-run entry; CLI dispatch :5900/:5902)
  run_guards                                      :5206
    timed_guard guard_guards_dir_registration     :4757
      guard_registration_decisive_lines "$conf"   :3303
```

It grades **the deployed text of this file**, comment-stripped, in two ways:

* **PRESENCE** — seven decisive lines must occur in the executable text (both pinned lookups, the
  empty-result refusal, the round-trip equality, and the three tracked-blob reads).
* **BEHAVIOUR** — the two decisive comparisons are **cut out of the deployed line and evaluated**,
  once on an input they must refuse and once on an input they must accept. A line kept but neutered
  is present and not discriminating, and presence alone would call that green — P-22, *"a guard, a
  canary, or a control that cannot fail is worse than none, because it is believed."*

**Every needle is assembled at run time from fragments**, so no needle appears whole on any line of
this file and this function can never be the occurrence it counts. That is deliberate: a control
that hides from `git grep` by respelling its token is evasion, and one that satisfies itself by
spelling its own needle is worse.

It is NOT wired through `timed_guard` — that would move `GUARD_COST_TIMED` and make
`guard_cost_census`'s *"this function calls fifteen guards"* false. It runs inside
`guard_guards_dir_registration`'s existing 60 s ceiling; the measured cost of that guard is
unchanged at 0–1 s.

---

## WHAT I COULD NOT CLOSE — by name and by spelling

Recorded so silence is not read as completion. `[UNVERIFIED]` on every line.

* **`git update-index --skip-worktree`** and **`git update-index --assume-unchanged`** — index bits,
  not blob changes. After T445 no graded read can see them; before T445 they let a working-tree lie
  sit under a clean `git status`. **No arm built.**
* **a sparse checkout** — `git sparse-checkout set …`, `core.sparseCheckout=true`. Structurally
  identical to arm `WGONE`. **Not driven as its own arm.**
* **`.gitattributes` smudge rules that make a checkout differ from its blob** — `* text eol=crlf`,
  `* ident`, and `filter=<name>` (the last additionally needs `filter.<name>.smudge` in local
  config, which a clone does not carry). **Not driven.**
* **`core.symlinks=false`.** **Not driven.**
* **macOS unicode normalisation** — `core.precomposeunicode`, and an **NFD/NFC pair of index
  entries** folding to one filesystem path. Same shape as the case route with a different folding
  rule. **NOT DRIVEN, and I could not rule it out.**
* **a genuinely case-SENSITIVE filesystem, and a second git binary.** The bound T404, T407, T431 and
  T444 each recorded. `CASE` and `MCASE` are *consequences* of case-insensitivity, so a
  case-sensitive host is where they would NOT reproduce and where the same commit would materialise
  both files — **the guard's verdict was host-dependent for such a commit, which is itself the
  objection, and reading the index removes the dependence.**
* **the pinned toolchain.** Every arm ran under the announced FALLBACK toolchain. RED and GREEN are
  like-for-like; neither is graded under the pinned toolchain.
* **`.softhouse/patterns.md`** — T444's `C-4` remedy of record is a paragraph there, and
  `patterns.md` is **outside this grant**. Filed as `FU-T445-4`. I neither adopted nor rejected
  T444's `-c core.quotePath=false` measurement; I did not re-derive it.
* **`.softhouse/bin/fire-program.sh:1406`** cites `conformance.sh:3217-3220` for a quoted refusal;
  those lines are a comment and the function header. **Already rotted before T445 and NOT moved by
  T445** — every line T445 adds is below `:3271` [VERIFIED: `sed -n '3217,3220p'` before and after].
  Out of grant. Filed as `FU-T445-5`.
* **`guard_dead_path_frontier`'s census crashes** rather than diagnosing on a non-ASCII path, a
  newline path or a gitlink under `.softhouse/guards/` [T444 `C-4`]. Different guard, out of grant.
  Filed as `FU-T445-6`.
* **`guard_registration_decisive_lines` defines two helper functions (`present`, `discriminates`) in
  the global namespace for the duration of its run and `unset -f`s them at the end.** No other
  function in this file has either name [VERIFIED: `grep -n 'present()\|discriminates()'` returns
  only my two definitions], but the `unset -f` would remove a caller-defined function of that name
  if one ever appeared. Disclosed rather than renamed, because renaming after the drive would make
  the barred tree differ from the driven tree.

---

## CITATION AND CARDINAL HYGIENE IN THIS COMMIT

* **`.softhouse/RESUME.md` no longer carries a `conformance.sh:NNNN` citation at all.** The driver
  rewrote it at the start of this fire; I re-measured rather than inheriting T444's `:3782`.
  `grep -c 'conformance\.sh:[0-9]' .softhouse/RESUME.md` = **0** [VERIFIED].
* **`patterns.md:3426 → conformance.sh:3271` is PRESERVED.** Every line added by T445 is below
  `:3271`; `sed -n 3271p` prints the same `population is EMPTY` refusal before and after [VERIFIED,
  three times during this task].
* **No comment added by T445 restates a line number, a distance in lines, or a count that something
  else derives.** Checked with `grep -n 'lines up\|line above\|lines below\|lines down'` over the
  changed span; the two first-draft instances were removed before the drive.

---

## FOLLOW-UPS FILED

* **`FU-T445-1`** — the NOT-DRIVEN divergence mechanisms above, especially the **NFD/NFC index
  pair**, which is the one I could not rule out.
* **`FU-T445-2`** — `guard_registration_decisive_lines` grades presence and discrimination of the
  decisive lines but still runs **no end-to-end forgery fixture**. The strongest version would build
  a scratch repository and drive one forgery through the real predicate. That needs the guard
  parameterised on `REPO_ROOT`, which is a larger change than this grant.
* **`FU-T445-3`** — the guard's verdict for a case-colliding commit is **host-dependent**: on a
  case-SENSITIVE host both files materialise and the constructions refuse for different reasons.
  Nothing in this program runs on such a host today.
* **`FU-T445-4`** — T444 `C-4`: record the plain-ASCII path constraint in `patterns.md`, with the
  three places that break otherwise.
* **`FU-T445-5`** — `fire-program.sh:1406`'s rotted citation.
* **`FU-T445-6`** — T444 `C-4`: `guard_dead_path_frontier`'s census crashes rather than diagnosing.
* **`FU-T445-7`** — T431's `FU-T431-4`, seconded by T444 and now by a third generation: `patterns.md`
  still has **no P-number for "freeze the drive before you run it"**. Three tasks have now paid for
  the lesson and nobody has written it down.
* **`FU-T445-8`** — a new one, and it is the pattern this task actually taught:
  **"a test that reads the WORKING TREE cannot decide a question about what is COMMITTED."** Six
  fail-opens in this one function have now had that single shape. It deserves a P-number.

---

## THE BAR

`bash .softhouse/conformance.sh` from the worktree, cwd `/tmp/t445final` (scratch, outside the
repo), on the **COMMITTED tip**, with `git status --porcelain` **EMPTY before AND after**.
Full transcript, 861 lines: `.softhouse/capture/t445-case-route/evidence/90-FINAL-BAR-committed-tip.log`.

```
EXIT = 0
grep -c 'probe = ' = 1                    <- PRESENCE read BEFORE the value (P-84)
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

| figure | `main` @ `2a1dac46` | this tip | required |
|---|---|---|---|
| exit | 0 | **0** | 0 |
| `probe = ` line count, read before its value | 1 | **1** | ≥ 1 |
| probe value | `up` | **`up`** | — |
| VERDICT | PASS 46 / 7884 | **PASS 46 / 7884** | unmoved |
| wrong ledger implementations | 16, all dead | **16, all 16 DIED through this harness** | 16 |
| guards-dir census | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | **identical** | unmoved |
| `deadOccurrences` / `deadFiles` | 108 / 75 | **108 / 75** | unmoved |
| dead-path FRONTIER | 11, pinned 11 | **11, pinned 11** | unmoved |
| dead-path corpus | 1528 | **1534** (+6: my instruments and evidence) | no pin on it |
| host-state census | 18, pinned 18 | **18, pinned 18** (195 instruments, was 192) | unmoved |
| `guard_guards_dir_registration` cost | — | **2 s / ceiling 60 s**, 0 breaches | under ceiling |
| guards timed | 15 | **15** | unmoved — the new function is NOT a `timed_guard` |
| NEW census line | — | `registration decisive lines: 7 present, 2 evaluated on an input they must refuse AND an input they must accept` | — |
| `patterns.md:3426` → `conformance.sh:3271` | resolves | **resolves** | resolves |
| tree clean after the run | yes | **yes** | yes |

**Branch:** `softhouse/T445-case-route`. `git log --oneline main..HEAD` carries every commit listed
in this handoff; the tree barred above is the tip.

