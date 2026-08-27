# T129 — independent review of T122 (`softhouse/T122-g8-t114-fixes`), and the rebuilt G-8 scope audit

Reviewer: T129, spawned fresh, worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3f12dc0e10ddf70d`, branch
`softhouse/T129-review-t122` (forked from `main`).

Artefact under review: the G-8 section of `.softhouse/gates.md` on
`softhouse/T122-g8-t114-fixes` (`300b52d`, lines **894–1540**), the handoff
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T122.md`, T122's corrections to
`.softhouse/handoff/…/T112.md` and `…/T100.md`, and the evidence under
`.softhouse/capture/t83-nonamortizing/`, `.softhouse/capture/t100-g8-rescope/` and
`.softhouse/reviews/T84-evidence/`.

Reference oracle (Fineract) pinned checkout `/Users/buv/fineract` at `426a23544`. **I started
nothing, restarted nothing, rebuilt nothing, re-seeded nothing, and wrote nothing to any container
or to the oracle database. I did not contact the oracle at all** — every number below was
re-derived from committed capture bytes with my own from-scratch code, read from committed sources
in this repository, or produced by `bash .softhouse/conformance.sh` on my own branch. **I
synthesised no oracle observation.** I promoted nothing and modified no vector, `PIN.json`,
`capabilities.json`, `contract.go` or `gates.md`.

**Float discipline (P-25).** Every re-derivation below is **exact rational or integer** end to end:
money is parsed to integer minor units by removing the decimal point, rates and gaps are
`fractions.Fraction`, the sub-ulp test is the exact comparison `abs(gap) < Fraction(1, 10**19)`,
and **the printed digit strings are rendered from the exact `Fraction` by integer arithmetic,
rounded HALF_UP** — no `float` is constructed anywhere in my analysis, **not even for display**.
Scripts: `/tmp/t129/t129_ulp.py`, `t129_scope.py`, `t129_scope2.py`, `t129_rp.py`,
`t129_trap.py`, `subset_check.py`. They share no code with T83's, T84's, T100's, T112's, T114's or
T122's classifiers.

---

## VERDICT: **MICRO-FIX**

**The measurement is exact and the corrections are correct.** I re-derived every load-bearing number
in the section from scratch and **all of it reproduced** — 687 / 312 / 29 / 346, the 11-of-12 rate
split, **the 32-row boundary table row for row**, both canonical capture digests, MNT 0.23 /
MNT 2.91 / 12.65× / MNT 1.09, the 59-118-176-234-291 growth series with all five brackets,
761-with-0-diffs and 2525-with-1-diff and all four exit codes, 341 = 312 + 29 and 331 = 198 + 111 +
22, 330/330 and 320-held/22-refuted/0-ties, **and the four exact-rational ulp gaps digit for digit
with the crossing at n = 106 / 107**. F-T114-1, F-T114-2, F-T114-4 and the two probe-source
dispositions (F-T114-5/6) are all correctly applied, and I **re-measured** rather than read back
both of T122's own harmlessness measurements. The `.gz`-vs-`.json` trap is real: **I reproduced
T122's wrong first-run numbers exactly — 16 family-B cells and 3 non-sub-ulp exceptions — and
independently confirmed the extracts are strict content-identical subsets.** Gate discipline is
intact: G-8 stays **OPEN**, (b) and (c) are neither decided, implied-decided nor pre-implemented,
no recommendation language exists, and family attribution is correct at **all 16** sites.

**One prose statement in `gates.md` is false**, and it is false in the same way T122 was dispatched
to fix in T112: the gate now records a **superseded** disposition of `.softhouse/tasks.json`
(*"wholesale from `main`"*), which T122 changed its mind about in a later commit and swept for in
none of the five places it is stated. The correction is five words in one line of `gates.md` and
three lines of `T112.md`; the true values are measured and supplied verbatim below. Five P3 items
follow it. Nothing here touches a number, a family attribution, a gate state or the merge.

**On the `tasks.json` deviation the driver asked me to rule on: T122 is right and the brief was
wrong.** Full ruling in §7.

---

## 0. Baseline, and the environment

```
$ bash .softhouse/conformance.sh                                  (branch softhouse/T129-review-t122)
conformance: reference oracle (https://localhost:8443/…/health) probe = up
    parity vectors          PASS 42   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    self-test fixtures      PASS 1    FAIL 0
    refused 0   inadmissible 0   harness errors 0
    cells compared          5576 graded, 84 ungraded
    invariant violations    0
    invariant assertions    0 NOT RUN
VERDICT: PASS (exit 0)                                            EXIT=0
```

All six invariants **hold 43 / violated 0 / exempt 0 / n/a 0 / not-asserted 0**. Log at
`/tmp/t129/conformance.log`. I ran it with `bash`, never `sh`; `probe = up`, so exit 0 is a real
pass and not an ambiguous exit 2.

```
$ /Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin/gofmt -l ./nexus
nexus/internal/apps/loanschedule/contract/contract.go            <- EXACTLY this, the expected G-3 state
$ (in nexus/) go build ./...                                      exit 0
$ (in nexus/) go test ./...
ok  github.com/gerege/nexus/internal/apps/loanschedule            9.420s
ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance 10.051s   exit 0
```

Go toolchain go1.26.6 at `/Users/buv/gerege-nbfi/.softhouse/toolchain/go` via
`.softhouse/bin/go-env.sh` (P-30 — nothing below is tagged `[UNVERIFIED]` for want of it).

Promotion state on the branch:

```
$ git diff --stat main...softhouse/T122-g8-t114-fixes -- nexus .softhouse/vectors      (EMPTY)
$ git diff --stat main...softhouse/T122-g8-t114-fixes -- \
      .softhouse/capture/{pathb,t91,charges,t108-grep,t74-multiplesof} \
      .softhouse/conformance.sh .softhouse/program.json                                (EMPTY)
contract.go     softhouse/T122… 4bcbafad…   main 4bcbafad…      identical, never gofmt'd
PIN.json        softhouse/T122… b51595bb…   main b51595bb…      identical
capabilities.json softhouse/T122… 882e97bc… main 882e97bc…      identical
```

Every sibling worker's path is untouched.

---

## 1. The four ulp gaps — F-T114-1, re-derived in exact rational arithmetic

My own classifier, my own `a(r,n)`, my own HALF_UP integer renderer, over all four committed raw
captures (T83 and T100 read from committed blobs, T84 and T84B read from the **`.gz`**):

```
TOTAL non-calibration swept cells: 687
split: {'clean': 346, 'A': 312, 'B': 29}
  t83   n=330  {'clean': 132, 'A': 198}
  t84   n=249  {'A': 99, 'clean': 146, 'B': 4}
  t84b  n=93   {'clean': 63, 'B': 18, 'A': 12}
  t100  n=15   {'B': 7, 'clean': 5, 'A': 3}
FAMILY B principals (minor): [1]        FAMILY B rates (1): 600.00
FAMILY B n set: [104…122, 150, 200, 250]   distinct n: 22
FAMILY B uniform (psum==0, totprin==0, nz==0, last_int==1, B==1): True

ulp of 1/2 at 19 significant digits = 1e-19 = Fraction(1, 10**19)

family-B cells where |gap| is NOT below the ulp: 4 of 29
   T100-FAMB-R600p0-N104-B1       n=104  gap=+2.4293e-19 = 2.43 ulp
   T84B-NSW-R600p0-N104-B1        n=104  gap=+2.4293e-19 = 2.43 ulp
   T84B-NSW-R600p0-N105-B1        n=105  gap=+1.6195e-19 = 1.62 ulp
   T84B-NSW-R600p0-N106-B1        n=106  gap=+1.0797e-19 = 1.08 ulp
   -- then --
   T84B-NSW-R600p0-N107-B1        n=107  gap=+7.1979e-20 = 0.72 ulp   (first sub-ulp cell)
   T100-FAMB-R600p0-N250-B1       n=250  gap=+4.7441e-45 = 4.7441e-26 ulp

every family-B gap strictly positive: True
duplicate-n cells agree EXACTLY: True   (n measured more than once: [104,108,120,121,150,200])
gap strictly decreasing in n across the 22 distinct n: True
ULP CROSSING (exact): largest n with gap >= 1 ulp = 106; smallest n with gap < 1 ulp = 107
crossed exactly once (all n <= 106 are >=1ulp, all n >= 107 are <1ulp): True

spot values quoted in gates.md:
   n=104  gap=+2.4293e-19      n=108  gap=+4.7986e-20
   n=200  gap=+3.0249e-36      n=250  gap=+4.7441e-45
```

**Every figure T122 put in the gate reproduces.** 2.43 / 2.43 / 1.62 / 1.08 ulp at n = 104, 104,
105, 106; n = 107 at 0.72 ulp; n = 250 at 4.7441e-45; the crossing exactly at 106 → 107 and crossed
once. The two independent n = 104 cells (T84B's and T100's) agree to every digit, as do all six
duplicated n. `gates.md:1326`'s `+2.429e-19` at n = 104 and `+3.025e-36` at n = 200 and
`:1376`'s `+4.799e-20` at n = 108 are all correct to the digits quoted.

