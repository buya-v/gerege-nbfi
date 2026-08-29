# T454 — the sixth route forges the harness itself, and there is a seventh

**Branch:** `softhouse/T454-longs-route`. **Subject:** T446's `MAJOR-1`, `MAJOR-2`, `MINOR-1`,
`MINOR-2` and the three `LOW`, filed against T445 as delivered.
**Grant:** `.softhouse/conformance.sh` and `.softhouse/capture/t454-t446-conditions/`.
**Method:** every number below is mine. I built my own instrument, planted my own fixtures, and
drove every arm through the WHOLE bar from a cwd outside every repository involved. Where I only
read, I say so.

**Host, and every claim below is a claim about THIS host and no other:** macOS 26.5.1 (build
25F80), APFS volume "Macintosh HD", case-INSENSITIVE and normalisation-insensitive,
`git version 2.50.1 (Apple Git-155)` with `core.precomposeunicode=true` and `core.ignorecase=true`,
`GNU bash 3.2.57(1)-release (arm64-apple-darwin25)`.

---

## THE CHAIN, AND WHERE THIS LINK LANDS

T404 disclosed a residual and rated it unreachable → T407 reached it → T431 closed that and wrote a
new unreachability claim → T444 reached that one → T445 closed four fail-opens and wrote *"provably
cannot win"* → T446 reached that. Six links, six times.

**I did not write a seventh "cannot". I went looking for the seventh route first, I found it, I
drove it, and it is disclosed by name below (`LONGSTRIP`).** The remedy in this branch closes the
forgery that does not also strip the guard, and raises the cost of the one that does. It does not
close the class, and the thing that can is not in this file.

---

## 1. MAJOR-1 — RE-DERIVED ON MY OWN INSTRUMENT, ON UNMUTATED `main`

`instruments/drive-t454.sh` clones the tree under test, plants, commits **without a subsequent
`git add -A`** (T446's recorded trap: `git add -A` re-reads the case-folded working tree and
silently downgrades a `--cacheinfo` symlink entry), **re-clones** so a collision materialises as a
fresh checkout would, and runs the whole bar from `$WORK/cwd`. It reads the probe line's
**PRESENCE before its VALUE** (P-84), and it treats an absent or empty bar log as an INSTRUMENT
failure (`exit 3`) rather than as a refusal.

### RED, on `main` at `cbc8733c` — the harness before this branch touched it

| arm | construction | result |
|---|---|---|
| `Z` | control, unmutated | **EXIT 0**, probe PRESENT ×1 `up`, `VERDICT: PASS … 46 parity vectors … 7884 cells`, `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` |
| `LONGSCTL` | an unregistered checker `.softhouse/guards/zz-t454-unreg.sh`, and nothing absolving it | **EXIT 2**, probe line count **0**, `invoked-by-nothing=1`, `guard_guards_dir_registration` REFUSES |
| **`LONGS`** | the SAME commit plus ONE extra index entry `.softhouse/conformance.ſh` (`U+017F`) carrying a forged harness with a third DECLARATION TABLE row | **EXIT 0**, probe PRESENT ×1 `up`, **`VERDICT: PASS … 46 … 7884`**, `declared=3 invoked-by-nothing=0` — the identical checker **ABSOLVED** |

```
                                  LONGSCTL            LONGS
committed blob of the harness     62cda497…           62cda497…   <- IDENTICAL. What `git show` prints.
materialised at that path         62cda497…           8bfafdda…   <- *** NOT the committed blob ***
```

`git clone` itself printed `warning: the following paths have collided … '.softhouse/conformance.sh'
'.softhouse/conformance.ſh'` — on **clone's** stderr, which no transcript of the bar contains and no
guard reads. `git status --porcelain` of the graded clone reported ` M .softhouse/conformance.sh`.
Neither channel is inside the harness.

Transcripts: `evidence/09-RED-arm-Z-control-on-main.txt`, `evidence/10-RED-arm-LONGSCTL.txt`,
`evidence/11-RED-arm-LONGS.txt`.

### GREEN, on the delivered tip, same instrument, same fixtures

