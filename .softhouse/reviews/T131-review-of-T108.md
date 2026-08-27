# T131 — independent review of T108 (`softhouse/T108-grep-adjudication`, `50e8869`)

**Branch:** `softhouse/T131-review-t108`
**Reviewed:** `git diff main...softhouse/T108-grep-adjudication` (30 files, +2033 −3), handoff
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T108.md`, `MATRIX.md`, all five committed scripts.
**My own evidence:** `.softhouse/capture/t131-grep/` — eight probes, all re-runnable, all written by me.
**Oracle:** never contacted. No container, no POST, no vector JSON, no `PIN.json`, no `capabilities.json`,
no `nexus/`, no `conformance.sh` edit, no `patterns.md` edit, no `tasks.json` edit. Nothing promoted.

---

## VERDICT: **MICRO-FIX**

**The ruling holds.** I re-derived the load-bearing claim by four independent methods and it survives all
four. The 360-cell matrix reproduces **byte-identically** from the committed generator. Both withdrawals
(T80 vindicated, T91's non-reproduction withdrawn) are correct and I confirmed each by re-reading T91's own
committed bytes. T107's ugrep limb is vindicated and C-7 should be retired. **F-T108-1 is real, I
demonstrated it myself on the true pipe shape, and I rule it LATENT — not a live break.**

Six defects, none of which changes the ruling, two of which have **already propagated into `patterns.md`
P-33 on `main`** and should be corrected there:

| id | sev | one line |
|---|---|---|
| **F-T131-1** | **P2** | `command -v` does **not** bypass shell functions. Asserted three times (T108 table, §3.3, P-33 ×2 on `main`). Proven false by construction. |
| **F-T131-2** | **P2** | The Bash-tool `grep` has a **second** silent-miss mode the ruling never states — `--ignore-files`. **Neither token fixes it.** Live in this repo: sibling worktrees are invisible to a repo-root `grep -r`. |
| **F-T131-3** | P3 | "`LC_ALL=C grep -qaF` … is the **only** cell correct against both tools" is false; `-qa` and `-al` are equally correct. The true statement is stronger. |
| **F-T131-4** | P3 | The matrix's own classifier can only score a silent miss that prints `0`. ugrep's 72 wrong cells print **nothing** and land in `OTHER`, so the headline `SILENT-MISS: 12` excludes the *more* silent failure. |
| **F-T131-5** | P3 | "13 shapes × 4 tools × 3 locales × 2 flag sets = 360" does not multiply (= 312). |
| **F-T131-6** | P3 | P-31: T108 authors a change to `tasks.json`. It merges clean **today** (verified), but `main` edited that file in **6** commits since the fork point. Luck, not design. |

---

## 1. The two-programs ruling — attacked four ways, holds four ways

### 1.1 `type -a`, in the Bash tool

```
$ type -a grep
grep is a shell function from /Users/buv/.claude/shell-snapshots/snapshot-zsh-1787270426748-3up36x.sh
grep is /usr/bin/grep

$ grep --version | head -1
ugrep 7.5.0 aarch64-apple-macosx +neon/AArch64; -P:pcre2jit; -z:zlib,bzip2,zstd,brotli,7z,tar/pax/cpio/zip

$ command grep --version
grep (BSD grep, GNU compatible) 2.6.0-FreeBSD
```

### 1.2 The same three probes from inside a script

`sh /tmp/t131-probe1.sh` **and** `bash /tmp/t131-probe1.sh`, identical output:

```
grep is /usr/bin/grep
/usr/bin/grep
grep (BSD grep, GNU compatible) 2.6.0-FreeBSD
```

Shell functions are not exported to children. **VERIFIED.**

### 1.3 The function itself, read from the snapshot

`declare -f grep`, verbatim, load-bearing lines:

```sh
local _cc_bin="${CLAUDE_CODE_EXECPATH:-}"
[[ -x $_cc_bin ]] || _cc_bin=/Users/buv/.local/bin/claude
ARGV0=ugrep "$_cc_bin" -G --ignore-files --hidden -I \
    --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg \
    --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl ${1+"$@"}
