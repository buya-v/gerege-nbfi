# F-2026-09-11 — Tier D pilot (`OH-TIERDPILOT-BK`): the loan tenant pin refuses the replayed read-backs; nothing promoted

**Status: PILOT RESULT — REFUSED AT ADMISSION.**
Three candidate vectors were transcribed from the Tier-D replay read-back of UC6 loan 1
(`LoanUpdateApprovedAmount.feature`) and offered to three **existing** `loan` seams. All three are
**refused by the `tenant_params` equality rule**, because the replay tenant `tierd` is **EUR** and the
pinned loan tenant is **MNT**. The rule was **not relaxed**, and **no `loan` seam admits the case**
(§4). **Zero vectors promoted; `.softhouse/vectors/loan/` is unchanged at 31 vectors.** The brief
states this is a valid pilot result.

**Task:** `OH-TIERDPILOT-BK`, bounded context **`loan`**, branch `feat/OHTIERDPILOTbk`.
**Driver provenance decision applied:** the 2026-09-11 decision (throwaway tenant `tierd`, same image
`sha256:e596339626bf…`, `Asia/Ulaanbaatar`, rounding mode 4/HALF_UP, instance destroyed), on the T305
precedent. Every candidate's `provenance` names tenant `tierd`, the image, the replayed scenario, and
says it is **NOT** tenant `gerege`.

## 1. What was transcribed (the pilot promotion attempt)

Three candidates, each onto an existing `loan` seam the THIRD-PASS Q4 table marks "maps directly":

| candidate | existing seam | graded cells (integer minor units) | transform applied | observation |
|---|---|---|---|---|
| `LN-TD-L10-loan-1-pending-amortizes-to-zero` | `loan-schedule-amortization` | `principal_disbursed_minor` `100000`; `principal_components_minor` `[16426,16521,16618,16715,16812,16908]`; `principal_sum_minor` `100000`; `final_principal_balance_minor` `0` | major→minor ×100, per component | UC6 loan 1, `associations=all`, line 22145 |
| `LN-TD-L06-loan-1-schedule-interest-period-1` | `loan-schedule-interest` | `principal_minor` `100000`; `rate_per_annum_pct` `7`; `days_in_year` `360`; `days_in_month` `30`; `interest_minor` `583` | major→minor ×100; enums from observed `daysInYearType.id`/`daysInMonthType.id` | same read-back, `periods[1].interestOriginalDue 5.83` |
| `LN-TD-L06-loan-1-disbursement-net` | `loan-disbursement` | `approved_principal_minor` `100000`; `charges_due_at_disbursement_minor` `0`; `net_disbursal_minor` `100000` | major→minor ×100 | `approvedPrincipal 1000.00`, `feeChargesAtDisbursementCharged 0.0`, `netDisbursalAmount 1000.00` |

**Only observed values were transcribed; nothing was computed.** Every cited cell was re-read from
`.softhouse/capture/tierd-feasibility/uc6/loan-1-detail-associations-all.json` with `jq` after the
vectors were written. The capture's sha256 is
`b38d5d38d621745b7dadd8c6c9e3b981600cc5225197c3fe902a378a2217460a`, matching `OWNER.md` line 35. The
`LN-L10` invariant holds exactly on the transcribed components: they sum to `100000`, and the final
principal balance is `0`.

Per the driver decision, the `tenant_params` and `provenance.capture_ref` / `capture_sha256` /
`capture_case_id` blocks were **set from the capture**, not inherited from the `gerege`/MNT vectors.
The observed currency is EUR, so `tenant_params.currency` was written **`EUR`**. That is the field that
refuses the vector.

### The three candidate vectors as offered

`LN-TD-L10-loan-1-pending-amortizes-to-zero`:

```json
{
 "schema": "gerege.loan.vector/v1",
 "case_id": "LN-TD-L10-loan-1-pending-amortizes-to-zero",
 "class": "parity",
 "context": "loan",
 "oracle": { "seam": "loan-schedule-amortization", "fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb" },
 "provenance": {
  "kind": "oracle-capture",
  "capture_ref": ".softhouse/capture/tierd-feasibility/uc6/loan-1-detail-associations-all.json",
  "capture_sha256": "b38d5d38d621745b7dadd8c6c9e3b981600cc5225197c3fe902a378a2217460a",
  "capture_case_id": "dac98689-65f0-43e6-9ad2-707f149c1af4",
  "note": "TENANT `tierd` -- NOT tenant `gerege`. IMAGE sha256:e596339626bf... SCENARIO LoanUpdateApprovedAmount.feature, 'Verify update approved amount for progressive loan - UC1' (C3858). Asia/Ulaanbaatar, rounding mode 4 (HALF_UP); instance destroyed."
 },
 "tenant_params": { "rounding_mode": "HALF_UP", "rounding_ordinal": 4, "precision": 19, "currency": "EUR", "minor_units": 2, "timezone": "Asia/Ulaanbaatar" },
 "request": { "schedule_amortization": { "principal_disbursed_minor": "100000", "principal_components_minor": ["16426","16521","16618","16715","16812","16908"] } },
 "expect": { "principal_sum_minor": "100000", "final_principal_balance_minor": "0" },
 "capabilities_required": ["schedule-principal-amortization"],
 "graded_against": ["loan-go"]
}
```

