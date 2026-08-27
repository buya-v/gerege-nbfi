# Reproducing the T37 DEC-1 §8 binding captures

Path A — the embeddable seam, **in process**. No Fineract server is started and no PostgreSQL
is contacted; this seam reaches no database at all. (The PostgreSQL-only rule still governs the
program; it simply has no bearing on this seam.)

## Preconditions — a failure here INVALIDATES the capture, it does not warn

```sh
# 1. the pinned source, clean and at the pin of record
git -C /Users/buv/fineract rev-parse HEAD          # 426a23544e8426a38ae43ae404670a0a7e85b9eb
git -C /Users/buv/fineract status --porcelain      # must be empty

# 2. the pinned image
docker image inspect fineract:latest --format '{{.Id}}'
# sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a

# 3. the seam-class copy is byte-identical to the pinned original.  ANY OUTPUT INVALIDATES
#    THE CAPTURE — it would mean the run did not execute the oracle's code.
diff .softhouse/capture/dec1-binding/src/EmbeddableProgressiveLoanScheduleGenerator.java \
     /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java
```

The seam class is compiled from source because it is **not** bundled in
`/app/fineract-provider.jar`. Everything else it calls comes from that jar.

**Do not start, stop or reconfigure `fineract-fineract-1` / `fineract-db-1`.** The container
below is `--rm` and isolated; keep it that way.

## Run, from the repo root

```sh
docker run --rm --user 0 --entrypoint sh \
  -v "$PWD/.softhouse/capture/dec1-binding:/cap" fineract:latest -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CaptureBinding.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" CaptureBinding \
      > /cap/out/t37-binding-raw.json 2> /cap/out/t37-binding-stderr.txt
'
```

Only `.softhouse/capture/dec1-binding` is mounted, so the run cannot write to
`.softhouse/capture/src|out|pathb`.

## Post-step — split the oracle's own log off the front of stdout, and KEEP it

The oracle's SLF4J logger writes `MoneyHelper` initialisation lines to **stdout**, ahead of the
JSON. They are evidence, not noise: they independently corroborate which rounding mode each
case's tenant got.

```sh
cd .softhouse/capture/dec1-binding/out
grep -n '^{' t37-binding-raw.json | head -1          # -> 12 on the recorded run
head -n 11 t37-binding-raw.json > t37-binding-log.txt
tail -n +12 t37-binding-raw.json > t37-binding.json
python3 -m json.tool t37-binding.json > /dev/null     # must parse
```

`t37-binding-raw.json` is kept verbatim as well — it is the unsplit stdout exactly as the
oracle produced it.

## Analysis (contacts no oracle)

```sh
cd .softhouse/capture/dec1-binding/analysis
python3 select_shapes.py   # shape selection, run BEFORE the capture: does each candidate
                           # separate the readings at all?  Re-derivation only.
python3 discriminate.py    # observation vs both readings, cell by cell.  The verdict per item.
```

Then verify every digest in `ATTESTATION.md` §8:

```sh
cd .softhouse/capture/dec1-binding && find . -type f | sort | xargs shasum -a 256
```

## Determinism check

Re-running the docker block into a scratch file and `diff`-ing the JSON payload against
`out/t37-binding.json` produced **no output** on the recorded run. Only the log's wall-clock
timestamps differ between runs.
