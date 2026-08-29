# T477 — REPAIR PASS ON T466 UNDER T473's THREE MAJORs

Branch `softhouse/T477-t473-repair`, cut from **T466's tip `11afb281`, not from `main`**, because
T466 is deliberately unmerged: it closed three forgery routes and opened a fourth, and this branch
is what gets merged in its place. It carries T466's work plus the repair.

Scope held: `.softhouse/conformance.sh`, `.softhouse/capture/t477-t473-repair/`, this handoff.
`tasks.json`, `LOCK`, `RESUME.md`, `program.json`, `patterns.md`, `fire-program.sh`, every `.pin`
and every file under `.softhouse/guards/` are untouched, and T473's review was not edited.

Every number below was measured by an instrument in
`.softhouse/capture/t477-t473-repair/instruments/` and its transcript is in `../evidence/`.
Nothing is inherited from T466 or T473: where I confirm them I say what I ran.

---

## 0. THE HEADLINE

| T473 finding | verdict after re-derivation | what T477 did |
|---|---|---|
| **M-2** PATH-resolved `python3` in the trust base | **CONFIRMED, and worse than T473 could show** — T473's arm was confounded by a global shim; a TARGETED shim reaches **EXIT 0, probe `up`, PASS 46 / 7884** over a forgery only the recompute can see | absolute interpreter + `-I -S` + a **CHALLENGE** whose answer is not in the recompute's input |
| **M-1** the read-census table was measured on the pre-fix harness | **CONFIRMED to the integer** — 35/69/114/309 is blob `7c543532…`, the shipped blob `d1c45afc…` is **40/74/119/331** | table re-measured and anchored to **blob ids**; S1 for the running bytes **derived and printed every run** |
| **M-3** an honest committed filter is named a `SUPPRESSION` | **CONFIRMED** — and the carve-out is the wrong repair | **KEEP THE REFUSAL, CORRECT THE TEXT**, in three places, with the reason |
| m-1 `core.attributesFile` census hole | confirmed | all **four** attribute sources counted and printed |
| m-2 NUL input / newline output | confirmed | output NUL-framed, written as raw bytes, read with `read -r -d ''` **from a file** |
| m-3 a gitlink refuses the whole bar | confirmed, and **correct** | kept; declared and explained at the refusal (push-gate C1) |
| m-4 sparse checkout / unmerged not named | confirmed | both named in the index-bit refusal |

**I did not refute T473 on any point.** Two reviewer patches have been refuted in this program and
that outcome was available; I looked for it and it is not here. Where I go beyond T473 I say so:
the targeted shim (§2), the `sitecustomize` hijack of the **absolute** interpreter (§2), and the
hashing shim that still wins (§2.5).

---

## 1. M-1 — THE READ CENSUS, RE-MEASURED ON THE SHIPPED BYTES

`instruments/readcensus.sh` + `instruments/foldimages.py`, transcript
`evidence/30-read-census.txt`. The corpus is taken as a **BLOB ID** and extracted with
`git cat-file blob`, so the header names the object it measured; the fold images are **derived
from their thirteen codepoints**, never typed, and the derivation calibrates on U+017F → `s`
before it prints anything (11 distinct images from 13 members).

The numbers are produced by **T466's own `read-census.py`, unmodified**, because T473 reproduced
its S1/S2/S3 to the integer from an independently written instrument — the question here is the
CORPUS, not the selector.

| | `7c543532…` (T454 tip, what was measured) | `d1c45afc…` (T466 tip, what the words pointed at) |
|---|---|---|
| lines / non-comment | 6327 / 2310 | 6784 / 2555 |
| locals from the root variable | 36 | **40** |
| S0 touch | 35 (28 foldable) | **40 (33)** |
| S1 direct | 69 (59) | **74 (64)** |
| S2 +anchor | 114 (104) | **119 (109)** |
| S3 +vars | 309 (277) | **331 (298)** |

**T473's M-1 reproduces exactly, every row.** The load-bearing conclusion survives and is
strengthened: 40 > 35 > 27, monotone in the selector.

