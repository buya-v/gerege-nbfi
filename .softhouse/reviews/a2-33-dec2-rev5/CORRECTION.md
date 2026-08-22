# LABELLED CORRECTION — `sweep.sh` in this directory was repaired by T238 on 2026-08-22

Filed per **T114 / T176**: superseded evidence gets a labelled correction or a successor file,
never a silent edit. This is the label.

Measured at commit `162dddbc4abd302277baf76976f5a50ffae6988b`, forked from `origin/main` at
`477dc2da0f9edf3922e7d29e689bc6473289befc` (**measured**, not asserted — P-71 has been falsified
twice in this program, in opposite directions).

---

## READ THIS FIRST — WHAT IS *NOT* BEING CORRECTED

**DEC-2 revision 5 is RATIFIED and is NOT re-opened. G-11's ratification is NOT undermined.
Nothing in this file, and nothing T238 did, touches `docs/adr/`.** Amending a ratified DEC-n is a
`user` gate and nothing here approaches one.

`A2-33`'s sweep **ran, and it found things.** Its committed transcript
`sweep-output-live-population.txt` carries **34 patterns, ZERO `(no hits)` and 6334 hit lines**,
recorded while its worktree still existed. That transcript is **untouched**, as are
`sweep-counts-full-population.txt`, `sweep-triage.txt`, both recall-calibration files, `REVIEW.md`
and every other artefact in this directory.

**The defect was REPRODUCIBILITY, not the result.**

---

## WHAT WAS WRONG

`sweep.sh:7` hard-coded

```
WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a5244bad2b6814a39
```

a worktree deleted after A2-33 finished, and the body was

```
( cd "$WT" && git grep -n -I -i -E "$re" -- . ) || echo "   (no hits)"
```

When the `cd` fails the subshell exits non-zero, the `||` arm fires, and the script prints
`(no hits)` **for every pattern** and **exits 0**.

Measured by T238, running the original verbatim from the repo root
[`.softhouse/capture/t238-failopen/evidence/red-drive/00-baseline-original.txt`]:

```
ORIGINAL   exit=0    "(no hits)" lines=34    hit lines=34
```

34 patterns declared, 34 reassurances, **zero measurements**. To a later auditor re-running this
instrument to *check* the ratification, that output is indistinguishable from
*"I swept the repository and the concept is absent."* **A sweep that fails OPEN on re-run is worse
than one that cannot run at all, because its silence corroborates whatever the reader already
believed.**

## WHAT CHANGED

| | before | after |
|---|---|---|
| corpus root | hard-coded absolute worktree path | `git rev-parse --show-toplevel`, resolved at run time |
| unreachable corpus | prints `(no hits)`, exits **0** | aborts, exit **90** |
| empty corpus | prints `(no hits)`, exits **0** | aborts, exit **91** (P-35: inspecting nothing is an ERROR) |
| broken engine/pattern | prints `(no hits)`, exits **0** | aborts, exit **92** — calibration on a known positive (P-72) |
| engine error mid-sweep | prints `(no hits)`, exits **0** | aborts, exit **93** |
| a genuine zero | `(no hits)` | `MEASURED ZERO (engine ran over N files and matched nothing)` |
| the string `(no hits)` | 2 occurrences | **0 — removed from the instrument entirely** |
| trailer | none | `SWEEP-RESULT: … patterns=N hit_lines=M calibration=PASS` |

**ALL 34 PATTERNS ARE BYTE-IDENTICAL TO THE ORIGINAL.** Verified: the `^run ` lines of the original
and the repaired file both sha256 to
`6895b1bf930023c1e05a72be564e5aaa7b0f70e9806d88a5e6784e92ec0e3cac`.

## THE ORIGINAL BYTES

The original file is preserved verbatim at
`.softhouse/capture/t238-failopen/evidence/red-drive/sweep-ORIGINAL.sh`.

```
sha256(sweep.sh, as A2-33 committed it) = c076016e292186b8d320b8b7cbab34adc29502d4c54395eda0487551d0e35eb2
```

