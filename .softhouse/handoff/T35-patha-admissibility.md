# T35 — Path A / embeddable-seam admissibility — handoff

**Task:** T35, branch `softhouse/T35-patha-admissibility`, worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-aab46ce1ac868d925`, 2026-08-18.
**Fire context:** local, on Buyan's Mac. **The reference oracle (Fineract) was REACHABLE**, which is the
whole reason these items could be closed — they had been parked `oracle_unreachable` across several fires.
**Inputs of record:** `.softhouse/reviews/T21-capture-pass3-audit.md` (authority for P0-2/P0-3/P0-4),
`.softhouse/reviews/T27-corpus-corrections-review.md` (RC-5, RC-6), `.softhouse/handoff/T25-corpus-corrections.md`,
`.softhouse/handoff/T30-corpus-remainder.md`, `.softhouse/capture/PASS3-REPORT.md`.

> **NOTHING WAS PROMOTED to the parity vector store, and no expected value was hand-authored.** Every
> number below was observed from the pinned reference oracle in this fire, read from an artefact already
> committed on `main`, or read from the pinned Fineract source. Where I could not verify something, it is
> in **`## Unverified`** and is not dressed up as a result.

---

## What I closed

### 1. T21 P0-2 — the attestation block — **CLOSED**

New top-level `attestation` object in `out/capture-prod3b-raw.json`, plus a **machine-readable sidecar next
to the captures**, `out/capture-prod3b-attestation.json`. Everything outside `runnerSupplied` is measured
inside the container during the run; the docker image id and host checkout are echoed and **labelled as
echoes**, and the runner asserts them independently and fails the run on mismatch.

| attested value | observed | source |
|---|---|---|
| image ref / id | `fineract:latest` / `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` | [VERIFIED: `docker image inspect`, this fire] |
| **Fineract commit built into the image** | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git.dirty=false`, describe `1.15.0-273-g426a235`, commit time `2026-08-12T12:59+0000` | [VERIFIED: `BOOT-INF/classes/git.properties` read in-container] |
| pinned checkout | same commit, working tree clean | [VERIFIED: `git -C /Users/buv/fineract`] |
| `/app/fineract-provider.jar` | sha256 `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9`, 230,485,171 B | [VERIFIED: measured in-container] |
| JVM | OpenJDK 64-Bit Server VM `21.0.11+10-LTS`, Zulu, vendor Azul Systems; Linux aarch64 6.12.76-linuxkit | [VERIFIED: system properties, in-container] |
| **JVM input flags** | **none** — `inputArgumentCount = 0` | [VERIFIED: `RuntimeMXBean.getInputArguments()`] |
| encoding / locale / default TZ | `UTF-8` / `en_US` / `GMT` | [VERIFIED: in-container] |
| `MoneyHelper.PRECISION` | **19** | [VERIFIED: read at runtime; and `MoneyHelper.java:35`] |
| **effective `MathContext`** for a tenant initialised with value 4 | **precision 19, `HALF_UP`, RoundingMode ordinal 4**; `matchesRatifiedProductionSetting: true` | [VERIFIED: `MoneyHelper.getMathContext()`/`getRoundingMode()` at runtime] |
| per capture | all twelve: ambient `(19, HALF_UP, ordinal 4)`. Eleven at explicit `mc` `(19, HALF_UP, ordinal 4)`; `P-CAL` at explicit `mc` `(12, HALF_UP)` | [VERIFIED: `capture-prod3b-raw.json`] |
| oracle's own SLF4J lines | **13** kept in `out/capture-prod3b-log.txt` — 12 capture tenants + the attestation probe tenant, all `HALF_UP` | [VERIFIED: `capture-prod3b-log.txt`] |
| seam class | sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714`, byte-identical to the pinned original | [VERIFIED: `cmp` + `shasum`, both sides] |
| classpath | **350** entries; per-entry digests in `out/capture-prod3b-classpath-sha256.txt`; aggregate digest in the attestation | [VERIFIED] |

