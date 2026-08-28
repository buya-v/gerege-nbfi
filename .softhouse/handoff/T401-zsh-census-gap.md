# T401 — F-T385-4: the censuses read `.sh`/`.py` only, and `.zsh` is invisible

Branch `softhouse/T401-zsh-census-gap`. Grant `.softhouse/capture/t401-zsh-census-gap/`.
Bar on the final tree: **exit 0, probe line present (`grep -c 'probe = '` = 1), 46 parity /
7884 cells, `deadOccurrences 108`, fail-open frontier 11 == pin 11, host-state 18 == pin 18,
all 14 wrong ledger implementations killed.** Transcript: `evidence/50-bar.txt`.

`conformance.sh` was **not edited** — it is held by T404. Everything below that touches it is a
REQUEST, driven red first.

---

## 1. THE FOUR COUNTS, RE-MEASURED. ALL FIVE OF T385'S FIGURES HAVE ROTTED.

Instrument `instruments/10-measure-counts.sh`. Two transcripts, both committed:
`evidence/10-counts-at-dispatch.txt` (basis commit `1eacb63e`) and `evidence/10-counts.txt`
(the final tree). Selector printed beside every figure. Whole repo, `git ls-files` (tracked only, the index — not the disk).

**The basis commit matters and is stated.** The table below is measured at **`1eacb63e`**, the
fire iter4 dispatch commit — the tree T385 was looking at, so the drift column is a like-for-like
comparison. This task then committed 5 instruments of its own, so the *final* tree reads
`.sh` 662, `.py` 739, `.zsh` **121 (unchanged — I added none)**. Both transcripts are in
`evidence/` so the two readings cannot be confused for a disagreement. Quoting a corpus cardinal
without its commit is the defect this section is about; the transcript prints the commit on
line 1 of every run.

| what | T385's prose | **T401 measured** | drift |
|---|---|---|---|
| tracked `.zsh`, whole repo | 110 | **121** | +11 |
| ...under `capture/` + `reviews/` | 98 | **109** | +11 |
| tracked `.sh` | 626 | **657** | +31 |
| tracked `.py` | 722 | **738** | +16 |
| fail-open linter `corpus` | 1348 | **1395** | +47 |

Where I looked, and the two things worth knowing that the prose did not say:

* `git ls-files | grep -cE '\.zsh$'` over the whole repo → **121**, and **all 121 are under
  `.softhouse/`** — 62 `capture/`, 47 `reviews/`, 11 `handoff/`, 1 `bin/`, **0 in
  `.softhouse/guards/`**. Zero `.zsh` outside `.softhouse/`.
* `657 + 738 = 1395` exactly, and **1395 is also the count of `git ls-files '.softhouse/*.py'
  '.softhouse/*.sh'`** — i.e. *every* tracked `.sh`/`.py` in this repository is under
  `.softhouse/`. The two censuses have different selectors but, today, identical corpora. That
  is a coincidence of the current tree, not a property, and the request below does not rely on it.
* The dead-path pathspec has **no `:(glob)` magic**, so `*` crosses `/` and it is already
  any-depth. Asserted by running it (section D of the transcript: 738 rows contain `/`, 0 rows
  are at depth 1), not assumed.

**A measurement defect found while building the instrument, worth more than the counts.**
`grep -c '\.sh$\|\.py$'` returns **738** — the `.py` count *alone* — under the `/usr/bin/grep` a
non-interactive `bash` gets here, and **1395** under the interactive zsh's `grep` (ugrep 7.8.4).
A BRE `\|` that silently drops a branch and exits 0 is a measuring instrument that
**undercounts and reports success**: the fail-open shape, inside the tool built to find
fail-opens. Every alternation in this task's instruments is `-E`. Anyone re-deriving a census
figure on macOS should assume `\|` is not portable.

---

## 2. THERE ARE **FOUR** `.sh`/`.py`-ONLY SELECTORS, NOT TWO — AND TWO OF THEM ARE IN `conformance.sh`

