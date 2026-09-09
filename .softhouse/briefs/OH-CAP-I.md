# OH-CAP-I — two loanschedule defects change money and NOTHING can see them

Worktree: `/Users/buv/oh-gerege-capi` (branch `feat/OHCAPi`, from main `732a30be`)
Work ONLY in that directory.

## The measurement you are acting on
All four loanschedule wrong-drives were measured yesterday against the 50-vector store:
```
loanschedule-wrong-days-in-year-365          FAIL 45 of 50
loanschedule-wrong-half-even                 FAIL  5 of 50
loanschedule-wrong-round-segments-then-sum   PASS  0  <-- INERT
loanschedule-wrong-due-date-exclusive        PASS  0  <-- INERT
```
Reproduce that yourself first; do not take it on trust:
```
cd nexus && go run ./internal/apps/loanschedule/conformance/cmd/conformance \
  -impl loanschedule-wrong-round-segments-then-sum
```
(NOTE: loanschedule's binary REJECTS `-root`. Others require it.)

**Both inert drives change money.** Fifty vectors — the largest corpus in the programme —
cannot tell a correct port from either one. Your job is to close that, with observations.

## The two seams
1. **Aggregation order** — `roundSegmentsThenSum`. Rounding each segment before summing
   versus summing then rounding. These differ only when at least two segments each carry a
   fractional minor unit whose individual roundings do not sum to the rounding of the sum.
   You must construct a loan whose schedule HAS such a period.
2. **Period boundary** — `registrationBoundaryDueExclusive`. Inclusive versus exclusive due
   date. This differs only when an event lands exactly ON a due date. Construct that.

Read `nexus/internal/apps/loanschedule/wrongdrives.go` and `emi.go` for exactly where each
variant branches — the branch condition tells you what input reaches it.

## How to capture
loanschedule has **no captures under `.softhouse/capture/loanschedule/`** — its vectors come
from the **Path A embeddable seam**, captured by a Java rig. The model is:
```
.softhouse/capture/src/run-pass3f.sh      the executable recipe (fails the run on any
                                          precondition breach — read its header first)
.softhouse/capture/src/Capture3f.java     the harness
```
An existing vector's `provenance.note` names the pass that produced it. Follow that shape:
a new pass, a new case list, the same rig. Record `threaded_mathcontext` (precision 19,
HALF_UP) and the `fineract_commit` pin `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

## Success is a NUMBER, and it may be zero
For each of the two drives, report its kill count BEFORE and AFTER. Moving a drive from 0
to 1 is a complete success — one vector that provably catches a money defect is worth more
than ten that catch nothing.

**If the arithmetic cannot produce a discriminating case, say so and show the algebra.**
It is possible the port's segment structure makes `roundSegmentsThenSum` unreachable — in
which case the correct outcome is to DELETE that drive with the argument for why, not to
leave a permanently inert drive implying coverage that does not exist.

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
