# T125 — proof directory for the effective-rounding-mode gate

**NOTHING HERE IS A CAPTURE SET AND NOTHING HERE IS PROMOTABLE.** These directories are the
evidence for one defect and its fix. They are not vectors, they are not an oracle corpus, and no
downstream tool reads them.

> **`red-pre-fix-default/attestation.json` IS A DELIBERATELY DEFECTIVE ARTEFACT.** It was produced
> on a **HALF_EVEN** JVM by the pre-fix generator, to demonstrate that the generator would produce
> it. It records `MathContext(19, HALF_EVEN)`, `observed_period1_interest: 20925.04`,
> `verdict: MODE NOT CONFIRMED`, `produced_by.task: T125-RED-DEMO`, and its directory carries
> `CAPTURED-FROM-TENANT = default`. **Never cite it as an attestation of anything except the
> absence of the gate.** The fixed generator can no longer produce it (see
> `red-post-fix-default/`, which contains no attestation at all).

## Scripts

| script | what it proves | how to run |
|---|---|---|
| `drive-canary-red.sh <dir-ending-in--default>` | the gate's behaviour on a **real HALF_EVEN JVM** — tenant `default` on the shared oracle | `bash drive-canary-red.sh red-post-fix-default` |
| `drive-canary-green.sh` | both live sidecars, **unmodified, full preconditions**, on the ratified `gerege` tenant: exit 0, gate proves HALF_UP, and no committed capture changes its bytes | `bash drive-canary-green.sh` |
| `drive-stale-fork.sh` | RED/GREEN for `charges/bin/attest.py`, which is a stale fork that cannot complete a capture | `bash drive-stale-fork.sh` |
| `gate-selftest.py` | every refusal clause the live oracle cannot reach, fired individually — **30 cases** (22 from T125, 8 added by T147 for the document grader) | `python3 gate-selftest.py` |
| `blast-radius.py` | re-grades the five **committed** attestations *produced by these three sidecars* against the facts each recorded of itself (T136 mutation-tested it: 7 tamperings, 7 detected) | `python3 blast-radius.py` |
| `compare-bytes.py` | digest comparison of re-captured bodies against their committed counterparts. **T147:** zero files inspected is now exit 2, not a pass (P-35) | called by `drive-canary-green.sh` |

## What is simulated, and what is not

The HALF_EVEN JVM is **real**. The shared reference-oracle container serves `gerege` at HALF_UP
and `default` at HALF_EVEN from one process — measured 2026-08-21 on the pinned exact tie
(`1,162,502.50 × 0.018 = 20,925.045`): `gerege` → `20925.05`, `default` → `20925.04`, both HTTP
200. No container was restarted, rebuilt, re-seeded or reconfigured.

The two canary requests differ **only** in `productId` (11 on `gerege`, 10 on `default`), and that
is not a loose end: T136 compared `to_jsonb(m_product_loan)` for id 10 @ `fineract_default` against
id 11 @ `fineract_gerege` — **89 columns compared, 1 differing, and the differing column is `id`**.
So the `20925.05` / `20925.04` split is the rounding mode and nothing else.

The **only** simulated element is in `drive-canary-red.sh` and `drive-stale-fork.sh`: the OUTER
precondition gate is disabled by one labelled substitution, because `preconditions.sh` is what
currently refuses a wrong-mode tenant and the question those scripts ask is what the INNER canary
block does when it is reached. Each script prints and archives its own `scratch.diff` so the exact
extent of the change is on the record — and since T147 `drive-canary-red.sh` **asserts** that diff's
size against what its substitutions can account for, instead of printing the number beside a prose
"expect 4" that nothing compared (it was printing `changed lines: 2 (expect 4 …)`).

**Ordering is proved by differential, not by reading** (T136): neuter only the pre-capture gate and
**4 capture bodies appear**; unmutated, **0**. With the first gate gone the document grader still
refuses on live data, exit 4, and no `attestation.json` is written — the two layers are genuinely
independent.

**One thing this directory does NOT prove**, stated plainly (P-22): **`attest-t40.py` has no live
RED proof.** `drive-canary-red.sh` drives `t36/attest.py` and `drive-stale-fork.sh` drives
`charges/bin/attest.py`; nothing drives `attest-t40.py` against a wrong-mode tenant, because
`m_charge` has 0 rows on `default` and all 44 charge-bearing shapes return HTTP 404 there. Its gate
is the same shared call and `gate-selftest.py` covers the logic — but "proven by construction" is
not "driven red", and closing it needs charges provisioned on a second tenant, i.e. a write to the
shared oracle.

The gate itself lives in `.softhouse/capture/lib/attest_gate.py` and is imported — never inlined —
by all three attestation sidecars. See `.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T125.md`.
