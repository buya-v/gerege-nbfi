# DO NOT APPLY `FU-T386-7-red-drive-must-report-failure.patch`

**It is superseded.** Apply instead:

```
.softhouse/capture/t424/patches/FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch
```

`git apply --check` clean against `main` at the time of writing; both patches touch the same
file, `.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh`, and **they
conflict** — the amended one replaces the tail guard with a wrapper at the head.

**Why.** T402's guard re-reads `$T381_DRIVE_LOG` **while `tee` is still writing it**, so whether
it sees the last `DID NOT REPRODUCE` line is a property of the `tee` binary, not of the guard.
Measured (`.softhouse/capture/t424/out/T424-buffered-writer-drive.txt`, 8 runs per arm):

| guard | writer | failing arm on screen | guard exit |
|---|---|---|---|
| T402 | host `tee` (BSD) | yes | **1** — correct, 8/8 |
| T402 | 1 MiB stdio-buffered stand-in | yes | **0** — FAIL-OPEN, 8/8 |
| T424 | 1 MiB stdio-buffered stand-in | yes | **1** — correct, 8/8 |
| T424 | host `tee` (BSD) | yes | **1** — correct, 8/8 |
| T424 | either writer, healthy run | no | **0** — not vacuous, 8/8 |
| T424 | either writer, drive dies early | — | **2** — refuses, 8/8 |

This program has already ruled that a host-dependent guard is not a guard. The amendment does not
make the buffer bigger and does not sleep: it makes the script own its transcript and grade it
**after the writer has exited**, which the shell guarantees by waiting for every member of a
pipeline. It also stops prescribing `| tee` to the caller. `[T424, closing F-T408-4]`

**T402's patch is kept, not deleted** — it is the record of the finding it did close (the drive
used to exit 0 whatever its arms said), and the RED arm above is measured against its actual
shipped text, extracted from this very file by content.
