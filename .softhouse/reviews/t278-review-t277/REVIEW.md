# T278 — INDEPENDENT REVIEW of T277 (merged at `e8374743`)

**Branch:** `softhouse/T278-review-t277`. **Reviewer standing: adversarial, and THIRD PARTY.**

## VERDICT: **APPROVE-WITH-FINDINGS**

One MAJOR finding, two MINOR. The verdict is not a REJECT and the reason is stated plainly:
**the block T277 re-worded is TRUE about main on the whole domain that block governs — every one
of its figures reproduced against a third instrument that shares no line of code with either prior
party.** What is *not* true is **the rest of the file it edited**: law (ii) has **five further live
homes inside `.softhouse/gates.md`**, every one of them **FALSE on exactly the same seven cells**,
and the correction reaches none of them. Reverting would make the record strictly worse; the remedy
is a follow-up task, and it is `F-T278-1`.

---

## 0. Independence, and where I looked

**I imported nothing.** Not T264's scripts, not the cloud's `rederive_t241.py`, not T277's
`shapelaw_census_t277.py` / `crosscheck_seven_t277b.py` / `dump_seven_t277.py`, not T229's
`site3.py` / `validate_corpus.py`. My instrument is
`.softhouse/reviews/t278-review-t277/probe/t278_rederive.py`; it reads only the committed raw
`.json.gz` captures, contacts no oracle, and its `--selftest` asserts its own independence at AST
level (it fails if it ever imports a module whose name contains `t277`, `t241`, `t264` or `site3`).

The upstream handoff was read **from the branch, not from the author's working tree** —
`git show softhouse/T277-shapelaw-salvage:.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T277.md`
— and I derived the seven cells before reading T277's conclusions about them.

"Not found" is a statement about the search. Where I looked, for restatements of law (ii):
`grep -n 'n·δ\|n·delta\|B_minor − n\|max(0, B'` over `.softhouse/gates.md`; a repo-wide
`grep -rn 'B_minor − n·δ\|min(B_minor, n·δ)\|max(0, B_minor'` over `*.md *.json *.py *.go *.sh`;
and a targeted read of `.softhouse/vectors/loanschedule/T116-G8-*` reason strings.

---

## 1. MY OWN THIRD DERIVATION — the seven cells

Integer minor units throughout. `B` from the input disbursement, cross-checked against the
DISBURSEMENT row's principal. `n` cross-checked against the REPAYMENT row count. `E` = repayment
row 1's `total`. **`I₁q` COMPUTED from the exact monthly rate fraction and quantized HALF_UP —
never read from row 1's `interest`.** Observed principal = **the sum of the principal column**,
never a header. Rate carried as an integer `(num, den)` pair; HALF_UP as `(2a + b) // (2b)`.

`[VERIFIED: evidence/20-t278-seven-cells.txt]`

| cell | capture | n | `B` | `E` | `I₁q` | `δ` | `B ≤ n·δ` | law (ii) predicts | **T278 OBSERVED** | non-zero principal rows |
|---|---|---|---|---|---|---|---|---|---|---|
| `T117P2-R600p0-N108-B11` | `capture-t117p2-raw.json.gz` | 108 | 11 | 5 | 6 | 1 | yes | 0 | **5** | row 108 only |
| `T117P2-R600p0-N121-B11` | `capture-t117p2-raw.json.gz` | 121 | 11 | 5 | 6 | 1 | yes | 0 | **4** | row 121 only |
| `T117P2-R600p0-N150-B11` | `capture-t117p2-raw.json.gz` | 150 | 11 | 5 | 6 | 1 | yes | 0 | **2** | row 150 only |
| `T159-R600p0-N108-B11` | `capture-t159-raw.json.gz` | 108 | 11 | 5 | 6 | 1 | yes | 0 | **5** | row 108 only |
| `T159-R600p0-N121-B11` | `capture-t159-raw.json.gz` | 121 | 11 | 5 | 6 | 1 | yes | 0 | **4** | row 121 only |
| `T159-R600p0-N150-B11` | `capture-t159-raw.json.gz` | 150 | 11 | 5 | 6 | 1 | yes | 0 | **2** | row 150 only |
| `T159-R600p0-N2000-B999` | `capture-t159-raw.json.gz` | 2000 | 999 | 499 | 500 | 1 | yes | 0 | **166** | row 2000 only |