Closed form as stated: `gap = B_minor · a(r,n) − ½` with `a(r,n) = r/(1−(1+r)^−n)`, `r = annual/100/12`.
At the family-B shape `r = 600/100/12 = 1/2` **exactly**, so `gap = ½·(2/3)ⁿ/(1−(2/3)ⁿ)` — strictly
positive, strictly decreasing, and falling by a factor of exactly 3/2 per term. That is why the
crossing is a single clean threshold and why 2.4293/1.6195/1.0797/0.71979 are in exact 3:2 ratio.

---

## 2. The trap — verified independently, and REPRODUCED

`.softhouse/reviews/T84-evidence/out/` holds both the plain `.json` and the `.gz` for each T84
capture. The plain files **say so themselves** (`_t84_trim_note`, `_t84_full_capture_count`), which
T122's handoff does not mention — but the subset claim still needed testing, and it holds:

```
== capture-t84-raw   plain cases: 15  gz cases: 251
   ids present in plain but MISSING from gz : []
   ids present in both but DIFFERING        : []
   => strict content-identical subset       : True
   plain file _t84_full_captures_canonical_sha256 : 3900a2042b62f7d1…ccdcbf17
   my sha256(canonical over gz captures)          : 3900a2042b62f7d1…ccdcbf17    MATCH
   non-captures header identical (ignoring _t84_* trim keys): True
== capture-t84b-raw  plain cases: 14  gz cases: 95
   MISSING: []   DIFFERING: []   strict subset: True
   claimed 47611b047108daf8…22723313  ==  mine 47611b047108daf8…22723313   MATCH
```

Both extracts are strict, content-identical subsets, and — a check T122 did not make — **the
canonical sha256 each plain file records for the full capture reproduces exactly over the `.gz`
captures array**, which is independent provenance that the `.gz` is the capture and the plain file
is a faithful excerpt of it.

**And the trap is real. I reproduced T122's wrong first-run numbers exactly** by running my own
analysis over the plain files:

```
OVER THE PLAIN .json EXTRACTS:
  total non-calibration cells: 370   split: {'clean': 147, 'A': 207, 'B': 16}
  family-B cells: 16
  family-B cells NOT below the ulp: 3  [(104,'T100-FAMB-…-N104-B1'), (104,'T84B-NSW-…-N104-B1'), (105,'T84B-NSW-…-N105-B1')]
  ==> 16 family-B cells / 3 non-sub-ulp exceptions, against the TRUE 29 / 4
```

**16 and 3, exactly as T122 reports.** Both are plausible, both are wrong, and either would have put
a third wrong count into this gate. T122's account of the trap is accurate and its follow-up 6 is a
correct `patterns.md` candidate. I record it as a **P3 finding against the artefact** that the
Evidence block at `gates.md:1490` still lists `capture-t84-raw.json{,.gz}` with no note that the
plain files are 15- and 14-case extracts — see scope-table row 111.

---

## 3. The interpretation — tested as reasoning, not only as numbers

This is the strongest claim in the section and it redirects the next worker, so I graded the
inference and not just the arithmetic.

### (a) *"the EMI quantizes to zero because the gap is beneath the arithmetic's resolution" is refuted at the region's first three terms* — **SOUND, and correctly hedged**

The story as **quoted** has a factual premise — that the gap is beneath the arithmetic's resolution
— and at n = 104, 105, 106 that premise is measurably false: 2.43, 1.62 and 1.08 units in the last
place of ½ carried at the tenant's ratified `(19, HALF_UP)`. A story whose premise is false at a
cell cannot explain that cell. The deduction is valid.

The gate does **not** overreach on it. It says *"not **simple** exhaustion of significant digits"*
(`:1352`) and *"any candidate mechanism must explain n = 104, 105 and 106 on its own terms"*, and it
leaves family B's mechanism tagged `[UNVERIFIED]` at `:1333` and `:1197`. That hedge is doing real
work, and it is the right hedge: **what the measurement rules out is the one-rounding, 19-digit
version of the story, not every resolution story.** A chain of 19-digit-rounded operations can
accumulate more than one ulp of error, so a mechanism whose *effective* resolution at that shape is
coarser than 1e-19 would still be a resolution story and would still put the edge at 104. The gate's
wording survives that objection; an unhedged *"resolution stories are refuted"* would not have. I
record the objection here so the next worker has it, and I note that **the gate already tells them
where to start** (`:1362`, n = 104).

### (b) *the region's boundary and the sub-ulp boundary do not coincide, so at most one can be the cause* — **SOUND, and the stronger version is also true**

Both thresholds are exact and I measured both. Sub-ulp begins at n = 107. The region begins at
n = 104 — and this is **not** an artefact of sampling, which is the objection that would have killed
the argument. T84B swept the family-B shape **contiguously from n = 88**:

```
600.0 % / MNT 0.01 — every n asked, and its class:
 60 clean | 88…103 clean (contiguous, 16 terms) | 104…122 family B | 150, 200, 250 family B
```

So 104 is a **measured edge with sixteen contiguous clean cells beneath it**, not the bottom of the
sweep. A cause that tracked the sub-ulp condition would have put the edge at 107; it is at 104;
therefore the sub-ulp condition is not the cause. The gate's *"at most one of them can be the
cause"* is if anything weaker than what the measurement supports — sub-ulp is **ruled out** as the
determinant of the boundary, not merely put in competition — and the third bullet says exactly that
(*"a correlate over 25 of 29 cells, not the explanation of the family"*).

Loose wording, not a defect: a *threshold* is not a *cause*; the sentence means "at most one of the
two conditions these thresholds define can be the cause", which is what the bullet then says.

### (c) *sub-ulp is a correlate over 25 of 29 cells* — **exact.** 29 − 4 = 25, and the 25 are precisely n ≥ 107.

**Ruling: the interpretation is sound, correctly scoped, correctly hedged, and it is the right
redirection.** It is also the one place in the section where a *reasoning* error would have been
invisible to a numbers-only reviewer, which is why P-23 exists.

---

## 4. F-T114-2's scoped replacement — VERIFIED, both limbs

```
T84 (both captures) all n asked: [1,2,3,5,6,7,12,24,30,36,56,60, 88…121, 150, 170…204, 220,240,260, 360,480,600]
MAX n asked by T84 anywhere: 600    rates at that n: {0.12, 1.20, 3.60}
   ids include: T84B-XL-R0p12-N600-B291                                       <- the cell the gate names
T84 n asked at 600.0 % / MNT 0.01: [60, 88…121, 150, 200]
MAX n at the family-B shape: 200
```

Both figures in `gates.md:1173-1177` are exact, and the cell id resolves. The unqualified form
would indeed have contradicted `:1025` (*"terms up to n = 600"*) and `:1283` (*"n from 1 to 600"*) —
I confirmed both of those are themselves correct: **max n over all 687 swept cells is 600, min is 1.**

The attestation leak T122 found (P-21) is real and is correctly repaired: `T112.md:266-274` claimed
*"Every replacement I wrote carries both scope limbs itself … F-4's names T84's contiguous top **and**
its largest n separately"*, and F-4's replacement carried **no** scope limb. The correction is in
place, marked, and attributed. Correct disposition.

---

## 5. F-T114-4 and the second restored fact — VERIFIED

```
T84-RP-* cells: 12
their tenant ids: t84_rp_r16p8_n24_b10 … t84_rp_r7p0_n56_b24   (all start t84_rp_)
T83 tenant ids: cap_t83_*  (332 distinct)      any RP id also used by T83: False
  T84-RP-R36p0-N3-B1    <-> T83-SW-R36p0-N3-B1     observed byte-identical: True
  … all twelve …
matched: 12 / 12 ;  observed byte-identical: 12 / 12
```

Twelve cells, own `t84_rp_*` tenant ids **disjoint** from T83's `cap_t83_*`, a **unique** same-shape
T83 partner for each, and **all twelve whole `observed` blocks byte-identical**. The claim is exactly
as restored. See scope-table row 34 for a P3 precision nit on the words *"in reversed order"*.

T83's probe topology, all four citations checked at the committed source:

```
run-t83.sh:7    "…runs the embeddable progressive-loan schedule generator IN-PROCESS.
                 It does NOT start the Fineract server and it opens NO database connection."
run-t83.sh:102  cmp -s "$SEAM_LOCAL" "$SEAM_PINNED" || fail "seam class DRIFT…"
run-t83.sh:106-107  [ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] || fail "…Two files mutated the same way
                     compare equal under cmp; this check is the one that cannot be defeated by editing a file."
run-t83.sh:316  "…with zero input differences, tenant id included."
$ git merge-base --is-ancestor 5695609 7a6b347   ->  5695609 IS a strict ancestor of the capture commit
```

The `[VERIFIED at src/run-t83.sh:5-10 … :99-107 … :316]` citations all resolve, and the prediction
commit really is a strict ancestor of the evidence.

