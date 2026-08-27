# A2-33 — independent review of DEC-2 **revision 5**

**Task:** `A2-33`, run `2026-08-21-run2-tierA-gl-accounting-A2`
**Role:** INDEPENDENT REVIEWER. I did not plan or author revision 5.
**Branch:** `softhouse/A2-33-review-dec2-rev5`
**Subject:** `docs/adr/DEC-2-gl-accounting-adapter.md` at revision 5 (commit `cab9e82`, merged to `main` at `a7b828a`)
**Reviewer fork point:** `git merge-base main HEAD` = **`8f193b5`** — identical to the dispatch commit
the brief named. [VERIFIED: run in this worktree. The brief's warning about `P-71` is confirmed: a
worktree forks from the DISPATCH commit. `A2-32` hit the same thing from the other side and said so.]
**Review HEAD:** `8f193b5`. **Pinned reference oracle (Fineract):** `/Users/buv/fineract` @
`426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED: `git -C /Users/buv/fineract rev-parse HEAD`;
working tree clean].

---

## VERDICT

# APPROVED

**Revision 5 fixes exactly `A2-31`'s F-1 and F-2, both corrections are substantively TRUE on my own
independent re-measurement, the correction landed at all nine sites `A2-32` names, I found no tenth
live site with an instrument I calibrated to 17/17 recall on a known positive, every `[VERIFIED]`
and `[MEASURED]` stamp in the revision is true AT ITS OWN STAMP, and `A2-32` authored nothing beyond
`A2-31`'s two items.**

**I am NOT authorised to ratify G-11 and I do not.** This review is the input the driver needs; the
ratification decision is the driver's, under `CLAUDE.md`'s "DEC-n ratification is agent-decidable
once the contract passes an independent review clean". Cutover, regulatory sign-off and licence
facts remain hard `user` gates and are untouched by this review.

**Two findings are recorded below that are NOT grounds to reject revision 5 and must not be read as
such**: both are in **driver-owned files outside DEC-2**, both were introduced or left **after**
revision 5 forked, and one of them is the driver's own correction breaking itself. They are
`FU-A2-33-1` and `FU-A2-33-2`.

---

## What I re-derived, and what I got

Nothing below is inherited. Where I relied on someone else's measurement I say so and mark it.

### Requirement 1 — F-1 is fixed, and the guard's head does NOT drop CANNOT-CATCH on the pass path

**The ancestry.** [VERIFIED by `A2-33`, run in this worktree:]

```
$ git merge-base --is-ancestor 03e9094 2e97162 ; echo $?
0
03e9094  2026-08-22 09:18:26 +0800  T209: widen the ledger guard head's PASS-path filter so CANNOT-CATCH reaches green (FU-T208-1)
2e97162  2026-08-22 10:34:50 +0800  fire 20260822-000013: wave 2 dispatched (...)
```

Exit **0**. `T209` landed **1 h 16 m** before revision 4's fork point. Revision 5's arithmetic and
its ANCESTOR claim are both mine now, not inherited.

**The mechanism, read at revision 4's own commit and not taken on trust.** [VERIFIED by `A2-33`:
`git show 2e97162:.softhouse/guards/check-ledger-invariants.sh`.] At `2e97162` the head already
contained the `awk` block that re-emits the `CANNOT-CATCH` paragraph, **gated on `rc = 0`, i.e. on
the pass path specifically**:

```
  if [ "$rc" -eq 0 ]; then
    printf '%s\n' "$out" | LC_ALL=C awk '
      $0 ~ /^CANNOT-CATCH / { grab = 1 }
      ...
