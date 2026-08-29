# T479 — INDEPENDENT ADVERSARIAL REVIEW OF T477

**Subject:** branch `softhouse/T477-t473-repair`, tip `a6bf50a36296c097d96a805b63032d94801b0b9e`,
carrying T466's work plus T477's repair. **Harness under review:** `.softhouse/conformance.sh`,
blob `1ced9310c33d561b776e73aafa90e2fbe920f5b7` — identical under `git rev-parse HEAD:`,
`git hash-object --no-filters` and unflagged `git hash-object`, verified in a throwaway clone.
**Merge base with `main`:** `3f4e236ad458dd945bac26243a90ccc950924164`, harness `7c543532…`.
**`main` today:** `b810df3cabb0af75aca33c289e9cfa5a0811ea6b`, harness `db313f98…`.
**Reviewer tree:** `softhouse/T479-review-t477`, cut from `main`; T477 is **not** merged into it.

---

## VERDICT: **APPROVED WITH CONDITIONS**

### AND YES — THERE IS A FIFTH ROUTE, AND IT IS THE ONE T477 ADDED.

**T477's CHALLENGE — the novel mechanism, the third of its three layers, and the only one that
was supposed to survive a substituted interpreter — does not work.** I drove a shim that
**imports no `hashlib`, opens no tracked file and hashes zero bytes** and it answers the
challenge correctly, reaching **EXIT 0, probe presence 1 then `up`, `VERDICT: PASS … 46 …
7884`, 0 refusals** over the same SMUDGE forgery T477 built the layer to catch. The reason is
one line of the construction: **the challenge plants a *duplicate* record for a *tracked* path,
so the genuine record for that path — carrying the true HEAD id, which for an unmodified file
*is* the id of the bytes on disk — is still sitting in the listing.** The answer is a lookup,
not a hash.

And the harness says otherwise, in capitals, at run time, in the transcript that certified my
forgery:

```
conformance:   CHALLENGE: the recompute was handed a planted record for
conformance:   .softhouse/reviews/t382-review-t374/out/census-mine.txt
conformance:   carrying the decoy id c470650bcb5e04efc1bb9a20a2ed9dc4d473cbfc, and answered
conformance:   144f593a018571d613877164896e442bc016caa8, which is the id this guard took with
conformance:   git hash-object --no-filters BEFORE handing it over.
conformance:   The correct answer was NOT in the recompute's input, so an interpreter that
conformance:   echoes the ids it was given cannot produce it [T473 M-2].
```