---

## 6. F-T114-5 / F-T114-6 — correct disposition, and I RE-MEASURED both

The disposition is right: **editing a script that produced committed evidence destroys the
byte-reproducibility that makes the evidence evidence.** Recorded in three places, with
`KNOWN-DEFECTS.md` a **pointer only** (P-27). Correct.

### D-1 — `classify-boundary.py:102`, re-measured from a scratch copy

```
:20    "…Nothing here constructs a float."
:102   for (rate, n), rs in sorted(by_shape.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):
```

I copied the script unmodified to `/tmp/t129/scratch/`, produced a variant differing in **exactly
one** character range (`fractions.Fraction(str(…))` for `float(…)`; `diff` shows one line), and ran
both against the committed T83 capture:

```
emitted measured-boundary.json : IDENTICAL   (sha256 f04397c7661a1d56…30b4aa48 for both)
stdout boundary tables         : IDENTICAL   (cmp clean)
unmodified run vs the COMMITTED out/measured-boundary.json, invoked with the same source path:
                                 BYTE-IDENTICAL
```

(The only byte that differs when the input path differs is the `"source"` field the script echoes;
re-run from a directory laid out like the repo it is byte-for-byte the committed artefact.)
**T122's harmlessness claim is a measurement and it holds.** The `float()` is a sort key over the
four annual-rate *labels*; no money value is converted and no classification, comparison or count
reads it.

### D-2 — `closed_form_check.py:83`, re-run unmodified

```
$ shasum -a 256 <scratch copy>   55ecbc8f633765522ddcd7b038a3aaa46de6d5ec9c1b6be4489c21c6fdbae2f6   <- as quoted
$ python3 …/closed_form_check.py …/capture-t83-raw.json
cells evaluated (calibrations excluded): 330 / HELD 330 / REFUTED 0 / exact ties 0
ValueError: min() arg is an empty sequence          line 83                      EXIT=1
$ python3 …/closed_form_check.py capture-t84-raw.json.gz capture-t84b-raw.json.gz
cells evaluated: 342 / HELD 320 / REFUTED 22 / exact ties 0
smallest |gap| among refuted: 3.025e-36   largest: 2.429e-19                     EXIT=0
   -> emitted out/closed-form-check.json BYTE-IDENTICAL to the committed one
```

Both halves reproduce, including the byte-identity and the source digest. Every count prints
**before** the crash, so no recorded number is affected, and the hazard really is a signalling one.
The sibling-script citations are right too: `swept_domain.py:6` and `closed_form_check.py:13-16`
both carry an accurate, scoped float note.

---

## 7. RULING on the `tasks.json` deviation — **T122 is RIGHT and the brief was WRONG**

State, measured on my branch:

```
merge-base(main, softhouse/T122-g8-t114-fixes) = c395982
merge-base blob   .softhouse/tasks.json = 7e49bd93c1cfeb11c18bdb59560ff0296a9c9dfb
branch    blob    .softhouse/tasks.json = 7e49bd93c1cfeb11c18bdb59560ff0296a9c9dfb   <- EQUAL to base
main      blob    .softhouse/tasks.json = 14b219c4f49939a3db3dba26952a492689354ce9   (main @ e35ea7b)
$ git diff main softhouse/T122-g8-t114-fixes -- .softhouse/tasks.json | wc -l    1097   <- NOT empty
```

The evil merge is real and re-verified independently:

```
$ git rev-list --parents -n 1 eea5e80 -> eea5e80  6b0c1da(T100)  c395982(main at dispatch)
   eea5e80 blob 30e69115…   6b0c1da blob 0048d37f…   c395982 blob 7e49bd93…   7d723b5 blob 30e69115…
$ git merge-base --is-ancestor 7d723b5 eea5e80  -> exit 1   (NOT an ancestor)
$ grep -c '"T113"' :   6b0c1da = 0    c395982 = 0    eea5e80 = 1
```

**The ruling.**

1. **The brief's remedy could not satisfy the brief's own requirement.** The operative requirements
   are (i) the branch authors no intentional change to the orchestrator's file and (ii) the file
   produces no merge conflict. A **snapshot** of `main` satisfies (i) only at the instant it is
   taken and cannot satisfy (ii) at all, because the orchestrator edits `tasks.json` continuously.
   T122 observed `main` move three times during its task; **I watched it move twice more during this
   review** — `79a67d1` → `fdcdf09` → `e35ea7b`, with the `tasks.json` blob going
   `5d5dba7d` → `cc3cc925` → `14b219c`. A snapshot taken at any of those is stale before it lands.
2. **Reverting to the merge-base blob is the only disposition with the property the brief actually
   wants.** With `theirs == base`, git's three-way merge takes `ours` (`main`) unconditionally, for
   **any** future `main`, with no conflict and no human resolution. That is a structural guarantee,
   not a timing coincidence.
3. **It was tested by merging, not asserted** (P-24) — and I re-tested it against two `main` heads
   T122 never saw (§8). Both clean, merged blob == `main`'s blob exactly.
4. **The consequence T122 flags is the correct reading, not a defect.** `git diff main -- tasks.json`
   being non-empty says the branch is *behind* `main` on that file. For a file the branch must not
   author, *behind* is precisely what "did not touch it" looks like in git. A branch that were
   byte-equal to `main` on a file `main` is editing would be **authoring** that file's content into
   the merge.
5. **The brief's literal check is itself the P-24 anti-pattern.** `git diff main -- …` is a
   moving-baseline assertion; it can pass only at an instant, and it will follow `main` exactly when
   nobody is watching — the same failure P-24 records for `git merge-base main HEAD`. The
   post-merge check is the one that means anything, and it passes.

**Deviation UPHELD. The brief was wrong and refusing it was correct (P-20).** T122's follow-up 5 is
a well-formed `patterns.md` candidate and I second it: *a snapshot of a file the orchestrator is
actively editing is a time bomb; the resolution for a branch that must author no change is the
**merge-base blob**, not `main`'s copy.*

**But the deviation was not swept** — see F-T129-1. T122 recorded the *new* disposition in its own
handoff and left the *old* one standing in five other places, including `gates.md`.

---

## 8. The scratch merge, redone against CURRENT `main` (which moved twice more)

`main` was `79a67d1` when T122 finished. It is `e35ea7b` now.

```
--- pass A, against main@fdcdf09 ---
$ git merge-tree --write-tree main softhouse/T122-g8-t114-fixes
  c6202f6445ed7187363666ce8a28045dbbd8b51c            exit 0   NO CONFLICT on any path
  merged tasks.json cc3cc925… == main's blob EXACTLY
  merged gates.md   b1823015… == the branch's blob EXACTLY
  PIN.json b51595bb… / capabilities.json 882e97bc… == main
  grep -c "^## G-8" on merged gates.md  ->  1

--- pass B, after main moved again to e35ea7b ---
$ git merge-tree --write-tree main softhouse/T122-g8-t114-fixes
  a00d371359c61b4efaf84dd41efad2617dae7908            exit 0   NO CONFLICT
  merged tasks.json 14b219c… == main's blob EXACTLY
  merged gates.md   b1823015… == the branch's blob EXACTLY
  PIN.json / capabilities.json / contract.go == main, byte for byte
  grep -c "^## G-8"  ->  1 ;  the only surviving mention of the deleted block is the supersedes bullet at :911

--- pass C, a REAL merge in a throwaway clone (P-24) ---
$ git clone --no-local /Users/buv/gerege-nbfi /tmp/t129/mergecheck && cd /tmp/t129/mergecheck
$ git checkout main && git merge --no-ff origin/softhouse/T122-g8-t114-fixes
  Merge made by the 'ort' strategy.  63 files changed, 106528 insertions(+), 111 deletions(-)   EXIT=0
  .softhouse/tasks.json does NOT appear in the changed-file list at all
  HEAD:.softhouse/tasks.json = 14b219c… = origin/main's blob
  grep -c "^## G-8" .softhouse/gates.md  ->  1
```

Nothing pushed; the clone is throwaway. All four post-merge corrections grep present in the merged
file (`25 of the 29`, the scoped `largest n T84 asked *at this shape*`, `12 of 12 identical`,
`Two KNOWN DEFECTS`). **T122's merge property holds against two `main` heads it was never tested
on**, which is the whole point of the disposition it chose.

---

## 9. Gate discipline

- **G-8 state: OPEN.** `:907-908` says so and says neither T112 nor T122 decided it *"and neither
  may."*
- **(b) and (c) untouched.** `:1449-1450` states both amend the graded domain, that this is a change
  to a ratified DEC-n, and that it is a hard `user` gate no agent may cross. Nothing in the section
  decides them, implies they are decided, or pre-implements either.
- **No recommendation language.** A sweep for `recommend|should adopt|propose to|the right
  option|prefer option|we choose|best option|decid(e|ed) that` over the 647-line section returns
  **one** hit — `:1451`, *"decided none, recommended none, and pre-implemented none"*, which is the
  disclaimer. A sweep for `should|must|ought to|will be adopted` returns 7 hits, all reading
  instructions or next-step engineering guidance (*"the next worker should start at n = 104"*,
  *"a re-run must fix these FIRST"*); **none** is a gate recommendation.
