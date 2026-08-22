# T263 — independent review of T164, `analyze7.py`'s float guard

**Reviewing:** T164, branch `softhouse/T164-analyze7-float-guard` @ `f0848190c62f1623e4bf99b7a873f39063213654`
(1 commit, 8 files, 2113 insertions, 0 deletions).
**Branch point:** `a71c1408d3315493bca763472598680c85b9ad0b`. **`main` at review time:** `7c292739`.
**Reviewer worktree:** `/Users/buv/gerege-nbfi/.claude/worktrees/agent-a8b0f7b84e947d39c`.
**Vector store, read live:** `git rev-parse HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`.
**UNMOVED**, and T164's diff touches nothing under `.softhouse/vectors/`.
**Oracle:** not contacted. Everything below runs against scratch copies in throwaway temp dirs.

I did not write the code under review. Every number in this document was produced by an
instrument I wrote for this review, listed in §12. I re-ran none of T164's own harness as
evidence of correctness; where I quote T164's transcript it is to compare against my own run.

---

## VERDICT: **MICRO-FIX**

The premise is true, the fix is a real improvement, and the load-bearing fail-open arm holds
under attack I designed. But the diff ships **three claims that are materially stronger than
what the code does**, one **register escape** that lets an out-of-tree file license an in-tree
float, and it leaves the old blind guard superseded **only in prose** while a review harness
still invokes it. Those are cheap to fix and must be fixed before this is called done.

**On the unwired-guard question, stated plainly, as asked:** see §11. Short answer — an unwired
guard **may** merge here, but **only** with the wiring task filed as a real dispatched task with
an owner, not as a bullet in a handoff. This program has shipped five unwired guards; the sixth
merging on a prose promise is the failure mode itself.

---

## Findings

### F-1 — the premise is TRUE. Not a phantom. **[VERIFIED — informational]**

I reproduced the original defect from scratch before reading T164's transcript.

Sabotage: on a scratch copy, delete `parse_float=decimal.Decimal` from `analyze7.py:39`
(`return json.load(f, parse_float=decimal.Decimal)` → `return json.load(f)`), leave the
docstring at `:6` alone. `parse_float` then occurs on line **[6] only** — the prose.

Running the **unmodified** `prove-mkreq7-guard-red.py` against that sabotaged rig:

```
analyze7.py — no binary floating point on any amount
  ok   it parses JSON numbers as Decimal
  ok   it never calls bare float()
  ok   an oracle amount literal loads as Decimal, not float  Decimal 1200000.000000

16 assertions, 0 failed
EXIT=0
```

Both limbs measured, not one (P-67). The sabotage is real:

```
SABOTAGED analyze7.load -> pageItems[0].amount = 1200000.0 type: float
```

The third assertion cannot save it: it calls `json.loads` **inline inside the prover**, not
through `analyze7.py`, so it is green regardless of what `analyze7.py` does. The second
assertion, `"float(" not in src.replace("parse_float=", "")`, is the same whole-file grep from
the negative side. **Where I looked (P-66/P-70):** `prove-mkreq7-guard-red.py:139-150`,
`analyze7.py:1-45`, run against a `cp -R` of the committed rig. A2-11's finding is confirmed
independently, not inherited.

---

### F-2 — the selector misses 11 of 17 adversarial shapes, and the anti-dodge check is itself a source-text grep. **[MEDIUM]**

I attacked the selector with shapes T164 did not design it around. **Every shape was also
EXECUTED** against `{"amount": 1200000.25}`, so a miss is a measured miss on a file that really
builds a binary double, never a miss on dead code. Each root also contained one compliant call
site, so the guard could never bail out on NIL COVERAGE and be scored as if it had caught
something. Full transcript: `ATTACK-SELECTOR.txt`.

