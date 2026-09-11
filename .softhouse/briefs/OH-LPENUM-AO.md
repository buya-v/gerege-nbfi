# OH-LPENUM-AO — grade every OBSERVED loanproduct enum member. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lpenum` (branch `feat/OHLPENUMao`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/loanproduct.md` — seams, vectors, drives, port functions with file:line.
2. `.softhouse/findings/F-2026-09-11-loanproduct-graded-coverage.md` §6 — the method and the first gap.

## The blind spot, and the method that sees it
The loanproduct seam decodes six stored-value vocabularies. **Coverage cannot tell which MEMBERS are
graded** — every member runs the same statements. OH-LPCOV-AL found period-frequency graded for stored
2/3/4 only, while the capture every such vector cites observes 0 (DAYS) and 1 (WEEKS) as well.

**The method:** for EACH of the six vocabularies,
1. list the option ids the committed capture(s) OBSERVE (e.g. `loanproducts-template-raw.json`
   `repaymentFrequencyTypeOptions`, and the sibling `*Options` lists — find the one per vocabulary via
   the existing vectors' `capture_ref` / citation, which the map lists);
2. list the stored values the committed vectors GRADE;
3. diff. Every observed-but-ungraded member is a vector to promote.

Write the full table (vocabulary × observed ids × graded ids × gap) into the vector notes or a short
finding `.softhouse/findings/F-2026-09-11-loanproduct-enum-members.md`.

## The task
Promote ONE vector per observed-but-ungraded member, each a near-copy of its vocabulary's existing
vector (e.g. `LP-freq-months.json` → `LP-freq-days.json`, `LP-freq-weeks.json`), citing the SAME
capture with its sha256. **Never promote a member the capture does not observe** — a port table entry
is not an observation.

Drives: the obvious one per vocabulary is an **ordinal shift** (decodes stored n as n+1, or the
iota-from-zero defect `parties-wrong-iota-ordinals` names). Register a drive only if a NEW vector kills
it that the old corpus did not — measure each WITHOUT and WITH your vectors, report every count. If the
existing four loanproduct drives already die on your new vectors, report that; do not duplicate them.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or **delete it
with the argument**. **Do not manufacture coverage.**

## Non-negotiables (a violation is a rejection)
- **Do not touch `.softhouse/guards/`** (12 pairs) or `.softhouse/conformance.sh` (census **17**).
- **Do not touch the progressive-recomputation kernel** (`calculator.go`, `repaymentperiod.go`,
  `schedulemodel.go`, …) — its fate is a driver decision recorded in the finding.
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- `capture_ref` must be a **JSON** capture record; `capture_sha256`, `citation`; **re-verify the hash after
  writing**. Never synthesise a value you did not observe.
- **One bounded context: `loanproduct`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with the line
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure, not the recorded decision.**
~400 iterations. **Commit by iteration 120**, then after each vocabulary.
**Write commit messages to a file and use `git commit -F <file>`. Never commit TASK.md.**
