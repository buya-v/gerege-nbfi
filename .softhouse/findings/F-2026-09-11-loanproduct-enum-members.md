# F-2026-09-11 — loanproduct enum members: observed vs graded

Status: RESOLVED (vectors promoted; drives measured; no new drive warranted)
Context: `loanproduct` (one bounded context)
Method: `.softhouse/briefs/OH-LPENUM-AO.md`; parent finding
`F-2026-09-11-loanproduct-graded-coverage.md` §3/§6.

## 1. The blind spot and the method

The loanproduct seam decodes six stored-value vocabularies (`frequency.go`,
`method.go`). Every member of a vocabulary runs the *same* port statements, so a
statement/line/branch coverage instrument cannot tell which MEMBERS are graded.
The 15 committed vectors only request stored values `2/3/4` of
`period-frequency`; the capture each of them cites observes `0` and `1` as well.
Those two members were implemented, observed, and **ungraded**.

The method, applied to each of the six vocabularies:

1. list the option ids the committed capture OBSERVES (the `*Options` lists in
   `loanproducts-template-raw.json`, found via the existing vectors' `capture_ref`);
2. list the stored values the committed vectors GRADE;
3. diff — every observed-but-ungraded member is a vector to promote.

This is a MEMBER census, not a line/branch census. A port-table entry is not an
observation: only a `*Options` id observed in the capture counts.

Observation source (all 15 vectors cite it):
`.softhouse/capture/loanproduct/out/loanproducts-template-raw.json`
sha256 `6168b177ec87a259015aa5a2cd8eb93a838de571765a0a3d16a66a6683c523fe`
(re-verified after writing the new vectors, below).

## 2. The full table (vocabulary × observed ids × graded ids × gap)

Observed ids are the option-list ids in the capture. Graded ids are the stored
values the 15 committed vectors request. Gap = observed − graded.

| vocabulary | capture option list(s) | observed ids | graded stored | gap |
|---|---|---|---|---|
| `amortization-method` | `amortizationTypeOptions` | 0, 1 | 0, 1 | — |
| `interest-method` | `interestTypeOptions` | 0, 1 | 0, 1 | — |
| `interest-calc-period` | `interestCalculationPeriodTypeOptions` | 0, 1 | 0, 1 | — |
| `period-frequency` | `repaymentFrequencyTypeOptions`, `interestRateFrequencyTypeOptions` | 0, 1, 2, 3, 4 | 2, 3, 4 | **0 (DAYS), 1 (WEEKS)** |
| `days-in-month` | `daysInMonthTypeOptions` | 1, 30 | 1, 30 | — |
| `days-in-year` | `daysInYearTypeOptions` | 1, 360, 364, 365 | 1, 360, 364, 365 | — |

Per-member detail for the one gap:

| vocabulary | capture key | id | wire code | expected enum code | name | status |
|---|---|---|---|---|---|---|
| `period-frequency` | `repaymentFrequencyTypeOptions` | 0 | `repaymentFrequency.periodFrequencyType.days` | `periodFrequencyType.days` | `DAYS` | **ungraded → promoted** |
| `period-frequency` | `repaymentFrequencyTypeOptions` | 1 | `repaymentFrequency.periodFrequencyType.weeks` | `periodFrequencyType.weeks` | `WEEKS` | **ungraded → promoted** |
| `period-frequency` | `repaymentFrequencyTypeOptions` | 2 | `repaymentFrequency.periodFrequencyType.months` | `periodFrequencyType.months` | `MONTHS` | graded |
| `period-frequency` | `interestRateFrequencyTypeOptions` | 2 | `interestRateFrequency.periodFrequencyType.months` | `periodFrequencyType.months` | `MONTHS` | graded |
| `period-frequency` | `interestRateFrequencyTypeOptions` | 3 | `interestRateFrequency.periodFrequencyType.years` | `periodFrequencyType.years` | `YEARS` | graded |
| `period-frequency` | `interestRateFrequencyTypeOptions` | 4 | `interestRateFrequency.periodFrequencyType.whole_term` | `periodFrequencyType.whole_term` | `WHOLE_TERM` | graded |

Note the port grades the enum's OWN `getCode()` (`periodFrequencyType.*`,
`frequency.go`), while the DTO on the wire qualifies it with the field prefix
(`repaymentFrequency.` / `interestRateFrequency.`). The `capture_case_id` is the
enum code as it appears in the JSON, so both new vectors satisfy the
containment admission (the string literally occurs in the capture file).

## 3. Promotions

