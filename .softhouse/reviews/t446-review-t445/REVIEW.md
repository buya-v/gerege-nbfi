# T446 — independent review of T445 (`softhouse/T445-case-route`, tip `236fc829`)

**Reviewer:** T446, own worktree, branch `softhouse/T446-review-t445`.
**Subject:** T444's `M-1` plus `C-1`…`C-4` and the five LOW, as delivered by T445.
**Method:** every number below is MINE. I built my own instrument, planted my own fixtures and
drove every arm through the WHOLE bar from a cwd outside the repo. Where I merely read, I say so.
**Host:** macOS 26.5.1, APFS (case-INSENSITIVE), `git version 2.50.1 (Apple Git-155)`,
`bash 3.2.57(1)-release`. Every git claim below was verified on THAT git and no other.

---

## VERDICT: **APPROVED WITH CONDITIONS**

The remedy is real, it is the right remedy, and I reproduced every fail-open T445 claims. But the
chain's record holds for a sixth link: **there is a SIXTH ROUTE, I drove it, and it lands on the
one working-tree read T445 chose to keep and argued "provably cannot win".**

| # | finding | severity |
|---|---|---|
| **MAJOR-1** | **SIXTH ROUTE, DRIVEN.** Claim 3 is false on this host: an all-lowercase ASCII path is **not** unbeatable. `U+017F` (`ſ`) folds onto ASCII `s` on APFS and sorts AFTER it, so `.softhouse/conformance.ſh` **wins the checkout collision against `.softhouse/conformance.sh`**. Driven on the T445 TIP: the committed harness is honest, the harness that RUNS is forged, and `guards-dir registration: PASS` absolves a checker the identical commit without that entry refuses. | **MAJOR** |
| **MAJOR-2** | `guard_registration_decisive_lines` pins the **reads**, not the **uses**. The needle for "the WITNESS naming test reads the TRACKED BLOB" sits on the assignment, not on the `grep`. **M-1 is restored by one substitution with all 7 pins still reporting present and 2 evaluated.** | **MAJOR** |
| **MINOR-1** | The presence test is a substring search over the whole comment-stripped file, and `discriminates` grades the FIRST match. A needle in a trailing comment, or on a `:` no-op line, satisfies the pin; a decoy `elif` earlier in the file satisfies the behaviour test. | MINOR |
| **MINOR-2** | The audit table says the harness's own text is the only remaining working-tree read. There are **four**, and one of them (`grep -v '#' "$conf"` inside `guard_registration_decisive_lines`) was **added by T445 itself** — a second read of a quantity already in hand, which this same function's comments call a defect. | MINOR |
| **LOW-1** | Deleting the `-f` test also deletes T364's DIRECTORY-witness and PATHSPEC-MAGIC-witness refusals, which the file's own T375-era comment calls load-bearing. Not a fail-open; an accepted/refused boundary moved without being stated. | LOW |
| **LOW-2** | The inbound-citation sweep was ONE pin deep. 16 repo-wide `conformance.sh:NNNN` citations point ABOVE `:3271` and were therefore moved by this commit. I resolved all 16 on both trees: every one was **already rotted on `main`**, so the conclusion "no pin moved" survives — by luck, not by the evidence offered. | LOW |
| **LOW-3** | The handoff's own wiring citation `timed_guard guard_guards_dir_registration :4757` is `:4760` on the delivered tip — a line number restated in prose, in the commit that removed seventeen of them (P-80). | LOW |

**Nothing here is merge-blocking on its own.** MAJOR-1 and MAJOR-2 are both *outside* the class
T445 was asked to close: T445 closed every member/witness/declared-witness working-tree read and I
confirm that. What is left is (i) the harness's own text, and (ii) the watch that guards the lines.
Both belong in a follow-up task with the file, not in a rejection of this one.

---

## 0. SCOPE, MONEY, AND THE DIFF

```
$ git diff --name-only main...softhouse/T445-case-route | grep -v '^\.softhouse/capture/t445-case-route/'
.softhouse/conformance.sh
.softhouse/handoff/T445-case-route.md
```

Grant respected. No arithmetic, no money, no float, no ledger, no vector, no DEC-n, no contract,
no database driver [VERIFIED: `grep '^+' <diff> | grep -E 'float|[0-9]+\.[0-9]+|bc |BigDecimal'`
returns one hit and it is the string `git 2.50.1` inside a comment]. The money non-negotiables are
not touched by this change.