`instruments/30-conformance-own-selectors.sh`, transcript `evidence/30-conformance-selectors.txt`.
The transliterated regexes are **byte-asserted against the live `conformance.sh`** before any
figure prints; a drifted selector refuses rather than reporting a number about a different search.

| | selector | lives in | reaches `.zsh`? |
|---|---|---|---|
| **S1** | `f.endswith((".sh", ".py"))` | `capture/t238-failopen/instruments/50-failopen-lint.py:210-211` | no |
| **S2** | `git ls-files '.softhouse/*.py' '.softhouse/*.sh'` | `capture/t316-dead-path-guards/census_dead_paths.py:110` | no |
| **S3** | `git grep -l -E "$rw" -- '*.sh' '*.py'` | **`.softhouse/conformance.sh:2131`** | no |
| **S4** | `:(glob)<guards>/**/*.{sh,py,go}` | **`.softhouse/conformance.sh:3267-3269`** | no |

F-T385-4 named S1 and S2. S3 is the host-state census — it hunts `NAME=/tmp/…` assignments
*inside repo-wide search instruments*, and **two tracked `.zsh` files are repo-wide search
instruments today**, so it has the same blindness for the same reason. S4 is the unwired-checker
census; there are 0 `.zsh` under `.softhouse/guards` today, so widening it is pure insurance.

Note the ownership split, because it decides what this task could and could not do: **S1 and S2
are not in `conformance.sh` at all.** A `conformance.sh` patch cannot fix them. It can only stop
`conformance.sh` from *printing* a coverage claim those two selectors do not have.

---

## 3. WHAT IT COSTS. MEASURED, NOT ARGUED.

`instruments/20-cost-of-extending.sh` — runs each census twice, shipped selector and
one-token-wider selector, and diffs the frontiers. The widened copies are materialised in
scratch and **never committed**; a committed copy would enter both corpora and move the very
figures it exists to measure. A `sed` that matched nothing is a silent no-op that would report a
zero delta and read as *"extending is free"*, so both patches are `cmp`-verified to have changed
the file and an unchanged copy is a refusal.

| | corpus | pinned rows | **cost** |
|---|---|---|---|
| **S1** fail-open | 1401 → 1522 | frontier **11 → 11** | **ZERO new rows** |
| **S2** dead-path | 1401 → 1522 | dead **108 → 115** | **+7 rows in 5 files** |
| **S3** host-state | population 163 → 165 | **18 → 18** | **ZERO new rows** |
| **S4** guards-dir | 0 `.zsh` in `guards/` | unchanged | **ZERO new rows** |

**Three of the four widenings are free. Only the dead-path pin moves, by 7 rows.** The
"reddens the bar in a single step" risk in the task statement is real for S2 and measured to be
absent for S1, S3 and S4.

Two figures that look alarming and are not: the fail-open corpus gains 121 files but **146 → 148**
inspected instruments (only 2 `.zsh` run repo-wide searches), and the raw count of `NAME=/tmp`
lines in `.zsh` files is 38 — but **0** of them are inside a repo-wide search instrument, so the
host-state pin does not move. S3's own population restriction already does that filtering.

### The 7 rows, each inspected by hand

`instruments/25-new-deadpath-rows.py`, output `evidence/25-new-deadpath-rows.txt`. Exact pin
spelling (`FILE | LITERAL`), added 7, **removed 0** — a widening may only add, and the
instrument fails if it does not.

```
capture/t324-worktree-prune-skipbit/instruments/10-skipbit-taxonomy-probe.zsh | .softhouse/handoff-draft.md
capture/t324-worktree-prune-skipbit/instruments/20-blindspot-guard-drive.zsh  | .softhouse/handoff-draft.md
capture/t353-t342-conditions/bin/probe-scratch.zsh                            | .softhouse/x
reviews/t202-probe/green-Tb.zsh                                               | .softhouse/LOCK.bak
reviews/t202-probe/green-Tb.zsh                                               | .softhouse/LOCKDIR/f.md
reviews/t202-probe/green-Tb.zsh                                               | .softhouse/LOCKED_STATE.md
reviews/t202-probe/red-Tb.zsh                                                 | .softhouse/vector.json
```