Two vectors, each a near-copy of `LP-freq-months.json`, citing the SAME capture:

| vector | vocabulary | request.stored | expect.stored | expect.code | expect.name |
|---|---|---|---|---|---|
| `.softhouse/vectors/loanproduct/LP-freq-days.json` | `period-frequency` | 0 | 0 | `periodFrequencyType.days` | `DAYS` |
| `.softhouse/vectors/loanproduct/LP-freq-weeks.json` | `period-frequency` | 1 | 1 | `periodFrequencyType.weeks` | `WEEKS` |

Hash re-verification: `sha256sum` of the capture equals the
`provenance.capture_sha256` in both new vectors (and every old vector). No value
was synthesised: both expect cells are the enum's declared `getCode()`/name for
the observed option ids.

The store now admits 17 vectors (was 15), all PASS against `loanproduct-go`;

    VERDICT: PASS (exit 0)
    vectors_loaded=17 parity_pass=17 parity_fail=0 refused=0 inadmissible=0 harness_error=0
    graded_cells=51 invariant_violations=0

and the committed-store control still passes
(`TestCommittedCorpusPassesTheReferenceImplementation`).

## 4. Drives — every count WITHOUT and WITH the new vectors

Measured with the mandated binary, one impl at a time, on this worktree. WITHOUT
= the two new vectors temporarily removed (15-vector corpus); WITH = 17-vector
corpus.

| drive (file:line) | WITHOUT | WITH | delta | newly enabled? |
|---|---|---|---|---|
| `loanproduct-wrong-swap-days360-365` (`impl.go:201`) | 2 | 2 | 0 | no |
| `loanproduct-wrong-iota-ordinals` (`impl.go:204`) | 7 | 9 | **+2** | no — already dies on the old corpus |
| `loanproduct-wrong-dim-sibling-name` (`impl.go:214`) | 1 | 1 | 0 | no |
| `loanproduct-wrong-freq-field-qualified-code` (`impl.go:220`) | 3 | 5 | **+2** | no — already dies on the old corpus |

`redcount` (drives that kill) = 4 both WITHOUT and WITH. Every registered drive
kills ≥1 on both corpora; **no drive is inert**, so the rule on inert drives
requires no promotion or deletion.

### The ordinal-shift candidate, and why no new drive is registered

The obvious drive for a vocabulary is an ordinal shift — decodes stored `n` as
`n+1`, i.e. the defect `parties-wrong-iota-ordinals` names. For `loanproduct`
that drive already exists: `loanproduct-wrong-iota-ordinals` re-encodes the
decoded member as its contiguous Go iota ordinal (`PeriodFrequencyType` declares
`INVALID` first, so `DAYS..WHOLE_TERM` sit one past their stored `0..4`). It
already dies on the old corpus (7) because `MONTHS/YEARS/WHOLE_TERM` were
graded; the new vectors add their two kills (9), they do not enable it. The same
holds for `loanproduct-wrong-freq-field-qualified-code` (3 → 5). Per the brief:
the existing drives already die on the new vectors — report it, do **not**
duplicate them.

A defect that could be killed ONLY by the two new members would have to be
confined to `{DAYS, WEEKS}` and be correct on every old graded member — in
practice an adjacent transposition of stored `0`/`1`. That is a real defect class
(this codebase hosts adjacent-transposition drives: `swap-days360-365`,
`parties-wrong-transfer-states-swapped`), and it would measure
WITHOUT = 0 / WITH = 2. It is **not** registered here: the new vectors are
promoted for MEMBER coverage (the blind spot the method exists to close), the
ordinal-shift candidate the brief names is already covered, and the brief's
instruction is not to duplicate existing drives. Registering a bespoke
transposition solely to give the new vectors a private red-drive would be
manufacturing coverage, not measuring it.

## 5. Non-negotiables

- `.softhouse/guards/` untouched; `.softhouse/conformance.sh` untouched.
- Progressive-recomputation kernel (`calculator.go`, `repaymentperiod.go`,
  `schedulemodel.go`, …) untouched.
- PostgreSQL only; no Oracle Database. No capture taken; no POST/PUT/DELETE.
- `capture_ref` is a JSON capture record; `capture_sha256`/`citation` present;
  hash re-verified after writing.
- One bounded context: `loanproduct`.

## 6. Controls (regression sentinels from the map)

`loanschedule-wrong-days-in-year-365 = 45`, `loanschedule-wrong-half-even = 5`,
`parties-wrong-iota-ordinals = 12`, `charges-wrong-rounding-half-even = 1`. These
are other contexts and were not modified by this change.
