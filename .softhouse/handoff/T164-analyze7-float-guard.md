# T164 — `analyze7.py`'s float guard was kept green by its own docstring

**Branch:** `softhouse/T164-analyze7-float-guard`
**Branch point:** `a71c1408d3315493bca763472598680c85b9ad0b`
**files_hint:** `.softhouse/capture/tierA-a2/` — nothing outside it was written.
**Vector store:** `git rev-parse HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` at start
and at finish. **Unmoved.**
**Oracle:** not contacted. Every red arm runs against a scratch copy in a throwaway temp dir.

---

## 0. In one paragraph

`prove-mkreq7-guard-red.py:143` asserted "no binary float on any amount in `analyze7.py`"
with a **whole-file source grep**. `parse_float=decimal.Decimal` occurs **twice** in
`analyze7.py` — at `:39` in the code and at `:6` in the file's **own docstring** — so the
assertion is satisfied by the prose. **Reproduced:** delete the keyword from the code, leave
the docstring, and the old guard prints `ok` three times and exits 0 while every oracle
amount loads as a Python `float`. Replaced by `guard-parse-float-ast.py`, which **parses the
source and grades call sites by line number**, treats **zero call sites inspected as an
ERROR**, and carries a **default-deny, enumerable, self-invalidating declaration register**
for the two cases where "add `parse_float`" is the wrong repair. Driven red on **17 arms /
41 assertions**, including both halves of the original defect. The concept sweep says: of
the source-grep sites under `.softhouse/` whose target can be resolved statically, **11 are
wired to a verdict and exactly 1 of those 11 has this hole — the one T164 was assigned**;
742 further sites are **unmeasured, not clean**, and are counted as such.

---

## 1. Deliverable 1 — the reproduction (the premise is TRUE)

`prove-parse-float-guard-red.py` ARM 0, transcript `RED-GREEN-T164-parse-float-ast.txt`:

```
ARM 0 -- REPRODUCE: the OLD grep guard stays GREEN with parse_float deleted from analyze7.py's CODE
         analyze7.py:39 is now: 'return json.load(f)'
         `parse_float` now occurs on line(s) [6] -- the DOCSTRING only:
           6: money). Every amount is parsed with `parse_float=decimal.Decimal`, so the JSON literal
  ok   OLD guard assertion 1 `"parse_float=decimal.Decimal" in src` still TRUE -> it still reports ok
  ok   OLD guard assertion 2 `"float(" not in src...` still TRUE
  ok   OLD guard verdict on the SABOTAGED rig: PASS (this is the defect)   0 failures -> exit 0
  ok   meanwhile the sabotaged loader really does build a binary double
         an oracle amount now loads as type 'float'
```

Both limbs measured: the guard passes **and** the sabotage is real — `out/A2-235-je-after-recovery.json`'s
`pageItems[0].amount` comes back as `float`, not `Decimal`. A2-11's finding is confirmed
independently, not inherited.

**Second-order P-35 confirmed too.** The old guard's other assertion,
`"float(" not in src.replace("parse_float=", "")`, is a *negative* whole-file grep — the
same shape from the other side.

## 2. Deliverable 2 — the fix

**`guard-parse-float-ast.py`** (new). Property, stated positively:

> every `json.load` / `json.loads` **call site** passes `parse_float=`, and the value it
> passes is not the builtin `float`.

- **AST, not text.** `parse_float` in a docstring, a comment or a string literal is
  invisible to it.
- **Selector checked before conditions (P-76 addendum).** Loader names are resolved from
  each file's **own imports**, so `import json as J`, `from json import load`, and
  `from json import loads as L` cannot hide a site. A **selector self-test** runs on every
  invocation against a synthetic source carrying all four alias shapes plus three decoys
  (docstring / comment / string literal); it must find exactly 4 sites and 0 decoys, or the
  guard **refuses**. Driven red (ARM 16).
- **`parse_float=float` fails.** A keyword that satisfies a grep and changes nothing is a
  violation, counted in its own column (ARM 8).
