# T362 — independent review of T357

**Verdict and full reasoning: [`T362-VERDICT.md`](T362-VERDICT.md).** Handoff:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T362.md`.

**Headline:** APPROVED. The corpus-isolation proof is CORRECT and I re-derived all three of
its legs without reusing T357's tooling. Two real fail-opens found in T357's own guard layer
(F-1: section 4's adjudicated RC 1 absorbs a mutated captured oracle observation; F-2: the
new corpus guard passes vacuously over an empty vector store), both strictly narrower than
the fail-open the branch removes, both filed as follow-ups rather than blockers.

## Building the target tree these scripts operate on

Nothing in `rig/` hard-codes a checkout path — that is the exact defect T357 repaired in the
five A2-11 scripts, and repeating it in the review of that repair would be indefensible. The
read-only scripts derive the repo root from `$0` / `__file__`; the **mutating** ones take the
target tree as `$1` with **no default**, because a mutation script with a default target is
one typo away from rewriting the live repo.

```sh
TREE=$(mktemp -d -t t362-tree)
git clone --local --shared <repo> "$TREE"
git -C "$TREE" checkout main
git -C "$TREE" merge softhouse/T357-a2-11-section1-red
# run-all.sh section 5 needs this ref to exist LOCALLY (finding F-6);
# a fresh clone only has the remote-tracking copy, and without it section 5
# dies with git exit 128 and run-all.sh exits 1.
git -C "$TREE" branch -f softhouse/A2-7-capture-mandatory-accounts \
      origin/softhouse/A2-7-capture-mandatory-accounts
```

## rig/ — what each script proves

| script | argument | proves |
|---|---|---|
| `t362-token-sweep.sh` | — | 38 T362-constructed tokens (superset of T357's 7) are absent from all 69 vector files and from **three** `conformance.sh` versions (T357's fork-point 4132-line copy, current `main`'s 4441, T358's 4729). Carries a positive control. |
| `t362-structural-vector-scan.py` | — | The same absence **structurally**: walks every vector's JSON tree with `parse_float=Decimal`, separates free-prose fields from graded ones, and shows the only non-prose hits are ledger journal-entry provenance paths. Exits 1 by design (there are non-prose `tierA-a2` hits) — read the listing, not the code. |
| `t362-a2211-root-fact.sh` | — | The root fact: the three key names and the literal `null` occur **0** times in the A2-211 capture A2-7 attributed its fabricated excerpt to. |
| `t362-section-diff.py` | `<committed transcript> <tree>` | Output-neutrality of the five `__file__` reroots, re-derived against the 2026-08-21 committed transcript without T357's `diff-sections.py`. Sections 1, 2, 3, 6, 7 byte-identical. |
| `t362-fresh-vs-obs-shas.sh` | `<tree>` | T357's fresh live re-observation is byte-identical to the committed `obs/` on 4 of 4 reads, and the tenant has drifted 27 → 33 products. |
| `t362-float-and-stack-scan.sh` | `<tree>` | P-25 float audit (AST) of every file T357 adds or edits, plus the prohibited-stack scan. |
| `t362-drive-red-both-directions.sh` | `<tree>` | **MUTATES and reverts.** Drives `adjudicate-section1.py` RED end-to-end in both directions on real `obs/` bytes — D1 a *vanished* failure (the dangerous one), D2 a *fourth* failure — and D3, T362's own probe, exposes the vacuity gap F-2. Exits non-zero if D1 or D2 fails to trip. |
| `t362-section4-absorption-probe.sh` | `<tree>` | **MUTATES and reverts.** P1 independently recomputes `out/` + `req/` byte-identity against the fork sha. P2 proves finding **F-1**: a mutated captured oracle observation leaves `run-all.sh` at exit 0 printing `PASS`. |

## evidence/ — raw output, all regenerated from the rig above

| file | what it shows |
|---|---|
| `10-token-sweep-38-tokens.txt` | the 38-token table across vectors and three `conformance.sh` versions |
| `11-structural-vector-scan.txt` | 6 prose hits, 12 non-prose hits, all ledger provenance; positive control 104 |
| `20-…-BEFORE-on-current-main-exit0.txt`, `21-…-transcript-…` | **the fail-open**: `run-all.sh` exits **0** on current `main` with 6 `exit=1` lines and 5 tracebacks in its own transcript |
| `22-…-AFTER-on-merge-result-exit0.txt` | the repaired runner on `main + T357`: exit 0, 9/9 as adjudicated, 0 deviations |
| `23-adjudicator-on-merge-result.txt` | `adjudicate-section1.py` exit 0, 7/7 controls, corpus table all zero over 69 files |
| `30-drive-red-both-directions.txt` | D1 adj rc 1 / run-all rc 2, D2 adj rc 1 / run-all rc 1, D3 rc 0 (the gap) |
| `31-section4-absorption-probe.txt` | 431 fork-sha files (327 `out/`, 76 `req/`), 0 differing under `out/`+`req/`; and **F-1 confirmed** |
| `40-section-diff-t362-independent.txt` | sections 1,2,3,6,7 IDENTICAL — matches T357's claim |
| `50-fresh-vs-obs-byte-identity.txt` | 4/4 sha256 identical; 27 → 33 products; ids 54,55,56,57,58,60 appeared |
| `51-a2211-root-fact.txt` | 0/0/0 occurrences; no `None`-valued key |
| `60-float-and-prohibited-stack-scan.txt` | 0 float literals / 0 `float()` calls in the new code; prohibited stack clean |
| `70-conformance-main-plus-T357.txt` | `bash .softhouse/conformance.sh` → exit 0, probe present + `up`, `VERDICT: PASS — 46 parity vectors, 7884 cells` |
| `71-conformance-…-plus-T358.txt` | the same on `main + T357 + T358`: exit 0, PASS, dead-path frontier GREEN, `deadOccurrences=109` unchanged |

No probe was fired against the shared reference oracle by this review. Every oracle-facing
fact here is re-derived from committed bytes or from T357's own read-only capture.