`LN-TD-L06-loan-1-schedule-interest-period-1`:

```json
{
 "schema": "gerege.loan.vector/v1",
 "case_id": "LN-TD-L06-loan-1-schedule-interest-period-1",
 "class": "parity",
 "context": "loan",
 "oracle": { "seam": "loan-schedule-interest", "fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb" },
 "provenance": {
  "kind": "oracle-capture",
  "capture_ref": ".softhouse/capture/tierd-feasibility/uc6/loan-1-detail-associations-all.json",
  "capture_sha256": "b38d5d38d621745b7dadd8c6c9e3b981600cc5225197c3fe902a378a2217460a",
  "capture_case_id": "dac98689-65f0-43e6-9ad2-707f149c1af4",
  "note": "TENANT `tierd` -- NOT tenant `gerege`. IMAGE sha256:e596339626bf... SCENARIO LoanUpdateApprovedAmount.feature, 'Verify update approved amount for progressive loan - UC1' (C3858). Asia/Ulaanbaatar, rounding mode 4 (HALF_UP); instance destroyed."
 },
 "tenant_params": { "rounding_mode": "HALF_UP", "rounding_ordinal": 4, "precision": 19, "currency": "EUR", "minor_units": 2, "timezone": "Asia/Ulaanbaatar" },
 "request": { "schedule": { "principal_minor": "100000", "rate_per_annum_pct": 7, "days_in_year": 360, "days_in_month": 30 } },
 "expect": { "interest_minor": "583" },
 "capabilities_required": ["schedule-interest-rounding"],
 "graded_against": ["loan-go"]
}
```

`LN-TD-L06-loan-1-disbursement-net`:

```json
{
 "schema": "gerege.loan.vector/v1",
 "case_id": "LN-TD-L06-loan-1-disbursement-net",
 "class": "parity",
 "context": "loan",
 "oracle": { "seam": "loan-disbursement", "fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb" },
 "provenance": {
  "kind": "oracle-capture",
  "capture_ref": ".softhouse/capture/tierd-feasibility/uc6/loan-1-detail-associations-all.json",
  "capture_sha256": "b38d5d38d621745b7dadd8c6c9e3b981600cc5225197c3fe902a378a2217460a",
  "capture_case_id": "dac98689-65f0-43e6-9ad2-707f149c1af4",
  "note": "TENANT `tierd` -- NOT tenant `gerege`. IMAGE sha256:e596339626bf... SCENARIO LoanUpdateApprovedAmount.feature, 'Verify update approved amount for progressive loan - UC1' (C3858). Asia/Ulaanbaatar, rounding mode 4 (HALF_UP); instance destroyed."
 },
 "tenant_params": { "rounding_mode": "HALF_UP", "rounding_ordinal": 4, "precision": 19, "currency": "EUR", "minor_units": 2, "timezone": "Asia/Ulaanbaatar" },
 "request": { "disburse": { "approved_principal_minor": "100000", "charges_due_at_disbursement_minor": "0" } },
 "expect": { "net_disbursal_minor": "100000" },
 "capabilities_required": ["disbursement-net"],
 "graded_against": ["loan-go"]
}
```

(The three files additionally carry a `title` and an explanatory `_note`; those fields are not graded
and are elided here. No copy of the candidates is committed, because committing them under
`.softhouse/` would place an inadmissible vector in a censused tree.)

## 2. The refusal — the exact rule, and the exact message

`nexus/internal/apps/loan/conformance/admit.go:115-124`:

```go
// Tenant context: the loan rows are read under the tenant's monetary
// context, so a capture taken under a different tenant is not a parity
// observation.
if v.TenantParams == nil {
    problems = append(problems, "tenant_params is missing: ...")
} else if opts.Pin != nil && *v.TenantParams != opts.Pin.TenantParams {
    problems = append(problems, fmt.Sprintf(
        "tenant_params %+v does not match the pinned tenant %+v", *v.TenantParams, opts.Pin.TenantParams))
} else if err := validateTenantParams(v.TenantParams); err != nil {
    ...
}
```

