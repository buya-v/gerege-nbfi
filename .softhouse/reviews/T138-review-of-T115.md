# T138 — independent review of T115 (`softhouse/T115-t91-microfixes`, `bd59187`)

**VERDICT: MICRO-FIX.**
**THE T91 STREAM IS MERGEABLE** — T91 + T107 + T115 merge clean into current `main` (`bcf2c55`),
every artefact is green on the merged tree, and none of the seven findings below changes a single
measured result. Every one is a one-liner the driver can apply at merge, and the replacement text
is supplied.

Reviewer: T138, branch `softhouse/T138-review-t115`. Oracle (Fineract) **UP** throughout —
`{"status":"UP"}`, `fineract-fineract-1` Up 2 days (healthy), `fineract-db-1` Up 3 days (healthy).
Read-only use only: `docker ps`, and `POST /loans?command=calculateLoanSchedule` via the precondition
rig. **No restart, no rebuild, no re-seed, no tenant write.** Every destructive step ran inside a
`git archive` export or a throwaway clone under `/tmp`.

**Nothing was inherited.** I did not invoke `t115-drive-mf1.sh`, `t115-drive-mf2.sh` or
`t115-drive-mf3-mf4.sh` for any Part 1 or Part 2 claim, and I read no committed T115 transcript as
evidence. I wrote my own drivers; they are committed under `.softhouse/reviews/T138-evidence/` with
their raw output under `out/`. (T115's scripts *were* run once, on the merged tree only, as the P-24
post-merge artefact re-run — that is a different question and it is labelled as such in §5.)

---

## 0. Scoreboard

| | claim | ruling |
|---|---|---|
| MF-1 | red/green + the shape test T107b left open | **REPRODUCED** |
| MF-2 | red/green + five callers | **REPRODUCED** |
| **N9 / N10** | **MF-2 does NOT close them; F-2 is NOT discharged** | **REPRODUCED — both still exit 0** |
| MF-3 | 5 FAIL → 5 FAIL, delta 0, breach *replaced* | **REPRODUCED** |
| MF-4 | 20 distinct files, 23 executable call sites | **REPRODUCED (third measurement)** |
| V-A | scorer contradicts its own visible table | **REPRODUCED — the sharpest thing in the branch** |
| V-C | a non-matching `sed` is a copy | **REPRODUCED** |
| V-E | one-sided comparison domain | **REPRODUCED** |
| V-F | scratch in the audited directory | **REPRODUCED, but the stated CONDITION is wrong** → F-T138-4 |
| V-G | two skip-branches returning success | **REPRODUCED** |
| F-6 | `prove-guards.sh` now asserts, red two ways | **REPRODUCED — 4 legs named, exactly as claimed** |
| V-B | reported, not fixed | **RULED — see §4. Fragility overstated 3×; fix it, but do not block on it.** |
| Part 3 | attacks / conformance / go / P-24 merge | **ALL REPRODUCED on current `main`** |

**New findings: 8.** One P2 that matters (F-T138-1), one P2 documentation defect (F-T138-2), five
P3, one P4.

---

## 1. Part 1 — the four assigned micro-fixes, re-driven

### MF-1 — `verdict.sh` (`.softhouse/capture/t91/verdict.sh:121-134`) — **REPRODUCED**

Driver: `.softhouse/reviews/T138-evidence/r1-mf1.sh`, `r1b-mf1-red.sh`. Output:
`out/R1-MF1.txt`, `out/R1b-MF1-RED.txt`. Baselines are literal shas
(`PRE=ccf3c14171dea52bd044d81d5ca67aba8054b74c`, `POST=bd59187cf83c7c7161db23668e91d45bd46be2a8`);
the driver aborts if the PRE tree already contains MF-1.

```
=== base=postfix-livetwin-sh scorer=PRE
EXIT=0
last line: ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION.
ERROR rows in table: 0

=== base=postfix-livetwin-sh scorer=POST
EXIT=1
ERROR rows in table: 10
```

Ten of thirteen transcripts replaced by `truncated, nothing was ever run`; pre-fix **exit 0** with
`ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION` and zero ERROR rows; post-fix **exit 1** with **ten**
`ERROR (no EXIT= line — the transcript has no attack body)` rows. Same result over
`postfix-livetwin-bash` and `postfix-copy-sh`.

GREEN, real pre-fix transcripts, post-MF-1 scorer: **exit 1** with exactly **six** admissions —
`A2a`, `A2c`, `A4c`, `A5`, `A7`, `A8` — identical across all four pre-fix transcript directories.
GREEN, real post-fix transcripts: **exit 0**, `ALL 13`, across all six post-fix directories including
T115's own `t115-post-{sh,bash}`. The fix does not blunt the scorer.

**T107b's residual — closed, and driven both ways** (`out/R1-MF1.txt`, LEG 6). A transcript whose last
line is the bare numeral `5`:

```
--- value test only (T107's specified rule), emulated:
   value test: shape=OK, st=5 -> BREACH row scores OK (vacuous pass)
--- shipped rule (shape + value):
A2a-mutated-canary-gerege.txt   -  -  -  ERROR (no EXIT= line — the transcript has no attack body)
EXIT=1
--- and the PRE-fix scorer on the same input:
A2a-mutated-canary-gerege.txt   5  no no  OK
PRE_EXIT=0
```

**The shape test creates no false ERROR anywhere** (LEG 5). I ran the post-fix scorer over **all 20**
committed transcript directories on both branches (8 on T91's tip, 12 on T115's) — `false-ERROR
rows: 0` in every one, and independently every `A*.txt` last line conforms to `^EXIT=[0-9]+$`
(`0 non-conforming` per directory). The five `happy/` transcripts are a different shape and are not
scored by `verdict.sh`; that is correct and unchanged.

