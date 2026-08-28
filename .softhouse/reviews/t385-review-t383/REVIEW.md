# T385 — independent review of T383 (`softhouse/T383-t380-conditions` @ `151ef180`)

Subject: `.softhouse/bin/fire-program.sh`, **the wrapper that launches every fire, including the
one this review ran inside.** Reviewer grant: `.softhouse/reviews/t385-review-t383/` only.
Nothing outside it was written. `fire-program.sh` was **read and copied, never written.**

| | sha256(`.softhouse/bin/fire-program.sh`) | measured by T385 |
|---|---|---|
| `main` @ `f3bf5563` (still, after main advanced) | `dbb18b7b80033384455a9c93086d681ecdf453558bedd049141bc1a542123d89` | ✔ matches T383's "before" |
| `softhouse/T383-t380-conditions` @ `151ef180` | `5c4f0244c8b54dc6a6493e7371b89864fc90f5c00e4bcb06767d3ef371a60ae1` | ✔ matches T383's "after" |

`git diff --numstat main...T383 -- fire-program.sh` = **`144 / 6`**, as claimed. Row census
`^\s*_(row|arow)\s` = **45 on both sides** — no invocation added, removed or moved.
`main` advanced during this review (`d1a6b7e6 → f3bf5563`) but **T383 is still not merged**, the
merge-base `05ce01de` is unchanged, and the three-dot diff is still the same 18 files.

---

## VERDICT: **APPROVED WITH CONDITIONS**

The three fixes are real, they are in the direction claimed, and every claim in §1–§5 of T383's
handoff that this review re-drove came back true. **A healthy fire still starts** — answered first
and separately below. The conditions are all **prose in a live control file that says something
measurably untrue about the code beside it**, and one of them (F-T385-2) says the code is protected
against a drift it is not protected against; I drove that drift and it lands as a lock-reader
misattribution, which is precisely the fault class F-T380-2 was opened to close.

| id | severity | what | condition |
|---|---|---|---|
| **F-T385-1** | MINOR (prose) | The stated *reason* the anchored selector keeps substring containment green is **false**. Measured: the naive unanchored count **starts** the healthy fire. | correct `fire-program.sh:1437-1439` and handoff §1 |
| **F-T385-2** | **MODERATE** (false safety claim, driven) | `fire-program.sh:748-749` says the z06/z07 offsets "cannot drift apart" from the rows. **They are re-spelled at `:883-884`** and I drove the drift: the gate does not see it and the wiring blames "the READERS". | make z06/z07 consume `_SKEW_FAR`/`_SKEW_NEAR`, **or** delete the claim |
| **F-T385-3** | MINOR (restated cardinal, P-80) | `fire-program.sh:724` — "the four tests below ARE the four fixture expressions" — the code has **six** (`:756-761`); the handoff says six. | say six, or list six bullets |
| **F-T385-4** | BACKLOG, **not T383's** | the fail-open / dead-path census corpus is tracked `.sh`/`.py`; **110 tracked `.zsh`** files (98 under `capture/`+`reviews/`) are invisible to it. T383's selector reasoning is **correct**; the gap is real. | file it (own grant) |

None of the conditions is a fail-open in the shipped behaviour. All three are one-line-to-one-block
comment edits inside T383's own grant.

---

## 0. ANSWERED FIRST: **DOES THE FIX REFUSE A HEALTHY FIRE? — NO. A HEALTHY FIRE STILL STARTS.**

T383's fix briefly became a control that refuses every fire (`${#${(f)…}}` read the **41-character
length** of the summary), and T383 caught it with its own `m00`. Because *"a control that refuses
everything and a control that cannot fail are the same defect wearing opposite signs"*, this was
checked before anything else, three independent ways, none of them reusing T383's driver.

**(a) The file as shipped on the branch, driven at `--probe` against a throwaway repo**
[`out/01-healthy-control-fixed.txt`]:

```
[20:24:40] lockselftest| ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0
[20:24:40] lockselftest: tally VERIFIED by the wiring — 45 executed + 0 skipped = 45 declared …
[20:24:40] probe only — exiting without taking the lock or invoking the driver
rc 0
```

**(b) Twelve independent healthy-start cases in my own drivers, all `rc 0` against the fixed file:**
`d00` (one well-formed summary), `d10` (summary split across a WRITE boundary — the case a careless
multiplicity fix refuses), `d12` (three lines, two of which merely CONTAIN the token — the case a
naive count refuses) [`out/02-green-fixed.txt`], and `t00`/`t03`/`t04`/`t07`/`t09`/`t10` — the
**defaults the launchd plist actually runs** plus five legitimate non-default thresholds
[`out/07-green-thresholds-fixed.txt`], plus `s00` [`out/11-skew-drift.txt`].

**(c) The zsh idiom re-derived from first principles in a scratch script** under the shell that runs
the wrapper [`out/04-zsh-idiom.txt`, `bin/t385-zsh-idiom.zsh`]:

