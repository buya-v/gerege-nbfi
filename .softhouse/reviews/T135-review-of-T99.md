# T135 — independent review of T99 / T99b (`softhouse/T99-pathb-lower-findings`, 11 commits)

Reviewer branch: `softhouse/T135-review-t99`.
Under review: `ab2de89..8474bf0` — 8 commits from a worker the harness killed (rescued, no handoff)
and 3 from T99b, which was sent to regenerate the evidence rather than trust it.
Every number below is from a command I ran; where I could not run it, it is in the `[UNVERIFIED]`
list. All my probe scripts are committed under `.softhouse/reviews/T135-evidence/`.

---

## VERDICT: **MICRO-FIX**

The substance is right. All four of T85's findings are genuinely closed; F-5 and F-6 are real,
correctly diagnosed and correctly fixed; the rescued half is admissible; and the shared reference
oracle is undisturbed. I attacked the rig with shapes T99b did not try and it held every time.

Three things must change before merge, and one of them is a defect the program has already paid for
twice:

| # | severity | finding |
|---|---|---|
| **T135-1** | **P1** | `t99/lib.sh:25` computes the pre-fix baseline as `git merge-base main HEAD` — the exact anti-pattern `main` already documents as having failed twice (T87→T98→T102). **Measured on a scratch merge into current `main`: f1/f2/f3 abort exit 3 and `prove-f4.sh` exits 1 reporting "F-4 NOT CLOSED".** One-line fix, verified. |
| **T135-2** | **P2** | The backlog ruling that T133 will act on is **wrong twice**: the two "copies" are byte-identical (so the second has **three** F-5 sites, not two), and **the transcription is not sufficient** — those copies are the pre-T76/T77/T80/T85 generation and are holed on the *ratified rounding mode*, which I demonstrated **live**. |
| **T135-3** | **P2** | The widened sweep pattern is complete over *this tree today* (verified) but is **not a detector**: 10 alternate spellings of the same vacuous shape all fire on empty input and the pattern catches 1 of 10. Its own "WHAT THIS SWEEP CANNOT FIND" list omits precisely the class that already cost two P0s — P-26 in the same file that fixed a P-26. |

Plus three P3 corrections (§7). Nothing here touches money math, no vector moved, and conformance is
green with the exact expected numbers.

---

## 1. Does the rescued half reproduce? **Yes — byte-identically, from a third party.**

P-28 says a rescued document is a claim. T99b claims it re-ran all six scripts under both shells and
got all ten transcripts byte-identical to the committed ones, including both live-oracle legs. That
is the hinge, so I re-ran it myself, in a **fresh `--no-local` clone at a different filesystem path**
(`/tmp/t135/clone`), not in T99b's worktree:

```
$ sh run-all.sh                                    # 5m41s
f1 sh exit 0   f1 bash exit 0   f2 sh exit 0   f2 bash exit 0
f3 sh exit 0   f3 bash exit 0   f4 sh exit 0   f4 bash exit 0
  IDENTICAL f1-sh.txt == f1-bash.txt (4297 bytes)
  DIFFERS   f2 — three lines, all the interpreter LABEL ("sh" vs "bash"); no verdict, no digest
  IDENTICAL f3-sh.txt == f3-bash.txt (6828 bytes)
  IDENTICAL f4-sh.txt == f4-bash.txt (20480 bytes)
  sweep exit 0 ; provenance verify exit 0
ALL FOUR PROOFS CLOSED under both shells; sweep exit 0; provenance verify exit 0.

$ diff -rq /tmp/t135/committed /tmp/t135/clone/.softhouse/capture/pathb/t99/out
$ echo $?
0
```

**10 of 10 committed transcripts reproduced byte-identically**, including the two live-oracle legs
(1b and 3f-green). The path normalisation in `run-all.sh:35-40` is what makes this portable, and it
works: a different repo root reduces to `<REPO>` and the digests, counts and verdicts are unchanged.

I also independently re-derived the four `PIN_PREFIX_*` digests against `git archive ab2de89`, with
**Go** (`crypto/sha256`, repo-local toolchain, P-30) — an implementation the rig does not contain:

```
t36/recapture.sh          efccb0a4323628b45952a7e2dff12590e7dce3a2705ae66aa73aa53cd3b0d7d7  MATCHES pin
t36/preconditions.sh      7c68f2dcc539a27648f2fb0623927c1231c9b3729bdfb77eb01bd90e67ae876b  MATCHES pin
t80/forbidden-sentence.sh 71142e40b4af9ec873f0eca6a3ecb60d18033f2f0d37f75a2b29ffc4b9bf798f  MATCHES pin
t36/attest.py             0edced54a750fa17981af5a287b413c1a8298680ce2b7d4952087a14e61ce780  MATCHES pin
```

and confirmed `git diff --stat ab2de89 main -- .softhouse/capture/pathb` is empty, so the "before"
side really is `main`'s live bytes and not a stale ref.

**Ruling: the rescued bytes are admissible evidence.** (Their `[VERIFIED]` badges are a separate
question — see §7.3, where one of the inherited claims turns out to be false on this host.)

---

## 2. F-5 — the finding that mattered most. Re-run on all three legs, plus a fourth.

### 2.1 The defect, reproduced on `main`'s bytes by me

`t36/preconditions.sh` on `main` (`git archive ab2de89`, sha256 `7c68f2dc…`):

