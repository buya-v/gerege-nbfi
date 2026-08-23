# CORRECTION: the driver mislabelled this fire's id, and the error propagated into a worker's finding

Recorded by the driver of the local fire that opened 2026-08-23T00:00:16Z, while that fire was still running.

## What happened

The fire's launch note gave the start time in **UTC** — `2026-08-23T00:00:16Z`. Fire ids in this program are
stamped in **Asia/Ulaanbaatar local time** (`date +%Y%m%d-%H%M%S` in `fire-program.sh`), which at that instant
read **2026-08-23 08:00**. The driver instead built the id from the UTC clock and slid the date forward a day,
labelling the fire **`20260824-000016`**.

Every dispatch record, commit message and manifest line this fire wrote before the correction carries that
wrong id. **The fire is the 2026-08-23 08:00 local fire.**

## Why this is worth a file rather than a quiet fix

**P-85's incident was a fire wearing the wrong identity.** On 2026-08-22 a local fire opened a second session
that reused the same fire id and the same `started_at`, a live holder therefore wore a six-hour-old timestamp,
a cloud fire applied the staleness rule correctly against a false input, and four worker branches died with
its sandbox. The lesson recorded then was about the *freshness signal*; this is the same class of defect one
step earlier — **the id itself**. An id that does not match the wall clock of the host that minted it will
eventually be compared against one that does.

## It was not contained. It propagated into a finding.

`T296` reported that T287's probe `a1-02` *"armed **yesterday** (2026-08-24)"*. That is **false**, and the
driver measured it first-hand rather than reasoning about it:

```
host local                    Sun Aug 23 10:52:40 +08 2026
guard-probe-expiry.sh         business date: 2026-08-23 (DERIVED — enable-business-date='f',
                              m_business_date rows: 0; today in Asia/Ulaanbaatar)
  ok      a1-01  transactionDate 2026-12-31 > business date 2026-08-23 — still refuses
  ok      a1-02  transactionDate 2026-08-24 > business date 2026-08-23 — still refuses
  REFUSE  a2-01  *** NO GLClosure EXISTS at office 1 *** — firing this POSTS 2 JOURNAL ENTRIES
  REFUSE  a2-02  *** NO GLClosure EXISTS at office 1 *** — firing this POSTS 2 JOURNAL ENTRIES
exit 1
```

**`a1-02` arms TOMORROW, not yesterday.** The mislabelled id is the most likely source: the driver's own
prompts and manifest dated this fire 2026-08-24, and a worker reading that would compute exactly the offset
T296 reported. **A driver's clerical error became a worker's factual claim about an armed, irreversible
probe** — which is the reason this is filed rather than silently corrected.

## A second measurement error, the driver's, corrected in the same breath

The driver first read `guard-probe-expiry.sh`'s exit status through a pipe:

```
sh guard-probe-expiry.sh 2>&1 | tail -20 ; echo "GUARD EXIT=$?"      ->  0   ← tail's status, NOT the guard's
sh guard-probe-expiry.sh > /tmp/guard.txt 2>&1 ; echo "EXIT=$?"      ->  1   ← the guard's actual status
```

The guard is **RED, exit 1**, as the record says. But a pipeline's `$?` is the *last* command's, and reading it
as the guard's would have reported a fail-closed guard as passing. This is the same shape as `P-84` — reading a
status that was never the one you meant to read — and the same shape as `T293`'s F2, where `restoredAsFound=1`
was printed by something that had not observed the restoration.

## What the next fire should take from this

1. **Derive the fire id from the host clock, not from a timestamp in a prompt.** The wrapper already does this
   correctly; the driver overrode it by hand.
2. **A date in a worker's finding is an input the driver may have supplied.** When a worker reports a
   calendar-dependent fact, check it against the host and the oracle before merging it into the record.
3. **Never read an exit status through a pipe.** Redirect, then read `$?`.
