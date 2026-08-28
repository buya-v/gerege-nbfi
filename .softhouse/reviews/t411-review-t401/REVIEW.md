# T411 — independent review of T401 (`.zsh` census gap)

**VERDICT: APPROVED WITH CONDITIONS.**

T401's central claim is correct and I reproduced it from scratch: the live censuses select
tracked `.sh`/`.py` only, tracked `.zsh` files are invisible to them, and a byte-identical
copy of the canonical TIER1 fail-open is not seen if you name it `.zsh`. Its cost table is
right in **every delta**. Its four options are argued on measurement, not preference. Its
committed bytes are clean.

Three things are wrong, none of them fatal to the conclusion:

* its **diagnosis** of the grep defect is wrong, which sends the follow-up sweep in the
  wrong direction (**F-T411-1**);
* it reports all five of T385's figures as "rotted"; **two of them were wrong when
  written**, which is a different defect with a different remedy (**F-T411-3**);
* one of REQUEST A's ten line citations does not point at what it says (**F-T411-6**).

And I found one thing neither T385 nor T401 looked for: **a live expression in
`conformance.sh` that has never once produced output** (**F-T411-2**).

**Are the requests safe to apply as written? A1–A4 and B: yes, subject to C1 and C2.
C (the dead-path pin): yes, subject to C3. A5: only under the ordering constraint T401
itself states, which I confirm.**

Bar on this branch: **exit 0, probe line present, 46 parity / 7884 cells, deadOccurrences
108, fail-open frontier 11 == pin 11, host-state 18 == pin 18, all 14 wrong ledger
implementations killed, pin 14.** Transcript `evidence/90-bar.txt`.

---

## 1. THE FIVE COUNTS, RE-MEASURED INDEPENDENTLY

Instrument `instruments/10-t411-counts.sh`. Measured from `git ls-tree -r --name-only` at a
**named commit**, never from the working disk. Every alternation is `-E`; every `grep` is
`/usr/bin/grep` spelled absolutely, because in this harness a bare `grep` may or may not be
a ugrep shim depending on how the script was launched (F-T411-1).

Transcripts: `evidence/10-counts-at-1eacb63e.txt`, `evidence/11-counts-at-main.txt`.

| figure | selector | T385 prose | **T411 @ `1eacb63e`** | **T411 @ `main`** | T401 |
|---|---|---|---|---|---|
| tracked `.zsh` | `grep -cE '[.]zsh$'` | 110 | **121** | **121** | 121 ✓ |
| ...under `capture/`+`reviews/` | `grep -cE '^[.]softhouse/(capture\|reviews)/.*[.]zsh$'` | 98 | **109** | **109** | 109 ✓ |
| tracked `.sh` | `grep -cE '[.]sh$'` | 626 | **657** | **657** | 657 ✓ |
| tracked `.py` | `grep -cE '[.]py$'` | 722 | **738** | **738** | 738 ✓ |
| S1 corpus (`.sh`+`.py`) | `grep -cE '([.]sh\|[.]py)$'` | 1348 | **1395** | **1395** | 1395 ✓ |

Cross-checked three ways (summed separately, and via Python `str.endswith`, which shares no
code with the grep path). All agree. **T401's five numbers are exactly right.**

`main` has since advanced past `1eacb63e`; the five figures are unchanged at both.

---

## 2. FINDINGS

### F-T411-1 — MAJOR. The instrument defect is REAL, but T401's diagnosis of it is WRONG, and the correct diagnosis implies a different sweep.

**Reproduced.** `evidence/50-bre-blast-radius.txt` §1.

```
/usr/bin/grep -c '\.sh$\|\.py$'   over 'a.sh','b.py','c.zsh'  ->  1   exit 0
```

Over the real corpus it returns **738** — the `.py` count *alone* — at **exit 0**. T401's
number and its characterisation of the *effect* are confirmed: this is a measuring
instrument that undercounts and reports success, the fail-open shape inside the tool built
to find fail-opens.

**But the stated cause is false.** T401 says a "BRE `\|` silently drops a branch". It does
not:

```
/usr/bin/grep -c '\.sh\|\.py'      -> 2    alternation ALONE is fine
/usr/bin/grep -c '\.py$\|\.sh$'    -> 1    swap the order, the OTHER branch survives
/usr/bin/grep -c '\.sh$\|\.py$'  against the line  a.sh$X   -> 1    <-- the proof
```

The last line settles it. In BSD BRE, **`$` is an anchor only at the END of the whole
pattern**; anywhere earlier it is a **literal dollar character**. So in `A$\|B$` the first
`$` is literal, branch A can never match a line *ending* in A, and the whole pattern
degrades to `B$`. Alternation is not involved.

**Why the distinction matters.** T401's advisory is "assume `\|` is not portable", which
implies the sweep *grep for `\|`*. That sweep both over- and under-reports:

* **76** BRE `\|` sites across the 792 tracked `.sh`/`.zsh` files.
* Of those, **3 are genuinely broken today** (plus 2 that are this defect's own
  documentation, in T401's instrument and mine). An unanchored `\|` is harmless.
  Grepping for `\|` over-reports by ~25×.
* It also **misses** the mirror-image case: **7** sites put `\|` *inside* an `-E`/`-P`
  pattern, where it is a literal pipe — the opposite bug, invisible to a `\|` sweep framed
  as "BRE alternation is unreliable".

**The three genuinely broken committed figures**, all silently dropping their first branch:

| site | pattern | what is lost |
|---|---|---|
| `.softhouse/capture/t238-failopen/instruments/20-run-the-class.sh:45` | `'no hits\|^ *none$\|(none)'` | the `^ *none$` branch is dead — inside the T238 fail-open apparatus itself |
| `.softhouse/reviews/T184-evidence/t184-sweep.sh:18` | `'pass$\|continue'` | the `pass$` branch is dead |
| `.softhouse/reviews/t43-probe/t43_ambient_sites.sh:10` | `'Money.of(getCurrencyData(), [A-Za-z]*)$\|Money.of(...)'` | first branch dead — **this is an ambient-`MathContext` census on a money path** |

The third is the one worth a follow-up: it is a census of ambient rounding sites in
Fineract, and it has been reporting a partial answer.

**There is a second half T401 does not mention at all, and it is the operationally
dangerous one.** In this harness `grep` resolves two different ways:

```
inline in a Bash-tool / interactive shell : a `grep` SHELL FUNCTION shimming to ugrep 7.8.4  -> 1395
`bash script.sh`                          : the function is NOT inherited; /usr/bin/grep     ->  738
```

So a worker who measures a figure **inline** gets the GNU-compatible answer, and the guard
that re-measures it **from a script** gets the BSD answer. The hazard is not "grep is
wrong"; it is that **the author and the grader can run different engines on the same
pattern and neither is told**. Any instrument that says a bare `grep` is asking a question
whose answer depends on how it was launched.

*Drive:* `bash .softhouse/reviews/t411-review-t401/instruments/50-t411-bre-blast-radius.sh`
— §1 prints the six discriminating cases; §2 prints the sweep with the broken sites named.

---

### F-T411-2 — MAJOR (new; neither T385 nor T401 looked here). `conformance.sh:4530` is a dead expression that has never produced a line, and the repo already documented the reason.

BSD `sed` is **stricter** than BSD grep: it does not implement `\|` as alternation *at all*.
It is a literal pipe.

```
printf 'a\nb\n' | /usr/bin/sed -n 's/^\(a\|b\)$/HIT/p'   ->  0 rows
printf 'a|b\n'  | /usr/bin/sed -n 's/^\(a|b\)$/LITERAL/p' ->  LITERAL   <-- matched the literal pipe
```

`.softhouse/conformance.sh:4530` is the only live `sed`+`\|` site in the graded set:

```sh
LC_ALL=C sed -n 's/^\( *ledger \(parity\|oracle-refusal\|inadmissible\|harness errors\).*\)$/\1/p' "$out" >&2
```

Exercised against the shape of output it is meant to summarise, it prints **0 rows where it
should print 3**.

**Severity, stated honestly: this is diagnostic loss, not a fail-open.** It sits in the
`SURVIVED` branch of the wrong-implementation gate, *after* `bad=1` has already been set.
It gates nothing; the gate still fails correctly. What it costs is the evidence line telling
an operator **why** a deliberately-wrong ledger implementation survived. It has never run in
a green bar, which is exactly why nobody has seen it.

Two aggravating details:

* The two sibling expressions that **are** load-bearing (`pfail`/`rfail` → `kills` → the
  KILLED/SURVIVED decision, at `:4519-4520`, located by grepping the sentence not by line
  number) use no `\|` and are **correct**. So the defect is isolated.
* **The repo already knew.** `.softhouse/guards/check-capture-namespace.sh:95` carries a
  comment saying `/usr/bin/sed` on this host "does not implement `\|` in a basic" RE. The
  knowledge was written down in one guard and nothing enforced it anywhere else.

*Drive:* `instruments/50-t411-bre-blast-radius.sh` §3 — demonstrates the sed semantics, then
enumerates every live `sed`+`\|` site and exercises `:4530` against realistic input.

---

### F-T411-3 — MAJOR. Not all five figures "rotted". Three rotted; **two were already wrong when T385 wrote them**, and the cause is that T385's instrument did not count T385's own branch.

T401 presents a single uniform drift column. The history does not support it.
`instruments/12-t411-rot-history.sh`, `evidence/12-rot-history.txt`:

| commit | | `.zsh` | c+r | `.sh` | `.py` | corpus |
|---|---|---|---|---|---|---|
| `3ce7787f` | T385's **first** commit | 117 | 105 | **626** | **722** | **1348** |
| `7c9770e2` | T385's **last** commit | 118 | 106 | 626 | 723 | 1349 |
| `main` | today | 121 | 109 | 657 | 738 | 1395 |
| | **T385's prose claimed** | **110** | **98** | **626** | **722** | **1348** |

`.sh`, `.py` and `corpus` were **exactly right when written** and rotted afterwards — that is
T401's thesis and it holds for three of five.

`.zsh` and `capture+reviews` were **never right at any commit on T385's branch**. Walking
every commit on `main` (`instruments/13-...`, `instruments/14-...`): 110/98 held at 49
commits, and the **last** of them is `b96e4be4 Merge T380-review-t377` — which is precisely
**T385's own merge-base**. T385's branch then added exactly **7** `.zsh` files, all its own
probes (`t385-192-state.zsh`, `t385-multiplicity-drive.zsh`, …). `110 + 7 = 117`.

**T385 quoted the count of its base, and the 7 files it had itself added were the very thing
the sentence was about.** That is not rot; it is an instrument that does not count itself,
and the remedies differ: rot is cured by re-deriving on a schedule, a self-excluding
measurement is cured by making the instrument state its commit *and* read the tree it is
actually standing on. T401's own instrument does print the commit on line 1 — the right fix
— but because it diagnosed the class as rot it did not claim this, and the pattern goes
unrecorded.

---

### F-T411-4 — CONFIRMED, with two additions. "Four censuses" is right **for the live set**, and I derived it independently.

I did not read T401's enumeration before doing my own. Two orthogonal sweeps
(`instruments/20-...`, `instruments/21-...`; evidence `20-`, `21-`):

1. **Reachability.** Transitive closure of `.softhouse/`-rooted `.py`/`.sh` path literals from
   `conformance.sh` → **73 files**. Of those, the bar actually *executes* only
   `50-failopen-lint.py`, `check-pnumber-citations.py`, `run-ownership-matrix.py`, and three
   guards.
2. **Corpus-shape.** Every `endswith((…))` / `ls-files '*.x'` / `git grep -- '*.x'` /
   `--include='*.x'` / `:(glob)` site in the tracked tree.

The live, graded set is exactly T401's four:

| | selector | reached via | blind to `.zsh` |
|---|---|---|---|
| S1 | `f.endswith((".sh", ".py"))` | `conformance.sh:1655` runs `50-failopen-lint.py:211` | yes |
| S2 | `git ls-files '.softhouse/*.py' '.softhouse/*.sh'` | `conformance.sh:2795` → `guards/check-dead-path-frontier.sh` → `census_dead_paths.py:110` | yes |
| S3 | `git grep -l -E "$rw" -- '*.sh' '*.py'` | `conformance.sh:2131` | yes |
| S4 | `:(glob)<guards>/**/*.{sh,py,go}` | `conformance.sh:3267-3269` | yes |

**Addition 1 — two more extension corpora inside `conformance.sh` that T401 does not name:**
`:1284` (`git ls-files -z -- '*.java'`, the Fineract LOC floor) and `:2361`
(`'.softhouse/capture/*/attest/*.disposable'`). Neither can ever match a `.zsh` instrument,
so the conclusion is unaffected — but "there are four" is itself a cardinal, and stating it
without the qualifier *live, instrument-corpus* is the same shape of claim that rotted in
T385. **The right sentence is "four live instrument-corpus selectors", not "four selectors".**

**Addition 2 — the two live guards that are NOT blind, which is why the answer is four and
not six:** `check-pnumber-citations.py:719` and `check-capture-namespace.sh:77` both use a
**bare `git ls-files`** with no extension pathspec. They are the counter-example that shows
the gap is a choice, not a constraint.

**Not a gap today, but a loaded gun:** ~30 **dormant** `.sh`/`.py`-only selectors sit in
closed task grants. Two deserve naming because they are *narrower still* and will be copied:
`census_variable_paths.py:123` selects `.softhouse/*.py` **only** — it misses `.sh` entirely
— and `sweep-t164-selfmatch-guards.py:324` already reads `(".sh", ".zsh", ".bash")`, i.e.
somebody had already solved this once and the fix did not propagate.

---

### F-T411-5 — CONFIRMED. The cost table is right in every delta, and I re-derived the 7 rows rather than reading them.

`instruments/30-t411-cost-rederive.sh`, `evidence/30-cost-rederive.txt`. Widened copies are
materialised in scratch, deleted on exit, residue asserted 0; each patch is `cmp`-verified to
have changed the file, because a `sed` that matched nothing would report a zero delta and read
as *"extending is free"*.

| | shipped → widened | pinned rows | cost |
|---|---|---|---|
| S1 fail-open | corpus 1401 → 1522 | frontier unchanged | **0 new rows** |
| S2 dead-path | corpus 1401 → 1522 | **108 → 115** | **+7 rows, −0** |
| S3 host-state | population +2 | 18 → 18 | **0 new rows** |
| S4 guards-dir | 6 → 6 | unchanged | **0 new rows** |

The **+7 rows are byte-identical to T401's list** — same files, same literals, same order.
I inspected all seven independently: every one is a path the probe **creates** in a scratch
fixture (`print -r -- … > …`), not one it reads expecting it to be there. **None is a
fail-open.** Confirmed.

Absolute figures differ from T401's by 2 (its branch and mine each add instruments that
qualify as repo-wide search instruments). **The deltas — the only stable quantity — agree
exactly.** T401 says this itself and it is correct to.

