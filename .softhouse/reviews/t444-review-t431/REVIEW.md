# T444 — INDEPENDENT REVIEW of T431 (`softhouse/T431-t407-conditions`)

**Status: PROVISIONAL — the two remaining arm blocks (`NLMEM`/`GITL`/`GITL2`/`2ROW` on both
trees) are still running. The verdict below is stable for everything already driven and will be
finalised, not reversed, unless one of those arms is a live fail-open.**

**PROVISIONAL VERDICT: `APPROVED WITH CONDITIONS`.**

Subject: T431's change to `.softhouse/conformance.sh` inside `guard_guards_dir_registration`
(`C-T407-1`), plus `C-T407-2`, `C-T407-3`, `C-T407-4`. Reviewed as GRADING INFRASTRUCTURE: this
function decides whether every other task in this program passes.

Honesty rule: every material claim is `[VERIFIED: <source>]` or `[UNVERIFIED]`.
Every scratch worktree is under a shared temporary root **taken as an argument** by every
instrument in `evidence/`; no instrument in this review binds a literal shared-temp path to a
name, so none of them adds a row to `HOSTSTATE_PIN_TEMP_ASSIGN_LIST`.

---

## 1. THE HEADLINE — re-derived from git, not from T431's report. IT HOLDS.

T407 prescribed the one-token pin `":(literal)$self_norm"`. T431 reports that the pin **alone
does not close the hole**. I re-derived this from git's behaviour before reading T431's
evidence [VERIFIED: `evidence/01-git-quoting.txt`, git 2.50.1 (Apple Git-155),
`core.ignorecase=true`]:

```
=== ls-files (default quotePath) ===
d/plain.txt
"d/q\".txt"
"d/w\\x.txt"
"d/w\303\251.txt"
"d/\320\266\320\260\320\263\321\201\320\260\320\260\320\273\321\202.txt"
=== ls-files with -c core.quotePath=false ===
d/plain.txt
"d/q\".txt"
"d/w\\x.txt"
d/wé.txt
d/жагсаалт.txt
```

So `git ls-files` C-quotes a non-ASCII byte, a backslash and a double quote, and prints the
result **wrapped in literal double quotes**. `self_norm` is the OUTPUT of a pathspec lookup,
therefore **`self_norm` is a rendering, not a path** — and feeding that rendering back as
`":(literal)$self_norm"` matches **nothing** [VERIFIED: same file, the round-trip section].
`core.quotePath=false` removes the non-ASCII quoting but **not** the backslash or dquote
quoting [VERIFIED: same file] — exactly as T431 states.

**The 8-way necessity matrix, evaluated with the guard's own expressions transcribed verbatim**
[VERIFIED: `evidence/03-necessity-redundancy-matrix.txt`]:

```
--- XQ   typed witness: g/zz/wé.txt      self_norm = ["g/zz/w\303\251.txt"]
        pin=no  empty=no  rt=no  -> ACCEPT
        pin=no  empty=yes rt=no  -> ACCEPT
        pin=yes empty=no  rt=no  -> ACCEPT          <-- THE RATIFIED PIN, AND IT ACCEPTS
        pin=yes empty=yes rt=no  -> ACCEPT          <-- PIN + EMPTY, AND IT STILL ACCEPTS
        pin=no  empty=no  rt=yes -> REFUSE:round-trip
        pin=no  empty=yes rt=yes -> REFUSE:round-trip
        pin=yes empty=no  rt=yes -> REFUSE:round-trip
        pin=yes empty=yes rt=yes -> REFUSE:round-trip
```

**T431's headline is correct and it is a result about this program's own review process: a
remedy an independent reviewer had already approved, and which the driver ratified, was
insufficient, and the insufficiency is not a corner — it is four out of eight configurations.**
The pin is the right *primary* fix (it makes the lookup semantically correct) but it does not,
on its own, close `C-T407-1`. Anyone who had applied T407's prescription and stopped would have
shipped a still-open hole with a review signature on it.

