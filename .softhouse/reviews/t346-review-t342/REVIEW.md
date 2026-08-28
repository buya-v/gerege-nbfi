# T346 — independent review of T342 (`softhouse/T342-releasedat-failopen` @ `d870db1d`)

Reviewer: T346, fire `20260828-140005`. I did not plan T342 and I am not its author.
Everything below was **re-derived**; no transcript of T342's was accepted as evidence.
My drives are in `bin/`, my outputs in `out/`.

## VERDICT: **ACCEPT-WITH-CONDITIONS**

T342's central engineering judgement is **correct and is confirmed by independent
measurement**: the shipped string surgery was fail-open on a wide class of lock bodies,
the one-line repair could not reach most of it, and replacing the four field reads with a
real JSON parse is the right remedy. My own adversarial corpus — written without reusing
T342's fixtures — makes the defect **worse** than T342 reported, not better: **19
fail-opens and 4 fail-shuts on `main`**, against the 7 and 2 T342 recorded.

But **two fail-opens survive on T342's branch** (F-T346-1), and the source comment T342
ships states two things about its own controls that are not true (F-T346-4, F-T346-5).
The conditions are below; all of them are small and one patch closes the safety half.

---

## Adjudication of T342's five claims

| # | T342's claim | My finding |
|---|---|---|
| 1 | Reproduced T280's F-A: `released_at: null` as last key → live lock declared FREE | **TRUE.** My row A02 reproduces it independently: `got=FREE-released` against a live pid on this host [`out/01-BEFORE-census.txt`] |
| 2 | 17 bodies, 7 fail-open, all fail-open; one-liner fixes one row and half of a second | **TRUE and UNDERSTATED.** My 35-row corpus finds **19** fail-opens and **4** fail-shuts on `main`. T342's 7 reproduces exactly on its own corpus [`out/01`, regenerated T342 census = 7] |
| 3 | Two unrecorded fail-SHUT defects; arm 2 could not reclaim a dead holder when `pid` was last key | **TRUE.** My rows B01/B02 reproduce it; I found **two more** (B04, C02) [`out/01-BEFORE-census.txt`] |
| 4 | Parser fixes it: census 7→0, positive controls 2→0, 192-driver 0→0 | **TRUE on T342's corpus; INCOMPLETE on mine.** 19→2 on my corpus. The two survivors are F-T346-1 |
| 5 | `lock_decide()` deliberately not touched | **TRUE.** Diff confirms; 192-state driver unchanged at 0 |

---

## Findings

### F-T346-1 — MAJOR — direction: **OPEN (P-85 safety)**. Two fail-opens survive the fix.

`_lock_json_field released_at str` accepts **any non-empty JSON string**, and `lock_decide`
arm 1 fires on any non-empty `rel`. So a `released_at` whose value is a string that *means
not released* is read as **released**, and a live lock is declared FREE.

Measured on the shipped branch, live pid on this host, fresh `started_at`
[`out/03-stringy-null-AFTER.txt`]:

```
released_at="null"     -> verdict=FREE-released
released_at="None"     -> verdict=FREE-released
released_at="NULL"     -> verdict=FREE-released
released_at="pending"  -> verdict=FREE-released
released_at=" "        -> verdict=FREE-released
released_at="false"    -> verdict=FREE-released
released_at="0"        -> verdict=FREE-released
released_at="-"        -> verdict=FREE-released
```

`"None"` is the one that decides the severity: it is what a naive Python writer emits from
`str(None)` or an f-string, and this program writes JSON from Python in
`ready-tasks.py`. `"pending"` is what a hand-writer produces to mean *not yet released*.
Both are the **exact inversion** T342 correctly identified for `null` — and T342's own
argument for BLOCKING severity ("the field written to say HELD was read as FREE") applies
to them verbatim. The fix narrowed the class; it did not close it.

Why T342 missed it: its census has **no `exit`** and always returns 0
[verified: `grep -n exit` on `census-lock-readers.zsh` returns nothing], so "0 fail-opens"
was never a mechanical check, only a human reading `*** FAIL-OPEN` lines off a corpus that
did not contain this shape. My census exits 1 on any failure, which is how it surfaced.

