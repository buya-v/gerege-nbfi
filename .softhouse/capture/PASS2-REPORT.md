# Capture pass 2 — tenant-context captures against the pinned reference oracle

**Fire:** local `20260818-152328` (Buyan's Mac), 2026-08-18
**Executed by:** the orchestrator (vector capture is orchestrator-only — it touches the oracle)
**Status:** RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED** — pending task T19. Nothing here may be
promoted into the vector store, and no gate may be answered on it, until that audit lands.

## Provenance

| Fact | Value | How established |
|---|---|---|
| Reference oracle image | `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | `docker image inspect fineract:latest --format '{{.Id}}'` |
| Image created | `2026-08-17T11:29:56Z` | same |
| Fineract commit of record | `426a23544e8426a38ae43ae404670a0a7e85b9eb` | `.softhouse/reference-oracle.md`; matches pass 1's claim |
| JVM inside the image | `openjdk 21.0.11 2026-04-21 LTS`, Zulu21.50+19-CA (build 21.0.11+10-LTS) | `java -version` inside the container |
| Database | none touched — this is the embeddable in-process seam, no server, no PostgreSQL | see "What this seam is" below |
| Seam class provenance | `.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java` is **byte-identical** to the pinned original | `diff` against `/Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/.../EmbeddableProgressiveLoanScheduleGenerator.java` → no output |
| Classpath | `BOOT-INF/classes` + all `BOOT-INF/lib/*.jar` unzipped from `/app/fineract-provider.jar` inside the image | see command in `.softhouse/capture/README-pass2.md` |

Prohibited engines: none involved. No `ojdbc` / `oracle.jdbc` / `:1521`, no MySQL/MariaDB driver. The
PostgreSQL rule is not weakened by this seam — it simply does not reach a database at all.

**Artefacts:** `src/Capture2.java` (harness), `out/capture-tenant-raw.json` (13 captures),
`out/capture-tenant-log.txt` (the oracle's own `MoneyHelper` init log lines), `out/capture-tenant-stderr.txt`.

## Why pass 2 exists

Pass 1's `D-04` died with `IllegalStateException: No tenant context available. MoneyHelper requires a
valid tenant context` (`MoneyHelper.java:178-179`). That error gated two whole classes of behaviour,
both of which are open questions on gate **G-1**:

- `allowFullTermForTranche = true` — the branch that reaches `MoneyHelper` at all.
- `installmentAmountInMultiplesOf != null` — T17 called this *"the single largest gap"* and *"the
  highest-risk one for the Mongolian market"*; it is `null` at all 97 in-seam occurrences, so no test pins it.

Pass 2 supplies a tenant via `ThreadLocalContextUtil.setTenant(...)` +
`MoneyHelper.initializeTenantRoundingMode(tenantId, value)`, per case, with a distinct tenant identifier
per case so no static cache entry is shared (`MoneyHelper.java:37-38`).

## Controls — these hold, so the rest is comparable

| Check | Result |
|---|---|
| `T-00-notenant` (C-00 inputs, no tenant) vs pass-1 `C-00` | **identical** — totals `2.05` / `102.05`, all 7 periods |
| `T-00-notenant` vs `T-00-he` (tenant, HALF_EVEN) | **identical**, every column |
| `T-00-he` vs `T-00-hu` (tenant, HALF_UP) | **identical**, every column |

So the tenant context does not perturb the base schedule path, and pass 2's environment reproduces
pass 1's. `MoneyHelper.PRECISION` was read from the running oracle as **19**, and the ambient context
materialised as `precision=19 roundingMode=HALF_EVEN` / `…HALF_UP` exactly as configured — corroborating
T17's source reading that `6` → `HALF_EVEN` and `4` → `HALF_UP`.

## Finding 1 — pass 1's `D-04` gap is CLOSED: the flag is live but schedule-neutral here

With a tenant context, `allowFullTermForTranche = true` **runs to completion**:

| Pair | Result |
|---|---|
| `T-04f` (false) vs `T-04t` (true), 100 / 6 / 7.0 % | **identical**, all 7 periods, every column |
| `T-04f-big` vs `T-04t-big`, 87,654,321 / 18 / 18.5 % | **identical**, all 19 periods, every column |

Two things are true at once and must not be collapsed:

1. **The field is not dead.** It is threaded end-to-end — `assembleFrom` maps it at
   `LoanApplicationTerms.java:606` — and setting it `true` demonstrably takes a *different code path*,
   because that path reaches `MoneyHelper` and pass 1 died there for want of a tenant. This is now a
   **third independent confirmation**, and the first from the running oracle rather than from source
   reading, of what T3b and T5 each concluded separately.
2. **On a single-disbursement loan it does not change the emitted schedule.** Pinning it to `false` in
   DEC-1 stays behaviourally safe *for this shape of loan*.

Not established: its effect on a genuine **multi-disbursement / tranche** loan, which is what the flag is
named for. The embeddable seam takes `disbursementDatas(new ArrayList<>())` (`LoanApplicationTerms.java:600`),
so it cannot express more than one disbursement. That remains `TO_BE_CAPTURED` through a different path.

## Finding 2 — `installmentAmountInMultiplesOf` is silently DROPPED by the capture seam

**This is the most consequential result of the fire and it is rejection-grade for DEC-1.**

Observed: setting the parameter changes **nothing**.

| Pair | Result |
|---|---|
| `T-00-he` (null) vs `T-IM100-he` (100) | **identical**, every column |
| `T-IM100-he` (100) vs `T-IM1-he` (1) | **identical**, every column |
| `T-IM100-he` vs `T-IM100-hu` (rounding mode varied too) | **identical**, every column |
| `T-MNT5M-he` (multiplesOf 100) vs `T-MNT5M-plain-he` (null) | **identical**, all 19 periods |

On a 100-unit loan with EMI `17.01`, rounding to multiples of 100 cannot possibly be a no-op. So this is
not the parameter being honoured and happening not to bite — it is the parameter never arriving.

**Root cause, from source.** `LoanRepaymentScheduleModelData` is a record with **19 components**
(`LoanRepaymentScheduleModelData.java:32-40`). `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
(`LoanApplicationTerms.java:579-606`) — the sole entry the embeddable seam uses
(`ProgressiveLoanScheduleGenerator.java:82`) — reads **18 of them**. The one accessor never called is
`modelData.installmentAmountInMultiplesOf()`. The builder is therefore constructed without it, so
`loanApplicationTerms.getInstallmentAmountInMultiplesOf()` is `null` at
`ProgressiveLoanScheduleGenerator.java:110` and `:335`, and `safeRoundingForEMI`
(`ProgressiveEMICalculator.java:1763-1764`) is never reached.

**Wiring ruled out.** The harness supplied the value through *both* available channels simultaneously —
`LoanRepaymentScheduleModelData`'s own component **and** `CurrencyData.inMultiplesOf` — and neither moved a
single figure. This is the seam's behaviour, not a harness defect.

**Why this matters more than an ordinary gap.** The whole Tier-0 capture plan is built on this seam, and
the *server* path does honour the parameter (`LoanApplicationTerms.java:1301-1305, 1617-1618`;
`Money.java:154`). Therefore:

- The gap is not merely *uncaptured*, it is **uncapturable through this seam**. The capture plan's proposal
  to close it here cannot work, and should be re-marked accordingly.
- A Go port graded only against seam-captured vectors could implement either *honour it* (matching the
  server) or *drop it* (matching the seam) and **pass identically**. That is precisely the defect class
  T5 identified for precision-vs-scale — a contract input the corpus provably cannot discriminate — now
  found in a second, independent field.
- For the Mongolian market this is a live money risk, not a theoretical one: rounding installments to a
  multiple (e.g. the nearest 100 ₮) is an ordinary product feature, and "silently ignore it" is a wrong
  answer that today's corpus would certify as correct.

## Finding 3 — the tenant rounding mode did not move any figure captured here

`HALF_EVEN` (the `application.properties:77` default, value `6`) and `HALF_UP` (what the unit tests mock,
value `4`) produced **identical output in every pair captured**: `T-00-he`/`T-00-hu`,
`T-IM100-he`/`T-IM100-hu`, `T-MNT5M-he`/`T-MNT5M-hu`.

**Read this narrowly.** It says the *ambient* `MoneyHelper` `MathContext` does not reach the arithmetic on
*these* inputs through *this* seam — consistent with T17's finding that `ProgressiveEMICalculator` contains
zero `MoneyHelper` references. It does **not** show the tenant rounding mode is irrelevant to Fineract, and
it does **not** answer G-1 decision 6, because the two paths that *do* consult it —
`installmentAmountInMultiplesOf` (Finding 2) and multi-disbursement `allowFullTermForTranche` (Finding 1) —
are exactly the two this seam cannot exercise. **The question that most needs the answer is the one still
out of reach.**

## Finding 4 — a first MNT-scale observation

`T-MNT5M-*` captures MNT 5,000,000 over 18 months at 18.5 %: total interest `763,994.33`, total repayment
`5,763,994.33`. The largest principal carrying a literal schedule anywhere in the Fineract seam is `245,000`
(T17 gap 3), so this is ~20× beyond anything the corpus pins. Recorded as **observed**, never extrapolated.
Note the currency code is inert here — pass 1's `D-01-mnt` already showed `MNT` and `usd` agreeing digit-for-digit
at equal decimal places.

## What this pass does and does not license

**Does:** close pass 1's `D-04` error; confirm from the running oracle that `allowFullTermForTranche` is
live; establish that `installmentAmountInMultiplesOf` is inert through the capture seam and *why*; add a
first MNT-scale observation; confirm the ambient `MathContext` is `precision=19` + tenant mode.

**Does not:** license any vector into the store (T19 audit pending); answer any G-1 decision; say anything
about multi-disbursement behaviour; or show the tenant rounding mode is safe to leave unspecified.

**New work this raises:**

1. `installmentAmountInMultiplesOf` and multi-disbursement `allowFullTermForTranche` need a capture path
   that is **not** the embeddable seam — most likely the running Fineract server's loan-schedule preview
   API against PostgreSQL. That is a materially larger capture rig than Tier 0 assumed.
2. DEC-1 must state explicitly, for every input in its domain, whether the *seam* honours it — an input the
   contract exposes but the grading path ignores is unconformance-testable by construction.
