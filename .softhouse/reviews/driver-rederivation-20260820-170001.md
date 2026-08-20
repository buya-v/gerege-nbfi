# Driver re-derivation — local fire 20260820-170001

Written by the `/softhouse-program` driver. Committed so a ruling on a worker's report cannot turn on
whose document reads better.

---

## 1. THE DRIVER'S BRIEF FOR T76 WAS STALE, AND T76 REFUTED IT BEFORE TOUCHING THE ORACLE

**What the driver asserted when dispatching T76:** that T22's `P0-3`, `P0-4`, `P0-5` and `P0-6` were still
open, and that closing them was the task. The driver took this from `.softhouse/RESUME.md` ("Also still
waiting, and ORACLE-ONLY: T25's parked P0s … T22 P0-3/4/5/6 … They still block vector promotion") and from
`T25`'s own note in `tasks.json`, and **did not check whether a later task had already closed them.**

**T76 checked, and the driver has now re-checked from the commits directly.** Verified at the listed
commits on `main`:

| item | claimed closer | driver's independent check |
|---|---|---|
| T22 **P0-4** (preconditions must FAIL the run) | T36 `c3bbf26` | **CONFIRMED** — commit subject *"Path B fail-the-run preconditions (T22 P0-4), validated live + negative control on default"*; adds `pathb/t36/preconditions.sh` (183 lines) and `out/preconditions-default-NEGATIVE.txt` |
| T22 **P0-6** (re-point at a production-settings tenant) | T36 `fab040a`, `60c08ad` | **CONFIRMED** — *"re-capture B-01..B-04 on production-settings tenant gerege (19,HALF_UP / Asia/Ulaanbaatar)"*, plus a second arm with T36-owned re-created products |
| T22 **P0-3** (machine-readable attestation sidecar) | T36 `78c5bda` | **CONFIRMED** — *"attestation sidecar (T22 P0-3) read live from server+PostgreSQL"*; adds `attest.py` (351 lines) and `out/recapture-gerege/attestation.json` (224 lines) |
| T22 **P0-5** (the broken `-o out/B-$n-*-raw.json` glob) | T30 `1b65b1c` | **NOT DIRECTLY VERIFIED BY THE DRIVER.** `1b65b1c` does touch `pathb/REPRODUCE.md` (+41 lines) and is titled *"dropped/mis-parked T22 items"*, which is consistent, but the driver did not open the diff to confirm the glob itself was rewritten. Left to T77. |
| T22 **P1-14** (B-03/B-04 never independently re-derived) | T30 `1b65b1c` | **CONFIRMED** — adds `reviews/t30-probe/t30_rederive_b03_b04.py` (305 lines) and `t30-rederive-output.txt` |

**The driver's brief was also imprecise on the contract.** It told T76 to read "`contract.go` REVISION 10
(around lines 97-115)". `contract.go` is at **REVISION 11** — `:50` ("honours 16 of them (REVISION 11…)"),
`:314`, `:908`, `:1217` [DRIVER-VERIFIED by reading the file]. `REVISION 10` at `:97` is a *section heading
inside* a revision-11 document, not the document's revision.

**This is the same failure mode as last fire's F-1**, and the driver committed it again: a claim was carried
from one document into a dispatch prompt without being opened. Last fire it was a line number (`:1226`);
this fire it was an entire task premise. `P-12` and `P-16` both apply.

**Where the stale sentence lives, so it stops propagating:** `.softhouse/RESUME.md` (the "Also still
waiting, and ORACLE-ONLY" paragraph) and the `note` field of task `T25` in `tasks.json`, which still reads
`PARKED oracle_unreachable: … T22 P0-3/4/5/6`. T25's park list was written on 18 August **before** T30 and
T36 ran, and nothing updated it when they did. Both are corrected this fire.

## 2. T76's PROMOTION REFUSALS — DRIVER-VERIFIED AGAINST THE FROZEN CONTRACT

T76 promoted **nothing**, and the driver agrees. Checked by reading `contract.go`, not T76's account:

- **B-02** (`installmentAmountInMultiplesOf = 100`). `contract.go:114-116` states in the frozen text:
  *"InstallmentRoundingMultipleMinor stays in this contract and is refused for Run 1 (DEC-1 section 4.7)
  precisely because the field is money-moving one call away, not because the oracle ignores it."*
  `:1130` pins `InstallmentRoundingMultipleMinor == 0`. **Refusal correct** — and note the contract refuses
  it *while agreeing it moves money*, which is exactly why the refusal is a shelving, not a dismissal.
- **B-03 / B-04** (`daysInYearCustomStrategy`). `contract.go:1183` pins
  `daysInYearCustomStrategy = null`. The frozen `GenerateRequest` has no component to carry it, so a vector
  over it would grade nothing. **Refusal correct**; promoting would need a contract shape change, which is a
  hard `user` gate.
- **B-01**. Refused as money-identical to the already-promoted `P-MNT-1M2`. **Left to T77** — the driver did
  not check that cell by cell, and if the identity is wrong a promotable vector was discarded.

This is the T66 rule holding for the second fire running: **a capture that grades no field the frozen
contract returns is not a vector**, and refusing to promote it is the correct outcome, not a failure to
deliver.

## 3. WHAT T76 DELIVERED ONCE ITS BRIEF DISSOLVED — not yet adjudicated

Recorded here as claims, pending T77: a third independent re-capture on `gerege` byte-identical to both
prior sets; two holes closed in the precondition script (`CANARY_EXPECT` was env-overridable, and the canary
request was pinned only by path); a new failable mirror-column invariant `I7`; and the observation that
`sh .softhouse/conformance.sh` dies on bash process substitution at line 104 and exits **2** — the harness's
own fatal code, which the driver considers the most dangerous item in the report if confirmed, because
`exit 2` is the code that must never be read as a pass.

## 4. STANDING CORRECTION TO THE DRIVER'S OWN PROCEDURE

A `parked` list inside a task note is **evidence of what was true when it was written, not a work queue.**
Before dispatching from one, check whether a later commit closed the items. The cost of not checking, this
fire, was one full opus worker re-verifying work that was already done — which it converted into genuine
findings only because it was told to check the driver's claims. Filed as a candidate pattern for the
postmortem.
