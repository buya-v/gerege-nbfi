# READ THIS BEFORE RUNNING `t261-redB-attack.sh` OR `t261-redC-wrap.sh`

Added by **T284**. Nothing in this directory was edited — this file is new, and every
pre-existing byte here and under `../evidence/` is unchanged.

Since **T274** every fresh capture through `oracle_send` is sidecar **schema 2**. Both
instruments call `verify` with request-only arguments, so the verifier **REFUSES** (exit 2).
That refusal is the contract working, not a regression in the verifier — but it leaves both
instruments dead, and one of them dead *quietly*.

## `t261-redB-attack.sh` — dead, LOUDLY

Its calibration positive control refuses, and the script correctly **ABORTS at exit 4 with
zero of its eleven attacks scored**, rather than grading against a broken baseline. Measured:
`.softhouse/capture/t284-schema2-callsites/evidence/RED-site2.txt`.

**T284's decision: TAUGHT SCHEMA 2 by a successor.** Six of its eleven attack shapes (A3, A5,
A7, A8, A9, A11) appear in no other instrument in the tree, so retirement would drop coverage.

> Run instead: `.softhouse/capture/t284-schema2-callsites/successors/t284-redB-attack-v2.sh`
> — all eleven shapes plus A12 (the response *header* record swapped, only expressible since
> T274). Measured 12 caught / 0 accepted.

## `t261-redC-wrap.sh` — dead, QUIETLY, and this is the dangerous one

Measured (`.softhouse/capture/t284-schema2-callsites/evidence/RED-site3.txt`):

* all **17** wrap-sweep `verify` calls print `verify FAILED`, and the script still ends
  **`exit 0`** — its exit status is unconditional, so a caller that reads the status sees
  success;
* the `dupid` leg receives rc=2 (the *schema* refusal, nothing to do with header
  multiplicity) and prints **`verify rc=2 DETECTED`** — a refusal scored as a security win;
* the `mbtrunc` leg does the same.

A refusal is the *absence* of a verdict. It is never a detection.

**T284's decision: SPLIT.**

| leg | disposition |
|---|---|
| the 17-length wrap sweep | **RETIRED** onto `.softhouse/capture/t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh`, which runs the identical experiment schema-2-natively |
| duplicate-identical-header multiplicity, CRLF injection, multibyte `Content-Length` and mid-character truncation | **TAUGHT SCHEMA 2** by `.softhouse/capture/t284-schema2-callsites/successors/t284-redC-residual-v2.sh` |

The successor **asserts** the retirement rather than citing it: it fails if T274's instrument
20 is gone or if its length list has moved.

## Frozen means frozen

Both files produced committed evidence — 265 files under `../evidence/`, including the
per-arm `.vout` / `.verr` that **are** the output of these calls. T114's standing ruling:
*anything that produced committed evidence is superseded by a scratch copy, never edited in
place.* Neither file was touched.

The full decision record is `.softhouse/capture/t284-schema2-callsites/SUPERSEDES.md`, and
this file's existence is **enforced**: `.softhouse/capture/t284-schema2-callsites/instruments/
10-callsite-registry.py` pins both call sites, their classes and both files' sha256, and fails
if any of them moves.
