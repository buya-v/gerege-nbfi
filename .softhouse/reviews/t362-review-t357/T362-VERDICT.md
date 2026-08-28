# T362 — INDEPENDENT review of T357

Reviewed: `softhouse/T357-a2-11-section1-red`, head `85a30a79`, 32 files / +4832 / -76,
forked from `e0819a76`. Reviewer branch `softhouse/T362-review-t357`.
Reviewer rig and raw output: `rig/` and `evidence/` beside this file.

## VERDICT: **APPROVED** — merge it.

Two findings against the deliverable (F-1, F-2) are real fail-opens in the guard layer and
must be filed as follow-ups, but **both are strictly narrower than the fail-open the branch
removes**, and the facts they would fail to catch are, today, independently measured TRUE by
me. Rejecting would leave a measured, live fail-open on `main` in order to punish a smaller
one. Four further findings (F-3..F-7) are minor.

I did **not** call MICRO-FIX. The two fixes worth making are new guard assertions — logic,
not mechanics — and the files are in T357's scope, not mine.

---

## THE FINDING THE WHOLE TASK RESTS ON: the corpus-isolation proof

**T357's answer is CORRECT. No currently-graded vector is touched by the three section-1
failures. The driver's report that the corpus is unaffected was right.**

I re-derived all three legs without reusing T357's tooling or its seven tokens.

### Leg 1 — token absence, on a token list I built myself

T357 searched 7 tokens. I constructed **38** from the three failing assertions
(`check-shape.py:104-106`, the labels `"  <field> present and null"`) and their subject
matter: the three collection field names, all nine write→read accounting-mapping slot names
in both spellings, the three accrual receivables, six spellings of "loan product", the
schema column `m_product_loan`, `product_id`/`productId`, the review's own provenance tokens
(`a2-11`, `A2-7`, `A2-211`, `tierA-a2`, `check-shape`), the assertion text itself, and the
port-side concepts `omitempty` and `serializeNulls`. Searched against **all 69 files under
`.softhouse/vectors/`** and against **three** versions of `conformance.sh` — T357's
fork-point copy (4132 lines), **current `main`'s (4441 lines, which T357 never saw)**, and
**`softhouse/T358-t323-conditions`' (4729 lines)**. `evidence/10-token-sweep-38-tokens.txt`.

Every subject-matter token is **0** in every conformance.sh. Five tokens my broader list
found that T357's seven did not have non-zero counts in `vectors/`:

| token | vectors | where |
|---|---|---|
| `loanPortfolioAccount` | 2 | prose: `capabilities-ledger.json:34` `evidence`, `LDG-04:8` `_note` |
| `chargeOffExpenseAccount` | 1 | prose: `capabilities-ledger.json:84` `evidence` |
| `m_product_loan` | 3 | prose `_note`/`evidence` |
| `product_id` | 18 | prose `_note`/`evidence` |
| `tierA-a2` | 12 | `provenance.capture_ref` / `request_capture_ref` of six **ledger** vectors |

The sweep carries a positive control (`loanschedule`, `ledger`, `principal_minor`,
`capture_ref` all non-zero) so a zero row is an absence, not a blind grep.

### Leg 2 — a STRUCTURAL walk, because a token list only sees the tokens you thought of

`rig/t362-structural-vector-scan.py` parses every vector with `parse_float=Decimal`, walks
the whole JSON tree, and separates hits in free-prose fields (`_note`, `evidence`,
`citation`, …) from hits anywhere else. `evidence/11-structural-vector-scan.txt`:

- **6** hits inside prose — these grade nothing.
- **12** hits outside prose, and every one is a `provenance.capture_ref` or
  `provenance.request_capture_ref` on a **ledger journal-entry** vector, pointing at
  `A2-337/338/343/344/345/346/347/382/383/390` — journal entries and one DB read-back.
- **Zero** hits in `request`, `expect`, `oracle`, `capabilities_required` or `graded_against`
  on any vector.
- Positive control: 104 non-prose scalars contain `loanschedule`, so the walker is not blind.

**I also enumerated `provenance.capture_ref` myself:** 23 distinct values across the 68 JSON
files — 22 real plus the empty string. None points at a loan-product read. Every real one is
`loanschedule` capture (`capture-prod3*`, `t116-*`, `pathb/t149`) or `ledger` capture
(`t287`, `t294`, `t305`, `t327`, `tierA-a2/A2-3xx`). T357's count and conclusion reproduce.

