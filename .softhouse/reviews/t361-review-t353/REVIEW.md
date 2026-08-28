# T361 — independent review of the stack `T342` → `T353`

**Verdict: ACCEPT-WITH-CONDITIONS. The pair MAY merge, as one change, now.**

Branch under review `softhouse/T353-t342-conditions` @ **`539a7201`**, based on
`softhouse/T342-releasedat-failopen` @ `d870db1d`. Reviewer branch
`softhouse/T361-review-t353`. Everything below was **run on this tree**; no transcript of
T342's, T346's or T353's was accepted as evidence (P-22). Where I re-ran one of their
scripts I say so and I re-ran it, and where I built my own instrument I say that too.

`sha256(fire-program.sh @ 539a7201)` =
`c55a9c8b3a56e894030f4dc68a2bc4c8597d43a0ba18fce048d11c327086e22d`, printed by every
instrument below so no transcript here can be about a different file.

**Fail-direction convention used throughout, and every finding carries one.**
**OPEN** = a lock held by a LIVE process reads as takeable — the **P-85** safety direction,
*"TWO ORCHESTRATORS HELD THE LOCK AT ONCE, AND THE CAUSE WAS AN UNPUSHED IN-FLIGHT STATE"*
[`.softhouse/patterns.md:2822`, resolved and quoted, P-86]. **SHUT** = a reclaimable lock is
not reclaimed, or the fire refuses to start — a liveness cost, never a data-loss one.

---

## The short version

1. **The stack is a real, measured improvement in the OPEN direction and it regresses
   nothing.** On my own corpus, written without reusing anyone's rows, T342's head scores
   `FAIL_OPEN=11` and T353's scores `FAIL_OPEN=7` on the same 24 bodies, **row for row, with
   no row moving the wrong way** [`out/03`, `out/04`]. On Linux, T342 loses arm 3 entirely
   (`FAIL_SHUT` on both ceiling rows) and T353 restores it [`out/11`, `out/10`].
2. **`_iso8601_epoch` survives everything I could throw at it.** 93 adversarial checks —
   including the century rules, day 0, month 13, hour 24, `:60`, five-digit and negative
   years, `+00:00`, lowercase `z`, an embedded NUL, a 10 MB argument, arithmetic and command
   injection, and non-ASCII digits — **0 wrong, on macOS and inside Linux** [`out/01`,
   `out/24`]; **10 locales, 0 wrong** [`out/23`]; 4012 round-trips and 509 format
   cross-checks against python, 0 mismatches. **No input reaches `$(( ))` unsanitised** and
   the injection canary never fired. Overflow is unreachable: the 4-digit-year glob bounds
   the output to `[-62167219200, 253402300799]`, seven orders of magnitude inside int64.
3. **Every instrument T353 reports reproduces**, including the two I most expected to be
   flattered: T346's mutate-driver returns **96 / 12 / 27 / 9 / 15**, control 0, M07 blind,
   M08 VOID, and M07b/M08b/M09b blind-to-driver-caught-by-self-test, **byte-for-byte**
   [`out/13`]; the 17-check red drive returns `CHECKS=17 WRONG=0` with r06 GREEN [`out/14`].
4. **The bar disagreement is honest and I regenerated both halves on a NEWER `main` than
   T353 used** (`e9b7e5c3`, not `65bb4e6e`): merge result **EXIT 0**, probe line present
   reading `up`, 46 parity / 0 FAIL / 0 inadmissible, frontier GREEN, ledger pins unmoved
   [`out/15`]; branch alone **EXIT 2** with **exactly one** hard-guard failure and **no
   second failure hiding behind it** [`out/22`].
5. **The driver's framing is refuted and T353 is right about it.** Re-derived from scratch:
   `local-launchd` pairs with `Buyanmunkhs-Mac-mini` and **nothing else**, in every LOCK
   commit that has ever existed; there is no CI workflow, no second invoker, and STEP 0's own
   text treats the cloud fire as not running this file [`out/12`]. The defect was **latent
   and SHUT**, not live.
6. **Eleven findings.** None is a merge blocker. The two that matter are **F-T361-1** — a
   `released_at` of `0001-01-01T00:00:00Z`, which is what Go's zero `time.Time` marshals to,
   frees a live lock (**OPEN**) — and **F-T361-2**, an unchecked `mktemp` in the new
   self-test that makes its EXIT trap issue `rm -rf /`.

---

## 1. `_iso8601_epoch` — the hand-rolled date parser, attacked

`.softhouse/reviews/t361-review-t353/bin/attack-iso8601.zsh`, outputs
[`out/01-attack-iso8601-mac.txt`] and [`out/24-attack-iso8601-linux.txt`].
The function is **extracted from the shipped file by `sed`, never retyped** (P-46), and the
drive **aborts** if the extraction does not yield a callable function — an empty extraction
that "passes" is the P-22 shape, *"a guard, a canary, or a control that cannot fail is worse
than none — because it is believed"* [`.softhouse/patterns.md:473`].

**Expectations are derived independently of T353's rig.** T353's `epoch-parity.zsh` grades
against BSD `date -j` and `strptime`; I grade against `calendar.timegm`, and for year 0000 —
which python's `datetime` cannot represent — against the proleptic-Gregorian identity
`0000-01-01 = -719528 days` computed by hand.

### `CHECKS=93 WRONG=0`, twice: macOS/arm64 zsh 5.9, and Alpine/aarch64 zsh 5.9.

| attack | result | fail direction if it had been wrong |
|---|---|---|
| epoch, 1969-12-31, 2038 boundary both sides, 1901-12-13 (int32 min) | exact | — |
| **1900-02-29, 2100-02-29** (century non-leap) | **REFUSE** | accept → OPEN at `released_at` |
| 2000-02-29, 2004-02-29, 2400-02-29 (leap) | exact | — |
| 2026-02-29, 2026-02-30, 2026-04-31, 06-31, 09-31, 11-31 | REFUSE | accept → OPEN |
| **day 00, day 32, month 00, month 13, month 99** | REFUSE | accept → OPEN |
| **hour 24, hour 99, minute 60, second 61, second 99** | REFUSE | accept → OPEN |
| **`:60` leap second** | **ACCEPTED**, maps to the next second | see below |
| lowercase `z`, `+00:00`, `+08:00`, `-00:00`, no zone, space-for-`T`, lowercase `t` | REFUSE | accept → OPEN |
| fractional seconds, basic format `20260828T140005Z` | REFUSE | accept → OPEN |
| **5-digit year, 3-digit year, negative year, leading `+`** | REFUSE | accept → OPEN |
| leading/trailing space, leading/trailing newline, tab, CR | REFUSE | accept → OPEN |
| **trailing NUL, NUL in the middle** | REFUSE | accept → OPEN |
| **`10 MB` of digits; 10 MB appended to a valid instant** | REFUSE | — |
| `None`, `null`, `pending`, `" "`, `Z`, date-only, a bare epoch integer | REFUSE | accept → OPEN |
| **arith injection `${_T361_CANARY::=99}`, `$(touch …)`, backtick, `<1-9>`, `[0-9]…`, `0x10`** | REFUSE, **canary unfired, no side-effect file created** | accept → **code execution** |
| **Arabic-Indic, fullwidth, Devanagari digits, superscript two** | REFUSE | accept → non-ASCII into `10#` arithmetic |
| leading-zero fields `08`/`09` (the classic octal shell-date bug) | exact | wrong value → arm-3 drift |
| shape max `9999-12-31T23:59:59Z`, shape min `0000-01-01T00:00:00Z` | exact | — |
| round-trip `_epoch_iso8601` → `_iso8601_epoch`, 4012 pairs | 0 mismatches | — |
| `_epoch_iso8601` vs python `strftime`, 509 values | 0 disagreements | a wrong "100 h ago" fixture makes self-test group C prove nothing |