One thing worth adding that T431 does not state: after the fix, `self_norm` reaching the closing
`grep` is **guaranteed to be a real path**, because no C-quoted rendering can round-trip — the
rendering starts with `"`, and `"` is itself a character git quotes, so any tracked file
literally named that rendering renders differently again. That invariant, not the arm count, is
what makes the repair a class fix rather than a spelling fix.

## 2. THE FOUR FAIL-OPENS — reproduced on TODAY's `main`, with my own construction

Driven with my own instrument (`evidence/drive-t444.sh`, different directory leaves, different
member names, written from my reading of the guard), cloning `main` at **`290d8f84`** — *newer*
than either tree T431 measured [VERIFIED: `evidence/10-RED-BEFORE-t444-drive-on-main.txt`].

`T444-X-literal-FAILOPEN` on today's `main` [VERIFIED:
`evidence/11-RED-arm-X-full-bar-on-main.txt`]:

```
conformance:     REACHED-BY .softhouse/guards/zz-t444x/zz-t444x-member.sh — declared in its own header, reached by
conformance:   GUARDS-DIR-REGISTRATION: population=7 invoked=3 declared=2 reached-by=2 invoked-by-nothing=0 symlink-members=0
conformance: reference oracle (…/actuator/health) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

An unwired planted checker, ACCEPTED at `reached-by=2`, vouched for by a symlink to itself,
whole bar exit 0.

*(XT / XI / XQ / XQ0 rows: see §RESULTS below — filled from the running drive.)*

## 3. NECESSITY AND REDUNDANCY — checked BOTH ways, and the answer is sharper than T431's

`evidence/03` gives the full matrix. Reading it:

| line | independently necessary for a REFUSAL? | covered by |
|---|---|---|
| round-trip | **YES** — `XQ` is ACCEPTED in all four `rt=no` configurations | nothing |
| pin | **no** | round-trip catches `X` (the de-magicked lookup returns two lines, so `self_path` carries the decoy path and a newline) |
| empty-result | **no** | round-trip (`self_path` is empty, `self_norm` is not) |

T431 reports exactly this and does not dress it up. **Verified, both directions.**

**The adversarial question: two parts are redundant only because of a neighbour — what happens
when the neighbour moves?** The neighbour that covers for both is the round-trip line, and it is
the one line with no automated arm anywhere in the harness. See condition **C-2**.

I also looked for a case in which the pin is independently necessary on the *healthy* side — a
legitimate witness the pin ACCEPTS and the un-pinned lookup would make round-trip refuse. I could
not construct one: a legitimate witness legitimately named `w[1].txt` is ACCEPTED under all eight
configurations, and one with a colliding honest sibling `w1.txt` is refused as `self_multi` under
all eight, at the FIRST (still-unpinned) lookup [VERIFIED: `evidence/03`, scenarios `LEGG`,
`LEGG2`]. So the pin's justification is correctness of the lookup, not coverage — which is what
T431 says, and I could not improve on it.

## 4. THE CONVERSE RISK — does the fix now REFUSE TOO MUCH? **No. But the tree already did.**

This is the point the brief flagged as a potential MAJOR, so it is driven with the whole bar on
BOTH trees, not modelled.

* `T444-LEGA` — honest member, witness an independent tracked regular ASCII file:
  **ACCEPTED on `main` AND on T431's branch**, exit 0, probe PRESENT,
  `population=7 … reached-by=2 … symlink-members=0` [VERIFIED: both drives].
* `T444-LEGC` — **the same thing with a Cyrillic witness filename `гэрчилгээ.txt`**:
  **REFUSED on `main`** (exit 2, probe ABSENT, `…THAT REACHED-BY WITNESS DOES NOT NAME
  zz-t444c-member.sh`) **and REFUSED on T431's branch** (exit 2, probe ABSENT, the NEW
  `matched NO INDEX ENTRY` branch, printing the C-quoted rendering) [VERIFIED: full-bar
  transcripts on both trees].

**So the over-refusal is PRE-EXISTING and T431 does not cause it.** What T431 changes is the
*message*, from a misleading "that witness does not name the member" — which sends the next
worker to inspect the file's contents — to an accurate one that names the cause. That is an
improvement, not a regression, and **the MAJOR the brief anticipated is NOT realised.**

It is still a real constraint on this program and it is broader than the witness path: a Cyrillic
**directory** under `.softhouse/guards/` additionally makes `guard_dead_path_frontier`'s census
instrument crash — `unreadable corpus member ".softhouse/guards/\321\205\320\260\320\273\321\202/…":
[Errno 2] No such file or directory` [VERIFIED: `T444-LEGM` transcript, on `main`]. It refuses
rather than passing (P-81 respected), but nothing anywhere records that **the harness cannot
grade a tree carrying non-ASCII paths under `.softhouse/`** — in a program whose CLAUDE.md is
about Mongolia. See condition **C-4**.

## 5. THE DISCLOSED BOUNDS — driven, not accepted

*(filled from the running drive — `NLMEM`, `GITL`, `GITL2`, `2ROWH`, `2ROWX`.)*

One bound T431 listed as reasoned-not-driven, I drove: **a conflicted index.** See **C-1** — it
falsifies a sentence T431 wrote into the shipped source.

## 6. THE ROTTED CARDINALS — `C-T407-2`, `C-T407-3`, `C-T407-4`

All verified independently.

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
  The three identifiers actually live at `run_guards` defined `:4165` / called `:4660`,
  `probe_oracle` defined `:4637` / invoked `:4685`, `guard_cost_census` defined `:4106` /
  called `:4215` [VERIFIED: `grep -n` on `main`]. The replacement `grep -n` command regenerates
  the block and cannot go stale.
* **Line-count neutrality holds and the citation it protects still resolves**:
  `patterns.md:3426` cites `conformance.sh:3271`; `sed -n 3271p` prints the same
  `population is EMPTY` refusal on `main`, on T431's tree, **and in the merge result**
  [VERIFIED: all three].
* **`C-T407-4`'s two corrections are true.** `…/t404-t384-conditions/evidence/10-…txt` lines 15
  and 23 both score `marker=NO census=NO … >>> FAIL` [VERIFIED: read the file], and
  `evidence/11-…txt` lines 11 and 14 carry `line 501: r: command not found` and
  `line 521: syntax error near unexpected token 'fi'` [VERIFIED: read the file]. T431's added
  point — that T407's own citation pointed at the wrong directory — is consistent with what I
  found.
* **The freeze claim is checkable and it checks out.** `sha256(drive-t431.sh)` as COMMITTED is
  `f4f0e5845774fe8864019f878868e5aee995f6b60656974457048f7c2283ba2a`, and that is the
  `FROZEN drive: … sha256=` recorded in the headers of **both** `evidence/40` (RED) and
  `evidence/50` (GREEN) [VERIFIED: `shasum -a 256` on the committed blob vs the two headers].
  The committed instrument is byte-identical to the one that produced both transcripts. That is
  a provenance claim reviewers usually cannot check, and this one holds.
* **T431's two new `patterns.md` line citations resolve**: `:1654` is P-57 and `:2775` is P-80
  [VERIFIED]. See LOW-2.

## BAR

**The merge result is the bar that matters, and I built it rather than reasoning about it.**

`git merge origin/softhouse/T431-t407-conditions` onto `main` — **rc=0, no conflict rows from
`git ls-files -u`, clean worktree** [VERIFIED: `evidence/05-BAR-MERGE-RESULT-main-plus-T431.txt`
and the merge log]. T431's argument that the merge is clean because `main`'s only
`conformance.sh` change since its fork is far from its edits is **correct in substance**
(`683c8aff..main` on `conformance.sh` is exactly `EXEMPTION_PIN_LEDGER_WRONGIMPLS=15 → 16`
[VERIFIED: the diff is that one line]) — but I did not accept it, I merged.

| figure | `main` @ `cab6be41` | MERGE RESULT | required |
|---|---|---|---|
| exit | 0 | **0** | 0 |
| `probe = ` line PRESENT (count read BEFORE its value, P-84) | 1 | **1** | ≥1 |
| probe value | `up` | **`up`** | — |
| VERDICT | PASS 46 / 7884 | **PASS — 46 parity vectors, 7884 cells** | unmoved |
| **wrong ledger implementations** | 16 | **16, all 16 died through the harness** | **16** |
| `EXEMPTION_PIN_LEDGER_WRONGIMPLS` | 16 | **16** (at `:4694`) | 16 |
| guards-dir census | `population=6 invoked=3 declared=2 reached-by=1 invoked-by-nothing=0 symlink-members=0` | **identical** | unmoved |
| `deadOccurrences` | 108 | **108** | unmoved |
| dead-path corpus | 1524 | **1525** (+1 = `drive-t431.sh`) | no pin |
| `deadFiles` / `resolving` / `indeterminate` | 75 / 1444 / 117 | **75 / 1444 / 117** | unmoved |
| host-state census | 18 == pinned 18 | **18 == pinned 18** | unmoved |
| exemption grounding | 4 GROUNDED / 0 UNGROUNDED | **4 / 0** | unmoved |
| `guard_guards_dir_registration` cost | — | **1 s / ceiling 60 s**, 0 breaches | under ceiling |
| the three fix lines present | 0/0/0 | **1/1/1** | 1 each |
| `patterns.md:3426` → `conformance.sh:3271` | resolves | **resolves** | resolves |
| tree clean after the run | yes | **yes** | yes |

**`main` is 16 and the merge result is 16.** T431's own tree shows 15 with pin 15 — internally
consistent with its fork point, and the merge takes `main`'s 16 without conflict because T431
never touched that line.

---

## CONDITIONS

*(final ratings and the remaining arms land in the next revision of this file)*

### C-1 (MINOR) — the fix reintroduces the exact "unreachable-by-construction" claim this task exists to punish, and it is measurably false

T431's new `C-T407-3` block says of `member_multi`:

> On any git that HONOURS `:(literal)` — 1.9 and later, i.e. every git this program will meet —
> a literal pathspec matches AT MOST ONE index entry, so THIS BRANCH CANNOT FIRE. Its only
> driven route is R1, which is a SYNTHETIC REVERT … It is deliberately
> unreachable-by-construction.

**Driven false** [VERIFIED: `evidence/02-conflicted-index-literal-pathspec.txt`, git 2.50.1, no
revert of anything]:

```
=== git ls-files -s -- ':(literal)<path>' ===
100644 df967b96… 1	.softhouse/guards/zz/c.sh
100644 351be5bf… 2	.softhouse/guards/zz/c.sh
100644 e45c9c26… 3	.softhouse/guards/zz/c.sh
=== line count === 3
```

A conflicted index carries three stages for ONE path, and `:(literal)` honours the path, not the
stage. The branch has a live, non-synthetic route on a conforming git.

**Direction of failure is safe** — `member_multi` refuses — so there is no hole. The finding is
that the SENTENCE is the same sentence that produced this whole task: `T404` rated
`FU-T404-1` unreachable, `T407` reached it, and T431's headline is that a remedy prescribed on
that reasoning was insufficient. T431 also records the conflicted-index case for the *witness*
side in its own `## Unverified` list, so **two statements in one commit cannot both be true.**