### Leg 3 — the call graph, re-derived on CURRENT main, not T357's fork point

`conformance.sh` on `main` (4441 lines): `HARNESS_PKG` / `CMD_PKG` at **:410-411** point at
`internal/apps/loanschedule/conformance`; the ledger arm's `vecdir` at **:2312** is
`.softhouse/vectors/ledger`. Same lines as T357 cited, on a file 309 lines longer. There is
no loan-product arm. `bash .softhouse/conformance.sh` on `main + T357`:

- probe line **PRESENT** (checked before its value, P-83) → `probe = up`, `oracle probe UP`
- `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
  compared` — identical to the number T357 recorded.
- `evidence/70-conformance-main-plus-T357.txt`

**Independent root fact.** `evidence/51-a2211-root-fact.txt`: in
`capture/tierA-a2/out/A2-211-read-product-nine-mandatory.json` (7489 bytes, sha256
`fc70e10b…`) each of the three key names occurs **0** times, the literal `null` occurs **0**
times, no key has value `None`, and the only Account/Mapping keys are
`accountMovesOutOfNPAOnlyOnArrearsCompletion`, `accountingMappings`, `accountingRule`.
A2-7's excerpt was fabricated; the RED is the correct verdict. [VERIFIED: that capture file;
`A2-11.md:429+`, `A2-7.md:211-221`, `A2-8.md:101+`, `patterns.md:1508-1532` all read and
matching]

---

## (a) run-all.sh really did exit 0 no matter what — MEASURED, not inferred

On a clean checkout of **current `main`** (pre-T357):

```
$ bash .softhouse/reviews/A2-11/run-all.sh ; echo $?
0
```

and its own transcript, written in the same run, records **six `exit=1` lines and five Python
tracebacks**. `evidence/20-runall-BEFORE-on-current-main-exit0.txt`,
`evidence/21-runall-BEFORE-transcript-6-reds-5-tracebacks.txt`.

Mechanism confirmed at the source: the old file has **no** `set -e`, **no** `set -o
pipefail`, **no** `PIPESTATUS`, and **no** `exit` — its last command is
`{ … } 2>&1 | tee "$DIR/TRANSCRIPT-A2-11.txt"`, so the script's status is `tee`'s. [VERIFIED:
`git show main:.softhouse/reviews/A2-11/run-all.sh`]

**Can the new VERDICT block regress to it?** I read every escape path and could not find one:

- the per-section codes are appended to a `mktemp` file, so they survive the `| tee` subshell;
- the verdict is written to `"$STATUS.rc"` **inside** the subshell and read **outside** it;
- `RC=$(cat "$STATUS.rc" 2>/dev/null || echo 1)` — if the block dies, if `tee` dies and
  SIGPIPEs the block, or if the file is never written, **RC=1**. Fail-closed;
- an empty or non-numeric `.rc` makes `exit "$RC"` itself fail non-zero;
- `SECTIONS -ne 9` (too few **or** too many) is FAIL, so a section that did not run is never
  read as a pass;
- `DEVIATIONS` is bounded by 9, so `exit "$RC"` cannot wrap to 0.

And it is not merely argued — I watched it fail. My first run of the new `run-all.sh` was in
a fresh clone lacking the local ref `softhouse/A2-7-capture-mandatory-accounts`; section 5
died, moved off its adjudicated RC 0, and **`run-all.sh` exited 1 with `*** MOVED ***`**
(see F-6). With the ref present it exits **0**, 9/9 as adjudicated, 0 deviations —
reproducing T357's headline claim **on the merge result with current main**, not just on its
fork point. `evidence/22-runall-AFTER-on-merge-result-exit0.txt`.

---

## (b) BOTH directions driven RED by me, on real bytes

T357's in-file controls (a) and (b) are pure-function tests: they feed `parse_verdict` a
fabricated string. That is not the same thing as the pipeline going red. I drove the real
one. `rig/t362-drive-red-both-directions.sh`, `evidence/30-drive-red-both-directions.txt`.

**D1 — VANISHED (the dangerous direction, and the easy one to fake).** I injected **all
three** fabricated fields as JSON `null` into the real
`obs/a2-11-get-loanproduct-46.json` — i.e. I forged exactly A2-7's claim into the evidence:

```
check-shape.py             rc=0   PASS paymentChannelToFundSourceMappings present and null -- None
                                  PASS feeToIncomeAccountMappings present and null -- None
                                  PASS penaltyToIncomeAccountMappings present and null -- None
                                  FAILURES: 0            <-- section 1 now looks HEALTHY
adjudicate-section1.py     rc=1   FAIL check-shape.py exits 1 (RED)
                                  FAIL all three adjudicated failures are STILL PRESENT
                                       missing=[all three, named]
run-all.sh                 rc=2   sections 1 and 9 *** MOVED ***, RUN-ALL VERDICT: FAIL
```

Two independent layers caught it. The dangerous direction is genuinely covered.
(T357's own NC2 injects only one of the three; mine injects all three, which is the stronger
forgery, and it is still caught.)

**D2 — FOURTH failure.** I mutated the observed `name` on `obs/a2-11-get-glaccount-2.json`:

```
check-shape.py             rc=1   FAILURES: 4, the fourth named
adjudicate-section1.py     rc=1   FAIL NO UNADJUDICATED FAILURE
                                       unexpected=["  GET /glaccounts/2 glCode 10100, name 'Fund Source', type INCOME"]
run-all.sh                 rc=1   section 9 *** MOVED ***, RUN-ALL VERDICT: FAIL
```

Both mutations reverted with `git checkout --`; `git status --porcelain` clean after each.

---

## (c) check-shape.py and obs/** are BYTE-UNCHANGED — verified at the git object level

Stronger than "absent from the diff": I compared blob shas.

- `check-shape.py` blob = `817d152805ba7a31db2df5a6b0897064a3dc7193` at the fork point
  `e0819a76`, at T357's head, **and** at `main`. Three-way identical.
- `git ls-tree -r` over `reviews/A2-11/obs/` at the fork point and at T357's head: **31 files,
  identical mode + blob sha + name on every line.**

The legitimacy claim holds: T357 touched the reading layer and left the evidence alone.

---

## (d) the "output-neutral" claim for the five `__file__` reroots — REPRODUCED

I did not use T357's `diff-sections.py`. `rig/t362-section-diff.py` slices each section body
out of the **2026-08-21T08:11:39Z committed transcript as it stands on `main`**, runs the
T357-patched script for that section fresh, and diffs. `evidence/40-section-diff-t362-independent.txt`:

| section | script | result |
|---|---|---|
| 1 | check-shape.py | **IDENTICAL** (65 lines) |
| 2 | enumerate-corpus.py | **IDENTICAL** (61 lines, including its three findings against A2-7) |
| 3 | verify-double-entry-minor-units.py | **IDENTICAL** (44 lines) |
| 4 | verify-manifest-independently.py | DIFFERS — manifest 571 → 1139, delta 141 → 709 |
| 5 | audit-float.py | DIFFERS — enumerates the current rig, which has grown |
| 6 | prove-resolve7-float-red.py | **IDENTICAL** (29 lines) |
| 7 | prove-a2-7-guards-are-falsifiable.py | **IDENTICAL** (44 lines) |

`T362 MEASURED identical: [1, 2, 3, 6, 7]` — **MATCHES T357'S CLAIM** exactly, and the two
that differ differ for the reason stated at each site. The substitution
`parents[3]` is also correct in a plain checkout, in a worktree, and in a clone, which is a
genuine portability gain over the retired absolute path.

---

## (e) section 4's 428/430, and the out/ + req/ integrity claim

Fresh run of `verify-manifest-independently.py` on the merge result: **430 pre-existing
entries, 428 byte-identical, 2 DIFFER (`CAPTURE-PLAN.md`, `cap.sh`), 0 missing, 0 unreadable,
current manifest agrees with disk on all 430.** T357's figure reproduces.

**I recomputed it independently rather than trusting that script** (`rig/t362-section4-absorption-probe.sh`
P1, `evidence/31-section4-absorption-probe.txt`): the fork sha `12a7f8d9` holds **431** files
under `capture/tierA-a2` — 25 top-level, **327 `out/`**, **76 `req/`**, 3 `sql/`. Comparing
each git blob against disk today: **0 missing, 3 differing** — `CAPTURE-PLAN.md`, `cap.sh`
and `MANIFEST.sha256`. (The script says 2 because its population is the 430 manifest entries,
which exclude the manifest itself; section 4 arm 4 names `MANIFEST.sha256` separately as the
only non-Added path on the branch. No discrepancy, two populations.)