**One unsourced cardinal to drop, not to trust.** T401 says "the raw count of `NAME=/tmp`
lines in `.zsh` files is 38". With a `/tmp|/var/tmp|/private/tmp` selector I measure **54**.
The *conclusion* is unaffected and independently verified — **0** of them sit inside a
repo-wide search instrument, so the host-state pin does not move — but the 38 is a number
with no selector printed beside it, in a handoff whose subject is numbers with no selector
printed beside them.

**A caveat on "all 7 are benign" that T401 half-raises and should be promoted.** The
classification *"the probe creates it, therefore it is scratch"* is inferred **by reading**,
by one worker, once. Nothing enforces it. T401's §8 follow-up — port the T238 linter's
existing "a path the file itself creates or deletes is scratch" filter into the T316 census —
is the correct fix and would likely take the +7 to +0 *and* shrink the existing 108. It is
rightly a separate task. **It should be filed now, not left as a bullet in a handoff.**

---

### F-T411-6 — MINOR, but blocking for T413. One of REQUEST A's ten line citations does not point at what it claims, and the P-80 restatement list is incomplete.

`instruments/60-t411-citation-check.sh`, `evidence/60-citation-check.txt`. Checked every
`conformance.sh` citation in REQUEST A against the file as it stands now:

* `:2131`, `:2225`, `:3267`, `:3865`, `:1676`, `:1707`, `:3048`, `:3453` — **all accurate.**
* `:3860-3862`, cited as "the comment … restating `'*.sh'`/`'*.py'`/`'*.go'` as the
  population" — **STALE.** Those lines hold a `REFUSED` warn block and contain no population
  restatement.