**The evaluation question, answered by construction and then by driving it.** Every value
that reaches arithmetic (`y=10#${s[1,4]}` and friends, `fire-program.sh:306-307`) is a
substring at a FIXED offset of a string the glob at `:305` has already constrained to
exactly 20 characters, each of which is `[0-9]`, `-`, `T`, `:` or `Z`. `[0-9]` in a zsh
pattern is a **code-point range, not a collation range** — measured across **10 locales
including `tr_TR`, `ar_SA`, `mn_MN`, `ja_JP` and `en_US.ISO8859-1`, 0 wrong**
[`out/23-locale-sweep-mac.txt`]. This matters because the wrapper runs under launchd and
does not pin a locale. So no attacker-controlled byte can reach `$(( ))`.

**Overflow is unreachable, not merely untested.** The glob fixes the year at four digits, so
`|days * 86400|` is bounded by `2.6e11` against an int64 limit of `9.2e18`.

**The leap second is a deliberate acceptance and T353 discloses it.** `2016-12-31T23:59:60Z`
→ `1483228800`, which is BSD `date`'s answer too and one second past `23:59:59`. Python's
`strptime` refuses it. I record it as an acceptance rather than a disagreement, as T353 did.

### The regression surface T353's own rig does not enumerate

`bin/diff-vs-date-j.zsh`, [`out/02-diff-vs-date-j.txt`]. "Does the new parser AGREE with
`date -j` on 19 well-formed instants" is the wrong question for a **replacement**; the risk
is the inputs where they DISAGREE on the one host where the old code worked. BSD `date -f`
is lenient — it normalises out-of-range fields and ignores trailing garbage — so they
**cannot** agree everywhere.

`SAME=25  NEW-ONLY-REFUSES=10  NEW-ONLY-ACCEPTS=2  VALUE-MOVED=0`.

* All ten new refusals are **SHUT** at `lock_started_age` (`2026-02-30`, `2026-04-31`,
  `1900-02-29`, `2100-02-29`, day 00, trailing garbage…). Every one of those inputs is a
  malformed `started_at`, and refusing it costs a takeover, never grants one.
* The two new acceptances are `0000-01-01` and `0001-01-01`. **At `lock_started_age` they
  are still SHUT** — the epoch is negative and `[[ "$e" == <1-> ]]` at `:427` rejects it,
  measured as rows `x02`/`x03` of [`out/03`]. **At `lock_released_at` they are OPEN**, and
  that is **F-T361-1**.
* **`VALUE-MOVED=0`** is the load-bearing row: on no input do the two parsers return
  *different numbers*. Arm 3's threshold cannot have drifted.

---

## 2. Every arm when the parser refuses, and the ceiling off-BSD

`bin/t361-linux-probe.zsh`, run inside my own image (`bin/Dockerfile.t361-linux`, written
rather than reused). **BEFORE** = T342's shipped file, **AFTER** = T353's, same rows, same
container.

Host facts measured in the container, not read: `/bin/date` is **GNU coreutils 9.11**,
`-j` → `invalid option -- 'j'` rc 1, **and as shipped with `2>/dev/null` it is EMPTY**.
`/usr/bin/stat` **does not exist at all** — which independently corroborates T353's
follow-up F3 about the five `stat -f` sites.

| row | BEFORE (T342) | AFTER (T353) |
|---|---|---|
| C01 100 h old → `TAKE-ceiling` | `HELD-default`, **FAIL-SHUT**, `started_age=<unreadable>` | `TAKE-ceiling`, `started_age=360000` |
| C02 same, compact | **FAIL-SHUT** | `TAKE-ceiling` |
| A01 fresh live holder | HELD | HELD |
| B01 dead pid here | `TAKE-dead-pid` | `TAKE-dead-pid` |
| R01 `started_at` unparseable | HELD | HELD |
| R02 `started_at` = `2026-02-30` | HELD | HELD |
| R03 100 h old + `released_at:"None"` | `FREE-released` **FAIL-OPEN** | `TAKE-ceiling` |
| R04 `released_at:"pending"` | `FREE-released` **FAIL-OPEN** | HELD |
| R05 `released_at:"0001-01-01T00:00:00Z"` | `FREE-released` | `FREE-released` ← **F-T361-1** |
| D01 genuine release | `FREE-released` | `FREE-released` |
| F01/F02 foreign host | HELD (`other_host`) | HELD (`other_host`) |
| | `ROWS=12 FAIL_OPEN=2 FAIL_SHUT=3` | `ROWS=12 FAIL_OPEN=1 FAIL_SHUT=0` |

**Q1 answered: the ceiling fires off-BSD after this stack and did not before.** VERIFIED,
regenerated, not read.

**Q2 answered: when `_iso8601_epoch` refuses, every arm lands SHUT.** `sage` reads empty,
`rel` reads empty, and the verdict is `HELD-*` — with the one correct exception that a body
whose `started_at` IS readable and over the ceiling still fires arm 3 regardless of what
`released_at` says (R03). That exception is the design, and it is why the SKILL.md patch
handed to T343 overstates the polarity (F-T361-6).

**Q3, mine: the self-test itself passes inside the container** — `ROWS=27 FAIL_OPEN=0
FAIL_SHUT=0 SKIPPED=0`, `SELFTEST_EXIT=0`. So the wired control is valid on the host the fix
is for, not only on the host that never had the bug.

---

## 3. The self-test: three properties, verified separately, then mutated

**(a) 27 rows.** Run directly: `ROWS=27 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0`
[`out/06-selftest-pristine-mac.txt`]. Group B did not skip on any of the ~30 invocations
across this review.

