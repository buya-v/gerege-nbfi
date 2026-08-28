# Exit attestation — fire `20260828-140005`, chain iteration 3

`bash .softhouse/guards/repo-state-attest.sh fire-compare <before> <after>` → **rc 0**,
**`VERDICT: NO DAMAGE — every delta is inside the declared writ`**.

Snapshots taken with the shipped guard at the fire's start and immediately before exit, so the writ is the
one the guard defines rather than one the driver restated. `git status --porcelain` is also empty — but that
was never sufficient: **T318 drove nine distinct destructive shapes that all leave `git status` CLEAN**
(a committed clobber, a `git stash`, an `--assume-unchanged`, a deleted branch, a commit on the wrong
branch, …), which is exactly why this seven-term attestation exists.

## THE TWO ADVISORIES, ATTRIBUTED — because the guard told me to, and an unattributed advisory is not a pass

The guard raised two `ADVISORY` lines: an invariant artefact changed in `HEAD` that the writ does not name.
Its own text says *"the operation merges other agents' branches and cannot enumerate artefacts in advance.
**Attribute it before trusting it.**"* So:

### `.softhouse/conformance.sh` — four commits, all accounted for
| commit | author task | authorised by |
|---|---|---|
| `a49599da` | `T375` | its exclusive grant — closes T364's two fail-opens |
| `957b8e0b` | `T375` | its grant — the four further fail-opens it found |
| `d175051e` | `T375` | its grant — re-derived P-45 citations that rotted twice inside one task |
| `d8ea93b8` | **the driver** | the pin bump `13 → 14` on the merge result, matched **by name** (P-83, P-86) |

`T375` held this file exclusively for the entire wave. No other worker wrote it — `T360` needed one integer
here and correctly filed `CONFORMANCE-SH-PATCH-REQUEST.md` instead of reaching outside its grant.

### `.softhouse/vectors` — one commit, one file, zero deletions
`71e15a6c` (`T360`) adds `LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json`, **+112 insertions, 1 file
changed, nothing modified and nothing removed**. That is precisely the authorised change: one new vector in
the new divergence class. **No existing vector was touched**, which is the property that matters — a store
whose existing vectors move is a store that can no longer be compared to yesterday's.

## Bar at exit, on `main` @ `2b667af0`
```
EXIT 0 · probe line PRESENT (count 1), reads `up`   ← presence tested BEFORE value, P-84
VERDICT: PASS — 46 parity vectors / 7884 cells
ledger parity 7/0 · oracle-refusal 6/0 · inadmissible 0 · 144 cells, 39 MONEY (money UNMOVED)
LDG-DIV-01 · divergence · PASS · 2 cells, ZERO money cells
all 14 wrong ledger implementations DIED through this harness, not by hand
dead-path frontier GREEN, deadOccurrences 108, frontier 11 == pinned 11
```
