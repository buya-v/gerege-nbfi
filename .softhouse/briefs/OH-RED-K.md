# OH-RED-K — cob, provisioning and origination: 17 vectors, one generic drive each

Worktree: `/Users/buv/oh-gerege-redk` (branch `feat/OHREDk`, from main `93f70645`)
Work ONLY in that directory.

## The finding you are acting on
```
cob           6 vectors   cob-wrong-shift-order          shifts every business-step order by one
provisioning  8 vectors   provisioning-wrong-blank-description
origination   3 vectors   origination-wrong-swap-status  swaps ACTIVE/PENDING
```
One defect per context cannot be the only way those ports can be wrong. The ledger context
carries eleven wrong implementations, each arguing a specific misreading of the Fineract
source with the line cited and the killing vector named. **That is the standard** — read the
`RegisterWrong` calls in `nexus/internal/apps/ledger/conformance/` before writing one.

## Seams worth attacking, but use your own judgement after reading each context's vectors

**cob** — the Close-of-Business step ORDER is already guarded by a whole-sequence shift.
What is not: an individual step transposed with its neighbour (a shift is not a swap and a
vector may catch one without the other); a step SKIPPED rather than reordered; the business
date advanced before rather than after the steps run.

**provisioning** — provisioning categories carry non-sequential stored ids and a percentage
applied to an outstanding balance. The percentage is a rounding surface: if a capture shows
a provision amount whose HALF_UP and HALF_EVEN results differ, that is a sixth independent
seam proving the tenant mode and worth more than anything else in this brief. Also: a
category matched by name instead of stored id; an age-bucket boundary read inclusive where
the oracle reads exclusive.

**origination** — status ordinals again (`ACTIVE`=300 class of defect), plus whatever the
three vectors actually grade. With only three vectors and two captures this context may
simply lack the observations; if so, say that rather than inventing drives it cannot see.

## Success is a NUMBER
For each drive: the measured `parity_fail`. A drive killing zero is a finding to report and
then resolve — promote a vector that sees it, or delete it with the argument.

## Measure, never assert
Every claim about a drive is a NUMBER you produced:
```
go run ./internal/apps/<ctx>/conformance/cmd/conformance -root <worktree> -impl <name>
```
Record the exact `parity_fail=N`. **A drive that kills ZERO vectors is a FINDING, not a
failure** — it means the store cannot see that defect. Report it, and then either promote a
vector that can see it, or DELETE the drive with the argument for why no vector ever could.
A permanently inert drive implies coverage that does not exist and is worse than no drive.
(Precedent: OH-CAP-I deleted two loanschedule drives after proving `generator.go:293-294`
refuses any request with more than one disbursement, so the discriminating input cannot
enter the graded domain at all.)

## Never synthesise a value you did not observe
Captures are at `.softhouse/capture/<ctx>/out/*-raw.json` (note the `out/`). Every vector
carries `capture_ref`, `capture_sha256` and a `citation` quoting the observed bytes;
re-verify the hash after writing. A stale hash is treated as a fabricated vector.
If a value you want is in no capture, that is an ORACLE GAP — say so.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, field, column or fixture,
  including intermediates. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3). Append-only (I-4).
- Rounding is **HALF_UP** (ordinal 4), precision 19, tz Asia/Ulaanbaatar. HALF_UP and
  HALF_EVEN differ ONLY on an exact half-minor-unit tie **whose truncated value is EVEN**
  (0.025 -> 0.03 vs 0.02; 0.035 -> 0.04 under both). Getting this backwards has already
  cost this programme a wrong brief.
- **Sub-minor-unit residue is REFUSED** — ratified 2026-09-09, gate G-19, DEC-2 predicate
  G-08. Never truncate, never round it away, and never write a parity vector for a residue
  value: no int64 of MNT minor units equals it.
- PostgreSQL only. **Never write to the `default` tenant.** SQL is READ-ONLY.
  `enable-business-date` is the only configuration row you may change.

## Do NOT pad
An earlier run was given a vector-count target and cloned to reach it: 18 files carrying 10
distinct (request, expect) pairs, eight thrown away. **You are measured on defects provably
caught.** Before adding a vector, confirm no existing vector grades that exact pair.

## Traps that have cost this programme time
1. `go test ./...` does not grade every context — some conformance packages have no test
   files. Always run the `cmd/conformance` binary.
2. `-root` is not universal: most binaries REQUIRE it, `loanschedule`'s REJECTS it.
3. `grep -c` prints 0 and exits 1 — never `grep -c ... || echo 0`.
4. Read exported names before using them; do not derive them from a directory name.

## The bar — green before you commit
```
cd nexus && go build ./... && go test ./...
gofmt -l .    # only loanschedule/contract/contract.go may appear; pre-existing
bash ../.softhouse/guards/ledger-invariants-compare.sh   # must say exactly 12 pairs
```
Run `gofmt -w` in the SAME command as any scripted patch.

## COMMIT EACH INCREMENT AS YOU FINISH IT
One prior agent exited with seven files uncommitted; another had its staged index recovered
from dangling blobs. Commit as you go. Do not merge to main, do not push.

## Report
- each drive registered or vector promoted, with its MEASURED before/after kill count
- any drive that kills zero, and whether you promoted a vector or deleted it, with why
- any ORACLE GAP, stated plainly
- the final `ledger-invariants-compare` line, verbatim