**The named instance reproduces to the unit: `T159-R600p0-N2000-B999` repays 166 minor units
against a law-predicted 0.** Hand-worked and asserted in my self-test: `600.0 %` → monthly `1/2`;
`999 · 1/2 = 499.5`; HALF_UP → `I₁q = 500`; `E = 499`; `δ = 1`; `999 ≤ 2000 · 1` so the block's own
`FULL family B` antecedent holds and law (ii) predicts exactly zero. Header `totalPrincipalAmount`
equals my row sum on all seven and on all 296 / all 578 — nothing here rests on a header.

**I agree with both prior parties. There is no third opinion to report on the seven.**

### Every published census figure reproduces

`[VERIFIED: evidence/10-t278-census-t229corpus.txt, evidence/11-t278-census-all.txt]`

| measured | **T278 (mine)** | T277 / T264 published |
|---|---|---|
| stuck cells, `t229corpus` | **296** | 296 |
| `δ` histogram | **{0: 113, 1: 183}** | {0: 113, 1: 183} |
| FACT A holds / fails | **220 / 76** | 220 / 76 |
| law (ii), all 296 | **289** | 289 |
| **law (ii) on the FACT-A domain** | **213 of 220** | 213 of 220 |
| law (ii) at `δ = 0` | **113 of 113** | 113 of 113 |
| law (ii) on the `FULL family B` antecedent | **176 of 183** | 176 of 183 |
| interest `= n·E + B` holds / fails | **176 / 120**, and **0 of 113** at `δ = 0` | 176 / 120, 0 of 113 |
| corrected interest `n·E + B − principal`, FACT A vs not | **220/220 vs 0/76** | 220/220 vs 0/76 |
| `TOTAL REPAYMENT = n·E + B`, FACT A vs not | **220/220 vs 0/76** | 220/220 vs 0/76 |
| principal confined to the LAST row, on FACT A | **220/220**, and **441/441** on `all` | 220/220, 441/441 |
| `max(0, E + B − I_last)` on FACT A | **220/220**, and **441/441** on `all` | 220/220, 441/441 |
| header principal ≠ row sum | **0 of 296, 0 of 578** | 0 |
| `all` scope: captures / stuck | **775 / 578** | 775 / 578 |
| `all` scope: law (ii) exception set | **still exactly the seven** | exactly the seven |
| `all` scope: `PARTIAL family B` witnesses | **5, law (ii) holds on all 5** | 5, holds on all 5 |
| `PARTIAL family B` witnesses inside the 296 | **0** | 0 |
| stuck cells excluded on rate inexactness | **exactly 1 — `T84-RP-R7p0-N56-B23`** | exactly 1, same id |

**Bookkeeping reconciliation, so a later reader does not read a disagreement where there is none.**
T277 reports `578 + 197 = 775`; I report `761 admitted + 14 rejected = 775`. Both are complete.
T277 counts the 183 admitted-but-amortizing cells as "rejected"; I count them as admitted-not-stuck.
`183 + 14 = 197`. Same partition, different label. `[VERIFIED: evidence/11-t278-census-all.txt]`

I also confirmed independently that of the **8** captures at 7.0 % p.a. (whose monthly factor
`7/1200` does not terminate inside 19 fractional digits), **exactly one is a stuck cell** —
`T84-RP-R7p0-N56-B23` — so gates.md's "one cell is excluded and counted" is exact, not approximate.

---

## 2. THE PRIMARY CHARGE — is the re-worded block true on the WHOLE DOMAIN it governs?

**The block itself: YES.** Every claim inside `#### CORRECTION (T277)` (`gates.md:2308`) reproduces
against my instrument, including the ones T277 could have got away with asserting: the `all`-scope
figures, the `PARTIAL family B` zero-witness claim, the 37/113 split, the header-vs-row-sum check,
the single excluded cell, and the `I₁q` trap's exact 183-cell false refutation.

**The FILE it edited: NO — and that is `F-T278-1`.**

### F-T278-1 — **MAJOR** — law (ii) has five further LIVE homes in `gates.md`, all false on the same seven, none reached by the correction

Law (ii) `TOTAL PRINCIPAL = max(0, B_minor − n·δ)` is algebraically identical to the residual form
`residual = B_minor − max(0, B_minor − n·δ) = min(B_minor, n·δ)`. That residual form is stated as a
bare, present-tense, unqualified fact at **five** live sites in the file T277 edited:

| line (post-merge `gates.md`) | what it says | reached by `CORRECTION (T277)`? |
|---|---|---|
| `:1164` | "The residual is `min(B_minor, n·δ)`" | **no** |
| `:1865` | "`TOTAL PRINCIPAL = max(0, B_minor − n·δ)`, which predicted the amount repaid…" | no (points at gap 2, not at the correction) |
| `:1891` | "The residual of an unrescued family-B cell is `min(B_minor, n·δ)`" | **no** |
| `:2603` | "`residual = B_minor − max(0, B_minor − n·δ) = min(B_minor, n·δ)`" | **no** |
| `:3543` | "the residual is `min(B_minor, n·δ)` — a function of the **PRINCIPAL**" | **no** |
| `:3679` | "**The residual of an unrescued family-B cell is `min(B_minor, n·δ)`**" — inside a **prescriptive disclosure instruction** for G-8 | **no** |

**MEASURED, not argued** `[VERIFIED: evidence/40-t278-domain-audit-t229corpus.txt,
evidence/41-t278-domain-audit-all.txt]`:

```
'the residual of an unrescued family-B cell IS min(B_minor, n*delta)'
  t229corpus:  holds 289 of 296   FAILS 7
  all:         holds 571 of 578   FAILS 7
  exception set of the residual form == exception set of law (ii)?  True

  T117P2-R600p0-N108-B11   formula residual=11    OBSERVED residual=6    (repaid 5)
  T117P2-R600p0-N121-B11   formula residual=11    OBSERVED residual=7    (repaid 4)
  T117P2-R600p0-N150-B11   formula residual=11    OBSERVED residual=9    (repaid 2)
  T159-R600p0-N108-B11     formula residual=11    OBSERVED residual=6    (repaid 5)
  T159-R600p0-N121-B11     formula residual=11    OBSERVED residual=7    (repaid 4)
  T159-R600p0-N150-B11     formula residual=11    OBSERVED residual=9    (repaid 2)
  T159-R600p0-N2000-B999   formula residual=999   OBSERVED residual=833  (repaid 166)
```

**This is the defect T264 named, repeated one level out.** T264's charge against `df0aed2c` was that
it measured one of two laws and affirmed the other sound *without testing it on the domain it had
just written*. T277 measured law (ii) on the cells that motivated the edit and corrected the block
that fences it — and did not test whether the same law lives elsewhere **in the very file it was
editing**. Its own follow-up 3 scopes the open sweep as *"restatements of law (ii) **outside**
`gates.md`"* and asserts *"I corrected **the one** live statement I own"*. There are at least six
live statements in the one file it owns.

**The severity is bounded, and I state the bound because a law wrongly accused is as bad as one
wrongly trusted:**

- **The direction is SAFE.** On both scopes, the number of cells where the OBSERVED residual
  **exceeds** the formula is **0**. So `min(B_minor, n·δ)` survives as a valid **upper bound** on
  unamortized exposure. Nothing under-states risk. What is false is the asserted **equality**.
- **No record figure moves.** Re-measured from the principal column on the `all` scope: largest
  unamortized residual **3000** (`T219-…-B3001`, `T219-…-B4499`), largest FULL family-B residual
  **2999** (`B2999`), largest failing disbursement **4499** (`B4499`) — the three figures the GATE
  REGISTER carries, unchanged. `[VERIFIED: evidence/41-t278-domain-audit-all.txt]`
- **G-8's conservative region survives, and I tested it rather than taking T277's word.** With
  `B_minor < 1.5·n` written in integers as `2B < 3n`: **failing cells OUTSIDE the region = 0** on
  both scopes, and **all seven exceptions are inside it**. The superset claim holds.