* REQUEST B's `50-failopen-lint.py:211` and REQUEST C's `census_dead_paths.py:110` are both
  accurate, and the regeneration tool REQUEST C names (`t326-.../10-regen-pin.py`) exists.

Deriving the restatement list by searching rather than inheriting it also turns up **`:3082`,
`:3242`, `:3259`**, which T401 does not list. Those three are *historical narrative* about a
past defect ("the population was `'*.sh'` alone") and **must not** gain `.zsh` — rewriting
them would falsify a record. That is precisely why T413 must derive the list and classify
each hit, not apply a list of line numbers.

---

### F-T411-7 — MINOR. The red drive reaches the right conclusion, but **none of T401's controls exercises the widening**, which is the P-98 defect in its milder form.

T401's controls are `capture/charges/bin/selfcheck.sh` (S1/S2) and `bin/fire-program.sh`
(S3). Both are **`.sh`**. A `.sh` control sits in the corpus in *both* arms; its membership
does not change when the selector widens. So it proves the linter does not refuse
everything — the "refuses everything" half of P-98 — but it says **nothing** about whether
widening the selector adds files *without* adding false rows. On that question the control
is a constant.

The control that tests the widening is a **healthy `.zsh`**: absent from the shipped corpus,
present in the widened one, and still spared. I built that drive rather than re-running
T401's — `instruments/40-t411-discrimination-drive.sh`, `evidence/40-discrimination-drive.txt`.
Bait is never authored: each arm is baited with a **byte copy of a file already on that
arm's own pinned frontier**, extension as the only difference. Real index untouched (scratch
`GIT_INDEX_FILE`), teardown asserts residue 0.