- **Family attribution — 16 sites, count VERIFIED, none backwards.**
  `grep -inE "761|2525|0 cell diff|cell diffs|zero port change|no port change|option \(a\)|reachable today"`
  over the branch's `gates.md` returns exactly **16** lines — 914, 1101, 1187, 1205, 1207, 1209,
  1222, 1223, 1225, 1230, 1234, 1239, 1438, 1466, 1506, 1524 — and I read every one. All 16 are
  correct: option (a) is reachable today on **FAMILY B** (761 graded cells, **0** cell diffs, FAIL
  on `principal_portions_sum_to_disbursed` + `principal_amortizes_to_zero` → **PASS** under the
  exemption, zero port change); **FAMILY A** is 2,525 cells with **exactly one** diff per case
  (`row 360 outstanding_principal_minor: expected 109 minor units, got 0`) and stays **FAIL —
  unchanged** under the exemption. Re-derived from `out/exemption-demo-t100.json` myself: exit codes
  **1 / 2 / 1 / 1**, `parityFail` **1 / 0 / 1 / 1**, `invariantViolations` **2 / 0 / 0 / 0**,
  `graded_cells` **761 / 761 / 2525 / 2525**. **No site is backwards.** My own dispatch brief also
  stated it correctly.

---

## FINDINGS

### F-T129-1 — **P2.** `gates.md:1540` records a SUPERSEDED `tasks.json` disposition, and it leaked to four more sites

`.softhouse/gates.md:1540`, the **last line of the section and of the file**:

> …and it took `.softhouse/tasks.json` **wholesale from `main`** (F-T114-3, the evil merge in `eea5e80`).

**False.** T122 did not take `main`'s copy. Commit `b4b5712` did; commit **`c698200`** — *"tasks.json
— revert to the merge-base blob so the branch authors NO change to the orchestrator's file"* —
undid it, and the branch's blob is the **merge-base blob `7e49bd93`** (`c395982`'s copy), not
`main`'s (`14b219c` at `e35ea7b`). T122's own handoff states the correct disposition at length and
explicitly warns that `git diff main -- .softhouse/tasks.json` is **not** empty.

The gate is the artefact the decision-maker reads, and as written it tells a future auditor to
expect an empty diff on that path. They will get **1,097 lines**, and conclude the branch modified
the orchestrator's file — the exact misreading T122 foresaw and wrote a paragraph to prevent, in the
one document that does not carry the paragraph.

**Timing makes this a sweep failure, not an ordering accident:** `c698200` (the revert) precedes
`300b52d` (the last commit, which edited `gates.md` again). T122 had the file open after changing
its mind.

**Five sites carry the superseded disposition** (`git grep` over the branch):

| file:line | text | true value |
|---|---|---|
| `.softhouse/gates.md:1540` | "took `.softhouse/tasks.json` **wholesale from `main`**" | reverted to the **merge-base blob `7e49bd93`**; the branch authors no change |
| `.softhouse/handoff/…/T112.md:11` | "was taken **wholesale from current `main`** — not merged, not reconciled, not edited" | same |
| `.softhouse/handoff/…/T112.md:13` | "`git diff main -- .softhouse/tasks.json` is **empty**." | **not empty** — 1,097 lines; the branch is *behind* `main`, which is correct |
| `.softhouse/handoff/…/T112.md:310` | "T122 reset it to current `main`'s copy." | reverted to the merge-base blob |
| `.softhouse/handoff/…/T112.md:387` | "T122 reset it to current `main`'s copy wholesale" | same |

This is **P-21 / P-26 for the third time in this chain**, and this time the leaking correction is
T122's own change of mind rather than an inherited defect. T122 swept for the *concept* when
correcting T112's four `tasks.json` denials — and did not sweep for its own.

**Exact replacement text**, arithmetic already done, no oracle, no re-measurement:

`gates.md:1540` — replace
> and it took `.softhouse/tasks.json` **wholesale from `main`** (F-T114-3, the evil merge in `eea5e80`).

with
> and it left `.softhouse/tasks.json` at the **merge-base blob `7e49bd93`**, so the branch authors
> **no change at all** to the orchestrator's file and any merge into any future `main` takes
> `main`'s side with no conflict (F-T114-3, the evil merge in `eea5e80`; a snapshot of `main` was
> tried first and was rejected because `main` edits that file continuously —
> `git diff main -- .softhouse/tasks.json` on the branch is therefore **not** empty, and that is the
> correct state for a file the branch must not touch).

`T112.md:11-13` — replace *"was taken **wholesale from current `main`** — not merged, not
reconciled, not edited — because T112 authored no intentional change to it and it is the
orchestrator's file, which has moved substantially on `main` during this fire. `git diff main --
.softhouse/tasks.json` is **empty**."* with *"was set back to the **merge-base blob `7e49bd93`**, so
this branch authors no change to it at all. A snapshot of `main` was tried first and abandoned:
`main` edits `tasks.json` continuously, so a snapshot conflicts. `git diff main --
.softhouse/tasks.json` on the branch is therefore **not** empty — it shows the branch is *behind*,
which is the right state for a file it must not author. The check that matters is post-merge, and it
passes: the merged tree's blob equals `main`'s exactly."*

`T112.md:310` and `:387` — replace *"reset it to current `main`'s copy"* with *"set it back to the
merge-base blob `7e49bd93`, so this branch authors no change to it"*.

### F-T129-2 — **P3.** `gates.md:1166-1167` understates T84's 300.0 % sweep

> T84 swept 300.0 % with **B = 2 through n = 204** and 300.0 % with B = 1 at six terms up to n = 260

The **B = 1** half is exact — six terms, n = 100, 150, 175, 196, 220, 260, all six family A. The
**B = 2** half is not: measured from the captures,

```
300.0 %, B=2 minor: 41 cells, n = 100, 150, 170…204 (contiguous), 220, 260   max n = 260   all clean
```

The top is **260**, not 204; 204 is the top of the *contiguous run*. This under-states the domain —
the safe direction, and the conclusion it supports (no family B at 300 %) is unaffected — but it is
a false statement about a swept domain in the one section whose whole discipline is naming domains
exactly. Suggested: *"T84 swept 300.0 % with B = 2 at n = 100, 150, **170…204 contiguously**, 220
and 260 — 41 cells, all clean — and 300.0 % with B = 1 at six terms up to n = 260"*.

### F-T129-3 — **P3.** *"in reversed order"* is not literally true of T84's 12-cell re-ask

`gates.md:1012`. Measured: taking the twelve `T84-RP-*` cells in their own emission order, their
partners' positions in T83's capture are

```
265, 79, 78, 2, 215, 214, 285, 284, 171, 170, 19, 18
```

— neither increasing nor decreasing. Each boundary **pair** is locally reversed relative to T83
(79 before 78, 215 before 214, …), and the set as a whole is in a different, scrambled order. The
*conclusion* — that the boundary is neither tenant-dependent nor order-of-emission dependent — is
fully supported and I verified it (12/12 byte-identical with disjoint tenant ids). Only the phrase
is loose; it is inherited from T84's own review. Suggested: *"in a different emission order, with
each boundary pair reversed"*.

### F-T129-4 — **P3.** The non-decision roster at `gates.md:1450` is stale by two tasks

> T83, T84, T100, T101 and T112 have each handled them and **decided none, recommended none, and
> pre-implemented none**

**T114** reviewed this section and **T122 edited it**; neither is in the list. I checked, and both
in fact decided, recommended and pre-implemented nothing — so the sentence is not false, it is
**incomplete, in the sentence that carries the gate's own non-decision attestation**, and its
incompleteness is invisible to a reader. Exactly the P-21 shape: T112 added itself and T122 did not.
Suggested: add *"T114 and T122"*. Any future editor of this section must add itself here.

### F-T129-5 — **P3.** The Evidence block does not carry the `.json` / `.json.gz` trap

`gates.md:1490` lists `capture-t84-raw.json{,.gz}`, `capture-t84b-raw.json{,.gz}` with no note that
**the plain files are 15- and 14-case extracts and the `.gz` are the 251- and 95-case captures**.
That trap cost T122 a full wrong analysis (16 cells / 3 exceptions — which I reproduced), and it is
recorded only in T122's handoff, not in the artefact the next worker reads. This is P-26's own named
blind spot: *a silence where a qualification should be*. Suggested: append *"(the plain `.json`
files are 15- and 14-case committed **extracts**; the `.gz` are the full 251- and 95-case captures
and are what every count in this section is derived from)"*.

### F-T129-6 — **P3.** One substantive clause of the deleted UPDATE block is still unrestored

`gates.md:918-924` asserts, on the strength of two claim-by-claim audits, that nothing true was lost
with `main`'s deleted `## G-8 — UPDATE` block. I made that a **third** audit, reading
`main:.softhouse/gates.md:939-1021` end to end and tracing each substantive claim into the current
section. **One is not there:** `main:947`'s