* `:96-99` — `banned=$(docker inspect … 2>/dev/null | grep -icE 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver')` then `[ "$banned" = "0" ] && ok …`
* `:102-105` — `jarhits=$(docker exec … unzip -l … 2>/dev/null | grep -icE 'ojdbc|oracle-jdbc|mysql-connector|mariadb-java')` then `[ "$jarhits" = "0" ] && ok …`
* `:151-154` — `scp=$(docker exec … psql … 2>/dev/null …)` then `[ -z "$scp" ] && ok …`

With `docker` and `curl` stubbed to `exit 1` (`f5-deadtool.sh`):

```
=== main  EXIT=1
PASS lines=3
FAIL lines=18
--- the three prohibition verdicts:
  PASS  0 prohibited-engine hits in container env
  PASS  0 prohibited driver jars in fineract-provider.jar
  PASS  schema_connection_parameters is empty
```

That is starker than the handoff puts it. In a **completely dead environment**, the *only three
assertions in the whole suite that still say PASS* are the three that carry the CLAUDE.md
"PostgreSQL is the only database / Oracle Database, MySQL and MariaDB are prohibited" non-negotiable.
Confirmed P-22, on a non-negotiable.

I enumerated every assertion in `main`'s script by hand: P1, P2, P3, P4, P6-`pgdrv`, P7, P8, P9, P10,
P12, P13, P14a/b/c, P15 all fail closed on empty input. **Exactly three sites are vacuous, and T99b
found all three.**

### 2.2 RED — branch, same conditions

```
=== branch  EXIT=1
PASS lines=0
FAIL lines=21
  FAIL  prohibited-engine scan of the container env INSPECTED NOTHING: `docker inspect
        fineract-fineract-1` returned no environment at all, so a count of 0 would mean
        'not looked', not 'clean'. …
  FAIL  prohibited-driver-jar scan INSPECTED NOTHING: …
  FAIL  schema_connection_parameters check INSPECTED NOTHING: …
```

18 → 21 FAIL, 3 → 0 PASS. Matches T99b exactly.

### 2.3 GREEN — live reference oracle, both sides

```
=== branch LIVE  EXIT=0   PASS=22  FAIL=0
  PASS  0 prohibited-engine hits in container env (47 env line(s) actually scanned)
  PASS  0 prohibited driver jars in fineract-provider.jar (5406 jar entry line(s) actually scanned)
  PASS  schema_connection_parameters is empty (a row was returned and its value is the empty string)
  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.

=== main LIVE    EXIT=0   PASS=22  FAIL=0     (same 22, without the witness counts)
```

**22 PASS on both sides — nothing was weakened**, and each of the three verdicts now carries its
witness count. The 47/5406 figures reproduce.

### 2.4 POSITIVE CONTROL — with **my own** poisoned `docker`, not T99b's

`f5-positive-control.sh` delegates every call to the real `docker` except three, which it poisons
with `jdbc:mariadb://db:3306/…` in the env, `mysql-connector-j-8.3.0.jar` in the jar listing and
`serverTimezone=UTC&useLegacyDatetimeCode=false` in the tenant row:

```
=== main   POSITIVE CONTROL  EXIT=1  PASS=19  FAIL=3
=== branch POSITIVE CONTROL  EXIT=1  PASS=19  FAIL=3
  FAIL  1 prohibited-engine hits in container env (Oracle Database / MySQL / MariaDB are prohibited)
  FAIL  1 prohibited driver jars inside fineract-provider.jar
  FAIL  schema_connection_parameters = 'serverTimezone=UTC&useLegacyDatetimeCode=false' …
```

Both fire; the branch strips the bracket wrapper out of the message correctly. The fix is not
"refuse everything".

### 2.5 A fourth leg T99b did not run — **partial outage**

The realistic failure is not "docker is gone", it is "the fineract container is gone and the database
is still up". `f5-container-gone.sh` uses the **real** docker with the container name rewritten, so
the stdout/stderr/exit behaviour is docker's own:

```
=== main   CONTAINER GONE  EXIT=1  PASS=15  FAIL=7
  PASS  0 prohibited-engine hits in container env          <- vacuous
  PASS  0 prohibited driver jars in fineract-provider.jar  <- vacuous
=== branch CONTAINER GONE  EXIT=1  PASS=13  FAIL=9
  FAIL  prohibited-engine scan … INSPECTED NOTHING
  FAIL  prohibited-driver-jar scan … INSPECTED NOTHING
```

The fix holds on a shape it was not designed against. Good.

### 2.6 The second-order finding — **confirmed, and it is worse than stated**

T99's own sweep pattern was `grep -c|grep -ac|wc -l`. Run from a script (BSD grep, `LC_ALL=C`,
`sweep-pattern-check.sh`) against `main`'s `preconditions.sh`:

```
=== T99's ORIGINAL pattern
107:        | grep -c 'BOOT-INF/lib/postgresql-')

=== T99b's widened pattern
97:         | grep -icE 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver')
103:          | grep -icE 'ojdbc|oracle-jdbc|mysql-connector|mariadb-java')
107:        | grep -c 'BOOT-INF/lib/postgresql-')

=== T99b's absence-assertion pattern
98:[ "$banned" = "0" ] …   104:[ "$jarhits" = "0" ] …   153:[ -z "$scp" ] …
```

T99's sweep found **one** line — and it is the one site in P5/P6 that is *not* vacuous (`pgdrv` is a
positive-presence check). It saw neither of the two defects it existed to find. The widened pattern
catches all three. **Confirmed both ways.**

See §5 for what the widened pattern still cannot see.

---