**Measuring the diff:** `main` has advanced past the merge base. Everything above is three-dot
(`main...softhouse/T445-case-route`, merge base `b102875c`); a two-dot diff would have
misattributed the driver's later merges.

---

## 1. CLAIM 1 — "M-1 was one instance of a class, and `main` had THREE MORE LIVE MEMBERS"

**RE-DERIVED, AND CONFIRMED.** I did not inherit T445's fixtures. My instrument
(`instruments/drive-t446-v5.sh`) clones the tree under test, plants, commits, **RE-CLONES** so a
collision materialises as a fresh checkout would, applies any working-tree-only mutation to the
tree that is graded, and runs the whole bar from `$WORK/cwd`, outside every repo. It **detects the
implementation under grade from that tree's own text** and prints it on every arm; the mode is not
passable in. It reads the probe line's **PRESENCE before its VALUE** (P-84).

### The arms, on UNMUTATED `main`

| arm | construction | `main` result | reading |
|---|---|---|---|
| `Z` | control | **EXIT 0 / probe PRESENT ×1 / `up` / PASS 46-7884**, `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | a clean tree passes |
| `LEGA` | an entirely honest plain-ASCII registration | **EXIT 0 / PRESENT / `up` / PASS**, `reached-by=2` | honest work is accepted |
| **`CASE`** | T444's M-1, my own construction: header declares `W.txt`; `W.txt` is a 100644 decoy naming nothing; `w.txt` is a 120000 symlink to the member and sorts LAST | **`registration: PASS`, `reached-by=2`**, and the guard printing *"REACHED-BY …/zz-t446-member.sh — declared in its own header, reached by .softhouse/guards/**W.txt** (verified: it names zz-t446-member.sh)"* | **M-1 confirmed live on `main`** |
| **`MCASE`** | two index entries whose DIRECTORIES differ only in case; the smuggled `ZZ-T446M/x.sh` carries **no registration row at all** in its committed blob | **EXIT 0 / PRESENT ×1 / `up` / PASS 46-7884**, `population=8 invoked=3 declared=2 **reached-by=3**`, and `ZZ-T446M/x.sh` printed as *"declared in its own header"* | **new fail-open confirmed, at exit 0** |
| **`LEGDIRTY`** | the registration row exists **only in the working tree** | **EXIT 0 / PRESENT ×1 / `up` / PASS 46-7884**, `reached-by=2` | **confirmed** |
| **`WDIRTY`** | the witness names the member **only in the working tree** | **EXIT 0 / PRESENT ×1 / `up` / PASS 46-7884**, `reached-by=2` | **confirmed** |
| **`CDIRTY`** | the DECLARED witness stops naming its token in the working tree only | **`guard_guards_dir_registration FAILED`**, `declared=1`, exit 2 with the probe **ABSENT** | **confirmed** — the DECLARED verdict was decided by this host (fail-CLOSED direction) |
| `WGONE` | a committed witness this checkout does not materialise | `main` refuses | LOW-4's over-refusal confirmed |

Every one of `MCASE`, `LEGDIRTY` and `WDIRTY` reached **exit 0, probe line present exactly once,
`probe = up`, `VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells`** on unmutated `main`.
Transcripts: `evidence/11-arms-queue1.log`, `evidence/10-RED-arms-main-run1.log`.

`CASE` reached the guard's own PASS sentence and `reached-by=2` on a run whose overall exit was 2
because the local reference-oracle container was down at that minute (`probe = down`, see §9). The
guard runs before the probe, so its verdict is independent of the outage; I am reporting what I
measured rather than what I would have liked to measure.

### The arms on the T445 TIP

| arm | tip result |
|---|---|
| `Z` | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` — **unmoved** |
| `LEGA` | `reached-by=2`, accepted — **honest work still accepted** |
| **`CASE`** | **refused**, `reached-by=1`, probe **ABSENT** — **M-1 CLOSED** |
| **`MCASE`** | **refused**, `reached-by=2 invoked-by-nothing=1` — the smuggled member refused **and the honest sibling still REACHED-BY in the same run** |
| **`LEGDIRTY`** | **refused**, `reached-by=1 invoked-by-nothing=1` |
| **`WDIRTY`** | **refused**, `reached-by=1` |
| **`CDIRTY`** | registration **PASS**, `declared=2` — the DECLARED verdict is no longer decided by this host |
| **`WGONE`** | accepted, `reached-by=2` — LOW-4's over-refusal is gone |

**Claim 1 is upheld in full, on my own fixtures.**