The interpreter that produced that line **did exactly what the line says it cannot do.** This is
the same defect class the guard exists to prosecute — the file saying something false about
itself — shipped inside the correction, for the **third consecutive time** in this thread
(T454's `27`, T466's read-census table, and now T477's challenge). That is why the condition is
MAJOR and why it is stated as loudly as T473 stated the fourth route.

**It does not block the merge.** The stack is still a large net improvement over `main`, the
defect is in a *newly added* defence that fails **open only where `main` already fails open**,
and it costs nothing and refuses nothing honest. **The stack is safe to merge**, and the
condition must be recorded and repaired — I drove a repair, so it is nine lines of work.

| # | severity | one line |
|---|---|---|
| **M-1** | **MAJOR** | **THE CHALLENGE IS ANSWERABLE BY LOOKUP.** The decoy record duplicates a tracked path whose genuine record is still in the listing; a shim that hashes nothing answers it and reaches EXIT 0 / PASS over a forgery. Driven twice, position-dependent and position-independent. The harness asserts the opposite at run time and in its declared-OPEN list. Repair driven. |
| m-1 | MINOR | The interpreter fix is **local to one guard** and the block comment and §7 do not say so. **Three PATH-resolved `python3` call sites remain**, one of them the T238 fail-open linter that grades the frontier; I drove the `sitecustomize` hijack **firing 62 times** in them on the shipped tip. |
| m-2 | MINOR | "The challenge record is indistinguishable from the ten thousand real ones" is false on **two** independent counts — it is always **last**, and its **path is duplicated**. Both tells driven; either alone suffices. |
| L-1 | LOW | The challenge path is drawn from the **index** while the listing handed over is the **HEAD tree**. Harmless here (10400 = 10400) and fail-safe elsewhere, but unstated — and it is exactly the asymmetry that decides whether the honest answer is in the input. |
| L-2 | LOW | A tracked path containing a newline or a quote is C-quoted by `ls-files` even under `core.quotepath=false`, so it can never be chosen as the challenge path (the `[ -f ]` test rejects it). Fail-safe and undocumented. |
| L-3 | LOW | The shipped `RECOMPUTE:` census line reads "N HEAD entries re-hashed from their bytes on disk" — a claim about *work performed*, printed unconditionally from a number the recompute reports about itself. It is the sentence my shim falsified. |

**Everything else T477 claims, I re-derived and it holds** — M-1's corrected table to the
integer on the shipped blob, M-3's decision and its reasoning, all four minors, the rewritten
hasher, the honest-dirty boundary, the citation sweep, both pins, and the scope.

---

## 1. WHAT I RE-DERIVED, AND HOW

Nothing below is inherited from T477, T473 or T466. Every arm ran in a **throwaway clone under
`/tmp/t479-work`, outside the repository**; the residue check in §10 is taken in my own worktree
and is clean of all four classes. **Nine full bar runs** were taken. In every one the probe
line's **PRESENCE** was counted with `grep -c 'probe = '` **before** its value was read.
Transcripts are in `evidence/`.

**My forgery fixture is my own bytes in T477's shape**, and it is deliberately the hardest one:
a clean filter whose half is *not* the identity, attached in the clone's **private
`.git/info/attributes`**, applied to **one tracked file that is not the harness**, materialised
with `git checkout --` so git's stat cache agrees.

```
victim                     : .softhouse/reviews/t459-review-t454/evidence/00-fold-probes.txt
committed blob             : 7ecb3e05261f765dcda4a4485aea59377612acd4
hash-object --no-filters   : 80fb668b4a466e134de015915b0a15a8aa6e6db9   <- the forged bytes
hash-object (no flag)      : 7ecb3e05261f765dcda4a4485aea59377612acd4   <- the honest id, over forged bytes
git status --porcelain     : 0 lines
git diff-index --name-only : 0 lines
ls-files -v not H          : 0
```

**Its only detector in the shipped harness is the whole-tree recompute.** No index bit exists
for the bits census, and the forged file is not the harness, so the two-ids comparison cannot
see it either. An arm that neutralises the recompute is an arm that **certifies** this forgery.

**CONTROL, `evidence/00`** — T477's tip, clean throwaway clone, honest everything:

```
grep -c 'probe = '  -> 1        <-- PRESENCE, read first
probe value         -> up
EXIT = 0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
RECOMPUTE: 10400 HEAD entries      READ CENSUS (S1) … 81      COST 4s / ceiling 300s
frontier 11, pinned at 11          literal /tmp … : 18, pinned at 18
GUARD-COST CENSUS: 16 guards timed, 65s total wall, ceiling breaches 0
real 74.73s  user 44.24s  sys 15.74s
```

**RED CONTROL, `evidence/10`** — same tip, the forgery present, honest interpreter: **EXIT 2**,
**probe presence 0**, 0 verdicts, and the guard names the victim. T477's baseline reproduces.

---

## 2. CLAIM 1 — M-2, AND WHETHER THE FOURTH ROUTE IS CLOSED

### 2.1 Layer 1 and layer 2 — VERIFIED, and layer 2 is stronger than T477 claims

**The flag matrix reproduces exactly** (`evidence/21`), measured against a `PYTHONPATH`
`sitecustomize.py` on this host's `/usr/bin/python3` (Python 3.9.6, the Xcode CLT stub):

```
flags=[     ] -> HIJACKED-BY-SITECUSTOMIZE|program ran|
flags=[-E   ] -> program ran|
flags=[-S   ] -> program ran|
flags=[-I   ] -> program ran|
flags=[-I -S] -> program ran|
```

So **T477's refutation of T473's absolute-path remedy is CONFIRMED**: an absolute interpreter
path alone is not sufficient, `sitecustomize` runs attacker code inside `/usr/bin/python3`
before the `-c` program, and `-I -S` is what closes it. I also took four rows T477 did not:

- **`-s` alone is NOT enough** — the user-site flag leaves `PYTHONPATH` on `sys.path`, so the
  hijack still fires. It is `-E` (implied by `-I`) that does the work, not `-s`.
- `PYTHONHOME`, `PYTHONWARNINGS` — ignored under `-I -S`. `PYTHONSTARTUP` is never read
  non-interactively. `PYTHONEXECUTABLE` moves `sys.executable` only, and this hasher never
  re-execs. A `.pth` file and an installed-`site-packages` `sitecustomize` both need `site`,
  which `-S` suppresses.
- **`DYLD_INSERT_LIBRARIES` is stripped by SIP** before the interpreter sees it (`os.environ`
  reports `None` in the child). `LD_PRELOAD` is not a macOS mechanism.
- **The vector that matters most, and T477 does not claim it.** Without flags, `sys.path[0]`
  is the **current directory**, and this guard `cd`s into `REPO_ROOT` before invoking. A file
  named `hashlib.py` at the repository root therefore **shadows the stdlib inside T466's
  recompute** — driven, `CWD-HASHLIB-SHADOW|`. **That route is committable and survives a
  clone**, unlike `PATH` and `PYTHONPATH`, which are local and uncommitted. `-I` removes it.
  So layer 2 closes a route **strictly stronger than the class T477 files it under**. Latent
  today: **829 tracked `.py` files, zero whose basename collides with a stdlib module name.**

**GREEN, `evidence/20`** — the shipped tip, the forgery present, and **both** interposition
routes armed at once (a targeted PATH shim *and* `PYTHONPATH` + `sitecustomize`):

```
EXIT = 2      probe line PRESENCE = 0      VERDICT lines = 0
PATH shim fired                          : 0   <- NEVER REACHED (the path is absolute)
sitecustomize fired inside the recompute : 0   <- NEVER IMPORTED (-I -S)
sitecustomize fired in OTHER python3 calls: 62  <- see m-1
guard_harness_text_is_committed: THE BYTES ON DISK AT …/00-fold-probes.txt ARE NOT THE
                                COMMITTED BYTES, AND GIT DID NOT REPORT IT.
```

**Layers 1 and 2 hold.** On this host, with the shipped bytes, neither interposition route
reaches the recompute at all.

### 2.2 M-1 (MAJOR) — LAYER 3 DOES NOT

The dispatch asked for the hardest scrutiny of the challenge, and it does not survive it.

**The construction, read from the shipped source.** The guard picks a tracked path from
`git ls-files -s`, hashes it with `git hash-object --no-filters`, draws a 40-hex decoy from
`/dev/urandom`, and then:

```
printf '%s blob %s\t%s' "$chalmode" "$chaldecoy" "$chalpath" >>"$headlist"
printf '\000' >>"$headlist"
```

It **appends**. The genuine `git ls-tree` record for that same path is **still in the file**.
So for any path whose disk bytes equal its HEAD bytes — which is *every* path on a clean tree,
and every path but one under an attack — the honest answer `DIFFERS <disk id> <decoy> <path>`
has a left-hand id that is **printed verbatim, in the same input, in the record the challenge
duplicated**. The claim in the comment — *"the real id is nowhere in the listing"* — and the
claim in the transcript — *"The correct answer was NOT in the recompute's input"* — are both
**false**.

**Driven, `evidence/11`.** Isolation is exactly T477's own CHALLENGE-ONLY arm: layer 1 and
layer 2 reverted to a bare PATH-resolved `python3` and **nothing else changed**, the mutation
**committed** in the throwaway clone so the harness's own two ids agree and layer 3 is isolated
alone. The shim is targeted — it answers only `-c` and `exec`s the real interpreter otherwise —
and it **imports no `hashlib` and opens no tracked file**:

```
cmode, cdecoy, cpath = P[-1]                  # the challenge is appended, so it is last
honest = <the sha of the OTHER record with the same path>
emit CALIB  <selfrel's record sha> <the same sha>       # committed == on disk on this tree
emit DIFFERS <honest> <cdecoy> <cpath>
emit SCANNED <len(P)>
```

```
EXIT                                          = 0
probe line PRESENCE                           = 1        probe value = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
shim fired                                    = 1   (and hashed nothing)
guard_harness_text_is_committed refusal lines = 0
conformance:   RECOMPUTE: 10400 HEAD entries re-hashed from their bytes on disk;
conformance:   differing 0 … git did NOT report 0 (SUPPRESSED)
```

**Not one byte was hashed and the bar reached a full PASS over the forged tree, with the
challenge printed as answered.**

**And the positional tell is not load-bearing** (`evidence/12`). A second shim makes no
assumption about where the decoy sits: it finds the **duplicated path**, then tells the decoy
from the honest id by asking `git cat-file -e` which of the two is a real object — the decoy
came from `/dev/urandom` and is not in the object store. Two O(1) processes, still zero bytes
hashed: **EXIT 0, probe 1 `up`, PASS 46 / 7884, 0 refusals.** So "append the decoy at a random
offset" or "shuffle the listing" does **not** close it.

### 2.3 THE TRUE BOUND, AND T477's DECLARED ONE

T477 declares, in §7.2 and in the harness's own OPEN list:

> A substituted interpreter that REIMPLEMENTS the hasher — `git hash-object --no-filters
> --stdin-paths` does the whole job in one process — still answers the challenge and can omit
> one row. … What it buys is that a substituted interpreter must now REIMPLEMENT the recompute
> correctly in order to lie about one line of it.

**That is not the bound.** The measured bound is **zero work**: parse the input, read one field
out of it, print three rows. The gap between "must correctly re-hash 10,400 entries and 241 MiB"
and "must read a field it was handed" is the entire content of the layer. T477's own
CHALLENGE-ONLY arm found the echo shim refused because **that** shim printed only `CALIB` and
`SCANNED` and never looked at its input; five more lines of shim and it wins.

### 2.4 IS THE DECOY DISTINGUISHABLE? (m-2, MINOR)

The comment says the challenge record "is indistinguishable from the ten thousand real ones, so
it must be ANSWERED, not skipped." **It is distinguishable on two independent counts**, both
driven: it is **always the last record**, because it is appended; and its **path occurs twice**,
because it is a duplicate. Its *shape* is right — `<mode> SP blob SP <40 hex> TAB <path>` matches
`ls-tree` exactly, and a `/dev/urandom` decoy is indistinguishable from a real sha as a *value*.
The tell is structural, not lexical, and an attacker reading the committed source (which is
where the mechanism lives, so assume they do) finds it in one minute.

### 2.5 FALSE REFUSALS — NONE OBSERVED, AND THE SAME MEASUREMENT IS THE FINDING

`evidence/70`. 400 trials of the guard's own selection predicate, transliterated from the
shipped shell: **0 selection-loop exhaustions**, **0 disagreements** between
`git hash-object --no-filters` and a raw-bytes `sha1`. Of **10400** index rows the selector
rejects exactly **one** — the harness itself, excluded by name. Across **nine full bar runs**
in this review, `THE RECOMPUTE FAILED ITS CHALLENGE` fired **0 times**. The declared honest
failure mode (a file rewritten mid-run) is real and correctly named at the refusal; I did not
observe it and the bar is **not** flaky.

**And that same census is the finding.** Index rows **10400** and HEAD entries **10400** are the
same number, so **every selectable challenge path is also in the HEAD listing**, so the honest
answer is **always** present in the challenge's own input on a clean tree. The residual value of
the challenge against a lookup shim is **zero, not small**.

The one case where it would bite — the challenge landing on the attacker's own forged path, so
that the disk id genuinely differs from the HEAD id — is **1 in 10400**, and an attacker who
forged that file knows its disk id and special-cases it for free. That is not a defence.

### 2.6 THE REPAIR, DRIVEN — NOT PROPOSED

The dispatch is explicit that a reviewer patch must be driven, and that three have been
overturned in this program. So I drove mine (`evidence/80`). Nine lines: **pose the challenge
over bytes git has never seen.** A throwaway file of `/dev/urandom` under `TMPDIR`, planted
under its **absolute** path, so the answer is absent from the listing, absent from the object
store, and unreachable by `git ls-tree` or `git cat-file`. The only way to produce it is to hash
it. Four arms, on the same smudged clone with layer 1 reverted so the shim is reachable:

| arm | result |
|---|---|
| **R1** repaired + lookup shim A | **EXIT 2**, probe presence **0**, 0 verdicts, `THE RECOMPUTE FAILED ITS CHALLENGE.` |
| **R2** repaired + lookup shim B | **EXIT 2**, probe presence **0**, 0 verdicts, same refusal |
| **R3** repaired + honest interpreter, smudged tree | **EXIT 2**, the SMUDGE still refused at the victim by name — the repair removes no coverage |
| **R4** repaired + clean tree + honest interpreter | guard refusal lines **0**, recompute and challenge both clean, `COST 4s / ceiling 300s`, `leftover challenge files in TMPDIR: 0` |

**R4's verdict line is NOT a pass and is not reported as one** — the reference oracle went down
during that run; see §9.

**What the repair does not buy, said plainly so it is not oversold:** it forces a substituted
interpreter to hash 4 KiB **correctly**. It does not force it to hash the tree, and a shim that
reimplements the hasher still wins. That really is LONGNOP's class and it is genuinely
irreducible from inside this file. The repair's whole content is that the **zero-work** evasion
stops working and the sentence the harness prints becomes **true**. The condition would be
satisfied equally by *correcting the text* and declaring the challenge as what it is — a
speed-bump against the O(1) echo — but the harness has now shipped a false self-description
three times running, and a mechanism that makes the sentence true is cheaper than a fourth
correction.

### 2.7 m-1 (MINOR) — THE FIX IS LOCAL TO ONE GUARD AND THE TEXT DOES NOT SAY SO

`evidence/20` records `sitecustomize fired in OTHER python3 calls: 62`. The harness still
resolves `python3` from `PATH` at **three** call sites, none of them under `-I`/`-S`:

- two inside the shared checker-runner used for the `.softhouse/guards/*` checkers
  (`… python3 "$script" --selftest`, `… python3 "$script" "$REPO_ROOT"`), and
- `( cd "$REPO_ROOT" && FAILOPEN_LINT_JSON="$json" python3 "$lint" )` in
  `guard_no_fail_open_instruments` — **the guard that computes the fail-open frontier the bar
  pins at 11.**

None of this is a regression T477 introduced, and T473 noted the shape. The condition is on the
**words**: the block comment says "`/usr/bin/python3` … closes the PATH route" and OPEN item 2
says "T477 closed the PATH route … and the environment route", with no qualifier. A reader lands
on that and concludes the harness closed them. It closed them **for this one guard**. One clause
fixes it. (For completeness: `guard_pnumber_citations` and `guard_reconciler_ownership` do use
the absolute path, but not `-I`/`-S`, so their `sys.path[0]` is their script's own tracked
directory — latent, since no tracked `.py` basename collides with a stdlib module.)

---

## 3. CLAIM 2 — M-1's ANTI-ROT MECHANISM

### 3.1 The figures reproduce, every row, on the shipped bytes

`evidence/30`. Corpora taken as **blob ids** and extracted with `git cat-file blob`, then
**re-hashed** so the header names the object measured. The 13 fold images are **derived from
their codepoints**, never typed, and the derivation calibrates on **U+017F → `s`** before it
prints anything: **11 distinct images from 13 members** — `ss s ; \` k ff fi fl ffi ffl st`.
The selector is T466's own `read-census.py`, unmodified, because the question is the corpus.

| | `7c543532…` (T454 tip) | `d1c45afc…` (T466 tip) | `eeae56b7…` | `1ced9310…` (T477 tip) |
|---|---|---|---|---|
| lines / non-comment | 6327 / 2310 | 6784 / 2555 | 7162 / 2717 | 7170 / 2723 |
| locals from the root variable | **36** | **40** | 44 | 44 |
| S0 touch | **35 (28)** | **40 (33)** | 47 (40) | 47 (40) |
| S1 direct | **69 (59)** | **74 (64)** | **81** (71) | **81** (71) |
| S2 +anchor | **114 (104)** | **119 (109)** | 126 (116) | 126 (116) |
| S3 +vars | **309 (277)** | **331 (298)** | 353 (320) | 353 (320) |

**T477's corrected table is exact, every row and both columns**, and T473's M-1 reproduces to
the integer. The shipped comment's anchoring is faithful to this.

### 3.2 Does anchoring to a blob id prevent rot? **Yes — and it is the right remedy.**

A path names whatever is there today; a blob id names an immutable object. "These are the
figures for blob `7c543532…` and blob `d1c45afc…`" is true forever, **including after the commit
that ships it**, which is precisely the event that falsified T454's and T466's cardinals. It
does not make the table *current* — but a stale-and-correctly-labelled table is not the defect;
a table that claims to be about the file in front of you and is not, is. The distinction is the
whole of T473's M-1 and T477 got it right.

**And the second half is what actually carries the load.** The number about *this* file is no
longer typed: `guard_harness_text_is_committed` derives S1 from the running bytes every run and
prints it beside their object id. **It read 74 on T466's tip and reads 81 on this one — it moved
in the very commit that installed it**, which is the event that rotted the last two cardinals.
I validated the cheap shell derivation against `read-census.py` on **four** blobs, not T477's
three: **69 / 74 / 81 / 81, agreeing on every one.**

**Cost on the critical path: none measurable.** It is two `grep`s over a 7170-line file inside a
guard whose measured cost across my nine runs was **1 s, 4 s, 4 s, 4 s, 5 s, 5 s, 5 s, 6 s**
against a 300 s ceiling, in a bar whose total wall was 74.7 s. T477's reported `COST 5s /
ceiling 300s` is honest; so is its `GUARD-COST CENSUS: 16 guards timed` (I measured 65 s total
wall to its 74 s, host load being the only difference). **The recompute's cost is honest and it
now runs on every bar without breaching anything.**

L-6 was taken correctly: the parenthesised column is relabelled to what it measures — "LINE
contains a fold image", approximately "the line contains an `s`" — rather than dropped, and only
the weak claim it supports is made.

---

## 4. CLAIM 3 — M-3's DECISION. **RIGHT, AND FOR THE RIGHT REASON.**

T477 chose **keep the refusal, correct the text**. I tested the reasoning rather than the taste,
and it holds: **a carve-out keyed on "the attribute is declared in a committed `.gitattributes`"
is forgeable by committing a file.** Two lines of diff — a `.gitattributes` and a
`filter.*.clean` half — would disarm every `SUPPRESSED` refusal in the tree, and that is
**strictly cheaper than all three routes T466 just closed**, each of which needs local state an
attacker must already have. The premise the recompute rests on (raw bytes are the truth) is
*not* generally true of git — the blob is *defined* as the post-clean bytes — and it is the
right premise against an adversary **because** it disagrees with that definition. Accepting a
false positive on git-lfs is the correct trade for a fail-closed boundary that cannot be talked
out of.

**Is the trade right?** Yes, on this tree and this program: **zero tracked `.gitattributes`, no
`core.attributesFile`, no `core.autocrlf`, no `core.eol`, no filter driver at any config level**
(re-measured, `evidence/90`). The cost is entirely prospective and lands on a *task*, not on a
run.

**Does the corrected text tell a future worker what to do?** Yes, and I checked all three
places. The block comment quotes the old misleading sentence in place rather than deleting it,
then states the true rule in capitals. The run-time LOCAL-STATE census no longer implies filters
pass. And the refusal itself now reads:

```
IF YOU JUST ADOPTED git-lfs OR 'text=auto', THIS IS YOU, AND IT IS NOT A FALSE POSITIVE
[T473 M-3, driven]. … There is no way to declare a legitimate filter here and the carve-out
was refused deliberately: it would be forgeable by committing a .gitattributes. Teach this
guard first; do not disable it.
```

That names the two mechanisms, names the reason, and gives the instruction. It is what a worker
needs. **The `CTLSMUDGE` behaviour is now exactly what the file says will happen** — I drove it
(`evidence/10`) and the words match the outcome.

---

## 5. CLAIM 4 — THE REGRESSION SURFACE. **THE REWRITE IS CLEAN.**

### 5.1 The hasher, re-verified after the rewrite (`evidence/40`)

Extracted **verbatim from the harness on disk** (between the `recpy` quotes, refused unless the
extracted text contains both `hashlib` and `blobsha`) and run against a corpus built to break
it. **19 HEAD entries, quoted as a set with its tree** (a fresh single-commit corpus repository,
13 × `100644`, 1 × `100755`, 5 × `120000`): empty file; all 256 byte values twice including
NULs; CRLF; lone CR; no trailing newline; the exec bit; invalid-UTF-8 **content**; a name with
glob metacharacters; **a name containing a newline**; a name with space and tab; a name
containing U+017F; a 5-deep nesting; a **12 MiB** file; a `ümläut` name; and five symlinks —
relative, absolute, **broken**, UTF-8 target, 300-character target.

```
unperturbed tree : SCANNED 19,  DIFFERS 0,  MODE/UNREADABLE/MALFORMED/MISSING 0,  stderr 0 bytes
vs git hash-object --no-filters : regular entries compared = 14,  MISMATCHES = 0,  OMITTED = 0
perturbation     : regular files PERTURBED = 14  ->  DIFFERS rows = 14,  symlink rows = 0
gitlink          : MODE 160000 mysub    (the ungradeable-entry refusal, as declared)
```

**Zero DIFFERS on the unperturbed tree means the hasher reproduces every committed id**,
including all five symlinks (mode `120000`, hash the link *target string*, do not dereference)
and the empty file's `e69de29b…`. **0 omitted** — T477's note is confirmed: NUL framing carries
the newline-named path that T473's own newline-delimited parser dropped. **14 of 14
perturbations detected, symlinks correctly untouched.** T477's self-reported instrument defect
(its perturbation leg read `ls-files` newline-delimited and silently skipped four C-quoted
names, reporting 10/14 as a pass) is the same shape it repaired, and my instrument was
NUL-framed from the first draft, so it does not reproduce.

### 5.2 T473's CONFIRMED list, re-driven at T477's tip (`evidence/50`)

| arm | EXIT | probe presence | VERDICT | harness-guard refusals |
|---|---|---|---|---|
| CTL clean clone | 0 | 1 (`up`) | PASS 46 / 7884 | 0 |
| **WDIRTY** honest uncommitted edit | **0** | **1 (`up`)** | **PASS 46 / 7884** | **0** |
| SKIPWT `--skip-worktree` + forged text | **2** | **0** | none | **3** |
| ASSUME `--assume-unchanged` + forged | **2** | **0** | none | **3** |
| SMUDGE filter forgery, unrelated victim | **2** | **0** | none | **1** |
| NOPY `recpython` points at nothing | **2** | **0** | none | **1**, by name |

- **SKIPWT and ASSUME each fire THREE independent refusals** — the index bit, the SUPPRESSION at
  the harness path, and the two ids compared by name — reading three different inputs.
- **SMUDGE fires ONE, and one is right.** There is no index bit to find, and with an *unrelated*
  victim the harness's own two ids agree, so only the recompute can see it. (T473's L-5
  correction — "two, not three" — is about the harness-as-victim shape; with a third-party
  victim it is one, and one is enough.)
- **THE HONEST-DIRTY BOUNDARY IS INTACT.** WDIRTY: `committed 1ced9310… / on disk 3f7d228d…`,
  and the run passes with the edit **named and printed**:
  `HARNESS-TEXT: uncommitted edit — .softhouse/conformance.sh (on disk 3f7d228d…)` then
  `this harness is edited but not committed — git agrees`. The harness remains usable during
  development. **Nothing here is merge-blocking.**
- **NOPY fails closed by name** at the `[ ! -x ]` pre-check, `COST 1s`, before any recompute.

### 5.3 The citation sweep and the pins (`evidence/60`)

Independently built extractor over the branch tree at `a6bf50a3`, and a `difflib` line map under
**both** defensible baselines:

```
merge-base 3f4e236a -> tip a6bf50a3  (6327 -> 7170 lines)
  citations whose cited line MOVED  : 20   across 10 files
  citations to a line that VANISHED : 0
  citations PAST THE END of the base: 0
```

The 10-file breakdown, **quoted as a set with its tree** (tree `a6bf50a3`): `t371-t367-conditions
CASUALTY-SWEEP` 2, `t406-review-t391/REVIEW.md` 2, `t409-review-t390/REVIEW.md` 2,
`t411-review-t401/REVIEW.md` 2, `t411-…/evidence/50-bre-blast-radius.txt` 3,
`t446-review-t445/REVIEW.md` 1, `t446-…/evidence/05-conformance-line-citation-sweep.txt` 3,
`t450-review-t412/REVIEW.md` 1, `t459-review-t454/REVIEW.md` 1, `tasks.json` 3. **Identical to
T473's and T477's, and not one of the 20 is load-bearing**: all are review prose, committed
evidence transcripts, or `tasks.json` string fields; none is a `.pin`, none is under
`.softhouse/guards/`, none is `patterns.md`, `fire-program.sh` or the harness.

**Total reconciled:** I count **1797** excluding the harness's **two self-citations**; `git grep`
over the same tree counts **1799** including them. T473's and T477's 1799 is the inclusive count
and reproduces exactly (1295 plain + 502 range, 232 citing files, 440 distinct cited lines,
excluding self). For contrast, `main → tip` moves **233 across 51 files** — that is T458's
pre-existing drift on `main`, not T477's, and it is filed as T478.

**The pins did not move.** `FAILOPEN_PIN_FILE_LIST` and `HOSTSTATE_PIN_TEMP_ASSIGN_LIST` are
**byte-identical at `main`, the merge base, T466's tip and T477's tip** — same start line (1627
and 2097), same line count, same md5 (`8ddc6eb9…` and `70405fc5…`). Live on every graded run:
**`frontier 11, pinned at 11`, `frontier == pinned (all 11 rows, by path)`**, and **`literal
/tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 18`**, with
`dead-path frontier: GREEN, and the T323 reconciliation list is empty.`

**Scope held.** Diffed against the merge base: `tasks.json`, `RESUME.md`, `program.json`,
`patterns.md`, `bin/fire-program.sh` — **0 changed**; `.softhouse/guards/**` and every `*.pin` —
**0 changed**; T473's review — **0 changed**. `.softhouse/LOCK` is `bc5f4a33bb9c…` at `main`,
the merge base, T466's tip and T477's tip. **`git merge-tree` against current `main` produces a
tree with no conflict.**

---

## 6. CLAIM 5 — WHAT IS DECLARED OPEN

The OPEN list is **in the harness itself**, which is the right place, and eight of its nine
claims are accurate: LONGNOP/LONGSTRIP; every non-identity filter and eol conversion refused
honest or not; the gitlink refusing the bar (and agreeing with push-gate C1); the index-bit
refusal being absolute and naming sparse checkout and unmerged entries; PHANTOM printed not
refused; the transcript-not-commit class; U+037E and U+1FEF untargeted; and the challenge's one
honest failure mode, named at the refusal itself.

**One is understated, and it is item 2** — the subject of M-1. It says a substituted interpreter
"must REIMPLEMENT the recompute correctly"; the measured requirement is that it must read one
field out of its own input. **And one qualifier is missing** — m-1: "closed the PATH route and
the environment route" is true of this guard and of no other, while three PATH-resolved `python3`
call sites remain and the environment route is live in them (62 fires, driven).

`patterns.md:3271` / `fire-program.sh:3217` are rotted on `main` by T458; the driver has filed
that as T478 and I took no action.

---

## 7. WHAT I DID NOT RE-DERIVE

Stated so nobody counts it as checked:

1. **The fold census sweep** (1401 candidates / 1091 single-image / 310 multi-image over
   0…0x10FFFF). I used the **13 confirmed codepoints as input**, derived their images
   programmatically and calibrated on U+017F → `s` before counting, but I did not regenerate the
   candidate sweep. T459, T466 and T473 all reproduce it and T477 changed no line of it.
2. **A live U+FB01 checkout collision at `.softhouse/bin/fire-program.sh`**, and **LONGNOP as a
   checkout collision.** Both are T466/T473 declared-open items; T477 changed nothing bearing on
   either.
3. **T477's per-arm `records=` figures** (10368 / 10375 / 10378). They are about trees that no
   longer exist; mine read 10400 throughout, and the number is printed by the guard rather than
   typed, which is the point.
4. **Cold-cache cost.** The page cache cannot be purged on this host, so my 4–6 s figures are
   warm, like T477's 5 s. Neither T466's 21 s nor T473's 51.3 s is a pinned fact, and the shipped
   comment now says so.
5. **A second, git-lfs-shaped honest-filter fixture.** T473 drove it; the mechanism is identical
   to my SMUDGE (a non-identity clean half) and I agree with T477 that a second copy of a
   confirmed finding is effort spent on agreement.
6. **An oracle-backed PASS at my own tip** — see §9.

---

## 8. STILL OPEN AFTER T477, AS I MEASURE IT

1. Everything in the harness's own list, with item 2 corrected to the true bound.
2. **The challenge is answerable by lookup** (M-1) until it is posed over bytes git has never
   seen, or until the text is corrected to say what it buys.
3. **Three PATH-resolved `python3` call sites** remain, including the guard that grades the
   fail-open frontier (m-1). Latent today; the mechanism is driven.
4. A tracked `hashlib.py` (or any stdlib-shadowing basename) at the repository root would hijack
   any interpreter this file invokes **without** `-I`, and that route is **committable**. Zero
   collisions among 829 tracked `.py` files today. Nothing checks it.
5. The whole class remains: what is forged is a **transcript**, never the commit. The verifier
   that closes it is still outside this file, and it must use `--no-filters`.

---

## 9. THE ORACLE

The reference oracle was **UP** for the runs that carry this review's load-bearing verdicts —
the CONTROL on T477's tip (`probe presence 1`, `probe = up`, `PASS 46 / 7884`), the WDIRTY arm,
and both LOOKUP arms that reached `PASS` over the forgery. Every `exit 2` reported above is a
**guard refusal with probe presence 0** — the run never reached the probe — and never an outage.

**It then went down partway through this review**, during the repair drive's R4 arm. That is
recorded rather than hidden: `probe line PRESENCE = 1`, `probe value = down`, and the bar
correctly printed `VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT
A PASS.` The Docker daemon is gone from this host (`/Users/buv/.docker/run/docker.sock` absent),
so it is an **outage, not a corpus fault and not a refusal**. Retried repeatedly through the rest
of the review; it did not return. **No PASS is claimed for any run taken after it went down**,
including the final bar at my own tip in §10.

---

## 10. RESIDUE — VERIFIED IN MY OWN WORKTREE, NOT ASSERTED

Every index bit, filter driver, attributes file, `PATH` shim, `PYTHONPATH` hijack and harness
mutation used by this review lived in **nine throwaway clones under `/tmp/t479-work`**, outside
the repository. Nothing was committed but this review and its evidence: **zero `.sh` or `.py`
files added**, so neither the T238 fail-open frontier nor `guard_no_host_state_in_lint_corpus`
can be moved by it. Full transcript in `evidence/90-residue.txt`:

```
--- 1. INDEX BITS        entries NOT in state H : 0
--- 2. ATTRIBUTE SOURCES, ALL FOUR
    ABSENT : <worktree git-dir>/info/attributes
    ABSENT : /Users/buv/gerege-nbfi/.git/info/attributes        <- the COMMON git-dir, a second file
    ABSENT : /Users/buv/.config/git/attributes
    core.attributesFile   : []  (empty = unset)
    TRACKED .gitattributes files: 0
--- 3. CONTENT FILTERS, EVERY CONFIG LEVEL
    local 0   global 0   system 0   ALL 0     core.autocrlf : []   core.eol : []
--- 4. WORKING TREE      git status --porcelain lines : 0
--- 5. tracked paths carrying the forged-marker token : 0 ; naming the scratch root : 0
       tracked .sh/.py added by this review           : 0
--- 6. LOCK in HEAD = LOCK on disk = bc5f4a33bb9c3ac1504ae344cbf2466c739d9985
       tasks.json / RESUME.md / program.json / patterns.md / conformance.sh /
       fire-program.sh changed vs main : 0 / 0 / 0 / 0 / 0 / 0
--- 7. scratch root /tmp/t479-work   is it inside the repo? : no
```

**No pin was moved and none needed to be.** The two censuses that caught T466's and T473's own
instruments did not catch mine, because I committed no instrument: the shims, the hijack module
and the repair patch are quoted in `evidence/` as text and live nowhere in the tree.

**FINAL BAR ON MY OWN COMMITTED TREE:** `evidence/91-final-bar.txt`, taken at my tip
`fb7e65e2337b8c01d01a5b63877a039bdb02303b` with `bash` (never `sh`/`zsh`), working tree clean,
0 index bits, probe **presence** counted before its value.

```
grep -c 'probe = '  -> 1        <-- PRESENCE, read first
probe value         -> down
EXIT = 2
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
refusal lines matched ('guard_<name>:' on stderr) : 0
this harness: committed db313f98… / on disk db313f98…
frontier 11, pinned at 11   ·   frontier == pinned (all 11 rows, by path)
literal /tmp, /private/tmp or /var/tmp path to a name: 18, pinned at 18
dead-path frontier: GREEN, and the T323 reconciliation list is empty.
guard-cost: PASS — every guard timed, every ceiling row used, none breached.
```

The exit 2 is the **outage of §9, not a guard refusal** — the probe line is present and reads
`down`, and **no guard refused anything: the refusal-line count is 0.** I do not report it as a
PASS. **Which harness graded it:** this branch is cut from `main` and T477 is *not* merged into
it, so the grader is `main`'s `db313f98…`, which does not carry T466's whole-tree recompute —
hence no `RECOMPUTE` / `CHALLENGE` / `READ CENSUS` lines in that transcript. That is deliberate,
and it is T473's method: a reviewer graded by the artefact under review is not an independent
measurement. The graded runs of the *artefact* are the nine arms in `evidence/00`–`evidence/50`,
all taken in throwaway clones at `a6bf50a3`, and the oracle was **up** for every one of them.

---

## 11. IS THIS STACK SAFE TO MERGE?

**Yes.** Explicitly, and with the MAJOR on the record.

- Against `main` as it stands, T477's stack **closes three forgery routes that currently reach
  `VERDICT: PASS`** (SKIPWT, ASSUME, SMUDGE — I re-drove all three GREEN), plus the `PATH` and
  environment interposition routes on the guard that matters most, plus a committable
  cwd-shadowing route it does not even claim.
- The defect I found is in a **newly added defence that fails open exactly where `main` already
  fails open**. It makes nothing worse than the status quo; it makes a claim that is not true.
- It **refuses nothing honest**: 0 challenge refusals in nine runs, 0 in 400 simulated
  selections, the honest-dirty boundary intact, the hasher byte-correct over a nasty corpus, and
  the cost 4–6 s against a 300 s ceiling.
- Scope is held, both pins are byte-identical, the frontier is 11/11, host-state is 18/18, and
  the branch merge-trees into current `main` without conflict.

**Merge it, and file M-1 as a repair task** — the patch is nine lines and I have driven it RED
and GREEN. Do not let the merge stand as agreement that the challenge does what the harness says
it does: **it does not, and a reader who trusts that sentence is trusting a lie the harness
prints about itself.**

---

*Reviewer: T479. Instruments and transcripts: `.softhouse/reviews/t479-review-t477/evidence/`.
Nine full bar runs; every probe line's presence counted before its value; every arm in a
throwaway clone outside the repository.*