| arm | result | reading |
|---|---|---|
| `Z` | **EXIT 0**, probe PRESENT ×1 `up`, `PASS 46 / 7884`, census `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | a clean tree is still accepted |
| `LONGSCTL` | **EXIT 2**, probe count **0**, `invoked-by-nothing=1` | still refuses |
| **`LONGS`** | **EXIT 2**, probe count **0**, **`guard_harness_text_is_committed FAILED: 1 substituted path(s)`** | **CLOSED** |
| **`WDIRTY`** | **EXIT 0**, probe PRESENT ×1 `up`, `PASS 46 / 7884`, census unmoved, and `HARNESS-TEXT: uncommitted edit — .softhouse/conformance.sh (on disk a69d8006…)` | **an honest dirty tree is still accepted, and the edit is named** |

The refusal, verbatim from `evidence/40-barlog-arm-LONGS-refusal.log`:

```
conformance: guard_harness_text_is_committed: THE FILE ON DISK AT .softhouse/conformance.sh IS NOT THE FILE
conformance: COMMITTED THERE — IT IS THE COMMITTED BLOB OF ANOTHER INDEX ENTRY.
conformance:   path graded by everything downstream : .softhouse/conformance.sh
conformance:   object id materialised at that path  : e84808aeed70474d491f62b3f7181383e78a5f16
conformance:   the index entry that blob belongs to : .softhouse/conformance.ſh
```

### THE REMEDY — `guard_harness_text_is_committed`

Wired **second** in `run_guards`, immediately after `guard_graded_root_is_this_tree`, through
`timed_guard`, with its own row in `GUARD_COST_BUDGETS` (ceiling 60 s; **measured 2 s**). It joins
the `failed=1` tally rather than short-circuiting: unlike a diverged `$REPO_ROOT` a substitution
does not make the other guards' output unreadable, it makes it untrustworthy, and the reader needs
both findings.

**What it refuses, and why it is NOT "refuse a dirty tree".** The forgery's signature is not
dirtiness. It is that the bytes materialised at a tracked path **are the committed blob of a
different index entry** — which is inherent to the route, because the winner of a checkout
collision is always some index entry's blob:

* **SUBSTITUTED** — the disk bytes at tracked `P` hash to the blob of a tracked `Q ≠ P`. **REFUSED**,
  with `P`, `Q` and the object id all named.
* **EDITED** — the disk bytes at `P` differ from `HEAD` and match no other index entry. **ACCEPTED,
  and printed.**

**The second row is a decision, and I argue it rather than assume it.** Refusing every dirty tree
would be one line shorter and it would be wrong: every task in this program edits this file and
runs this bar *before* committing — I did it myself six times today — so a bar that refuses a dirty
tree is a bar that gets run with a flag to switch this off, which is the same outcome as not having
it. That is P-22's own reasoning ("a guard that refuses honest work gets switched off") applied to
the guard rather than to the predicate. The cost is real and is paid daily. What is *not* given up
is visibility: an uncommitted edit is named, counted and printed on every run.

**It also prints its own two object ids on every run, pass or fail**, which converts T446's
out-of-band human protocol step into one command a reader can recompute from the commit alone:

```
conformance:   this harness .softhouse/conformance.sh: committed <id> / on disk <id>
conformance:   (RECOMPUTE THE LEFT-HAND ID FROM THE COMMIT ALONE:
conformance:    git rev-parse HEAD:.softhouse/conformance.sh …)
```

**It is calibrated before it is allowed to report a zero** (P-72 / T238's sweeplib invariant,
adopted in shape — this is not a sweep and has no engine to calibrate): this file's own committed
object id must be findable in the index the guard is about to search. A search that cannot find the
file it is running from cannot be believed when it says it found nothing. `HEAD` unresolvable, an
empty index, a `git diff-index` that errors, a `grep` that exits `>1`, an empty hash: **five
distinct refusals**, none of which can be reached by the same path as "clean".

---

## 2. THE SEVENTH ROUTE — `LONGSTRIP`. FOUND, DRIVEN, AND **NOT CLOSED**

A guard that lives inside the text under attack cannot survive an attacker who edits that text.
Arm `LONGSTRIP` is `LONGS` with three extra lines deleted from the forged blob: the
`timed_guard guard_harness_text_is_committed` wiring and its budget row.

**Spelling, so the next reader can find it:** `.softhouse/conformance.ſh`, the same
`U+017F LATIN SMALL LETTER LONG S` entry, whose blob additionally omits every line matching
`timed_guard guard_harness_text_is_committed` and the `GUARD_COST_BUDGETS` row
`guard_harness_text_is_committed|60`.

**MEASURED ON THE DELIVERED TIP: `LONGSTRIP` reaches EXIT 0, probe PRESENT ×1 `up`,
`VERDICT: PASS … 46 parity vectors … 7884 cells`, `declared=3`, with the planted checker
absolved** — `evidence/34-OPEN-arm-LONGSTRIP-seventh-route.txt`. The committed harness reads
`7c543532…`; the harness that ran is `f863ce3f…`. I am not writing "cannot" about it. It works.

**What the remedy still buys, stated exactly and measured:**

1. it closes the forgery that does **not** also strip it — which is precisely the forgery T446
   drove, whose forged blob differed from the honest one by ONE table row (`LONGS`: EXIT 2);
2. it makes the surviving attack **larger and louder**, and by an amount the harness already
   enforces. **Arm `LONGSTRIP1` deletes only the `timed_guard` line and leaves the
   `GUARD_COST_BUDGETS` row: EXIT 2, probe count 0** —
   `guard-cost: GUARD_COST_BUDGETS carries a row for guard_harness_text_is_committed, which this
   run NEVER TIMED … 1 stale budget row(s)` [`evidence/42-barlog-arm-LONGSTRIP1-stale-budget-row.log`].
   So the smallest working forgery is now **two deletions in two separate places** plus the row it
   wanted, not one row — and `git diff` of the two blobs shows a deleted guard;
3. it makes the *honest* case self-reporting, on every run, in a form a reader can recompute.

**What can actually close it, and it is not in this file:** a verifier OUTSIDE the text — the fire
driver, or CI, comparing `git rev-parse HEAD:<path>` with `git hash-object <path>` (and refusing a
`git clone` that emits `warning: the following paths have collided`) **before** it trusts a
transcript. Filed as `FU-T454-1`. I hold `conformance.sh`; `.softhouse/bin/fire-program.sh` and the
CI wiring are somebody else's grant this wave.

---

## 3. THE FOLD CENSUS — HOW MANY OTHERS?

T446 wrote: *"One fold is enough to falsify 'cannot win'; I make no claim about how many there
are."* This is that claim, measured. `instruments/fold-census.py` generates candidates from
Unicode (`str.lower`, `str.casefold`, single-codepoint `NFKD` — deliberately **wider** than APFS's
own table, because over-generation is filtered by the filesystem probe while under-generation would
silently shrink the answer), then **asks the filesystem**: write two distinguishable contents at
two spellings, read back which survived. It calibrates on `U+017F` (must collide) and `z` (must
not) before reporting any count, and a read that returns neither content is `exit 3`.

**Over every printable ASCII character** (`evidence/02-fold-census-all-ascii.txt`):

```
TOTAL candidates generated      : 1075
TOTAL that COLLIDE on this fs   : 4
TOTAL that also SORT AFTER      : 4
TOTAL usable as a checkout win  : 4
```

| ASCII | folds from | sorts after? |
|---|---|---|
| `s` | **`U+017F` LATIN SMALL LETTER LONG S** | yes (`c5 bf` > `73`) |
| `k` | **`U+212A` KELVIN SIGN** | yes (`e2 84 aa` > `6b`) |
| `;` | **`U+037E` GREEK QUESTION MARK** | yes |
| `` ` `` | **`U+1FEF` GREEK VARIA** | yes |

