# T149 — the HALF_UP exact tie, captured on Path B and promoted

This directory is the capture set and the evidence behind the parity vector
`.softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json`, which is
the **first parity vector in the store observed through the running Fineract server**.

Everything here was taken live from the pinned reference oracle on 2026-08-21. Nothing
here is synthesised, and nothing here was restarted, rebuilt or re-seeded — other workers
shared the containers this fire. Every request is
`POST /loans?command=calculateLoanSchedule`, which persists nothing.

## Layout

```
t149/
├── req/                          the four requests, each a one-field edit of the
│                                 committed canary calc-pmode2-gerege.json
├── out/gerege/                   the capture set + attestation.json   (tenant gerege, HALF_UP)
├── out/default-HALF-EVEN-ARM/    the counterfactual arm               (tenant default, HALF_EVEN)
│                                 NOT PRODUCTION-REPRESENTATIVE, NOT PROMOTABLE, no attestation
└── redgreen/                     the transcripts every claim above rests on
```

## The captures

All four are the same request shape as the digest-pinned rounding-mode canary — MNT
principal over `12 x 21.6 %` p.a., monthly, disbursed and starting 2026-01-01, declining
balance, `interestCalculationPeriodType = 1` — differing only in `productId` and
`principal`.

| id | product | day count | principal | response sha256 |
|---|---|---|---|---|
| `T149-TIE-P9` | 9 `T22 probe p09-sarp-360-30` | fixed 30/360 | 1,162,502.50 | `39f56dc2…` |
| `T149-TIE-P1` | 1 `PathB Progressive MNT` | actual/actual | 1,162,502.50 | `39f56dc2…` |
| `T149-CTRL-P9-1M2` | 9 | fixed 30/360 | 1,200,000 | `713a3560…` |
| `T149-CTRL-P1-1M2` | 1 | actual/actual | 1,200,000 | `713a3560…` |

Two identities fall out of that table and neither was assumed:

* **the day count moves nothing on this shape** — the 30/360 and ACT/ACT responses are
  byte-identical, at both principals;
* **`713a3560…` is the digest of the committed `.softhouse/capture/pathb/out/B-01-baseline-raw.json`**,
  captured by T36 in a different fire. The 1.2M control reproduces it exactly.

The tie capture was taken **twice** in this task, on two versions of the rig, an hour
apart, and came back byte-identical both times.

## What each script does

| script | what it establishes |
|---|---|
| `t36/attest.py gerege t149` | drives the four captures behind the 15 fail-the-run preconditions and the effective-rounding-mode gate, and writes `out/gerege/attestation.json`. The capture set is registered in `t36/attest.py` itself rather than forked into a private copy (P-21). |
| `capture-halfeven-arm.sh` | the HALF_EVEN arm on tenant `default`. Digest-pins its request, asserts the tenant's `rounding-mode` ordinal is 6 and that period-1 interest is `20925.04`, and refuses otherwise. It deliberately does **not** go through `attest.py`, whose gate refuses a non-HALF_UP tenant — correctly, because an attestation asserts capture at `(19, HALF_UP)`. |
| `compare-arms.py` | re-establishes T136's 89-column product-twin finding from the rows, then diffs the two arms cell by cell in exact minor units. |
| `crosscheck-vs-patha.py` | closes T76's `[UNVERIFIED]` on `interestCalculationPeriodMethod` by comparing the 1.2M control against the promoted Path A vector `P-MNT-1M2`, with the day count controlled. |
| `promote-vector.py` | transcribes the vector. Reads with `parse_float=str` throughout — Path B emits money as bare JSON numbers on the wire. |
| `grade-scratch-store.sh` | grades a candidate in a scratch store before it goes near the real one. **Not** a conformance verdict; every verdict this task reports came from `bash .softhouse/conformance.sh`. |
| `prove-redgreen.sh` | the three arms of the discrimination proof, with assertions rather than printed numbers. |

## The red/green proof

```sh
bash prove-redgreen.sh
```

| arm | store | port | expected | observed |
|---|---|---|---|---|
| 1 | the **42**-vector store, this vector parked | mutated to HALF_EVEN (`M7`) | FAIL 3 | parity PASS 39 FAIL 3 — `T61-HE-A/B/C` |
| 2 | the **43**-vector store | mutated to HALF_EVEN (`M7`) | this vector RED | parity PASS 39 FAIL 4 — `T149-PATHB-TIE` + the three |
| 3 | the **43**-vector store | unmutated | GREEN | `VERDICT: PASS (exit 0)`, 43 parity, 5,664 cells |

The driver **asserts** each of those, it does not print them beside a prose expectation —
that shape is the defect T136 recorded as F-2 in this very tree.

**Arm 1 is the important one, and it is a correction to the task that commissioned this
work.** The brief said *"0 of 46 vectors carry either tie answer — so nothing in the parity
corpus would notice a port that inherited Fineract's stock HALF_EVEN default."* The first
clause is true of the literal characters `20925.05` and `20925.04`. The inference is false:
T61's three tie vectors were already killing exactly this mutation. Searching the store for
a value is not the same question as asking what the store kills.

The mutation is not this task's invention either — it is the already-named `M7`
`MONEY-QUANTIZATION-HALF-EVEN` of `.softhouse/handoff/T61-mutations.py`, which runs an
unmutated baseline first and refuses to attribute anything to a mutation unless that
baseline is green, and reverts in a `finally`. Nothing under `nexus/` is committed mutated;
`git status` on `nexus/` was verified empty after every run.

## What this directory does NOT establish

* **Nothing about a charge, a holiday, a working-day adjustment or a daily interest
  calculation.** Path B can exercise all of them; none was captured here.
* **Nothing about `interestCalculationPeriodMethod` in general.** The closure above is for
  this shape — monthly, single disbursement on the schedule start date — and it is a
  measurement, not an amendment to DEC-1's pin.
* **Nothing about cutover.** That is a hard `user` gate.
