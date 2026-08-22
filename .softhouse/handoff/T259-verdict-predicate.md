# T259 — a verdict field that never consulted its own recorded predicate

**Branch:** `softhouse/T259-verdict-predicate`. **Role:** coder. **Model:** opus.
**Base:** `main` at `a71c1408d3315493bca763472598680c85b9ad0b`.
**Depends on:** T241 (merged `d20836e`).
**Vector store digest:** `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` at start **and** at finish —
read live with `git rev-parse HEAD:.softhouse/vectors` both times (P-61). **Not touched by T259.**

Full argument: `.softhouse/capture/t256-verdict-predicate/DECISION-verdict-vs-predicate.md`.
(The directory is named `t256-…` because that is the `files_hint` T259 was dispatched with; the
task was renumbered T256 → T259 on merge after a concurrent cloud fire published a different T256.
The name is left alone deliberately — renaming it would break the only pointer the task carries.)

---

## 1. The re-derivation — the driver's "five and three" is CONFIRMED, exactly

Re-counted from the bytes, not from the brief, by
`.softhouse/capture/t256-verdict-predicate/rederive_counts_t259.py`:

* target `.softhouse/capture/t229-g8-site3/out/classify-t229.json`
* sha256 `f831736f07f1a6fecd4ee69b5a1de8dac0abcae89210f997e72526070f62821a`
* git blob `2f740a8bd064fae24bb80a3e1da439dd73c2f72b` at HEAD `a71c140` (P-69)

| measured | value |
|---|---|
| rows in file | 9 |
| rows **carrying** `P2_totalInterestEqualsNEplusB` | 6 |
| rows **lacking** it | 3 (all `RESCUED_BY_SITE3`; the P2 block is computed only on unrescued cells) |
| carriers with value **false** | **5** — driver said 5 ✔ |
| of those, verdict **affirmative** | **3** — `-B201`, `-B251`, `-B299`; driver's exact list ✔ |
| of those, verdict **negative** | 2 — `-B199`, `-B1450` |

**The driver is right and needed no correction.** One refinement worth carrying: the denominator
is **6, not 9** — "five of the six rows that carry the key", never "five of nine rows" (P-67, both
terms counted).

**Where I looked** (P-66/P-70): `out/classify-t229.json`, `src/classify_t229.py` (all 91 lines),
`PREDICTION.md` §2 incl. P1–P6, `prediction.json`, `src/cells-t229.json`, `src/site3.py`,
T241's two correction banners, both `MANIFEST.sha256` files, and all 1,499 JSON files under
`.softhouse/capture/`.

**How `verdict` is actually computed:** from `classify_t229.py`, it reads **exactly two things** —
the observed OUTCOME family against `predictedOutcome`, and `observedPrincipalMinor ==
predictedTotalPrincipalMinor`. It reads **zero** registered P-predicates, and structurally cannot:
every `P2_*` key is assigned *after* `verdict` is already in the row. `P1`, `P3`, `P4`, `P5` are
never computed per row at all.

---

## 2. The decision — ARGUED, with the losing side stated

> **The PREDICATE is the broken half. The verdict values stand, all nine.**

P2's third conjunct as registered, `totalInterestAmount = n·E + B`, is arithmetically wrong;
`n·E + B` is the total **repayment**. The recorded `false` is a correct measurement of an incorrect
claim.

**The measurement that decides it** — re-derived per row in integer minor units:

| | agreement between predicate and verdict |
|---|---|
| under the **registered** predicate | **3 of 6** carriers |
| under the **corrected** predicate `n·E + B − principalRepaid` | **6 of 6**, both directions |

A verdict genuinely tracking a *different* proposition would still disagree with a *correct*
predicate somewhere. This one disagrees nowhere. There is one error here, not two.

**The losing side, stated so the reviewer can weigh it** (full version in the DECISION, §4):
"`verdict` is the broken half; it should AND in every registered predicate the row computed."
Serious — P1–P6 are registered under *"Also predicted, and stated so it can fail"*, and the bare
word `verdict` does overclaim. **It loses because it would print three FALSE REFUTATIONS** on
`-B201`, `-B251`, `-B299`, cells that hit the predicted family *and* the predicted principal to
the minor unit (1, 51, 99 — figures `PREDICTION.md` says no other rule predicts at all). Recording
a successful novel prediction as refuted because the predictor's arithmetic was wrong elsewhere is
a worse and less reversible error than the one being fixed. It also would require either
retro-editing `classify_t229.py` (prohibited) or a successor that ANDs in a predicate now known to
be wrong.

