# T216 — close T168's P-40 tail: the three SIGQUIT-omission sites T168 named and skipped

Branch `softhouse/T216-quit-trap-tail`. Fork point (`git merge-base HEAD main`) =
**`2d41838`**, matching the dispatch-commit `HEAD` the driver verified. Worktree clean
before any edit.

Every material claim below is `[VERIFIED: <source>]` or `[UNVERIFIED]`.

## Materiality — stated honestly, not inflated

**LOW, as the task said, and I'm not raising it.** All three original sites (and the
two more this sweep turned up, see below) leak a `mktemp -d` scratch directory in
`/tmp` on `SIGQUIT`, or — for the fixture — change nothing at runtime at all, because
it is never executed. **No vector, no committed evidence, no money path is at risk
anywhere in this task.** This is exactly T168's own framing, unchanged. The only reason
to close it is P-26: a signal-list omission is a *concept*, and a family fixed at 5 of
8 (now understood to be more like 7 of 10 before this task, see census) is a family
that keeps growing back one script at a time.

## Changes made

1. **`.softhouse/capture/tierA-a2/cap.sh:65`** — `trap 'rm -rf "$TMPD"' EXIT HUP INT TERM`
   → `... EXIT HUP INT TERM QUIT`, with a two-line comment explaining why (same pattern
   T168 used in `prove-redgreen.sh`).
2. **`.softhouse/capture/tierA-a2/cap8.sh:67`** — identical fix, identical shape.
3. **`.softhouse/reviews/t179-guard-classifier/fixtures/green_real_trap.sh:7`** —
   `trap '...' EXIT INT TERM HUP` → `... EXIT INT TERM HUP QUIT`. See "the fixture
   question" below for why this was safe.
4. **`.softhouse/capture/tierA-a2/prove-a2-26-guards-red.sh:23`** (now line 25, two
   comment lines added) — same fix, same shape. **Not one of the three named sites** —
   found by this task's own re-sweep. See "growth found by this sweep" below for why I
   fixed this one but not the other new find (`cap9.sh`).
5. **New evidence/tooling** (both in scope, `.softhouse/capture/tierA-a2/`):
   `prove-quit-trap-cap.py` (drives `cap.sh`/`cap8.sh` RED then GREEN) and
   `prove-quit-trap-a226.py` (same for `prove-a2-26-guards-red.sh`). Transcripts under
   `T216-evidence/`.

**Not touched**: `.softhouse/bin/fire-program.sh` (explicit do-not-touch, a fire is
running from it — verified unchanged, still carries QUIT, see census). `.softhouse/gates.md`,
`.softhouse/vectors/`, `.softhouse/conformance.sh`, `.softhouse/patterns.md` — none
edited. `.softhouse/capture/tierA-a2/cap9.sh` — deliberately left, named below.

## Drive RED and GREEN per site (P-22)

### `cap.sh` / `cap8.sh`

Both scripts' trap only guards a `mktemp -d` scratch dir used to hold the response body
until the HTTP exchange completes. No network call is needed to prove the leak/no-leak:
`prove-quit-trap-cap.py` replaces `curl` on `PATH` with a stub that sleeps ~1.2s and
writes a canned `200`, so the real reference oracle is never touched and `out/` is
never touched (everything runs in a throwaway sandbox). The pre-fix bytes are read from
the **immutable git blob** at the fork point (`22baf85f…` for `cap.sh`,
`62b84060…` for `cap8.sh`), sha256-checked before use, so the RED case cannot silently
drift onto the fixed code.

```
=== PRE-FIX (pinned git blobs) -- expect RED (leak) on both ===
--- PRE-FIX  cap.sh (blob 22baf85faa50)           exit=-3 leaked-dirs=['cap.iljYWU'] => RED (LEAKED)
--- PRE-FIX  cap8.sh (blob 62b8406081a1)          exit=-3 leaked-dirs=['cap8.93xZGb'] => RED (LEAKED)
=== LIVE (current on-disk script) -- diagnostic, no assertion ===
--- LIVE     cap.sh  exit=1 leaked-dirs=[] => GREEN (CLEANED)
--- LIVE     cap8.sh exit=1 leaked-dirs=[] => GREEN (CLEANED)
```
Full transcript: `T216-evidence/RED-GREEN-cap-cap8.txt`.