```
one summary line is 41 characters long
A. BUGGY  _NSUM=${#${(f)v}}       lines=0 -> 0    lines=1 -> 41   lines=2 -> 2    lines=3 -> 3
B. SHIPPED arr=( ${(f)v} ); ${#arr} lines=0 -> 0  lines=1 -> 1    lines=2 -> 2    lines=3 -> 3   ALL CORRECT
```

This is **worse than T383 described and confirms its account exactly**: the buggy nested form is
right for 0, 2 and 3 lines and wrong **only for one** — i.e. wrong on precisely the healthy case and
correct on every multiplicity case. It would have passed every "does it refuse?" test and refused
every real fire. The shipped array form is correct at 0, 1, 2 and 3.

I also checked the two zsh hazards around that idiom (`out/04`, sections C and D): a *quoted*
`( "${(@f)EMPTY}" )` split yields **one empty element** — a phantom tally line — and the shipped
code's `[[ -n "$_ST_SUMS" ]]` guard is what stops it; and the unquoted assignment is not subject to
filename generation here (`GLOB_SUBST` off), so a glob metachar cannot inflate the count. Neither is
reachable anyway, because the anchored grep admits only `[0-9]+` fields.

**If you read nothing else: the wrapper starts a fire normally. This is not a REJECT on that axis.**

---

## 1. THE MULTIPLICITY REFUSAL — RE-DRIVEN, ALL THREE DIRECTIONS, WITH SEVEN NEW ATTACKS

`bin/t385-multiplicity-drive.zsh` — **written from scratch, 20 cases, does not reuse
`t383-red-drive.zsh`.** Expectations are POST-FIX, so the same driver is RED against `main` and
GREEN against T383's file; every mutation must replace an anchor occurring **exactly once** or the
case scores VOID and can never pass.

* **GREEN, T383's file (`5c4f0244…`): `CHECKS=20 WRONG=0 VOID=0` — `RESULT: PASS`**
  [`out/02-green-fixed.txt`]
* **RED, `main` (`dbb18b7b…`): `CHECKS=20 WRONG=8 VOID=0` — `RESULT: FAIL`**
  [`out/03-red-shipped.txt`]

### The three directions hold

| direction | case | fixed |
|---|---|---|
| **ZERO** → refuse | `d01` printer removed; `d07` only summary has trailing whitespace; `d11` line-boundary split; `n03` CRLF-only summary | all `rc 2`, `printed NO TALLY LINE`, P-84 cited at `patterns.md:2813` |
| **ONE** → unchanged | `d00`, `d10`, `d12` clean → `rc 0` fire starts; `d02` one FAILING summary → `rc 2` **`FAILED (rc=0, FAIL_OPEN=1`**, and it must **not** say "TALLY LINES" — graded, forbidden, absent |
| **TWO+** → refuse | `d03`, `d04`, `d05`, `d08`, `d09`, `n01`, `n06` → `rc 2`, `printed 2 TALLY LINES`, both offending lines echoed |

**P-84 vs P-83 confirmed by reading the file**: `patterns.md:2806` is P-83 (reconcile by running),
`:2813` is P-84 (read the absence), `:2822` is P-85. T383's citations are right in both the source
comment and the handoff; the earlier off-by-one is gone.

### The five defeats T383 listed — none succeeds against T383's file

| # | defeat | vs `main` (T385-measured) | vs T383's file |
|---|---|---|---|
| 1 | **data inside a string** (`d08`) | `rc 2` **but for the wrong reason** — see below | `rc 2` multiplicity |
| 2 | **summary on STDERR** (`d09`) | **`rc 0`, FIRE STARTS** | `rc 2` multiplicity |
| 3 | **trailing whitespace**, both roles (`d06`/`d07`) | `rc 2` | `rc 2`, and `d06` still blames the READERS, not multiplicity — correct |
| 4 | **write-boundary split** (`d10`) | `rc 0` | **`rc 0` — no false refusal** |
| 5 | **line-boundary split** (`d11`) | `rc 2` | `rc 2` zero-arm |

Plus the two T380 orderings: `d03` (failing THEN clean — T380's exact input) and `d05` (two
identical clean lines) are **`rc 0`, FIRE STARTS on `main`** and `rc 2` on T383's file. `d04` (the
`head -1` mirror) refuses on both, but on `main` it refuses while **blaming the READERS**; on
T383's file the readers are unblamed. Graded as a forbidden string, so this is measured, not read.

**One correction to T383's table.** T383 records `m07` (data inside a string) as `rc 0, FIRE STARTS`
on the shipped file. My `d08` injects `ROWS=99 …`, and on `main` it lands `rc 2` — but on the
**reconcile** check, not the multiplicity check:

```
FATAL: … does not reconcile — ROWS=99 + SKIPPED=0 = 99, but 45 rows are DECLARED …
       Rows exist that neither ran nor announced themselves skipped, so the tally understates …
```

