# `provisioning` — capture and promotion attestation (OH-3)

**Task:** OH-3, branch `feat/OH3-provisioning`. **Context:** the `provisioning` conformance
harness, its RAW oracle captures, and the parity vectors promoted from them.

**Reference oracle (Fineract) reachability, this fire: REACHABLE**
[VERIFIED: `curl -sk https://localhost:8443/fineract-provider/actuator/health` →
`{"status":"UP","groups":["liveness","readiness"]}`; `gerege-oracle-app` up 28 h healthy,
`gerege-oracle-db` (`postgres:18.3`) up 5 days healthy — run by this task].
Pinned checkout `/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

> **RAW OBSERVED FORM ONLY.** Every file under `capture/provisioning/out/` is an unmodified
> HTTP response body from the running oracle. Nothing was computed, nothing contract-shaped.
> Every number in a vector is transcribed from one of these captures and cited to it.

## 1. What was captured

| file | endpoint / seam | observed body |
|---|---|---|
| `CAT-00-categories-raw.json` | `GET /v1/provisioningcategory` | the four `m_provision_category` rows (ids 1–4, STANDARD / SUB-STANDARD / DOUBTFUL / LOSS) |
| `CRI-00-criteria-empty-raw.json` | provisioning criteria list | `[]` — zero provisioning criteria |
| `CRI-01-template-raw.json` | provisioning criteria template | 1 loan product, 4 category definitions, `glAccounts: []` |
| `ENT-00-entries-empty-raw.json` | provisioning entries | `{"pageItems":[],"totalFilteredRecords":0}` |
| `ENT-01-entries-list-empty-raw.json` | provisioning entries (list) | `{"pageItems":[],"totalFilteredRecords":0}` |

The two entries captures are two distinct request shapes over the same empty result, kept so the
emptiness is corroborated rather than assumed from one probe.

## 2. What was promoted

Four parity vectors, each class `parity`, schema `gerege.provisioning.vector/v1`, context
`provisioning`, all citing `CAT-00-categories-raw.json` with
`capture_sha256 = b7c62862064d9b02e5506fb20b4d88e1449de20a62e54593fbdfcb6764eaf787`
(`shasum -a 256` of that file, recomputed by this task):

* `PV-01-STANDARD` — category id 1 → STANDARD / "Punctual Payment without any dues"
* `PV-02-SUB-STANDARD` — category id 2 → SUB-STANDARD / "Principal and/or Interest overdue by x days"
* `PV-03-DOUBTFUL` — category id 3 → DOUBTFUL / "Principal and/or Interest overdue by x days and less than y"
* `PV-04-LOSS` — category id 4 → LOSS / "Principal and/or Interest overdue by y days"

Each vector's `expect` carries only `id`, `name` and `description`, transcribed field-for-field
from the cited capture row. **No expected value was computed.** The `request.category_id` is the
capture row's own `id`; the `expect` fields are that row's `id`, `categoryName` and
`categoryDescription`. `tenant_params` on every vector: `HALF_UP`, ordinal 4, precision 19, `MNT`,
2 minor units, `Asia/Ulaanbaatar` (as pinned in `.softhouse/PIN-provisioning.json`).

## 3. What could NOT be captured (and was left out, not invented)

The reserve-amount arithmetic (`money.go:45` `PercentageOf`), the age-band matching rule
(`Matches`/`ReserveRate`) and the overlap invariant (`Overlaps`/`ValidateRange`) are functions of
criteria DEFINITIONS and per-loan overdue rows. The gerege tenant holds zero criteria, zero
definitions, zero loan-product mappings, zero loans and zero provisioning entries, so the oracle
exposes no reserve amount, no matched band and no overlap refusal to transcribe. Observing any of
them would require writing a criteria, mapping or loan to the shared server, which the capture
contract forbids. Those behaviours are therefore NOT in this harness's graded domain — see
`nexus/internal/apps/provisioning/conformance/doc.go`.

## 4. Tenant left EXACTLY as found

[VERIFIED by this task, READ-ONLY SQL after the captures — `SELECT` only, no write to any schema,
no restart, no re-tenant]:

```
docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -tAc
"select 'category',count(*) from m_provision_category
 union all select 'criteria',count(*) from m_provisioning_criteria
 union all select 'criteria_def',count(*) from m_provisioning_criteria_definition
 union all select 'loanproduct_mapping',count(*) from m_loanproduct_provisioning_mapping
 union all select 'loanproduct_entry',count(*) from m_loanproduct_provisioning_entry
 union all select 'history',count(*) from m_provisioning_history
 union all select 'loan',count(*) from m_loan
 union all select 'product_loan',count(*) from m_product_loan"
```

yields `category|4  criteria|0  criteria_def|0  loanproduct_mapping|0  loanproduct_entry|0
history|0  loan|0  product_loan|1`. The four categories are the seeded default rows; every
provisioning criteria/definition/mapping/entry table is empty, and there is one loan product and
zero loans. This is the exact state the captures describe, so nothing was written, and PostgreSQL
18.3 is the only engine reached.