**The run did NOT run at a different setting.** Had it, that would have been a finding; the recipe also
fails the run in that case rather than leaving a mislabelled artefact behind.

**Bonus, now machine-checkable:** the classpath digest file shows `postgresql-42.7.11.jar` and **zero**
`oracle`/`ojdbc`/`mysql`/`mariadb` entries — the PostgreSQL-only rule is now evidenced by an artefact
rather than by assertion. (Path A opens no database connection at all; stderr is 0 bytes.)

### 2. T21 P0-3 — the missing columns — **CLOSED**, and P1-9 with it

`src/Capture3b.java` runs pass 3's **same twelve cases, input for input**, and adds `periodFromDate`,
`feeAmount`, `penaltyAmount` on every period type that carries them
[`LoanSchedulePlanRepaymentPeriod.java:26-38`, `…DisbursementPeriod.java:26-30`, `…DownPaymentPeriod.java:26-33`]
plus the plan totals `totalPrincipalAmount`, `totalFeeAmount`, `totalPenaltyAmount`, `totalOutstandingAmount`
[`LoanSchedulePlan.java:36-43`]. Every `BigDecimal` now leaves through `toPlainString()`, and the error
branch prints the top 25 stack frames and the cause instead of discarding them (T21 P1-9).

`Capture3.java` and `out/capture-prod-raw.json` are **untouched**, deliberately: pass 3 stays reproducible
as committed, and pass 3b can be compared against it.

New checks that only exist now the columns do (`out/t35-newcolumn-checks.py`, **all twelve PASS**): **N1**
period-boundary contiguity `fromDate[i] == dueDate[i-1]`; **N2** first repayment `fromDate` == schedule
start; **N3** fee/penalty scale and sign discipline; **N4** fee/penalty totals = their sums; **N5**
`totalPrincipalAmount` = Σ principal = `totalDisbursedAmount`. All integer minor units, no tolerance.

### 3. T21 P0-4 — the executable run recipe — **CLOSED, and validated by running it**

`src/run-pass3b.sh`, run from the repo root, **executed three times against the pinned image on this fire**.
It fails the run on: docker/image absent; image id mismatch; pinned checkout missing, wrong commit, or dirty
tree; **seam-class drift** (`cmp` against the pinned original); non-zero container exit; no JSON on stdout or
unparseable JSON; **non-empty stderr**; wrong capture count, any `"observed": null` or `error` key; and the
effective `MathContext` not being `(19, HALF_UP)`/ordinal 4, the image's `git.commit.id` disagreeing with the
pinned checkout, `git.dirty ≠ false`, or the runner's echoed attestation disagreeing with its own
measurement. Documented in `README-pass3b.md`.

**The T22 P0-5 defect class, checked for on my own scripts.** A shell glob in an output path cannot expand
against a file that does not exist yet, so `-o out/X-*.json` creates a file named literally `X-*.json`.
**Every output path in all three scripts I wrote is a literal filename** — no `*`, no `?` in any redirect
target. `run-rc6-rounddown-attestation.sh` additionally captures `-w '%{http_code}'` and treats any non-200
body as an error body, refusing to call it a capture.

**Digests, so a re-run is verified rather than eyeballed.** `out/capture-prod3b-sha256.txt` hashes every
output, and the sidecar carries per-file digests plus a **run-stable** digest:

```
capturesCanonicalSha256 = 02e94174cda26540e882d6da0f0ac3aabc02923ddf501a4dde90fd7d60aa38ec
```

sha256 of the canonicalised `captures` array. **Identical on all three runs**; the whole-file digest is not,
because the attestation carries a UTC timestamp — which is exactly why the canonical digest exists.

### 4. T27 RC-5 — `t21v2-probe2-oracle-out.txt` re-emitted with a provenance header — **CLOSED**