**(b) It exits non-zero.** Not accepted from the handoff. My own mutations n01 (shape gate
removed), n02 (duplicate-key hook dropped), n05 (age negated) and n12 (epoch shifted −1 day)
each produce rc 1 with a non-zero count [`out/07-t361-mutate-readers.txt`]. Independently,
T353's red drive reproduces rc 1 on r01/r04/r05/r07/r08/r09 [`out/14`].

**(c) It runs fatally, by the fire, BEFORE the lock is read — verified by reading the
control flow, not the claim.** In `fire-program.sh` @ `539a7201`:

```
 937–962  PYTHON3 PREFLIGHT ......................... exit 2 on failure
 964–984  self-test, `zsh "$FIRE_SELF" --self-test-lock-readers`, exit 2 on rc != 0
 986      if (( PROBE_ONLY )) ....................... `--probe` returns here
1023–1027 LOCK_REL / LOCK_SAGE / LOCK_PSTATE / lock_decide  ← the real lock read
```

979 < 1023. Confirmed on the executing path as well: the red drive's wiring section runs the
**real `--probe`** and gets `PROBE_EXIT=0` on pristine, `PROBE_EXIT=2` with the fail-open
reader restored, `PROBE_EXIT=2` with python3 absent, `PROBE_EXIT=2` with a lying
interpreter [`out/14`, rows r04/r10/r11].

**Two scope notes on (c), neither a defect.** `--lock-decide` (`:450`) and `--lock-signals`
(`:462`) are handled early and exit before the preflight, so they read the lock **without**
the self-test — correct, they are print-only queries that take nothing. And the
`--self-test-lock-readers` handler at `:504` sits **before** the T301 snapshot re-exec at
`:672`, so the subprocess does not re-exec; combined with `FIRE_SELF` being `${0:A}` **after**
the exec, the self-test grades the snapshot bytes, which are the bytes that will decide.
T353's claim about this is exactly right.

### Then I mutated a reader, as T346 did to the driver

`bin/t361-mutate-readers.zsh`, [`out/07`]. Every mutant is `cmp`-checked against pristine and
`zsh -n`-checked; a mutation that did not apply or does not parse is **VOID**, never a pass.
13 checks, 0 unexpected after two expectations of mine were **measured and corrected in
writing rather than rescored**.

| mutation | self-test |
|---|---|
| c00 comment-only control | green (correctly unmoved) |
| n01 `lock_released_at` shape gate removed | **CAUGHT** `FAIL_OPEN=6` |
| n02 python `object_pairs_hook=no_dupes` dropped | **CAUGHT** `FAIL_OPEN=1` |
| n05 `lock_started_age` age negated | **CAUGHT** `FAIL_SHUT=2` |
| n12 `_iso8601_epoch` epoch shifted **−1 day** | **CAUGHT** `FAIL_OPEN=13` |
| n03 python `released_at` str/ctrl check dropped | BLIND — **masked** by the TypeError landing outside the `try` → unreadable → HELD |
| n04 python accepts a bool pid | BLIND — **masked** by `[[ "$pid" == <1-> ]]` at `:383` rejecting `"True"` |
| **n07 `lock_pid_state` host check DELETED** | **BLIND** ← F-T361-4 |
| n06 day-of-month bound dropped | **BLIND** ← F-T361-5 |
| n08 century leap rule → plain `%4` | **BLIND** ← F-T361-5 |
| n09 `[[ "$e" == <1-> ]]` deleted | **BLIND** ← F-T361-5 |
| n11 `_iso8601_epoch` epoch shifted **+1 day** | **BLIND** ← F-T361-5 |

n11 versus n12 is the sharp result: the self-test catches a one-day error in **one
direction** and not the other, because it has ceiling rows that MUST take and no
near-boundary row that must NOT.

**T353's justification for the self-test existing is independently confirmed.** I re-ran
T346's mutate-driver **unedited** through T353's own staging harness [`out/13`]:
`96 / 12 / 27 / 9 / 15` on arms, `0` on the control, and `0` — DRIVER BLIND — on all three
reader mutations, each of which the self-test catches with rc 1. T346's figures reproduce
exactly, and so does the blindness they were filed to demonstrate.

---

## 4. P-22 on the wiring itself

**The `${0:A}` fix is real and complete for its class.** `FIRE_SELF="${0:A}"` is at `:721`;
the only `cd` that persists is `:861`; `cd "$REPO"` at `:463` is inside the `--lock-signals`
branch, which exits at `:474`. **`awk 'NR>861 && /\$\{0|\$0/'` over the shipped file returns
one hit and it is a comment** — there is no other post-`cd` self-path resolution to fix.
`SCRIPT_DIR` (`:708`), `FIRE_SCRIPT_DIR` (`:669`), `FIRE_REPO_SCRIPT` (`:670`), the `source`
at `:773` and `ATTEST` at `:811` are all pinned or used before `:861`.

T353's choice of a **new** variable rather than reusing the already-pinned `FIRE_REPO_SCRIPT`
is deliberate and correct: `FIRE_REPO_SCRIPT` names the repo copy, `FIRE_SELF` names the
running copy, and the self-test must grade the running copy.

**But two hazards of the same "the new control bricks the fire" class remain, and I drove
both** — F-T361-2 (`mktemp`) and F-T361-3 (config coupling), below.

---

## 5. The preflight gates — can they stop every fire?

**Fail direction: SHUT, by design, and yes they can — that is what they are for.** The
question worth answering is whether they can do it **spuriously**, and whether they widen the
blast radius.

* **They do widen it, and T353 does not say so.** `ready-tasks.py`'s failure is *not* fatal
  (`fire-program.sh:2128-2138`: rc is logged into `RECON_VERDICT` and the function
  `return 0`s), and the two `branch_sweep.py` calls at `:906-907` are `|| true`. So **before
  T353 a fire on a python3-less host still RAN** — degraded, unable to reclaim a lock it
  could not read, but running. **After T353 it refuses.** Recorded as **F-T361-11**; it is a
  deliberate, argued trade (a silent permanent wedge for a stated refusal) and I do not
  contest it, but "it cannot become the thing that stops every fire" is the wrong reading and
  the source comment should not be read as claiming it.
* **They add no new HANG risk.** `/usr/bin/python3` is already invoked at `:906` and `:907`,
  *before* the gate at `:954`, so a stub that blocks (macOS without Command Line Tools pops a
  GUI prompt) would already have blocked. Pre-existing, not widened. Neither gate has a
  timeout; neither did the calls before them.
* **Gate 2 is correctly stricter than `-x`.** `_PY_OK` must equal exactly `ok`; a banner on
  stdout yields `banner\nok` ≠ `ok` → refuse. Driven three ways (absent / broken / liar) with
  `PROBE_EXIT=2` and an attributed message each time [`out/14` r10/r11, `out/20`].