So the data-string defeat only reaches `rc 0` on `main` when the injected `ROWS` **equals the
census** (T383 evidently used `ROWS=45`; I used 99). This does not weaken T383's finding — it
narrows it, and the same transcript is a live sighting of the F-T380-3 prose defect in the wild:
99 > 45 is an **over**count and `main` calls it "understates".

**Four rc-0 fail-opens measured on `main` by this review**: `d03`, `d05`, `d09`, **`n01`**.

### Seven attacks T383 did **not** list. **A sixth defeat exists — against `main`, not against the fix.**

| case | attack | vs `main` | vs T383's file |
|---|---|---|---|
| **`n01`** | a summary line emitted as a **FILENAME** the self-test echoes (`mktemp -d`, `: > "$d/ROWS=45 …"`, `for f in $d/*(N)`) | **`rc 0`, FIRE STARTS** — a **sixth** fail-open on `main`, not in T380's or T383's lists | **`rc 2` multiplicity** |
| `n02` | **CRLF** impostor beside a real failing line | `rc 2` | `rc 2`, still `FAIL_OPEN=1` — CR keeps it out of the population, so it cannot silence the real line |
| `n03` | the **only** summary has a CRLF ending | `rc 2` | `rc 2` zero-arm — unrecognisable == absent, SHUT |
| `n04` | **UTF-8 fullwidth digit** (`SKIPPED=０`) impostor | `rc 2` | `rc 2`, real failing line survives |
| `n05` | **UTF-8 NBSP** as the field separator in an impostor | `rc 2` | `rc 2`, real failing line survives |
| `n06` | a **NESTED REAL invocation** of the self-test emitting a second genuine summary | `rc 2` (both lines happen to be `FAIL_OPEN=1`, so `tail -1` is accidentally right) | **`rc 2` multiplicity**, both lines echoed |
| `n07` | a line matching the **CENSUS selector** but never executed (census inflation) | `rc 2`, lowercase "understates" | `rc 2`, **`UNDERSTATES`** — correct direction |

`n01` is the interesting one: it is a genuine sixth way to defeat `| tail -1` — a summary line
arriving through the *filesystem* rather than through a `print` — and **T383's fix closes it without
having enumerated it**, which is the sign that the fix is a property (singleton population) and not
a patch list. **No defeat, old or new, succeeds against T383's file.**

**Stale-log reuse and commit-message echo are not vectors, and I checked rather than assumed.**
`_ST_OUT` is captured fresh from a subprocess on every fire; nothing downstream re-reads `$LOG`; and
the self-test runs *before* `git pull`, so no commit text is in scope. Recorded as reasoned-not-
driven.

**The residual limit, stated because T383 also owns it:** a self-test that runs zero rows but prints
one well-formed `ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0` still starts the fire. Multiplicity,
reconcile and census close every *inconsistent* lie; a *consistent* one is out of reach of any
wiring that grades the grader's own output. That is inherent, not a T383 defect.

---

## 2. **F-T385-1 — the substring-containment RATIONALE is false as stated.** Driven.

T383 keeps substring containment green deliberately, and gives this reason in the shipped source
(`fire-program.sh:1437-1439`) and again in the handoff:

> "a line that merely CONTAINS the token — `note: … ROWS=45 …`, **or this wiring's own
> `lockselftest| ROWS=…` echo** — is NOT in the population"
> "the wiring's own `lockselftest| ROWS=` echo is a substring line, and **a naive `grep -c ROWS=`
> fix would have refused every healthy fire**."

The task asked me to verify this reasoning independently. It does not hold.
The population is taken over `$_ST_OUT`:

```
_ST_OUT="$(/bin/zsh "$FIRE_SELF" --self-test-lock-readers 2>&1)"          # fire-program.sh:1339
print -r -- "$_ST_OUT" | while IFS= read -r l; do log "lockselftest| $l"; done   # :1340
_ST_SUMS="$(print -r -- "$_ST_OUT" | LC_ALL=C grep -E '^ROWS=…$')"        # :1459
```

The `lockselftest| ` prefix is added **downstream of the capture**, when each line is handed to
`log()`. It is never in `$_ST_OUT`, so it cannot join the population **whether the selector is
anchored or not**. Measured [`out/05-substring-claim.txt`, `bin/t385-substring-claim.zsh`]:

```
A. $_ST_OUT on a healthy run: 70 lines
     unanchored /ROWS=/                 : 1
     the shipped anchored selector      : 1
     /lockselftest\| ROWS=/             : 0        <-- not in the capture at all
B. the same run's LOG:  'lockselftest| ROWS=' lines : 1   (emitted, but downstream)
C. DECISIVE — build the naive wrapper T383 says would refuse every healthy fire:
     _ST_SUMS="$(print -r -- "$_ST_OUT" | LC_ALL=C grep 'ROWS=')"
     -> HEALTHY input -> rc 0, "tally VERIFIED …", "probe only — exiting"
   C-control: the SHIPPED anchored wrapper, same input -> rc 0
```

**So the substring line IS emitted on a healthy run — into the log, which is the wrong side of the
capture — and the naive unanchored count STARTS the healthy fire.** T383's example is wrong.