### HOW I STOPPED IT ROTTING AGAIN — two changes, not one

1. **The table is anchored to blob ids.** A path names whatever is there today; a blob id names an
   immutable object. The shipped table now says "these are the figures for blob `7c543532…` and
   blob `d1c45afc…`" and claims **nothing** about the bytes a reader is looking at. That statement
   is true forever, including after this commit, which made the file a third object.
2. **The number about *this* file is no longer typed at all.**
   `guard_harness_text_is_committed` now **derives S1 every run**, from the bytes actually
   executing, and prints it beside their object id:

   ```
   conformance:   READ CENSUS (S1), DERIVED THIS RUN, NEVER TRANSCRIBED: 81
   conformance:   non-comment line(s) of the bytes now on disk at .softhouse/conformance.sh spell
   conformance:   the root variable. That object is <id>. The four-selector table in this
   conformance:   guard's comment is anchored to two OTHER blob ids and is not about it.
   ```

   It read **74** on T466's tip and reads **81** on mine — i.e. it already moved once, in the
   commit that installed it, which is exactly the event that rotted the last two restated
   cardinals. This is the same remedy T466 applied to the last hand-typed cardinal it removed
   (`yet three of them are invoked verbatim` → the derived `invoked=`).

   **The cheap shell derivation was validated against `read-census.py` on three blobs, not one**
   (`evidence/20-read-census.txt`): `d1c45afc…` → both say **74**; `eeae56b7…`, this branch's
   own harness → `read-census.py` says **81** and the guard printed **81** on the same object.
   A derivation that agreed on one corpus and not another would be a coincidence; two corpora
   apart and one of them mine is a check.

I also took T473's **L-6** while I was in the paragraph: the parenthesised column is measured over
the WHOLE LINE with `s` among the images, so it is approximately "the line contains the letter
`s`". It is relabelled to what it measures rather than dropped, and the weak claim it actually
supports is stated.

---

## 2. M-2 — THE INTERPRETER. RED, GREEN, AND THE ANSWER TO THE HARDER QUESTION

### 2.0 The fixture, and why it is a SMUDGE rather than a forged harness

Every forgery arm uses one shape: a `filter=` attribute in the clone's private
`.git/info/attributes` with an **inverting clean half**, applied to ONE tracked file, materialised
with `git checkout --` so git's stat cache agrees. Measured in every arm:

```
victim                     : .softhouse/capture/t238-failopen/evidence/class-runs/a2-11-enumerate.txt
committed blob             : c900ce84…
hash-object --no-filters   : 09fc75e9…      <- the forged bytes
hash-object (no flag)      : c900ce84…      <- the honest id, over forged bytes
git status --porcelain     : 0 lines
git diff-index --name-only : 0 lines
ls-files -v not H          : 0
```

That shape is chosen deliberately: **its only detector in the shipped harness is the whole-tree
recompute.** There is no index bit for the bits census to find, and the forged file is not the
harness, so the harness's own two ids cannot see it either. An arm that neutralises the recompute
is therefore an arm that CERTIFIES this forgery — which is the thing under test, rather than a
proxy for it.

**Control, `evidence/10-RED-CTLSMUDGE.txt` — T466's tip, honest interpreter:** EXIT **2**, probe
presence **0**, `VERDICT` lines 0, and

```
guard_harness_text_is_committed: THE BYTES ON DISK AT …/a2-11-enumerate.txt ARE NOT THE
COMMITTED BYTES, AND GIT DID NOT REPORT IT.
```

T466's closure of SMUDGE is real, and this is the baseline the RED arms have to beat.

### 2.1 RED — the echo shim wins on T466's tip

`evidence/11-RED-ECHO.txt`, `instruments/shim-echo.sh`. The shim is **targeted**: it answers only
`-c` invocations — which is how, and only how, the recompute is called — and `exec`s the real
interpreter for everything else, so `guard_dead_path_frontier` and the rest are undisturbed and
the arm measures one thing. **This is the confound T473 records and could not remove.** It prints
two lines and hashes nothing:

```
CALIB <git rev-parse HEAD:harness> <git hash-object --no-filters -- harness>
SCANNED <the number of NULs it was handed>
```

Result on `11afb281`:

```
EXIT = 0
probe line PRESENCE = 1        probe value = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
shim fired: 1 time(s)   records=10368 committed=d1c45afc… ondisk=d1c45afc…
guard_harness_text_is_committed REFUSAL lines: 0
conformance:   RECOMPUTE: 10368 HEAD entries re-hashed from their bytes on disk;   <- a lie
```

**Not one byte was hashed and the bar reached a full PASS over a forged tree.** T473 established
that the guard printed a fabricated clean census; this establishes the consequence T473's
confound prevented — the verdict itself.

### 2.2 RED — AND AN ABSOLUTE PATH DOES NOT FIX IT. THIS IS THE ANSWER TO THE HARDER QUESTION.

**No, an absolute path is not sufficient, and that was driven rather than reasoned.**

`site` is imported during interpreter start-up and imports `sitecustomize` from `sys.path`, and
`PYTHONPATH` is on `sys.path`. So a directory on `PYTHONPATH` runs attacker code **inside
`/usr/bin/python3`, before the `-c` program**, with no shim on `PATH` and no write access to any
system directory. Measured directly (`evidence/01-interpreter-flags.txt`):

```
flags=[     ] -> HIJACKED-BY-SITECUSTOMIZE|program ran|
flags=[-E   ] -> program ran|
flags=[-S   ] -> program ran|
flags=[-I   ] -> program ran|
flags=[-I -S] -> program ran|
```

and then driven on the real harness — T466's tip with the invocation rewritten to
`/usr/bin/python3 -c` and **nothing else changed** (`evidence/12-RED-SITE-abs.txt`):

```
the line now reads: ( cd "$REPO_ROOT" && /usr/bin/python3 -c "$recpy" … )
EXIT = 0        probe PRESENCE = 1   probe = up
VERDICT: PASS (exit 0) — 46 parity vectors … 7884 cells compared.
sitecustomize fired inside /usr/bin/python3: d1c45afc… d37cca56…
guard_harness_text_is_committed REFUSAL lines: 0
```

**An absolute interpreter path, on its own, certified the same forgery.** T473's remedy is
necessary and it is not sufficient, and saying only the first half would have been the same
mistake T466 made about its own table.

### 2.3 THE FIX — three layers, and each was driven on its own

1. **`/usr/bin/python3` with the `[ ! -x ]` pre-check**, which is this file's own convention at
   `guard_pnumber_citations` and `guard_reconciler_ownership` (I re-derived both: they do exactly
   what T473 says). The path is a **local**, `recpython`, assigned once and used twice — not a
   parameter and not an env lookup, because an interpreter this guard can be *told* to use is the
   defect it is closing; the local also lets an arm point THIS guard's interpreter somewhere else
   without disturbing the other two, which would otherwise refuse first and mask the finding.
2. **`-I -S`.** `-I` is isolated mode (implies `-E`, so `PYTHONPATH`/`PYTHONHOME` are ignored, and
   `-s`, so the user site directory is), and `-S` suppresses `site` altogether, which is the only
   thing that also closes a `sitecustomize` reachable from an installed `site-packages`.
3. **THE CHALLENGE — calibrating on a value the caller does not hand it.** P-72 as T466 applied it
   uses a known positive the instrument is HANDED: this file's two object ids, **both cheaply
   derivable by the interpreter being calibrated**. That calibration is passed by an echo. So one
   tracked path is chosen **per run, pseudorandomly**, and a duplicate record for it is appended to
   the listing carrying a **decoy object id drawn fresh from `/dev/urandom`**. An honest hasher must
   answer `DIFFERS <the real id of the bytes on disk> <decoy> <path>`, and **the real id is nowhere
   in the listing**; this guard knows what the answer must be because it took it with
   `git hash-object --no-filters` — a **different program** — before handing the challenge over.
   The challenge record is indistinguishable from the ten thousand real ones, so it must be
   ANSWERED, not skipped. The challenge path is still adjudicated normally: only the row whose
   HEAD-side id is the decoy is consumed, so a genuine difference at the same path arrives as its
   own row and is refused or printed like any other. The challenge adds coverage and removes none.

