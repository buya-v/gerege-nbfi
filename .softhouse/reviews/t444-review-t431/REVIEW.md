# T444 — INDEPENDENT REVIEW of T431 (`softhouse/T431-t407-conditions`)

# VERDICT: `APPROVED WITH CONDITIONS`

**The change is correct, its central claim is true, and I reproduced every fail-open it reports
plus one it does not. It should merge.** The conditions below are one **MAJOR** (a fifth,
driven, live fail-open of the same class that survives this fix — a RESIDUAL, present on `main`
too, not caused by T431), two **MINOR**, and four **LOW**. None of them is a reason to hold the
merge; the MAJOR is a reason not to let the record say the class is closed.

Subject: T431's change to `.softhouse/conformance.sh` inside `guard_guards_dir_registration`
(`C-T407-1`), plus `C-T407-2`, `C-T407-3`, `C-T407-4`. Reviewed as **grading infrastructure**:
this function decides whether every other task in this program passes.

Honesty rule: every material claim is `[VERIFIED: <source>]` or `[UNVERIFIED]`.
Every instrument in `evidence/` takes its work root **as an argument**; none binds a literal
shared-temp path to a name, so none adds a row to `HOSTSTATE_PIN_TEMP_ASSIGN_LIST` — the merge
bar shows the host-state census still `18 == pinned 18` [VERIFIED].

---

## 1. THE HEADLINE — re-derived from git, and IT HOLDS

T407 diagnosed the hole and prescribed the one-token pin `":(literal)$self_norm"`. T431 reports
that **the pin alone does not close it**. I derived this from git before reading T431's evidence
[VERIFIED: `evidence/01-git-quoting.txt`, git 2.50.1 (Apple Git-155), `core.ignorecase=true`]:

```
=== ls-files (default quotePath) ===          === ls-files with -c core.quotePath=false ===
d/plain.txt                                   d/plain.txt
"d/q\".txt"                                   "d/q\".txt"
"d/w\\x.txt"                                  "d/w\\x.txt"
"d/w\303\251.txt"                             d/wé.txt
"d/\320\266\320\260\320\263…\321\202.txt"     d/жагсаалт.txt
```

`git ls-files` C-quotes a non-ASCII byte, a backslash and a double quote and wraps the result in
**literal double quotes**. `self_norm` is the OUTPUT of a pathspec lookup, so **`self_norm` is a
rendering, not a path**, and handing it back as `":(literal)$self_norm"` matches nothing
[VERIFIED: same file]. `core.quotePath=false` removes the non-ASCII quoting but **not** the
backslash or dquote quoting [VERIFIED] — exactly as T431 states.

**The 8-way matrix over (pin, empty-result, round-trip), evaluated with the guard's own
expressions transcribed verbatim** [VERIFIED: `evidence/03-necessity-redundancy-matrix.txt`]:

```
--- XQ   typed witness g/zz/wé.txt      self_norm = ["g/zz/w\303\251.txt"]
        pin=no  empty=no  rt=no  -> ACCEPT
        pin=no  empty=yes rt=no  -> ACCEPT
        pin=yes empty=no  rt=no  -> ACCEPT      <-- THE RATIFIED PIN, AND IT ACCEPTS
        pin=yes empty=yes rt=no  -> ACCEPT      <-- PIN + EMPTY-RESULT, AND IT STILL ACCEPTS
        (all four rt=yes rows) -> REFUSE:round-trip
```

**This is a result about this program's own review process and it should be stated plainly: a
remedy an independent reviewer had already approved was insufficient, and not marginally — in
four of eight configurations.** Anyone who had applied T407's prescription and stopped would
have shipped a still-open hole with a review signature on it. T431 found this by probing git's
behaviour *before* trusting the one-token change; that is the method, and it worked.

One thing T431 does not state and which is worth adding, because it is what makes this a class
fix rather than a spelling fix: **after the change, the `self_norm` that reaches the closing
`grep` is guaranteed to be a real path.** No C-quoted rendering can round-trip — a rendering
begins with `"`, and `"` is itself a character git quotes, so a tracked file literally named
that rendering renders differently again. The fixed point of the round-trip test is exactly the
set of unquoted renderings.

## 2. THE FOUR FAIL-OPENS — all four reproduced on TODAY's `main`, with my own construction

Driven with my own instrument `evidence/drive-t444.sh` (my own directory leaves, member names
and arm set, written from my reading of the guard), cloning `main` at **`290d8f84`** — newer
than either tree T431 measured [VERIFIED: `evidence/10-RED-BEFORE-t444-drive-on-main.txt`,
`evidence/15-RED-decisive-lines-per-arm.txt`]. Probe PRESENCE is counted before any value is
read, in the runner itself.

| my arm | typed witness spelling | `main` @ `290d8f84` |
|---|---|---|
| `T444-X` | `:(literal)P` | **exit 0 / probe PRESENT ×1 / VERDICT PASS 46/7884** |
| `T444-XT` | `:(top,literal)P` | **exit 0 / probe PRESENT ×1 / VERDICT PASS 46/7884** |
| `T444-XI` | `:(literal,icase)P` | **exit 0 / probe PRESENT ×1 / VERDICT PASS 46/7884** |
| `T444-XQ` | the **C-QUOTED** witness + a decoy at the quoted literal name | **exit 0 / probe PRESENT ×1 / VERDICT PASS 46/7884** |

