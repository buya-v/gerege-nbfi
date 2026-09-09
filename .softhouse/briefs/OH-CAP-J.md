# OH-CAP-J — charges has 10 vectors and cannot see its own rounding

Worktree: `/Users/buv/oh-gerege-capj` (branch `feat/OHCAPj`, from main `732a30be`)
Work ONLY in that directory.

## The measurement you are acting on
```
charges-wrong-percent-one-scale-short   FAIL 3 of 10
charges-wrong-percent-truncating        FAIL 1 of 10
charges-wrong-rounding-half-even        PASS 0  <-- INERT
charges-wrong-validation-skipped        PASS 0  <-- INERT
```
Reproduce it first (charges' binary REQUIRES `-root <worktree>`).

`charges-wrong-rounding-half-even` killing nothing means **no charges vector lands on a
rounding tie.** Charges is a MONEY context. The five seams that prove the tenant's HALF_UP
are loanschedule, ledger, loan, branch and shares — charges is not among them, and this
measures why. A percentage fee is a rounding surface; it should be able to prove it.

## Your task
1. **The rounding tie.** A percentage charge is `base x rate`, rounded to the minor unit.
   Find or construct a (base, rate) pair whose exact product lands on an exact half minor
   unit with an ODD truncated value — the only case where HALF_UP and HALF_EVEN differ.
   Observe the oracle's answer. Promote it. Then re-measure the drive.
2. **Validation.** `charges-wrong-validation-skipped` kills nothing, so no vector grades a
   refusal. `.softhouse/capture/charges/out/` already holds
   `XR-01-fee-before-disbursement-HTTP403.json` — an observed REFUSAL. If no vector grades
   it, that is the gap: promote the refusal, with its HTTP status and error code as
   observed.

## Look before you capture
charges has **658 capture files** under `.softhouse/capture/charges/`, including `out/`,
`req/`, `fc/`, `control/` and an `attested/` subtree. A discriminating observation may
already be on disk. Search first; capture only what is genuinely absent.

## Success is a NUMBER, and it may be zero
Report each targeted drive's kill count BEFORE and AFTER. If no (base, rate) the oracle
will accept produces a tie, say so and show the arithmetic you tried — then DELETE the
inert drive with that argument rather than leaving it implying coverage that is not there.

## The rule that outranks everything else here
**Never synthesise a value you did not observe from the oracle.** If you cannot make the
oracle produce a discriminating observation, the honest outcome is a report saying so.
A fabricated expect cell is the one unrecoverable failure in this programme.

## Non-negotiables (a violation is a rejection, not a discussion)
- Money is **integer minor units**. No float in any money path, struct field, column, API
  field, or test fixture — including intermediates. MNT = ISO 496, minor unit 2.
- Balances are **derived, never written** (I-3). Append-only (I-4).
- Rounding is **HALF_UP** (ordinal 4), precision **19**, tz Asia/Ulaanbaatar.
- PostgreSQL only. **Never write to the `default` tenant.** SQL is READ-ONLY, for
  verification. `enable-business-date` is the only configuration row you may change.
- The oracle is Fineract at `https://localhost:8443/fineract-provider/api/v1`
  (self-signed TLS, use `curl -k`). It is UP — probe before assuming.

## Every new vector must carry provenance
`capture_ref`, `capture_sha256`, and a `citation` quoting the observed bytes. Follow the
shape of an existing vector in the same context exactly. Re-verify the sha256 after
writing — a stale hash is treated as a fabricated vector.

## Do NOT pad
An earlier run was told to reach a vector count and reached it by cloning: 18 vectors
carrying 10 distinct (request, expect) pairs. Eight were thrown away. **You are measured
on defects provably caught, never on file count.** Before adding a vector, confirm no
existing vector already grades that exact (request, expect) pair.

## Traps that have already cost this programme time
1. **`go test ./...` does not grade every context.** Some conformance packages have no test
   files; the harness is the `cmd/conformance` binary. Always run the binary.
2. **`-root` is not universal.** Most `cmd/conformance` binaries REQUIRE `-root <checkout>`;
   `loanschedule`'s REJECTS it. The two error texts differ. Check per binary.
3. **`grep -c` prints 0 and exits 1.** Never write `grep -c ... || echo 0` — it yields
   "0\n0" and breaks every later arithmetic expression.
4. **Read exported names before using them.** Do not derive an identifier from a directory.

## The bar — green before you commit
```
cd nexus && go build ./... && go test ./...
gofmt -l .        # only loanschedule/contract/contract.go may appear; pre-existing
bash ../.softhouse/guards/ledger-invariants-compare.sh   # must say exactly 12 pairs
```
Run `gofmt -w` in the SAME command as any scripted patch.

## COMMIT EACH INCREMENT AS YOU FINISH IT
One prior agent exited with seven files uncommitted; another was stopped and its staged
index had to be recovered from dangling blobs. Commit as you go. Do not merge, do not push.

## Report
- what you captured, and the exact command that reproduces it
- each vector added, its provenance, and the drive it moves off zero
- the BEFORE and AFTER kill count of every drive you targeted
- anything you could NOT make the oracle show, stated plainly
- the final `ledger-invariants-compare` line, verbatim
