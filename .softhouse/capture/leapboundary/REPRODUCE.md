# Reproducing the T55 leap-boundary captures

Everything runs against the **pinned** reference oracle (Fineract) on the local fire's host.
**Do not start, stop, restart or reconfigure `fineract-fineract-1` / `fineract-db-1`.** T55 touches
only `POST /loans?command=calculateLoanSchedule`, which persists nothing, plus read-only `SELECT`s.
`/Users/buv/fineract` is **read-only** to this task. No Gradle build, no Docker build, no JDK needed.

All paths below are relative to the repository root. Every command is copy-pasteable as written.

## 0. Preconditions you can check by hand

```sh
git -C /Users/buv/fineract rev-parse HEAD          # 426a23544e8426a38ae43ae404670a0a7e85b9eb
git -C /Users/buv/fineract status --porcelain      # must print nothing
docker image inspect fineract:latest --format '{{.Id}}'
# sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a
curl -sk https://localhost:8443/fineract-provider/actuator/health -w '\nHTTP %{http_code}\n'
# {"status":"UP","groups":["liveness","readiness"]}
# HTTP 200
docker exec fineract-db-1 psql -U root -t -c 'select version();'   # PostgreSQL 18.3 …
```

## 1. Capture (Path B, 33 responses)

```sh
sh .softhouse/capture/leapboundary/bin/t55-capture.sh
```

`t55-capture.sh` is a **precondition script, not a wrapper**. Before any POST it asserts the pinned
commit and its cleanliness, runs T36's 21-assertion gate (including the behavioural half-cent
rounding canary), asserts products 7/3/4 are ACT/ACT + DAILY with `UNSET` / `FULL_LEAP_YEAR` /
`FEB_29_PERIOD_ONLY`, asserts those three products agree on **22 other schedule-feeding columns**,
and records `m_loan` / `m_product_loan` / `m_client`. After the POSTs it re-asserts all three counts
and asserts `RestartCount = 0` on both containers. **Any breach prints `BREACH: …` and exits 1.**
A run that does not print `== PASS -- capture admissible` produced nothing admissible.

Every response is written with an explicit `-o` **per file** and its status read with
`-w '%{http_code}'`; the script aborts on any status other than `200` and additionally re-checks
`out/HTTP-CODES.txt` for non-200 rows and every raw file for zero length. (T22's P0-5 audit failed a
pass for exactly the opposite: a broken `-o out/…` glob and a missing `%{http_code}`.)

Writes, under `.softhouse/capture/leapboundary/`:

| path | what |
|---|---|
| `req/calc-LB-*.json` | the 33 requests, authored as text |
| `out/LB-*-raw.json` | the 33 raw response bodies — **the observations** |
| `out/HTTP-CODES.txt` | one `<id> <code>` line per capture |
| `out/preconditions.txt` | the 21-assertion gate's output |
| `out/products-asserted.txt`, `out/products-matched.txt` | the product rows and the matched-pair count |
| `out/container-state.txt` | `StartedAt` and `RestartCount` for both containers |
| `out/DIGESTS.txt` | `shasum -a 256` of every raw response |

## 2. Analysis (contacts no oracle)

```sh
python3 .softhouse/capture/leapboundary/analysis/t55-analyse.py
```

Writes the exact-text sidecars `out/LB-*-exact.json`, then prints and self-checks:

* the **settings asserted** (re-derivation precision and rounding mode);
* the **discrimination table** — for all 11 shapes × 3 pairs, cells compared, cells differing, and
  the largest difference in minor units;
* the **anchor** check — `LB-LEAPIN` vs T48's committed `T48B-PUREB`, which must be 0 cells;
* the **branch re-derivation** — per period, the observed interest against both candidate readings;
* the **gradeability** table — whether each capture would fail two named naive ports;
* the **invariants** — I1…I7 per capture.

Exits **1** on any breach: an `UNATTRIBUTED` period, a period whose observed branch contradicts the
source prediction, an invariant violation, a `p7 vs p3` difference, an inert comparator (no non-zero
pair, or no zero pair), a named control that is not 0 cells, a sidecar with a bare JSON number, or a
`T55_NEG_*` override left set. Recorded output: `analysis/T55-ANALYSIS.txt`.

```sh
python3 .softhouse/capture/leapboundary/analysis/t55-prior-capture-assessment.py
```

Scores **T48's** committed Path B captures with the same code, to answer "does an existing capture
already discriminate?" mechanically. Read-only with respect to `.softhouse/capture/actualactual/**`.
Recorded output: `analysis/T55-PRIOR-CAPTURE-ASSESSMENT.txt`.

## 3. Determinism

```sh
sh .softhouse/capture/leapboundary/bin/t55-determinism.sh
```

Re-posts the **same committed request files** and byte-compares against the committed captures into
`out/rerun/`. Recorded run: **33 re-posted, 0 byte-differences**, `m_loan` still 0.

## 4. Proving the recipe FAILABLE

```sh
sh .softhouse/capture/leapboundary/bin/t55-negative-tests.sh
```

Nine legs, each required to exit non-zero naming its breach; the script exits 1 if any leg PASSes.
Recorded output: `NEGATIVE-TESTS-OUTPUT.txt`. See `NEGATIVE-TESTS.md` for the table.

## 5. Digests

```sh
cd .softhouse/capture/leapboundary && find . -type f | sort | xargs shasum -a 256
```

## Notes

* The `T55_NEG_PREC`, `T55_NEG_ROUND` and `T55_NEG_DOCTOR` environment hooks exist **only** for the
  negative tests. If any is set, `t55-analyse.py` **fails the run and names the hook** — a hook left
  set cannot masquerade as a PASS.
* `T55_PIN_COMMIT` and `T55_ORACLE_SRC` exist so leg N1 can point the capture script at a wrong pin.
  Leave both unset for a real capture.
* `bin/t55-capture.sh` **is** idempotent: it creates nothing and re-posting produces identical
  bodies (§3). Re-running it is safe.