### 2.4 GREEN — the shim is refused

Ten arms, all on commit **`abfe785c`**, harness blob **`eeae56b7…`**, `evidence/4*.txt`. (Two
later commits touch the harness — `c5832efa` adds five `warn` lines naming the challenge's one
honest failure mode, `f48af591` adds two comment lines. Neither changes a predicate; the final bar
in §8 is taken at the tip.)

| arm | EXIT | probe presence | probe | VERDICT | shim fired | what the guard said |
|---|---|---|---|---|---|---|
| **CTL** clean clone | 0 | 1 | up | PASS 46 / 7884 | 0 | census clean, `RECOMPUTE: 10377 HEAD entries` |
| **WDIRTY** honest uncommitted edit | 0 | 1 | up | PASS 46 / 7884 | 0 | `HARNESS-TEXT: uncommitted edit … (on disk 8346b8de…)`, then `git agrees` |
| **SKIPWT** | **2** | **0** | — | none | 0 | **3 refusals**: index bit + suppression + the two ids |
| **ASSUME** | **2** | **0** | — | none | 0 | **3 refusals**, same three |
| **CTLSMUDGE** | **2** | **0** | — | none | 0 | SUPPRESSED at the victim |
| **NOPY** interpreter unreachable | **2** | **0** | — | none | 0 | `/usr/bin/python3 is absent`, by name |
| **ECHO** shim first on `PATH` | **2** | **0** | — | none | **0 — NEVER REACHED** | SUPPRESSED at the victim |
| **SITE** `PYTHONPATH` hijack | **2** | **0** | — | none | **0 — NEVER REACHED** | SUPPRESSED at the victim |
| **CHALLENGE-ONLY** (`recpython` reverted to a bare `python3`) + echo shim | **2** | **0** | — | none | **1 — REACHED, records=10378** | `THE RECOMPUTE FAILED ITS CHALLENGE.` |
| **HASHER** (bound, §2.5) | **0** | 1 | up | PASS 46 / 7884 | **1 — REACHED, hid the victim** | nothing — **the declared bound** |

The last row is the one that matters most, because it isolates the third layer: with the absolute
path and the flags **removed**, the shim IS reached (`records=10375`, i.e. 10374 entries plus the
challenge) and the guard refuses anyway. **The challenge closes the route on its own; the absolute
path and the flags close it before the shim is ever consulted. Both were driven separately.**

### 2.5 AND THE SHIM THAT STILL WINS — the declared bound, driven rather than asserted

`instruments/shim-hasher.sh`, `evidence/49-BOUND-HASHER.txt`. Reimplementing the recompute is
cheap: `git hash-object --no-filters --stdin-paths` does the whole job in one process. That shim
answers the calibration, answers the challenge, and simply omits the `DIFFERS` row for the victim.
With the absolute path removed so it can be reached, it reaches **EXIT 0, probe `up`, PASS 46 /
7884** over the same forgery.

**So the bound is exactly this: T477 removes the PATH route and the environment route, and makes an
O(1) ECHO fail. It does not remove the interpreter from the trust base.** Nothing computable from
this repository can, because the challenge lives in the same repository — a substituted interpreter
can always shell out to git. What it buys is that a substituted interpreter must now REIMPLEMENT
the recompute correctly in order to lie about one line of it. That is class (1) — LONGNOP — and
the answer to class (1) is still a verifier outside this file.

---

## 3. M-3 — DECISION: **KEEP THE REFUSAL, CORRECT THE TEXT**