### An arm of mine that measured the wrong thing, recorded rather than deleted

My **first** `CASE` construction (instrument `drive-t446-v4.sh`) refused on `main` — which looks
like "M-1 does not reproduce" and is not. Two separate instrument defects, both mine:

* `commit_all`'s `git add -A` ran AFTER the plant's `git update-index --cacheinfo`, so git re-read
  the case-folded working tree and **silently downgraded my 120000 symlink entry to the decoy's
  own 100644 blob**. Fixed in `v4` (`NOADD`), and the fix is in the file as a comment.
* `v4`'s planted member did not name itself in its own header. The symlink DID win the collision
  and `grep` DID dereference to the member — but the member's text did not contain its own
  basename, so the naming test missed **for a reason that has nothing to do with the defect**.
  Every real member of `.softhouse/guards` names itself in its header. Fixed in `v5`.

Both are in `evidence/11-arms-queue1.log` under the `v4` heading. An arm that refuses for the wrong
reason is indistinguishable from an arm that worked; that is why they are printed, not dropped.

---

## 2. CLAIM 2 — "zero working-tree reads of any graded path". **VERIFIED MECHANICALLY, WITH TWO ADDITIONS**

My enumeration is `evidence/00-t446-read-enumeration.md`; the search is stated there before its
result. Result:

* On `main`, six working-tree reads of graded paths exist, at `:3593`, `:3809`, `:3883`, `:4001`,
  `:4010`, `:4021`.
* On the tip, **all six survive only inside comments**. Every surviving `$REPO_ROOT` expansion in
  the function's executable text is either name construction or `cd "$REPO_ROOT" && git
  ls-files|cat-file`. **The headline claim — zero working-tree reads of any member, witness or
  declared witness — HOLDS.**

**MINOR-2.** The claim as generalised in the audit ("the only file it still reads from this host is
`.softhouse/conformance.sh`") is not exact. There are four working-tree reads, not one:

| line | read | in the author's table? |
|---|---|---|
| `:3221` | `[ ! -d "$gd" ]` — does `.softhouse/guards` exist on this host | **no** |
| `:3229` | `[ ! -f "$conf" ]` | folded into row 2 |
| `:3248` | `code="$(grep -v '^[[:space:]]*#' "$conf")"` | row 2 |
| `:4401` | the SAME `grep -v` on the SAME file inside `guard_registration_decisive_lines` | **no — and T445 added it** |

`:3221` can only fail closed. `:4401` is a second read of a quantity already held in `$code`; this
function's own comment about `member_blob` says *"It is not re-read here: two reads of one quantity
are two chances to disagree."* Harmless within one process. It is still the file's own stated
discipline broken in the same commit that invokes it.

---

## 3. CLAIM 3 — the one working-tree read that is KEPT. **THE JUSTIFICATION IS FALSE. MAJOR-1.**

T445 keeps `$conf` on the working tree, argued (a) *"the text that executes is the text on disk"*
and (b) the case attack **provably cannot win**, because the index entry that sorts **LAST** wins a
collision, so an all-lowercase path is unbeatable.

**(a) is right. The mechanism in (b) is right. The corollary in (b) is FALSE on this host.**

### The mechanism, re-measured on git 2.50.1 (Apple Git-155)

`instruments/collision-order.sh` → `evidence/02-collision-order-probe.txt`. Two 100644 entries
`A.txt` and `a.txt`: after `git clone`, the materialised file carries **`CONTENT-2`, the entry that
sorts LAST**. `instruments/symlink-collision.sh` → `evidence/03-symlink-collision-probe.txt`
extends it to the shape M-1 actually needs — a 100644 decoy sorting first and a **120000 symlink**
sorting last — and the symlink still wins, so a filesystem read of the decoy's name dereferences to
the member. **"Last wins" holds, including when the winner is a symlink. I verified it on
`git version 2.50.1 (Apple Git-155)` and on no other git.**

### The corollary does not

Case is not the only fold this filesystem applies. `evidence/01-filesystem-fold-probe.txt`, on this
APFS volume:

```
uppercase C                  files=1  conformance.sh reads=DECOY   <== FOLDS
uppercase H (.sH)            files=1  conformance.sh reads=DECOY   <== FOLDS
long s U+017F                files=1  conformance.sh reads=DECOY   <== FOLDS   <<<<<<
Kelvin U+212A                files=2  conformance.sh reads=REAL   (distinct)
```

`U+017F LATIN SMALL LETTER LONG S` folds onto ASCII `s`, and its UTF-8 bytes `c5 bf` are **greater
than** ASCII `s` = `73`. So `.softhouse/conformance.ſh` sorts **AFTER** `.softhouse/conformance.sh`
in the index and **WINS** the checkout. An all-lowercase path is beatable, and
`.softhouse/conformance.sh` contains four `s`-es to choose from.

### Driven, not argued — arm `LONGS` on the T445 TIP

`instruments/drive-longs.sh`. Same commit twice; the only difference is one extra index entry.

```
                              CONTROL (no ſh entry)      LONGS (with it)
