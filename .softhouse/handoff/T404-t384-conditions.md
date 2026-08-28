# T404 — T384's conditions closed: the FIFTH registration fail-open is shut, with its arms

**Branch:** `softhouse/T404-t384-conditions`.
**Subject:** `FU-T375-7` / `F-T384-1`. `guard_guards_dir_registration` handed the member's own
path to git as a **pathspec, not a literal**, so **two committed files — one of them entirely
honest — neutralised both of T375's new tests at once.**

---

## VERDICT

**CLOSED, DRIVEN RED BEFORE GREEN, AND THE HEALTHY CONTROLS STAY GREEN.**

The fifth fail-open reproduces on **today's** tree, not just on the T375 branch: whole bar
**exit 0, probe PRESENT, `VERDICT: PASS`**, a tracked **symlink** credited `reached-by=3`, and
the census printing **`symlink-members=0`** while that symlink member sat in the population.
After the repair the same arm is **exit 2, probe ABSENT, `IS A SYMLINK`, `symlink-members=1`**.
**Reverting both halves of the repair reopens the hole exactly** — arm `R3`, byte-identical
census to the pre-fix arm `G`.

**19 arm runs, 19 PASS / 0 FAIL** — 8 RED-BEFORE and 11 GREEN-AFTER. Every arm cloned
`--no-hardlinks`, mutated, `git add -A` **and committed**, asserted `dirty=no`, and ran the
**whole bar** with `bash`. **Final bar on a clean committed tree: exit 0, every baseline count
unmoved.**

**T375 was RIGHT not to patch this in flight, and I want that on the record.** An executable
change would have invalidated the 61-arm drive that was its branch's whole evidentiary basis,
and **a one-token change shipped without its arm is precisely what that task existed to
refuse.** What was wrong was the **severity rating**, not the process. The threat model of this
guard is **deliberate forgery inside a task's own edit grant, where the attacker chooses the
filename** — so "no such file exists on any tree today" is not narrowness. **Two files, one of
them honest, is a cheaper forgery than any of the four T375 had just closed.** Its recorded
mechanism — *"could match MORE THAN ONE path, and `member_mode` would be taken from whichever
line git printed first"* — was **exactly right**, and it is why T384 found this in twenty
minutes and why I could re-derive it from the description rather than from anyone's script.

---

## 1. THE MECHANISM, RE-MEASURED ON THIS TREE

Two tracked paths in the canonical guards directory:

* `…/zz-t404g1.sh` — an ordinary member with an **entirely honest** `REACHED-BY` row. Nothing
  about it is forged. It exists only so the pathspec matches **twice**.
* `…/zz-t404g[1].sh` — a tracked **SYMLINK**, the unwired checker being smuggled in.

`git ls-files` prints in byte order and `1` (0x31) sorts before `[` (0x5B):

    $ git ls-files -s -- ".../zz-t404g[1].sh"            # what the guard ran
    100644 587be6b4… 0	.../zz-t404g1.sh
    120000 909c4277… 0	.../zz-t404g[1].sh

    $ git ls-files -s -- ":(literal).../zz-t404g[1].sh"  # the ground truth
    120000 909c4277… 0	.../zz-t404g[1].sh

`member_mode` was therefore the decoy's `100644`, so **T375's symlink-member refusal never
fired**; and `member_blob` was the decoy's blob, so **T375's blob test compared the wrong
file**. The arm asserts both counts (2 as a pathspec, 1 as a literal) and that the `100644`
decoy sorts first, as a **precondition inside the mutation** — so the arm fails loudly rather
than measuring something else if this ever stops being true.

---

## 2. RED BEFORE GREEN — ARM G, WITH CONTROLS E AND F

All arms `dirty=no`. RED-BEFORE ref `5e5c3a61` (fix ABSENT), GREEN-AFTER on the fixed tree.
The drive **detects** which guard it is grading **from the ref's own blob** and refuses to be
told, so it cannot be lied to about the tree it is measuring.