- **Three refusals fire before any verdict** (exit 2): 0 Python files; **0 call sites
  inspected**; any file that will not parse. A file the guard cannot read is not a file the
  guard may skip.
- **Exit codes:** `0` pass, `1` FAIL (a real violation), `2` REFUSE (cannot honestly reach a
  verdict). Distinguishing 1 from 2 is deliberate — P-80's "an error is not a zero", applied
  to the guard's own output.

Live green run, `LEG 1` of the transcript:

```
PASS -- 20 call site(s) across 32 file(s): 14 carry parse_float=, 6 are declared and
their preconditions hold, 0 violations.
```

### 2.1 The declaration mechanism — T207's binding constraint

T207 ruled that **"add `parse_float`" is sometimes the wrong repair**: a script whose job is
to **reproduce** a target that loads without it must keep loading the same way, or its
published figure becomes a claim about a tool that does not exist. T114 separately forbids
editing any script that produced committed evidence. Both need a declaration. Neither may
become a silent skip. `PARSE-FLOAT-EXEMPT.txt` is that register:

| property | how it is enforced |
|---|---|
| **DEFAULT-DENY** | a site absent from the register with no `parse_float` is a FAIL; an unrecognised **category** is a REFUSE (ARM 12) |
| **ENUMERABLE** | every record is printed in full on every run, green or red, with its precondition outcome |
| **PINNED** | field 4 pins the exact stripped source of the line; drift ⇒ REFUSE (ARM 11) |
| **STALE = ERROR** | a record naming a non-existent site ⇒ REFUSE (ARM 9); a record for a site that **now carries `parse_float`** ⇒ REFUSE (ARM 10) |
| `FROZEN-T114` | valid **only while** the named committed evidence exists **and** the file's sha256 still equals what `MANIFEST.sha256` pins. **Edit the file and the exemption dies with it** (ARM 13) |
| `REPRODUCTION-T207` | valid **only while** the named target still has a `json.load` at that line **and still lacks `parse_float`**. **Fix the target and the exemption dies** (ARM 15) |

### 2.2 Each site decided on what it is reproducing, with materiality measured

Six sites in the rig lack `parse_float`. None is a T207-style faithful reproduction (T207's
two reproduction sites live under `leapboundary/`, outside this files_hint). All six are
T114-frozen; each is declared with its **measured** materiality, not an assumption:

| site | evidence it produced | JSON-float leaves in the documents it can load |
|---|---|---|
| `prove-mkreq7-guard-red.py:70` | `RED-GREEN-A2-7-guards.txt` | 12 generated bodies, **0** |
| `prove-mkreq7-guard-red.py:119,126` | `RED-GREEN-A2-7-guards.txt` | sandbox `{"clientId":1,"productId":46}`, **0** |
| `resolve7.py:24` | `req/a2-7-loan-220-resolved.json` | **MATERIAL — 11** across 117 `req/*.json` (e.g. `/debits/0/amount 100000.25`) |
| `resolve7.py:25` | `req/a2-7-loan-220-resolved.json` | **MATERIAL — 12** across 5 `out/A2-21*.json` (e.g. `/principal 1200000.0`) |
| `verify-provenance-a2-15.py:24` | `PROVENANCE-A2-15.txt` | 6 vectors, **0** — every promoted money cell is a **string** (`amount_major_text`, `amount_minor`) |

`resolve7.py` is A2-11's original P-25 finding; it is material, which is exactly why T163
froze it and replaced it with `resolve8.py` (`SUPERSEDED.txt`, enforced by
`census-json-float-siblings.py` as a redirect, not an allowlist). `resolve8.py:101,265` both
carry `parse_float`.

**`analyze7.py` itself was NOT edited** — it was already correct. The defect was in the
guard, not in the thing guarded.

## 3. Deliverable 3 — the red drive, both arms

`prove-parse-float-guard-red.py`, **17 arms, 41 assertions, 0 failed, exit 0.**