> **T83** built its own probe … **took no number from T75** …

The independence-of-T75 claim. It is load-bearing for `gates.md:1075`'s *"T75's report is CONFIRMED
and is a strict subset of this"* — a confirmation only counts if it is independent — and for a
`user`-gate reader weighing provenance. Everything else traced, including two things worth naming
because they are the restatement shapes P-26 warns about: *"0 holes / contiguous failing prefix on
all 32 shapes"* survives as the `contiguous` column of the boundary table (a claim restated **as a
table**, correctly), and *"342 new cells"* survives at `:1322`. Suggested: add *"and took no number
from T75"* to `:1008`.

---

## PART 2 — the REBUILT scope table

Rebuilt from scratch over the branch's current G-8 text (`gates.md:894-1540`, 647 lines), one row
per claim-bearing sentence, clause or table row. This supersedes T101's 56-row table, which predates
two rounds of corrections that both **added** prose.

**117 rows. 6 fail** (rows 8/9 are one finding; 34, 54, 103, 111, 117). Columns: the family the
claim holds for; the domain it was measured over; whether the sentence **says so**; and the verdict.
`[UNVERIFIED by T129]` marks a claim I accepted on citation without re-executing it — listed again
in full at the end.

| # | line | claim | holds for | measured over | says so? | verdict |
|---|---|---|---|---|---|---|
| 1 | :897 | class ENGINEERING to measure; the *remedy* is a DEC-n amendment = hard `user` gate | n/a (gate meta) | n/a | yes | PASS |
| 2 | :898-905 | task provenance chain, each task tagged with the family it measured | both, per task | n/a | yes | PASS |
| 3 | :903-904 | T114 re-derived every load-bearing number and all of it reproduced | both | T112's text | yes | PASS — my own re-derivation agrees |
| 4 | :907-908 | state OPEN; neither T112 nor T122 decided the gate "and neither may" | n/a | n/a | yes | PASS |
| 5 | :911-916 | the deleted block attributed the 761/0-diff/FAIL→PASS result to family A; it is **family B** | B | T100's exemption run | yes | PASS |
| 6 | :916 | the deleted block carried the superseded **18** count | B (all 22 refutations are family B) | T84's 342 cells | via :1325 | PASS |
| 7 | :917-918, :922-924 | this is now the only G-8 write-up; verified on a scratch merge into current `main` | n/a | merged tree | yes | PASS — re-verified at two later `main` heads, exactly one `## G-8` |
| 8 | :918 | "Nothing it said correctly is lost; everything is restated below" | both | the deleted block | yes | **FAIL P3 — F-T129-6** (`main:947` "took no number from T75" unrestored) |
| 9 | :919-924 | "audited claim-by-claim twice … T114 found exactly one loss … T122 one further clause" | n/a | the deleted block | yes | **FAIL P3 — same finding; the audit reads exhaustive and is not** |
| 10 | :928-930 | "Everything below is scoped to the family it was measured on" | meta | n/a | yes | PASS |
| 11 | :930-932 | the domain is graded **by sampling**; rate, principal, n are unbounded in it | both | `contract.go:1163-1170` | yes | PASS — cite verified verbatim |
| 12 | :936 | principal column sums to disbursed: A **yes** / B **NO (0.00)** | per family | 312 A + 29 B | yes (table) | PASS — verified 341/341 |
| 13 | :937 | `totalPrincipalAmount` = disbursement (A) / `0.00` (B) | per family | same | yes | PASS — verified 341/341 |
| 14 | :938 | non-zero principal rows: exactly one, **the last**, whole disbursement (A) / **none** (B) | per family | same | yes | PASS — verified 312/312 and 29/29 |
| 15 | :939 | last row's interest `0.00` (A) / `0.01` (B) | per family | same | yes | PASS — verified 341/341 |
| 16 | :940 | balance column constant at the disbursed amount (**both**) | both | same | yes | PASS — verified 341/341 |
| 17 | :941 | `totalOutstandingAmount` = 0 for both — "so this field does not discriminate" | both | same | yes | PASS — verified 341/341 |
| 18 | :942 | forced memo recompute: A → `0.00` / B unmoved | per family | T83 5/5 + 4/4 controls; T84 3/3; T100 3/3 + controls | yes | PASS by citation — `[UNVERIFIED by T129]` (Java probe not re-executed) |
| 19 | :943 | the port diverges on exactly one cell per case (A) / reproduces cell for cell (B) | per family | 312 A / 29 B | yes | PASS — 2525/1 and 761/0 re-verified; the 312-wide re-grade `[UNVERIFIED by T129]` |
| 20 | :944 | `invariant_exemptions` **inert** (A) / **decisive** (B) | per family | T100's four runs | yes | PASS — verified from `exemption-demo-t100.json` |
| 21 | :945 | A: 11 of 12 rates, `3 ≤ n ≤ 600`, **312** cells / B: one rate 600.0 %, `104 ≤ n ≤ 250`, **29** cells | per family | four raw captures | yes | PASS — every figure verified |
| 22 | :947-949 | 312 = 198 + 111 + 3; 29 = 22 + 7 | per family | same | yes | PASS — verified |
| 23 | :950-951 | every table row holds on every cell of its family, no exceptions, no mixed cases; the families are disjoint | both | "in those captures" | yes | PASS — I verified 8 of 10 rows on all 341 cells; rows 18 and half of 19 are probe/grader results |
| 24 | :953-958 | T75's original finding: MNT 0.01 / 6 × 21.6 % makes the oracle emit a never-zero balance while the port returns 0 | **A** | T75's probe | yes ("That shape is family A") | PASS |
| 25 | :958-964 | the citation correction — `T83-SW-R21p6-N6-B1` is the shape; T100 had tagged the neighbouring MNT 0.02 cell | A | T83's capture | yes | PASS — verified (B=1 → family A, psum 1, last row 1 minor outstanding) |
| 26 | :966-970 | on family A this is a live port-vs-oracle divergence on an **admitted** shape, setting two project rules against each other | A | — | yes | PASS |
| 27 | :972-975 | on family B "there is no divergence to arbitrate … a mechanism would have to say *both are wrong*" | B | — | yes | PASS |
| 28 | :977-979 | conformance is PASS with 42 vectors / 0 violations **only because no vector covers either family** | both | the promoted corpus | yes | PASS — 42/0 re-measured; and 0 parityFail **and** 0 invariantViolations is itself proof (a family-A vector would fail parity, a family-B vector would violate invariants) |
| 29 | :987-993 | the three-part family-A discriminator, "checked on every cell claimed below" | A | 312 cells | yes | PASS |
| 30 | :990-992 | "in every family-A cell **measured so far** by exactly one non-zero principal row" | A | measured set | yes | PASS — 312/312 |
| 31 | :995-998 | test 3 is decisive and was named in advance by the driver's re-derivation | A vs B | n/a | yes | PASS |
| 32 | :1002-1010 | T83's probe topology: in-process Path A seam, **no server, no DB**, `cmp` + sha256 pin, prediction a strict ancestor, zero input diffs incl. tenant id | A | T83's run | yes | PASS — `run-t83.sh:7,102,106-107,316` all verified; `5695609` is a strict ancestor of `7a6b347` |
| 33 | :1011 | reproduced by T84 byte-identically, canonical sha256 `01b41d9c…3101b`, 332 cases | A | T83's capture | yes | PASS — my digest = `01b41d9ca79e…64e3101b`; 332 captures |
| 34 | :1012-1016 | T84 re-asked 12 boundary cells "with different tenant ids and **in reversed order** — 12 of 12 identical" | A | 12 cells | yes | **FAIL P3 — F-T129-3.** 12/12 and the tenant-id disjointness are exact; the emission order is a **scramble with each pair reversed**, not a reversal |
| 35 | :1016-1017 | re-classified a third time by T100: 198 fail / 132 clean / **0 family B** | A | T83's capture | yes | PASS — verified |
| 36 | :1017-1022 | T83's swept domain: rates {7.0,16.8,21.6,36.0} × n {2,3,4,6,12,24,36,56}, principals 1..27 minor, all inside the graded domain at (19, HALF_UP) | A | T83's grid | yes | PASS — verified exactly |
| 37 | :1024-1025 | T84's extension: **111** further family-A cells at 11 named rates, terms up to n = 600, principals 1..100 000 minor | A | T84's two captures | yes | PASS — 111 cells, exact rate set, max n 600, principals 1..100000 |
| 38 | :1027-1031 | T100's 3 family-A cells, different tenant ids, scrambled order, sha `314c4d55…2bfba`, three named shapes, all predicted in advance | A | T100's capture | yes | PASS — digest = `314c4d551c1a…9c92bfba`; all three shapes verified |
| 39 | :1033-1038 | "**This table describes 4 rates × 8 terms and nothing else**" | A | T83's grid | yes, emphatically | PASS — model row |
| 40 | :1040-1073 | the 32-row boundary table (largest failing / smallest clean / contiguous, per shape) | A | T83's grid | yes | PASS — **all 32 rows re-derived independently and matched cell for cell** |
| 41 | :1075-1080 | T75 confirmed and a strict subset; MNT 0.03–0.06 clean at 21.6 %/n=6 is "the entire range swept above the boundary at that shape" | A | that shape | yes | PASS — 1..6 asked; 1,2 fail; 3..6 clean; nothing larger asked |
| 42 | :1082-1091 | family A at **11 of the 12** rates and **NOT** at 600.0 %; family A at 600.0 % is the **empty set** | A | 687 cells | yes | PASS — verified; empty set confirmed |
| 43 | :1092-1093 | the rate moves the boundary **down** as it rises; region empty at n = 2 at all four rates; grows with the term | A | "Across T83's grid" | yes | PASS — verified from the table (n=56: 7.0→23, 16.8→19, 21.6→17, 36.0→13) |
| 44 | :1097-1100 | the divergence is the **final row's outstanding principal and nothing else**; 198 divergent cells over 198 failing cases; +111 in T84's sweep | A | T83 + T84 | yes (heading "family A only") | PASS on shape; the 198/111 counts `[UNVERIFIED by T129]` |
| 45 | :1100-1103 | `T100-FAMA-R3p6-N360-B109` grades **2525 cells with exactly one diff — row 360** | A | one grader run | yes | PASS — verified from `exemption-demo-t100.json` |
| 46 | :1105-1109 | the `:400`/`:1180`/`:1210` chain is **T75's**, one fire before the driver restated it | A | T75's review | yes | PASS by citation — `[UNVERIFIED by T129]` |
| 47 | :1113-1125 | the source chain `:398`, `:400`, `:278`/`:283`, `:1160`, `:1180`, `:1210`, `:617`, `:1629` | A | pinned Fineract `426a23544` | yes | PASS by citation — **`[UNVERIFIED by T129]`** (T114 re-read these line by line) |
| 48 | :1127-1129 | the driver's candidate site `getInitialBalanceForEmiRecalculation()` `:413-426` is **REFUTED** | A | source | yes | PASS by citation — `[UNVERIFIED by T129]` |
| 49 | :1131-1141 | the mechanism is **observed**: T83 5/5 + 4/4 controls, T84 reproduced, T100 re-ran T84's probe (1.09 → 0.00, 3 controls unmoved, path identity 7/7) | A | the named probes | yes (heading "family A only") | PASS by citation — `[UNVERIFIED by T129]` |
| 50 | :1143-1146 | "family A is precisely … stale wrt its own final EMI adjustment"; **and in the unscoped form T83 wrote it, it is false — see family B** | A | — | yes, with the historical error named | PASS — model row |
| 51 | :1154-1160 | the family-B discriminator and its uniformity (0.00 against 0.01, `totalPrincipalAmount` 0.00, no non-zero principal row, last interest 0.01, memo unmoved) | B | "every family-B cell measured so far" | yes | PASS — the four capture-derivable limbs verified 29/29 |
| 52 | :1164 | "T84 measured 22 family-B cells; T100 measured 7 more" | B | — | yes | PASS — verified |
| 53 | :1166-1167 | 600.0 % — **and no other rate has ever produced a family-B cell** | B | the union | yes | PASS — verified |
| 54 | :1166-1169 | "T84 swept 300.0 % with **B = 2 through n = 204**" and B = 1 at six terms up to 260; the 300 % failures are family A (6 A, 0 B) | A/B | T84's captures | yes | **FAIL P3 — F-T129-2.** B=1 half exact; B=2 top is **260**, not 204 (n = 100, 150, 170…204, 220, 260) |
| 55 | :1170 | principal **MNT 0.01** — no other principal has produced a family-B cell | B | the union | yes | PASS — verified, distinct principals = {1 minor} |
| 56 | :1171-1173 | n ∈ {104…122} ∪ {150,200,250}; T84 measured 104…121 contiguously plus 150 and 200 — **22 cells, n = 108 and n = 120 measured twice, agreeing** | B | T84's two captures | yes | PASS — probe 1 = {108,120,150,200}, probe 2 = {104…121}; duplicates exactly {108,120}; 20 distinct n, 22 cells |
| 57 | :1173-1177 | **F-T114-2's replacement**: n = 122 above T84's contiguous top of 121 but not above the largest n T84 asked **at this shape** (200); n = 250 IS above every n asked **at 600.0 %/MNT 0.01**; T84's largest n **anywhere** is **600**, at 0.12 % (`T84B-XL-R0p12-N600-B291`) | B, with the family-A shape named for contrast | T84's two captures | **yes, both limbs** | **PASS — the correction under review, and it is exact** |
| 58 | :1176-1177 | "Nothing above n = 250 has ever been asked at the family-B shape" | B | the union | yes | PASS — verified |
| 59 | :1177-1178 | at n = 103 the same shape is **clean** [T84; re-measured by T100] | B-shape | T84B + T100 | yes | PASS — both captures clean at n = 103 |
| 60 | :1178-1180 | T84's n at 600.0 %/MNT 0.01 runs **88…121 contiguously plus 60, 150 and 200** | B-shape | T84's captures | yes | PASS — verified exactly |
| 61 | :1186-1188 | the port reproduces family B cell for cell, **0 divergent cells**; T100 through the real grader: **761 graded cells, 0 cell diffs** | B | 22 cells + one grader run | yes | PASS — 761/0 verified; the 22-wide port run `[UNVERIFIED by T129]` |
| 62 | :1190-1192 | family B is **NOT** order-dependent (T84 3/3; T100 3/3 at n = 104, 108, 120 with the family-A control moving 1.09 → 0.00); the family-A mechanism does **not** explain it and no claim is made that it does | B | 3 + 3 cells | yes | PASS by citation — `[UNVERIFIED by T129]` |
| 63 | :1194-1201 | four `[UNVERIFIED]` unknowns: the cause; other rates/principals/below n = 104; whether it terminates; `MinorUnitDigits ≠ 2` and Path B/REST | B | — | yes | PASS — model rows |
| 64 | :1207-1212 | option (a) defined; exemptions have power over invariant statuses and **none** over cell diffs (`grade.go:488`, early return `:489-493`) | both | the grader | yes | PASS — verified at those exact lines |
| 65 | :1214-1218 | both halves measured in one run with the **real** `conformance.Run` and the **real** port over a throw-away store; nothing written to `.softhouse/vectors`; the corpus count did not change | both | T100's run | yes | PASS — branch changes nothing under `.softhouse/vectors` |
| 66 | :1220-1226 | the two-column table: 761 / 2525 graded cells, **0 / 1** cell diffs, FAIL / FAIL without exemption, **PASS / FAIL-unchanged** with, both admissible | per family, both columns headed with the shape | T100's four runs | yes | PASS — every figure verified from `exemption-demo-t100.json` |
| 67 | :1230-1233 | **on family B option (a) is reachable TODAY** — no port change, no DEC-n amendment; "the cheap option … on the family T83 never sampled" | B | — | yes | PASS |
| 68 | :1234-1237 | **on family A option (a) still requires a port change**, and its full shape is emit-the-stale-balance *then* exempt; no agent proposes to make it | A | — | yes | PASS |
| 69 | :1239-1240 | T83's "Option (a) is NOT reachable" is **true of A and false of B**, and was recorded unscoped | per family | — | yes | PASS — model row |
| 70 | :1242-1254 | **three of the four exits ARE the finding**; only FAMILY-B-WITH-EXEMPTION's exit 2 is scratch-store noise (`monthend.reanchor` coverage fatal) | per family, per run | T100's four runs | yes | PASS — verified: 1/2/1/1, parityFail 1/0/1/1, invViol 2/0/0/0, and `grade.go:154-160` orders the branches exactly as stated |
| 71 | :1256-1263 | the exit-code record, and T101 reproduced all four runs on `main`'s current port | both | the committed run record | yes | PASS for the file's own figures; T101's re-run `[UNVERIFIED by T129]` |
| 72 | :1265-1268 | proposed vectors prepared and **NOT promoted**, for both families, at named paths | both | — | yes | PASS — paths exist; nothing promoted |
| 73 | :1274-1276 | the retired "far below one MNT / largest is MNT 0.23" sentence was true of **T83's grid** and false as a statement about the graded domain | A | — | yes | PASS — model row |
| 74 | :1278-1281 | **MNT 0.23** over T83's grid, at 7.0 %/n = 56, over the **eight discrete terms** (a set, not a range) | A | T83's grid | yes | PASS — `T83-SW-R7p0-N56-B23` |
| 75 | :1282-1285 | **MNT 2.91** over the union (687 cells; 12 rates 0.12–600.0 %; n from 1 to 600) at 0.12 %/n = 600, with MNT 2.92 clean beside it | union (both families) | the union | yes | PASS — 291 minor; `T84B-XL-R0p12-N600-B291` and T100's re-ask; n over all 687 cells runs 1..600 |
| 76 | :1286-1291 | "the two absolute figures are the statement", ratio **291 ÷ 23 = 12.65×**, with the retired 2.91 ÷ 0.25 = 11.64 named so the reader can reconcile | A / union | both grids | yes | PASS — exact rational: 291/23 = 12.652…, 291/25 = 11.64 |
| 77 | :1292-1295 | **MNT 1.09 fails at 3.6 %/n = 360** with MNT 1.10 clean; "not sub-MNT dust … the shape that produces it is not absurd" | A | T84 + T100 | yes | PASS — verified in **both** captures |
| 78 | :1296-1300 | at 0.12 % the largest failing principal runs **59, 118, 176, 234, 291** minor at n = 120, 240, 360, 480, 600 — ≈ n/2 — each bracketed by a measured clean cell one minor unit above | A | T84 + T100 | yes | PASS — **all five figures and all five brackets verified** |
| 79 | :1302-1307 | what was NOT swept: dp, currency, day count, frequency, single disbursement, no down payment, no charges, multiples-of null, only (19, HALF_UP), only 12 rates, the named gaps in the continuum | both | — | yes | PASS — model row |
| 80 | :1307-1309 | **no term above n = 600 has ever been asked**; the largest failing principal grows with n; **the measurement establishes no upper bound over the graded domain — only over the grid swept** | both | the union | yes | PASS — max n over all 687 cells = 600 |
| 81 | :1309-1311 | the practical reading "no commercially realistic Mongolian loan *amount* has been observed to fail" holds **over that grid** and is not a proof about the domain | both | that grid | yes | PASS — model row |
| 82 | :1315-1319 | T83 registered the closed form and **labelled it a HYPOTHESIS**; on its own grid it held on all 32 shapes, 106/106, 0 refuted | A | T83's grid | yes | PASS by citation — `[UNVERIFIED by T129]` |
| 83 | :1321-1323 | T100's exact-rational re-evaluation: **330/330** on T83's cells; **320 held / 22 refuted / 0 exact ties** on T84's 342 | both | both sets | yes | PASS — **re-run by me from a scratch copy; output byte-identical to the committed JSON** |
| 84 | :1324-1326 | **every one of the 22 refutations is a family-B cell** — 600.0 %/B = 1/n ≥ 104 — where the closed form predicts CLEAN (gap `+2.429e-19` at n = 104 falling to `+3.025e-36` at n = 200) and the oracle fails | B | 342 cells | yes | PASS — exact rationals: `2.4293e-19`, `3.0249e-36`; all 22 are family B |
| 85 | :1327-1329 | the gap is below the ulp of ½ at 19 significant digits on **25 of the 29** cells — and **NOT** on the four at n = 104, 105, 106, where it is **2.43, 1.62, 1.08 ulp** | B | 29 cells | yes | **PASS — the headline correction, re-derived exactly** |
| 86 | :1329-1333 | a sub-ulp argument does not reach the region's **lower boundary**; sub-ulp is offered as a possible explanation **for the other 25**, not a verified mechanism, and **not** for n = 104…106 `[UNVERIFIED]` | B | 29 cells | yes | PASS |
| 87 | :1335-1344 | T122's exact-rational bracket: the method, all four gaps, the two agreeing n = 104 cells, n = 107 at 0.72 ulp, n = 250 at `+4.7441e-45`, strict positivity, strict decrease, crossing **between 106 and 107**, crossed exactly once | B | 29 cells | yes | **PASS — every figure reproduced digit for digit by an independent implementation** |
| 88 | :1349-1354 | bullet 1 — the "quantizes to zero because the gap is beneath the resolution" story is **refuted at the region's first three terms**; more than **two** ulp at the ratified precision, "a difference the oracle's own (19, HALF_UP) arithmetic **can** represent"; not **simple** exhaustion | B | 4 cells | yes | PASS **as hedged** — see §3(a) for the one thing it does not rule out |
| 89 | :1355-1359 | bullet 2 — the region's boundary (104) and the sub-ulp boundary (107) do not coincide; a cause tracking sub-ulp would have put the edge at 107; **at most one can be the cause** | B | 29 cells + the contiguous 88…103 clean run | yes | PASS — and the stronger version holds: 104 is a measured edge with **16 contiguous clean cells beneath it** |
| 90 | :1360-1364 | bullet 3 — sub-ulp is a **correlate over 25 of 29**, not the explanation; must not be used to argue family B is confined to negligible residuals; the next worker starts at **n = 104** | B | 29 cells | yes | PASS |
| 91 | :1366-1370 | 18 vs 22; T101 adjudicated in exact rational arithmetic and **ruled for 22**; 330/0 on T83, 320/22/0-ties on T84 | B | both sets | yes | PASS — re-derived |
| 92 | :1372-1380 | the four disputed cells are `T84-TIE-R600p0-N{108,120,150,200}-B1`; `prediction.json` stores `BtimesA` as the IEEE-754 double `0.5`; the exact residual is `+4.799e-20` at n = 108 | B | 4 cells | yes | PASS — `+4.7986e-20` verified; the stored literal `[UNVERIFIED by T129]` |
| 93 | :1382-1389 | record the cause not just the correction; the no-float rule visibly bound the port/schema/vectors/fixtures and not the **analysis scripts**; "22 is the count"; now P-25 | meta | — | yes | PASS |
| 94 | :1393-1400 | both known defects "**Neither changes any published number** — stated as a measurement, not an assurance"; left byte-identical because editing an executed probe source destroys byte-reproducibility; a re-run must fix them first, in a new pass with new ids | meta | — | yes | PASS — **correct disposition; I re-measured both** |
| 95 | :1402-1414 | D-1 — `classify-boundary.py:102`'s `float()` against the file's own `:20` "Nothing here constructs a float"; **the header is false**; no published result affected, **measured** by an exact-Fraction variant emitting an identical `measured-boundary.json` | meta / A-evidence | the committed capture | yes | **PASS — re-measured: identical emitted JSON (sha256 `f04397c7…`), identical stdout, and the unmodified run reproduces the committed artefact byte for byte** |
| 96 | :1414-1416 | the four labels 7.0/16.8/21.6/36.0 order the same under either key; the sibling scripts got it right (`swept_domain.py:6`, `closed_form_check.py:13-16`) | A-evidence | — | yes | PASS — both cites verified at those lines |
| 97 | :1417-1429 | D-2 — `closed_form_check.py:83` crashes on its own all-clean path; every count prints **before** the crash; the committed JSON came from the 342-cell run; re-run unmodified (sha `55ecbc8f…`) | meta | both inputs | yes | **PASS — re-run by me: 330/330/0/0 then exit 1 at line 83; 342/320/22/0 exit 0, output byte-identical to the committed JSON; source digest matches** |
| 98 | :1431-1433 | "the closed form is a good description of **family A on the grid where it was fitted**, and it is not a law. It does not predict family B at all." No claim for any un-sampled rate, term or day-count | per family | both grids | yes | PASS — held on 100 % of family-A cells in both sweeps, refuted on 22 of 22 family-B cells asked. Wording note: it *does* emit a prediction on family-B cells (CLEAN); it is wrong there |
| 99 | :1437-1439 | **(a)** reachable today on family B with zero port change; port change on family A; "**Scope any decision to one family; a vector for one says nothing about the other**" | per family | — | yes | PASS |
| 100 | :1440-1443 | **(b)** cheap in code **for family A over the grid swept** — but the region is not fully bounded, and it is a **graded-domain amendment** | A, with the bound caveat naming B | — | yes | PASS |
| 101 | :1444-1447 | **(c)** is what the port does today, ungraded, **on family A only** — "**(c) does not describe family B at all**" | per family | — | yes | PASS |
| 102 | :1449-1450 | **(b) and (c) both amend the graded domain = a ratified DEC-n change = a hard `user` gate no agent may cross. Buyan decides.** | n/a | — | yes | PASS — **gate discipline intact** |
| 103 | :1450-1453 | "T83, T84, T100, T101 and T112 have each handled them and **decided none, recommended none, and pre-implemented none**" | n/a | those five tasks | yes for those five | **FAIL P3 — F-T129-4.** Roster stale by two: **T114** reviewed the section and **T122 edited it**; neither is listed, in the sentence carrying the gate's own non-decision attestation |
| 104 | :1455-1457 | what unblocks it (a `user` decision, now on **two** phenomena) / what it blocks (nothing today) | n/a | — | yes | PASS |
| 105 | :1457-1460 | **341** uncovered cells = **312** family-A divergences + **29** family-B cells where the **port itself** does not repay; "the last 29 are the worse half" | per family | the union | yes | PASS — 312 + 29 = 341 verified |
| 106 | :1460-1463 | T84's narrower **331** = 198 + 111 + 22 is right on T84's set; **341** is right on this section's union | per family | both sets | yes | PASS — arithmetic verified |
| 107 | :1463-1466 | T101's re-grade: **312** family-A cells one diff each, always the final row; **29** family-B cells **0 diffs across 25,751 graded cells** | per family | T101's run on `main`'s port | yes | PASS by citation — **`[UNVERIFIED by T129]`** and `[UNVERIFIED by T122]`; nobody has re-run it since T101 |
| 108 | :1466-1468 | T112's independent re-derivation: 687 swept / 312 A / 29 B / 346 clean | both | four raw captures | yes | PASS — my own classifier: **687 / 312 / 29 / 346** |
| 109 | :1470-1472 | conformance is unmoved: PASS, exit 0, 42 vectors, 5576 graded cells, 0 invariant violations; nothing promoted; `PIN.json`/`capabilities.json` untouched | n/a | this repo | yes | PASS — **re-measured, every figure, plus 0 assertions NOT RUN and `probe = up`** |
| 110 | :1476-1482 | family-A evidence file list | A | — | yes | PASS — all present on the branch |
| 111 | :1484-1491 | family-B evidence file list, incl. `capture-t84{,b}-raw.json{,.gz}` | B | — | **no** | **FAIL P3 — F-T129-5.** No note that the plain `.json` are 15-/14-case **extracts** and the `.gz` are the 251-/95-case captures. The silence is the trap that cost T122 a wrong analysis and me a reproduction of it |
| 112 | :1493-1501 | the two-family evidence list | both | — | yes | PASS |
| 113 | :1503-1508 | T101's review: the **56-row** scope table; 25,751 graded cells / 0 diffs on family B; 312 family-A one diff each; the 18-vs-22 ruling | both | — | yes | PASS by citation |
| 114 | :1510-1516 | T112's corrections; "T112 measured nothing new against the reference oracle" | both | — | yes | PASS |
| 115 | :1518-1530 | T114's review: MICRO-FIX, own classifier from scratch, the list of numbers reproduced, it **attacked the rig**, two false sentences, and it **refused a false premise in its own brief** | both | — | yes | PASS — I reproduced the same list of numbers |
| 116 | :1532-1539 | T122's paragraph: contacted the oracle **not at all**; the four ulp gaps in exact rational arithmetic; T84's n-set and the 12 `T84-RP-*` re-ask; the two probe-source defects re-verified from scratch copies; changed no vector, `PIN.json`, `capabilities.json`, `contract.go` or `nexus/` file | both | — | yes | PASS — every limb verified |
| 117 | :1540 | "and it took `.softhouse/tasks.json` **wholesale from `main`**" | n/a | — | yes | **FAIL P2 — F-T129-1. FALSE.** The branch's blob is the **merge-base blob `7e49bd93`**; it authors no change. `git diff main -- .softhouse/tasks.json` is **1,097 lines**, not empty |

