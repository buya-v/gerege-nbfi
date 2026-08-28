# T368 — independent review of T365. Instruments and transcripts.

**The review is `REVIEW.md`. Verdict: APPROVED.**

Everything here was run on this host (macOS arm64, zsh 5.9), in this worktree, by me. No
transcript of T365's or T361's is accepted as evidence; where I re-ran one of their scripts I
re-ran it, and where I built my own I say so.

## Reproducing

Both vintages of the file under review are extracted from git, never retyped:

```
git show softhouse/T365-t361-conditions:.softhouse/bin/fire-program.sh > /tmp/t365-fire-program.sh
git show main:.softhouse/bin/fire-program.sh                          > /tmp/main-fire.sh
#   after  sha256 06c57d0e192fa1484b9c25ad5ac7995049471a98ddf4425d0d663561b034bf53
#   before sha256 c55a9c8b3a56e894030f4dc68a2bc4c8597d43a0ba18fce048d11c327086e22d
```

T361's corpus, byte-for-byte, and T365's derived variant:

```
git show '380f0d64^2':.softhouse/reviews/t361-review-t353/bin/t361-reader-corpus.zsh
git show softhouse/T365-t361-conditions:.softhouse/capture/t365-t361-conditions/bin/t365-reader-corpus.zsh
```

**Use `zsh`, never `bash`** — `fire-program.sh` is `#!/bin/zsh` and uses zsh glob and subscript
syntax bash cannot parse. Use `bash` for `conformance.sh`, never `sh`.

## `bin/` — my instruments

| file | what it drives |
|---|---|
| `t368-mutate.py` | 11 mutations of the shipped file through the wired self-test. Every mutation is an exact string replacement and reports **VOID** if the anchor is not found exactly once. Contains the decisive `m03` (skew bound → ban) that proves `z07` is a live control, `m06` (century rule) that reproduces T365's FINDING 1, and `m07lo`/`m07hi` that reproduce FINDING 2's sign asymmetry. |
| `t368-control-integrity.py` | `m10` guts all 45 rows — does the wired FATAL control still pass? `m11` forces the reaped-pid acquisition to fail — does `SKIPPED` tell the truth? |
| `t368-c2-refusal.zsh` | condition C2 on both vintages with an unwritable `TMPDIR`. Proves the pre-C2 trap **issues** `rm -rf /` (not merely reaches it) without risk, because BSD `rm` refuses `/` and says so. |
| `t368-live-lock.zsh` | both vintages' extracted readers over the LOCK body that exists right now — does C1 change the live verdict? (No.) |
| `t368-epoch-constants.zsh` | closes T365's UNVERIFIED item (a) by running Go, and derives group H's five constants with `calendar.timegm` rather than with the function under test. |
| `t368-go-zerotime.go.txt` | the Go source that probe compiles. Kept as `.txt` so `go build ./...` over the repo cannot pick it up. |

## `out/` — transcripts

| file | result |
|---|---|
| `01-selftest.txt` | `ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0`, rc 0 |
| `02-mutate.txt` | 11 mutations, `VOID/anchor failures: 0`. **`m03` → `z07` FAIL-SHUT alone.** |
| `03-192driver.txt` | 192 states, **0 disagreements**, `RESULT: PASS` |
| `04-probe.txt` | `--probe` rc 0, wired control logs 45/0/0/0 |
| `05-conformance.txt` | **exit 0**, `parity vectors PASS 46 FAIL 0`, `inadmissible 0`, 13/13 wrong ledgers KILLED |
| `06-knob.txt` | `LOCK_RELEASE_SKEW_SECS` under 7 values incl. an injection attempt — **every bad value fails SHUT and rc 1** |
| `07-corpus-BEFORE-main.txt` | T361's unedited corpus vs `main`: `ROWS=24 FAIL_OPEN=7 FAIL_SHUT=0` |
| `08-corpus-AFTER-t365.txt` | same corpus vs T365: `ROWS=24 FAIL_OPEN=0 FAIL_SHUT=1` (the 1 is `x11`, and it is C1 working) |
| `09-t365corpus-AFTER.txt` | T365's derived corpus vs T365: `ROWS=24 FAIL_OPEN=0 FAIL_SHUT=0`, rc 0 |
| `10-live-lock.txt` | both vintages on the live LOCK: `VERDICT=HELD-live`, **identical** |
| `11-control-integrity.txt` | **`m10`: 45 rows deleted → `ROWS=0`, rc 0.** `m11`: `ROWS=41 … SKIPPED=4` |
| `12-c2-refusal.txt` | T365 → `exit 2` clean; `main` → `scratch=/` and **`rm: "/" may not be removed`** |
| `13-go-and-epoch-constants.txt` | `go1.23.4` → `{"holder":"go-fire","released_at":"0001-01-01T00:00:00Z"}`; group H's five constants derived independently |

## Not run, and said so

An Alpine run of the self-test, to settle whether `/usr/bin/mktemp` exists on busybox. Docker
is available on this host (29.6.2) and the image did not pull inside this review, so **no
off-BSD result is reported here** — the question stays exactly where T365 left it, and it is
latent rather than live because this file has only ever run on the Mac mini.
