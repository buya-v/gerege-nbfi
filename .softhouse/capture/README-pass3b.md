# Reproducing capture pass 3b (Path A)

**Supersedes the prose instructions in `README-pass2.md` for Path A captures.** That file described the
recipe; this one is a script that runs it and **fails the run** on any precondition breach. It closes
T21 §10 P0-4.

Everything below runs against the pinned reference-oracle (Fineract) **image**, in-process. It does **not**
start the Fineract server and does **not** touch PostgreSQL — the embeddable schedule-generator seam is a
library call. (The PostgreSQL-only rule still governs the program; this seam simply reaches no database.)

## Run it

From the repo root:

```sh
sh .softhouse/capture/src/run-pass3b.sh
```

That is the whole recipe. It checks its own preconditions, runs the capture, splits the oracle's SLF4J
lines off the front of stdout (keeping them), validates the result, writes the machine-readable attestation
sidecar, and hashes every output.

Optional environment:

- `PINNED_FINERACT` — path to the pinned Fineract checkout (default `/Users/buv/fineract`).
- `CAP_OUT_DIR` — write the outputs somewhere other than `.softhouse/capture/out` (useful for a
  side-by-side determinism check without disturbing the committed artefacts).

## What makes it fail

Non-zero exit, and no capture is left behind that could be mistaken for a good one:

1. docker missing, or the image absent;
2. image id ≠ `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`;
3. the pinned checkout missing, at a commit other than `426a23544e8426a38ae43ae404670a0a7e85b9eb`, or with
   a dirty working tree;
4. **seam-class drift** — `.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java` differing
   from the pinned original by a single byte. The seam class must be compiled from source because it is not
   bundled in `/app/fineract-provider.jar`; if the copy has drifted, the run is not executing the oracle's
   code and the capture is void;
5. non-zero container exit;
6. no JSON document on stdout, or JSON that does not parse;
7. non-empty stderr — a stack trace where a capture was expected;
8. wrong capture count, any `"observed": null`, or any `error` key present;
9. the effective `MathContext` not being the ratified production `(19, HALF_UP)` / RoundingMode ordinal 4;
   the image's `git.commit.id` disagreeing with the pinned checkout; `git.dirty` not `false`; or the
   runner's echoed attestation disagreeing with what the runner itself measured.

## Verifying a re-run

Do not eyeball it. Compare **`capturesCanonicalSha256`** in `out/capture-prod3b-attestation.json`:

```
02e94174cda26540e882d6da0f0ac3aabc02923ddf501a4dde90fd7d60aa38ec
```

That digest covers the canonicalised `captures` array and is **stable across runs**. The whole-file sha256
is not, because the attestation carries a UTC timestamp and a run id — three runs on 2026-08-18 produced
three different file digests and the same canonical digest.

To compare against the older pass-3 corpus, value for value:

```sh
python3 .softhouse/capture/out/t35-byte-identity.py \
        .softhouse/capture/out/capture-prod-raw.json \
        .softhouse/capture/out/capture-prod3b-raw.json
python3 .softhouse/capture/out/t35-newcolumn-checks.py \
        .softhouse/capture/out/capture-prod3b-raw.json
python3 .softhouse/reviews/t21v2/t21v2-invariants.py \
        .softhouse/capture/out/capture-prod3b-raw.json
```

A **VALUE CHANGED** line from the first script is a finding to report loudly, never to reconcile.

## Note on output paths

Every output path in these scripts is a literal filename. A shell glob in an output path cannot expand
against a file that does not exist yet, so `-o out/X-*.json` makes the tool create a file named literally
`X-*.json` — the defect T22 P0-5 found on the Path B side. Do not reintroduce it.

Findings and their evidence: `PASS3B-REPORT.md` (and `PASS3-REPORT.md` for the pass it extends).