> **DIFFERING under `out/` or `req/`: 0.**
> T357's claim *"No captured oracle observation under `out/` or `req/` has been mutated"* is
> **CONFIRMED** by my own recompute.

---

## FINDINGS AGAINST T357

### F-1 · MATERIAL — section 4's adjudicated RC 1 **absorbs** a mutated oracle observation

T357 adjudicates section 4 to RC 1 and tells the reader the reason is drift, adding: *"If it
ever stops being true, §4 says so by name."* It says so **in printed text only**. Section 4
already exits 1 because of the two count arms, so the evidence-integrity arm is **saturated**:
it cannot make the section any redder, and `run-all.sh`'s verdict therefore cannot see it.

**PROVED.** I appended a marker to a pre-existing captured oracle observation,
`.softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http`:

```
verify-manifest-independently.py  rc=1   byte-identical 427, DIFFER 3,
                                         DIFF out/A2-000-glaccounts-preexisting.http   <-- detected
run-all.sh                        rc=0   4  EXPECTED 1  ACTUAL 1  "as adjudicated"
                                         deviations: 0
                                         RUN-ALL VERDICT: PASS
```

A mutated captured oracle observation produces **exit 0 and the word PASS**. That is the same
defect class T357 removed one level up — a verdict that cannot distinguish "still fine" from
"newly broken". *(Not a regression: before T357 the runner reported 0 unconditionally, so this
was equally invisible. But the handoff's sentence claims more than the code delivers.)*

**Fix shape (do not let this evaporate):** split section 4 into a drift arm (adjudicated RED,
allowed to rot) and a **byte-identity arm with its own exit code**, adjudicated GREEN, so the
aggregate can see it. T357's own OPEN item 3 proposes exactly this split; F-1 is the
measurement that makes it load-bearing rather than tidy-up.

### F-2 · MODERATE — the new corpus guard passes **VACUOUSLY** over an empty population

`adjudicate-section1.py` §4 builds `vector_files` with `(SOFTHOUSE / "vectors").rglob("*")`
and asserts every token count is 0. It **prints** the population size and **never asserts it**.

**PROVED** (`evidence/30-drive-red-both-directions.txt`, D3). With `.softhouse/vectors/` moved
aside, the adjudicator reports:

```
(population searched: 0 files under .softhouse/vectors/, plus conformance.sh)
PASS  NO vector in the store ... the three failures touch NOTHING in the graded corpus
PASS  NO vector's provenance.capture_ref points at a loan-product read
      0 distinct capture_ref values inspected
rc=0
```

T357 markets this as *"executable and permanent, not a paragraph"* and *"goes RED if any count
stops being zero"*. It also stays GREEN if there is nothing to count. That is a positive-control
gap in the file that spends 60 lines prosecuting positive-control gaps (P-22, P-45).
*Mitigation, stated so the severity is not overstated:* `conformance.sh`'s
`guard_accepting_side_gap_declared` fails closed on a missing ledger vecdir, so the store
actually vanishing would be caught elsewhere.

**Fix shape, ~3 lines, for T357 or a follow-up to apply (I did not, see verdict note):**
```python
check("POSITIVE CONTROL — the vector store was actually READ; a zero-hit table over an "
      "empty population is a vacuous pass", len(vector_files) > 0,
      "%d files under .softhouse/vectors/" % len(vector_files))
```

### F-3 · MINOR — negative control (a) prints a false message when it matters most

`fake4 = r1.stdout + …` derives the synthetic transcript from the **live** stdout. When the
tree genuinely carries a fourth failure, `n4 - ADJUDICATED` holds two entries, the equality
check fails, and the file prints:

```
NEGATIVE CONTROL DID NOT TRIP: (a) a FOURTH failure is detected as UNADJUDICATED
```

Observed in my D2 drive. It is fail-**closed** (it adds a failure), but the message is wrong —
the control tripped harder than expected — and it appears in exactly the situation the guard
exists to make legible. Use a fixed synthetic base rather than `r1.stdout`.

### F-4 · MINOR — the capture_ref enumeration covers one of two provenance ref fields

The regex `"capture_ref"\s*:\s*"([^"]*)"` does **not** match `"request_capture_ref"`, which
exists on six ledger vectors. I enumerated it myself: all six point at journal-entry `.req`
captures, so **the conclusion is unaffected** — but the permanent guard does not look there.
Also, of the 68 JSON files only **64** carry a `capture_ref` at all (PIN.json, PIN-ledger.json,
capabilities.json, capabilities-ledger.json carry no `provenance` block), and 5 of the 23
distinct values are the **empty string** (the selftest and the four contract-refusal vectors).
"All 23 distinct values cited by the 68 JSON files" overstates the coverage slightly.

### F-5 · MINOR — the T356 disclosure is complete for scripts, incomplete for tracked evidence

T357 discloses **six** edited files with an exact revert per file. `git diff --name-status
e0819a76 85a30a79` shows **seven** modified tracked paths: the six plus
`.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt` (367 lines changed), which has no revert entry.
The transcript is not a script, so it is arguably outside the class T356 owns — but it **is**
committed evidence, it is overwritten by this branch, and it is overwritten again by every
subsequent `bash run-all.sh` (line 2 carries a generation timestamp). T357's R1 sentence
*"check-shape.py and every byte under obs/ are untouched"* is TRUE and I verified it at blob
level; a reader should not extend it to "no committed evidence was rewritten".
**I am not re-deciding T356's rule** — I am grading the disclosure, and this is the one item
missing from it. Practical consequence for the driver: re-running `run-all.sh` on the merge
result will dirty a tracked file; `git checkout -- .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt`
afterwards.

### F-6 · MINOR — `run-all.sh` needs a **local** branch ref, and the new verdict makes that fatal

Section 5 (`audit-float.py`) runs
`git diff … 12a7f8d9…softhouse/A2-7-capture-mandatory-accounts`. In a fresh clone, where only
`origin/softhouse/A2-7-capture-mandatory-accounts` exists, this raises
`CalledProcessError … returned non-zero exit status 128`, section 5 moves off RC 0, and
`run-all.sh` exits 1. Pre-existing (it comes with the P-24 literal-sha design), **not**
introduced by T357 — but before T357 it was invisible and now it is a FAIL. Anyone reproducing
this review outside the working repo must create the local ref first. Recorded because a
future reader hitting exit 1 will otherwise think T357 broke something.

### F-7 · COSMETIC — P-46 cited at `patterns.md:1495-1530`; it is now at `1508-1532`

Content matches exactly, including rule 3. This is the line-number rot P-80 names.
Also, T357 cites two `new GsonBuilder()` sites in `GoogleGsonSerializerHelper.java`
(:53-59, :61-85 — the builders are at **:56** and **:82**); there is a **third** at **:100**,
uncited and also plain. The omission strengthens rather than weakens the conclusion.

---

## THE SOURCE-LEVEL CLAIM — spot-checked in the pinned checkout, not accepted from the citation

`/Users/buv/fineract` @ `426a23544`:

```
$ grep -rn "serializeNulls" fineract-core/src/main fineract-provider/src/main
fineract-core/.../serialization/CommandProcessingResultJsonSerializer.java:38:  builder.serializeNulls();
```

**Exactly one occurrence**, and it is the command-result serializer, as T357 says. [VERIFIED]
`GoogleGsonSerializerHelper.java` builds plain `new GsonBuilder()` at :56, :82 and :100 and
calls `registerTypeAdapters`; no `serializeNulls()` anywhere in the file. The loan-product read
path reaches it: `LoanProductsApiResource.java:160` holds
`DefaultToApiJsonSerializer<LoanProductData>` and :253 / :389 serialise the single-product read
through it. [VERIFIED: those files/lines] Gson omits nulls by default, so **absent-when-unset is
the read-path rule** and A2-7's "opposite way" claim is refuted at the source.

**Re-derived from T357's own fresh capture bytes** (`evidence/50-fresh-vs-obs-byte-identity.txt`):

| read | fresh bytes | sha256 | vs committed `obs/` |
|---|---|---|---|
| `GET /loanproducts/46` | 7510 | `04b14461410412ed…` | **IDENTICAL** |
| `GET /loanproducts/22` | 7726 | `b2c060af179538cd…` | **IDENTICAL** |
| `GET /loanproducts/28` | 7806 | `7d6b4a79af7576d3…` | **IDENTICAL** |
| `GET /glaccounts/2` | 353 | `1d7fc3cb1e0fe2d7…` | **IDENTICAL** |

All five status files read `200`. In the fresh product-46 bytes the three fields are **absent**,
the literal `null` occurs **0** times, and no key has value `None`. Product 22 has
`paymentChannelToFundSourceMappings` **present as a `list`** while its two unset siblings are
**absent** — set → present, unset → absent, never null. T357's contrast case is real.

**The re-observation was read-only.** `re-observe-t357.sh` issues five `curl` **GET**s and
writes only under its own `out/`; no POST/PUT/DELETE, no write to `obs/`. The irreversibility
concern for the shared oracle is not engaged. I fired **no** probe of my own.

**The tenant drift T357 found is real:** the fresh list read returns **33** products against the
committed **27**; ids **54, 55, 56, 57, 58, 60** appeared, none disappeared. Exactly as claimed.
And `check-shape.py:127`'s label *"the list holds 26 products"* asserts a **27**-id list and
prints `27 products` in its own detail string — T357's fourth finding is correct, and it left
the file byte-unchanged, which is the right call.

---

## NON-NEGOTIABLES, CONTRACT, SCOPE — all checked, all clean

`evidence/60-float-and-prohibited-stack-scan.txt`.

- **Money / P-25.** T357's three new Python files (`adjudicate-section1.py`, `patch-roots.py`,
  `diff-sections.py`) have, by AST: **0 float literals, 0 `float()` calls**; import sets are
  `{ast, pathlib, re, subprocess, sys}`, `{pathlib, sys}`, `{difflib, pathlib, re, sys}`. The
  five edited files gain only `import os` / `import pathlib` and one `ROOT`/`RIG` line. Every
  `float`/decimal-literal hit in the branch is inside pre-existing prose or inside
  `prove-resolve7-float-red.py`, whose purpose is to demonstrate double lossiness. **No money
  value is asserted anywhere in section 1** — it compares ids, key sets and strings — so
  `MathContext(19, HALF_UP)` admissibility is not engaged, and I agree with T357's grading of
  this as a **wire-shape** finding, material to the port and immaterial to the corpus.
