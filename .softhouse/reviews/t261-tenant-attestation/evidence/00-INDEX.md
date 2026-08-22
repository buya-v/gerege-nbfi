# T261 evidence — what each file is, so no run is mistaken for another

Every capture under `redA/`, `redB/`, `redC/` is a REAL exchange with the live
reference oracle (Fineract, `https://localhost:8443`) made during this review.
Nothing is synthesised.

| file | what it is |
|---|---|
| `10-t261-population-base.txt` | MY independent population sweep, T250 base tree `a71c140`. Wider selector than T250's (adds `.write(` and heredoc emitters). **TERM 2 = 4.** |
| `11-repro-t250-inst10-base.txt` | T250's OWN instrument 10, population source repointed at `a71c140`. **RATE 4 / 29** — reproduces its claim exactly. |
| `12-cap-defect-lines.txt` | The tenant / auth / content-type lines of all four `cap*.sh`, by line number, read directly. |
| `13-t261-tenant-term-base.txt` | MY independent tenant split. **A=52 B=6 literal=6 DERIVED=0 D=46.** |
| `14-repro-t250-inst12-base.txt` | T250's OWN instrument 12, repointed. **A=50 B=5 literal=5 DERIVED=0 D=45** — reproduces exactly. |
| `15-t261-population-finish.txt` | P-69 finish re-measure at `d2b5772`. TERM 2 4 → 5; the +1 is instrument 10 matching its own calibration fixture, exactly as T250 self-reported. |
| `20-redA.txt` | Independent live reproduction of the F-2 defect. Sent `default`, legacy sidecar said `gerege`, HTTP 200. |
| `30-redB-attack.txt` | 11 attacks on the tamper-detector, none in T250's arm set. **7 detected / 4 MISSED.** |
| `40-redC-wrap.txt` | The `--trace-ascii` 64-byte wrap fix swept across the boundary (1…4000 bytes). All EXACT. Also the duplicated-identical-header gap, CRLF injection, and the multibyte body. |
| `50-vector-census.txt` | 62 files in the pinned tree / 59 vectors / **0 with a `tenant` field**. Parsed with `parse_float=str`. |
| `60-guard-on-t250-tree.txt` | The unmodified wire-float round-trip guard run over T250's tree: **exit 0, clean.** |
| `61-fixture-location.txt` | Where the deliberately-malformed fixture ended up, asked of the guard's OWN `derive()`, plus the counter-check that renaming it back to `*.req` makes the guard reach it and refuse it. |
| `70-instrument-audit.txt` | T250's 7 instruments: engine purity and calibration/abort, per file. |
| `71-caller-and-trap.txt` | **0 external callers** of `oracle_send`/`wire_attestation` in T250's tree; and the EXIT-trap clobber driven red with a control arm. |
| **`90-bar.txt`** | **FULL log of the FINAL BAR — my worktree + T250's 130 files. VERDICT PASS, exit 0.** |
| `92-bar-merged-T250.txt` | Summary of that same final run: probe PRESENCE first, then value; frontier 11 == pinned 11; 9/9 exemption pins. |
| `91-bar-baseline-noT250*.txt` | Attribution run with T250's files held aside — also PASS. |
| `93-bar-FAILING-run-tmp-race.txt` | **A BAR run that EXITED 2.** Kept deliberately. Its cause is finding **F-11**: the fail-open frontier flips on whether `/tmp/t234_matrix2.txt` exists. It is NOT T250's defect and NOT this review's verdict. |
