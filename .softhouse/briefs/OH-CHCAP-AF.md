# OH-CHCAP-AF — grade the percentage-fee cap clamp. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-chcap` (branch `feat/OHCHCAPaf`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/charges.md` — every seam, vector, drive and port function with file:line.
2. `.softhouse/findings/F-2026-09-11-charges-graded-coverage.md` §5 — the target, with every figure.

## The target
`charges.MinimumAndMaximumCap` [`nexus/internal/apps/charges/money.go:86`] clamps a percentage fee
into `[minCap, maxCap]`. The committed-store test shows its two cap branches (`money.go:87-89` raise to
minCap, `:90-92` lower to maxCap) are reached by **no vector** — all 12 charges vectors omit
`min_cap_minor` / `max_cap_minor`.

## The observations — committed, verify every figure against the files
`.softhouse/capture/charges/out/t51/` (tenant gerege, pinned jar 426a23544, HALF_UP — see
`preconditions-T51.txt`), PERCENT_OF_AMOUNT (calc type 2) on principal 1,200,000.00:

    T51-TR-10-c2-maxcap-raw.json   1.2345% -> 14,814.00, maxCap 5000  -> fee 5000.00   (sha256 e72d8f14…)
    T51-TR-12-c2-mincap-raw.json   0.1%    ->  1,200.00, minCap 8000  -> fee 8000.00   (sha256 6340a095…)

Charge definitions: `req-create-c2-maxcap.json`, `req-create-c2-mincap.json` beside them; requests in
`.softhouse/capture/charges/req/`. The `c5` cases (calc type 5, per-instalment) exist too — **use them
only if they map onto an existing charges seam without inventing inputs; otherwise say why not.**

## The task — ONE property
> **A percentage fee below minCap is raised to minCap; above maxCap it is lowered to maxCap.**

Promote TWO vectors (max, min). Drives, each discriminated here:
* **ignores both caps** — max case reads 1481400, min case 120000.
* **caps swapped** (min treated as max) — both cases move.
* **clamps before rounding / on the rate instead of the fee** — only if the figures discriminate it;
  otherwise do not register it.

Coverage must show both cap branches reached from the committed-store test (`-count=1`), or say why not.

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
**One bounded context: `charges`.**
