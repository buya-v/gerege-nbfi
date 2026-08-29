# T459 — independent review of T454 (`softhouse/T454-longs-route`, tip `02fb1af4`)

**Subject:** T454's answer to T446's `MAJOR-1`, `MAJOR-2`, `MINOR-1`, `MINOR-2` and three `LOW`.
**Base for every RED arm:** unmutated `main` at `cbc8733c` (`git merge-base main softhouse/T454-longs-route`).
**Base for every GREEN arm:** the delivered tip `02fb1af4`.

**METHOD.** Every number in this file is mine. I wrote my own drive instrument, planted my own
fixtures, and ran every arm through the WHOLE bar from a scratch cwd outside every repository
involved. Where I only read, I say so. No arm reuses T454's instrument, its fixtures or its
blobs — my forged blobs differ from T454's (`0162b8ef…` where T454 recorded `8bfafdda…`) because
the fixture text is mine, which is the point.

**HOST, and every claim below is a claim about THIS host and no other.** macOS 26.5.1 (build
25F80), APFS, case-INSENSITIVE and normalisation-insensitive, `git version 2.50.1 (Apple
Git-155)` with `core.ignorecase=true` and `core.precomposeunicode=true`, `GNU bash
3.2.57(1)-release`. Reference oracle reachable (`https://localhost:8443/…/health` → 200).

---

## VERDICT

# APPROVED WITH CONDITIONS

T454 did what six links before it did not: it stopped writing "cannot", went looking for the next
route first, found it, drove it and named its spelling. `LONGS` is genuinely closed; `RWB3` is
genuinely closed and refuses **by name**; the Kelvin correction against T446 is **right**, and I
re-derived it two ways. The branch is a net improvement on `main` and nothing in it is a
regression.

It is approved **with conditions** because two of the things it *claimed* are not what I measured:

* the two residuals it named-but-did-not-drive, **`SKIPWT` and `SMUDGE`, are STRICTLY STRONGER
  than the seventh route it did drive** — both reach `EXIT 0` with the guard fully intact and with
  `git status --porcelain` **EMPTY**, which `LONGSTRIP` does not; and `SMUDGE` additionally
  defeats the recompute affordance the guard advertises **and** the external verifier `FU-T454-1`
  proposes; and
* the measured cost claim — "the smallest working forgery is now **two deletions in two separate
  places**" — is **false**. **One inserted line** (`return 0` at the top of the guard's own body)
  reaches `EXIT 0`, keeps the `timed_guard` wiring, keeps the budget row, and keeps
  `GUARD-COST CENSUS: 16 guards timed / guard-cost: PASS`. Arm **`LONGNOP`**.

| # | rating | finding | evidence |
|---|---|---|---|
| `C-T459-1` | **MAJOR** | `SKIPWT` and `SMUDGE` driven: `EXIT 0`, clean `git status`, guard intact. The guard reads its own two object ids and never compares them | `evidence/26`, `27`, `28` |
| `C-T459-2` | **MAJOR** | The `LONGSTRIP` cost claim is false: `LONGNOP` is one INSERTED line, no deletion | `evidence/24` |
| `C-T459-3` | MINOR | The fold census excludes multi-character folds by construction; 13 collide over printable ASCII on this host, not 4 — and one of the nine it misses has a live target, `.softhouse/bin/fire-program.sh` (`fi` ← `U+FB01`) | `evidence/02`, `07`, `08` |
| `C-T459-4` | MINOR | A hand-typed cardinal survives in refusal text — "yet **three** of them are invoked verbatim" | `evidence/05` |
| `C-T459-5` | LOW | The worktree-read census's selector is not stated well enough to reproduce 27; my own selector gives 67 | `evidence/03` |
| `C-T459-6` | LOW | The citation sweep's survivor enumeration names one `tasks.json` occurrence; there are six | `evidence/04` |

---

## 1. `LONGS` — RE-DERIVED IN BOTH DIRECTIONS. THE CLAIM HOLDS.

### RED, on unmutated `main` at `cbc8733c`, my own instrument and my own fixtures

| arm | construction | result |
|---|---|---|
| `Z` | control, unmutated | **EXIT 0**, probe PRESENT ×1 `up`, `VERDICT: PASS … 46 parity vectors … 7884 cells`, `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0`; committed blob `62cda497…` = materialised `62cda497…` |
| `CTL` | an unregistered checker `<guards>/zz-t459-unreg.sh` plus a witness, nothing absolving it | **EXIT 2**, probe line count **0**, `invoked-by-nothing=1` — the guard REFUSES |
| **`LONGS`** | the SAME commit plus ONE extra index entry `<softhouse>/conformance.<U+017F>h` carrying a forged harness with a third DECLARATION TABLE row | **EXIT 0**, probe PRESENT ×1 `up`, **`VERDICT: PASS … 46 … 7884`**, `declared=3 invoked-by-nothing=0` — the identical checker **ABSOLVED** |

```
                                  CTL                 LONGS
committed blob of the harness     62cda497…           62cda497…   <- IDENTICAL. What `git show` prints.
materialised at that path         62cda497…           0162b8ef…   <- *** NOT the committed blob ***
git status --porcelain            (empty)             " M .softhouse/conformance.sh"
```

`evidence/10-RED-main-Z-control.txt`, `11-RED-main-CTL.txt`, `12-RED-main-LONGS-failopen.txt`.

### GREEN, on the delivered tip `02fb1af4`, same instrument, same fixtures