```
PASS  S1 shipped: bait INVISIBLE (=0)      PASS  S1 widened: bait CAUGHT (=1)
PASS  S2 shipped: bait INVISIBLE (=0)      PASS  S2 widened: bait CAUGHT (=1 row)
PASS  control spared in ALL FOUR arms      control IS in the widened corpus (3/3 planted files)
DRIVE: PASS -- the widening discriminates on CONTENT, not on extension.
```

The S2 bait catch carries its literal, so the arm is not counting coincidences:

```
.../bait-deadpath.zsh | .softhouse/tasks.json.t288.tmp
```

**T401's conclusion is right; its drive under-proves it.** Given the widening is about to be
applied to live selectors, the stronger drive is worth having on the record — and this is it.

*(For the record: T401 correctly uses a **different bait per arm**, because the canonical
TIER1 fail-open carries no dead `.softhouse/`-rooted literal and therefore cannot bait S2 at
all. My first attempt made that mistake and the drive caught it. Credit where due.)*

---

### F-T411-8 — MAJOR, governance, not technical. T401 was merged to `main` **while this review was in flight**.

My dispatch commit `442bf52e` reads "T401 held for review, T411 dispatched". T401 is now an
**ancestor of `main`**, merged at `842607fc Merge T401`, recorded at `108b9821`.

**Substantively harmless, and I say so plainly:** T401's diff is purely additive evidence and
instruments, it applied no live change by design, and its committed bytes are clean
(F-T411-9). Nothing on `main` is worse for it. But the review was then not a gate on the
merge, and had I found a defect in its committed instruments it would already be shipped. The
requests themselves — the part that touches live census selectors — remain unapplied and are
T413's, so the conditions below still bite where it matters.

---

### F-T411-9 — CONFIRMED, and the candidate pattern is real. T401's committed bytes carry **zero** residue of its four self-inflicted reddenings.

Run against the merged tree: T401's grant lints **TIER1 0, TIER1B 0, TIER2 0, TIER3 0 —
PASS**, and the dead-path census returns **0 rows** naming `t401`. All four self-reddenings
really were repaired before it landed.