`.softhouse/reviews/t21v2/T21v2Probe2Attested.java` is a **wrapper, not an edit**: `T21v2Probe2.java` is the
T21-v2 audit's evidence-generating source and is cited by `PASS3-REPORT.md`, so it is left byte-unchanged
and the rows are produced by literally the same class. Header now carries the image ref/id, the jar's
`git.commit.id` and sha256, the pinned commit, the JVM string, `MoneyHelper.PRECISION`, the effective
`MathContext` (19, HALF_UP, ordinal 4), the per-run tenant rounding mode with its source line, the fixed
inputs, and the sha256 of every compiled source. The oracle's own `MoneyHelper` INFO lines are kept
interleaved, one per run, as independent corroboration.

**The 17 data rows are byte-identical to the committed transcript** — verified by diff *before* overwriting,
and the script refuses to overwrite if they are not. `sha256(t21v2-probe2-oracle-out.txt) =
f44a72f40b822055333b82ad5f24af57d233bc3ec20ff77dcbcad10e54748c04`.

### 5. T27 RC-6, attestation half — **CLOSED**

`out/t35-rc6-rounddown-attestation.json`, produced by `src/run-rc6-rounddown-attestation.sh`. Three
independent legs, none of them inference from a filename:

1. **The tenant's own configuration, read live.** `GET /configurations` under
   `Fineract-Platform-TenantId: gerege` → `rounding-mode = 4`. That is the exact key
   `MoneyHelperInitializationService.getRoundingModeFromConfiguration()` reads
   [`MoneyHelperInitializationService.java:102-106`; `GlobalConfigurationConstants.java:41` →
   `ROUNDING_MODE = "rounding-mode"`].
2. **The oracle's own startup log.** `docker logs fineract-fineract-1` →
   `Initialized rounding mode for tenant \`gerege\`: HALF_UP` (and, for contrast,
   `tenant \`default\`: HALF_EVEN`). `MoneyHelper.updateTenantRoundingMode` has **no production caller** in
   the pinned checkout — only its declaration at `MoneyHelper.java:104` and test callers — so the cached
   per-tenant mode cannot have drifted from the startup value without a restart. [VERIFIED: repo-wide grep.]
3. **The probe re-run, today, on that attested environment.** The committed request
   `pathb/t22-audit/req/calc-prounddown.json`, unmodified, POSTed to `?command=calculateLoanSchedule` (a
   preview — it creates no loan, no client, no product, and writes nothing). It **AGREES with the committed
   observation to the minor unit** on every period column and every plan total, compared as integer minor
   units with no tolerance. Observed EMI periods 1-11: **`111100.00`**, exactly as committed.

Precision needs no runtime reading: `MoneyHelper.PRECISION = 19` is a compile-time constant
[`MoneyHelper.java:35`] and `getMathContext()` = `new MathContext(PRECISION, getRoundingMode())` [`:91-93`].

**I did not write to `.softhouse/capture/pathb/`** — the round-down inputs were read, and all outputs went
to `.softhouse/capture/out/`. I did not start, stop, restart or reconfigure any container.

---

## What I could not close (and why)

| item | status | why |
|---|---|---|
| **Promotion of the eleven `(19, HALF_UP)` records** | **NOT DONE, deliberately** | Not mine to make. DEC-1 is at revision 6 and **UNRATIFIED** (gate G-1); captures stay in RAW OBSERVED form. T30's standing verdict that nothing may be promoted is unchanged by this task. |
| **T21 P1-8** — capture the `decimalPlaces == 0` `CurrencyData.inMultiplesOf` behaviour | **OPEN** | Requires fixing T19-10 first: `Capture3b.java` inherits pass 3's structural defect — one `installmentMultiplesOf` field feeds the `CurrencyData` constructor, the model's `installmentAmountInMultiplesOf`, **and** both emitted JSON keys, so the two cannot be varied independently. Fixing it changes the `Case` record and the emitted inputs; I judged that out of scope for a task whose central claim is "the twelve cases are input-for-input identical to pass 3", because it would have made the byte-identity comparison weaker. It is a small, self-contained next task. |
| **T21 P1-11** — capture the `36 × 16.8 %` small-principal shape | **OPEN** | Same reason: adding cases to `Capture3b` would have broken the input-for-input comparison that makes P0-3 checkable. The shape is a demonstrated discriminator (oracle diverges at principal **4.00**) and deserves its own capture id series, not a smuggled row. |
| **T21 P1-10** | **still deferred-and-recorded** (T25) | Untouched. |
| **T22 P0-3 / P0-4 / P0-6** | **OPEN** | Path B, owned by another worker this fire. I did not touch `pathb/`. |
| **T22 P1-11, second clause** — a vector that forces the EMI re-adjust loop to iterate | **OPEN** | Not in this task's brief; needs a deliberately-chosen input, and on Path A it would again mean adding cases. |

