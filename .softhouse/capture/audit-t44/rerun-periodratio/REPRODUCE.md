# Reproducing the T39 periodRatio observation captures

Path A — the embeddable seam, **in process**. No Fineract server is started and no PostgreSQL is
contacted; this seam reaches no database at all. (The PostgreSQL-only rule still governs the
program; it simply has no bearing on this seam. `run-periodratio.sh` nonetheless proves the
oracle classpath has zero Oracle Database / MySQL / MariaDB entries.)

**Do not start, stop or reconfigure `fineract-fineract-1` / `fineract-db-1`.** Every container
here is `--rm` and mounts only `.softhouse/capture/periodratio`; keep it that way.

## One command

```sh
bash .softhouse/capture/periodratio/src/run-periodratio.sh
```

It is a **precondition script, not a wrapper**. It checks the pin, the cleanliness of the pinned
checkout, the image id, the seam-class bytes, the container exit code, stderr, JSON parseability,
every case's observation, the ambient and threaded `MathContext`, the tenant rounding ordinal,
that no negative-test override was left set, and the classpath's freedom from prohibited drivers.
**Any breach prints `BREACH: …` and exits 1.** A run that does not print
`== PASS -- capture admissible` produced nothing admissible.

The recipe has been **proved failable** on seven axes — see `NEGATIVE-TESTS.md`.

## What it writes (under `out/`)

| file | what |
|---|---|
| `t39-periodratio-raw.json` | verbatim stdout: the oracle's own SLF4J log lines followed by the JSON |
| `t39-periodratio-log.txt` | the log lines split off the front — evidence, not noise |
| `t39-periodratio.json` | the JSON payload, i.e. **the observation** |
| `t39-periodratio-stderr.txt` | stderr (must be empty) |
| `t39-periodratio-oracle-identity.txt` | jar sha256, `java -version`, the jar's own `git.properties`, the classpath listing |
| `t39-periodratio-classpath.txt` | the 348 classpath entries, for the digest and the driver scan |

## Preconditions, if you want to check them by hand

```sh
git -C /Users/buv/fineract rev-parse HEAD          # 426a23544e8426a38ae43ae404670a0a7e85b9eb
git -C /Users/buv/fineract status --porcelain      # must be empty
docker image inspect fineract:latest --format '{{.Id}}'
# sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a

# the seam-class copy must be byte-identical to the pinned original.  ANY OUTPUT INVALIDATES
# THE CAPTURE -- it would mean the run did not execute the oracle's code.
diff .softhouse/capture/periodratio/src/EmbeddableProgressiveLoanScheduleGenerator.java \
     /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
```

The seam class is compiled from source because it is **not** bundled in
`/app/fineract-provider.jar`. Everything else it calls comes from that jar.

## Analysis (contacts no oracle)

```sh
cd .softhouse/capture/periodratio/analysis
python3 select_shapes.py   # run BEFORE a capture: does each candidate separate the readings
                           # at all?  RE-DERIVATION only.
python3 controls.py        # calibration + three reproduction controls.  exit 1 on any mismatch.
python3 discriminate.py    # the observation against R1/R2/R3, cell by cell.  The verdict.
```

Then verify every digest in `ATTESTATION.md` §9:

```sh
cd .softhouse/capture/periodratio && find . -type f | sort | xargs shasum -a 256
```

## Determinism check

```sh
T39_OUT_PREFIX=t39-determinism bash .softhouse/capture/periodratio/src/run-periodratio.sh
diff .softhouse/capture/periodratio/out/t39-periodratio.json \
     .softhouse/capture/periodratio/out/t39-determinism.json      # must print nothing
```

On the recorded run this produced **no output** — the payload is byte-identical from a fresh
container. Only the log's wall-clock timestamps differ between runs.