T316's header says a dead literal "is a SMELL that must be inspected once, by a human, and then
either repaired or pinned with its reason." I inspected all seven. **Every one is a file the
probe CREATES in a scratch fixture repository**, never one it reads expecting it to be there:

* `green-Tb.zsh:44-46` — `print -r -- "genuine work" > .softhouse/LOCKED_STATE.md`, same for
  `LOCK.bak`, and `mkdir -p .softhouse/LOCKDIR; print -r -- w > .softhouse/LOCKDIR/f.md`.
* `red-Tb.zsh:25` — `print -r -- "vector capture" > "$S/.softhouse/vector.json"`.
* `probe-scratch.zsh:14` — `print -r -- x > "$S/repo/.softhouse/x"`.
* both `t324` probes — `print -r -- 'PLAIN UNTRACKED WORKER OUTPUT' > "$1/.softhouse/handoff-draft.md"`,
  the fixture for the "plain untracked file" taxonomy row.

**None is fail-open. All 7 are the same benign class**, and that class has a name: the T238
linter already filters "a path the file itself creates or deletes is scratch rather than corpus",
and **the T316 dead-path census has no such filter**. See §7 — that is a better fix than pinning
them, and it is a separate task.

---

## 4. THE OPTIONS, COSTED

**(a) Extend and re-pin in ONE commit — CHOSEN.** Cost: S1/S3/S4 free; S2's pin goes 108 → 115,
regenerated by *running* `capture/t326-frontier-host-state/instruments/10-regen-pin.py` against
the widened census (P-83 — the pin file's own header already says "DERIVED … NEVER TYPED", so
this is the mechanism the pin was built for, not a new one). Buys: 121 files enter the fail-open
corpus at zero pin cost, and the class "a fail-open instrument in the language new instruments
are written in" closes on the next commit rather than the next fire.

**(b) Report-only mode first, publish the count.** Rejected, and not because it is timid —
because **this task has already published the count**, with the frontier diff, the 7 rows by
path and literal, and each one inspected. Report-only mode would require code changes to
T238's and T316's instruments *and* to `conformance.sh` — i.e. the full serialisation cost of
option (a) — to produce a number that is in this document. It buys one thing option (a) does not:
it cannot redden the bar. But the measurement says option (a) cannot redden the bar either, since
the pin moves in the same commit. Paying the serialisation twice for a number already in hand is
the "switched off within two fires" outcome T323 refused for T304's destructive-site census,
approached from the other side.

**(c) Rule that driving instruments must be `.sh`/`.py`, convert the 121.** Rejected on cost and
on second-order damage. 121 renames across at least 8 task grants (`t202`, `t279`, `t324`,
`t353`, `bin/`, …); every handoff, review and pin row naming one of them by path breaks, which
**manufactures dead-path rows** — the guard that motivated the change would go red from the
change. And the `.zsh` files are zsh for a reason: `print -r --`, `${(f)…}`, `zstyle` and the
worktree-prune skip-bit probes are zsh-specific. Rewriting a working probe corpus in a second
language to satisfy a glob is the tail wagging the dog. The rule also does not survive contact:
nothing stops the next worker writing `.zsh`, so it needs a guard — and the guard is a widened
selector, i.e. option (a) plus 121 renames.

**(d) Do nothing.** The measured status quo is that a byte-identical copy of
`sweep-ORIGINAL.sh` — the canonical TIER1 fail-open, the one this whole apparatus was built
around — is **invisible** if you name it `.zsh`. §5 shows it.

---

## 5. THE RED DRIVE — planted `.zsh`, with a healthy control

`instruments/40-red-drive-planted-zsh.sh` (S1, S2, running the real instruments) and
`instruments/45-red-drive-conformance-selectors.sh` (S3, S4, at selector level).
Transcripts `evidence/40-red-drive.txt`, `evidence/45-red-drive-s3-s4.txt`. Both **PASSED**.

