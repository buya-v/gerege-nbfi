# T387 — independent review of T360 (the DIVERGENCE vector class, G-19)

**Target.** `T360` on `softhouse/T360-divergence-class` @ `d6979763`, complete, not merged.
**Reviewer branch.** `softhouse/T387-review-t360`. Grant: `.softhouse/reviews/t387-review-t360/` only.
**Reference oracle.** UP and used **read-only** throughout:
`GET https://localhost:8443/fineract-provider/actuator/health` → `{"status":"UP",…}`.
T387 posted nothing, created nothing and deleted nothing in the oracle instance. The only oracle
call it made was one `GET /journalentries?transactionId=a29bca0816a7&transactionDetails=true`.

---

# VERDICT: **APPROVED WITH CONDITIONS**

The conditions are all merge-mechanical or follow-up; none of them is a defect in T360's own diff.

1. **PATCH 1 must land with the merge.** `EXEMPTION_PIN_LEDGER_WRONGIMPLS` `13` → `14` at
   `.softhouse/conformance.sh:3923`. **I verified `14` is the right number by counting the
   population from the binary itself**, and I verified by *running* that the merge result is
   exit 0 with it and exit 2 without it. **I did not apply it on my branch** — see §7.
2. **A follow-up should carry T360's own PATCH 3 further than T360 asked.** The run's top-line
   verdict prose in `loanschedule/conformance/report.go:592` now sits, unqualified, over a corpus
   that contains one captured vector on which the port demonstrably does **not** match the oracle
   (F-T387-1, MINOR). That file was outside T360's grant.
3. **`verbatimInCapture` is `bytes.Contains`, so a numeric PREFIX of a captured amount satisfies
   it** (F-T387-2, MINOR — driven, and shown to be *self-correcting* on this class).
4. **T359's measured remedy must be marked DO-NOT-APPLY in the record**, not merely "not taken".
   See §1: I drove it, and it is worse than T360 said.

Nothing in T360's diff violates a CLAUDE.md non-negotiable. **No float reached any money path.**

---

# 1. THE CENTRAL QUESTION — T360 vs T359 on `impl.go:276-279`

## Adjudication: **T360 IS RIGHT, and it is more right than the two reasons it gave.**

T359's F-T359-1 measured a one-line change at `impl.go:276-279` making the port's sub-minor-unit
residue refusal return `(*Refusal, nil)` with `HTTP 422` instead of a Go `error`, and reported
that T352's banked candidate vector then grades `FAIL`, exit 1, with no schema change. T360
declined it and routed the decision in `gradeOne` on the class instead, with `PortRefusal`
carrying no HTTP status field at all.

I did not take either side on assertion. **I rebuilt T359's remedy from source in a scratch
worktree at `main` and ran it, both against `ledger-go` and against the wrong implementation
T360 registers.** Instruments: `instruments/patch_t359.py`, `instruments/add_wrongimpl.py`.
Transcripts: `out/DRIVE-A2-t359-remedy-ledgergo-FULL.log`,
`out/DRIVE-B2-t359-remedy-wrongimpl-FULL.log`.

## 1.1 T359's measurement REPRODUCES exactly. That part of the review is sound.

`out/DRIVE-A-t359-remedy.log`, `out/DRIVE-A2-…-FULL.log`, full store, `ledger-go`:

```
LDG-T352-CANDIDATE-residue-3dp   parity  ledger_rest_posting  FAIL   1 cells (0 money)
    the implementation REFUSED a request the oracle ACCEPTED (HTTP 422
    error.msg.glJournalEntry.sub.minor.unit.residue): leg 0: ledger: monetary text
    "100.125000" carries sub-minor-unit residue at scale 2 …
    leg_count: want 2, got 0
ledger parity  PASS 7  FAIL 1        ledger harness errors  0        EXIT = 1
```

So T359 was right that the polarity exists, right that `amount_minor` is never compared on that
path, and right that the HARNESS-ERROR is caused by the error-leg return. **T352's original
"the schema cannot represent it" premise is indeed false, and T359's correction of it stands.**

## 1.2 But the remedy INVERTS THE GRADING. This is the decisive finding.