**On the candidate pattern — it is real, it is distinct, and I have independent evidence for
it, but T401 has named the wrong half of it.**

T401 proposes: *an example in a comment is a graded row — the census reads bytes, it does not
know prose from intent.* That is real and it is **not** covered by any existing numbered
pattern: P-80 is cardinal restatement, P-84 is presence-before-value, P-86 is grep-the-sentence.
None of them says that illustrative prose enters a graded corpus. **Recommend it be recorded.**

But the four instances T401 lists and the defect that actually recurs are two different
things. T401's four were all *dead-path literals in prose*. Writing this review I
reintroduced a **different** shape — `… | grep X || echo "(none)"`, printing a reassuring
negative off a pipeline exit status — **three separate times**, in instruments whose entire
purpose is to detect that shape, each time caught by the T238 linter (frontier 12 vs pin 11,
twice; the third caught by the bar itself). I have left all three in the branch history
rather than tidying them away.

Two lessons that belong with the pattern:

1. **The idiom is not carelessness, it is the default way a shell author writes "show me the
   hits".** Any remedy that relies on authors remembering will fail. The linter is the
   remedy, and it works.
2. **The fail-open linter grades the INDEX (`git ls-files`), so a worker's own instrument is
   ungraded until it is committed.** My instrument 30 passed a scoped lint while untracked
   and went TIER2 the instant I committed it. A worker who lints before committing gets a
   green that means nothing. That is worth a line in the pattern too.

---

## 3. THE DECISION (item 5) — both rejections are argued on measurement, and the risk posture is right

* **(b) report-only first — rejected.** Sound. Report-only would require changing T238's and
  T316's instruments *and* `conformance.sh` — the full serialisation cost of option (a) — to
  produce a number that is already published with its frontier diff and its 7 rows inspected.
  The one thing it buys is that it cannot redden the bar, and the measurement shows (a) cannot
  either, because the pin moves in the same commit. **One qualification T401 does not make:**
  report-only's real benefit is decoupling the *selector* move from the *pin* move, so a
  botched pin regeneration cannot redden anything. That risk is small only because P-83
  requires the pin to be regenerated **by running** the tool rather than typed — which is
  condition C3 below. The argument survives, but it rests on C3 being enforced.
* **(c) convert the 121 `.zsh` to `.sh` — rejected.** Sound, and on the strongest ground of
  the four: the renames would break every handoff, review and pin row naming those paths by
  path, which **manufactures dead-path rows — the guard that motivated the change would go red
  from the change**. I verified the shape of that claim: the 7 new rows are already
  path-literal references into `.zsh` files, and 121 renames would multiply that class. The
  zsh-specific idioms (`print -r --`, `${(f)…}`, `zstyle`) are real and I confirmed they are
  what the probe corpus uses.
* **"Extend all four at once" — the right posture.** Three of four are independently verified
  free; only S2 moves, by +7, in the same commit as its regenerated pin. The one real hazard
  is the A5-before-B ordering, which T401 identifies itself and I confirm below.

---

## 4. CONDITIONS — each drivable

**C1 (BLOCKING, ordering).** **A5 must not land before or without REQUEST B.** A5 changes the
sentence `conformance.sh` prints *on behalf of a linter it does not own*. If it lands first,
`conformance.sh` prints a coverage claim the selector does not have — the exact defect T358
repaired at `:3082`, and that repair's own comment is still in the file three lines from
where A5 edits. A1–A4 are independent of B and may land alone.
*Drive:* apply A5 without B, run the bar, and confirm the printed corpus sentence names
`.zsh` while `50-failopen-lint.py` still selects `.sh`/`.py`.

**C2 (BLOCKING, F-T411-6).** **T413 must locate every edit site by grepping the sentence, not
by T401's line numbers**, and must derive the P-80 restatement list rather than inherit it.
`:3860-3862` is already stale, and `:3082`, `:3242`, `:3259` are restatements T401 does not
list which **must not** be changed because they are historical narrative about a past defect.
`conformance.sh` is under concurrent edit by T404; every line number in REQUEST A is stale the
moment T404 commits.
*Drive:* re-run `instruments/60-t411-citation-check.sh` immediately before applying; it fails
loudly on any citation that has moved.