**Restricted to the characters of `.softhouse/conformance.sh` and `.softhouse/guards`
(`evidence/01-fold-census-paths.txt`): 486 candidates, exactly ONE collides — `U+017F`.**

**T446's `U+212A` row is a false negative and I correct it.** T446 reported *"Kelvin U+212A
files=2 conformance.sh reads=REAL (distinct)"*. There is no `k` in `conformance.sh`, so that probe
substituted the Kelvin sign into a path with nothing to fold onto, compared two genuinely different
names, and read "distinct" as "does not fold". Measured directly
(`evidence/00-host-and-fold-probes.txt`):

```
U+212A KELVIN vs ASCII k                          : files=1  xky reads=BBB      <- IT FOLDS
U+017F LONG S in conformance.sh                   : files=1  conformance.sh reads=BBB
U+212A appended to conformance.s (no k to fold)   : files=2  conformance.sh reads=AAA   <- T446's probe
```

**And the generalisation that matters more than the count.** Every non-ASCII collider sorts after
its ASCII partner **unconditionally**: UTF-8 encodes every codepoint `>= U+0080` with a leading
byte `>= 0xC2`, which is greater than every ASCII byte. So "an all-lowercase ASCII path is
unbeatable" is not merely false for `U+017F` — it is false for the *entire* non-ASCII collider set,
whatever its size on a given host. The only fold partners that sort BEFORE their target are ASCII
uppercase, which is the case T445 correctly analysed and incorrectly generalised from.

