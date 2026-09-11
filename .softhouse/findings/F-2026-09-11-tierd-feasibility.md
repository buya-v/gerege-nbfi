# F-2026-09-11 — Tier D feasibility: FIRST ATTEMPT, partial (salvaged by the driver)

**Status: OPEN — question 1 partly answered, questions 2-5 unanswered.** `OH-TIERD-BG` stopped at
257 events without committing; the driver salvaged its rig and wrote this record.

## What was learned
1. **The e2e runner needs Fineract's Feign client SDK built from source.** `fineract-e2e-tests-core`
   depends on `fineract-client-feign`, generated from the OpenAPI spec and compiled with Gradle — the
   run started `./gradlew` on the PINNED checkout (`/Users/buv/fineract`). The build ran for minutes and
   **failed: "Gradle build daemon disappeared unexpectedly"** — consistent with memory pressure on a
   16 GB host that was also running the standing oracle, another agent run and unrelated containers.
2. **The build wrote gitignored output into the pinned checkout** (`fineract-client-feign/build`,
   `fineract-e2e-tests-core/build`). HEAD stayed `426a23544` and `git status --porcelain` stayed empty,
   so no capture rig's precondition broke — but the checkout is read-only by rule. **The driver deleted
   both directories** (they were newer than the brief; older gitignored build dirs were left alone).
3. **The run wrote a throwaway rig** (`.softhouse/capture/tierd-feasibility/throwaway/`): compose file,
   env, preflight, isolation guard, teardown — copied from T305's, tenant named `tierd`, port 8444, no
   published DB port. **It was never started**: no container was created (driver checked `docker ps -a`).
4. The run's last action was an unbounded `find /Users/buv …`, which never returned.

## What the next attempt must do differently
* Build the SDK in a DISPOSABLE COPY of the pinned checkout (e.g. `cp -a` or a `git worktree` of
  `426a23544` outside `/Users/buv/fineract`), never in the pinned tree.
* Build only the two modules needed, `--no-daemon`, with a bounded JVM heap, and nothing else heavy running.
* Never run `find` over the home directory.

---

## SECOND ATTEMPT (OH-TIERD2-BH) — the replay WORKS; salvaged by the driver

`OH-TIERD2-BH` did not finish its write-up: at 430 events its model calls began failing with
`DeepseekException "Insufficient Balance"` (the DeepSeek account reached −0.11 USD; the fallback
did not engage because the provider answers a 400, not a retriable error). The driver recorded
what its evidence establishes. **Questions 1–3 are answered positively; 4 and 5 are not.**

1. **Harness — yes, on this host, with a recipe.** The Feign client SDK and the runner build in a
   JDK container (`eclipse-temurin:21-jdk`) over a disposable `cp` copy of the pinned checkout
   (`/Users/buv/fineract-tierd`, not a git worktree; the pinned tree is untouched), with
   `--no-daemon --max-workers=1`, a bounded heap (`-Xmx3g -XX:+UseSerialGC`) and a named Gradle
   cache volume. Six builds failed first (one in generated `StandingInstructionsApi.java`
   with missing symbols) before `BUILD SUCCESSFUL`.
2. **Replay — yes, and fast.** Against the throwaway (same image `e596339626bf`, tenant `tierd`,
   `Asia/Ulaanbaatar`, rounding mode 4), **12 scenario executions from
   `LoanUpdateApprovedAmount.feature` (UC1, UC3, UC5_1, UC5_2, UC6 ×2, UC7_1, UC7_2, UC8_2, UC8_3 and
   two over-applied variants) all PASSED — every step — in 0.5–1.5 s each** (allure results in the
   disposable copy). Passing means the oracle, replayed, reproduced the `.feature` file's own
   expected values.
3. **Capture — yes, but coarse.** A Feign debug hook (`-Dfineract.feign.debug=true`) wrote every
   request and response: `feign-s1.log` 243 MB (1,809 exchanges, 24 schedule read-backs) and
   `feign-uc6.log` 147 MB. Most of the volume is the runner's global initializer seeding the
   tenant. A usable pipeline must extract the per-scenario loan read-backs from that stream.
4. **Mapping — NOT ANSWERED.** Whether those read-backs fit the `loanschedule`/`loan` vector shapes
   was being examined when the run died.
5. **Scale and cost — partly.** Per-scenario replay is ~1 s after a one-off initializer; the cost is
   the one-off SDK build and the log extraction, not the replay.

**Isolation, driver-verified after the run died:** tenant `gerege`'s last writes are 07:05:39Z
(OH-CHGCAP-BD's final repayment and waive, commands 234–235), before Tier D began; `default` has
had no write since 2026-09-03. The rig's own teardown reported "THE STANDING ORACLE MOVED" on every
counter — a false alarm: its baseline file lived in the first attempt's deleted worktree, so it
compared against empty values. Every `tierd-*` container was removed. The pinned checkout was
rebuilt into once more by the STALE first run after the first cleanup; the driver removed that
output again (HEAD `426a23544`, porcelain empty throughout).

**Recommendation (driver):** Tier D is feasible. The next run — after the model credit is restored —
answers question 4 from the existing `feign-*.log` evidence without re-running anything: extract one
scenario's loan read-back and map it onto a `loanschedule` vector, or say which cells cannot map.
The disposable copy (997 MB) is kept for it.