Every one at `population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0
symlink-members=0`, with the guard printing, over a witness that is a symlink to the member
itself [VERIFIED: `evidence/11-RED-arm-X-full-bar-on-main.txt`]:

```
conformance:     REACHED-BY .softhouse/guards/zz-t444x/zz-t444x-member.sh — declared in its own header, reached by
conformance:   GUARDS-DIR-REGISTRATION: population=7 … reached-by=2 … symlink-members=0
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

**All four are real, and all four are refused on T431's branch** [VERIFIED: my GREEN drive]:
`X`, `XT`, `XI` by `THAT WITNESS IS A SYMLINK` (the pin lands the lookup on the real witness,
which round-trips, so the mode test does its job); `XQ` by `DID NOT ROUND-TRIP`; `XQ0` by
`matched NO INDEX ENTRY`. Exit 2, probe ABSENT, every one.

## 3. NECESSITY AND REDUNDANCY — checked both ways; T431's honesty is verified

| line | independently necessary for a REFUSAL? | if removed, what covers it |
|---|---|---|
| **round-trip** | **YES** | **nothing** — `XQ` is ACCEPTED in all four `rt=no` configurations |
| pin | no | round-trip: the de-magicked lookup returns two lines, so `self_path` carries the decoy path and an embedded newline |
| empty-result | no | round-trip: `self_path` is empty, `self_norm` is not |

Driven end-to-end, not only modelled: `T444-RVQ` (kill the round-trip line alone on the fixed
tree) reaches **exit 0, probe PRESENT, `VERDICT: PASS 46/7884`, `reached-by=2`** [VERIFIED:
`evidence/16-GREEN-arm-RVQ-hole-reopens.txt`]. **The hole reopens. Round-trip is independently
necessary and T431's report of that is exact.**

**The adversarial question — two parts are redundant only because of a neighbour; what happens
when the neighbour moves?** The neighbour covering both is the round-trip line, and it is the
one line in this repair with no automated arm anywhere in the harness. See **C-2**.

I also went looking for a case where the pin is independently necessary *on the healthy side* —
a legitimate witness the pin accepts and the un-pinned lookup would make round-trip refuse. **I
could not construct one.** A legitimate witness named `w[1].txt` is ACCEPTED under all eight
configurations; the same name with a colliding honest sibling `w1.txt` is refused as
`self_multi` under all eight, at the FIRST (still unpinned) lookup [VERIFIED: `evidence/03`,
scenarios `LEGG`, `LEGG2`]. So the pin's justification is that it makes the lookup *correct*,
not that it covers anything — which is precisely what T431 says, and I could not improve on it.

## 4. THE CONVERSE RISK — does it now refuse too much? **No.**

Driven with the whole bar on BOTH trees, because this is the point the brief flagged as a
possible MAJOR.

Eight legitimate witness spellings under the fixed configuration, **all eight ACCEPTED**
[VERIFIED: `evidence/07-healthy-witness-spellings-under-the-fix.txt`] — including the
`./`-spelled form T375 kept an arm for, a `..`-normalised form, spaces, glob characters and `+`.

Full-bar arms:

| arm | `main` @ `290d8f84` | T431's branch |
|---|---|---|
| `T444-Z` unmutated | exit 0, PRESENT, `population=6 … reached-by=1` | **identical** |
| `T444-LEGA` honest ASCII witness | **exit 0, PRESENT, `reached-by=2`** | **exit 0, PRESENT, `reached-by=2`** |
| `T444-LEGC` honest **Cyrillic** witness `гэрчилгээ.txt` | **exit 2, ABSENT** (`…DOES NOT NAME…`) | **exit 2, ABSENT** (`matched NO INDEX ENTRY`) |
| `T444-LEGM` Cyrillic directory **and** witness | **exit 2, ABSENT** | **exit 2, ABSENT** |

**The over-refusal of non-ASCII witness paths is PRE-EXISTING. T431 does not cause it, and the
MAJOR the brief anticipated is NOT realised.** What T431 changes is the *message* — from a
misleading "that witness does not name the member", which sends the next worker to inspect file
contents, to an accurate one naming the C-quoting as the cause and printing the rendering. That
is strictly better.

It is still a real standing constraint, and broader than the witness path: a Cyrillic
**directory** under `.softhouse/guards/` additionally crashes `guard_dead_path_frontier`'s
census instrument — `unreadable corpus member ".softhouse/guards/\321\205\320\260\320\273\321\202/…":
[Errno 2] No such file or directory` [VERIFIED: `T444-LEGM` transcript]. It refuses rather than
passing (P-81 honoured), but the cause it prints is not the cause. See **C-4**.

## 5. THE DISCLOSED BOUNDS — five driven, and one of them is a live fail-open

T431 lists six bounds as *unreached, not unreachable*. I drove five.

| T431's bound | driven as | result |
|---|---|---|
| 1 — a path containing a literal NEWLINE, and the member enumeration `while IFS= read -r rel` | `T444-NLMEM` | **fail-CLOSED.** `git ls-files` C-quotes the newline, so the enumeration reads one whole line; the member then hits the member-side `RESOLVES TO NO INDEX ENTRY` refusal (T404's arm N branch). exit 2, probe ABSENT, on **both** trees [VERIFIED] |
| 2 — a GITLINK entry ending in `.sh` | `T444-GITL`, `T444-GITL2` | **fail-CLOSED.** A mode-`160000` entry DOES enter the population; it is refused `IS INVOKED BY NOTHING`, even when its basename is borrowed from a genuinely invoked member (`check-capture-namespace.sh`). exit 2, probe ABSENT [VERIFIED] |
| 3 — a case-sensitive host | `T444-CASE` (the *other* direction) | **LIVE FAIL-OPEN — see M-1** |
| 6 — a member carrying MULTIPLE `REACHED-BY` rows | `T444-2ROWH`, `T444-2ROWX` | **not a fail-open, but the second row is never graded.** `grep -m1` takes row 1: honest-first is ACCEPTED at `reached-by=2` and the hostile row-2 (a symlink to the member) is silently ignored; hostile-first is REFUSED `THAT WITNESS IS A SYMLINK` [VERIFIED]. See LOW-5 |
| "conflicted index" (T431's own `## Unverified`, reasoned not driven) | `evidence/02` | **driven, and it falsifies a sentence T431 shipped — see C-1** |