- **No promoted vector is affected.** `.softhouse/vectors/` contains no restatement of law (ii)
  (`grep -rn 'n·δ\|n\*delta\|B_minor' .softhouse/vectors/` → no match). The exempted
  `T116-G8-FAMB-*` vectors state a per-cell observed fact ("every repayment row carries principal
  0.00") about `n = 108, B = 1`, which my census confirms repays 0 and satisfies law (ii). The
  seven are all `B = 11` or `B = 999`.

**Remedy: a follow-up task, not a revert.** Either scope the five sites to the exception set, or —
better, and this is a reviewer's recommendation not a ruling — state the residual as
`residual ≤ min(B_minor, n·δ)`, with equality **outside** the seven, which is the strongest form
that is true on the whole domain and is the form the disclosure instruction at `:3679` actually
needs. `.softhouse/gates.md` is not mine to edit and I did not touch it.

---

## 3. PER-ITEM GRADES

### 1. The seven cells — **REPRODUCED. CORROBORATED, not merely accepted.**
Third instrument, no shared code, integer minor units, principal from the column. All seven, to the
unit, including the 166. See §1. **GRADE: PASS.**

### 2. The disjointness claim — **VERIFIED, and T277 did check amount-for-amount.**
My own measurement `[VERIFIED: evidence/30-t278-census.json]`:
`exceptions ∩ δ = 0` → **0**; `exceptions ∩ the 76 FACT-A failures` → **0**;
`exceptions_all_satisfy_fullFamilyB` → **True**; and the resolving fact —
**all 76 FACT-A failures are `δ = 0`, but only 76 of the 113 `δ = 0` cells fail FACT A; the other
37 hold it.** My amounts in id order: `[5, 4, 2, 5, 4, 2, 166]`, exactly gap 2's own list.

**And I checked that T277 did what it said, rather than counting to seven twice**
`[VERIFIED: crosscheck_seven_t277b.py:80-87, :448-449]`: the expectation is a tuple table carrying
`(id, n, B, E, I₁q, δ, predicted, OBSERVED)` per cell, graded by
`tuple(sorted(observed_tuples)) != tuple(sorted(EXPECT_SEVEN))` — a full tuple comparison including
the amount. Independently corroborated by the fact that mutation **M3**, which changes only `166` to
`165`, trips. A cardinality check could not do that. **GRADE: PASS.**

### 3. No float in any instrument — **PASS, and the driver's false-positive class is confirmed, not inherited.**
`[VERIFIED: evidence/60-t278-float-audit.txt]` My auditor classifies rather than counts. HARD hits
(literals, `/` nodes, `float()`/`round()` calls, `decimal`/`fractions`/`math`/`numpy` imports):

```
shapelaw_census_t277.py     HARD=0  BENIGN=1
crosscheck_seven_t277b.py   HARD=0  BENIGN=1
dump_seven_t277.py          HARD=0  BENIGN=0
t278_rederive.py            HARD=0  BENIGN=0     (mine)
t278_domain_audit.py        HARD=0  BENIGN=0     (mine)
t278_float_audit.py         HARD=0  BENIGN=0     (mine)
verify_t277.sh              decimal-looking literals: none
```

The two BENIGN hits are `shapelaw_census_t277.py:588` and `crosscheck_seven_t277b.py:339`, both
literally `isinstance(node.value, float)` inside those files' own float **detectors**
`[VERIFIED: sed -n '585,591p'` and `sed -n '336,342p'`]. **`FU-T277-7` confirmed** — the driver's
2 violations are the detector naming the type it detects. I did not repeat the driver's error and I
did not let it excuse anything: my auditor still reports a bare `float` identifier **outside** an
`isinstance`/type-comparison position as HARD, and found none. My own instrument additionally
**refuses at runtime** to parse a money field that arrives as anything but a string, so no JSON
float can enter through the data either. **GRADE: PASS.**

### 4. G-8's substance and the GATE REGISTER row — **UNCHANGED, byte-checked.**
`[VERIFIED: git diff 30fbdefe e8374743]` The merge touches 18 files: the capture directory, the
handoff, and `gates.md` at **194 insertions / 1 deletion**. The single deleted line is
`The shape of an **unrescued** cell follows from FACT A plus the deficit carry:` and its replacement
**preserves that text verbatim** as its opening clause. The fenced law block is byte-unchanged
(present at `:2295` before and `:2298` after — the shift is the four inserted lines above it).
`gates.md:30`, the GATE REGISTER row for G-8, is **byte-identical across the merge** (`cmp` clean),
and it still carries the conservative superset `B_minor < 1.5·n`, the unproven `δ ≤ 1`, and
"options (b)/(c) STILL MUST NOT be put to Buyan". No `DEC-n`, no vector, no Go file, no
`conformance.sh` touched. **And I measured the substance rather than reading the assertion**: the
conservative region is still a genuine superset — 0 failing cells outside it on either scope, all
seven exceptions inside it. **GRADE: PASS.**

