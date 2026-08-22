# T207 — `t44_float_roundtrip_v2.py` is SUPERSEDED by `T207/t44_float_roundtrip_v3.py`

## Which one is authoritative

| file | status |
|---|---|
| `T207/t44_float_roundtrip_v3.py` | **AUTHORITATIVE.** Use this one. |
| `t44_float_roundtrip_v2.py` | **RETAINED, BYTE-IDENTICAL, DO NOT RUN FOR A NEW ANSWER.** It reports `PASS` and exits 0 on a value-corrupted money literal (T185 F-1, proven in `T207-red/`). It is the instrument that produced the `_v2` transcripts inside `T175-red/drive-red-output.txt`. |
| `t44_float_roundtrip.py` | **RETAINED, BYTE-IDENTICAL, DO NOT RUN FOR A NEW ANSWER.** T175's ruling stands unchanged: it produced `t44_float_roundtrip-output.txt`, which `T44-capture-audit.md §T44-X1` cites. |
| `t44_float_roundtrip-output.txt` | **RETAINED, BYTE-IDENTICAL.** Re-verified this fire: the original still reproduces it byte-for-byte. |
| `T175-red/drive-red.sh`, `T175-red/drive-red-output.txt`, `T175-red/census.py` | **RETAINED, BYTE-IDENTICAL.** Widened scratch copy at `T207/T207-red/drive-red-v3.sh`. |

Recorded digests, taken this fire and unchanged by T207 (nothing under
`audit-t44/analysis/` outside `T207/` was written):

```
2f968545261f56b704db447f0c4416bf02c757a0b2b041bb7146c7a4eab4179b  t44_float_roundtrip.py
```

(the same value T175 recorded; re-computed and re-checked — see the handoff for the full set)

## Why `_v2` is retained rather than fixed

T114's standing ruling. `_v2` produced committed evidence — the `_v2` transcripts embedded in
`T175-red/drive-red-output.txt`, which is what LEGs 1–5 of T175's battery record. Editing `_v2`
would silently change what that transcript is a transcript *of*, and would make T175's committed
red/green claim unreproducible from the file next to it.

## The defect

`_v2:170-190` computes `lossy_value` — the literals whose **value** changes under a binary-double
round trip — prints them, and never appends them to `failures`. `_v2:206` therefore prints

    T175 SUCCESSOR: PASS -- 1 of 1 files scanned, 0 skipped, 5 distinct literals inspected.

and returns 0, on a corpus in which **3 of 5 literals are value-corrupted** — including one whose
residue is a **whole tugrik** (`9007199254740993.00` → `9007199254740992.0`). Proven, not argued:
`T207-red/drive-red-v3-output.txt`, LEG V-RED.

The PASS banner is **new in `_v2`**. The original has no `main()`, no `sys.exit`, no `failures`,
and the strings `PASS`/`FAIL` do not occur in it or in its committed transcript.

## Why fixing it was a DECISION and not a repair

`_v2:169` carries `# HAZARD CHARACTERISATION ONLY - these floats never touch a verdict.` Making
`lossy_value` fail the run puts a float-derived predicate on a verdict path, which that line
forbids. The ruling — Zone A, response leg, predicate may and must gate — is argued in full in
`T207/RULING-float-derived-predicate.md`. In one line:

> T186 rule A1 **already** gates `conformance.sh` on `repr(float(tok)) == tok`, a predicate that
> cannot be evaluated without a float. The non-negotiable bans a float from **carrying value**, not
> from **being measured**. `_v2:169` was true of the ORIGINAL, which has no verdict; T175 gave the
> file a verdict and carried the sentence over unchanged.

## What the successor changes

R1 value-loss fails the run · R2 text-loss explicitly does **not** gate, with T186 A4's reason
printed every run · R3 the false self-description removed · R4 no bare `PASS`; an explicit
`DOES NOT ESTABLISH` list · R5 population stated, `NIL-COVERAGE` shape on an empty one ·
R6 `--selftest` driving both directions · R7 `_v2`'s skip and zero-input behaviours kept verbatim.

**The arithmetic is unchanged.** Over the same 92-file charges corpus `v3` reports the identical
**245 distinct / 9,122 occurrences / max scale 6 / 41 text-lossy / 0 value-lossy**, asserted
leg-by-leg against `_v2` in the battery.

## Driven red AND green

    bash .softhouse/capture/audit-t44/analysis/T207/T207-red/drive-red-v3.sh

transcript at `T207-red/drive-red-v3-output.txt`, exits 0 with **ALL LEGS AS PREDICTED**.

* **LEG 0** — the original still reproduces its committed output byte-identically; and it is
  measured to contain no verdict machinery, so the banner is provably new in `_v2`.
* **LEG V-RED** — a value-corrupted `numeric(19,6)` corpus: `_v2` exits **0** printing `PASS`;
  `v3` exits **1** naming every literal and its exact residue.
* **LEG V-GREEN** (P-50) — the legitimate corpus: `v3` exits **0** with figures identical to `_v2`'s.
* **LEG T** — 41 text-lossy literals present and `v3` still exits 0, so it provably did **not**
  tighten onto byte-fidelity and refuse the oracle's own `DECIMAL(19,6)` emissions.
* **LEG S** — every `_v2` skip behaviour preserved: 18 unacknowledged skips refuse;
  `--expect-skips 18` accepts; `--expect-skips 17` refuses; an empty glob refuses.
* **LEG X** — `v3 --selftest`: 10 cases, 4 fire the value gate, 3 fire only the text predicate.
* **LEG D-GREEN / D-RED** — F-3's `cells()` drop counter, green on the real corpus (0 of 1,554)
  and red on a planted root (6 of 6 dropped), with the committed tool shown reporting
  `money deltas CONSIDERED : 0` and exiting 0 in silence on that same root.

## Reproduce

    bash .softhouse/capture/audit-t44/analysis/T207/T207-red/drive-red-v3.sh

    python3 .softhouse/capture/audit-t44/analysis/T207/t44_float_roundtrip_v3.py --selftest

    # the authoritative instrument, on the original's own corpus:
    python3 .softhouse/capture/audit-t44/analysis/T207/t44_float_roundtrip_v3.py \
        '.softhouse/capture/periodratio/out/*.json' \
        '.softhouse/capture/mathcontext/out/*.json' \
        '.softhouse/capture/charges/out/fc/*.json' \
        '.softhouse/capture/charges/out/attested/*.json' \
        --expect-skips 18

## Still not wired to anything

T185's F-4 stands, now for `v3` too: no harness, no CI and no `conformance.sh` entry drives this
instrument. `conformance.sh` is held by another worker this fire and is outside T207's scope.
Named as a tail, not silently left.