**Patch, verified, in `out/07-PROPOSED-patch-F-T346-1.diff`** — I did not apply it,
`fire-program.sh` is T342's file:

```zsh
  [[ -n "$(TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "$v" +%s 2>/dev/null)" ]] || return 0
```

in `lock_released_at`, after the `-z` test. It requires the value to be the same ISO-8601
instant `lock_started_age` already requires. With it applied: my census **0 fail-open, 0
fail-shut** (from 2/0), T342's census 0, T342's positive control exit 0, T280's probe 0
FAIL, 192-state driver 0 disagreements, `zsh -n` PASS. It also closes F-T346-3.

### F-T346-2 — MAJOR — direction: **SHUT (liveness)**. A missing interpreter silently voids arm 3's guaranteed takeover.

The new reader forks `/usr/bin/python3` per field. I enumerated the verdict per arm with
the interpreter absent and with it broken, by rewriting the hard-coded path in a **copy**
[`bin/t346-no-python.zsh`, `out/04-no-python.txt`]:

| arm | signal it needs | verdict when the interpreter is gone | direction |
|---|---|---|---|
| 0 `FREE-no-lock` | `[[ -f $LOCK ]]` only — **not parsed** | unaffected | — |
| 1 `FREE-released` | `released_at` | never fires → HELD | **shut** (safe) |
| 2 `TAKE-dead-pid` | `host`,`pid` → `absent` | never fires | **shut** |
| 3 `TAKE-ceiling` | `started_at` | never fires | **shut** |
| 4 `HELD-live` | tip age — **not parsed** | still fires | — |
| 5 `TAKE-both-stale` | `started_at` | never fires | **shut** |
| 6 `HELD-default` | — | **always** | **shut** |

**The safety direction is correct — no arm fails OPEN.** That is the important half and
T342 got it right. But arms 2, 3 and 5 are *every* takeover path, so with no interpreter
the lock is **permanently unreclaimable except by `--force`**. STEP 0 calls arm 3 "the arm
that gives the lock a *guaranteed* takeover time"; that guarantee is now conditional on an
interpreter starting, and nothing says so.

It fails **silently**: the log reads `started_age=<unreadable> pid_state=absent`, which is
indistinguishable from a genuinely corrupt lock body. The two earlier `/usr/bin/python3`
call sites (`:602`, `:603`) are both `|| true`, so nothing aborts first.

**Condition:** a one-line preflight before the lock decision at `:669` —
`[[ -x /usr/bin/python3 ]] || { log "FATAL: /usr/bin/python3 missing; the lock cannot be read and no takeover arm can fire"; exit 2; }` — converts a silent permanent wedge into a
stated one. Cheap, and it makes the new dependency legible.

### F-T346-3 — MINOR (MAJOR if F-T346-1 is not taken) — direction: **OPEN (P-85 safety)**. Interpreter stdout becomes a verdict.

`_lock_json_field` redirects **stderr** (`2>/dev/null`) but reads **stdout** verbatim. Any
interpreter that prints to stdout and exits 0 — a `sitecustomize` banner, a shim, a wrapper
— is read as the field value. Modelled with a stub that echoes one word
[`out/04-no-python.txt`, `is: liar`]: **every** arm flips to `FREE-released`, including
against a live holder and a dead holder. Fail-OPEN on all four probes.

`host`, `pid` and `started_at` are shape-checked downstream (hostname equality, `<1->`,
date parse), so `released_at` is the **only** field where stray stdout survives to a
verdict. F-T346-1's patch therefore closes this too, and I verified it does: with the patch,
the lying interpreter yields HELD-default on all four probes.

### F-T346-4 — MINOR. The source comment claims a control that is not wired and cannot fail.

`fire-program.sh:98-100` states the fail-open count "**is DERIVED on every run** by
`census-lock-readers.zsh`". Neither new drive is wired: I searched `.softhouse/conformance.sh`
for `census-lock-readers` and `positive-control` — **no match**. And the census has no
`exit`, so even once wired it cannot fail. There is no "every run".