T473 is right that an honest, committed, git-lfs-shaped clean filter is called a `SUPPRESSION` and
refused, and right that the shipped words said the opposite. The dispatch offered two defensible
repairs. I chose the second, and the reason is not taste:

**A carve-out for a "committed, honest" filter is forgeable by committing a file.** Keying the
exemption on "the attribute is declared in a committed `.gitattributes`" hands an attacker a route
**strictly cheaper than the three T466 just closed**: commit a `.gitattributes` and a
`filter.*.clean` half, and every `SUPPRESSED` refusal in the tree is disarmed by a two-line diff
nobody reads. The recompute's premise — RAW BYTES ARE THE TRUTH — is **not generally true of git**,
whose blob is *defined* as the post-clean bytes; it is the right premise against an adversary
precisely because it disagrees with that definition, and a filter that is honest is a filter that
makes the blob differ from the file, which is the same observable.

The cost is a legitimate LFS or `text=auto` adoption. This program has not made one — **zero
tracked `.gitattributes`, no `core.attributesFile`, no `core.autocrlf`, no filter driver** — the
behaviour is fail-**closed**, and adopting one would be a task rather than a surprise, because the
refusal now names it and says so in terms.

Corrected in **three** places, so the text and the behaviour agree wherever a reader lands:

- the block comment's asymmetry paragraph, which quotes the old sentence in place rather than
  deleting it, and states the true rule in capitals;
- the run-time LOCAL-STATE census, which used to imply filters pass;
- the `SUPPRESSED` refusal itself:

```
IF YOU JUST ADOPTED git-lfs OR 'text=auto', THIS IS YOU, AND IT IS NOT A FALSE POSITIVE
[T473 M-3, driven]. … There is no way to declare a legitimate filter here and the carve-out
was refused deliberately: it would be forgeable by committing a .gitattributes. Teach this
guard first; do not disable it.
```

**Drive:** the `CTLSMUDGE` arm is that behaviour — a filter, `git status` empty, `SUPPRESSED`,
EXIT 2 — and it is now what the file says will happen. I did not build a second LFS fixture: the
mechanism is identical (a non-identity clean half) and T473 already drove the honest-shaped one;
building a second copy of a confirmed finding would be effort spent on agreement.

---

## 4. THE MINORS

- **m-1 — closed.** The census counts and prints **four** attribute sources:
  `.git/info/attributes`, the **common** git-dir's copy (this repository is a linked worktree, so
  those are two different files), **`core.attributesFile`** with its path, the XDG file, and the
  number of **tracked `.gitattributes`**. On this tree: `ATTRIBUTE SOURCES 0`.
- **m-2 — closed.** The hasher's rows are `\0`-terminated and written as **raw bytes** (no decode,
  so a path that is not valid UTF-8 cannot raise inside the hasher either), and the shell reads
  them with `read -r -d ''` **from a file** — a command substitution would have spliced the whole
  stream into one row, which is the failure T466 records hitting on its first graded run. **stderr
  is kept separate and any byte on it is a refusal**, because merged into a NUL stream a trailing
  diagnostic is silently DROPPED by `read -d ''` and a leading one is spliced onto a real row.
  Verified by `instruments/hashdiff.sh`: the newline-named path is now **compared, not omitted**.
- **m-3 — judged correct, kept, and declared.** A gitlink refuses the whole bar, and that agrees
  with the rest of the program rather than being an oversight: push-gate condition **C1** forbids a
  gitlink on `refs/heads/main`, and T450 drove one on with `--no-verify`, which is why the post-hoc
  reconciliation exists. A submodule's working tree is not covered by this commit, so "the bytes on
  disk are the committed bytes" has no meaning there and reporting a MATCH would be the fail-open
  answer. The refusal now says all of that, and names what has to be taught if the pinned Fineract
  checkout is ever vendored as a submodule.
- **m-4 — closed.** The index-bit refusal now names **sparse checkout** (`S` outside the cone) and
  **an unmerged entry** (`M`), says the `--no-skip-worktree` command will not help either of them,
  and says what will.