Not driven by me either: a **second git binary**, and an actual **case-SENSITIVE filesystem**.
**[UNVERIFIED — bounds on my search.]**

## 6. THE ROTTED CARDINALS — `C-T407-2`, `C-T407-3`, `C-T407-4` all verified

* **All seven cited cardinals are rotted on today's `main`, and `:4090` is a bare double quote
  mid-string** [VERIFIED: `awk` on `main`]:
  ```
  4090: "
  4109:     warn "conformance: guard-cost: NOT ONE guard was timed. …"
  4140:       stale=$((stale + 1))
  4143:       warn "conformance: NEVER TIMED. …"
  4585:     return 1
  4610:   if [ "$bad" -ne 0 ]; then
  4611:   warn "conformance:"
  ```
  The three identifiers actually live at `run_guards` defined `:4165` / called `:4660`;
  `probe_oracle` defined `:4637` / invoked `:4685`; `guard_cost_census` defined `:4106` / called
  `:4215` [VERIFIED: `grep -n` on `main`]. The replacement `grep -n 'run_guards\|probe_oracle\|
  guard_cost_census'` regenerates the block in one command and cannot go stale. **Deleting rather
  than refreshing is the right call and the cost argument for declining a guard is sound.**
* **Line-count neutrality holds and the citation it protects still resolves.**
  `patterns.md:3426` cites `conformance.sh:3271`; `sed -n 3271p` prints the same
  `population is EMPTY` refusal on `main`, on T431's tree **and in the merge result**
  [VERIFIED: three separate checks].
* **`C-T407-3`'s substance is right** — `member_multi` must not be deleted as dead code and `R1`
  must not be cited as coverage — **but one sentence in it is false. See C-1.**
* **`C-T407-4`'s two corrections are true.** `…/t404-t384-conditions/evidence/10-…txt` lines 15
  and 23 both score `marker=NO census=NO dirty=no >>> FAIL` [VERIFIED: read the file];
  `evidence/11-…txt` lines 11 and 14 carry `line 501: r: command not found` and
  `line 521: syntax error near unexpected token 'fi'` [VERIFIED: read the file].
* **The freeze claim is checkable, and it checks out.** `sha256` of the COMMITTED
  `drive-t431.sh` is `f4f0e5845774fe8864019f878868e5aee995f6b60656974457048f7c2283ba2a`, and
  that is the `FROZEN drive: … sha256=` in the headers of **both** `evidence/40` (RED) and
  `evidence/50` (GREEN) [VERIFIED: `shasum -a 256` vs the two headers]. The committed instrument
  is byte-identical to the one that produced both transcripts. Reviewers rarely get to check a
  provenance claim; this one holds.
* **T431's two new `patterns.md` citations resolve**: `:1654` is P-57, `:2775` is P-80
  [VERIFIED]. See LOW-2.

---

## THE FULL ARM TABLE — my own drive, both trees

`RED` = today's `main` at `290d8f84`, `GREEN` = T431's tip `d459ec82`. Same frozen instrument
for both (`sha256 b173219c61d32b5c87194a80fac8361f53dec376296a5de038d03d6b2a475675`, `chmod
a-w` before either run, so an edit could not reach a run in flight — T431's `C-T407-4` lesson,
adopted). Mode detected from the ref's own blob and not passable in: `RED` reported
`pin=no empty=no round-trip=no`; `GREEN` reported `pin=yes empty=yes round-trip=yes`.
`=== T444 DRIVE: 12 PASS / 2 FAIL of 14 ===` (RED) and `13 PASS / 2 FAIL of 15` (GREEN)
[VERIFIED: `evidence/10-RED-BEFORE-t444-drive-on-main.txt`,
`evidence/17-GREEN-AFTER-t444-drive-on-T431-branch.txt`].