| arm | RED-BEFORE (fix absent) | GREEN-AFTER (fix present) |
|---|---|---|
| **`G`** ambiguous glob + symlink member | **exit 0, PRESENT, `VERDICT: PASS`**, `population=8 … reached-by=3 … symlink-members=0` | **exit 2, ABSENT, `IS A SYMLINK`**, `population=8 … reached-by=2 … symlink-members=1` |
| `E` **control** — same filename shape, witness a **COPY**, no second match | exit 2, ABSENT, `BYTE-IDENTICAL`, `symlink-members=0` | **identical** |
| `F` **control** — same shape, member **IS** a symlink, one match only | exit 2, ABSENT, `IS A SYMLINK`, `symlink-members=1` | **identical** |
| `Z` **healthy control** — unmutated | exit 0, PRESENT, `population=6 … reached-by=1` | **identical** |
| `Y` **HEALTHY CONTROL** — honest checker, independent regular-file witness | **exit 0, PRESENT, ACCEPTED at `reached-by=2`** | **identical — still ACCEPTED** |
| `H` two symlink members | exit 2, ABSENT, `population=9 … symlink-members=1` | exit 2, ABSENT, `population=9 … **symlink-members=2**` |
| `W` ambiguous **witness** path | exit 2, ABSENT, `MORE THAN ONE TRACKED PATH` | **identical** |
| `N` C-quoted member path | exit 2, ABSENT, `IS INVOKED BY NOTHING`, `invoked-by-nothing=1` | exit 2, ABSENT, `TO NO INDEX ENTRY`, `invoked-by-nothing=0` |

**E AND F ARE NOT DECORATION, AND WITHOUT THEM THE FINDING IS MIS-STATED.** They use arm G's
filename **shape** without the second matching path and are **correctly REFUSED** in both
directions. git's pathspec matcher tries **exact literal equality before wildmatch**, so a
glob-named path always matches itself. **A glob character alone does not defeat this guard —
AMBIGUITY does.** Rejecting glob characters in filenames would have been the **wrong repair**:
it would refuse legitimate names and leave the hole open one spelling over.

**THE HEALTHY CONTROL IS THE ONE THAT MATTERS MOST FOR THIS CHANGE.** `Y` plants an honestly
registered checker whose witness is an **independent tracked regular file** — asserted
byte-different from the member by a precondition, so it is not surviving through T375's blob
refusal by accident. It is **ACCEPTED at `reached-by=2` in both directions.** A repair that
tightens what the guard will look at is nearest to the failure mode of **refusing a wired
checker**, and it does not.

---

## 3. THE P-22 EVIDENCE — R1, R2, R3

The repair is **two** changes, so one revert arm would not have shown which line carries it.

| arm | what it undoes | result |
|---|---|---|
| `R1` | `":(literal)$rel"` → `"$rel"`, multi refusal KEPT | **exit 2, ABSENT — `RESOLVES TO MORE THAN ONE INDEX ENTRY`**, `symlink-members=0` |
| `R2` | multi refusal disarmed, `":(literal)"` KEPT | **exit 2, ABSENT — `IS A SYMLINK`**, `symlink-members=1` |
| **`R3`** | **BOTH** | **exit 0, PRESENT, `VERDICT: PASS`, `reached-by=3`, `symlink-members=0` — THE HOLE REOPENS** |

`R3`'s census is **byte-identical to the pre-fix arm `G`**. Neither line is decoration; each is
independently sufficient against arm G, and the hole returns only when both are gone.

`R1` refuses with `symlink-members=0` **and that is correct**: the multi refusal fires *before*
the symlink test, so the member is refused without ever being classified as a symlink member.
Stated here so nobody reads that `0` as a miss.

---

## 4. C-T384-2 — `symlink-members` COUNTS, AND THE COUNT CAN RISE

The condition is stronger than "refuse the member", and it is asserted by its own column in the
arm runner rather than read by eye. **A fix that refused and still miscounted would pass an
exit-code-only arm.**

* **Arm `G`:** `symlink-members` **0 → 1** across the repair.
* **Arm `H`, on an UNCHANGED population of 9:** `symlink-members` **1 → 2**. Pre-fix the census
  counted only the symlink member that had **no decoy**, i.e. it was **undercounting by exactly
  the smuggled member** while printing a number a reader would believe.