**Scoping correction to T115's own table.** T115 writes the RED leg as "10 of 13 **committed**
transcripts" without naming the base set. It matters: over `postfix-livetwin-sh` the pre-fix scorer
gives exit 0 / `ALL 13` (T115's claim, reproduced); over `prefix-livetwin-sh` the same input gives
**exit 1** with three ADMITS, because `A4c`/`A7`/`A8` already admit there. `t115-drive-mf1.sh:41,44`
is explicit about the base; the handoff table is not. Cosmetic — logged as F-T138-8.

### MF-2 — both shims — **REPRODUCED**, and **the negative claim holds**

Driver: `r6-mf2.sh`, `r6b-mf2-green.sh`. Output: `out/R6-MF2.txt`, `out/R6b-MF2-GREEN.txt`.

**Premise re-measured, not inherited.** `pathb/t36/preconditions.sh` contains exactly **two** `exit`
statements — `:234 exit 1`, `:237 exit 0` — both top-level; the only functions are `ok()`/`bad()` at
`:57-58`. In a *sourced* script those exit the caller's shell, so control reaching the line after
`. "$RIG"` really does mean the rig never completed.

**RED:**

```
--- pre, DIRECT call          exit=0  stdout bytes=0  stderr bytes=0
--- pre, wrapper              exit=0  transcript bytes=0   PRECONDITIONS_EXIT=0
--- post, DIRECT call         exit=2  stderr: PRECONDITIONS NOT RUN: the rig at '…' returned
                                      without exiting — nothing was asserted.
--- post, wrapper             exit=2  transcript bytes=158  PRECONDITIONS_EXIT=2
```

**GREEN — five callers, both trees, live oracle, identical cell for cell:**

| caller | pre-MF-2 (P/F/rc) | post-MF-2 (P/F/rc) |
|---|---|---|
| C1 `bin/run-preconditions.sh`, tenant `gerege` | 22/0/0 | 22/0/0 |
| C2 `t51-negative.sh`'s form — direct, `default`, no `CANARY_REQ` | 16/5/1 | 16/5/1 |
| C3 `t55-negative-tests.sh:52` N2 — `t55-no-such-tenant` | 12/9/1 | 12/9/1 |
| C4 T44's control via `preconditions-COPY.sh`, `default` | 17/5/1 | 17/5/1 |
| C5 C1 from a foreign CWD (`/tmp`), absolute path | 22/0/0 | 22/0/0 |

All five transcripts **byte-identical** pre vs post once the export path is normalised out.
`has no row in fineract_tenants.tenants`: 1 occurrence, both trees.

> **Method note against myself.** My first pass gave C3 as **13**/9/1, not 12/9/1. My harness had
> supplied a `CANARY_REQ`; the real N2 at `leapboundary/bin/t55-negative-tests.sh:52` supplies none,
> which turns the digest-pin PASS into a FAIL. Run in its true form the cell is **12/9/1** and T115's
> figure is right. Recorded because a reviewer's deviation from the caller's real form is exactly the
> way a false discrepancy gets published.

### **N9 and N10 — MEASURED OPEN. F-2 IS NOT DISCHARGED.**

Both measured **through the post-MF-2 shim**, so this is an observation about the shipped fix and not
a caveat about it (`out/R6-MF2.txt`; independently again on the merged tree, `out/R9-POSTMERGE.txt`).

**N9** — the rig at its path replaced by the pre-hardening bytes (blob
`e6c1795a172168105d788321a71ee4ca62b73e36`, sha256 `9256b881153d3dea…`), shim asserted to carry the
MF-2 marker:

```
   EXIT=0
     PASS  MNT enabled for the tenant
   ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.
     PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
```

**N10** — the post-MF-2 shim reached through a symlink in a foreign tree, my own stub rig beside it:

```
   symlink: /tmp/T138-n10/evil/charges/bin/preconditions.sh -> …/charges/bin/preconditions.sh
   EXIT=0
     PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
   ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.
```

**Both still admit.** MF-2 closes the empty-rig limb (T107's N8a) and nothing else. The shim still
selects its rig by a `$0`-relative path with **no identity check**. Only **FU-1** — a digest pin, or
at minimum `shasum -a 256 "$RIG"` echoed into the transcript — closes them. T115 says this in both
shims, in `prove-guards.sh:91-93`, four times in its handoff and on every driver run, and it is
right to. **Nobody may merge this believing F-2 is discharged.**

### MF-3 — **REPRODUCED**, delta 0

Driver: `r7-mf3-mf4.sh`. Output: `out/R7-MF3-MF4.txt`. Pre-T91 = the unhardened copy resolved from
blob `e6c1795a…` (sha256 `9256b881153d3dea…`); post = the shipped shim (sha256 `829fe1181fe2641b…`).

```
/bin/sh     pre-T91: 16 PASS / 5 FAIL / exit 1   post: 16 PASS / 5 FAIL / exit 1   FAIL delta: 0
/bin/bash   pre-T91: 16 PASS / 5 FAIL / exit 1   post: 16 PASS / 5 FAIL / exit 1   FAIL delta: 0
```

Both FAIL sets printed side by side confirm the mechanism T115 describes: the hardened rig
**replaces**

```
FAIL  rounding-mode canary NOT run (set CANARY_REQ to the committed half-cent request). …
```

with

```
FAIL  rounding-mode canary NOT run: CANARY_REQ is unset. Set it to the committed half-cent request
      (t22-audit/req/calc-pmode2-gerege.json, sha256 2a6621be…352154). …
```

Five distinct FAIL texts before, five after. **There is no sixth.** The shipped header sentence now
says so.

### MF-4 — **REPRODUCED**, third independent measurement

Driver: `r7b-census.sh`. Output: `out/R7b-CENSUS.txt`.

My first net anchored on the literal path `charges/bin/preconditions.sh` and found only 2 direct
call sites — it missed the three callers that build the path from `$CH` or `os.path.join(HERE, …)`.
Widening it to every `.sh`/`.py` mention under `.softhouse/capture/` (64 raw lines) and then
classifying gives:

- **5 direct call sites in 5 files** — `charges/bin/run-preconditions.sh:9`, `charges/bin/attest.py:90`,
  `charges/bin/attest-t40.py:91`, `charges/bin/t51-negative.sh:21`,
  `leapboundary/bin/t55-negative-tests.sh:52`. All five quoted verbatim in the transcript.
- **18 wrapper call sites in 15 files.** All 18 listed.
- **TOTAL: 20 distinct files, 23 executable call sites.** Exactly T115's and T107b's figure.

T115's stated exclusions check out verbatim: `charges/bin/selfcheck.sh:15` is
`| grep -v 'bin/preconditions.sh' | …` — an exclusion, not a call; `charges/bin/attest-t40.py:305`
is a provenance string. I add two of my own: `charges/bin/attest.py:269` and
`pathb/t36/attest.py:369` are `'preconditions_script': 't36/preconditions.sh'` provenance strings
naming the **rig**, correctly outside this census (and the first is T115's own FU-3 — a shipped
attestation naming the rig as the authority for a run the *shim* executed).

---

## 2. Part 2 — the unreviewed sweep

### V-A — **REPRODUCED, and it is the sharpest thing in the branch**

Driver: `r2-va.sh`. Output: `out/R2-VA.txt`. `id -u` = 501, not root, so mode 555 really is
read-only.

```
verdict.sh (pre-fix) over a READ-ONLY transcript dir  [mode 555]
A2a-mutated-canary-gerege.txt   0  YES  no  ADMITS (printed the HALF_UP certification)
…/verdict.sh: line 86: /tmp/T138/va-PRE/.score-fail: Permission denied
…
A8-foreign-cwd.txt              0  YES  no  ADMITS (HALF_UP certification without a passing digest pin on gerege)

ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION.
EXIT=0
visible ADMITS rows on screen: 6
```

**Six `ADMITS` rows printed on screen, and the last line of the same run says all thirteen met their
expectation, exit 0.** The scoring loop is a pipeline subshell (`echo "$TABLE" | while …`), so no
variable it sets survives; the only channel was `$D/.score-fail`, and `$D` is the directory under
audit. Post-fix, same directory: **exit 1**, the six admissions named. Control (writable `$D`,
pre-fix scorer): exit 1. No attacker required — a read-only checkout, an export owned by another
user, or a read-only mount is enough.

Two things worth keeping from the transcript. First, the `Permission denied` diagnostics go to
**stderr**, so any caller that pipes stdout to a file — which is how every transcript in this rig is
produced — loses them entirely and keeps the false verdict. That is T80's F-1 shape recurring inside
the file whose own honesty note is about that class. Second, T115's fix is the right one: the channel
moves to a `mktemp -d` the script owns, and **writability is asserted before any scoring** with a
refusal (exit 3) if it cannot record a failure (`verdict.sh:87-96`). Mutation-tested at §3 below: put
the channel back in `$D` and G-5's RED leg goes red.

### V-C — **REPRODUCED**

Driver: `r3-vcef.sh`. Output: `out/R3-VCEFG.txt`. Reformat the canonical request `1162502.5` →
`1162502.50` — the same number, a different digest (`2a6621be…` → `b79ec0a1…`) — and apply T91's two
committed `sed` mutations:

```
   req-mutated-55.json is BYTE-IDENTICAL to the (reformatted) canon — the 'attack' is a copy
   req-crafted-04.json is BYTE-IDENTICAL to the (reformatted) canon — the 'attack' is a copy
      principal now: "principal":1162502.50,
```

Both "mutated canary" attacks silently degrade into firing the **pinned tie** at the rig. The
comparison was done with `decimal`, not float (P-25): `principal canon = 1162502.5`,
`reformatted = 1162502.50`, `numerically equal: True`. T115's fix (`run-attacks.sh:56-69`) asserts
the mutation **differed** from `$CANON` and carries the intended principal, and asserts A7's symlink
reads back as the tie; both fire before any oracle contact. Driven red as G-6 — see §3.

### V-E — **REPRODUCED**

```
-- PRE-fix:   identical  A1.txt
              pairs compared: 1   differing: 0
              RESULT: sh and bash agree on all 1 transcripts for label 'z'.
              PRE_EXIT=0
-- POST-fix:  identical  A1.txt
              MISSING  /tmp/T138/ve/z-sh/A2.txt  (present under z-bash only)
              pairs compared: 2   differing: 1
              POST_EXIT=1
```

A wildly different `A2.txt` present only on the bash side, and the pre-fix script reports agreement.
The mirror case (sh-only) *was* covered pre-fix — the domain was one side's list, and it was the
wrong side to trust. The union fix is correct. Driven red as G-7 — see §3.

### V-F — reproduced, but **the stated condition is wrong** → **F-T138-4**

Driver: `r3b-vf.sh`. Output: `out/R3b-VF.txt`. T115 states the hazard as *"a read-only `$O` would
leave the previous run's files and grade stale bytes."* A shell redirect to an **existing** file does
not need directory write permission, so that is not sufficient. Four cases over a pair that genuinely
differs:

| case | `$O` | scratch | pre-fix result |
|---|---|---|---|
| 0 control | writable | absent | `DIFFERS`, exit 1 — caught |
| 1 | **555** | absent | redirect cannot create; `diff: No such file`; **false `DIFFERS`, exit 1 — fail-closed** |
| 2 | **555** | present, **644** | redirect succeeds; `DIFFERS`, exit 1 — caught |
| 3 | **555** | present, **444** | **`pairs compared: 1  differing: 0` … `RESULT: sh and bash agree`, exit 0** |
| 4 | writable | present, **444** | **same vacuous pass — `$O` need not be read-only at all** |

So the vacuous pass is real (cases 3 and 4) but it is caused by **read-only scratch files**, not by a
read-only `$O`; a read-only `$O` alone is *fail-closed*. Case 3', the same directory under the
post-fix script: `DIFFERS`, exit 1. **The fix is right; only its stated reason is wrong** — the same
P-11 shape as F-T138-2 below.

### V-G — **REPRODUCED**

Pre-fix `prove-guards.sh:66-67`:

```sh
cp "$ROOT/.softhouse/capture/t91/out/prefix-copy-sh"/A*.txt "$S/poison/" 2>/dev/null || \
  { echo "   (no committed pre-fix transcripts to poison; skipping G-4)"; exit 0; }
```

`exit 0` — a tree with no committed transcripts produced a clean, fully-successful run of a guard
that never executed. Post-fix it is `ABORT … exit 2`. The pre-fix `ugrep` else-branch asserted an
interactive measurement as fact; post-fix it states the absence of a measurement. And the pre-fix
script's last statement is `echo "=== done"` with no `exit`, i.e. exit 0 unconditionally. All
confirmed from source and by execution (`out/R3-VCEFG.txt`, `out/R4-GUARDS.txt`).

---

## 3. Every guard driven red by me

Driver: `r4-guards-red.sh`, `r5-mutate-g5-g7.sh`, `r14b-g4fix.sh`. Output: `out/R4-GUARDS.txt`,
`out/R5-MUTATIONS.txt`, `out/R14b-G4FIX.txt`.

**Baseline: `prove-guards.sh` on the T115 tip = exit 0, 13 legs `OK`, matching the committed
`out/GUARDS-RED.txt` leg-for-leg.**

### The two red drives T115 claims — both reproduced

**(a) From a non-git export.**

```
export at /tmp/T138-nongit is NOT a git repo (no .git)
--- POST-fix (T115):  ABORT: git archive failed — there is nothing to prove anything against.
                      POST_EXIT=2
--- PRE-fix  (T91) from the SAME export: a full-looking transcript, "=== done", PRE_EXIT=0
```

**(b) With a guard it grades neutered** (`verdict.sh` → `#!/bin/sh\nexit 0\n`):

```
--- POST-fix:
   exit=0  EXPECTED 3  *** NOT AS EXPECTED ***  [G-2 verdict.sh over an empty set]
   A2a NOT named as an admission  *** NOT AS EXPECTED ***  [G-4]
   exit=0  EXPECTED 1  *** NOT AS EXPECTED ***  [G-5 GREEN discriminates]
   exit=0  EXPECTED 1  *** NOT AS EXPECTED ***  [G-5 RED read-only transcript dir …]
done — 4 leg(s) did NOT behave as expected.
POST_EXIT=1
--- PRE-fix on the same tree: PRE_EXIT=0
```

**Exactly four legs, exactly the four T115 names.**

### Mutation tests — revert each fix, does its guard go red?

| fix reverted | guard | result |
|---|---|---|
| V-A (channel back into `$D`) | G-5 RED | `exit=3 EXPECTED 1 *** NOT AS EXPECTED ***`, script **exit 1** ✔ |
| V-E (iterate the sh side only) | G-7 RED | `exit=0 EXPECTED 1 *** NOT AS EXPECTED ***`, script **exit 1** ✔ |
| V-F (scratch back into `$O`) | — | every leg `OK`, script **exit 0** ✘ — **no guard covers V-F** |
| MF-1's shape test | — | every leg `OK`, script **exit 0** — covered by `t115-drive-mf1.sh` instead, not a defect |

### **F-T138-1 [P2] — G-4 cannot fail on the failure it exists to detect**

`.softhouse/capture/t91/prove-guards.sh:128-136` (the poison) and `:167` (the assertion).
**Two independent reasons, either sufficient.**

**(a) The assertion is satisfied by the exit-code rule.** G-4 asserts only
`LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS"`. In the pre-fix transcript set `A2a` exits 0 and expects
`BREACH`, so the exit-code rule alone already produces `ADMITS (exited 0, expected a breach)`.
I blinded the sentence scanner (`c=no` unconditionally — precisely the outcome a silent-miss grep
produces) and G-4 printed `A2a named as an admission on the poisoned set   OK      [G-4]`; the whole
script exited 0.

**(b) The poison is placed in the one position that cannot fail.** The insertion is
`b[:j] + b'\xff\xfe' + b[j:]` where `j = b.find(b'\n', i)` — i.e. **after** the match, same line.
That is T108 shape `s02`. I measured on this host (`out/R12-GREP.txt`, `/usr/bin/grep` = BSD grep
2.6.0-FreeBSD, from inside a script per P-33):

```
SHAPE          INVOCATION               rc (0=found, 1=NOT found)
before         utf8 -qF                 1      <- silent miss
before         utf8 -aqF                1      <- -a does NOT fix it
before         LC_ALL=C -qF             0      <- LC_ALL=C does
before         LC_ALL=C -aqF            0
after          utf8 -qF                 0
after          utf8 -aqF                0
other          utf8 -qF                 0
```

So G-4's input is structurally incapable of producing the effect. **And its two display lines
(`:139`, `:141`) run BOTH arms under `LC_ALL=C` — the mitigation under test** — which is P-33's
named error, still present.

**The consequence, measured end to end** (`out/R14b-G4FIX.txt`). Remove `LC_ALL=C` from
`verdict.sh`'s sentence scanner — the exact regression G-4 exists to catch — and the **shipped**
`prove-guards.sh` reports `A2a named as an admission on the poisoned set   OK  [G-4]` and exits **0**.

**Fix, driven red by me before prescribing it (P-22).** Two edits, and I measured that **both** are
required:

| tree | healthy | `LC_ALL=C` removed | scanner blinded |
|---|---|---|---|
| shipped | exit 0 | **exit 0** ✘ | exit 1 |
| poison-position edit only | — | **exit 0** ✘ | — |
| assertion edit only | — | **exit 0** ✘ | — |
| **both edits** | **exit 0** ✔ | **exit 1** ✔ | **exit 1** ✔ |

Edit 1 — `prove-guards.sh:134`:

```python
-open(p, 'wb').write(b[:j] + b'\xff\xfe' + b[j:])
+open(p, 'wb').write(b[:i] + b'\xff\xfe' + b[i:])   # BEFORE the match, same line (T108 shape s01/s06)
```

(`j` becomes unused and its line may go.) Edit 2 — `prove-guards.sh:167`:

```sh
-if LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS" "$S/g4.txt"; then
+# The old form (^A2a.*ADMITS) is satisfied by the EXIT-CODE rule alone — A2a exits 0 and expects
+# BREACH — so it stayed green with the sentence scanner fully blinded (T138 F-T138-1).  Assert the
+# SENTENCE-SPECIFIC verdict, which only c=YES can produce.
+if LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS (printed the HALF_UP certification)" "$S/g4.txt"; then
```

Recommended edit 3 — `prove-guards.sh:139,141`: run one arm in a UTF-8 locale so the display shows
the discrimination instead of two `rc=0`s taken under the mitigation:

```sh
LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /usr/bin/grep -aqF "$S" "$f"; echo "   BSD utf8   -aqF rc=$?  (1 = the silent miss)"
LC_ALL=C                            /usr/bin/grep -aqF "$S" "$f"; echo "   BSD LC_ALL=C -aqF rc=$?  (0 = correct)"
```

> **Method note against myself.** My first attempt at edit 1 used a `sed` whose pattern did not
> match, so the python block was **copied unchanged** and the "fix" was a no-op — V-C's own lesson
> landing on the reviewer. I caught it only because the harness echoes the block back. `r14b` redoes
> it in python with `assert old in s`, so a non-matching edit aborts. Both transcripts are committed
> (`out/R14-G4FIX.txt` is the failed attempt; `out/R14b-G4FIX.txt` is the sound one).

### **F-T138-7 [P3] — printed-not-compared, recurring inside T115's own new guards**

`prove-guards.sh:220` (G-6) and `:236` (G-7) print the diagnostic line through
`grep … | head -n | sed 's/^/   /'` and never compare it or touch `BAD`. Only the exit status is
graded. Demonstrated (`out/R4-GUARDS.txt`): with `assert_mutated` removed **and** A7's symlink target
broken, G-6 reported

```
   exit=2   EXPECTED 2   OK      [G-6 RED reformatted canary -> harness error, not an 'attack']
   HARNESS ERROR: A7's symlink does not read back as the canonical request
```

— a different error entirely, and the script exited 0. This is T107's own F-6.3 ("`(expect 3)`
printed instead of compared") reappearing inside the fix for F-6. Scoped honestly: it needs two
simultaneous edits, so G-6 is **weak, not vacuous**. One-line fix, both legs:

```sh
LC_ALL=C /usr/bin/grep -aq 'is byte-identical to the canonical request' "$S/g6.txt" \
  || { echo "   *** G-6 exited 2 for the WRONG reason ***"; BAD=$((BAD+1)); }
```

### **F-T138-5 [P3] — "each new one is driven red by a committed guard" is false for two of five**

`T115.md` §4 summary. G-5 covers V-A, G-6 covers V-C, G-7 covers V-E. **V-F and V-G have no leg.**
Mutation-tested above: reverting V-F leaves `prove-guards.sh` exit 0 with every leg `OK`. V-G's
G-4-skip ABORT and the `ugrep` else-branch are text changes with nothing exercising them. Either add
legs, or restate the sentence as *"three of the five new ones are driven red by a committed guard
(G-5, G-6, G-7); V-F and V-G are argued from source and are not."* The second is honest and is one
edit.

---

## 4. **V-B — my ruling: report-not-fix was the WRONG call, but it does not block the merge**

Driver: `r13-vb.sh`. Output: `out/R13-VB.txt`. Thirteen dead-oracle-shaped transcripts (the rig runs,
every oracle-dependent check FAILs, the certification sentence never printed, `EXIT=1`).

**(a) The hazard is real.** With `A4c`, `A7` and `A8` all retyped `CLEAN` → `BREACH`:

```
A2a … A8   1  no  no  OK      (all thirteen rows)
ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION.
EXIT=0
```

A clean sweep reported over an oracle that never answered.

**(b) T115 overstates the fragility by 3×.** T115 writes: *"Retyping **any one** of those three rows
to `BREACH` would silently create a scorer that reports a clean sweep."* Measured — retyping **one**
(`A7`) still gives `EXIT=1` with two `REGRESSION` rows remaining. It takes **all three**. This is
logged as part of F-T138-3 because a standing hazard handed to the driver gets *cited*, and a 3×
overstatement in a hazard note is the same defect as a 3× understatement.

**(c) The deeper fact T115 identified is correct and is the one that matters.** No row in the table
asserts the certification sentence is **present**. `NEVER` forbids it; `PINNED` merely *permits* it —
`if [ "$c" = YES ]` gates the whole check, so when the oracle is dead and `c=no`, the `PINNED` rows
assert nothing at all. The only thing between a dead oracle and a clean sweep is that three rows
happen to expect exit 0. That is an accident of the data, exactly as T115 says.

**Ruling.** **Fix it; do not block on it.**

*Why fix rather than document.* T115's stated reason for not fixing — *"changing the expectation
table is a substantive act, not a micro-fix"* — is sound as far as it goes, but it does not apply to
the cheapest correct fix, which changes **no expectation at all**. Add a global assertion after the
zero-file check at `verdict.sh:161`:

```sh
# T138 (V-B).  Nothing in the table asserts the oracle ANSWERED: NEVER forbids the certification
# sentence and PINNED merely permits it.  Resistance to a dead oracle rested entirely on A4c/A7/A8
# being CLEAN rows — an accident of the data, measured by T138.  Make it deliberate.
if ! LC_ALL=C grep -alF "$S" "$D"/A*.txt >/dev/null 2>&1; then
  echo "ERROR: not one transcript contains the rounding-mode certification sentence — the suite" >&2
  echo "       never reached a live oracle.  Scoring it would grade an outage as a clean sweep." >&2
  exit 3
fi
```

**I drove this fix red before prescribing it** (`r15-vbfix.sh`, `out/R15-VBFIX.txt`), applying it to
a copy of the shipped `verdict.sh` with the anchor asserted rather than assumed:

* **No-op on every committed transcript directory.** All **20** of them (8 on T91's tip, 12 on
  T115's) carry the certification sentence in 5 or 6 transcripts, and the patched scorer's exit code
  is **identical to the shipped one in every single directory** — eight `exit=0`, twelve `exit=1`,
  `SAME` twenty times out of twenty.
* **Red on a dead oracle.** The 13 dead-oracle transcripts: shipped `exit=1` (accidental), patched
  **`exit=3`** with `ERROR: not one transcript contains the rounding-mode certification sentence —
  the suite never reached a live oracle.`
* **Red on the case that matters.** Dead oracle **and** all three `CLEAN` rows retyped to `BREACH` —
  the configuration that scored `ALL 13 …`, exit **0** before — now **`exit=3`**.

It changes no row, it costs nine lines, and it converts the accident into an assertion. If the driver
prefers the structural form, the alternative is a third `sentence-permitted` value `REQUIRED` (must
appear, and only with a passing pin on `gerege`) applied to `A4c`/`A7`/`A8` — also a no-op today,
since all three real transcripts score `c=YES d=YES g=YES`.

*Why it does not block.* (i) The shipped table **does** resist a dead oracle — measured, exit 1 with
three `REGRESSION` rows. (ii) The oracle is up and every committed transcript is a real observation.
(iii) T107b established that **zero of 42 promoted parity vectors depend on this gate**, so nothing
downstream is certified through it. The hazard is prospective — it fires on a *future* edit to the
table — which is precisely what makes an assertion better than a paragraph.

*On the T121 analogy.* It holds, and it points the same way. T121 removed a probe that survived by an
accident of spelling rather than documenting it, on the principle that an accidental property doing
load-bearing work should be made deliberate or removed. The difference here is that the accidental
property is doing *correct* work, so the remedy is to make it deliberate, not to remove it — and the
cost of doing so is nine lines that change nothing. Documenting it puts the burden on the next person
to edit the expectation table, and that person will be reading the table, not the handoff.

---

## 5. Part 3 — is the stream mergeable?

### Attack suite end to end — **REPRODUCED**

On the merged tree (`out/R9-POSTMERGE.txt`):

| | scorer | result |
|---|---|---|
| pre-fix `sh` | exit **1** | **6 of 13 ADMIT** — `A2a`, `A2c`, `A4c`, `A5`, `A7`, `A8` |
| pre-fix `bash` | exit **1** | the same **6** |
| post-fix `sh` | exit **0** | **0 of 13**, `ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION` |
| post-fix `bash` | exit **0** | **0 of 13** |
| invariance, `t115-pre` | exit 0 | **13 pairs compared, 0 differing** |
| invariance, `t115-post` | exit 0 | **13 pairs compared, 0 differing** |

**Additive — confirmed by tree hash, not by inspection** (`out/R11-HYGIENE.txt`). All nine of T91's
own `out/` directories are **byte-identical** between `ccf3c14` and `bd59187`:
`prefix-copy-{sh,bash}`, `prefix-livetwin-{sh,bash}`, `postfix-copy-{sh,bash}`,
`postfix-livetwin-{sh,bash}`, `happy`. The only pre-existing file touched under `out/` is
`GUARDS-RED.txt`, regenerated as declared; everything else is `A`.

Modified files in the whole T115-vs-T91 diff: the two shims, `PREDICTION.md`, `GUARDS-RED.txt`, and
the four rig scripts. **Nothing else.** No vector, no `PIN.json`, no `capabilities.json`, no
`conformance.sh`, no `gates.md`, no `tasks.json`, no `nexus/`.

### Conformance — **PASS**

`bash .softhouse/conformance.sh` on the **merged** tree:

```
    parity vectors          PASS 42   FAIL 0
    cells compared          5576 graded, 84 ungraded
    invariant violations    0
    invariant assertions    0 NOT RUN
VERDICT: PASS (exit 0)
```

Identical to the run T115 committed at `out/CONFORMANCE-T115.txt`.

### Go — **clean** (P-30; toolchain at `.softhouse/toolchain/go/bin/go`)

```
go version go1.26.6 darwin/arm64
go build ./...   BUILD_EXIT=0
go test ./...    ok  …/loanschedule  9.477s
                 ok  …/loanschedule/conformance  26.467s
gofmt -l .       internal/apps/loanschedule/contract/contract.go     (count: 1)
```

`gofmt -l` names **exactly** `contract.go` — gate G-3, expected. **No `gofmt -w` was run.**

### P-24 — scratch merge into **current** `main`

`main` had moved again: T115 merged against `9cf1f90` and `e35ea7b`; current `main` is
**`bcf2c55`**. `r8-merge.sh` merges **T91 (`ccf3c14`) + T107 (`b70b295`) + T115 (`bd59187`)** into a
throwaway clone of `bcf2c55`. **All three merges clean, rc=0, no conflict.** Merged head `9050783`.

Frozen surfaces, `main` vs merged — **all six IDENTICAL**:

```
   .softhouse/vectors/PIN.json                             b51595bbca0d  IDENTICAL
   .softhouse/vectors/capabilities.json                    882e97bc4853  IDENTICAL
   nexus/…/contract/contract.go                            4bcbafaddd60  IDENTICAL
   .softhouse/conformance.sh                               a91079467b16  IDENTICAL
   .softhouse/gates.md                                     57a8aa380722  IDENTICAL
   .softhouse/tasks.json                                   73378228be78  IDENTICAL
```

`git diff main HEAD` over `.softhouse/vectors/`, `nexus/`, `pathb/`, `charges/out/`,
`t74-multiplesof/`, `t83-nonamortizing/`, `conformance.sh`, `gates.md`: **empty**. No sibling
worker's surface touched. (`tasks.json` identical to `main`'s is the correct P-31 outcome — the
branch authors zero change to it.)

**All five artefacts re-run ON THE MERGED TREE** — not only conformance, because re-running the
*artefact* is what caught T98's relocated time bomb:

| artefact | result on merged `main` |
|---|---|
| `prove-guards.sh` | **exit 0**, 13 legs `OK` |
| `t115-drive-mf1.sh` | **exit 0** — `MF-1 driven RED and GREEN, every leg as specified` |
| `t115-drive-mf2.sh` | **exit 0** — five callers identical; **`N9 STILL ADMITS` / `N10 STILL ADMITS`** |
| `t115-drive-mf3-mf4.sh` | **exit 0** — breach delta 0 both interpreters; **20 files / 23 sites** |
| `t115-rerun-attacks.sh` | **exit 0** — pre 6/13 exit 1, post 0/13 exit 0, 13/13 identical |
| `conformance.sh` | **exit 0**, 42 / 5576 / 0 / 0 |

**Baselines are literal immutable shas — confirmed.** `git grep` for `merge-base`, `main:`,
`origin/main` and `rev-parse main` across the two shims and all of `capture/t91/` returns **nothing**.
The only 40-hex constants are `PRE_SHA=ccf3c141…` (twice), `PRE_RIG_BLOB=e6c1795a…`,
`PRE_SHIM_BLOB=e6c1795a…` (twice) and the canary `PIN=2a6621be…`. The POST side resolves `HEAD`,
which is correct — that is "the tree under test", not a baseline that can follow `main`. This is
exactly the property T98's fix got wrong, and it is why the artefacts pass identically on the branch
and on merged `main`.

### `LC_ALL=C grep -a` — **not weakened anywhere**

Occurrence counts, `ccf3c14` → `bd59187`:

```
verdict.sh             LC_ALL=C:  5 ->  7     grep -a:  4 ->  4
run-attacks.sh         LC_ALL=C:  1 ->  2     grep -a:  0 ->  1
shell-invariance.sh    LC_ALL=C:  1 ->  1     grep -a:  0 ->  0
prove-guards.sh        LC_ALL=C:  6 -> 13     grep -a:  5 -> 11
```

Monotonically up or flat. Every remaining bare `grep` is in a comment, an `echo` string, or
`verdict.sh:154` (`echo "$TABLE" | grep -c '|'`, over an in-script string, not a file). No removal,
no weakening.

### **F-T138-2 [P2] — the two "under adjudication by T108" comments should now be UPDATED, and the current text is affirmatively wrong**

The brief asks whether they should be updated. **Yes, and not cosmetically** — they assert as
measured fact something T108 has refuted and I refuted again on this host in one command.

`verdict.sh:26-30` and `prove-guards.sh:143-145` say:

> *"with `/usr/bin/grep` — BSD grep 2.6.0-FreeBSD — a silent miss does NOT reproduce, with an invalid
> multibyte sequence or an embedded NUL, in any locale. T107b's probe matched 18 of 18 combinations.
> So **T80's stated BSD behaviour does not reproduce on this host** and is not repeated here as fact."*

It reproduces. `out/R12-GREP.txt`, `/usr/bin/grep` from inside a script, invalid byte **before** the
match on the same line: `utf8 -qF` → **1**, `utf8 -aqF` → **1**, `LC_ALL=C -qF` → **0**. T108's
ruling: T80's *measurement* was correct and exactly reproduced (`t108-grep/out/matrix.tsv`, 12 silent
misses in 360 cells, all BSD grep in a UTF-8 locale); only T80's *generalisation* ("matches nothing
in a FILE") was wrong — the blindness is per line and directional. The two failed reproductions
failed because the probes put the poison **after** the match and ran both arms under `LC_ALL=C`.

`verdict.sh:32-38` and `prove-guards.sh:155-161` further mark the `ugrep` limb `[UNVERIFIED]` resting
on *"ZERO committed evidence"*. T108 retired that: `t108-grep/out/probe-flags.txt` §B is the committed
evidence, and C-7 is withdrawn.

Both comments are honestly hedged — "THE HARDENING STANDS", "under adjudication by T108" — which is
why this is a MICRO-FIX and not worse. But the wrong half is exactly the half a future editor would
cite to drop `LC_ALL=C`, and P-33 is already in `patterns.md`. **Replacement text is in §7.**

### The known leftover — `T91.md:8`

**Confirmed.** Line 8 still reads *"is the one that **17 capture scripts and `attest.py` actually
invoke**"* against the measured 20/23. Replacement text in §7.

Sweeping the merged tree for the concept and the numbers (P-26), every other restatement is already
correct or already annotated: `charges/bin/preconditions.sh:13` (MF-4 correction),
`PREDICTION.md:14` (struck through and corrected), `t115-drive-mf3-mf4.sh:11`, `T107.md:191`,
`T107-review-of-T91.md:200,579`, `T115.md:110,138,308`. **`tasks.json` restates it in two notes
(`:1946`, `:2249`)** — correctly *not* touched by T115 under P-31; the orchestrator owns that file.
**What this sweep could not have found:** a restatement phrased in words rather than digits, one
carried as a count inside a table, or one in a file outside the merged tree.

---

## 6. Findings register

| id | sev | file:line | finding |
|---|---|---|---|
| **F-T138-1** | **P2** | `capture/t91/prove-guards.sh:128-136`, `:139`, `:141`, `:167` | **G-4 is green on a tree with `LC_ALL=C` removed from the scanner it guards.** Its assertion is satisfied by the exit-code rule; its poison sits in the one position BSD grep handles correctly; its two display arms both run under the mitigation. Fix in §3, driven red. |
| **F-T138-2** | **P2** | `capture/t91/verdict.sh:26-30`, `:32-38`; `prove-guards.sh:143-145`, `:155-161` | Two shipped comments assert "T80's BSD behaviour does not reproduce on this host" and "[UNVERIFIED] … ZERO committed evidence". Both **refuted by T108** and re-refuted by me in one command. Text in §7. |
| **F-T138-3** | P3 | `T115.md` §4 V-B row, §7 V-B row | V-B's fragility overstated 3× — it takes **all three** CLEAN rows retyped, not "any one". Hazard itself confirmed. Ruling in §4. |
| **F-T138-4** | P3 | `T115.md` §4 V-F row; `shell-invariance.sh:40-42` comment | V-F's stated condition ("a read-only `$O`") is **fail-closed**, not vacuous. The vacuous pass needs read-only **scratch files**; `$O` need not be read-only at all. Fix is correct; reason is wrong. |
| **F-T138-5** | P3 | `T115.md` §4 header sentence | "each new one is driven red by a committed guard" — **false for V-F and V-G**. Mutation-tested. |
| **F-T138-6** | P3 | `capture/charges/bin/preconditions.sh:89` | Dangling evidence pointer: *"transcripts under `.softhouse/capture/t91/out/t115-mf2/`"* — **that directory does not exist** (189 committed paths under `out/`, zero matching). The real transcript is `out/T115-MF2-RED-GREEN.txt`. In a file that ships to `main`. |
| **F-T138-7** | P3 | `prove-guards.sh:220`, `:236` | G-6 and G-7 **print** their diagnostic instead of comparing it; only the exit code is graded. T107's F-6.3 recurring inside the fix for F-6. Demonstrated: G-6 `OK` on a completely different exit-2. |
| **F-T138-8** | P4 | `T115.md` §2 MF-2 table, §4 last para, §6 | (a) "162 bytes" is **path-dependent** — I measured 158 on my export; the message embeds an absolute path. State the message, not the length. (b) "**7 guards** (G-1, G-1b, G-2, G-3, G-4, G-5, G-6, G-7)" lists **eight** names; the run reports **13 legs**. (c) MF-1's RED table says "10 of 13 committed transcripts" without naming the base set, which changes the answer. |

**Residual risk, not a finding.** `t115-drive-mf1.sh:32` discriminates the pre-baseline on the string
`no EXIT= line`, which the *post*-fix file carries in both a comment and a `printf`. The pre baseline
lacks it entirely, so the check is sound today; a future comment mentioning that phrase in a pre
baseline would misfire — **fail-closed (ABORT)**, so harmless. Noted because it is one character away
from the self-catch T115 records against itself.

**Constraints checked and clean.** No float anywhere in the diff or in my analysis scripts (P-25 —
the only derived quantities are counts from `grep -c` and shell integer arithmetic; the one numeric
comparison I made, canon vs reformatted principal, used `decimal.Decimal`). No `gofmt -w`. No vector,
`PIN.json`, `capabilities.json`, `conformance.sh`, `gates.md`, `tasks.json` or `nexus/` touched by
T115 or by me. No sibling worker's capture tree touched. Nothing promoted. **T115's fix was not
modified.** All destructive work in `/tmp`.

---

## 7. Replacement text the driver may apply at merge

None of these changes any measured result.

### 7.1 `.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T91.md:8-9`

Replace:

```
byte-identical to the named copy — is the one that **17 capture scripts and `attest.py` actually
invoke**. The named copy is invoked by nothing. Both are now call-throughs to the one hardened rig.
```

with:

```
byte-identical to the named copy — is the one that **20 distinct files invoke, from 23 executable
call sites**: 5 direct (`charges/bin/run-preconditions.sh:9`, `charges/bin/attest.py:90`,
`charges/bin/attest-t40.py:91`, `charges/bin/t51-negative.sh:21`,
`leapboundary/bin/t55-negative-tests.sh:52`) and 18 through the T40 wrapper
`charges/bin/run-preconditions.sh`. The "17 capture scripts and `attest.py`" written here originally
was wrong in both directions — it omitted a *direct* invoker in another subtree and it counted files
where the load-bearing figure is call sites. Corrected by T115 (MF-4); measured independently three
times (T107b, T115, T138); re-derive with `.softhouse/capture/t91/t115-drive-mf3-mf4.sh` rather than
trusting this number. The named copy is invoked by nothing. Both are now call-throughs to the one
hardened rig.
```

### 7.2 `.softhouse/capture/t91/verdict.sh:21-42` — the T108 block

Replace the block from `*** THE HARDENING STANDS. ITS STATED REASON IS UNDER ADJUDICATION BY
T108. ***` through the `[UNVERIFIED on Linux …]` line with:

```
#     *** SETTLED BY T108 (2026-08-21).  BOTH TOKENS ARE LOAD-BEARING, AGAINST TWO DIFFERENT
#     PROGRAMS.  DO NOT REMOVE EITHER. ***
#     On this host the token `grep` names two programs and which one you get depends on where you
#     type it (P-33):
#       * inside a script (`sh x.sh` / `bash x.sh`): /usr/bin/grep — BSD grep 2.6.0-FreeBSD.
#       * typed into the Claude Code Bash tool: a shell function re-exec'ing the `claude` binary
#         with argv[0]=ugrep — ugrep 7.5.0 with `-I` hard-coded.  There is NO ugrep binary on this
#         host; ugrep is embedded in `claude`.  That is why every search for one came back empty.
#     They fail in OPPOSITE ways:
#       * BSD grep goes blind to the rest of ONE LINE, from an invalid multibyte byte rightwards.
#         `LC_ALL=C` fixes it; `-a` does NOT.
#       * ugrep `-I` skips the WHOLE FILE.  `-a` fixes it; `LC_ALL=C` does NOT.
#     [VERIFIED: .softhouse/capture/t108-grep/MATRIX.md §1 and §3.1; out/matrix.tsv — 360 cells,
#     12 silent misses, every one BSD grep in a UTF-8 locale; out/probe-flags.txt §B for ugrep.]
#
#     T80's MEASUREMENT was correct and is exactly reproduced.  Only T80's GENERALISATION — "matches
#     nothing in a FILE" — was wrong: the BSD blindness is per line and directional, never per file.
#     An earlier version of this comment said T80's behaviour "does not reproduce on this host".
#     THAT WAS WRONG, and it was wrong for a reason worth keeping: T91's and T107b's probes put the
#     invalid byte AFTER the match on the same line and ran both arms under LC_ALL=C — the very
#     mitigation under test.  N-of-N green cells refute nothing unless the failing shape is among
#     the N.  T138 re-measured on this host: byte BEFORE the match, `utf8 -qF` -> 1, `utf8 -aqF` ->
#     1, `LC_ALL=C -qF` -> 0.  T107's ugrep limb is likewise no longer [UNVERIFIED]: T108 committed
#     the evidence and retired C-7.
#
#     Independent of both: `LC_ALL=C` also defends against GNU grep on Linux, where a UTF-8 locale
#     genuinely can fail to match across an invalid multibyte sequence.  These scripts run on macOS
#     today and nothing pins that.  [UNVERIFIED on Linux — no Linux host available.]
```

### 7.3 `.softhouse/capture/t91/prove-guards.sh:143-147` and `:154-162`

`:143-147` →

```sh
echo "   NOTE (T138): the poison above is inserted BEFORE the match on the same line — T108 shape"
echo "   s01/s06, the only shape BSD grep fails on.  An earlier version put it AFTER the match"
echo "   (shape s02), which BSD grep handles correctly in every locale, so the leg could not"
echo "   produce the effect it exists to detect."
echo "   RULED BY T108 (2026-08-21), MATRIX.md §1/§3.1: BSD grep goes blind to the rest of ONE LINE"
echo "   from an invalid byte rightwards — LC_ALL=C fixes it, -a does NOT.  ugrep -I skips the WHOLE"
echo "   FILE — -a fixes it, LC_ALL=C does NOT.  T80's measurement was correct; only T80's"
echo "   generalisation ('matches nothing in a FILE') was wrong."
echo "   *** BOTH TOKENS ARE LOAD-BEARING AGAINST DIFFERENT PROGRAMS.  DO NOT REMOVE EITHER. ***"
```

the `else` branch at `:154-162` →

```sh
else
  echo "   ugrep is not a BINARY on this host and never was.  T108 established that the token"
  echo "   \`grep\` typed into the Claude Code Bash tool runs a shell FUNCTION re-exec'ing the"
  echo "   \`claude\` binary with argv[0]=ugrep — ugrep 7.5.0 with -I hard-coded — which a script"
  echo "   cannot reach, because shell functions are not exported to children.  So this branch is"
  echo "   the EXPECTED one here, and the ugrep limb is no longer unmeasured: it is [VERIFIED] in"
  echo "   .softhouse/capture/t108-grep/out/probe-flags.txt §B — -qF returns 1 ('absent') on a file"
  echo "   that contains the sentence, in BOTH locales, and -qaF returns 0.  T107b's C-7 downgrade"
  echo "   is retired.  ugrep -I skips the whole file; -a fixes it and LC_ALL=C does not."
fi
```

### 7.4 `.softhouse/capture/charges/bin/preconditions.sh:89`

```
-# ADMIT — measured by T115, transcripts under .softhouse/capture/t91/out/t115-mf2/.  Only FU-1 (a
+# ADMIT — measured by T115 and re-measured by T138; transcript at
+# .softhouse/capture/t91/out/T115-MF2-RED-GREEN.txt, re-derivable with t115-drive-mf2.sh.  FU-1 (a
```

### 7.5 The three code fixes

`prove-guards.sh:134` and `:167` (F-T138-1, both required, both driven red — §3);
`prove-guards.sh:139,141` (F-T138-1 edit 3); `prove-guards.sh:220,236` (F-T138-7);
`verdict.sh` after `:161` (V-B assertion — §4).

---

## 8. `[UNVERIFIED]` — what I did not measure

* **Anything on Linux, or with GNU grep.** No Linux host. The `LC_ALL=C` defence against GNU grep's
  UTF-8 behaviour is reasoned, not measured here.
* **The ugrep limb, first-hand.** I confirmed from inside a script that `command -v grep` is
  `/usr/bin/grep` and no `ugrep` binary is reachable, which is consistent with T108. I did **not**
  re-run T108's `probe-flags.txt` §B; I read its ruling and re-derived only the **BSD** half, which
  is the half my findings depend on.
* **N9/N10 beyond the two shapes measured.** Substituted rig and symlinked shim. A rig reached via a
  hard link, a `PATH`-relative invocation, or a bind mount is untested.
* **The five `happy/` transcripts' content.** I checked their shape (they are not `verdict.sh`
  inputs) and did not re-derive their preconditions.
