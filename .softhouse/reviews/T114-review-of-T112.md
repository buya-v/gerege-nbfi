# T114 — independent review of T112 (`softhouse/T112-g8-rework-retry`)

Reviewer: T114, spawned fresh, worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac812bed6c7163f93`, branch
`softhouse/T114-review-t112` (forked from `main`).

Artefact under review: the G-8 section of `.softhouse/gates.md` on
`softhouse/T112-g8-rework-retry` (lines **894–1410**), the handoff
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T112.md`, and the evidence under
`.softhouse/capture/t83-nonamortizing/` and `.softhouse/capture/t100-g8-rescope/`.

Reference oracle (Fineract) pinned checkout `/Users/buv/fineract` at `426a23544`, clean tree,
verified. **I started nothing, restarted nothing, rebuilt nothing, re-seeded nothing, and wrote
nothing to any container or to the oracle database. I did not contact the oracle at all** — every
number below was re-derived either from committed capture bytes with my own from-scratch code, or
by reading pinned Fineract source, or by reading Go source in this repository. I promoted nothing
and modified no vector, `PIN.json`, `capabilities.json`, `contract.go` or `gates.md`.

---

## VERDICT: **MICRO-FIX**

**The measurement is sound and T112's three assigned corrections are correctly and completely
applied.** I re-derived every load-bearing number in the section from scratch, in integer minor
units, with my own classifier that shares no code with T83's, T84's, T100's or T112's — 687 swept
cells / 312 family A / 29 family B / 346 clean, all ten discriminator rows holding on 341 of 341
cells, the 11-vs-12 rate split, the 22-cell / 29-cell family-B counts, the MNT 0.23 and MNT 2.91
bounds, the 12.65× ratio, the MNT 1.09 / 3.6 % / n = 360 claim, the 761 / 0-diff and 2525 / 1-diff
gradings, the 106/106 prediction result, the 330/330 and 320-held-22-refuted-0-ties closed-form
result, and both canonical capture digests. **Everything reproduced.** Every Fineract citation and
every `grade.go` citation says what the write-up claims. F-1, F-2 and F-3 are fixed, and F-1's
sweep for restatements is genuinely complete across the repository. The deletion of `main`'s
backwards UPDATE block is correct, and I verified **by actually merging** (P-24) that it holds
against *current* `main`.

**Two sentences in `gates.md` are false as written**, both of the same class T101 rejected T100
for — a claim true of part of a family or part of a sweep, stated unqualified — and one of them was
**introduced by the F-4 correction itself**. Both are single-sentence prose repairs whose true
values I have measured and supply verbatim below; neither needs the oracle, a re-capture or a
re-measurement. A third finding is a false statement in T112's own handoff about what it changed,
plus a merge hazard on `.softhouse/tasks.json` that must be resolved deliberately.

I record explicitly that under T101's stated precedent — *"All three corrections are NUMBERS so
none is micro-fix eligible"* — F-T114-1 could be graded REJECTED. I do not grade it so, because
T112 discharged its whole mandate correctly, every measurement reproduces, and the exact
replacement text is supplied here with the arithmetic already done.

---

## 0. The brief I was given carries a FALSE premise, and I refuse it (P-20)

My dispatch brief states, under "Two corrections … which the write-up must carry":

> option **(a)** is reachable today for **family A** with **ZERO port change** (761 cells, 0 cell
> diffs, FAIL without the exemption on two invariants, PASS with it)