## 3. F-1 to F-4 — each driven red against `git archive ab2de89` bytes, with my own shapes

### F-1 — resolved-path + shape + leaf + no-nesting guard

`f1-attack.sh`: nine bypass shapes, none of them in T99b's table, hermetic (`docker`/`curl` stubbed,
the guard runs before either):

| shape | main | branch |
|---|---|---|
| A1 dot component through an existing dir `t36/out/./recapture-default/sub-gerege` | ADMITTED | REFUSED |
| A2 doubled slashes `t36/out//recapture-default//sub-gerege` | ADMITTED | REFUSED |
| A3 middle component in the wrong case `t36/OUT/case-gerege` | ADMITTED | REFUSED |
| A4 **symlink at the MIDDLE component** (`out/midlink -> recapture-default`) | ADMITTED | REFUSED |
| A5 **task dir symlinked out of the tree** (`evil-task -> /tmp/...`) | ADMITTED | REFUSED |
| A6 **relative path with cwd = `t36/out`** | ADMITTED | REFUSED |
| A7 `out/` repeated: `t36/out/out/x-gerege` | ADMITTED | REFUSED |
| A8 leaf is the **bare tenant** one level down: `…/recapture-default/gerege` | ADMITTED | REFUSED |
| A9 trailing `/.` on the nested attack | REFUSED | REFUSED |
| happy `t36/out/recapture-gerege` | ADMITTED | ADMITTED |
| happy `t36/out/gerege` (bare tenant leaf) | ADMITTED | ADMITTED |

8 of 9 new shapes bypassed `main`; 9 of 9 refused on the branch; both happy paths intact.
A3's admission on `main` is worth naming: on this case-insensitive APFS volume the write **actually
landed in the real `t36/out/`** (`ls t36/out/` shows `case-gerege`), so the leaf check was adjudicating
a path that is not the path that was written.

`f1-attest-attack.sh` does the same to `attest.py`: **7 of 7 new shapes ADMITTED on main, 7 of 7
REFUSED on the branch**, including the `emiloop` capture set nested inside `recapture-default/`
(refused by containment/shape, which correctly still apply to it). Both happy paths —
`t80/out/attest-gerege` and `t36/out/emiloop` — still accepted on both sides, so the historical
`emiloop` leaf exemption is not a regression.

Guard read line by line: `recapture.sh:80-133` (resolve → containment → shape → leaf → no-nesting →
`O=$Or`, so nothing downstream receives an unadjudicated path) and `attest.py:57-95` (same five
operands via `os.path.realpath`). `W`/`D` are derived from `$0`, not from the environment, so the
evidence root is not attacker-settable.

### F-2 — PATH-proof digest instrument

**Both canary digests re-derived by five implementations, all outside the rig** (`f2-canary-digests.sh`):

```
committed canary calc-pmode2-gerege.json
  openssl / python3 / sha256sum / shasum / GO   2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154
one-character mutation (1162502.5 -> 1162502.55)
  openssl / python3 / sha256sum / shasum / GO   13ce2f4f21a1ad568b080b859682b9e995aac97712e00fcf44c6fc177d6b9ca5
```

`PIN_CANARY_SHA256` is the real thing and the rig is not grading itself.

**The cross-check compares, and it fires — with my own clever liar** (`f2-clever-liar.sh`, a liar that
answers the two KAT inputs correctly and returns the pin for everything else):

```
liar in slot 'shasum' — tools surviving the KAT: shasum(<my liar>) sha256sum openssl python3
  the liar PASSED the known-answer test (as designed)
  RESULT: REFUSED — sha256 IMPLEMENTATIONS DISAGREE on '…': shasum says '2a6621be…',
          sha256sum says '13ce2f4f…' …
control, no liar: digest=13ce2f4f… (used shasum+sha256sum+openssl+python3)
```

`sha256.sh:158` is `if [ "$_d" != "$_first" ]` — a comparison, not a print. Confirmed by reading and
by driving it. And `_sha256_path` (`sha256.sh:70-85`) is a literal table of absolute paths with no
`$PATH` lookup, so there is no resolution step to poison.

I additionally **measured** the claim T99b inherited and did not re-measure — see §7.3, where it is
false on this host but the decision it justifies is still right.

### F-3 — non-vacuous forbidden-sentence check

`f3-check.sh`, against the **real committed evidence** and against three constructed states:

```
real evidence      main: EXIT=0, OK=8 absent=19 violations=0   (no counters printed)
                 branch: EXIT=0, files inspected: 27 / carrying the sentence: 8 / violations: 0
zero files         main: EXIT=0 + "RESULT: the HALF_UP claim is never made…"   <- the false pass
                 branch: EXIT=2 "ERROR: this check INSPECTED NOTHING"
two decoy files    main: EXIT=0 + the RESULT sentence
                 branch: EXIT=2 "…NOT ONE of them contains the guarded sentence"
planted violation  main: EXIT=1 violations=1   branch: EXIT=1 violations=1
```

**T85's 27 / 8 / 0 property is intact on real evidence** and the check still fires on a planted
violation. Exit contract `0 / 1 / 2` as documented.

### F-4 — content-addressed provenance index

The design decision (index, not re-capture) is **right, and I can now show why from observation
rather than argument**: `provenance.py whence` on `t36/out/recapture-gerege/B-01-baseline-raw.json`
returns **12 records sharing those bytes**, six of them stamped `gerege`. A re-capture would have
overwritten bytes that six other capture sets are proved identical to.

`f4-check.sh`, eight tamper cases of my own against a throwaway export:

```
untampered                      exit=0  17 dirs, 111 files, 0 problems
one byte appended               exit=1  BYTES MOVED … index 713a3560…, on disk cc090147…
stamp deleted                   exit=1  MISSING FILE + STAMP REMOVED
stamp forged on an unstamped dir exit=1 UNACCOUNTED FILE (…AND IT IS A STAMP…) + STAMP APPEARED
smuggled capture directory      exit=1  UNACCOUNTED DIRECTORY
capture file deleted            exit=1  MISSING FILE
index deleted                   exit=2
index emptied of all records    exit=2  (0 dirs, 0 files, 17 UNACCOUNTED DIRECTORY)
empty tree, index present       exit=2  "INSPECTED NOTHING … This is NOT a pass."
restored                        exit=0  17 / 111 / 0
```

**`verify` cannot pass by not running**: missing index → 2, empty index → 2, nothing inspected → 2,
any problem → 1, and every green branch is a real comparison against a recorded digest
(`provenance.py:303-370`, digests computed in-process with `hashlib`, `:104-109`).

Discoverability reproduces: in place, renamed into an empty directory, and moved out of the tree with
`--index` all find the record by digest; one byte changed → NOT FOUND, which is correct.

**`emit` is deterministic**: re-emitting inside the git checkout produced a **byte-identical**
`PROVENANCE-INDEX.json`. (Outside a checkout the tier-B/C `first_commit` fields go null — `verify` is
unaffected, it reads only digests and stamp state.)

### F-6 — two predicates set by an absence, and a discarded exit code

**Item 1 — `prove-f1`'s `prefix_admitted`. Driven red on REAL bytes, not simulated.**
T99b could only exercise this at predicate level, because the digest pin refuses any mutation of the
pre-fix bytes. There is a reachable unrelated death that does the job: an invalid `TENANT` makes
`main`'s `recapture.sh` die at its identifier check, which prints `ABORT: TENANT=…` — *not* the string
`ABORT: output directory` — and creates nothing (`f6-prove-f1-predicate.sh`):

```
the run's output:
    ABORT: TENANT='bad/tenant' is not a valid tenant identifier (expected [a-z0-9_-]+).
artefacts: attack directory present=no  stamp=''

OLD prove-f1 predicate  prefix_admitted = 1   <- 1 means 'the guard let the attack through'
NEW prove-f1 predicate  prefix_admitted = 0
```

The old predicate reports "the defect reproduced" from a run that wrote nothing. The new one does not.
**Confirmed on real bytes.**

**Item 2 — `prove-f4` leg 4a** (`f6-prove-f4-abort.sh`):

```
=== against the pre-stamp commit 352f623
  EXIT=3
    T99 PROOF ABORT: 4a precondition: the pre-fix t80/out/recapture-gerege carries no
    CAPTURED-FROM-TENANT to delete, so 'both look the same afterwards' would prove nothing
=== control at the real fork point
  EXIT=0  RESULT: F-4 CLOSED — red before, green after.
```

and I verified the reason independently: `git show 352f623:…/t80/out/recapture-gerege/CAPTURED-FROM-TENANT`
→ *"exists on disk, but not in '352f623'"*.

**Item 3 — `run-all.sh` discarded the sweep's and the verifier's exit codes.** Driven red both sides
with one tampered byte in a committed capture, everything else green (`f6-runall-red.sh`):

```
=== run-all.sh as of: prefix (38c8b5f)
  RUNNER EXIT=0
    f1..f4 all exit 0 ; wrote out/sweep.txt (exit 0)
    exit 1 —   BYTES MOVED t36/out/recapture-gerege/B-01-baseline-raw.json …
    ALL FOUR PROOFS CLOSED under both shells.          <-- over a FAILING verification, at exit 0

=== run-all.sh as of: fixed
  RUNNER EXIT=1
    exit 1 —   BYTES MOVED …
    NOT CLEAN — at least one of: a proof did not close, the sweep failed, the provenance …
```

Exactly the claimed defect and exactly the claimed fix.

---

## 4. T135-1 (P1) — the P-24 recurrence. **`t99/lib.sh:25`**

```sh
PREFIX_REF=${T99_PREFIX_REF:-$(git -C "$T99" merge-base main HEAD)}
```

with the comment *"The fork point, not the moving branch"*. That is true **on the branch** and false
**on merged main** — after the merge `HEAD == main`, so the merge base of the two is the merge commit
itself, which contains the fix. This is T98's defect verbatim, and `main` already carries the lesson
in `.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh:48-63`, which states
in terms *"NOT `main:`. NOT `merge-base main HEAD`. NOT ANY COMPUTED REF … This has now failed twice"*
and refuses to run without a literal 40-hex sha in a `FORK-POINT-SHA` file.

**Measured** (`p24-scratch-merge.sh`, throwaway clone, `main` at `2f3d7d2` — it has moved several
commits since the branch forked):

```
merge result: ce53ddc Merge remote-tracking branch 'origin/softhouse/T99-pathb-lower-findings'
conflicts: 0
git merge-base main HEAD = ce53ddc…   HEAD = ce53ddc…     <- the merge commit itself

prove-f1.sh -> exit 3   pre-fix recapture.sh sha256 d122bac1… DOES NOT MATCH the pinned efccb0a4…
prove-f2.sh -> exit 3   pre-fix preconditions.sh sha256 62a4cfe3… DOES NOT MATCH the pinned 7c68f2dc…
prove-f3.sh -> exit 3   pre-fix forbidden-sentence.sh sha256 db2141e9… DOES NOT MATCH the pinned 71142e40…
prove-f4.sh -> exit 1   RESULT: F-4 (stamp-absence ambiguity) NOT CLOSED.
```

