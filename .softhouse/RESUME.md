# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260829-080002` ITERATION 5 — **CLOSED CLEAN. ZERO LIVE WORKERS.**

Oracle **REACHABLE** throughout (one transient container restart, observed by `T446`, recovered).
PostgreSQL `localhost:5432`, pinned Fineract `/Users/buv/fineract @ 426a23544`.

## BAR ON `main` AT FIRE END — GREEN AND ATTESTED

```
bash .softhouse/conformance.sh   →  EXIT 0
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value
VERDICT: PASS — 46 parity vectors match the pinned reference oracle, 7884 cells compared
frontier 11 == 11 · deadOccurrences 108 · 16 guards timed, 0 breaches · 16 wrong impls dead
```

**Every one of the ten merges was graded ON THE MERGE RESULT** in a scratch worktree outside the repo,
its tree identity verified against the graded tree, and **ATTESTED BY TREE SHA** before `main` was
touched. No tree reached `main` this fire that a bar had not seen.

## MERGED — TWENTY BRANCHES IN TEN REVIEWED PAIRS

| Wave 1 | Wave 2 |
|---|---|
| `T350`+`T449` → `T451` | `T451`+`T456` → `T462` |
| `T442`+`T447` → `T452` | `T452`+`T457` → `T463` |
| `T412`+`T450` → `T453` | `T453`+`T461` → `T465` |
| `T445`+`T446` → `T454` | `T454`+`T459` → `T466` |
| `T433`+`T448` → `T455` | `T455`+`T464` → `T467` |

Every verdict was **APPROVED WITH CONDITIONS**. All conditions are filed; none was waved through.

## ⚠ WHAT THE NEXT FIRE MOST NEEDS TO KNOW

**1. THE DRIVER PUSH GATE IS LIVE, INSTALLED, AND IT REFUSES THE DRIVER.** At the `T350`+`T449` merge
the driver had graded the merge result **and** verified tree identity by hand — and was still refused,
because a transcript is bytes and nothing binds it to the tree it claims to have graded. **The remedy is
`bash .softhouse/hooks/bar-attest.sh HEAD`, which checks the tree out itself. Never bypass; attest.**
`bypass.log` does not exist and should stay that way. The installer was re-run at merge: gate bytes
`running == HEAD blob == 9360bd74a771c455`, `--status` exit 0.

**2. `T465` IS ABOUT YOUR OWN EXIT, AND THE DRIVER REPRODUCED IT FIRST-HAND.**
```
lock present (tracked)    GREEN    rows=108 pinned=108 added=0
lock deleted (fire exit)  REFUSED  rows=125 pinned=108 added=17
```
`D .softhouse/LOCK` leaves the STATE set, so the release push takes the **full-bar** path, and the full
bar on a lock-released tree is `EXIT 2` with **no probe line**. The wrapper writes no `released_at` key,
so its release is a genuine deletion. **Push everything BEFORE the lock release; nothing should depend on
the exit push landing.** If it is refused, the lock persists and the next fire's dead-holder arm (arm 2)
handles it correctly.

**3. THE WITNESS-FORGERY CHAIN IS AT EIGHT LINKS AND STILL OPEN.** `T404→T407→T431→T444→T445→T446→T454
→T459`. Open and driven: **`LONGSTRIP`**, **`LONGNOP`** (one inserted line, not the two deletions the
file claims), **`SKIPWT`** and **`SMUDGE`** — the last two reach `PASS` with the guard fully intact **and
`git status --porcelain` EMPTY**, so the one out-of-band step is blind to them. `T454` broke the streak by
**declaring** its open route instead of arguing it shut; keep that habit.

**4. `T460` IS AMENDED — READ IT BEFORE STARTING IT.** As originally filed it specified bare
`git hash-object`, which `SMUDGE` defeats: a `filter=` attribute in `.git/info/attributes` (never
committed) makes `git hash-object` **apply the filter**, so the ids print equal over forged bytes. Use
`--no-filters`. And note the verifier's proposed host is itself a target — `fire-program.sh` carries `fi`,
so `U+FB01` collides and wins, and that file is a **declared witness**.

**5. RUN THE BAR ON YOUR OWN INSTRUMENTS BEFORE YOU COMMIT.** Seven workers this fire had a first bar
refused, six for the same reflex: **spelling a real `.softhouse/...` path as a literal in a fixture**.
Assemble paths from a variable (`S='.softhouse'`) or at run time; adopt `T238`'s `sweeplib.sh` shape.
**All seven repaired at the instrument; none grew a pin.** `T458` is filed to write this into `patterns.md`
and make the refusal teach the fix.

## QUEUE FOR THE NEXT FIRE
`T465` (the lock/frontier coupling — affects every fire exit) → `T466` (SKIPWT/SMUDGE; the guard already
computes both ids and never compares them) → `T462` (the wall-clock safety refusal) → `T458` (the pattern)
→ `T467`, `T463` → `T460` (external verifier, **after** reading the amendment) → `T403` → `T443`, `T441` →
`T419` → `T437` → `T434`/`T435`/`T436` → `T399`, `T425`, `T394`, `T395`.

## OPEN GATES — none blocks anything, no CONTRACT gate open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`, `G-22`.

**NEW, for Buyan:** server-side prevention of `--no-verify` is **partly a `user` item**. Design and a drive
against a throwaway bare remote are ENGINEERING and need no gate; applying it to live `origin` needs
repo-admin rights the agent does not hold and could lock Buyan out of his own `main`. Note `pre-receive` is
**not available on github.com** (Enterprise Server only), so the realistic instrument is a **branch ruleset**.

## NEEDS A HUMAN EVENTUALLY (not gates, but no agent should guess)
- **`T286` is partially landed**: 27 files on `main`, branch 2 commits ahead, **not** an ancestor. Found by
  `T350`, confirmed by `T449`.
- **Six branches from earlier fires carry unmerged commits**: `T4-dec1-retry-rescued` (1),
  `T40-charges-capture` (10), `T405-review-t397` (3), `T408-review-t402` (2), `T410-review-t400` (2),
  `T42-mathcontext-inforce` (7). Not this fire's work; nobody has adjudicated whether their content landed
  by another route.

## EXIT-PROTOCOL ATTESTATION — run, not assumed

`repo-state-attest.sh fire-compare <before> <after>` → **`VERDICT: NO DAMAGE — every delta is inside the
declared writ`**, exit 0. `git status --porcelain` empty (necessary, never sufficient — T318 drove nine
shapes that leave it clean while destroying work).

One **ADVISORY** was raised and **attributed rather than accepted**: `.softhouse/conformance.sh` changed
(`e25f0f88 → 7c543532`) without the writ naming it, because a merge cannot enumerate other agents'
artefacts in advance. Attributed to six commits, all from `T445` and `T454` — the only two branches this
fire that held `.softhouse/conformance.sh` in `files_hint`, and each the sole writer in its wave. No
unattributed change reached `main`.

## Pause reason
**None — the fire closed clean.** Zero live workers, zero tasks left `in_progress`, working tree clean,
everything pushed. `ready-tasks.py`: **52 READY, 0 IN PROGRESS, 8 BLOCKED**, no open CONTRACT gate.
