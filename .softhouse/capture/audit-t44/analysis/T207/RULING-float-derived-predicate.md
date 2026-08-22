# T207 — May a float-derived predicate reach a verdict? The ruling

**Task:** T207. **Branch:** `softhouse/T207-float-derived-predicate`.
**Raised by:** T185 as its F-1, deliberately left unfixed and registered as a decision.
**Scope:** `.softhouse/capture/audit-t44/analysis/T207/`, `.softhouse/capture/leapboundary/analysis/T207/`,
and the handoff. No vector, no `nexus/**` file, no `conformance.sh` line, no `.softhouse/bin/` file
is touched.

---

## 0. The ruling in one paragraph

`t44_float_roundtrip_v2.py` occupies **Zone A — the oracle-facing wire — on the RESPONSE leg**.
In Zone A a float-derived predicate **may** reach a verdict, because **T186 already ratified one that
does**: rule A1's `repr(float(tok)) == tok` cannot be evaluated without constructing the float, and it
gates `conformance.sh` on every run today. The first non-negotiable bans a float from **carrying a
monetary value**, not from **being measured**; the predicates here return a `bool` and every amount
they compare is a `Decimal` built from exact text. So the answer is **yes — and on this corpus,
must**: value-loss (`P3`) is the only predicate that can gate the response leg, because byte-loss
(`P2`) has **41 legitimate failures** in this very corpus, which are the oracle's own `DECIMAL(19,6)`
scale witnesses that T186 rule A4 forbids treating as defects. `_v2`'s inherited comment *"these
floats never touch a verdict"* was **true of the original and false of `_v2`**, and it is the reason
the strongest measurement in the file was never wired to the verdict it prints.

---

## 1. The defect, re-verified from the live files (P-63 — nothing inherited from the brief)

### 1.1 The detector fires and the script reports PASS

`_v2` computes `lossy_value` at `:170`, `:176-177`, prints it at `:184-189`, and consults it at
`:190`. The identifier appears **nowhere inside any `failures.append(...)`**
[VERIFIED: `grep -A3 'failures.append' t44_float_roundtrip_v2.py | grep -c lossy_value` → `0`,
asserted in the battery, `T207-red/drive-red-v3-output.txt` LEG 0]. So `:201` sees an empty
`failures`, `:206` prints `T175 SUCCESSOR: PASS`, and `main` returns `0`.

Driven live, not argued [VERIFIED: `T207-red/drive-red-v3-output.txt`, LEG V-RED]:

```
  AS PREDICTED      _v2 exit status on a VALUE-CORRUPTED corpus (the DEFECT: it passes): 0
  AS PREDICTED      _v2 DID detect it and print it under VALUE-lossy: 1
  AS PREDICTED      _v2 nevertheless prints the PASS banner: 1
  --- _v2's own words, verbatim:
    |   literals whose float VALUE != the decimal : 3 of 5
    | T175 SUCCESSOR: PASS -- 1 of 1 files scanned, 0 skipped, 5 distinct literals inspected.
```

**A detector that detects and then reports PASS is P-22** — a guard that structurally cannot fail —
and this program's sixth-plus instance.

### 1.2 The PASS banner is NEW in the successor — confirmed

The original `t44_float_roundtrip.py` has **no verdict machinery whatsoever**: no `main()`, no
`sys.exit`, no `failures` list, and the strings `PASS` and `FAIL` do not occur in it
[VERIFIED: `grep -cE 'PASS|FAIL'` → `0`; `grep -cE 'sys\.exit|def main'` → `0`; battery LEG 0]. Its
committed transcript contains no verdict word either [VERIFIED: `grep -ci 'fail\|pass'
t44_float_roundtrip-output.txt` → `0`]. T175 added `failures`, the exit codes, and the banner.

**So the brief's description is correct on all three counts, and each was re-derived here.**

### 1.3 The corpus that would trip it is not exotic

Every literal in the planted negative control is a legal `numeric(19,6)` value — the shape Fineract's
own schema permits it to emit [VERIFIED: `LoanProductRelatedDetail.java:61-62`, `scale = 6,
precision = 19`, cited by T186 §2.2, and `DECIMAL(19, 6)` in
`db/changelog/tenant/parts/0001_initial_schema.xml:2040`].