**The bait is a runtime copy of a file already on the frontier, not authored bait**, and the
extension is the *only* difference from the original — so a difference in verdict cannot be
attributed to anything else. Why it is done that way is §6.

| arm | selector | result |
|---|---|---|
| 1 | S1 shipped | corpus 1401, frontier 11, **0 rows naming the bait — BLIND** |
| 2 | S1 widened | corpus 1525, frontier 12, **`FAILOPEN-FRONTIER TIER1 …/bait-failopen.zsh`**, control **not** flagged |
| 3 | S2 shipped | `deadOccurrences=108`, **0 rows naming the bait — BLIND** |
| 4 | S2 widened | `deadOccurrences=118`, bait caught with its literal, control **not** counted dead |
| A | S3 shipped | planted host-state site: **0 in population, 0 rows — BLIND** |
| B | S3 widened | `bait-hoststate.zsh:31:SCRATCH=/tmp/t116-harness` censused; control **enters the population and produces no row** |
| A | S4 shipped | unwired `.zsh` checker in `guards/`: **0 in population — BLIND** |
| B | S4 widened | **1 in population** — must be INVOKED, DECLARED or REACHED-BY |

Bait and controls, all chosen at runtime from the tree:

* **BAIT-FO** `capture/t238-failopen/evidence/red-drive/sweep-ORIGINAL.sh` — the canonical pinned
  TIER1. Rename it `.zsh` and the shipped linter cannot see it.
* **BAIT-DP** `bin/fire-program.sh` (names `.softhouse/tasks.json.t288.tmp`).
* **BAIT-HS** `capture/t116-familyb-promotion/src/run-harness-mutations-t116.sh` — already on the
  host-state pin.
* **CONTROL (S1/S2)** `capture/charges/bin/selfcheck.sh` — a repo-wide search instrument on
  *neither* list, so "not flagged" is not trivially true.
* **CONTROL (S3)** `bin/fire-program.sh` — asserted to **enter** the widened population and still
  produce no row, so the widening is shown to discriminate on the assignment, not on the extension.
  A control that never entered the population would make "no row" vacuous, and the drive fails if so.

The real index is never touched: copies go into a `GIT_INDEX_FILE` clone that the censuses
inherit, and teardown asserts residue 0.

**Stated limit.** S3 and S4 are driven at *selector* level, because the guards that use them are
spelled inside the T404-held file and running them end to end would mean editing it. What is
proven is reach; what is not proven is the enclosing guard's full behaviour. That is why they are
a request and not a merge.

---

## 6. FOUR TIMES THIS TASK REDDENED THE BAR WITH ITS OWN PROSE

Recorded because it is the same defect three times and it generalises. Each was caught by a
guard, none reached `main`.

1. `10-measure-counts.sh` spelled one illustrative fake path in a comment to *explain* the
   selector. `deadOccurrences 108 → 109`.
2. `20-cost-of-extending.sh` spelled its untracked scratch target as one `.softhouse/`-rooted
   literal — then spelled it **again inside the comment explaining defect 1**. Two more rows.
3. `40-red-drive-planted-zsh.sh` wrote its bait with `cat <<'PLANTED'` heredocs under a comment
   reading *"the DEFECT LIVES IN SCRATCH, never in a tracked file"*. **That comment was false**:
   a heredoc body is text in the tracked file. The bar came back
   `THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER … + TIER1 …/40-red-drive-planted-zsh.sh`
   and `T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=108 added=2 removed=0` — the instrument
   written to demonstrate a blind census became a genuine TIER1 fail-open row.
4. `45-red-drive-conformance-selectors.sh` spelled its scratch directory inside the guards
   directory as one `.softhouse/`-rooted literal. Frontier 108 → 109. This was **after** the
   comment in defect 2 explaining defect 2, in the same task, by the same author.

