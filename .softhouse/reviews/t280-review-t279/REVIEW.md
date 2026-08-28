# T280 — INDEPENDENT review of T279 (STEP 0 repo-lock protocol)

**Reviewer:** T280, isolated worktree, branch `softhouse/T280-review-t279`.
**Under review:** T279, merged `eac45bdc` (`.claude/skills/softhouse-program/SKILL.md` STEP 0 +
`.softhouse/bin/fire-program.sh` `lock_decide()` + `.softhouse/capture/t279-lock-partition/`).
**Base for every diff below:** `ca745981` (first parent of the merge) → `0b3ce8e6` (T279's tip).

## VERDICT: **REJECTED**

Two blocking findings, one material finding that changes T336's premise, three minor.
Every claim below is marked `[VERIFIED: …]` or `[UNVERIFIED]`. Every probe I wrote is in
`probe/`, every raw output in `out/`. I re-ran T279's own instruments rather than reading
their committed output.

| id | severity | one line |
|---|---|---|
| **F-A** | **BLOCKING — fail-OPEN** | `lock_released_at()` reads `"released_at": null` as `null}` when it is the last key → arm 1 → **`FREE-released` on a lock held by a live process**. |
| **F-B** | **BLOCKING — the headline claim is false of the shipped artefacts** | The partition holds of `rules.py:NEW_ARMS` only. The shipped **prose** has 36 multi-match / 33 opposite-verdict states; the shipped **wrapper** is first-match-wins and transposing arms 3 and 4 changes 3 verdicts, including the exact case arm 3 was built for. |
| **F-C** | **MATERIAL — input to T336** | The `post-checkout` hook **cannot refuse**. In `enforce` mode `git worktree add` exits 1 *and creates the branch, checks out the files and registers the worktree*. It is a warning with an exit code, not a precondition. |
| F-D | minor (pre-existing, not T279's) | SKILL.md: "`heartbeat` is written and refreshed as well" — the wrapper writes it once and never refreshes it. |
| F-E | minor (pre-existing, not T279's) | pid liveness is consumed only in the "dead → TAKE" direction. Arm 5 takes a lock whose `pid_state=alive_here` on this host. |
| F-F | minor (doc) | SKILL.md says the driver diffs the wrapper "against **this text**". It diffs against `rules.py`. T279's handoff says this correctly; the shipped skill drops the qualifier. |

---

## 1. THE STATE SPACE, AUDITED BEFORE THE COVERAGE (brief item 1)

### 1.1 The cardinality and the enumeration reproduce

`python3 enumerate.py`, run by me, is **byte-identical to T279's committed `out/enumeration.txt`**
[VERIFIED: `out/enumeration-rerun.txt`; `diff` against `.softhouse/capture/t279-lock-partition/out/enumeration.txt` empty].

* 192 = 2 × 2 × 4 × 3 × 4. Arithmetic correct [VERIFIED: `rules.py:39-43`].
* 97 distinguishable after collapsing `lock=absent` (the other four axes are unobservable with
  no file to read them from). The collapse is sound [VERIFIED: `rules.py:collapse`].
* OLD: 18 zero-match / 24 multi-match / 22 conflicting. NEW: 0 / 0 / 0, all pairwise disjoint.
  Both halves reproduce [VERIFIED: `out/enumeration-rerun.txt:11,31,57,103,105,107`].

**But the NEW result is true by construction, not by discovery.** `N6`'s predicate is literally
`not (N0 or N1 or N2 or N3 or N4 or N5)`, so "0 zero-match" is a tautology; and `N2…N5` carry
explicit exclusion prefixes (`_lock_held`, `not dead_pid_here`, `not started_over_24h`), so
"0 multi-match" is a property the transcription *installed* [VERIFIED: `rules.py:118-160`].
That is legitimate *if and only if* the shipped artefacts carry the same conjuncts. They do not
— see F-B.

### 1.2 Per-axis exhaustiveness — one axis is NOT exhaustive

I drove the **shipped reader** (`fire-program.sh --lock-signals`, against scratch repos) over
real-world lock bodies the axes do not name, to see where each lands
[VERIFIED: `probe/drive-lock-bodies.zsh` → `out/lock-bodies.txt`]:

| real state | axis value it lands on | verdict | polarity |
|---|---|---|---|
| body is not JSON at all (merge-conflict clobber) | released=null, started=unreadable, pid=absent | `HELD-live` / `HELD-default` | fail-closed ✔ |
| `"pid": null` (last key) | pid=absent | `HELD-live` | fail-closed ✔ |
| `"pid": 0` (T265 F-4) | pid=absent | `HELD-live` | fail-closed ✔ |
| `pid` key missing | pid=absent | — | fail-closed ✔ |
| `started_at` in the **future** (+48 h, age −172799) | fails the `<0->` glob | `HELD-live` (fresh tip) / `HELD-default` (stale tip) | fail-closed ✔ |
| tip age **negative** (clock skew / future commit) | fails the `<0->` glob | `HELD-default` | fail-closed ✔ |
| `origin/main` absent entirely (fresh `git init`, no remote branch) | tip=unreadable | falls to arm 2/6 | fail-closed ✔ |
| **`"released_at": null` as the LAST key** | **released=set** | **`FREE-released`** | **fail-OPEN ✘ — F-A** |

So seven of the eight fall inside the space and fail closed. The eighth does not, and the axis it
escapes through is the one axis that has no `unreadable` value: `RELEASED = ("null", "set")`, while
`STARTED` and `TIP` both carry `unreadable` [VERIFIED: `rules.py:39-43`]. The enumeration models
`released` as a clean boolean and **never tests the function that produces it**. That is the same
failure mode T279 correctly diagnosed in the arms — a property proved of a model rather than of the
shipped thing — recurring one layer down.

Minor correction to the wrapper's own comment: `fire-program.sh:73-74` says a negative age
"fails the `<0->` glob and lands in arm 6 → HELD". It lands in **arm 4** when the tip is fresh and
arm 6 only when it is not [VERIFIED: `out/lock-bodies.txt`, direct `--lock-decide` probes]. Both
are HELD so the safety claim survives; the stated mechanism is wrong.

---

## 2. F-A (BLOCKING) — a live holder's lock reads FREE

`lock_released_at()` extracts the value up to the first **comma**:

```zsh
v="${${body#*\"released_at\":}%%,*}"
v="${v//[$' \t\r\n\"']/}"          # strips space/tab/CR/LF/quote — NOT `}`
[[ "$v" == null || -z "$v" ]] && return 0
```
[VERIFIED: `.softhouse/bin/fire-program.sh:120-131`]

When `released_at` is the **last key** there is no trailing comma, so the match runs to the end of
the object and the value carries the closing brace. The strip class does not remove `}`. The value
becomes the 5-character string `null}`, which is non-empty, so `lock_decide` takes arm 1.

Driven end to end against a **genuinely running process that I own** (`pid_state=alive_here`,
uid 501) [VERIFIED: `probe/drive-releasedat-failopen.zsh` → `out/releasedat-failopen.txt`]:

```
--- 2. released_at null but NOT the last key
    lock_present=1 released_at=<null>  ... pid_state=alive_here   verdict=HELD-live
--- 3. released_at null AS THE LAST KEY            <-- THE DEFECT
    lock_present=1 released_at=null}   ... pid_state=alive_here   verdict=FREE-released
--- 4. python json.dumps(indent=2), released_at added last
    lock_present=1 released_at=null}   ... pid_state=alive_here   verdict=FREE-released
--- 5. compact json.dumps, released_at last
    lock_present=1 released_at=null}   ... pid_state=alive_here   verdict=FREE-released
```

A held, live lock declared free is **P-85** verbatim — *"two orchestrators held the lock at once"*
[VERIFIED: `.softhouse/patterns.md:2822`].

**Reachability, stated precisely.** I grepped `.softhouse/` and `.claude/` for every occurrence of
`released_at`: the only writes anywhere in this repo are **none** — the wrapper releases by
`rm -f "$LOCK"` and never emits the field [VERIFIED: `fire-program.sh:618-630, 741-751`; grep in
§7 below]. So arm 1 has **no in-repo producer**, and its only possible input is a **hand-written
LOCK** — which is exactly the case STEP 0 governs (*"a hand-run must honour it too"*,
`SKILL.md` STEP 0.0) and exactly the case `rules.py`'s own docstring names (*"STEP 0 is read by an
agent on a fresh clone with a hand-written LOCK"*). The most natural way for an agent to write that
file — `json.dumps` with `released_at` set last — triggers it. This is latent, not currently firing;
it is still a fail-open in a lock protocol, on the one code path arm 1 exists to serve.

**Fix (1 added line), measured.** Adding `}` to the strip character class **does not work** — zsh
rejects the pattern (`bad pattern: [$' \t\r\n\"{`). What works is cutting the value at the first `}`
as well as the first `,`:

```zsh
v="${${body#*\"released_at\":}%%,*}"
v="${v%%\}*}"                      # <-- add this line
v="${v//[$' \t\r\n\"']/}"
```

Verified on all three shapes [VERIFIED: `probe/fixcheck.zsh` → `out/proposed-fix-check.txt`]:
`released_at` null-as-last-key → `''` (HELD); a real timestamp as last key → the clean timestamp
(the shipped reader returns it with a trailing `}` today, right verdict, garbled log); null
mid-object → `''`. The corresponding `released` axis needs an `unreadable`/`malformed` value and a
test of the *reader*, not only of the arms.

---

## 3. F-B (BLOCKING) — the partition claim is false of both shipped artefacts

SKILL.md STEP 0 asserts, in bold:

> **THE TEST — SEVEN ARMS, AND THEY PARTITION.** Read every arm; the answer is the one that
> matches, and **exactly one always matches.** The arms are written to be **mutually exclusive**,
> not merely first-match-wins, so reading them out of order cannot change the answer.

[VERIFIED: `.claude/skills/softhouse-program/SKILL.md` STEP 0]

### 3.1 The shipped PROSE is not a partition

I transcribed arms 0–6 **literally from the shipped SKILL.md**, under `rules.py`'s own stated
transcription discipline — *"where a sentence names no term for a dimension, the arm is silent on
that dimension … the transcription must not 'helpfully' add the missing conjunct"* (`rules.py:11-14`)
— and honoured the two priority markers that **are** in the text (arm 2's *"whatever every other
signal says"*, arm 4's *"(short of arm 3)"*). Nothing else in the prose excludes anything
[VERIFIED: `probe/prose_arms.py` → `out/prose-enumeration.txt`]:

```
===== PROSE AS WRITTEN, honouring arm 2's textual priority marker =====
B. matched MORE THAN ONE arm (order-dependent): 36
C. of those, OPPOSITE verdicts: 33
VERDICT: NOT A PARTITION  (multi=36, conflicting=33)
```

The cleanest counterexample, and it needs no exotic input:

```
{lock=present, released_at=set, started_at<6h, tip<6h, pid=absent}
  arm 1 -> FREE   "`released_at` is non-null -> free. Take it."
  arm 4 -> HELD   "origin/main's newest commit is under 6 h old -> HELD ... (short of arm 3)."
```

There is **no textual tiebreak between arm 1 and arm 4**. Arm 4's only exclusion is *"short of arm
3"*; it says nothing about `released_at`. Reading arm 1 first → take the lock. Reading arm 4 first →
exit. `rules.py` answers this state uniquely (`[('N1','FREE')]`) **only because `N4` carries
`_lock_held(s)`, i.e. the conjunct `released_at is null`, which the prose sentence does not
contain** [VERIFIED: `out/prose-enumeration.txt`, final section; `rules.py:141-144`].

Direction of harm for arm 1 vs arm 4 is fail-closed (a careful reader exits); arm 1 vs arms 2/3/5
are FREE-vs-TAKE, both "may proceed". So the prose ambiguity alone opens no new safety hole. What it
does destroy is the claim, and the claim is the whole product of T279's F-1 work. It also
re-opens **T265 F-3** in a new form: on those 33 states the wrapper (first match → `FREE-released`)
and a careful prose reader (→ `HELD`) give **opposite** answers, which is precisely *"the two
documents that must agree provably did not"*. Combined with F-A, `released=set` is reachable from a
lock that is **not** released.

### 3.2 The shipped WRAPPER is first-match-wins, not disjoint — and order is load-bearing

`lock_decide()` is a chain of early returns with no exclusion conjuncts: arm 4 is
`tage < LOCK_MAX_AGE_SECS`, with **no** `sage < LOCK_CEILING_SECS` guard. It agrees with the
disjoint model only because its evaluation order happens to match
[VERIFIED: `.softhouse/bin/fire-program.sh:76-93`].

I built a copy with **arms 3 and 4 transposed and nothing else changed** and ran the exact case
T279 built arm 3 to fix [VERIFIED: `probe/drive-arm-order.zsh` → `out/arm-order.txt`]:

```
=== the case T279 cites: lock 105 h old, tip 2.99 h old ===
  SHIPPED order (3 before 4)      -> TAKE-ceiling
  TRANSPOSED order (4 before 3)   -> HELD-live
=== sweep over the 192 states ===
  states whose verdict CHANGES under the transposition: 3
    lock=present released=null started=ge24 tip=lt6 pid=alive_here    TAKE-ceiling -> HELD-live
    lock=present released=null started=ge24 tip=lt6 pid=absent        TAKE-ceiling -> HELD-live
    lock=present released=null started=ge24 tip=lt6 pid=other_host    TAKE-ceiling -> HELD-live
```

This answers the brief's item 5 directly. **The arms do not truly partition in the shipped
implementation, so ordering is not irrelevant** — and the sentence *"reading them out of order
cannot change the answer"* is an active invitation to a future editor to reorder them, which
restores exactly the F-2 bug T279 exists to remove (a 105 h lock read as HELD indefinitely).
The code is correct **today**; the property it is documented to have, it does not have.

### 3.3 Arm 3 vs arm 4, re-derived (brief item 5)

Arm 3 **does** bound the case, end to end through the shipped reader with a live holder:

```
--- 6. lock 105 h old, tip 2.99 h old, holder ALIVE
    lock_present=1 released_at=<null> started_age=378000 tip_age=10741 pid_state=alive_here
    verdict=TAKE-ceiling
```
[VERIFIED: `out/releasedat-failopen.txt`]

T279's argument is sound on the merits: arm 4 alone asks a question about the *repository*
(*"was anything published?"*), which third parties refresh, so it supplies no guaranteed takeover
time; `started_at` is invalid as freshness and valid as a lifetime bound. The 9.52 h-longest-fire →
24 h ceiling → 2.52× margin reasoning I did **not** independently re-measure against the fire
history [UNVERIFIED: I did not re-run `measure-f2.py` against the 25-fire corpus; I verified only
that arm 3 produces `TAKE-ceiling` on the cited signal values]. The *rejection of the author-match
alternative* I also did not re-measure [UNVERIFIED].

---

## 4. F-C (MATERIAL) — the hook cannot refuse. T336's premise must change.

Driven first-hand in a scratch repo, `/usr/bin/git` **2.50.1 (Apple Git-155)** on this host
[VERIFIED: `probe/drive-hook.sh` → `out/hook-drive.txt`]:

| case | gate | `git worktree add` rc | branch created | files checked out | registered in `worktree list` | hook fired |
|---|---|---|---|---|---|---|
| clean, all pushed | enforce | 0 | yes | yes | yes | no |
| unpushed dispatch record | default (`warn`) | **0** | yes | yes | yes | **yes** |
| unpushed dispatch record | **`enforce`** | **1** | **yes** | **yes (2 files)** | **yes** | yes |
| dirty `.softhouse/` only | enforce | 1 | yes | yes | yes | yes |
| spawned **from a linked worktree** | enforce | 1 | yes | yes | yes | yes |

**`post-checkout` is a post-action hook. The checkout has already happened when it runs.** In
`enforce` mode git propagates the non-zero status *and the worker worktree is fully usable*:
branch created, files present, entry in `git worktree list`. A caller that does not inspect the exit
status — or runs `git worktree add … || true`, or is a harness rather than a shell — proceeds with a
live worker. **It can only warn.** Say that plainly, and T336 must scope to "install a loud warning
plus a non-zero rc that some caller must actually check", not "install a precondition".

Two things follow.

1. T279 **did** measure this: `out/drive-post-checkout.txt:95` records `rc=1   worktree dir exists:
   yes` [VERIFIED]. The measurement is in the evidence; the **conclusion is stated nowhere a reader
   of the hook or of STEP 0 will see it**, and STEP 0 describes the hook as *"the hook that would
   enforce it at the instant it must hold"*, which is not what was measured.
2. The hook's own rationale for defaulting to `warn` — *"a hook that can abort every worker spawn
   on a false positive is a hook that parks the whole program"* (`post-checkout:31-32`) — rests on a
   capability the same file's evidence shows it does not have. Since `enforce` cannot park anything,
   defaulting to `warn` discards the only thing `enforce` adds (a non-zero rc) for no benefit.

Confirmed **not installed** in the live repo: `/Users/buv/gerege-nbfi/.git/hooks/` contains only
`reference-transaction` (plus stock `.sample` files) and `core.hooksPath` is unset [VERIFIED: `ls`,
`git config --get core.hooksPath` rc=1]. So T279's disclosure is accurate.

---

## 5. F-5 AND F-6 — RECORDED, NOT SILENTLY FIXED (brief item 4)

**Both confirmed recorded and both confirmed unfixed. No scope creep into arm 2.**

* **Recorded**: a new paragraph *"KNOWN AND DELIBERATELY UNFIXED, so they are not rediscovered as
  defects"* names (a) `kill -0`/EPERM and (b) `%ct` moving backwards, cites `[T265 F-5, F-6]`, and
  narrows the polarity claim to *"for a holder running as the same user"*
  [VERIFIED: `git diff ca745981 eac45bdc -- .claude/skills/softhouse-program/SKILL.md`, hunk at
  diff line 82-90; and `fire-program.sh:96-102`].
* **Not fixed (F-5), in code**: `kill -0 "$pid" 2>/dev/null && { print alive_here }` is semantically
  identical to the pre-T279 `kill -0 "$pid" 2>/dev/null && return 1`. No uid check, no `ps` fallback,
  no `procfs` probe was added [VERIFIED: `/tmp/t280-wrapper.diff` lines 100 vs 193].
* **Not fixed (F-5), demonstrated live**: pid **1** (`launchd`, root-owned, unquestionably alive) is
  read as `pid_state=dead_here` by the shipped reader running as uid 501, and the verdict is
  `TAKE-dead-pid` [VERIFIED: `out/lock-bodies.txt` case A].
* **Not fixed (F-6)**: `origin_main_tip_age()` is still `git log -1 --format=%ct origin/main` with no
  `--first-parent`, no `max()` over recent commits, no monotonic floor
  [VERIFIED: `fire-program.sh:148-156`].

`lock_holder_is_dead` is retained as a thin wrapper so the comments at `:884` and `:1057` stay
true — a correct, minimal refactor [VERIFIED: `fire-program.sh:102`].

---

## 6. THE MTIME-vs-PUSH-RECENCY DISAGREEMENT — CONSTRUCTED, NOT ASSUMED (brief item 3)

T279's `drive-wrapper-vs-skill.zsh` "demonstrates" this case with **three hard-coded integers**
(`OLD_MTIME_AGE=759`, `STARTED_AGE=28800`, `TIP_AGE=43200`). Nothing in it reads a file mtime or a
git tip; the "OLD wrapper rule" line prints the result of `(( 759 < 21600 ))` [VERIFIED: read the
script]. So the brief is right to say "construct that case".

I built it: a lock stamped 8 h ago by a **live** holder, a lock commit backdated 12 h so nothing has
been published since, pushed, then **cloned fresh and `git pull --ff-only`'d** exactly as STEP 0.2
does [VERIFIED: `probe/drive-mtime-disagreement.zsh` → `out/mtime-disagreement.txt`]:

```
  lock file mtime age     : 1s
  started_at age          : 28801s
  origin/main tip age     : 43201s
  ratio mtime:started_at  : 28801.0x
  verdict=TAKE-both-stale       (mtime_age=1   # printed only; decides nothing)
```

The disagreement is **worse than T265's 38×** — a fresh clone's checkout writes the file *now*, so
mtime reads 1 s against a true age of 8 h. And mtime genuinely decides nothing: holding every other
signal fixed and moving **only** the mtime across 1 s → 1 857 s → 259 257 s leaves the verdict at
`TAKE-both-stale` all three times [VERIFIED: same file]. The only two uses of the lock mtime in the
wrapper are the two log lines at `:183` and `:563`; the only other `stat -f %m` is on `RESUME.md`
at `:2182`, unrelated [VERIFIED: grep in `out/mtime-disagreement.txt`].

`drive-wrapper-vs-skill.zsh` itself reproduces: **192 states driven through the shipped file,
0 disagreements** [VERIFIED: `out/wrapper-vs-skill-rerun.txt`]. Note what that measures — the
script's own line says *"disagreements with SKILL.md STEP 0 **as modelled in rules.py**"*, and
T279's handoff repeats the qualifier correctly. **The shipped SKILL.md drops it** and says the driver
*"diffs them against **this text**"* (F-F). Given §3.1, the unqualified sentence is false.

---

## 7. MINOR FINDINGS

**F-D — "`heartbeat` is written and refreshed as well" is false.** The wrapper writes `heartbeat`
exactly once, in the single `cat > "$LOCK"` at `:618-630`, and there is no refresh anywhere: no
second write to `$LOCK`, no `touch`, no `sed`, no `refresh_lock` [VERIFIED: grep for
`> "$LOCK"`, `heartbeat`, `refresh_lock`, `touch .*LOCK` over the whole file — the only hits are the
initial write and comments]. So `heartbeat` is a second copy of `started_at` and "disambiguates a
fire that is thinking hard between pushes" is not something it can do. **Provenance: pre-existing,
not introduced by T279** — the sentence is present verbatim at `ca745981` (`SKILL.md:67-68`) and
T279 only appended *"`heartbeat` appears in no arm above; that is deliberate"* [VERIFIED:
`git show ca745981:.claude/skills/softhouse-program/SKILL.md | grep -n heartbeat`; skill diff hunk].
It nonetheless now sits inside the paragraph T279 rewrote and is asserted by it.

**F-E — pid liveness is used in one direction only, the unsafe one.** Arm 2 takes `dead_here` as
decisive evidence of death. There is no symmetric arm treating `alive_here` on this host as
evidence of life. Measured consequence: a lock whose holder is a **demonstrably running process
that I own** is taken over by arm 5 [VERIFIED: `out/releasedat-failopen.txt` case 7 —
`started_age=28800 tip_age=43200 pid_state=alive_here → TAKE-both-stale`, holder still running].
**Provenance: pre-existing.** Old arm 3 (*"both `started_at` and the tip over 6 h → stale"*) had the
same shape and also no pid term, so this is not a T279 regression
[VERIFIED: `rules.py:OLD_ARMS` O3; `/tmp/t280-wrapper.diff`]. But T279's own justification for
promoting arm 2 — *"a hard-killed local fire is the normal outcome on this host"* — argues that
same-host pid state is trustworthy, and it is consumed only where it frees the lock. The two local
fires are 6 h apart and `LOCK_MAX_AGE_SECS` is 6 h, so an 08:00 fire still running at 14:00 with no
push in the interval is displaced by arm 5 while `alive_here` sits in the log. Worth a follow-up
task; out of scope for a micro-fix.

**F-F — the wrapper-vs-skill claim is unqualified in the shipped skill.** See §6.

**Observation, not a finding (pre-existing, untouched by T279):** taking the lock is not atomic —
two fires that both read "no LOCK" both `cat > "$LOCK"` and push, and the loser's
`git push -q origin main 2>/dev/null || log "WARN: could not push lock"` **logs and continues**
[VERIFIED: `fire-program.sh:632-634`]. Unchanged by T279 and outside its brief; recorded so the next
lock task sees it.

---

## 8. WHAT I CHECKED AND FOUND NOTHING WRONG WITH

So silence is distinguishable from not having looked.

* `zsh -n .softhouse/bin/fire-program.sh` → rc=0 [VERIFIED].
* `enumerate.py` re-run independently: byte-identical to the committed output, both the OLD
  18/24/22 and the NEW 0/0/0 [VERIFIED: `out/enumeration-rerun.txt`].
* `drive-wrapper-vs-skill.zsh` re-run against the shipped file: 192/192, 0 disagreements
  [VERIFIED: `out/wrapper-vs-skill-rerun.txt`].
* T279's `collapse()` of the `lock=absent` states to one canonical state: sound.
* The `case` statement's `*)` default (`:578-582`) catches `HELD-default` **and** any unexpected
  verdict string → exit. Fail-closed [VERIFIED: `fire-program.sh:576-583`].
* `lock_pid_state` refactor: `other_host` before the numeric check, `pid == $$` before `kill -0`,
  junk/`0`/`null` → `absent`. The old *"junk ⇒ alive"* behaviour becomes *"junk ⇒ absent"*; both
  end in HELD on the decisive paths, no regression found [VERIFIED: `/tmp/t280-wrapper.diff`;
  `out/lock-bodies.txt` cases F, G].
* `--lock-decide` is handled before the T301 snapshot re-exec and before preflight, takes no lock,
  writes nothing, needs no repo [VERIFIED: `fire-program.sh:158-167`; ran it ~600 times in
  `probe/drive-arm-order.zsh` with no side effect].
* `LOCK_MAX_AGE_SECS` / `LOCK_CEILING_SECS` are defined (`:24-25`) before `lock_decide` (`:76`) and
  before the `--lock-decide` branch (`:162`), and honour env overrides [VERIFIED].
* `patterns.md` citations in the new STEP 0 text resolve: `P-85` at `patterns.md:2822`, `P-45` at
  `patterns.md:1503-1506`, both quoted accurately [VERIFIED: `sed -n` at both ranges].
* The hook's `$3 == 1` branch-checkout guard and `SOFTHOUSE_PUSH_GATE=off` escape hatch both behave
  as documented [VERIFIED: `out/hook-drive.txt` cases 1 and T279's own file-checkout arm].
* The hook fires correctly when the spawn originates **from a linked worktree**, reporting the main
  worktree's state — a case T279 did not test and which is how this pipeline actually spawns
  [VERIFIED: `out/hook-drive.txt` case 5].
* S8's self-refutation (*"if the holder commits and never pushes, the repaired arms take the lock
  too"*) is present and correct in the handoff and in STEP 0. T279 did not overclaim P-85 as fixed
  [VERIFIED: `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T279.md:263-271`].
* T279's self-report against the driver — dispatch record + `RESUME.md` (`59fc41b4`) pushed
  10:46:19, first `git worktree add` 10:44:04, 135 s late — is recorded in STEP 0 rather than
  softened. I did not independently re-derive those two timestamps [UNVERIFIED].

**Things I did NOT verify**, so they are not evidence for anything above: the 25-fire /
1967-commit corpus behind `measure-f2.py` (the 9.52 h longest fire, the 0-of-24 author-match
result, the 24-of-25 multi-identity result, the 105 h/2.99 h reading at
`fire-20260827-230001`); T279's `drive-two-fires.zsh`; T325 gate 1; and whether any *other* caller
in the pipeline inspects `git worktree add`'s exit status (which is what would decide how much F-C
actually buys once installed).

---

## 9. WHAT TO CHANGE

1. **F-A** — add `v="${v%%\}*}"` to `lock_released_at()` (measured; the naive character-class
   variant does not compile under zsh). Add `malformed` to the `RELEASED` axis in `rules.py` and a
   reader-level test, so the enumeration covers the function that produces the axis and not only the
   axis.
2. **F-B** — either (a) put the exclusions into the shipped prose (arms 2–5 each need
   *"and `released_at` is null"*; arm 5 needs *"and `started_at` is under 24 h"*) **and** into
   `lock_decide()` (arm 4 needs the `sage < LOCK_CEILING_SECS` guard), or (b) retract the claim and
   say plainly *"evaluate in order, take the first match; the order is load-bearing"* — which is what
   the shipped wrapper actually is. Do not leave a doc that says order cannot matter above an
   implementation where it changes 3 of 192 verdicts. Then re-run the enumeration against a
   transcription of the **prose**, not of a model.
3. **F-C** — state the measured conclusion in the hook header and in STEP 0: *`post-checkout`
   cannot abort `git worktree add`; in `enforce` it yields rc=1 with the worktree fully created.*
   Re-scope T336 accordingly, and drop the "false positive parks the program" rationale, which is
   unfounded.
4. **F-D** — either refresh `heartbeat` or delete the words "and refreshed".
5. **F-E** — file a follow-up: should `pid_state=alive_here` on this host outrank arm 5?