| arm | what it is | on `main` | on T431 | reading |
|---|---|---|---|---|
| `Z` | unmutated | 0 / PRESENT | 0 / PRESENT | the guard still passes a clean tree |
| `LEGA` | honest ASCII witness | 0 / PRESENT, `reached-by=2` | **0 / PRESENT, `reached-by=2`** | **honest work is still accepted** |
| `LEGC` | honest **Cyrillic** witness | 2 / ABSENT `DOES NOT NAME` | 2 / ABSENT `matched NO INDEX ENTRY` | pre-existing refusal, better message — **C-4** |
| `LEGM` | Cyrillic dir + witness | 2 / ABSENT | 2 / ABSENT | pre-existing; also crashes the dead-path census |
| `X` | `:(literal)P` + decoy | **0 / PRESENT / VERDICT PASS** | 2 / ABSENT `THAT WITNESS IS A SYMLINK` | closed |
| `XT` | `:(top,literal)P` + decoy | **0 / PRESENT / VERDICT PASS** | 2 / ABSENT `THAT WITNESS IS A SYMLINK` | closed |
| `XI` | `:(literal,icase)P` + decoy | **0 / PRESENT / VERDICT PASS** | 2 / ABSENT `THAT WITNESS IS A SYMLINK` | closed |
| `XQ` | C-QUOTED + quoted-name decoy | **0 / PRESENT / VERDICT PASS** | 2 / ABSENT **`DID NOT ROUND-TRIP`** | **closed only by round-trip** |
| `XQ0` | C-QUOTED, no decoy | 2 / ABSENT | 2 / ABSENT `matched NO INDEX ENTRY` | closed both ways |
| `RVQ` | round-trip killed on the fixed tree | — | **0 / PRESENT / VERDICT PASS** | **the hole reopens; round-trip is independently necessary** |
| `NLMEM` | member filename contains `0x0A` | 2 / ABSENT | 2 / ABSENT | **T431 bound 1 — fail-CLOSED** |
| `GITL` | gitlink `.sh` member | 2 / ABSENT `INVOKED BY NOTHING` | 2 / ABSENT | **T431 bound 2 — fail-CLOSED** |
| `GITL2` | gitlink borrowing a real member's basename | 2 / ABSENT `INVOKED BY NOTHING` | 2 / ABSENT | fail-CLOSED |
| `2ROWH` | two `REACHED-BY` rows, honest first | 0 / PRESENT | 0 / PRESENT | **T431 bound 6 — row 2 never graded**, LOW-5 |
| `2ROWX` | two rows, hostile first | 2 / ABSENT | 2 / ABSENT | fail-CLOSED |
| **`CASE`** | index/filesystem case divergence | **0 / PRESENT / VERDICT PASS** | **0 / PRESENT / VERDICT PASS** | **M-1 — LIVE ON BOTH TREES** |

`LEGC` and `LEGM` are scored FAIL by the runner because I wrote their expectation as
ACCEPT — that expectation is the finding, not an instrument failure, and it is identically
unmet on `main`.

## BAR

**T431's tree AND the merge result. I built the merge rather than reasoning about it.**

`git merge origin/softhouse/T431-t407-conditions` onto `main`: **rc=0, `git ls-files -u` empty,
clean worktree** [VERIFIED]. T431's argument that the merge is clean is correct in substance —
`git diff 683c8aff main -- .softhouse/conformance.sh` is exactly the one line
`EXEMPTION_PIN_LEDGER_WRONGIMPLS=15 → 16` [VERIFIED] — but I did not accept it, I merged and
barred.

| figure | `main` @ `cab6be41` | **MERGE RESULT** | required |
|---|---|---|---|
| exit | 0 | **0** | 0 |
| `probe = ` line count, read BEFORE its value (P-84) | 1 | **1** | ≥1 |
| probe value | `up` | **`up`** | — |
| VERDICT | PASS 46 / 7884 | **PASS — 46 parity vectors, 7884 cells** | unmoved |
| **wrong ledger implementations** | 16 | **16, all 16 died through the harness** | **16** |
| `EXEMPTION_PIN_LEDGER_WRONGIMPLS` | 16 | **16** (at `:4694`) | 16 |
| guards-dir census | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | **identical** | unmoved |
| `deadOccurrences` | 108 | **108** | unmoved |
| `deadFiles` / `resolving` / `indeterminate` | 75 / 1444 / 117 | **75 / 1444 / 117** | unmoved |
| dead-path corpus | 1524 | **1525** (+1 = `drive-t431.sh`) | no pin on it |
| host-state census | 18 == pinned 18 (189 instruments) | **18 == pinned 18** (190) | unmoved |
| exemption grounding | 4 GROUNDED / 0 UNGROUNDED | **4 / 0** | unmoved |
| `guard_guards_dir_registration` cost | — | **1 s / ceiling 60 s**, 0 breaches | under ceiling |
| the three fix lines, by content | 0 / 0 / 0 | **1 / 1 / 1** | 1 each |
| `patterns.md:3426` → `conformance.sh:3271` | resolves | **resolves** | resolves |
| tree clean after the run | yes | **yes** | yes |

**`main` is 16 and the merge result is 16.** T431's own tree carries pin 15 with 15
implementations — internally consistent with its fork point, and the merge takes `main`'s 16
because T431 never touched that line.

**This review branch's own bar**, run from the worktree with `bash`, at commit `92c40c0d`
[VERIFIED: `evidence/20-BAR-this-review-branch-figures.txt`, full transcript
`evidence/19-BAR-this-review-branch.txt`]:

```
EXIT=0        grep -c 'probe = ' = 1        probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
CENSUS wrong ledger implementations — discovered 16 … all 16 … DIED through this harness
GUARDS-DIR-REGISTRATION: population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0
T316-DEADPATH-CENSUS: corpus=1528 deadFiles=75 deadOccurrences=108 resolving=1445 indeterminate=117 prose=387
CENSUS host state … 192 repo-wide search instrument(s) … 18, pinned at 18
```