**A count that cannot rise is a count nobody should read.** `H` is the arm that shows this one
can.

---

## 5. C-T384-3 — THE TWO RESTATED CARDINALS ARE **DELETED**, NOT REFRESHED

Recounted independently on the two blobs T375's own table names — pass 1 `2422adc9`, pass 2
`2c1f5723` — with `LC_ALL=C grep -c`:

| | T375 §6 said | **measured by T404** | reproduces? |
|---|---|---|---|
| `bad=1` | 20 → 23 | 20 → 23 | **yes — kept** |
| `return 1` | 84 → 84 | 84 → 84 | **yes — kept** |
| `EXIT_UNUSABLE` | 23 → 23 | 23 → 23 | **yes — kept** |
| `warn "` | 366 → 396 | **367 → 405** | **NO — deleted** |
| `say "` | 137 → 137 | **139 → 139** | **NO — deleted** |

**This is T384's measurement independently reproduced**, and only the two rows it named are
wrong. **The load-bearing claim — no refusal path was removed — is TRUE and is not withdrawn**;
`bad=1` rose by three and nothing else moved. Both rows are **deleted from §6** with the
recount command left in their place, and the **same figure restated in §5 is marked withdrawn**
rather than refreshed. Deleting one copy and refreshing the other is exactly the rot `P-80`
names; that is why §5 moved too. This is the remedy `DEC-2` revision 8 chose for the same shape.

**My own change's cardinals, stated once, with the command rather than the number as the
record** — `LC_ALL=C grep -c 'warn "' .softhouse/conformance.sh`: `warn "` 405 → **422**,
`say "` 139 → **145**, `bad=1` 23 → **25**, `return 1` **84 → 84**, `EXIT_UNUSABLE` **23 → 23**.
**No refusal, no `exit` and no `return` was removed;** two lines were replaced in place.

---

## 6. EXACTLY WHICH `conformance.sh` SYMBOLS I TOUCHED

**All of them inside `guard_guards_dir_registration`. Cite by NAME — every identifier is unique
in the file and `grep -n` re-derives it in one command.**

1. `local … member_multi` — the declaration line gained one name.
2. `member_stat=""; member_mode=""; member_blob=""; member_multi=0` — the initialiser.
3. the `member_stat=` assignment — `git ls-files -s -- "$rel"` becomes
   **`git ls-files -s -- ":(literal)$rel"`**.
4. a new `case "$member_stat" in *"$CONF_LF"*) member_multi=1 ;; esac` — no pipeline, no second
   process, for the reason `P-57` gives and this function keeps everywhere else.
5. a new refusal **`RESOLVES TO MORE THAN ONE INDEX ENTRY`** — the `self_multi` shape the
   witness side of this same function already has.
6. a new refusal **`RESOLVES … TO NO INDEX ENTRY`** — because if a host's git ever ignored or
   rejected `:(literal)` the lookup would come back **empty**, and an empty `member_stat` skips
   the symlink test *and* the blob test at once, which is the identical disablement arm G buys
   by ambiguity.
7. **six `say` lines** appended to the `GUARDS-DIR-REGISTRATION` census explanation, after the
   existing selector block.

**`EXEMPTION_PIN_LEDGER_WRONGIMPLS` — NOT TOUCHED. It reads 14.** My insertion moved it
**`:4476` → `:4551` (+75)**. **T391 must match it BY NAME.** Nothing else in the file was
edited: no pinned count, no other guard, no ledger or money path.

**THE CENSUS LINE'S SHAPE IS UNCHANGED.** `symlink-members=N` remains the **last** field, so
every T323 / T358 / T375 arm that matches that line by a substring ending at
`invoked-by-nothing=N` is untouched — appending cannot retune an older arm where a new field in
the middle would have.

---

## 7. FINAL BAR — CLEAN COMMITTED TREE

`git status --porcelain` **EMPTY *before* the run**, `bash` and never `sh`. **P-84: the probe
line's PRESENCE was established before its value — `grep -c 'probe = '` is `1`.**