* **`prove-guards.sh` G-1 GREEN against a *wrong* oracle.** The oracle was up and correct throughout;
  a vacuous pass that needs the oracle to be *wrong* rather than *absent* is out of reach here, as
  T115 also says.
* **The other capture trees.** My sweep is the T91 rig and the two shims, exactly as T115's was. I
  did not sweep `pathb/t36/preconditions.sh`, `attest.py`, `attest-t40.py`, `t51-negative.sh`,
  `t55-negative-tests.sh` or any sibling worker's tree, all of which contain checks of this shape and
  none of which anybody has swept. F-T138-1 is evidence that the class is not exhausted.
* **What a grep census structurally cannot find** (inherited from MF-4 and re-stated because it binds
  my third measurement too): an invocation built by string concatenation, held in a variable, made
  from CI or a Makefile, made through a symlink or a copied path, or typed by a human at a prompt.

---

## 9. Ruling

**MICRO-FIX. The T91 stream — T91 + T107 + T115 — IS MERGEABLE.**

Merge it. Apply §7.1 through §7.5 at merge; none of them changes a measured result, and §7.2/§7.3
correct statements that are now affirmatively false in files that ship to `main`.

Carry forward, unchanged and undischarged:

* **FU-1 is open and F-2 is NOT discharged. N9 and N10 both still exit 0.** Re-measured by me,
  through the shipped shim, on the branch and again on merged `main`.
* **F-T138-1** should be fixed before the next task cites `GUARDS-RED.txt` as evidence that the
  `LC_ALL=C grep -a` hardening is guarded. It is not: the guard is green with the hardening removed.
* **V-B** — fix per §4, do not block.
* T115's own FU-3 (`AUDIT-CHARGES.md:190`, `attestation*.json:11`) and FU-5 remain open.