- **Frozen contract / DEC-n.** Not in the diff. No `nexus/`, no `conformance.sh`, no
  `.softhouse/vectors/`, no contract or DEC-* file is touched. Verified by `--name-only`.
- **Scope.** Every path in the branch is under `.softhouse/reviews/A2-11/`,
  `.softhouse/capture/t357-a2-11-section1-red/`, or `handoff/…/T357.md`. Nothing wandered.
- **Prohibited stack.** 0 added-line hits for `ojdbc`, `oracle.jdbc`, `1521`, `mysql`,
  `mariadb`, `docker-compose-mysql`, `docker-compose-mariadb`, Stripe, Plaid, Lithic, Persona.
- **Deposit / insurance language.** No savings, deposit, insured, protected or guaranteed
  string is added.

---

## FOR THE DRIVER — the two questions you said you would act on

### 1. Is `softhouse/T357-a2-11-section1-red` safe to merge into current `main`? **YES.**

- `git merge` onto `main` is **clean**, no conflicts, tested twice as `main` advanced
  (`f6c83157` → `0dd9c41f` → `635c6f60`; all three merge clean, all three moves were
  dispatch/doc commits that left `conformance.sh` at 4441 lines).
- On the merge result: `bash .softhouse/conformance.sh` → **exit 0**, probe line present,
  `probe = up`, `VERDICT: PASS — 46 parity vectors … 7884 cells`, dead-path frontier **GREEN**
  (`deadOccurrences=109`, which is the pin — T357's comment repair holds on the merge result),
  namespace census PASS, guards-dir registration PASS.
- On the merge result: `bash .softhouse/reviews/A2-11/run-all.sh` → **exit 0**, 9/9 sections at
  their adjudicated codes, 0 deviations. `adjudicate-section1.py` → **exit 0**, 7/7 controls.

**What to re-run on the merge result before believing it, in this order:**

1. `bash .softhouse/conformance.sh` — **read the probe line's PRESENCE before its value (P-83)**;
   then confirm `46 parity vectors / 7884 cells` is unmoved. This is the only check that speaks
   to parity, and T357 moves nothing it reads.
2. `bash .softhouse/reviews/A2-11/run-all.sh` — expect **exit 0** and 9/9 "as adjudicated".
   **You need the local ref `softhouse/A2-7-capture-mandatory-accounts` to exist** (F-6); it does
   in the working repo, it does not in a fresh clone. Afterwards,
   `git checkout -- .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt`, because the run rewrites that
   tracked file's timestamp line (F-5).
3. `python3 .softhouse/reviews/A2-11/adjudicate-section1.py` — expect **exit 0**.
4. Optionally `bash .softhouse/capture/t357-a2-11-section1-red/prove-verdict-can-fail.sh` —
   expect exit 0 and a byte-clean tree afterwards. It mutates and reverts `obs/`; my
   independent equivalent (`rig/t362-drive-red-both-directions.sh`) reproduces its result and
   goes further in the vanished direction.

**Do not read `run-all.sh` exit 0 as "the A2-11 evidence is intact."** Per F-1 it is not
sensitive to a mutated capture under `out/`.

### 2. Interaction with `softhouse/T358-t323-conditions`? **NONE observed.**

- **Zero file overlap.** T357 touches `reviews/A2-11/*`, `capture/t357-*`, `handoff/T357.md`.
  T358 touches `.softhouse/conformance.sh`, `.softhouse/guards/ledgerguard/main.go`,
  `capture/t358-*`, `handoff/T358.md`. T357 does not touch `conformance.sh` at all.
- **Both orders merge clean.** I built `main + T357 + T358` in a scratch clone: both merges
  return 0, no conflicts.
- **The one plausible semantic coupling, tested.** T358 modifies `guard_dead_path_frontier`,
  `guard_guards_dir_registration`, `guard_capture_namespace`, `guard_reconciler_ownership`,
  `guard_accepting_side_gap_declared`, `guard_graded_root_is_this_tree` — and T357 adds tracked
  files carrying repo paths in comments, which is exactly what the dead-path census counts.
  So I ran `bash .softhouse/conformance.sh` on the **combined** tree:
  **exit 0**, probe present / `up`, `VERDICT: PASS — 46 parity vectors, 7884 cells`,
  `dead-path frontier: GREEN`, `deadOccurrences=109` (unchanged), guards-dir registration PASS
  with the population now 6. `evidence/71-conformance-main-plus-T357-plus-T358.txt`.
- T357's 38-token corpus sweep is **0 across T358's 4729-line `conformance.sh`** too, so landing
  T358 does not admit a loan-product arm and does not invalidate the corpus answer.

---

## WHAT I CHECKED AND FOUND NOTHING WRONG WITH — so silence is distinguishable from not looking

- Every `[VERIFIED:]` tag in T357's handoff traced to real source: the `serializeNulls` grep,
  `GoogleGsonSerializerHelper` :53-59 / :61-85, `CommandProcessingResultJsonSerializer.java:38`,
  `check-shape.py:25` and `:47` (`parse_float=Decimal`), `check-shape.py:127`,
  `conformance.sh:410-411` and `:2312`, `A2-11.md:429+`, `A2-7.md:211-221`, `A2-8.md:101+`,
  P-46 in `patterns.md`. Only the P-46 line range had drifted (F-7).
- The four sha256 prefixes in T357's fresh-observation table — all four reproduce exactly.
- The 27 → 33 product-count drift and the six new ids — reproduce exactly.
- The 428 / 430 / 2 / 0 figures in section 4 — reproduce exactly, and I recomputed the
  underlying byte comparison myself from the fork tree.
- `patch-roots.py` is a faithful, non-idempotent, refuse-loudly producer: it asserts each target
  substring occurs exactly once and exits 1 otherwise, so a re-run cannot half-patch.
- `prove-verdict-can-fail.sh` is honest about what it does; its NC1 (missing obs file) and NC2
  (vanished failure) are real mutations of the working tree with verified reverts.
- No arithmetic in this branch produces a monetary value, so there was no money computation to
  re-derive. I state that rather than claiming to have re-derived one.
- I could **not** verify T357's claim that `parents[3]` resolved to `agent-a3ac3d56d665ff7da` in
  the original worktree — that worktree no longer exists (`ls` confirms). **[UNVERIFIED]** by
  direct test. It is, however, supported by the right evidence: the section-by-section
  reproduction of the committed transcript, which I re-derived independently and which is the
  measurement that actually matters.