| literal | float round trip | residue | plain meaning |
|---|---|---|---|
| `1234567890123.456789` | `1234567890123.4568` | **`0.000011`** | ≈1.23 trillion ₮ |
| `9999999999999.999999` | `10000000000000.0` | **`0.000001`** | `numeric(19,6)` near its own max |
| `9007199254740993.00` | `9007199254740992.0` | **`-1.00`** | 2⁵³+1, the textbook binary64 cliff |
| `12345678901234567890.12` | `1.2345678901234567e+19` | **`-890.12`** | T163 measured this same residue |

[VERIFIED: `T207/t44_float_roundtrip_v3.py --selftest`, transcript in the battery LEG X.]

---

## 2. Placing the file on T186's map

T186's boundary, quoted verbatim from `.softhouse/reviews/T186-wire-money-form-ruling.md` §7:

> **A float-shaped money token is admissible exactly where it is a faithful transcription of bytes
> the ORACLE defined, and is a rejection everywhere GEREGE defines the bytes.**
> Zone A: oracle defines them → admissible, byte-fidelity enforced.
> Zones B and C: Gerege defines them → rejection.

and the mechanical rule that decides which region a file is in:

> A future guard can implement this without judgement calls. **Path decides the rule.**
> ### Zone A — oracle-facing wire. `.softhouse/capture/**`

**`t44_float_roundtrip_v2.py`'s corpus is `.softhouse/capture/**/out/*.json`** — its own recipe names
`capture/periodratio/out/`, `capture/mathcontext/out/`, `capture/charges/out/fc/` and
`capture/charges/out/attested/` [VERIFIED: `_v2` docstring `:48-52`, reproduced byte-identically by
battery LEG 0]. These are **captured oracle responses**. Not `nexus/**` (Zone B). Not
`.softhouse/vectors/**` (Zone C).

> **REGION: Zone A, response leg.**

For completeness, because "which region" is the graded question: the file **is not** in Zone B — it
declares no Go type, no adapter field, no schema column; and **is not** in Zone C — it writes nothing,
least of all a vector (`git rev-parse HEAD:.softhouse/vectors` is unchanged at
`73c3ea7b43dd75f04884072719a87fc8e1d255c1`, asserted in the handoff).

---

## 3. The argument — why Zone A permits a float-derived verdict, and here requires one

### 3.1 Zone A already gates on a float-derived predicate, by ratified decision

T186 rule **A1**:

> **A1 — byte preservation (P2).** Every numeric token in every **request body** must satisfy
> `repr(float(tok)) == tok`. **This is already implemented and wired**:
> `.softhouse/capture/lib/check_wire_float_roundtrip.py`, invoked from `.softhouse/conformance.sh:784`.

[Line number re-derived: the invocation is live at **`conformance.sh:997`**, not `:784` — the file has
moved since T186 was written. The guard file and the invocation both exist. VERIFIED this fire.]

`repr(float(tok)) == tok` **cannot be evaluated without constructing a binary double**. It is a
float-derived predicate, it is ratified, it is wired, and it gates: a failure exits 2. That guard's
own docstring states the principle in the exact terms this ruling adopts:

> **THE ONE DELIBERATE `float()` (P-25)**
> The line marked SIMULATE calls `float()` on purpose: it **SIMULATES THE DEFECT, which is the only
> way to measure it.** No money conclusion is drawn from it — the comparison is between two STRINGS.

[VERIFIED: `.softhouse/capture/lib/check_wire_float_roundtrip.py`, module docstring.]

**Therefore the general question is already answered.** "May a float-derived predicate reach a verdict
in Zone A?" — it does, today, on every conformance run, by a decision T186 ratified and strengthened.
Answering *no* for `t44` would not be a cautious application of the non-negotiable; it would be an
unlicensed reversal of A1 by a task with no mandate to touch it.

### 3.2 The non-negotiable bans floats from carrying value, not from being measured

`CLAUDE.md`, first non-negotiable:

> **Money is integer minor units.** No floating-point in any monetary code path, struct field, schema
> column, API field, or test fixture — including intermediate calculation.

Every noun in that list — code path, struct field, schema column, API field, test fixture,
intermediate calculation — names a place where a float would **hold an amount**. In `t44_*_v3.py`:

- the parse hook returns `Decimal(s)` and the literal is keyed by its **exact source text**;
- `p2_text_lossy(s)` compares **two strings**;
- `p3_value_lossy(s)` compares **two `Decimal`s**;
- `residue(s)` is `Decimal − Decimal`;
- the only thing any `float()` produces is a **`bool`**.

No amount is ever held in, derived from, or rounded by a float. The float is the **simulated defect**,
not the arithmetic.

