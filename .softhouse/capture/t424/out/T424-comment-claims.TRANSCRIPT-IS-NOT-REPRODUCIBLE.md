# ✅ RESOLVED BY T442 — this file's own headline is now HISTORY, not a live warning

**The transcript `T424-comment-claims.txt` beside this file was re-captured by `T442` on
2026-08-29 from committed bytes on a clean detached checkout, and it now reproduces.**
The filename is kept, and only the filename, because `.softhouse/tasks.json` (T442's brief) and
the driver's merge note both point at this path; renaming it would break two live references to
buy a tidier name. **Read the banner, not the filename** — and note that a *name* carrying a
stale claim is the same defect this whole chain is about, which is why it is called out here
rather than left for the next reader to trip over.

| | |
|---|---|
| instrument | `.softhouse/capture/t424/instruments/t424-comment-claims-drive.sh` |
| transcript | `.softhouse/capture/t424/out/T424-comment-claims.txt` — **re-captured** |
| **RED**, the defect on committed bytes | `out/T442-C1-RED.txt` → `disagreements=1`, **exit 1** |
| **GREEN**, after the repair | `out/T424-comment-claims.txt` → `disagreements=0`, **exit 0** |
| **red/green harness**, both arms from committed bytes | `out/T442-C1-REPRODUCTION.txt` → `T442-C1-REPRODUCTION-RESULT: disagreements=0` |
| the class, swept | `out/T442-CLASS-SWEEP.txt`, adjudicated in `out/T442-CLASS-SWEEP-ADJUDICATION.md` |

---

## What was wrong (kept verbatim, because the record of the defect is the point)

**Raised by T440 as `C-T440-1` (MAJOR). Re-verified by the driver at merge, 2026-08-29, by running
the instrument rather than reading either account of it.**

```
transcript that shipped on main : T424-COMMENT-CLAIMS-RESULT: disagreements=0
what the committed code did     : T424-COMMENT-CLAIMS-RESULT: disagreements=1, exit 1
```

Line 103 of the instrument was its **no-match control**:

```sh
git grep -q 'zzq-no-such-token-t424' -- .softhouse > /dev/null 2>&1; g_absent=$?
```

The probe token was spelled **in the instrument's own tracked source**. So once the instrument was
committed, `git grep` *found* it — the control that is supposed to prove "no match returns 1" got
a match and returned 0, the drive counted a disagreement, and the run exited 1. **The shipped
transcript can therefore only have been taken while the instrument was still untracked.** Not that
the claim was wrong: that the record and the code disagreed, and the record was the one on `main`.

## What was never wrong

The **claim the drive was testing is true**, established independently by T440 with a
runtime-assembled token: `git grep` returns `1` on no match, `128` on an invalid pattern, `0` on a
match. **No money figure and no vector was affected.** T424's substance was re-derived by T440 and
none of it was falsified.

## What T442 changed

* CLAIM 3's probe is **assembled at run time** (`zzq-$$-$RANDOM-$(date +%s)-t442-…`), so no byte
  sequence equal to it exists in any tracked file, at any commit. It was **not** respelled in
  pieces to slip past `git grep` — that would hide the control from the census instead of
  repairing it.
* Three arms were added and are graded: the probe must be absent from the **whole repository**,
  not just `.softhouse`; the probe must not be spelled in the instrument's own source (**the
  C-T440-1 regression check** — it is what fires if anyone hard-codes it back); and a literal
  known to be in tracked source is searched and **shown to self-match**, so a reader sees the
  inversion happen instead of taking it on trust.
* The transcript was re-captured **on a clean detached clone**, which is the property that failed.
  It is not byte-reproducible and says so: the probe is a nonce. What reproduces is the verdict,
  and `t442-c1-reproduction-drive.sh` is the machine check for exactly that — ARM A green from
  committed bytes, ARM B red with the defect re-injected and committed.

## The class

`git grep` for a literal probe over a corpus that includes the searcher was swept across all
**1,704** tracked scripts under `.softhouse/`: **4** instruments spell a self-matching probe that
changes what their search reports, **all 4 invert, all 4 fail-CLOSED, 0 fail-OPEN.** One is this
one (repaired); the other three are `t379-anticalibration-drive.sh`, `t367 drive-sweep-failopen.sh`
and `t245-oracle-pin/measure.sh`, each measured, none of them this task's grant, all three filed.
Details and the fail-open hunt's blind spots: `out/T442-CLASS-SWEEP-ADJUDICATION.md`.