**NFD/NFC: confirmed refuted, cheaply, and I did not spend more.** `core.precomposeunicode=true`
on this host [VERIFIED: `git config --get core.precomposeunicode` → `true`], and
`.softhouse/conformance.sh` is pure ASCII and has no NFD form. Negative result inherited from T446,
spot-checked, not re-driven.

---

## 4. THE GENERAL FORM — WHAT ELSE INHERITS IT

> **THE TEXT THAT EXECUTES IS NOT NECESSARILY THE TEXT THAT IS COMMITTED.**

`instruments/worktree-read-census.py` counts the sites in `conformance.sh` that touch this host's
filesystem at a `$REPO_ROOT` path. **It does the two-pass thing on purpose**, because a census that
matched only the line carrying `$REPO_ROOT/` would commit T446's own `MAJOR-2` error: almost every
site in this file *binds* the path to a local and *touches* the filesystem somewhere else.

```
total $REPO_ROOT/ occurrences (comments included): 32
of which EXECUTABLE text                         : 18
variables bound to a $REPO_ROOT path             : 15
EXECUTABLE sites that TOUCH the filesystem       : 27
of those, whose path contains a character this host FOLDS : 26
```

**Twenty-six of twenty-seven**, because every path under `.softhouse/` contains the `s` of
"softhouse". The list is `evidence/03-worktree-read-census.txt` and it includes every checker this
harness *executes* from the working tree — `check-ledger-invariants.sh`, `check-capture-namespace.sh`,
`check-dead-path-frontier.sh`, `50-failopen-lint.py`, `check-pnumber-citations.py`,
`run-ownership-matrix.py`, `.softhouse/bin/ready-tasks.py`, `ledgerguard/main.go` — three of which
additionally contain a `k` and are therefore reachable by `U+212A` as well as by `U+017F`.

**Every one of those 26 is covered by `guard_harness_text_is_committed`**, because the guard does
not enumerate a declared set: it takes `git diff-index --name-only HEAD` over the WHOLE tree and
adjudicates each modified path. A new working-tree read added tomorrow is covered without anyone
remembering to register it. **What is NOT covered is `LONGSTRIP` — the guard removing itself —
and that applies to all 26 equally.**

**The sentence I would put in `patterns.md`** (I do not hold that file; `FU-T454-2`):

> **A test may read the working tree only for questions ABOUT THIS RUN.** For any question about
> what is COMMITTED — is it registered, does it name me, is it tracked, *is it the code I am
> executing* — the working tree is not evidence, and on a case- or fold-insensitive filesystem it
> is not even a function of the commit. **"What executes is what is on disk" is a reason to READ
> the disk, never a reason to TRUST it.**

---

## 5. MAJOR-2 — THE WATCH PINNED THE READS, NOT THE USES

### RED, on `main` at `cbc8733c`, my own fixture, ONE substitution

```
-        elif ! LC_ALL=C grep -qF -- "$base" <<<"$self_text"; then
+        elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then
```

Over a fresh T444 M-1 fixture: `.softhouse/guards/zz-t454-member.sh` declaring
`REACHED-BY .softhouse/guards/W.txt`; `W.txt` a 100644 decoy naming nothing; `w.txt` a 120000
symlink to the member, sorting last and winning the checkout.