**Row count: 117. Failing: 6** — rows 8 and 9 (one finding, F-T129-6), 34 (F-T129-3), 54 (F-T129-2),
103 (F-T129-4), 111 (F-T129-5), 117 (F-T129-1).

### What this rebuild says about the base rate

T101 audited 56 rows and found a false-scope sentence. T114 audited and found two, one **introduced
by T112's own fix**. T122 read the section end to end and found none — it did not rebuild the table,
and said so. I rebuilt it at 117 rows and found **six**, of which:

- **one is in prose added by a correction** (row 117, T122's own commit `b4b5712`, invalidated by its
  own commit `c698200` three commits later) — the F-T114-2 pattern **repeating one round later**;
- **one is an omission created by a correction** (row 103, stale since T112 added itself);
- **two are inherited and never audited** (rows 34 and 54, from T84's and T100's original wording);
- **two are silences** (rows 8/9 and 111) — the shape no grep can find and only a sentence-by-sentence
  read catches.

**The section did not become less reliable; the audit became more granular.** 117 rows over 647
lines is one claim per 5.5 lines, against T101's 56 rows over a shorter section. Six failures at
that granularity is a **5 % defect rate on claim-bearing sentences**, and every one is a scope or
disposition statement rather than a measurement — the measurements are, on this reading, **perfect**.