```

`argv[0]=ugrep` re-exec of the `claude` binary, `-I` hard-coded. **VERIFIED.**
`CLAUDE_CODE_EXECPATH=/Users/buv/.local/share/claude/versions/2.1.233`; `command -v ugrep` → empty, exit 1.
**There is no standalone `ugrep` binary. VERIFIED.**

> **Detail T108's ruling omits, and it matters — see F-T131-2.** `-I` is not the only hard-coded flag.
> `--ignore-files` and six `--exclude-dir` flags are hard-coded beside it. T108's own `run-matrix.sh:28`
> names `--ignore-files` in a comment; the **ruling, the handoff table and P-33 all drop it**.

### 1.4 By observing the two behaviours differ — the decisive test

Same file (`corpus/before.txt`: `line1 ok\nPIN_PG_MAJOR_MINOR\xe2: unbound variable\nline3 ok\n`),
same pattern, one typed into the Bash tool and one run from a script:

| invocation | output | exit |
|---|---|---|
| `grep -c 'unbound variable' before.txt` *(Bash tool → ugrep `-I`)* | **nothing at all** | 1 |
| `grep -ac …` *(Bash tool)* | `1` | 0 |
| `LC_ALL=C grep -c …` *(Bash tool)* | **nothing at all** | 1 |
| `/usr/bin/grep -c …` UTF-8 *(script)* | `0` | 1 |
| `/usr/bin/grep -ac …` UTF-8 *(script)* | `0` | 1 |
| `LC_ALL=C /usr/bin/grep -c …` *(script)* | `1` | 0 |

**`0` versus *nothing at all* is the fingerprint** — two different programs, and their mitigations are
exactly swapped. `.softhouse/capture/t131-grep/run-bsd.sh` is the full 24-cell BSD sweep:

```
BSD  before     en_US.UTF-8  -c   out='0'  exit=1      BSD  before     C  -c   out='1'  exit=0
BSD  before     C.UTF-8      -ac  out='0'  exit=1      BSD  after      *  *    out='1'  exit=0
BSD  otherline  *            *    out='1'  exit=0      BSD  clean      *  *    out='1'  exit=0
```

BSD moves with the **locale** and not with `-a`; blind only when the byte is **before the match, same line**.
ugrep skips the whole file on `before`, `after` **and** `otherline` alike — the positions BSD survives.
**The two failure modes are genuinely orthogonal, so both tokens are load-bearing. RULING CONFIRMED.**

### 1.5 The T107b corollary — confirmed, but for one reason not two

T107b's own review states its 18 cells used `clean.txt`, `badutf8.txt` (*sentence* + `\xff\xfe` + `\xc3\x28`)
and `withnul.txt` (*sentence* + `\x00`) — **all three put the poison AFTER the match**, the one position BSD
grep survives (my `after.txt` row above). *N*-of-*N* green with the failing shape absent. **T108 is right.**

T107b also reports `grep --version` → *BSD grep* and `command -v grep` → `/usr/bin/grep`. In the Bash tool
`grep --version` prints **ugrep 7.5.0**. So T107b must have run from a script — which is exactly T108's
first reason, and it is sufficient on its own. **T108's second reason is wrong: see F-T131-1.**

---

## 2. The matrix — re-run from the committed generator

Copied the rig to a scratch directory, deleted `out/matrix.tsv`, re-ran:

```
$ bash run-matrix.sh
cells run:     360
SILENT-MISS:   12
LOUD-MISS:     0