**Remedy (in-grant, one sentence):** replace "THIS BRANCH CANNOT FIRE … unreachable-by-construction"
with "this branch has one known live route on a conforming git — a CONFLICTED INDEX, where
`git ls-files -s` prints one line per stage for a single path (driven, T444) — and it is
fail-closed on it."

### C-2 (MINOR) — the only independently necessary line is the one with no automated arm

The matrix in §3 shows the round-trip test is the sole line that closes `XQ`; the pin and the
empty-result branch are redundant *for refusal*. `conformance.sh` executes **no**
registration-forgery drive — the only capture drive it runs is
`drive-red-ledger-invariants.sh`, via its own declared row [VERIFIED: `grep` for every
`drive-*` reference in `conformance.sh`]. So T431's 18-arm drive is capture-only, and a later
edit that removes the round-trip line takes the whole bar to **exit 0** — which is precisely
what arm `RVQ` measures. Four paragraphs above that line, this same function quotes P-45,
"a guard that only works when someone remembers to run it enforces nothing."

**Remedy of record (choose one, argue it down if you disagree):** (a) wire a red-drive row the
way `guard_ledger_invariants` already does for `drive-red-ledger-invariants.sh`; or (b) the
cheap structural version — a guard that asserts the three lines are present in
`guard_guards_dir_registration` by content, which is what T431 itself did to locate the site.
Not blocking: it is a class-level gap that predates T431 and applies to every refusal in this
family since T375. It is filed here because T431 is the commit that made one of those lines
load-bearing and alone.

