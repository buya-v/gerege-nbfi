# T255 — DEC-2 revision 8, PREPARED AND LANDED IN ONE FIRE

**Branch:** `softhouse/T255-dec2-rev8`. **Not merged — the driver merges.**
**Fork point / measurement commit:** `a71c1408d3315493bca763472598680c85b9ad0b` (`git merge-base
main HEAD` = my HEAD at dispatch). Every `[MEASURED by T255 at a71c140]` stamp in the document was
taken there.

**Files changed:** `docs/adr/DEC-2-gl-accounting-adapter.md` (+688 / −185) and
`.softhouse/capture/t255-dec2-rev8/`. **Nothing else.** `git status --porcelain` showed exactly those
two paths before commit.

---

## 1. What I did

**Revision 8 is LANDED in the ADR**, not proposed in a sidecar. That was the point of the task: rev 7
was prepared in one fire, `main` moved four merges under it, and its freshly re-measured citations
were already stale at the commit where it would have landed — G-14's own defect reproduced inside
the fix for G-14.

It carries **all of revision 7's substance** (which two independent reviews confirmed moved no
obligation and strengthened the caution), plus T251's `C-1`…`C-8`, plus the two sites the local
review found and the cloud review did not, plus **four more live stale sites neither review
enumerated**.

**43 hunks, applied by `instruments/30-apply-revision-8.py`, which is itself content-addressed:**
every hunk names an exact substring and asserts it occurs **exactly once** before replacing it. It
refuses rather than applying to a guessed position, and it proved that by refusing on its first run
(`H-6`'s BEFORE was missing two spaces of list-continuation indent). `T260` can re-run it against
`HEAD`'s blob and get the same bytes.

### C-1 … C-8, disposed

| | disposition |
|---|---|
| **C-1** every `conformance.sh` citation, re-measured at my landing commit | **NOT re-measured — ELIMINATED.** Measuring again would buy one cycle. `run_guards` was `:1474` in the draft, `:1504` at `66b7453`, and **`:1548` at `a71c140`**; the tallied invocations are `:1563-1569` and `guard_ledger_invariants` is `:1568`. **None of those numbers is in the document.** |
| **C-2** L821, the I-3 row | **CORRECTED.** Its *"Graded today?"* answer is NO and stays NO — no wording sweep over the answer column could ever reach it — so the falsehood was in the supporting citation, which is now an ANCHOR. |
| **C-3** §4.4.1 L847-874, incl. the fence listing **seven** and omitting `guard_no_fail_open_instruments` | **CORRECTED AND MADE DERIVED.** The fence now lists all eight and is re-parsed from `run_guards()` and compared IN ORDER. The "Five of the seven … and a sixth" arithmetic is now "Six of the eight … DERIVED by subtraction, not independently asserted". "The seventh does" → the NAME. |
| **the 35th site** §4.4's lead paragraph, *"and none of them can be graded today"* | **CORRECTED**, and named as the 35th site in §10 so the near-miss is recorded. |
| **C-4** the ordinal | **COUNT KEPT, "is the sixth" NOT PUBLISHED AS PROSE.** Prose uses the NAME everywhere. Both ordinals (invocation #7, tallied #6) live in one `[DERIVED: …]` token where both are re-derived and compared, so the basis can never be switched silently again. |
| **C-5** §5's heading *"and today that is ZERO vectors"* | **CORRECTED** — the old claim is kept in quotation marks as a past claim. |
| **C-6/7** §8.3's *"the seventh guard"* ×2 | **CORRECTED** to the name. |
| **C-8** `admit.go:139-147` ambiguous between two packages; `vector.go:77-81` is `:78-82` | **CORRECTED at every site revision 8 rewrites**, by ANCHOR, and the ambiguity is named in the banner. **Both defects confirmed at `a71c140`:** `func SchemaContexts` exists in `ledger/conformance/vector.go:71` AND `loanschedule/conformance/vector.go:78`. |
| **also:** *"DRAFT (revision 5), NOT RATIFIED"* while a ratified revision 6 | **CORRECTED**, and §10 now carries entries for revision 6, the rejected revision 7 and revision 8. |

### Four LIVE stale sites neither review enumerated, found by census and fixed

1. **`conformance.sh:718` / `:721`** for *"never runs `go test`"* — both stale (they are
   `guard_no_float_in_harness` comments at `a71c140`), and **the count was stale too**: the document
   said *"both occurrences"*; there are **four**, all comments. Fact holds; citation and count did not.
2. **`conformance.sh:1254`** for the `-context` pass-through — stale.
3. **`conformance.sh:1115-1116`**, `FU-A2-25-2`'s stale harness comment — **the comment is GONE.**
   `git grep -n -F 'records as not existing' -- .softhouse/conformance.sh` → **0 matches, exit 1**, a
   real measured negative (`P-80`, not `|| echo`). DEC-2 claimed in the present tense that it *"still
   reads"*. **`FU-A2-25-2` is recorded CLOSED.**
4. **`conformance.sh:401` / `:411`** — both **TRUE** at `a71c140`, converted to ANCHORs anyway. A
   citation that is correct today and perishable tomorrow is the class revision 8 exists to
   eliminate, not one it gets to skip because it happens to be green.

## 2. The mechanism, and why

**Full argument in `capture/t255-dec2-rev8/GATE-CLOSURE-BLOCK.md`.** In one paragraph: I adopted
**ANCHOR** (bind to an exact unique substring, with a `git grep -n -F` recipe) and **DERIVED** (a
source-property is written once, in a sentinel-marked fence, and re-parsed and compared), and argued
DOWN the third option — wiring a line-number checker — because it would have gone RED on `T253`'s
unrelated `mktemp` edits in this very fire, and **a gate with that false-positive rate is pinned into
an amnesty within two fires**, which is a life-cycle this harness already documents in
`FAILOPEN_PIN_FILE_LIST`. Elimination is stronger than detection: **an anchored document is correct
with nothing running.**

**Measured, both terms (P-67):** `verify-line-numbers.py`'s `SH_ROWS` holds **4** rows. DEC-2
carried **115** `path:NNNN` citations at `a71c140`, **90** into this repo. A hand-written row list
answers a question about its author's memory (`P-66`). My checker reads its population **out of the
document**.

**The document already prescribed this.** Revision 4 recorded it as `A2-25` FU-A2-25-3 — *"cite
function name plus a grep recipe … Revision 4 re-took them by hand; that does not scale and will go
stale again"* — and left it undone. It went stale twice more. Revision 8 performs it.

### Red drive (P-22) — `RED DRIVE: ALL ARMS BEHAVED AS REQUIRED`

Seven arms; the load-bearing one is **R1, the deliberate T253 collision**: 30 lines inserted above
every citation. **Anchors exit 0. The line-number checker goes red.** And the three numbers the
review re-measured now resolve to plausible neighbouring `warn` strings — **misleading a reader
rather than stopping one**, which is why this was never clerical. R2 rename → ROT. R3 duplicate →
AMBIG. R4 guard removed → count mismatch. R5 two guards **reordered with counts unchanged** →
order mismatch (a count-only check passes this; the arm exists because it would). R6 the document's
own token edited → mismatch. R0 calibrates clean. The instrument asserts the real tree is
byte-identical before and after, and it is.

## 3. No obligation moved — VERDICT: NO

`instruments/60-obligation-diff.py` → **`NO OBLIGATION MOVED: 0 finding(s)`**. Three complementary
legs, none sufficient alone:

* **LEG 1 — byte identity** over six obligation-bearing blocks: §4.2's predicates
  (`46c34263214b0ff8`, 10069 chars), §4.6's A-1…A-4, §4.10's registry, **§5.2's requirements 1–7**
  (`e6c3663f6eecfa75`, 20811 chars), **§5.3's ten-row table** (`47065d5ee6867bba`, 4240 chars),
  §5.5's `graded_against`. All **IDENTICAL**.
* **LEG 1b — cell-by-cell** over all seven rows of §4.4's invariant table. Only cell 5 moved, on
  exactly the four rows revision 8 edits; **column 4, where the obligations live, is byte-identical
  on every row including `I-7`'s `Idempotency-Key`**.
* **LEG 2 — modal-sentence set difference.** 87 distinct modal lines before, 95 after. **8 LOST,
  every one accounted in the instrument's own `ACCOUNTED` table** with the hunk that owns it — so
  the accounting is code, not prose. 16 GAINED, all printed so a reviewer can check none invents an
  obligation; they are about readers, resolvers and this document's process.
* **LEG 3** — the two obligations welded into §4.4's rule paragraph appear **verbatim on both
  sides**. The only clause deleted is the FACT *"and grades none of them today"*, and the added tail
  (*"no growth of this corpus will ever discharge them"*) **strengthens** the guard obligation.

Per-hunk table: `capture/t255-dec2-rev8/PER-HUNK-NO-OBLIGATION-MOVED.md`. **No row is class
OBLIGATION.**

## 4. Did not re-litigate what T251 settled

`PIN-ledger.json` stays at `dec2_revision: 5` — admission compares **vector to pin** and never reads
the ADR, anchored in the document at `add("dec2_revision %d but the store pins %d", …)`. The vector
store digest is unchanged. T247's §5.3 refusal is preserved and **restated in revision 8**: it does
not certify that any precondition is *adequately* discharged. The `P-5` claim is **re-measured by me
at `a71c140`**, not inherited (`instruments/15-p5-probe.py`): P-1 3, P-2 5, P-3 3, P-4 2, **P-5 0**,
P-6 4, P-7 4, P-8 1, P-9 3, P-10 8, **P-99 0** as a negative control, over 27 tracked files listed
in the transcript; `\b` discrimination proved where both needles exist (`patterns.md`: `\bP-5\b` 12,
`\bP-50\b` 2, unanchored 40).

## 5. BAR

| | |
|---|---|
| **probe line PRESENT?** | **YES — printed.** `70-bar-final.log:92` `reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`, repeated at `:101` as `oracle probe UP`. Presence read first, then value (`P-83`). |
| **verdict** | `70-bar-final.log:506` **`VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.`** Exit **0**. |
| **ledger** | parity 4/0 · oracle-refusal 2/0 · inadmissible 0 · harness errors 0 · 70 cells graded, 21 MONEY in `int64` minor units · invariants 0 violations, 11 non-vacuous assertions, 10 INDEPENDENT · all 6 wrong ledger implementations killed through the harness |
| **fail-open frontier** | 918 tracked `.sh`/`.py` inspected, **frontier 11 == pinned 11**. My instruments did not join it. **Re-run AFTER committing**, because the linter's population is `git ls-files` and an untracked instrument is not inspected — the first run's silence would have been a statement about the search, not the tree (`P-66`). |
| **vector store** | `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, read live. **UNCHANGED.** |
| **`.softhouse/conformance.sh`** | **NOT TOUCHED.** It is `T253`'s this fire. |

## 6. G-14

**Closeable on this artefact; not by my act.** `T255` is the preparing task; ratification is the
driver's, after `T260` passes clean. Full block: `capture/t255-dec2-rev8/GATE-CLOSURE-BLOCK.md`.

## 7. Follow-ups

* **`FU-T255-1` (HIGH, the honest weakness).** `20-verify-anchors.py` is **HAND-RUN**, which is the
  `P-45` shape. `.softhouse/conformance.sh` is `T253`'s this fire and not in my `files_hint`.
  **Pre-written wiring** for whoever next holds it, so it is mechanical:
  ```
  guard_dec2_citations() {
    python3 "$REPO_ROOT/.softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py" || return 1
  }
  ```
  invoked in `run_guards()` as `guard_dec2_citations || failed=1`. **Note what wiring it does to the
  document: it adds a NINTH invocation, which §4.4.1's DERIVED fence will then correctly fail on
  until the fence is regenerated — by design.** Elimination is why the document is correct in the
  meantime.
* **`FU-T255-2` (MEDIUM).** ~70 bare `admit.go` / `vector.go` / `grade.go` / `capability.go`
  citations under `nexus/` remain, **ambiguous between `loanschedule/conformance/` and
  `ledger/conformance/`** as well as perishable. Census in
  `evidence/10-citation-census-AFTER-rev8.txt`. Not converted: outside the enumerated site list, and
  converting 70 citations in the same fire that lands the mechanism would have buried the mechanism.
* **`FU-T255-3` (LOW).** `docs/adr/DEC-2-...:952` cites `guards/ledgerguard/main.go:151` and `:980`
  cites `main.go:852` — same class, not in my site list. **Not measured for staleness by me.**
* **`FU-A2-25-2` — CLOSED.** Recorded in revision 8 §8.3.
* **`FU-T247-2`, `FU-T247-3`, `G-12`** — inherited, untouched, still open. `FU-T247-2` is in
  `gates.md`, which another worker holds and which is not in my `files_hint`; **I deliberately did
  not re-measure it.**
* **A pattern worth landing** (`T251`'s FU-T251-4, sharpened): *every hit a sweep prints gets an
  explicit disposition — corrected, HISTORY, or refused with a reason — and an undisposed hit is a
  defect.* Revision 7's own sweep printed §4.4's lead paragraph and §5.2's heading; neither reached
  its edit list. Recorded in revision 8's §10 entry.

## 8. Unverified — marked honestly

1. **`[UNVERIFIED]` — that the 43 hunks are ALL the remaining stale sites.** I enumerated by
   instrument (`10-enumerate-citations.py`, whose population is the document, not a list) plus
   reading every region T251 named. The classes I cannot reach are the ones every prior pass named:
   a restatement in none of my forms, a claim carried as a bare NUMBER in a table cell, and a claim
   expressed as a SILENCE where a qualification should be.
2. **`[UNVERIFIED]` — that no obligation is expressed WITHOUT a modal verb.** LEG 2 is line-level.
   LEG 1 and 1b cover the blocks I identified as obligation-bearing; **that identification is mine
   and is not itself proved exhaustive.**
3. **`[UNVERIFIED]` — that each §5.3 precondition is adequately discharged.** Not claimed, by me or
   by revision 8. `FU-T247-3` stands.
4. **`[UNVERIFIED]` — `T243`'s authorship of `guard_no_fail_open_instruments`.** I verified it
   EXISTS and is invoked; I did not trace it with `git log -S`. Revision 8 attributes it to `T243`
   on the strength of the harness's own in-file comment, which is a transcription, not a
   measurement.
5. I ran the harness **twice** — once before editing, once after committing. Two green runs are not
   a stability claim.
6. **`main` may move under this branch.** That is now survivable in a way it was not for revision 7:
   the ADR carries no `conformance.sh` line number, so an insertion above one cannot invalidate
   anything. The `[MEASURED by T255 at a71c140]` stamps are honest stamps of when a figure was taken
   and are meant to be re-run, per the document's own freshness rule.

## 9. Standing-instruction compliance

* **P-75** — no bare `grep`, no `rg` in any committed instrument. All five are `python3 re` /
  `python3 str.count`; the two shell recipes I put IN the document are `git grep -n -F`.
* **P-80** — `git grep`'s status is classified everywhere: the `FU-A2-25-2` negative is reported as
  **0 matches, exit 1**, and my instruments' exit codes distinguish 0 / 1 / 2 with **2 reserved for
  "could not do the job", never printed as an absence**. No `|| true`, no `|| echo`, no
  `# lint-failopen: ok` hatch used. Confirmed against the linter itself: frontier 11 == pinned 11.
* **P-66/P-70** — every non-existence states where I looked and carries a calibrated positive
  control.
* **P-67** — both terms counted: 6/14 and 8/14 capabilities; 115 → 108 citations, 25 pinned / 70
  ambiguous; 87 → 95 modal lines, 8 lost / 16 gained; 4 checker rows vs 90 repo citations.
* **P-69** — every claim stamped `a71c140`, and the anchors re-verified after the final edit.
* **P-74** — committed with `git commit -F`, heredoc, no backtick through `-m`.
* **P-83** — probe **presence** read first, then value.
* **G-3** — `contract.go` untouched; no `gofmt -w` run on anything.
