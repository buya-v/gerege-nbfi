# Reproducing the T42 MathContext-in-force captures

Path A — the embeddable seam, **in process**, in throwaway `docker run --rm` containers. No
Fineract server is started and no PostgreSQL is contacted; this seam reaches no database at all.
(The PostgreSQL-only rule still governs the program; it simply has no bearing on this seam. Both
runner scripts nonetheless prove the oracle classpath has zero Oracle Database / MySQL / MariaDB
entries.)

**Do not start, stop or reconfigure `fineract-fineract-1` / `fineract-db-1`.** Every capture
container is `--rm` and mounts only `.softhouse/capture/mathcontext`. `read-pathb-wiring.sh`
does `docker exec` into the *running* `fineract-fineract-1` but is **read-only**: it runs `javap`
and `unzip` into `/tmp` inside that container and never restarts, re-tenants, reconfigures or
writes schema.

## The three commands

```sh
bash .softhouse/capture/mathcontext/src/run-mathcontext.sh    # capture 1: the ambient/threaded matrix
bash .softhouse/capture/mathcontext/src/run-mathcontext2.sh   # capture 2: precision sweep + wiring
bash .softhouse/capture/mathcontext/src/read-pathb-wiring.sh  # Path B wiring, from the DEPLOYED bytecode
```

Each is a **precondition script, not a wrapper**. Any breach prints `BREACH: …` and exits 1. A run
that does not print `== PASS -- capture admissible` produced nothing admissible.

`run-mathcontext.sh` checks: the pin, the cleanliness of the pinned checkout, the image id, the
seam-class bytes, the container exit code, stderr, JSON parseability, **that the ambient-absence
probe is not vacuous**, that every case's threaded and ambient contexts are exactly what its id
declares, that the controls and the calibration produced observations, and the classpath's
freedom from prohibited drivers.

`run-mathcontext2.sh` additionally asserts **the wiring**: a `PATH_A_INDEPENDENT_MC` case must
hand the generator its own `(19, HALF_UP)` whatever the tenant is, and a
`PATH_B_AMBIENT_SOURCED_MC` case must hand it a `MathContext` *equal to the ambient reading*
whatever the tenant is. That assertion is the experiment.

Both recipes and the control suite have been **proved failable** on six axes — see
`NEGATIVE-TESTS.md`.

## Preconditions, if you want to check them by hand

```sh
git -C /Users/buv/fineract rev-parse HEAD          # 426a23544e8426a38ae43ae404670a0a7e85b9eb
git -C /Users/buv/fineract status --porcelain      # must be empty
docker image inspect fineract:latest --format '{{.Id}}'
# sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a

# the seam-class copy must be byte-identical to the pinned original.  ANY OUTPUT INVALIDATES
# THE CAPTURE -- it would mean the run did not execute the oracle's code.
diff .softhouse/capture/mathcontext/src/EmbeddableProgressiveLoanScheduleGenerator.java \
     /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
```

The seam class is compiled from source because it is **not** bundled in
`/app/fineract-provider.jar`. Everything else it calls comes from that jar.

## What the runs write (under `out/`)

| file | what |
|---|---|
| `t42-mathcontext.json` | capture 1's payload — 214 cases: the calibration, 4 reproduction controls, the 13×5 ambient/threaded matrix, the 48×3 precision sweep |
| `t42-mathcontext2.json` | capture 2's payload — 140 cases: the 62-shape precision bisection and the 16 wiring cases |
| `t42-*-raw.json` / `-log.txt` / `-stderr.txt` | verbatim stdout; the oracle's own SLF4J lines split off the front; stderr (must be empty) |
| `t42-*-oracle-identity.txt` / `-classpath.txt` | jar sha256, `java -version`, the jar's own `git.properties`, the 348 classpath entries |
| `t42-pathb-wiring.txt` | `javap -p -c` of the **deployed** `LoanScheduleAssembler` and `LoanScheduleGeneratorServiceImpl`, read inside the running server |
| `negative/` | the six negative-run transcripts |

## Analysis (contacts no oracle)

```sh
cd .softhouse/capture/mathcontext/analysis
python3 controls.py      # 172 cells vs TRANSCRIBED literals.  exit 1 on any mismatch.
python3 discriminate.py  # capture 1: the matrix and the first precision sweep
python3 discriminate2.py # capture 2: the precision bisection and the two wirings
python3 count_cells.py   # how many cells were actually compared
```

Then verify every digest in `ATTESTATION.md` §7:

```sh
cd .softhouse/capture/mathcontext && find . -type f -not -path './out/negative/*' | sort | xargs shasum -a 256
```

## Determinism check

```sh
T42_OUT_PREFIX=t42-determinism  bash .softhouse/capture/mathcontext/src/run-mathcontext.sh
T42_OUT_PREFIX=t42-determinism2 bash .softhouse/capture/mathcontext/src/run-mathcontext2.sh
diff out/t42-mathcontext.json  out/t42-determinism.json    # must print nothing
diff out/t42-mathcontext2.json out/t42-determinism2.json   # must print nothing
```

On the recorded runs both produced **no output** — the payloads are byte-identical from fresh
containers (sha256 `f2a037a1…6553` and `f7ffeb2a…6b84`). Only the log's wall-clock timestamps
differ between runs.
