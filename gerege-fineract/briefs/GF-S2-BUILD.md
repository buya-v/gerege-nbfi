# GF-S2 — prove a Gerege module builds into Fineract OUT OF TREE and loads at runtime

Worktree: `/Users/buv/gf-s2` (branch `feat/GF-S2`). Read `gerege-fineract/SPIKE-PLAN.md` and
`gerege-fineract/DECISIONS.md` first; nothing else in the repository concerns you.
**Write and commit ONLY under `gerege-fineract/extensions/` and `gerege-fineract/spike/s2-build/`.** Touch no other
folder. Never write into `/Users/buv/fineract` — it is the READ-ONLY reference source. Never touch the standing
reference instance (port 8443) or any `tierd-*` / `gf1-*` container. The driver pushes; never push.

## Why
The Fineract-core road only works if Gerege's capabilities live OUTSIDE Fineract's core code, so Fineract upgrades stay
cheap. Fineract supports this: its `settings.gradle` (lines 85-94) includes every `custom/<company>/<category>/<module>`
directory, and `:custom:docker` builds an image containing them. See the worked example in `/Users/buv/fineract/custom/acme`
(read it; do not edit it). This step proves the path end to end with a minimal Gerege module.

## Steps — commit after each (`git commit -F <file> </dev/null`, message file inside the worktree)
1. **Disposable source copy.** `git clone /Users/buv/fineract gerege-fineract/.work/fineract-src` and check out
   `426a23544`. `.work/` is gitignored and never committed. Record the commit in `spike/s2-build/OWNER.md`.
2. **The module, in the repository.** Create `gerege-fineract/extensions/gerege/client/nationalid/` in the acme
   layout: a `build.gradle`, and Java under package `mn.gerege.fineract.client.nationalid`.
   - a Spring auto-configuration class (registered the way the acme starters register theirs);
   - a **no-op COB business step** named `GEREGE_NOOP`, modelled on `custom/acme/loan/cob/.../AcmeNoopBusinessStep.java`,
     so its presence is visible through Fineract's API;
   - a plain validator class `MongolianNationalId`: exactly 10 characters, 2 Cyrillic letters then 8 digits, validated
     structurally (the check digit is unpublished — do NOT invent one), with JUnit tests for valid, wrong-length,
     Latin-letter and non-digit cases. It is NOT hooked into client creation yet; that is S3.
3. **Build.** Write `spike/s2-build/build.sh`. It copies `extensions/gerege` into `.work/fineract-src/custom/gerege`,
   then builds inside Docker with the local image `eclipse-temurin:21-jdk` (the host has no Java). Mount the source
   copy, give Gradle a bounded heap (`-Xmx3g`), and run the module's tests plus the custom image build (find the
   task in `custom/docker/build.gradle`, e.g. `jibDockerBuild`) to produce the image `fineract-gerege:spike`. Record
   the build time, the image size and the test results in `OWNER.md`. If the build fails, record the exact error and
   stop there. That is a result.
4. **Load.** Write `spike/s2-build/compose.yml`: containers `gf2-db` (`postgres:18.3`) and `gf2-app`
   (`fineract-gerege:spike`), host port **8446**, tenant `gspike2`, Asia/Ulaanbaatar, rounding mode 4 (copy the shape
   of `.softhouse/capture/tierd-feasibility/throwaway/docker-compose.tierd.yml`; do not edit it). Start it, wait for
   health with a bounded loop, then prove the module loaded: the COB business-step API lists `GEREGE_NOOP` (find the
   endpoint in the pinned source READ-ONLY and cite file:line), and the startup log shows the auto-configuration.
   Save the responses under `spike/s2-build/evidence/` with a sha256 `manifest.json`.
5. **Tear down and report.** `docker compose -f spike/s2-build/compose.yml down -v` (only `gf2-*`). In `OWNER.md`:
   - what built;
   - what loaded;
   - whether ANY file outside `custom/` had to change in the Fineract copy (target: none; list any with a reason);
   - how a Fineract version bump would work: re-clone at a newer commit and re-run `build.sh`.

## Rules
- Every command in the FOREGROUND with a bound; never `&`, `jobs`, `wait`, or `sleep` over 60 seconds. A long Gradle
  build runs in the foreground inside `docker run --rm` with a timeout.
- Never create or edit `AGENTS.md`. Never bypass a git hook (`-c core.hooksPath`, `--no-verify`). If a commit does not
  return, STOP and say so.
- No money logic in this step. PostgreSQL only; **Oracle Database is prohibited.**
- If a step fails, record it with the evidence, tear down what you started, and finish.
- About 300 iterations. Commit the module skeleton by iteration 100.
