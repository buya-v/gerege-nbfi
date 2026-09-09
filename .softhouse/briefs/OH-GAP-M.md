# OH-GAP-M — answer "is this closable?" for the three thinnest contexts

Worktree: `/Users/buv/oh-gerege-gapm` (branch `feat/OHGAPm`)
Work ONLY in that directory.

## This task is different: A DOCUMENTED GAP IS A SUCCESSFUL OUTCOME

You are NOT being asked to raise a vector count. You are being asked to settle three
questions and produce an argument for each. "This cannot be closed, and here is the proof"
is a first-class result — it retires a question permanently instead of leaving it to be
rediscovered every few weeks.

The precedent is OH-CAP-I. It was dispatched to close two loanschedule seams with new
captures. It proved instead that `generator.go:293-404` refuses any request with more than
one disbursement, so the discriminating input CANNOT ENTER the graded domain, deleted both
drives, and removed dead branches from money code. That was a better outcome than the
captures it was asked for, and it is the model for this task.

## The three questions

### 1. origination — 3 vectors, 2 captures, one generic drive
`origination-wrong-swap-status` (FAIL 2 of 3) is all that guards it. Is that because nobody
wrote more drives, or because two captures cannot support more?
**Settle it.** Read the two captures and the three vectors. If a second defect shape IS
observable, register and measure it. If the observations genuinely do not exist, say so
with the specific list of what a capture would have to contain — and then say whether the
live oracle could produce it, since it is up.

### 2. collateral — the ScaledInt valuation
The port's `ScaledInt` valuation arithmetic is believed to have NO observable oracle
counterpart: no API read-back computes it. **Verify or refute that.** Read the port's
valuation path, then search every collateral capture and, if needed, ask the live oracle
whether any endpoint returns a computed valuation. If none does, record it as a permanent
ORACLE GAP with the endpoints you checked, so nobody re-opens it.

### 3. investor — the purchase price
The transfer purchase price (97.25% of an outstanding balance) appears in no capture. A
previous agent queried the oracle database directly and was mid-investigation. **Finish
it.** Does any endpoint expose a settled transfer amount? If yes, capture it and promote a
vector. If no, record the gap with the endpoints and tables you checked.

## Rules of evidence
- **Cite source lines** for any claim about what the port or the oracle refuses or computes.
  A claim without a file:line is not an argument.
- **SQL is READ-ONLY.** Never write to the `default` tenant. `enable-business-date` is the
  only configuration row you may change.
- **Never synthesise a value you did not observe.** Captures are at
  `.softhouse/capture/<ctx>/out/*-raw.json`. Every vector carries `capture_ref`,
  `capture_sha256` and a citation; re-verify the hash after writing.
- The oracle is Fineract at `https://localhost:8443/fineract-provider/api/v1`
  (self-signed TLS, `curl -k`). It is UP — probe before assuming.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float anywhere in a money path, including
  intermediates. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3); append-only (I-4).
- Rounding is **HALF_UP** (ordinal 4), precision 19, tz Asia/Ulaanbaatar. HALF_UP and
  HALF_EVEN differ ONLY on an exact half-minor-unit tie **whose truncated value is EVEN**
  (0.025 -> 0.03 vs 0.02; 0.035 -> 0.04 under both).
- **Sub-minor residue is REFUSED** — ratified 2026-09-09, gate G-19, DEC-2 predicate G-08.
  Never write a parity vector for a residue value; no int64 of MNT minor units equals one.
- PostgreSQL only.

## Every drive you register must be MEASURED
```
go run ./internal/apps/<ctx>/conformance/cmd/conformance -root <worktree> -impl <name>
```
Record the exact `parity_fail`. **A drive that kills zero must not be committed** — promote
a vector that sees it, or do not register it. The store currently has 65 drives and NOT ONE
that kills nothing; do not be the run that breaks that.

## The bar — green before you commit
```
cd nexus && go build ./... && go test ./...
gofmt -l .      # only loanschedule/contract/contract.go may appear; pre-existing
bash ../.softhouse/guards/ledger-invariants-compare.sh    # must say exactly 12 pairs
```
Run `gofmt -w` in the SAME command as any scripted patch.

## COMMIT WITH A REAL MESSAGE AS YOU GO
Commit each increment as you finish it. **If you make a diagnostic or probe commit, AMEND
IT before you move on** — a previous agent left 373 lines of real work under the message
"probe-commit-hang". Do not merge to main, do not push.

## Report — this is the deliverable
For each of the three questions: **CLOSABLE** (with the vector/drive and its measured kill
count) or **ORACLE GAP** (with the endpoints, tables and source lines you checked, and what
an observation would have to contain). Then the final `ledger-invariants-compare` line.
