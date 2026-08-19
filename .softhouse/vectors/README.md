# The golden-vector store — schema and promotion contract

This directory is the parity corpus for the Fineract → Go migration. A vector here
says: **the reference oracle, at the pinned commit and at the production
MathContext, returned exactly this for exactly this request.** Nothing else may
live here.

> **"The oracle" means the Fineract reference implementation** we grade Go output
> against (test-oracle sense). Oracle Database is a prohibited product in this
> program. PostgreSQL is the only permitted database.

The harness that reads this directory is `.softhouse/conformance.sh` and
`nexus/internal/apps/loanschedule/conformance/`. **This format is a contract with
the promotion task**: a later task fills it mechanically from
`.softhouse/capture/`, so every rule below is enforced in code, not by convention.

---

## Layout

```
.softhouse/vectors/
├── README.md                      this file
├── PIN.json                       store-level comparability pin (one edit, not N)
├── capabilities.json              which seam sees which capability class
├── _selftest/                     HAND-AUTHORED harness self-test. NEVER parity.
│   └── SELFTEST-01-*.json
└── <context>/                     one directory per bounded context
    └── <case>.json                one vector per file
```

`<context>` today is `loanschedule`. `conformance.sh <context>` filters to one.

---

## The three classes, and why the distinction is structural rather than labelled

| class | expected value comes from | counts toward parity? |
|---|---|---|
| `parity` | **OBSERVED** from the reference oracle, transcribed from a committed capture | **yes — and only this class does** |
| `contract-refusal` | **DERIVED** from the ratified contract's own normative doc comments | no, tallied separately |
| `selftest` | **HAND-AUTHORED** by a harness author | no, and the report says so on every run |

A label is not a safeguard. Each class is locked by properties the harness checks
mechanically, so a file cannot become something it is not by being renamed:

* **`parity` requires the production MathContext, read off the file itself.**
  `oracle.threaded_mathcontext` **and** `oracle.ambient_mathcontext` must both be
  `(19, HALF_UP)`, and `request.rounding` must agree with the threaded one.
  Passes 1 and 2 of the capture corpus ran at precision **12 or 8**; production
  runs at 19. Those captures are **discrimination probes** — they document how the
  arithmetic responds to precision — and *the numbers in them were produced at a
  precision the harness reads*, so relabelling one as `parity` fails on the
  numbers, not on the label. `PIN.json` also carries a `never_promotable`
  denylist of the known probe and calibration case ids as a second line.
* **`parity` requires a capture that exists.** `provenance.capture_ref` must
  resolve to a real file in this repository, and `provenance.capture_case_id`
  must name the case **inside** it — Path A captures are bundles of up to 2,016
  cases in one file, so a path alone is not provenance. An optional
  `capture_sha256` is verified when present.
* **`contract-refusal` may not contain money at all.** `expect.periods` must be
  empty and `oracle.seam` must be `none`. It cannot smuggle an unobserved amount
  into the store because it has nowhere to put one.
* **`selftest` and `_selftest/` are locked to each other in both directions.** A
  `selftest` file outside `_selftest/` is inadmissible, and a file inside
  `_selftest/` may carry no other class. It must also carry
  `provenance.note` exactly `"hand-authored, NOT observed from the oracle"`.

**Everything in this store is unpromoted today.** The store holds one self-test
fixture and four contract-refusal vectors. `conformance.sh` therefore exits **2**
with `NO PARITY VECTOR WAS GRADED`, which is the correct and intended state until
the promotion task runs.

---

## Money, and why every monetary field is a string

**Every monetary field is a base-10 integer STRING counting minor units.**
`"amount_minor": "100000"` is MNT 1,000.00 (MNT = ISO 4217 numeric 496, minor
unit 2).

Not a JSON number, and the reason is not fastidiousness. Most JSON readers — `jq`
among them — decode every number into an IEEE-754 double, so a perfectly integral
JSON number can be corrupted by the *reader* rather than by the file. A string
removes the question, and it lets the harness enforce one rule with no exceptions:

> **No JSON number anywhere in a vector file may contain `.`, `e` or `E`.**

Enforced twice: by `RejectFloatTokens` before any typed decoding (so a float in a
field the typed shape would drop is still caught), and by a `perl`+`grep` HARD
guard in `conformance.sh`. Non-monetary counts — `number_of_repayments`,
`repayment_every`, a date's `year`/`month`/`day`, a `Rate`'s `numerator` and
`denominator` — stay JSON integers. They are dimensionless, small, and not money.

### Rates are exact rationals, never decimals

`{"numerator": 27, "denominator": 125}` is 21.6% p.a. Canonical form is mandatory:
`denominator > 0`, `numerator >= 0`, lowest terms. A zero rate is exactly
`{"numerator": 0, "denominator": 1}`.

### Decimal strings: where they are allowed, and how they are compared

The frozen contract's response carries **only integers and civil dates** — no
decimal anywhere — so the graded expectation needs no decimal field at all, and
**a decimal string may not appear inside a graded cell.**

Three optional `*_major_text` fields per period carry the oracle's **own emitted
characters** in major units, verbatim. The harness re-derives the minor-unit
integer from them by exact integer/string arithmetic and marks the vector
**INADMISSIBLE** if the two disagree. They are a cross-check on the
**transcription**, never a grading standard, and **no tolerance is ever applied to
them** — finding T17-F6 is why: a truncated 12-decimal-place transcription hides a
divergence in digits 13 and beyond, so comparing decimals would create exactly the
blind spot this store exists to close.

Observed scale is **not uniform** in the corpus and must not be normalised: Path A
emits `"totalOutstandingAmount": "0"` (scale 0) beside scale-2 siblings, Path B
emits `"feeChargesDue": "15000"` on a disbursement row and `"0.00"` on repayment
rows, and persisted product rows are scale 6 (`"1200000.000000"`). The converter
pads short fractions and accepts trailing zeros beyond the currency scale, and
**rejects a significant digit beyond it** rather than rounding a transcription.

---

## Capability classes — the load-bearing idea

`capabilities_required` names the capability classes a case's inputs exercise.
`capabilities.json` says, **per seam**, which classes that seam structurally
exercises and which it silently ignores. The harness refuses any vector whose
required class is not `exercised` by its seam.

**Why it is modelled this way rather than as "does this case involve charges?".**
The Path A embeddable seam's entry point delegates with
`generate(mc, loanApplicationTerms, null, null)` at
`ProgressiveLoanScheduleGenerator.java:83`. **Two** hard-wired nulls, each a blind
spot found separately:

1. `loanCharges = null` (T50-N2) → **no Path A capture can ever exercise a
   charge.** Charge conformance can only ever be graded on the server path.
2. `holidayDetailDTO = null` (D-2) → holiday and non-working-day adjustment is a
   **guaranteed silent no-op on Path A**. `DefaultScheduledDateGenerator`'s
   `adjustRepaymentDate` has its **entire body** inside
   `if (holidayDetailDTO != null)` at `:224`. That null-guard is exactly why Path A
   captures run instead of throwing NPE: the seam's usability and its blindness
   have the same cause.

And separately, that seam drops `installmentAmountInMultiplesOf` (no Builder
setter) and never copies `daysInYearCustomStrategy` out of its Builder, while
Path B honours both. **"The seam drops an input" is a recurring pattern, not a
one-off, and the two nulls above are the ones somebody checked — not an
exhaustive audit.**

So the registry lives in **`capabilities.json`, as data**. Recording a third blind
spot is one row there: every affected vector starts being refused immediately,
**with no vector file changing, no schema migration and no code change.**

Four statuses, because "not exercised" has materially different causes:

| status | meaning | gradeable |
|---|---|---|
| `exercised` | the input reaches the calculation | **yes** |
| `blind` | structurally invisible; honouring it and ignoring it score identically | no |
| `aliased` | a value from **another configuration scope** is delivered into the slot | no |
| `partial` | reached, but on a narrower subset than a reader would assume | no |
| *(absent)* | nobody audited it | no — **default-deny** |

