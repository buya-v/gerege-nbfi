# T44 — the auditor's OWN independent checks on `capture/mathcontext/` (T42)

These are the parent auditor's checks, run separately from and concurrently with the dedicated
mathcontext audit leg (`.softhouse/capture/audit-t44/mathcontext/AUDIT-MATHCONTEXT.md`). Where the
two agree, the agreement is between two workers with no shared context.

## Verified CLEAN

**1. The E1 absence probe reproduces exactly as claimed.**
Recomputed from `out/t42-mathcontext.json` by separating two different throws that a crude scan
conflates — the *ambient read* throwing (which is the probe firing) from the *generation* throwing.

- All **13** `-D` cases record `ambientMoneyHelperMathContext` = `java.lang.IllegalStateException:
  Rounding mode is not initialized for tenant …`. **The probe is live on every case** — the tenant
  really was left uninitialised, so the probe is not vacuous.
- **11 of 13 generated a schedule anyway** (`T42-MX-00-D` … `-06-D`, `-09-D` … `-12-D`), i.e. on
  those shapes the ambient context is **provably never consulted**.
- **2 threw** — `T42-MX-07-D` and `T42-MX-08-D`, which are exactly T42's two 0-decimal-place +
  `inMultiplesOf` shapes.

T42's "11 of 13" is correct as published. [VERIFIED: this task, from the committed payload.]

**2. The headline separating shape is in the payload, at the published values.**

| case | principal | n | rate | observed total interest |
|---|---|---|---|---|
| `T42B-PREC-30-p19` | 50,000,000 | 360 | 21.6 | **274527298.56** |
| `T42B-PREC-30-p12` | 50,000,000 | 360 | 21.6 | **274527296.51** |

[VERIFIED: `out/t42-mathcontext2.json`.]

**3. T42 §4 leg 2 — "no committed capture reaches the Path A ambient leak" — independently
confirmed.** `Money.java:49-51` reaches `roundToMultiplesOf(BigDecimal, Integer)` only when
`decimalPlaces == 0 && inMultiplesOf > 0`.

- `grep -rln '"currencyDecimalPlaces": *0[^0-9]' .softhouse/capture` → **only files under
  `capture/mathcontext/out/`**, i.e. T42's own. No other committed capture is 0 dp.
- The only committed non-T42 file carrying a positive `currencyInMultiplesOf` is
  `.softhouse/capture/out/capture-tenant-raw.json`, and **all 13 of its cases record
  `"currencyDecimalPlaces": 2`**.

So the leak is unreachable in the committed corpus, as T42 says. [VERIFIED: this task.]

**4. Write-surface discipline.** `git diff --name-only $(git merge-base main
softhouse/T42-mathcontext-inforce)..softhouse/T42-mathcontext-inforce` authored exactly
`.softhouse/capture/mathcontext/**` plus `.softhouse/handoff/T42-mathcontext-inforce.md` — nothing
else. (T39 and T40 are equally clean on the same test.)

**5. Prohibited-engine tokens.** Every occurrence of `ojdbc|oracle.jdbc|:1521|com.mysql.cj|mariadb|
go-sql-driver` across all three sets is inside a detection pattern or an
`prohibited_engines_asserted_absent` list. No driver, dialect or dependency. [VERIFIED: this task.]

**6. Float discipline in the payloads.** Every Path A payload — `periodratio` and `mathcontext`
alike — carries **0 bare non-integer JSON numbers**: money is a JSON string throughout, so the
`json.load(...)` calls in the analysis scripts that omit `parse_float` are **inert** on these files.
(That is *not* true of the Path B charges captures — see finding **T44-X1** in the review.)
[VERIFIED: `t44_float_scan-output.txt`.]

## Finding raised by the parent auditor

**M-P1 (P2) — T42 complies with its own rule 2 in capture 2 and not in capture 1, and capture 1 is
the one that carries the decisive experiment.**

T42's attestation rule 2 requires: *"On the THREADED context, echo the object, not the intent. Print
`mc.getPrecision()`, `mc.getRoundingMode()` and `mc.toString()` read off the reference handed to the
callee."*

- **`CaptureMathContext2.java:203-205` complies fully** — it writes `mc` (via `toString`),
  `mc.getPrecision()` and `mc.getRoundingMode()`, and adds an explicit `wiring` field
  (`PATH_A_INDEPENDENT_MC` / the Path B variant). This is the best-attested capture in the program.
- **`CaptureMathContext.java:394-395` does not** — it writes `c.precision()` and `c.mode()`, the case
  record's own fields, i.e. the **intent**, under keys named `threadedMathContextPrecision` /
  `threadedMathContextRoundingMode`. Nothing reads the `mc` object.

Capture 1 is where **E1**, the absence probe, lives — the experiment whose result became the ratified
eight-point rule. So the run that established "only the threaded context is evidence about money" is
itself attested on the threaded axis by intent rather than by object, under field names that assert
otherwise.

**Materiality is low and should be stated plainly:** the ambient field in capture 1 *is* read off the
object, the two 0-dp shapes' stack traces are direct observations, and the E1 conclusion is an
**absence** result that does not depend on the threaded echo at all. No value is affected. It is a
rule-compliance defect in the set that authored the rule, and it is the same shape as **F39-3**
against T39 — which suggests the two capture harnesses share the ancestor that has it.

**Required change:** echo `mc.getPrecision()` / `mc.getRoundingMode()` / `mc.toString()` in
`CaptureMathContext.java` as capture 2 already does, or rename the two fields so they do not claim to
be readings of the threaded object.
