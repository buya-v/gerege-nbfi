# T50 — separate the AMBIENT rounding mode from the THREADED one

**STATUS: INTERIM (Tier 1 landed; Tier 2 in progress).** Superseded by the final revision on this branch.

Tier 1 is complete and admissible: `out/t50-tier1.json`, 2016 cells, runner
`src/run-t50-tier1.sh` printed `== PASS -- capture admissible`.

Headline, all `[VERIFIED: t50-tier1.json]`:

- `Money.of(currency, amount…divide(100, mc))` at the two N46-1 loci: **ambient moves the observation
  in 7/7 threaded columns; threaded moves it in 0/7 ambient rows.** N46-1 CONFIRMED BY OBSERVATION.
- `MathUtil.percentageOf(a, pct, 19)`: same — ambient 7/7, threaded 0/7. N46-3 CONFIRMED BY OBSERVATION.
- The mirror counterfactuals (3-arg `Money.of`, `percentageOf(…, MathContext)`) invert exactly:
  threaded 7/7, ambient 0/7.
- Absence probe: 42/42 ABSENT cases threw `IllegalStateException` on every ambient-reading site and
  0/42 on the two threaded sites.