`in_graded_domain` is a **separate** flag per capability, because the two questions
are independent: a seam can exercise a capability that no promoted vector grades
(ACT/ACT on Path A today), and a capability can sit in the contract domain while no
seam can see it at all.

### Refusal is a first-class outcome, and refusals retire differently

| reason | what retires it |
|---|---|
| `SEAM_BLIND` | **re-capture on another seam.** Promoting anything from this seam cannot help. |
| `UNGRADED_CAPABILITY` | **promote a discriminating vector**, then flip `in_graded_domain`. |
| `UNGRADED_REQUEST` | **widen the graded domain** — behaviour, not shape, so no amendment. |
| `UNKNOWN_CAPABILITY` / `UNKNOWN_SEAM` | **declare it** in `capabilities.json`. |

Two live examples the store already encodes:

* **`DayCountActualActual` is refused, correctly.** The arm is re-derived (T30) and
  captured (58 captures in `.softhouse/capture/actualactual/`), but nothing is
  promoted. T48's **finding N4** is why promotion is not a formality: where both
  calendar years have the **same length** the per-year fractions sum to the plain
  fraction **exactly**, so a cross-year shape inside a run of non-leap years grades
  a port identically whether it implements the arm or not. **Any vector promoted
  for this arm must cross a leap-year boundary with a non-zero first segment.**
* **Holiday adjustment is refused even on Path B.** Finding **D-2a**
  `[UNVERIFIED: no Path B capture exists]`: this generator adjusts only the
  **final** period, because the `:66` call sits inside
  `if (repaymentPeriodNumber == numberOfRepayments)` at
  `DefaultScheduledDateGenerator.java:61`. "Adjust every date that lands on a
  holiday" is the obvious and **wrong** thing for a port to write, and it would
  pass the entire existing corpus silently. Path B's status is therefore `partial`.

---

## Comparability: the pin, and the frozen contract's digest

`PIN.json` carries `fineract_commit`, `dec1_revision`, the production rounding
policy, and `contract_sha256` — the digest of the ratified `contract.go`.

The contract's package comment says its doc comments **are** the specification and
that "a shape change invalidates the conformance corpus". The digest is the
mechanical form of that sentence: if those bytes change at all, every vector stops
being *known* to be expressed in the ratified shape, and the harness says so
instead of grading on. Re-stamping it is a deliberate act that belongs with the
gate that authorised the amendment.

**The harness never runs `gofmt -w` over `contract.go`, and its gofmt guard
explicitly exempts that one file.** `gofmt -l` reports it; that is expected and
recorded as gate **G-3**. The diff is doc-comment list normalisation, semantically
inert, and deliberately not applied — reformatting the doc comments of a ratified
artefact is rewriting the specification.

---

## Field reference

