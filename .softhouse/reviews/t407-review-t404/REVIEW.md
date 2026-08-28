# T407 — INDEPENDENT REVIEW OF T404 (`softhouse/T404-t384-conditions`)

**Reviewer:** T407. **Subject:** T404, closing `FU-T375-7` / `F-T384-1` — the fifth
registration fail-open in `guard_guards_dir_registration`.
**Method:** re-derived from T384's and T404's PROSE, on my own drive
(`.softhouse/reviews/t407-review-t404/drive-t407.sh`), with **different filenames and a
different glob metacharacter** — T404 used a bracket expression `zz-t404g[1].sh`, I used a
question mark `zz-t407g?.sh`. I did not run T404's script to establish any claim in this review.

---

## VERDICT

# APPROVED WITH CONDITIONS

**The fix is real, correctly scoped, correctly motivated, and its red-before/green-after is
sound.** I reproduced the pre-fix green **on today's `main`**, reproduced all three P-22 revert
arms, confirmed both healthy controls stay ACCEPTED, confirmed the census count can RISE, and
independently re-measured every cardinal in C-3. **Nothing T404 claims as a result failed to
reproduce.** 14 of my arms PASS on the fixed tree, 9 on the unfixed tree, 0 FAIL.

**And the residual T404 disclosed against itself is REACHABLE.** `FU-T404-1` — the witness-side
lookup `git ls-files -s -- "$self_norm"` at `:3677` — is **not** unreachable. **Arm `X` drives
the whole bar to `exit 0`, `probe PRESENT`, `VERDICT: PASS` on T404's OWN FIXED TREE**, with an
unwired planted checker **ACCEPTED at `reached-by=2` and vouched for by a SYMLINK TO ITSELF.**
T404 declined a one-token change on the ground that it could not build an arm. It could have;
the severity call is now **wrong for the third generation running**.

I am not rejecting, and the reason matters. **T404's change is a strict improvement that
regresses nothing, and the residual is T375's defect, not T404's** — T404 inherited it, named
it, gave its exact line number, and described the mechanism precisely enough that I found the
route in half an hour. Discarding a correct, well-driven fix because it did not also close a
neighbouring hole would be the worse trade. **But the branch must not be cited as closing this
class**, and `C-T407-1` is drivable with arms already committed here.

| condition | severity | drivable by |
|---|---|---|
| **`C-T407-1`** close `FU-T404-1` — pin the witness lookup to `:(literal)` | **MAJOR** | arms `X` / `XS` / `XC` / `XF` / `XFY`, in this grant, runnable today |
| **`C-T407-2`** delete the seven rotted line cardinals at `conformance.sh:3169-3175` | MODERATE | `sed -n '4090p;4109p;4140p;4143p;4585p;4610p;4611p'` on both blobs |
| **`C-T407-3`** §3 — say that `member_multi` is unreachable on a conforming git | MINOR | reading, plus arm `R1` |
| **`C-T407-4`** §8 — one sentence overstated, and a SECOND corruption is unnamed | MINOR | `evidence/10` and `evidence/11`, as committed |

---

## 1. I REPRODUCED THE PRE-FIX GREEN MYSELF, ON TODAY'S TREE, WITH A DIFFERENT FORGERY

Ref `5e378102` — **today's `main`**, not T404's private RED-BEFORE ref `5e5c3a61`. My arm `G`
plants an **honest** decoy `zz-t407g1.sh` and a tracked **symlink** `zz-t407g?.sh`. `1` (0x31)
sorts before `?` (0x3F) exactly as it sorts before `[` (0x5B), so the decoy is line 1.

    T407-Z-healthy-UNMUTATED                   exit=0 probe=PRESENT  >>> PASS
        census: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0
    T407-G-AMBIGUOUS-symlink-member-FAILOPEN   exit=0 probe=PRESENT  >>> PASS
        census: population=8 invoked=3 declared=2 reached-by=3 invoked-by-nothing=0 symlink-members=0

**Whole bar `exit 0`, probe PRESENT, `VERDICT: PASS`, a tracked symlink credited
`reached-by=3`, and `symlink-members=0` printed with that symlink member in the population.**
Post-fix the same arm is `exit 2, ABSENT, IS A SYMLINK, symlink-members=1`.