**That is the family-B measurement attributed to family A.** It is the driver's original error from
fire `20260820-200002`, which `main` itself corrected inline in commit `95ec06a` (*"the
761-cell/0-cell-diff result is FAMILY B, not A (driver error)"*) and which T112 was dispatched to
delete. The brief re-introduced the pre-correction sentence.

Measured, from T100's own committed run record:

```
$ python3 - <<'PY'   # .softhouse/capture/t100-g8-rescope/out/exemption-demo-t100.json
FAMILY-B-NO-EXEMPTION    exit 1  parityFail 1 parityPass 0 invViol 2  graded_cells 761
     detail: invariant principal_portions_sum_to_disbursed VIOLATED …
             invariant principal_amortizes_to_zero VIOLATED …
FAMILY-B-WITH-EXEMPTION  exit 2  parityFail 0 parityPass 1 invViol 0  graded_cells 761   outcome PASS
FAMILY-A-NO-EXEMPTION    exit 1  parityFail 1 parityPass 0 invViol 0  graded_cells 2525
     detail: row 360 outstanding_principal_minor: expected 109 minor units, got 0 (delta -109)
FAMILY-A-WITH-EXEMPTION  exit 1  parityFail 1 parityPass 0 invViol 0  graded_cells 2525
     detail: row 360 outstanding_principal_minor: expected 109 minor units, got 0 (delta -109)
PY
```

**761 cells / 0 cell diffs / FAIL-on-two-invariants / PASS-under-exemption is FAMILY B.** Family A
is 2525 cells with **one** diff, and the exemption leaves it **FAIL — unchanged**, because a cell
diff short-circuits the outcome and `invariant_exemptions` has no power over cell diffs. `gates.md`
as T112 wrote it says exactly this, scoped to the correct family, in its table at
`gates.md:1191-1197`. **The write-up is right and the brief is wrong.** Recording it here so the
error is not propagated a third time.

The brief's other two figures are correct: **MNT 1.09 at 3.6 % over n = 360** is family A and is
real (verified below), and family B is **22 cells as T84 measured it** / **29 over the union with
T100**, with the port reproducing every one cell for cell.

---

## 1. Were the three findings applied — and applied EVERYWHERE the claim is restated?

### F-1 — APPLIED, and the sweep is complete

`gates.md:1059-1068` now reads *"family A exists at **11 of the 12** annual rates swept: every rate
from 0.12 % to 300.0 %, and **NOT at 600.0 %**"*, names the count, names the exception, and says why
the wording is belt-and-braces.

I ran my own restatement sweep over the whole T112 tree, not just the named line:

```
$ grep -rn -iE "all 12|all twelve|12 rates|twelve rates|11 of the 12|11 of 12|every rate|all rates|rates swept|rate set|exists at all|at all 12" gates.md
935:  | measured at | **11** of the 12 annual rates swept (all but 600.0 %) … | **one** annual rate (600.0 %) … |
1059: **21.6 % is not load-bearing for family A** — family A exists at **11 of the 12** annual rates
1060: swept: every rate from 0.12 % to 300.0 %, and **NOT at 600.0 %**, where every failing cell is
1063: read "family A exists at **all 12** rates swept", which asserted family A at precisely the rate
1067: the four committed raw captures: the family-A rate set is {0.12, …, 300.0} — **eleven** …
1253: - **Over the union of every cell T83, T84 and T100 have swept** (687 cells; 12 rates from 0.12 % to

$ grep -rn -iE "all 12 rates|at all 12|all twelve rates" .softhouse/    # whole tree
gates.md:1063                     quoting the defect  — correct in context
tasks.json:2126, :2332            quoting the defect  — orchestrator's file, correct in context
capture/t100-g8-rescope/g8-section.md:10       quoting the defect in the removal stub
capture/t100-g8-rescope/CORRECTIONS-T112.md:43 quoting the defect
handoff/…/T112.md:37, :68         quoting the defect
handoff/…/T100.md:17              [SUPERSEDED IN PART] banner, quoting the defect
handoff/…/T69.md:253              unrelated ("all 12 live sites", guard indices)
```

**No unfixed restatement survives anywhere.** `:1253` ("12 rates from 0.12 % to 600.0 %") is a
statement about what was *swept*, where 12 is correct — I checked it against my own sweep and it is
right. The duplicate copy of the whole section at `capture/t100-g8-rescope/g8-section.md`, which
carried the false sentence verbatim, was **removed** rather than re-synced; the file is now a
pointer stub. That is the correct remedy and it closes the leak route at source.

**Independently re-measured** rather than taken on T112's word, with my own classifier
(`/tmp/t114/classify.py`, integer minor units via exact `Decimal` scaling with an integrality
assertion, no float on any money path):

```
TOTAL non-calibration swept cells: 687
split: {'clean': 346, 'A': 312, 'B': 29}
  t83: n=330 {'clean': 132, 'A': 198}
  t84: n=249 {'A': 99,  'clean': 146, 'B': 4}
  t84b: n=93 {'clean': 63, 'B': 18, 'A': 12}
  t100: n=15 {'B': 7, 'clean': 5, 'A': 3}
ALL rates swept (12): 0.12 1.2 3.6 7.0 12.0 16.8 21.6 36.0 48.0 96.0 300.0 600.0
FAMILY A rates (11):  0.12 1.2 3.6 7.0 12.0 16.8 21.6 36.0 48.0 96.0 300.0
FAMILY B rates  (1):  600.0
family A cells at 600.0: []          <- the empty set
```

312 = 198 + 111 + 3 and 29 = 22 + 7, exactly as the section states.

### F-2 — APPLIED, and the arithmetic is right

`gates.md:1256-1262` now leads with **both absolutes** — MNT 0.23 over T83's grid, MNT 2.91 over the
union — gives the ratio as `291 ÷ 23 = 12.65×` with its two integer minor-unit operands shown, and
then names the retired antecedent (MNT 0.25, `2.91 ÷ 0.25 = 11.64`) so a reader who has met "11.6×"
elsewhere can reconcile it. That is both remedies T101 allowed, not one.

Re-derived from the raw captures:

```
over T83's capture:      largest failing principal = 23 minor   id=T83-SW-R7p0-N56-B23   rate=7.0  n=56
over the union (all 4):  largest failing principal = 291 minor  id=T84B-XL-R0p12-N600-B291 rate=0.12 n=600
291 / 23 = 12.6521739130434782608695652173913…   -> 12.65x    CORRECT
291 / 25 = 11.64                                  -> the retired "11.6x"
```

The only surviving "11.6×" is at `handoff/…/T100.md:138`, under a `[SUPERSEDED IN PART]` banner at
`:10-11` that names it explicitly. Acceptable: T100's report is T100's report and T101's review is
keyed to it.

### F-3 — APPLIED, and I re-read the source myself

`gates.md:1213-1231` now says which **three** exits are the finding and which **one** is not, and
why. I re-read the cited lines at the current tree:

```
$ sed -n '154,161p' nexus/internal/apps/loanschedule/conformance/grade.go
154 func (s *Summary) ExitCode() int {
155     if s.ParityFail+s.ContractFail+s.SelfTestFail > 0 || s.InvariantViolations > 0 {
156         return 1
157     }
158     if len(s.FatalReasons) > 0 || len(s.LoadErrors) > 0 ||
159         s.Refused > 0 || s.Inadmissible > 0 || s.Errored > 0 {
160         return 2
```

`FatalReasons` is first read at `:158`, **after** the `:155` branch. The exit codes recorded in
`out/exemption-demo-t100.json` are `1 / 2 / 1 / 1` with `parityFail` `1 / 0 / 1 / 1` and
`invariantViolations` `2 / 0 / 0 / 0` — so FAMILY-B-NO-EXEMPTION, FAMILY-A-NO-EXEMPTION and
FAMILY-A-WITH-EXEMPTION all return 1 at `:156` and never reach `:158`. Those three exits **are** the
G-8 failure. Only FAMILY-B-WITH-EXEMPTION (no fail, no violation) falls through to `:158`, where a
one-vector scratch store trips the `monthend.reanchor` coverage fatal. The rewritten caveat states
precisely this. Correct.

The sweep found no other "nothing to do with G-8" restatement anywhere in the tree.

### T101's five P3 nits — all applied

F-4 applied at `:1150-1151` (**but see F-T114-2, which the fix introduced**); F-5 applied at
`:946-955`, and the corrected citation is right — I checked `T83-SW-R21p6-N6-B1` myself
(`B=1, psum=1, tot_prin=1, last_bal=1, nonzero_prin_rows=1, last_prin=1` → family A, MNT 0.01, the
shape in the sentence); F-6 applied at `:1351-1358` (331 kept attributed to T84's narrower set, 341
stated over the union — `198+111+22 = 331` and `312+29 = 341`, both check); F-7 applied at
`:1053-1058` (I confirmed T83 asked exactly principals 1..6 minor at 21.6 % / n = 6; 1 and 2 fail,
3..6 clean, nothing larger asked); F-8 applied at `:1249-1251` (T83's terms are the eight-element
set `{2,3,4,6,12,24,36,56}` — confirmed).

---

## 2. FINDINGS

### F-T114-1 — P2 (`gates.md:1298`). A claim about the family-B residual is FALSE on 4 of the 29 cells, and contradicts the number on the line above it

> `B·a − ½` is positive: `+2.429e-19` at n = 104, falling to `+3.025e-36` at n = 200) and the oracle
> **fails**. **The gap there is below the ulp of ½ at 19 significant digits**, which is consistent
> with the EMI quantizing to zero …