Two observations:

1. **The digest pins do their job for three of four** — they abort loudly rather than comparing the
   fixed code against itself. That is why this is P1 and not P0: the post-merge rig produces no false
   green.
2. **`prove-f4` has no pin, and it does not abort.** It runs both sides against the fixed bytes,
   observes that the defect does not reproduce, and reports **"F-4 NOT CLOSED"** — a false negative
   that a future driver would read as a regression in the very finding this branch closed.

The merge itself is clean (0 conflicts) and `main`'s pathb bytes are untouched since `ab2de89`, so
there is no content conflict — only the time bomb.

**MICRO-FIX, verified** (`p24-microfix-check.sh`, same merged clone):

```
post-merge, with T99_PREFIX_REF pinned to the literal fork sha ab2de893…:
  prove-f1.sh -> exit 0   RESULT: F-1 … CLOSED — red before, green after.
  prove-f2.sh -> exit 0   RESULT: F-2 … CLOSED — red before, green after.
  prove-f3.sh -> exit 0   RESULT: F-3 … CLOSED — red before, green after.
  prove-f4.sh -> exit 0   RESULT: F-4 … CLOSED — red before, green after.
```

Required change: replace the computed default at `lib.sh:25` with the literal
`ab2de89356986c8ed85a9d2e26c2bc86b0fb8720`, preferably as a `FORK-POINT-SHA` file next to `lib.sh`,
matching the convention already ratified on `main`. If the file is missing or not a full 40-hex sha,
abort — **no computed fallback**, per T102. Recommended additionally: give `prove-f4` a baseline
assertion of its own (e.g. that `PROVENANCE-INDEX.json` is *absent* from the prefix export), so that
it too aborts rather than reporting NOT CLOSED if the baseline is ever wrong.

---

## 5. T135-3 (P2) — the widened sweep pattern is not a detector, and does not say so

`sweep.sh:66` and `:70`:

```sh
LC_ALL=C grep -rnE 'grep -[a-zA-Z]*c[a-zA-Z]*( |$)|wc -l' …
LC_ALL=C grep -rnE '\[ "\$[a-z_]+" = "?0"? \]|\[ -z "\$[a-z_]+" \]' …
```

**Complete over this tree today: yes** — verified in §2.6, and a deliberately broader sweep of my own
(`sweep-broad.sh`: any grep counting form including split flags and `--count`, any `= / == / -eq 0`
verdict, `grep -q` as an absence test, `test -s`, and the Python-side `len()==0 / not x` shapes) over
the whole Path B tree found **no additional real vacuous-prohibition site**. Every other hit is proof
instrumentation (counting lines in a transcript, where a zero is the reported observation, not a
verdict) or already hardened — `recapture.sh:164` and `emiloop-probe.sh:33` pair their `grep -ac`
with the exit status as a second operand; `forbidden-sentence.sh:62,68` and `provenance.py:360` are
the F-3/F-4 fixes themselves.

**Complete as a detector: no.** `sweep-missprobe.sh` is ten alternate spellings of the same defect.
All ten pass vacuously on empty input; `sweep-misscheck.sh`:

```
--- the probe's own behaviour on EMPTY input (every line printed is a vacuous pass):
PASS1 … PASS10                                    <- 10 of 10 fire
--- T99b sweep grep-3 pattern A:      1 hit  (line 8 only)
--- T99b sweep pattern B:             1 hit  (line 5 only)
```

Missed: `grep -i -c` (split flags), `grep --count`, `[ "$n" -eq 0 ]`, an **uppercase** variable name,
`if ! grep -q`, `[ "x$out" = "x" ]`, `[ ${#out} -eq 0 ]`, `[ -s file ] ||`, `awk 'END{if(NR==0)}'`,
`case "$out" in "")`, `test -z`.