**The standing recommendation for this section**: nobody may edit G-8 again without rebuilding this
table, and **the editor must add itself to row 103's roster**. The correction is the highest-risk
prose in the document, exactly as the brief said, and the evidence for that is now three consecutive
rounds deep.

---

## `[UNVERIFIED]` — claims I accepted on citation and did NOT re-execute

Stated in full because an unstated limit reads as exhaustive (P-26).

1. **The Fineract source chain** (rows 46, 47, 48) — `RepaymentPeriod.java:398`, `:400`, `:278`,
   `:283`, `:413-426`; `ProgressiveEMICalculator.java:1160`, `:1180`, `:1210`, `:617`, `:1629`, and
   the "only three readers" census. T114 re-read these line by line at `426a23544` and reported them
   correct; **I did not open the pinned checkout at all.** `[UNVERIFIED by T129]`
2. **Every Java probe** — `CaptureT83`, `CaptureT84{,B}`, `CaptureT100`, `ProbeOrderDep{,2}`. I
   re-derived **from the committed capture bytes**; I executed no Java and contacted no oracle. So
   the order-dependence results (rows 18, 49, 62) and the "3 of 3 / 5 of 5 / 4 of 4" counts are
   citations, not my measurements. `[UNVERIFIED by T129]`
3. **T101's full re-grade** (rows 19-partial, 107) — 25,751 graded cells with 0 diffs on all 29
   family-B cells, and exactly one diff on each of 312 family-A cells, through the real
   `conformance.Run`. Also `[UNVERIFIED by T122]`. **Nobody has re-run it since T101**, and it is the
   widest quantitative claim in the section. I verified its *shape* on the two representative cells
   in T100's committed run record (761/0 and 2525/1).
