# T117 — how to reproduce the family-B extent probe

Task **T117**, gate **G-8**. Local-fire-only work: this needs the pinned Fineract image on the
host that has it. **The oracle here is the Fineract reference implementation. Oracle Database is a
prohibited product and this probe opens no database connection at all** — it starts no server and
does not touch `fineract-fineract-1` / `fineract-db-1`; it runs a throw-away `docker run --rm` from
the pinned image and calls the in-JVM Path A embeddable seam.

## Pass 1 — 200 probe cases + 2 rig calibrations

```bash
# 1. registered prediction and case list (writes prediction.json, /tmp/t117-cases.java,
#    /tmp/t117-ids.json). Committed in a STRICT ANCESTOR of the capture — commit a9a2e53.
python3 src/gencases.py

# 2. derive the harness mechanically from the committed CaptureT100.java (no file is edited)
python3 src/build_harness.py

# 3. stage the probe directory and run against the pinned image
rm -rf /tmp/t117probe && mkdir -p /tmp/t117probe/src /tmp/t117probe/out
cp src/CaptureT117.java src/postcheck.py /tmp/t117probe/src/
cp /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/\
org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java \
   /tmp/t117probe/src/
bash src/run-t117.sh <repo-root>

# 4. analysis (all of it in integer minor units / Fraction / Decimal — P-25)
python3 src/classify_t117.py     out/capture-t117-raw.json.gz prediction.json > out/t117-classified.json
python3 src/shape_check.py       out/capture-t117-raw.json.gz                 > out/shape-check.json
python3 src/ctrl_reproduction.py out/capture-t117-raw.json.gz                 > out/ctrl-reproduction.json
python3 src/tie_profile.py       out/capture-t117-raw.json.gz                 > out/tie-profile.json
python3 src/threshold_exact.py                                                > out/threshold-exact.json
```

### Pinned facts asserted by `run-t117.sh` BEFORE the run (it exits 1 and names the breach otherwise)

| Fact | Value |
|---|---|
| image ref / id | `fineract:latest` / `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` |
| Fineract commit | `426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean |
| seam source | `cmp`-identical to the pinned checkout **and** sha256 `bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714` |
| calibration reference | `.softhouse/capture/out/capture-prod3g-raw.json` sha256 `6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91` |
| harness | `CaptureT117.java` sha256 `6f218e58af87fb0d4ab2ea4ae18097938dc4fddfbfc32f5f6d16d4ee221fe504` |
| run id | `t117-20260821T080240Z` |

### Postconditions asserted AFTER the run (`src/postcheck.py`)

- emitted id list **equals the registered list exactly and in order** — 202 ids;
- every case at `(19, HALF_UP)` threaded **and** ambient, MNT, dp 2, DAYS_30/DAYS_360, MONTHS/1,
  no down payment, both multiples-of inputs null, `fixedLength` null — the graded domain;
- every case emits exactly `numberOfRepayments` REPAYMENT rows;
- `stderr` empty; `observed` non-null on every case; no `error` key on any case;
- `P-CAL-ZPA` / `P-CAL-ZPB` reproduce pass 3g's `T64-ZP-A` / `T64-ZP-B` **cell for cell with 0 input
  diffs**;
- attestation `gitCommitId` matches the pin and `gitDirty` is `false`.

Runner output, verbatim:

```
capture OK: 202 cases, 93433 emitted period rows, canonical sha256 1568885c6acfba7e39f9eec85d0ada907c7281d80cd6e0687af7a31a06c4bb31
  id list matches the registered list exactly and IN ORDER: 202 ids
  calibrations P-CAL-ZPA/ZPB reproduce T64-ZP-A/B cell-for-cell, 0 input diffs
RUNNER EXIT 0
```

### Digests — name the canonicalisation (P-38)

| Artefact | sha256 |
|---|---|
| `capture-t117-raw.json` (uncompressed, as emitted; **not committed**, 21,622,784 bytes) | `27c507767af40c332c7f771d09f80f73884748ae718bbd2f6d08a77055a0994f` |
| `out/capture-t117-raw.json.gz` (`gzip -9`, **this is the committed artefact**) | `bb0bdcdb758ff54e89e65a5af7c2706de580e26836d132fd63ecdaed57d98199` |
| canonical digest over the `captures` array | `1568885c6acfba7e39f9eec85d0ada907c7281d80cd6e0687af7a31a06c4bb31` — sha256 of `json.dumps(doc['captures'], sort_keys=True, separators=(',',':'))` UTF-8 encoded |

`gunzip -c out/capture-t117-raw.json.gz | shasum -a 256` reproduces the uncompressed digest, and
`classify_t117.py` produces an **identical** classification from the `.gz` and from the plain JSON
[VERIFIED this fire]. P-32 still applies to any *other* pair of artefacts in this program: check
which one is the capture before analysing it.

## Pass 2 — how far up in principal does family B go?

Pass 1 refuted the registered prediction that the failing principal cannot exceed one minor unit.
Pass 2 asks the same seam for larger **odd** principals; its own prediction is registered in
`PREDICTION-PASS2.md` / `prediction-pass2.json`, committed in a strict ancestor of its capture, and
it is reproduced by the same four steps with `src/gencases_pass2.py`, `src/build_harness_pass2.py`,
`src/run-t117-pass2.sh` and `src/postcheck_pass2.py`.

## What is NOT here

No vector was added. `PIN.json`, `capabilities.json`, `contract.go` and every ratified DEC-n are
untouched, and `gofmt -w` was never run. This directory is a **measurement**, not a promotion.