Corpus `1524 → 1528` is my four tracked `.sh` instruments; `deadOccurrences` is **unmoved at
108** because every planted repo-rooted path in them is assembled at run time from a directory
variable plus a leaf, and **the host-state census is unmoved at `18 == 18`** because every
instrument takes its work root as an argument.

**Re-run on the FINAL tip `b4ea4438`, `git status --porcelain` EMPTY before AND after**
[VERIFIED: `evidence/22-FINAL-BAR-figures.txt`; full transcript, 840 lines,
`evidence/21-FINAL-BAR-this-review-branch-clean-tree.txt`]: **EXIT 0**, `grep -c 'probe = ' = 1`
then `probe = up`, `VERDICT: PASS 46 / 7884`, **16** wrong ledger implementations all dead,
`population=6 … reached-by=1 … symlink-members=0`, `deadOccurrences=108`, host state
`18, pinned at 18`. Corpus `1529` (+1, `own-bar-t444.sh`).

---

# CONDITIONS

## M-1 (MAJOR) — A FIFTH ROUTE IS LIVE, IT SURVIVES ALL THREE NEW LINES, AND IT IS DRIVEN

**This is a RESIDUAL, not a regression: it is a fail-open on `main` too, and T431 listed the
case bound as unreached.** It is filed MAJOR because the record must not be allowed to say the
witness side is closed, and because the remedy is known and cheap.

**The construction.** T431 records "a case-SENSITIVE filesystem" as its unreached bound. The
live route is the *other* direction — on a case-INSENSITIVE host, which is the host this whole
program runs on, the INDEX can hold two entries differing only in case while the FILESYSTEM
holds one file:

```
index:   .softhouse/guards/zz-t444k/W.txt  100644  DECOY blob        <- the path the member DECLARES
         .softhouse/guards/zz-t444k/w.txt  120000  symlink -> member <- sorts AFTER 'W', so it WINS
                                                                       the checkout collision
filesystem after a FRESH CLONE:  w.txt -> zz-t444k-member.sh   (only)
```

Every test in this direction that reads the INDEX grades `W.txt`; the closing `grep`, which
reads the FILESYSTEM, opens `w.txt` — the symlink — and dereferences it to the member itself.

**What it defeats, one by one** [VERIFIED at git level:
`evidence/09-case-symlink-route-model.txt`, `evidence/11-case-attacker-chosen-order-ACCEPT.txt`]:

* the **pin** — `:(literal)W.txt` resolves that exact entry;
* the **empty-result branch** — the lookup is non-empty;
* **the round-trip test — `self_path == self_norm` EXACTLY.** This is the point: round-trip
  compares two *renderings of the same lookup*, and both lookups agree. It cannot see that the
  filesystem resolves the agreed path somewhere else;
* the **symlink refusal** — `self_mode` is `100644`, read from the index at the declared path;
* the **blob refusal** — `self_blob` is the decoy's, not the member's.

**Driven through the WHOLE BAR, on T431's own fixed tree, in a FRESH CLONE** [VERIFIED:
`evidence/12-CASE-full-bar-on-T431-branch-ACCEPTED.txt`]:

```
EXIT=0
grep -c 'probe = ' = 1        (presence read before value)
probe = up
GUARDS-DIR-REGISTRATION: population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0 symlink-members=0
    REACHED-BY .softhouse/guards/zz-t444k/zz-t444k-member.sh — declared in its own header, reached by
               .softhouse/guards/zz-t444k/W.txt (verified: it names zz-t444k-member.sh)
(no registration refusal printed)
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

An unwired planted checker ACCEPTED at `reached-by=2`, `symlink-members=0`, with the guard
printing its own *"(verified: it names …)"* sentence over a witness that is a symlink to the
member itself. **Identical on `main`** [VERIFIED:
`evidence/13-CASE-full-bar-on-MAIN-ACCEPTED.txt`] — so it is pre-existing.

**Two honest mitigations, stated so this is not overrated.** git prints a loud
`warning: the following paths have collided` on checkout, and `git status --porcelain` reports
` T .softhouse/guards/zz-t444k/W.txt` on every checkout of that commit — so the tree is
permanently dirty. Neither is read by `conformance.sh`, and the bar passes anyway. Also, the
order matters: if the attacker lets the *decoy* win the collision the guard refuses
`DOES NOT NAME` [VERIFIED: `evidence/10-case-fresh-clone-order-matters.txt`] — but the attacker
chooses the order, and choosing it is one character.

**THE REMEDY, DRIVEN** [VERIFIED: `evidence/14-remedy-read-the-tracked-blob.txt`]:

```
HONEST   grep(FILESYSTEM)=NAMES-IT       grep(TRACKED BLOB)=NAMES-IT
CASE     grep(FILESYSTEM)=NAMES-IT       grep(TRACKED BLOB)=does-not-name
```

**Read the TRACKED BLOB, not the filesystem.** T375 wrote the argument itself, for the blob
test, and never applied it to the `grep` that actually decides:

> *"Comparing object ids compares what is COMMITTED, not what is on this host, so it is stable
> across checkouts."*

The closing `grep -qF -- "$base" "$REPO_ROOT/$self_norm"` is the last test in this direction
still reading the host. Replacing it with a read of `self_blob` — which is already in hand from
the pinned lookup — closes the case route, refuses nothing legitimate (`HONEST` is unchanged),
and removes the entire index-versus-filesystem divergence family from this direction at once.
**Note the P-57 constraint honestly:** the naive form is a pipeline
(`git cat-file blob … | grep -q`), which this function avoids everywhere; the in-idiom form
writes the blob to a temporary and greps the file, as `guard_pnumber_citations` and
`guard_dead_path_frontier` already do.

**What must change in the record, at minimum:** `FU-T431-1`'s "honest citation" currently reads
*"T404 + T431 close the pathspec-ambiguity and pathspec-quoting routes on the witness side,
driven; the newline, gitlink, case-sensitive-host and multiple-row routes are unreached, not
unreachable."* After this review: newline and gitlink are **driven and fail-closed**; the
multiple-row route is **driven and not a fail-open**; and **the CASE route is not "unreached" —
it is DRIVEN AND LIVE, on the case-insensitive host this program actually runs on, on `main` and
on this branch.** File it as `FU-T444-1`.

## C-1 (MINOR) — the fix ships the exact "unreachable-by-construction" claim this task exists to punish, and it is measurably false

T431's new `C-T407-3` block says of `member_multi`:

> On any git that HONOURS `:(literal)` — 1.9 and later, i.e. every git this program will meet —
> a literal pathspec matches AT MOST ONE index entry, so THIS BRANCH CANNOT FIRE. Its only
> driven route is R1, which is a SYNTHETIC REVERT … It is deliberately
> unreachable-by-construction.

**Driven false** [VERIFIED: `evidence/02-conflicted-index-literal-pathspec.txt`, git 2.50.1, no
revert of anything]:

```
=== git ls-files -s -- ':(literal).softhouse/guards/zz/c.sh' ===
100644 df967b96… 1	.softhouse/guards/zz/c.sh
100644 351be5bf… 2	.softhouse/guards/zz/c.sh
100644 e45c9c26… 3	.softhouse/guards/zz/c.sh
=== line count === 3
```

A conflicted index carries three stages for one path; `:(literal)` pins the path, not the stage.
The branch has a live, non-synthetic route on a conforming git.

**The direction of failure is safe** (`member_multi` refuses), so there is no hole. The finding
is the sentence. `T404` rated `FU-T404-1` unreachable, `T407` reached it, and T431's own
headline is that a remedy prescribed on that reasoning was insufficient — and then T431 wrote
"CANNOT FIRE" about a branch it had not exhausted. T431 also records the conflicted-index case
for the *witness* side in its own `## Unverified` section, so **two statements in one commit
cannot both be true.**