| # | arm | result |
|---|---|---|
| 0 | old grep guard stays **GREEN** with `parse_float` deleted from the code | reproduced |
| 1 | same sabotage ⇒ AST guard **exit 1**, names `analyze7.py:39`, reports exactly 1 violation, and the `:6` docstring occurrence does **not** rescue it | red |
| 2 | the **legitimate rig, untouched, still PASSES** (exit 0, 20 sites stated) | green |
| **3** | **ZERO CALL SITES INSPECTED ⇒ exit 2**, `NIL COVERAGE … INSPECTED NOTHING`, and no `PASS` printed | red |
| 4 | zero Python files ⇒ exit 2 | red |
| 5 | an unparseable file ⇒ exit 2, file named, never a silent skip | red |
| 6 | `import json as J; J.load(x)` cannot hide a site | red |
| 7 | `from json import loads as L; L(x)` cannot hide a site | red |
| 8 | `parse_float=float` ⇒ violation, counted as a dodge | red |
| 9–13 | register: stale record / unnecessary exemption / pinned-source drift / unknown category / **FROZEN dies when the file is edited** — all ⇒ **exit 2** | red |
| 14–15 | `REPRODUCTION-T207` green while the target is unfixed; **dies the moment the target is fixed** | green then red |
| 16 | **the selector self-test is itself failable** — blinding the selector ⇒ exit 2, not a green "0 problems found" | red |

ARM 3 is the arm the brief asked to be verified specifically. It is verified: the guard
finds nothing and **exits 2**, printing the NIL-COVERAGE refusal, and never prints `PASS`.

## 4. Deliverable 4 — the concept sweep (P-26), both terms

`sweep-t164-selfmatch-guards.py` → `SWEEP-T164-SELFMATCH-GUARDS.txt`. AST for Python,
`tokenize` for the prose/code split, `python3 re` for shell and Go. **No bare `grep`, no
`rg`** anywhere in it (P-75).

```
POPULATION WALKED
  files under .softhouse/ ......... 5145
  .py  (AST-scanned) ............. 511
  .sh/.zsh/.bash (regex-scanned) . 441
  .go  (regex-scanned) ........... 5
  SKIPPED, not instruments ....... 4188

BOTH TERMS (P-67)
  TERM 1 -- literal-token-in-whole-file-source SITES ... 796
            ... WIRED TO A VERDICT, i.e. actual GUARDS   191
            ... not wired (evidence dumps, generators)   605
            ... target file resolved statically ....... 54
            ... target NOT statically resolvable ...... 742
  TERM 2 -- resolved sites WITH THE SELF-MATCH HOLE .... 8
            ... of those, WIRED TO A VERDICT (real) ... 1
            ... of those, token in prose ONLY ......... 4
            ... of those, the grep is SELF-directed ... 0
            resolved sites with NO prose occurrence ... 46 (of which wired: 10)
```

**Term 1 is split on purpose.** A generator splicing a Java snippet and a guard grading a
file both contain `"tok" in src`; counting them together would inflate the numerator and
make the ratio meaningless. Wiring is decided by an AST walk to an enclosing `assert`, a
`check(...)`-shaped call, or an `if` whose branch reaches a failure sink.

**The one wired hole is T164's own defect**
(`prove-mkreq7-guard-red.py:143`, token `parse_float=decimal.Decimal`, target
`analyze7.py`, verdict PROSE-ONLY) — now superseded.

### 4.1 Backlog items — outside `files_hint`, reported not fixed

Seven further holes, all **evidence dumps rather than guards** (`|| true`, `| head`), so
none can currently make a verdict lie. They are the same shape and will bite if anyone
wires them:

| site | token | target |
|---|---|---|
| `.softhouse/capture/t243-wiring/instruments/10-wrongimpl-red-drive.sh:91` | `go test` | `.softhouse/conformance.sh` — **prose-only** |
| `.softhouse/reviews/T184-evidence/t184-sweep.sh:15,18` | `except` | `.softhouse/capture/lib/check_wire_float_roundtrip.py` |
| `.softhouse/reviews/a2-34-review-a2-15/bar-and-oracle.sh:76,77` | `A2-348`, `I-5` | `nexus/…/conformance/invariants.go` — **prose-only** |
| `.softhouse/reviews/a2-34-review-a2-15/check-money-and-additive.sh:60,61` | `AmountMinor`, `TotalDebitsMinor` | `nexus/…/conformance/vector.go` |

