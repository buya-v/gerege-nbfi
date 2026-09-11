# OH-TIERD-BG — Tier D FEASIBILITY: can Fineract's own e2e scenarios become observed vectors in bulk?

Worktree: `/Users/buv/oh-gerege-tierd` (branch `feat/OHTIERDbg`)
Work ONLY in that directory. **A run works ONLY in its own worktree.** The driver pushes; never exercise the
push gate. **This is a FEASIBILITY STUDY: its deliverable is a finding, plus at most a small proof capture.
Promote NO vector. Write no `.go`.**

## The decision behind it (Buyan, 2026-09-11)
Tier D ("Fineract's ~321k test LOC and e2e suites are converted into golden vectors, not ported as tests",
CLAUDE.md) has not started. `fineract-e2e-tests-runner` holds **137 `.feature` files (~200k lines; 65 carry
repayment schedules)** whose steps assert concrete schedule / transaction / balance tables. Buyan approved
ONE run to find out whether replaying them against a Fineract instance and capturing the results is a
practical way to produce observed vectors at scale. **An expected table printed in a `.feature` file is
NOT an observation** — only what an oracle instance returns when the scenario is replayed is.

## WHERE IT MAY RUN — read this twice
* **NEVER against the standing oracle's tenants.** Not `gerege` (the suite creates products, clients and loans
  by the hundred and would bury the tenant every committed capture reads), and **never `default`**.
* Run it, if at all, on a **THROWAWAY instance built from the SAME image** the standing oracle runs — the
  pattern T305 established and documented: `.softhouse/capture/t305-openingbalance-accepting-side/throwaway/`
  (`capture.sh`: image-id check, a seeded tenant at `Asia/Ulaanbaatar` with rounding-mode 4 HALF_UP, the
  standing oracle's counters read before / during / after to PROVE it was untouched, teardown in the same
  run). **Copy that rig's discipline exactly.** If the throwaway cannot be built, stop and report why.
* "The oracle" is the Fineract reference; **Oracle Database is prohibited.** PostgreSQL only.

## The questions — answer each with evidence
1. **Harness.** How is the e2e runner configured (base URL, tenant, credentials, business date, what it seeds
   itself)? Can it be pointed at a throwaway instance's seeded tenant? `file:line` for every claim, from
   `/Users/buv/fineract/fineract-e2e-tests-*` (pinned `426a23544`, read-only).
2. **Replay.** Pick **three** schedule-bearing scenarios from different feature files (prefer
   progressive-schedule ones — the `loanschedule` context grades progressive schedules). Can one scenario be
   replayed in isolation, and how long does it take?
3. **Capture.** For each replayed scenario, can the actual oracle responses (schedule / transactions) be
   saved as JSON records alongside the request bodies? Does the replay reproduce the `.feature` file's own
   expected table? (A mismatch is a finding, not a failure.)
4. **Mapping.** Would those captures fit the existing `loanschedule` (or `loan`) vector shapes, or need new
   seams? Which rows/cells map, which do not.
5. **Scale and cost.** Rough throughput, the blockers, and a recommendation: a bulk pipeline, a hand-picked
   subset, or not worth it — with the reasons.

If everything goes well, commit the three proof captures under `.softhouse/capture/tierd-feasibility/`
(JSON + request bodies + an OWNER.md naming the throwaway instance and the untouched-oracle proof).

**Write `.softhouse/findings/F-2026-09-11-tierd-feasibility.md`** — the five answers, then the recommendation.

## Non-negotiables
- The standing oracle's tenants must be untouched — prove it with before/after counters as T305 did.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/`, or `.softhouse/maps/`.**
- Money in integer minor units in anything you write; never a sub-minor value.

## The budget and how to commit
~400 iterations. **Commit the finding's first draft by iteration 150** (a half answer committed beats a full
one lost); commit captures as they land. **`git commit -F <file>`. Never commit TASK.md.** Tear down every
container you start.
