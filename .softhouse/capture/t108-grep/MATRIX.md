# T108 — `grep`, invalid multibyte sequences, and the four claims that contradicted each other

**Status: SETTLED BY EXPERIMENT. 360 cells, all committed, all re-runnable.**

Re-run everything with:

```sh
cd .softhouse/capture/t108-grep
python3 gen-corpus.py          # rebuild the 13 byte-exact test files
bash    capture-env.sh         # out/env.txt, out/shell-function.txt, out/hexdumps.txt
bash    run-matrix.sh          # out/matrix.tsv  — 360 cells
bash    probe-flags.sh         # out/probe-flags.txt — -q/-qF/-l forms, verbatim exits
bash    replicate-t91-g4.sh    # out/replicate-t91-g4.txt — T91's own probe, corrected
bash    probe-conformance-guards.sh   # out/probe-conformance-guards.txt — §6, the money guard
```

---

## 0. The one fact that explains all four disagreements

**On this host the token `grep` means two different programs depending on where it is typed.**

| Where `grep` is typed | What actually runs |
|---|---|
| Directly into the Claude Code **Bash tool** | a **shell function** from `~/.claude/shell-snapshots/<session>.sh` that re-execs the `claude` binary with `argv[0]=ugrep` — i.e. **ugrep 7.5.0**, with **`-I` (skip binary files) hard-coded** |
| Inside a script run as `sh x.sh` / `bash x.sh` | `/usr/bin/grep` — **BSD grep 2.6.0-FreeBSD**. Shell functions are not exported to child processes. |
| After `command grep` / as `/usr/bin/grep` | `/usr/bin/grep` — the function is deliberately bypassed |

There is **no standalone `ugrep` binary on this host** — `command -v ugrep` is empty, nothing named
`ugrep` exists under `/usr/local` or `~/.local`, and `/opt/homebrew`, `~/bin` and
`/pkg/env/global/bin` do not exist as directories. ugrep is **embedded in the `claude` executable**
and reached by argv[0]. That is why every search for a `ugrep` *file* came back empty while
`grep --version` prints `ugrep 7.5.0`.

[VERIFIED: `out/env.txt`, `out/shell-function.txt`, `out/probe-flags.txt` §C.]

Every one of the four workers measured something real. They measured **different programs** and
each named it "grep".

---

## 1. The ruling, in one table

| Tool | Fails on | `-a` fixes it? | `LC_ALL=C` fixes it? | How loud is the failure |
|---|---|---|---|---|
| **BSD grep 2.6.0-FreeBSD** (`/usr/bin/grep`, what every **script** gets) | a **line** whose invalid byte comes **before** the match text — that line only | **NO** | **YES** | count `0`, exit `1`, **no stderr** |
| **ugrep 7.5.0 `-I`** (what an **agent typing `grep`** gets) | the **whole file**, if any invalid byte or NUL is anywhere in it | **YES** | **NO** | **no output at all** (not even `0`), exit `1`, **no stderr** |
| ugrep 7.5.0 without `-I` (control) | nothing | n/a | n/a | n/a |

**Therefore `LC_ALL=C grep -a` is correct and BOTH tokens are load-bearing — but each defends
against a different tool, and neither token alone is sufficient across both.** Removing `LC_ALL=C`
re-opens the BSD hole in scripts; removing `-a` re-opens the ugrep hole for any agent that runs the
same command by hand. **Do not remove either.**

The ugrep failure is the nastier of the two: `n=$(grep -c PAT f)` assigns the **empty string**, not
`0`, so `[ "$n" != "0" ]` is *true* and a naive gate may fire the wrong way, while
`[ "$n" -gt 0 ]` dies with a syntax error.

---

## 2. Verdict on each of the four claims