T342 discloses both facts honestly in its handoff F3. The problem is that the **source
comment**, which is what ships and what the next reader believes, states it as fact. That is
the P-45 shape — *"when hardening a check, verify the path that actually executes in
CI/conformance calls it, not merely that a test does"* [`.softhouse/patterns.md:1503-1506`,
verified — P-45 is at that line]. **Condition:** soften the comment to "is derived by
`census-lock-readers.zsh`, **which is not yet wired into `conformance.sh` — see T342 F3**",
or wire it. Wiring requires adding the missing `exit`, per T342's own F3.

### F-T346-5 — MINOR. P-80 self-violation: the comment restates the cardinal it forbids restating.

`fire-program.sh:96-99` reads *"OF 17 ADVERSARIAL LOCK BODIES THE STRING SURGERY GOT 7
WRONG … **DO NOT RESTATE THAT 7 ANYWHERE** (P-80 — a corrected cardinal rots in every place
it was restated)"*. The sentence forbidding the restatement **is** the restatement, and it
hard-codes both 17 and 7. P-80 checked against the deliverable's own rule: it fails.

This is not pedantry — my census returns **19** on the same file, because the number is a
property of the corpus, not of the reader. The cardinal has already rotted. **Condition:**
delete the two numerals and keep the derivation sentence.

### F-T346-6 — MINOR — direction: **SHUT**. `lock_pid_state` lost read atomicity.

Previously `host` and `pid` came from **one** `body="$(<"$LOCK")"` snapshot. They now come
from **two independent forks**, so the file can change between them; a fire start now takes
four snapshots where it took three. I constructed the reachable interleavings and all land
**shut** (a truncated or deleted body makes a read fail → `absent` → HELD), and I could not
construct a fail-OPEN instance — but I did not exhaustively prove none exists, and I am
saying so rather than implying coverage. Recording it, not blocking on it. A single
`json.load` returning all four fields in one fork would remove the window and cut the cost
4×.

### F-T346-7 — INFORMATIONAL. The brief's premise about `main` being RED is false; T342 was right and has already been actioned.

The brief told me T342's "`main` is RED" and the driver's EXIT 0 "disagree" and asked me to
resolve it. **Neither statement is wrong; they are separated by a commit.**

- T342's base is `a2fa69f4` (`git merge-base`), which **is** an ancestor of `main`.
- Commit **`dc4e3ee3`** on `main` — *"softhouse: FIX main RED — driver merged T280 without
  running the bar; T342 caught it"* — repairs exactly the row T342 filed
  (`T316-DEADPATH-FRONTIER REFUSED rows=110 pinned=109 added=1`,
  `.softhouse/reviews/t280-review-t279/probe/drive-hook.sh` writing `"$T/wt/.softhouse/late.txt"`).
- It **repaired the path rather than moving the pin**, which is the correct remedy and the
  one T342 recommended as "the real fix".
- I ran `bash .softhouse/conformance.sh` on my base myself [`out/05-conformance-main.txt`]:
  **EXIT=0**, probe line **PRINTED** and reading `up` (P-83/P-84: I checked it was printed
  before reading its value), `dead-path frontier: GREEN`, `parity vectors PASS 46 FAIL 0`,
  `7884 cells`.

So T342's blocker was **true when filed, correctly diagnosed, correctly declined as
out-of-grant, and is now fixed**. It should be credited, not adjudicated against.

### F-T346-8 — INFORMATIONAL. The 192-state driver is **not** decorative — but T342's F4 is now measured.

The brief flagged the driver's unchanging `0 disagreements` as the P-22 shape — *"a guard
you have not seen fail is not a guard"*. I mutation-tested it [`bin/t346-mutate-driver.zsh`,
`out/06-mutate-driver.txt`]:

```
M01 arm 1 inverted                        disagreements=96   CAUGHT
M02 arm 2 deleted                         disagreements=12   CAUGHT
M03 arm 3 comparison flipped              disagreements=27   CAUGHT
M04 arm 4 freshness gutted                disagreements=9    CAUGHT
M05 arm 6 default flipped to TAKE         disagreements=15   CAUGHT
M06 control: comment-only change          disagreements=0    correctly unmoved
```