### C-3 (LOW→MINOR) — the neutrality analysis checked one citation; a second live one rots

`.softhouse/RESUME.md:52` cites `conformance.sh:3677` for "the witness-side lookup". On today's
`main`, `:3677` **is** that lookup [VERIFIED]; on T431's tree the pinned lookup is at `:3782`
and `:3677` is a comment about blob comparison [VERIFIED]. T431's neutrality argument covered
`patterns.md:3426` only.

A repo-wide sweep of `conformance.sh:NNNN` citations restricted to **live directive files**
(`patterns.md`, `RESUME.md`, `obligations.md`, `gates.md`, `.softhouse/bin/`, `.claude/skills/`,
`docs/`, `CLAUDE.md`) finds exactly **two** citations into or above the changed region — and
T431 protected one and rotted the other [VERIFIED: the sweep is in
`evidence/06-conformance-line-citation-sweep.txt`]. Nothing grades `RESUME.md`, so it does not
redden `main`; and `RESUME.md`'s T431 row is stale anyway now that T431 is complete. **The
finding is the method, not the damage:** "I checked the citation I knew about" is how this file
has now rotted three times.

**Remedy:** in the merge commit, rewrite `RESUME.md:52` to cite
`guard_guards_dir_registration` by name — the same remedy T431 records for `FU-T431-2`.

