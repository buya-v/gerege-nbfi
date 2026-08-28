# T368 — independent review of T365 (`fire-program.sh`, T361's conditions C1–C5, C8, C9, C11)

**Verdict: APPROVED. Merge it.**

Branch under review `softhouse/T365-t361-conditions` @ `5aedfc4a`. Reviewer branch
`softhouse/T368-review-t365`. Four findings, all LOW / LOW-MEDIUM, **none a merge blocker**,
none requiring a number to change. Two of them are misses T365 could have closed; two are
inherited from T353's wiring and are enlarged rather than created by T365.

`sha256(fire-program.sh)` **before** `c55a9c8b3a56e894030f4dc68a2bc4c8597d43a0ba18fce048d11c327086e22d`
(= `main`, byte-identical to what T361 reviewed) **after**
`06c57d0e192fa1484b9c25ad5ac7995049471a98ddf4425d0d663561b034bf53`
[VERIFIED: `git show main:… | shasum -a 256`, `git show softhouse/T365-t361-conditions:… | shasum -a 256`].
Both hashes are printed by every instrument below, so no transcript here can be about a
different file.

**Everything below was run on this host, in this worktree, by me.** No transcript of T365's
or T361's is accepted as evidence. Where I re-ran one of their scripts I say so and I re-ran
it; where I built my own instrument I say that too.

**Fail-direction convention.** **OPEN** = a lock held by a LIVE process reads as takeable —
the P-85 safety direction. **SHUT** = a reclaimable lock is not reclaimed, or the fire
refuses to start — a liveness cost.

---

## Why this review is graded harder than most, and what that changed

The self-test T365 grows runs **fatally, before the fire reads the lock**
[VERIFIED: `fire-program.sh:1139-1145` — `_ST_OUT="$(/bin/zsh "$FIRE_SELF"
--self-test-lock-readers 2>&1)"; _ST_RC=$?` … `if (( _ST_RC != 0 )); then log "FATAL: …";
exit 2; fi`, and the `PROBE_ONLY` exit and the lock section both follow it]. A defect here
stops every fire, including the fire that would fix it. So I drove the failure modes of the
*control* as hard as the failure modes of the *fix*, and I attacked the new knob
specifically, since a new environment variable on a fatal path is the shape that wedges a
program silently.

**The single most reassuring measurement in this review**: I could not find a hostile value
of `LOCK_RELEASE_SKEW_SECS` that fails OPEN *and* starts the fire. Every bad value I drove
fails SHUT and loud, and the self-test catches it before the lock is read (§4).

---

## 1. z07 is a real control, not a ban wearing a control's name

This was the brief's headline question and it is the one I spent most effort on.

`z07`'s body carries `released_at = _NOW_E + LOCK_RELEASE_SKEW_SECS / 2` and wants
`FREE-released` [VERIFIED: `fire-program.sh:696`]. It is **derived from the same knob the
predicate reads**, so it scales with the bound instead of restating it — the P-80 shape C3
was written to enforce, applied to the new fixture too.

A control is only a control if it can fail. **I made it fail, four different ways**, with my
own driver (`bin/t368-mutate.py`, `out/02-mutate.txt`). Every mutation is applied by exact
string replacement and reports **VOID** if the anchor is not found exactly once; `VOID/anchor
failures: 0` on this run, so no mutation passed vacuously.

| my mutation | rc | red rows | reading |
|---|---|---|---|
| `m00` control, unmutated | 0 | none, `ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0` | baseline |
| `m03` skew bound tightened to a **ban on any future instant** (`_e <= _now`) | 1 | **`z07` FAIL-SHUT, and nothing else** | z07 is precisely the row that separates *bound* from *ban* |
| `m04` C1 turned into a **total ban** (no `released_at` ever believed) | 1 | **`d01` and `z07` FAIL-SHUT** | a ban is caught twice, by two independent rows |
| `LOCK_RELEASE_SKEW_SECS=abc` (§4) | 1 | `d01`, `z07` FAIL-SHUT | z07 catches a misconfigured knob too |

`m03` is the decisive one: a one-token tightening of the predicate turns `z07` red **and
leaves all 44 other rows green**. A row that goes red alone, for the exact defect it names,
is a control. [VERIFIED: `out/02-mutate.txt` m03; independently corroborated by T365's own
kept transcript `out/06`, where `z07` went FAIL-SHUT twice under unrelated mutations.]

**z07 cannot be made to fail by moving the knob**, and that is correct rather than a hole:
at `LOCK_RELEASE_SKEW_SECS` of 0, 1, and 3600 it stays green [VERIFIED: `out/06-knob.txt`],
because both z06 and z07 are derived from the knob. The bound's *value* is configuration; the
bound's *existence* is what z06/z07 grade, and they do.

**ACCEPT.** z07 is a live control.

---

