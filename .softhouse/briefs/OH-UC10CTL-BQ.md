# OH-UC10CTL-BQ — the control: does LoanRepaymentSchedule UC10 fail in EUR too? CAPTURE ONLY.

Worktree: `/Users/buv/oh-gerege-uc10ctl` (branch `feat/OHUC10CTLbq`)
Work ONLY in that directory (plus the disposable copy `/Users/buv/fineract-tierd`). **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate. The overnight queue is running a `loan` Go run beside
you; you touch no Go and no vector.

## Read first
1. `.softhouse/findings/F-2026-09-11-tierd-repsched-mnt-uc10.md` — in MNT, UC10 (feature line 824) period 2 of loan
   10 came back balance 43477 / principal 42973 / interest 1129 against the feature's expected 43476 / 42974 / 1128.
2. `.softhouse/capture/tierd-feasibility/uc6-mnt/currency-seed-mnt.diff` — the five constants that made the copy MNT.
3. `.softhouse/capture/tierd-feasibility/repayment-schedule-mnt/run-repsched-mnt.sh` and the rig — reuse both.

## The question — ONE
**Is the one-unit split caused by the MNT re-seed, or does the pinned build disagree with its own test in EUR too?**

1. In the disposable copy ONLY, revert the five currency constants to `EUR` (reverse exactly the recorded diff's
   currency hunks; leave the build/capture plumbing). Rebuild only what that touches.
2. `preflight.sh`, throwaway up, replay **UC10 alone** with the Feign capture on, `down.sh`.
3. Record: PASSED or FAILED in EUR, and if failed, the actual vs expected cells of the failing step.
4. **Restore the MNT constants** and confirm with `git -C /Users/buv/fineract-tierd diff` that the copy is back to
   the MNT state recorded in `currency-seed-mnt.diff`.
5. Append the result and its meaning to the UC10 finding:
   * **fails identically in EUR** → the pinned build disagrees with its own upstream test; the oracle's output (not
     the feature table) is what this program grades; record that the test is not a trustworthy expectation at this pin.
   * **passes in EUR** → the currency changes the arithmetic somewhere; UC10's MNT output must not be promoted until
     the cause is found; name the next step.

Commit the EUR run's log, result, `teardown-isolation.txt` and the finding under
`.softhouse/capture/tierd-feasibility/uc10-eur-control/`.

## Non-negotiables
Standing tenants untouched (proven by the rig's fail-closed baseline and teardown). Never write into
`/Users/buv/fineract`. Tear down every `tierd-*` container. Never `find` over `/Users/buv`. **Do not touch `nexus/`,
`.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, or `.softhouse/maps/`.**

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~200 iterations. **`git commit -F <file>`. Never commit TASK.md.**
