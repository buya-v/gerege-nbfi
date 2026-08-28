# T342 — the LOCK's field readers, and the fail-opens in them

Subject: `lock_released_at()`, `lock_started_age()` and `lock_pid_state()` in
`.softhouse/bin/fire-program.sh` — the four signal readers STEP 0's lock decision runs on.

Raised as T280 F-A (one defect). Driven here over the full adversarial shape space: of
**17** bodies the shipped readers got **7** wrong, all in the fail-open direction — plus
**2** in the fail-SHUT direction that no census would have found.

> Both cardinals are DERIVED on every run and are not to be restated (P-80, `patterns.md`):
> `census-lock-readers.zsh` prints one `*** FAIL-OPEN` line per failing row, and
> `positive-control.zsh` prints one `FAIL` line per arm that stopped firing. Count the lines.

## Scripts (`bin/`)

| script | what it does |
|---|---|
| `drive-releasedat-failopen.zsh` | T280's original probe, copied per T114 (never edited in place). Drives the shipped wrapper's `--lock-signals` over the exact bodies T280 used. |
| `fixcheck.zsh` | T280's isolation check of the narrow one-line repair. Copied per T114. |
| `why-brace-class-fails.zsh` | **T342.** Establishes what actually happens to the "obvious" fix (add `{}` to the strip class) — parse vs runtime, and which spellings do work. |
| `census-lock-readers.zsh` | **T342.** The census. Every reader × {key last, value with a comma, key twice, not valid JSON, compact separators}, driven through the shipped file. |
| `positive-control.zsh` | **T342.** The other half: arms 0, 1 and 2 must still FIRE on the inputs they are written for. A reader that always said HELD would pass the census and strand the lock for 24 h. |
| `cost-json-parse.zsh` | **T342.** Costs the alternative in seconds rather than adjectives. |
| `drive-lock-bodies.zsh` | T280's body probe, copied per T114, re-run as a regression check. |

## Outputs (`out/`)

| file | reading |
|---|---|
| `01-BEFORE-releasedat-failopen.txt` | **RED.** Cases 3/4/5: `pid_state=alive_here` and `verdict=FREE-released`. |
| `02-fixcheck.txt` | The narrow fix works in isolation on the one case it addresses. |
| `03-why-brace-class-fails.txt` | The naive `{}` class **parses** (`zsh -n` rc 0) and fails at **runtime** with `bad pattern`. Two other spellings do work. |
| `05-BEFORE-census.txt` | **7 of 17 rows fail open** — 1b, 1e, 1f, 1g, 2c, 4b, 4d. |
| `06-cost-json-parse.txt` | ~104 ms/fork; 0.42 s per fire start. |
| `11-BEFORE-positive-control.txt` | The old readers also had **two fail-SHUT** defects: arm 2 could not fire when `pid` was the last key or the separators were compact. |
| `04-BEFORE-wrapper-vs-skill.txt` | 0 disagreements — **with every one of those fail-opens live in the tree.** See the note below. |
| `07-AFTER-releasedat-failopen.txt` | **GREEN.** Cases 3/4/5 now `HELD-live`. |
| `08-AFTER-census.txt` | 17/17 rows HELD. 0 fail-opens. |
| `09-AFTER-wrapper-vs-skill.txt` | 0 disagreements, 192/192. |
| `10-AFTER-positive-control.txt` | Arms 0/1/2 still fire; the two fail-shut cases are also repaired. |
| `12-AFTER-drive-two-fires.txt` | Every verdict identical to T279's committed output. |
| `13-AFTER-lock-bodies.txt` | Only case B changes (the defect); case D's log line stops carrying a stray `}`. |

## The thing the 192-state driver cannot see, and it is worth writing down

`drive-wrapper-vs-skill.zsh` drives `lock_decide()` — it **supplies** the five signals as
arguments. It never runs a signal READER. So it reported `0 disagreements` both before and
after, and it would have reported `0` on every day the fail-open was live. Its PASS is a
statement about the decision function only, and any future claim that "the lock protocol
is proven over 192 states" must be read with that boundary attached. `census-lock-readers.zsh`
and `positive-control.zsh` exist to cover the half it does not reach; neither is wired into
`.softhouse/conformance.sh` (T323 holds that file), so under P-45 **nobody may cite them as
an enforced control until they are wired.** The wiring lines are in the T342 handoff.