| arm | result on `main` |
|---|---|
| `RWB3CTL` | **EXIT 2**, probe count **0**, `reached-by=1` — the tip refuses the fixture |
| **`RWB3`** | **EXIT 0**, probe PRESENT ×1 `up`, **`VERDICT: PASS … 46 … 7884`**, `reached-by=2`, and the guard printing `.softhouse/guards/W.txt (verified: it names zz-t454-member.sh)` — **over a committed blob that names nothing** — while the watch printed **`registration decisive lines: 7 present, 2 evaluated`** |

Transcripts: `evidence/12-RED-arm-RWB3CTL.txt`, `evidence/13-RED-arm-RWB3.txt`.

### GREEN, on the delivered tip — and the attribution, because the refusal is over-determined

`RWB3` refuses on the tip at **EXIT 2, probe count 0**. But `guard_harness_text_is_committed`
**also** fires on this fixture (the `W.txt` / `w.txt` symlink collision is a substitution in exactly
its sense), so "it refused" would not by itself show that the needle did the work. **It did, and
the guard says which needle**, from `evidence/41-barlog-arm-RWB3-refusal.log`:

```
conformance: guard_registration_decisive_lines: THE DECISIVE LINE IS GONE —
conformance:   the WITNESS naming test USES the tracked blob as its HAYSTACK [T454, arm RWB3]
…
conformance: guard_registration_decisive_lines FAILED: 1 of 10 decisive
conformance: line(s) ABSENT and 0 NOT UNIQUE, in the body of
conformance: guard_guards_dir_registration as deployed in …
```

**Two independent refusals, and I am claiming only the second for `MAJOR-2`.**

### THE REMEDY

Three new needles pin the **step that consumes** each tracked blob, so the haystack of each
deciding `grep` is now part of the pinned text:

```
grep -qF -- "$base"  <<<"$self_text"      the WITNESS naming test
grep -qF -- "$token" <<<"$wit_text"       the CALLER token test
grep -qF -- "$member_text" …              the SUBJECT token test
```

(assembled at run time from fragments, as the existing seven are, so no needle appears whole on a
line of the file and this function cannot be the occurrence it counts). **Ten needles, and the
watch now prints `10 present EXACTLY ONCE in the body of guard_guards_dir_registration`.**

---

## 6. MINOR-1 — THE PIN GRADED A LINE, NOT A STEP

Three defects, one remedy each, all in `guard_registration_decisive_lines`:

| defect | remedy |
|---|---|
| `present()` was a substring `case` over the **whole comment-stripped file** — an occurrence in any function, in a `say` string, anywhere, satisfied it | the haystack is now the **body of `guard_guards_dir_registration`**, cut between its opening line and the next `}` in column zero. **A body it cannot cut is an INSTRUMENT failure and refuses**, because "no occurrences" and "no haystack" must not share a verdict |
| a **trailing** comment survives `grep -v '^[[:space:]]*#'` (full-line only), so `foo   # git cat-file blob "$self_blob"` satisfied the pin; so did a `:` no-op | a line qualifies only if the needle occurs **before any trailing ` #`** and the line is not a `:` no-op |
| `discriminates()` graded the **FIRST** `grep -m1` match, so an earlier decoy `elif` carrying the needle satisfied the behaviour test while the real line sat neutered | both tests use **the same qualifying scan**, and **`decisive_hits` must be exactly 1** — `0` is `THE DECISIVE LINE IS GONE`, `>1` is `THE DECISIVE LINE IS NOT UNIQUE`, two findings with two refusals |

---

## 7. THE CORRECTED AUDIT TABLE — **FOUR**, AND NOW **THREE**

T445 stated the remainder as *"the only file it still reads from this host is
`.softhouse/conformance.sh`"*. T446 found four. I re-derived the enumeration and removed one.

