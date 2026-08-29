# The gate graded a REAL `/softhouse-program` driver push, unplanned, 58 seconds after install

Not an arm of any drive. This happened on its own, and it is the only evidence that matters for
the question "is this installed or merely written".

## The timeline, from the reflogs and the ledger

| time (UTC+8) | event | source |
|---|---|---|
| 10:26:2x | `bar-attest.sh main` starts; scratch worktree at `b102875c` | `.git/softhouse-driver-gate/attested-729cd8a0….log` |
| 10:27:54 | attested FULL: tree `729cd8a0…`, exit 0, probe PRESENT ×1 `up`, VERDICT PASS 46/7884 | ledger row 1 |
| **10:29:12** | **`pre-push` installed** into `$(git rev-parse --git-common-dir)/hooks/` | `stat` on the hook |
| 10:29:36 | the driver commits `4e7d678a` — *"softhouse iter5: T350 complete (bar EXIT 0, scope clean); dispatch T449 to review it"*, `.softhouse/tasks.json`, 19 insertions | `git log -1 4e7d678a` |
| **10:30:10** | **the gate runs on the driver's own push and writes `CHEAP ed1b2ee1… 4e7d678a…`** | ledger row 2 |
| 10:30:11 | `origin/main` advances to `4e7d678a` | `git reflog show origin/main` |

One second between the gate's verdict and the ref moving. The driver did not know the gate was
there; nothing in `RESUME.md`, `tasks.json` or the skill mentions it. It ran because it is a
`pre-push` hook in the shared hooks directory and `git push` is the driver's own git command.

## What the gate actually decided, and why that is the right answer

`4e7d678a`'s delta from the attested ancestor `b102875c` is `.softhouse/tasks.json` alone — one
file, `.json`, under `.softhouse/`, MODIFIED. That is inside the STATE set, so the gate ran the
cheap subset on the **pushed tree** `ed1b2ee1…` rather than on the driver's working tree, found
0 fatal citation findings in the directive zone, allowed the push, and recorded a CHEAP row.

Had that commit carried the 2026-08-28 defect — the token `P-100` written into a directive file
naming a rule that did not exist — the same code path would have refused it, which is arm I4 of
`drive-installed.sh`, driven at
`13-I4-RED-bad-citation.txt`: `PNUMBER-CITATIONS: FATAL UNDEFINED .softhouse/RESUME.md:73 P-150`,
`PUSH REFUSED. Nothing was sent.`

## Ledger rows written on this host, verbatim

```
FULL   729cd8a07c986a0ebb3244ee2e6e3f47f8e18cb1  b102875c…  2026-08-29T02:27:54Z  exit0 probe=1xup VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
CHEAP  ed1b2ee107e9d124f8af0a15b0b09e55473757ca  4e7d678a…  2026-08-29T02:30:10Z  delta-from-b102875c…-confined-to-STATE   <-- THE LIVE DRIVER PUSH
CHEAP  ed1b2ee107e9d124f8af0a15b0b09e55473757ca  4e7d678a…  2026-08-29T02:30:24Z  delta-from-b102875c…-confined-to-STATE   <-- arm I3 of drive-installed.sh, 14 s later
CHEAP  0d54d19a9dac257ef7cb551d483e280b7a070d9d  6e137d7e…  2026-08-29T02:31:27Z  delta-from-b102875c…-confined-to-STATE   <-- arm I5, the healthy synthetic control
```

Timestamps in the ledger are UTC; the table above is UTC+8 (`Asia/Ulaanbaatar`), which is why
`02:30:10Z` and `10:30:10` are the same instant.

## The one thing this does NOT prove

It does not prove the gate would have stopped instances 2 or 3 *in the live path*, because
neither has recurred since install. Those are driven synthetically — arms 6, 7 and 12 of
`drive-gate.sh`, and arm I2 of `drive-installed.sh`. A refusal driven on a fixture is weaker
evidence than a refusal observed in the wild, and that difference is stated rather than blurred.