Same patched tree, same store, one flag different —
`-ledger-impl=ledger-wrong-residue-rounding` (T360's fourteenth, a port that rounds the residue
HALF_UP and posts). `out/DRIVE-B2-t359-remedy-wrongimpl-FULL.log`:

| implementation | `LDG-T352-CANDIDATE` | ledger parity | run exit |
|---|---|---|---|
| `ledger-go` — **the CORRECT port** | **FAIL** (1 cell, 0 money) | PASS 7 **FAIL 1** | **1** |
| `ledger-wrong-residue-rounding` — **DELIBERATELY WRONG** | **PASS** (11 cells, **4 MONEY**) | **PASS 8 FAIL 0** | **0** |

Under T359's measured remedy, **the deliberately wrong implementation is the one that passes and
turns the bar green, and the correct port is the one that turns it red.** It passes by matching
`"amount_minor": "10013"` — the number T352 wrote knowing neither system produced it — across
**four money cells**, and those four cells are folded into the census:
`ledger cells compared 143 → 153 graded, of which 39 → 43 are MONEY cells`.

That is a fabricated minor-unit money value entering the corpus *and being graded against a port*,
which is CLAUDE.md's first non-negotiable read literally ("no floating-point … in any … test
fixture" is the float half; "money is integer minor units" does not license inventing the
integer). It also inflates `LEDGER money cells compared`, a pinned figure.

**This is not something either T359 or T360 wrote down, and it settles the question on its own.**

## 1.3 T360's stated objection (1) — the fabricated 422 — holds, and is understated.

To return `(*Refusal, nil)` the port must fill a `Refusal`, and `Refusal` is documented and used
throughout as an **oracle-observed wire refusal**. Every one of the nine `&Refusal{…}` sites the
port already has carries an **observed** `403` and a **real Fineract globalisation code**
(`impl.go:377,410,461,490,509,676,765,963,971` — e.g. `403` +
`error.msg.journalentry.defining.openingbalance.not.allowed`). T359's route needs an invented
status **and** an invented `Code`; my drive had to make up
`error.msg.glJournalEntry.sub.minor.unit.residue` to run it at all, and that string then gets
**printed into the conformance report** beside eleven real ones. T360's type
(`PortRefusal{Marker, ObservedText}`) has nowhere to put either. Objection (1) is correct.

## 1.4 T360's stated objection (2) — the meaning changes for every class — holds, but it is the weaker one.

It is true that under T359's change a residue arriving on a *parity* vector grades as "the port
refused" rather than HARNESS-ERROR, and that "the corpus is broken" and "the port is wrong" stop
being distinguishable. Both are still red (exit 1 vs exit 2), so this degrades **diagnosis**, not
**detection**. Real, but it would not on its own have justified overriding a measured review.

## 1.5 A third consequence neither task named: the wrong-implementation gate degrades.

`.softhouse/conformance.sh:gate_wrong_ledger_impls_die` decides a wrong port DIED from
`rc == 1 && banner && (parityFAIL + refusalFAIL) >= 1`, read off the *printed* figures. Under
T359's remedy `ledger-go` **itself** prints `ledger parity FAIL 1` permanently. A baseline
FAIL that every implementation inherits makes `>= 1` a criterion that a wrong port satisfies
without the corpus discriminating anything — the kill census becomes vacuous in exactly the
`P-35` shape. T360's design leaves the correct port at `FAIL 0` and moves the figure only for a
port that actually diverges (measured: §2).

## 1.6 And T359's route can never be green, structurally.

On `main`, `grade.go`'s refusal-on-a-parity-vector branch appends its diff **unconditionally**
before `cmpInt("leg_count", …)`; `gradeOne` then sets `OutcomeFail` whenever `Detail` is
non-empty. There is no vector shape — not even `expect.legs: []` — that reaches that branch and
passes. **G-19 is an open, gated, recorded disagreement; T359's polarity can only express it as a
permanently red bar**, which is the state a later engineer deletes to get a green run. T360's §1
argument is correct on this point, and I verified the mechanism in the source rather than
inferring it from the run.

## 1.7 What the record must say