| | |
|---|---|
| **exit** | **0** |
| **probe** | **PRESENT ×1**, reading `up` |
| **VERDICT** | **PASS — 46 parity vectors, 7884 cells** |
| guards-dir census | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` |
| dead-path census | `corpus=1396 deadFiles=75` **`deadOccurrences=108`** |
| fail-open frontier | **11 == pinned 11**, GREEN |
| ledger | parity FAIL **7** + oracle-refusal FAIL **0** on the wrong implementation |
| ledger cells | **144** graded, **39** MONEY in int64 minor units |
| wrong implementations | **all 14** died through the harness |
| `EXEMPTION_PIN_LEDGER_WRONGIMPLS` | **14**, by name, `:4551` |
| guard cost | `guard_guards_dir_registration` 0 s / ceiling 60 s |
| P-number citations | VERDICT PASS |

**`corpus` 1395 → 1396 is EXACTLY my `drive-red-t404.sh` entering T316's corpus, and
`deadOccurrences` did NOT move.** Every planted path in the drive is **assembled at run time**
from `$GUARDS_REL` plus a leaf variable — no `.softhouse/`-rooted literal in it fails to
resolve. **No pin regeneration is required by this branch.**

**Census-bait check, done by measurement rather than intention** (T401 reddened the bar four
times with its own prose): every `.softhouse/`-rooted literal in my `conformance.sh` diff is
`.softhouse/conformance.sh`; the drive adds `.softhouse/patterns.md` and bare `.softhouse/`.
All resolve. Every P-number I cite is defined — `P-22` at `patterns.md:473`, `P-84` at `:2813`.

---

## 8. A DEFECT IN MY OWN INSTRUMENT, FOUND BY TWO TRANSCRIPTS DISAGREEING

**This is the most useful thing in this handoff after the finding itself.** Two invocations of
my drive overlapped. Both used `/tmp/t404-drive/<ARM NAME>`, so each `rm -rf`'d the other's
scratch checkout **mid-bar**. Arms `H` and `W` came back **`exit=2 probe=ABSENT
census=<none printed>`** — which reads **exactly like a clean REFUSAL** and was really a deleted
tree. The tell was not the verdict; it was **BSD `sed` aborting** (`Assertion failed:
(advance > 0) … process.c, line 462`) while printing the tail.

**A harness whose failure mode is indistinguishable from the finding it hunts is the shape this
whole task exists to refuse.** The work root is now `/tmp/t404-drive/run-$$-<epoch>` and an
existing root is a **REFUSAL, never a reuse**. **Both conflicting transcripts stay committed,
unedited** (`evidence/10`, `evidence/11`) — a transcript that only survives when it agrees with
you is not evidence — and **neither corrupted row is claimed as a result**. `H`, `W` and `N`
were re-driven clean under the repair (`evidence/12`, `evidence/13`).

**The general lesson: exit 2 with a plausible refusal text is not self-validating.** The census
column is what caught this — `<none printed>` cannot be produced by any refusal in this guard
that reaches the census line.

---

## 9. T401's REQUEST A3/A4 — ADJUDICATED, NOT APPLIED

**COMPATIBLE with the `:(literal)` repair, and orthogonal to it.** A3 edits the **selector**
(the `pop="$( … git ls-files -- …` pathspec list) at **`:3266-3269`, which my change does not
move** — my edit sits ~190 lines below it. A3 decides **which paths enter the population**; my
repair decides **how each `$rel` is resolved once it is in**. Different call, different
question, no interaction.

**A3 makes the repair strictly more valuable**: a `.zsh` checker can carry a glob character in
its name exactly as an `.sh` one can, so without `:(literal)` the widened population would
inherit this fail-open on day one. A3 also cannot reintroduce the ambiguity — its `:(glob)` is
a selector over a wildcard pattern; my `:(literal)` is over one concrete path.

**THE ONE HAZARD FOR WHOEVER LANDS IT: A4's ANCHOR MOVED, A3's DID NOT.** A4's two `say` lines
were `:3865`; they are now **`:3934-3935`**. The restated-prose sites likewise: `:3048`
unmoved, `:3453` → **`:3454`**, `:3860-3862` shifted by the same +75. **Apply A4 by CONTENT,
never by line** — the identical rot the by-name pin rule exists for.

---