The pinned tenant is `.softhouse/PIN-loan.json`:

```json
"tenant_params": { "rounding_mode": "HALF_UP", "rounding_ordinal": 4, "precision": 19,
                   "currency": "MNT", "minor_units": 2, "timezone": "Asia/Ulaanbaatar" }
```

The harness reports, verbatim (`go test -run Committed ./internal/apps/loan/conformance/`):

```
LN-TD-L06-loan-1-disbursement-net is INADMISSIBLE: tenant_params {rounding_mode HALF_UP,
  rounding_ordinal 4, precision 19, currency EUR, minor_units 2, timezone Asia/Ulaanbaatar}
  does not match the pinned tenant {rounding_mode HALF_UP, rounding_ordinal 4, precision 19,
  currency MNT, minor_units 2, timezone Asia/Ulaanbaatar}
LN-TD-L06-loan-1-schedule-interest-period-1 is INADMISSIBLE: (same, currency EUR)
LN-TD-L10-loan-1-pending-amortizes-to-zero      is INADMISSIBLE: (same, currency EUR)
→ parity_fail=0 refused=0 inadmissible=3 errored=0
```

**The only divergent field is `currency`.** Rounding mode, ordinal, precision, minor units and
timezone all match the pin, because the replay instance was seeded at `Asia/Ulaanbaatar` with rounding
mode 4 (HALF_UP) — exactly what the driver decision certified. But the money in this capture is EUR,
and the pin pins MNT. The rule is a strict equality over the whole `tenant_params` struct, so an
otherwise byte-perfect observation is refused.

**The rule was not relaxed and the pin was not edited.** Writing `"currency": "MNT"` into these
vectors would assert a denomination the bytes do not carry — that is precisely the *silent inheritance*
of the gerege/MNT block that `F-2026-09-11-tierd-feasibility.md` §2b forbids. The honest encoding
(`EUR`) is the one that refuses.

## 3. Why the driver's own T305 precedent does not carry here

`LDG-05` was promoted from throwaway tenant `t305` and is the precedent the driver's decision cites.
Two facts separate it from this case:

1. `t305` was seeded **MNT** — `LDG-05-openingbalance-accepted-empty-ledger.json` carries
   `request.currency.code = "MNT"`. The T305 instance matched the graded tenant's currency.
2. The ledger schema has **no `tenant_params` block at all**, so no ledger vector is checked against a
   pinned tenant. The loan schema **does** pin it, and the check is the first tenant rule in `Admit`.

So "same image, same timezone, same rounding mode" was sufficient for LDG-05 but is **not** sufficient
for a loan vector: the loan store additionally pins the currency, and the Tier-D replay ran the e2e
runner, which seeds EUR (see `OWNER.md` line 10). The precedent is about a MNT-compatible throwaway;
Tier D produced a EUR one.

## 4. No `loan` seam admits the case — the refusal is seam-independent

The brief says: if refused, *try a seam that admits the case*. There is none.

The tenant check is at `admit.go:115-124`, **before** the seam dispatch (`admitRequest(v)` at line 126),
and it compares the vector's tenant block to the single store-wide `opts.Pin`. Currency is a
**store-level** property here, not a **per-seam** one: no `loan` seam's own validator can ever be
reached by a vector whose `tenant_params` does not equal the pin. All **13** seams in the store
(`loan-charge-lifecycle`, `loan-delinquent-days`, `loan-journal-entry-batch-balance`,
`loan-repayment-allocation`, `loan-schedule-amortization`, `loan-summary-outstanding`,
`loan-transaction-balance`, `loan-transaction-reversal`, `loan-writeoff-four-bucket`,
`loan-writeoff-journal-entries`, `loan-disbursement`, `loan-schedule-interest`, `loan-status`) share
the one pin and therefore refuse an EUR-tenant vector identically. The harness confirms it: the store
with the three honest candidates reports `inadmissible=3`, **`refused=0`** (nothing even reached a
seam), and the whole graded run is UNUSABLE (exit 2).

**If a vector is refused … try a seam that admits the case. None does. Promote nothing.** That is this
run's result.

## 5. Counterfactual drive measurement (for the record; NOT promoted)

To answer "which drives would notice these vectors", the *identical* candidates were re-run with one
field changed — `tenant_params.currency` `EUR`→`MNT`, the pin's value — in a throwaway store **outside
the repository** (`/tmp`, never committed, never in `.softhouse/`). That is a **counterfactual**, not a
promotion: it measures what the vectors would kill if the currency rule were relaxed, and it is not
admissible provenance.