**Remedy (in-grant, one sentence):** replace "THIS BRANCH CANNOT FIRE … deliberately
unreachable-by-construction" with "this branch has one known live route on a conforming git — a
CONFLICTED INDEX, where `git ls-files -s` prints one line per stage for a single path (driven,
T444) — and it is fail-closed on it."

## C-2 (MINOR) — the only independently necessary line is the one with no automated arm

§3 shows round-trip is the sole line that closes `XQ`. `conformance.sh` executes **no**
registration-forgery drive: everything it runs is
`check-ledger-invariants.sh`, `check-capture-namespace.sh`, `check-dead-path-frontier.sh`,
`50-failopen-lint.py`, `check-pnumber-citations.py`, `run-ownership-matrix.py` and the
`capture/lib` census scripts [VERIFIED: every external invocation in the file]. T431's 18-arm
drive is capture-only. A later edit that deletes the round-trip line takes the whole bar to
**exit 0 / probe PRESENT / VERDICT PASS** — driven, as arm `RVQ`. Four paragraphs above that
line, this same function quotes P-45: *"a guard that only works when someone remembers to run it
enforces nothing."*

**Remedy of record — the file already knows how to do this, in three places.**
`guard_pnumber_citations`, `guard_dead_path_frontier` and `guard_reconciler_ownership` each run
their checker's `--selftest` before trusting its verdict. Either (a) give
`guard_guards_dir_registration` the same shape — one synthetic fixture, one refusal expected —
or (b) the cheap structural version: assert the three lines are present **by content**, which is
how T431 itself located the site. Not blocking: the gap predates T431 and applies to every
refusal in this family since T375. It is filed here because T431 is the commit that made one of
those lines load-bearing and alone.

## C-3 (LOW→MINOR) — the neutrality analysis checked one citation; a second live one rots

`.softhouse/RESUME.md:52` cites `conformance.sh:3677` for "the witness-side lookup". On today's
`main`, `:3677` **is** that lookup; on T431's tree the pinned lookup is at `:3782` and `:3677`
is a comment about blob comparison [VERIFIED: both].

A repo-wide sweep of `conformance.sh:NNNN` citations restricted to live directive files
(`patterns.md`, `RESUME.md`, `obligations.md`, `gates.md`, `.softhouse/bin/`, `.claude/skills/`,
`docs/`, `CLAUDE.md`) returns 24 rows [VERIFIED:
`evidence/06-conformance-line-citation-sweep.txt`]. Exactly **three** land inside T431's changed
span, and the outcome is 2 preserved / 1 rotted:

| citation | on `main` | on T431's tree |
|---|---|---|
| `patterns.md:3426` → `:3271` | correct | **still correct** — the neutrality T431 sized for |
| `.softhouse/bin/fire-program.sh:1406` → `:3217-3220` | already rotted (function header, not the quoted refusal) | **unchanged** — those four lines are below the neutral hunk and do not move [VERIFIED] |
| `.softhouse/RESUME.md:52` → `:3677` | **correct — it is the witness-side lookup** | **ROTTED** — the lookup is at `:3782`; `:3677` is now a comment about blob comparison |