$ diff .softhouse/capture/t108-grep/out/matrix.tsv <re-run>/out/matrix.tsv
IDENTICAL: 361 lines byte-for-byte
```

`gen-corpus.py` also **regenerates all 13 corpus files byte-identically** (`diff -r`, clean).

My own cross-tab of the 360 rows — not T108's summary, my `awk` over the TSV:

| tool | locale | `-c` | `-ac` |
|---|---|---|---|
| `bsd` | `C.UTF-8` / `en_US.UTF-8` | 12 OK / **3 SILENT-MISS** | 12 OK / **3 SILENT-MISS** |
| `bsd` | `LC_ALL=C` | 15 OK | 15 OK |
| `ccfn` and `ugrepGI` | all three | 3 OK / **12 blind** | 15 OK |
| `ugrepG` (control) | all three | 15 OK | 15 OK |

**Every claim in T108 §2 confirmed.** BSD rows move with locale, never with `-a`; ugrep rows move with `-a`,
never with locale; the control is clean in all 30 cells.

The 12 BSD silent misses are exactly `s01` (`0xFF` before match), `s06` (`0xE2` before match) and
`t80-exact-repro`/`unbound variable`, × 2 UTF-8 locales × 2 flag sets — **all with `stderr=<none>` and
`exit=1`.** On `t80-exact-repro` the other two patterns are fine (`^  PASS` → the true **3**, all six cells),
which is precisely why T80's "a file" is wrong and "the rest of a line" is right.

**F-T131-4.** The classifier only scores `SILENT-MISS` when `got == "0"`:

```sh
elif [ "$got_clean" = "0" ] && [ "$exp" != "0" ] && [ -z "$err" ]; then verdict=SILENT-MISS
```

ugrep prints **nothing**, so its 72 wrong cells (`got=<empty>`, `exit=1`, `stderr=<none>`) fall through to
`OTHER`. The headline `SILENT-MISS: 12` therefore **excludes the more silent of the two failure modes.**
T108's per-tool table does disclose the 12-blind, so this is not concealment — but the headline number is the
one that travelled into the commit message, into the driver's `main` commit, and into my brief. P-22 in
miniature: a counter that cannot count the worst case.

**F-T131-5.** `13 × 4 × 3 × 2 = 312`, not 360. The real count is 360 because `t80-exact-repro` carries three
patterns → **15 shape-pattern combinations × 24**. State it that way.

---

## 3. Shapes T108 did not test

Four new fixtures, run through the **actual guard shape** (`perl … | grep -Eq`), plus one structural probe.
`.softhouse/capture/t131-grep/probe-extra-shapes.sh`, `probe-stdin.sh`, `probe-ignorefiles.sh`.

| shape | UTF-8, bare guard | verdict |
|---|---|---|
| **X1** float **both sides** of the poison, same line | FLOAT FOUND | a float **left** of the byte still fires — **narrows the hole** |
| **X2** valid em dash `e2 80 94` before the float | FLOAT FOUND | valid multibyte is harmless — the shape that actually exists in the store |
| **X3** poison **inside** a JSON string, float outside | FLOAT FOUND | `perl` strips the whole string literal, poison with it — **a second, accidental layer** |
| **X4** **truncated** em dash `e2 80` outside a string | **clean — SILENT PASS** | the realistic corruption path |

**X3 and X4 are the two that matter for the latent-vs-live ruling, and T108 measured neither.**

**Pipe vs file.** T108's whole matrix uses file arguments. The money guard reads **stdin**. I re-ran the
guard's exact `perl -0pe … | LC_ALL=$loc grep -Eq …` pipeline across 3 locales × {`-Eq`, `-aEq`, `-Eqa`}:
the blindness is **identical on a pipe**, `-a` is inert in every cell, `LC_ALL=C` fixes every cell.
The ruling is unaffected — but the matrix did not cover the shape its own headline finding lives in.

---

## 4. F-T108-1 — verified, and ruled **LATENT**

**The finding is real.** Both call sites are bare `grep -Eq` reading from a pipe
(`.softhouse/conformance.sh:184`, `:201`), `conformance.sh` **sets no locale anywhere** (`grep -n` for
`LC_ALL|LANG=|LC_CTYPE|setlocale` → zero hits) and the ambient locale is `LANG=C.UTF-8`, `LC_ALL=` unset.
**So the guards run in a UTF-8 locale, in a script, against BSD grep — the blind combination.**

Demonstrated by me, on a scratch copy, on the pipe shape:

```
PIPE  vec-float-poisoned   C.UTF-8      grep -Eq    -> clean - PASSES     *** SILENT PASS ON A FLOAT ***
PIPE  vec-float-poisoned   C.UTF-8      grep -aEq   -> clean - PASSES     *** -a DOES NOT HELP ***
PIPE  vec-float-poisoned   en_US.UTF-8  grep -Eq    -> clean - PASSES
PIPE  vec-float-poisoned   C            grep -Eq    -> FLOAT FOUND (correct)
PIPE  vec-float-clean      *            *           -> FLOAT FOUND (correct)   [the control fires]
```

This guards the **first non-negotiable in CLAUDE.md**. T108's proposed fix is correct.

### 4.1 Latent, not live — and here is the measurement

`probe-vector-bytes.py` (**driven RED first** against a deliberately poisoned scratch file, and GREEN against
a clean one, before being pointed at the store — my first attempt at this scan was a shell one-liner whose
bracket expression errored on **every** file and still printed `0 dirty`, a textbook P-22 vacuous guard; I
threw it away).

```
vector json files scanned: 49
files with any byte outside TAB/LF/CR/0x20-0x7e: 5
ANY INVALID UTF-8 BYTE ANYWHERE IN THE COMMITTED VECTOR STORE: False
```

**Ruling: LATENT.** No committed vector can trigger it today. But the received reason is wrong and should not
be relied on:

1. **The store is NOT ASCII.** Five committed vectors carry `e2 80 94` (U+2014 EM DASH), 15 line-occurrences:
   `vectors/capabilities.json` (9 lines), `vectors/_selftest/SELFTEST-01-two-period-zero-rate.json:17`,
   `vectors/loanschedule/REFUSE-01-…:17`, `REFUSE-02-…:17`, `REFUSE-03-…:6` (2). **T119's "all 47 `case_id`s
   are ASCII" does not extend to file contents** — I checked, and it does not.
   `nexus/internal/apps/loanschedule` is worse: **18 of 21 `.go` files** carry the same sequence.
2. **They are all VALID UTF-8**, so BSD grep decodes them and the guard fires normally (my X2 shape).
   *That* is the only reason the guard is not blind today.
3. **A second, accidental layer exists for JSON** and nobody has written it down: every one of those 15
   occurrences sits **inside a string literal**, which `perl -0pe 's/"(\\.|[^"\\])*"//g'` deletes before grep
   sees it (my X3 shape). Well-formed JSON can carry non-ASCII **only** inside strings, so a valid-JSON
   vector is doubly protected. **This layer does not exist for `guard_no_float_in_harness`, which strips
   comments only** — a Go string literal is not stripped. Go source must be valid UTF-8 to compile, so that
   guard is protected by the compiler instead, which is also not by design.
4. **The distance to a live break is one corrupted byte.** X4: truncate an existing `e2 80 94` to `e2 80`
   outside a string and the guard silently passes. Nothing in the pipeline enforces ASCII, validates UTF-8,
   or fails closed on an unreadable vector.

> **Latent, by accident of content, in a guard that fails OPEN.** Fix it. The fix does not depend on the
> answer, which is exactly what T108 said.

**Exact replacement text for T132 is in the handoff.** I did not touch `conformance.sh`.

---

## 5. F-T131-2 — the second silent-miss mode, **which neither token fixes**

The ruling's payoff sentence — *"`LC_ALL=C grep -a` is right and both tokens are load-bearing"* — is true and
**not sufficient**. `--ignore-files` is hard-coded into the same shell function as `-I`, and under **recursion**
it silently drops any path matched by an ignore file. Controlled fixture (`probe-ignorefiles.sh`):

```
/usr/bin/grep -arl  → visible.txt  AND  ignored.txt      (control: both)
grep -rl            → visible.txt only            (Bash tool)
grep -arl           → visible.txt only            -a does NOT help
LC_ALL=C grep -arl  → visible.txt only            neither token helps
```

An explicitly **named** file is still scanned; the skip bites on **descent** from the directory holding the
ignore file. The live consequence in this repo, where `.gitignore` carries `.claude/worktrees/` and
`.softhouse/toolchain/`:

```
# ARM 1 -- Bash-tool grep, start point "."
$ cd /Users/buv/gerege-nbfi && grep -rl '<canary>' .
exit=1                                        <-- NOT FOUND.  The string exists.

