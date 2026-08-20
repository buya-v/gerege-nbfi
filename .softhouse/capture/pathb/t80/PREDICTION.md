# T80 — predictions, registered BEFORE running any attack against the hardened recipe

P-9 discipline. Written and committed **before** the first attack transcript exists. The code
changes to `t36/preconditions.sh`, `t36/recapture.sh` and `t36/attest.py` are already made at the
time of writing (they are in the same commit as this file); what is *not* yet observed is how they
behave, and that is what is predicted here. Anything I get wrong stays in the record.

Read-only oracle contact already made before this file: `curl actuator/health` and
`docker ps` (both containers `Up (healthy)`), plus `shasum` of the committed canary request.
No capture, no attack run, no POST beyond that.

## Environment predicted

* `fineract-fineract-1` and `fineract-db-1` both `Up (healthy)`, image `fineract:latest`
  `sha256:e596339626bf…`, `postgres:18.3`. Unrestarted for the whole task.
* Canary request `t22-audit/req/calc-pmode2-gerege.json` sha256
  `2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154` — **already measured**, so
  this is a record, not a prediction.

## Predictions

| # | attack | predicted outcome |
|---|---|---|
| P-1 | `TENANT=default sh t36/recapture.sh` | **exit 1**, `ABORT: preconditions breached`, **5** FAIL lines (tz Asia/Kolkata, `rounding-mode` row = 6, JVM logline HALF_EVEN, MySQL-era `schema_connection_parameters`, canary HTTP 404 on `default` where product 11 does not exist). **Zero** `B-0*-raw.json` written anywhere. Output directory is `out/recapture-default`, never `recapture-gerege`. |
| P-2 | `TENANT=default RECAPTURE_OUT=<…/t36/out/recapture-gerege> sh t36/recapture.sh` | **exit 1** at the directory-name guard, **before** the preconditions even run; `recapture-gerege` untouched — its files keep their committed digests. |
| P-3 | mutated canary, principal `1162502.5` → `1162502.55`, on tenant `gerege` | **exit 1**, exactly **1** FAIL: `canary request DIGEST MISMATCH` naming **both** digests. **No** `PASS effective rounding mode canary` line anywhere in the output — the canary is not sent at all. |
| P-4 | the same mutated canary on tenant `default` (the HALF_EVEN one) | **exit 1**; the digest-mismatch FAIL is present and `PASS … canary … (= HALF_UP)` is **absent**. This is the exact sentence T77 produced against T76's script; it must be unreachable now. |
| P-5 | swapped canary — point `CANARY_REQ` at another *committed, valid* request (`t22-audit/req/calc-pmode-gerege.json`) on `gerege` | **exit 1**, digest mismatch, canary not sent. |
| P-6 | `CANARY_EXPECT=20925.04 … preconditions.sh default` (the attack T76 *documented* but did not run) | **exit 1**, **6** FAIL — the five `default` breaches plus `CANARY_EXPECT was set in the environment`. This is the number T76's transcript claimed and T77 measured as 5, because T76's tripwire watched a decoy variable. If it is not 6 I will publish the number I measure, not the one I predicted. |
| P-7 | every attack re-run under `bash` instead of `sh` | identical exit codes and identical FAIL/PASS counts. |
| P-8 | happy path, `RECAPTURE_OUT=<…/t80/out/recapture-gerege> sh t36/recapture.sh` on `gerege` | **exit 0**, **22 PASS / 0 FAIL** (same count as T76's transcript — the digest pin replaces the substring pin in the same slot, it does not add a line), and the four captures **byte-identical** to the committed corpus: `713a3560…`, `9de8757d…`, `892dd6f5…`, `c80f62b0…`. |
| P-9 | `.softhouse/vectors/` unchanged; `git diff main...HEAD -- .softhouse/vectors/` empty | nothing promoted. |
| P-10 | `python3 t36/attest.py` re-run is **not** performed for the happy path | I intend to prove the *recipe* (`recapture.sh`), not to produce a fourth attestation set. If I do run `attest.py` it will be into a `t80/`-owned directory and the sidecar will read revision **12 / RATIFIED** from `PIN.json` + `gates.md` rather than the hard-coded "6 / UNRATIFIED". |
| P-11 | `m_loan` row count in `fineract_gerege` stays **0** | every request I send is `POST /loans?command=calculateLoanSchedule`, a pure calculation endpoint. |

## What I expect to be WRONG about

I have not measured the FAIL count on `default` myself this fire; 5 is T76's and T77's number and
tenant state could have moved. If it is not 5, P-1/P-6 are refuted and I will say so.
