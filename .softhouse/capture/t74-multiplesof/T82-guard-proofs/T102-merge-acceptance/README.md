# T102 — the counterproof baseline, proved in BOTH states

The rig's counterproof rows extract "the old code" from a baseline commit. Twice that baseline was a
**computed ref**, and twice it was correct on the branch and wrong on merged main:

| version | baseline expression | on the branch | on merged main |
|---|---|---|---|
| v1 (T82) | `main:` | fork point | **the fix itself** |
| v2 (T98) | `git merge-base main HEAD` | fork point | **the merge commit = the fix itself** |
| v3 (T102) | `cat FORK-POINT-SHA` → `8da4b831b96a146c2b46ad34d85ed098395de160` | fork point | fork point |

v2 is the instructive one: after a merge `HEAD == main`, so the merge base of the two is the merge
commit. The indirection hid the identical defect.

## The four runs in this directory

All four are `bash prove-guards-go-red.sh`, unedited stdout+stderr.

| file | code under test | where it ran | result |
|---|---|---|---|
| `prefix-branch.txt` | v2 (computed) | branch `softhouse/T102-literal-fork-sha` @ `55409cf` | **25 as expected, 0 not** |
| `prefix-merged.txt` | v2 (computed) | throwaway clone, branch merged into its own `main` (`ff73824`) | **18 as expected, 7 not** |
| `postfix-branch.txt` | v3 (literal) | branch, at final HEAD | **25 as expected, 0 not** |
| `postfix-merged.txt` | v3 (literal) | throwaway clone, final branch merged into its own `main` (`a3808f0`, from main `d0ef08d`) | **25 as expected, 0 not** |

Row 2 is the reproduction of the defect and row 4 is the acceptance test. Without row 2 the pair
could not tell a fix from a no-op.

**Rows 3 and 4 are BYTE-IDENTICAL** once the repo root path is normalised
(`diff` exit 0 after a single `s|<root>|ROOT|g` on each). Not merely the same score — the same
transcript, including every extracted sha256 and every guard's stdout. That is the property a
literal pin is supposed to have and the property the computed forms did not have.

## What moved, in one number

The counterproof extracts `run-pass3i.sh` from the baseline. Its sha256:

- pinned / fork point (correct pre-T82 bytes) — `d84ec7bf9888baa1b1fa3f75be679af982ae7435c4aa2e1edbb06f999084e0d3`
- computed on merged main (the FIXED bytes) — `3ca0d3f6380a74d32c8bca000f8587724927b4b55eb0c51b8e64be7cefe2a519`

`3ca0d3f6…` is exactly the sha256 the transcript prints on its first line for the branch's own
*shipping* `run-pass3i.sh`. The counterproof was comparing the fixed code against itself.

The seven rows that flipped in `prefix-merged.txt` are exactly the seven COUNTERPROOF rows —
E-1, E-3, D-1 (×2), D-2 (×3). No GUARD, CONTROL or REGRESSION row moved.

## Reproducing it

The clone is essential and a worktree will not do: `git worktree add --detach <tmp> main` leaves the
ref `main` pointing at the pre-merge commit, so `merge-base main HEAD` still resolves to the fork
point and the defect does **not** appear. The bug needs `main` **itself** to be the merge, which is
what the real merge does and what a clone can reproduce safely.

    git clone --local --no-hardlinks <repo> /tmp/t102-clone
    git -C /tmp/t102-clone merge --no-edit origin/softhouse/T102-literal-fork-sha
    bash /tmp/t102-clone/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh

## The no-fallback behaviour, exercised

`FORK-POINT-SHA` has no computed fallback by design. All four failure modes abort with **exit 2**
before any proof row runs — see `no-fallback.txt`. A silently-wrong baseline prints a GREEN row for
a comparison that never happened, which is worse than no counterproof at all.