T359's F-T359-1 is a **good finding with a bad remedy**. Its diagnosis (the polarity exists; the
routing is the cause; the real gap is the missing unknowable-money sentinel) is sound and T360
built on it correctly. **Its "measured, not argued" patch at `impl.go:276-279` must be recorded as
DO-NOT-APPLY**, because a later reader who applies it from the review alone will (a) fabricate a
wire status and a globalisation code, (b) invert the grading of the residue case, (c) admit an
invented `amount_minor` into the money-cell census, and (d) make the wrong-impl kill criterion
vacuous. **T360 was right to refuse it, and right to say so in `grade.go` rather than only in a
handoff.**

---

# 2. NON-VACUITY — DRIVEN IN BOTH DIRECTIONS, PLUS THE GUARD IN THE MIDDLE

All on T360's branch as committed, from a clean tree (`git status --porcelain` empty).

| direction | conditions | result | transcript |
|---|---|---|---|
| **KILL** | full store, `-ledger-impl=ledger-wrong-residue-rounding` | **exit 1**; `LDG-DIV-01 … divergence … FAIL 2 cells (0 money)`; `ledger parity PASS 7 FAIL 1`; `divergence vectors PASS 0 FAIL 1`; **all thirteen pre-existing vectors PASS**; money cells still **39** | `out/DRIVE-C-t360-KILL.log` |
| **DEFLATION GUARD** | `LDG-DIV-01` withheld, `divergencePinCount` left at 1 | **exit 2**, `LEDGER FATAL: DIVERGENCE POPULATION 0, PINNED 1` | `out/DRIVE-D-t360-withheld-PIN-INTACT.log` |
| **LOAD-BEARING** | `LDG-DIV-01` withheld **and** `divergencePinCount` temporarily 0 | **`VERDICT: PASS (exit 0)`**; `ledger parity PASS 7 FAIL 0`; 142 graded / 39 money / 10 money + 21 structural kills / 26 citations | `out/DRIVE-E-t360-SURVIVES.log` |
| **CONTROL for the above** | same withheld/pin-0 tree, `ledger-go` | exit 0, identical ledger section | `out/DRIVE-F-t360-ledgergo-withheld.log` |

**The wrong implementation SURVIVES the whole store at exit 0 when `LDG-DIV-01` is withheld, and
dies only when it is restored. The new vector is the only thing that kills it.**

**Byte-identity, checked rather than believed.** I diffed the entire `LEDGER` section of
`DRIVE-E` (wrong impl) against `DRIVE-F` (`ledger-go`), same tree, vector withheld. The **only**
difference is the implementation-name banner — every vector row, every cell count, every money
count, every kill count, every citation figure is identical. T360's claim of byte-identity on all
thirteen pre-existing vectors is **confirmed**.

T360's own committed `out/T360-D02-wrongimpl-SURVIVES-without-the-vector.txt` reproduces my
`DRIVE-E` line for line on every counter. Its transcripts are honest.

**The kill is not decoration.** With the vector restored, `divergence.port_outcome` and
`divergence.port_refusal_marker` both move, the FAIL folds into `ledger parity FAIL`, the
`gate_wrong_ledger_impls_die` sed pattern matches it, and the merge run prints
`KILLED  ledger-wrong-residue-rounding — exit 1, ledger parity FAIL 1 + oracle-refusal FAIL 0`
(§7).

---

# 3. THE MONEY NON-NEGOTIABLE

## 3.1 No float reached a money path. Greps and the repo's own guards.

- Every `float`-family token in the diff (`float`, `float64`, `ParseFloat`, `json.Number`,
  `big.Float`, `big.Rat`, `%f`, `math.*`, `strconv.*`) is in a **comment or a test name**. Added
  non-comment lines matching `float|strconv|json\.Number|big\.|%f|math\.`: **zero**.