### 4.2 What was SKIPPED, and why (P-40)

- **4,188** non-instrument files (`.md .json .txt .http .status .sql .sha256` …) — no
  assertions in them.
- **742** sites whose target expression is **not static** (a loop variable, `argv`, a glob).
  The sweep cannot say what file they grade without executing them, so it **says so**.
  **These are unmeasured, not clean** — P-66: "not found" is a statement about the search.
- **0** Python files failed to parse.
- Shell coverage is a regex over `grep`/`git grep`/`rg` with a **quoted literal and a file
  operand**; a pattern built in a variable, or a heredoc'd `python3 -c`, is not seen. Go
  coverage is `strings.Contains(x, "lit")` only.
- Routes **other** than "literal token in whole-file source" — an AST guard with a wrong
  selector, a numeric threshold, a regex over captured stdout — are a different concept and
  are out of this sweep. Naming them is not covering them.

## 5. Deliverable 5 — manifest accounting

`manifest.py verify` was **already clean at the branch point** (exit 0, `OK: 963 files`), so
T236's 13 pre-existing discrepancies were already absorbed; none of that history is being
re-laundered here.

After `manifest.py write`: **`OK: 969 files match MANIFEST.sha256` (884 under out/ req/ sql/,
85 rig + docs, this script included), exit 0.**

The rewrite is **provably additive** — `git diff -U0` on `MANIFEST.sha256` is
**6 lines added, 0 removed, 0 changed**:

```
+ …  PARSE-FLOAT-EXEMPT.txt
+ …  RED-GREEN-T164-parse-float-ast.txt
+ …  SWEEP-T164-SELFMATCH-GUARDS.txt
+ …  guard-parse-float-ast.py
+ …  prove-parse-float-guard-red.py
+ …  sweep-t164-selfmatch-guards.py
```

No pre-existing file's digest moved, because no pre-existing file was edited. **`verify` is
clean at the branch tip.**

## 6. Deliverable 6 — which published numbers changed, MEASURED

T207 measured that no published number moved from its narrower change. **That does not hold
here**, and the brief was right to say measure it.

| number | before | after | note |
|---|---|---|---|
| `manifest.py verify` file count | **963** (884 + 79) | **969** (884 + 85) | published in `handoff/…/T236.md:317`. Six new rig files. |
| `census-json-float-siblings.py` — POPULATION | 29 `.py`, 34 `.sh` | **32** `.py`, 34 `.sh` | |
| … mechanical candidates | 20 | **21** | `prove-parse-float-guard-red.py` names a `req/` path |
| … unclassified list | `['a2-29-retype-path.py','census-a2-26.py','mkje-a2-29.py']` | **+ `prove-parse-float-guard-red.py`** | |
| … R5 scope | 12 files | **13** files, still **0** float literals | |
| … census exit code | **1** | **1** | unchanged — see below |
| `prove-mkreq7-guard-red.py` | 16 assertions, 0 failed, exit 0 | **identical** | file untouched; its transcript still reproduces |
| `.softhouse/conformance.sh` | — | — | **no change**: it makes no reference to `tierA-a2` (`git grep -P tierA-a2` over it and `.softhouse/bin/`, exit 1 = real measured negative) |
| vector store digest | `13b8342e…` | `13b8342e…` | unmoved |
| all three new `.py` files' census tier | — | **INERT, 0 R1 hits** | they carry no unguarded `json.load` |

