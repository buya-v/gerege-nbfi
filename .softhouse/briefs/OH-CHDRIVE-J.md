# OH-CHDRIVE-J — prove the charges corpus discriminates. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-chdrive` (branch `feat/OHCHDRIVEj`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

## THE MEASUREMENT

`charges` holds **12 vectors on a single seam (`charge-evaluate`) behind 4 drives**:

    charges-wrong-percent-one-scale-short
    charges-wrong-percent-truncating
    charges-wrong-rounding-half-even        (kills 1)
    charges-wrong-validation-skipped

All four are about **percentage arithmetic and validation**. The corpus varies far more
than that, and a port ignoring an unvaried-by-any-drive field passes all 12.

Distinct values across the 12 vectors, measured by the driver — **verify before relying
on it**:

    VARIES                          distinct   covered by a drive?
      amount_minor                      8        no
      percentage                        4        YES (percent-* drives)
      base_amount_minor                 4        no
      time_type                         3        no
      calculation_type   FLAT | PERCENT 2        NO  <-- biggest money effect
      penalty            true | false   2        NO  <-- books to the wrong account
    CONSTANT — cannot discriminate anything
      currency_code, applies_to, payment_mode, active, deleted

## The task — ONE property, applied per field

> **For each VARYING field no drive covers, a port that IGNORES that field must DIE.**

Two are worth doing first, and the reasons are not symmetric:

* **`calculation_type` (FLAT vs PERCENT)** — the largest money effect available. A port
  that always treats a charge as flat (or always as percent) computes a different amount on
  roughly half the corpus. Nothing tests it.
* **`penalty` (true vs false)** — this one reaches past the charges seam. The GL work
  landed this week shows a fee credits **`OHLGR-Income-From-Fees`** while a penalty credits
  **`OHLGR-Income-From-Penalties`** — *different accounts*
  (`.softhouse/capture/loan12-four-bucket-allocation/out/journalentries-loan-12-after-raw.json`).
  A port that ignores the penalty flag books revenue to the wrong income account, and every
  total still balances. Grading the flag HERE is what makes that defect catchable at all.

Then `base_amount_minor`, `time_type`, `amount_minor` as budget allows. **Order matters more
than count: two drives that kill beat five never measured.**

## THE RULE ON INERT DRIVES — and a zero here is a RESULT

**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument** and record which field.

**A zero is genuinely interesting** and must be reported as one: it means the corpus varies
a field but no vector's OUTPUT depends on it — the field is decorative at this seam.
`OH-LSDRIVE-I` did exactly that one run ago: it built `wrong-currency-code-ignored`,
measured ZERO across all 50 loanschedule vectors, and deleted it with the argument that
money scales off `MinorUnitDigits` (2 for both MNT and USD) and the output never reads the
code. **That is the standard.** Report the kill count for every drive you register.

## Measuring it
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh loan         loan-wrong-summary-drops-penalty      -> 2

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

**A conformance binary needs `-oracle-probe=up` for a PASS verdict** — without it you get
`VERDICT: UNUSABLE (exit 2) — THIS IS NOT A PASS`, which is the harness refusing to grade
without a live oracle, NOT a failure of your change. Kill counts are unaffected: a kill is
a FAIL and needs no live oracle. The driver misread this an hour ago; do not repeat it.

After your change `charges-go` must still pass **all 12** vectors and the four existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02;
  0.035 → .04 under both). An earlier brief stated this INVERTED; this form is correct.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not weaken or delete an existing vector** to make a drive kill. If a drive cannot
  kill, that is the finding.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `charges`.**
- Cite `file:line` from the FILE, not a comment-stripped view.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit each drive as it is measured rather than batching** —
`OH-LSDRIVE-I` did that and kept everything; every run this week that batched had to be
salvaged by hand.