**The fix is motivated, and the finding is not an artefact of bracket syntax.** The mechanism is
pathspec **AMBIGUITY**, and it reproduces on any metacharacter that can match a sibling.

## 2. THE P-22 TRIPLE — ALL THREE RE-DRIVEN, AND ONE CLAIM NEEDS QUALIFYING

| arm | result (my drive, ref `31b7e1f6`) |
|---|---|
| `R1` revert `:(literal)` only | `exit 2, ABSENT, RESOLVES TO MORE THAN ONE INDEX ENTRY`, `symlink-members=0` |
| `R2` disarm multi refusal only | `exit 2, ABSENT, IS A SYMLINK`, `symlink-members=1` |
| **`R3` revert BOTH** | **`exit 0, PRESENT, VERDICT: PASS`, `population=8 … reached-by=3 … symlink-members=0`** |

**`R3`'s census is byte-identical to my own pre-fix arm `G` above** — `population=8 invoked=3
declared=2 reached-by=3 invoked-by-nothing=0 symlink-members=0`. The hole reopens exactly, and
only when both lines are gone. **T404's claim that each half is independently sufficient is
TRUE and I measured it.**

**`F-T407-3` (MINOR) — "neither is redundant" needs one qualification.** Against arm `G` each
half suffices; that is measured. But on any git that honours `:(literal)` — 1.9 and later, i.e.
every git this program will meet — **the `member_multi` branch cannot fire**, because a literal
pathspec matches at most one index entry. Its only driven route is `R1`, which is a *synthetic
revert of the very line that makes it unreachable*. That does not make it decoration: it is the
fail-closed backstop for a git that ignores the magic, and T404's in-code comment argues for it
correctly and pairs it with the `member_none` branch for the same reason. **The handoff's §3
wording, read alone, invites a later reader to treat `R1` as evidence of a live path.** Say it
is unreachable-by-construction and kept deliberately, so nobody later deletes it as dead code
or cites it as coverage.

Note also, and correctly stated by T404: `R1` refuses with `symlink-members=0` because the multi
refusal fires *before* the symlink classification. I re-measured that and it is not a miss.

## 3. THE WRONG REPAIR STAYED NOT-MADE — CONFIRMED BY READING **AND** BY DRIVING

**The diff rejects no glob character anywhere.** The only two predicates added are
`case "$member_stat" in *"$CONF_LF"*)` — an embedded newline, i.e. *more than one line of
output* — and `[ -z "$member_stat" ]`. Neither inspects the filename. I read the whole hunk;
there is no character class, no `case` on `*[*?[]*`, nothing of the shape.

Driven, on both refs:

* `E` — glob-named member, witness a plain **COPY**, one match → `exit 2, BYTE-IDENTICAL`.
* `F` — glob-named member **IS** a symlink, one match → `exit 2, IS A SYMLINK`,
  `symlink-members=1`.

**Both are correctly REFUSED, and both are refused for their OWN reason, unchanged across the
repair.** git's pathspec matcher tries exact literal equality before wildmatch, so a glob-named
path always matches itself; **a legitimate filename carrying `?` or `[` is not grounds for
refusal here, and is not refused.** T404's framing is exactly right and E/F are load-bearing
rather than decorative.

## 4. THE HEALTHY CONTROLS — NOT INVERTED

`Y` plants an honestly registered checker whose witness is an **independent tracked regular
file** (asserted byte-different from the member by a precondition inside the mutation, so it is
not surviving via the blob refusal by accident).

    T407-Y-healthy-honest-witness-ACCEPTED   exit=0 probe=PRESENT  >>> PASS   (both refs)
        census: population=7 … reached-by=2 … symlink-members=0

**ACCEPTED at `reached-by=2` on the unfixed tree, on the fixed tree, and — arm `XFY` — under the
witness-side repair I am asking for in `C-T407-1` as well.** `Z`, the unmutated control, is
`exit 0` with the baseline census in every direction. **This is not a control that refuses
everything (`P-98`, `.softhouse/patterns.md:3411`), and the inversion this fire produced once
before has not recurred here.**

## 5. `C-2` — THE COUNT RISES, AND THE LINE SHAPE DID NOT MOVE

| arm `H` (two symlink members, population unchanged) | `symlink-members` |
|---|---|
| ref `5e378102` (unfixed) | `population=9 … symlink-members=1` |
| ref `31b7e1f6` (fixed) | `population=9 … **symlink-members=2**` |

**The population is identical and the count changes**, so pre-fix the census was undercounting
by exactly the smuggled member while printing a number a reader would believe. **A count that
cannot rise is a count nobody should read; this one can.**

**The census line's SOURCE is byte-identical between `main` and T404's branch** — I diffed it:

    main :3864   say "conformance:   GUARDS-DIR-REGISTRATION: population=$total invoked=$invoked declared=$decl_ok reached-by=$selfdecl invoked-by-nothing=$unwired symlink-members=$symlinked"
    T404 :3933   (identical string; only the line number moved, +69)

`symlink-members=N` is still the **last** field. Every older arm that matches this line by a
substring ending at `invoked-by-nothing=N` is untouched. **Downstream readers do not break.**

## 6. `F-T407-1` — **`FU-T404-1` IS REACHABLE. MAJOR.**

**This is the finding of this review.** T404 wrote:

> *"I could not construct an arm that reaches it … every spelling I tried is caught first — the
> literal spelling trips `self_multi`, and every non-literal spelling (`?`-globbed,
> bracket-escaped, magic-prefixed) fails the `-f` test on the TYPED spelling."*

**The first two clauses are true. The third is not.** `-f` runs on
`"$REPO_ROOT/$self_wit"`, and when `$self_wit` carries a pathspec magic prefix that string is
**an ordinary relative filesystem path** — `<repo>/:(literal).softhouse/guards/…/w?.txt`.
An attacker who is already planting files **simply creates it**: a real, tracked directory
literally named `:(literal).softhouse`. Then `-f` passes, and the two git calls disagree
because only one of them carries the magic:

    $ git ls-files --error-unmatch -- ":(literal).softhouse/guards/zz-t407x/w?.txt"
    .softhouse/guards/zz-t407x/w?.txt                     # ONE line -> self_multi NEVER FIRES

    $ git ls-files -s -- ".softhouse/guards/zz-t407x/w?.txt"    # the second lookup, :3677
    100644 <blob> 0  .softhouse/guards/zz-t407x/w1.txt    # the DECOY, 0x31 sorts before 0x3F
    120000 <blob> 0  .softhouse/guards/zz-t407x/w?.txt    # the SYMLINK the guard should refuse

`self_mode` becomes the decoy's `100644` and `self_blob` the decoy's object, so **T375's
symlink-WITNESS refusal and T375's byte-identical-blob refusal are disabled at the same time** —
the identical disablement T404 closed one call earlier on the member side. The closing
`grep -qF -- "$base" "$REPO_ROOT/$self_norm"` then dereferences the symlink to the member and
finds the member's own name.

**Driven, on ref `31b7e1f6` — T404's OWN FIXED TREE:**

    T407-X-WITNESS-ambiguity-FAILOPEN         exit=0 probe=PRESENT  VERDICT: PASS   >>> PASS
        census: population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0 symlink-members=0

and the guard printed, at `evidence/40`, line 157:

    conformance:     REACHED-BY .softhouse/guards/zz-t407x/zz-t407x-member.sh — declared in its own header, reached by
    conformance:                .softhouse/guards/zz-t407x/w?.txt (verified: it names zz-t407x-member.sh)

**"(verified: it names …)" — where the witness is a symlink to the member itself.** An unwired
checker lands GREEN by vouching for itself, which is the exact amnesty this direction exists to
refuse and the exact sentence T375's own refusal text describes.

**THE CONTROLS, so this is not mis-stated as "magic characters break the guard":**

| arm | change from `X` | result |
|---|---|---|
| `XS` | **no decoy** — the witness resolves to one entry | `exit 2, ABSENT, THAT WITNESS IS A SYMLINK` |
| `XC` | **plain typed spelling** instead of the magic one | `exit 2, ABSENT, MORE THAN ONE TRACKED PATH` |
| `X`  | magic spelling **and** decoy | **`exit 0`, ACCEPTED** |

**The symlink-witness refusal is alive (`XS`). The plain route is genuinely closed, exactly as
T404 says (`XC`). AMBIGUITY REACHED THROUGH A MAGIC SPELLING is the whole of the defect** — one
variable between the refused control and the accepted forgery.

**THE REPAIR IS ONE TOKEN AND I DROVE IT** (in a scratch clone only — I did not edit
`.softhouse/conformance.sh`):

    -            git ls-files -s -- "$self_norm" 2>/dev/null )" || self_stat=""
    +            git ls-files -s -- ":(literal)$self_norm" 2>/dev/null )" || self_stat=""

    T407-XF-witness-literal-REPAIR-REFUSES-X      exit=2 ABSENT  THAT WITNESS IS A SYMLINK  >>> PASS
    T407-XFY-healthy-Y-UNDER-the-repair-ACCEPTED  exit=0 PRESENT reached-by=2               >>> PASS

**Sufficient, and it refuses nothing legitimate.** `evidence/41` line 157 shows T375's own
refusal firing on arm `X` once the lookup is pinned.

**WAS SHIPPING A REASONED-NOT-DRIVEN RESIDUAL RIGHT? The process was right; the sentence was
not.** Declining to ship a one-token change without its arm is the correct instinct and I would
not have it otherwise — it is the same call T375 made and T404 says so explicitly. What is
wrong is that T404 recorded a **bound on the defect** ("every spelling is caught first") when
what it had was a **bound on its own search** ("I did not find one"). Those read identically to
a later reader and only one of them is true. **This is the third generation of the same
inversion in this lineage — T375 disclosed the member-side hole and rated it unreachable, T384
reached it in twenty minutes; T404 disclosed the witness-side hole and rated it unreachable, I
reached it in about thirty.** The disclosure quality is *why* both were found that fast, and it
is the best thing about both handoffs. The lesson is not "disclose less" — it is **"an
unreached hole is UNREACHED, never UNREACHABLE,"** and the honest form of §10's bullet is a
statement about the searcher.

## 7. `F-T407-2` — T404's `+75` ROTTED SEVEN LINE CITATIONS IN ITS OWN FILE. MODERATE.

`conformance.sh:3169-3175` is the `P-45` block that carries the **standing structural evidence
for `P-84`** — that no path exists on which a HARD guard fails and the probe line still prints.
It cites seven line numbers. **T404's insertion moved every one of them by `+75` and none was
updated.** Measured, both blobs, same seven line numbers:

| cited as | `main` has | **T404's branch has** |
|---|---|---|
| `:4090` `run_guards` DEFINED | `run_guards() {` | `"` |
| `:4109` short-circuit exit | `exit "$EXIT_UNUSABLE"` | a `warn` about guard-cost selectors |
| `:4140` `guard_cost_census` call | `guard_cost_census … \|\| failed=1` | `stale=$((stale + 1))` |
| `:4143` tally exit | `exit "$EXIT_UNUSABLE"` | a `warn` about a never-timed guard |
| `:4585` the single call site | `run_guards` | `return 1` |
| `:4610` `probe_oracle` invoked | `probe="$(probe_oracle)"` | `if [ "$bad" -ne 0 ]; then` |
| `:4611` the probe line printed | the `say` that prints it | `warn "conformance:"` |

**Seven citations to nothing, in the file T404 edited, in the block that says of ITSELF "THIS
BLOCK HAS NOW ROTTED TWICE INSIDE ONE TASK" and "MATCH BY NAME, NEVER BY LINE."** That makes
this the third rot. It is `P-80` (`patterns.md:2775`) and `P-86` (`:2854`) in the file that
names them.

Two things sharpen it rather than excuse it. T404's §6 says *"Cite by NAME — every identifier is
unique in the file"* and claims to enumerate exactly what it touched; §9 warns the next task
*"Apply A4 by CONTENT, never by line"* **because** the anchors moved `+75`. **T404 knew the
shift, warned others about it, and did not apply the rule to the seven cardinals sitting inside
its own diff's blast radius.** And nothing catches it: the bar's `P-number citations` guard
grades `P-<n>` tokens against `patterns.md`, not `conformance.sh` self-citations, so the run was
green.

**`C-T407-2`: DELETE the seven cardinals, do not refresh them** — the remedy T404 itself argued
for and applied in `C-3`, leaving `grep -n run_guards` in their place. Refreshing buys one cycle
and hands the next reader seven numbers to re-verify instead of one command to run.

**I checked the blast radius.** Of the live instruments — `conformance.sh`, `patterns.md`,
`.softhouse/guards/**` — **only `conformance.sh` carries a line citation into the shifted
region.** Handoffs cite it too, but a handoff is a record of its own moment and this program
does not rewrite them.

## 8. `F-T407-4` — THE INSTRUMENT DEFECT: THE HONESTY IS EXCELLENT, ONE SENTENCE IS TOO STRONG, AND A SECOND CORRUPTION IS UNNAMED. MINOR.

**What T404 did right, and it should be copied.** Both conflicting transcripts are committed
**unedited** (`evidence/10`, `evidence/11`). **Neither corrupted row is claimed as a result** —
I checked the handoff's arm table against the re-driven transcripts and it carries
`evidence/12`'s and `evidence/13`'s values, not `evidence/10`'s: `H` = `population=9 …
symlink-members=1`, `W` = `MORE THAN ONE TRACKED PATH`, `N` = `invoked-by-nothing=1`. **I
independently reproduced `H` RED-BEFORE at `population=9 … symlink-members=1`.** The work root
is now `run-$$-<epoch>` and an existing root is a refusal, which I adopted verbatim in my own
drive rather than re-learning it.

**Where the account is too strong.** §8 opens with the claim that `H` and `W` came back
`exit=2 probe=ABSENT census=<none printed>` and that this *"reads exactly like a clean
REFUSAL."* The committed transcript disagrees with the sentence: `evidence/10` scores both rows

    marker=NO  census=NO  dirty=no  >>> FAIL

**The instrument DID distinguish them, in its own verdict column, at the time.** That is what
§8's *closing* sentence says correctly — *"the census column is what caught this"* — so the
handoff contradicts itself by one paragraph, in the safe direction. Fix the opening sentence:
the fields looked like a refusal, **the arm did not pass**.

**What is unnamed.** `evidence/11` records a **second and different corruption** that §8 does
not mention: the drive script was **edited while `bash` was executing it**, so the interpreter
resumed at a stale byte offset —

    drive-red-t404.sh: line 501: r: command not found
    drive-red-t404.sh: line 521: syntax error near unexpected token `fi'

That is not the shared-work-root defect; a unique work root does not prevent it. **A drive
script must be frozen before it is run**, and the hazard belongs in the record next to the one
that was named. It is the same `P-98` shape — a corrupted run that can look like a verdict.

## 9. `C-3` — RE-MEASURED FROM SCRATCH; T404's RECOUNT REPRODUCES, T375's DOES NOT

`LC_ALL=C grep -c` on the two blobs T375's own table names, pass 1 `2422adc9`, pass 2 `2c1f5723`:

| | T375 §6 said | T404 measured | **T407 measured** | |
|---|---|---|---|---|
| `bad=1` | 20 → 23 | 20 → 23 | **20 → 23** | reproduces — kept, correctly |
| `return 1` | 84 → 84 | 84 → 84 | **84 → 84** | reproduces — kept, correctly |
| `EXIT_UNUSABLE` | 23 → 23 | 23 → 23 | **23 → 23** | reproduces — kept, correctly |
| `warn "` | 366 → 396 | 367 → 405 | **367 → 405** | **T375 wrong, T404 right — deleted, correctly** |
| `say "` | 137 → 137 | 139 → 139 | **139 → 139** | **T375 wrong, T404 right — deleted, correctly** |

**AND I VERIFIED THE LOAD-BEARING CLAIM DIRECTLY, NOT VIA THE CARDINALS.** Counts can net out;
a removal plus an addition leaves a total unmoved. So I read the pass-1 → pass-2 diff itself:
**18 content lines are removed. Exactly four are executable** — three `warn` continuation lines
inside an existing refusal message, and the one `say` census line that was replaced by the
version carrying `symlink-members`. **Zero removed lines carry `bad=1`, `return 1`,
`EXIT_UNUSABLE`, `exit` or `continue`** outside a comment (the two apparent hits are both `#`
lines). **"No refusal path was deleted" is independently TRUE and is correctly not withdrawn.**

**Deletion was the right remedy, not a refresh.** `P-80` (`patterns.md:2775`) says a corrected
cardinal rots in every place it was restated, and this cardinal had already been restated twice
in one handoff — §5 and §6. Refreshing `396` to `405` would have left a number that the next
edit to `conformance.sh` invalidates again; the recount command does not go stale. **Marking §5
withdrawn rather than refreshing it was also right**, and it is precisely the treatment `DEC-2`
revision 8 gave the same shape. Note the small irony recorded in `F-T407-2`: T404 applied this
rule rigorously to someone else's cardinals and not at all to the seven line numbers its own
insertion invalidated.

## 10. SCOPE

**Every change is inside `guard_guards_dir_registration`.** The function spans `:3219` to
`:3961` on T404's blob; the three diff hunks are at `:3378` (one `local` name), `:3454-3533`
(the lookup, the two refusals) and `:3944` (six `say` lines). **The next top-level function
begins at `:4068`.** Nothing else in `conformance.sh` is touched.

**`EXEMPTION_PIN_LEDGER_WRONGIMPLS` — NOT TOUCHED, reads `14`, now at `:4551`** (`:4476` on
`main`, `+75`). **T391 must match it BY NAME.** No pinned count, no other guard, no ledger or
money path is in the diff.

**Nothing in this branch touches money, the ledger, a vector, a DEC-n or the frozen adapter
contract.** No floating point is introduced anywhere; the diff contains no arithmetic at all.
No database driver, dialect or port appears in it.

**Anything that cites by line:** see `F-T407-2`. Inside the live instruments only the
`conformance.sh:3169-3175` block broke. The `say`-line anchors T404 flags for T401's A4
(`:3865 → :3934-3935`) are content, not citations, and T404's own §9 handles them correctly.

## 11. NOT CLOSED, AND T404 SAYS SO — I AM NOT TREATING SILENCE AS COMPLETION

Still open after this branch, unchanged and correctly declared by T404:

* **`FU-T375-5`, the `DECLARED` direction** — driven by no arm in any generation, mine included.
* **A case-SENSITIVE filesystem.** This host is `core.ignorecase=true` and I did not obtain one
  either.
* **`guard_graded_root_is_this_tree`'s short-circuit** — driven by no arm in any generation.
* **A member path containing a NEWLINE, and a gitlink/submodule entry ending in `.sh`.** T404's
  arm `N` covers only the C-quoted route and claims only that; the newline additionally breaks
  the `while IFS= read -r rel` loop, which no arm exercises.
* **The `member_none` branch** is driven only through `N`'s C-quoting route, never by a git that
  actually lacks `:(literal)`.

**New, from this review:**

* **`FU-T407-1`.** My `C-T407-1` repair pins `-s -- ":(literal)$self_norm"`, but `self_norm`
  itself is the OUTPUT of `git ls-files --error-unmatch -- "$self_wit"`, which is **still a
  pathspec**, and for a C-quotable witness path that output arrives wrapped in literal double
  quotes — the same shape as the member-side case T404 drove as arm `N`. **Reasoned, not
  driven.** I am recording it as a bound on my own search and not on the defect.

## 12. MY ARMS AND MY EVIDENCE

`bash .softhouse/reviews/t407-review-t404/drive-t407.sh <repo> <ref> [arm …]`. The drive
**detects** fixed/unfixed from the ref's own blob and cannot be told which tree it is grading.
Every arm clones `--no-hardlinks`, mutates, `git add -A` **and commits**, asserts `dirty=no`, and
runs the **whole bar** with `bash`. Probe **presence** is read before its value (`P-84`,
`patterns.md:2813`). Preconditions — match counts, first-line mode, byte-difference of witness
and member — are **asserted inside the mutation**, so an arm that stopped measuring what it
claims fails loudly.

* `evidence/10-RED-BEFORE-all-arms-on-todays-main.txt` — 9 arms, ref `5e378102`.
* `evidence/20-GREEN-AFTER-all-14-arms-on-T404-fixed-tree.txt` — 14 arms, ref `31b7e1f6`.
* `evidence/40-X-FAILOPEN-full-bar-transcript.txt` — the whole `VERDICT: PASS` bar for arm `X`.
* `evidence/41-XF-one-token-repair-REFUSES-X.txt` — the same forgery, refused.
* `evidence/50-FINAL-BAR-clean-committed-tree.txt` — my bar.

**Totals: 23 arm runs, 23 PASS / 0 FAIL** — 9 RED-BEFORE, 14 GREEN-AFTER.

## 13. MY BAR

Recorded in `evidence/50-FINAL-BAR-clean-committed-tree.txt`, run with `bash` on a clean
committed tree with `git status --porcelain` empty **before** the run. My branch is a review
branch off `main`, so it does **not** carry T404's fix; the baseline it must hold is `main`'s.
The figures are in that file and in the summary below.