4. **The 198 / 111 port-divergence counts** (row 44) — T83's `out/port-vs-oracle.json` and T84's
   re-run. I did not execute the port over those cells. `[UNVERIFIED by T129]`
5. **T83's 106/106 prediction result** (row 82) and `check-prediction.py`'s red-testing. T114 drove
   it red three ways; I did not re-run it. `[UNVERIFIED by T129]`
6. **The stored `BtimesA: 0.5` literal** in `.softhouse/reviews/T84-evidence/prediction.json`
   (row 92). I re-derived the exact residual (`+4.7986e-20`) but did not re-open the file. Read back
   by T112. `[UNVERIFIED by T129]`
7. **T75's attribution of the mechanism** (row 46) — I did not open
   `T75-pathA-multiplesof-review.md` §5. `[UNVERIFIED by T129]`

### What my own audit could NOT have found

- **It is a reading, not a proof.** 117 rows is my judgement of where a claim begins and ends; a
  claim I did not draw a row around is a claim I did not grade. A different reader would draw
  different boundaries and could find a seventh.
- **It cannot find a false claim whose supporting evidence is also false in the same direction.**
  Every number here traces to the four committed raw captures; if a capture is wrong, my
  re-derivation is wrong identically. The captures' own defence is calibration
  (`T64-ZP-A`/`T64-ZP-B` reproduced cell for cell with zero input diffs) and byte-reproduction across
  three independent parties — which is strong, and is not the same thing as being right.
- **It does not cover `main`'s other G-8 block.** `main:894-938` still carries the *original* G-8
  write-up that this section supersedes in place; the branch rewrites it. I audited the branch's
  text and the *deleted* UPDATE block, not `main`'s surviving pre-rewrite prose, which the merge
  replaces.
- **`main` can move again.** My merge was clean at `fdcdf09` and again at `e35ea7b`. Nothing on
  `main` has touched `gates.md` since `c395982`; that is a fact with a timestamp, not a guarantee.

---

## Recommendation to the orchestrator

**MICRO-FIX.** Apply F-T129-1 (five sites, exact text supplied) before merge — it is the one item
that puts a false statement in front of the `user`-gate reader. F-T129-2 through F-T129-6 are P3 and
may be applied in the same pass or carried; none affects a number, a family, the gate state or the
merge. **Do not** re-run any probe, re-capture anything, or touch the oracle for any of it.

Two `patterns.md` candidates seconded, both T122's, both earned by measurement:

1. *A snapshot of a file the orchestrator is actively editing is a time bomb, and "take `main`'s
   copy" is the wrong remedy for a branch that must author no change. The merge-base blob is the
   disposition that stays clean however far `main` moves.* — P-24 applied to a **file** rather than
   a **baseline ref**, and found the same way P-24 was: by merging instead of asserting.
2. *A directory holding both `x.json` and `x.json.gz`, where the plain file is a small extract, is a
   live trap.* It produced a plausible wrong result (16 cells / 3 exceptions) for T122 and **I
   reproduced that wrong result exactly**. Committed extracts must be named for what they are, and
   the qualification belongs in the artefact, not only in a handoff.

And one of my own:

3. **A correction that is itself revised must be swept a second time.** F-T129-1 exists because
   `b4b5712` wrote a disposition, `c698200` reversed it, and nothing swept the five places the first
   one was recorded. P-21 says a correction leaks to its restatements; this is the sharper case —
   **a correction that is later reversed leaves its own restatements behind as fossils**, and they
   are the most convincing fossils in the document because they were written by the person who now
   knows better.