# ARM 2 -- BSD grep with BOTH hardening tokens, SAME start point "."
$ cd /Users/buv/gerege-nbfi && LC_ALL=C command grep -arl '<canary>' .
./.claude/worktrees/agent-…/.softhouse/capture/t131-grep/out/canary.txt
./.claude/worktrees/agent-…/.softhouse/reviews/T131-review-of-T108.md
exit=0                                        <-- FOUND, twice

# control -- move the start point below the ignore file and ARM 1 recovers
$ cd /Users/buv/gerege-nbfi && grep -rl '<canary>' .claude
.claude/worktrees/agent-…/.softhouse/capture/t131-grep/out/canary.txt
```

**Same string, same start point, same moment, opposite answers** — the two arms differ only in which
program runs, and the hardened `LC_ALL=C … -a` arm is the one that sees the file. `out/repo-root-ab.txt`.

Two details worth keeping. ARM 2 took **over 120 s** across the 135 MB tree and had to be backgrounded,
while ARM 1 returned "not found" immediately: **the fast wrong answer is the dangerous one**, and an agent
under time pressure will prefer it. And ARM 2's second hit is **this review**, which quotes the canary — so
the sweep an auditor would run to find restatements of a claim is precisely the sweep that cannot see them.

**An agent typing `grep -r` at the repo root cannot see any sibling worktree** — which is exactly where every
census, sweep and P-26 restatement-hunt needs to look, and exactly the kind of task that concludes "zero hits".
T108's §6.3 honestly lists what its sweep could not find and **this is not on the list**; if its lexical sweep
was run recursively from the repo root through the Bash tool, its own coverage claim is narrower than stated.
`[UNVERIFIED]` — I did not attempt to reconstruct how T108 ran its sweep.

**Consequence for the standing rule:** `LC_ALL=C grep -a` remains right for **content** in a rig. For a
**recursive** grep typed by an agent it is not enough — add `--no-ignore` (ugrep) or use
`LC_ALL=C /usr/bin/grep -ar`, and prefer naming paths explicitly. Routed to the driver for P-33.

---

## 6. F-T131-1 — `command -v` does not bypass shell functions

T108 asserts it three times, and it has already reached `main`:

* handoff §1 ruling table, row 3: *"`command grep`, `command -v grep`, `/usr/bin/grep` | BSD grep — the
  function is **deliberately bypassed**"*
* handoff §3.3: *"it used `command -v ugrep` / `command -v grep`, which **deliberately bypass shell functions**"*
* proposed P-29 clause 1, **landed on `main` as P-33** at `patterns.md:645` (table row) and `:655`
  (*"T107b used `command -v` and ran from a script: **both blind to a shell function by construction**"*)

Measured (`probe-commandv.sh`), by construction, in both shells:

```
bash -c 'foo(){ :; }; command -v foo'    -> foo          # reports the FUNCTION
zsh  -c 'foo(){ :; }; command -v foo'    -> foo          # reports the FUNCTION
bash -c 'grep(){ echo FUNCTION RAN; };
         grep --version'                 -> FUNCTION RAN
         command grep --version'         -> grep (BSD grep, GNU compatible) 2.6.0-FreeBSD
         command -v grep'                -> grep         # NOT /usr/bin/grep