| Claim | Who | Ruling |
|---|---|---|
| "BSD grep in a UTF-8 locale returns 0 on a file with an invalid multibyte sequence; `-a` is not enough; `LC_ALL=C` fixes it" — the **measurement** `grep -ac 'unbound variable' f` → `0`, `LC_ALL=C grep -ac` → `1` | T80 (accepted by T85) | **CORRECT AND EXACTLY REPRODUCED.** `out/matrix.tsv`, shape `t80-exact-repro`, pattern `unbound variable`, tool `bsd`: `utf8C -ac` → `0` exit `1`; `posixC -ac` → `1` exit `0`. |
| "…matches **NOTHING in a FILE** containing an invalid multibyte sequence" — the **generalisation** | T80 | **FALSE, and this is the sentence to correct.** The blindness is **per line, and only from the invalid byte rightwards**. On the very same file, `^  PASS` still returns the true `3` under BSD grep in UTF-8. It is *ugrep `-I`* that goes blind to a whole file — T80 attributed ugrep's failure mode to BSD grep. |
| "T80's BSD-grep behaviour DID NOT REPRODUCE here" | T91 | **FALSE — the experiment was defective, twice over.** See §4. T91 was right to report a non-reproduction rather than parrot the claim; the honesty was correct even though the conclusion was not. |
| "the `grep` on this environment's interactive PATH is a shim onto ugrep 7.5.0 with `-I`; without `-a` it reports a present sentence as absent" | T91 (interactive limb), T107 | **CORRECT AND NOW REPRODUCED WITH COMMITTED EVIDENCE.** `out/probe-flags.txt` §B: `ccfn -qF` → exit `1` ("absent") on a file that plainly contains the sentence, in **both** locales; `ccfn -qaF` → exit `0`. It was never a PATH shim — it is a shell function — but the behaviour is exactly as described. |
| "there is no ugrep on this host; the ugrep limb rests on zero committed evidence and moves to `[UNVERIFIED]`" | T107b | **HALF RIGHT.** No ugrep *binary* — correct, and independently confirmed here. But the conclusion drawn from it is wrong: ugrep is embedded in `claude` and is what the bare token `grep` runs. C-7 can now be **retired**: the limb is VERIFIED, and `out/probe-flags.txt` is the committed evidence it asked for. |
| "BSD grep matched in 18/18 combinations" | T107 / T107b | **REPRODUCED, and not evidence for the conclusion drawn from it.** Those 18 cells did not include the one shape that fails. Here BSD grep is OK in 78 of 90 cells and silently wrong in 12 — a corpus that omits the failing shape reports green forever (P-22 / the discriminating-vector lesson from Run 1). |

---

## 3. The matrix

13 file shapes × 4 tools × 3 locales × 2 flag sets, scored against the **true** count.
Full data: `out/matrix.tsv`. Bytes of every shape: `out/hexdumps.txt`.

```
cells run:     360
SILENT-MISS:   12      (all of them BSD grep, all in a UTF-8 locale)
LOUD-MISS:     0       (nothing ever printed a diagnostic — that is the point)
```

Rollup by tool × locale × flags (15 cells each):

| tool | locale | `-c` | `-ac` |
|---|---|---|---|
| `bsd` | `utf8C` (`LANG=C.UTF-8`) | 12 OK / **3 SILENT-MISS** | 12 OK / **3 SILENT-MISS** |
| `bsd` | `utf8enUS` (`en_US.UTF-8`) | 12 OK / **3 SILENT-MISS** | 12 OK / **3 SILENT-MISS** |
| `bsd` | `posixC` (`LC_ALL=C`) | **15 OK** | **15 OK** |
| `ccfn` (ugrep `-I`) | `utf8C` | 3 OK / **12 blind** | **15 OK** |
| `ccfn` (ugrep `-I`) | `utf8enUS` | 3 OK / **12 blind** | **15 OK** |
| `ccfn` (ugrep `-I`) | `posixC` | 3 OK / **12 blind** | **15 OK** |
| `ugrepGI` (`-G -I` only) | all three | 3 OK / **12 blind** | **15 OK** |
| `ugrepG` (`-G`, no `-I`) | all three | **15 OK** | **15 OK** |

Read the two decisive facts off that table:

* the **BSD** row changes with the **locale** and not with `-a`;
* the **ugrep** rows change with **`-a`** and not at all with the locale.

### 3.1 Which shapes BSD grep goes blind on

| shape | invalid byte | position relative to the match | BSD grep, UTF-8 |
|---|---|---|---|
| `s01-ff-same-line-before` | lone `0xFF` | **before**, same line | **SILENT MISS** |
| `s06-e2-same-line-before` | lone `0xE2` | **before**, same line | **SILENT MISS** |
| `t80-exact-repro` / `unbound variable` | lone `0xE2` | **before**, same line | **SILENT MISS** |
| `s02-ff-same-line-after` | lone `0xFF` | **after**, same line | matches correctly |
| `s03`, `s04`, `s07`, `s08` | `0xFF` / `0xE2` / `0xE2 0x80` | **different line** | matches correctly |
| `s09`, `s10` | embedded `NUL` | either | matches correctly |
| `t80-exact-repro` / `^  PASS` | lone `0xE2` | on a **different** line | matches correctly, **3** |

The rule is mechanical: BSD grep's multibyte decode of a line fails **at** the offending byte, so the
part of the line **to the left** of it is still searchable and the part to the right is not. The
failure is **per line and directional**, never per file.