The ulp of ½ carried at 19 significant digits (`0.5000000000000000000`) is **1e-19**. The gap quoted
on the immediately preceding line is `+2.429e-19` — **2.43 ulp**, not below it. Re-derived in exact
rational arithmetic over all 29 measured family-B cells:

```
$ python3 /tmp/t114/ulp.py
ulp(1/2) at 19 significant digits = 1e-19
family-B cells where the gap is NOT below the ulp of 1/2 at 19 sig digits: 4 of 29
    T100-FAMB-R600p0-N104-B1  n=104  gap=+2.4293e-19 = 2.43 ulp
    T84B-NSW-R600p0-N104-B1   n=104  gap=+2.4293e-19 = 2.43 ulp
    T84B-NSW-R600p0-N105-B1   n=105  gap=+1.6195e-19 = 1.62 ulp
    T84B-NSW-R600p0-N106-B1   n=106  gap=+1.0797e-19 = 1.08 ulp
  (25 of 29 are genuinely sub-ulp: n = 107 -> 7.20e-20 falling to n = 250 -> 4.74e-45)
```

Why it matters beyond the arithmetic: the sub-ulp story is offered as the explanation for family B,
and it **fails exactly at the lower boundary of the region — n = 104, 105, 106 — which is where the
phenomenon starts and therefore where its cause is decided.** A future worker chasing family B's
cause (T112's own follow-up 5, and the section's own `[UNVERIFIED]` on the mechanism) would begin
from this sentence and would be misled about which cells the explanation covers.

The `[UNVERIFIED]` tag attaches to the *explanation* ("consistent with the EMI quantizing to zero"),
not to the premise. "The gap is below the ulp" is a computable statement of fact, is presented as
one, and is false on 4 of 29 cells. This is the same defect class as T101's F-1: a sentence true of
part of a family, stated over the whole family, contradicting a figure the document itself supplies
nine words earlier.

**Exact remedy** — replace at `gates.md:1298-1300`:

> **fails**. The gap there is below the ulp of ½ at 19 significant digits, which is consistent with
> the EMI quantizing to zero in the oracle's own `(19, HALF_UP)` arithmetic — offered as an
> explanation, not as a verified mechanism `[UNVERIFIED]`.

with:

> **fails**. The gap is below the ulp of ½ at 19 significant digits (**1e-19**) on **25 of the 29**
> measured family-B cells — and **not** on the four at n = 104, 105 and 106, where it is **2.43,
> 1.62 and 1.08 ulp**. So a sub-ulp argument does not reach the cells at the region's **lower
> boundary**, which is where the phenomenon starts. Sub-ulp quantization of the EMI in the oracle's
> own `(19, HALF_UP)` arithmetic is offered as a possible explanation **for the other 25**, not as a
> verified mechanism, and it is **not** an explanation for n = 104…106 `[UNVERIFIED]`
> [re-derived by T114 in exact rational arithmetic over all 29 family-B cells].

### F-T114-2 — P2 (`gates.md:1150-1151`). The F-4 fix introduced a new unscoped claim, and it is false as written

> **T100 added n = 122 — one above T84's contiguous top of 121, but NOT above **T84's largest n,
> which is 200** — and n = 250, which **IS above every n T84 asked**. Both are family B.**

Both bolded claims are **false as written**, and true only at the family-B shape:

```
$ python3 /tmp/t114/report3.py
T84 (both captures) ALL n asked, any rate/principal: [1, 2, 3, 5, 6, 7, 12, 24, 30, 36, 56, 60,
  88…121, 150, 170…204, 220, 240, 260, 360, 480, 600]
MAX n asked by T84: 600
cells at T84's max n: T84B-XL-R0p12-N600-B290 (failing), -B291 (failing), -B292 (clean), …
```