```jsonc
{
  "schema": "gerege.loanschedule.vector/v1",
  "case_id": "...",                  // stable, unique within the context
  "context": "loanschedule",         // must equal the directory name
  "class": "parity",                 // parity | contract-refusal | selftest
  "title": "...",                    // what this vector discriminates, in prose
  "dec1_revision": 12,               // must equal PIN.json

  "capabilities_required": ["schedule.core"],

  "provenance": {
    "kind": "oracle-capture",        // oracle-capture | contract | hand-authored
    "note": "...",
    "capture_ref": ".softhouse/capture/out/capture-prod3b-raw.json",
    "capture_sha256": "",            // optional; verified when present
    "capture_case_id": "P-01",       // the id INSIDE the capture bundle
    "citation": ""                   // required for contract-refusal
  },

  "oracle": {
    "fineract_commit": "426a2354...",
    "seam": "path_a_embeddable",     // must exist in capabilities.json
    "captured_at": "...",
    "threaded_mathcontext": { "precision": 19, "rounding_mode": "HALF_UP" },
    "ambient_mathcontext":  { "precision": 19, "rounding_mode": "HALF_UP" }
  },

  "request": {                       // the frozen DEC-1 GenerateRequest, snake_case
    "time_zone": "Asia/Ulaanbaatar", // IANA name; a fixed offset is invalid
    "currency": { "code": "MNT", "minor_unit_digits": 2 },
    "rounding": { "significant_digits": 19, "rate_factor_scale": 19, "mode": "HALF_UP" },
    "schedule_start_date": { "year": 2026, "month": 1, "day": 1 },
    "disbursements": [ { "date": {...}, "amount_minor": "120000000" } ],
    "number_of_repayments": 12,
    "repayment_every": 1,
    "repayment_frequency_unit": "MONTHS",          // DAYS|WEEKS|MONTHS|YEARS
    "annual_nominal_interest_rate": { "numerator": 27, "denominator": 125 },
    "interest_method": "DECLINING_BALANCE",
    "day_count": "FIXED_30_360",                   // FIXED_30_360|ACTUAL_ACTUAL
    "down_payment_percentage": { "numerator": 0, "denominator": 1 },
    "installment_rounding_multiple_minor": "0"
  },

  "expect": {
    "kind": "schedule",              // schedule | refusal
    "sentinel": "",                  // required when kind is refusal
    "last_repayment_due_date": {...},// optional; see below
    "observed_total_interest_minor": null,
    "periods": [
      {
        "kind": "REPAYMENT",         // DISBURSEMENT|DOWN_PAYMENT|REPAYMENT
        "installment_number": 1,     // 0 on a DISBURSEMENT row
        "from_date": {...},
        "due_date": {...},
        "principal_minor": "9048237",
        "interest_minor": "2160000",
        "outstanding_principal_minor": "110951763",
        "principal_major_text": "90482.37",         // optional cross-check
        "interest_major_text": "21600.00",
        "outstanding_principal_major_text": "1109517.63",
        "unrecorded_fields": [],                     // see below
        "observed_total_due_minor": "11208237"       // optional
      }
    ]
  },

  "invariant_exemptions": [ { "invariant": "...", "reason": "..." } ]
}
```

Enums are **names, never ordinals**: an ordinal silently re-points if a member is
inserted, and a name either resolves or errors. No Fineract type, class or enum
name appears in a vector file — the contract forbids one crossing the boundary,
and a vector is on the contract's side of it.

### `unrecorded_fields` — the field that prevents fabrication

Names the graded fields of **that row** the capture did **not** record. The harness
does not compare them, counts them as **ungraded cells**, and prints the count.

It exists because the corpus demands it. Path A **pass 3** records only
`{type, dueDate, principal}` on a DISBURSEMENT row — **not** that row's balance —
while **pass 3b** records it (12 of 12). Filling
`outstanding_principal_minor` on a pass-3 disbursement row from the contract's rule
"it equals the principal advanced" would be **deriving** a value and storing it as
an **observation**, which is the exact defect the honesty rule exists to prevent:
the port would then be graded against the harness's own assumption. A cell nobody
observed grades nothing, and the report says how many such cells were skipped, so
coverage is a number rather than an impression.

### `last_repayment_due_date`

The graded domain's window predicate is
`ScheduleStartDate <= Disbursements[0].Date < the last repayment DueDate`. The
harness reads that last due date from the expected schedule, or from this field on
a refusal vector that has no schedule. **The harness never computes it** — that
would mean implementing the month-end stepping rule, which belongs to the port
(T10). *The harness contains no schedule generation and no date stepping of any
kind*, only comparison, so the port cannot borrow an implementation from the thing
that grades it.

---

## The property invariants

Checked against **what the implementation returned**, not against the vector, so
they catch defects on shapes no vector covers. Each is derived from the ratified
contract's own normative text; none asserts more.