The sweep does carry a "WHAT THIS SWEEP CANNOT FIND" section (`sweep.sh:90-102`), and it is a good
one — but the only vacuity item it lists is about the *source* of the emptiness ("an empty SQL result,
an empty JSON array, a `for` over an unset variable"), never about the *spelling of the test*. That
is the exact class that made T99's sweep blind and cost the program two P0s. A sweep whose stated
limits omit the limit that already bit it reads as exhaustive — P-26, in the file that fixed a P-26.

**MICRO-FIX:** add to `sweep.sh:90-102` a bullet naming the spellings the patterns cannot match, and
widen the flag-cluster pattern to tolerate separated flags and `--count` and an uppercase variable.
This is documentation and pattern breadth, not a guard, so it is P2.

### P-33 check

`sweep.sh` is always invoked as `sh sweep.sh`, so its `grep` is always `/usr/bin/grep` — BSD grep
2.6.0-FreeBSD (measured with `type -a` from inside a script, never `command -v`). I ran both patterns
through the Claude Code Bash tool's `grep` (the shell function re-execing `claude` as `ugrep -I`) as
well: **identical hit sets**, so the divergence does not bite for these patterns on this input. The
tree also has **zero** files that would make a UTF-8 grep go blind (`sweep.txt` §0), and every sweep
grep is `LC_ALL=C` with `-a` where it matters. Five facts pinned: binary `/usr/bin/grep` and the
ugrep shell function, version 2.6.0-FreeBSD, locale `LC_ALL=C`, invocation from a script vs the Bash
tool, input = the pathb `.sh` corpus.

---

## 6. T135-2 (P2) — the backlog ruling, and why the transcription is **not** sufficient

T99b flags that the F-5 defect exists verbatim in
`.softhouse/capture/charges/bin/preconditions.sh:79,85,128` and
`.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh:79,85`, and rules that "the fix is a
direct transcription". **I confirm the sites and refute the ruling.**

### 6.1 The sites — confirmed, with two corrections

```
charges/bin/preconditions.sh              sha256 9256b881153d3deab2013cb9d95fae95258b68b398cdf22e5da9a8a416a46b54  183 lines
audit-t44/charges/bin/preconditions-COPY.sh sha256 9256b881153d3deab2013cb9d95fae95258b68b398cdf22e5da9a8a416a46b54  183 lines
```

* The two files are **byte-identical**. The COPY therefore has the P11 site too, at `:128` — T99b
  listed only `:79,85` for it, implying two sites where there are **three**. This is P-27 in its
  textbook form: a second copy of a document, and a claim about it that has already drifted.
* The cited lines `:79` and `:85` are the `grep -icE` lines; the **verdict** lines are `:80`, `:86`
  and `:128`. A transcriber going to `:79` finds the pipe, not the comparison.
* The three defective blocks *are* byte-identical to `main`'s pathb blocks (`diff` clean), so the
  replacement text does transcribe cleanly.

### 6.2 Why the transcription is not sufficient — **the copies are a whole hardening generation behind**

`diff charges/bin/preconditions.sh <pathb on main>` shows the charges copies predate T76, T77, T80
and T85. Three of the gaps are worse than F-5, because they are on the **ratified rounding mode**:

**(a) `charges:36` — `CANARY_EXPECT=${CANARY_EXPECT:-20925.05}`. The strongest assertion in the suite
can still be talked out of failing.** Demonstrated with a stub `curl` answering `20925.04` (what a
HALF_EVEN process returns) and `CANARY_EXPECT=20925.04` supplied by the runner
(`charges-attack-expect-override.sh` — a statement about the guard, not about the oracle):

```
  --- charges          EXIT=0
        PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)
  --- pathb-hardened   EXIT=1
        FAIL  CANARY_EXPECT was set in the environment ('20925.04') — the canary expectation is a
              CONSTANT (20925.05). Refusing to grade the arithmetic against a value supplied by the runner.
        FAIL  effective rounding-mode canary returned period-1 interest '20925.04', expected '20925.05'
```

A HALF_EVEN answer, labelled `(= HALF_UP)`, at exit 0.

**(b) `charges` has no `PIN_CANARY_SHA256` at all — T77's tautology is live.** Demonstrated
**against the live reference oracle**, tenant `gerege`, with the one-character mutation
(`charges-attack-live.sh`):

```
  --- charges          EXIT=0
        PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
      ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only.
  --- pathb-hardened   EXIT=1
        FAIL  canary request DIGEST MISMATCH — computed sha256 '13ce2f4f…' … pinned '2a6621be…'
```

`ALL PRECONDITIONS HOLD` at exit 0 from a request that is **not** a half-minor-unit tie and therefore
answers the same under HALF_UP and HALF_EVEN. The sentence certifies nothing and a reader believes it.

**(c) `charges:96` — the unbraced `'$PIN_PG_MAJOR_MINOR…'`, T85's F-2.** Under `set -u` the variable
reference runs into U+2026 and the script dies:

```
under bash: PIN<0xe2>: unbound variable
under sh:   PIN<0xe2>: unbound variable
```

so a P7 failure takes P8-P15 — including the entire rounding-mode canary — down with it.

**Ruling for T133: the transcription of the F-5 liveness operands is necessary but nowhere near
sufficient. T133 must port the whole T76/T77/T80/T85 hardening generation into
`charges/bin/preconditions.sh`, and must decide what to do with `preconditions-COPY.sh` — which under
P-27 should not exist at all.** I have not touched either file (T115 holds one; T133 is registered).

---

## 7. Smaller corrections

**7.1 The 8-shape bypass table is prose only.** T99b's headline independent-attack evidence — 8 shapes
× 2 sides against `recapture.sh` plus 5 against `attest.py` — exists nowhere in the branch as a script
or a transcript; I grepped `t99/*.sh` and `t99/out/*.txt`. P-22 says *"State the input that makes it
fail, and commit the transcript."* The **claim is true** — I re-derived a superset of it (9 shapes
against `recapture.sh`, 7 against `attest.py`, §3) — but the evidence for it is not committed.
`f1-attack.sh` and `f1-attest-attack.sh` in this review's evidence directory are offered as the
missing artefact.

**7.2 Handoff staleness.**
* The `run-all.sh` block quoted in the handoff says `IDENTICAL f3-sh.txt == f3-bash.txt (6521 bytes)`.
  The committed file is **6828** bytes; the quoted block predates commit `81beff4`. `f1` (4297) and
  `f4` (20480) are correct.
* *"`git diff --name-only main...HEAD` returns 0 files outside that tree"* is false as committed —
  the handoff itself is outside it. Measured: **1** file outside `.softhouse/capture/pathb/`, and it
  is `T99.md`. (Scope is otherwise clean; see §8.)
* 4e's summary *"(iii) moved out of the tree entirely — all three find the record by digest"*
  compresses a transcript that is more precise than the summary: the ascent **correctly fails**, and
  the digest finds the record only when `--index` is named. Reproduced both ways.