* **F-T346-3 is independently closed.** Re-running T346's own no-python probe on this tree:
  absent, broken and liar all give `HELD-default` on all four states — **no fail-open in any
  interpreter variant** [`out/20-rerun-t346-no-python.txt`]. T346 had measured a liar
  flipping every arm to `FREE-released`.
* **Timing reproduces**: 5 `--lock-signals` invocations in 2003 ms ≈ 400 ms each, against
  T353's 410 ms and T346's pre-change 500 ms.

---

## 6. The census, re-derived — the driver's framing really was wrong

`bin/t361-lock-census.sh`, written from scratch, [`out/12-t361-lock-census.txt`].

My population is `git log --all` and finds **137** commits touching `.softhouse/LOCK`, not
T353's 124 — a different ref set, not a different fact, and it is the *pairing* that carries
the argument, not the cardinal:

| holder @ host | n |
|---|---|
| `local-launchd @ Buyanmunkhs-Mac-mini` | 69 |
| (LOCK deleted at that commit) | 58 |
| `cloud-routine @ claude-code-remote-sandbox` | 3 |
| `local-fire-20260822-060013[b] @ buyan-mac` / `@ Buyanmunkhs-Mac-mini` | 5 |
| `none @ -` | 2 |

**Six distinct `holder`/`host` pairs have ever existed and `local-launchd` appears with
exactly one host.** The wrapper hard-codes `"holder": "local-launchd"`
(`fire-program.sh:620`), so a lock it wrote from the cloud sandbox would be visible and there
is none.

**And I looked for the paths the census cannot see, because "not found" is a statement about
the search.** I searched for: launchd plists (one, `mn.gerege.nbfi.softhouse-program.plist`,
`ProgramArguments = /bin/zsh -lc /Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh`, i.e.
an absolute Mac path); every tracked file that *invokes* rather than *names* the wrapper (one
— the T301 self-exec at `:681`); `.github/workflows` (**absent**); anything naming
`claude-code-remote-sandbox` (only `tasks.json` prose). And SKILL.md's own fire table lists
the cloud routine as `trig_01J7a66YFD7mzSLiKiFsj5XV` with **no** wrapper in its row
(`SKILL.md:23`), while `SKILL.md:304` says of the wrapper's attestation *"This item is what a
driver run by hand, or by the cloud fire, must do for itself."*

**Conclusion: T353's refutation stands. The defect was LATENT and SHUT.** The severity
reduction is earned; the correctness of the fix is unaffected.

---

## 7. The bar, both halves, regenerated on a fresher `main`

I re-ran T353's `bar-on-merge-result.sh` twice, against **`main = e9b7e5c3`** — five commits
newer than the `65bb4e6e` T353 used — and against the branch head **`539a7201`**, which is
newer than the `3a4f24f4` T353's last transcript names.

**Merge result — `main e9b7e5c3` + `539a7201` → `a0fe1668`: EXIT 0**
[`out/15-bar-MERGE-RESULT-exit0.txt`].
P-83 discipline applied rather than claimed: `grep -c 'probe = '` returns **1** — the line is
**PRESENT** — and only then did I read it: `probe = up`.

```
conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty.
conformance:   NAMESPACE-CENSUS: dirs=163 … collidingIds=2 declared=2 unclaimed=2 shortfallIds=0
    parity vectors          PASS 46   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    inadmissible            0
    cells compared          7884 graded, 93 ungraded
    ledger parity           PASS 7    FAIL 0
exemption census READ: LEDGER parity vectors = 7 == pinned 7 ; LEDGER money cells = 39 == pinned 39
VERDICT: PASS (exit 0)
MERGE_RESULT_CONFORMANCE_EXIT=0
```

`dirs=163` where T353 measured 161: `main` has moved, and `shortfallIds=0` either way. **No
pin moved.**

**Branch alone: EXIT 2, and it is the row T353 says it is — I checked for a second one**
[`out/22-bar-BRANCH-ALONE-exit2.txt`]. `grep -nE 'FAILED|REFUSED|EXIT 2'` over the whole
transcript returns **three lines and they are one event**:

```
T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=109 added=1 removed=0
> .softhouse/reviews/t280-review-t279/probe/drive-hook.sh | .softhouse/late.txt
conformance: guard_dead_path_frontier FAILED.
conformance: a HARD guard failed. EXIT 2
```

One added row, zero removed, nothing else red. And `dc4e3ee3` on `main` — *"FIX main RED —
driver merged T280 without running the bar; T342 caught it"* — touches exactly
`.softhouse/reviews/t280-review-t279/probe/drive-hook.sh`, which is the file the row names.
`grep -c 'probe = '` on the branch-alone transcript returns **0**: `run_guards` exits before
it is printed, so **there is no value to read there** — T353 says exactly this and did not
invent one (P-84).

**Committing both transcripts rather than the convenient one is the right call and I am
recording it as such.**

---

## 8. Grading T343's SKILL.md patch (handoff §10)

**First, a finding against my own brief.** The brief says *"the 192-state driver compares the
wrapper to **that text**, so a wrong edit there makes a wrong wrapper look correct."* **That
is false.** `drive-wrapper-vs-skill.zsh` never opens SKILL.md; it compares the wrapper to
`.softhouse/capture/t279-lock-partition/rules.py`, a hand-written model, and its own output
line says so: *"disagreements with SKILL.md STEP 0 **as modelled in rules.py**"*
(`drive-wrapper-vs-skill.zsh:62`). The hazard the brief describes is real but has the
opposite mechanism: **SKILL.md and `rules.py` can drift and nothing grades the gap.** T353's
four edits change no arm's boolean, so they introduce no such drift — but the next editor of
STEP 0 should be told, and is not. **F-T361-10.**

Grading the edits themselves against the shipped code:

* **(1) "Release is by DELETION. Nothing in this program writes a `released_at` field."**
  **TRUE, verified**: `grep -rn released_at` over `*.sh`/`*.zsh`/`*.py` outside
  `reviews/`/`capture/`/`handoff/` returns eight hits and **every one is a read or a log
  line**. ACCEPT — with the caveat in F-T361-1: the sentence that follows *invites* the
  defect, because a machine writing "an ISO-8601 UTC instant" from an unset time writes the
  Go zero.
* **(2) The arm-1 restatement.** Accurate about what makes arm 1 fire, and every listed
  negative is measured (`out/06` rows a09–a19). **But its closing clause is measurably
  false**: *"any doubt about the lock's contents is HELD, never free (arm 6)."* Doubt about
  `released_at` does not imply HELD — arms 2, 3 and 5 read other fields and can still TAKE.
  Measured: Linux row R03, `released_at:"None"` + a 100 h `started_at` → **`TAKE-ceiling`**,
  not HELD. **F-T361-6.**
