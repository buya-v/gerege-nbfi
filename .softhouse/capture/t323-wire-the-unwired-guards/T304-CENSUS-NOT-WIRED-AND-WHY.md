# T323 — why T304's evidence census is NOT wired, measured rather than argued

**Verdict: the first three guards are wired; T304's census is not.** The brief authorised this
outcome in advance — *"If you cannot solve the baseline pinning cleanly, WIRE THE FIRST THREE
AND SAY SO — a partial wiring that lands beats a complete one that does not."* This file is the
"say so", and it carries the measurement that makes the refusal a finding rather than a shrug.

## The brief's own worry, restated

> T304's guard protects **nine named files** and nothing stops a tenth being written; the
> **census** is the detector that scales. The baseline problem is real: T304 classified **223
> destructive sites** into defect / correct-by-design / correct-but-undeclared, so a census
> guard that fails on any hit re-reports the legitimate ones forever and **gets switched off
> within two fires**.

The obvious answer is the one this file already uses three times — `FAILOPEN_PIN_FILE_LIST`,
`HOSTSTATE_PIN_TEMP_ASSIGN_LIST`, and now T316's `dead-path-frontier.pin`: don't fail on the
population, **pin it and fail on GROWTH**. T323 tested whether that works here. It does not, and
the reason is structural rather than a matter of effort.

## Measurement 1 — the census has already moved, hard, in days

T304's pipeline re-run by T323 on this branch, unmodified, same three instruments in the same
order [VERIFIED: T323 ran them; buckets in `evidence/31-t304-resolver-buckets-today.txt`,
rows in `evidence/30-t304-census-rerun-today.tsv`]:

| stage | T304, committed 2026-08-27 | T323, this branch | delta |
|---|---|---|---|
| `10-population-census.py` raw destructive sites | 4,901 | **5,409** | +508 (+10.4%) |
| `20-resolve-targets.py` resolved sites | 1,574 | **1,798** | +224 (+14.2%) |
| `30-count-tracked-under-target.py` HARD sites | **223** | **307** | +84 (+37.7%) |
| distinct instruments contributing a hard site | 106 | **171** | +65 |

A guard pinned at T304's 223 would be **red by 84 rows on its first graded run**, one day after
the census was committed. Re-pinning 84 unreviewed rows per fire is not a frontier; it is an
amnesty machine, and it would launder a real defect through the noise. That is precisely the
"switched off within two fires" outcome the brief predicts.

## Measurement 2 — and this is the load-bearing one — the census is not a function of the instruments

The growth above could be innocent: new tasks write new scripts, new scripts do destructive
things. If that were all, a frontier pin would still work, because each new row would be
attributable to the commit that added it.

**It is not all.** T323 checked whether the newly-contributing instruments are new files:

| instrument newly contributing a HARD site | last touched | T304's census |
|---|---|---|
| `.softhouse/capture/charges/bin/t51-capture.sh` | **2026-08-19** | absent |
| `.softhouse/capture/t91/prove-guards.sh` | **2026-08-21** | absent |
| `.softhouse/capture/tierA-a2/cap.sh` | **2026-08-22** | absent |

[VERIFIED: `git log -1 --format=… -- <path>` for each; T304's `30-hard-sites.tsv` landed
`50d43b56`, **2026-08-27**.]

`t51-capture.sh` was last modified **eight days before** T304 took its census. Its bytes have not
changed. It did not produce a hard site then; it produces one now.