**C3 (BLOCKING, REQUEST C).** The dead-path pin must be **regenerated by running**
`capture/t326-frontier-host-state/instruments/10-regen-pin.py` against the widened census, in
the **same commit** as the selector change — never by pasting the 7-row block from T401's §3
or from §F-T411-5 of this review. Both blocks are cost statements for a reviewer, not pins.
The pin header must record that these 7 arrived **by widening, not by regression**, so a
future reader can tell "7 we declined to repair" from "7 that were always counted".
*Drive:* `git diff` the pin and confirm the selector change and the pin change are in one
commit; confirm the pin's 7 new rows match the census output byte-for-byte.

**C4 (SHOULD, F-T411-2).** While T404 holds `conformance.sh`, repair `:4530` — replace the
BRE `\|` alternation with either an ERE (`sed -E`) or three separate expressions. It is a
one-line fix in a file already open, and leaving a known-dead diagnostic in the
wrong-implementation gate because it "only fires on failure" is how a red run loses its
evidence.
*Drive:* `evidence/50-bre-blast-radius.txt` §3 exercises the expression against realistic
input and prints 0 where it should print 3; re-run after the fix and it prints 3.

**C5 (SHOULD, F-T411-1).** The portability note this program carries must say the **correct**
rule, or the next worker sweeps for the wrong thing. The rule is: *in a BSD BRE, `^` and `$`
are anchors only at the pattern boundary — anywhere else they are literal characters — and
BSD `sed` does not implement `\|` at all.* T401's handoff §1 states the wrong cause and is
already on `main`; it should be corrected in place. The 3 broken sites in F-T411-1 should be
filed, with `t43_ambient_sites.sh:10` prioritised because it is a money-path census.

**C6 (SHOULD, F-T411-5).** File the T316-adopts-the-T238-scratch-filter task now. It is the
fix that makes REQUEST C's +7 unnecessary and probably shrinks the existing 108; leaving it
as a bullet in a merged handoff is how it gets lost.

**C7 (NOTE, F-T411-4).** When A2/A4 rewrite the printed selectors, say **"four live
instrument-corpus selectors"**, not "four selectors" — `conformance.sh` contains two further
extension corpora (`*.java` at `:1284`, `*.disposable` at `:2361`) that the unqualified claim
silently contradicts.

---

## 5. WHAT I DID NOT VERIFY

* **S3 and S4 end to end.** Like T401, I drove them at **selector** level only, because the
  enclosing guards are spelled inside the T404-held file and running them end to end would
  mean editing it. What is proven is **reach and pin-neutrality**; what is not proven is the
  enclosing guard's full behaviour once the population grows. T401 states this limit itself
  and it is honestly stated.
* **The 108 existing dead-path rows.** I re-derived the +7 and inspected those; I did not
  re-inspect the pinned 108. T401's observation that an unknown share of them are also
  probe-created scratch is plausible and unmeasured — that is C6's job.
* **Nothing here touches money, the ledger, the schema, the oracle or any vector.** No
  floating point, no capture, no driver. Every instrument only reads, except the drive, whose
  writes go to a scratch `GIT_INDEX_FILE` and a scratch directory with asserted teardown.

---

## 6. BAR

`bash .softhouse/conformance.sh` from a clean tree after `git add -A` and commit —
`evidence/90-bar.txt`.

```
BAR EXIT = 0
probe line present (grep -c 'probe = ') = 1        reference oracle probe = up
parity vectors            PASS 46   FAIL 0
cells compared            7884 graded
fail-open frontier        11, pinned at 11
host-state census         18, pinned at 18
T316-DEADPATH-CENSUS      deadOccurrences=108
wrong ledger impls        14 discovered, pinned 14, all 14 KILLED
P-number citations        VERDICT PASS
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

Baseline held exactly. The bar went red twice during this task, both times on my own
instruments and both times correctly (F-T411-9); both are repaired and the transcript above
is from the final tree.