**What the losing side is right about, and is kept:** the unqualified word `verdict` overclaimed,
and a false predicate beside an affirmative verdict must never again be silent. Both are fixed —
the graded proposition is now written down (`acknowledged.json:gradedProposition`), and R-VPA
makes the disagreement impossible to print silently.

---

## 3. The rule — R-VPA, red-driven on shapes it was not designed around

`check_verdict_predicate_agreement.py`. A row may not carry an affirmative verdict over a
predicate it recorded as false, unless a **sha-pinned** acknowledgement says why. **An
acknowledgement changes the EXIT CODE only — never the noise.** Every disagreement is printed on
every run, acknowledged or not.

Fail-closed in four directions, each closing an evasion the naive rule leaves open:
1. an **unrecognised verdict word** is a refusal (else the rule is beaten by renaming);
2. an **unregistered boolean key** is a refusal (assuming intent is how P2 got past);
3. **nil coverage** is a refusal (PREDICTION.md's own P5 principle);
4. **acknowledgements are pinned to sha256** — edit one byte and the block goes VOID and the rows
   go RED. T114/T176 enforced by the instrument instead of by discipline.

Discovery is generic: every dict in every top-level list (`cells`, `calibration`, anything future),
and `^P[0-9]+_` for predicates. It is not written around `cells` and not written around `P2_`.

**`red/drive-red.sh` — 14 legs, 14 pass** (transcript `red/drive-red-output.txt`):

| leg | shape | expect |
|---|---|---|
| `R1-fresh-predicate-fresh-verdict-word` | **container `observations`, id key `probe`, predicate `P7_…`, verdict key `outcomeVerdict`, word `CONFIRMED`, cell `SCRATCH-R120p0-N7-B77` — not one token in common with a T229 row** | RED 1 ✔ |
| `R2-unclassified-verdict-word` | verdict `"LOOKS FINE"` | RED 1 ✔ |
| `R3-unclassified-boolean-key` | `sanityCheckHeld: false`, verdict REFUTED | RED 1 ✔ |
| `N1-nil-coverage` | zero rows | RED 1 ✔ |
| `G1-false-predicate-negative-verdict` | false predicate under REFUTED | GREEN 0 ✔ |
| `G2-all-true-affirmative-verdict` | all true under PASS | GREEN 0 ✔ |
| `L1-real-evidence-green` | the committed file | GREEN 0 ✔ |
| `L2-loudness` | GREEN run must still print all 3 disagreements | 3 printed ✔ |
| `Va-byte-pin-whitespace-only-mutation` | **one added newline** voids the ack block | RED 1 ✔ |
| `Vb-byte-pin-semantic-mutation` | flip the ONE true P2, on `T229-R36p0-N1400-B150` — **a row not in the ack list** | RED 1, 4 disagreements ✔ |
| `E1-missing-target` / `E2-unreadable-register` | error path | exit **2**, probe absent ✔ |
| `S-self-failopen-lint` | P-80 lint on T259's OWN instruments | 0 findings ✔ |
| `S2-lint-driven-red` | planted `\|\| echo 0`, `\|\| true`, `rg`, `2>/dev/null`, `git grep -E`, no strict mode | lint exits 1 ✔ |

Exit codes are classified and never conflated: a leg expecting 1 that gets 2 **fails**. Probe-line
PRESENCE is asserted before any VALUE is read (P-83).

---

## 4. Byte integrity — nothing was retro-edited

```
$ git diff --name-status main...HEAD
A  .softhouse/capture/t256-verdict-predicate/...   (new files only)
A  .softhouse/handoff/T259-verdict-predicate.md
```

**Zero `M` lines. Zero `D` lines.** Not one pre-existing file is modified by this branch.
`classify-t229.json`, `classify_t229.py`, `prediction.json`, `cells-t229.json`, `site3.py`,
`PREDICTION.md` are all byte-identical to `main`.

**The strict-ancestor falsifiability guarantee is INTACT**, verified live at the start of the task
and again at the end:

```
$ python3 src/site3.py src/cells-t229.json | cmp - ../prediction.json   ->  rc 0
   sha256 both sides: c4a3f5db454604b0201e32a39cd0d52027e6e3a34c28a46ec31249b4d7f08a5c
```

T241's comment-only annotation still reproduces `prediction.json` **byte for byte**. T259 changed
nothing that could have broken it, and confirmed rather than assumed it.

**Manifest check, done before choosing the route (T236's convention):** neither
`t177-so-nondeterminism/MANIFEST.sha256` nor `tierA-a2/MANIFEST.sha256` mentions `t229-g8-site3`
(`/usr/bin/grep -c` → 0, **rc 1 = a real measured negative**, classified per P-80), and
`git grep -F <sha256>` over the tracked tree returns **rc 1** — no tracked file records these
bytes. So **no manifest pinned them.** This is *absence of coverage*, not a manifest's silence —
the distinction matters given that `manifest.py verify` under `tierA-a2/` was silently RED across
two merges. **T259 adds the pin that was missing**, in `acknowledged.json`, and drives it red twice.

---

## 5. Materiality — LOW, verified rather than asserted

* **No verdict moves.** All nine `verdict` values stand; the ruling is that they were already right.
* **No vector moves.** `HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` at
  start and finish. T259 writes nothing under `.softhouse/vectors/`.
* **G-8's region boundary is untouched.** T259 wrote nothing to `.softhouse/gates.md` and proposes
  no change to the region, to the conservative superset `B_minor < 1.5·n`, or to the status of the
  unproven conjecture `δ ≤ 1`. **G-8 options (b) and (c) are not raised, not referenced as live,
  and not put to Buyan — unconditionally, with no expiry.**
* **No gate conclusion moves.** `gates.md` already carried the CORRECT interest form.
* **No promoted figure, no capture, no `nexus/**` file, no Go code is involved.**

**The value here is the shape, not the blast radius**, and overstating a hygiene finding is its own
defect in this program.

**What this does NOT establish:** that any other verdict in the corpus is correct; that P1, P3, P4
or P5 were ever evaluated (they were not); that the calibration statuses are consulted by anything
(they are not); or anything about parity, cutover, or the Go port.

---

## 6. What P-78 turned up when pointed at my own fix

`census_verdict_shape.py` over the whole capture tree — **1,499** JSON files, **13** with the
classification shape, **1,450** without, **36** skipped as unparseable and counted (P-40).
**8 disagreements total.** Three are T229's. One is my own red fixture. **Four are new:**

> **B-1 (BACKLOG, OUT OF T259's SCOPE).**
> `.softhouse/capture/t219-g8-residual/out/classify-t219.json` carries the SAME defect on
> **three distinct rows / four predicate-verdict pairs**: `T219-R600p0-N103-B1` (two predicates),
> `T219-R600p0-N3000-B4499`, `T219-R600p0-N3000-B3001`. `classify_t219.py` computes
> `P2_totalInterestEqualsNEplusB` and its `verdict` does not consult it either. This appears in no
> handoff. **T259 measured it read-only and changed nothing** — `t219-g8-residual/` is outside the
> `files_hint`. A successor task should apply the same ruling there; the expected outcome is the
> same (the registered predicate is wrong, the verdicts stand), but it must be re-derived, not
> assumed, because T219's cells include `B4499` where the principal repaid is 1,499 and the
> arithmetic is worth re-checking.

> **B-2 (BACKLOG — the honest half of P-78, about T259 itself).**
> **Nothing reads R-VPA's output automatically.** `run.sh` exists and exits non-zero on refusal,
> but no probe line invokes it: `.softhouse/conformance.sh` is held by **T253** this fire and T259
> may not touch it. Until it is wired, R-VPA is in exactly the condition it was written to condemn
> — a measurement nobody reads. Suggested probe: call
> `bash .softhouse/capture/t256-verdict-predicate/run.sh`, test the **presence** of the
> `T259-VPA:` line before its value (P-83), and pin `unacknowledged=0`.

> **B-3 (BACKLOG, small).** `classify_t229.py` records `calibration[].status` and a `throws` list;
> **nothing aggregates either.** P6 says "if they do not [reproduce], nothing else in this capture
> is admissible" — a claim with no reader. Both currently read REPRODUCED / empty, so this is the
> cheapest possible moment to add a reader. R-VPA already covers the calibration **booleans**
> (`inputsIdentical`, `observedIdentical`, `threwIdentical` are registered as P6 conjuncts), so a
> future false one under `status: "REPRODUCED"` will now go RED — but a `status: "DIFFERS"` with no
> false boolean would still pass unremarked.

---

## 7. WHAT I SKIPPED, counted (P-40)

| skipped | count | why |
|---|---|---|
| `.softhouse/conformance.sh` | 1 file | **held by T253 this fire.** Consequence: B-2, R-VPA is unwired. Named, not hidden. |
| `.softhouse/capture/lib/` | 1 dir | held by T250 |
| `.softhouse/capture/tierA-a2/` | 1 dir | held by T164. **Read** for the manifest question; nothing written. |
| `.softhouse/capture/t219-g8-residual/` | 1 dir, **4 live disagreements** | outside `files_hint`. Measured read-only; B-1. |
| other capture dirs with the shape, 0 disagreements | 9 files | `charges/out/attested/attestation-exact.json`, `t117-familyb/out/ctrl-reproduction.json`, `t117-familyb/out/rp-reproduction-pass2.json`, `t219-g8-residual/out/check-promoted-t219.json`, `t223-g8-region-predicate/out/classify-t223.json` + my own 4 fixtures. Clean; nothing to do. |
| JSON files skipped as unparseable by the census | **36** | raw gzip/NDJSON captures under `actualactual/`, `mathcontext/`, `periodratio/`, `audit-t44/rerun-periodratio/`, `dec1-binding/`, `t131-grep/corpus/` (the last are deliberately poisoned fixtures). Each is **named on the census transcript**, never waved past. |
| `site3.py`, `classify_t229.py`, `prediction.json`, `classify-t229.json` | 4 files | **committed evidence.** T114/T176: not edited, byte-verified unchanged (§4). |

---

## 8. Float discipline (T145 / T207)

Every `json.load` T259 adds carries `parse_float=Decimal`. T259's files **reproduce nothing**, so
T207's ruling (`.softhouse/capture/audit-t44/analysis/T207/RULING-float-derived-predicate.md`:
"add `parse_float` is sometimes the WRONG repair, when a line faithfully REPRODUCES an earlier
script that loaded without it") does not apply here and the guard is simply added — read before
touching anything.

**And the site it correctly does NOT apply to:** `site3.py:302` and `classify_t229.py`'s three
loads are unguarded, and **must stay that way** — `site3.py` must keep reproducing `prediction.json`
byte for byte, and `classify_t229.py` produced committed evidence. Measured mitigating facts, so
nobody later mistakes a latent hazard for a live one: `src/cells-t229.json` contains **no float
literal at all** (rates are strings, `n`/`bMinor` are ints), and `out/classify-t229.json` contains
**0 float-shaped numeric tokens out of 160**. Nothing monetary in T259 is computed from a float;
every quantity re-derived here is an `int` in minor units.

---

## 9. Files

| file | what |
|---|---|
| `DECISION-verdict-vs-predicate.md` | the argued ruling, the losing side, the manifest check, materiality |
| `rederive_counts_t259.py` | independent recount + the corrected-conjunct re-derivation |
| `check_verdict_predicate_agreement.py` | **R-VPA**, the rule |
| `boolean-key-register.json` | PREDICATE vs DESCRIPTIVE for every non-`P<n>_` boolean; unregistered = refusal |
| `acknowledged.json` | the sha-pinned, labelled acknowledgement; declares `gradedProposition` |
| `census_verdict_shape.py` | the capture-tree census that found B-1 |
| `lint_failopen_t259.py` + `RULES-failopen.md` | P-80 self-check, driven both ways |
| `run.sh`, `run-output.txt` | the entry point B-2 wants wired, and its transcript |
| `red/drive-red.sh`, `red/drive-red-output.txt`, `red/fixtures/*`, `red/*.py` | the 14-leg battery |