`exit=-3` = killed by `SIGQUIT` (Python's negative-returncode convention), matching
T156/T168's documented finding that bash does not run an untrapped `SIGQUIT`'s EXIT
trap. Post-fix `exit=1` (not `0`): the synthetic test delivers `SIGQUIT` while the
stub `curl` is still "in flight" (mid-sleep); the trap now fires immediately and
removes `$TMPD` out from under the still-running curl child, so the later `mv
"$TMPBODY" "$OUT"` fails against a directory that no longer exists and `set -eu` exits
1. **That `exit=1` is an artefact of this synthetic test's signal timing, not a new
defect** — the property under test (does the scratch dir leak?) reads clean: `leaked-dirs=[]`
on both post-fix runs, both times. In a real interruption, the trap doing its job (an
early, unconditional `rm -rf "$TMPD"`) is exactly the intended behaviour.

### `prove-a2-26-guards-red.sh`

This script's body (after the trap line) drives three guards, including a real request
against the oracle and a transient edit-then-restore of a *committed* `req/` file. To
avoid any risk of a signal landing inside that restore window for a claim that has
nothing to do with it, the prover extracts the file's **real preamble verbatim** (every
byte from line 1 through the trap statement, read from disk — never retyped) and
appends only `sleep 1.2; exit 0`. That drives the actual trap line under test with zero
risk to `req/a2-26-admit-p46.json` and no oracle dependency.

```
=== PRE-FIX (pinned git blob 69d6b13a567e) -- expect RED ===
--- PRE-FIX preamble (verbatim lines 1-23)        exit=-3 leaked-dirs=['a226prove.1LOGUv'] => RED (LEAKED)
=== LIVE (current on-disk file) -- diagnostic ===
--- LIVE preamble (verbatim lines 1-25)           exit=0 leaked-dirs=[] => GREEN (CLEANED)
```
Full transcript: `T216-evidence/RED-GREEN-prove-a2-26-guards-red.txt`. Clean `exit=0`
here (no curl-stub race to complicate it) — the strongest of the three drives.

### `green_real_trap.sh` — no RED/GREEN in the runtime sense; a different kind of proof

This file is **never executed** (checked: no caller invokes it as a script anywhere
under `.softhouse/` — `grep -rln "green_real_trap.sh"` finds exactly two references,
`T168.md` (prose) and `t179-guard-classifier/selftest.py` (reads it as *text*, never
`exec`s it) `[VERIFIED: grep -rln "green_real_trap.sh" .softhouse --include="*.py"
--include="*.sh" --include="*.md"]`). So there is no SIGQUIT to deliver and no scratch
dir to leak — the "RED/GREEN" that applies here is: **does editing it change what the
thing that reads it concludes?** See next section — verified by running
`selftest.py` byte-for-byte identically before and after the edit.

## The fixture question — what reads `green_real_trap.sh`, and why editing it is safe

`green_real_trap.sh` exists as a negative-control fixture for
`.softhouse/reviews/t179-guard-classifier/selftest.py`, case `s2`
(`SHELL_CASES = ["red_prose_guard.sh", "green_real_trap.sh"]`,
`.softhouse/reviews/t179-guard-classifier/selftest.py:77`). I read
`guard_classify.py`'s `classify_shell()` (`.softhouse/reviews/t179-guard-classifier/guard_classify.py:1163-1178`)
to find out exactly what it inspects:

```
def classify_shell(rel, src):
    """DOCUMENTED REFUSAL. ... this classifier REFUSES every shell file ..."""
    return {"path": rel, "lang": "shell", "refused": REFUSE_SHELL, ...}
```

**It never reads `src`'s content** (the parameter exists only to compute `len(src)` for
an unused `"bytes"` field — never asserted anywhere in `selftest.py` or any other file
under `t179-guard-classifier/` `[VERIFIED: grep -n "bytes" selftest.py
rederive_population.py list_trusted_unguarded.py` → no hits]). `classify_path()` routes
purely on file extension (`.sh`/`.bash` → `classify_shell()`, unconditionally
`REFUSE_SHELL`). **The trap's signal list — whether it has `QUIT` or not — cannot
possibly change the classifier's verdict on this file**, because the classifier never
looks past the file extension for shell files. That is the documented design: no
`bashlex`, so *every* `.sh`/`.bash` file is refused, by construction, to avoid the risk
of a wrong classification (T179's own stated purpose).

**Verified, not just reasoned:** ran `selftest.py` before touching the fixture (exit 0,
`green_real_trap.sh parser=REFUSED-SHELL-NO-PARSER expected=REFUSED-SHELL-NO-PARSER OK`)
and again after adding `QUIT` (identical output, exit 0,
`T216-evidence/selftest-AFTER-fixture-edit.txt`). **Byte-for-byte identical test
output.** So: adding `QUIT` does **not** alter the classification, and the edit is
safe. Had `classify_shell()` inspected the trap's signal set (it does not, but if a
future version did), this would have been the wrong move — the instruction to check
before editing was correct to give.

