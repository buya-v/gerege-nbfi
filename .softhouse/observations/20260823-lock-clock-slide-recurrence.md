# The fire-id date slide RECURRED — this time inside the LOCK itself

**Filed by the driver, fire `20260823-080004` session 2, 2026-08-23T03:55Z.**
Recorded rather than quietly corrected, because the previous session already filed this same defect
(`.softhouse/observations/20260823-driver-fire-id-and-date-error.md`) and it did not stay fixed.

## What was observed

`.softhouse/LOCK`, read at session start, carried:

```
"started_at": "2026-08-23T00:00:11Z"      <- correct
"heartbeat":  "2026-08-24T00:05:00Z"      <- ONE DAY AHEAD of wall clock
"fire_id":    "20260824-000016"           <- ONE DAY AHEAD
"log":        ".../fire-20260823-080004.log"   <- correct
```

Wall clock at read: `2026-08-23T03:54:44Z` (`date -u`). So two fields were stamped **~20 hours in the
future**, and two adjacent fields in the same file were correct. The log path and `started_at` disagree
with `heartbeat` and `fire_id` **inside a single JSON object**.

## Why this is worse than a cosmetic date bug

`heartbeat` is documented in the lock's own `heartbeat_note` as corroboration for liveness. A heartbeat
stamped in the FUTURE cannot expire. Any check of the form "is the heartbeat older than N hours" answers
**no, forever**, for the next 20 hours — the field fails **OPEN as 'alive'** exactly when it is most
wrong. The skill's STEP 0 already demotes `heartbeat` to corroboration and makes push-recency
authoritative, which is what contained this; but the containment was a design decision taken earlier, not
something this occurrence was caught by.

This is the same shape as P-84 and the T292 root: **one field serving as evidence for a question it can
answer wrongly in the unsafe direction.**

## What the driver did

- Corrected `heartbeat` to the real UTC clock and `fire_id` to `20260823-080004`, the id that matches the
  wrapper's own log path and pid.
- Did **not** treat the future-dated heartbeat as evidence of anything.
- Established liveness by the authoritative signal instead — and, additionally, by `ps` ppid chain:
  `94833 <- 93922`, proving this session is a SECOND `claude` inside the SAME wrapper rather than a second
  holder. That distinction is what kept this from being read as a P-85 double-holder incident.

## The open question this leaves — NOT fixed here

**Where is the slide coming from?** Two candidates, neither verified by this session:

1. `fire-program.sh` composing a date from a UTC clock while labelling it with a local-time convention
   (08:00 Asia/Ulaanbaatar == 00:00Z, so an off-by-one-day is exactly what a mixed-basis format produces).
2. A driver session writing the field by hand from a mis-derived id — which is what the *previous*
   session's observation file records happening.

**[UNVERIFIED]** which of the two produced *this* instance. The correct next step is to read the wrapper's
id-composition site directly. **T301 already owns `fire-program.sh`** (held to batch 2 on a file collision
with T302), so this belongs to T301 or its successor — filed here so it is picked up rather than
rediscovered a third time.

## Why it matters that this is the second occurrence

The first occurrence propagated: it put a wrong id on every dispatch record and commit message written
before the correction, and it PROPAGATED INTO T296's false claim that probe `a1-02` had already armed —
a claim about an **irreversible oracle write**, derived from a wrong date. A date error in this program is
not clerical; it reaches the armed-probe calendar.