## 10. WHAT I DID **NOT** CLOSE — inherited honestly, and added to

**Carried forward from T384, still not driven by anyone including me:**

* **`FU-T375-5`, the `DECLARED` direction.** Reasoned about by T375 and T384; **driven by no
  arm in any generation.**
* **Behaviour on a case-SENSITIVE filesystem.** This host is case-insensitive
  (`core.ignorecase=true`). I did not obtain a case-sensitive host.
* **`guard_graded_root_is_this_tree`'s short-circuit path** — still driven by **no arm in any
  generation**, T404 included.
* **A member path containing a NEWLINE, and a gitlink/submodule entry ending in `.sh`.**
  **PARTIALLY closed, and I claim only the part I drove.** Arm `N` drives the **C-quoted**
  member path (a non-ASCII byte) and it now refuses accurately instead of falling through to
  `INVOKED BY NOTHING`. A newline additionally breaks the `while IFS= read -r rel` loop itself,
  which arm `N` does **not** exercise. **Not driven, and I am not claiming it is safe.**

**New, disclosed against myself:**

* **`FU-T404-1` — the WITNESS side's second lookup, `git ls-files -s -- "$self_norm"` at
  `:3677`, is still a PATHSPEC.** I did **not** change it, deliberately. I could not construct
  an arm that reaches it: to make it ambiguous you need `--error-unmatch -- "$self_wit"` to
  return one line while `-s -- "$self_norm"` returns two, and every spelling I tried is caught
  first — the literal spelling trips `self_multi`, and every non-literal spelling (`?`-globbed,
  bracket-escaped, magic-prefixed) fails the `-f` test on the **typed** spelling, which runs
  before normalisation and which T375 deliberately left there. **REASONED, NOT DRIVEN.** Arm
  `W` drives the one construction that *is* reachable and confirms it is already refused.
  **I did not make the one-token change, because a one-token change without its arm is exactly
  what this lineage refuses** — the same call T375 made, for the same reason, and I am
  recording it the same way rather than quietly tightening a line I cannot test.
* **The `member_none` branch is driven only by arm `N`'s C-quoting route**, not by an actual
  `:(literal)`-unsupporting git. I have no such git to test on.

**Nothing about money, the ledger, a vector, a DEC-n or the frozen adapter contract is touched
by this branch.** Every change is to the bar's own coverage of itself.

---

## 11. HOW TO REPRODUCE EVERY CLAIM

    # the mechanism, in two commands, inside any arm-G scratch clone
    git ls-files -s -- '.softhouse/guards/zz-t404g/zz-t404g[1].sh'
    git ls-files -s -- ':(literal).softhouse/guards/zz-t404g/zz-t404g[1].sh'

    # any arm, either direction. The drive DETECTS fixed/unfixed from the ref's own blob.
    bash .softhouse/capture/t404-t384-conditions/drive-red-t404.sh <repo> <ref> [arm ...]

    # the fifth fail-open, before and after
    #   ... <repo> 5e5c3a61 T404-G-AMBIGUOUS-globname-symlink-member-FAILOPEN   -> exit 0, VERDICT PASS
    #   ... <repo> HEAD     T404-G-AMBIGUOUS-globname-symlink-member-REFUSED    -> exit 2, IS A SYMLINK

    # the P-22 arm: does the fix carry its own weight?
    #   ... <repo> HEAD     T404-R3-REVERT-BOTH-THE-HOLE-REOPENS                -> exit 0, the hole returns

    # C-3, recounted rather than read (367 then 405)
    git show 2422adc9:.softhouse/conformance.sh | LC_ALL=C grep -c 'warn "'
    git show 2c1f5723:.softhouse/conformance.sh | LC_ALL=C grep -c 'warn "'

**Evidence, complete and unedited**, in `.softhouse/capture/t404-t384-conditions/evidence/`:
`00` baseline bar · `10`/`11` the two conflicting transcripts of the collision, kept · `12`/`13`
`H`/`W`/`N` re-driven clean · `20` `R3` · `21` `R1`/`R2` · `22` `G`+`H` · `23` `Z`/`Y` ·
`24` `E`/`F` · `25` `W`/`N` · `30` the final bar.