* 34/34 vectors pass the `loan-go` reference (`parity_fail=0`).
* **No loan drive newly dies.** Every one of the 43 `loan-wrong-*` drives already dies on the committed
  31-vector store; adding the three candidates changes *which* drives die for none of them. There is no
  inert drive to wake and no green drive to turn red.
* Per candidate, measured against every drive:

  | candidate | drives it kills | drives it adds a *second* kill to | drives that notice it at all |
  |---|---|---|---|
  | `LN-TD-L10-…-amortizes-to-zero` | 0 | 3 (`loan-wrong-schedule-amortization-drops-final-component`, `…-uniform-rounded-up`, `…-uniform-truncated`) | 3 |
  | `LN-TD-L06-…-schedule-interest-period-1` | 0 | 0 | **0** |
  | `LN-TD-L06-…-disbursement-net` | 0 | 0 | **0** |

So even under the counterfactual, the pilot vectors are **cross-validation, not new coverage**: the
amortization vector independently re-kills three already-killed drives, and the interest and
disbursement vectors are noticed by **no drive in the corpus** (the schedule-interest values
1000/7%/360-30 do not tie HALF_UP against HALF_EVEN, and there is no `loan-wrong-disbursement-*`
drive at all). Under the honest encoding in §2, they kill nothing because they never load.

This matches the THIRD PASS's caution that the loan read-backs map onto single-cell read-back shapes
"with transforms" — but it adds the measurement Q4 did not make: a mapped vector is not the same as a
*useful* vector, and these three would be redundant at best.

## 6. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued; no container was started; the reference
  oracle was not contacted for any observation.
* **No vector was promoted.** `.softhouse/vectors/loan/` is unchanged at **31** vectors; the working
  tree contains no `LN-TD-*` file. The candidate JSON is recorded above, not loaded.
* No port code changed. `.softhouse/guards/` (baseline **8** pairs), `.softhouse/conformance.sh`
  (census 17), `.softhouse/capture/` and `.softhouse/maps/` are **untouched** (`git status --porcelain`
  empty for all four).
* PostgreSQL only; Oracle Database appears nowhere. Integer minor units throughout; no float.

## 7. Controls and the bar

* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit-2 line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run completed
  and the bar is refused by that recorded decision`. The graded run itself prints
  `VERDICT: PASS (exit 0) — 49 parity vectors match the pinned reference oracle`. **No `HARD guard
  failed`.** Ledger baseline **8** pairs; exemption census pinned; guard census 17.
* `.softhouse/briefs/tools/capcount.sh <wt> loanschedule loanschedule-wrong-days-in-year-365` → **48**
  (the brief's control).
* `.softhouse/briefs/tools/capcount.sh <wt> loan loan-wrong-summary-drops-penalty` → **2**.
* `.softhouse/briefs/tools/redcount.sh <wt> loan` → **43** drives.
* `go test -count=1 -run Committed ./internal/apps/loan/conformance/` on the committed store →
  **ok** (31/31 pass, 0 inadmissible). With the three honest candidates temporarily placed in the
  store it fails `inadmissible=3`; the store was restored to 31 in the same command.

Reproduce the refusal without touching the store:

```
# write the three candidates above (currency EUR) into a COPY of the store, then:
cd nexus && go run ./internal/apps/loan/conformance/cmd/conformance -root <copy-root>
# → refused=0 inadmissible=3 ... exit 2
```

## 8. What would unblock a promotion (a driver decision, not a run decision)

The blocker is a **provenance-policy** question, not a code question: may a `loan` parity vector be
seeded from a capture whose `tenant_params.currency` differs from the pin? Three consistent options,
none of which this run may take unilaterally:

1. **Refuse** (this run's action): throwaway captures back loan vectors only when the throwaway is
   seeded with the graded currency. Tier D's e2e replay is EUR, so it cannot back a loan vector.
2. **Re-capture on an MNT-seeded loan tenant**, replaying the same scenario, so the observation itself
   carries MNT — the T305 route, correctly applied.
3. **A ratified provenance exception** that admits a foreign-currency read-back while keeping the pin
   unchanged. This needs the driver's explicit record; it is not inferable from the 2026-09-11
   decision, whose text covers image, timezone, rounding mode and destruction but is silent on
   currency.

Until one is recorded, the honest result is: **the replayed read-backs are refused by the loan tenant
pin; nothing is promoted.**