### 3.2 One observed nuance, deliberately not relied on

`s05-ff-eof-no-trailing-newline` — a lone `0xFF` as the final byte of a file with no terminating
newline — is **not** treated as binary by ugrep `-I` (all 3 locales OK) and **is** matched by BSD
grep in UTF-8. I do not know why the heuristic draws the line there and I make no claim about it.
It is recorded because it is the reason not to reason about these heuristics at all: use both
tokens. `[OBSERVED, UNEXPLAINED]`

### 3.3 The `-q` / `-qF` / `-l` forms the rigs actually use

`out/probe-flags.txt` §B, on `t80-exact-repro.txt`, pattern `unbound variable`, which **is present**:

| form | BSD utf8 | BSD `LC_ALL=C` | ugrep`-I` utf8 | ugrep`-I` `LC_ALL=C` |
|---|---|---|---|---|
| `-q` | **1 WRONG** | 0 correct | **1 WRONG** | **1 WRONG** |
| `-qa` | **1 WRONG** | 0 correct | 0 correct | 0 correct |
| `-qF` | **1 WRONG** | 0 correct | **1 WRONG** | **1 WRONG** |
| `-qaF` | **1 WRONG** | 0 correct | 0 correct | 0 correct |
| `-l` | **1 WRONG** | 0 correct | **1 WRONG** | **1 WRONG** |
| `-al` | **1 WRONG** | 0 correct | 0 correct | 0 correct |

`LC_ALL=C grep -qaF` — the exact form in `pathb/t80/forbidden-sentence.sh` — is the **only** cell
correct against both tools. It was the right fix.

---

## 4. What T80 actually saw, and why T91 could not see it

### 4.1 T80's file

The pre-fix `pathb/t36/preconditions.sh` contained an **unbraced** `$PIN_PG_MAJOR_MINOR` running
straight into `…` (U+2026 = `e2 80 a6`). Under `set -u` bash takes `0xE2` as part of the identifier
and dies. Reproduced from first principles in `out/env.txt`; the diagnostic is byte-exactly:

```
… .sh: line 2: PIN_PG_MAJOR_MINOR e2 3a 20 unbound variable 0a
                                  ^^ a LONE 0xE2 — invalid UTF-8
```

A lone `0xE2`, **before** the words `unbound variable`, **on the same line**. That is precisely
shape `s06` / `t80-exact-repro`, and precisely the one shape BSD grep goes blind on.

**T80 was measuring BSD grep** — it was building `prove-f2.sh`, a script, and inside a script `grep`
is `/usr/bin/grep`. Its quoted numbers reproduce exactly. Its error is a single over-generalised
sentence: it said "a **file**" where the truth is "the rest of a **line**", and in doing so it
described ugrep's whole-file blindness while naming BSD grep. **Prefer this explanation: T80 saw
something real and reported it accurately as a measurement; only the summary sentence over-reached.**

### 4.2 Why T91's non-reproduction was not a non-reproduction

T91's G-4 probe is committed at
`softhouse/T91-preconditions-copy:.softhouse/capture/t91/prove-guards.sh:68-85`. It contains **two
independent reasons it could never have reproduced T80**:

1. **The poison lands after the match.** Its Python splice is
   `b[:j] + b'\xff\xfe' + b[j:]` where `j` is the index of the `\n` **ending** the matched line — so
   the invalid bytes sit at end-of-line, **to the right of** the sentence being searched for. BSD
   grep still matches everything left of them.
2. **Both arms were run under `LC_ALL=C`.** Lines 79 and 81 are
   `LC_ALL=C /usr/bin/grep -qF …` and `LC_ALL=C /usr/bin/grep -aqF …`. **A test of whether
   `LC_ALL=C` matters, run with `LC_ALL=C` in both arms, cannot answer the question.**

`out/replicate-t91-g4.txt` runs T91's exact byte transformation and T80's, each × {`LC_ALL=C`, UTF-8}
× {`-qF`, `-aqF`}:

```
SHAPE        LOCALE   FLAGS  EXIT   MEANING
t91-shape    posixC   -qF    0      FOUND (correct)     <- T91 ran this
t91-shape    posixC   -aqF   0      FOUND (correct)     <- and this
t91-shape    utf8     -qF    0      FOUND (correct)
t91-shape    utf8     -aqF   0      FOUND (correct)
t80-shape    posixC   -qF    0      FOUND (correct)
t80-shape    posixC   -aqF   0      FOUND (correct)
t80-shape    utf8     -qF    1      ABSENT (WRONG - the sentence IS there)
t80-shape    utf8     -aqF   1      ABSENT (WRONG - the sentence IS there)   <- T80's cell
```