It is also recoverable at any time with
`git show 477dc2d:.softhouse/reviews/a2-33-dec2-rev5/sweep.sh`.

## THE REPAIR WAS DRIVEN RED, THROUGH THE ROUTE THAT RUNS IT (P-22 / P-45)

`.softhouse/capture/t238-failopen/transcripts/40-red-drive.txt`, committed:

```
RED 1  corpus unreachable (not a git work tree)   exit 90   "(no hits)" lines 0   PASS
RED 2  corpus reachable but tracks ZERO files     exit 91   "(no hits)" lines 0   PASS
RED 3  calibration misses the known positive      exit 92   "(no hits)" lines 0   PASS
RED 4  single-file mode, target does not exist    exit 90   "(no hits)" lines 0   PASS
GREEN  the live corpus  exit 0 · 34 patterns · 5000 tracked files · 17354 hit lines
       SWEEP CALIBRATE: PASS — known positive 'a2-33' matched 60 time(s)
```

All 34 patterns return a non-zero hit count on the live corpus
[`evidence/red-drive/90-green-per-pattern-counts.txt`] — **no pattern in the set is dead.**

The green hit count (17,354) is **not** comparable with A2-33's 6,334: the corpus has grown, and it
now contains T238's own transcripts, which quote these patterns.

---

## T234's L-1b IS CLOSED, AND ITS CHARACTERISATION WAS WRONG

T234 recorded, `[UNVERIFIED]`:

> A2-33's own transcripts report **81** unique rev-4 lines under `git grep` vs **86** under ugrep.
> **A measured 5-line engine divergence**, committed, unexplained in those files.

**It is not an engine divergence.** rev 4 is recoverable — A2-28 wrote it at `1b6b3cf`, A2-32
replaced it at `cab9e82` — so the exact corpus is available
(`sha256 ce734f9c89e54be5fa3b07d8ddb833df8eaa5f17f8e24ce0ff00564ecf821a92`, 2842 lines). Replaying
all 34 patterns against that blob
[`.softhouse/capture/t238-failopen/transcripts/70-…`, `71-…`]:

| engine | case-insensitive (`-i`, as declared) | case-sensitive |
|---|---|---|
| `git grep -n -I -i -E` | **86** | 64 |
| `git grep -n -I -i -P` | **86** | 64 |
| `/usr/bin/grep -n -i -E` (BSD) | **86** | 64 |
| `perl` PCRE `//i` | **86** | 64 |

**All four engines agree exactly.** The engines never diverged. **86 is the correct count**, and it
is the number A2-33's *ugrep* leg reported. The number that reproduces under **no** engine is
**81** — the `git grep` leg.

So the 81 was measured over a **different corpus**: almost certainly the ADR as it sat in A2-33's
own worktree at the time, rather than the committed rev-4 blob. This **strengthens** A2-33 rather
than weakening it — `MISSES=0` held on both legs, and its ugrep number is the right one.

**Also verified, because it was the obvious candidate cause and it is now excluded:** A2-33's own
audit claim, *"no `\b`, `\d`, `\s` or `\w` in ANY pattern above"*, is **TRUE** — 0 of 34 patterns
use one. The `git grep -E` escape defect (P-53 / P-12) **cannot** explain the difference.

**Scope of this finding (P-66/P-70).** I could not run ugrep: it is **absent from this machine** —
not on `$PATH`, not in `/opt/homebrew`, not in `/usr/local`
[`.softhouse/capture/t238-failopen/transcripts/00-engines.txt`]. I have therefore **corroborated**
that 86 is the right answer under four engines; I have **not verified** the ugrep binary itself.

## WHAT THIS DIRECTORY STILL DOES NOT GUARANTEE

The repaired `sweep.sh` proves it can *reach and search* its corpus. It does **not** re-derive
A2-33's triage, and re-running it now sweeps a **larger and different** repository than A2-33 swept.
Nobody should read a green re-run as a re-confirmation of A2-33's conclusions; read it as evidence
that the instrument is now **checkable**, which is exactly what it was not.