The mechanism is in T304's own resolver, and T304 documented it honestly at
`instruments/20-resolve-targets.py:13` — *"A resolved operand is TRACKED if it is in `git
ls-files`, **or is a directory prefix of at least one tracked path**."* So a site's
classification depends on **the entire tracked corpus**, not on the instrument holding it.
Committing an unrelated file anywhere under a path an old script happens to name flips that
script from "scratch" to "destroys committed evidence" — with no commit touching it.

**That is what makes this unpinnable.** A frontier pin is only reviewable when a moved row is
attributable to the diff that moved it. Here rows move for reasons no diff contains, so every
fire would present a delta nobody can attribute, and the only available response is to
regenerate the pin. A pin that is regenerated rather than reviewed is `P-22` — *"a guard, a
canary, or a control that cannot fail is worse than none, because it is believed"* — with a
maintenance cost attached.

## What this says about T304's classification, which matters more than the wiring

T304's 223 sites were sorted into **defect / correct-by-design / correct-but-undeclared**. That
classification was correct when taken and **it is already stale**, by 84 rows, for a reason that
has nothing to do with anyone's code being wrong. Any future task that cites "T304 classified
223 sites" as a standing fact is citing a number that moves on its own.

This is `P-95`'s shape one level out — *"a fallback and a fail-open are indistinguishable by
reading, and they have opposite severities … it can never be classified by reading — only by
removing every candidate and observing the exit"* [VERIFIED: `.softhouse/patterns.md:3084`].
T304 classified by resolving. The resolution is corpus-dependent, so the classification inherits
the corpus's churn. **The removal experiment P-95 prescribes is per-site and cannot be
amortised across 307 of them.**

## What T323 recommends instead, for whoever files the follow-up

Not a census-with-a-pin. The scaling detector wants a predicate that is **local to the
instrument**, so a row moves only when that instrument's diff moves it. Two candidates, neither
of which T323 built or drove — stated as directions, not as findings:

1. **Declaration-at-the-site.** T304's `refuse-if-tracked.sh` already refuses when a target
   resolves tracked. Make that the *contract* rather than a nine-file allowlist: an instrument
   performing a hard-destructive operation on a path it did not create must carry an explicit
   in-file declaration, and the guard greps for the declaration in the instrument — a property
   of one file, so its diff explains its own row. This is T299's namespace design applied to
   destruction: *say who owns it* becomes *say what you are destroying*.
2. **Pin the CORPUS-INDEPENDENT half only.** Sites whose target resolves to a tracked path
   **literally** (`TRACKED-FILE`, 379 today) do not flip under corpus growth the way the
   directory-prefix half (`TRACKED-DIR`, 1,368) does. Whether the file half is actually stable
   is **[UNVERIFIED]** — T323 did not measure it across two commits, and it must be measured
   before it is believed, not assumed from the argument above.

## Honest limits of this document

- T323 re-ran T304's three instruments **unmodified** and read their own printed selectors. It
  did **not** audit whether those selectors are correct; the deltas above are statements about
  T304's predicate, not about the world (`P-70`).
- Some of today's +508 raw sites are **T323's own** — `drive-red-t323.sh` performs `rm`,
  `git reset --hard` and `sed -i`. That inflates the raw and resolved figures. It does **not**
  affect Measurement 2, which rests on three files T323 never touched, and the three
  last-touched dates above are the check on that.
- `[UNVERIFIED]` whether a per-instrument declaration guard would itself stay green on today's
  tree. It would need its own red drive and its own baseline, which is the next task's work.

---

# ITERATION 3 — A THIRD DATAPOINT, AND A SECOND, INDEPENDENT REASON TO REFUSE

Iteration 3 re-ran `10-population-census.py` unmodified on the delivered tree, as its own check
rather than accepting the two measurements above (**P-22** — *"a guard, a canary, or a control
that cannot fail is worse than none, because it is believed"*; the same disbelief is owed to a
predecessor's cardinals). Raw rows are in `evidence/70-t304-census-rerun-iter3.tsv`, the
per-operation breakdown in `evidence/71-t304-ops-iter3.txt`.

## The drift is not slowing — it is accelerating

| measured by | date | raw destructive sites |
|---|---|---|
| T304 | 2026-08-27 | 4,901 |
| T323 iteration 2 | 2026-08-28 | 5,409 |
| **T323 iteration 3** | **2026-08-28, same day, later** | **6,291** |

**+882 rows inside a single day**, on top of iteration 2's +508. A pin regenerated at the start
of a fire is stale by the end of the same fire. That is the "pin it and fail on GROWTH" answer
dying on contact for the second time, and the second measurement is the one that makes it a
property rather than an anecdote.

## THE SECOND REASON, WHICH IS WORSE, AND WHICH THE FIRST TWO MEASUREMENTS DID NOT NAME

The refusal above rests on *instability*. Iteration 3 also looked at **what the rows actually
are**, and the population is not merely unstable — it is overwhelmingly **not destructive sites
at all**.

Of the 6,291 rows, **4,971 (79.0%) are the `redirect` class**, and `redirect` is matching the
two-character sequence `->` in ordinary program output. Verbatim rows, unedited:

```
.softhouse/capture/charges/bin/t46-defvsreq.py   98  redirect  print(f"   if DEFINITION governs -> {pred_def}")
.softhouse/capture/charges/bin/t46-defvsreq.py  125  redirect  f"| HALF_UP -> {hu} | HALF_EVEN -> {he} | OBSERVED {observed} "
.softhouse/reviews/t49-probe/citecheck.py        28  redirect  if a<1 or b>n or a>b:
.softhouse/reviews/t47-probe/t47_monthend.py     75  redirect  return k - (1 if a.day > b.day else 0)
```

An ASCII arrow inside a `print`, and a **numeric comparison operator**, are being counted as
sites that destroy evidence. Note the third and fourth rows especially: `b>n` and `a.day > b.day`
are arithmetic, and one of them is in a **money-adjacent** month-difference probe — so a census
guard failing on any hit would be reporting *the loan schedule's date arithmetic* as an evidence
destruction risk. Nothing would discredit the guard faster with the next reader.

**Consequence for the baseline question the brief posed.** The brief's worry was that a census
guard "re-reports the legitimate ones forever and gets switched off within two fires". The
measurement says the situation is a full order of magnitude worse than that framing: it is not
223 legitimate-but-flagged sites, it is **~5,000 rows that are not destructive operations in any
sense**, growing by hundreds a day. Pinning that is pinning noise, and a pin over noise is an
amnesty with a checksum — it would go red on the next fire for reasons no reviewer could
adjudicate, and it would be switched off. Refusing to wire it is the outcome that preserves the
detector for whoever fixes the selector.

**WHAT WOULD MAKE IT WIREABLE, stated so the refusal is actionable and not a dead end.** The
defect is in `10-population-census.py`'s lexical matcher, not in the wiring and not in T304's
classification work, which remains sound for the sites it actually adjudicated. The `redirect`
class needs to distinguish a shell redirection from `->` and from `>` as a comparison — at
minimum by not applying shell-redirection lexis to `.py` files, which is where essentially all
of the noise lives. That is one task against `10-population-census.py`, after which the
population drops by roughly four fifths and the stability question can be asked again honestly.
**It is not this task**: T323's edit set is `conformance.sh` and its own capture directory, and
rewriting another task's instrument to make it gradeable would be exactly the scope-wandering
the program treats as a rejection.

**FAIL DIRECTION, HAD IT BEEN WIRED — recorded because the brief asked for one per guard.** It
would have failed closed towards "a tracked file gained a destructive operation against evidence
that nobody declared". It is **not wired**, so it has no direction today, and this file is the
statement of that rather than a silence a later reader could mistake for an oversight.