| # | read | in T445's table? | T454's judgement |
|---|---|---|---|
| 1 | `[ ! -d "$gd" ]` — does the guards directory exist on this host | **no** | **KEPT.** A question ABOUT THIS RUN, not about a commit, and it can only fail CLOSED |
| 2 | `[ ! -f "$conf" ]` — can this harness open itself | folded into row 2 | **KEPT.** Same shape, same direction |
| 3 | `code="$(grep -v '#' "$conf")"` — the DEPLOYED text | row 2 | **KEPT, and it is load-bearing.** A checker "invoked" only by a line that is not in the file that runs is not invoked. This is the read T446 attacked; it is now defended by `guard_harness_text_is_committed` |
| 4 | the SAME `grep -v` again, inside `guard_registration_decisive_lines` | **no — and T445 added it** | **REMOVED.** The stripped text is passed in as `$2`. T445 wrote *"two reads of one quantity are two chances to disagree"* four hundred lines above and broke it in the same commit |

The correction is now **in the file**, as a comment inside the function, so the next reader does
not have to reconstruct it from three handoffs. **All six of `main`'s graded-path working-tree
reads survive only in comments on the tip — T445's headline claim holds under my own enumeration.**

---

## 8. LOW — DISPOSITION

**`LOW-1` — the `-f` deletion moved a boundary silently. STATED IN THE FILE.** T445 deleted the
`-f` existence test to close T444's `LOW-4`, and **the deletion is correct**: `-f` could only ever
refuse, and it refused honest work (a committed-but-unmaterialised witness — sparse checkout,
partial checkout, or the loser of any collision — has a readable blob and no file). But two of
T364's refusals went with it, and T375's comment claiming they were *deliberately kept* was still
in the file, now false. On the tip:

* a **DIRECTORY** witness containing exactly one tracked file resolves to that file and is graded;
* a **PATHSPEC-MAGIC** witness matching exactly one tracked file does the same.

Neither is a fail-open — what is finally graded is still an independent committed file whose BLOB
must name the member, and self-reference, symlink, same-blob and round-trip all still refuse.
`self_multi` still refuses anything matching more than one entry, so "exactly one" is the whole of
the residue. **What was lost is reviewability**: the row's text stops being the path that gets
graded. Recorded, not driven — a statement about my search, not about the world.

**`LOW-2` — the sweep was one pin deep. RE-RUN TWO PINS DEEP, AND IT CHANGED WHAT I SHIPPED.**
`instruments/citation-sweep.py` resolves every `conformance.sh:NNNN` citation in the repository on
**both** trees. On my first commit (`28608f2c`): **1770 occurrences, 439 distinct line numbers,
170 at or below the first line I moved, and 58 that RESOLVED BEFORE AND ROTTED AFTER — including
`.softhouse/patterns.md:3426 → conformance.sh:3271`, the live pin T445 checked and T446 verified.**

I did not disclose that and move on. **I moved my own comment block below line 3271** so the pin
does not move [VERIFIED on the delivered tip: `sed -n '3271p'` is byte-identically
`warn "conformance: guard_guards_dir_registration: the population is EMPTY. That is a SELECTOR"`].
Re-swept at `f8466f7c`: first changed line **3276**, **138** citations moved, **34** broke.

All 34 survivors are historical transcripts, past reviews and past handoffs — records describing
the state at their own commit — plus `tasks.json:3385`. **None is a live pin any guard reads.**
Two honest limits on that number: "resolves" here is the weakest possible proxy (the cited line is
non-blank and non-comment), so a row that still "resolves" is **not** evidence the citation still
means what it meant; and the sweep sees only citations spelled `conformance.sh:NNNN`.
`evidence/04-citation-sweep.txt`.

**`LOW-3` — line-number citations in a handoff rot in the commit that moves them.** T446 found
T445's own wiring citation `:4757` had become `:4760` on the tip it shipped, in the very commit
that removed seventeen line-number citations. **This handoff cites nothing in `conformance.sh` by
line number.** Every reference to the file's contents is by function name, by needle text, or by
arm name. `grep -c 'conformance\.sh:[0-9]'` over this file returns **1**, and that one occurrence
is `patterns.md:3426 → conformance.sh:3271` — the pin this section is *about*, quoted as data.
That is P-80's own prescription and it is the only remedy that does not need maintaining.

---

## 9. WHAT I DID NOT CHECK — statements about my search, never about the world

* **A case-SENSITIVE filesystem, and a second git binary.** Every measurement here is APFS,
  case-insensitive, `git 2.50.1 (Apple Git-155)`, `bash 3.2.57`. The collision-order fact and the
  four-character fold table are facts about **that** host. On a case-sensitive filesystem the whole
  route disappears and `guard_harness_text_is_committed` costs 2 s and finds nothing — which is the
  correct behaviour and is also why nobody there will notice it working.