committed blob of
  .softhouse/conformance.sh       62cda497…                  62cda497…   <- IDENTICAL. What `git show` prints.
materialised at that path         62cda497…                  742934c5…   <- *** NOT the committed blob ***
EXIT                              2                          0
probe line count (read first)     0                          1
probe value                       ABSENT                     up
VERDICT                           (none)                     PASS (exit 0) — 46 parity vectors, 7884 cells
guards-dir census            population=7 invoked=3       population=7 invoked=3
                             declared=2 reached-by=1      declared=3 reached-by=1
                             invoked-by-nothing=1         invoked-by-nothing=0
the planted checker          "zz-t446-unreg.sh IS         absolved: "guards-dir registration: PASS"
                              INVOKED BY NOTHING",
                              guard FAILED
```

[`evidence/20-sixth-route-LONGS.log`]

The forgery is one extra DECLARATION TABLE row. A reviewer running `git show
HEAD:.softhouse/conformance.sh` sees a table with two rows and a harness that refuses the planted
checker. The harness that **runs** has three rows and passes it.

**Reproduction:**
`bash .softhouse/reviews/t446-review-t445/instruments/drive-longs.sh /tmp/t446x <repo> softhouse/T445-case-route CONTROL`
then the same with `LONGS`.

### What limits it, stated honestly

`git status --porcelain` of the graded clone reports ` M .softhouse/conformance.sh`, because the
materialised bytes differ from the index blob for that path. **Any** two-entry collision on
`conformance.sh` is inherently dirty, so this route cannot be made invisible to `git status`.

But nothing inside `conformance.sh` looks: `grep -n 'git status\|diff-index\|diff --quiet' ` over
the whole tip returns **nothing**, and no guard compares the harness's own disk text to its
committed blob. The detection is entirely an out-of-band protocol step that a human performs. That
is precisely the shape T445 spent this whole task removing from the graded reads, left standing on
the read that decides what the graded reads even are.

### And the residual the author named is NOT the route

I did what the task asked and tried NFD/NFC first. **On this host you cannot build an NFD/NFC index
PAIR by the ordinary path.** `evidence/02-collision-order-probe.txt`, third block: adding
`caf\xc3\xa9.sh` and `cafe\xcc\x81.sh` produces **ONE** index entry, `"caf\303\251.sh"` —
`core.precomposeunicode=true` normalises the NFD spelling into the NFC one before it reaches the
index, so the second add overwrites the first rather than colliding. And `.softhouse/conformance.sh`
is pure ASCII, so it has no NFD form to be attacked with in the first place. **T445's own prime
suspect is not where the hole is.** The hole is a different fold, on the same read.

---

## 4. CLAIM 4 — `guard_registration_decisive_lines`. **WIRED. AND EVADED. MAJOR-2 + MINOR-1.**

### Wiring — verified by grep, not asserted (P-45)

```
$ grep -n 'main_grade\|run_guards\|timed_guard guard_guards_dir_registration\|guard_registration_decisive_lines "\$conf"'
5206:main_grade() {
5209:  run_guards
4714:run_guards() {
4760:  timed_guard guard_guards_dir_registration       || failed=1
3219:guard_guards_dir_registration() {
3303:  guard_registration_decisive_lines "$conf" || return 1
5905:  *)           main_grade "${1:-}" 0; exit $? ;;
```

The chain is intact and unconditional on every graded run. It is **not** a `timed_guard`, and
`GUARD-COST CENSUS: 15 guards timed` is unmoved on both trees. It printed
`registration decisive lines: 7 present, 2 evaluated on an input they must refuse AND an input they
must accept` on every tip run I made.

### MAJOR-2 — the pin binds the READ, not the USE

The task asked: *"if someone rewrites a decisive line to something equivalent-looking but wrong,
does the pin catch it?"* **No.** The needle for the single most important line —

```
n="$(printf '%s' 'git cat-file blob '; printf '%s' '"$self_blob"')"
present "$n" "the WITNESS naming test reads the TRACKED BLOB [T445, closing T444 M-1]"
```

— matches the **assignment** at `:3934-3935`. The test that decides is a *different line*,
`:4060`:

```
elif ! LC_ALL=C grep -qF -- "$base" <<<"$self_text"; then
```

and **nothing pins its haystack**. Point it back at this host in one substitution and every pin
still reports green:

```
-        elif ! LC_ALL=C grep -qF -- "$base" <<<"$self_text"; then
+        elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then
```

`$self_text` is still assigned from the tracked blob, so needle 6 is present; `$self_text` simply
stops being consulted.

**DRIVEN, as arm `RWB3`, over T444's own M-1 fixture, on the T445 TIP**
(`instruments/drive-rwb3-v3.sh`; `evidence/31-rwb3-v3-control-and-attack.log`,
`evidence/32-rwb3-final-exit0.log`). Same commit twice; the only difference is that one line.

```
                                RWB3CONTROL (tip unmutated)       RWB3 (one substitution)
line 4060 as deployed      grep -qF -- "$base" <<<"$self_text"  grep -qF -- "$base" "$REPO_ROOT/$self_norm"
needle 6 present?                  1 occurrence                       1 occurrence
the NEW watch says          "registration decisive lines:       "registration decisive lines:
                             7 present, 2 evaluated"             7 present, 2 evaluated"   <- GREEN
EXIT                                2                                  0
probe count (read first)            0                                  1
probe value                       ABSENT                               up
VERDICT                           (none)                    PASS (exit 0) — 46 parity vectors, 7884 cells
guards-dir census             reached-by=1                        reached-by=2
the guard's own sentence   "…W.txt DOES NOT NAME              "…W.txt (verified: it names
                            zz-t446-member.sh IN ITS            zz-t446-member.sh)"
                            COMMITTED BYTES" — REFUSED
```

The committed blob of `.softhouse/guards/W.txt` names nothing. The file on disk at that path is the
120000 symlink to the member, which sorts last and won the checkout. **M-1 is back, at exit 0, with
the probe present and reading `up`, with `VERDICT: PASS`, and with the watch that exists to prevent
exactly this reporting seven of seven lines present.**

**Reproduction:**
`bash .softhouse/reviews/t446-review-t445/instruments/drive-rwb3-v3.sh /tmp/t446y <repo> softhouse/T445-case-route RWB3CONTROL`
then the same with `RWB3`.

**An earlier version of this arm did not measure it, and is kept** (`evidence/30-rwb3-v2-invalid.log`):
`drive-rwb3.sh` used `perl -0pi -e 's/\Q…\E/…/'`, and Perl interpolates `$base` and `$self_text`
INSIDE `\Q…\E`, so the pattern became a different string and the substitution silently did not
apply — the drive printed `SUBSTITUTION DID NOT APPLY` and refused to run, which is the only
reason it did not become a false negative. `drive-rwb3-v2.sh` substitutes in python instead. A
second version, `-v2`, then refused for the wrong reason: its planted member did not name itself,
so the dereferenced `grep` missed. `-v3` fixes that and is the arm above.

Five of the seven pins have this shape (only the two `discriminates` rows are evaluated), and for
those five the pin is satisfied by the *string being somewhere in the file*, not by the deciding
step using it.

### MINOR-1 — two cheaper evasions of the same watch, by reading

* **`present()` is a substring `case` over the whole comment-stripped file.** Comment stripping is
  `grep -v '^[[:space:]]*#'`, which removes FULL-LINE comments only. A **trailing** comment —
  `foo   # git cat-file blob "$self_blob"` — survives stripping and satisfies the pin. So does a
  `:` no-op line. The needle is not required to be inside `guard_guards_dir_registration`, or
  inside any function, or reachable.
* **`discriminates()` grades the FIRST match**, `grep -m1 -F -- "$needle" <<<"$code"`. An earlier
  decoy `elif` line carrying the same needle and a healthy expression satisfies the behaviour test
  while the real line is neutered.

Both are the same defect one level up from the one the guard closes: **it grades a line, not the
step that decides.** `FU-T445-2` (no end-to-end forgery fixture) is exactly the right remedy and
the author already filed it; MAJOR-2 is the measurement that makes it merge-relevant rather than
aspirational.

---

## 5. CLAIM 5 — the citation rot. **RE-MEASURED INDEPENDENTLY. EXACT.**

`instruments/citation-rot.sh` → `evidence/04-patterns-citation-rot-on-main.txt`.

```
$ grep -o 'patterns\.md:[0-9]*' conf-main.sh | wc -l     ->  17
$ grep -o 'patterns\.md:[0-9]*' conf-main.sh | sort -u | wc -l  ->   9
$ grep -o 'patterns\.md:[0-9]*' conf-t445.sh | wc -l     ->   0
```

**17 occurrences, 9 distinct numbers, 0 remaining on the tip.** Resolving each against `main`'s
`patterns.md`:

| cited | claimed rule | line actually says | verdict |
|---|---|---|---|
| `:473` | P-22 | `### P-22. A guard, a canary, or a control that cannot fail…` | resolves |
| `:1472` | **P-45** | `directory you are measuring is the same defect as a guard that cannot fail…` | **ROTTED — P-45 is at `:1503`, +31** |
| `:1503` | P-45 | `**P-45 — A test-only guard is not a guard.**` | resolves |
| `:1654` | P-57 | `**P-57 — THE MACHINERY THAT EXISTS TO CATCH A SILENT GUARD…**` | resolves |
| `:1931` | P-70 | `### P-70. "Latent", "not promoted"…` | resolves |
| `:2775` | P-80 | `**P-80 — A CORRECTED CARDINAL ROTS…**` | resolves |
| `:2782` | **P-84** | `two currencies. **The fix is never the new number…**` | **ROTTED — P-84 is at `:2813`, +31** |
| `:2813` | P-84 | `**P-84 — "EXIT 2 WITH NO PROBE LINE" IS THE GUARD WORKING…**` | resolves |
| `:3084` | **P-95** | *(blank line)* | **ROTTED — P-95 is at `:3115`, +31** |

**Three rotted, all off by exactly +31, exactly as claimed.** Note what my table shows that the
handoff does not: `main` carried BOTH a rotted and a correct citation for P-45, and BOTH for P-84.
That is P-80's own worked example sitting in the file, which strengthens rather than weakens the
remedy. And `grep -c 'conformance\.sh:[0-9]' .softhouse/RESUME.md` = **0** on the tip [VERIFIED].

---

## 6. CLAIM 6 — the pinned figures. **CONFIRMED, WITH LOW-2 ON THE METHOD**

Measured by me, `Z` control on both trees and my own baseline bar on `main`
(`evidence/11-arms-queue1.log`):

| figure | `main` | T445 tip | required |
|---|---|---|---|
| guards-dir census | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | **identical** | unmoved ✔ |
| `deadOccurrences` / `deadFiles` | 108 / 75 | **108 / 75** | unmoved ✔ |
| dead-path FRONTIER | `frontier 11, pinned at 11` | **11 == 11** | unmoved ✔ |
| host-state census | 18 == 18 | **18 == 18** | unmoved ✔ |
| guards timed | 15, 0 breaches | **15, 0 breaches** | unmoved ✔ |
| wrong ledger implementations | 16, all 16 died | **16, all 16 died** | 16 ✔ |
| `guard_guards_dir_registration` cost | 1 s | **1–2 s / ceiling 60 s** | under ceiling ✔ |
| `patterns.md:3426 → conformance.sh:3271` | `warn "… the population is EMPTY. That is a SELECTOR"` | **byte-identical line** | resolves ✔ |

**LOW-2 — the sweep was one pin deep.** T445 checked `patterns.md:3426` and `RESUME.md` and
concluded no pin moved. I swept the whole repository instead
(`instruments/conf-citations.sh` → `evidence/05-conformance-line-citation-sweep.txt`): **327
`conformance.sh:NNNN` citations**, of which **16 point above `:3271`** and are therefore moved by
this commit — in `tasks.json` (`:3385`, `:3469`, `:3923`, `:4530`×3) and in the T323/T358/T364
handoffs (`:3296`–`:3303`, `:3554`, `:3567`, `:3741`, `:3744`, `:4032`, `:4057`, `:4058`).
I resolved every one on BOTH trees. **All 16 were already rotted on `main`** — `tasks.json:6092`'s
*"ALSO FIX `conformance.sh:4530` … BSD `sed` does not implement `\|`"* already pointed at a `_cmp`
call, and T323.md's call graph already pointed at unrelated comments. So T445's conclusion stands;
its evidence did not reach it. The right remedy is the one T445 itself applied to `patterns.md`:
cite by name, not by line.

---

## 7. CLAIM 7 — LOW-4 closed by DELETING the `-f` test. **CORRECT, WITH LOW-1**

I argue it independently and reach the same answer.

**The deletion is right.** The evidentiary question this direction asks is *"is there a committed,
reviewable, independent file that names this member?"* That question is answered completely by the
index entry and the blob. Materialisation on **this host** adds nothing to it and can only subtract:
a sparse checkout, a partial checkout, or the loser of any collision has a perfectly readable blob
and no file. A test that refuses honest work gets switched off, which is the same outcome as not
having it. The test also graded the **typed** spelling while everything downstream graded
`$self_norm` from the index — two different files, one verdict. Driven as `WGONE`: `main` refuses a
committed-but-unmaterialised witness; the tip accepts it, and nothing about the record changed.
**Nothing that mattered was removed with it in the fail-open direction** — `-f` could only refuse.

**LOW-1, which the handoff does not say.** The file's own T375-era comment, still present on the
tip at `:3808`, records that `-f` was deliberately kept so that *"the two refusals T364 verified
fail-closed by inspection — a witness that is a DIRECTORY, and a witness carrying PATHSPEC MAGIC
such as `:(glob)*` — still refuse there and refuse first."* Both of those refusals go with it. What
remains is `self_multi` (a witness resolving to more than one line) plus the round-trip equality, so:

* a DIRECTORY witness containing **exactly one** tracked file now resolves to that file, round-trips,
  and is graded;
* a pathspec-magic witness that matches **exactly one** file does the same.

Neither is a fail-open — the file eventually graded is still an independent committed file whose
blob must name the member, and self-reference, symlink and same-blob all still refuse. What is lost
is *reviewability*: the row's text stops being the path that gets graded. That is a real change to
an accepted/refused boundary, made silently, and it deserves a sentence in the file. I did not drive
it; that is a statement about my search, not about the world.

---

## 8. CLAIMS 8, 9, 10

**Claim 8 — the residual.** Addressed in §3. **NFD/NFC is not reachable on this host** and
`conformance.sh` has no NFD form; the fold that *does* reach it is `U+017F`. MAJOR-1.

**Claim 9 — the two INVALID arms.** Both supersessions are real, verified from the committed
transcripts:

* `RWB`: `GREEN-RWB-bar.log` is two lines, both
  `…/conformance.sh: line 4276: syntax error near unexpected token 'done'`. Exit 2, probe absent —
  a refusal, but from `bash`, not from a guard. `RWB2` substitutes instead of deleting. **Correctly
  superseded.**
* first `LEGDIRTY`: `RED-LEGDIRTY-figures.txt` shows `--- git status of the fresh clone ---`
  **EMPTY**, proving the dirty edit never reached the graded tree, and the arm refusing with
  `IS INVOKED BY NOTHING` — the honest reason. **Correctly superseded** by `RED2-LEGDIRTY`.

**No conclusion in the arm table rests on either.** The table's `LEGDIRTY` row cites the RED2
measurement and the `RWB2` row is the one that carries the finding.

The instrument freeze record also checks out, which matters because three tasks have now paid for
that lesson. All four states are in the branch and each hashes to what the handoff says:
`81e35bea` → `99e43a60…` (the never-run local-expansion bug), `eb795f1d` → `4f1cc183…`,
`b2c49ca9` → `9adf98c4…`, tip → `dbcae7a0…`. I hit the identical bash-3.2 trap myself
(`local a="$1" b="$a"` is an unbound-variable error under `set -u`) and record my own instrument
versions and hashes for the same reason.

**Claim 10 — `FU-T445-8`.** *"A test that reads the WORKING TREE cannot decide a question about what
is COMMITTED."* **The statement is correct and it generalises**, and my MAJOR-1 is the proof that it
generalises **past this function**: the same confusion, applied to the harness's own text, lets a
commit that reads honest execute forged. I would sharpen the wording to name the discriminator,
because the exception matters and this task turns on it:

> **A test may read the working tree only for questions ABOUT this run.** For any question about
> what is COMMITTED — is it registered, does it name me, is it tracked — the working tree is not
> evidence, and on a case- or normalisation-insensitive filesystem it is not even a function of the
> commit. Seven fail-opens in one function have had that shape.

It should also carry the corollary MAJOR-1 establishes: **"what executes is what is on disk" is a
reason to READ the disk, never a reason to TRUST it** — the two can be made to differ, and the only
detector is `git status`, which no guard in this harness runs.

Other guards deserve the same audit, and that is a task worth filing (`FU-T446-1` below).

---

## 9. WHAT I DID NOT CHECK — statements about my search, not about the world

* **A case-SENSITIVE filesystem, and a second git binary.** Every measurement here is APFS,
  case-insensitive, `git 2.50.1 (Apple Git-155)`, `bash 3.2.57`. The collision-order fact in §3 is
  a fact about THAT git; it is exactly the kind of thing that is true on one version and false on
  another, and I say which one I used because nothing else would be honest.
* **The pinned toolchain.** Every arm ran under the announced FALLBACK toolchain, RED and GREEN
  alike. Neither side is graded under the pinned toolchain.
* **`--skip-worktree`, `--assume-unchanged`, sparse checkout, `.gitattributes` smudge rules,
  `core.symlinks=false`.** T445 disclosed all five and drove none; **I drove none either.** After
  T445 none of them can move a member/witness/declared-witness verdict, because those reads are
  blobs. All five can still move the harness's own text, which is MAJOR-1's surface.
* **Other folds onto `.softhouse/conformance.sh`.** I tested `U+017F` (folds), `U+212A` (does not,
  and there is no `k` in the path anyway) and NFD (no NFD form of an ASCII path). I did not
  enumerate the whole APFS folding table. **One fold is enough to falsify "cannot win"; I make no
  claim about how many there are.**
* **`guard_dead_path_frontier`'s crash-on-non-ASCII** (T444 `C-4`) — different guard, out of my
  scope too. Note it did NOT crash on my `LONGS` fixture, which carries a non-ASCII tracked path
  (`.softhouse/conformance.ſh`): that run reached `T316-DEADPATH-CENSUS: corpus=1535 deadFiles=75
  deadOccurrences=108` and `dead-path frontier: GREEN`. So the census survives a non-ASCII path at
  the REPOSITORY ROOT; T444's transcripts are for one under `.softhouse/guards/`.
* **`patterns.md`** — outside my scope as it was outside T445's. `FU-T445-4` and `FU-T445-7` are
  still unwritten and a fourth generation has now paid for the freeze-your-drive lesson.

## 10. FOLLOW-UPS I WOULD FILE

* **`FU-T446-1` (from MAJOR-1).** Give `guard_guards_dir_registration` — or better, `run_guards` —
  a refusal when the harness's own materialised text is not its committed blob:
  `git rev-parse HEAD:.softhouse/conformance.sh` vs `git hash-object .softhouse/conformance.sh`,
  or simply a `git status --porcelain` refusal on `.softhouse/conformance.sh`. It is two lines and
  it converts an out-of-band human protocol step into a guard. Drive it with arm `LONGS`.
* **`FU-T446-2` (from MAJOR-2).** Second `FU-T445-2` and raise it: the decisive-lines watch must
  pin the **step that decides**, not a line that mentions it. The strongest form is the end-to-end
  forgery fixture T445 already proposed; the cheap form is to pin the `grep`'s haystack
  (`<<<"$self_text"`) as an eighth needle and to require each needle to occur INSIDE the function's
  own line range rather than anywhere in the file.
* **`FU-T446-3` (from claim 10).** `FU-T445-8` deserves its P-number, with the discriminator and
  the corollary in §8 above, and then **every other guard in `conformance.sh` needs the same
  index-versus-worktree audit** — this one function produced seven fail-opens of the shape and
  nothing suggests it is the only function that reads the working tree to answer a question about a
  commit.
* **`FU-T446-4` (from LOW-1).** State in the file what the `-f` deletion did to T364's DIRECTORY
  and PATHSPEC-MAGIC refusals, and decide deliberately whether a witness row may be a pathspec.
* **`FU-T446-5` (from LOW-2).** Sweep `conformance.sh:NNNN` citations repo-wide the way T445 swept
  `patterns.md:NNNN`: 16 of them already point at nothing.
* **Reference-oracle stability.** The `fineract-fineract-1` container took `SIGTERM` (exit 143)
  three times during this review under the load of sequential bar runs. Every affected arm is
  reported with `probe = down` and its guard-level verdict, and every arm whose finding depends on
  a full `exit 0` was re-driven after restarting it. Worth a look before the next multi-arm task.

## 11. FINAL BAR — this review's own tree

Run from `/tmp/t446/finalbar`, scratch, outside the repo, on the committed tip of
`softhouse/T446-review-t445`, with `bash` (never `sh`/`zsh`). The probe line's **PRESENCE** is read
before its value (P-84 — an ABSENT probe line is the guard working, not `down`).

<!--BARRESULT-->