```

And in the live Bash tool: `command -v grep` → **`grep`**, not `/usr/bin/grep`.

POSIX requires `command -v` to report functions. **`command <cmd>` bypasses; `command -v <cmd>` does not.**
The operative reason T107b was blind is that it ran **from a script**, which T108 also gives and which is
sufficient. The *rule* P-33 draws — *"use `type -a`, never `command -v`, when the question is which program
runs"* — is **correct and worth keeping**, because `command -v` on a function returns a bare name that names
no program. Only the stated mechanism is wrong.

This is the same defect class T108 convicted T80 of — **right conclusion, wrong reason, propagated into a
durable file.** P-11. Correction text in the handoff.

---

## 7. The two withdrawals — both correct

### 7.1 T80 substantially vindicated — CONFIRMED

Reproduced the diagnostic from first principles (`probe-t80-bash.sh`): a two-line script with an unbraced
`$PIN_PG_MAJOR_MINOR…` under `set -u`. Hexdump of bash's own stderr:

```
… 4d 49 4e 4f 52  e2  3a 20 75 6e 62 6f 75 6e 64 20 76 61 72 69 61 62 6c 65 0a
   M  I  N  O  R  ^^   :     u  n  b  o  u  n  d     v  a  r  i  a  b  l  e
                  a LONE 0xE2 — invalid UTF-8, BEFORE the match, SAME line