---

## Attestation

The machine-readable record is `out/capture-prod3b-attestation.json` (sha256
`fb33fc8b3dfac1526f16b8acfc4ae37c0eb90743b13de67766b0a4a3a6e466e2`); the table in **§1** above is its
human-readable form and every row of it is measured, not assumed. In one line:

> **Path A pass 3b ran at `MathContext(19, HALF_UP)`, RoundingMode ordinal 4 — the ratified production
> setting — on image `sha256:e596339626bf…0459a`, whose jar was built from Fineract
> `426a23544e8426a38ae43ae404670a0a7e85b9eb` with `git.dirty=false`, the same commit as the pinned
> checkout, under Zulu OpenJDK 21.0.11+10-LTS with no JVM flags.**

Facts here that belong in `.softhouse/reference-oracle.md` — I did **not** edit that file; the orchestrator
should fold these in:

- The image's own `git.properties` reports commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`,
  `git.dirty=false`, build version `1.16.0-SNAPSHOT`, branch `develop`, describe `1.15.0-273-g426a235`.
  **The image and the pinned checkout are the same commit** — previously assumed, now measured.
- `/app/fineract-provider.jar` sha256 `60fb6dbd631dad8ea133d03fdd24761626f407c6d7dc4b1b41a4402eaf66f4c9`.
- Container JVM: Zulu OpenJDK `21.0.11+10-LTS`, Linux aarch64, no JVM input arguments; classpath 350 entries
  including `postgresql-42.7.11.jar` and **no** Oracle/MySQL/MariaDB driver.
- Live server tenants: **`gerege` → HALF_UP (rounding-mode = 4)**, `default` → HALF_EVEN, from the server's
  own startup log and from `GET /configurations`.
- Path A run recipe is now `sh .softhouse/capture/src/run-pass3b.sh` (supersedes the prose in
  `README-pass2.md` for Path A); `README-pass3b.md` documents it.

---

## Byte-identity check vs the committed corpus

**This is the check that mattered most, and it came back clean.**

**Step 1 — the committed pass 3 reproduces byte for byte on this fire.** `Capture3.java` unmodified, same
recipe: `sha256 11c5c74a27aa1d9e91b9eacf20e36e469bc5e34e3943e00b1543ad3671a732e2`, **identical** to the
committed `out/capture-prod-raw.json` and to the digest the T21 audit recorded. Baseline sound.

**Step 2 — pass 3b vs pass 3, value for value** (`out/t35-byte-identity.py`):

```
compared 1560 values published by pass 3, across 12 captures
  IDENTICAL      : 1560
  RENDERING-ONLY : 0
  VALUE CHANGED  : 0
  DROPPED by 3b  : 0
  ADDED by 3b    : 12  (keys pass 3 never emitted for that period type)
VERDICT: PASS
```

**No number pass 3 published changed.** The twelve additions are `balance` (`outstandingLoanBalance`) on the
DISBURSEMENT rows, which pass 3 emitted for repayment and down-payment rows but not for disbursement rows.
The comparator classifies "old present, new absent" as a **DROPPED** defect and "old absent, new present" as
an addition, so an addition can never mask a change.

**T21 P1-9 landed as a true no-op:** `RENDERING-ONLY : 0` means `toString()` and `toPlainString()` were
already identical on every value in this corpus — corroborating the T21 audit's `A5` finding from the other
direction. It is a latent-channel fix, not a correction.