### C-4 (MINOR) — "plain ASCII paths under `.softhouse/`" is now a printed instruction and still not a recorded constraint

Driven in §4. The refusal is pre-existing and T431 improves the message, so this is not a
condition *against* the change — it is the condition that the constraint T431's new warn text
now instructs workers to obey (`Name a witness with a plain ASCII path`) be written down where
workers read it, together with the second, undocumented consequence: a non-ASCII path under
`.softhouse/guards/` also crashes `guard_dead_path_frontier`'s census.

**Remedy of record:** add the constraint to `patterns.md` (both consequences), and note the
measured repair if anyone wants to lift it — `-c core.quotePath=false` on BOTH witness lookups
un-quotes non-ASCII while still quoting backslash and dquote [VERIFIED: `evidence/01`], so it
narrows the constraint from "no non-ASCII" to "no backslash, quote, control character or
newline" but does not remove it.

### LOW-1 — a wording slip in a bar-figure justification

"The merge is clean: that line is ~850 lines below my lowest edit." `EXEMPTION_PIN_LEDGER_WRONGIMPLS`
is at old `:4548`; T431's **lowest** edited line is `:3164` (distance 1384) and its **last** is
`:3724` (distance 824). The number matches the *last* edit, not the lowest. The merge is clean
regardless — I performed it [VERIFIED].

### LOW-2 — `C-T407-2` argues "have no numbers to grade", then adds two numbers

The replacement text cites `patterns.md:1654` (P-57) and `patterns.md:2775` (P-80). Both resolve
today [VERIFIED]. Neither is graded: `guard_pnumber_citations` matches a cited P-number against
the RULE SENTENCE `patterns.md` defines under that number, and never against a line number
[VERIFIED: read the guard at `:1833`-`:1896`]. `patterns.md` grows every fire.

### LOW-3 — the committed tip was not itself barred

