# T262 — independent review of T259 `softhouse/T259-verdict-predicate` @ `8d72844`

**Reviewer:** T262, isolated worktree, did not write what is reviewed.
**Target:** `softhouse/T259-verdict-predicate` @ `8d72844be3425a262737c21b22857ef5ad0a40d1`
(2 commits: `85197b2`, `8d72844`).
**Merge-base with `main`:** `a71c1408d3315493bca763472598680c85b9ad0b`.
**`main` at the time of review:** `1b8c1f84c48566380dfb1c75dc6e969849b480af` (it moved from
`7c29273` mid-review; a concurrent fire is live — see §9).
**Vector store:** `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` at `main` **and** at `8d72844`,
read live with `git rev-parse` at the start and again at the end of this review (P-69).

# VERDICT: **MICRO-FIX**

The money argument is **correct and reproduces exactly**. I re-derived it myself, in integer
minor units, from the raw gz capture rather than from T259's arithmetic, and I get T259's numbers
to the unit: **3 of 6 under the registered predicate, 6 of 6 under the corrected one, in both
directions.** The ruling — the predicate is the broken half, the nine verdicts stand — is sound,
and the strongest leg of it (the structural reading of `classify_t229.py`) I confirmed line by
line. Byte integrity is intact, the BAR reproduces, materiality really is LOW, and G-8 is
untouched.

It is **not a clean MERGE** because the instrument T259 shipped to make this defect impossible to
print silently **contains the same defect**: R-VPA has a path where its body prints
`REFUSED  NIL COVERAGE` and its probe line and exit code both say `GREEN 0` (F-1). Two of its
four error paths exit **1**, the code its own docstring reserves for a real measured negative
(F-2), and the handoff asserts the opposite. Eight of twelve adversarial shapes I invented walk
past it (F-3). And T259's own B-1 file contains a row that falsifies the expectation T259
recorded for it (F-4).

Every one of these is confined to files T259 created on this branch. **No committed evidence is
touched, no verdict moves, no vector moves, no gate conclusion moves.** Hence MICRO-FIX, not
REJECT.

---

## 0. Ruling requested by the brief: **may an unwired rule merge?**

**Yes — but only on these three conditions, and T259 meets one and a half of them.**

1. **The branch must say plainly that nothing reads it.** T259 does, twice, unprompted, in the
   file itself (`run.sh:4-7`), in the DECISION §6 and in handoff B-2. I verified the claim rather
   than accepting it: `/usr/bin/grep -c` for `t256-verdict-predicate|T259-VPA|check_verdict_predicate`
   over `.softhouse/conformance.sh` returns **0, rc 1 — a real measured negative**, and
   `git grep -l -F check_verdict_predicate_agreement 8d72844` returns **rc 0 with 8 paths, all of
   them inside T259's own directory or its handoff**. Nothing outside reads it. **CONDITION MET,
   and met honestly.**
2. **A wiring task must be FILED, not suggested.** B-2 is prose in a handoff. Prose does not fire
   on the next fire — which is T259's own argument against T241 (DECISION §3.2: *"Prose does not
   fire on the next capture. R-VPA does."*). The same standard applies to T259. **CONDITION NOT
   MET.** A successor task must exist in `tasks.json` before this merges, or B-2 becomes the
   seventh instance of the shape.
3. **The rule may not be cited as coverage anywhere until it is wired.** Nothing on this branch
   does cite it that way. **CONDITION MET.**

The reason to merge rather than block: the alternative is a correct ruling and a working
instrument rotting on a branch while `conformance.sh` is held by another task, which is strictly
worse than merging it with the wiring debt recorded. But it must **not** merge as though the job
were finished, and the handoff's own framing ("*until wired, it is in the condition it was written
to condemn*") is the right one and must survive into whatever text the driver carries forward.

---

## 1. My own integer re-derivation — shown in full (the money finding)