- **The repo's own guards ran on the branch and passed** (`out/BAR-branch-as-committed.log:1-8,
  659-660`): `no-float guard` over 69 vector `.json` and 6 Go packages / 63 `.go` files;
  `no-float census … 0 forbidden identifiers, 0 floating-point or imaginary LITERALS, 0 forbidden
  imports, 0 unscannable files`; the wire-float round-trip census, 0 altered.
- Every use of `ObservedAmountTexts` in the whole module is a `len`, a `%v` print, a
  `bytes.Contains`, or `hasResidueBeyondMinorUnit`'s byte scan. **It is never parsed, converted or
  compared numerically.** `hasResidueBeyondMinorUnit` finds `'.'` by index and compares each
  fraction byte with `'0'` — no `strconv`, no division, no exponent. The wrong implementation's
  `roundHalfUpText` / `incrementDecimalDigits` are string surgery with a hand carry.
- Every JSON **number** in `LDG-DIV-01…json` is an integer; the two decimals (`100.125`,
  `100.125000`) are JSON **strings**, which is this corpus's existing discipline for
  `amount_major_text` and not a new hole.

## 3.2 The money cells cannot be smuggled back in. **Nine authoring attacks, all refused.**

Every attack below was planted on `LDG-DIV-01` (or `LDG-01`) in a disposable worktree, driven,
and reverted; instruments `instruments/attack*.py`, `instruments/runattack*.sh`; transcripts
`out/attacks/`. The **control** is `out/CONTROL-t360-unmutated.log` — the unmutated store, same
binary, `LDG-DIV-01 … PASS 2 cells (0 money)`, `ledger inadmissible 0`.

| # | attack | outcome |
|---|---|---|
| A1 | `expect.legs` populated with **T352's `"10013"`** on both legs | **INADMISSIBLE** — *"expect.legs has 2 entries on a DIVERGENCE vector … Writing 10012 or 10013 records a number NEITHER SYSTEM PRODUCED"* |
| A2 | `expect.total_debits_minor` / `total_credits_minor` = `"10013"` | **INADMISSIBLE** — *"the port posted nothing to total"* |
| A3 | `expect.refusal` populated (422 + code + message) | **INADMISSIBLE** — *"that block is an ORACLE-OBSERVED wire refusal … the oracle did not refuse: it returned 200"* |
| A4 | `expect.http_status = 422` | **INADMISSIBLE** — *"this port produces no HTTP response at all"* |
| A5 | `oracle_accepted` smuggled onto the **parity** vector `LDG-01` | **INADMISSIBLE** — the both-directions guard fires on the *other* class |
| A6 | one digit changed in `observed_amount_texts` (`100.125000`→`100.125001`) | **INADMISSIBLE** — bytes not in the cited capture |
| A7 | a **representable** amount wearing the divergence badge (`100.120000`) | **INADMISSIBLE** — the vacuity guard *and* the verbatim check both fire |
| A8 | marker shortened to `"residue"` (7 chars) | **INADMISSIBLE** — *"the minimum is 12 … a comparison that cannot fail"* |
| A13 | marker not cut from `observed_text` | **INADMISSIBLE** |
| A14 | `oracle_accepted.gate` emptied | **INADMISSIBLE** |
| A10 | divergence **re-badged `parity`** (the way to inflate the parity tally) | **INADMISSIBLE** *and* `LEDGER FATAL: DIVERGENCE POPULATION 0, PINNED 1` |
| A11 | divergence re-badged `oracle-refusal` | **INADMISSIBLE** + the same population FATAL |
| A12 | class `divergence` with `expect.kind: journal-entry` | **INADMISSIBLE** |
| A15 | port made to refuse for an **unrelated** reason (leg off-chart) | **INADMISSIBLE** (pre-existing chart rule) |
| A16 | port made to refuse for an **unrelated** reason (future-date rule) | **INADMISSIBLE** (pre-existing date/outcome conflict rule) |

**A1–A4 are the ones the brief asked for specifically, and all four are refused.** An author
cannot be put in T352's position of inventing a minor-unit value: the fields are default-denied,
by name, with the reason printed.

## 3.3 The byte check is genuinely verbatim — isolated, with the sha pin neutralised.

`out/attacks/A9-capture-digit-mutated.log`, instrument `instruments/attack_capture.py`. I mutated
**one digit inside the cited capture artefact** (`T352-A09-residue-3dp-readback-cited.json`,
`100.125000` → `100.125001`) **and refreshed the vector's `provenance.capture_sha256` to the new
hash**, so the sha pin cannot be what catches it. Result — the verbatim check fires on its own:

```
oracle_accepted.observed_amount_texts[0] is "100.125000" and those bytes DO NOT OCCUR in
provenance.capture_ref (…/T352-A09-residue-3dp-readback-cited.json).
→ INADMISSIBLE, exit 2
```

**No normalisation, no parse, no numeric equality.** Confirmed.

## 3.4 The observation itself is real, and I re-derived it independently against the live oracle.

One read-only `GET /journalentries?transactionId=a29bca0816a7&transactionDetails=true` →
HTTP 200, `"amount":100.125000` on both legs, `"decimalPlaces":2` in the same body.
`out/T387-readback-a29bca0816a7.json`, and `out/T387-readback-sha256.txt`:

```
7163378b7ab73e9daf72175b6a90568f1607daa88e9813212d74c7e493b23841  T387's own live readback
7163378b7ab73e9daf72175b6a90568f1607daa88e9813212d74c7e493b23841  T352's cited capture
7163378b7ab73e9daf72175b6a90568f1607daa88e9813212d74c7e493b23841  T360's re-read
```

All three byte-identical, and that hash is the vector's own `provenance.capture_sha256`. The
divergence is live, and the vector's `rerun_invariant` re-runs.

---

# 4. THE CLASS DOES NOT INFLATE PARITY

Bar on the branch (`out/BAR-branch-as-committed.log`) and on the pin-patched merge result
(`out/BAR-merge-PIN-PATCHED.log`) agree:

- `ledger parity           PASS 7    FAIL 0` — **unmoved**.
- `exemption census READ: LEDGER parity vectors = 7 == pinned 7`.
- `exemption census READ: LEDGER money cells compared = **39** == pinned 39` — **unmoved**.
- `divergence vectors      PASS 1    FAIL 0   (pinned 1…)` — counted and printed **separately**,
  under its own heading, above the "what a green ledger section does not mean" block.
- `ledger cells compared 144` (+2, the two structural divergence cells), `kills named 10 money,
  **22** structural` (+1 structural, unpinned), `citations 28` (+2). All three movements were
  declared by T360 and all three reconcile against `DRIVE-E`'s measured 142 / 10+21 / 26 baseline
  **by running**, not by subtraction (P-83).
- The printed prose says, in terms: *"A DIVERGENCE IS NOT A PARITY PASS, and it is counted NOWHERE
  in `ledger parity PASS`"*, *"the port did NOT match the oracle"*, and *"A GREEN DIVERGENCE
  VECTOR MEANS 'THE DISAGREEMENT IS STILL EXACTLY AS RECORDED'. It is NOT progress, NOT a fix, and
  NOT evidence the port is right"*. **G-19 stays open and the bar says so.**

The asymmetric fold is real and I drove it: A17 (§6) produced `divergence vectors PASS 0 FAIL 1`
**and** `ledger parity PASS 7 FAIL 1`, exit 1. A divergence FAIL does turn the bar red.

---

# 5. THE PIN — 14 IS CORRECT, COUNTED NOT ASSUMED

```
$ conformance -list-implementations | grep -c 'DELIBERATELY WRONG'
14
```
and the fourteen names, sorted, include exactly one new one, `ledger-wrong-residue-rounding`.
**`EXEMPTION_PIN_LEDGER_WRONGIMPLS` must move `13` → `14`.** The pin is at
`.softhouse/conformance.sh:3923` on both `main` and the merge result; the symbol, not the line
number, is the anchor.

**T360 correctly did not touch the three held paths.** `git diff main...softhouse/T360-divergence-class`
is **empty** for all of `.softhouse/conformance.sh`, `.softhouse/bin/fire-program.sh` and
`.softhouse/capture/t363-oracle-baseline/instruments/`. Verified.

---

# 6. FINDINGS

## F-T387-1 — **MINOR.** The run's top-line verdict prose now sits over a vector the port does not match.

`nexus/internal/apps/loanschedule/conformance/report.go:592` prints, immediately under
`VERDICT: PASS (exit 0)`:

> `This means "matches the reference oracle on captured vectors, within the graded domain".`

With `LDG-DIV-01` in the store there is now **one captured vector on which this port demonstrably
does not match the reference oracle**. The sentence is saved only by its own trailing qualifier
(the divergence's graded domain *is* the two port-side structural cells) and by T360's census
~200 lines above it.

**Not T360's fault and not fixable in T360's grant** — `report.go` is outside it, which is why
T360 filed PATCH 3. **Condition:** the follow-up that lands PATCH 3 should also add the divergence
count to that sentence, e.g. *"…within the graded domain, and does NOT include the N recorded
divergences below"*. Driven: `out/BAR-merge-PIN-PATCHED.log:669-671` beside `:461-472`.

## F-T387-2 — **MINOR.** `verbatimInCapture` is `bytes.Contains`, so a numeric PREFIX passes.

`"100.12"` is "verbatim in" a capture containing `"100.125"`. Driven, A17
(`out/attacks/A17-request-prefix-substring.log`, instrument `instruments/attack5.py`): I replaced
both request legs' `amount_major_text` with `"100.12"` and the verbatim check **did not complain**.

**The class self-corrects, and that is the mitigating half of the finding.** The port then
converts happily and posts, so the grader catches it anyway:

```
LDG-DIV-01 … divergence … FAIL  2 cells (0 money)
    divergence.port_outcome: want "REFUSED", got "ACCEPTED"
    divergence.port_refusal_marker: want "carries sub-minor-unit residue at scale 2", got ""
    THE DIVERGENCE HAS MOVED: this port ACCEPTED a request it is recorded as REFUSING …