| shape | verdict | runtime type | named in output? |
|---|---|---|---|
| `f = json.load; f(fp)` | **MISSED (exit 0, PASS)** | `float` | NO |
| `j = json; j.load(fp)` | **MISSED** | `float` | NO |
| `from json import *; load(fp)` | **MISSED** | `float` | NO |
| `import json.decoder` then `json.load(fp)` | **MISSED** | `float` | NO |
| `pf = float; json.load(fp, parse_float=pf)` | **MISSED** | `float` | **yes — graded `ok`** |
| `json.load(fp, parse_float=lambda s: float(s))` | **MISSED** | `float` | **yes — graded `ok`** |
| decorator-wrapped loader | **MISSED** | `float` | NO |
| `json.JSONDecoder().decode(text)` | **MISSED** | `float` | NO |
| `functools.partial(json.load)` | **MISSED** | `float` | NO |
| `getattr(json, "load")(fp)` | **MISSED** | `float` | NO |
| a `.py` in a **subdirectory** of the root | **MISSED** | `float` | NO |
| `json.load(fp, **opts)` | CAUGHT (1) | `float` | yes |
| nested function inside a comprehension | CAUGHT (1) | `float` | yes |
| conditional import in an `if` branch | CAUGHT (1) | `float` | yes |
| `try: import ujson as json / except: import json` | CAUGHT (1) | `float` | yes |
| plain `json.load` inside `try/except` | CAUGHT (1) | `float` | yes |
| `parse_float=float` literal | CAUGHT (1) | `float` | yes |

**17 shapes: 6 caught, 0 refused, 11 missed — all 11 really produce a binary double.**

Two of the misses are the sharp ones, because the guard **names the site, grades it `ok`, and
prints `PASS`**:

`resolves_to_builtin_float()` is
`expr_text in ("float", "builtins.float", "__builtins__.float")` — a **comparison against three
literal source strings**. It is a grep on source text, in the file written to replace a grep on
source text. It cannot fail on any expression it does not literally spell: `pf = float` and
`lambda s: float(s)` both sail through. The docstring states the property as *"the value it
passes is not the builtin `float`"*; the code enforces *"the unparsed keyword expression is not
one of three strings"*. Those are different properties and only the weaker one is implemented.

**The handoff's alias claim is overstated.** It says loader names are resolved from each file's
own imports "so `import json as J` / `from json import loads as L` cannot hide a site." True —
of **import** aliases. It is presented as covering aliasing, and **assignment aliasing hides a
site completely**, as does `from json import *` and `import json.decoder`.

**Severity bounded honestly.** I measured whether any of these shapes exists in the guard's own
scope today, with an independently written AST scan over the 29 tracked `tierA-a2/*.py`:
**zero** star-imports, zero variable-aliased loaders, zero rebound `json` modules, zero
`getattr(json, …)`, zero `JSONDecoder`. Across all 508 tracked `.softhouse/**/*.py` there is
exactly **one** `parse_float=<lambda>`, at `.softhouse/handoff/T57-float-scan.py:39` — outside
`tierA-a2`. So the guard's current green is **not** concealing a live float in its own scope,
which is why this is MEDIUM and not HIGH. It is the *claims* that must be corrected, and the
dodge check that must stop being a string comparison.

*Caveat on my own instrument (P-40):* my scan does not resolve imports, so its "bare name"
column is a false-positive generator (it flags legitimate `Decimal`/`str`/`JsonNumber`
bindings) and I have not relied on it. The structural columns above are the measured result.

*Not a defect:* `parse_float` **cannot** be passed positionally — it is keyword-only in
`json.load`/`json.loads` on this interpreter (Python 3.9.6,
`(fp, *, cls=None, object_hook=None, parse_float=None, …)`). The brief listed that shape; it is
not reachable and I record it as ruled out rather than untested.

---

### F-3 — ZERO CALL SITES = ERROR: the load-bearing arm holds. **[VERIFIED — no action]**

This is the class the original defect belonged to (P-45/P-80), so I verified it independently
rather than trusting ARM 3. Six arms, two of which T164 did not test. For each I asserted
**two** things (P-67): the exit code, **and** that the string `PASS` appears on neither stdout
nor stderr. Transcript: `ATTACK-NILCOVERAGE.txt`.