Instrument: `rederive_t262.py` in this directory; transcript `rederive-t262-output.txt`.
Every `json.load` carries `parse_float=Decimal`. This file **reproduces nothing**, so T207's
ruling (`audit-t44/analysis/T207/RULING-float-derived-predicate.md` — *"add `parse_float` is
sometimes the WRONG repair, when a line faithfully REPRODUCES an earlier script that loaded
without it"*) does not apply and the guard is simply added; I read that ruling before touching
anything. Every quantity below is a Python `int` in minor units, asserted `type(v) is int`.
No float is constructed at any point, including intermediates.

Inputs, hashed by me:

* `out/classify-t229.json` — sha256 `f831736f07f1a6fecd4ee69b5a1de8dac0abcae89210f997e72526070f62821a`
  (**matches T259's claim exactly**); git blob `2f740a8bd064fae24bb80a3e1da439dd73c2f72b` at
  `8d72844` and **identical at `main`**.
* `out/capture-t229-raw.json.gz` — sha256 `ed5feab749755c41b0780d3b43ed6b57133ab761e40e1d4fbfe6b196bd314821`.
* Independent float census of the derived file: **160 numeric tokens, 0 float-shaped**. T259's
  §8 figure reproduces.

### 1.1 The counts (P-67 — both terms counted)

| measured | T262 | T259 said |
|---|---|---|
| rows in file | **9** | 9 ✔ |
| rows carrying `P2_totalInterestEqualsNEplusB` | **6** | 6 ✔ |
| rows lacking it | **3** | 3 ✔ |
| the 3 lacking, by `predictedOutcome` | **all `RESCUED_BY_SITE3`** | same ✔ |
| carriers with value `false` | **5** | 5 ✔ |
| carriers with value `true` | **1** (5 + 1 = 6) | 1 ✔ |
| of the 5 false, verdict affirmative | **3** — `-B251`, `-B201`, `-B299` | same list ✔ |
| of the 5 false, verdict negative | **2** — `-B199`, `-B1450` | same ✔ |

**T259's correction of the driver is CORRECT and worth recording.** The denominator is **6, not
9**. The key is absent by design on the three `RESCUED_BY_SITE3` rows — `classify_t229.py:102`
computes the P2 block only `if p["predictedOutcome"] != "RESCUED_BY_SITE3"`, and P2 is registered
in `PREDICTION.md` as scoped "on every unrescued cell". So "five of nine" would have been a false
denominator; "five of the six rows that carry the key" is the true sentence. **This is a driver
error T259 caught, not a P-67 defect T259 introduced.**

### 1.2 Is `n·E + B` the total repayment? — checked against the RAW emitted schedule rows

I did not take this from T259 or from the derived file. I summed the oracle's own `REPAYMENT`
rows out of the gz, and asserted the row sums equal the header totals on every row (they do).

```
  id                          sumTotal  sumPrin   sumInt     n*E+B  tot==nE+B  lastTot    I==T-P
  T229-R600p0-N200-B199           2553      199     2354     20199      False        0      True
  T229-R36p0-N1400-B1450          6469     1450     5019     63050      False        0      True
  T229-R600p0-N200-B251          25251       51    25200     25251       True      376      True
  T229-R600p0-N200-B201          20201        1    20200     20201       True      301      True
  T229-R36p0-N1400-B150           5750        0     5750      5750       True      154      True
  T229-R600p0-N200-B299          30099       99    30000     30099       True      448      True
```

**The algebra, done myself and stated precisely — this is sharper than T259 puts it:**

* `interest = totalRepayment − principalRepaid` is **exact and unconditional**. It is the column
  identity `Σ total = Σ principal + Σ interest`, and it holds on **6 of 6** rows (`I==T-P` column,
  all `True`), including the two where everything else collapses.
* `totalRepayment = n·E + B` is **conditional**, and holds on only **4 of 6**. It requires the
  schedule to actually be *n−1 rows of E plus a last row of E+B*. On `-B199` and `-B1450` the last
  row total is **0** and there are three distinct totals ex-last, so the structure never
  materialised and `n·E+B` (20199, 63050) is nothing like the real repayment (2553, 6469).
* Therefore `n·E + B − principalRepaid = totalInterest` **iff** `n·E + B = totalRepayment`.
  **It is not an identity, and it does not require full amortisation** — `-B251`, `-B201`,
  `-B299` are all partial cells (principal repaid 51, 1, 99 against 251, 201, 150 disbursed) and
  it holds exactly on all of them. The condition is the EMI-plus-balloon **row structure**, not
  amortisation.

This matters because it is what makes the 6-of-6 result **non-vacuous**: the corrected predicate
is genuinely discriminating, `False` on 2 and `True` on 4, not a tautology that agrees with
anything.

### 1.3 The decisive measurement — every one of the six checked

Agreement is defined as `predicate == (verdict == "AS PREDICTED")`. I recomputed the *registered*
predicate from the raw figures and asserted it equals the recorded `P2_…` on every row
(`assert reg == r[KEY]` — passes on all 6, so the committed file is internally faithful).

```
  id                             n  E_obs      B  P_rep     nE+B   nE+B-P  int_obs    REG   CORR   verd  agrREG  agrCORR
  T229-R600p0-N200-B199        200    100    199    199    20199    20000     2354  False  False  False    True     True
  T229-R36p0-N1400-B1450      1400     44   1450   1450    63050    61600     5019  False  False  False    True     True
  T229-R600p0-N200-B251        200    125    251     51    25251    25200    25200  False   True   True   False     True
  T229-R600p0-N200-B201        200    100    201      1    20201    20200    20200  False   True   True   False     True
  T229-R36p0-N1400-B150       1400      4    150      0     5750     5750     5750   True   True   True    True     True
  T229-R600p0-N200-B299        200    149    299     99    30099    30000    30000  False   True   True   False     True

  AGREEMENT under REGISTERED predicate : 3 of 6
  AGREEMENT under CORRECTED  predicate : 6 of 6
  corrected agreements, TRUE  direction: 4
  corrected agreements, FALSE direction: 2
```

**T259's 3-of-6 / 6-of-6 REPRODUCES EXACTLY.** There is **no row among the six** where the
corrected predicate and the verdict disagree. The brief's kill condition — "a single row where the
corrected predicate and the verdict disagree destroys the argument" — **is not met on T229**, and
I checked all six, not a sample.

**Robustness check T259 did not run.** The registered conjunct uses the *observed* row-1 total as
`E` (`classify_t229.py:106`), not `emiMinorPredicted`. Re-running the corrected predicate with the
*predicted* `E` instead: **still 6 of 6.** The result does not depend on which `E` you read.

### 1.4 The losing side — checked, and argued fairly, not strawmanned

Under the rejected reading ("`verdict` should have ANDed P2 in"), the three affirmative-over-false
cells flip to REFUTED. I verified each hit **both** graded columns to the minor unit:

```
  T229-R600p0-N200-B251  familyHit=True principalHit=True (obs=51 pred=51) correctedPredicate=True
  T229-R600p0-N200-B201  familyHit=True principalHit=True (obs=1  pred=1)  correctedPredicate=True
  T229-R600p0-N200-B299  familyHit=True principalHit=True (obs=99 pred=99) correctedPredicate=True
  cells that would flip to REFUTED despite hitting family AND principal exactly: 3
```

**Three false refutations. Confirmed.** And the losing side is stated in its strongest form, not
its weakest — DECISION §4 gives it three affirmative arguments including the one most damaging to
T259's own position (*"the pattern library is full of guards that computed the right thing and
reported the wrong thing … so the prior should be against it"*). That is a fair statement of an
opposing case. It was not assumed away.

---

## 2. Findings

### F-1 — **HIGH** — R-VPA prints `REFUSED` in its body and `GREEN 0` on its probe line. The fix reproduces the defect it exists for.

`check_verdict_predicate_agreement.py:252-256` reports NIL COVERAGE **per file**, but line 294
computes the gate **globally**:

```python
nil = 1 if rep.rows == 0 else 0     # rep.rows is the sum ACROSS ALL FILES
```

So one populated file in the same invocation switches the nil-coverage refusal off for every other
file in the batch, while the words `REFUSED  NIL COVERAGE` are still printed in the body. Measured
(`attack-t262-output.txt`, PART B):

```
  empty file ALONE                       : rc=1  probe=PRESENT  state=REFUSED
  empty file BATCHED with a populated one:
    rc                                   : 0
    body printed 'REFUSED  NIL COVERAGE' : True
    probe line: T259-VPA: GREEN files=2 rows=1 ... nilCoverage=0
```

**This is precisely the shape the task was dispatched to fix** — the guard runs, writes its answer
down, and the summary line above it says the opposite. It is P-45 one layer further in.

It is worse than a latent typo, because it also **silently converts two of my caught shapes into
misses**. `A1-nested-one-level-deeper` and `A2-toplevel-array` were caught **only** by nil
coverage (`rows=0`), never by the disagreement detector. Batched with the real
`classify-t229.json`, both flip to GREEN (`attack2-t262-output.txt`):

```
  A1-nested-one-level-deeper   rc=0  GREEN  rows=11  disagr=3   MISS   (alone: rc=1)
  A2-toplevel-array            rc=0  GREEN  rows=11  disagr=3   MISS   (alone: rc=1)
```

**Live, not theoretical:** B-1 is filed, and the obvious next step is
`check_verdict_predicate_agreement.py classify-t229.json classify-t219.json` — a two-file
invocation, which is exactly when this bites.

**Fix:** track nil coverage per file and OR it into `refused`; report `nilCoverageFiles=N` on the
probe line.

### F-2 — **MEDIUM** — two of four error paths exit **1**, not 2. The handoff's claim about this is false.

The docstring is explicit: *"2 ERROR — usage, IO, or parse. NEVER used to report an absence"*, and
the handoff states *"Exit codes are classified and never conflated"* and *"`E1`/`E2` … exit **2**"*.
There are **four** error paths, not two, and the two T259 did not test conflate. Measured
(`attack-t262-output.txt`, PART C):

```
  E1 missing target                  : rc=2  probeAbsent=True   ✔
  E2 unreadable register             : rc=2  probeAbsent=True   ✔
  E3 wrong autoPredicatePattern      : rc=1  probeAbsent=True   <<< CONFLATION
  E4 no .git ancestor                : rc=1  probeAbsent=True   <<< CONFLATION
```

Cause: `raise SystemExit("ERROR: …")` at line **144** (`load_registers`) and line **79**
(`repo_root`). `SystemExit` with a string argument prints to stderr and exits **1** — the code
reserved for a real measured negative. A caller reading only the exit code cannot distinguish
"the rule refused" from "the rule could not find the repository".

**Mitigated but not cured by P-83:** the probe line is genuinely absent in both cases, so a caller
that tests presence before value survives — and the probe B-2 proposes does test presence. That is
the discipline working. But the module must not require its callers to compensate for a defect its
own docstring forbids.

**Fix:** replace both with `print(..., file=sys.stderr); sys.exit(2)`. Correct the handoff sentence
from "its two error paths" to four, two of which were untested.

### F-3 — **MEDIUM** — the selector's genericity is overstated: 8 of 12 invented shapes walk past it.

I did not re-run T259's battery. I invented twelve shapes, each carrying an affirmative verdict
over a predicate the row itself recorded as not holding — ground truth `REFUSED, exit 1` for every
one. Results (`attack-t262-output.txt` PART A, `attack2-t262-output.txt`):

| shape | caught? | why it slips |
|---|---|---|
| `C0` control, flat T229 shape | **CAUGHT** | the designed case works |
| `A3` verdict int + a sibling `verdictWord` | **CAUGHT** | caught via the sibling key |
| `A1` row nested one level deeper (`{"results":{"cells":[…]}}`) | **caught alone, MISS batched** | `walk_rows` descends exactly two levels |
| `A2` top-level JSON **array** of rows (`prediction.json`'s own shape) | **caught alone, MISS batched** | `walk_rows` returns immediately unless the doc is a dict |
| `A3b` verdict as an object `{"word":"AS PREDICTED"}` | **MISS** | `isinstance(v, str)` filter, line 198 |
| `A3c` verdict as a bare int enum | **MISS** | same |
| `A4` verdict key named `result` | **MISS** | `is_verdict_key` requires `verdict`/`status` |
| `A4b` verdict key named `conclusion` | **MISS** | same |
| `A5` predicate `null` rather than `false` | **MISS** | `isinstance(v, bool)` filter, line 210 |
| `A6` predicate stored as the string `"false"` | **MISS** | same |
| `A7` predicate stored as `0` | **MISS** | same |
| `A8` predicate inside a nested list in the row | **MISS** | inner dicts are never walked |

**Eight misses of twelve** (ten, counting A1/A2 under the F-1 batching condition), and — this is
the part that matters — **every miss is SILENT**. The rule's own fail-closed principle 2 says *"a
boolean whose intent nobody has recorded cannot be assumed descriptive; assuming it is, is exactly
how P2 got past."* A key that **is** classified `PREDICATE` (auto, via `^P[0-9]+_`) but carries a
non-boolean value is not merely unhandled — it is dropped without a word, which is the same
assumption failure one type over.

The claim in DECISION §6 / handoff §3 — *"Discovery is generic … It is not written around `cells`
and not written around `P2_`"* — is **true on exactly the two axes it names and false on four
others**: nesting depth, JSON type of the predicate, JSON type of the verdict, and the verdict
key's name.

**Fix (minimum):** refuse when a `PREDICATE`-classed key holds a non-`bool`; refuse on a top-level
array; and restate the genericity claim as the two axes it actually covers.

### F-4 — **MEDIUM** — B-1 is real, and it contains a row that falsifies T259's recorded expectation for it and weakens one leg of the ruling.

**B-1 confirmed exactly.** `.softhouse/capture/t219-g8-residual/out/classify-t219.json`
(sha256 `5226eacea7ff004eb545a9d8d02278096834e22ccd64f74828472dc0c5708bc8`), read-only,
`spotcheck-b1-output.txt`:

```
  rows inspected: 11        DISAGREEING pairs found: 4        distinct rows: 3
  cells[3] T219-R600p0-N103-B1      P2_emiDifferenceEqualsB           verdict=AS PREDICTED
  cells[3] T219-R600p0-N103-B1      P2_totalInterestEqualsNEplusB     verdict=AS PREDICTED
  cells[5] T219-R600p0-N3000-B4499  P2_totalInterestEqualsNEplusB     verdict=AS PREDICTED
  cells[7] T219-R600p0-N3000-B3001  P2_totalInterestEqualsNEplusB     verdict=AS PREDICTED
```

**3 rows, 4 pairs, ids exactly as T259 listed.** The brief asked for one pair spot-checked; I
re-derived **all seven carriers** in integer minor units instead:

```
  id                                  n   E_obs       B   P_rep      nE+B    nE+B-P   int_obs    REG   CORR  agrREG  agrCORR
  T219-R600p0-N104-B1               104       0       1       0         1         1         1   True   True    True     True
  T219-R600p0-N3000-B2999          3000    1499    2999       0   4499999   4499999   4499999   True   True    True     True
  T219-R600p0-N103-B1               103       1       1       1       104       103        13  False  False   False    False
  T219-R600p0-N3000-B1001          3000     500    1001       0   1501001   1501001   1501001   True   True    True     True
  T219-R600p0-N3000-B4499          3000    2249    4499    1499   6751499   6750000   6750000  False   True   False     True
  T219-R600p0-N108-B1               108       0       1       0         1         1         1   True   True    True     True
  T219-R600p0-N3000-B3001          3000    1500    3001       1   4503001   4503000   4503000  False   True   False     True

  AGREEMENT under REGISTERED predicate : 4 of 7
  AGREEMENT under CORRECTED  predicate : 6 of 7      <<< NOT 7 of 7
```

T259 flagged `-B4499` as the cell needing care because principal repaid is 1499. **It flagged the
wrong cell.** `-B4499` and `-B3001` behave exactly as T259 expected — the corrected predicate
rescues both. The interesting row is **`T219-R600p0-N103-B1`**, verified against the raw gz
(`b1-row-detail-output.txt`, raw sha256 `8d3cce9de4c665183eb717daf8e3b9a442041c994d15f0d4305e6aac32efb86b`):

```
  repayment rows 103   sum of row totals 14   sum principal 1   sum interest 13
  row-1 total E 1      last row total 0       distinct totals ex-last [0, 1]
  n*E + B = 104        n*E + B - principalRepaid = 103        observed interest = 13
  REGISTERED predicate  : False
  CORRECTED  predicate  : False          <<<
  recorded verdict      : AS PREDICTED   <<<
```

So on `T219-R600p0-N103-B1` a **corrected** predicate and an **affirmative** verdict **disagree**.

**What this does and does not do to T259's ruling.**

* It does **not** overturn the ruling. On T229's six carriers the concordance is genuinely 6/6,
  and the decisive argument is anyway the *structural* one (§3 below): `verdict` is computed from
  family + principal and is finished before any `P2_` key exists. That leg is airtight and
  independent of the concordance.
* It **does** undercut the inference T259 leans on: *"A verdict genuinely tracking a different
  proposition would still disagree with a correct predicate somewhere. This one disagrees
  nowhere."* One capture over, same classifier design, same predicate, the verdict **does** disagree
  with a correct predicate. So "disagrees nowhere" is a property of T229's particular cell set,
  not evidence about what `verdict` tracks. Read strictly, T259's §1.3 already **proves** the
  verdict tracks a different proposition; the 6/6 table is corroboration, and T259 presents it as
  the load-bearing member (*"That is the whole argument in one table"*).
* It makes T259's B-1 handoff text — *"the expected outcome is the same (the registered predicate
  is wrong, the verdicts stand)"* — **wrong on one of the three rows**, and a successor that
  inherits that sentence will start from a false expectation. T259 was right that B-1 must be
  re-derived rather than assumed; it then recorded an assumption anyway.

**B-1 needs its own task, and yes, I say so explicitly.** It is a live, unread refutation of a
registered prediction in committed evidence, in no handoff, and R-VPA as wired will never see it
(§F-6). The task must be told that `-B103-B1` is the hard row.

### F-5 — **LOW** — the R1 red leg's "not one token in common" is misleading as evidence of genericity.

`R1-fresh-predicate-fresh-verdict-word.json` uses container `observations`, id key `probe`,
predicate `P7_lastRowExcessEqualsB`, verdict key **`outcomeVerdict`**, word **`CONFIRMED`**. The
claim "not one token in common with a T229 row" is literally true. But genericity is relative to
**the rule's hardcoded vocabularies**, not to T229's rows, and against those the leg shares every
load-bearing token it needs:

* `outcomeVerdict` contains the substring `verdict` — the exact thing `is_verdict_key` searches for;
* `CONFIRMED` is a hardcoded member of the `AFFIRMATIVE` set (line 67);
* `P7_` matches the hardcoded `^P[0-9]+_`.

So R1 varies only along the two axes the rule was deliberately generalised over. `A4`/`A4b`
(`result`, `conclusion`) are the honest version of that test, and the rule fails them. The leg is
not dishonest, but it should not be presented as showing the rule "is not written around `cells`
and is not written around `P2_`" in the strong sense the prose implies.

### F-6 — **LOW / structural** — R-VPA, as wired, opens exactly one file and can never see B-1.

`run.sh:43` invokes the checker with **no arguments**; the default target
(`check_verdict_predicate_agreement.py:269`) is `t229-g8-site3/out/classify-t229.json` alone.
Measured (`attack-t262-output.txt` PART D):

```
  files opened with no args: ['FILE .softhouse/capture/t229-g8-site3/out/classify-t229.json']
  t219 mentioned anywhere in output: False
```

The four live disagreements the census found are outside the rule's reach even once B-2 is
wired. The wiring task must pass the census's file list, not the default.

### F-7 — **LOW** — the sha pin holds exactly as claimed; the docstring overclaims by one file.

My first pin test was **invalid and I am recording that rather than deleting it**
(`pin-test-output.txt`): `repo_root()` walks up from the rule's own `__file__`, so with the rule
left in the real repo my scratch target's `rel` became an absolute path, no acknowledgement ever
matched, and CASE 1 refused for the wrong reason. Redone correctly with the whole instrument
directory copied into the scratch repo (`pin-test2-output.txt`), never touching the real evidence:

```
  CASE 1  unmodified evidence at the pinned path   rc=0  VOID=False  [ACK]=3  [UNACK]=0
  CASE 2  ONE APPENDED NEWLINE (whitespace only)   rc=1  VOID=True   [ACK]=0  [UNACK]=3
  CASE 3  semantic flip on a row NOT in the ack    rc=1  VOID=True   [ACK]=0  [UNACK]=4
  CASE 5  true bytes restored, ack left re-pointed rc=1  VOID=True   [ACK]=0  [UNACK]=3
```

**T259's claim is TRUE: the pin cannot be satisfied by a file that has changed.** A single
whitespace byte voids the whole block. That is a real mechanical enforcement of T114/T176 and it
is the best part of the instrument.

The overclaim: the docstring says *"you cannot make the record agree by retro-editing it."* You
can — by editing **two** files. CASE 4: mutate the evidence, re-point the ack's `sha256`, add a row,
and the rule returns **GREEN 0 with 4 acknowledged**. This is inherent to any acknowledgement
mechanism and is bounded (the disagreement is still printed on every run, and the `acknowledged.json`
diff is visible in review), but the sentence should read "by retro-editing the evidence alone."

### F-8 — **LOW** — the clean self-lint and the unmoved frontier are presented as corroboration they cannot provide.

The handoff: *"the frontier stayed at 11 … That is the project's own P-80 detector agreeing with
T259's self-lint."* Both figures are **true** (§4 below). But `lint_failopen_t259.py` is a
token/regex detector — `|| true`, `|| echo`, `2>/dev/null`, `set +e`, bare `grep`, `rg`,
`git grep -E`, catch-all `except` — and so is the harness frontier census. **Neither can see F-1
or F-2**, which are semantic. T259 added **one real fail-open** (F-1) and two exit-code
conflations (F-2) while both detectors reported clean. The conclusion "T259 added no fail-open" is
not supported by the evidence offered for it; what is supported is "T259 added no *token-detectable*
fail-open."

---

## 3. Claims I re-derived and **CONFIRM** (no defect)

**C-1 — how `verdict` is computed. CONFIRMED, line by line — and this is the strongest part of the
argument.** Read `classify_t229.py` in full (110 lines). `verdict` is assigned at line **95**
(rescued branch) and line **100** (unrescued branch). It reads exactly two things: `obs` versus
`p["predictedOutcome"]` (line 97-98), and `row["observedPrincipalMinor"] == pp` (line 99). The
three `P2_*` keys are assigned at lines **103, 104, 105-106** — *after* `verdict` is already in
the row. `P1`, `P3`, `P4`, `P5` appear nowhere in the file. **The ordering claim is exactly right
and the structural impossibility is real:** `verdict` cannot consult a `P2_` key because no `P2_`
key exists when it is computed.

**C-2 — byte integrity. CONFIRMED independently.**
* `git diff --name-status main...8d72844` → **22 `A`, 0 `M`, 0 `D`**, re-measured at the end.
* `git diff --stat main...8d72844 -- .softhouse/capture/t229-g8-site3/ .softhouse/gates.md .softhouse/vectors/ .softhouse/conformance.sh` → **empty**. Not one byte of the evidence, the gates file, the vector store or the harness moved.
* `git rev-parse main:…/classify-t229.json` and `8d72844:…` → **both `2f740a8bd064fae24bb80a3e1da439dd73c2f72b`**.
* **Strict-ancestor falsifiability, run by me:** `python3 src/site3.py src/cells-t229.json | cmp - prediction.json` → site3 rc **0**, `cmp` rc **0**, both sides sha256
  **`c4a3f5db454604b0201e32a39cd0d52027e6e3a34c28a46ec31249b4d7f08a5c`** — T259's figure to the
  character. T241's comment-only annotation still reproduces `prediction.json` byte for byte.

**C-3 — the manifest check and the rc-1-vs-rc->1 distinction (P-80). CONFIRMED.**
`/usr/bin/grep -c t229-g8-site3` prints **0** and exits **1** on both
`t177-so-nondeterminism/MANIFEST.sha256` and `tierA-a2/MANIFEST.sha256` — a real measured
negative, correctly classified, not an error. `git grep -F <sha256>` over `main` → **rc 1, no
tracked file**; over `8d72844` → **rc 0, 5 files**, all T259's. So the pin genuinely did not exist
and T259 genuinely added it. The distinction was made, and made correctly.

**C-4 — the census figures. CONFIRMED against the committed transcript.** `run-output.txt:139-159`
reads 1499 seen / 12 shaped / 1451 unshaped / 36 unparseable / **8 disagreements**, itemised by
file, with the R1 red fixture named as one of the eight rather than hidden. The prose matches the
transcript exactly. **The second commit `8d72844` is a genuine self-correction** (13→12, 1450→1451)
caught by T259's own P-69 re-measure, with the cause stated (a count taken before
`verdictScope`→`gradedProposition` was renamed). That is the discipline working, and it counts in
T259's favour.

**C-5 — materiality LOW, and G-8. CONFIRMED, verified rather than accepted.** `gates.md` is
byte-identical across the diff. The vector store digest is `13b8342e…` at `main` and at
`8d72844`. The **only** occurrences of "options (b) and (c)" on the branch are the two sentences
stating they are **not** raised, not referenced as live and not put to Buyan. **Nothing on this
branch moves a gate conclusion**, and the conservative superset `B_minor < 1.5·n` and the unproven
conjecture `δ ≤ 1` are untouched. No HIGH finding on materiality.

**C-6 — float discipline. CONFIRMED.** The derived file carries **0 float-shaped tokens out of
160** (my own count). T259's decision to leave `site3.py:302` and `classify_t229.py`'s loads
unguarded is **correct** and is the T207 ruling applied properly: `site3.py` must keep reproducing
`prediction.json` byte for byte, and adding `parse_float` there could change its output. Reading
T207 first was the right move and I reached the same conclusion independently.

---

## 4. The BAR — re-run by me, probe PRESENCE before value (P-83)

`bash .softhouse/conformance.sh` at `8d72844` (T259's files **tracked**, my review scripts
untracked and therefore invisible to `git ls-files`): **exit 0**, 528 lines, transcript
`/tmp/t262-bar.txt`. Verified by `bar_check_t262.sh` → `bar-check-output.txt`, which asserts
presence first and only then reads values, and which **aborts on `grep` exit >1** rather than
printing an absence:

```
=== STEP 1: probe-line PRESENCE (before any value is read) ===
  PRESENT  fail-open frontier probe
  PRESENT  frontier equality probe
  PRESENT  VERDICT line
  PRESENT  exemption census block

=== STEP 2: only now, the VALUES ===
  frontier 11, pinned at 11.
  frontier == pinned (all 11 rows, by path).
  CENSUS fail-open instruments — inspected 927 tracked .sh/.py file(s)
  exemption census rows: 9   rows reading '== pinned': 9
  HEAD:.softhouse/vectors = 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
  invariant violations    0

BAR CHECK: all probes present, all values match T259's table.   (rc 0)
```

**The census delta, measured independently:** `git ls-tree -r main --name-only` filtered to
`\.(sh|py)$` → **918**; `git ls-files '*.sh' '*.py'` at `8d72844` → **927**. **Delta 9, exactly
T259's nine scripts**, and the frontier held at **11 == pinned 11**. **The branch adds 22 files
and moves the fail-open frontier by zero rows.** The rejection condition in the brief is not met.

Also confirmed against T259's table: VERDICT PASS exit 0; loanschedule 46 parity / 7884 cells
graded / 93 ungraded; LEDGER 4 parity + 2 oracle-refusal / 21 money cells; refused 0,
inadmissible 0, harness errors 0; invariant violations 0; 0 NOT RUN; 9 census pins all `== pinned`.
Every figure matches.

Caveat recorded, not hidden: F-1 and F-2 are semantic and the frontier census is token-based, so
"frontier unchanged" does **not** mean "no fail-open added" (F-8). It means no token-detectable
one.

---

## 5. Required micro-fixes

All inside files T259 created on this branch. **None touches committed evidence, and none may.**

1. **F-1 (must).** Make nil coverage per-file, not global; OR it into `refused`; add
   `nilCoverageFiles=` to the probe line. Drive it red with an empty file batched with a populated
   one — the exact case that passes today.
2. **F-2 (must).** Replace `raise SystemExit("ERROR: …")` at lines 79 and 144 with stderr + exit
   **2**. Correct the handoff: four error paths, two of which were untested and conflated.
3. **F-3 (must, minimum form).** Refuse when a `PREDICATE`-classed key holds a non-`bool`; refuse
   on a top-level-array document rather than relying on nil coverage. Restate the genericity claim
   as the two axes it covers, naming the four it does not.
4. **F-4 (must).** Amend the B-1 backlog text: the corrected predicate does **not** rescue
   `T219-R600p0-N103-B1`; t219 is 6-of-7, not 7-of-7; `-B103-B1` is the hard row, not `-B4499`.
   **File B-1 as a task.**
5. **F-5 / F-7 / F-8 (should).** Soften three sentences to what was measured: R1's genericity,
   "cannot make the record agree by retro-editing it" → "…the evidence alone", and "T259 added no
   fail-open" → "no token-detectable fail-open".
6. **B-2 (must, gating).** File the wiring task before merge. Prose does not fire on the next fire
   — T259's own argument, applied to T259.

---

## 6. What I skipped, counted (P-40)

| skipped | count | why |
|---|---|---|
| T259's own 14-leg battery `red/drive-red.sh` | 1 harness | **deliberate, per brief.** Re-running an author's harness and reporting that its arms pass is reading, not reviewing. I attacked the selector with twelve shapes of my own instead. **Consequence: I did not verify T259's 14/14 claim.** I verified the rule's *behaviour* directly, and found 8 misses the battery does not cover. |
| files on the branch not read in full | **13 of 22** | `RULES-failopen.md`, `census_verdict_shape.py`, `rederive_counts_t259.py`, `red/drive-red.sh`, `red/drive-red-output.txt`, `red/make_scratch_ack.py`, `red/mutate_one_predicate.py`, `red/plant_failopen.py`, and 5 of the 6 red fixtures. `run-output.txt` read only at 139-160; `lint_failopen_t259.py` read to line 60 (enough to classify it as token-based, which is all F-8 needs). I verified their **effects** — census figures against the transcript, BAR against the harness, lint scope against its rule table — rather than their text. |
| files read in full | 9 | `check_verdict_predicate_agreement.py`, `classify_t229.py`, `run.sh`, `acknowledged.json`, `boolean-key-register.json`, the DECISION, the handoff, the R1 fixture, `PREDICTION.md` §2/P2 region |
| `.softhouse/conformance.sh` | 1 file | held by another task; **read** for the R-VPA reference check and **executed** for the BAR; nothing written. |
| `.softhouse/capture/lib/`, `.softhouse/capture/tierA-a2/` | 2 dirs | held; `tierA-a2/MANIFEST.sha256` read only, for C-3. |
| BAR run on `main` for a frontier comparison | 1 run | not run. I derived the 918 figure from `git ls-tree main` and relied on the harness's own **path-pinned** frontier (11), which lives in `conformance.sh` and is unchanged by this branch — so `frontier == pinned` at `8d72844` is sufficient. |
| `classify_t219.py`'s verdict logic | 1 file | not audited. B-1's *data* is re-derived (all 7 carriers, raw-verified); its *classifier* is left to the B-1 task. |
| the other 4 T219 disagreement-free carriers' raw rows | 4 | derived-file figures only; the 3 disagreeing rows were raw-verified. |

**Where I looked before recording any non-existence (P-66/P-70):** `.softhouse/conformance.sh`
(for R-VPA references, rc 1); the whole tracked tree at both `main` and `8d72844` via
`git grep -l -F` (for the evidence sha256 and for the rule's name); both `MANIFEST.sha256` files;
`gates.md` via `git diff --stat`; the branch's full 22-file name-status.

---

## 7. Instruments produced by this review

All under `.softhouse/reviews/t262-verdict-predicate/`. `set -euo pipefail` in the shell script;
no bare `grep` (only `/usr/bin/grep`), no `rg`, no `git grep -E`; `grep` exit 1 treated as a real
measured negative and exit >1 as an abort; every `json.load` carries `parse_float=Decimal`.

| file | what it establishes |
|---|---|
| `rederive_t262.py` / `rederive-t262-output.txt` | the counts, the raw-capture algebra, 3-of-6 vs 6-of-6, the predicted-`E` robustness check, the losing side's three cells |
| `attack_rvpa_t262.py` / `attack-t262-output.txt` | 11 invented shapes + the nil-coverage batching fail-open (F-1) + the four error paths (F-2) + the single-file wiring (F-6) |
| `attack2_compound_t262.py` / `attack2-t262-output.txt` | A1/A2/A3c flipping from caught to missed when batched (F-1) |
| `spotcheck_b1_t262.py` / `spotcheck-b1-output.txt` | B-1 confirmed: 4 pairs, 3 rows; all 7 t219 carriers re-derived; 6-of-7 (F-4) |
| `b1_row_detail_t262.py` / `b1-row-detail-output.txt` | `T219-R600p0-N103-B1` raw-verified: corrected predicate FALSE under an affirmative verdict (F-4) |
| `pin_test_t262.py` / `pin-test-output.txt` | **an INVALID first attempt, kept and labelled** — `repo_root()` walks from the rule's `__file__` |
| `pin_test2_t262.py` / `pin-test2-output.txt` | the corrected pin test: whitespace-only mutation voids the block; the two-file re-point residual (F-7) |
| `bar_check_t262.sh` / `bar-check-output.txt` | BAR probe presence before value, frontier, 9 census pins, vector digest |

---

## 8. Things I could not verify

1. **T259's `14 legs / 14 pass`.** Not re-run, by instruction. My twelve shapes are a different
   test and found eight misses; both can be true at once.
2. **That the six T229 verdicts are *correct*** in any sense beyond "consistent with the
   proposition `classify_t229.py` actually computes." R-VPA's own disclaimer says this and it is
   right to.
3. **That the 36 unparseable JSON files hide nothing.** I accepted T259's count against its
   transcript; I did not open them.
4. **Whether `-B199` / `-B1450`'s REFUTED verdicts are right on their merits.** They agree with
   both predicates, which is all my measurement shows.
5. **The oracle-side provenance of `capture-t229-raw.json.gz`.** I verified the derived file is
   faithful to the raw file; I did not re-run the Java capture.

---

## 9. Re-measurement at the end (P-69)

```
2026-08-22T13:18:03Z
T259 tip      : 8d72844be3425a262737c21b22857ef5ad0a40d1
main          : 1b8c1f84c48566380dfb1c75dc6e969849b480af   (moved from 7c29273 during this review)
merge-base    : a71c1408d3315493bca763472598680c85b9ad0b
vectors@T259  : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
vectors@main  : 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d   (identical)
classify blob : 2f740a8bd064fae24bb80a3e1da439dd73c2f72b
diff letters  : 22 A   (0 M, 0 D)
```

`main` advanced mid-review under a concurrent fire. The vector store digest is unchanged on both
sides and the merge-base is unmoved, so nothing in this review is stale. Every figure above was
taken at `8d72844` and every one was re-read here.

---

## Verdict, restated

**MICRO-FIX.** The money is right and I proved it myself: **3 of 6 → 6 of 6, reproduced exactly**,
in integer minor units, against the raw capture. The ruling stands, the evidence is untouched, the
BAR is clean, and materiality really is LOW. The defects are in the new instrument, not in the
finding — but one of them (F-1) is the very shape this task was dispatched to eliminate, shipped
inside the eliminator, and that must not merge unfixed. **An unwired rule may merge; an unfiled
wiring task may not follow it.**

---

## 10. The same bar, applied to this review's own instruments

The rejection condition in the brief ("a branch that adds files and moves the fail-open frontier
by even one row, without moving the pin in the same commit") binds T262 as much as T259. Measured
on this branch after committing:

```
BAR exit = 0
CENSUS fail-open instruments — inspected 926 tracked .sh/.py file(s)
frontier 11, pinned at 11.
frontier == pinned (all 11 rows, by path).
VERDICT: PASS (exit 0) — 46 parity vectors, 7884 cells compared.
```

**918 → 926**, this review's eight scripts, and the **frontier held at 11 == pinned 11**. One
short-circuit-to-echo in an early draft of `bar_check_t262.sh` was removed before the commit and
replaced with explicit `if` blocks that set a failure flag — a `|| echo` is exactly the
"prints an absence over an error" pattern this review criticises elsewhere, and it had no business
in the instrument measuring it.