## 2. The knob itself: what legitimate instant does 3600 s refuse?

T365 flagged the value as `[UNVERIFIED — a judgement, inherited, not measured]` and declined
to survey the writers. **I did the survey. The answer is: nothing this program has ever
written.**

**Fact 1 — no writer in this program emits `released_at` at all.** The wrapper writes the
lock with a fixed heredoc containing `holder / host / pid / fire / started_at / heartbeat /
heartbeat_note / log / oracle / postgres` and **no `released_at` key**
[VERIFIED: `fire-program.sh:1246-1258`]. Release is `rm -f "$LOCK"` followed by a commit of
the deletion [VERIFIED: `fire-program.sh:1370-1379`]. The self-test's own `a01` row says so
in as many words: *"baseline, no released_at key (what this file writes)"*.

**Fact 2 — across the whole recorded fire history, `released_at` has been non-null exactly
three times, and never as an ISO-8601 instant.** I dumped every version of the lock in the
repository: **143 commits touch `.softhouse/LOCK`** [VERIFIED:
`git log --format=%H --all -- .softhouse/LOCK | wc -l`]. The complete census of non-null
values:

```
2 × "released_at": "2026-08-22T-local-fire-20260822-060013-exit"
1 × "released_at": "2026-08-22T-local-fire-20260822-140002-exit"
8 × "released_at": null
```
[VERIFIED: `git log --all -p -- .softhouse/LOCK | grep -o '"released_at": *"[^"]*"' | sort | uniq -c`.]

Both strings are longer than 20 characters, so `_iso8601_epoch`'s shape glob refuses them
outright — **T353 already refuses them, before C1 exists**. The surrounding commit
(`ab3a011b`, `2026-08-22 21:52:16 +0800`) shows an agent hand-writing that marker to mean
*released*, and the next lock's note recording *"Prior lock read released_at non-null => FREE
(rule 1)"* — i.e. arm 1 fired on it under the **pre-T353 string-surgery** reader.

**Conclusion, which is stronger than T365 claimed for itself:** after T353 there is **no
recorded `released_at` in this program's history that arm 1 would accept at all**, so the
3600 s bound refuses **zero** instants the record contains. Its entire cost is against a
hypothetical future writer — precisely the Go writer C1 exists to defend against. Choosing
3600 over 300 or 86400 is therefore unfalsifiable from the record, which makes it a cheap,
reversible, env-overridable judgement rather than a measured one. **That is an acceptable
basis for shipping it**, and T365's `[UNVERIFIED]` flag was the honest label; I am upgrading
it to *measured-as-costless-against-the-record*, not to *proven-optimal*.

**The residual SHUT exposure, bounded.** A foreign host whose clock runs more than an hour
ahead, writing a genuine `released_at`, now reads as not-released. Re-derived from
`lock_decide` [VERIFIED: `fire-program.sh:80-95`]: arm 2 cannot fire (`other_host`), so the
lock waits for arm 5 (both signals ≥ 6 h) or **arm 3, the 24 h ceiling, which fires on a
readable `started_at` alone and ignores the tip entirely**. So the delay is bounded at 24 h
and cannot become a strand — **provided `started_at` is readable**. See finding F-T368-4 for
the case where it is not.

**No behaviour change on the lock that exists right now.** I drove both vintages' extracted
readers over the live `.softhouse/LOCK` body: `released_at=<empty>` and `VERDICT=HELD-live`
on **both**, identical [VERIFIED: `bin/t368-live-lock.zsh`, `out/10-live-lock.txt`]. Merging
this cannot disturb the fire currently holding the lock.

---

## 3. The self-test: 45 rows, all executed, and `SKIPPED` tells the truth

`zsh .softhouse/bin/fire-program.sh --self-test-lock-readers` (zsh, never bash — the file is
`#!/bin/zsh` and uses zsh glob and subscript syntax):
**`ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0`, rc 0** [VERIFIED: `out/01-selftest.txt`].

`zsh /tmp/t365-fire-program.sh --probe` (`GEREGE_NBFI_REPO` pointed at this worktree so it
could not touch the real repo; every repo write in the file is at `:1260` or later, well past
the `PROBE_ONLY` exit at `:1146-1149`): **rc 0**, with the wired control logging
`lockselftest| ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0`
[VERIFIED: `out/04-probe.txt`].