```

```
/usr/bin/grep -ac 'unbound variable'          -> 0   exit=1
LC_ALL=C /usr/bin/grep -ac 'unbound variable'  -> 1   exit=0
```

**T80's quoted numbers reproduce exactly.** Only the summary clause over-reached — and it over-reached into
the *other* tool's failure mode, which is the whole point of the ruling. **CONFIRMED.**

The correction applied to `T80.md:296-322` is well made: **struck, not deleted**, with a boxed
`[T108 CORRECTION C-T108-1]` stating what reproduces, what does not, and that the hardening must not be
reverted. Nit: with the strike applied the host sentence is grammatically broken ("in a UTF-8 locale , and
returns **0**"); the box immediately below repairs the meaning, so I do not require a change.

### 7.2 T91's non-reproduction withdrawn — CONFIRMED, both reasons, from T91's own bytes

`softhouse/T91-preconditions-copy:.softhouse/capture/t91/prove-guards.sh`:

```python
73:  j = b.find(b'\n', i)                          # j indexes the newline ENDING the matched line
74:  open(p,'wb').write(b[:j] + b'\xff\xfe' + b[j:])   # poison lands AFTER the match, at EOL
```
```sh
79:  LC_ALL=C /usr/bin/grep  -qF 'PASS  effective rounding mode canary' …
81:  LC_ALL=C /usr/bin/grep -aqF 'PASS  effective rounding mode canary' …
87:  if command -v ugrep >/dev/null 2>&1; then        # never true: no ugrep binary
```

**Reason 1 verified** — line 73/74, poison after the match; my `after.txt` row shows BSD matches that shape in
all six cells. **Reason 2 verified and it is the instructive one** — lines 79 and 81 are **both** `LC_ALL=C`.
*A test of whether `LC_ALL=C` matters, run with `LC_ALL=C` in both arms, cannot answer the question.* Even had
the byte been positioned correctly, both arms would have matched. T108's cited line numbers are exact.

T108's `replicate-t91-g4.sh` re-run on my branch reproduces its published table exactly, including the one
cell nobody ran: `t80-shape / utf8 / -aqF → exit 1 ABSENT (WRONG)`.

### 7.3 T107 vindicated, C-7 retired — CONFIRMED

`command -v ugrep` → empty, exit 1; nothing named `ugrep` on the host. **T107b's search was correct.** Its
*inference* was not: ugrep is reached at `ARGV0=ugrep $CLAUDE_CODE_EXECPATH`, and `grep --version` in the Bash
tool prints `ugrep 7.5.0`. T107's observation reproduces exactly and now has committed evidence.
**C-7 should be retired**, with the caveat that the retirement box's `command -v` clause needs F-T131-1
applied. Routed text in the handoff.

### 7.4 The three routed rig-comment sites — all confirmed to carry the wrong reason

| site | current text | correct? |
|---|---|---|
| `capture/pathb/t36/recapture.sh:86-87` | "silently fails to match **ANY line in a file**" | **wrong** — per line |
| `capture/pathb/REPRODUCE.md:280-281` | "silently matches **nothing** in a file" | **wrong** — per line |
| `capture/pathb/t80/prove-f2.sh:31-37` | "BSD grep suppresses matches it considers **binary**" + "cannot match a line … **at all**" | **wrong twice** — binary-suppression is ugrep's behaviour, not BSD's; and BSD matches everything left of the byte |

T108's replacement text for all three is accurate. Note `recapture.sh:90` runs in a **script**, so its `-a` is
inert and `LC_ALL=C` is the load-bearing token there — T108's proposed comment says exactly that.

**F-T131-3.** T108 §2: *"`LC_ALL=C grep -qaF` … is the **only** cell correct against both tools."* Its own
`probe-flags.sh` §B refutes it — under `LC_ALL=C`, **`-qa`, `-qaF` and `-al` are all correct against both**.
The true statement is stronger and should replace it: **any form carrying both `LC_ALL=C` and `-a` is correct
against both tools; no form missing either token is.**

---

## 8. `tasks.json` — P-31

T108 authors a **2-line** change: `/tasks/81/note` (T80) and `/tasks/92/note` (T91), each a raw-string
`|| T108 RULING …` append. I verified it is **strictly additive and nothing else** by diffing the merge result
structurally, not by reading the diff:

```
merged tasks.json parses as valid JSON: True
task count main = 136   merged = 136
ids only in merged: []          ids only in main: []
tasks differing: ['T80', 'T91']     T80 field note 3736 -> 4784 ; T91 field note 3926 -> 5038
T131 present: True   T132 present: True
```

`git merge-tree --write-tree main softhouse/T108-grep-adjudication` → **rc=0, clean**, "Auto-merging
.softhouse/tasks.json". `main`'s own T131/T132 registration survives. `main` does **not** already carry these
appends (`grep -c 'T108 RULING'` on `main:.softhouse/tasks.json` → 0), so they are not duplicates.

**Ruling: safe to merge.** But P-31 is not satisfied — it says a worker branch should author **zero** change
to an orchestrator file, and `main` has edited `tasks.json` in **six** commits since T108's merge-base
`6d2a1e9` (`e35ea7b`, `fdcdf09`, `9cf1f90`, `79a67d1`, `9027f00`, `f7e3d59`). It merged clean because those
six touched other task entries. **That is luck, and P-31 exists because the luck runs out.** The note content
is worth keeping — the right shape next time is to route the two note strings to the driver exactly as T108
routed `conformance.sh`, not to author them.

*(This branch authors no change to `tasks.json`, `patterns.md`, `program.json` or `conformance.sh`.)*

## 9. The sweep's stated limits

T108 §6.3 is honest and I confirmed the substance of the ones I could test. Its best limit is the one it
cannot fix: **the three worker briefs that repeated the claim are not files and cannot be corrected** — the
handoff and the two `tasks.json` notes are the only durable record a future brief-writer will meet. That is
correct, it is the right thing to have written down, and it is now *four* briefs, because **mine repeated the
`command -v` error too** (F-T131-1) — which is exactly the propagation mechanism T108 described, observed once
more, one layer out.

Two limits I add: **the `--ignore-files` blind spot is not on the list** (§5), and a recursive Bash-tool sweep
from the repo root **cannot see any sibling worktree**, so any "~100 other branches / 180 worktree refs"
coverage claim made with such a sweep is narrower than it reads.

## 10. Ruling on the proposed pattern

**Approve the substance; the driver has already landed it as P-33** (`patterns.md:632-661` on `main`,
renumbered from T108's P-29, which was taken). The failure story, the "nobody lied" framing, the
opposite-mitigations table and the two corollaries (*never run both arms under the mitigation under test*;
*N-of-N green refutes nothing if the failing shape is absent*) are all correct and well earned.

**Three corrections to P-33 as landed** (I did not edit `patterns.md`; text in the handoff):
1. `:645` table row — `command -v grep` does **not** resolve to BSD grep (F-T131-1).
2. `:655` — T107b was blind because it ran **from a script**; `command -v` is not a second reason.
3. Add `--ignore-files` to the ugrep row (F-T131-2), because the pattern's standing consequence
   ("`LC_ALL=C grep -a`, both tokens, always") is **not sufficient for a recursive grep** and the pattern
   currently reads as if it were.

The Rule paragraph's *"use `type -a`, never `command -v`"* is correct and stays.

---

## 11. `[UNVERIFIED]` register — mine

* **How T108 actually ran its lexical sweep** (Bash tool vs script, from which root). Decides whether its
  §6.3 coverage claim is affected by F-T131-2. Not reconstructible from the branch. `[UNVERIFIED]`
* **GNU grep** — still not measured; there is none on this host and I installed nothing. T108's `[UNVERIFIED]`
  stands and its documented loud-miss behaviour must not be cited from either of our evidence sets.
* **Any non-macOS environment, including CI.** One macOS 26.5.1 arm64 host, ambient `LANG=C.UTF-8`.
  `[UNVERIFIED elsewhere]`
* **ugrep/claude version stability** — ugrep 7.5.0 inside `claude` 2.1.233 (`CLAUDE_CODE_EXECPATH=
  …/versions/2.1.233`). Changes with the CLI. `[UNVERIFIED across versions]`
* **Why `s05` escapes ugrep's binary heuristic** — reproduced (OK in all 6 of its ugrep `-c` cells), still
  unexplained. `[OBSERVED, UNEXPLAINED]`
* **That T80's session carried this same shell function.** Same inference as T108's; snapshot not retained.
  Does not affect the ruling. `[UNVERIFIED]`
* **Whether an invalid byte could reach a committed vector by any real path** (capture scripts, Go JSON
  encode, editor). I measured that none has, and that the store is not ASCII, and that a truncated existing
  sequence would do it. I did **not** audit the write paths. `[UNVERIFIED]`
* **The `--exclude-dir` flags** (`.git`, `.svn`, `.hg`, `.bzr`, `.jj`, `.sl`) — read from the function
  definition, not exercised. `[UNVERIFIED]`
* **No money math, no Go build, no vector run this task.** `bash .softhouse/conformance.sh` → **PASS exit 0,
  42 parity vectors, 5576 cells graded, 0 invariant violations, 0 harness errors** — recorded as an
  unchanged-tree control only; this branch contains no Go and touches no vector. The oracle was never
  contacted (this task needs none).
