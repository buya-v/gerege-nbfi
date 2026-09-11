# OH-PROVCRIT-AJ — grade the provisioning age-band rule: add a criteria seam. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-provcrit` (branch `feat/OHPROVCRITaj`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/provisioning.md` — seams, vectors, drives, port functions with file:line.
2. `.softhouse/findings/F-2026-09-11-provisioning-graded-coverage.md` §4.1 and §5 — the target, the
   observations, and exactly why no existing seam can carry it.

## The target
`ReserveRate` [`nexus/internal/apps/provisioning/criteria.go:58`] and `Matches` [`:29`] map a loan's
overdue age to the provisioning band — category, reserve percentage, liability and expense accounts —
porting the oracle's join `pcd.min_age <= overdueInDays AND overdueInDays <= pcd.max_age`
[`ProvisioningEntriesReadPlatformServiceImpl.java:75-77`]. **This decides regulatory reserve money**,
and the graded corpus never reaches it: the reserve seam is handed the ALREADY-MATCHED percentage.

## The observations — committed, and the driver checked them against TODAY's oracle
* Definitions: `.softhouse/capture/provisioning/out/CRI-02-criteria-1-raw.json` (sha256 `fe372a96…`).
  **Driver-verified 2026-09-11:** read-only `GET /provisioningcriteria/1` on the live oracle matches it
  exactly — name, all four definitions, product 2. Cite it.

      STANDARD      [0, 29]      1.0%   liability 2  expense 4
      SUB-STANDARD  [30, 59]    25.0%
      DOUBTFUL      [60, 89]    50.0%
      LOSS          [90, 36500] 100.0%

* The oracle's DECISIONS: `.softhouse/capture/provisioning/out/ENT-04-entry-loan-products-raw.json`
  (sha256 `96d596c2…`, already cited by PV-05..09): overdue 0 → STANDARD, 31 → SUB-STANDARD,
  62 → DOUBTFUL, 92 → LOSS.

## The task — ONE property
> **An overdue age selects the ONE definition whose closed band [minAge, maxAge] contains it.**

1. Add a seam (e.g. `provisioning-criteria-band`) and a capability in the graded domain, following
   exactly how the existing two seams are declared (`.softhouse/capabilities-provisioning.json`,
   `conformance/vector.go:99-135`, `admit.go`). The request carries the definitions + one overdue age;
   the expect carries the selected category, percentage (micro-per-cent: 1.0 → 1000000) and accounts.
2. Promote FOUR vectors, one per observed decision (0, 31, 62, 92). Each cites CRI-02 as `capture_ref`
   and ENT-04 (path + sha256) for the observed decision.
3. Drives, each discriminated by these four:
   * **half-open band** (`overdue < maxAge`) — only if an observed age sits ON a boundary; **check: none
     of 0/31/62/92 is a maxAge, and 0 is a minAge**. If only 0 discriminates it, say so; if nothing does,
     do not register it and record what capture would (an age of exactly 29, 59 or 89).
   * **first band always** / **last band always**;
   * **bands off by one** (selects the next band up).

Coverage of `ReserveRate` and `Matches` must move off 0.0% from the committed-store test (`-count=1`).
## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or **delete it
with the argument**. **Do not manufacture coverage.** Measure each drive against the store WITHOUT
your vector(s) and WITH them; report every count.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. **HALF_UP**, ordinal 4, precision 19.
- **Do not touch `.softhouse/guards/`** (12 pairs) or `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- `capture_ref` must be a **JSON** capture record (the wire-float guard refuses anything else — a
  psql dump cannot be cited); `capture_sha256`, `citation`; **re-verify the hash after writing**.
  Never synthesise a value you did not observe.

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with the line
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure, not the recorded decision.**
Run it EARLY and again before your last commit. ~400 iterations. **Commit by iteration 120.**
**Write commit messages to a file and use `git commit -F <file>`. Never commit TASK.md.**
**One bounded context: `provisioning`.**