| arm | exit | `PASS` printed |
|---|---|---|
| empty directory (0 files at all) | 2 | no |
| directory of non-Python files only (`.json`/`.txt`/`.sh`) | 2 | no |
| Python files present, **zero** `json.load` call sites | 2 | no |
| one file that will not parse | 2 | no |
| **a single empty `.py`** *(not in T164's arms)* | 2 | no |
| **a root that does not exist** *(not in T164's arms)* | 2 | no |
| CONTROL: a compliant root | **0** | **yes** |

**ARMS FAILED: 0.** The refusal text names the cause every time
(`NIL COVERAGE — 0 Python files … INSPECTED NOTHING`;
`… 0 json.load/loads call sites found … This is an ERROR, not a pass`;
`broken.py will not parse … a file the guard cannot read is not a file the guard may skip`).
The control confirms the arms are not passing because the guard is inert. This part of T164 is
sound and I could not break it.

---

### F-4 — the exemption death conditions all fire, but `FROZEN-T114` is revivable by one routine command. **[MEDIUM]**

**All nine death conditions caused, all die correctly (exit 2).** Transcript:
`ATTACK-EXEMPT.txt`. Control first: the rig as committed is green (exit 0) and prints all six
records, so the arms below mean something.

| I caused | result |
|---|---|
| unknown category `FROZEN-T999` | REFUSE 2 |
| stale record — `resolve7.py:9999`, no such site | REFUSE 2 |
| target **fixed** so the record is unnecessary | REFUSE 2 |
| pinned source text drifted | REFUSE 2 |
| **frozen file edited** (sha256 moves) | REFUSE 2, `resolve7.py HAS BEEN EDITED (sha256 0d219a962063, manifest pins 61b80dabbfac)` |
| named committed evidence deleted | REFUSE 2 |
| `MANIFEST.sha256` removed | REFUSE 2 |
| malformed record (4 fields not 6) | REFUSE 2 |
| **`REPRODUCTION-T207` target gains `parse_float`** | REFUSE 2, `t263_target.py:3 NOW CARRIES parse_float — the target was fixed, so this is no longer a faithful reproduction` |

The last one required installing a `REPRODUCTION-T207` record, because **no live record uses
that category** (see F-10); I installed one, confirmed it grades `DECLARED REPRODUCTION-T207`
while the target is unfixed, then fixed the target and watched it die. The mechanism works.

Fail-closed behaviour also confirmed: **deleting** the register entirely → exit **1** (the six
declared sites become violations), and **emptying** it → exit **1**. It does not fail open.

**But the headline claim does not survive.** The register and the guard docstring both say:

> *"Edit the file and the exemption dies with it."*

It dies. It does not **stay** dead. `MANIFEST.sha256` is not immutable — `manifest.py write`
regenerates it, and **T164's own task ran it**. Measured end to end (`ATTACK-REVIVE.txt`):

```
ARM R1 -- edit a frozen file, then re-run `manifest.py write`
    1. pristine rig                              exit=0
    2. after editing the frozen file             exit=2   <- the exemption died
    3. `manifest.py write`                       exit=0   wrote MANIFEST.sha256 with 969 entries
    4. re-grade after manifest write             exit=0   <- IT CAME BACK TO LIFE
    -> ALLOW resolve7.py:24 FROZEN-T114  frozen: sha256 matches MANIFEST.sha256
```

`resolve7.py` now carries an edit **and is still exempt**. The property the register advertises
is cryptographic self-invalidation; what it actually delivers is **a diff a human must read**.

**And a new exemption can be minted in two commands** (ARM R2). A brand-new file with an
unguarded, money-shaped `json.load`:

```
1. new unguarded loader, no register record          exit=1   (default-deny works)
2. + a FROZEN-T114 record, before manifest write     exit=2   (MANIFEST does not pin it yet)
3. `manifest.py write`                               exit=0
4. re-grade                                          exit=0   <- MINTED
   ALLOW  t263_newmoney.py:5  FROZEN-T114  frozen: sha256 matches MANIFEST.sha256;
                                            produced RED-GREEN-A2-7-guards.txt
```

…for a file that produced **no** evidence, naming evidence belonging to another file. ARM R3:
`manifest.py verify` **also passes** afterwards, so nothing else in the rig notices either.

**Answering the brief's question directly — can a new exemption be added without review?** No,
not silently: both R1 and R2 require a committed change to `MANIFEST.sha256` (and R2 to the
register), visible in `git diff`. **Is the exempt list enumerated in the guard's output?** Yes —
all six records are printed in full on every run with category, precondition outcome and reason;
I counted 12 `FROZEN-T114` occurrences in one green run. That part is honest and good.

**Required micro-fix:** correct the claim in `PARSE-FLOAT-EXEMPT.txt` and in
`guard-parse-float-ast.py`'s docstring. "Edit the file and the exemption dies with it" must
become something like *"…dies until `MANIFEST.sha256` is regenerated; the durable control is
review of the manifest diff, and a manifest diff that re-pins an exempted file is a red flag."*
This matters because the entire justification for leaving a **MATERIAL** float site unguarded
(F-8, F-9) rests on this property being what it says it is.

---

### F-5 — `produced:` is existence-only, not provenance. **[MEDIUM]**

`check_frozen` verifies the named evidence path **exists**. It never verifies the exempted file
produced it. Measured: swap
`produced:req/a2-7-loan-220-resolved.json` → `produced:CAPTURE-PLAN.md` on the `resolve7.py:24`
record and the guard stays **green (exit 0)**. Any existing path in the rig satisfies the field,
which is what makes the R2 minting in F-4 possible. The field reads as an audit trail and is not
one.

**Micro-fix:** at minimum, state in the register header that `produced:` is a human-asserted
claim the guard only existence-checks. Better: require the evidence path to appear in
`MANIFEST.sha256` **and** the exempted file's name to occur in the evidence file (both of which
hold for all six live records today — `RED-GREEN-A2-7-guards.txt:3` literally reads
`Produced by:  python3 prove-mkreq7-guard-red.py`).

---

### F-6 — `reproduces:` accepts an absolute path outside the repository. **[MEDIUM]**

`check_reproduction` does `ap = tpath if os.path.isabs(tpath) else os.path.join(root, tpath)`.
An absolute path is taken as given. Measured: a `REPRODUCTION-T207` record pointing at
`/tmp/t263-outside-XXXX/external.py:3` — a file outside the rig, outside the repo, tracked by
nothing — is graded **`DECLARED REPRODUCTION-T207`** and the guard exits **0**.

An untracked, unreviewable, deletable out-of-tree file can license an in-tree unguarded money
load, and the licence silently changes meaning when that file changes. There is no legitimate
use for this: every T207 reproduction target named anywhere in this program
(`measure-other-sites-v2.py:85,86` → `t55-prior-capture-assessment.py:52`,
`t55-analyse.py:109`) is in-tree.

**Micro-fix, one line:** reject any `reproduces:` target that is absolute, or that escapes
`root` after `os.path.realpath` normalisation — `..` is untested but reaches the same place.

---

### F-7 — the guard does not verify its own register's integrity. **[LOW]**

Inserting a comment line into `PARSE-FLOAT-EXEMPT.txt` leaves the guard **green**; it never
compares the register against the digest `MANIFEST.sha256` pins for it
(`85e1bdbc79ad07f5cd84de70dcf7e4c38f869c7f34407bfb4d7f797ecc0aa448`). Mitigated in principle —
`manifest.py verify` would catch it — but the guard is wired to nothing (F-12) and
`manifest.py verify` is a separate manual invocation, so **nothing in the rig runs both**. The
guard already reads `MANIFEST.sha256`; checking one more digest is a two-line addition.

Related nit: `read_register` strips at the first `#` (`line.split("#")[0]`), so a pinned source
line containing `#` can never match. That direction fails **closed** (DRIFT → REFUSE), so it is
a documentation gap, not a hole.

---

### F-8 — materiality: all three re-measured claims are exact. **[VERIFIED]**

Re-measured from the same documents with my own leaf counter before reading T164's numbers
(`REMEASURE-MATERIALITY.txt`). A JSON-float leaf = a leaf `json` parsed into a Python `float`.

| site | T164 claims | **I measure** |
|---|---|---|
| `resolve7.py:24` — `req/*.json` | MATERIAL, 11 leaves over 117 files | **117 files, 11 leaves** ✔ |
| `resolve7.py:25` — `out/A2-21*.json` | MATERIAL, 12 leaves over 5 files | **5 files, 12 leaves** ✔ |
| `verify-provenance-a2-15.py:24` — `vectors/ledger/*.json` | 0 leaves over 6 vectors | **6 files, 0 leaves** ✔ |

Sample leaves confirm the shapes cited: `/debits/0/amount = 100000.25`,
`/credits/0/amount = 125000.62`, `/principal = 1200000.0`. The three sandbox sites have no
on-disk corpus and I did not re-measure them; stated, not assumed (P-40).

**One thing T164 did not state, in its own favour and against it.** The template `resolve7.py`
was actually run on — `req/a2-7-loan-220.json` — has **0** float leaves. The 11 leaves live in
`a2-26-manual-je-*.json`, which `resolve7.py` was never run on. So the committed evidence is
**undamaged**, and "MATERIAL" is a statement about latent risk rather than realised corruption.
That is the conservative direction and the label is right; the register would be clearer if it
said so.

---

### F-9 — T207 applied correctly, and not used as cover. **[VERIFIED — LOW residual]**

The brief's rule: *any site where a money amount becomes a binary double and is then used to
decide or carry a value is a HIGH finding, exemption or not.*

`resolve7.py:24` **is** a carrying site by construction — `:24` `json.load(open(tmpl))` →
`:34` `json.dumps(body, indent=2)` → `:39` `f.write(text)`, and that file is a **request body
POSTed to the reference oracle**. Not observed-and-discarded. I checked whether that makes it a
live HIGH, and it does not, for reasons that pre-date T164 and that I verified rather than
accepted:

- T163 already fixed it: `resolve8.py:101,265` both carry `parse_float=JsonNumber` (confirmed in
  the guard's own site table).
- `SUPERSEDED.txt` carries **both** required redirects: `resolve7.py -> resolve8.py` **and** its
  only caller, `run-220-a2-7-runtime.sh -> run-220-a2-7-runtime-v8.sh`.
- The census **enforces** those redirects, and enforces that each replacement is itself clean —
  I ran it at the branch point: `EVERY REDIRECT POINTS AT A REPLACEMENT THAT EXISTS AND IS
  ITSELF CLEAN … 4 redirect(s) verified`, PASS.
- `resolve7.py:25` is genuinely different: only `resp[key]` is read out of it, so its 12 leaves
  are observed and discarded, never carried. T164 labels both MATERIAL, which over-states `:25`
  in the safe direction.

**Did T164 use T207 as cover?** No — the opposite. It categorised **all six** sites as
`FROZEN-T114` and used `REPRODUCTION-T207` for **none**, correctly noting that T207's two
reproduction sites are at `measure-other-sites-v2.py:85,86` under `leapboundary/`, outside its
`files_hint`. I verified that attribution: the "wrong repair" ruling is real and is recorded at
`.softhouse/capture/leapboundary/analysis/T207/measure-other-sites-v2.py:20-26`, in
`program.json:1706` and in `tasks.json:264`. Minor citation nit — the sentence is **not** in
`RULING-float-derived-predicate.md` itself, which T164 and the register both cite as its home;
the ruling document covers the Zone-A float-derived-predicate half only.

**LOW residual:** the guard's top line is `PASS — … 6 are declared and their preconditions
hold, 0 violations`. It does not distinguish a **WIRE-carrying** exemption from an
analysis-only one; the distinction lives only in the free-text `reason`. A one-word column
(`WIRE` / `ANALYSIS` / `SANDBOX`, which the census already computes) would stop a green run
reading as "no float reaches the wire."

---

### F-10 — `REPRODUCTION-T207` is implemented, red-driven, and used by zero live records. **[LOW]**

Dead surface in a security-relevant register. It works (I exercised it in F-4), but no live
record uses it, so it will rot unobserved. Either delete it until a site needs it, or state in
the register header that it is currently unexercised by any live record.

---

### F-11 — the sweep is honest, and its Term 2 reproduces on an independent run. **[VERIFIED]**

**P-75 compliance of the instrument, measured not assumed.** I scanned all three new `.py`
files for actual invocations (`subprocess.*`, `os.system`, `os.popen` containing `grep`/`rg`):
**0 in all three.** The words appear only in prose and in the regexes the sweep uses to *detect*
shell greps. No bare `grep`, no `rg`.

**Internal arithmetic is consistent** (I checked every identity, P-67):
54 + 742 = **796** (Term 1); 8 + 46 = **54** (resolvable); 10 + 1 = **11** wired-with-resolvable-
target; 191 + 605 = **796**.

**I re-ran the sweep from this checkout.** It reports **12 holes, 5 wired** — but four of the
five "extra" wired holes are `prove-mkreq7-guard-red.py:143` inside **my own scratch copies** of
the rig, which inflated the walked population from 5,145 to 9,028 files. Discounting my scratch
copies: **8 holes, exactly 1 wired — T164's Term 2 reproduces exactly.** (Worth recording as a
property of the instrument: its denominator is checkout-dependent, and an untracked copy of the
rig in the tree changes the published figure.)

**Spot-check of the 7 declined holes — all correctly classified as unwired.** I read each in
context:

| site | shape | verdict |
|---|---|---|
| `t243-wiring/instruments/10-wrongimpl-red-drive.sh:91` | `echo -n …; grep -c … \|\| true` | exit status discarded, count printed. **Evidence dump.** ✔ |
| `reviews/T184-evidence/t184-sweep.sh:15,18` | `grep -n …`, `… \|\| echo "(the one…)"` | prints only, no assertion, no exit code. **Evidence dump.** ✔ |
| `reviews/a2-34-review-a2-15/bar-and-oracle.sh:76,77` | `grep -n -aF … \| head -4/-6` | prints only. **Evidence dump.** ✔ |
| `reviews/a2-34-review-a2-15/check-money-and-additive.sh:60,61` | `grep -n -aF … \| head -20/-5` | prints only. **Evidence dump.** ✔ |

**None is live.** T164's classification stands.

**Is 742 honestly labelled?** Yes, everywhere I checked: the transcript header
("*they are UNMEASURED, they are counted, and the denominator is printed in words*"), the sweep
body ("*NOT a measured negative — they are unmeasured, and counted as such*"), handoff §0
("*unmeasured, not clean, and are counted as such*") and §4.2. I found no place where it is
reported as clean.

Pre-existing backlog observed, **not T164's**: `reviews/T184-evidence/t184-sweep.sh` itself uses
**bare `grep`** (P-75) and hard-codes a retired worktree path
(`/Users/…/worktrees/agent-ae0f13a1bbf7c82f8`), so it cannot run from a fresh checkout.

---

### F-12 — the new guard is wired to nothing. **[MEDIUM — P-45, the sixth instance]**

Measured, not inferred: `git grep -F guard-parse-float-ast` over the entire T164 branch returns
the `MANIFEST.sha256` digest line, the register's own header comment, its own transcript, its
own docstring usage lines, its red-driver, and the handoff. **Zero executable callers.** Not in
`.softhouse/conformance.sh`, not in any `run-*.sh`, not in `.softhouse/bin/`.

T164 states this itself (handoff §8.2) and its reason is true — `conformance.sh` was held by
T253 this fire, and I confirmed `conformance.sh` makes no reference to `tierA-a2`, so there is
not even an existing hook to extend. That is an explanation, not a mitigation. See §11.

---

### F-13 — the old blind guard is superseded only in prose, and a live harness still runs it. **[MEDIUM]**

`prove-mkreq7-guard-red.py` is **absent from `SUPERSEDED.txt`**. That file is the rig's
machine-read supersession register — the census enforces it, and at the branch point it holds
exactly four redirects (`resolve7.py`, `cap.sh`, `run-220-a2-7-runtime.sh`, `cap9.sh`). The old
guard's supersession exists only in three prose locations: the new guard's docstring, a comment
in `PARSE-FLOAT-EXEMPT.txt`, and the handoff.

Meanwhile **`.softhouse/reviews/A2-11/run-all.sh:36` still invokes it**:

```
  python3 "$DIR/../../capture/tierA-a2/prove-mkreq7-guard-red.py"; echo "exit=$?"
```

So the trap is live exactly as the brief describes: run A2-11's harness today and you get
`ok   it parses JSON numbers as Decimal` / `16 assertions, 0 failed` / `exit=0`, with nothing on
screen saying that arm is dead — sitting next to a real guard that says the opposite.

T164 declined the `SUPERSEDED.txt` line because it would move the census's published register
count "for no gain." **I tested the fix rather than asserting it.** Appending
`prove-mkreq7-guard-red.py -> guard-parse-float-ast.py`:

```
SUPERSESSION REGISTER (SUPERSEDED.txt) — 5 entr(ies)
  PASS  EVERY WIRE WRITER IS EITHER CLEAN OR REDIRECTED …
  PASS  EVERY REDIRECT POINTS AT A REPLACEMENT THAT EXISTS AND IS ITSELF CLEAN …
          5 redirect(s) verified
FAILURES: 1          <- unchanged, the pre-existing one
CENSUS EXIT=1        <- unchanged
```

Accepted. Exactly **one** published number moves — the register count 4 → 5 — and it is recorded
when it moves. The trade T164 made was the wrong way round: a recorded +1 on a register count is
cheaper than a blind guard printing `ok` next to a real one.

---

### F-14 — every published number re-derives exactly, and the pre-existing red genuinely pre-dates the branch. **[VERIFIED]**

**Manifest.** `MANIFEST.sha256` is 963 lines at `main` **and** at the branch point `a71c140`,
969 at the tip. `git diff -U0 main...` on that file: **6 hunks, 6 added, 0 removed, 0 changed** —
the six new rig files and nothing else. **No pre-existing digest moved**, so T236's 13-discrepancy
history is untouched. `manifest.py verify` at the tip: **exit 0**,
`OK: 969 files match MANIFEST.sha256 (884 under out/ req/ sql/, 85 rig + docs, this script included)`.

**Census — "already red at the branch point" is a verified fact here, not a worker's claim,
because I ran it on the branch-point tree itself:**

```
CENSUS AT BRANCH POINT a71c140  EXIT=1
  POPULATION: 29 Python file(s), 34 shell file(s)
  FAIL  EVERY MECHANICAL CANDIDATE IS CLASSIFIED
          unclassified: ['a2-29-retype-path.py', 'census-a2-26.py', 'mkje-a2-29.py']
  FAILURES: 1
```

That is the same three files T164 names, landed by A2-29 before T164 existed. At the tip:

| number | branch point | tip | T164 claimed | ✔ |
|---|---|---|---|---|
| manifest file count | 963 | **969** | 963 → 969 | ✔ |
| census POPULATION `.py` | 29 | **32** | 29 → 32 | ✔ |
| census candidates | 20 | **21** | 20 → 21 | ✔ |
| census unclassified | 3 | **4** (`+prove-parse-float-guard-red.py`) | 3 → 4 | ✔ |
| census R5 scope | 12 files, 0 float literals | **13 files, 0 float literals** | 12 → 13 | ✔ |
| census exit code | 1 | **1** (same single failure) | unchanged | ✔ |

**Guard transcript reproduces.** Live run on the pristine T164 rig:
`SELECTOR SELF-TEST: 4 synthetic call sites … 3 decoy line(s)`, then
`PASS — 20 call site(s) across 32 file(s): 14 carry parse_float=, 6 are declared and their
preconditions hold, 0 violations.` — byte-consistent with `RED-GREEN-T164-parse-float-ast.txt`.

---

### F-15 — the guard is non-recursive, reproducing the `manifest.py` blindness it recorded as backlog. **[LOW]**

`main()` uses `os.listdir(root)`, not a walk. `tierA-a2` has three subdirectories (`out/`,
`req/`, `sql/`); I measured that none contains a `.py` today (32 `.py` recursive == 32 `.py`
top-level), so the hole is **not live**. But a `.py` placed in a subdirectory is silently
ungraded and the guard still prints `PASS` — shape Q in F-2, verified by execution.

T164 recorded exactly this shape as backlog item §8.6 for `manifest.py` ("*a new subdirectory
under `tierA-a2/` would be unhashed*"). It did not notice it had reproduced it in its own new
file. Either walk, or state the top-level-only scope in the docstring **and** print the
directory count that was skipped.

---

### F-16 — the sweep transcript is not re-derivable as committed. **[LOW]**

`SWEEP-T164-SELFMATCH-GUARDS.txt` records
`ROOT: /Users/…/worktrees/agent-a3ab0be4544b8a0a8/.softhouse` — a retired worktree. The script
takes the repo root as `argv[1]` and appends `.softhouse`, which is undocumented in the
transcript, so a reader cannot reproduce it without reading `sweep-t164-selfmatch-guards.py:310`.
Cosmetic; I did reproduce it (F-11) after finding the calling convention.

---

## Scope — confirmed independently

`git diff --name-status main...softhouse/T164-analyze7-float-guard`:

```
M  .softhouse/capture/tierA-a2/MANIFEST.sha256
A  .softhouse/capture/tierA-a2/PARSE-FLOAT-EXEMPT.txt
A  .softhouse/capture/tierA-a2/RED-GREEN-T164-parse-float-ast.txt
A  .softhouse/capture/tierA-a2/SWEEP-T164-SELFMATCH-GUARDS.txt
A  .softhouse/capture/tierA-a2/guard-parse-float-ast.py
A  .softhouse/capture/tierA-a2/prove-parse-float-guard-red.py
A  .softhouse/capture/tierA-a2/sweep-t164-selfmatch-guards.py
A  .softhouse/handoff/T164-analyze7-float-guard.md
```

**Eight paths, all inside `files_hint` (`.softhouse/capture/tierA-a2/`) plus the handoff.
One modified file, and it is the manifest, additively. Nothing under `nexus/`,
`.softhouse/vectors/`, `.softhouse/conformance.sh`, `.softhouse/bin/`, or `.softhouse/capture/lib/`.
Confirmed independently — the driver's finding holds.** T114 is honoured: every
evidence-producing file is byte-identical.

---

## §11 — May an unwired guard merge? **Yes, conditionally. State the condition in the merge record.**

This program has now shipped **five** guards that enforced nothing between their commit and the
task that noticed: `manifest.py verify`, `t44_float_roundtrip_v3`, T173's float guard,
`guard_ledger_invariants`, and T207's `v3` (its own §9.1). `guard-parse-float-ast.py` is the
sixth. T164 names it honestly, which is the difference between a tail and a lie.

**Holding the branch is the worse option.** If T164 does not merge, the only float guard on disk
for `analyze7.py` remains the blind grep — which I proved in F-1 passes on a sabotaged rig. A
correct-but-unwired guard strictly dominates an incorrect-but-wired one.

**So it may merge — but not as if the job were finished.** The condition:

> A wiring task must be **filed and dispatched with an owner** before this merge is recorded —
> not carried as a bullet in a handoff. It must (a) invoke `guard-parse-float-ast.py` from
> `.softhouse/conformance.sh` once T253 releases it, (b) treat exit 2 as a hard failure of the
> conformance run and not a skip, and (c) be driven red by breaking the rig and confirming
> `conformance.sh` goes red.

Without (c) the wiring is itself unverified, which is how this shape recurs. A handoff bullet is
not a task; five previous instances are the evidence.

---

## Micro-fixes required before this is done

1. **F-2** — correct the alias claim in the handoff and docstring (import aliases only), and
   make the dodge check something other than a three-string source comparison, or state plainly
   that it only catches the literal spelling `float`.
2. **F-4** — correct "edit the file and the exemption dies with it" in both
   `PARSE-FLOAT-EXEMPT.txt` and `guard-parse-float-ast.py`: the death is undone by
   `manifest.py write`; the durable control is review of the manifest diff.
3. **F-6** — reject absolute and `root`-escaping `reproduces:` targets. One line.
4. **F-13** — add `prove-mkreq7-guard-red.py -> guard-parse-float-ast.py` to `SUPERSEDED.txt`
   and record the register count 4 → 5. Verified accepted by the census.
5. **F-12/§11** — file the wiring task with an owner and a red-drive requirement.

Recommended, not blocking: F-5 (`produced:` provenance), F-7 (register self-digest), F-9
(WIRE/ANALYSIS column on the verdict line), F-15 (walk, or state top-level-only).

**T164 must not edit anything it froze to do these** — items 1–3 touch only files T164 itself
created this branch, and item 4 appends to `SUPERSEDED.txt`, which is not evidence-producing.

---

## §12 — what I could not verify, and my instruments

**Could not verify:**
- The three sandbox exemption sites' materiality (`prove-mkreq7-guard-red.py:70,119,126`) —
  their documents are built inside `tempfile.mkdtemp` at run time, so there is no on-disk corpus
  to count. T164's "0 leaves" is plausible from the document shapes it quotes
  (`{"clientId": 1, "productId": 46}`) but I did not re-derive it.
- `verify-provenance-a2-15.py` cannot run from any checkout (hard-coded retired-worktree `ROOT`),
  so I measured its corpus but not its behaviour.
- Whether T253's eventual `conformance.sh` will accept the wiring — that file is held this fire
  and I did not touch it.
- Whether `git grep`'s own recall is complete for the `guard-parse-float-ast` caller search
  (F-12); `git grep` exited **0** with hits, so this is a positive result, not an absence.

**Instruments I wrote for this review** (all in this directory, all `set -euo pipefail` or
Python with explicit abort-on-unexpected-exit; **no bare `grep`, no `rg`**; a guard exit outside
`{0,1,2}` aborts rather than being recorded):

| file | transcript | what it does |
|---|---|---|
| `attack-selector.py` | `ATTACK-SELECTOR.txt` | 17 adversarial shapes, each executed as well as graded |
| `attack-nilcoverage.sh` | `ATTACK-NILCOVERAGE.txt` | 6 fail-open arms + control; asserts exit code **and** absence of `PASS` |
| `attack-exempt.py` | `ATTACK-EXEMPT.txt` | 9 death conditions caused + 6 widening attacks |
| `attack-revive.py` | `ATTACK-REVIVE.txt` | is the freeze revivable? R1/R2/R3 |
| `remeasure-materiality.py` | `REMEASURE-MATERIALITY.txt` | independent JSON-float-leaf counts + the carry analysis |
| — | `SWEEP-RERUN-T263.txt` | my re-run of T164's sweep from this checkout |
| — | `CENSUS-AT-BRANCH-POINT.txt`, `CENSUS-AT-TIP.txt` | census at `a71c140` and `f084819` |
| — | `GUARD-LIVE-RERUN.txt` | the guard's green run on the pristine T164 rig |

Scratch copies of the rig used for the attacks were deleted after the transcripts were captured,
so this directory does not duplicate `tierA-a2` into the tree (see F-11 for why that matters).

**Vector store at the end of this review, read live:**
`git rev-parse HEAD:.softhouse/vectors` = `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`. **Unmoved.**
All claims above are stamped to T164 `f0848190c62f1623e4bf99b7a873f39063213654` (P-69).