- **L-1, L-2, L-3, L-5, L-6 — taken.** The budget paragraph no longer restates the entry count or
  the timings (both are printed by the guard on every run) and records that **neither cold figure
  is a pinned fact** (T466: 21 s; T473: 51.3 s; the rule gives 210 and 510 and the shipped 300 sits
  between them). "One line above" is corrected to "on the line below". "SMUDGE fires two of the
  three, not three" is stated in the block. The FOLDABLE column is relabelled.

---

## 5. REGRESSION — T473's CONFIRMED LIST, RE-CHECKED

| what T473 confirmed | still true? | how I checked |
|---|---|---|
| SKIPWT / ASSUME / SMUDGE genuinely closed | **YES** | arms `SKIPWT`, `ASSUME`, `CTLSMUDGE` at this tip: EXIT 2, probe presence 0 |
| the hasher is byte-correct | **YES, RE-TAKEN** | I rewrote it, so T473's verification does not carry over. `instruments/hashdiff.sh` extracts the program **verbatim from the harness on disk** and compares with `git hash-object --no-filters` over a nasty corpus — **19 entries compared, 0 MISMATCHES, 0 OMITTED** (T473's parser omitted one; NUL framing does not), and **14 of 14 perturbations detected, symlinks untouched** |
| it fails closed without `python3` | **YES** | arm `NOPY`: EXIT 2, probe presence 0, the `[ ! -x ]` refusal by name |
| the honest-dirty boundary is intact | **YES** | arm `WDIRTY`: EXIT 0, probe 1 `up`, PASS 46 / 7884, the edit NAMED and PRINTED |
| the fold census (1401/1091/310, 13 members, U+FB01 → `fi` → `fire-program.sh`) | **not re-driven, and nothing touched it** | T459, T466 and T473 all reproduce it; T477 changed no line of it. The 13 codepoints are used as INPUT to `foldimages.py`, which calibrates on U+017F → `s` before printing |
| 1799 citations / 20 moved / none load-bearing | **YES, IDENTICAL** | `instruments/citations.sh` over the merge base: **1799 total, 20 moved, 0 past the end**, the same 10-file breakdown. My insertions add **zero** moved citations; `patterns.md`, `fire-program.sh`, every `.pin` and every guard are untouched. `tasks.json` still carries its 3, all at one line, all prose — not edited by me |
| `FAILOPEN_PIN_FILE_LIST` byte-identical, frontier 11 | **YES** | every graded run: `frontier 11, pinned at 11`, `frontier == pinned (all 11 rows, by path)`; and `literal /tmp … : 18, pinned at 18` |

**The two censuses that caught T466 and T473 did not catch me,** and that is worth one sentence
rather than a paragraph: my instruments were written to the shape those guards prescribe from
the first draft — every `cd` fatal, every listing preceded by its MATCH COUNT, and the scratch root
`SCR="${T477_WORK:-}"` falling back to `mktemp -d "${TMPDIR:-/tmp}/…"` rather than a literal. **No
pin was moved and none needed to be.**

---

## 6. RESIDUE — VERIFIED AGAINST THIS REPOSITORY, NOT ASSERTED

Every index bit, filter driver, attributes file and `PATH` shim used by this task lived in a
throwaway clone under `/tmp/t477-work.*`; `arm.sh` **refuses to run** if the scratch root is inside
the repository under test. `instruments/residue-check.sh` is deliberately wider than the four
classes the dispatch named, for the reason m-1 gives. `evidence/80-residue-check.txt`:

```
--- 1. INDEX BITS   entries not in state H: 0
--- 2. ATTRIBUTE SOURCES, ALL FOUR
    ABSENT : <worktree git-dir>/info/attributes
    ABSENT : /Users/buv/gerege-nbfi/.git/info/attributes        <- the COMMON git-dir, a second file
    core.attributesFile   : []  (empty = unset)
    ABSENT : /Users/buv/.config/git/attributes
    TRACKED .gitattributes files: 0
--- 3. CONTENT FILTERS, AT EVERY CONFIG LEVEL
    local 0   global 0   system 0   ALL levels 0     core.autocrlf : []
--- 4. WORKING TREE   porcelain lines: 0
--- 5. tracked paths carrying the forged-marker token: 0 ; named for the scratch root: 0
--- 6. LOCK in HEAD = LOCK on disk = bc5f4a33bb9c3ac1504ae344cbf2466c739d9985
       tasks.json / RESUME.md / program.json / patterns.md changed vs merge-base: 0 / 0 / 0 / 0
```

The `porcelain lines: 0` figure is the run taken **after** the final commit; the run recorded
above it during the task showed `2`, and both were my own untracked evidence and handoff.

---

## 7. WHAT REMAINS OPEN — DECLARED, NOT ARGUED SHUT

This list is now **in the harness itself**, in the guard's header comment, so that a reader does not
have to find a handoff to learn what the guard does not do.

1. **LONGNOP / LONGSTRIP.** A guard inside the text under attack cannot survive an attacker who
   edits that text. Unchanged, and nothing in this file can change it. [FU-T454-1 / T460.]
2. **THE INTERPRETER IS STILL IN THE TRUST BASE.** §2.5, driven. A shim that reimplements the
   hasher wins. So does an interpreter replaced at `/usr/bin/python3` itself — though an attacker
   who can write there can write this file, which is (1).
3. **Every non-identity content filter and eol conversion is refused, honest or not.** §3. Chosen,
   latent on this tree, fail-closed.
4. **A gitlink refuses the whole bar.** §4. Chosen, and it agrees with push-gate C1.
5. **The index-bit refusal is absolute**, so a sparse checkout and a conflicted merge cannot run
   the bar. Judged right by three authors; the refusal now says so.
6. **PHANTOM is printed, not refused.** Unchanged from T466; T473 agreed with the call.
7. **The whole class: what is forged is a TRANSCRIPT, never the COMMIT.** Index bits, filters,
   attributes files and interpreter substitutions are all local and uncommitted. A reader who
   fetches the commit and hashes it themselves — **with `--no-filters`** — was never fooled by any
   of them, and is still the only reader who cannot be.
8. **U+037E → `;` and U+1FEF → `` ` `` have no tracked target today.** Not closed.
9. **The challenge has an honest failure mode**, named at the refusal: a tracked file rewritten
   *during* the run, between this guard hashing the challenge path and the recompute reading it.
   The window is seconds, the path is chosen afresh each run, and a second refusal at a different
   path is a finding rather than a race.
10. **`patterns.md:3271` and `fire-program.sh:3217` are rotted on `main` today, by T458, not by
    T466 or T477.** Out of scope here; T473 asks the driver to file it and I have not.
11. **I did not re-drive a U+FB01 collision at `.softhouse/bin/fire-program.sh`**, and I did not
    re-drive LONGNOP as a checkout collision. Both are T466/T473's declared-open items and T477
    changed nothing that bears on either.

---

## 8. FINAL BAR ON THE COMMITTED TREE

`instruments/finalbar.sh` — `bash`, not `sh`/`zsh`; the repository entered ONCE, fatally; the
root derived from the script's own location and the harness path assembled from fragments; every
grep printing its MATCH COUNT so an empty list is a number. **The probe line's PRESENCE is counted
before its value is read.** Transcript: `evidence/90-FINAL-BAR.txt`.

The commit that adds this section touches only this handoff and the evidence files — **not
`.softhouse/conformance.sh` and not any instrument** — so the harness graded below is
byte-identical on the branch tip. Recompute it yourself:
`git rev-parse HEAD:.softhouse/conformance.sh`, and the right-hand id with
`git hash-object --no-filters -- .softhouse/conformance.sh`, **with the flag** — the unflagged form
is the one SMUDGE defeats.

Run on commit `09ac6219`, harness blob `1ced9310c33d561b776e73aafa90e2fbe920f5b7` — identical
under `git rev-parse HEAD:`, `git hash-object --no-filters` and unflagged `git hash-object`.
Full 898-line transcript in `evidence/91-FINAL-BAR-full-transcript.log`.

```
=== 0. THE TREE BEING GRADED ===================================================
HEAD                                   = 09ac62196f8667e1b8034bc80fa8dd6e7b60b78b
git status --porcelain lines           = 0
git rev-parse HEAD:<harness>           = 1ced9310c33d561b776e73aafa90e2fbe920f5b7
git hash-object --no-filters <harness> = 1ced9310c33d561b776e73aafa90e2fbe920f5b7
git hash-object (no flag)   <harness>  = 1ced9310c33d561b776e73aafa90e2fbe920f5b7
ls-files -v, entries NOT in state H    = 0