## Census — re-running T168's sweep, now, with corrections

**Two independent grep programs, named (P-58)**: the interactive `grep` here (a shell
function re-execing as **ugrep** `-I`) and **`/usr/bin/grep`, BSD grep 2.6.0-FreeBSD**.
Same query T168 used: files under `.softhouse/` (`*.sh`, `*.py`) containing both the
literal `trap ` and the literal `INT`.

```
ugrep:      grep -rlI --include="*.sh" --include="*.py" -e "trap " . | xargs grep -l "INT" | sort
/usr/bin:   find . -name "*.sh" -o -name "*.py" | xargs /usr/bin/grep -lI "trap " | xargs /usr/bin/grep -l "INT" | sort
```

**36 files, both programs, byte-identical lists** (`diff` empty, path-prefix
normalized) — `T216-evidence/census-ugrep-list.txt`, `T216-evidence/census-bsdgrep-list.txt`.
T168 measured 30 at their fire; the +6 are files that didn't exist yet at T168's time
(`cap9.sh`, `prove-a2-26-guards-red.sh`, the `T158-drive-*.py` reviews,
`T188-probe`/`T191-probe`, `conformance.sh`'s current form, and this task's own two new
prover scripts) — population growth over calendar time, not a methodology change.

**Distinguishing live code from commentary (the driver's own near-miss on this exact
sweep, avoided here):** a coarse "contains the substrings" grep is a *superset* — it
also matches prose, docstrings and quoted old code. I read every file's actual `trap`
**statements**, not the coarse hits, using
`/usr/bin/grep -n -E "^[[:space:]]*trap[[:space:]]" <file>` — a line only counts if
`trap` is the **first non-whitespace token on the line**, which a `#`-comment or an
indented prose sentence inside a `"""docstring"""` can still slip past (a comment can
itself start with `trap`, and a docstring line can start "trap anywhere." after word
wrap — both happened in this population, see below). So I additionally read the actual
context of every match by eye. Two concrete false positives caught this way:

* `.softhouse/reviews/T158-drive-followups.py:7` — matched `trap` at line start, but
  it's the docstring sentence *"…with no\n     trap anywhere.  T156 read the shape…"* —
  English prose, not a statement. Confirmed by reading the surrounding
  `"""..."""` block. **Excluded.**
