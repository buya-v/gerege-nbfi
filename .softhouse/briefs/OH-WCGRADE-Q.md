# OH-WCGRADE-Q — grade the committed discount capture. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-wcgrade` (branch `feat/OHWCGRADEq`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything you
need is already committed on `main`.

## This is the second half of a deliberate split

`OH-WCCAP-P` created the observation and committed it; **you grade it.** That split exists
because the combined task was killed at 251 iterations having produced nothing
(`.softhouse/findings/F-2026-09-10-split-capture-from-grading.md`). **Do not create
anything in the oracle.**

## THE OBSERVATION — already on disk, with a map

`.softhouse/capture/wc-discount-nonzero/` — **read its `OWNER.md` first**; it records the
endpoints, ids, the snapshot, and the arithmetic.

    product   OHK-WC-Discount-Nonzero (id 2), discount 37.53 MNT
    facility  OHWCCAP-DISCNONZERO-L01 (id 2), client 5, disbursed 1000 on 2026-09-03

Observed balance (`out/wc-loan-discount-detail-raw.json`), and the arithmetic
`OH-WCCAP-P` predicted **before** the write and then confirmed:

    totalDiscountFee                 37.53   ->   3753 minor
    unrealizedIncomeFromDiscountFee  37.53   ->   3753 minor
    totalDiscountFeeAdjustment        0.0
    realizedIncomeFromDiscountFee     0.0
    principal                      1037.53   -> 103753 minor   (1000 + 37.53)

**Verify every one against the file before building on it.** All are whole minor units, so
G-19 does not bite.

## The task

1. **Promote a vector** on the `workingcapital` balance seam pinning the non-zero
   `total_discount_fee` (and the principal that includes it — `applyDisbursement` sets
   `principal = disbursedAmount + discount` [`WorkingCapitalLoanBalance.java:115-120`], so a
   port that drops the discount from principal is wrong).
2. **Relax the `ErrNoGradedCapture` refusal for `TotalDiscountFee` ONLY.**
   `workingcapital/balance.go` refuses every stored term the corpus cannot discriminate
   (added by `OH-WC-S`). That term is now graded; **the others are not.** **Do not remove a
   refusal you have not earned** — each one still standing is a true statement about the
   corpus, and silently dropping one is a loss of coverage that no test would catch.
3. **Register a drive** for a defect this observation discriminates — e.g. a port that
   drops the discount from `principal`, or one that hardcodes `totalDiscountFee` to zero
   (which every prior vector allowed, since all five carried it at 0).
4. **Measure the drive against the store WITHOUT your vector and WITH it.** Zero on the old
   corpus and non-zero on the new proves the gap was real. `OH-SHARES-K`, `OH-COLL-L`,
   `OH-ACCRUAL-M` and `OH-PROV-N` all did this.

## WHAT YOU CANNOT GRADE, and must not pretend to

`UnrealizedIncomeFromDiscountFee = max(totalDiscountFee − adjustment − realized, 0)`
[`balance.go:87-92`] now has its **first non-zero operand**, but `adjustment` and `realized`
are both **0**, so the expression is `max(37.53, 0)` — firmly on the **positive** branch.
**The clamp itself is still unexercised**: a port that omits `max(…, 0)` computes the same
answer here. **Do not register a drive for the clamp** — it would kill zero. Record what a
capture would need (an adjustment or realized income exceeding the discount, driving the
expression negative), exactly as `OH-WC-S` recorded this one for you.

**Also leave `total_disbursement` alone**: `OH-WC-S` proved there is no writer under
`src/main`, so it is structurally zero and no capture can ever grade it.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.

## Measuring it
    kills.sh workingcapital <impl>                              (existing: 4 drives)
    kills.sh provisioning provisioning-wrong-sum-then-round     -> 1
    kills.sh collateral   collateral-wrong-pct-hardcoded        -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY** — `-root` is required by
most and rejected by loanschedule's; `-oracle-probe` exists on some only. Use `kills.sh`.

After your change `workingcapital-go` must still pass **all** its vectors and the four
existing drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  `37.53` is `3753`. MNT = ISO 496, minor unit 2.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Never describe member savings as insured, protected or guaranteed.**
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `workingcapital`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations for a pure grading task. **Commit by iteration 120** — every pure-grading
run this session committed between ~64 and ~190.
