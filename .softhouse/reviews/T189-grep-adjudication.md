# T189 — adjudication: the grep invalid-byte claim at `fire-program.sh:224`

**Status: SETTLED.** The dispute is resolved, and it is resolved **without anyone having been wrong
about what they saw**. All four prior attempts measured correctly. Two of them measured **one
program** and two measured **a different program**, and the record then compared the results as if
they were four measurements of the same thing.

**One-line verdict.** The discriminator is **which program the token `grep` names** — the Claude Code
`grep` **shell function**, which re-execs the `claude` binary as **ugrep 7.5.0 with `-I` hard-coded**,
versus `/usr/bin/grep` (BSD 2.6.0-FreeBSD). It is **not** the OS build, **not** the locale, **not**
seekable-vs-pipe on its own, and **not** invalid-UTF-8-vs-NUL on its own — though byte class and input
shape are real *secondary* axes whose effect differs per implementation. The mitigating flag is
**`-a`**, which is already present on the live line.

---

## 1. The apparatus, pinned (P-33's five axes, all five recorded)

| axis | value |
|---|---|
| OS | macOS `ProductVersion: 26.5.1`, `BuildVersion: 25F80`, arm64 [VERIFIED: `sw_vers`, `uname -m`] |
| binary A | `/usr/bin/grep` → `grep (BSD grep, GNU compatible) 2.6.0-FreeBSD` [VERIFIED: `/usr/bin/grep --version`] |
| binary B | the `grep` **shell function** from `/Users/buv/.claude/shell-snapshots/snapshot-zsh-1787317182354-elwb1c.sh`, which runs `exec -a ugrep "$CLAUDE_CODE_EXECPATH" -G --ignore-files --hidden -I --exclude-dir=… "$@"` → **`ugrep 7.5.0 aarch64-apple-macosx`** [VERIFIED: `type -a grep`, `declare -f grep`, and `exec -a ugrep $CLAUDE_BIN --version`] |
| `CLAUDE_CODE_EXECPATH` | `/Users/buv/.local/share/claude/versions/2.1.233` [VERIFIED: `printenv`] |
| locale | swept `C`, `C.UTF-8`, `en_US.UTF-8`, `POSIX` |
| invocation path | `type -a` (not `command -v` — P-33's correction), plus absolute-path calls and an exact replica of the wrapper's argv |
| input shape | file argument · `<` redirection · anonymous pipe |
| pattern | **extracted** from the live line, never retyped (P-46): `sed -n '224p' … \| sed -e "s/.*grep -av '//" -e "s/'.*//"` → `^?? \.softhouse/LOCK$` (21 bytes, `od -c`-confirmed) |

Evidence: `.softhouse/reviews/T189-probe/` — `matrix.sh` + `matrix-out.txt` (124 cells),
`provenance.sh` + `provenance-out.txt`, `reachability.sh` + `reachability-out.txt`,
`hardening.sh` + `hardening-out.txt`, `tally.sh`.

**The `-I` is the whole story.** Extracted from the wrapper (P-46, `declare -f grep`):

```
exec -a ugrep "$_cc_bin" -G --ignore-files --hidden -I --exclude-dir=.git … ${1+"$@"}
```

`-I` is ugrep's *ignore binary files* flag. On a file it can classify as binary, ugrep with `-I`
**skips the entire file** and exits 1 — printing nothing. That is, byte for byte, the symptom T157
reported.

---

## 2. It reproduced accidentally, in vivo, mid-task

Before any analysis, this very adjudication tripped the bug on its own output file. Same file, same
pattern, two commands:

```
$ /usr/bin/grep -c "^IMPL=" .softhouse/reviews/T189-probe/matrix-out.txt
124
usrbin_rc=0

$ grep -c "^IMPL=" .softhouse/reviews/T189-probe/matrix-out.txt
wrapper_rc=1            # <-- nothing printed at all
```

`matrix-out.txt` contains the poison bytes echoed back in the cell dumps, so the wrapper's `-I`
classified it binary and skipped it whole. **Total silent suppression, exit 1** — the disputed
behaviour, reproduced without trying, from a bare `grep`. [VERIFIED, this session]

---

## 3. The matrix — 124 cells, computed tallies

Counts produced by `tally.sh` over `matrix-out.txt`, not hand-counted.

| arm | implementation | flags | outcome |
|---|---|---|---|
| **ARM 1** | `/usr/bin/grep` (BSD) | `-av`, `LC_ALL=C` — **the live line** | **27/27 correct**, exit 0, every byte class, every shape |
| **ARM 2** | `/usr/bin/grep` (BSD) | `-v`, `C.UTF-8` — the pre-T157 line | 21 correct · **6 THIRD-MODE** · **0 blind** |
| **ARM 3** | ugrep wrapper (`-I`) | `-v` | **18 BLIND (exit 1, 0 bytes)** · 9 correct |
| **ARM 4** | ugrep wrapper (`-I`) | `-av`, `LC_ALL=C` — live flags | **27/27 correct**, exit 0 |
| **ARM 5** | BSD, locale sweep | `-v`, file shape | 4 correct (invalid UTF-8) · 4 THIRD-MODE (NUL) — **identical in all 4 locales** |
| **ARM 6** | ugrep, locale sweep | `-v`, file shape | **8/8 BLIND — identical in all 4 locales** |

Byte fixtures: `\xe2` (T157's exact bytes), `\xff\xfe` (the driver's), `\xff`, `\x80`, `\xc0`, a real
`\x00`, a NUL-dense blob, poison-on-the-LOCK-line, and a clean control.

### Each candidate discriminator, separated rather than conflated

1. **Implementation / invocation path — THE discriminator.** `exit 1 with zero output` occurs in
   **0 of 62** BSD cells and in **26 of 62** ugrep cells. No BSD configuration produced it: not any
   locale, not any shape, not any byte class.
2. **`--binary-files` mode (`-a`) — the decisive mitigation.** ugrep `-v` → 18/27 blind; ugrep `-av`
   → **0/27 blind**. `-a` alone fully repairs ugrep. This is exactly what **P-33 already recorded**
   ("ugrep `-I` skips the **whole file**, which **`-a` fixes and `LC_ALL=C` does not**") — the
   pattern was in the record the entire time; nobody connected it to line 224.
3. **Locale — NOT a discriminator.** 16 locale-sweep cells across two implementations show **zero**
   variation between `C`, `C.UTF-8`, `en_US.UTF-8` and `POSIX`.
4. **Byte class — a real secondary axis, and NUL is strictly stronger than invalid UTF-8.**
   - BSD without `-a`: invalid UTF-8 triggers **nothing** (this refutes the "invalid byte" framing
     for BSD entirely). A real **NUL** triggers the third mode.
   - ugrep with `-I`: **both** trigger, but see (5).
5. **Seekable-vs-pipe — real, but ONLY for ugrep + invalid UTF-8, and it is NOT a general defence.**
   ugrep + invalid UTF-8: file/redir blind, **pipe safe**. ugrep + **NUL**: blind in **all three
   shapes, pipe included** (`b-nul` and `i-blob` pipe cells → exit 1, 0 bytes). BSD + NUL: third mode
   in **all three shapes, pipe included**. **So "it's safe because it's a pipe" — the reachability
   argument both T157 and T171 rested on — is refuted.**
6. **OS build — no longer needs to explain anything.** T171's puzzle ("two binaries reporting the
   identical version string behave differently") **dissolves**: they were never the same binary.
   There is no Apple-patch mystery to invoke.
7. **The third mode, characterised.** BSD grep without `-a`, NUL present — exact stdout bytes
   (`od -c`, `provenance-out.txt` §7):
   - file shape → `Binary file /…/b-nul.txt matches\n`, **exit 0**
   - redirection and pipe → `Binary file (standard input) matches\n`, **exit 0**

   So `DIRTY` would be **non-empty**, the guard **would** fire, and it would then print and act on a
   line that is a **message, not a path**. Neither fail-open nor fail-closed: call it
   **fail-confused**. With `-a` the same fixture returns the three real lines correctly in all three
   shapes (`provenance-out.txt` §8).

---

## 4. Reconciling the four attempts — nobody was wrong, and there were never four

| attempt | what it *said* it ran | what it *actually* ran | result | correct? |
|---|---|---|---|---|
| T154 | reasoned by analogy, did not drive it | — | "fail-closed" | **wrong — never measured** |
| T157 | Apparatus §: "`/usr/bin/grep` … 2.6.0-FreeBSD" | its own transcript shows bare **`grep`** → the wrapper → **ugrep 7.5.0** | file/redir blind exit 1; pipe fine | **measurement correct, attribution wrong** |
| a previous fire's driver | "independent reproduction on **ugrep 7.5.0**" | the **same wrapper** — `exec -a ugrep $CLAUDE_BIN --version` → `ugrep 7.5.0` | reproduced | **correct — but NOT independent** |
| T171 | `/usr/bin/grep` by absolute path | BSD grep | could not reproduce | **correct** |
| this fire's driver | `/usr/bin/grep` | BSD grep | could not reproduce; found the NUL third mode | **correct** |

T157's own transcript, extracted (P-46, from its committed handoff):

```
$ grep -v '^?? \.softhouse/LOCK' order1.txt        # FILE ARGUMENT
rc=1                                                 # ZERO lines printed — total blindness
```

Bare `grep`. Its Apparatus paragraph names `/usr/bin/grep` two sections earlier, and the two never
got cross-checked.

**Consequence for the record's framing: "two positives versus two negatives" is a miscount.** It is
**one program measured twice (positive) and another program measured twice (negative)**, and the
"second implementation" that made the positive look corroborated was the **same** program. The
driver's own caveat — *"the binary actually invoked may differ between measurements"* — was exactly
right, and is now confirmed.

---

## 5. Is `fire-program.sh:224` safe today?

**YES — but the reason recorded in the register is the wrong one.**

The live line, extracted (P-46):

```
DIRTY=$(git status --porcelain | LC_ALL=C grep -av '^?? \.softhouse/LOCK$' || true)
```

Safe for four independent reasons, strongest first:

1. **`-a` is present.** 27/27 correct under **both** implementations, every shape, every byte class
   **including NUL** (ARM 1 and ARM 4). This is the load-bearing defence. T157's edit was correct;
   only its stated rationale was wrong. (P-11 again: right fix, wrong reason.)
2. **The real fire never runs ugrep.** Verified four ways: the plist runs `/bin/zsh -lc <script>`
   [VERIFIED: `mn.gerege.nbfi.softhouse-program.plist`]; `fire-program.sh` is `#!/bin/zsh`, so the
   script is a **non-login, non-interactive** child that reads only `/etc/zshenv` + `~/.zshenv`, and
   **neither exists**; the wrapper is **not exported** to children (`bash -c 'type -t grep'` → `file`,
   `zsh -c 'whence -w grep'` → `grep: command`); and under the plist's **exact** `PATH`,
   `whence -a grep` reports **only** `/usr/bin/grep`.
3. **The input cannot carry a poisoned byte.** APFS refuses an invalid-UTF-8 filename
   (`OSError(92, 'Illegal byte sequence')` — re-verified, not inherited from T157); a NUL is
   impossible in any POSIX filename (`ValueError: embedded null byte`); and
   `git status --porcelain` **C-quotes** non-ASCII paths by default (`core.quotePath` unset → true),
   emitting `?? "\320\260\320\266…"` — pure ASCII by construction.
4. **The pattern is anchored at column 0** against a fixed ASCII literal the script itself creates.

**NOT safe "because it is a pipe."** That reason is **refuted** (§3.5): a pipe stops neither
implementation once a NUL is in the stream.

### The residual fail-open that is actually live, and is not about bytes at all

```
DIRTY=$(git status --porcelain | … || true)
```

If `git status` **fails**, `DIRTY` is empty and the guard silently concludes the tree is clean and
skips the rescue. Measured: outside a repo, `git status --porcelain` → **rc=128**, `DIRTY=[]`
(`hardening-out.txt` §S5). The script runs `set -uo pipefail` **without `-e`**, and the trailing
`|| true` discards the status regardless, so **nothing observes the failure**. This is a genuine
fail-open in the exit-protocol guard — the direction everyone has been arguing about, arriving
through a door nobody was watching. It is **not** hypothetical byte poisoning; it is one bad `cwd`,
a `.git` lock contention, or an interrupted index away.

---

## 6. Proposed minimal hardening — NOT applied here (see §7)

Two changes, both small; the second is the one that matters.

- Call the binary by **absolute path** so no shell function, alias or `PATH` entry can intercept it.
  Cheap, and it forecloses the exact confusion that produced this dispute.
- Better: **delete the grep from the load-bearing path entirely** and use git's own pathspec
  exclusion — the idiom **the very next line of the same function already uses**
  (`git add -A -- . ':!.softhouse/LOCK'`). Then check git's exit status instead of swallowing it.

```diff
--- a/.softhouse/bin/fire-program.sh
+++ b/.softhouse/bin/fire-program.sh
@@ -221,7 +221,14 @@ run_exit_guard() {
 # The driver is required to checkpoint on EVERY exit path (skill STEP 5.5). It has
 # been observed exiting rc=0 mid-run with deliverables uncommitted and RESUME.md
 # stale, which makes the work invisible to the next fire. Detect and rescue.
-DIRTY=$(git status --porcelain | LC_ALL=C grep -av '^?? \.softhouse/LOCK$' || true)
+# T189: no grep here at all. git's own pathspec exclusion does the filtering (the
+# same idiom the `git add` below already uses), which removes every byte-class,
+# locale, binary-detection and grep-implementation question from a load-bearing
+# guard. And git's exit status is CHECKED: a failing `git status` used to yield an
+# empty DIRTY, i.e. a silent "tree is clean" — the one genuinely live fail-open here.
+DIRTY=$(git status --porcelain -- . ':(exclude).softhouse/LOCK')
+GS_RC=$?
+if (( GS_RC != 0 )); then
+  log "ERROR: exit-protocol guard could not read git status (rc=$GS_RC) — REFUSING to conclude the tree is clean"
+  DIRTY="<git status failed rc=$GS_RC>"
+fi
 if [[ -n "$DIRTY" ]]; then
```

**Driven red/green on a production-shaped scratch repo** (`hardening.sh` / `hardening-out.txt`) —
`.softhouse/` **tracked**, so `.softhouse/LOCK` appears as its own porcelain line:

| scenario | live line | ugrep wrapper | proposed |
|---|---|---|---|
| S1 only `.softhouse/LOCK` untracked | *(empty)* | *(empty)* | *(empty)* — **must be empty, is** |
| S2 LOCK + ` M base.txt` + `?? new_deliverable.go` | both listed, LOCK excluded | same | **same** |
| S3 T172's regression: `.softhouse/LOCKED_STATE.md` sibling | kept | kept | **kept** |
| S4 non-ASCII path present (C-quoted) | listed | listed | **listed** |
| S5 `git status` fails | `DIRTY=[]` → **silent "clean"** | same | `rc=128` **visible → guard refuses** |

Behaviourally identical on every real scenario, including T172's anchor case, and strictly better on
the failure path. **A first probe using an *untracked* `.softhouse/` was discarded**: git collapsed it
to `?? .softhouse/`, so the LOCK exclusion was never exercised at all and the fixture proved nothing
(P-22 — a test that structurally cannot fail).

---

## 7. What I did NOT do, and why

- **I did not edit `fire-program.sh`.** It is the running wrapper for this very fire; the task routes
  the patch to the driver instead. The diff above is a proposal.
- **I did not re-open T172's anchoring fix.** Separate, settled, and my S3 row re-confirms it holds.
- **I did not revert to T154.** "Fail-closed" was never measured and is not what the evidence shows.
- **I did not settle it by vote.** The tally (2–2) was the wrong instrument; the fix was to ask which
  program each vote was cast about.

---

## 8. The scoped claim the record should now carry

> At `fire-program.sh:224`, the `grep -v` filter's behaviour on hostile bytes is determined by
> **which program the token `grep` names**, not by the byte class, the locale or the OS build.
> Under the **Claude Code `grep` shell function** — which is **ugrep 7.5.0 with `-I` hard-coded** —
> an unhardened `grep -v` on a seekable source containing an invalid UTF-8 byte, **or on any source
> containing a NUL**, prints **nothing** and exits 1: total silent suppression. Under
> **`/usr/bin/grep` (BSD 2.6.0-FreeBSD, macOS 26.5.1/25F80)** that never happens in 62 cells; instead
> a **NUL** — and only a NUL — yields `Binary file … matches` at exit 0, a **third mode** in which
> `DIRTY` is non-empty but carries a message instead of paths.
> **`-a` repairs both implementations completely (54/54 cells correct); `LC_ALL=C` repairs neither of
> these two modes; a pipe is not a defence.**
> The live line **has `-a`**, the real fire runs **BSD grep** (the wrapper is not exported to the
> script's shell), and `git status --porcelain` **C-quotes** non-ASCII so the input is ASCII by
> construction. **The line is therefore SAFE today** — via `-a`, not via the pipe.
> The one **live fail-open** in this guard is unrelated to bytes: a failing `git status` yields an
> empty `DIRTY`, i.e. a silent "clean".

Neither "fail-open" nor "fail-closed" is a property of the line. Both were attempts to give a single
direction to a behaviour that has **three** outcomes and depends on a variable — the resolved
program — that none of the four measurements pinned.

---

## 9. Pattern this earns (proposed text, for the driver to route — `patterns.md` is outside my scope)

> **P-58 — WHEN TWO CAREFUL MEASUREMENTS OF "THE SAME TOOL" DISAGREE, STOP ARGUING ABOUT THE
> BEHAVIOUR AND GO FIND OUT WHETHER IT WAS THE SAME PROGRAM.** Four attempts, two positive and two
> negative, produced a 2–2 deadlock that the record carried as an open dispute across three fires.
> All four were right. Two ran `grep` (a shell function re-execing `claude` as **ugrep 7.5.0 with
> `-I`**) and two ran `/usr/bin/grep`. The deadlock was never about grep's behaviour; it was about
> the resolution of a name — and a tally of results cannot detect that, because every cell in it is
> true.
>
> *Rules:*
> 1. **A 2–2 split on a deterministic tool is not a hard question, it is a missing axis.**
>    Deterministic programs do not disagree with themselves. Look for the unpinned variable before
>    looking for a subtle mechanism.
> 2. **Record the resolved program, not the typed token.** "I ran grep" is not apparatus. `type -a`
>    plus the absolute path plus `--version` **of the thing that actually ran** is.
> 3. **A handoff's Apparatus section and its transcript must be cross-checked against each other.**
>    T157's Apparatus said `/usr/bin/grep`; its transcript, two sections later, said bare `grep`.
>    Both were committed, and neither reviewer compared them.
> 4. **"Independent reproduction on a second implementation" needs the second implementation
>    verified, not named.** The ugrep corroboration was the *same* program as the original — which
>    turned one observation into an apparent consensus and hardened the wrong claim.
> 5. **The answer may already be in `patterns.md`.** P-33 recorded "ugrep `-I` skips the whole file,
>    which `-a` fixes and `LC_ALL=C` does not" before this dispute began. Search the pattern file for
>    the mechanism before re-deriving it.
