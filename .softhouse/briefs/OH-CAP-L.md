# OH-CAP-L — collateral and investor are the two thinnest contexts in the programme

Worktree: `/Users/buv/oh-gerege-capl` (branch `feat/OHCAPl`, from main `93f70645`)
Work ONLY in that directory.

## The finding you are acting on
```
collateral   2 vectors   9 captures on disk   1 generic drive
investor     1 vector    4 captures on disk   1 generic drive
```
Thinnest coverage in the programme, and both have unpromoted observations sitting on disk.

## collateral — captures already present
```
collateral-products-pre-raw.json     collateral-products-post-raw.json
collateral-product-raw.json          collateral-product-readback-raw.json
collateral-codevalue-raw.json
client-collateral-raw.json           client-collateral-readback-raw.json
loan-collateral-raw.json             loan-collateral-readback-raw.json
```
Note the shape: **pre/post and raw/readback PAIRS**. A before/after pair is a DELTA, and a
delta discriminates where a single read cannot — this is how the branch cashier summary was
pinned as a derivation rather than a re-read. Start there.

**A known limit, stated so you do not waste the run on it:** the port's `ScaledInt`
valuation arithmetic has no observable oracle counterpart — no API read-back computes it.
If that holds after you look, record it as an ORACLE GAP and grade what IS observable
(product identity, code values, the client/loan association rows, quantity and unit price
as stored).

## investor — the known gap
Its one vector pins the transfer READ. The purchase-price computation — 97.25% of an
outstanding balance — appears in NO capture, which was diagnosed as a CAPTURE gap, not a
promotion gap. Four captures exist:
```
transfer-read-loan-1-raw.json   transfer-read-loan-6-raw.json
transfer-read-no-param-raw.json transfer-search-raw.json
```
First promote whatever those four DO support that is not already graded. Then, and only
then, decide whether an endpoint exists that exposes a settled transfer amount; if one
does, capture it. If none does, say so plainly — that closes the question either way.

## Success is a NUMBER
Distinct facts graded and defects provably caught. Not file count.

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
