# Reproducing capture pass 2

Everything below runs against the pinned reference oracle **image**, in-process. It does **not** start the
Fineract server and does **not** touch PostgreSQL — the embeddable schedule-generator seam is a library call.
(The PostgreSQL-only rule still governs the program; this seam simply reaches no database.)

Preconditions:

- Docker running, and the pinned image present as `fineract:latest` with digest
  `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`. Verify before trusting a rerun:

  ```sh
  docker image inspect fineract:latest --format '{{.Id}}'
  ```

- The seam class copy is byte-identical to the pinned original. Verify:

  ```sh
  diff .softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java \
       /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
  ```

  No output = identical. **Any output invalidates the capture** — it would mean the run did not execute the
  oracle's code. The seam class must be compiled from source because it is not bundled in
  `/app/fineract-provider.jar`.

Run, from the repo root:

```sh
docker run --rm --user 0 --entrypoint sh -v "$PWD/.softhouse/capture:/cap" fineract:latest -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/Capture2.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" Capture2 > /cap/out/capture-tenant-raw.json 2> /cap/out/capture-tenant-stderr.txt
'
```

Post-step: the oracle's own SLF4J logger writes `MoneyHelper` initialisation lines to **stdout**, ahead of the
JSON. Split them out (they are kept, not discarded — they independently corroborate which rounding mode each
tenant got):

```sh
F=.softhouse/capture/out/capture-tenant-raw.json
S=$(grep -n '^{' $F | head -1 | cut -d: -f1)
head -n $((S-1)) $F > .softhouse/capture/out/capture-tenant-log.txt
tail -n +$S $F > /tmp/ct.json && mv /tmp/ct.json $F
```

Findings and their evidence: `.softhouse/capture/PASS2-REPORT.md`.