**Pre-existing red, recorded not inherited (P-69).** `census-json-float-siblings.py` **already
exited 1 at the branch point** — its check "EVERY MECHANICAL CANDIDATE IS CLASSIFIED" fails
on `a2-29-retype-path.py`, `census-a2-26.py`, `mkje-a2-29.py`, three files landed after T163
by A2-29. Its committed transcript `RED-GREEN-T163-census-sabotage.txt` was captured at
`22 .py / 15 .sh / FAILURES: 0` and was **already stale before T164 existed**. My prover adds
a **fourth** name to that same already-failing list; it does not create a new failure and
does not change the exit code. Fixing it would mean editing `census-json-float-siblings.py`,
which produced committed evidence and is **T114-frozen** — and is outside this files_hint.

> **BACKLOG (new task):** `census-json-float-siblings.py`'s classification table has drifted
> four files behind the rig and its committed transcript is stale by 10 `.py` / 19 `.sh`.
> Under T114 the fix is a scratch successor plus a `SUPERSEDED.txt` redirect, not an edit.

## 7. T114 compliance — every file the ruling catches

| file | produced which committed evidence | what T164 did |
|---|---|---|
| `prove-mkreq7-guard-red.py` | `RED-GREEN-A2-7-guards.txt` | **untouched, byte-identical.** Re-run: still `16 assertions, 0 failed`. Its float arm is superseded by `guard-parse-float-ast.py`; its three unguarded `json.load`s are declared `FROZEN-T114`. |
| `analyze7.py` | its output is quoted in `A2-7.md` | **untouched.** It was already correct. |
| `resolve7.py` | `req/a2-7-loan-220-resolved.json` | **untouched.** Already superseded by `resolve8.py` in `SUPERSEDED.txt`. |
| `verify-provenance-a2-15.py` | `PROVENANCE-A2-15.txt` | **untouched.** (It cannot run from this checkout at all — its `ROOT` is hard-coded to a retired worktree.) |
| `census-json-float-siblings.py` | `RED-GREEN-T163-census-sabotage.txt` | **untouched**, read only. |
| `manifest.py` | `MANIFEST.sha256` | **untouched**; invoked `write` + `verify` as designed. |
| `SUPERSEDED.txt` | read by the census | **untouched** — appending to it would have moved the census's register count, a published number, for no gain. |
| `.softhouse/conformance.sh`, `.softhouse/capture/lib/`, `.softhouse/capture/t229-g8-site3/` | — | **untouched** (held by T253 / T250 / T259 this fire). |
| `.softhouse/vectors/**` | the parity corpus | **untouched.** Digest read live at start and finish. |

## 8. Tails — named, not silently left

1. **The old blind assertion still exists** at `prove-mkreq7-guard-red.py:143` and still
   prints `ok`. It cannot be deleted without breaking its own committed transcript (T114).
   It is **superseded**, not removed: `guard-parse-float-ast.py` is the authority, and the
   old file's three unguarded loads are now declared and machine-checked.
2. **`guard-parse-float-ast.py` is wired to nothing.** Like T185's F-4 and T207's §9.1, the
   successor grades correctly but no harness invokes it — `conformance.sh` is held by T253
   this fire and makes no reference to `tierA-a2` at all. **Wiring it is a follow-up task.**
3. **742 unresolved sweep sites** are unmeasured, not clean (§4.2).
4. **7 unwired self-match holes** outside `files_hint` (§4.1).
5. **`census-json-float-siblings.py` is four files behind and already red** (§6).
6. **`manifest.py` does not walk top-level subdirectories** — only `out/`, `req/`, `sql/`
   recursively and top-level *files*. A new subdirectory under `tierA-a2/` would be
   unhashed. Noticed while placing this task's files (which is why they are all top-level).
   Not exploited, not fixed — `manifest.py` is frozen. **Backlog.**

## 9. Files

**New**, all under `.softhouse/capture/tierA-a2/`:
`guard-parse-float-ast.py`, `PARSE-FLOAT-EXEMPT.txt`, `prove-parse-float-guard-red.py`,
`sweep-t164-selfmatch-guards.py`, `RED-GREEN-T164-parse-float-ast.txt`,
`SWEEP-T164-SELFMATCH-GUARDS.txt`.
**Modified:** `MANIFEST.sha256` only (6 lines added, 0 removed).
**Deleted:** none.
