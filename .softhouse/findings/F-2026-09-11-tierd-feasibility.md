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