```

So revision 4's `[VERIFIED by A2-28 at commit 2e97162]` claim was **false at its own stamp**, exactly
as `A2-31` found and revision 5 retracts. **Confirmed.**

**I ran the harness and COUNTED the limits, as instructed.** [MEASURED by `A2-33` at `8f193b5`;
transcript `BAR-conformance-A2-33.txt`.]

- `CANNOT-CATCH` header at transcript line **33**.
- Numbered limits at lines **34, 39, 42, 45, 49, 53, 54, 63** — `grep -cE '^ledger-invariants:   [0-9]+\. '` = **8**.
- The run's verdict is `VERDICT: PASS (exit 0)`, `EXITCODE=0`.

**EIGHT limits, printed in full, on a green run. Revision 5's claim is correct and I measured it
myself.**

**Additionally re-measured at REVIEW time** (`A2-25`'s standing rule, which the brief told me to
adopt): the false printed line `guard prints on every run and its head DROPS on the pass path —
FU-T208-1` is **ABSENT from `.softhouse/conformance.sh` at `8f193b5`** — `T227` (merged `6f4d842`)
removed it. My own transcript now reads *"which its head prints IN FULL ABOVE since T209 — so this is
a redundant restatement"*. See "Staleness introduced after the fork" below.

### Requirement 2 — `I4-BUILDER`'s population is ZERO and the true ratio is FOUR of SEVEN. Measured by me, both polarities.

I did **not** reuse `A2-32`'s probe directory. I wrote my own AST walker from scratch
(`probe-i4builder-main.go.txt`), transcribing only `mutatingCallRe`, `mutatingExecRe`, `calleeName`
and `prunedDirs` from the guard at **my** HEAD. Driver: `redgreen.sh`. Transcript:
`i4builder-redgreen.txt`.

| arm | `A2-33` probe: `I4-BUILDER` population | the REAL `ledgerguard` binary |
|---|---|---|
| **GREEN** — the real `nexus/` tree at `8f193b5` | **0** | `clean: … across 47 Go files in 5 packages`; no `I4-BUILDER` finding; exit 0 |
| **RED** — `/tmp` copy, four builder verbs planted | **4** (`Update`, `Delete`, `Save`, `Upsert`) | `REFUSED …` with `[I4-BUILDER]`; exit nonzero |

**The calibration that makes the zero a measurement and not a broken probe** — and I took it at my
own HEAD, not `A2-32`'s:

- my probe's census is **files=47, packages=5, calls=5210**;
- the guard's own `CENSUS ledger-invariants` line on the same tree reads **47 Go files / 5 packages
  / … / 5210 calls**. **Identical to the digit.** My walker is walking the guard's population.
- **A second, independent calibration:** my probe measures `OPAQUE-SQL`'s population
  (`mutatingExecRe` matches) as **0**, and the guard *publishes* that same quantity as `0 exec-family
  calls (0 mutating)` and emits its `NIL-COVERAGE` line on it. Two of my counters agree with two
  figures the guard prints.

**Structural confirmation that the guard does NOT announce `I4-BUILDER`'s emptiness** [VERIFIED by
`A2-33` from source at `8f193b5`, `ledgerguard/main.go:850-866`]: there are exactly **three**
`NIL-COVERAGE` emission arms, gated on `c.SQLDMLTabled == 0`, `c.MutatingExec == 0` and
`c.HoldFuncs == 0`. **There is no arm gated on the `mutatingCallRe` count.** Revision 5's central
explanatory claim — that this silence is why four revisions and the driver all counted three — is
structurally true, not merely asserted.

**The denominator, re-derived by me:**

```
$ grep -oE 'Class: *"[^"]+"' .softhouse/guards/ledgerguard/main.go | sort -u
I3-FIELD-WRITE  I3-PKG-STATE  I3-SQL-BALANCE  I4-BUILDER  I4-DML  I6-HOLD-BALANCE  OPAQUE-SQL   -> 7
```

**SEVEN distinct classes.** [VERIFIED by `A2-33` at `8f193b5`.]

**And I closed the gap `A2-32` left open.** `A2-32`'s Unverified item 4 says it verified only that
`I3-FIELD-WRITE` and `I3-PKG-STATE` are non-empty — but `I3-PKG-STATE`'s population (`c.PkgVars`) is
**not printed on any CENSUS line**, so that figure was not readable off a transcript. **If
`I3-PKG-STATE` were also empty the ratio would be FIVE of seven and revision 5 would be wrong
again.** I measured it (`probe-pkgvars-main.go.txt`): **59 package-level var names across 47 files.**
Non-empty. Combined with `I3-FIELD-WRITE` = **343 write targets** and `I6-HOLD-BALANCE` = **1
hold-named func** (both from the guard's own CENSUS at my HEAD):

| class | population at `8f193b5` | measured how |
|---|---|---|
| `I3-FIELD-WRITE` | **343** | guard CENSUS |
| `I3-PKG-STATE` | **59** | **`A2-33`'s own probe — the figure nobody had taken** |
| `I6-HOLD-BALANCE` | **1** (over-match) | guard CENSUS |
| `I3-SQL-BALANCE` | **0** | guard `NIL-COVERAGE` |
| `I4-DML` | **0** | guard `NIL-COVERAGE` |
| `OPAQUE-SQL` | **0** | guard `NIL-COVERAGE` + `A2-33` probe |
| `I4-BUILDER` | **0** | **`A2-33` probe, both polarities — the guard announces nothing** |

**FOUR of SEVEN. Independently confirmed, with the one unmeasured term measured.**

**A red-arm difference from `A2-32`, disclosed because it is a real property of the guard.** My
planted file put `Update`/`Delete`/`Save` against a variable `je` **of type `journalEntry`**, and a
fourth call `Upsert("acc_gl_journal_entry")`. The real guard fired on **only the fourth**.
`mentionsProtected` inspects the *identifier text and string literals* under the call node, so a
variable of the protected TYPE whose NAME is not `journalEntry` escapes. My red arm still went red
(the guard REFUSED, named `[I4-BUILDER]`, exit nonzero) so it is a valid positive control — but this
is a narrower detection surface than "against a `journalEntry`" suggests. It is **already covered**
by §4.4.1's first blind spot (*"The detection surface is the NAME"*), so it is **not** a defect in
revision 5; I record it because `A2-32`'s disclosed null-control story would lead a reader to think
any call touching a journal-entry-typed value fires, and it does not. Registered as `FU-A2-33-3`.

### Requirement 3 — the correction landed at all nine sites, and THERE IS NO TENTH

**I did not inherit `A2-32`'s enumeration.** I built my own 34-pattern set across both claim classes
and — per the brief and per the driver's mid-task interrupt — **calibrated it on a known positive
before reporting any negative.**

**INSTRUMENT AUDIT (required by the driver's interrupt, and I reproduced the underlying defect
myself).** On this machine:

```
git grep -c -E  'balance column'   -> 93 files
git grep -c -E '\balance column'   -> 93 files   IDENTICAL: git's -E reads \b as a literal 'b'
git grep -c -P '\balance column'   ->  0 files   real word boundary
```

[VERIFIED by `A2-33` at `8f193b5`.] `git grep -E` here does **not** implement `\b`. Also confirmed:
`grep` on PATH is a **ugrep 7.5.0** shim, a different engine again.

- **My own pattern set contains NO `\b`, `\d`, `\s` or `\w`** — checked mechanically with
  `grep -nE '\\[bdswBDSW]'` over `sweep.sh`; the only hit is inside a comment. **My negatives are
  not void by this mechanism.**
- **`A2-32`'s committed `sweep.sh` contains no backslash escape in any of its 26 `pat` lines**
  either. [VERIFIED by `A2-33` from
  `.softhouse/handoff/…/A2-32-evidence/sweep.sh` on `main`.] **`A2-32`'s sweep is NOT void by this
  mechanism** — the driver's concern (3) does not land, and I say so explicitly because "unsupported"
  and "false" must not be conflated.
- **Engine and flags, stated as required:** repo sweep = `git grep -n -I -i -E`, **git 2.50.1
  (Apple Git-155)**; file-mode calibration = `grep -n -i -E` = **ugrep 7.5.0**. I calibrated **both**.

**RECALL CALIBRATION ON A KNOWN POSITIVE.** The positive I hold is **revision 4 of the ADR at
`33d19a6`**, which contains every one of the nine F-2 sites and the F-1 site. Ground truth line
numbers taken independently from the rev-4 → rev-5 diff hunks.

| engine | ground-truth sites recovered |
|---|---|
| `grep -n -i -E` (ugrep 7.5.0), file mode | **15 / 15** F-2 + **2 / 2** F-1 |
| **`git grep -n -I -i -E` (git 2.50.1) — the engine the repo sweep actually uses** | **15 / 15** F-2 + **2 / 2** F-1, **MISSES=0** |

Evidence: `sweep-recall-calibration-ugrep.txt`, `sweep-recall-calibration-gitgrep.txt`. **My
instrument finds every site I know is there, on the engine I swept with. Only then did I report a
negative.** (This is `P-72`; it is also the trap `T224` fell into with `\bexist\b` vs `EXISTING`.)

**POPULATION.** `git grep -n -I -i -E`, 34 patterns, **all tracked content at `8f193b5`** — **4,844
tracked files, 8,120 hit lines, 832 distinct files with at least one hit**. Full per-pattern /
per-file counts over the **entire** population, nothing dropped:
`sweep-counts-full-population.txt`. Full hit lines for everything that is not a committed vector or
committed capture transcript: `sweep-output-live-population.txt`. Raw driver: `sweep.sh`.

**THE TENTH-SITE TEST.** Finding the nine again is not the test; the test is whether a tenth exists.
I ran four independent discriminators over revision 5 (`tenth-site-hunt.txt`):

1. **line-level:** any line naming ≥2 of `{I4-DML, I3-SQL-BALANCE, OPAQUE-SQL}` **without**
   `I4-BUILDER`;
2. **paragraph-level** (blank-line delimited) of the same, because a markdown claim straddles lines
   and a line-level sweep is how a restatement hides;
3. any `empty population` / `inspected…empty` line without `I4-BUILDER`;
4. paragraph-level of (3).

**Result — every surviving hit is one of exactly three benign classes, and I opened each:**

- **the guard's own quoted `NIL-COVERAGE` transcript** (§4.4.1's code block) — a verbatim quotation
  of what the guard prints; it names three classes because the guard names three, which is the
  finding, not a violation of it;
- **§4.4.1's blind-spot item 4** (`The I-4 SQL classes inspected an empty population…`), explicitly
  scoped to the **SQL** classes and therefore TRUE — `I4-BUILDER` is not an SQL class;
- **historical quotations inside labelled retraction / change-log boxes** (§10's revision-4 entry
  item 2 at line 2703, §10's revision-3 entry at 2915, §8.1's revision-4 retraction, the `P-67` box).
  I checked that §10's revision-4 entry — the one that still reads *"the three that inspected an
  empty population are `I4-DML`, `I3-SQL-BALANCE` and `OPAQUE-SQL`"* — **carries its `⚠ CORRECTION,
  revision 5` box immediately below it**, which it does. That is the §5.1.1 restate-don't-reword
  discipline and it is applied correctly.

**And the positive check:** all nine sites carry **FOUR**, with the four classes **named** and **no
denominator** (`nine-sites.txt`). `git grep` for a surviving live "three" turns up only quotations.
`seven` survives only as a standalone measured fact about the guard, never as the denominator of a
ratio — I checked that claim of `A2-32`'s and it holds.

**CONCLUSION: no tenth live site inside DEC-2. I state what I checked so the negative is
distinguishable from not having looked:** 34 patterns, both claim classes, four structural
discriminators, two engines, whole tracked repo, recall-calibrated 17/17 on a held positive.

### Requirement 4 — `A2-32` authored nothing beyond `A2-31`'s two findings

I classified **every one of the 16 diff hunks** in `git diff 33d19a6 cab9e82 -- docs/adr/DEC-2-…md`:

| hunks | content | class |
|---|---|---|
| 1, 3, 4, 5, 6, 9, 11, 13 | the nine F-2 sites | `A2-31` F-2 |
| 7, 8 | the F-1 parenthetical + revision-5 retraction box | `A2-31` F-1 |
| 12, 16 | §8.1 fact-3 retraction; §10 revision-4 entry item 2 correction box | `A2-31` F-2 (records) |
| 14 | §9 item 14 CLOSED by measurement + its header | bookkeeping a revision cannot omit |
| 2, 10, 15 | status block rev 4 → rev 5; §8.1 heading; §10 revision-5 entry | bookkeeping |

**No hunk falls outside those classes. No new claim, no new citation, no new figure.**

**Both disclosed over-reaches were genuinely reverted — I checked the committed bytes, not the
disclosure:**

1. **`306` write targets.** Still reads `306` at three places in revision 5 (lines 879, 892, 916).
   `A2-32` did **not** re-stamp it to its own run's figure. **Correct call**: `306` is `A2-28`'s
   correctly-stamped measurement at `2e97162`, and the section carries an explicit census-drift box
   telling a ratifier to re-run rather than read the page. (At my HEAD the live figure is **343** —
   the drift is real, and the box already covers it. The box's own claim that `5 packages`,
   `1 hold-named`, `15 cases 13 RED 2 GREEN` and `Findings: 0` have not moved is **TRUE at my HEAD**;
   I checked all four.)
2. **No new `[UNVERIFIED]` claim was added.** The `[UNVERIFIED]` token count rises 15 → 21, which
   looks bad until you read them: **every added occurrence is a narrative mention of what revision 4
   did**, and the one actual `[UNVERIFIED]` *claim tag* — `[UNVERIFIED: whether I4-BUILDER inspects a
   non-empty population]` — was **REMOVED**, correctly, because it is now measured. **Net live claim
   tags: −1.** [VERIFIED by `A2-33` from the diff.]

**The one sentence that is new prose rather than a correction**, and my judgement on it: hunk 6
replaces the now-false `I4-BUILDER` `[UNVERIFIED]` bullet with *"So `I3-FIELD-WRITE` and
`I3-PKG-STATE` are the only classes with a genuinely non-empty population on this tree."* That is
**in scope** (it replaces one of the nine sites) and it is **TRUE** — I measured both populations
above, and the qualifier "genuinely" is carried by the immediately preceding sentence about
`I6-HOLD-BALANCE`'s over-match. It carries no stamp, but it asserts nothing the table above it does
not already state. **Not a defect.**

### Requirement 5 — every stamp traces to real source AND is true at its own stamp

This is how revision 4 died, so I re-derived **every line number revision 5 asserts, at the commit
each stamp names** (`stamp-verification.txt`).

**At `33d19a6` — revision 5's own stamp — ALL of the following are exact:**

| revision 5 claims | at `33d19a6` | |
|---|---|---|
| eight `Class:` literals at `:268 :286 :303 :500 :580 :596 :669 :680`, seven distinct | all eight exact; `sort -u` = **7** | ✅ |
| three `NIL-COVERAGE` sites at `:840 :847 :852` | all three exact | ✅ |
| `mutatingCallRe` at `:151`, applied at `:593-596` | `:151`; applied `:593` | ✅ |
| `calleeName` at `:406-418` | `:406` | ✅ |
| `prunedDirs` at `:161` | `:161` | ✅ |
| `check-ledger-invariants.sh:210-219` is the pass-path `awk` block | `:210` is `if [ "$rc" -eq 0 ]; then` … `:219` is `done` | ✅ |
| `conformance.sh` printed line `:1187`; stale comment at `:1163 :1166-1168 :1172 :1176 :1177 :1182` | **all seven verbatim** | ✅ |
| `merge-base --is-ancestor 03e9094 2e97162` exits 0; timestamps 09:18:26 / 10:34:50 | exact | ✅ |
| eight `CANNOT-CATCH` limits reach a PASS transcript | **I counted 8 on my own run** | ✅ |
| `A2-31` measured `I4-BUILDER` at `90c21d6`, both polarities, agreeing | `A2-31.md:178-208` records exactly that | ✅ |

**Not one stamp in revision 5 is false at its own stamp.** The specific failure mode that killed
revision 4 does not recur.

**Staleness introduced AFTER the fork — recorded, and NOT a defect.** `T227` merged into `main` at
`6f4d842`, *between* `A2-32`'s fork (`33d19a6`) and its merge. So revision 5's statement that the
retracted claim *"survives outside this document, in `.softhouse/conformance.sh` — one PRINTED line
and a 25-line comment block"* is **true at `33d19a6`** and **stale at `main`**: the printed line is
gone and the comment now carries `⚠ CORRECTION (T227…) FU-T208-1 IS CLOSED`. This is:

- **properly stamped** `[MEASURED by A2-32 at 33d19a6]`, so it makes no false claim about now;
- **explicitly routed** — the ADR says it *"is not this document's to fix, is routed as `T227`"*, and
  `T227` has since discharged it, including the wider 25-line block `A2-32` reported;
- **not something the author could have prevented**, a sibling task having landed after the fork.

Under the ADR's own MEASUREMENT FRESHNESS rule this is the anticipated condition, not a defect.
**Not grounds for rejection and not a micro-fix I will spend the document's stability on.** A
ratifier re-reading §4.4.1 today should know `T227` has landed; that belongs in the ratification
note, not in another revision.

**Line-number drift at review HEAD, recorded per `A2-25`'s re-measure rule:** `T227` moved
`ledgerguard/main.go` by 12 lines, so at `8f193b5` the classes are at `:280 :298 :315 :512 :592 :608
:681 :692`, `NIL-COVERAGE` at `:852 :859 :864`, `mutatingCallRe` at `:163`, `calleeName` at `:418`,
`prunedDirs` at `:173`. **Every one still resolves BY CONTENT.** The ADR already warns these drift
and tells the reader to re-derive; `A2-31`'s `FU-A2-31-4` (a re-measure gate) remains the right
answer and is still open.

### Requirement 6 — the Fineract citations at `426a23544`

Revision 5 **introduces no new Fineract citation and modifies none** [VERIFIED by `A2-33`: the only
`.java` token anywhere in the rev-4 → rev-5 diff is `JournalEntry.java:79`, carried unchanged through
the §4.4 `I-4` row rewrite]. I nevertheless re-resolved the Fineract citation set BY CONTENT at
`426a23544` rather than inheriting `A2-31`'s pass. **Result: see `fineract-citations.md` in this
directory** — every citation resolved by content; no `FAILS`.

---

## Findings — NEITHER is grounds to reject revision 5

Both are in **driver-owned files**, **outside DEC-2**, and **post-date revision 5's fork**. I raise
them because I swept the whole repo and silence would be indistinguishable from not looking.

### `FU-A2-33-1` (HIGH) — the driver's own `P-67` fix broke `P-67` a fourth time, arithmetically

`.softhouse/patterns.md:1767` at `8f193b5` reads:

> understating sounds like rigour: "three of four" says the guard is 25% live; **"three of seven" says 43%**.

**The framing is "% LIVE"**, fixed by the first clause: three-of-four empty ⇒ 1/4 = **25 % live** ✓.
Therefore **three-of-seven empty ⇒ 4/7 = 57 % live, NOT 43 %.** 43 % is the figure for **FOUR** of
seven. **The driver substituted the corrected PERCENTAGE under the uncorrected NUMERATOR**, producing
a sentence that is now false about both terms.

Worse, the correction box at `:1786` says *"The live figure is four of seven = 43 %, **corrected in
the sentence above**"* — **the sentence above was not corrected**; it still reads *"three of seven"*.
[VERIFIED by `A2-33` at `8f193b5`. The pre-fix bytes are preserved at
`.softhouse/reviews/a2-31-dec2-rev4/sweep-output.txt:121`, which captured `:1767` reading
*"three of seven" says 57%* — so the edit changed **57 → 43** and left the numerator.]

**DEC-2 itself has this right** (`:968-969`: *"'Three of seven' reads as 57 % of the guard live; the
measured figure is 43 %"*). The ADR is correct; `patterns.md` is not.

### `FU-A2-33-2` (HIGH) — a live survivor of the corrected claim, one SECTION over in `patterns.md`

`.softhouse/patterns.md:1941`, in the corrections register (a **different section** from the `P-67`
entry `A2-32`'s `FU-A2-32-1` named), still asserts as current fact:

> Driver-verified from the guard's own green-run output: **three of its seven declared** detection
> classes inspect an **empty population**

**It is four.** `A2-32` named `patterns.md`'s `P-67` entry; the driver fixed the `P-67` entry and
**missed this one**. **This is the correction-landed-where-NAMED-and-not-where-RESTATED defect
recurring for the fourth time, at the driver's hand, in the very file that documents it.**

I re-checked the other propagation targets at my HEAD so this is a complete list, not a sample:
`.softhouse/program.json:1598` **is correct** (FOUR of SEVEN); `.softhouse/RESUME.md`,
`.softhouse/gates.md:62` and `.softhouse/tasks.json:1483` **are correct**.
`.softhouse/gates.md:88` is **stale but harmless** (names `conformance.sh:1180`, which is
`T227`-discharged and was `:1187` anyway).

### `FU-A2-33-3` (LOW) — `mentionsProtected` matches identifier TEXT, not type

Recorded above under requirement 2. Already covered by §4.4.1's blind spot 1; no ADR change needed.

---

## BAR — run by me, never quoted

`. .softhouse/bin/go-env.sh` then **`bash .softhouse/conformance.sh`** (never `sh`), from this
worktree root. Full transcript: `BAR-conformance-A2-33.txt`.

| required | measured by `A2-33` at `8f193b5` | |
|---|---|---|
| probe line PRESENT, reads `up` | `reference oracle (https://localhost:8443/…/health) probe = up`; `oracle probe UP` | ✅ |
| PASS, exit 0 | `VERDICT: PASS (exit 0)`; `EXITCODE=0` | ✅ |
| 46 parity | `parity vectors PASS 46 FAIL 0` | ✅ |
| 7884 cells | `cells compared 7884 graded, 93 ungraded` | ✅ |
| 0 inadmissible | `inadmissible 0` | ✅ |
| 0 invariant violations | `invariant violations 0` | ✅ |
| 4 EXEMPTED | `invariant assertions 4 EXEMPTED BY A VECTOR` | ✅ |
| 4 GROUNDED / 0 UNGROUNDED / 0 UNDETERMINED | `4 GROUNDED …, 0 UNGROUNDED`; `0 UNDETERMINED-ON-THE-RECORD` | ✅ |
| store tree UNCHANGED | `git rev-parse HEAD:.softhouse/vectors` = `73c3ea7b43dd75f04884072719a87fc8e1d255c1` | ✅ |

**Docs/review only.** No Go under `nexus/`. No vector added, moved or edited. Nothing
contract-shaped. My probes live under `/tmp`; their **source is committed here as `.txt`** so it is
not compiled by anything and cannot enter the module.

---

## Unverified — limits of what I did

1. **I did not re-run requirement 6a/6b of §5.2.** `A2-31` authored and ran both and the brief
   records it as DISCHARGED and not in dispute. **[UNVERIFIED by `A2-33`.]**
2. **I did not re-litigate the 5.1.1 retraction, the five legs of §5.1, `run_guards` invoking SEVEN
   guards, or §2.2 B-4** — the brief placed all four out of dispute. I did incidentally confirm
   SEVEN detection *classes* (a different quantity). **[NOT RE-OPENED.]**
3. **I did not re-check the three harness citations `A2-31` reported drifted** (`grade.go:561`→`:631`
   etc.). Revision 5 does not touch them; `FU-A2-31-4` owns them. **[UNVERIFIED by `A2-33`.]**
4. **My sweep skipped nothing by pattern, but I did not open all 8,120 hit lines individually.** I
   opened every hit in every live (non-vector, non-capture) file, and triaged the vector/capture
   classes **by file**, with full per-file counts committed. If a site of the claim hides inside a
   committed vector's JSON my sweep counted it but I did not read it. I judge that near-impossible
   and I am stating it rather than implying coverage I did not take.
5. **`I4-BUILDER`'s population is MEASURED at `8f193b5`, and is not a standing fact.** Any commit
   adding an `.Update(…)`/`.Delete(…)`/`.Save(…)`-shaped call under `nexus/` moves it and **the guard
   will not announce the change** — which is the whole finding. A ratifier must re-take it.
6. **I did not audit `A2-32`'s 2,246-hit sweep line by line.** I established that it is **not void by
   the `\b` mechanism** (no backslash escape in any of its 26 patterns) and I **replaced** its
   enumeration with my own rather than inheriting it, which is the stronger control.
