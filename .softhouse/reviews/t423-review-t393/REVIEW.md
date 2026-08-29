# T423 — INDEPENDENT review of T393 (`softhouse/T393-t382-conditions`, 11 commits)

## VERDICT: **PROVISIONAL — work in progress**

This file is written EARLY and deliberately incomplete, so that a verdict exists if this
worker is killed the way its predecessor was. It is refined in place as each drive lands.

**Status of the evidence in this directory.** A previous T423 worker committed the four
instruments and the `out/` transcripts at `a12a9a83` and was killed before writing a verdict.
Under this program's rule a killed worker's output is a HYPOTHESIS. This worker re-runs every
instrument and records, per instrument, whether its own output matches the committed one.

| instrument | committed output | re-run by T423-2 | agrees? |
|---|---|---|---|
| `00-t423-independent-counts.py` | `out/00-t423-counts.txt`, `FAILURES: 0` | done | **YES — byte-identical apart from the `ROOT` header line** |
| `10-t423-f4-rerun.sh` | `out/T423-MATRIX.tsv`, 6 rows, 0 unexpected | in flight | pending |
| `20-t423-birth-blob-probe.py` | `out/20-birth-blob-probe.txt` | pending | pending |
| `30-t423-extra-drives.sh` | `out/T423-EXTRA-DRIVES.txt` | pending | pending |

PROVISIONAL leaning: **APPROVED WITH CONDITIONS**. Nothing found so far contradicts T393.