| arm | result |
|---|---|
| `Z` | **EXIT 0**, probe ×1 `up`, PASS 46 / 7884, census unmoved |
| `CTL` | **EXIT 2**, probe count 0 — still refuses |
| **`LONGS`** | **EXIT 2**, probe count **0**, **`guard_harness_text_is_committed FAILED: 1 substituted path(s)`** — **CLOSED** |

`evidence/20-GREEN-tip-Z-control.txt`, `21-GREEN-tip-LONGS-refuses.txt`.

**Claim 1 is confirmed in both directions.**

---

## 2. THE BOUNDARY — "DISCLOSE AN EDIT, REFUSE A SUBSTITUTION". JUDGED, AND IT IS NOT THE LINE IT SAYS IT IS.

**The design decision is right and the argument for it is right.** Refusing every dirty tree would
be a bar that gets run with a flag to switch it off, which is the same outcome as not having it.
T454 files that under `P-22` ("a control that cannot fire is worse than none, because it is
believed") applied to the guard rather than to the predicate; that is a slightly generous reading
of `P-22`'s own sentence, but the reasoning stands on its own feet without the citation and I
endorse the decision. The honest dirty tree still passes with the edit named — arm `WDIRTY`,
`evidence/29-GREEN-tip-WDIRTY-accepted-and-named.txt`.

**But the line the code actually draws is not "edit versus substitution".** It is:

> **"`git diff-index --name-only HEAD` mentioned this path" versus "the disk bytes hash to another
> index entry's blob".**

The first half of that predicate is **attacker-controllable without touching the file the guard
lives in**, and the whole guard is downstream of it: `mods` is empty ⟹ the loop never runs ⟹
`substituted=0` ⟹ `return 0`. I was asked to try to build a forgery that presents as an *edit*.
Two constructions do better than that: they present as **clean**.

### `SKIPWT` — DRIVEN. OPEN. `EXIT 0` WITH AN EMPTY `git status`.

`git update-index --skip-worktree` (and `--assume-unchanged`; both measured, identical outcome) on
the harness, then overwrite it on disk with the `ROW` forgery. **The guard is not stripped, not
edited, not touched.**

```
committed HEAD:harness  = 7c54353236aa1b40161173d75eb4d7905f08a306
on disk (--no-filters)  = ddb88d5a16e0d4f4fbd7cb773bfbf1098c44a39c
git status --porcelain          : (EMPTY)
git diff-index --name-only HEAD : (EMPTY)

EXIT      = 0
probe cnt = 1            <- PRESENCE read before the value (P-84)
probe val = up
VERDICT   = VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells compared.
census    = population=7 invoked=3 declared=3 reached-by=1 invoked-by-nothing=0 symlink-members=0
```

and the guard's own output, from the same log:

```
conformance:   this harness .softhouse/conformance.sh: committed 7c54353236aa1b40161173d75eb4d7905f08a306 / on disk ddb88d5a16e0d4f4fbd7cb773bfbf1098c44a39c
conformance:   HARNESS-TEXT CENSUS: HEAD …; tracked paths whose materialised bytes
conformance:   differ from HEAD: 0 — SUBSTITUTED by another index entry's blob
conformance:   0, uncommitted edits 0, deleted 0.
```

**The guard prints two DIFFERENT object ids for itself and then says "uncommitted edits 0".** It
holds both values in `$confblob` and `$confdisk`, uses them for a calibration that only checks
they are non-empty and that the left one is in the index, and **never compares them to each
other**. One `[ "$confblob" != "$confdisk" ]` — three lines, no new `git` call, no new cost, and
it cannot refuse an honest tree any harder than the existing EDITED branch already prints — would
have caught this. `evidence/26-OPEN-tip-SKIPWT.txt`, `27-OPEN-tip-SKIPWT-assume-unchanged.txt`.

### `SMUDGE` — DRIVEN. OPEN. WORSE THAN T454 PREDICTED, AND IT DEFEATS `FU-T454-1` AS WRITTEN.

T454 predicted a smudge filter "lands in my guard's EDITED branch and is therefore **printed and
accepted**". Measured: in the construction with an **inverting `clean` half**, it lands in
**nothing at all**, and the guard's flagship affordance actively corroborates the forgery.

* the attribute goes in **`.git/info/attributes`** — per-clone, **never committed**, invisible in
  every diff and in `git show`;
* `filter.<n>.smudge` injects the absolving row on checkout; `filter.<n>.clean` removes it again;
* **`git hash-object` applies the clean filter**, so the guard's `confdisk` equals `confblob`.

```
committed HEAD:harness       = 7c54353236aa1b40161173d75eb4d7905f08a306
on disk, RAW (--no-filters)  = ddb88d5a16e0d4f4fbd7cb773bfbf1098c44a39c   <- what bash executes
on disk, as git sees it      = 7c54353236aa1b40161173d75eb4d7905f08a306   <- what the guard sees
absolving row present on disk: 1
git status --porcelain          : (EMPTY)
git diff-index --name-only HEAD : (EMPTY)
committed footprint of the attack: 2 fixture files, 4 insertions. No harness change at all.

EXIT 0 / probe PRESENT ×1 `up` / VERDICT: PASS 46 / 7884 / declared=3
conformance:   this harness …: committed 7c543532… / on disk 7c543532…      <- THE IDS MATCH
```

**THE HONEST BOUND ON BOTH OF THESE, stated before anyone else has to find it.** `SKIPWT` and
`SMUDGE` live in **local, uncommitted state** — an index bit and a `filter.*` config — so neither
survives a reviewer's own fresh clone. They are attacks on the **transcript**, not on the commit;
`LONGS` and `LONGSTRIP` are attacks on the commit and are therefore a different and in one sense
larger thing. I rate them MAJOR anyway, for three reasons: (1) a transcript is exactly what this
program grades, and every completion message in `.softhouse/` is one; (2) **they leave
`git status --porcelain` EMPTY**, so the one out-of-band protocol step this program does apply —
"clean tree before and after" — does not see them, whereas it does see `LONGS` and `LONGSTRIP`
(` M .softhouse/conformance.sh`); and (3) neither depends on a fold, so unlike every other arm in
this chain they work on a case-SENSITIVE filesystem too.

I checked whether the same effect is reachable from a **committed** `.gitattributes` with no local
config — `eol=crlf`, `working-tree-encoding`, `ident` all produce disk bytes that git converts away
and therefore cannot see. It is not: each of those mangles the file into something `bash` will not
execute as a harness, so none can carry a payload. `SMUDGE` needs the attacker's own config, and
I say so rather than leaving the reader to assume the stronger claim.

**Consequence for `FU-T454-1`, which T454 calls "the important one" and "the only thing that can
close the class":** it is specified as *"comparing `git rev-parse HEAD:<path>` with
`git hash-object <path>`"*. **That comparison passes under `SMUDGE`.** The external verifier must
read the bytes bash will execute — `git hash-object --no-filters -- <path>`, or a plain
`shasum` of the file — and must additionally refuse a configured `filter` attribute. As filed,
the remedy inherits the hole. `evidence/28-OPEN-tip-SMUDGE.txt`.

### `SYMFORGE` — my own eighth-route candidate, DRIVEN, and **REFUTED**. Recorded because a negative that was measured is worth more than one that was assumed.

The guard's comment argues the SUBSTITUTED signature is *inherent*: "the winner of a checkout
collision is always some index entry's blob". I tried to falsify that without touching the guard:
make the colliding `U+017F` entry a **120000 symlink** pointing at a tracked forged harness, so the
disk bytes would hash to a short target string that is no tracked blob and land in the EDITED
branch. **It refuses.** `git hash-object -- <path>` **dereferences** a symlink, so the hash it
returns is the payload's blob, the payload must be tracked to survive a fresh clone, and the owner
lookup finds it:

```
is it a symlink?        : YES
git hash-object -- path = ddb88d5a…          <- the PAYLOAD's blob, not the link target
EXIT 2 / probe count 0 / guard_harness_text_is_committed FAILED: 1 substituted path(s)
```

The guard is **stronger than its own comment claims** on this one. `evidence/25-CLOSED-tip-SYMFORGE-refuted.txt`.

---

## 3. THE SEVENTH ROUTE AND ITS COST — `LONGSTRIP` CONFIRMED, `LONGSTRIP1` CONFIRMED, AND THE COST CLAIM FALSIFIED BY `LONGNOP`.

### Both of T454's measurements reproduce

| arm | construction | measured on the tip |
|---|---|---|
| **`LONGSTRIP1`** | `LONGS` whose forged blob deletes ONLY the `timed_guard` wiring | **EXIT 2**, probe count **0**, `guard_cost_census FAILED` on the stale budget row |
| **`LONGSTRIP`** | `LONGS` whose forged blob deletes the wiring **and** the `GUARD_COST_BUDGETS` row | **EXIT 0**, probe PRESENT ×1 `up`, `VERDICT: PASS … 46 … 7884`, `declared=3` — **the seventh route is real and OPEN on the delivered tip** |

`evidence/22-GREEN-tip-LONGSTRIP1-refuses.txt`, `23-OPEN-tip-LONGSTRIP-seventh-route.txt`.
**Both claims stand.** The mitigating measurement is genuine as far as it goes.

### `C-T459-2` — **MAJOR.** But it does not go where the branch says it goes.

The shipped file asserts, in `guard_harness_text_is_committed`'s own header comment:

> "the forged blob must now differ from the honest blob by a whole deleted guard rather than by one
> table row, which is loud in `git diff` of the two objects — **AND IT MUST DELETE TWO SEPARATE
> PLACES, not one.**"

and the handoff, §2: *"the smallest working forgery is now **two deletions in two separate places**
plus the row it wanted, not one row."*

**Arm `LONGNOP` falsifies that.** It is `LONGS` whose forged blob additionally inserts **one line**
— `  return 0` — as the first statement of `guard_harness_text_is_committed`'s own body. It
**deletes nothing**. The `timed_guard` wiring stays. The `GUARD_COST_BUDGETS` row stays.

```
EXIT      = 0
probe cnt = 1
probe val = up
VERDICT   = VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells compared.
census    = population=7 invoked=3 declared=3 reached-by=1 invoked-by-nothing=0 symlink-members=0
conformance:   GUARD-COST CENSUS: 16 guards timed, 48s total wall,
conformance:   guard-cost: PASS — every guard timed, every ceiling row used, none breached.
```

and the whole forgery, `diff` against the honest committed harness:

```
3424c3424,3425
< drive-red-ledger-invariants.sh|SUBJECT|…|ledgerguard"
---
> drive-red-ledger-invariants.sh|SUBJECT|…|ledgerguard
> zz-t459-unreg.sh|CALLER|…|zz-t459-unreg.sh"
4995a4997
>   return 0
```

Changed-line counts against the honest blob, measured: **`LONGS` 3 · `LONGNOP` 4 · `LONGSTRIP1` 4 ·
`LONGSTRIP` 5.** So the measured price the branch put on the surviving attack is **one extra
line**, not "a whole deleted guard in two separate places".

**Two tells exist and neither is enforced.** Under `LONGNOP` the guard is still *timed* —
`COST 0s / ceiling 60s   guard_harness_text_is_committed` — and it emits **zero** `HARNESS-TEXT`
lines, where the honest run emits four and costs 2s. So the run carries both a **missing output
block** and a **cost that fell to zero**, and `guard_cost_census` is a CEILING check with no floor,
so it reports `guard-cost: PASS`. A budget row is `<guard>|<ceiling>`; a guard that has just been
turned into `return 0` passes every ceiling there is.

**Root cause, and T454 has half of it.** `§9` discloses "whether `guard_harness_text_is_committed`
is itself pinned by anything — it is not", and files `FU-T454-3` to *decide deliberately* about it,
"knowing a pin does not stop `LONGSTRIP`". Verified: `guard_registration_decisive_lines`'s haystack
is the body of `guard_guards_dir_registration` and nothing else, and nothing anywhere in the tree
pins the `HARNESS-TEXT` output lines. **What the handoff does not do is connect that disclosure to
the cost claim it makes two sections earlier.** A pin does not stop `LONGSTRIP`; it does stop
`LONGNOP`, and `LONGNOP` is the cheaper forgery.

**Condition.** Either restate the claim in the file and the handoff to what is measured — "the
smallest working forgery grew by one line" — or pin this guard's decisive lines so that the
cheapest neutering really is a deletion. Do not leave the sentence standing as written: it is the
kind of measured-sounding cardinal this program keeps getting caught by, and it is now the seventh
consecutive link at which the next reader reached what the previous author called settled.

---

## 4. THE FOLD CENSUS — METHOD SOUND, KELVIN ADJUDICATED IN T454'S FAVOUR, CANDIDATE SET INCOMPLETE.

### The method is sound, and under T454's own selector I reproduce its numbers exactly

Write two distinguishable contents at two spellings, read back which survived; calibrate on a known
positive and a known negative before reporting any count; a read that returns neither content is an
instrument failure, never a "no". That is the right shape and I adopted it.

| run | T454 | T459 (mine) |
|---|---|---|
| restricted to the characters of the two working-tree-read paths, single-char image | 486 candidates, **1** collides (`U+017F`) | 486 candidates, **1** collides (`U+017F`) |
| all printable ASCII, single-char image | 1075 candidates, **4** collide | 1090 candidates, **4** collide |

The 15-candidate difference is over-generation on my side that the filesystem probe filters out;
**the answers are identical**. `evidence/02-fold-census.txt`.

### The Kelvin disagreement: **T454 is RIGHT and T446 was wrong.** Adjudicated, twice, on my own probes.

```
CALIB-POS  U+017F LONG S vs ascii s            files=1  zs.txt reads=BBB  -> COLLIDES
CALIB-NEG  ascii z vs ascii y                  files=2  zz.txt reads=AAA  -> distinct
U+212A KELVIN vs ascii k                       files=1  zk.txt reads=BBB  -> COLLIDES   <- IT FOLDS
U+212A appended where there is no k            files=2  zs.txt reads=AAA  -> distinct   <- T446's probe
```

I reproduced **both** T446's reading and its cause in the same run: substituting the Kelvin sign
into a path with no `k` in it compares two genuinely different names, and "distinct" then means
"these are two different files", not "this character does not fold". T454's correction is
accepted. `evidence/00-fold-probes.txt`.

### `C-T459-3` — **MINOR.** The candidate set is incomplete BY CONSTRUCTION, and the handoff's headline does not say so.

`fold-census.py`'s `fold_candidates()` keeps a candidate only `if len(f) == 1` — the ASCII image
must be **exactly one character**. That excludes every **multi-character** fold. Measured on this
host, they are real:

```
U+00DF SHARP S            -> ss   files=1 zss.txt reads=BBB -> COLLIDES
U+1E9E CAPITAL SHARP S    -> ss   COLLIDES
U+FB00 LIGATURE FF        -> ff   COLLIDES
U+FB01 LIGATURE FI        -> fi   COLLIDES
U+FB02 LIGATURE FL        -> fl   COLLIDES
U+FB03 LIGATURE FFI       -> ffi  COLLIDES
U+FB04 LIGATURE FFL       -> ffl  COLLIDES
U+FB05 LIGATURE LONG S T  -> st   COLLIDES
U+FB06 LIGATURE ST        -> st   COLLIDES
```

**Over all printable ASCII the count is 13, not 4** — and all 13 sort after their partner, so
T454's generalisation ("every non-ASCII collider sorts after, unconditionally, because UTF-8 gives
every codepoint ≥ U+0080 a leading byte ≥ 0xC2") is not merely intact, it **extends** to the nine
it missed. `evidence/01-multichar-folds.txt`, `evidence/02-fold-census.txt`.

**The restricted answer of ONE is correct, and correct for a reason the census did not check.**
I enumerated rather than assumed it: neither `.softhouse/conformance.sh` nor `.softhouse/guards`,
nor `check-ledger-invariants.sh`, `check-capture-namespace.sh`, `check-dead-path-frontier.sh`,
`ledgerguard/main.go`, `ready-tasks.py` or `go-env.sh`, contains any of those digraphs.

**But one graded path does, and it is not a small one.** `.softhouse/bin/fire-program.sh`
contains **`fi`**, and I drove the collision:

```
files in the directory      : 1
what "fire-program.sh" reads back : THE FORGED FIRE DRIVER
RESULT: COLLIDES. U+FB01 folds onto "fi" on this volume and its UTF-8 leading byte 0xEF
        sorts after ASCII "f" = 0x66, so the forged entry WINS a checkout.
```

That file is (a) **a DECLARED WITNESS in the DECLARATION TABLE** — row 1,
`repo-state-attest.sh|CALLER|.softhouse/bin/fire-program.sh|repo-state-attest.sh` — and (b) the
file `FU-T454-1` proposes to host the external committed-versus-materialised verifier. A verifier
that lives at a path spelled with `fi` is substitutable by a character T454's census reports does
not exist. **`guard_harness_text_is_committed` does cover it** (it adjudicates the whole
`diff-index` set and enumerates nothing), so this is not a live fail-open today — it is a hole in
the census that would mislead the next person deciding where to put a verifier.

Across the tracked tree the class is live: **2824 tracked paths contain `st`, 827 contain `ss`,
713 `ff`, 653 `fi`, 174 `fl`, 23 `ffi`, 4 `ffl`.** The instrument's own docstring says
over-generation is filtered by the probe "while under-generation would silently shrink the answer,
which is the failure mode this whole chain is about" — and then under-generates.
`evidence/07-digraph-exposure.txt`, `evidence/08-firefi.txt`. State the restriction, or lift it.

---

## 5. THE GENERALISATION — RE-COUNTED. DIRECTION CONFIRMED AND UNDERSTATED.

`C-T459-5` — **LOW.** I could not reproduce **27** and I do not think a reader can from the handoff
alone: "executable sites that touch this host's filesystem at a `$REPO_ROOT` path" is not a
selector until the set of filesystem-touching constructs is written down, and it is only in the
instrument. Under my own selector — non-comment lines that name `$REPO_ROOT` directly, or one of
the 15 locals bound to a `$REPO_ROOT` path, **and** hand it to a construct that opens a path —

```
variables bound to a $REPO_ROOT path                                    : 15
executable sites naming $REPO_ROOT directly and touching the filesystem : 39
executable sites reaching it through one of those variables             : 28
TOTAL                                                                   : 67
of those, on a path containing s / k / ; / ` (a fold that SORTS AFTER)  : 61
```

The six remaining are line-continuations whose path text is on the following physical line, so in
substance it is 67 of 67. `evidence/03-read-census.txt`.

**The two numbers are not comparable and that is the whole finding: mine is BIGGER.** The
qualitative claim — every `.softhouse/` path carries the `s` of "softhouse", so essentially every
working-tree read in this harness is reachable by `U+017F`, including every checker it *executes*
— is confirmed and if anything understated. **This should be stated plainly, and T454 does state
it plainly.** The condition is only that the census print its selector, which is the rule this
program applies to every other census in the tree.

---

## 6. `MAJOR-2` — RE-DERIVED IN BOTH DIRECTIONS. THE CLAIM HOLDS, INCLUDING THE ATTRIBUTION.

My fixture: `<guards>/zz-t459-member.sh` declaring `REACHED-BY <guards>/W.txt`; `W.txt` a tracked
100644 decoy whose committed bytes **name nothing**; `w.txt` a 120000 symlink to the member,
sorting last (`w` = 0x77 > `W` = 0x57) and winning the checkout on this volume. The mutation is a
**one-line** revert of the WITNESS naming test from the tracked blob back to the working tree.

| arm | base | result |
|---|---|---|
| `RWB3CTL` | `main` | **EXIT 2**, probe count **0**, `reached-by=1`, refused: "THAT REACHED-BY WITNESS DOES NOT NAME zz-t459-member.sh IN ITS COMMITTED …" |
| **`RWB3`** | `main` | **EXIT 0**, probe ×1 `up`, **`VERDICT: PASS … 46 … 7884`**, **`reached-by=2`**, `REACHED-BY …/zz-t459-member.sh — declared in its own header, reached by …` — over a committed witness blob that names nothing — while the watch printed **`registration decisive lines: 7 present, 2 evaluated`** |
| **`RWB3`** | tip | **EXIT 2**, probe count **0** |

**And the attribution is confirmed, which is the part that needed checking**, because the refusal
on the tip is over-determined: `guard_harness_text_is_committed` also fires on the `W.txt`/`w.txt`
collision. It does — and `guard_registration_decisive_lines` **names its own needle**, so the claim
for `MAJOR-2` is carried by the right guard:

```
conformance: guard_registration_decisive_lines: THE DECISIVE LINE IS GONE —
conformance:   the WITNESS naming test USES the tracked blob as its HAYSTACK [T454, arm RWB3]
```

`evidence/13-RED-main-RWB3CTL.txt`, `14-RED-main-RWB3-failopen.txt`, `15-GREEN-tip-RWB3-refuses.txt`.

**Two independent refusals; T454 claims only the second for `MAJOR-2`; that is the correct and
conservative reading and I confirm it.**

---

## 7. THE MOVED PIN, AND THE CARDINAL.

### The `:3271` pin — verified, and the disclosure question answered in T454's favour

T454's first commit rotted `patterns.md`'s live `conformance.sh:3271` pin and, rather than
disclosing the rot, it **moved its own comment block** so the line is byte-identical again.
Verified independently:

```
patterns.md:3426 (main) == patterns.md:3426 (tip)   ("`.softhouse/conformance.sh:3271`")
conformance.sh:3271 main : warn "conformance: guard_guards_dir_registration: the population is EMPTY. That is a SELECTOR"
conformance.sh:3271 tip  : (byte-identical)                       -> 3271 IDENTICAL
patterns.md                                                       -> UNTOUCHED by T454
```

**This is the right call and not a concealment.** `patterns.md` is outside T454's grant; the
alternatives were to rot a live pin it could not repair, or to raise a gate over a comment block.
Moving its own text is the only remedy inside its own file, and it disclosed the whole sequence in
`§8`. Recorded as correct. `evidence/05-pins-and-cardinals.txt`.

### `C-T459-6` — LOW. The citation sweep survives; the enumeration is one file short.

My own sweep, over every `conformance.sh:NNNN` citation in the tip tree, comparing the cited line's
text on `main` with its text on the tip:

```
distinct files carrying at least one : 223
total occurrences                    : 1772        (T454: 1770 — the +2 are T454's own handoff)
occurrences whose cited LINE TEXT CHANGED: 138      (T454: 138 — INDEPENDENTLY REPRODUCED)
files affected                       : 26
```

**The claim "none is a live pin any guard reads" is CONFIRMED.** The moved set contains no `.pin`
file, no guard script, and **not `patterns.md`**. Every affected file is an archival record —
`reviews/*/REVIEW.md` and `evidence/`, `capture/*/out/*.txt` transcripts, dated handoffs, one
captured copy of the harness — **except `.softhouse/tasks.json`, which carries six moved
occurrences, not the one (`:3385`) the handoff names**. I inspected all six: five are historical
narration; one is a live, open instruction to a future holder of the file
(*"ALSO FIX `conformance.sh:4530` WHILE YOU HOLD THE FILE (F-T411-2)"*) — and **it was already
rotted on `main` before T454 touched it**, so T454 did not break it. The finding is the
enumeration, not the consequence. `evidence/04-citation-sweep.txt`.

### `C-T459-4` — MINOR. One hand-typed cardinal survives in refusal text.

The claim checks out where it was made: on `main`, `guard_cost_census` warned *"this function calls
**fifteen** guards"*; on the tip that sentence is gone and replaced by a comment recording why, and
the figure is derived (`$GUARD_COST_TIMED`). Counted independently: `timed_guard` call sites are
**15 on `main` and 16 on the tip**, so `16` is a count and not a typed number. Good.

**But the sweep missed one of exactly the same shape**, in `guard_guards_dir_registration`'s own
calibration refusal:

```
warn "conformance: population was found on a non-comment line of this file, yet three of them"
warn "conformance: are invoked verbatim a few hundred lines above. The reading mechanism is"
```

`three` is a hand-typed cardinal for a quantity this very function derives and prints on every run
(`invoked=3`), inside a `warn` that only a reader in trouble will ever see. It is P-80's exact
shape. It is `MINOR` and not worse only because the branch that fires it is a refusal.

---

## 8. WHAT I DID NOT CHECK — statements about my search, never about the world

* **A case-SENSITIVE filesystem, and a second `git`.** Every arm here is APFS,
  `git 2.50.1 (Apple Git-155)`, `bash 3.2.57`. On a case-sensitive volume `LONGS`, `LONGSTRIP`,
  `LONGNOP`, `SYMFORGE` and `RWB3` all disappear; **`SKIPWT` and `SMUDGE` do not** — neither has
  anything to do with folding, and both work on any filesystem. That is a further reason to rate
  them above the seventh route.
* **The pinned toolchain.** Every arm, RED and GREEN, ran under the announced FALLBACK toolchain.
* **`core.symlinks=false`, sparse checkout, a partial clone.** Named by T445, T446, T454 and now by
  me; driven by none of us.
* **Whether `LONGNOP` has a smaller sibling.** I stopped at one inserted line because one line is
  already smaller than the claim it falsifies. I did not search for a zero-line forgery and I make
  no claim that none exists.
* **`patterns.md`** — outside my grant, as it was outside T454's. `FU-T454-2`'s sentence is still
  unwritten and a sixth generation has now paid for it.
* **Nothing outside `.softhouse/reviews/t459-review-t454/` was modified by this review.**

---

## 9. FOLLOW-UPS THIS REVIEW CREATES

* **`FU-T459-1`** *(from `SKIPWT`, and it is three lines)*. In `guard_harness_text_is_committed`,
  compare `$confblob` with `$confdisk` — the guard already reads both — and treat a mismatch that
  `git diff-index` did **not** report as a REFUSAL, because that combination is not an honest dirty
  tree, it is a suppressed one. Additionally refuse a `skip-worktree`/`assume-unchanged` bit
  (`git ls-files -v`, flags `S`/`h`) on any tracked path. Drive with arm `SKIPWT`.
* **`FU-T459-2`** *(from `SMUDGE`, and it amends `FU-T454-1` rather than adding to it)*. Every
  committed-versus-materialised comparison in this program — inside the harness and in the external
  verifier `FU-T454-1` proposes — must read the bytes bash will execute:
  `git hash-object --no-filters`, never bare `git hash-object`. And refuse a configured `filter`
  attribute on a graded path (`git check-attr filter`, which reads `.git/info/attributes` too).
* **`FU-T459-3`** *(from `LONGNOP`)*. Resolve `FU-T454-3` in the direction of pinning, or correct
  the cost sentence. Do not ship both the sentence and the absence of the pin.
* **`FU-T459-4`** *(from the fold census)*. Lift `len(f) == 1`, or say in the handoff that the
  count is over single-codepoint folds only. Either way, `.softhouse/bin/fire-program.sh` is a
  target for `U+FB01` and `FU-T454-1` proposes to put the external verifier there.
* **`FU-T459-5`**. Delete the hand-typed "three" from `guard_guards_dir_registration`'s calibration
  refusal; it is derivable from `$invoked`'s siblings in the same function.

---

## 10. THE BAR, ON MY OWN COMMITTED TREE

See `evidence/90-FINAL-BAR.log` and the figure table at the end of this file.

---

## 11. PER-CLAIM DISPOSITION — every claim T454 made, and what I measured

| T454's claim | my measurement | disposition |
|---|---|---|
| `LONGS` fails open on `main` (`EXIT 0`, probe `up`, `PASS 46-7884`, `declared=3`) | reproduced on my own instrument and my own fixtures: `EXIT 0`, probe ×1 `up`, `PASS 46 / 7884`, `declared=3`, committed `62cda497…` vs materialised `0162b8ef…` | **CONFIRMED** |
| `LONGS` refuses on the tip (`EXIT 2`, probe count 0, `1 substituted path(s)`) | reproduced: `EXIT 2`, probe count **0**, `guard_harness_text_is_committed FAILED: 1 substituted path(s)` | **CONFIRMED** |
| the boundary "disclose an edit, refuse a substitution" is the right line | the decision is right; the **implemented predicate** is `git diff-index` mentioned it, which two constructions defeat while leaving the guard intact and `git status` clean | **CONFIRMED with `C-T459-1`** |
| `LONGSTRIP` reaches `EXIT 0` on the delivered tip | reproduced: `EXIT 0`, probe ×1 `up`, `PASS 46 / 7884`, `declared=3` | **CONFIRMED** |
| `LONGSTRIP1` refuses on the stale budget row | reproduced: `EXIT 2`, probe count 0, `guard_cost_census FAILED` | **CONFIRMED** |
| "the smallest working forgery is now two deletions in two separate places" | **FALSIFIED.** `LONGNOP`: one inserted line, no deletion, `EXIT 0`, 16 guards timed, `guard-cost: PASS` | **`C-T459-2`, MAJOR** |
| 1075 candidates / 4 collide over all printable ASCII; 486 / 1 restricted | both reproduced **exactly** under T454's own selector (1090 candidates, same 4). Multi-character folds are excluded by construction: **13** collide over printable ASCII | **CONFIRMED within its scope; `C-T459-3`** |
| T446's `U+212A` negative is a false negative | reproduced the fold AND reproduced T446's construction that produced the false negative | **T454 IS RIGHT. T446 WAS WRONG.** |
| every non-ASCII collider sorts after its ASCII partner unconditionally | measured on all 13, including the 9 T454 did not generate: all sort after | **CONFIRMED AND EXTENDED** |
| 27 filesystem-touching sites, 26 foldable | selector not reproducible from the handoff; my own gives 67, of which 61 by line-granularity and 67 in substance | **DIRECTION CONFIRMED, UNDERSTATED; `C-T459-5`** |
| `RWB3` fails open on `main` at `reached-by=2` with the watch printing "7 present" | reproduced: `EXIT 0`, probe ×1 `up`, `PASS 46 / 7884`, `reached-by=2`, `registration decisive lines: 7 present, 2 evaluated` | **CONFIRMED** |
| `RWB3` refuses on the tip **by name** | reproduced, and the attribution holds: `guard_registration_decisive_lines: THE DECISIVE LINE IS GONE — the WITNESS naming test USES the tracked blob as its HAYSTACK [T454, arm RWB3]` | **CONFIRMED** |
| `MINOR-1` closed: haystack scoped to the deciding function's body, exactly-once, no trailing comment, no `:` no-op, uncuttable body refuses | read and verified line by line in the deployed text; all five properties present | **CONFIRMED (read, not driven)** |
| `MINOR-2` closed: the second working-tree read removed, corrected audit in the file | verified: `$2` is the already-stripped text; the three-row audit table is in the file with the removed read named | **CONFIRMED (read, not driven)** |
| `LOW-1` stated in the file | verified: the DIRECTORY and PATHSPEC-MAGIC consequences are written in the deployed text | **CONFIRMED (read, not driven)** |
| `16 guards timed` is DERIVED; the hand-typed "fifteen guards" deleted | verified: 15 `timed_guard` sites on `main`, 16 on the tip; the `warn` is gone. **But one hand-typed cardinal of the same shape survives** | **CONFIRMED; `C-T459-4`** |
| `conformance.sh:3271` byte-identical; 34 broken citations all historical, no live pin | `:3271` byte-identical, `patterns.md` untouched; **138 moved reproduced exactly**; no `.pin`, no guard, not `patterns.md` | **CONFIRMED; `C-T459-6`** |
| `SMUDGE` "lands in the EDITED branch: printed and accepted" | **DRIVEN, and worse:** with an inverting `clean` half it lands in nothing, `git status` is clean, and the guard prints the two ids as EQUAL | **`C-T459-1`, MAJOR** |
| `SKIPWT` "suppresses `git diff-index`, so the guard reports clean" | **DRIVEN. Correct, and it is `EXIT 0` with a PASS verdict and a clean `git status` — a working forgery, not just a blind spot** | **`C-T459-1`, MAJOR** |
| `KELVIN` not driven, covered by the same guard | not driven here either; 790 tracked `.softhouse/` paths contain a `k`, so the target set is large | open, undriven, disclosed |
| `GREEKQ` / `VARIA` measured, no target in this repository | verified: **0** tracked paths contain `;` or a backtick | **CONFIRMED** |
| `NFD` refuted (`core.precomposeunicode=true`, ASCII paths) | `core.precomposeunicode=true` verified on this host; NFD/NFC collide at the *filesystem* layer but git collapses the pair at `update-index` | **CONFIRMED** |
| the HEAD/index divergence where the colliding entry is in HEAD but not the index | **not driven here either.** Deprioritised deliberately: it requires a staged deletion, so it is visible in `git status`, which makes it strictly weaker than `SKIPWT`, which is not | open, undriven |

---

## 12. REPRODUCTION RECIPES

Every instrument is in `instruments/`. All of them assemble the repo-relative paths they plant at
run time rather than spelling them, so none of them puts a row on the dead-path frontier — verified
before committing (`deadOccurrences` unmoved at 108 with all of them staged, and the fail-open lint
`PASS`).

**Common preamble.** Nothing is run inside the repository under test.

```
export SRCREPO=<path to a clone or worktree of this repository>
export T459_WORK=/tmp/t459                      # scratch; the default, outside every repo
export T459_MAIN_CONF=/tmp/t459-main-conf.sh    # git show main:<softhouse>/conformance.sh
export T459_TIP_CONF=/tmp/t459-tip-conf.sh      # git show softhouse/T454-longs-route:<same>
```

| finding | recipe | expected |
|---|---|---|
| `LONGS` RED on `main` | `bash instruments/arms.sh cbc8733c Z CTL LONGS` | `Z` EXIT 0 · `CTL` EXIT 2, probe count 0 · **`LONGS` EXIT 0, probe ×1 `up`, PASS 46/7884, `declared=3`** |
| `LONGS` closed on the tip | `bash instruments/arms.sh 02fb1af4 Z CTL LONGS` | `LONGS` EXIT 2, probe count 0, `1 substituted path(s)` |
| `LONGSTRIP` / `LONGSTRIP1` | `bash instruments/arms.sh 02fb1af4 LONGSTRIP1 LONGSTRIP` | `LONGSTRIP1` EXIT 2 on the stale budget row · `LONGSTRIP` **EXIT 0** |
| **`C-T459-2`** `LONGNOP` | `bash instruments/arms.sh 02fb1af4 LONGNOP` | **EXIT 0**, probe ×1 `up`, PASS 46/7884, `16 guards timed`, `guard-cost: PASS`; the forgery is a **two-line** diff |
| **`C-T459-1`** `SKIPWT` | `bash instruments/skipwt.sh 02fb1af4 skip-worktree` and `… assume-unchanged` | **EXIT 0**, `git status --porcelain` EMPTY, and the guard prints two DIFFERENT object ids for itself |
| **`C-T459-1`** `SMUDGE` | `bash instruments/smudge.sh 02fb1af4` | **EXIT 0**, `git status` EMPTY, `git diff-index` EMPTY, the guard prints the two ids as EQUAL, and the absolving row is on disk |
| `SYMFORGE` (refuted) | `bash instruments/symforge.sh 02fb1af4` | EXIT 2 — `git hash-object` dereferences the symlink and the payload's blob is found in the index |
| honest dirty tree still passes | `bash instruments/wdirty.sh 02fb1af4` | EXIT 0, `HARNESS-TEXT: uncommitted edit — …` naming the path and the on-disk id |
| `RWB3` both directions | `bash instruments/rwb3.sh cbc8733c CTL` · `… cbc8733c MUT` · `… 02fb1af4 MUT` | EXIT 2 · **EXIT 0 `reached-by=2`** · EXIT 2 naming `THE DECISIVE LINE IS GONE — the WITNESS naming test USES the tracked blob as its HAYSTACK` |
| **`C-T459-3`** fold census | `bash instruments/fold-probe.sh` · `bash instruments/fold-probe2.sh` · `python3 instruments/fold-census.py` | Kelvin COLLIDES; the nine multi-character folds COLLIDE; 486/1 and 1090/4 under T454's selector, 1380/13 with the restriction lifted |
| **`C-T459-3`** the live `fi` target | `bash instruments/digraph.sh <repo>` · `bash instruments/firefi.sh` | `.softhouse/bin/fire-program.sh` carries `fi`; `U+FB01` collides and wins |
| **`C-T459-5`** read census | `python3 instruments/worktree-read-census.py "$T459_TIP_CONF"` | 67 sites, 61 foldable by line granularity |
| **`C-T459-6`** citation sweep | `python3 instruments/citation-sweep.py <repo>` | 1772 occurrences, **138 moved**, 26 files, no `.pin`, no guard, not `patterns.md` |
| **`C-T459-4`** pins and cardinals | `bash instruments/pins.sh` | `:3271` byte-identical; 15→16 `timed_guard` sites; the surviving `yet three of them` |
| the final bar | `bash instruments/finalbar.sh <repo>` | see §13 |