### 5. The re-bucketing instrument RE-RUNS — **YES. I ran it.**
`bash .softhouse/capture/t277-shapelaw-salvage/src/verify_t277.sh` → **exit 0**
`[VERIFIED: evidence/50-t278-ran-verify_t277.txt]`:

```
  PASS-CASE  ok    census --selftest
  PASS-CASE  ok    census both scopes
  PASS-CASE  ok    seven-cell row dump
  PASS-CASE  ok    cross-check --selftest
  PASS-CASE  ok    cross-check t229corpus
  FAIL-CASE  tripped  M1 census: law (ii) pinned 220/220 on FACT A (df0aed2c's claim)
  FAIL-CASE  tripped  M2 census: T159-R600p0-N2000-B999 dropped from the exception set
  FAIL-CASE  tripped  M3 cross-check: 165 minor units expected where 166 is measured
  FAIL-CASE  tripped  M4 cross-check: I1q read from the schedule instead of computed
  T277 VERIFY: PASS
```

The positives **re-run both censuses over the raw `.json.gz`**; this is not a transcribed table.
**GRADE: PASS.**

### 6. T277's own three findings

**`FU-T277-4` (the `I₁q` dead end) — FULLY CLOSED, and independently reproduced.**
My instrument carries its own `--i1q-from-row` switch, written from my definitions, not T277's
`[VERIFIED: evidence/42-t278-i1q-trap.txt]`:

```
  correctly computed  : delta histogram {'0': 113, '1': 183} , law (ii) fails on 7
  I1q read from row 1 : delta histogram {'0': 296}           , law (ii) fails on 183
  all stuck cells forced to delta=0 by that route? True
```

**183, exactly as claimed.** The trap is real, is landed in `gates.md` inside the correction block,
and is reproducible on demand from *two* independent instruments. **GRADE: CLOSED.**

**`FU-T277-5` (the false green in its own verifier) — CLOSED, and I have the transcript it needed.**
Pressed hardest, per the brief. I did not accept "I fixed it": I rebuilt the meta-calibration from
outside, in `probe/t278_meta_calibrate.sh` `[VERIFIED: evidence/51-t278-meta-calibration.txt]`.

- **B1 — the anchor-moved no-op.** I copied the whole `src/` to scratch, repointed M1's mutation at
  a string that is not in the census **and removed the mutation's own `assert`**, so that nothing
  but `mutate()`'s no-op guard stood between it and a false green. Result:
  `ABORT: mutant m1.py is byte-identical to shapelaw_census_t277.py -- the edit was a no-op.`
  **exit 2.** The fix holds under a harder version of its own test.
- **B2 — a negative repointed at `true`.** `FAIL-CASE DID NOT TRIP M4 (B2-NEUTERED: pointed at
  true)`, `T277 VERIFY: FAIL`, **exit 1**. The verifier notices a negative that cannot fail.
- **B3 — the property `FU-T277-5` actually generalises to: did each mutant BUILD?** All three
  delivered mutants **parse**, run **without a traceback**, and exit 1 on a **graded** assertion
  (`RESULT: FAIL — EXCEPTION SET moved`, and so on). **Every trip in the delivered verifier is
  EARNED.** See `F-T278-2` for the residue.

**GRADE: CLOSED for the delivered artifact; one MINOR residue filed.**

**`FU-T277-6` (the `:1868` citation) — SUBSTANCE VERIFIED, and its own cardinal is one off.**
On `main` immediately before the merge (`30fbdefe`) `[VERIFIED: git show 30fbdefe:.softhouse/gates.md
| sed -n '1866,1872p'` and `| grep -n 'Seven corpus cells'`]: line 1868 sits inside the
answered-questions bullet whose sentence at 1869–1870 reads *"See gap 2 of SITE 3, CHARACTERISED
below."* Gap 2's enumerated item **begins at `:2348`** and its `N2000-B999` line is at `:2351` —
**480 lines lower.** The finding is correct. See `F-T278-3`. **GRADE: CLOSED, with a nitpick.**

---

## 4. FINDINGS

