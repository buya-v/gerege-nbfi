# Reproducing the T48 ACTUAL/ACTUAL captures

Everything here runs against the **pinned** reference oracle (Fineract) on the local fire's host.
**Do not start, stop, restart or reconfigure `fineract-fineract-1` / `fineract-db-1`.** Every Path A /
Path A2 container is `docker run --rm` and mounts only `.softhouse/capture/actualactual`; the Path B leg
is additive and touches only `POST /loans?command=calculateLoanSchedule`, which persists nothing.

`/Users/buv/fineract` is **read-only** to this task. No Gradle build is run.

## Path A and Path A2 — three sets, one command each

```sh
T48_SET=seam  bash .softhouse/capture/actualactual/src/run-actualactual.sh
T48_SET=calc  bash .softhouse/capture/actualactual/src/run-actualactual.sh
T48_SET=exact bash .softhouse/capture/actualactual/src/run-actualactual.sh
```

`run-actualactual.sh` is a **precondition script, not a wrapper**. It checks the pin, the cleanliness of
the pinned checkout, the image id, the seam-class bytes, the container exit code, stderr, JSON
parseability, the negative-test overrides, the **threaded** `MathContext` read off the object, the
**ambient** `MoneyHelper` context, the tenant rounding ordinal, the absence of any JSON float or
scientific notation in the observations, and the classpath's freedom from Oracle Database / MySQL /
MariaDB drivers. **Any breach prints `BREACH: …` and exits 1.** A run that does not print
`== PASS -- capture admissible` produced nothing admissible.

### What each set writes, under `out/`

| file | what |
|---|---|
| `t48-<set>-raw.json` | verbatim stdout: the oracle's own SLF4J lines followed by the JSON |
| `t48-<set>-log.txt` | the log lines split off the front — evidence, not noise |
| `t48-<set>.json` | the JSON payload, i.e. **the observation** |
| `t48-<set>-stderr.txt` | stderr (must be empty) |
| `t48-<set>-oracle-identity.txt` | jar sha256, `java -version`, the jar's `git.properties`, the classpath |
| `t48-<set>-classpath.txt` | the 348 classpath entries, for the digest and the driver scan |

## Path B — the production wiring

```sh
sh .softhouse/capture/actualactual/src/pathb-capture.sh
```

Runs T36's 21-assertion preconditions gate first (including the behavioural half-cent canary), asserts
products 7 / 3 / 4 out of PostgreSQL, captures 13 responses, then asserts that `m_loan` is still 0 and
`m_product_loan` still 16. Creates **no** product and **no** charge.

## The charge-gap pass (a different subtree)

```sh
sh .softhouse/capture/charges/bin/t48-capture.sh       # creates NEW charge ids only
python3 .softhouse/capture/charges/bin/t48-analyse.py
sh .softhouse/capture/charges/bin/t48-determinism.sh
```

`t48-capture.sh` is **not idempotent** on the charge-definition step: re-running it creates further
`T48 …` charge rows. The ids it created on this fire are recorded in
`.softhouse/capture/charges/out/t48/created-charges.txt` and `CREATED-IDS.txt`.

## Analysis — contacts no oracle

```sh
python3 .softhouse/capture/actualactual/analysis/discriminate.py       # full-cell + rate-factor-only
python3 .softhouse/capture/actualactual/analysis/pathb-crosscheck.py   # Path B vs Path A2, cell for cell
python3 .softhouse/capture/charges/bin/t48-analyse.py                  # the charge gaps
```

Each exits 1 if a comparison that must be identical is not, or a comparison that must separate does not.
Recorded outputs: `analysis/DISCRIMINATION-OUTPUT.txt`, `analysis/PATHB-CROSSCHECK.txt`,
`.softhouse/capture/charges/out/t48/ANALYSIS.txt`.

## Determinism

```sh
T48_OUT_PREFIX=t48det T48_SET=seam  bash .softhouse/capture/actualactual/src/run-actualactual.sh
T48_OUT_PREFIX=t48det T48_SET=calc  bash .softhouse/capture/actualactual/src/run-actualactual.sh
T48_OUT_PREFIX=t48det T48_SET=exact bash .softhouse/capture/actualactual/src/run-actualactual.sh
cd .softhouse/capture/actualactual/out
diff t48-seam.json t48det-seam.json && diff t48-calc.json t48det-calc.json && diff t48-exact.json t48det-exact.json
```

Printed nothing on the recorded run: the payloads are byte-identical from fresh containers.

## Proving the recipe FAILABLE

```sh
bash .softhouse/capture/actualactual/src/negative-tests.sh
```

Eight legs, each required to exit non-zero with a `BREACH` naming the breach. See `NEGATIVE-TESTS.md`
for the recorded output. Leg 4 temporarily appends a line to the seam-class copy and restores it, then
`diff`s it against the pinned original to prove the restore.

## Checking the preconditions by hand

```sh
git -C /Users/buv/fineract rev-parse HEAD          # 426a23544e8426a38ae43ae404670a0a7e85b9eb
git -C /Users/buv/fineract status --porcelain      # must be empty
docker image inspect fineract:latest --format '{{.Id}}'
# sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a

# ANY OUTPUT FROM THIS DIFF INVALIDATES THE CAPTURE -- it would mean the run did not execute
# the oracle's own code.
diff .softhouse/capture/actualactual/src/EmbeddableProgressiveLoanScheduleGenerator.java \
     /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
```