| invariant | statement |
|---|---|
| `principal_portions_sum_to_disbursed` | Σ principal on DOWN_PAYMENT+REPAYMENT rows == Σ principal on DISBURSEMENT rows, exactly. Two sums compared, not one column summed: direction is the row's `Kind`, never a sign bit. |
| `principal_amortizes_to_zero` | the final row's outstanding principal is exactly 0. |
| `balance_roll_forward` | a DISBURSEMENT row's outstanding **is** the amount advanced; a REPAYMENT row emitted **before** the disbursement is all zero; otherwise outstanding == `max(0, carried in − principal)` with the oracle's own clamp. DOWN_PAYMENT rows are accepted **without** assertion — their rule is specified from source but UNGRADED. |
| `splits_sum_to_whole` | principal + interest == the oracle's **own observed total** for the row, where a capture recorded one; **N/A** otherwise, because `p + i == p + i` is not a test. |
| `monotonic_due_dates` | repayment windows are non-empty, strictly increasing and **contiguous** (`FromDate[i] == DueDate[i−1]`), so no day accrues twice or not at all. |
| `contract_row_ordering` | the contract's normative **window-key** order. The naive "sort by date, disbursement first" rule is refuted at a reachable boundary: a disbursement dated exactly on period *k*'s due date belongs to period *k+1* and is emitted **after** repayment *k*. |

`invariant_exemptions` switches one off for one vector, with a reason that is
printed on every run. An invariant that cannot be switched off gets deleted the
first time a legitimate shape trips it, and a deleted invariant protects nothing.

---

## Promotion notes for whoever fills this store

Read `.softhouse/capture/` — never edit it. It is the audited output of other
tasks.

* **Path A** captures are **bundles**: one `.json` with `captures[]` or `cases[]`,
  each element carrying its own `id`, `inputs` and `observed`. Money is **already
  quoted strings**. Key names differ between passes: pass 3b uses
  `periodFromDate`/`feeAmount`/`penaltyAmount` where T37 uses
  `fromDate`/`fee`/`penalty`. Map to this schema's names; do not invent new ones.
* **Path B** captures are one request file per case in `req/` and the **raw
  response bytes** in `out/<id>-raw.json`, whose numbers are **bare floats on the
  wire** (9,122 of them across the corpus). **Read the `-exact.json` sidecar**, or
  parse with `parse_float=str, parse_int=str`. Never a default JSON decoder.
* **Precision-12/8 captures may never be promoted as parity vectors.** Pass 1
  (`C-00`, `D-01`, `D-01-p8`, `D-01-mnt`, `D-02`, `D-02b`, `D-03`, `D-04`), all 13
  of pass 2, `P-CAL`, and the `*-CAL` calibration cells. `D-01-p19` is the one
  pass-1 record at the production precision. The list is in `PIN.json`; the
  MathContext check catches them even if the list is incomplete.
* **Pass 3's 11 production-setting candidates** are enumerated in the corpus itself
  at `out/capture-prod3b-attestation.json` → `productionSettingsCaptureIds`:
  `P-00`, `P-01`, `P-02`, `P-02b`, `P-03`, `P-04f`, `P-04t`, `P-MNT-5M`,
  `P-MNT-1M2`, `P-MNT-50M`, `P-MNT-4M999`. `calibrationCaptureIds` is `["P-CAL"]`.
* Transcribe; never compute, extrapolate or interpolate. A plausible invented
  number looks exactly like a real one and silently poisons every parity claim
  above it. Where the capture recorded no cell, say so in `unrecorded_fields`.

---

## Running it

```sh
.softhouse/conformance.sh                 # grade everything
.softhouse/conformance.sh loanschedule    # one context
.softhouse/conformance.sh --self-test     # grade the HARNESS (never a conformance PASS)
.softhouse/conformance.sh --prove         # the harness's own red/green mutation proofs
```

Exit **0** requires: every graded vector passed, **at least one parity vector was
graded**, and the reference oracle was confirmed reachable. Exit **1** is a
mismatch or a violated invariant. Exit **2** is "unusable, so no verdict is
available" — no implementation, unreachable oracle, zero parity vectors, an
inadmissible or refused vector.

A PASS means **"matches the reference oracle on captured vectors, within the graded
domain"**. It never means safe to cut over. Cutover is a `user` gate.