**`SKIPPED=0` honestly means every row executed, and I proved it by forcing the skip path.**
The rows count 21 (A) + 3 (B) + 2 (C) + 1 (D) + 7 (Z) + 2 (E) + 4 (G) + 5 (H) = **45**, and
27 = A+B+C+D is exactly the pre-T365 total. `_row`/`_arow` each do `_n+=1` on an executed row
and the skip branches increment `_skipped` without incrementing `_n` — so the two counters
cannot both be lying. Driven: with the reaped-pid acquisition forced to fail (`_DEAD=0`),
the run reports **`ROWS=41 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=4`** with both WARNING lines
printed [VERIFIED: `bin/t368-control-integrity.py`, `out/11-control-integrity.txt` m11]. That also proves **T365's `_skipped+=3` correction is
necessary and correct**: under T353's `_skipped=3` this run would have reported 3 while 4 rows
were skipped, and `typeset -i _n=0 _open=0 _shut=0 _skipped=0` at `:590` makes `+=` arithmetic
rather than string concatenation [VERIFIED by reading `:590` and by the measured `SKIPPED=4`].

**The C1 fix and the host guard are graded, and I re-derived which row grades what**
(`out/02-mutate.txt`; my mutations, my expectations, not T365's):

| mutation | red rows | matches T365's claim? |
|---|---|---|
| `m01` `(( _e > 0 ))` removed | `z01 z02 z03` FAIL-OPEN | yes (its r01) |
| `m02` skew bound removed | `z04 z05 z06` FAIL-OPEN | yes (its r02) |
| `m05` the P-85 host guard deleted | `e01` FAIL-OPEN | yes (its r04) |
| `m08` day-of-month bound dropped | `g02` FAIL-OPEN (+ `h04`) | yes (its r06 subject) |

**Group H's five constants were derived independently of the code under test**, by me, with
`calendar.timegm` — not by calling `_iso8601_epoch` [VERIFIED: `1970-01-01T00:00:00Z`→`0`,
`1970-01-02T00:00:00Z`→`86400`, `2000-02-29T00:00:00Z`→`951782400`,
`2099-12-31T23:59:59Z`→`4102444799`, and python refuses `2100-02-29` with *"day is out of
range for month"*]. All five agree with what the shipped file prints. Grading a function
against its own output is the failure the group exists to avoid, and it does not commit it.

---

## 4. The new knob under hostile values — the "stops every fire" question, answered

A new env variable on a fatal path is the thing that wedges a program. I drove it
(`out/06-knob.txt`):

| `LOCK_RELEASE_SKEW_SECS` | rc | rows | reading |
|---|---|---|---|
| unset / `''` | 0 | 45/0/0 | `:-3600` default holds |
| `0`, `1` | 0 | 45/0/0 | z06/z07 derive, so a tight bound is still self-consistent |
| `abc` | **1** | `d01` `z07` FAIL-**SHUT** | fire refuses, loudly |
| `99999999999999999999` (int64 overflow) | **1** | `d01` `z07` FAIL-**SHUT** | wraps negative → everything refused; still SHUT |
| `-100000` | **1** | `z06` FAIL-OPEN + 2 SHUT | rc 1, so **the fire still does not start** |
| `0)) \|\| { print HACKED; }; ((1` | **1** | `d01` `z07` FAIL-SHUT | **`HACKED` never printed** — no arithmetic-to-command injection through the knob |

**Every hostile value fails SHUT and is caught by the self-test before the lock is read.** The
one that produces a FAIL-OPEN *row* (`-100000`) still exits 1, so the fire refuses rather than
misreading a lock. That is the correct polarity throughout. Recorded as F-T368-3 is the one
imperfection: the FATAL log then blames the *readers* rather than the *threshold*.

---

## 5. The 192-state driver — 0 disagreements, and I re-derived why that is expected

`zsh .softhouse/capture/t279-lock-partition/drive-wrapper-vs-skill.zsh /tmp/t365-fire-program.sh`
→ **192 states driven, `disagreements … : 0`, `RESULT: PASS`** [VERIFIED:
`out/03-192driver.txt`]. **No arm's verdict moved on any of the 192 states, so no `SKILL.md`
change is implied and T365 correctly made none.**

T365 says this is "expected and not luck". **Re-derived from the driver's source and
confirmed**: the driver calls `fire-program.sh --lock-decide <present> <relv> <sage> <tage>
<pid>` and **supplies** `relv="2026-08-28T00:00:00Z"` itself
[VERIFIED: `drive-wrapper-vs-skill.zsh:54-56`], and `--lock-decide` dispatches straight to
`lock_decide` [VERIFIED: `fire-program.sh:488-489`]. `lock_released_at` — the only function
C1 touches — is **never on that path**. So C1 is structurally invisible to this driver, and a
"0" here is a true statement about the arms and says nothing about the readers. T365's
framing of that is accurate and is the honest way to report it. This is also T361's F-T361-10
and T346's standing complaint, unchanged and still open.

---

## 6. FINDING 1 adjudicated — the century rule through a lock body

**T365's finding is correct, I reproduced it independently, and the compensating group H is
adequate. ACCEPT.**

My mutation `m06` breaks the century non-leap rule (`(( (y % 4 == 0 && y % 100 != 0) || y %
400 == 0 ))` → `(( y % 4 == 0 ))`). Result: **`h04` FAIL-OPEN, and not one body row moves**
[VERIFIED: `out/02-mutate.txt` m06 — `rc=1 ROWS=45 FAIL_OPEN=1`, red rows `h04`]. So T361's
proposed `released_at: 2100-02-29T00:00:00Z` body row would indeed have shipped blind, and
group H is the only grader that sees the defect.

I also checked T365's claim that **no substitute date exists**, and it holds: Feb 29 of a
non-leap century year is 1900 or earlier (negative epoch, refused by `_e > 0`) or 2100 or
later (refused by the skew bound), and routing through `started_at` yields a negative age,
which fails `[[ "$sage" == <0-> ]]` and lands on arm 6 HELD either way
[VERIFIED by reading `lock_decide:83-95` and by `g03`'s measured `HELD-live`].

**The trade.** C1 buys the closure of seven fail-OPEN rows and costs the reachability of one
correctness rule through the primary interface. That is a good trade on its face — OPEN is
the safety direction and SHUT is the liveness one — and T365 did not merely accept the cost,
it added a second interface (`_arow`, asserting the parser directly against constants derived
outside the code under test) and said in the source exactly why. Adding coverage beyond what
the review asked for, and *declaring* that you did, is the correct response to discovering
that a reviewer's proposed row would not have graded anything.

**One caveat I record rather than hold against it:** group H asserts `_iso8601_epoch` in
isolation, so it grades the *arithmetic* but not the *wiring* of that arithmetic into arm 1.
`m08` (day bound dropped) turns **both** `g02` and `h04` red, which shows the two groups
overlap and are not redundant in the same direction. Coverage is adequate.

---

## 7. FINDING 2 verified — the sign asymmetry, and the kept transcript

**Both halves check out.**

*The transcript is kept and it does show the failure.* `out/06-red-drives.txt` is committed
and ends `CHECKS=15 WRONG=2`, with `r05` printed as `*** WRONG` and the diagnostic line
`expected row pattern /^g01 \*\*\* FAIL-OPEN/ present: NO` [VERIFIED: `git show
softhouse/T365-t361-conditions:.softhouse/capture/t365-t361-conditions/out/06-red-drives.txt`].
It was not overwritten by `out/07`, which is the second, clean run. A control that caught its
own author, preserved rather than tidied away, is the evidence that the control works.

*The claim it caught was genuinely false, and the shipped code handles both signs.* I drove
both signs myself, on the shipped file:

| my mutation | result | reading |
|---|---|---|
| `m07lo` epoch one day **LOW** | rc 1, `FAIL_OPEN=27 FAIL_SHUT=1`, **`g01` red** | a low epoch makes ages read LARGER → arm 3 fires on a live holder. The OPEN direction, caught. |
| `m07hi` epoch one day **HIGH** | rc 1, `FAIL_OPEN=5 FAIL_SHUT=3`, **`g01` green**, `h01 h02 h03 h05` red | a high epoch makes ages read SMALLER → no `want=HELD` row can see it. Only group H catches it. |

[VERIFIED: `out/02-mutate.txt`.] My `m07hi` tally (`5 open / 3 shut`) is identical to T365's
own `r05` reading in `out/06`. **T365's original claim was wrong, its driver caught it, the
correction is right, and the shipped `g01` row-note now states the asymmetry accurately**
[VERIFIED: `fire-program.sh:570-576, 712`].

---

## 8. C2, and the `rm -rf /` item T365 left unverified — I closed it

**The refusal path works.** `TMPDIR=/nonexistent-t368/ /bin/zsh <T365's file>
--self-test-lock-readers` → `self-test: could not create a scratch directory under
/nonexistent-t368/; refusing to run against an unknown path`, **rc 2**, no trap installed
[VERIFIED, run on this host]. Structurally, the `[[ -z … || ! -d … || == "/" ]]` check is
before the `trap` line and the trap gained a `!= "/"` belt [VERIFIED: `fire-program.sh:549-557`].

**And the pre-C2 shape really does issue `rm -rf /`. I observed it directly, on this host,
non-destructively.** The same command against `main`'s file:

```
_row:2: read-only file system: /LOCK
…
ROWS=27 FAIL_OPEN=0 FAIL_SHUT=6 SKIPPED=0
rm: "/" may not be removed
```

The last line is BSD `rm` refusing the deletion **after the trap issued it**. T365 declined to
reproduce this and reconstructed the shape with the `rm -rf` neutered to a `print`, relying on
T361's container measurement. That caution was defensible, but the closure was available at
zero risk on this very host, and I took it. **T365's `[UNVERIFIED]` item (b) is now VERIFIED
by me**: the trap is issued, and the only thing between `main`'s code and the root filesystem
is `rm`'s own guarantee — exactly as T361 stated and exactly why C2 is correct.

`/usr/bin/mktemp` (absolute) came from **T361's supplied diff**, not from T365, and it matches
the file's own existing idiom at `:815` (`_t301_dir="$(/usr/bin/mktemp -d …)"`), so it is
consistent rather than novel [VERIFIED: `grep -n mktemp`]. I attempted a Linux run to check
whether `/usr/bin/mktemp` exists on busybox; the container image did not pull in time, so the
off-BSD question stays open exactly where T365 left it (§11).

---

## 9. Provenance — all four claims verified from source, none taken on T365's word

The driver misrouted a message into T365 and gave it a `git show` ref that fatalled, so
T365's provenance statements needed checking rather than accepting.

1. **The three spellings of T361's review yield the same blob.** [VERIFIED, run by me:
   `git show '380f0d64^2':…/REVIEW.md`, `git show b4bf2abf:…`, and
   `git show softhouse/T361-review-t353:…` each hash to
   `fb75133bda6a28ef4741a697c9b2dcd6c41a62348d05f60da5963e4e18eb03ac`; and
   `git rev-parse '380f0d64^2'` = `git rev-parse softhouse/T361-review-t353` =
   `b4bf2abf3cb293bfa908e3bd4a1db1c763878683`.] T365's recorded hash is correct to the byte.
2. **It did not act on the misrouted message.** The three-dot diff touches **24 files**:
   `fire-program.sh`, 22 files under its own `capture/t365-t361-conditions/`, and its handoff.
   **No `reference-oracle.md`, no `capture/t363-oracle-baseline/`, nothing outside grant**
   [VERIFIED: `git diff --name-only main...softhouse/T365-t361-conditions`].
3. **It reconstructed no C1–C12 claim from a paraphrase.** I read T361's REVIEW.md myself and
   compared each condition against what shipped. C1's two predicates and the
   `LOCK_RELEASE_SKEW_SECS:-3600` declaration are **T361's supplied diff applied verbatim**;
   C2 is T361's diff plus the disclosed `!= "/"` belt; C3 derives the fixture as C4 asks;
   C4's e01/e02 rows match T361's supplied rows including the `_DEAD` gate; C9 is `/bin/zsh`;
   C11 is the one-sentence blast-radius statement. **C8's quotation is exact**: the shipped
   text is *"A test-only guard is not a guard … when hardening a check, verify the path that
   actually executes in CI/conformance calls it, not merely that a test does"*, which is
   `patterns.md:1503-1506` verbatim, and the paraphrase is gone from that site
   [VERIFIED by reading `patterns.md:1500-1506` and `:3372-3382`]. The one place T365
   *departed* from T361 — substituting group G's month-13 row for T361's proposed
   `2100-02-29` body row, and adding group H — is declared prominently as its own finding
   rather than absorbed. **That is the correct handling and the opposite of the honesty
   violation this program grades hardest.**
4. **T361's corpus was run byte-for-byte unedited, and 7 → 0 reproduces.** T365's committed
   `bin/t361-reader-corpus.zsh` is **byte-identical** to `b4bf2abf`'s original (both
   `sha256 107c774b56da78300b3df3a5cc6535ef637e6fdf2dea2c19df47e9930a19a354`)
   [VERIFIED: `diff` clean]. I ran it myself against both vintages:

   ```
   main  (c55a9c8b…)  ROWS=24 FAIL_OPEN=7 FAIL_SHUT=0
   T365  (06c57d0e…)  ROWS=24 FAIL_OPEN=0 FAIL_SHUT=1
   ```
   and diffed the transcripts row by row: **z01–z06 and y01 all move `FREE-released` →
   `HELD-live`, and not one other row moves**, except `x11`
   [VERIFIED: `out/07-corpus-BEFORE-main.txt`, `out/08-corpus-AFTER-t365.txt`, and the diff].

   **`x11` is C1 working, and T365's diagnosis of it is right.** Its body carries the fixed
   wall-clock literal `2026-08-28T14:00:05Z`; my run was at 09:31Z, so the instant was ~4.5 h
   in the future and C1 correctly refused it. The row's verdict is a function of the hour it
   runs — a harness defect in T361's row, not a reader defect. T365's derived variant
   (`t365-reader-corpus.zsh`) scores **`ROWS=24 FAIL_OPEN=0 FAIL_SHUT=0`, rc 0**
   [VERIFIED: `out/09-t365corpus-AFTER.txt`], and I diffed the two corpora: **the change is
   exactly one row plus a header**, the row keeps `want=FREE-released` and its actual subject
   (`2` decoding to the digit `2`, so the shape check runs on the decoded string), and it
   gains an abort if `$NOW` does not start with `2`. **No other row was weakened.**

**Also closed: the Go claim, item (a).** T365 relied on T361's measurement. Go **is** on this
host, so I ran it:

```
$ go version                                          → go version go1.23.4 darwin/arm64
$ json.Marshal(struct{Holder string; ReleasedAt time.Time}{Holder:"go-fire"})
  {"holder":"go-fire","released_at":"0001-01-01T00:00:00Z"}
```
[VERIFIED, run by me.] Python confirms the other two sentinels:
`datetime.min` → `0001-01-01T00:00:00Z`, `datetime.max` → `9999-12-31T23:59:59Z`.
So `z01`'s and `z04`'s stated provenance are both facts.

**And T365's independence claim checks out**: the fix does not depend on the Go fact. `z01` is
refused by `(( _e > 0 ))` on plausibility grounds alone, whatever emits the string — proven by
`m01`, where removing that one predicate and nothing else turns `z01`/`z02`/`z03` fail-open.
The Go fact is the *motivation*, not the *mechanism*, exactly as stated.

---

## 10. The bar, and the non-negotiables

* `bash .softhouse/conformance.sh` → **exit 0**, `parity vectors PASS 46 FAIL 0`,
  `inadmissible 0`, `harness errors 0`, `invariant violations 0`,
  `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells
  compared`, all 13 deliberately-wrong ledger implementations KILLED
  [VERIFIED: `out/05-conformance.txt`]. Run with `bash`, never `sh`. **Not weakened.**
* **Money discipline.** No money is computed on this path, but the rule holds everywhere.
  Grepping the added lines of `fire-program.sh` for
  `float|double|decimal|mysql|mariadb|ojdbc|oracle.jdbc|:1521|first_name|last_name|Stripe|Plaid|Lithic|Persona`
  returns **nothing**, and for any `N.N` literal returns **nothing** [VERIFIED, my grep over
  `git diff main...softhouse/T365-t361-conditions -- .softhouse/bin/fire-program.sh`].
  Every added variable is `local -i` / `typeset -i` and every comparison is inside `(( ))`
  [VERIFIED by reading `:445-453`, `:590`]. `LOCK_RELEASE_SKEW_SECS / 2` in z07 is integer
  division. The parser accepts only a `Z` suffix, so no UTC offset is hard-coded.
* **Scope.** 24 files, all inside grant (§9.2). No `nexus/`, no vector store, no
  `conformance.sh`, no `SKILL.md`, no contract change. The frozen adapter contract is
  untouched.
* **C6 / C7 / C10** belong to T343 and were not reviewed here, per the brief.

---

## 11. Findings

### F-T368-1 — the P-45 paraphrase C8 removed survives at **three more sites in the same file**, and three of them cite P-45 by name. **LOW. Fail direction: none (rot, plus a false attribution in an operator-facing log line).**

T365's C8 comment states, correctly, that `patterns.md:3374-3379` *"is a standing erratum
written to stop that exact string spreading, and citing it here added a site to the table."*
It then fixes **one** site and leaves three, all in the file it holds the write grant for:

| line (T365's file) | text | attributed to P-45? |
|---|---|---|
| `:961` | `log "ERROR: … (P-45: 'a guard that only works when someone remembers to run it enforces nothing' — one that is not on disk enforces less.)"` | **yes, explicitly** |
| `:1042` | `P-45 — "a guard that only works when someone remembers to run it enforces nothing" — is exactly how fire 20260827-230001 …` | **yes, explicitly** |
| `:2238` | `two remembered obligations, which is P-45's exact shape: "a guard that only works when someone remembers to run it enforces nothing."` | **yes, explicitly** |

[VERIFIED: `grep -n "remembers to run it" <T365's file>` returns 4 hits, of which `:1130` is
T365's own C8 comment *quoting* the paraphrase in order to retire it.]

All three predate T353 — they are on `main` at `:822`, `:903`, `:2077`
[VERIFIED: `grep -n … /tmp/main-fire.sh`, 4 hits]. So **this is not a T365 regression, it is a
miss**. It also means **T361's own F-T361-8 is factually wrong about this file** when it says
*"this is one lapse, not a habit"* and *"the other four citations are clean"*: T361 examined
only the site T353 added. The one at `:961` is the worst of the three, because it is a runtime
`log "ERROR: …"` string that an operator reads during an incident, asserting a rule that
`patterns.md` explicitly records as not being P-45's.

**Not a blocker.** It changes no behaviour and no number. Recorded as a condition on whoever
next holds `fire-program.sh` (I may not write it): replace the paraphrase at `:961`, `:1042`
and `:2238` with P-45's recorded text, or drop the `P-45` attribution.

### F-T368-2 — the wired FATAL control has no presence or floor test on its own tally, and a gutted self-test passes. **LOW-MEDIUM. Fail direction: OPEN-coverage. Inherited from T353, enlarged by T365.**

The fire's wiring inspects **only** `_ST_RC` [VERIFIED: `fire-program.sh:1139-1145`; and
`grep -n 'ROWS=' <file>` finds the tally printed at `:727` and referenced in a comment at
`:114`, and **nowhere in the wiring**]. Driven, by me:

* delete the `print -r -- "ROWS=…"` line → **rc 0**, no tally in the output, fire proceeds
  [VERIFIED: `out/02-mutate.txt` m09].
* delete **all 45** `_row`/`_arow` invocations → **`ROWS=0 FAIL_OPEN=0 FAIL_SHUT=0
  SKIPPED=0`, rc 0**, fire proceeds [VERIFIED: `bin/t368-control-integrity.py`, `out/11-control-integrity.txt` m10].

An empty control passes. That is P-22 — *"a guard, a canary, or a control that cannot fail is
worse than none — because it is believed"* [`patterns.md:473`] — applied to the wiring itself,
and it is the same charge T365 levels at `epoch-parity.zsh` four hundred lines earlier in the
same file.

**T365 does assert a floor, but in the wrong place.** `t365-red-drives.zsh:56-62` requires the
summary line to exist and to report `>= 27` rows, and `r14` drives its absence
[VERIFIED: `git show softhouse/T365-t361-conditions:…/bin/t365-red-drives.zsh`]. That script is
in a capture directory and **is invoked by nothing** — precisely the position T365 correctly
condemns `epoch-parity.zsh` for occupying. P-83's presence-before-value is tested on the
driver, not on the path that executes.

**Not a blocker**, because the defect is latent (rows are deleted by an editor, not by a
runtime condition) and pre-existing. **Condition on whoever holds the wiring:** add
`print -r -- "$_ST_OUT" | grep -qE '^ROWS=[0-9]+'` and a floor derived from the row count, at
`:1140`, so the fatal control cannot pass while grading nothing.

### F-T368-3 — a nonsense value in the new knob reads as a *reader regression*, not as a misconfiguration. **LOW. Fail direction: SHUT. Same class as C3, one knob later.**

`LOCK_RELEASE_SKEW_SECS=abc` (or any int64-overflowing value) turns `d01` and `z07` FAIL-SHUT,
rc 1, and the fire logs *"the lock-reader self-test FAILED … A FAIL-SHUT row means a
reclaimable lock cannot be reclaimed"* — blaming the readers when a threshold is malformed
[VERIFIED: `out/06-knob.txt`]. This is exactly F-T361-3's complaint, which C3 fixed for
`LOCK_CEILING_SECS` by deriving the fixture. **T365 did derive z06 and z07 from the new knob**,
which closes the *in-range* half correctly; the residual is only non-integer and overflowing
values, and `LOCK_CEILING_SECS=abc` behaves the same way today. So this is a pre-existing class
that gains one member, not a new defect.

**The important half is positive and I record it as such:** every hostile value fails SHUT, the
fire refuses rather than misreading a lock, and an arithmetic-injection attempt through the
knob executed nothing.

### F-T368-4 — *"a delay, never a stranding"* is true only when `started_at` is readable. **LOW. Fail direction: SHUT. A comment-precision item.**

`fire-program.sh:439-442` states the cost of C1 as *"the lock still has arms 2, 3 and 5, so it
is a delay, never a stranding."* Re-derived from `lock_decide` [VERIFIED: `:80-95`]: arm 2
requires `dead_here`; **arms 3 and 5 both require `[[ "$sage" == <0-> ]]`**. So a body whose
`released_at` is a valid-but-far-future instant **and** whose `started_at` is absent or
unreadable now lands on arm 6 `HELD-default`, with no guaranteed takeover time — reclaimable
only by `--force`. Before C1 that body read `FREE-released`.

The stranding *class* pre-exists — any body with both signals unreadable already had it, which
is the deliberate fail-closed polarity the file states at `:76-79` — so **C1 adds an input to
an existing hole rather than creating one**, and the OPEN direction it closes is strictly
worse than the SHUT direction it widens. The sentence in the source simply promises more than
the arms deliver. Non-blocking; I may not write the file.

### C12 — the grant boundary is genuine, and the recorded fix is right but names one site of two. **NIT.**

`bar-on-merge-result.sh` lives at
`.softhouse/capture/t353-t342-conditions/bin/bar-on-merge-result.sh` — **T353's capture
directory, already merged to `main`** [VERIFIED: `git ls-tree main -- …`]. T365's write grant
was `fire-program.sh` plus `capture/t365-t361-conditions/`. **That is a real boundary, not an
evasion**, and recording the fix in the handoff rather than reaching into a merged task's
evidence directory is the correct call.

The recorded fix is correct as far as it goes — the header at `:14` says *"clones LOCALLY
(hardlinks, no network)"* while `:24` passes `git clone --quiet --local --no-hardlinks
--shared` [VERIFIED by reading the file on `main`]. It is **two lines, not one**: `:23` prints
`"=== cloning $ROOT -> $S/clone (local, hardlinked, no network)"` at runtime, repeating the
same false claim to the operator. ("no network" is accurate in both; only "hardlinks" is
wrong.) T361's F-T361-12 named only the header, so T365 recorded T361's item faithfully.

---

## 12. What I checked and found nothing wrong with

So that silence is distinguishable from not looking:

* `zsh -n` parses; `--self-test-lock-readers` and `--probe` both rc 0 at 45/0/0/0.
* The three-dot diff of `fire-program.sh` line by line: every hunk is one of C1, C2, C3, C4,
  C5 (groups G and H, `_arow`), C8, C9, C11, the `_skipped+=` correction, and the two
  comment/banner edits C3 requires (`a20`'s note and group C's banner). **No unexplained hunk
  and no drive-by edit.** The only literals added are the new knob's default
  (`LOCK_RELEASE_SKEW_SECS:-3600`, T361's value), and derivation terms that read a threshold
  rather than restate one (`LOCK_CEILING_SECS * 2 + 60`, `LOCK_CEILING_SECS - 3600`,
  `LOCK_RELEASE_SKEW_SECS * 2 + 60`, `LOCK_RELEASE_SKEW_SECS / 2`). C3 **removed** two
  restated cardinals ("360000", "100 h") and added none.
* Arm ordering and polarity in `lock_decide` are untouched by this branch.
* `local -i _e _now` is declared inside `lock_released_at` and the command-substitution exit
  status is still the one `|| return 0` tests (it is a plain assignment, not `local -i _e=$(…)`,
  which would have swallowed it). Negative epochs assign and compare correctly — `z01`–`z03`
  prove it end to end.
* `LOCK_RELEASE_SKEW_SECS` is declared at `:28`, above every function that reads it, which
  `set -u` requires; the self-test re-exec is a fresh process that re-establishes the default.
* Group G's `g01` fixture (`LOCK_CEILING_SECS - 3600`) and group C's (`LOCK_CEILING_SECS * 2 +
  60`) are both derived, so raising the ceiling cannot turn either red — C3's actual subject.
* No `git push` from the branch; no `SKILL.md`, `conformance.sh`, `program.json`, `tasks.json`,
  vector-store or `nexus/` path touched.
* T365's handoff claims 1–12 in its "Vectors run" table: I re-ran 1, 2, 3, 4, 5, 6, 11 and 12's
  subject independently and all agree. I did not re-run 7 (T346 census), 8/9 (T342 census and
  positive control) or 10 (two-fires drive); those are T353-era instruments already
  re-measured by T361 on this same file's parent, and nothing in C1–C11 touches what they read.

## 13. Still open, and correctly disclosed by T365

* **Off-BSD behaviour.** T365's `[UNVERIFIED]` flag was right at the time. Docker **is**
  available on this host (`29.6.2`), so it is closable; I started an Alpine probe and the image
  did not pull within the review, so I am not reporting a result I do not have. The specific
  thing to check is whether `/usr/bin/mktemp` (C2, and the pre-existing `:815` snapshot site)
  exists on busybox — if it does not, the self-test refuses with `exit 2` on every Linux host.
  **Latent, not live**: T361's census established that this file has only ever run on
  `Buyanmunkhs-Mac-mini`, and the cloud fire does not execute it. This is T365's follow-up 4
  and I second it.
* **`epoch-parity.zsh` still wired into nothing.** T365 made the source say so, which is honest
  but does not make it a control. Belongs to whoever holds `conformance.sh`.
* **The 192-state driver still does not read `SKILL.md`** (F-T361-10). Unchanged.

---

## Verdict

**APPROVED — merge `softhouse/T365-t361-conditions` as it stands.**

The change closes a real P-85 fail-open hole (7 rows on an independent, byte-identical corpus,
reproduced by me), it is graded by rows that I made fail individually for the exact defects
they name, the control that keeps C1 a bound rather than a ban is real, the fatal path refuses
loudly under every hostile input I could construct, and it does not move the verdict on the
lock that exists right now. The one place it departed from its review — substituting group G's
row and adding group H — it declared as a finding instead of absorbing, and the finding is
correct. The one claim it got wrong, it caught with its own driver and kept the transcript.

Four findings, all LOW / LOW-MEDIUM, none of which changes a number or a behaviour: three of
them (F-T368-1, F-T368-2, F-T368-4) are conditions on whoever next holds `fire-program.sh`,
which I do not; F-T368-3 is the same class as an accepted pre-existing one. Two items T365
flagged `[UNVERIFIED]` I closed myself (the Go zero `time.Time`, and the pre-C2 `rm -rf /`) —
flagging them was honest, but both were cheap to close on this host and should have been.