**7.3 An inherited `[UNVERIFIED]` claim is false on this host** (P-11, and P-28's corollary about
rescued badges). The handoff carries, as inherited-and-not-re-measured, the claim that
`/usr/local/bin` and `/opt/homebrew/bin` are *"user-writable on this machine and therefore correctly
excluded"* from `sha256.sh`'s candidate table. Measured (`f2-tooldir-writability.sh`, user `buv`,
uid 501):

```
  /usr/local/bin         read-only    drwxr-xr-x root wheel
  /opt/homebrew/bin      ABSENT
  /usr/local/bin: touch probe -> no      /opt/homebrew/bin: no / absent
  /usr/bin /bin /sbin /usr/sbin: all drwxr-xr-x root wheel, all read-only to this user
  /usr/bin/shasum /sbin/sha256sum /usr/bin/openssl /usr/bin/python3
  /usr/bin/awk /usr/bin/env /usr/bin/mktemp /bin/rm — all -rwxr-xr-x root wheel
```

The **exclusion decision is right** (`/usr/local/bin` is user-writable on a great many macOS setups,
and excluding it costs nothing), and every path the table actually selects is root-owned and
unwritable, so `sha256.sh`'s bounded claim holds. Only the stated *reason* is wrong on this host. Fix
the sentence; do not change the table.

**7.4 `prove-f2` cannot be proved with the oracle down.** Measured: with `T99_LIVE=0`, f1/f3/f4 exit 0
and **f2 exits 1** — *"defect reproduces on the PRE-FIX bytes: NO — this proof proves nothing"*. Both
of F-2's verdict predicates are set only inside the live legs; 2c/2d/2e are hermetic but do not feed
the verdict. This is the **right** failure mode (a skipped leg is never a pass) and the script says so,
but it means `run-all.sh` cannot go green in an oracle-down fire. Worth a line in the header.

**7.5 A conservative false refusal on a case-insensitive filesystem.** `t36/OUT/x-gerege` is refused
by the branch's shape rule (`the middle component is 'OUT', expected literally 'out'`) even though on
APFS the write would land in the real `t36/out/`. `pwd -P` preserves the typed case rather than
canonicalising it. This errs toward refusing, no recipe types `OUT`, and it forces the canonical
spelling — **not a defect**, recorded so nobody rediscovers it as one.

---

## 8. Blast radius — settled from committed evidence, not inferred

*How many committed Path B captures were taken through a `preconditions.sh` that could pass vacuously,
and does anything follow for their admissibility?*

**Structurally: all of them. Evidentially: none of them, and this is provable from bytes already in
the repository.**

Each of the three vacuous assertions reads a stream that **also feeds a co-located positive assertion
in the very same transcript**, and a positive PASS is impossible over an empty stream:

| vacuous assertion | its stream | the positive witness in the same transcript |
|---|---|---|
| P5 `banned` | `docker inspect … Config.Env` | `PASS driverClassName org.postgresql.Driver` **and** `PASS JDBC URL is jdbc:postgresql://…` |
| P6 `jarhits` | `docker exec … unzip -l <jar>` | `PASS PostgreSQL JDBC driver present in the jar` (`pgdrv ≥ 1` over the *same* listing) |
| P11 `scp` | psql join on `fineract_tenants` for `$TENANT` | `PASS tenant schema_server_port = 5432` (*same* join, *same* table, *same* tenant) |

The discriminator discriminates (`blast-discriminate.sh`), on transcripts my own red runs produced:

```
MAIN's bytes, scans had NO input:
  docker+curl dead                  P5w=0 P6w=0 P11w=0   vacuous-shaped PASS lines: 3
  fineract container gone, db alive P5w=0 P6w=0 P11w=1   vacuous-shaped PASS lines: 3
MAIN's bytes, LIVE:
  live oracle                       P5w=1 P6w=1 P11w=1   vacuous-shaped PASS lines: 3
```

Applied to every committed precondition transcript (`blast-measure.sh`):

```
.softhouse/capture/pathb   — transcripts examined: 11 ; all three witnesses present: 11
.softhouse/capture/charges — transcripts examined: 22 ; all three witnesses present: 22
```

**Ruling: no committed Path B capture was taken through a vacuous prohibition PASS. Nothing needs
re-capturing, and no capture's admissibility is affected.** The same holds for the charges tree, which
matters because that tree's script is *still* holed (§6). The bound is on the three F-5 assertions
only; it says nothing about a `docker` that answers plausibly and lies selectively, which remains open
and which T99b correctly declines to close.

---

## 9. Environment and scope