**Invariants re-run on the new artefact.** `t21v2-invariants.py` → `SIX-CLAIMED verdict: ALL PASS` on all
twelve, `A2` violated on `P-03` alone — exactly the pass-3 result, and exactly the `A2`-formulation artefact
the T21 audit diagnosed (§6.1). `t21-probe-invariants.py` (T25's repaired `X2`) → `ALL PASS` on all twelve.

**Re-run stability.** Three runs of the recipe; `capturesCanonicalSha256` identical on all three; the two
compared artefacts differ in nothing but `capturedAtUtc` and `runId`.

### New finding — `totalOutstandingAmount` is a hard-coded zero, at scale 0

Newly emitted by P0-3, so nobody had seen it before. It is `"0"` on **all twelve** captures — scale 0, while
every other money string in the artefact is scale 2. The mechanism is not rounding:

```java
// ProgressiveLoanScheduleGenerator.java:156-157
final BigDecimal totalPrincipalPaid = BigDecimal.ZERO;
final BigDecimal totalOutstanding   = BigDecimal.ZERO;
```

passed straight through to `LoanScheduleModel.from(...)` [`:159-164`] and out via
`LoanSchedulePlan.totalOutstandingAmount` [`LoanSchedulePlan.java:43, 85-96`].
[VERIFIED: pinned checkout, both files.] Two consequences:

1. **The field carries no information on this path.** It is the literal `BigDecimal.ZERO`, not "the
   schedule's outstanding total". A Go port must emit zero there and nobody should read meaning into it.
   Worth a line in DEC-1 — **I did not touch `docs/adr/`**.
2. **It would break the scale-discipline invariant `A5` asserts, and `A5` never saw it**: `A5` inspects
   `{principal, interest, total, balance, totalOutstandingBalance}` plus three plan totals only
   [`t21v2-invariants.py:96-101`]. Any future scale check must decide explicitly whether `"0"` is acceptable
   at that key. I assert **no** expected value for it; it is reported as observed (`N6`).

Also newly observed, and worth stating because it bounds what these vectors can grade: every `feeAmount` and
`penaltyAmount` is `0.00` (144 of each) and both plan totals are `0.00` on all twelve. **The corpus has zero
discriminating power over charges** — a Go port that mishandles fees passes every one of these vectors.

---

## Admissibility verdict

**Stated plainly, as asked: the three T21 Path A P0 items are now CLOSED, and the eleven `(19, HALF_UP)`
Path A records are STILL NOT ADMISSIBLE AS PARITY VECTORS — and I promoted nothing.**

What changed: the eleven are now **attested**, carry **every column the capture plan mandates**, and are
produced by a **committed recipe that has actually been run** (three times, with a stable digest). On the
T21 §11 wording, they have moved from "audited observations" to "**attested** audited observations". That is
a real step, and it is not promotion.

What still blocks them, in order of seriousness:

1. **DEC-1 is at revision 6 and UNRATIFIED — gate G-1.** Captures stay in RAW OBSERVED form until the
   contract they would be graded against is settled. This is the binding blocker, it is a `user`-adjacent
   contract gate, and it is not mine to cross. Closing P0-2/3/4 does not touch it.
2. **The seam's blind spots are a property of the RIG, not of the run, and are unchanged.** Path A accepts a
   19-component `LoanRepaymentScheduleModelData` and honours 17: `installmentAmountInMultiplesOf` is
   structurally unreachable and `daysInYearCustomStrategy` is silently dropped by a hand-maintained builder
   copy [T21 §7, from source]. Pass 3b adds the *charges* blind spot as a newly **observed** fact rather than
   an inferred one. So "these vectors pass" must never be read as "the contract is covered" — and a corpus
   admitted as *parity* vectors without that caveat attached in the store would be actively misleading.
3. **T21 P1-8 is open** — the harness still cannot vary `CurrencyData.inMultiplesOf` independently of
   `installmentAmountInMultiplesOf` (T19-10), so the one multiples-of channel Path A can reach — the one
   the T21 audit showed **moves money** at `decimalPlaces = 0` (763,994 vs 764,100) — remains unvectored.
4. **T21 P1-11 is open** — the `36 × 16.8 %` small-principal shape, on which the oracle diverges at principal
   **4.00**, is still not captured. It is the cheapest known discriminator for the precision seam.
5. **`P-CAL` is never promotable** as a parity vector: `(12, HALF_UP)`. Unchanged, and correctly labelled in
   the artefact (`mathContextPrecision: 12`), so a consumer can tell mechanically.

Path B is a separate list and I did not work it: **T22 P0-3, P0-4, P0-6 remain open.** Of the T27 items,
**RC-5 and RC-6's attestation half are closed** by this task.

---

## Unverified

- **[UNVERIFIED] The environment of the ORIGINAL round-down probe run.** RC-6 is closed by attesting
  *today's* environment and showing the probe reproduces on it unchanged. I cannot retroactively attest what
  the tenant's configuration was at the moment T22 ran it; no artefact from that run records it. What I can
  say is that the tenant is HALF_UP now, that the mode cannot drift without a restart
  (`updateTenantRoundingMode` has no production caller), and that the observation is identical — and that
  the round-down conclusion is mode-robust either way (at `111,148.35` the nearest multiple of 100 is
  `111,100` under HALF_UP and HALF_EVEN alike).
- **[UNVERIFIED] Whether `111,148.35`, the unrounded EMI, is what the oracle computes internally.** It is
  model-derived (T22, re-derived by T27); the oracle never emits it. I did not re-derive it and this task
  does not add evidence for it.
- **[UNVERIFIED] That the `attestation` block's shape matches what the capture plan §4.1 requires field for
  field.** I implemented every field the T21 audit's §10 P0-2 sentence names, plus more. I did not locate a
  separate capture-plan document to check the schema against; if one exists with a fixed field list, the
  sidecar may need renaming, not re-measuring.
- **[UNVERIFIED] Anything about the Path B four (`B-01`…`B-04`).** I did not open, run or re-check them
  beyond reading the round-down probe's request and committed output.
- **Cosmetic, disclosed:** in `t21v2-probe2-oracle-out.txt`, one oracle SLF4J line (the header's own probe
  tenant) prints *before* the provenance header, because SLF4J writes to stdout unbuffered while the header
  is assembled and printed in one go. The header explains that its INFO lines are interleaved. Harmless, but
  I would rather disclose it than have a reviewer wonder.

---

## Follow-ups

1. **T21 P1-8 + T19-10, as one task.** Split `CurrencyData.inMultiplesOf` from
   `installmentAmountInMultiplesOf` in the harness `Case` record, the model construction and the emitted
   JSON; then capture the `decimalPlaces == 0` channel that moves money. Do it as **pass 3c with new case
   ids**, not by editing the twelve — the input-for-input identity of those twelve is now load-bearing
   evidence.
2. **T21 P1-11.** Capture the `36 × 16.8 %` shape at principals 4, 59, 72, 340, 426, 6,940 as a new id
   series. Cheap, and the most sensitive precision-seam discriminator known.
3. **DEC-1, next revision (T28 or successor owns the file — I did not touch it):**
   - `totalOutstandingAmount` is `BigDecimal.ZERO` by construction on the progressive path
     [`ProgressiveLoanScheduleGenerator.java:156-157, :159-164`], emitted at **scale 0** (`"0"`), and carries
     no information. A port must emit zero; no consumer may read meaning into it.
   - `periodFromDate` is now vectored: `fromDate[i] == dueDate[i-1]` holds on all twelve, and on `P-03` the
     first repayment period's `fromDate` is the schedule start `2024-01-01` while the disbursement row sits
     at `2024-02-01`.
   - The Path A corpus has **zero** discriminating power over fees and penalties (all `0.00`, observed).
4. **`reference-oracle.md`** — fold in the attestation facts listed under **## Attestation** above. I did not
   edit that file.
5. **`tasks.json` / `RESUME.md`** — the orchestrator owns them. Suggested substance: T21 **P0-2, P0-3, P0-4
   and P1-9 are CLOSED (T35)**; T27 **RC-5 and RC-6's attestation half are CLOSED (T35)**; **still open:**
   T21 P1-8, P1-10, P1-11 and T22 P0-3, P0-4, P0-6, P1-11(second clause); **outstanding P0 count drops from
   6 to 3, all three on Path B**; and **promotability is unchanged — nothing may be promoted**, now blocked
   by DEC-1's unratified state and the rig's blind spots rather than by missing attestation.
6. **Whoever builds the vector store** must carry the blind-spot caveat as data, not prose: any Path A
   record needs a machine-readable "does not grade: installmentAmountInMultiplesOf, daysInYearCustomStrategy,
   fees, penalties, multi-disbursement" field, or a green conformance run will be over-read.

---

## Boundaries respected

- Wrote only under `.softhouse/capture/src/`, `.softhouse/capture/out/`, `.softhouse/capture/*.md`,
  `.softhouse/reviews/t21v2/` and `.softhouse/handoff/`. `git diff --stat b5ac8dc..HEAD` confirms: 24 files,
  all inside those paths.
- **Did not touch** `.softhouse/capture/pathb/`, `.softhouse/capture/dec1-binding/`,
  `.softhouse/reference-oracle.md`, `.softhouse/program.json`, `.softhouse/tasks.json`,
  `.softhouse/RESUME.md`, `docs/adr/`, `nexus/`.
- **Did not start, stop, restart or reconfigure** `fineract-fineract-1` or `fineract-db-1`. Server
  interaction was two GETs and one `calculateLoanSchedule` preview (creates nothing, writes nothing).
- `/Users/buv/fineract` read-only; working tree verified clean before and unchanged after.
- Path A ran in throwaway `docker run --rm` containers against a mount of this worktree's
  `.softhouse/capture`.
- No push. Commits on `softhouse/T35-patha-admissibility` only.
- **Nothing promoted, no DEC-n touched, no gate crossed, no Go written.**

## Non-negotiables scan

| check | result |
|---|---|
| Money as integer minor units; **no float in any money path** | ✅ `Capture3b.java` uses `BigDecimal` only — no `float`/`double` token appears in it. My Python parses every money value with `decimal.Decimal` and compares integer minor units with **no tolerance**; the only `float` tokens are `parse_float=Decimal` and the docstring sentence explaining that it exists to prevent a float being constructed. |
| Prohibited DB engines (`ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`) | ✅ Zero hits in anything I wrote. Now also evidenced: the captured classpath (350 entries) contains `postgresql-42.7.11.jar` and **no** Oracle/MySQL/MariaDB driver. |
| PostgreSQL only | ✅ Path A opens no DB connection (stderr 0 bytes, no JDBC type imported). The RC-6 leg talked to the running server, which is on `postgres:18.3`. |
| "oracle" terminology | ✅ used only in the **test-oracle** sense (the pinned Fineract reference implementation). Oracle Database appears only where named as prohibited. |
| MNT | ✅ ISO 4217 numeric 496, minor unit 2; all MNT captures `currencyDecimalPlaces = 2`; the round-down product is `MNT`, `digitsAfterDecimal 2`. |
| Ratified tenant parameters | ✅ `(19, HALF_UP)`, ordinal 4, **attested by measurement** on Path A and on the `gerege` tenant. `P-CAL` at `(12, HALF_UP)` still labelled calibration, never a parity vector. |
| No US payment rails / vendors | ✅ zero hits. |
| Three-field names / deposit language / hard-coded tz or threshold | ✅ none introduced; no customer-facing string written. |
| Nothing promoted / no contract-shaped storage / no gate answered | ✅ confirmed above. |
| Go module | ✅ no Go changed. |