**Candidate pattern — AN EXAMPLE IN A COMMENT IS A GRADED ROW. The census reads bytes; it does
not know prose from intent, and it is right not to.** The remedies that work: assemble scratch
paths from a variable whose prefix resolves (`"$G/<name>"`), write example paths with a
placeholder (`<grant-dir>/<name>`) so they classify INDETERMINATE, and **never** author bait —
copy a file that is already on the frontier and change only its extension. The last is also the
better experiment.

---

## 7. THE REQUESTS

### REQUEST A — `conformance.sh`, to **T404** (holder this wave)

Two selector widenings and three printed-claim corrections. Driven red in
`evidence/45-red-drive-s3-s4.txt`. **Zero new pinned rows in both censuses** — neither
`HOSTSTATE_PIN_TEMP_ASSIGN_LIST` nor the guards-dir declared table changes.

**A1 — S3 host-state selector, `:2131`**

```diff
-  ( cd "$REPO_ROOT" || exit 9; LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' ) >"$list.raw" 2>/dev/null
+  ( cd "$REPO_ROOT" || exit 9; LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' '*.zsh' ) >"$list.raw" 2>/dev/null
```

**A2 — S3 printed selector, `:2225`** (P-70: the printed selector must be the selector)

```diff
-  say "conformance:   read from git grep over tracked *.sh/*.py under $REPO_ROOT; sites that assign a"
+  say "conformance:   read from git grep over tracked *.sh/*.py/*.zsh under $REPO_ROOT; sites that assign a"
```

**A3 — S4 guards-dir population, `:3266-3269`**

```diff
   pop="$( cd "$REPO_ROOT" 2>/dev/null && git ls-files -- \
             ":(glob)$gdrel/"'**/*.sh' \
             ":(glob)$gdrel/"'**/*.py' \
-            ":(glob)$gdrel/"'**/*.go' 2>/dev/null )"
+            ":(glob)$gdrel/"'**/*.go' \
+            ":(glob)$gdrel/"'**/*.zsh' 2>/dev/null )"
```

**A4 — S4 printed selector, `:3865`**

```diff
-  say "conformance:   (selector: git ls-files with ':(glob)' magic over the TRACKED '*.sh', '*.py'"
-  say "conformance:   and '*.go' files at ANY DEPTH under $gdrel, from \$REPO_ROOT. NOT closed over"
+  say "conformance:   (selector: git ls-files with ':(glob)' magic over the TRACKED '*.sh', '*.py',"
+  say "conformance:   '*.go' and '*.zsh' files at ANY DEPTH under $gdrel, from \$REPO_ROOT. NOT closed over"
```

The two prose blocks at `:3048` and `:3453` and the comment at `:3860-3862` restate
`'*.sh' / '*.py' / '*.go'` as the population and must gain `.zsh` **in the same commit** —
P-80, a cardinal (or a class) rots in every place it was restated.

**A5 — the fail-open claim `conformance.sh` prints on behalf of a linter it does not own,
`:1676` and `:1707`.** These are the only lines here that describe **S1**, whose selector is in
T238's file. **They must move only when REQUEST B moves**, and this is the one ordering
constraint in this handoff:

```diff
-    warn "conformance: the fail-open linter reports a corpus of $corpus tracked .sh/.py files."
+    warn "conformance: the fail-open linter reports a corpus of $corpus tracked .sh/.py/.zsh files."
...
-  say "conformance: CENSUS fail-open instruments — inspected $corpus tracked .sh/.py file(s) under"
+  say "conformance: CENSUS fail-open instruments — inspected $corpus tracked .sh/.py/.zsh file(s) under"
```