* **`--skip-worktree`, `--assume-unchanged`, sparse checkout, `.gitattributes` smudge filters,
  `core.symlinks=false`.** T445 disclosed all five and drove none; T446 drove none; **I drove
  none.** Three of them are now *partly* covered as a side effect: `--assume-unchanged` and
  `--skip-worktree` suppress `git diff-index`, so a harness modified under either would be reported
  as clean by my guard. **A smudge filter is worse and I name it as an open route: `SMUDGE`** — a
  `.gitattributes` filter can produce disk bytes that are not any tracked blob, which lands in my
  guard's EDITED branch and is therefore **printed and accepted**, not refused. Closing it needs a
  `git check-attr filter` refusal on the graded paths; I did not write it and I did not drive it.
* **Whether `guard_harness_text_is_committed` is itself pinned by anything.** It is not.
  `guard_registration_decisive_lines` watches one function and I did not widen it to a second,
  because `LONGSTRIP` shows self-pinning does not survive the attacker it is aimed at — but it
  *would* survive an honest future edit that neuters the guard, which is a different and real
  threat. `FU-T454-3`.
* **The pinned toolchain.** Every arm ran under the announced FALLBACK toolchain, RED and GREEN
  alike. Neither side is graded under the pinned toolchain.
* **`patterns.md`** — outside my grant, as it was outside T445's and T446's. The P-number for §4's
  sentence is still unwritten and a fifth generation has now paid for it.

---

## 10. FOLLOW-UPS

* **`FU-T454-1`** *(from `LONGSTRIP`, and it is the important one)*. Put the committed-vs-materialised
  comparison **outside** `conformance.sh`: `.softhouse/bin/fire-program.sh`, or CI, comparing
  `git rev-parse HEAD:<path>` with `git hash-object <path>` and refusing a checkout whose `git clone`
  emitted `warning: the following paths have collided`, **before** it trusts a bar transcript.
  Drive it with arm `LONGSTRIP`.
* **`FU-T454-2`**. `patterns.md` needs §4's sentence under its own P-number, with the discriminator
  and the corollary.
* **`FU-T454-3`**. Decide deliberately whether `guard_harness_text_is_committed`'s decisive lines
  get a pin of their own against honest neutering, knowing a pin does not stop `LONGSTRIP`.
* **`FU-T454-4`** *(from `SMUDGE`)*. Refuse a configured `filter` attribute on any graded path.
* **`FU-T454-5`** *(from `LOW-1`)*. Decide deliberately whether a witness row may be a directory or
  a pathspec at all, now that `-f` no longer refuses either.
* **`FU-T454-6`** *(from `LOW-2`)*. 34 more `conformance.sh:NNNN` citations rotted with this commit
  and 70 were already dead. The remedy is the one T445 applied to this file's outbound citations:
  cite by name. Somebody who holds those files should do it.

---

## 11. ROUTES I COULD NOT CLOSE — BY NAME AND SPELLING