**The counter moves.** The driver is live over `lock_decide()`, and the brief's suspicion is
not borne out. What **is** borne out is T342's own F4, which I converted from an argument
into a measurement by mutating the *readers* instead of the arms:

```
M07 lock_released_at gutted: ALWAYS reports released   disagreements=0   DRIVER BLIND
M08 lock_pid_state host read replaced by a constant    disagreements=0   DRIVER BLIND
```

A **maximal** fail-open — every lock always reported released — moves the counter by zero.
T342's F4 is correct and should be recorded as a pattern: *a conformance driver that
SUPPLIES a function's inputs proves nothing about the code that DERIVES them.* This is
precisely why F-T346-4 matters: the two drives that **can** see the readers are the two that
are not wired.

---

## Checks that passed

- **Anchor repair (DEC-2 rev-8 F-2).** T342 replaced `":884 and :1057"` with sentence
  anchors. Both resolve, and each returns **2** matches — the citation itself plus its
  referent (`:208`→`:1091`, `:209`→`:1264`). Self-inclusive matching is the benign case, not
  the F-2 defect (which is two *distinct* referents). `grep -n lock_holder_is_dead` finds
  both call sites as claimed. **No fresh rot**: the only `:NNN` citations left in the file
  are `patterns.md:2822` and `patterns.md:1503-1506`, both of which I resolved and both of
  which are correct (P-85 header is at 2822, P-85 body text matches T342's quotation;
  P-45 text matches). P-86 satisfied — rule text is quoted beside each P-number.
- **Wiring (P-45), by file and line.** The real fire path calls the readers at
  `fire-program.sh:670-674` (`LOCK_REL`/`LOCK_SAGE`/`LOCK_PSTATE` → `lock_decide`), and
  `_lock_json_field` is called at `:226`, `:227`, `:243`, `:251`. Not test-only.
- **`zsh -n`** PASS on the shipped file and on the patched copy.
- **Cost.** T342 claims 0.42 s/fire. I measured 5 × `--lock-signals` (4 parses + a git call)
  at 2498 ms ≈ 500 ms each. Consistent; the claim is not inflated.
- **Money non-negotiables.** Nothing to grade. I grepped the added lines for
  `float|double|decimal|round|amount|balance|currency|MNT|mysql|mariadb|ojdbc|oracle.jdbc|1521|first_name|last_name`
  — **zero hits**. No monetary value, no ledger row, no DB driver, no name field. The only
  arithmetic is integer epoch seconds. The new Python explicitly rejects a float or a bool
  where an `int` is required, which is the right direction. PostgreSQL-only untouched.
- **T342's own drives regenerated, not accepted** (P-22): census 7→0, positive control
  exit 1→exit 0, T280's probe 0 FAIL, 192-state driver 0→0. All reproduce.

## Conditions for ACCEPT

1. **F-T346-1** — apply `out/07-PROPOSED-patch-F-T346-1.diff` (or equivalent). This is the
   only condition with a safety (fail-open) direction.
2. **F-T346-4** — correct the "derived on every run" claim in the source comment, or wire
   the drives and give the census an `exit`.
3. **F-T346-5** — remove the restated cardinals `17` / `7` from the comment.
4. **F-T346-2** — add the `/usr/bin/python3` preflight, or state the dependency in the
   comment beside the polarity paragraph.

F-T346-3 is closed by condition 1. F-T346-6 is recorded, not blocking.

## Unverified

- I never ran a real fire or touched the real `.softhouse/LOCK`. Every drive used a scratch
  directory under `$TMPDIR` with `GEREGE_NBFI_REPO` pointed at it.
- The interpreter-absent and lying-interpreter results were obtained by rewriting the
  hard-coded path in a **copy** of the shipped file. I verified the substitution applied
  before trusting each result (the harness aborts if it did not), but I did not remove the
  real `/usr/bin/python3`.
- I did not re-audit whether consumers of `LOCK` exist beyond `fire-program.sh` and
  `ready-tasks.py`; I accepted T342's grep, which is a statement about that search.
- I could not construct a fail-OPEN TOCTOU interleaving for F-T346-6, but did not prove
  none exists.