* **(3) The 192-driver boundary paragraph.** Substantively correct and worth having. **But it
  writes five fresh cardinals — `96 / 12 / 27 / 9 / 15` — into a living document**, which is
  the exact restatement T353 spent Condition 3 deleting from `fire-program.sh` under P-80,
  *"A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED. The count is the same defect as
  the line number"* [`.softhouse/patterns.md:2775`]. **F-T361-7.**
* **(4) The new "(c)" interpreter entry.** Accurate; the `date -j` sentence and the
  no-fail-open claim both reproduce. One scoping slip: *"On this host the wrapper reads every
  lock field through `/usr/bin/python3`"* — the path is hard-coded at `:217` on **every**
  host, which is precisely why the entry is needed.

---

## Findings

Numbered `F-T361-n`. **Severity** is about this repo, not in the abstract. **None is a merge
blocker**; the conditions are listed after them.

### F-T361-1 — a `released_at` of `0001-01-01T00:00:00Z` frees a live lock. **MEDIUM. Fail direction: OPEN (P-85 safety).**

T353 tightened arm 1's input from "any non-empty JSON string" to "any syntactically valid
ISO-8601 UTC instant". That closes `"None"`, `"pending"`, `"null"`, `" "`. It does **not**
close the **zero-value instants**, which are what a machine emits for a timestamp it never
set — and which mean *not released* exactly as loudly as `"pending"` does.

**Measured, not reasoned** [`out/03-t361-reader-corpus-T353.txt`, rows z01–z06, y01; and
[`out/10-linux-AFTER-T353.txt`] row R05, so it is not a macOS artefact]. Holder is a **LIVE
pid on THIS host** in every row:

| body's `released_at` | verdict | what emits it |
|---|---|---|
| `0001-01-01T00:00:00Z` | **`FREE-released`** | **Go's zero `time.Time` through `encoding/json`** |
| `0000-01-01T00:00:00Z` | `FREE-released` | year-zero sentinels |
| `1970-01-01T00:00:00Z` | `FREE-released` | an int64 `0` formatted |
| `0001-01-01T00:00:01Z` | `FREE-released` | — |
| `9999-12-31T23:59:59Z` | `FREE-released` | `datetime.max` / a "never" sentinel |
| `2999-01-01T00:00:00Z` | `FREE-released` | a "not yet" sentinel |
| now + 1 year | `FREE-released` | a clock-skewed or scheduled writer |

**The Go fact is verified by running Go, not recalled.** `go1.23.4`,
`json.Marshal(struct{ ReleasedAt time.Time }{})` →
`{"holder":"go-fire","released_at":"0001-01-01T00:00:00Z"}`. Python's
`datetime.min` formats to the same string. **This repository's stated programme is a
"Fineract → Go native migration"** (CLAUDE.md), and the SKILL.md patch T353 hands to T343
tells a hand-writer *"if you do write one it must be an ISO-8601 UTC instant"* — which a Go
or python writer with an unset field satisfies by emitting exactly this.

**Not a regression, and that is why it is a condition and not a rejection.** The same corpus
on T342's head scores `FAIL_OPEN=11` and on T353's `FAIL_OPEN=7`; **no row moves the wrong
way**, and z01–z06/y01 are `FREE-released` on both. T353 strictly shrinks the hole. But it is
the same class as F-T346-1, which T353 was written to close, and the closure is one predicate
short.

**Condition C1** — reject a `released_at` that cannot be a real release. One line, the same
idiom `lock_started_age` already uses at `:427`:

```diff
--- a/.softhouse/bin/fire-program.sh
+++ b/.softhouse/bin/fire-program.sh
@@ lock_released_at()
   v="$(_lock_json_field released_at str)" || return 0
   [[ -z "$v" ]] && return 0
-  _iso8601_epoch "$v" >/dev/null || return 0
+  # T361 F-1, direction OPEN. A SYNTACTICALLY valid instant is not the same as a REAL
+  # release time. `0001-01-01T00:00:00Z` is what Go's zero `time.Time` marshals to through
+  # encoding/json (VERIFIED by running go, not recalled) and what python's `datetime.min`
+  # formats to; `1970-01-01T00:00:00Z` is an int64 0. Each is a writer saying NOT RELEASED,
+  # exactly like the `"None"`/`"pending"` strings T353 closed — and each was read as FREE
+  # while a LIVE pid held the lock. So the instant must also be PLAUSIBLE: after the epoch,
+  # and not in the future beyond a generous clock skew. A refusal here is HELD, which is the
+  # fail-closed side.
+  local -i _e _now
+  _e="$(_iso8601_epoch "$v")" || return 0
+  (( _e > 0 )) || return 0
+  _now=$(date +%s)
+  (( _e <= _now + LOCK_RELEASE_SKEW_SECS )) || return 0
   print -r -- "$v"
 }
```
with `LOCK_RELEASE_SKEW_SECS="${LOCK_RELEASE_SKEW_SECS:-3600}"` **added beside the other
thresholds at `:24-25` in the same commit** — the new variable is a new dependency and `set -u`
is in force. **This is applied and measured, not proposed**: see "The conditions, proven"
below. It closes z01–z06 and y01 — all seven — and it must ship with the self-test rows that
grade it, or the fix is invisible to the only wired control.

**The stated cost of C1, so nobody rediscovers it as a bug:** a `released_at` more than
`LOCK_RELEASE_SKEW_SECS` in the future now reads as *not released*. Direction **SHUT**,
configurable, and strictly preferable to the OPEN direction it replaces. Measured as corpus
row x11 flipping to HELD once C1 is applied [`out/26`].

### F-T361-2 — the new self-test's EXIT trap can issue `rm -rf /`. **MEDIUM. Fail direction: SHUT (realized), with an unstated dependency on `rm`'s own root guard.**

`fire-program.sh:505-507`:
```zsh
LOCK="$(mktemp -d "${TMPDIR:-/tmp}/fire-selftest.XXXXXX")/LOCK"
_st_dir="${LOCK:h}"
trap '[[ -n "${_st_dir:-}" ]] && rm -rf "$_st_dir"' EXIT
```
`mktemp` is unchecked. If it fails, `LOCK` becomes `/LOCK`, `_st_dir` becomes `/`, the
non-empty test passes, and the trap runs **`rm -rf /`**.