**The shared reference oracle was not disturbed.** Read before my first run and again after
everything (full `run-all.sh`, four live `preconditions.sh` runs, the F-1 live legs, and the merged
clone's runs):

```
fineract-fineract-1  State.StartedAt  2026-08-18T09:51:53.088984338Z   (byte-identical, before and after)
fineract-db-1        State.StartedAt  2026-08-17T11:30:08.172024591Z   (byte-identical, before and after)
gerege  m_loan=0   m_product_loan=21   c_configuration.rounding-mode = 4/true
default m_loan=0   m_product_loan=10   c_configuration.rounding-mode = 6/true
```

**The rounding-mode readings, checked myself and corroborated in-band.** `java.math.RoundingMode`
ordinals put `HALF_UP` at **4** and `HALF_EVEN` at **6**, so the DB rows say gerege = HALF_UP
(ratified) and default = HALF_EVEN. A DB row is not proof of the mode in force, so I read the running
JVM's own log as well:

```
Initialized rounding mode for tenant `default`: HALF_EVEN
Initialized rounding mode for tenant `gerege`: HALF_UP
```

and the arithmetic itself answered `20925.05` on the pinned half-cent tie (`= HALF_UP`). Three
independent readings agree. The distinction is load-bearing for every Path B capture and it holds.
No restart, no rebuild, no re-seed, no persisted loan; every write-shaped request was
`POST /loans?command=calculateLoanSchedule`, a pure calculation.

**Scope.**

```
$ git diff --name-only ab2de89..softhouse/T99-pathb-lower-findings | grep -cv '^\.softhouse/capture/pathb/'
1                       # .softhouse/handoff/…/T99.md — expected
$ … | grep -icE 'PIN\.json|capabilities\.json|vectors/|\.go$'
0
```

No vector JSON, no `PIN.json`, no `capabilities.json`, no Go file. Nothing promoted. `contract.go`
untouched (G-3 safe).

**P-25.** No floating-point arithmetic anywhere in the diff. The decimal literals present
(`20925.05`, `1162502.5`, `20925.045`) are canary values quoted from the oracle's own JSON and
compared as **strings**; a search for shell arithmetic over a decimal across every changed `.sh`
returns nothing, and no changed `.py` contains `float(` or float arithmetic.

**Conformance**, from this worktree:

```
    parity vectors          PASS 42   FAIL 0
    cells compared          5576 graded, 84 ungraded
    invariant violations    0
    invariant assertions    0 NOT RUN
VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576 cells compared.
```

Exactly the expected figures.

---

## 10. `[UNVERIFIED]` — what I did **not** establish

* **The 8×2 bypass table as T99b ran it.** I re-derived the *property* with nine shapes of my own and a
  superset result, but I did not reproduce T99b's specific eight, because no script or transcript for
  them is committed (§7.1).
* **`prove-f2` legs 2c/2d override `_sha256_path`**, so they exercise the cross-check *logic*, not a
  reachable injection. That is honest and unavoidable — the real injection path is closed by the
  absolute-path table, which is why there is nothing to inject through — but it means the liar legs are
  a test of the comparison, not of the instrument's reachability. My own liar run has the same shape.
* **A `docker` or `curl` that answers plausibly and lies selectively** still defeats most of the
  precondition suite. F-5 closes "0 hits because nothing was scanned"; it does not close this. The
  witness counts now printed (47 env lines / 5406 jar entries) make a one-line junk answer visible to a
  human reader, but nothing enforces them. Open, and correctly declared open by T99b.
* **`provenance.py` shells out to a bare `git`** for `first_commit` / date, so those fields are
  `$PATH`-reachable. Tier-B/C metadata; the digests are `hashlib` in-process. Not re-examined further.
* **The index is not signed.** Anyone who can edit a capture can re-run `emit`; the only trace is the
  diff of the committed JSON. Stated design; I did not test any signing property because there is none.
* **Behaviour under `dash`, `ash` or bash 5.** Measured: `/bin/sh` and `/bin/bash` are different
  binaries but both report `GNU bash, version 3.2.57(1)-release (arm64-apple-darwin25)`, so the
  sh-vs-bash comparison exercises POSIX mode vs not, not two implementations. T99b says this; it is
  correct and it bounds the identity result.
* **`m_product_loan = 21` on `gerege`.** Unchanged across every one of my runs, so nothing in this
  review created a product. Its provenance is still unestablished; nothing in T99, T99b or T135 creates
  one.
* **The HALF_EVEN limb of the canary.** I attempted the `CANARY_EXPECT` override end-to-end against the
  live `default` tenant and it could not complete: the pinned request returns **HTTP 404** there (the
  product ids do not exist on `default`). The override defect is therefore demonstrated with a stub
  `curl` (§6.2a) — a statement about the guard, not an oracle observation. T85's open item stands.
* **The tier-B/C narrative attributions in `PROVENANCE-INDEX.json`** (which script wrote which
  directory, which commit first committed it). I verified the digests by running `verify` and I verified
  `emit` is deterministic; I did not re-derive the prose from git history.

---

## 11. What must change before merge

1. **T135-1 (P1, blocking).** `t99/lib.sh:25` — replace the computed default with the literal
   `ab2de89356986c8ed85a9d2e26c2bc86b0fb8720`, ideally as a `FORK-POINT-SHA` file with no computed
   fallback, matching `T82-guard-proofs/`. Give `prove-f4` a baseline assertion so it aborts rather than
   reporting NOT CLOSED. Verified fix, §4.
2. **T135-2 (P2, hand to T133).** Correct the backlog entry: the two files are byte-identical
   (`9256b881…`), the COPY has **three** sites not two, the verdict lines are `:80,:86,:128`, and the
   transcription is **not sufficient** — those copies are the pre-T76/T77/T80/T85 generation, and the
   canary expectation and the canary request are both still unpinned. Live evidence in §6.2.
3. **T135-3 (P2).** Widen the sweep's flag-cluster and absence patterns, and add the missing bullet to
   `sweep.sh:90-102` naming the spellings the patterns cannot match.
4. **P3 (§7).** Commit the bypass-table transcript; correct `6521` → `6828` and the "0 files outside"
   sentence; correct the `/usr/local/bin` writability sentence to say what was actually measured; note
   in `run-all.sh`'s header that `prove-f2` requires the live oracle.

None of these touches money math, a vector, or a guard's correctness. The four findings, F-5 and F-6
are closed.
