# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-080001` — **CLOSED CLEAN. ZERO LIVE WORKERS.**

Every worker awaited, every branch merged, every deliverable committed and pushed. `git status --porcelain`
empty. Nothing is running; nothing is half-done.

## Bar on `main` at close — measured, not asserted

```
bash .softhouse/conformance.sh   →  exit 0
  probe line PRESENT (count 1, presence tested BEFORE value)  reading "up"
  46 parity vectors / 7884 cells / 0 FAIL / 0 inadmissible
  LEDGER parity 7 == pinned | oracle-refusal 6 == pinned | money cells 39 == pinned
  ALL 13 wrong ledger implementations DIED through the harness, not by hand
  dead-path frontier 109 == pinned, added=0 | corpus 1281
  P-number citations: VERDICT PASS      ← guard wired THIS fire
```

## What moved, in ledger terms

| | at fire start | at close |
|---|---|---|
| LEDGER parity vectors | 5 | **7** |
| LEDGER oracle-refusal vectors | 5 | **6** |
| LEDGER money cells compared | 29 | **39** |
| wrong ledger implementations, all dying | 11 | **13** |

**The headline: `ledger-wrong-date-rules-always-refusing` is DEAD.** Before T328, the store pinned only the
**refusing** side of both date rules, so **a port that refused every dated entry passed the entire corpus**.
Measured both ways — it passed 5/5 + 5/5 before, and with both vectors withdrawn the hole reproduces.

## Merged this fire — 19 tasks

T306 `3da08fbb` · T272 `16c59715` · T329 `61c0f382` · T277 `e8374743` · T326 `6c3d0787` · T330 `fc104776` ·
T325 `e590b865` · T282 `35a92f30` · T328 `817d2b53` · T322 `f39ed526` · T278 `fa045d8c` · T331 `57521fee` ·
T145 `08be3c56` · T301 `3e024dfa` · T321 `4246ce63` (+ follow-on `a06e48e6`) · T334 `1fdf1c49` ·
T307 `ca745981` · T279 `eac45bdc` · T332 `167b98fc`

## Filed for the next fire

`T330`✓ (done) · **`T332`✓** (done) · **`T333`** wire T145's narrow float-comparison guard — *P-45 for the
third time* · **`T334`✓** (done) · `FU-T279-3` **install the post-checkout hook** — the highest-value open
item, and the only thing that could have closed this fire's 135-second window · `FU-T279-1` T265's review is
not on `main` · `FU-T307-4` A1-01 still unpromotable · `FU-T328-6` nothing grades the refusal precedence
between `:630` and `:636` · `FU-T332-2` a live twin site in `gates-proposed-answers.md`, outside T332's scope
· `FU-T322-1` two `impl.go` prose sites that change pinned transcript output.

## Two driver errors, corrected forward, NOT buried

1. **The P-84 gloss.** The driver wrote *"a failed HARD guard — a money non-negotiable"* into ~14 worker
   prompts and three `tasks.json` descriptions. **P-84 says nothing about money** — it distinguishes a
   HARD-guard refusal from an **oracle outage**, and its recorded instance is an instrument-hygiene guard.
   **T331 refuted it from the definition.** Live prescriptions corrected; merged handoffs left as record.
   See `.softhouse/observations/20260828-driver-gloss-on-P84-drifted.md`.
2. **push-before-spawn.** Batch 1 obeyed it. **Batches 2–5 spawned first and recorded after.** One of five.
   **T279 caught it by disbelieving a brief that asserted compliance.** Nothing broke — *the window is the
   defect, not the consequence*. See
   `.softhouse/observations/20260828-driver-broke-the-push-before-spawn-obligation.md`.

## Pause reason

**None — the fire completed its work and closed.** No `user` gate was crossed; no gate is newly pending.
The oracle was **REACHABLE throughout** and the vector work that only a local fire can do was done.