**Driven, in a throwaway container, not argued** [`out/21-mktemp-failure-drive.txt`]:
```
mktemp: failed to create directory via template '/nowrite/fire-selftest.XXXXXX': Permission denied
self-test: … scratch=/
_row:2: permission denied: /LOCK        (×27)
ROWS=27 FAIL_OPEN=0 FAIL_SHUT=6 SKIPPED=0
rm: it is dangerous to operate recursively on '/'
rm: use --no-preserve-root to override this failsafe
SELFTEST_RC=1
```
The `rm` **was issued**; GNU coreutils refused it. macOS `/bin/rm` refuses too — the string
`"/" may not be removed` is in the binary. So the realized outcome is: the self-test reports
6 fail-shut rows, rc 1, and the fire exits 2 — **SHUT**. Two things make that acceptable only
by luck: the refusal comes from an **external guarantee the code neither states nor tests**,
and the SHUT outcome depends on groups B/C/D existing (group A alone would have reported
**green while testing nothing**, because no body was ever written).

**This file already knows the pattern.** 170 lines later, `:676-679` does
`_t301_dir="$(… mktemp -d …)" || _t301_dir=""` and then tests it before use. The self-test
does not.

**Condition C2:**
```diff
-  LOCK="$(mktemp -d "${TMPDIR:-/tmp}/fire-selftest.XXXXXX")/LOCK"
-  _st_dir="${LOCK:h}"
+  # T361 F-2. UNCHECKED `mktemp` here made `LOCK=/LOCK` and `_st_dir=/`, and the trap below
+  # then issued `rm -rf /` — refused by BSD and GNU rm, but by THEIR guarantee, not ours.
+  # Same shape this file already handles correctly for `_t301_dir` at the snapshot re-exec.
+  _st_dir="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/fire-selftest.XXXXXX" 2>/dev/null)" || _st_dir=""
+  if [[ -z "$_st_dir" || ! -d "$_st_dir" || "$_st_dir" == "/" ]]; then
+    print -u2 "self-test: could not create a scratch directory under ${TMPDIR:-/tmp}; refusing to run against an unknown path"
+    exit 2
+  fi
+  LOCK="$_st_dir/LOCK"
```

### F-T361-3 — a configuration value, not a defect, makes the fatal self-test stop every fire. **MEDIUM. Fail direction: SHUT.**

`LOCK_CEILING_SECS="${LOCK_CEILING_SECS:-86400}"` (`:24`) is environment-overridable. The
self-test's group-C fixture is **hard-coded**: `_OLD="$(_epoch_iso8601 $(( _NOW_E - 360000 )))"`
(`:512`, "100 h ago: past the 24 h ceiling"). Raise the ceiling past 100 h and the fixture
stops being past it.

**Driven** [`out/25-selftest-config-coupling.txt`]:

| `LOCK_CEILING_SECS` | self-test | rc |
|---|---|---|
| unset / 86400 / 172800 / 359999 / 360000 / 360001 | `FAIL_SHUT=0` | 0 |
| **604800** (7 days) | **`FAIL_SHUT=2`** | **1** |

rc 1 at `:981` → `exit 2` → **the fire does not start**, and the log says the readers
regressed when in fact a threshold moved. This is the same defect class T353 fixed at `:512`
in prose ("past the 24 h ceiling" is a comment restating a configurable value) and the same
P-80 shape it removed elsewhere.

**Condition C3** — derive the fixture from the threshold:
```diff
-  _OLD="$(_epoch_iso8601 $(( _NOW_E - 360000 )))"          # 100 h ago: past the 24 h ceiling
+  # T361 F-3. DERIVED from the threshold, never typed: `LOCK_CEILING_SECS` is overridable
+  # from the environment, and a hard-coded "100 h" fixture turns a THRESHOLD CHANGE into a
+  # fail-shut that stops the whole fire (measured at LOCK_CEILING_SECS=604800).
+  _OLD="$(_epoch_iso8601 $(( _NOW_E - (LOCK_CEILING_SECS * 2 + 60) )))"
```
and change the group-C banner to print the derived age beside the threshold.

### F-T361-4 — the host guard is graded by neither control, and it is the literal P-85 line. **MEDIUM. Fail direction: OPEN (coverage, not a live defect).**

`lock_pid_state:382` — `[[ "$host" == "$(hostname -s)" ]] || { print other_host; }`, commented
*"never judge another machine"* — is the single line preventing the local fire from deciding
that the **cloud fire's** pid is dead and taking its lock. The census above shows the cloud
fire has written **three** such locks.

Mutation **n07 deletes that line and BOTH graders stay green**: the 192-state driver cannot
see it (it supplies `pid_state`), and the self-test has **no row with a foreign `host`** —
every one of its 27 bodies uses `$_H` [`out/07`, and confirmed by reading `:520-556`].

The line is correct today; my own foreign-host rows F01/F02 pass [`out/10`]. The finding is
that **nothing would notice if it stopped being correct**, in the one direction that
destroyed four worker branches on 2026-08-22.