T431's final bar is recorded on `20018d18`; the branch tip is `d459ec82`, which adds
`evidence/60`, `evidence/61` and the handoff. Evidence-only, but the barred tree is not the
merged tree. I barred the **merge of the tip**: EXIT 0 [VERIFIED].

### LOW-4 — the `-f` test now grades a different file from everything downstream

`[ ! -f "$REPO_ROOT/$self_wit" ]` runs on the TYPED spelling. For any magic-prefixed spelling
that is an ordinary relative path the attacker created, and it is NOT the file the mode, blob and
grep tests read. After the fix that is harmless — grading is consistent on `self_norm` — but the
test is decorative for exactly the family that motivated this task, and T404's stated reason for
it has now been measured wrong twice (once by T431 for the backslash route, once here).

---

## WHAT I CHECKED AND FOUND CLEAN

So that silence is distinguishable from not looking:

1. The diff contains **no arithmetic, no floating point, no money, no ledger, no vector, no
   DEC-n, no contract change, no database driver and no pin change** [VERIFIED: read the whole
   `conformance.sh` diff].
2. `self_path="${self_stat#*"$CONF_TAB"}"` is correct and fail-closed in every degenerate case I
   could construct: `git ls-files -s` separates the path with a single TAB and C-quotes any TAB
   *in* a path, so the field split cannot be fooled; if `CONF_TAB` were ever empty the expansion
   returns the whole line, which cannot equal `self_norm`, so the guard refuses.
3. **Branch ORDER is correct.** `-z "$self_stat"` precedes the round-trip test, which precedes
   the `120000` mode test — so an empty `self_stat` cannot reach a `self_path` comparison against
   an empty string, and neither new branch shadows the symlink or blob refusals. Arms `X`/`XT`/`XI`
   are refused by the SYMLINK refusal on the fixed tree (the pin makes the lookup land on the real
   witness, which round-trips), which is the correct reason, not an accident.
4. `CONF_TAB` is spelled once, beside `CONF_LF`, with the same `printf`/strip idiom, and is
   declared `local` on the same line — no new global.
5. **No pipeline is introduced.** Both field extractions are parameter expansion (P-57).
6. The new `warn` blocks print no attacker-controlled string in a way that could be mistaken for
   a harness verdict, and every one sets `bad=1` before printing.
7. The comment block edits are line-count-neutral where they claim to be (25 → 25) and the whole
   diff is `+201/−29` on `conformance.sh` [VERIFIED].
8. **The healthy population is unchanged**: `population=6 invoked=3 declared=2 reached-by=1
   invoked-by-nothing=0 symlink-members=0` on `main`, on the T431 arm `Z`, and on the merge
   result [VERIFIED: three separate runs].
9. `guard_pnumber_citations` VERDICT PASS on the merge result — T431's P-57/P-80 usages match
   the sentences `patterns.md` defines [VERIFIED].
10. No new host-state row, no dead-path frontier movement, no fail-open frontier movement in the
    merge result [VERIFIED].

## WHAT I DID NOT CHECK

* **T431's own two RED clones (`ec285e17`, `e864dd3d`).** They are gone. I did not re-verify that
  those were the SHAs. **[UNVERIFIED by me]** — superseded: I reproduced the fail-opens on
  `290d8f84`, newer than both.
* **A second git binary, and a case-sensitive filesystem.** Same bound T404, T407 and T431 all
  recorded. This host is git 2.50.1, `core.ignorecase=true`. **[UNVERIFIED — a bound on my
  search.]**
* **The pinned toolchain.** Every arm here ran under the announced FALLBACK toolchain, as T431's
  did. RED and GREEN are like-for-like; neither is graded under the pinned toolchain.
  **[UNVERIFIED for the pinned toolchain.]**
* **Machine contention.** Two of my drives and other agents' runs shared this host. No guard
  breached its ceiling in the merge bar (worst `guard_reconciler_ownership` 27 s / 500 s), but no
  timing here is a cost measurement. **[UNVERIFIED as a cost claim.]**