### `F-T278-1` — **MAJOR** — the fix repeats the shape of the defect it fixes, one level out
Law (ii)'s algebraic twin `residual = min(B_minor, n·δ)` is stated **live and unqualified at five
sites in `gates.md`** (`:1164 :1891 :2603 :3543 :3679`, plus a sixth restatement of law (ii) proper
at `:1865`), none of them reached by `#### CORRECTION (T277)` at `:2308`. **Measured false on
exactly the same seven cells, in both scopes.** One of the six (`:3679`) is a **prescriptive
disclosure instruction** for G-8, so the falsehood sits in an instruction, not only in a narrative.
T277's follow-up 3 scopes its open sweep as "outside `gates.md`" and asserts it corrected "the one
live statement I own". **Bounded:** direction is safe (0 cells where observed residual exceeds the
formula), no record figure moves, the conservative region is still a genuine superset, no vector is
affected. **Remedy:** a follow-up task scoping those sites, or restating the form as
`residual ≤ min(B_minor, n·δ)` with equality outside the seven. Not a revert.
`[VERIFIED: evidence/40-, 41-t278-domain-audit-*.txt]`

### `F-T278-2` — **MINOR** — `mutate()` proves the edit APPLIED; it does not prove the mutant BUILDS
`FU-T277-5`'s own generalisation is *"a negative case must prove the mutant was BUILT, not merely
that the run exited non-zero."* What `verify_t277.sh:mutate()` enforces is: the copy succeeded, the
edit script exited 0, and the result is not byte-identical. That is strictly weaker — a mutation
that produces a `SyntaxError` satisfies all three and would still be scored `tripped`. **The
delivered mutants are fine** (B3: all three parse and trip on a graded assertion), but **M2 is a
line-deletion mutation**, the class most likely to produce an unparseable mutant after a future
edit. **Remedy:** one line in `mutate()` — `python3 -c "import ast;ast.parse(open(...).read())"` on
the mutant, fatal on failure. `[VERIFIED: verify_t277.sh:56-84; evidence/51-t278-meta-calibration.txt]`

### `F-T278-3` — **MINOR (P-86, in the small, a third time in the same lineage)** — the citation finding's own cardinal is off by one
T277's handoff states *"Gap 2 itself was at line 2349"*. On `30fbdefe` the item begins at **`:2348`**.
T277's *supporting* evidence (`grep -n "N2000-B999"` → 2351) is exact, so the substance is verified
and only the unsupported prose ordinal is not. **The landed `gates.md` text is clean** — it says
"roughly 480 lines above" and points at a grep-able heading, never an ordinal. This is a handoff-prose
defect only. `[VERIFIED: git show 30fbdefe:.softhouse/gates.md | grep -n 'Seven corpus cells']`

### `F-T278-4` — **INFO** — the bar baseline in my dispatch brief does not match the tree I was given
The brief states current `main` reads LEDGER parity **7**, money cells **39**, **12/12** wrong ledger
implementations DIED, dead-path frontier **109**, corpus **1237**. On this worktree (branch point
`5a306243`) the bar reads LEDGER parity **5**, oracle-refusal **5**, money cells **29**, **11/11**
DIED, dead-path frontier **11 (pinned 11)**. Exit 0, probe PRESENT reading `up`, **46 vectors /
7884 cells** all match. **Not a T277 defect and not a T278 defect** — T277 moved no vector, no Go
file and no harness file, and my branch adds only files under `.softhouse/reviews/t278-review-t277/`.
Recorded because a later reader comparing the two baselines would otherwise think something regressed.
`[VERIFIED: evidence/70-t278-conformance-bar.log:127, :517-539, :92, :549-551, :566]`

---

## 5. `bash .softhouse/conformance.sh`

Run with **`bash`**, never `sh`/`zsh`/`dash`. **Staged before running** (`git add -A`;
`git status --short` empty). Run on the delivered tree.

**P-84 applied in the right order — PRESENCE before VALUE.**

- **probe line PRESENT** — `evidence/70-t278-conformance-bar.log:127`:
  `conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`
- **probe VALUE** — `up`; summary `oracle probe UP` at `:136`.
- **exit 0.**

```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
  parity vectors      PASS 46  FAIL 0        contract-refusal PASS 4 FAIL 0
  invariant violations 0
  no-float census     6 Go packages / 59 Go files — 0 forbidden identifiers, 0 FP literals
  all 11 wrong ledger implementations DIED through this harness, not by hand.
  dead-path frontier: GREEN, frontier 11 pinned at 11
```