Nothing grades `RESUME.md`, so `main` does not redden, and the row is stale anyway now that
T431 is complete. **The finding is the method, not the damage:** "I checked the citation I knew
about" is how this file has now rotted three times, and one `grep` over the tree finds the
whole set in a second.

**Remedy:** in the merge commit rewrite `RESUME.md:52` to name
`guard_guards_dir_registration` — the same remedy T431 records for `FU-T431-2`.

## C-4 (MINOR) — "plain ASCII paths under `.softhouse/`" is now a printed instruction and still not a recorded constraint

Driven in §4. The refusal is pre-existing and T431 improves the message, so this is not a
condition against the change. It is the condition that the constraint T431's new warn text now
instructs workers to obey — *"Name a witness with a plain ASCII path"* — be written where
workers read it, together with the second consequence nothing documents: a non-ASCII path under
`.softhouse/guards/` also crashes `guard_dead_path_frontier`'s census, and so does a newline
path (`[Errno 2]`) and a gitlink (`[Errno 21] Is a directory`) [VERIFIED: three transcripts].
In a program whose `CLAUDE.md` is about Mongolia, this is worth one paragraph in `patterns.md`.

**Remedy of record, with the measured limit:** `-c core.quotePath=false` on both witness lookups
un-quotes non-ASCII while still quoting backslash and dquote [VERIFIED: `evidence/01`], so it
narrows the constraint from "no non-ASCII" to "no backslash, quote, control character or
newline" — it does not remove it.

## LOW-1 — a wording slip in a bar-figure justification
"the merge is clean: that line is ~850 lines below my lowest edit."
`EXEMPTION_PIN_LEDGER_WRONGIMPLS` is at old `:4548`; T431's **lowest** edited line is `:3164`
(distance 1384), its **last** is `:3724` (distance 824). The number matches the *last* edit, not
the lowest. The merge is clean regardless — I performed it [VERIFIED].

## LOW-2 — `C-T407-2` argues "have no numbers to grade", then adds two numbers
The replacement text cites `patterns.md:1654` (P-57) and `patterns.md:2775` (P-80). Both resolve
today [VERIFIED]. Neither is graded: `guard_pnumber_citations` matches a cited P-number against
the RULE SENTENCE `patterns.md` defines under it, never against a line number [VERIFIED: read
the guard]. `patterns.md` grows every fire.

## LOW-3 — the committed tip was not itself barred
T431's final bar is recorded on `20018d18`; the branch tip is `d459ec82`, which adds
`evidence/60`, `evidence/61` and the handoff. Evidence-only, but the barred tree is not the
merged tree. I barred the **merge of the tip**: EXIT 0 [VERIFIED].

## LOW-4 — the `-f` test grades a different file from everything downstream
`[ ! -f "$REPO_ROOT/$self_wit" ]` runs on the TYPED spelling. For a magic-prefixed spelling that
is an ordinary relative path the attacker created, and it is not the file the mode, blob and
grep tests read. After the fix that is harmless — grading is consistent on `self_norm` — but the
test is decorative for exactly the family that motivated this task, and T404's stated reason for
it has now been measured wrong twice (once by T431 for the backslash route; once here).

## LOW-5 — a member's SECOND `REACHED-BY` row is never graded by anything
`grep -m1` takes the first row. Driven: honest-first is ACCEPTED at `reached-by=2` with a
hostile second row (a symlink to the member) sitting in the file ungraded; hostile-first is
REFUSED [VERIFIED: `T444-2ROWH`, `T444-2ROWX`]. Not a fail-open — the member really is witnessed
by row 1 — but a reviewer reading the file sees two declarations and the harness graded one.
**Remedy:** count the rows and refuse more than one, or say in the code that only the first is
graded. One line either way.

---

# FOLLOW-UPS TO FILE

* **`FU-T444-1` (from M-1, MAJOR).** Close the index-versus-filesystem divergence in
  `guard_guards_dir_registration`'s witness direction by making the closing `grep` read the
  TRACKED BLOB (`self_blob`, already in hand) instead of `"$REPO_ROOT/$self_norm"`. Driven
  remedy and driven defect both in `.softhouse/reviews/t444-review-t431/evidence/`. Keep the
  P-57 no-pipeline discipline: write the blob to a temporary and grep the file, the shape
  `guard_pnumber_citations` and `guard_dead_path_frontier` already use. Amend `FU-T431-1`'s
  honest citation at the same time — newline and gitlink are now **driven fail-closed**, the
  multiple-row route is **driven and not a fail-open**, and the case route is **driven and
  live**, not unreached.
* **`FU-T444-2` (from C-1).** One-sentence correction to the `C-T407-3` block: `member_multi`
  is not unreachable-by-construction; a conflicted index reaches it on a conforming git.
* **`FU-T444-3` (from C-2).** Give `guard_guards_dir_registration` a selftest, in the shape the
  file already uses three times, so the round-trip line cannot be deleted silently.
* **`FU-T444-4` (from C-3).** Rewrite `.softhouse/RESUME.md:52` to name
  `guard_guards_dir_registration` instead of `conformance.sh:3677`, in the merge commit. Same
  remedy as `FU-T431-2` for `fire-program.sh:1406`.