**Is the discrimination nonetheless principled? Yes.** The rule "only a whole line that is nothing
but a summary is a summary" is independently right and independently *measured* here — it is what
makes `d06`/`d07` (whitespace), `d08` (data), `d09` (stderr), `n02`/`n03` (CRLF) and `n04`/`n05`
(UTF-8) land SHUT in both roles, and it is what keeps `d12` green. It is a property, not a special
case, and the next echo will not break it: any *future* narration line emitted **by the self-test
itself** carrying the token would falsely trip an unanchored count, and the anchoring is exactly the
defence. Today the self-test emits no such line (measured: 1 unanchored match, which is the summary).

**Condition:** replace the `lockselftest| ROWS=…` example with one that is actually in the
population — self-test narration — in `fire-program.sh:1437-1439` and the handoff. The code needs no
change.

---

## 3. **F-T385-2 — the z06/z07 offsets ARE re-spelled. The "cannot drift apart" claim is false, and I drove the drift.** MODERATE.

`fire-program.sh:748-749` (T383's new block):

> "The z06/z07 offsets are named here rather than re-spelled, so the tests below and the rows that
> consume them **cannot drift apart**."

Every occurrence of the four gate variables, read out of the shipped file
[`out/11-skew-drift.txt`, top]:

```
697  _OLD_AGE=$(( LOCK_CEILING_SECS * 2 + 60 ))      698  _OLD="$(_epoch_iso8601 … _OLD_AGE …)"
706  _NEAR_AGE=$(( LOCK_CEILING_SECS - 3600 ))       707  _NEAR="$(_epoch_iso8601 … _NEAR_AGE …)"
753  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS * 2 + 60 ))
754  _SKEW_NEAR=$(( LOCK_RELEASE_SKEW_SECS / 2 ))
756-761  the six gate assertions            763  the refusal message
866  group C header (reads _OLD_AGE)        900  _row g01 (reads _NEAR / _NEAR_AGE)
```

`_SKEW_FAR` and `_SKEW_NEAR` occur **only in the gate and its own message**. The rows that consume
those offsets still spell them inline:

```
883  _row z06 HELD "… \"released_at\": \"$(_epoch_iso8601 $(( _NOW_E + LOCK_RELEASE_SKEW_SECS * 2 + 60 )))\" …"
884  _row z07 FREE-released "… \"released_at\": \"$(_epoch_iso8601 $(( _NOW_E + LOCK_RELEASE_SKEW_SECS / 2 )))\" …"
```

C and G are genuinely shared (`_OLD`/`_NEAR` are computed once and consumed by the rows). **Z is
not.** The gate and the rows are two independent spellings of one expression — the P-80 shape the
block above it invokes.

**Driven, with its control** [`bin/t385-skew-drift-probe.zsh`, `out/11-skew-drift.txt`,
`CHECKS=3 WRONG=0 VOID=0`]:

| | mutation | result |
|---|---|---|
| `s00` | CONTROL, unmutated | `rc 0`, z06 `ok`, z07 `ok`, fire starts |
| **`s01`** | drift **the ROW's** spelling only (`* 2 + 60` → `/ 2` at `:883`); the gate untouched | **the gate does NOT fire.** `z06 *** FAIL-OPEN want=HELD got=FREE-released`, then `FATAL: … FAILED (rc=1, FAIL_OPEN=1 …). The thresholds validated at startup, so this is the READERS.` `rc 2` |
| `s02` | CONTROL, drift **the GATE's** variable instead | **`rc 78`**, `past-skew offset=0`, THRESHOLD — the gate is live and reacts to its own variable |

`s01` is the exact fault F-T380-2 exists to close — *a broken **fixture** graded as a **reader**
fault* — reproduced through the spelling the comment claims is protected. `s02` proves `s01` is not
a dead gate.

**Severity: MODERATE, not a live fail-open.** With today's file both spellings are identical, so
every threshold value behaves correctly (§4 below). What is wrong is that the comment tells the next
editor a safety property that does not exist, and that editor is exactly the reader who would touch
one spelling and not the other.

**Condition (either is sufficient):** move `_SKEW_FAR` / `_SKEW_NEAR` above the group-Z rows and have
`:883`/`:884` consume them — which would make the claim true and is a two-line change inside T383's
grant — **or** delete the sentence and say plainly that Z's offsets are duplicated.

---

## 4. F-T380-2 AND ITS NEW COST — **it is a BOUND, not a BAN.** Re-driven, and the TOP of the range measured for the first time.

`bin/t385-threshold-drive.zsh` — my own, 14 cases, nothing mutated (the environment IS the input),
every refusing case paired with an accepting one on the other side.

* **GREEN, T383's file: `CHECKS=14 WRONG=0` — `RESULT: PASS`** [`out/07-green-thresholds-fixed.txt`]
* **RED, `main`: `CHECKS=14 WRONG=6` — `RESULT: FAIL`** [`out/08-red-thresholds-shipped.txt`]

| case | `LOCK_*` | `main` | T383's file |
|---|---|---|---|
| `t00` | **defaults 86400 / 3600** | `rc 0` | **`rc 0` — the configuration that actually runs STARTS** |
| `t03` | ceiling 604800 (7 d) | `rc 0` | `rc 0` |
| `t04` | ceiling **3601** | `rc 0` | **`rc 0`** — one second above the bound |
| `t05` | ceiling **3600** | **`rc 0`** | **`rc 78`**, `inside-ceiling age=0` |
| `t02` | ceiling 1800 | **`rc 0`, vacuous g01** | **`rc 78`**, `inside-ceiling age=-1800` |
| `t09` | ceiling 86401 | `rc 0` | `rc 0` |
| `t07` | skew 0 | `rc 0` | `rc 0` — the minimum is still 0, `>=` is deliberate |
| `t10` | skew 86400 | `rc 0` | `rc 0` |
| `t01` | ceiling int64max | `rc 2`, **blames READERS** | **`rc 78`, THRESHOLD** |
| `t06` | skew int64max | `rc 2`, **blames READERS** | **`rc 78`, THRESHOLD** |
| `t08` | ceiling `abc` | `rc 78` `_knob_int` | `rc 78`, **same** `_knob_int` message — the new gate did not displace the old one |
| `t13` | ceiling int64max/2 | `rc 2`, blames READERS | `rc 78` |

`t04`/`t05` straddle the lower boundary by **one second**, which is what makes it a comparison
against the fixture rather than a typed cardinal. T383's f01–f08 all reproduce.

### NEW — the TOP of the accepted range, which T383 recorded `[UNVERIFIED]`

The binding constraint is `_NOW_E - (CEILING*2 + 60) >= 0`, so the maximum is **derived by running
the same arithmetic**, never typed:

```
now(epoch)=1787921434  =>  derived maximum ceiling = 893960687 s  ~ 28 years
t11  ceiling = max - 3600  -> rc 0   fire starts
t12  ceiling = max + 3600  -> rc 78  THRESHOLD
```

**≈ 28.3 years**, which lands exactly on T380's estimate. The accepted interval for
`LOCK_CEILING_SECS` is therefore **`(3600, ~8.94e8]`** — nine and a half orders of magnitude wide,
containing the 24 h default four orders above its floor. This is unambiguously a bound.

### Can the `<= 3600` bound refuse a legitimate configuration? **No.**

* `.softhouse/launchd/mn.gerege.nbfi.softhouse-program.plist` and the **installed**
  `~/Library/LaunchAgents/…plist` are byte-identical and set **no** `LOCK_*` variable at all —
  `EnvironmentVariables` carries only `PATH` and `HOME`. So the default `86400` is what runs.
* The launchd job runs `/bin/zsh -lc …`, so a login profile could override it. There is none:
  `~/.zshenv`, `~/.zprofile`, `~/.profile` do not exist and `~/.zshrc` sets no `LOCK_*`.
* Repo-wide, the **only** assignment outside test drivers, captures, reviews and handoffs is
  `fire-program.sh:24` — `LOCK_CEILING_SECS="${LOCK_CEILING_SECS:-86400}"`.
* `.claude/skills/softhouse-program/SKILL.md:77` states arm 3 as **24 h**, and `:97` justifies it
  ("the longest fire ever recorded ran 9.52 h"). 86400 is **24×** the refusal bound.

No committed config or default sits at or below 3600, and none is near it. The refused region
(`<= 1 h`) is also, as T383 argues, the P-85 direction — a lifetime ceiling under an hour has arm 3
take over the lock of a fire that is still running.

**`rc == 78` really is reachable in a single-process run now**, and I reached it seven times through
the subprocess (`t01`, `t02`, `t05`, `t06`, `t12`, `t13`, `s02`), each landing on the wiring's
`the lock-reader self-test refused with EX_CONFIG (rc=78) … This is NOT a lock-reader regression`.
T377's `[UNVERIFIED]` is closed.

---

## 5. THE SEVEN LOCK ARMS STILL PARTITION — **0 disagreements, and `lock_decide` is byte-identical**

`.softhouse/capture/t279-lock-partition/drive-wrapper-vs-skill.zsh` re-run by me against the shipped
file at T383's head, **and against `main` as a control** [`out/06-192-state.txt`,
`bin/t385-192-state.zsh`]:

```
SUBJECT  T383 5c4f0244…   expected 192   driven 192   disagreements 0   RESULT: PASS
CONTROL  main dbb18b7b…   expected 192   driven 192   disagreements 0   RESULT: PASS
STRUCTURAL  lock_decide() bytes  shipped=1005  fixed=1005   IDENTICAL
```

No arm moved, so **no `SKILL.md` edit was implied and none was made** — `.claude/skills/` is not in
T383's diff. The structural check is the stronger statement: `lock_decide()` is byte-for-byte the
same function, and T383's edits are in `--self-test-lock-readers` and in the wiring, both of which
run *after* the `--lock-decide` dispatch. The P-85 double-holder hazard
(`patterns.md:2822`) is not opened by this branch.

---

## 6. F-T380-3 — the prose direction is read from the numbers. **Both directions driven, each grade forbidding the opposite word.**

`bin/t385-prose-drive.zsh`, two cases, each mutating the *rows* rather than the message.

* **GREEN, T383's file: `CHECKS=2 WRONG=0 VOID=0` — PASS** [`out/09-green-prose-fixed.txt`]
* **RED, `main`: `CHECKS=2 WRONG=2 VOID=0` — FAIL** [`out/10-red-prose-shipped.txt`]

| | forced condition | `main` | T383's file |
|---|---|---|---|
| `p-under` | one row wrapped in `if false` → `ROWS=44`, census 45 | "the tally **understates**" | "**UNDERSTATES** … a group guarded off, an early return, or a mangled if" |
| `p-over` | two rows joined onto ONE line → `ROWS=45`, census 44 | **the same "understates" sentence — false** | "MORE rows ran than the census can find declared … the tally **OVERSTATES** … Nothing was left ungraded" |

