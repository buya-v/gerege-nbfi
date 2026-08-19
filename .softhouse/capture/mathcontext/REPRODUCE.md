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

---

## T46 — reproducing the audit corrections

Everything in this section was added by T46 to close the T44 audit's findings M-1…M-11
(`.softhouse/reviews/T44-capture-audit.md` §3). No T42 payload was modified.

### M-3 — distinct coverage of the E1 matrix (contacts no oracle)

```sh
cd .softhouse/capture/mathcontext
python3 analysis/t46_distinct_coverage.py            # reads out/t42-mathcontext.json only
```

Recorded result (`analysis/t46_distinct_coverage-output.txt`): 13 `-A` baselines, **4** of them
byte-identical to `plain`, so **10 distinct**; `plain` vs `multiples1000` differ in **0 of 74**
cells; period-1 total `212787.28` on both, not a multiple of 1000.

### M-1 / M-2 — the hard-coded `MathContext` inventory (contacts no oracle)

```sh
bash analysis/t46_mathcontext_inventory.sh /Users/buv/fineract
```

Every line is a grep hit with `file:line`; nothing is derived. Recorded result:
`analysis/t46_mathcontext_inventory-output.txt`.

### M-11 — the 172 control cells, published

```sh
python3 analysis/controls.py                          # default: the original 2-line summary
                                                      # sha256 4b847fc9…72548d, unchanged
T42_CONTROLS_VERBOSE=1 python3 analysis/controls.py    # every compared cell, one per line
# or: python3 analysis/controls.py --verbose
```

Recorded verbose result: `analysis/t46-controls-cells-output.txt` — 172 cells, 172 MATCH.

### M-6 — the Path B slot assertion, positive and negative

```sh
bash src/t46-assert-pathb-slot.sh
```

Re-reads the deployed bytecode off the running `fineract-fineract-1` with `javap` (**read-only**:
it unzips two `.class` files into a fresh `/tmp/t46j` inside the container; nothing is restarted,
re-tenanted, reconfigured or written), asserts A1/A2/A3 on both the committed transcript and the
re-read, then asserts them against a slot-drifted copy which it must reject. Recorded result:
`analysis/t46-pathb-slot-assertion-output.txt` — PASS, PASS, FAIL(6).

### M-8 — the vacuity guard, exercised

```sh
bash src/t46-negative-vacuity.sh      # no container; extracts the shipped guard and corrupts
                                      # only the ambientCanary field
```

Recorded result: `out/negative/t46-n7-vacuity-guard.txt` — guard fires (exit 1) on the corrupted
payload, silent (exit 0) on the clean one, 140,978 observed cells identical between the two.

### M-5 — the re-emission with the object echo, and its identity proof

```sh
python3 analysis/t46_make_capture3.py   # regenerate src/CaptureMathContext3.java
bash src/run-mathcontext3.sh            # throwaway `docker run --rm`; refuses to publish
                                        # unless the identity proof passes
bash src/t46-negative-identity.sh       # prove the identity check is failable
```

Recorded results: `analysis/t46-m5-identity-proof.txt` (147,630 of 147,634 leaves byte-identical,
4 enumerated harness self-frames exempt, 856 keys added, 0 object/intent disagreements over 214
cases) and `out/negative/t46-n9-identity-check-failable.txt`.

`run-mathcontext3.sh` moves its payload to `*.json.REJECTED` and exits non-zero if the identity
proof fails; `out/negative/t46-n8-identity-check-rejects.txt` is the transcript of that happening.

### Digests

```sh
cd .softhouse/capture/mathcontext && find . -type f | sort | xargs shasum -a 256
```

Compare against `ATTESTATION.md` §9 (T42 artefacts) and §9.1 (T46 artefacts, including the two
T42 files whose digests moved and why).
