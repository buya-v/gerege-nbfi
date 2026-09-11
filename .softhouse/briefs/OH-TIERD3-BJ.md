# OH-TIERD3-BJ — Tier D question 4: do the replayed read-backs map onto our vectors? NO ORACLE, NO REPLAY.

Worktree: `/Users/buv/oh-gerege-tierd3` (branch `feat/OHTIERD3bj`)
Work ONLY in that directory. **A run works ONLY in its own worktree.** The driver pushes; never exercise the
push gate. **Model credit is limited — be direct.** **Start no container. Build nothing. Replay nothing.**

## Read first
1. `.softhouse/findings/F-2026-09-11-tierd-feasibility.md` — both attempts; questions 1–3 answered yes.
2. `.softhouse/maps/loanschedule.md` and `.softhouse/maps/loan.md` — the vector shapes.

## The evidence already on disk (read-only)
`/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-uc6.log` (147 MB) and `feign-s1.log`
(243 MB): every HTTP exchange of the replays (Feign debug format), incl. 24 schedule read-backs in s1;
allure results in `…/build/allure-results/` (12 passed executions). **Do not load a whole log into the
terminal** — grep/awk for the lines you need.

## The task
1. From `feign-uc6.log`, extract ONE loan's full detail/schedule read-back (the response body of
   `GET /loans/{id}?associations=…` or the schedule endpoint) for the UC6 scenario, and the request bodies
   that created that loan. Save them as JSON under `.softhouse/capture/tierd-feasibility/uc6/` with an
   OWNER.md (the throwaway instance, tenant `tierd`, and that it is NOT tenant `gerege`).
2. Map it onto the nearest existing vector shape — `loanschedule` parity vectors (template:
   `.softhouse/vectors/loanschedule/P-03-disbursement-on-repayment-due-date.json`) or the `loan` schedule
   seams. Cell by cell: which map directly, which need a transform, which cannot map and why (e.g. the
   loanschedule seam is the embeddable generator, not the REST read-back).
3. Answer question 5 (cost) from the evidence: bytes per scenario, extraction effort, and what a bulk
   extractor would have to do. Then a RECOMMENDATION: a bulk pipeline, a hand-picked subset, or not worth it.

Append all of it to the finding under a "## THIRD PASS (OH-TIERD3-BJ)" heading. **Promote NO vector** —
provenance from a throwaway tenant needs a driver decision first; say what that decision is.

## Non-negotiables
- Money in integer minor units in anything you write. **Do not touch `.softhouse/guards/`,
  `.softhouse/conformance.sh`, `nexus/`, or `.softhouse/maps/`.** "The oracle" is the Fineract reference;
  **Oracle Database is prohibited.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~200 iterations. **Commit the extraction by
iteration 60**, the finding after. **`git commit -F <file>`. Never commit TASK.md.**