* `.softhouse/capture/tierA-a2/prove-quit-trap-cap.py` and `prove-quit-trap-a226.py`
  (this task's own new files) — both are `.py`; any line reading `trap 'rm -rf ...'
  EXIT HUP INT TERM` inside them is a **docstring quotation of the target `.sh`
  file's line**, illustrating the defect for a reader — Python has no `trap` builtin,
  so this text can never execute. Same shape as the driver's `fire-program.sh`
  near-miss, caught here because the file extension (`.py`) makes the exclusion
  mechanical: **any `trap` text in a `.py` file is data or prose, never a live shell
  trap**, by construction of the language. **Excluded.**
* Full per-file `trap`-statement dump used for this pass: `T216-evidence/census-trap-lines-per-file.txt`.

**Numeric-signal traps** (T168 also checked this, found zero): re-ran with the same
regex, **calibrated first against a known positive** (P-72) — a synthetic
`trap "cleanup" 2 15 1 3` file matched under `-E` on both engines (my first attempt
without `-E` silently found nothing on the calibration file too, which is exactly the
failure mode P-72 warns about — caught before it became a false negative). With `-E`
confirmed working, the real sweep: **zero matches, both engines.** No numeric-signal
trap exists in this population, confirming T168's finding still holds.

### The population, by disposition (10 sites carry the multi-signal-trap concept; 36 files matched the coarse grep, 26 excluded as EXIT-only cleanup traps or false positives — full list in `census-trap-lines-per-file.txt`)

| # | site | has QUIT (now) | disposition |
|---|---|---|---|
| 1 | `.softhouse/capture/pathb/t149/prove-redgreen.sh:170-173,124` | **yes** | T168's own fix, out of my scope, read not touched — unchanged |
| 2 | `.softhouse/capture/pathb/t80/prove-f1-sandbox-run.sh:34` | **yes** (`trap cleanup EXIT INT TERM HUP QUIT PIPE`) | pre-existing (T161), out of scope, unchanged |
| 3 | `.softhouse/capture/pathb/t80/prove-f1.sh:259,323-327` | **yes** | pre-existing (T161), out of scope, unchanged |
| 4 | `.softhouse/bin/fire-program.sh:415-419` | **yes** (`trap 'on_signal QUIT 131' QUIT` at line 418 — a real statement, not a comment; the driver's own near-miss read a *comment quoting old code* elsewhere in this file and I did not repeat that: I read the actual `trap` statements at 415-419 directly) | explicit do-not-touch, verified unchanged and correct |
| 5 | `.softhouse/capture/tierA-a2/cap.sh:65` | **yes — FIXED, this task** | named site 1/3 |
| 6 | `.softhouse/capture/tierA-a2/cap8.sh:67` | **yes — FIXED, this task** | named site 2/3 |
| 7 | `.softhouse/reviews/t179-guard-classifier/fixtures/green_real_trap.sh:7` | **yes — FIXED, this task** | named site 3/3; verified test-neutral (above) |
| 8 | `.softhouse/reviews/t202-probe/patch.py:128-131` + `orphan-heartbeat.py` (string literal reproducing the already-fixed pattern for probe purposes, not live top-level code) | **yes** | pre-existing evidence, no work needed (T168's own finding, re-verified) |
| 9 | `.softhouse/capture/tierA-a2/cap9.sh:49` | **NO — left, named** | **newly discovered by this sweep** (did not exist at T168's fire). See below. |
| 10 | `.softhouse/capture/tierA-a2/prove-a2-26-guards-red.sh:23→25` | **yes — FIXED, this task** | **newly discovered by this sweep**, fixed anyway (in scope, no committed-evidence conflict) |

**Count discipline (P-40): 10 sites carry the concept. 9 of 10 now carry `QUIT`. 1
(`cap9.sh`) deliberately left, named, with reasons below.** Against the task's own
framing ("it should be 8 of 8, or say why not"): **the three explicitly named sites are
3 of 3 fixed**, and T168's originally-counted 8-site population is **8 of 8** resolved
(5 already had it, 3 now fixed). This sweep's own re-run additionally surfaced **2 more
instances of the same concept that did not exist at T168's fire** — this is exactly the
"family grows back" behaviour P-26 warns about, not a miss in T168's own count. Of
those 2: 1 fixed (`prove-a2-26-guards-red.sh`), 1 named and left (`cap9.sh`).

### `cap9.sh` — why I did not fix it

`cap9.sh` is **not one of the three named sites**, and unlike `cap.sh`/`cap8.sh`/the
fixture, it has **already produced committed evidence**: the `A2-300`–series files
under `out/`, git-tracked
(`[VERIFIED: git ls-files .softhouse/capture/tierA-a2/out/A2-300-glaccount2-classification-today.http`
→ tracked; content confirms an `Idempotency-Key`-bearing capture, `cap9.sh`'s
signature]). This rig's own standing convention — stated in `cap9.sh`'s own header and
enforced by `SUPERSEDED.txt` — is: once a script has produced committed evidence, edit
a **new successor file**, never the original in place (`cap.sh → cap8.sh → cap9.sh` is
that exact chain). A trap-only defensive fix does not change any request/response
content and would not actually break re-derivability, but the local convention here is
consistently conservative (no exception is recorded anywhere in this rig for
"safe" edits), and the task's own materiality framing — **LOW, not to be inflated** —
does not justify minting a `cap10.sh` successor purely to add one word to a temp-dir
cleanup trap, when the task named exactly three sites and this is not one of them. I am
naming it, per P-40, for a follow-up task rather than acting outside the given scope on
a judgment call the task didn't ask for.

## Verification — BAR (driver-corrected figures, `2d41838`)

`bash .softhouse/conformance.sh` (never `sh` — confirmed run under `bash`):
- probe line **PRESENT**, reads `up`: `conformance: reference oracle
  (https://localhost:8443/fineract-provider/actuator/health) probe = up` /
  `oracle probe    UP`
- `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884
  cells compared.` — matches BAR exactly (46/7884)
- inadmissible 0, harness errors 0, invariant violations 0
- `4 EXEMPTED BY A VECTOR` / `4 REPRODUCED, 0 DIVERGED, 0 COULD NOT SAY` (port conjunct)
  — matches BAR's 4 EXEMPTED/4 GROUNDED/0 UNGROUNDED/0 UNDETERMINED
- `exemption census READ:` lines confirm `exempted (graded)=4==pinned 4`,
  `declared=4==pinned 4`, `GROUNDED=4==pinned 4`, `UNDETERMINED=0==pinned 0`,
  `UNGROUNDED=0==pinned 0`

`bash .softhouse/conformance.sh --prove`: `PROOFS: 23 passed, 0 failed` — matches BAR.

Go toolchain (`GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go`, etc., per
`.softhouse/bin/go-env.sh`, exported directly since `. go-env.sh` was blocked by the
worktree-isolation sandbox on this session — same effective environment):
- `go build ./...` — clean, 0 errors
- `go vet ./...` — clean, 0 errors
- `go test -count=1 ./...` — `ok` on `ledger`, `loanschedule`, `loanschedule/conformance`;
  no test files in `conformance/cmd/conformance`, `contract` — matches BAR
- `gofmt -l .` from `nexus/` — exactly one file: `internal/apps/loanschedule/contract/contract.go`
  — matches BAR (`contract.go` untouched by me, never `gofmt -w`'d, per G-3)

`git rev-parse HEAD:.softhouse/vectors` = `73c3ea7b43dd75f04884072719a87fc8e1d255c1` —
**matches the pinned digest, unchanged by this task** (this worktree's `HEAD` is still
the fork-point commit; I have not committed yet at time of this check).

## Scope discipline

Touched only: `.softhouse/capture/tierA-a2/{cap.sh,cap8.sh,prove-a2-26-guards-red.sh,
prove-quit-trap-cap.py,prove-quit-trap-a226.py}`,
`.softhouse/reviews/t179-guard-classifier/fixtures/green_real_trap.sh`, and this
handoff + its evidence directory. Did not touch `fire-program.sh`, `gates.md`,
`vectors/`, `conformance.sh`, `patterns.md`, or `cap9.sh`.

## What I did not check (P-66/P-70 — named, not left as a silent caveat)

* **`nexus/` (Go) and anything outside `.softhouse/`** — same exclusion T168 recorded;
  Go uses `signal.Notify`, a different mechanism this sweep's lexical grep cannot see.
  Not probed here either.
* **`.md` code blocks** — same gap T168 left open; not probed.
* Directories other workers hold this fire and that are outside my `files_hint`
  (`pathb/t80`, `pathb/t99`, `t91`, etc.) — read their `trap` lines for the census
  table above (to report accurately), but made **no edits** there; all confirmed
  already `QUIT`-bearing so there is nothing live to report as a gap in those trees.

## Summary for the driver

- Branch: `softhouse/T216-quit-trap-tail`. Fork point verified: `git merge-base HEAD
  main` = `2d41838` (matches dispatch commit).
- The three named sites: **3 of 3 fixed**, each driven RED then GREEN (or, for the
  fixture, proven test-neutral by identical `selftest.py` output before/after).
- Sweep re-run: **10-site population** (T168's 8, resolved 8/8, plus 2 new finds this
  sweep surfaced). 9 of 10 now carry `QUIT`. 1 gap left and named: `cap9.sh` — has
  committed evidence, not one of the three named sites, local convention says
  successor-file-not-edit, materiality LOW; recommend a small follow-up task (`cap10.sh`
  or an explicit exception ruling) rather than acting on it here.
- BAR: all figures matched the driver-corrected numbers exactly (46/7884, 23/0 proofs,
  build/vet/test/gofmt clean except `contract.go`, vectors digest unchanged).
- Materiality: LOW throughout, as instructed — no vector, no money path, no committed
  evidence content at risk anywhere in this task.
