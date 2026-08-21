# T175 — `t44_float_roundtrip.py` is SUPERSEDED by `t44_float_roundtrip_v2.py`

## Which one is authoritative

| file | status |
|---|---|
| `t44_float_roundtrip_v2.py` | **AUTHORITATIVE.** Use this one. |
| `t44_float_roundtrip.py` | **RETAINED, BYTE-IDENTICAL, DO NOT RUN FOR A NEW ANSWER.** It is the instrument that produced the committed `t44_float_roundtrip-output.txt`, which the T44 audit cites. |
| `t44_float_roundtrip-output.txt` | **RETAINED, BYTE-IDENTICAL.** True about the run it records; see "what it does not say" below. |

## Why the original is retained rather than fixed

The original produced committed evidence, and under T114's standing ruling committed evidence
is not edited in place. Editing it would silently change what `T44-capture-audit.md §T44-X1`
cites, and would make the committed output unreproducible from the file next to it. It is kept
so the audit trail stays checkable; it is superseded so nobody takes a new answer from it.

sha256 of the original, recorded before and after all T175 work, unchanged:

    2f968545261f56b704db447f0c4416bf02c757a0b2b041bb7146c7a4eab4179b  t44_float_roundtrip.py

## The defect

`t44_float_roundtrip.py:26-30`:

    for p in paths:
        try:
            json.load(open(p), parse_float=hook)
        except Exception:
            pass

A file the scan cannot parse is skipped **without a word**. Everything the script then prints
— distinct literals, total occurrences, max scale, "literals whose float VALUE != the decimal"
— is a statement about an inspected denominator the reader is never told. Handed a glob that
matches nothing parseable it prints `distinct: 0`, `occurrences: 0`, and then

    => no literal changes VALUE on a float round-trip at these magnitudes and scales,
       so no committed charges number is corrupted TODAY.

which reads as a clean bill of health for a scan that read zero files. That is a vacuous pass
sitting on the first non-negotiable in `CLAUDE.md`.

Its own sibling `t44_float_scan.py:44-46` gets this right — it prints `UNPARSEABLE (…)` and
names the file — which is how we know the corpus really does contain unparseable inputs.

## What the committed output does not say, measured

Re-running the original today with the recipe that reproduces its committed output
**byte-identically** shows it was handed **128 files** and silently skipped **18** of them
(nine `periodratio/out/*-raw.json`, nine `mathcontext/out/*-raw.json`; all are JVM stdout logs
carrying a `.json` extension, so `json.load` raises `Extra data: line 1 column 2`). The
committed output contains **zero** occurrences of "skip", "unparse", "unscanned", "error" or
"fail".

The measured consequence is in `T175.md`: the 18 files embed their JSON payload after the log
lines, and that payload carries **0** bare non-integer numbers, so the committed 245/9122/0
figures are **still supported**. That was never checked before T175 — it was true by luck, not
by test.

## What the successor changes, and nothing else

1. **Skip register.** Every unparseable file is named (path, exception type, message) and
   counted; the register prints on every run, including a run with zero skips.
2. **A non-zero skip count fails the run** unless the caller acknowledges it with
   `--expect-skips N`, which must match exactly. The count is printed prominently either way
   and is never rendered as zero.
3. **Zero inspected is an ERROR (P-35)** — zero globs, zero matched files, or zero literals
   found each fail rather than producing a confident report about nothing.
4. **Every figure is scoped to its denominator in the line that prints it** ("over N of M
   requested files"), including the closing hazard paragraph.

The arithmetic is unchanged: over the same 92-file charges corpus the successor reports the
same **245 distinct literals / 9,122 occurrences / max scale 6 / 41 text-lossy / 0
value-lossy** as the original. This is a fix, not a rewrite.

## Driven red

`T175-red/drive-red.sh` (run with **bash**, never `sh`), transcript committed at
`T175-red/drive-red-output.txt`, exits 0 with **all legs as predicted**:

* **LEG 0** — the original reproduces its committed output byte-identically, so every leg
  below is about *that* run.
* **LEG 1** — real corpus: 18 unparseable files; 0 mentions of them in the original's output;
  the successor exits 1 and names all 18.
* **LEG 2** — planted `PLANTED-not-json.json` alone in a directory: the original prints the
  full clean-bill-of-health paragraph having read **zero** files; the successor exits 1 and
  names the file.
* **LEG 3** — a glob matching nothing: same vacuous pass from the original; the successor
  calls zero-inspected an ERROR.
* **LEG 4** (the other half, P-50) — charges-only corpus, 92 of 92 parsed, 0 skipped: the
  successor **exits 0** with the identical 245/9122/0 figures.
* **LEG 5** — `--expect-skips 18` is accepted and still prints 18; `--expect-skips 17` is
  refused.

## Reproduce

    bash .softhouse/capture/audit-t44/analysis/T175-red/drive-red.sh

    # the authoritative instrument, on the original's own corpus:
    python3 .softhouse/capture/audit-t44/analysis/t44_float_roundtrip_v2.py \
        '.softhouse/capture/periodratio/out/*.json' \
        '.softhouse/capture/mathcontext/out/*.json' \
        '.softhouse/capture/charges/out/fc/*.json' \
        '.softhouse/capture/charges/out/attested/*.json' \
        --expect-skips 18
