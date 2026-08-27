# READ THIS BEFORE RUNNING `30-redB-mismatch-detected.sh`

Added by **T284**. Nothing in this directory was edited — this file is new, and every
pre-existing byte here and under `../evidence/` is unchanged.

## Do not run it in place

Its first act is `rm -rf` over `../evidence/redB`, which is **committed evidence** *and* the
input to T274's `P1` control in
`.softhouse/capture/t274-attestation-failopen/instruments/10-four-routes-red-green.sh:224`.
T283 did this to itself and spent an iteration reading the result as a regression
(finding `F-T283-6`).

## What it does today, and why that is correct

Since **T274** every fresh capture through `oracle_send` is sidecar **schema 2**. This
instrument's `verify` call at **line 74** presents no response artefacts, so the verifier
**REFUSES** (exit 2) rather than issuing a verdict it cannot support.

Measured on branch `softhouse/t284-schema2-callsites`
(`.softhouse/capture/t284-schema2-callsites/evidence/RED-site1.txt`):

```
arms as expected: 2    arms NOT as expected: 6
RED-DRIVE B: FAIL
EXIT=1
```

**The refusal is the contract working.** It is not a regression in the verifier.

Note also that **arm 3 scores `ok` for the wrong reason**: its stated test is "header record
DELETED → must refuse", and the refusal it actually receives is the *schema* refusal. That arm
measures nothing today.

## T284's decision: RE-FROZEN, SCOPED TO SCHEMA 1

The instrument is **frozen** — T114's standing ruling: *anything that produced committed
evidence is superseded by a scratch copy, never edited in place*. It produced 127 committed
files under `../evidence/`, including the per-arm `verify.out` / `verify.err` that **are** the
output of that call. So it is not edited. Its arms are retained by two successors:

| what you want | run this |
|---|---|
| the eight arms against T250's **committed schema 1** corpus, oracle-free | `.softhouse/capture/t284-schema2-callsites/instruments/20-site1-schema1-replay.sh` |
| the eight arms against a **fresh schema 2** capture, live | `.softhouse/capture/t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh` |

Both were run on `softhouse/t284-schema2-callsites`; transcripts under
`.softhouse/capture/t284-schema2-callsites/evidence/`.

The full decision record is
`.softhouse/capture/t284-schema2-callsites/SUPERSEDES.md`, and this file's existence is
**enforced**, not merely hoped for: `.softhouse/capture/t284-schema2-callsites/instruments/
10-callsite-registry.py` pins this call site, its class and this instrument's sha256, and
fails if any of them moves.