ledger parity PASS 7 FAIL 1     divergence vectors PASS 0 FAIL 1     exit 1
```

On the **oracle** side the same prefix trick is closed by the representability guard (A7).
**Suggested hardening, not a blocker:** anchor the amount texts with a delimiter-aware match, or
require at least one `request.legs[].amount_major_text` to carry a residue beyond the minor unit —
which would also tie the port's refusal *reason* to the class by construction rather than only via
the marker.

## OBS-1 — cosmetic. A pre-existing conflict diagnostic does not know the new `expect.kind`.

A16 produced: *"…but this vector records `expect.kind "port-refusal"` **(a POSTED ENTRY)**"*.
The refusal is correct; the parenthetical is wrong for the new kind. One string, pre-existing rule.

## OBS-2 — pre-existing, out of scope. `-context ledger` prints a mislabelled empty-store fatal.

Running with `-context ledger` prints *"ZERO VECTORS FOUND under …/vectors/ledger"* (it is the
loanschedule store that is empty) and normally exits 2; when a real FAIL is present the printed
verdict drops to exit 1 (A17). Both directions are non-zero, so nothing greens. Present on `main`,
not introduced by T360. My authoritative runs are the **full-store** ones.

## Not findings — claims I checked and found true

- All thirteen `divergence_test.go` tests named in the handoff exist and pass, including
  `TestTheResidueScanNeverBecomesANumber`, `TestTheWrongImplementationRoundsWithoutAFloat`,
  `TestTheWrongImplementationIsIndistinguishableOnEveryOtherVector`,
  `TestADivergencePassIsNotAParityPass`, `TestDivergencePopulationIsPinnedInBothDirections`.
- The divergence census is computed **above every early return in `Run`**, so an emptied corpus
  refuses rather than satisfying the pin by having nothing in it. Driven: A10/A11 both trip it.
- `AssertInvariants` deliberately does **not** run on the divergence class. Correct: the port
  posted nothing; asserting double-entry balance over an empty entry would be a green line over
  no evidence.
- `CellFields()` exercises `diffDivergence` with a probe, so both cell names are in the derived
  vocabulary and `divergent_cells` naming them is admissible. Confirmed by the vector loading
  admissible with its kill declared.
- The kill is declared `structural` with `margin_minor: "0"` — forced, not chosen: a money kill
  needs two int64 minor-unit values and this class has neither.
- `CONFORMANCE-SH-PATCH-REQUEST.md` is accurate: line 3923, the symbol, the reason, and the
  measured before/after all check out.

---

# 7. VERIFICATION — EXIT CODES, FROM CLEAN TREES

Every figure below was captured **after** the tree was clean (`git status --porcelain` empty).
No transcript here was taken with an untracked file present (the T370/T361 failure mode).

## On T360's branch as committed (`d6979763`, scratch worktree, clean)

| command | exit | probe line |
|---|---|---|
| `cd nexus && go build ./...` | **0** | — |
| `cd nexus && go test -count=1 ./...` | **0** | — |
| `bash .softhouse/conformance.sh` | **2** | **PRINTED**, reads `up` |

**The 2 is the pin working (P-84, `.softhouse/patterns.md:2813`), and it is the SOLE refusal.**
The probe line printed and reads `up`, so it is not an oracle outage; no HARD guard failed and the
build succeeded, so it is not either of those. The whole diagnostic is:

```
conformance: CENSUS wrong ledger implementations — discovered 14 registered as DELIBERATELY
conformance:   WRONG from the binary's own -list-implementations; pinned at 13.
conformance: WRONG-IMPLEMENTATION POPULATION 14, PINNED 13.
conformance: EXIT 2 — no verdict is available. This is NOT a pass.
```

I checked for a second failure hiding behind it: **there is none.** All nine
exemption-census reads printed `== pinned`, including `LEDGER parity vectors = 7`,
`LEDGER money cells compared = 39` and `LEDGER declared exemptions = 0`; there is no other
`warn`-level line and no other `EXIT` line in the log.

## On the MERGE RESULT — T360's branch merged into current `main` (`d1a6b7e6`)

Scratch worktree `/tmp/t387/merge`, branch `t387-scratch-merge`. **The merge is clean — no
conflicts.**

| tree | exit | note |
|---|---|---|
| merge result, **pin NOT patched** | **2** | probe `up`; sole refusal `WRONG-IMPLEMENTATION POPULATION 14, PINNED 13` — the merge hazard, exactly as T360 declared |
| merge result, **pin patched 13 → 14 in scratch** | **0** | probe `up`; committed first so the tree was clean |
| merge result: `go build ./...` | **0** | |
| merge result: `go test -count=1 ./...` | **0** | |

With the pin applied, the merge result is **genuinely exit 0**, and it prints the line the
non-vacuity requirement asks for, alongside the other thirteen:

```
conformance:   KILLED  ledger-wrong-residue-rounding — exit 1, ledger parity FAIL 1 + oracle-refusal FAIL 0
conformance:   all 14 wrong ledger implementations DIED through this harness, not by hand.
```

and `ledger parity PASS 7 FAIL 0`, `divergence vectors PASS 1 FAIL 0`,
`LEDGER money cells compared = 39 == pinned 39`.

> **THE PIN WAS APPLIED IN A SCRATCH WORKTREE ONLY AND IS NOT ON MY BRANCH.**
> `softhouse/T387-review-t360` does not touch `.softhouse/conformance.sh`. T375 holds that file.
> Per P-83 the driver reconciles the number by **running** the merge result after T375 lands, not
> by arithmetic — my measurement above is that reconciliation done in advance, not a substitute
> for it.

## Scope

T387 wrote only inside `.softhouse/reviews/t387-review-t360/`. It did not touch
`.softhouse/conformance.sh`, `.softhouse/bin/fire-program.sh`,
`.softhouse/capture/t363-oracle-baseline/instruments/`, `.softhouse/reviews/t382-review-t374/` or
`.softhouse/reviews/t389-review-t388/`. All mutation experiments were performed in disposable
`/tmp` worktrees and reverted; each was re-verified clean before the next.

---

# 8. WHAT THIS REVIEW DOES NOT SETTLE

- **G-19 remains OPEN.** Nothing here decides which behaviour is correct for Gerege. A green
  `LDG-DIV-01` means only *"the disagreement is still exactly as recorded"*.
- **T359's F-T359-5** (the blast radius: the `t305`/`t327` rigs pinning `60/64` and `26` by string
  equality, `reference-oracle.md:907,917,1001`) is untouched by T360 and by me. Still open.
- **The corpus still cannot grade the oracle's over-scale value against anything.** T360 prints
  this limit on every run. Closing it needs a decided rule for over-scale money — a gate, not a
  wider schema.
- **Cutover is unaffected.** This is a recording mechanism, not evidence of parity.