=== 1. THE RUN =================================================================
command: bash <harness>   (bash, not sh, not zsh)
EXIT = 0

=== 2. PROBE PRESENCE BEFORE PROBE VALUE =======================================
grep -c 'probe = '  -> 1      <-- PRESENCE, read first
probe value         -> up

=== 3. VERDICT =================================================================
VERDICT lines: 1
    VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.

=== 4. THIS GUARD'S OWN OUTPUT =================================================
    conformance:   LOCAL-STATE CENSUS (uncommitted, in no diff, and it decides what git …
    conformance:   HARNESS-TEXT CENSUS: HEAD 09ac6219…
    conformance:   RECOMPUTE: 10398 HEAD entries re-hashed from their bytes on disk;
    conformance:   CHALLENGE: the recompute was handed a planted record for
                   .softhouse/reviews/T135-evidence/f1-attack.sh
    conformance:   READ CENSUS (S1), DERIVED THIS RUN, NEVER TRANSCRIBED: 81
    conformance:   this harness .softhouse/conformance.sh: committed 1ced9310… / on disk 1ced9310…

=== 5. GUARD COST ==============================================================
    conformance:   GUARD-COST CENSUS: 16 guards timed, 74s total wall,
    conformance:     COST 5s / ceiling 300s   guard_harness_text_is_committed
    conformance:   guard-cost: PASS — every guard timed, every ceiling row used, none breached.

=== 6. THE PINS ================================================================
    frontier 11, pinned at 11      frontier == pinned (all 11 rows, by path).
    literal /tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 18
    dead-path frontier: GREEN, and the T323 reconciliation list is empty.

=== 7. EVERY GUARD REFUSAL, COUNT FIRST ========================================
refusal lines matched: 0
```

Two things in that transcript are the M-1 and M-2 repairs answering for themselves rather than
being described: **`READ CENSUS (S1) … 81`** is the cardinal that used to be typed into a comment,
now measured from the bytes that ran; and **`CHALLENGE: … a planted record for
.softhouse/reviews/T135-evidence/f1-attack.sh`** is a different path from the one the previous run
chose, because it is drawn afresh every run.

---

## 9. INSTRUMENT DEFECTS I FOUND IN MY OWN WORK — recorded, not tidied away

Two, both repaired at the instrument:

1. `hashdiff.sh`'s perturbation leg read `git ls-files` **newline-delimited**, so the four
   C-quoted names — the newline one, the glob one, the U+017F one, the `ümläut` one — failed `-f`
   and were silently skipped: **10 perturbed of 14**, and the leg still reported PASS because it
   compared its own two numbers. That is the same shape as the defect T473 found in its own
   parser and the same shape the guard under test exists to refuse. Repaired to
   `git -c core.quotepath=false ls-files -z` + `read -r -d ''`: **14 of 14 perturbed, 14 detected.**
2. `arm.sh` reported the mutation with `grep -c "$RECPAT"` where `$RECPAT` begins with `-`, so
   `grep` read it as an option and printed a usage error into the transcript instead of a count.
   Repaired to `grep -c -e "$RECPAT"`. It affected no measured value — the mutation is shown by
   the printed line and by the arm's own outcome — but a count that cannot be taken must not be
   printed as if it were.

