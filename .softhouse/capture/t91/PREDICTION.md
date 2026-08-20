# T91 — predictions, registered BEFORE any attack was run

Committed before `run-attacks.sh` was executed for the first time, so the record cannot be
back-fitted to the result. Each prediction is scored in the handoff; a prediction I got wrong is
reported as wrong, not quietly deleted.

## What is under test

Three files that were, at some point, the same bytes:

| path | role |
|---|---|
| `.softhouse/capture/pathb/t36/preconditions.sh` | the rig T76+T80 hardened. Read-only to me. |
| `.softhouse/capture/charges/bin/preconditions.sh` | **live** twin, invoked by 17 capture scripts |
| `.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh` | the file T91 names; invoked by nothing |

The latter two are **byte-identical to each other** (`sha256 9256b881…a46b54`, measured).

## Predictions about the attacks (pre-fix = the unhardened bytes)

- **PR-1 — A2a (mutated canary, `principal` 1162502.5 → 1162502.55, tenant gerege).** The pre-fix
  script accepts any readable file as `CANARY_REQ`, so it will POST the mutated request, get
  `20925.05` (1162502.55 x 0.018 = 20925.0459, not a tie, so both modes agree), and print
  `PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)` with **exit 0**.
  That sentence will be a tautology: it would have printed on a HALF_EVEN JVM too.
- **PR-2 — A2c (crafted canary `principal` 1162502.4 **plus** `CANARY_EXPECT=20925.04`, tenant
  gerege).** 1162502.4 x 0.018 = 20925.0432 -> `20925.04` under either mode. Both operands of the
  check are attacker-supplied, so the pre-fix script will print
  `PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)` — the rig
  certifying HALF_UP while displaying the value the comment says means HALF_EVEN — **exit 0**.
  This is the sharpest form of the defect and I expect it to reproduce exactly.
- **PR-3 — A3a (canary swapped for another committed valid request, `calc-pmode-gerege.json`).**
  I do **not** know what period-1 interest that request yields. I predict it is **not** 20925.05
  and the pre-fix run therefore FAILS — but fails for the wrong reason (arithmetic disagreement),
  not because the rig noticed the request was not the pinned tie. If it happens to yield 20925.05
  the pre-fix run passes and the hole is worse than I predicted. Recorded as genuinely open.
- **PR-4 — A3b/A3c (canary missing / unset).** Pre-fix already fails closed: `bad "rounding-mode
  canary NOT run"`, exit 1. No change expected post-fix beyond a longer message.
- **PR-5 — A4a (`CANARY_EXPECT=20925.04` on tenant `default`).** T80 recorded that the pinned
  request's `productId 11` does not exist on `default`, so the POST returns **HTTP 404** and the
  canary limb is never graded. I predict the same here, which means **A4a cannot demonstrate the
  override hole** and PR-2 is the demonstration that has to carry it.
- **PR-6 — A4b (`CANARY_EXPECT=20925.04`, canonical request, tenant gerege).** Real answer is
  20925.05, expectation is 20925.04, so this FAILS pre-fix. The override hole is invisible in this
  direction; only PR-2's direction exposes it.
- **PR-7 — post-fix, every attack class.** Exit 1, the string
  `PASS  effective rounding mode canary` **absent from every attack transcript**, and the two new
  breach lines (`CANARY_EXPECT was set in the environment`, `canary request DIGEST MISMATCH`)
  present where applicable.
- **PR-8 — `sh` vs `bash` invariance.** Every transcript pair identical apart from timestamps.

## Prediction about the remedy

- **PR-9.** A call-through is mechanically possible for both twins: neither takes an argument the
  hardened rig does not take, neither depends on its own working directory, and the one caller that
  supplies `CANARY_REQ` (`run-preconditions.sh`) already supplies exactly the digest-pinned file
  (`sha256 2a6621be…352154`, measured). I predict the hardened rig, called through, gives
  **21 PASS / 0 FAIL** on tenant `gerege`, i.e. the happy path is unchanged and only the attack
  paths move.
- **PR-10.** `t51-negative.sh` calls the script with **no** `CANARY_REQ`, so post-fix it gains one
  extra breach line. It is a negative control that already exits 1; I predict the exit status is
  unchanged and only the breach count rises.