Each grade **forbids the opposite word**, so a future edit that re-collapses the branches fails here.
Numbers and refusal are unchanged in both directions; only the sentence moved. `n07` in the
multiplicity drive is a third, independent route into the UNDER branch (census inflation by a line
that matches the selector but never executes) and also reads `UNDERSTATES`.

---

## 7. THE BACKLOG T383 DID NOT REACH INTO — both confirmed genuinely outside its grant, and untouched

`git diff --name-only main...T383` is exactly the 18 paths T383 declares: `fire-program.sh`, three
`.zsh` drivers and thirteen transcripts under `capture/t383-t380-conditions/`, and its handoff.
**Not touched:** `.softhouse/conformance.sh` (T375's), `.softhouse/capture/t363-oracle-baseline/`
(T381's), `.softhouse/capture/t353-t342-conditions/` (T353's — where C12 lives),
`.softhouse/patterns.md` (T392's one entry), `.claude/skills/**`, `program.json`, `tasks.json`,
`nexus/`, `.softhouse/vectors/`. Confirmed.

### C12 — how severe is it for the merge instrument the driver is about to use?

`.softhouse/capture/t353-t342-conditions/bin/bar-on-merge-result.sh`, read at my head:

```
14   # It clones LOCALLY (hardlinks, no network), merges, and runs the bar in the clone.
23   echo "=== cloning $ROOT -> $S/clone (local, hardlinked, no network)"
24   git clone --quiet --local --no-hardlinks --shared "$ROOT" "$S/clone"
```

Both prose sites say **hardlink(ed)**; the flag is `--no-hardlinks`. *"local, no network"* is
accurate at both sites.

**Severity: LOW for correctness of the bar, MODERATE as documentation — and it is worse than a wrong
word.** The operative flag is not `--no-hardlinks` at all, it is **`--shared`**: the clone gets an
`objects/info/alternates` pointing back at the source object store and copies no objects. So the
prose is wrong twice — not "hardlinks" (it is alternates), and not the isolation model a reader
would infer. Hardlinked objects survive a source-side prune because the inode survives; **objects
borrowed through `--shared` do not.** The residual risk is that a concurrent fire running
`git gc --prune` in the shared checkout during a merge-bar run could take an object out from under
the clone.

**Why it is still LOW for the driver about to use it:** that failure mode is a *crash*, not a false
green — a missing object makes git and therefore the bar fail loudly, and `conformance.sh` returns
its own non-zero. **The misdescription cannot make the bar lie.** The script also does what it
claims where it matters: it never writes `$ROOT`, and it runs the bar on the merged tree.
It is a real defect, it should be fixed in T353's grant, and it does **not** block using the
instrument today. I used it (§8) and it behaved as documented apart from the word.

### The vacuous-pass rule as a numbered pattern (filed as T392)

`patterns.md` is not T383's grant and T383 did not write it — confirmed. I agree with T380's and
T383's shared argument for keeping the four implementations independent rather than factoring a
shared helper: a shared helper makes all four checks fail together, and these are the four gates
that stand between a broken self-test and a fire. **This branch adds a fifth site with the same
shape** (the multiplicity arm), which strengthens the case for numbering the rule.

### F-T385-4 — a gap in the census, and it is not T383's to close

T383's selector reasoning is **correct and I verified it**: `conformance.sh:1707` prints
`inspected $corpus tracked .sh/.py file(s)`, and the fail-open linter's corpus is tracked `.sh`/`.py`
only. `.zsh` files are genuinely invisible to the dead-path/fail-open census, so `10-regen-pin.py`
was neither needed nor run, and a green frontier says nothing about T383's three drivers (or my
five). T383 states this qualification openly rather than hiding it.

**It is worth filing.** `git ls-files` counts **110 tracked `.zsh`**, of which **98** are under
`.softhouse/capture/` or `.softhouse/reviews/` — i.e. the census excludes the language a large and
growing share of this program's *driving instruments* is written in, while covering 626 `.sh` and
722 `.py`. A fail-open linter whose corpus systematically omits one instrument language is a
coverage hole that widens with every fire. Needs its own grant (`conformance.sh` is T375's).

---

## 8. THE BAR

Run per the task's discipline: `bash`, never `sh` (`sh conformance.sh` exits 3 = wrong-interpreter
refusal), from a **CLEAN tree, after `git add -A` and commit**, and the probe line was checked for
**presence before value** (P-84): exit 2 + printed probe `down` = oracle unreachable; exit 2 with
**no** probe line = a HARD guard firing, i.e. the guard *working*; exit 3 = wrong interpreter.

### On my review branch — `EXIT 0`, probe line **PRINTED**, reads **`up`**

`git status --porcelain` was **empty** before the transcript was captured; the review dir was
`git add -A`'d and committed at `3ce7787f` first. Full transcript: `out/12-bar-on-branch.txt`
(665 lines).

```
bash .softhouse/conformance.sh        ->   EXIT 0
  reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
  oracle probe    UP
  parity vectors          PASS 46   FAIL 0
  inadmissible            0
  harness errors          0
  invariant violations    0
  cells compared          7884 graded, 93 ungraded (never recorded by the capture)
  ledger parity           PASS 7    FAIL 0      ledger cells 142 graded, 39 MONEY cells int64 minor units
  CENSUS fail-open instruments -- frontier 11, pinned at 11
  frontier == pinned (all 11 rows, by path).
  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
  T316-DEADPATH-CENSUS: corpus=1348 deadFiles=76 deadOccurrences=109 resolving=1258 ...
  VERDICT: PASS (exit 0) -- 46 parity vectors match the pinned reference oracle, 7884 cells compared.
```

**Read correctly, per the task's own rule.** The probe line **was printed** and reads `probe = up`,
and the exit is 0 — the oracle-reachable green, not the exit-2-with-no-probe-line shape that means a
HARD guard fired, and not the exit-3 wrong-interpreter refusal. Every figure matches the one T383
reported for its own branch.

**T383's `10-regen-pin.py` reasoning verified empirically on my own branch.** My branch adds seven
`.zsh` drivers and no `.sh`; `git ls-files | grep -cE '\.(sh|py)$'` is **1348 at my base `d1a6b7e6`
and 1348 at my head**, and the run reports `corpus=1348 deadOccurrences=109` — unchanged. `.zsh` is
genuinely invisible to the `.sh`/`.py` selector, so the pin needed no regeneration on T383's branch
either. That is also **F-T385-4**: the invisibility is real, and it is a gap.

### Second run, on the fully clean tree that includes this review's own instruments — `EXIT 0`

Re-run after committing the two bar transcripts and `bin/t385-mutate.py`, so the cited transcript is
itself from a fully clean tree (`git status --porcelain` empty). `out/14-bar-on-branch-run2.txt`.

```
bash .softhouse/conformance.sh   ->   EXIT 0
  reference oracle (…/actuator/health) probe = up
  parity vectors  PASS 46  FAIL 0      cells compared 7884
  frontier 11, pinned at 11 ; frontier == pinned (all 11 rows, by path).
  T316-DEADPATH-CENSUS: corpus=1349 deadFiles=76 deadOccurrences=109 …
  VERDICT: PASS (exit 0)
```

`corpus` moved **1348 → 1349** — exactly my one `.py` instrument — while `deadFiles=76`,
`deadOccurrences=109` and the frontier are **unchanged**. So `t385-mutate.py` enters the corpus and
adds no frontier row, and `10-regen-pin.py` was neither needed nor run here either. Measured, not
assumed; this is the run that says so.

### On the MERGE RESULT (`main` + `softhouse/T383-t380-conditions`, in a scratch clone) — `EXIT 0`

`bash .softhouse/capture/t353-t342-conditions/bin/bar-on-merge-result.sh <root>
softhouse/T383-t380-conditions main`, in a scratch clone — **not** on the branch alone. Full
transcript: `out/13-bar-on-merge-result.txt`.

```
=== base:   origin/main   f3bf5563
=== merging origin/softhouse/T383-t380-conditions  151ef180
=== merge result: 5bb4260d          (merged cleanly, no conflict)
=== running: bash .softhouse/conformance.sh
  reference oracle (…/actuator/health) probe = up
  parity vectors          PASS 46   FAIL 0
  frontier 11, pinned at 11 ; frontier == pinned (all 11 rows, by path).
  dead-path frontier: GREEN, and the T323 reconciliation list is empty.
  T316-DEADPATH-CENSUS: corpus=1372 deadFiles=75 deadOccurrences=108 resolving=1287 …
  VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
MERGE_RESULT_CONFORMANCE_EXIT=0
```

Probe line **printed**, reads `up`; **exit 0**. The merge is clean and the merge result is green.
The census figures differ from my branch's (`1372/108` vs `1348/109`) because the two trees have
**different bases** — the merge result is `main @ f3bf5563` while my branch forked at `d1a6b7e6`,
and `main` took several merges in between. The *pinned* gate — frontier 11 == 11, **by path** — is
green on both, which is the figure that gates.

**C12, measured while using the instrument.** I inspected the clone the script left behind:

```
$ cat <clone>/.git/objects/info/alternates
/Users/buv/gerege-nbfi/.git/objects
$ find <clone>/.git/objects -type f | grep -vc info/
6
```

Six objects in the clone, and an `alternates` file pointing at the **live shared checkout's** object
store. That is the `--shared` model, definitively not hardlinks — which puts the measurement behind
the C12 severity call in §7.

---

## 9. MONEY-MATH AND NON-NEGOTIABLES

No money is computed anywhere on this path; `fire-program.sh` is a launchd wrapper that decides a
lock and starts an orchestrator. I re-grepped T383's **added lines** rather than trusting its
self-report: every value the diff computes is an integer count of seconds, of lines, of rows or an
exit status, and every comparison is inside `(( ))`. No float/double/decimal literal. No
`mysql|mariadb|ojdbc|oracle\.jdbc|:1521`. No `first_name|last_name`. No
`Stripe|Plaid|Lithic|Persona`. No hard-coded UTC offset — the ISO-8601 helpers accept a `Z` suffix
only and are untouched. "Oracle" here is the Fineract reference implementation; the only database
near this work is PostgreSQL on 5432. No contract change, no `DEC-n` touched, no deposit surface.

## 10. WHICH WRAPPER INVOCATIONS T385 RAN, AND WHY EACH WAS SAFE

**A driver session is running under this file right now.** Every invocation below is a query or a
self-test, and **none can start a fire, take the repo lock or dispatch anything.**

| invocation | count | why safe |
|---|---|---|
| `zsh -n` / static read (`grep`, `sed`, `shasum`, python `.count`) | many | nothing executes |
| `--self-test-lock-readers` | ~6 (directly; plus once inside every `--probe`) | reassigns `$LOCK` to a `mktemp -d` scratch dir for its own lifetime; reads no repo, takes no lock, no network |
| `--lock-decide <5 signals>` | 384 (192 × 2 files) | a pure query, dispatched before the T301 re-exec and before any preflight; takes nothing, writes nothing, spawns nothing |
| `--probe` | ~130 | **always** `GEREGE_NBFI_REPO=/tmp/t385/subject` (a throwaway git repo I created) and `LOG_DIR` under `/tmp`. It exits at `probe only — exiting without taking the lock or invoking the driver`, which is **before** `git pull`, before the lock is read, and before anything is dispatched |

**Never** with no arguments, **never** `--force`, **never** pointed at `/Users/buv/gerege-nbfi`. The
repo lock was never taken. Every mutation case ran against a **copy** under `/tmp/t385/`; the shipped
files were executed unmodified only on the entry points above. I did not run the non-probe path.

**T383's recorded live-fire hazard, confirmed and honoured.** This session's environment really does
carry `FIRE_SNAPSHOT_OF=/Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh`,
`FIRE_SCRIPT_DIR` and `FIRE_REPO_SCRIPT`. My first probe inherited them and logged
`RUNNING FROM A SNAPSHOT — repo copy=/private/tmp/…` only *after* I unset them; the guard at
`fire-program.sh:999` is `[[ -z "${FIRE_SNAPSHOT_OF:-}" && "${FIRE_NO_SNAPSHOT:-0}" != "1" ]]`, so
`FIRE_NO_SNAPSHOT=1` genuinely does **not** override an inherited `FIRE_SNAPSHOT_OF`. **Every driver
in `bin/` here `unset`s all four as its second line.** T380 hit this, T383 hit this, T385 hit this —
three tasks in a row. It is now written down a third time.

## 11. WHAT T385 DID **NOT** CHECK, so this review's coverage is not overread

* I did **not** run the wrapper's non-probe path, start a fire, or take a lock.
* I did **not** re-run T383's own three drivers. I wrote six of my own (multiplicity, threshold, prose, skew-drift, substring-claim, zsh-idiom) plus a 192-state runner and two helpers, and drove both file states
  with them; the 192-state driver is the one existing instrument I re-ran, and the task named it.
* I did **not** test the off-BSD surface (`/usr/bin/stat -f`, `shasum`, `/bin/ps` flags,
  `hostname -s`). Unchanged by this branch and still untested. `[UNVERIFIED]`
* Seven of my nine instruments are `.zsh` and therefore outside the dead-path census's selector — the same
  honest qualification T377, T380 and T383 all made. A green frontier says nothing about them.
* I did **not** exercise a `LOCK_MAX_AGE_SECS` extreme; the new gate does not read it and
  `_knob_int` already bounds it from below.
* One of my instruments, `bin/t385-mutate.py`, is a `.py` and therefore **does** enter the
  `.sh`/`.py` census corpus. Its effect on the frontier and the census was **measured, not
  assumed** — see the second bar run in §8.
