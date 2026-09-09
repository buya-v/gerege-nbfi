# OH-2b — PROMOTE the existing charges captures into parity vectors

WORKING DIRECTORY: /Users/buv/oh-gerege-oh2b  (branch feat/OH2b-charges-promote)
NEVER commit to `main`. NEVER touch the other worktrees.

## READ THIS BEFORE ANYTHING ELSE — the work is half done already
A previous attempt at this failed by trying to invent a capture pipeline from
scratch, spending 923 events and producing nothing. Do not repeat it.

**The oracle observations ALREADY EXIST**, captured by task T40/T46 on fire
20260819-080001 against the reachable oracle:

    .softhouse/capture/charges/     658 files
      bin/   43 scripts, incl. capture.sh, run-preconditions.sh, attest.py
      req/  131 request fixtures, e.g. calc-FC-01-flat-disbursement.json
      out/   20 result sets
      REPRODUCE-T46.md   the recipe, path-independent by design
      ATTESTATION-T46.md

T40's handoff states plainly what they are and what remains:
  "RAW OBSERVED FORM ONLY. NOTHING WAS PROMOTED to the parity vector store...
   Promotion is a separate decision and is explicitly not mine."

It stopped at raw because DEC-1 was UNRATIFIED then and shaping a capture to an
unratified contract would prejudge it. DEC-1 is now at REVISION 12. Promotion is
unblocked. **Promotion is your task.**

## What a promoted vector looks like
Read two from .softhouse/vectors/loanschedule/ and copy the shape exactly. Every
one carries provenance of this form:

  "provenance": {
    "kind": "oracle-capture",
    "note": "TRANSCRIBED, never computed, from ...",
    "capture_ref":    ".softhouse/capture/out/capture-prod3b-raw.json",
    "capture_sha256": "8d23c48f...",
    "capture_case_id": "...",
    "citation": "..."
  }

Yours must cite the CHARGES capture files and their real SHA-256, computed by
you from the file on disk.

## What to do
1. Read REPRODUCE-T46.md and ATTESTATION-T46.md first. They tell you what was
   observed and how.
2. Decide which observations are promotable as parity vectors — the fee and
   penalty behaviour the corpus is blind to. T35 established that every fee and
   penalty in the committed corpus is 0.00, so a Go port "could have got charge
   handling arbitrarily wrong and passed 100% of the corpus." That blindness is
   what you are closing.
3. Write vectors into .softhouse/vectors/charges/, each TRANSCRIBING values from
   the raw captures — never computing, extrapolating or authoring one.
4. Every vector carries `tenant_params`: rounding_mode AND rounding_ordinal,
   precision, currency, minor_units, timezone. The captures were taken under
   `gerege` — HALF_UP, ordinal 4, MNT, 2 minor units, Asia/Ulaanbaatar.
5. Make .../apps/charges/conformance grade them.

## If a capture is stale
The captures are from 2026-08-19. If you find one you cannot trust, you MAY
re-issue it: `sh bin/capture.sh` and `bin/run-preconditions.sh`, which aborts on
any of its 15 breaches. The oracle is UP and tenant `gerege` is restored
(HALF_UP, proved live: 1,162,502.50 x 0.018 -> 20925.05 under gerege, 20925.04
under default). Capture under `gerege`, NEVER `default`.

## Refusals
- NEVER synthesise, compute or author a vector value. Transcribe only.
- Do NOT edit the charges conformance harness to make a vector pass. If it
  refuses your vector, the vector or the port is wrong.
- Do NOT edit any guard, gate, pin or existing vector.
- Do NOT modify the oracle's tenants or schemas.

## DONE means: paste RAW output with exit codes for
   cd nexus && go build ./... && go test ./...
   bash .softhouse/conformance.sh
   the vector count, and ONE full vector JSON including its provenance and
   tenant_params

Report exit codes. Never say complete / done / goal achieved. If an observation
cannot be honestly promoted, leave it and say why — a small true corpus beats a
large invented one.