T91 ran two cells of the eight, and neither was the one under dispute.

The same applies to the "18 of 18" that T107 and T107b each measured: 18 green cells that do not
include the failing shape are 18 green cells, not a refutation.

### 4.3 Why T107b found no ugrep

T107b's probes ran from `/tmp/t107b/grepprobe.sh` — **a script**, where the shell function does not
exist — and it checked `command -v ugrep` and `command -v grep`, both of which deliberately bypass
shell functions. Every method it used was blind to the function by construction. Proof that the
function is invisible from inside a script is `out/probe-flags.txt` §C: `bash /tmp/…sh` and
`sh /tmp/…sh` both report `grep is /usr/bin/grep` / `BSD grep 2.6.0-FreeBSD`, while the same session's
Bash tool reports `ugrep 7.5.0`.

---

## 5. What this evidence does NOT establish

* **That T80's session had this same `grep` function.** Every retained snapshot on this host from
  2026-07-27 to 2026-08-21 defines it identically, but T80's own session snapshot was not retained.
  The inference is strong; it is not an observation. `[UNVERIFIED]`
* **Anything about GNU grep.** There is **no GNU grep on this host** — no `/opt/homebrew`, no
  `ggrep` under `/usr/local`. The brief asked for it; it cannot be measured here without installing
  software, which I did not do. GNU grep is widely documented to treat a file with invalid bytes as
  binary and print `Binary file … matches` (a *loud* miss, unlike both tools measured here), but
  that is **not measured** and must not be cited from this document. `[UNVERIFIED]`
* **Whether CI or any non-macOS environment behaves this way.** Everything here is one macOS 26.5.1
  arm64 host. `[UNVERIFIED elsewhere]`
* **Why `s05` escapes ugrep's binary heuristic.** Observed, unexplained, not relied on.
* **Whether `ugrep` version 7.5.0 is pinned.** It ships inside `claude` 2.1.233 and will change when
  the CLI updates. A future reader who gets a different answer should re-run `capture-env.sh` first.
  `[UNVERIFIED across versions]`

---

## 6. The defect reaches a MONEY guard — new finding, F-T108-1

The brief said to determine what the rigs actually invoke **by reading them**. I did. Across
`pathb/t36/recapture.sh`, `pathb/t80/forbidden-sentence.sh`, `pathb/t36/preconditions.sh`,
`pathb/t36/attest.py` and `.softhouse/conformance.sh` the content scanners in use are:

```
 43 grep     16 perl     14 tr     8 sed     3 python3     2 shasum
```

No `rg`, no `ag`, no `awk`, no standalone `ugrep`. All of it runs **inside scripts**, so all of it
gets **BSD grep**, and the BSD failure mode is the one that applies.

Two of those greps are **HARD money guards** in `.softhouse/conformance.sh`, and **neither carries
either token**:

```sh
:184  guard_no_float_in_vectors
        perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" | grep -Eq '[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]'
:201  guard_no_float_in_harness
        perl -0pe '...' | grep -Eq '\bfloat(32|64)\b|\bbig\.Float\b|...'
```

These are *fires-when-it-finds-something-bad* guards, so a blind grep is a **silent pass on a
float** — the exact defect class of P-25, arrived at from the opposite direction.

Measured (`out/probe-conformance-guards.txt`):

| vector file | locale | guard says | verdict |
|---|---|---|---|
| `clean.json` (float, no bad byte) | UTF-8 | FLOAT FOUND | correct |
| `poisoned.json` (lone `0xE2` **before** the float, same line) | **UTF-8** | **clean — PASSES** | **SILENT PASS ON A FLOAT** |
| `poisoned.json` | `LC_ALL=C` | FLOAT FOUND | correct |
| `earlier-line.json` (bad byte on another line) | UTF-8 | FLOAT FOUND | correct |

With `LC_ALL=C grep -aEq` substituted, **all six cells are correct**.

**I did not apply this fix.** `.softhouse/conformance.sh` belongs to another worker this fire and is
on T108's explicit stay-out list. The exact two-token edit is handed to the driver in the T108
handoff.

**Honest scoping of the reachability.** What is *measured* is that the guard goes blind on that
input. What is **not** measured is whether an invalid byte could actually survive into a committed
vector JSON — the rest of the pipeline (Go's JSON decoding, the capture scripts) may reject it
first. `[UNVERIFIED]` Fail-closed does not depend on that question being answered: a money guard
that can be silenced by one byte should carry the two tokens regardless.