* **`FU-T444-5` (from C-4).** Record in `patterns.md`: paths under `.softhouse/` must be plain
  ASCII, with no backslash, quote, control character or newline — and the three places that
  break otherwise (`guard_guards_dir_registration` member side, its witness side, and
  `guard_dead_path_frontier`'s census, which crashes rather than diagnosing).
* **`FU-T444-6` (from LOW-5).** Either refuse a member carrying more than one `REACHED-BY` row,
  or say in the code that only the first is graded.
* **`FU-T444-7` (from T431's `FU-T431-4`, seconded).** `patterns.md` still has no entry for
  "freeze the drive before you run it". T431 adopted the discipline and I adopted it from T431
  (`sha256 b173219c…` recorded before both of my runs, `chmod a-w` applied); two generations
  have now paid for the lesson and nobody has written the P-number.

# WHAT I CHECKED AND FOUND CLEAN

So that silence is distinguishable from not looking.

0. **T431 stayed inside its grant.** The whole branch touches three places and nothing else:
   `.softhouse/conformance.sh`, `.softhouse/capture/t431-t407-conditions/**` and
   `.softhouse/handoff/T431-t407-conditions.md` — 22 files, `+6824 / −29`, of which
   `conformance.sh` is `+201 / −29` [VERIFIED: `git diff --name-only main...`].
1. **No non-negotiable is touched.** The `conformance.sh` diff contains no arithmetic, no
   floating point, no money, no ledger, no vector, no DEC-n, no contract change, no database
   driver, no pin change [VERIFIED: read the whole diff].
2. **`self_path="${self_stat#*"$CONF_TAB"}"` is correct and fail-closed in every degenerate case
   I could construct.** `git ls-files -s` separates the path with exactly one TAB and C-quotes
   any TAB *inside* a path, so the field split cannot be fooled; if `CONF_TAB` were ever empty
   the expansion returns the whole line, which cannot equal `self_norm`, so the guard refuses.
   A conflicted index makes the pinned lookup multi-line, `self_path` then carries an embedded
   newline and refuses.
3. **Branch ORDER is right and nothing is shadowed** [VERIFIED: read the chain on T431's tree]:
   `-z self_wit` → `self_multi` → self-reference → `! -f typed` → `-z self_norm` →
   **`-z self_stat`** → **round-trip** → `120000` → blob → grep. An empty `self_stat` cannot
   reach a `self_path` comparison, and neither new branch shadows the symlink or blob refusals.
   `X`/`XT`/`XI` are refused by the SYMLINK refusal on the fixed tree, which is the correct
   reason and not an accident.
4. **`CONF_TAB` is spelled once**, beside `CONF_LF`, with the same `printf`/strip idiom, declared
   `local` on the same line — no new global.
5. **No pipeline is introduced.** Both field extractions are parameter expansion (P-57).
6. **Every new branch sets `bad=1` before printing**, and no `warn` prints an
   attacker-controlled string in a shape that could be mistaken for a harness verdict.
7. **The comment hunk is line-count-neutral where it claims to be** (25 → 25); the whole
   `conformance.sh` change is `+201 / −29`.
8. **The healthy population is unchanged** — `population=6 invoked=3 declared=2 reached-by=1
   invoked-by-nothing=0 symlink-members=0` on `main`, on arm `Z` of both drives, and on the merge
   result [VERIFIED: four separate runs].
9. **`guard_pnumber_citations` VERDICT PASS on the merge result** — T431's P-57 and P-80 usages
   match the sentences `patterns.md` defines [VERIFIED].
10. **No new host-state row, no dead-path frontier movement, no fail-open frontier movement, no
    exemption movement, no guard-cost breach in the merge result** [VERIFIED].
11. **The instrument provenance claim holds** — see §6, the frozen-drive sha256.
12. **T431's `## Unverified` section is honest.** Everything in it that I could check was true,
    and the one item I drove (conflicted index) confirms its reasoning while contradicting a
    different sentence in the same commit (C-1).

# WHAT I DID NOT CHECK

* **T431's own two RED clones (`ec285e17`, `e864dd3d`).** They are gone; I did not re-verify the
  SHAs. **[UNVERIFIED by me]** — superseded: I reproduced all four fail-opens on `290d8f84`,
  newer than both.
* **A second git binary, and a genuinely case-SENSITIVE filesystem.** Same bound T404, T407 and
  T431 all recorded. This host is git 2.50.1 with `core.ignorecase=true`. Note that M-1 is a
  *consequence* of case-insensitivity, so a case-sensitive host is where M-1 would NOT reproduce
  — and where a commit carrying it would materialise both files and refuse. **The verdict of
  this guard is therefore host-dependent for that commit, which is itself the objection.**
  **[UNVERIFIED — bound on my search.]**
* **The pinned toolchain.** Every arm ran under the announced FALLBACK toolchain, as T431's did.
  RED and GREEN are like-for-like; neither is graded under the pinned toolchain.
  **[UNVERIFIED for the pinned toolchain.]**
* **Machine contention.** Two of my drives plus other agents' runs shared this host. No guard
  breached its ceiling in the merge bar (worst: `guard_reconciler_ownership` 27 s / 500 s), but
  no timing here is a cost measurement. **[UNVERIFIED as a cost claim.]**
* **`FU-T375-5` (the `DECLARED` direction), `guard_graded_root_is_this_tree`'s short-circuit, and
  the `member_none` branch on a git that genuinely lacks `:(literal)`** — restated from T431's
  list so silence is not read as completion. Not touched by T431 and not driven by me.