If A5 lands **before** B, `conformance.sh` prints a coverage claim that is false — exactly the
defect T358 repaired at `:3082` ("the population was `'*.sh'` alone while the handoff claimed a
fourth unwired checker cannot land"). **If B is not taken, A5 must not be taken.** A1–A4 are
independent of B and may land alone.

### REQUEST B — `capture/t238-failopen/instruments/50-failopen-lint.py` (T238's grant)

Zero new frontier rows; `FAILOPEN_PIN_FILE_LIST` does not change.

```diff
 files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True)
-         .stdout.split("\n") if f.endswith((".sh", ".py"))]
+         .stdout.split("\n") if f.endswith((".sh", ".py", ".zsh"))]
 if not files:
-    print("LINT ABORT (2): corpus reachable but contains ZERO .sh/.py files. "
+    print("LINT ABORT (2): corpus reachable but contains ZERO .sh/.py/.zsh files. "
           "Linting nothing proves nothing (P-35).", file=sys.stderr)
```
```diff
-print("corpus    : %d tracked .sh/.py; %d are repo-wide search instruments" % (len(files), inspected))
+print("corpus    : %d tracked .sh/.py/.zsh; %d are repo-wide search instruments" % (len(files), inspected))
```
plus the SCOPE line in the module docstring at `:51`.

**`conformance.sh:1673` parses that printed line** with
`sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p'` — the capture ends before `tracked`, so
it survives. Verified by running the widened linter's output through that exact `sed`: it parses,
yielding the widened corpus figure (1522 on the final tree). The corpus cardinal moves with
the tree on every commit; the stable quantities are the DELTAS -- +121 corpus, +0 frontier.

### REQUEST C — `capture/t316-dead-path-guards/census_dead_paths.py` + the pin (T316's grant)

The only one with a cost. **Selector and pin must move in ONE commit**, and the pin must be
**regenerated by running** `capture/t326-frontier-host-state/instruments/10-regen-pin.py`, never
by pasting the block in §3 — that block is the cost statement for the reviewer, not a pin.

```diff
     proc = subprocess.run(
-        ["git", "ls-files", ".softhouse/*.py", ".softhouse/*.sh"],
+        ["git", "ls-files", ".softhouse/*.py", ".softhouse/*.sh", ".softhouse/*.zsh"],
         cwd=str(root), capture_output=True, text=True)
```
```diff
-    print("  corpus     : git ls-files '.softhouse/*.py' '.softhouse/*.sh'   -> %d tracked file(s)"
+    print("  corpus     : git ls-files '.softhouse/*.py' '.softhouse/*.sh' '.softhouse/*.zsh'   -> %d tracked file(s)"
```
plus the docstring at `:11`.

**The pin header must say these 7 rows arrived by WIDENING, not by regression.** T323's rule is
"a `+` row is a NEW site: REPAIR it rather than pinning it." These 7 are not new sites — they are
old sites becoming visible, all 7 benign by inspection (§3). Merged silently, a future reader
cannot tell "7 we declined to repair" from "7 that were always counted". The pin already carries
T326's precedent for exactly this kind of annotated re-baseline.

**Projected frontier delta if A + B + C all land:**

```
fail-open frontier      11  ->  11    (pin unchanged)
host-state census       18  ->  18    (pin unchanged)
guards-dir population    6  ->   6    (0 tracked .zsh under guards/)
dead-path frontier     108  -> 115    (pin regenerated by running; +7, -0)
parity / cells                        unchanged: 46 / 7884
```

---

## 8. FOR THE DRIVER

* **`T399` is distinct and there is no file collision.** T399 is guards wired to nothing; this is
  a guard that runs and cannot see. The one place they touch is **S4** — T399 owns the
  guards-directory *registration* logic, request A3/A4 widens its *population* glob by one
  pathspec line. If T399 is rewriting that function, A3/A4 should be folded into its diff rather
  than applied on top. A1/A2 (host-state) and B/C are outside T399 entirely.
* **A follow-up worth more than request C.** The T238 linter filters "a path the file itself
  creates or deletes is scratch rather than corpus"; the T316 dead-path census has no such
  filter. **All 7 new rows, and an unknown share of the pinned 108, are files the instrument
  writes with `>`.** Adopting the linter's filter in the census would very likely take the +7 to
  +0 and shrink the existing pin. That is a classifier change, needs its own red drive against
  the existing 108, and is a task, not a line in this one.
* **Nothing here touches money, the ledger, the schema or the oracle.** No floating point, no
  driver, no vector, no capture. The instruments only read.