**Condition C4** — two rows in the self-test, one per direction:
```zsh
_row e01 HELD "{\"host\": \"not-$_H\", \"pid\": $_DEAD, \"started_at\": \"$_NOW\"}" \
     "FOREIGN host, pid dead HERE: arm 2 must NOT fire -- P-85, never judge another machine"
_row e02 HELD "{\"host\": \"not-$_H\", \"pid\": $_LIVE, \"started_at\": \"$_NOW\"}" \
     "FOREIGN host, pid live here: still other_host"
```
(group B's `_DEAD` guard applies to e01 as it does to b01–b03.)

### F-T361-5 — the parser's arithmetic is graded only by a script wired into nothing. **MEDIUM. Fail direction: OPEN. This is P-80 on the deliverable.**

T353's own charge against T342 is that its census *"is wired into nothing and has no `exit`"*,
reached through P-45 and P-22. **`epoch-parity.zsh` is in exactly that position.** It lives in
`.softhouse/capture/t353-t342-conditions/bin/`; `grep -rn epoch-parity` over the whole repo
outside `capture/`, `reviews/` and `handoff/` returns **one hit, and it is a comment**
(`fire-program.sh:338`). `conformance.sh` names neither it nor `drive-wrapper-vs-skill.zsh`.

So the only wired grader of `_iso8601_epoch` is the self-test, and the self-test is **blind to
its arithmetic**: n06 (day bound), n08 (century leap rule), n09 (negative-epoch guard) and n11
(+1 day) all leave it green [`out/07`].

**These are not cosmetic.** n11 is the sharpest: with the epoch one day high, a lock **one
hour old** reads as **25 hours old**, arm 3 fires, and a live holder's lock is taken — the
P-85 outcome, produced by a one-character arithmetic error in a function that the wired
control cannot see. n08 makes `2100-02-29T00:00:00Z` a valid instant, which at
`lock_released_at` is OPEN.

**Condition C5** — the cheapest sufficient fix, and it needs no new file: give the self-test
four arithmetic rows it currently lacks (a near-boundary `started_at` that must **not** fire
arm 3; a `released_at` of `2026-02-30T00:00:00Z`; one of `2100-02-29T00:00:00Z`; a pre-epoch
`started_at`), and state in the source that `epoch-parity.zsh` is **evidence, not a control**.
Wiring `epoch-parity.zsh` into `conformance.sh` is the alternative and belongs to whoever
holds that file — it is the natural companion to T353's own F1.

### F-T361-6 — the SKILL.md patch overstates arm 1's polarity. **LOW-MEDIUM. Fail direction: documentation reads safer than the code is.**

§10 edit (2): *"…all read as *not released* — **any doubt about the lock's contents is HELD,
never free** (arm 6)."* Measured false: `released_at:"None"` with a 100 h `started_at` yields
**`TAKE-ceiling`** [`out/10`, R03]. Arms 2, 3 and 5 read other fields and can take the lock
while `released_at` is unreadable — which is the design, and which arm 3 exists for.

**Condition C6** — hand T343 this wording instead:
> …a duplicated key, or a body that will not parse **all read as *not released*, so arm 1
> will not fire.** That is **not** the same as HELD: arms 2, 3 and 5 read other fields and may
> still take the lock on their own signals — a body that is 100 h old still fires the ceiling
> whatever `released_at` says. What is guaranteed is narrower and is the guarantee that
> matters: **an unreadable `released_at` is never, by itself, permission to take the lock.**

### F-T361-7 — the SKILL.md patch writes five fresh cardinals into a living document. **LOW. Fail direction: none (rot).**

§10 edit (3) inserts `96 / 12 / 27 / 9 / 15` into `SKILL.md`. Condition 3 of this very task
was deleting two cardinals from `fire-program.sh` on P-80 grounds, and T353 quotes the remedy
in the source: *"the fix is never the new number — it is to make the second site READ the
first"* [`patterns.md:2775`]. **Condition C7:** replace the five numerals with
`zsh .softhouse/capture/t353-t342-conditions/bin/run-t346-mutate.zsh .softhouse/bin/fire-program.sh`
and the sentence "mutating any arm moves the counter; gutting a reader does not."

### F-T361-8 — a paraphrase is cited as P-45's text, and patterns.md has a named erratum for that exact string. **LOW. Fail direction: none.**

`fire-program.sh:976-977` (new in T353):
> `P-45, *"a guard that only works when someone remembers to run it enforces nothing"*
> [`.softhouse/patterns.md:1503`]`

`patterns.md:3374-3379` is a standing erratum whose first sentence is: *"**The paraphrase "a
guard that only works when someone remembers to run it enforces nothing" is NOT `P-45`'s
recorded text, and it is not any other pattern's text either.**"* P-45 at `:1503-1506` reads
*"when hardening a check, verify the path that actually executes in CI/conformance calls it,
not merely that a test does."* T353 quotes it **correctly** at `:116-118`, so this is one
lapse, not a habit — but it adds a site to a table written to stop the string spreading.
**Condition C8:** use the recorded text, which also supports the point better.

*(The other four citations are clean: `:2822` → P-85, `:2775` → P-80, `:473` → P-22,
`:1503` → P-45, each resolved and each carrying its sentence. P-86 satisfied.)*

### F-T361-9 — `zsh` is invoked bare where the file's own idiom is `/bin/zsh`. **LOW. Fail direction: SHUT.**

`:979` `zsh "$FIRE_SELF" --self-test-lock-readers` versus `:681` `exec /bin/zsh …`. A PATH
without zsh turns the new fatal control into a fire that cannot start (`rc=127` → `exit 2`),
which is the same failure T353 hit with `${0:A}` and fixed. Residual risk is small — the plist
runs `/bin/zsh -lc` and `/bin` is always on PATH — but the file has an idiom and this line
does not follow it. **Condition C9:** `/bin/zsh`.

### F-T361-10 — the 192-state driver does not read SKILL.md, so SKILL.md and `rules.py` can drift ungraded. **LOW. Fail direction: none today; OPEN if an arm is ever edited in one place only.** *(also a refutation of this reviewer's brief)*

`drive-wrapper-vs-skill.zsh:62` prints *"disagreements with SKILL.md STEP 0 **as modelled in
rules.py**"*. It never opens SKILL.md. T353's four edits change no boolean, so nothing drifts
now; but STEP 0 says *"If you change an arm here, that driver fails until you change it there
too"* (`SKILL.md:121`), which is **only true of `rules.py`, not of SKILL.md**. Worth a
sentence when T343 edits the file.

### F-T361-11 — the python3 preflight widens the blast radius, and that should be said. **LOW. Fail direction: SHUT. Accepted, recorded.**

Before T353 a python3-less fire ran: the two `branch_sweep.py` calls are `|| true` (`:906-907`)
and `ready-tasks.py`'s rc is logged and swallowed (`:2128-2138`, `return 0`). After T353 it
refuses at `:955`. That is a deliberate trade and I agree with it — a silent permanent wedge is
worse — but the source comment argues only the lock half. **Condition C11 (one sentence):** say
that the refusal is broader than the lock, and that it is chosen deliberately.

### F-T361-12 — comment/code mismatch in `bar-on-merge-result.sh`. **NIT.**

The header says *"clones LOCALLY (hardlinks, no network)"*; the code passes
`--local --no-hardlinks --shared`. Harmless, and the run is read-only against the source, but
the sentence describes a different command.

---

## What T353 claims, and what I measured

Every row re-run on this tree. **Nothing below is copied from a committed transcript.**

| # | instrument | T353 reports | T361 measured | agree? |
|---|---|---|---|---|
| 1 | T346's 35-row corpus (unedited) | `ROWS=35 FAIL_OPEN=0 FAIL_SHUT=0` | identical [`out/16`] | ✔ |
| 2 | T342's census, 17 bodies | 17/17 `=> held. safe.`, 0 FAIL-OPEN | 17 / 0 [`out/17`] | ✔ |
| 3 | 192-state driver | 192 states, 0 disagreements, PASS | identical [`out/09`] | ✔ |
| 4 | T346 mutate-driver | 96/12/27/9/15; M07/M08b/M09b driver-blind, self-test rc 1 | **byte-for-byte** [`out/13`] | ✔ |
| 5 | T342 positive control | PASS, every takeover arm fires | PASS, 7/7 [`out/18`] | ✔ |
| 6 | T346 no-python / broken / liar | no fail-open in any variant | confirmed, all fail-shut [`out/20`] | ✔ |
| 7 | T279 two-fires drive | 9 verdict lines byte-identical | **`diff` clean, byte-identical** [`out/19`] | ✔ |
| 8 | Linux arms probe | before 2 FAIL-SHUT + 2 FAIL-OPEN → after 0/0 | my own rows, my own image: before 3 SHUT + 2 OPEN → after 0 SHUT, 1 OPEN (= F-T361-1) [`out/11`,`out/10`] | ✔ |
| 9 | self-test inside Linux | `ROWS=27 FAIL_OPEN=0 FAIL_SHUT=0` | identical [`out/10`] | ✔ |
| 10 | epoch parity, 51 rows | 0 disagreements, macOS **and** Alpine | 51/0 on both | ✔ |
| 11 | red drives | `CHECKS=17 WRONG=0`, r06 GREEN | identical [`out/14`] | ✔ |
| 12 | `zsh -n` on the shipped file | PASS | PASS | ✔ |
| 13 | bar, merge result | EXIT 0, probe `up`, 46/0/0 | EXIT 0 on a **newer** main [`out/15`] | ✔ |
| 14 | bar, branch alone | EXIT 2, one row, `dc4e3ee3`'s | EXIT 2, **one** hard failure, that row [`out/22`] | ✔ |
| 15 | holder@host census | `local-launchd` only ever on the Mac | re-derived over `--all` [`out/12`] | ✔ |

**r06, and why it is a finding rather than a gap.** Restore `date -j` and the self-test on
this Mac still passes — because on this Mac `date -j` works. I confirm both halves: r06 GREEN
on the Mac [`out/14`], and the **same** code RED on Linux with `FAIL_SHUT` on both ceiling
rows [`out/11`]. A self-test cannot detect a portability defect on the platform that does not
have it; saying so plainly, and shipping the container run that can, is the correct handling.

**Scope: clean.** T353's own increment touches `fire-program.sh`, its capture dir and its
handoff — nothing else. `conformance.sh` and `SKILL.md` are untouched, as claimed. No
`nexus/`, no vector store.

**CLAUDE.md non-negotiables: clean.** Grepping the added lines of the whole stack for
`float|double|decimal|mysql|mariadb|ojdbc|oracle.jdbc|:1521|first_name|last_name|Stripe|Plaid|Lithic|Persona`
returns only prose, conformance transcripts, and one deliberate adversarial fixture
(`"pid": <n>.0`, "pid is a float", correctly rejected). `_iso8601_epoch` and `_epoch_iso8601`
are integer-only (`local -i`, `(( ))`); the only division is integer division; fractional
seconds are **refused**. No database of any kind. No hard-coded UTC offset — the parser
accepts **only** `Z`, which is strictly better than the `TZ=UTC date` it replaces, whose
correctness depended on an environment variable.

---

## The conditions, proven

A condition handed over as an untested diff is a guess, and this lineage is five repairs
deep. So C1–C4 were **applied to a throwaway copy** of the shipped file — never to the file —
and driven: `bin/t361-prove-conditions.zsh`, [`out/26-prove-conditions.txt`]. Every patch is
`cmp`-checked and reports **VOID** if it did not apply.

| check | result |
|---|---|
| `zsh -n` on the patched file | **PASS** |
| T361 reader corpus | `FAIL_OPEN` **7 → 0**; controls x16 (a genuine release must still FREE) and x17 (a 100 h lock must still TAKE) **both green** |
| `--self-test-lock-readers` with the five new rows | **`ROWS=32 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0`, rc 0** |
| **C1 reverted** — is the fix graded? | **rc 1, `FAIL_OPEN=3`** — yes |
| **C4 reverted** (host check deleted) — is it graded now? | **rc 1, `FAIL_OPEN=1`** — yes, where it was BLIND before |
| T342 positive control | **PASS**, all 7 takeover states still fire |
| 192-state driver | **0 disagreements** — no arm moved |
| **C3 at `LOCK_CEILING_SECS=604800`** | **`FAIL_SHUT=0`, rc 0** — the value that stopped the fire no longer does |
| C2 | `_st_dir` is checked before use; `_st_dir="${LOCK:h}"` occurrences: **0** |
| residual | one row, x11, and it is **C1 working** (see F-T361-1's stated cost), not C1 breaking |

**One finding came out of proving the conditions rather than out of the code**, and it is
worth recording because it is the same class as F-T361-3: my reader corpus originally typed
`LOCK_MAX_AGE_SECS` and `LOCK_CEILING_SECS` as literals, so the moment C1 added a third
threshold the harness reported a **false FAIL-SHUT** on the genuine-release control. The
corpus now **extracts the thresholds from the source** (`grep -E '^LOCK_[A-Z_]+='`). A harness
that hard-codes its subject's configuration is P-80's shape, and I sprang it on myself while
writing the finding about it.

---

## Verdict

**ACCEPT-WITH-CONDITIONS. `T342` + `T353` may merge as one change, now.**

The stack does what it says: it converts four fail-open lock readers into a real parser, then
converts a BSD-only `date` call — which silently removed the only arm guaranteeing the lock
can ever be taken over — into portable integer arithmetic that I could not break in 93
adversarial cases across two operating systems and ten locales, and it wires the first
control this program has ever had over the **readers**, on the path that actually executes,
with a real exit. Every instrument it reports reproduces, including the ones I most expected
to be flattered. It refuted its own brief, disclosed a defect its own wiring introduced,
committed the inconvenient bar transcript beside the convenient one, and stated its blind
spot (r06) rather than implying it away. The merge result is green on a `main` five commits
newer than the one it tested against.

**None of the twelve findings blocks the merge**, and I want to be explicit about why: on my
own independently written corpus the stack moves `FAIL_OPEN` from **11 → 7** with **no row
moving the wrong way**, and off-BSD it moves `FAIL_SHUT` from **3 → 0**. Holding it back to
close F-T361-1 would leave `main` strictly more fail-open than merging it does.

**Conditions, all follow-ups, none a merge blocker. C1, C2, C3 and C4 should be one task and
it should be next**, because three of them are in the new code and the fourth is the P-85 line
itself:

* **C1** (F-1, **OPEN**) — reject implausible instants in `released_at`; add a self-test row
  per closed case. Diff supplied.
* **C2** (F-2, SHUT) — check `mktemp`; never let `_st_dir` be `/`. Diff supplied.
* **C3** (F-3, SHUT) — derive the group-C fixture from `LOCK_CEILING_SECS`. Diff supplied.
* **C4** (F-4, OPEN-coverage) — two foreign-host rows in the self-test. Rows supplied.
* **C5** (F-5, OPEN-coverage) — four arithmetic rows in the self-test; say in the source that
  `epoch-parity.zsh` is evidence, not a control.
* **C6** (F-6) / **C7** (F-7) / **C10** (F-10) — for **T343**, before the SKILL.md patch is
  applied: fix the "never free" overstatement, delete the five cardinals, and note that the
  192-driver grades `rules.py` and not SKILL.md.
* **C8** (F-8), **C9** (F-9), **C11** (F-11), **C12** (F-12) — one-line corrections.

`fire-program.sh` is not mine, so **every condition above is a diff or a literal row, and I
have written none of them into the file.**