| name | spelling | status |
|---|---|---|
| **`LONGSTRIP`** | `.softhouse/conformance.ſh` (`U+017F`), forged blob additionally deleting every line matching `timed_guard guard_harness_text_is_committed` and the budget row `guard_harness_text_is_committed|60` | **DRIVEN. OPEN.** Unclosable from inside this file. `FU-T454-1` |
| **`KELVIN`** | `.softhouse/guards/chec<U+212A>-ledger-invariants.sh`, `.softhouse/guards/chec<U+212A>-capture-namespace.sh`, `.softhouse/guards/chec<U+212A>-dead-path-frontier.sh`, `.softhouse/capture/t282-pnumber-drift/bin/chec<U+212A>-pnumber-citations.py`, `.softhouse/bin/ready-tas<U+212A>s.py` | **NOT DRIVEN.** The fold is measured; the substitution is the identical construction to `LONGS` against a different read. Covered by `guard_harness_text_is_committed` by the same mechanism, and defeated by the same `LONGSTRIP` |
| **`SMUDGE`** | a `.gitattributes` `filter=` on a graded path | **NOT DRIVEN. OPEN.** Lands in the guard's EDITED branch: printed, accepted. `FU-T454-4` |
| **`SKIPWT`** | `git update-index --skip-worktree .softhouse/conformance.sh` (and `--assume-unchanged`) | **NOT DRIVEN. OPEN.** Suppresses `git diff-index`, so the guard reports clean |
| `GREEKQ` / `VARIA` | `U+037E` → `;`, `U+1FEF` → `` ` `` | **MEASURED, no target.** No tracked path in this repository contains a `;` or a backtick |
| `NFD` | an NFD spelling of any tracked path | **REFUTED** (T446, spot-checked here). `core.precomposeunicode=true` collapses the pair at `update-index` time; ASCII paths have no NFD form |

---

## 12. FINAL BAR — MY OWN COMMITTED TREE

Run from `/tmp/t454/finalbar`, scratch, **outside the repo**, with `bash` (never `sh`/`zsh`), on
the committed tip. Probe line **PRESENCE** read **before** its value (P-84 — an absent probe line
is the guard working, not `down`).

Run from `/tmp/t454/finalbar`, scratch, **outside the repo**, with `bash` (never `sh`/`zsh`), on
the committed tree `94cb9abc`. `git status --porcelain` was **EMPTY before AND after**.
Full transcript: `evidence/90-FINAL-BAR-committed-tree-94cb9abc.log`.

```
EXIT = 0
grep -c 'probe = ' = 1                     <- PRESENCE read BEFORE the value (P-84)
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

| figure | required | measured |
|---|---|---|
| exit | 0 | **0** |
| `probe = ` line count, read before its value | >= 1 | **1** |
| probe value | — | **`up`** |
| VERDICT | PASS 46 / 7884 | **PASS 46 / 7884** |
| guards-dir census | unmoved | **`population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0`** |
| `deadOccurrences` / `deadFiles` | 108 / 75 | **108 / 75** |
| fail-open frontier | 11 == 11 | **`frontier 11, pinned at 11`; `frontier == pinned (all 11 rows, by path)`** |
| dead-path frontier | GREEN | **GREEN, reconciliation list empty** |
| host-state census | 18 == 18 | **`census == pinned (all 18 site(s), by path and source line)`** |
| wrong ledger implementations | 16, all dead | **all 16 DIED through this harness** |
| guards timed | — | **16** (was 15; this branch adds one, and the number is DERIVED by counting, never typed — the hand-written "fifteen guards" in `guard_cost_census`'s own refusal text is deleted in the same commit, P-80) |
| `guard_harness_text_is_committed` cost | under 60 s | **0–2 s / ceiling 60 s**, `guard-cost: PASS` |
| registration decisive lines | — | **`10 present EXACTLY ONCE in the body of guard_guards_dir_registration`, 2 evaluated** |
| HARNESS-TEXT census | 0 substitutions on a clean tree | **`differ from HEAD: 0 — SUBSTITUTED … 0, uncommitted edits 0, deleted 0`**, and `committed 7c543532… / on disk 7c543532…` |

The dead-path CORPUS moved 1613 → 1618 (+5: this task's instruments). Nothing pins it, and
`deadOccurrences` — which is pinned — did not move: the first committed version of
`drive-t454.sh` put **five NEW rows on the frontier** by spelling its fixture paths as literals,
the guard refused the whole bar, and the paths are now assembled at run time. **Repaired rather
than pinned, which is the rule that guard prints.**

**A second bar, on the tip that carries this transcript.** The commit above cannot contain its own
transcript, so the delivered tip is one commit later and its bar was run separately; its figures
are reported in the task's completion message and were identical.

---

## 13. VERDICT ON MY OWN WORK

The remedy is real and it is the right shape for the attack T446 drove. **It is not a closure of
the class, and I say so in the file as well as here.** The next reader should assume there is an
eighth route and go looking for it before believing this paragraph. The two questions I would ask
first, because they are the ones I did not finish: **what does this harness trust that is not a
blob and not on this host at all** — the reference-oracle container, the toolchain, `$PATH` — and
**what happens to all of this on a case-SENSITIVE filesystem, where every arm above is a no-op and
the guard that would catch a different attack has never been seen to fire?**