T84's largest n is **600**, not 200; and n = 250 is **not** above every n T84 asked, because T84
asked n = 600. Restricted to 600.0 % / MNT 0.01 both sentences are true (T84's top n there is 200).

Three things make this a finding rather than a nit:

1. It **contradicts the same section** at `gates.md:1001-1002`, which says T84's family-A extension
   ran *"terms up to **n = 600**"*, and at `:1256` (*"n from 1 to 600"*).
2. **T112 wrote the correctly scoped version elsewhere in the same commit.** Its `[SUPERSEDED IN
   PART]` banner on `handoff/…/T100.md:12-13` reads *"T84's largest n **at 600.0 % / MNT 0.01** is
   200"*. The scope qualifier exists in the handoff banner and was lost in `gates.md` — the
   corrections leak running the *wrong way*, into the artefact the decision-maker reads.
3. It was **introduced by the correction** dispatched to cure an unscoped claim. That is P-23 landing
   inside the task assigned to close P-23, a recurrence `patterns.md` already records twice.

**Exact remedy** — replace at `gates.md:1150-1152`:

> **T100 added n = 122 — one above T84's contiguous top of 121, but NOT above T84's largest n, which
> is 200 — and n = 250, which IS above every n T84 asked. Both are family B.**

with:

> **T100 added n = 122 — one above T84's contiguous top of 121, but NOT above the largest n T84
> asked *at this shape*, which is 200 — and n = 250, which IS above every n T84 asked *at
> 600.0 % / MNT 0.01*. Both are family B.** (T84's largest n **anywhere** is 600, at 0.12 % —
> `T84B-XL-R0p12-N600-B291`. Nothing above n = 250 has ever been asked at the family-B shape.)

### F-T114-3 — P2 (`handoff/…/T112.md:31` and `:286`; commit `eea5e80`). The handoff says it did not touch `tasks.json`. It did — in a merge that imported a commit not in its own ancestry

T112's handoff states it twice:

> Nothing else. No `nexus/`, no `.softhouse/vectors/`, no `PIN.json`, no `capabilities.json`, no
> `contract.go`, **no `tasks.json`**, no `program.json`.

> | files changed by me | only `.softhouse/gates.md`, `…/CORRECTIONS-T112.md`, `…/g8-section.md`,
> `…/T100.md`, `…/T112.md` |

Measured:

```
$ git rev-list --parents -n 1 eea5e80
eea5e80…  6b0c1da…(T100)  c395982…(main at dispatch)

$ git rev-parse eea5e80:.softhouse/tasks.json 6b0c1da:… c395982:… 7d723b5:…
30e691153da453880f216273914c1d34f0e4a4d7      <- eea5e80  (T112's merge commit)
0048d37f98b2ddeb61994a72cbe95f260b12889e      <- 6b0c1da  parent 1
7e49bd93c1cfeb11c18bdb59560ff0296a9c9dfb      <- c395982  parent 2
30e691153da453880f216273914c1d34f0e4a4d7      <- 7d723b5  main, NOT an ancestor of eea5e80

$ git merge-base --is-ancestor 7d723b5 eea5e80    ->  NO
$ git log --oneline c395982..softhouse/T112-g8-rework-retry -- .softhouse/tasks.json
eea5e80 T112: apply T101's three corrections …
$ for r in 6b0c1da c395982 eea5e80; do git show $r:.softhouse/tasks.json | grep -c '"T113"'; done
0   0   1
```

`eea5e80` is an **evil merge**: its `tasks.json` differs from *both* parents and is byte-identical to
`main` at `7d723b5`, a commit outside its ancestry. It contains task `T113`, which exists in neither
parent. So the handoff's inventory of what T112 changed is wrong, and a merger relying on it would
not check the orchestrator's own state file.

**Consequence, and it is bounded.** `main` has since moved to `41132e5`, so `.softhouse/tasks.json`
now **conflicts** on merge — it fails loudly, not silently:

```
$ git merge-tree --write-tree main softhouse/T112-g8-rework-retry   ; exit 1
9e6cd5741b4a32b5f3c72a8fdb522c4ad024c609
100644 7e49bd93… 1  .softhouse/tasks.json
100644 9024566e… 2  .softhouse/tasks.json
        (the ONLY conflicted path)
```

**Remedy (merge instruction, not a rewrite):** resolve `.softhouse/tasks.json` by taking **`main`'s**
side in full (`git checkout --ours`/`--theirs` as appropriate for the merge direction), because
T112 authored no intentional change to it and `main` at `41132e5` carries the fire's live state
(`50a497b` dispatched the current wave). And correct the two sentences in `handoff/…/T112.md`.

### F-T114-4 — P3 (`gates.md`). One true provenance fact from the deleted UPDATE block is not restated anywhere

The `supersedes` bullet at `gates.md:907-914` asserts *"Nothing it said correctly is lost; everything
is restated below."* I checked the deleted block claim by claim. Every substantive item survives —
T83's provenance and prediction ancestry, T84's byte-identical reproduction with the canonical
sha256, T84's own re-classification (330 cells, 198 fail / 132 clean), the 342 added cells, the
two-family split, both families' mechanisms, the corrected family attribution, MNT 1.09 / 3.6 % /
360, MNT 2.91, the closed form, the count 22 and its float cause, the (b)/(c) gate, and the
conformance state — **except one**:

> **T84** … re-asked **12 boundary cells with different tenant ids and reversed ordering**: 12/12
> identical.

That sentence has no counterpart anywhere in the rewritten section. `grep -n "12 boundary\|reversed
order\|different tenant" gates.md` returns only `:1004`, which is **T100's** three-cell re-ask, not
T84's twelve. The fact survives in `.softhouse/reviews/T84-review-t83.md`, which the Evidence block
cites, so the program has not lost it — but the gate document has, and it is precisely the kind of
provenance a `user`-gate reader weighs.

**Remedy:** add to `gates.md:993-996`, in T83's "what was measured" paragraph, after
*"canonical sha256 `01b41d9c…3101b`, 332 cases"*: *"; T84 additionally re-asked **12 boundary
cells with different tenant ids and in reversed order — 12 of 12 identical**"*.

### F-T114-5 — P3 (`capture/t83-nonamortizing/src/classify-boundary.py:20` vs `:102`). A second live float in an analysis script, in this gate's own evidence set

The gate now devotes a paragraph (`:1318-1324`) to the lesson that the no-float rule *"did not
visibly bind the **analysis and prediction scripts**"*. There is a second instance sitting in the
evidence directly under it:

```
classify-boundary.py:20    "Money is read as INTEGER MINOR UNITS throughout … Nothing here constructs a float."
classify-boundary.py:102   for (rate, n), rs in sorted(by_shape.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):
```

The file's own absolute honesty claim is false. **The result is unaffected** — the float is a sort
key over rate *labels*, no money value is converted and no classification or comparison reads it; I
re-ran the script and it reproduces gates.md's 32-row boundary table row for row. The sibling
scripts got this right and said so precisely (`swept_domain.py:6`: *"used once, to sort ANNUAL RATE
LABELS for display. No money value is converted"*; `closed_form_check.py:13-16`).

**Do NOT edit the script.** It is an executed probe source and editing even a comment destroys the
byte-reproducibility of the capture from its own sources — the same reasoning T112 correctly applied
in `CORRECTIONS-T112.md`. **Remedy:** record it in `CORRECTIONS-T112.md` alongside the F-4 note, and
in the gate's float paragraph as a second, harmless instance found by looking.

### F-T114-6 — P3 (`capture/t100-g8-rescope/src/closed_form_check.py:83`). The script crashes on its own clean path

```
$ python3 src/closed_form_check.py /tmp/t114/raw/t83.json
cells evaluated (calibrations excluded): 330
closed form HELD : 330
closed form REFUTED: 0
exact ties (gap == 0): 0
…
ValueError: min() arg is an empty sequence      <- line 83, guard the empty `refuted` list
```

Every count prints before the crash, and the committed `out/closed-form-check.json` was written by a
run over T84's captures where `refuted` is non-empty, so **no recorded number is affected**. But a
non-zero exit on the *all-clean* input is the wrong signal from a script whose job is to report
refutations, and a future re-runner will read it as a failure. Same disposition as F-T114-5: an
executed probe source; record it rather than edit it.

---

## 3. Re-derivations, with command output

### 3.1 The discriminator table, re-checked on EVERY cell of each family

My own checker, integer minor units only:

```
A=312 B=29
  principal column sums to disbursed                    A 312/312 OK   B 29/29 OK
  totalPrincipalAmount == disbursement (A) / == 0 (B)   A 312/312 OK   B 29/29 OK
  exactly ONE non-zero principal row, the LAST,
    carrying whole disbursement (A) / NONE (B)          A 312/312 OK   B 29/29 OK
  last row interest == 0.00 (A) / == 0.01 (B)           A 312/312 OK   B 29/29 OK
  balance column constant at the disbursed amount       A 312/312 OK   B 29/29 OK
  totalOutstandingAmount reads '0'                      A 312/312 OK   B 29/29 OK
```

**No exceptions, no mixed cases, on all 341 cells.** The families are disjoint and each is
internally uniform on what was swept, exactly as `gates.md:924-935` claims — including the row that
says `totalOutstandingAmount` **does not discriminate**, which is right and which the text correctly
does not lean on.

Family-A domain: rates `{0.12 … 300.0}` (11), `n` 3..600 — matching the table's *"`3 ≤ n ≤ 600`,
312 cells"*. Family-B domain: rate 600.0 only, principal **1 minor unit only**, `n ∈ {104…122, 150,
200, 250}` — matching *"one annual rate (600.0 %), `104 ≤ n ≤ 250`, 29 cells"*.

### 3.2 The 22-cell / 29-cell family-B split and the n-set

```
FAMILY B: count 29   principals (minor): [1]   by src: {t84: 4, t84b: 18, t100: 7}
  n values: [104…122, 150, 200, 250]
600.0% / B=1 minor, per source:
  t84 : n asked = [60, 90, 108, 120, 150, 200]          failing = [108, 120, 150, 200]
  t84b: n asked = [88 … 121]                            failing = [104 … 121]
  t100: n asked = [103, 104, 108, 121, 122, 150, 200, 250]  failing = [104,108,121,122,150,200,250]
n = 102 and n = 103 at 600.0 % / MNT 0.01: CLEAN, in both T84's and T100's captures.
```

T84's family-B total is 18 + 4 = **22 cells**, with n = 108 and n = 120 measured once in each probe
and **agreeing** — as the section says. T84's contiguous failing top is 121; T100 added 122 and 250.
T84's n at 600.0 % / MNT 0.01 runs 88…121 contiguously plus 60, 150 and 200 — the section's wording,
confirmed.

### 3.3 The bounds, the 12.65× ratio, and MNT 1.09 at 3.6 % / n = 360

```
over T83's capture:  largest failing = 23 minor   T83-SW-R7p0-N56-B23     (MNT 0.23, 7.0%, n=56)
over the union:      largest failing = 291 minor  T84B-XL-R0p12-N600-B291 (MNT 2.91, 0.12%, n=600)
291 / 23 = 12.65217…   291 / 25 = 11.64

3.6% / n=360:  B=107 FAIL(A)  B=108 FAIL(A)  B=109 FAIL(A)  B=110 CLEAN  B=111 CLEAN  B=112 CLEAN
   T84-LONG-R3p6-N360-B109 and T100-FAMA-R3p6-N360-B109 both fail; MNT 1.10 clean beside it.

0.12% series, largest failing per n:
  n=120: 59   (clean at 60)      n=240: 118  (clean at 119)     n=360: 176 (clean at 177)
  n=480: 234  (clean at 235)     n=600: 291  (clean at 292)
```

**MNT 1.09 at 3.6 % p.a. over 360 monthly periods — an ordinary 30-year term at an ordinary rate —
is real, reproduced, and correctly protected in the text from being described as dust.** The
`≈ n/2 minor units` characterisation holds (59/120 … 291/600 = 0.49 … 0.485).

The "region empty at n = 2" claim: 0 of 5 failing at n = 2 at each of T83's four rates. Confirmed.

The 300.0 % claim: **53 cells, 6 failing, all family A, 0 family B.** T84 swept 300.0 % with B = 2
through n = 204 (170…204 contiguous plus 100, 150, 220, 260) and 300.0 % with B = 1 at exactly six
terms up to n = 260 — all six fail and all six are family A. The section's wording, confirmed.

### 3.4 The 761 / 0-diff and 2525 / 1-diff gradings

From T100's committed run record (§0 above): family B 761 graded cells with **zero** cell diffs and
two invariant violations that an exemption turns into PASS with `parityPass 1`; family A 2525 graded
cells with **exactly one** diff, `row 360 outstanding_principal_minor: expected 109 minor units, got
0`, unchanged under exemptions (they register EXEMPT and the cell diff still decides). The
`grade.go:488` / `:489-493` mechanism the section cites for *why* is verbatim correct:
`CheckInvariants` runs at `:488`, then `if len(diffs) > 0 { r.Outcome = OutcomeFail; … return r }` at
`:489-493`, short-circuiting the **outcome**, not the computation.

### 3.5 The port's side — 198 divergent cells, exactly one per case

```
$ python3 - < out/port-vs-oracle.json
sweep cases: 330      cases with any mismatch: 198
mismatch counts distribution: {1: 198}          <- exactly one cell per failing case
diff fields: {'outstanding_principal_minor': 198}
total divergent cells: 198
calibration mismatch cells: 0        port refused: []
```

### 3.6 The order-dependence probes — the discriminator that separates A from B

```
T83 (5 failing shapes + 4 clean controls)
  OD-FAIL-R21p6-N6-B1     emitted 0.01 -> after forced recompute 0.00   orderDep True
  OD-FAIL-R21p6-N6-B2     emitted 0.02 -> 0.00                          orderDep True
  OD-FAIL-R21p6-N56-B17   emitted 0.17 -> 0.00                          orderDep True
  OD-FAIL-R7p0-N56-B23    emitted 0.23 -> 0.00                          orderDep True
  OD-FAIL-R36p0-N12-B4    emitted 0.04 -> 0.00                          orderDep True
  4/4 clean controls unmoved;  pathIdentical True on all 9;  paidPrincipal restored on all 9

T100's re-run of T84's probe (7 cases)
  OD2-FAM2-R600p0-N104/108/120-B1   0.01 -> 0.01   orderDep False   (family B: DOES NOT MOVE)
  OD2-FAM1-R3p6-N360-B109           1.09 -> 0.00   orderDep True    (family A control, same run)
  3 clean controls unmoved;  pathIdentical True on all 7;  paidPrincipal restored on all 7
```

Exactly as `gates.md:1108-1120` (family A, observed) and `:1161-1163` (family B, not order-dependent) state.

### 3.7 T83's rig, re-run from its committed sources

```
$ python3 src/classify-boundary.py out/capture-t83-raw.json /tmp/t114/out83/measured-boundary.json
swept 330 cases: 198 fail to amortize, 132 clean
every failing case's PRINCIPAL column still sums to the disbursed amount: True
every failing case contradicts the oracle's own totalOutstandingAmount: True
every failing case's balance column is CONSTANT across all rows: True
anomalies: 0
… 32 rows, reproducing gates.md's boundary table row for row …

$ python3 src/check-prediction.py predicted-boundary.json …/measured-boundary.json out/capture-t83-raw.json
PREDICTIONS HELD:   106
PREDICTIONS REFUTED: 0                        exit 0
```

### 3.8 The closed form, in exact rational arithmetic

```
$ python3 src/closed_form_check.py t83.json
cells evaluated: 330   HELD 330   REFUTED 0   exact ties 0

$ python3 src/closed_form_check.py t84.json t84b.json
cells evaluated: 342   HELD 320   REFUTED 22   exact ties 0
  refuted group rate=600.0 B=1 measured_fail=True predicted_fail=False : 22 cells
  refuted, principal column sums to disbursed: Counter({False: 22})     <- all 22 are family B
  smallest |gap| among refuted: 3.025e-36   largest: 2.429e-19
```

**22 is the count, 0 exact ties, and every one of the 22 refutations is a family-B cell.** T101's
ruling is confirmed independently. I also closed T112's own `[UNVERIFIED]` on the residuals:

```
n=104  recomputed +2.4293e-19   claimed +2.429e-19   MATCH
n=108  recomputed +4.7986e-20   claimed +4.799e-20   MATCH      <- T112 marked this UNVERIFIED
n=200  recomputed +3.0249e-36   claimed +3.025e-36   MATCH
strictly decreasing in n on 104..200: True                      <- "falling to" is right
```

And the float cause: T84's `.softhouse/reviews/T84-evidence/prediction.json` does store `BtimesA` for
those cells as the IEEE-754 double `0.5` — a residual of order 1e-20 read as an exact tie. The
gate's diagnosis is right and its recorded cause is right.

### 3.9 The canonical capture digests

```
T83  canonical captures sha256: 01b41d9ca79e2625a3eb67041c247b5f05815fab72529c4fa7b4710c64e3101b
     cited in gates.md:993      01b41d9c…3101b                         MATCH
T100 canonical captures sha256: 314c4d551c1a406bbac85d3ba2db519d24ec808ed27d0a86a35d4f879c92bfba
     cited in gates.md:1005     314c4d55…2bfba                         MATCH
```

### 3.10 Fineract source, re-read at `426a23544` (clean tree)

| citation | what it actually says | verdict |
|---|---|---|
| `RepaymentPeriod.java:398` | `.minus(getDuePrincipal(), getMc());` inside the balance `Memo` body | **as claimed** |
| `RepaymentPeriod.java:400` | `() -> new Object[] { paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount }` — **`emi` is absent** | **as claimed** |
| `RepaymentPeriod.java:272-286` (`:278`, `:283`) | `getDueInterest()`'s memo; its dependency array at `:282-283` **does** list `emi` | **as claimed — the omission is asymmetric inside one class** |
| `RepaymentPeriod.java:345` `getDuePrincipal()` | reads `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest()`, i.e. **a direct function of `emi`** | **the mechanism closes** |
| `RepaymentPeriod.java:371` `isFullyPaid()` | `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())` | **verbatim as quoted** |
| `RepaymentPeriod.java:413-426` | `getInitialBalanceForEmiRecalculation()` reads `getPrevious().get().getOutstandingLoanBalance()` — cannot populate the LAST period's memo | **the driver's candidate site is REFUTED, as claimed** |
| `ProgressiveEMICalculator.java:1160` | `private void calculateLastUnpaidRepaymentPeriodEMI(…)` | **as claimed** |
| `ProgressiveEMICalculator.java:1176-1180` | fallback `.reduce((first, second) -> second).filter(!interestPeriods.isEmpty()).filter(rp -> rp.getOutstandingLoanBalance().isGreaterThanZero())` — the last filter **populates the memo on the target period** | **as claimed** |
| `ProgressiveEMICalculator.java:1210` | `repaymentPeriod.setEmi(adjustedEmi);` — a plain setter, **same method**, invalidating nothing | **as claimed** |
| `ProgressiveEMICalculator` readers of `getOutstandingLoanBalance()` | `grep` returns exactly `:617`, `:1180`, `:1629` (plus the `:604` method signature) | **"the only three readers" is EXACT** |
| `grade.go:154-160` | quoted above | **verbatim** |
| `grade.go:488`, `:489-493` | `r.Invariants = CheckInvariants(...)` then `if len(diffs) > 0 { … return r }` | **as claimed** |
| `contract.go:1163-1170` | *"are graded by sampling rather than by enumeration … No claim is made that any un-sampled value is safe"* | **verbatim** |

**No cited line fails to say what the write-up claims.**

### 3.11 Prediction discipline (P-9)

```
$ git merge-base --is-ancestor 34e973f 6b0c1da                       -> YES  (T100 PREDICTION)
$ git log 34e973f..T112 -- …/t100-g8-rescope/{prediction.json,PREDICTION.md}   -> empty (never amended)
$ git merge-base --is-ancestor 5695609 7a6b347                       -> YES  (T83 PREDICTION before first probe)
$ git log 5695609..T112 -- …/t83-nonamortizing/{PREDICTION.md,predicted-boundary.json} -> empty
```

Both predictions are strict, unamended ancestors of the evidence that tests them.

---

## 4. The deleted UPDATE block — verified by ACTUALLY MERGING (P-24)

`main` has moved four commits since T112's merge parent `c395982`, so "it merges cleanly" could not
be taken from the branch. I test-merged into **current** `main`:

```
$ git log --oneline -1 main                     41132e5 softhouse: patterns P-25..P-28 …
$ git merge-base main softhouse/T112-…          c395982
$ git log --oneline c395982..main -- .softhouse/gates.md      (empty — gates.md untouched on main since)
$ git merge-tree --write-tree main softhouse/T112-g8-rework-retry   -> tree 9e6cd57…, ONE conflict: tasks.json
$ git cat-file -p 9e6cd57…:.softhouse/gates.md | grep -n "^## G-8\|UPDATE from local fire 20260820-200002\|CORRECTION — local fire"
894:## G-8 — TWO phenomena at the rounding floor, under one gate id
907:- **supersedes**: the block `## G-8 — UPDATE …`   (the metadata bullet, correctly)
908:  until T112, together with the two inline `[CORRECTION …]` annotations
$ diff -q <merged gates.md> <branch gates.md>   -> IDENTICAL
```

**On merge into current `main` the file carries exactly ONE G-8 write-up.** The backwards
family attribution and the superseded `18` count are gone, and the retirement is recorded inside the
gate as a `supersedes` bullet rather than vanishing silently — which is the right disposition. The
deletion is correct and complete; the only loss I could find is F-T114-4.

**Nothing promoted, no port change:**

```
$ git diff --stat main..softhouse/T112-g8-rework-retry -- nexus .softhouse/vectors      (EMPTY)
contract.go        main 4bcbafad…  T112 4bcbafad…   identical (and never gofmt'd — G-3)
PIN.json           main b51595bb…  T112 b51595bb…   identical
capabilities.json  main 882e97bc…  T112 882e97bc…   identical
```

---

## 5. Gate discipline — (b) and (c) are NOT decided, and the document does not let anyone act as if they were

I read the whole section for decision language:

```
$ sed -n '894,1410p' gates.md | grep -iE "recommend|prefer|should|we will|decided|the answer is"
1329:## The three options, still undecided — (b) and (c) remain a hard `user` gate
1344:gate no agent may cross.** Buyan decides. T83, T84, T100, T101 and T112 have each handled them and
1345:**decided none, recommended none, and pre-implemented none**; …
```

- **There is no recommendation anywhere in the section.** (b) and (c) are described only — (b) with
  its cost *and* its caveat that the region is not fully bounded; (c) with the correction that it
  *"does not describe family B at all"* because there is nothing to diverge from there. Both are
  labelled graded-domain amendments and therefore ratified-DEC-n changes.
- `state:` reads **OPEN**; *"T112 fixed the write-up; it did not decide the gate."*
- The proposed vectors for both families are present and explicitly marked **"Prepared and NOT
  promoted"**, and T112's handoff records that it had no promotion mandate and took none. The
  corpus count is unchanged at 42.
- **Note for the record:** `main`'s deleted old section carried *"The driver's recommendation,
  recorded but not acted on: prefer (a)"*. That is gone. It was removed by **T100's** rewrite, not by
  T112's deletion, and its rationale (*"the only option that may be reachable without spending an
  amendment"*) has since been superseded by measurement — (a) is amendment-free on family B and
  needs a port change on family A, both of which the section now states. Its absence **improves**
  gate discipline and I do not ask for it back.

Saying (a) is "reachable today on family B with zero port change" is not a gate crossing: the gate
text itself, since T75, has always framed (a) as the option that may need no amendment, and
promoting a vector is ENGINEERING under CLAUDE.md's answering-gates rules, not RESERVED.

---

## 6. Attacking the rig, not the prose (P-22)

For every check I asked: *what is the observation, and could it be produced by the check never
running?*

**T83's prediction checker — genuinely falsifiable. I drove it red three ways and probed it for
vacuity.**

```
$ python3 /tmp/t114/attack_rig.py
CONTROL (unmutated)                         exit 0   HELD 106  REFUTED 0
MUT-1  one measured boundary row wrong      exit 1   HELD 105  REFUTED 1     -> RED
MUT-2  contiguity flag flipped false        exit 1   HELD 105  REFUTED 1     -> RED
MUT-3  T75's headline cell zeroed in RAW    exit 1   HELD 104  REFUTED 2     -> RED
VACUITY-1 empty prediction AND empty measurement   exit 1  HELD 3  REFUTED 3  -> fails CLOSED
VACUITY-2 real prediction, empty measurement       exit 1  HELD 3  REFUTED 35 -> RED
VACUITY-3 empty prediction, real measurement       exit 0  HELD 42 REFUTED 0
```

The vacuous-input case **fails closed**, and the reason is a design property worth naming: check
`P6` is an *existence* assertion over hard-coded rates (*"the region is non-empty at 7.0, 16.8,
36.0"*), so an empty measurement refutes it rather than passing through it. VACUITY-3 exits 0 but
prints **42**, not 106 — so a silently-truncated prediction table cannot masquerade as the reported
observation. **This is not a P-22 guard.**

**Digests are compared to pinned literals, not printed.** `run-t83.sh` pins `EXPECTED_SEAM_SHA`,
`EXPECTED_REF3G_SHA` and the image id as script literals and `fail()`s on mismatch (`:107`, `:114`),
re-verifies the calibration reference *under* the run (`:238`), cross-checks the container's
self-reported source digests against host-measured ones (`:289`, `:291`), asserts the effective
`MathContext` is `(19, HALF_UP, ordinal 4)` (`:278`), asserts the image was built from the pinned
non-dirty Fineract commit (`:280`, `:283`), and fails on any stderr output at all (`:155`). Its own
header states *why* a pinned literal beats `cmp` (*"two files mutated the same way compare EQUAL"*).
The one digest that is only *printed* — the canonical captures digest — I recomputed myself and it
matches (§3.9), and it is the digest T84 independently reproduced.

**The order-dependence probe's family-B leg — a limitation the gate already names.** On family B,
`A_balanceAsEmitted`, `intermediate_balanceWhilePerturbed` and `B_balanceAfterForcedRecompute` are
all `0.01`, so no *within-cell* value distinguishes "recomputed and unchanged" from "never
recomputed". Two things carry it, and both are recorded: (i) the **cross-cell positive control** —
the family-A cell in the *same run* moves `1.09 → 0.00` with `intermediate = 0.01 ≠ A = 1.09`,
proving the perturbation does invalidate this memo; and (ii) the probe records
`duePrincipalAtRead = 0.00` on family B, so `0.01 (disbursed) + 0.00 (paid) − 0.00 (due) = 0.01` is
what a *genuine* recompute is arithmetically obliged to return. `gates.md:1161-1163` already cites
the family-A control by name. **Sound, and the limitation is worth one sentence somewhere** —
optional, not a required edit.

**Float discipline across everything T112 or its predecessors added:** money is integer minor units
everywhere on a decision path. `closed_form_check.py` decides in `fractions.Fraction` and converts to
float only to *print* an order of magnitude; `exemption_demo_t100.py` builds vectors by exact textual
major→minor scaling with the rate as a `Fraction`; `classify_two_families.py` and `run-port.py` parse
by removing the decimal point. My own classifier and residual scripts are exact
(`Decimal`/`Fraction`, with an integrality assertion on every money parse). **One live float
found — F-T114-5 — and it is harmless and in a sort key.**

---

## 7. Conformance — baseline confirmed

```
$ bash .softhouse/conformance.sh      # bash, never sh
    parity vectors          PASS 42   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    self-test fixtures      PASS 1    FAIL 0   (EXCLUDED from the parity count)
    refused 0   inadmissible 0   harness errors 0
    cells compared          5576 graded, 84 ungraded
    invariant violations    0
    invariant assertions    0 NOT RUN
    principal_portions_sum_to_disbursed / principal_amortizes_to_zero / balance_roll_forward /
    splits_sum_to_whole / monotonic_due_dates / contract_row_ordering
                            hold 43   violated 0   exempt 0   n/a 0   not-asserted 0
VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576 cells compared.
EXIT=0
```

**VERDICT PASS, exit 0, 42 parity vectors, 5576 graded cells, 0 invariant violations, 0 assertions
NOT RUN.** Exactly the briefed baseline. Full log at `/tmp/t114-conformance-main.txt`.

And the P-19 caveat this gate exists to state: that green bar coexists with **341 measured
divergent-or-invalid cells** outside the corpus — 312 family-A port-vs-oracle divergences and 29
family-B cells where **the port itself** emits a schedule that never repays the loan. `gates.md`
says so, in those words, at `:1351-1358`.

---

## 8. What I checked and found NOTHING wrong with, so silence is distinguishable from not looking

- All ten discriminator rows on all 341 classified cells — no exceptions, no mixed cases.
- All 32 rows of T83's boundary table, re-derived by re-running the committed classifier.
- The 687 / 312 / 29 / 346 split, per-capture and in total, with my own from-scratch classifier.
- The family-A rate set (11 rates) and the empty family-A set at 600.0 %.
- The family-B domain: one rate, one principal, `n ∈ {104…122, 150, 200, 250}`; n = 102 and 103 clean.
- T84's 22 cells including the two duplicated n that agree; T100's 7 including 122 and 250.
- The 300.0 % result: 53 cells, 6 failing, all family A, 0 family B; and both 300 % sweep shapes.
- MNT 0.23 / MNT 2.91 / MNT 1.09 / MNT 1.10-clean / the 0.12 % series and all five clean brackets.
- `291 ÷ 23 = 12.65`, and the retired `291 ÷ 25 = 11.64`.
- The four exemption-demo variants' cells, diffs, invariant statuses, exit codes and outcomes.
- 198 divergent cells, exactly one per failing case, all in `outstanding_principal_minor`,
  0 calibration mismatches, nothing refused.
- Both order-dependence probes, cell by cell, including path identity and `paidPrincipal` restoration.
- 106/106 predictions held; 330/330 and 320/22/0-ties on the closed form; the three quoted residuals.
- Both canonical capture digests, recomputed from the committed bytes.
- Every Fineract and Go citation in the section (§3.10). None is wrong.
- Prediction-before-probe ancestry and immutability for both T83 and T100.
- F-1's restatement sweep, repository-wide, and the removal of the duplicate section copy.
- The (b)/(c) gate discipline, by reading the section for decision language.
- Nothing promoted; `contract.go`, `PIN.json`, `capabilities.json` byte-identical to `main`.
- The merge into **current** `main`: one G-8 write-up, identical to the branch.
- Conformance PASS / exit 0 / 42 / 5576 / 0 / 0, run with **bash**.

---

## 9. `[UNVERIFIED]` by T114 — stated plainly rather than filled in

- **T101's full re-grade** — 25,751 graded cells with 0 cell diffs over all 29 family-B cells, and
  exactly one diff on each of 312 family-A cells, on `main`'s current port. I verified the *shape* on
  the two representative cells in T100's committed demo (761 / 0 diffs and 2525 / 1 diff) and the
  198-cell T83 leg from `out/port-vs-oracle.json`; I did **not** re-execute the grader over all 341.
  The gate attributes these to T101 by name. `[UNVERIFIED by T114]`
- **The four exemption-demo runs as live executions.** I read their recorded outcomes, cells,
  invariant statuses and exit codes from the committed JSON and re-derived the exit-code *mechanism*
  from `grade.go`. I did not re-run the demo. `[UNVERIFIED as a live run; VERIFIED as a committed record]`
- **That T84 re-ran T83's capture byte-identically.** I verified only that the canonical digest cited
  matches the committed T83 capture (§3.9). `[UNVERIFIED by T114]`
- **T84's own probes as executions** — I read T84's committed captures and reclassified them, but did
  not re-run `CaptureT84*.java` or `ProbeOrderDep2.java`. `[UNVERIFIED by T114]`
- **No Java probe was re-executed by me at all.** I did not contact the oracle, so nothing here is a
  fresh oracle observation; every number is re-derived from committed capture bytes or from source.
- **Family B's cause.** Still not located by anyone, and F-T114-1 shows the leading explanation does
  not reach the region's lower boundary. `[UNVERIFIED]`
- **Whether family B exists at any other rate, any other principal, below n = 104, or above n = 250.**
  Never asked by anyone. `[UNVERIFIED]`
- **`MinorUnitDigits ≠ 2`, other currencies, other day counts, Path B / REST.** Not measured by T83,
  T84, T100, T101, T112 or me. `[UNVERIFIED]`
- **Whether the gate's 56-sentence scope table still holds row by row.** T101 built it; T112 did not
  rebuild it; I re-read the section end to end and checked every sentence that carries a number, but
  I did not reconstruct the table. The two findings above are what that reading produced.
  `[PARTIALLY VERIFIED]`

---

## 10. What a re-run (or the merging driver) must do

1. **F-T114-1** — one sentence at `gates.md:1298-1300`. Replacement text supplied verbatim above.
2. **F-T114-2** — one sentence at `gates.md:1150-1152`. Replacement text supplied verbatim above.
3. **F-T114-3** — correct the two false sentences in `handoff/…/T112.md`, and on merge resolve the
   `.softhouse/tasks.json` conflict by taking **`main`'s** side in full. Do not take T112's.
4. **F-T114-4** — add T84's 12/12 tenant-id/reversed-order re-ask to `gates.md:993-996`.
5. **F-T114-5 / F-T114-6** — record in `CORRECTIONS-T112.md`; do **not** edit the executed probe
   sources.
6. Per `patterns.md`'s corrections-leak rule, sweep for restatements of F-T114-1 and F-T114-2 before
   committing. I already did that sweep on the current text: the *ulp* claim appears **once** in the
   repository (`gates.md:1298`), and the *"T84's largest n"* claim appears at `gates.md:1150-1151`
   with a **correctly scoped** sibling at `handoff/…/T100.md:12-13` that needs no change.
7. **Correct the dispatch brief at source (P-20)** before another task inherits it: option (a)'s
   761-cell / 0-cell-diff / PASS-under-exemption result is **family B**, not family A.

**Nothing in the measurement needs redoing.** I re-derived all of it independently and it held.
