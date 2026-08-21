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
| `gate-selftest.py` | every refusal clause the live oracle cannot reach, fired individually — 22 cases | `python3 gate-selftest.py` |
| `blast-radius.py` | re-grades all five **committed** attestations against the facts each recorded of itself | `python3 blast-radius.py` |
| `compare-bytes.py` | digest comparison of re-captured bodies against their committed counterparts | called by `drive-canary-green.sh` |

## What is simulated, and what is not

The HALF_EVEN JVM is **real**. The shared reference-oracle container serves `gerege` at HALF_UP
and `default` at HALF_EVEN from one process — measured 2026-08-21 on the pinned exact tie
(`1,162,502.50 × 0.018 = 20,925.045`): `gerege` → `20925.05`, `default` → `20925.04`, both HTTP
200. No container was restarted, rebuilt, re-seeded or reconfigured.

The **only** simulated element is in `drive-canary-red.sh` and `drive-stale-fork.sh`: the OUTER
precondition gate is disabled by one labelled substitution, because `preconditions.sh` is what
currently refuses a wrong-mode tenant and the question those scripts ask is what the INNER canary
block does when it is reached. Each script prints and archives its own `scratch.diff` so the exact
extent of the change is on the record.

The gate itself lives in `.softhouse/capture/lib/attest_gate.py` and is imported — never inlined —
by all three attestation sidecars. See `.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T125.md`.
