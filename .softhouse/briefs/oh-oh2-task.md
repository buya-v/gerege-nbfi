# OH-2 — capture parity vectors for `charges` from the running oracle

WORKING DIRECTORY: /Users/buv/oh-gerege-oh2  (branch feat/OH2-charges-vectors)
NEVER commit to `main`. NEVER touch the other worktrees. NEVER modify the oracle.

## What is already true
- `nexus/internal/apps/charges/conformance/` EXISTS — 1,946 lines, built and
  verified, and it has NEVER GRADED ANYTHING. `.softhouse/vectors/charges/` is
  empty. `TestEmptyStoreRefuses` passes today because the corpus is empty and the
  harness correctly REFUSES rather than passing vacuously.
- The ratified tenant `gerege` was restored and PROVED on the running oracle:
      1,162,502.50 x 0.018 = 20,925.045
        gerege  (HALF_UP, ordinal 4, Asia/Ulaanbaatar) -> 20925.05
        default (HALF_EVEN, ordinal 6, Asia/Kolkata)   -> 20925.04
  Connection facts: .softhouse/reference-oracle.md

## Your task
Capture parity vectors for the `charges` context FROM THE RUNNING ORACLE, under
the `gerege` tenant, and make the harness grade them green.

## Non-negotiable
- CAPTURE ONLY. Never synthesise, transcribe, hand-write or infer a vector value.
  A vector is a RECORDING of what the oracle answered. If you cannot observe it,
  you do not have it.
- Capture under `gerege`, never `default`. A capture from default records the
  wrong rounding under the right name.
- EVERY vector carries `tenant_params` — rounding_mode AND rounding_ordinal,
  precision, currency, minor_units, timezone. The mechanism is merged and the
  harness REFUSES a vector whose params differ from the store pin's.
- Follow the existing vector schema. Read two vectors from
  .softhouse/vectors/loanschedule/ to learn its shape. Do not invent a new one.
- Do NOT edit the harness to make a vector pass. If the harness refuses your
  vector, the vector or the port is wrong, not the harness.
- Do NOT edit any guard, gate or pin.

## Coverage
Start with the charge arithmetic that actually moves money: flat vs percentage
calculation, the charge-time and charge-calculation enum combinations, and at
least one case that exercises rounding at the currency quantization. Breadth
beats depth for a first corpus — a vector per distinct behaviour, not twenty
variations of one.

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   bash .softhouse/conformance.sh
   the count of vectors captured, and for ONE of them the full JSON including
   its tenant_params

Report exit codes. Never say complete / done / goal achieved. If the oracle
refuses a request, report the refusal — a refusal observed is itself a vector
class in this store. If you can capture nothing, say so plainly and stop.
