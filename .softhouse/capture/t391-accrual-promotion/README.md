# T391 — the accrual promotion rig

**Branch:** `softhouse/T391-accrual-promotion`. **Fire** `20260828-140005` iteration 4.
Tenant `gerege`, database `fineract_gerege`, PostgreSQL 18.3, reference oracle (Fineract)
pinned at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, health probed UP.

## THE MUTATION BUDGET WAS ZERO, AND IT IS ENFORCED STRUCTURALLY

**No entity in the reference oracle was created, modified or deleted by this task.**
That is not a promise in prose; it is a property of the two tools:

* `capget.sh` **has no method argument.** It can only issue `GET`. There is nothing to
  pass it that would make it POST.
* `capsql-readonly.sh` **refuses the file before psql is invoked** if the executable text
  (`--` comments and `\echo` lines stripped) contains a write keyword, or if the file uses
  any psql meta-command other than `\echo` — `\copy` writes, `\i` includes, `\o` redirects,
  `\!` shells out — or if it contains a `/*` block comment that could hide executable text
  from the line-oriented scan.

Every observation this task promoted already existed in the oracle; re-issuing a POST
would have moved it a second time and corrupted the evidence being promoted, which is
T389's own reason for not re-issuing T388's twenty POSTs.

## THE THING THAT WAS NOT THERE WHEN T388 LOOKED

T388 recorded, as the one thing it could not capture, *"the SCHEDULED job (id 16) firing
on its own … its next run is 2026-08-28 16:02"*. **A scheduled job fired at 16:01:00 and
produced three more accrual transactions** — `L32`/`L33`/`L34`, loan transactions 32/33/34,
journal entries 96–113, nine more receivable-slot legs. `m_portfolio_command_source` is
still 379, so no API call made them.

`job_run_history` puts **job 11 `Add Accrual Transactions`** at `16:01:00.049 → .120`,
`trigger_type cron`, status success — an interval that **strictly contains** every one of
those `created_on_utc` timestamps (`.100` … `.117`) — while job 22 ran `.002 → .030` and
job 16 not until `16:02:00.002`. **Stated as a limit:** `job` and `job_run_history` record
*when* a job ran, not *which rows it wrote*, and no foreign key joins a journal entry to a
job. This eliminates two candidates; it is not a proof of authorship, and nothing is
promoted as one.

## Files

| file | what it is |
|---|---|
| `env.sh` | the oracle endpoint and tenant. A COPY, never a cross-directory `.` (T287's rule) |
| `capget.sh` | GET-only capture. Writes `.http` / `.status` / `.json` and **no `.req`** — see below |
| `capsql-readonly.sh` | T388's `capsql.sh` plus a write-statement refusal. A successor file, not an edit (T114) |
| `manifest.sh`, `MANIFEST.sha256` | digests the WHOLE rig, scripts included |
| `sql/q1` … `sql/q5` | the SELECT-only queries, exact bytes executed |
| `bin/10-decode-legs.py` | decodes a `/journalentries` body **keeping the amount as the oracle's characters** (`parse_float=str`) |
| `bin/20-compare-to-t388.py` | is today's response the one T388 recorded? Key-order-normalised, values byte-compared |
| `bin/30-product-mapping.py` | product 63's accounting mappings as the CONTRACT BOUNDARY renders them |
| `bin/50-emit-vectors.py` | the transcription assembler. **No arithmetic anywhere in it** |
| `bin/60-rewrite-capabilities.py` | the `ledger.accrual.entry` rewrite. Asserts the OLD text before replacing it, so it cannot run twice or against a drifted file |
| `bin/70-drive-wrongimpl.sh` | the non-vacuity drive, both directions plus a control |
| `out/` | every artefact, verbatim |

## Two guards that fired on this rig, kept in the record rather than tidied away

1. **`capsql-readonly.sh`'s first draft refused a SELECT-only file because a COMMENT
   contained the word `call`.** A guard that cries wolf on prose gets disabled by the next
   author. Fixed by scanning the executable text only, and the false positive is documented
   in the script's own header.
2. **The bar REFUSED at exit 2 on eight `.req` files that are not request bodies.** The
   repository-wide wire-float round-trip guard takes every `*.req` under `.softhouse/capture`
   as a request body and requires it to parse as JSON. A GET has no body, so `capget.sh` had
   nothing to pin and was writing the request *line and headers* under a name that claims to
   be a body. **The guard was right and the script was wrong**: `capget.sh` no longer writes
   `.req` at all — matching `cap11.sh`, whose GET captures carry `.http`/`.status`/`.json` and
   nothing else — and the vectors cite the `.http` record, which holds the request line, the
   headers and the `Idempotency-Key` actually sent.

## What this rig did NOT do

* **It posted none of the five remaining accrual slots** (6 `LOSSES_WRITTEN_OFF`, 10
  `TRANSFERS_SUSPENSE`, 11 `OVERPAYMENT`, 12 `INCOME_FROM_RECOVERY`, 13 `GOODWILL_CREDIT`).
  They are DECLARED instead, in `capabilities-ledger.json`'s `ledger.slot.resolution` row, so
  the harness prints the gap on every run. Reasoning in the handoff.
* **It discharged no `PROBES.tsv` obligation** — that file is T390's, outside this grant, and
  T388's twenty command-source rows remain UNATTRIBUTED.
* **It made no precision claim.** No leg observed here carries a non-zero third decimal, so
  nothing in this capture discriminates `(19, HALF_UP)`.