I made **no POST to the reference oracle** and no oracle contact of any kind from any of my
instruments — all three read only committed `.json.gz` bytes and repository text.

---

## 6. Scope — what I touched

`git diff --name-only 5a306243 HEAD` is **`.softhouse/reviews/t278-review-t277/` and nothing else**
(16 files: `REVIEW.md`, 4 `probe/`, 11 `evidence/`), plus this task's handoff. **I edited no file of
T277's.** Specifically untouched, as required: `.softhouse/gates.md`, `.softhouse/conformance.sh`
(T331), `nexus/internal/apps/ledger/conformance/admit.go` and
`.softhouse/vectors/capabilities-ledger.json` (T322), `.softhouse/bin/fire-program.sh` (T301),
`.softhouse/capture/t316-dead-path-guards/` (T321), `.softhouse/patterns.md`, `.softhouse/gates.md`,
`tasks.json`, `program.json`, every `DEC-n`, every vector. **Everything I found is a finding, not an
edit.**

*(Note for the reader: `git diff main HEAD` on this branch shows unrelated files, because `main` has
advanced to `5301f24b` since my branch point. The true change set is `git diff 5a306243 HEAD`. Same
two-dot-against-a-moved-tip caution T277 recorded for itself.)*

---

## 7. What I did NOT verify — stated as a statement about my search

- **The mechanism behind the seven.** I confirmed the whole discrepancy is confined to the last row
  and closes as `max(0, E + B − I_last)` on 220/220 and 441/441, and I derived `I_last` no further
  than T277 did. I asked the oracle nothing and guessed nothing. Gap 2 stays open. `[UNVERIFIED]`
- **`δ` for `T84-RP-R7p0-N56-B23`.** Excluded by my instrument too, on the same ground (`7/1200`
  does not terminate inside 19 fractional digits). Every `δ`-dependent figure above is silent about
  it. `[UNVERIFIED]`
- **Restatements of law (ii) outside `.softhouse/gates.md` and `.softhouse/vectors/`.** My repo-wide
  grep hit `gates-proposed-answers.md:214`, T229's `PREDICTION.md` / `site3.py`, T219's
  `PREDICTION.md` / `site3.py`, and several handoffs. **I did not grade those** — committed evidence
  and prediction registers are correcting-forward territory (T114/T176/T316), and I make no claim
  about them beyond noting they exist. `.softhouse/gates-proposed-answers.md:214` is the one live
  non-evidence file among them and a follow-up should look at it. `[UNVERIFIED]`
- **T277's `all`-scope figures as *independent confirmation*.** They are not, and neither are mine:
  no document predates either instrument for that scope. Mine reproduce T277's, which makes them a
  cross-check, not a prior-publication match. Only the `t229corpus` figures reproduce numbers
  published before any of the three instruments existed.
- **The rejected cloud branch's scope-table rebuild, `CORRECTION-T241.md` and `G-8-NOTICE` ruling.**
  I re-ran none of them and make no claim. `[UNVERIFIED]`
- **`.softhouse/reviews/t264-*` does not exist.** I looked: `ls .softhouse/reviews/` — T264's review
  is a commit message on `406cfb06`, not a review file. T277 recorded the same; I confirm it.

---

## 8. Instruments committed under `probe/`

| file | what it does |
|---|---|
| `t278_rederive.py` | the third derivation. Integer minor units, exact rational rates, HALF_UP as `(2a+b)//(2b)`, 19-digit termination test, completeness refusal, `--selftest` with hand-checked arithmetic and an AST money+independence audit of itself, `--scope`, `--seven`, `--i1q-from-row`, `--json`. |
| `t278_domain_audit.py` | grades the claims the correction leaves standing: the residual form on every stuck cell, the conservative-region superset claim, the three record figures, and the `I₁q` trap. |
| `t278_float_audit.py` | classifying no-float auditor (HARD vs BENIGN-detector) over all six Python instruments, T277's and mine. |
| `t278_meta_calibrate.sh` | reviewer-built meta-calibration of `verify_t277.sh`: B1 anchor-moved no-op, B2 un-failable negative, B3 does each mutant actually build. |