**And the opposite reading is self-defeating.** If no float-derived predicate may gate, then nothing
may detect a float hazard, and the first non-negotiable becomes enforceable only by assertion — which
is precisely the condition P-22 names as worse than no guard. The reading that forbids the detector
protects the defect.

### 3.3 Which predicate gates: P3 (value), not P2 (bytes)

On the **response** leg, byte-loss is not a defect. T186 rule **A4**:

> **A4 — responses are observations.** Never rewrite, never re-emit through a float, never normalise
> scale. `1200000.000000` is not a typo for `1200000.0`; the scale witnesses `DECIMAL(19,6)`.

and T186 §6.3 measured the population:

> **All 245 P2 failures are trailing-zero decimal forms** — `1200000.000000` → `1200000.0`,
> `21.600000` → `21.6`, `0.100000` → `0.1` — i.e. **scale-6 emissions by Fineract itself on the
> RESPONSE leg**, matching `DECIMAL(19,6)`. **The value is intact in every one; only the scale would
> be lost.**

This corpus carries **41 such literals** [VERIFIED: `t44_float_roundtrip-output.txt:6`, and re-measured
at 41 of 245 by `v3` this fire]. Gating on P2 here would refuse the oracle's own correct output and
pin the instrument permanently red — the exact error T186 rule **A2** forbids ("a rule of the form
'no float-shaped token in a request body' is **WRONG** and must be rejected in review").

**P3 is what remains**, and it is the narrower event: if the characters round-trip, the values are
necessarily equal, so **P3 failure strictly implies P2 failure**. A P3 hit is a P2 hit *plus* the
money changing.

### 3.4 The counter-argument, stated and answered

T186 §6.4 says, of P3:

> **So the money corpus sits ~7 orders of magnitude of significant digits below the value-loss
> threshold.** That is the honest reason P3 is zero — the margin is enormous, not marginal. It is also
> why **P3 should not be adopted as the guard property**: it would pass a corpus that had already
> drifted badly, and it will keep passing right up until it doesn't.

Read carelessly, that looks like "do not gate on P3", i.e. leave `_v2` as it is.

It is not, and the distinction is the whole of this ruling:

1. **That sentence is about A1 — the REQUEST-BODY guard** — where **P2 is available and is strictly
   stronger than P3**. There, adopting P3 *instead of* P2 would be a downgrade, and T186 is right to
   refuse it. On the **response** leg P2 is unavailable (§3.3), so the choice T186 was rejecting does
   not exist here.
2. **"Too weak to be the only alarm" is not "must be silent when it rings."** No reading of §6.4 makes
   `detect → print PASS → exit 0` correct. A predicate that fires only in a catastrophe is a
   *tripwire*, and a tripwire that stays quiet is not a weak tripwire, it is a decoration.
3. **The cost of wiring it is zero while it is green.** It currently reports `0 of 245`
   [VERIFIED: battery LEG V-GREEN]. This is T186's own G-C1 argument, applied here: *"the cheapest
   moment to add a guard is while it is already green."*

> **[T207's reading, marked as inference.]** T186 ruled on the request-body guard and did **not** rule
> on the response leg. §3.4 is T207's application of a T186 sentence written in a narrower context. It
> is recorded as reasoning, not quoted as T186's finding. If a later reviewer reads §6.4 as a blanket
> ban on P3 ever gating, that is a genuine disagreement to be settled, not a misquotation to be
> corrected — and it would still not license `PASS` on a corrupted literal, only a *rename* of the
> banner (§4).

---

## 4. The state `_v2` is in is indefensible under EITHER answer

This is worth stating because it is what makes the decision safe to make:

| if the ruling had been… | then `_v2` is wrong because… | the fix |
|---|---|---|
| **predicate MAY gate** (this ruling) | it detects and prints `PASS` | wire `lossy_value` to `failures` |
| **predicate MAY NOT gate** | it prints a **verdict** it has no basis to reach, on a corpus about which its own strongest measurement is silent | drop/rename the `PASS` banner and say loudly what it does not establish |

**`v3` does both**, which is why the ruling is low-risk: the value predicate now gates (R1), *and* the
bare word `PASS` is gone from the success banner, replaced by a scoped statement plus an explicit
`DOES NOT ESTABLISH` list (R4). A reviewer who overturns §3 gets a correct instrument anyway; only the
exit code changes.

---

## 5. What `v3` changed, and what it did not

Named changes R1–R7 are in `t44_float_roundtrip_v3.py`'s docstring. In summary: the value predicate
gates; text-loss explicitly does not, with the reason printed on every run; the false self-description
is removed; the bare `PASS` is gone; the population inspected is stated including the `NIL-COVERAGE`
shape; and a `--selftest` drives both directions.

**Unchanged: the arithmetic.** Over the legitimate 92-file charges corpus, `v3` reports the **same
245 distinct / 9,122 occurrences / max scale 6 / 41 text-lossy / 0 value-lossy** as `_v2` and as the
original [VERIFIED: battery LEG V-GREEN asserts `_v2` and `v3` agree on all three headline figures].

---

## 6. T114 — every file the standing ruling catches

**"Anything that produced COMMITTED EVIDENCE is superseded by a scratch copy, NEVER edited in place."**

| file | produced which committed evidence | what T207 did |
|---|---|---|
| `audit-t44/analysis/t44_float_roundtrip.py` | `t44_float_roundtrip-output.txt`, cited by `T44-capture-audit.md §T44-X1` | **untouched, byte-identical.** Re-run to confirm it still reproduces its transcript byte-for-byte (battery LEG 0). |
| `audit-t44/analysis/t44_float_roundtrip_v2.py` | the `_v2` transcripts recorded inside `T175-red/drive-red-output.txt` (LEGs 1–5) | **untouched.** Superseded by `T207/t44_float_roundtrip_v3.py`; supersession recorded in `T207/T207-SUPERSEDES.md`. It is **re-run** by the battery as the negative control, which is a read. |
| `audit-t44/analysis/T175-red/drive-red.sh` | `T175-red/drive-red-output.txt` | **untouched.** Widened scratch copy at `T207/T207-red/drive-red-v3.sh`; every widening named W1–W6. |
| `audit-t44/analysis/T175-red/census.py` | its counts appear inside `drive-red-output.txt` | **untouched, invoked read-only** by the T207 battery for the same two counts. |
| `leapboundary/analysis/T175-red/measure-other-sites.py` | `T175-red/measure-other-sites-output.txt` — where "12 pairs / 772 deltas / 0 swallowed / 57 considered" were published | **untouched.** Scratch copy at `leapboundary/analysis/T207/measure-other-sites-v2.py`, re-run from scratch; both transcripts kept. It is **re-run** on the planted root as the F-3 negative control. |
| `leapboundary/analysis/t55-analyse.py` | the T55 report and every `-exact.json` sidecar | **untouched.** Imported READ-ONLY for `cells` and `MONEYISH`. The drop counter lives in the **measurer**, never in `t55-analyse.py` — which is also what F-3 asked for. |
| `leapboundary/analysis/t55-prior-capture-assessment.py` | `T55-PRIOR-CAPTURE-ASSESSMENT.txt` | **untouched and not read for edit.** It is the *subject* of the measurement, not a target. |
| `.softhouse/vectors/**` | the parity corpus | **untouched.** Digest re-checked. |
| `.softhouse/conformance.sh`, `.softhouse/bin/`, `.softhouse/gates.md`, `.softhouse/capture/tierA-a2/` | — | **untouched** (held by other workers this fire). `tierA-a2` was **read** for T163's prover discipline; nothing under it was written. |

---

## 7. F-2 — the `json.load(parse_float=)` counts, both terms, re-measured

See `.softhouse/capture/leapboundary/analysis/T207/json-load-census-output.txt` and
`census-at-rev-output.txt`. Summary in the handoff. Headline: **T185's table reproduces exactly**
under an independently written AST counter (P-33), and the live figure has since moved
**211 → 224** (P-69).

## 8. F-3 — the drop counter

Added to the scratch measurer, driven **red** (6 dropped on a planted root) and **green**
(0 dropped over 1,554 leaves on the real corpus), with the population stated in the
`NIL-COVERAGE — … inspected an empty population` shape. See the handoff.

---

## 9. What this ruling does NOT decide

1. **It does not wire `v3` into `conformance.sh`.** That file is held by another worker this fire and
   is out of T207's scope. T185's F-4 ("the successors are wired to nothing") therefore **still
   stands**, now for `v3` as well as `_v2`. Named as a tail, not silently left.
2. **It does not touch A1 or `check_wire_float_roundtrip.py`.** A1 remains the request-body guard,
   unchanged; `v3` explicitly declines to duplicate it and says so on every run.
3. **It does not rule on Zones B or C.** T186's rulings there are unchanged and were not re-litigated.
4. **It establishes nothing about parity, cutover, or any Go code.** A green `v3` run means exactly:
   *none of the literals it actually inspected changes value under a binary-double round trip.*
