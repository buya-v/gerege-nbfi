# ⚠ `T424-comment-claims.txt` RECORDS A RESULT ITS OWN SHIPPED CODE DOES NOT PRODUCE

**Raised by T440 as `C-T440-1` (MAJOR). Re-verified by the driver at merge, 2026-08-29, by running the
instrument rather than reading either account of it. DO NOT TRUST THE `disagreements=0` LINE.**

| | |
|---|---|
| instrument | `.softhouse/capture/t424/instruments/t424-comment-claims-drive.sh` |
| transcript | `.softhouse/capture/t424/out/T424-comment-claims.txt` |
| transcript records | `T424-COMMENT-CLAIMS-RESULT: disagreements=0` |
| **what the code actually does** | `T424-COMMENT-CLAIMS-RESULT: disagreements=1`, **exit 1** |

Driver's own run, on a detached scratch worktree of `softhouse/T424-t408-conditions` under `/tmp`,
against the committed bytes with nothing modified:

```
ACTUAL EXIT=1
T424-COMMENT-CLAIMS-RESULT: disagreements=1
```

## Why it defeats itself

Line 103 of the instrument is its **no-match control**:

```sh
git grep -q 'zzq-no-such-token-t424' -- .softhouse > /dev/null 2>&1; g_absent=$?
```

The probe token is spelled **in the instrument's own tracked source**. So once the instrument is
committed, `git grep` *finds* it — the control that is supposed to prove "no match returns 1" gets a
match and returns 0, the drive counts a disagreement, and the run exits 1.

**The shipped transcript can therefore only have been taken while the instrument was still untracked.**
That is the whole finding: not that the claim is wrong, but that the record and the code disagree and
the record is the one on `main`.

## What is NOT wrong

The **claim the drive was testing is true**, established independently by T440 with a runtime-assembled
token that is never spelled in tracked bytes: `git grep` returns `1` on no match, `128` on an invalid
pattern, `0` on a match. Nothing downstream of this instrument is in doubt, and **no money figure and no
vector is affected**. T424's substance was re-derived by T440 and none of it was falsified.

## The class

This is `F-T424-N1`'s own defect — *a committed record asserting something the run did not do* — landing
**inside the artefact T424 wrote to hunt that class**. It is the same shape as `T421`↔`T391`, `F-T422-3`,
and `C-T423-1`, all of them this fire. A control whose probe is spelled in tracked bytes is a control
that changes meaning the moment it is committed, and it changes in the fail-**open** direction for
"absent" probes and the fail-**closed** direction here.

**The repair is filed as `T442`.** Do not fix it by respelling the token in pieces to slip past
`git grep` — that hides the control from the census instead of fixing it. Assemble the probe at runtime,
as T440 did.
